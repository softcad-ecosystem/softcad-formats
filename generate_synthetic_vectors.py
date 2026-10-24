#!/usr/bin/env python3
"""Create tiny, deterministic, deliberately INVALID/incomplete format-signature fixtures.

A fixture that matches a magic signature is NOT a valid document. These fixtures
must never be used as production format templates or writer implementations.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import struct
import zlib
import zipfile

HERE=Path(__file__).resolve().parent
OUT=HERE/'vectors'
OUT.mkdir(exist_ok=True)

cases={
 'header_only.tcb':(b'TCB\x01'+b'\x00'*30,'TCB','signature'),
 'header_only.cgb':(b'CGB1'+b'\x00'*30,'CGB','signature'),
 'header_only.txb':(b'TXB1'+b'\x00'*30,'TXB','signature'),
 'old_dxb1.txb':(b'DXB1'+b'\x00'*30,'TXB','legacy_signature'),
 'header_only.tdb':(b'TDB1'+b'\x00'*30,'TDB','signature'),
 'shared_tdb1.tdba':(b'TDB1'+b'\x00'*30,'TDBA','container_candidate'),
 'header_only.tcad':(b'TCAD 1.2\n'+b'\x00'*20,'TCAD','text_prefix'),
 'text_directive.tdoc':(b'\xef\xbb\xbf  @tdoc\n'+b'\x00'*12,'TDOC','text_prefix'),
 'header_only.tdocb':(b'TDOCB\x01'+b'\x00'*30,'TDOCB','signature'),
 'shield_header.tsx':(b'TSSX\x00'+b'\x00'*30,'TSX','signature'),
 'react_source.tsx':(b'import React from "react";\n','UNKNOWN','unknown'),
 'header_only.pdf':(b'%PDF-1.7\n'+b'\x00'*20,'PDF','signature'),
 'header_only.dwg':(b'AC1027'+b'\x00'*20,'DWG','signature'),
 'extension_only.tvw':(b'not a real TVW script\n','TVW','unverified_extension'),
 'extension_conflict.tcb':(b'TXB1'+b'\x00'*20,'TXB','signature'),
 'not_recognized.bin':(b'SOFTCAD test fixture, no magic','UNKNOWN','unknown'),
 'header_only.gpkg':(b'SQLite format 3\x00'+b'\x00'*52+b'GPKG'+b'\x00'*28,'GPKG','signature'),
}

def tdb3(version:int=1, corrupt=False):
 data=bytearray(12288)
 h=struct.pack('>8sHHd16s',b'TDB3\x00\r\n\x1a',version,0,0.0,b'\x01'*16)
 data[:40]=h+struct.pack('>I',zlib.crc32(h)&0xffffffff)
 sb=struct.pack('>8sQQI32sQ',b'TDB3SUPR',3,0,0,b'\x00'*32,12288)
 data[4096:4096+72]=sb+struct.pack('>I',zlib.crc32(sb)&0xffffffff)
 if corrupt:data[39]^=1
 return bytes(data)

cases['valid_crc_only.tdb3']=(tdb3(), 'TDB3','signature')
cases['bad_header_crc.tdb3']=(tdb3(corrupt=True),'TDB3','signature')
cases['future_version_2.tdb3']=(tdb3(version=2),'TDB3','signature')

with io.BytesIO() as out:
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_STORED) as zipf:
  zipf.writestr('FORMAT','TDOCB synthetic candidate, not a real valid document')
 cases['zip_format_member.tdocb']=(out.getvalue(),'TDOCB','container_candidate')
with io.BytesIO() as out:
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_STORED) as zipf:
  zipf.writestr('README.txt','ZIP without FORMAT must not be verified')
 cases['zip_without_format.tdocb']=(out.getvalue(),'TDOCB','unverified_extension')

manifest={'schema':'SoftCAD synthetic signature fixtures v1.30.11',
 'warning':'SIGNATURE EXAMPLES ONLY. These bytes are not valid CAD/TDB/Shield/TVW documents and cannot be used as format writers or normative vectors.',
 'source':'SoftCAD 4.80.1 file identity registry + public TDB3 RC1 header constants',
 'cases':{}}
for name,(data,identity,quality) in sorted(cases.items()):
 (OUT/name).write_bytes(data)
 manifest['cases'][name]={'sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data),'identified':identity,'confidence':quality,'valid_document':False}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(f"Generated {len(cases)} synthetic identity fixtures")
