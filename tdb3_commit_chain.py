#!/usr/bin/env python3
"""SoftCAD TDB3 0.5.0 RC1 independent read-only commit ancestry verifier.

Checks only the active K commit chain up to 64 commits and 32 MiB of chunks.
Does not traverse catalogs, document contents, journal, index trees or Merkle DAG.
No source from the TDB3 engine is included or imported.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import struct
import zlib
from tdb3_root_probe import inspect as inspect_root

MAX_CANON = 8 * 1024 * 1024
MAX_CHUNK = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
MAX_COMMITS = 64
CHUNK = struct.Struct('>4sBBHIII')
LOC = struct.Struct('>QI')

class _Reference(dict):
    """Only a binary tag 0x09 can construct this internal reference type."""

class ConformanceError(ValueError):
    """An expected, reportable format or integrity failure."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _varint(data: bytes, pos: int) -> tuple[int, int]:
    val = 0
    for shift in range(0, 70, 7):
        if pos >= len(data):
            raise ConformanceError('commit_truncated_varint')
        byte = data[pos]
        pos += 1
        val |= (byte & 127) << shift
        if byte < 128:
            return val, pos
    raise ConformanceError('commit_varint_out_of_range')


def _take(data: bytes, off: int, count: int) -> bytes:
    if count < 0 or off < 0 or off + count > len(data):
        raise ConformanceError('commit_canonical_truncated')
    return data[off:off + count]


def _parse_value(data: bytes, off: int, loc: list[tuple[int,int]], cursor: list[int], depth: int=0):
    if depth > 8:
        raise ConformanceError('commit_decode_depth_limit')
    tag = _take(data, off, 1)[0]
    off += 1
    if tag in (0, 1, 2):
        return (None if tag == 0 else tag == 2), off
    if tag == 3:
        v, off = _varint(data, off)
        return ((v >> 1) if not (v & 1) else -((v + 1) >> 1)), off
    if tag == 4:
        return struct.unpack('>d', _take(data, off, 8))[0], off + 8
    if tag in (5, 6):
        n, off = _varint(data, off)
        if n > MAX_CANON:
            raise ConformanceError('commit_string_limit')
        blob = _take(data, off, n)
        if tag == 5:
            try:
                return blob.decode('utf-8'), off + n
            except UnicodeDecodeError as e:
                raise ConformanceError('commit_invalid_utf8') from e
        return blob, off + n
    if tag == 9:
        digest = _take(data, off, 32)
        count, off = _varint(data, off + 32)
        i = cursor[0]
        if i >= len(loc):
            raise ConformanceError('commit_missing_locator')
        cursor[0] += 1
        pos, n = loc[i]
        return _Reference(sha256=digest.hex(), offset=pos,
                length=n, count=count, locator_index=i), off
    if tag in (7, 8):
        n, off = _varint(data, off)
        if n > 2048:
            raise ConformanceError('commit_collection_limit')
        if tag == 7:
            values=[]
            for _ in range(n):
                value, off = _parse_value(data,off,loc,cursor,depth+1)
                values.append(value)
            return values, off
        values={}
        old_key = None
        for _ in range(n):
            klen, off = _varint(data, off)
            if klen > MAX_CANON:
                raise ConformanceError('commit_key_limit')
            kb = _take(data, off, klen)
            if old_key is not None and kb <= old_key:
                raise ConformanceError('commit_noncanonical_keys')
            old_key = kb
            off += klen
            try:
                key = kb.decode('utf-8')
            except UnicodeDecodeError as e:
                raise ConformanceError('commit_invalid_utf8') from e
            values[key], off = _parse_value(data,off,loc,cursor,depth+1)
        return values, off
    raise ConformanceError('commit_unknown_value_tag')


