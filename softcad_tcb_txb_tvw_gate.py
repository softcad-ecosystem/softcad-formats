#!/usr/bin/env python3
"""TCB/TXB/TVW envelope and source-readiness gate, informational ONLY.
No decoding/encoding. No user file contents returned. All checks are bounded.
"""
from __future__ import annotations
from pathlib import Path

MAX_SOURCE=65536

def inspect(path: Path)->dict | None:
    suffix=path.suffix.lower()
    if suffix not in ('.tcb','.txb','.dxb','.txbi','.tvw'):
        return None
    size=path.stat().st_size
    with path.open('rb') as h: data=h.read(min(size, MAX_SOURCE+1))
    return inspect_bytes(path.name,data,size)

def inspect_bytes(name:str, data:bytes, size:int|None=None)->dict|None:
    suffix=Path(name).suffix.lower()
    if suffix not in ('.tcb','.txb','.dxb','.txbi','.tvw'):
        return None
    n=len(data) if size is None else size
    result={'checked':True,'format_authenticity':'UNVERIFIED','can_write':False,
            'codec_included':False,'normative_spec_covered':False,
            'validation_scope':'IDENTITY_AND_TEXT_PLAUSIBILITY_ONLY',
            'status':'unknown','detail':'Not a full file-format or language validator'}
    if suffix=='.txbi':
        result.update(status='auxiliary_index',detail='TXBI is an optional TXB index, not a standalone drawing');return result
    if suffix=='.dxb':
        if data.startswith(b'DXB1'):status='ambiguous_dxb_collision';detail='DXB1 can denote historical SoftCAD data; .dxb belongs to Autodesk and is not automatically TXB'
        elif data.startswith(b'TXB1'):status='extension_collision';detail='TXB1 under Autodesk .dxb extension; do not write or convert automatically'
        else:status='external_dxb_outside_scope';detail='Autodesk DXB: not parsed or recognized by this SoftCAD gate'
        result.update(status=status,detail=detail);return result
    if suffix=='.tcb':
        if data.startswith(b'TCB\x01'):
            result.update(status='signature_only',detail='TCB\\x01 signature matches; full binary layout unavailable')
        elif data.startswith((b'TXB1',b'DXB1')):
            result.update(status='signature_conflict',detail='TXB/DXB signature conflicts with .tcb extension')
        else:
            result.update(status='signature_missing',detail='No full TCB\\x01 prefix; cannot establish TCB identity')
        return result
    if suffix=='.txb':
        if data.startswith(b'TXB1'):
            result.update(status='signature_only',detail='TXB1 prefix found, payload not decoded')
        elif data.startswith(b'DXB1'):
            result.update(status='legacy_read_only',detail='Historical DXB1 in .txb: reading may be supported; writing DXB1 or Autodesk .dxb is not supported')
        elif data.startswith(b'TCB\x01'):
            result.update(status='signature_conflict',detail='TCB signature conflicts with .txb extension')
        else:
            result.update(status='signature_missing',detail='No TXB1/DXB1 prefix; cannot establish TXB identity')
        return result
    # TVW: only check UTF-8 and prohibited binary controls; do NOT pretend to parse the grammar.
    if n==0:
        result.update(status='empty_source',detail='No content to examine');return result
    if n>MAX_SOURCE:
        result.update(checked=False,status='source_size_limit',detail='TVW text-plausibility probe limited to 64 KiB');return result
    try:
        source=data.decode('utf-8-sig','strict')
    except UnicodeDecodeError:
        result.update(status='not_utf8_text',detail='Does not decode as UTF-8 source text');return result
    if any(ord(c)<32 and c not in '\t\r\n' for c in source):
        result.update(status='binary_controls',detail='Contains binary control characters; not plausible UTF-8 source');return result
    result.update(status='utf8_text_candidate',detail='Text is valid UTF-8; this does not parse or validate TVW syntax',text_lines=len(source.splitlines()))
    return result
