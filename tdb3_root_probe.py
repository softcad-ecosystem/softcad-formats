"""TDB3 0.5.0 RC1 read-only root-chunk integrity probe.
Public minimal independent verifier. Does not parse tables or validate history.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import struct
import zlib

MAGIC = b'TDB3\x00\r\n\x1a'
HEADER = struct.Struct('>8sHHd16sI')
SUPER = struct.Struct('>8sQQI32sQI')
CHUNK = struct.Struct('>4sBBHIII')
MAX_CANON = 8 * 1024 * 1024
MAX_STORED = 8 * 1024 * 1024


def inspect(path: Path) -> dict:
    size = path.stat().st_size
    result = {'layout':'TDB3 0.5.0 RC1','checked':False,'verified':False,
              'scope':'active commit root only; not the complete Merkle tree or database'}
    with path.open('rb') as f:
        prefix = f.read(12288)
        if len(prefix)<12288 or not prefix.startswith(MAGIC):
            return dict(result, reason='not_tdb3_or_short_file')
        magic,ver,reserved,created,ident,crc = HEADER.unpack_from(prefix)
        result['storage_version'] = ver
        result['header_crc_valid'] = (zlib.crc32(prefix[:36]) & 0xffffffff)==crc
        if ver!=1 or not result['header_crc_valid']:
            return dict(result, checked=True, reason='unsupported_version_or_header_crc')
        slots=[]
        for off in (4096,8192):
            block=prefix[off:off+SUPER.size]
            mag,seq,pos,ln,sha,end,check=SUPER.unpack(block)
            valid=(mag==b'TDB3SUPR' and (zlib.crc32(block[:-4]) & 0xffffffff)==check)
            slots.append({'slot_offset':off,'sequence':seq,'root_offset':pos,'root_length':ln,
                          'root_sha256':sha.hex(),'committed_end':end,'valid_crc':valid})
        result['superblocks']=[{'slot_offset':s['slot_offset'],'sequence':str(s['sequence']),'valid_crc':s['valid_crc']} for s in slots]
        valid=[s for s in slots if s['valid_crc']]
        if not valid:return dict(result,checked=True,reason='no_valid_superblock')
        active=max(valid,key=lambda s:s['sequence'])
        result.update(active_slot_offset=active['slot_offset'],active_sequence=str(active['sequence']),
                      root_offset=active['root_offset'],root_length=active['root_length'],
                      expected_sha256=active['root_sha256'],committed_end=active['committed_end'],
                      physical_end=size,uncommitted_tail_bytes=max(0,size-active['committed_end']))
        off,ln,end=active['root_offset'],active['root_length'],active['committed_end']
        result['checked']=True
        if end>size or end<12288:
            return dict(result,reason='commit_boundary_outside_file')
        if off<12288 or ln<CHUNK.size or off+ln>end:
            return dict(result,reason='root_reference_outside_commit')
        if ln>MAX_STORED:
            return dict(result,checked=False,reason='root_chunk_exceeds_read_limit')
        f.seek(off)
        body=f.read(ln)
    if len(body)!=ln:return dict(result,reason='short_root_chunk')
    sig,kind,codec,reserved,canonical_len,stored_len,nloc=CHUNK.unpack_from(body)
    result.update(chunk_kind=chr(kind),chunk_codec=codec,canonical_length=canonical_len,
                  stored_length=stored_len,locator_count=nloc)
    if sig!=b'\xd7TB3' or kind!=ord('K') or codec not in (0,1):
        return dict(result,reason='root_chunk_magic_type_or_codec')
    if CHUNK.size+stored_len+12*nloc!=ln:
        return dict(result,reason='root_chunk_length_mismatch')
    if canonical_len>MAX_CANON:
        return dict(result,checked=False,reason='canonical_payload_exceeds_limit')
    payload=body[CHUNK.size:CHUNK.size+stored_len]
    if codec==0:
        canonical=payload
    else:
        try:
            decompressor=zlib.decompressobj()
            canonical=decompressor.decompress(payload,MAX_CANON+1)
            if len(canonical)>MAX_CANON or decompressor.unconsumed_tail or not decompressor.eof or decompressor.unused_data:
                return dict(result,reason='invalid_or_oversized_compressed_root')
            canonical+=decompressor.flush()
        except zlib.error:
            return dict(result,reason='zlib_root_decompression_failed')
    if len(canonical)!=canonical_len:
        return dict(result,reason='root_canonical_length_mismatch')
    digest=hashlib.sha256(canonical).hexdigest()
    result['actual_sha256']=digest
    result['verified']=digest==active['root_sha256']
    result['reason']='root_sha256_match' if result['verified'] else 'root_sha256_mismatch'
    return result