def _read_commit(f, ref: dict, committed_end: int, budget: list[int]):
    off, length = ref['offset'], ref['length']
    if off < 12288 or length < CHUNK.size or off + length > committed_end:
        raise ConformanceError('history_parent_outside_commit')
    if length > MAX_CHUNK or budget[0] + length > MAX_TOTAL:
        raise ConformanceError('history_read_limit')
    f.seek(off)
    raw = f.read(length)
    if len(raw) != length:
        raise ConformanceError('history_short_chunk')
    budget[0] += length
    magic, kind, codec, unused, canon_len, stored_len, count = CHUNK.unpack_from(raw)
    if magic != b'\xd7TB3' or kind != ord('K') or codec not in (0, 1):
        raise ConformanceError('history_commit_chunk_type')
    if count > 4096:
        raise ConformanceError('history_locator_limit')
    if CHUNK.size + stored_len + LOC.size * count != length:
        raise ConformanceError('history_chunk_length_mismatch')
    if canon_len > MAX_CANON:
        raise ConformanceError('history_read_limit')
    packed = raw[CHUNK.size:CHUNK.size+stored_len]
    if codec == 0:
        data = packed
    else:
        try:
            decoder = zlib.decompressobj()
            data = decoder.decompress(packed, MAX_CANON + 1)
            if len(data)>MAX_CANON or decoder.unconsumed_tail or not decoder.eof or decoder.unused_data:
                raise ConformanceError('history_invalid_zlib_chunk')
            data += decoder.flush()
        except zlib.error as e:
            raise ConformanceError('history_invalid_zlib_chunk') from e
    if len(data) != canon_len:
        raise ConformanceError('history_canonical_length_mismatch')
    if hashlib.sha256(data).hexdigest() != ref['sha256']:
        raise ConformanceError('history_parent_sha256_mismatch')
    locoff = CHUNK.size + stored_len
    loc = [LOC.unpack_from(raw, locoff + i * LOC.size) for i in range(count)]
    cursor=[0]
    value,end = _parse_value(data,0,loc,cursor)
    if end != len(data) or cursor[0] != len(loc):
        raise ConformanceError('history_commit_encoding_mismatch')
    if not isinstance(value,dict) or not isinstance(value.get('secventa'),int) or isinstance(value.get('secventa'),bool):
        raise ConformanceError('history_commit_metadata_invalid')
    parent = value.get('parinte')
    catalog = value.get('catalog')
    if parent is not None and not isinstance(parent,_Reference):
        raise ConformanceError('history_parent_type_invalid')
    if catalog is not None and not isinstance(catalog,_Reference):
        raise ConformanceError('history_catalog_type_invalid')
    return {'sequence':value['secventa'], 'parent':parent,
            'catalog_exists':catalog is not None, 'locator_count':count}


def inspect(path: Path, max_commits: int=MAX_COMMITS) -> dict:
    """Verify active commit and parent K chunks only; fail closed on corrupt refs."""
    path=Path(path)
    root=inspect_root(path)
    result={'layout':'TDB3 0.5.0 RC1', 'scope':'active commit ancestry (K chunks) only; no catalog, Merkle, or row validation',
            'checked':False,'verified':False,'complete':False,'commit_count':0,
            'max_commits':max_commits,'commits':[]}
    if not root.get('verified'):
        return dict(result,reason='history_root_not_verified')
    if not 1 <= max_commits <= MAX_COMMITS:
        raise ValueError('max_commits must be 1..64')
    ref={'offset':root['root_offset'],'length':root['root_length'],'sha256':root['expected_sha256']}
    end=root['committed_end']
    expected_sequence=int(root['active_sequence'])
    visited=set()
    budget=[0]
    try:
        with path.open('rb') as f:
            for level in range(max_commits):
                key=(ref['offset'],ref['length'],ref['sha256'])
                if key in visited:
                    raise ConformanceError('history_cycle_detected')
                visited.add(key)
                commit=_read_commit(f,ref,end,budget)
                seq=commit['sequence']
                if (level == 0 and (seq != expected_sequence or seq < 1)) or (level > 0 and (seq >= expected_sequence or seq < 1)):
                    raise ConformanceError('history_sequence_invalid')
                parent=commit['parent']
                result['commits'].append({'sequence':str(seq), 'sha256':ref['sha256'],
                    'offset':ref['offset'],'parent_exists':parent is not None,
                    'catalog_exists':commit['catalog_exists']})
                result['commit_count']=len(result['commits'])
                expected_sequence=seq
                if parent is None:
                    result.update(checked=True,verified=True,complete=True,read_bytes=budget[0],
                                  reason='history_chain_valid_complete')
                    return result
                if parent['offset']>=ref['offset']:
                    raise ConformanceError('history_parent_not_older')
                ref=parent
    except ConformanceError as e:
        return dict(result,checked=True,read_bytes=budget[0],reason=e.reason)
    result.update(checked=False,verified=False,complete=False,read_bytes=budget[0],
                  reason='history_chain_limit_reached')
    return result

if __name__=='__main__':
    import argparse,json,sys
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file',type=Path)
    parser.add_argument('--strict',action='store_true')
    args=parser.parse_args()
    report=inspect(args.file)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    sys.exit(0 if (not args.strict or report['verified']) else 2)
