#!/usr/bin/env python3
"""Identity-only fixtures; never represent complete, valid CAD/DB documents."""
import tempfile
from pathlib import Path
from softcad_format_probe import classify,inspect_tdb3_header

def check(name,content,want,confidence=None):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/name;p.write_bytes(content)
        result=classify(p)
        assert result['identified']==want,(name,result)
        if confidence:assert result['confidence']==confidence,(name,result)

check('d.tcb',b'TCB\x01'+b'0'*24,'TCB','signature')
check('d.cgb',b'CGB1'+b'0'*24,'CGB')
check('d.txb',b'TXB1'+b'0'*24,'TXB')
check('old.txb',b'DXB1'+b'0'*24,'TXB','legacy_signature')
check('d.tdb',b'TDB1'+b'0'*24,'TDB')
check('d.tdba',b'TDB1'+b'0'*24,'TDBA','container_candidate')
check('d.tcad',b'TCAD 1.2\n', 'TCAD')
check('observed.tcad',b'TCAD 2.0\nmeta\n', 'TCAD','text_prefix')
check('d.tdoc',b'@tdoc\n', 'TDOC')
check('d.tdocb',b'TDOCB\x01\x00', 'TDOCB')
check('shield.tsx',b'TSSX\x00\x12', 'TSX')
check('react.tsx',b'const App = () => <div/>;',None,'unknown')
check('d.tvw',b'not validated syntax','TVW','unverified_extension')
check('d.pdf',b'%PDF-1.7\n','PDF')
check('d.tdb3',b'TDB3\x00\r\n\x1a', 'TDB3')
check('d.gpkg',b'SQLite format 3\x00'+b'\x00'*52+b'GPKG'+b'\x00'*64, 'GPKG')
check('conflict.tcb',b'TXB1\x00','TXB')
print('PASS: 17 public identity-only checks')

# Two additional checks for the read-only RC1 CRC gate: never create live records.
import struct
import zlib
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'synthetic_rc1.tdb3'
    data=bytearray(12288)
    header=struct.pack('>8sHHd16s',b'TDB3\x00\r\n\x1a',1,0,0.0,b'\x01'*16)
    data[:40]=header+struct.pack('>I',zlib.crc32(header)&0xffffffff)
    block=struct.pack('>8sQQI32sQ',b'TDB3SUPR',7,0,0,b'\x00'*32,12288)
    data[4096:4096+72]=block+struct.pack('>I',zlib.crc32(block)&0xffffffff)
    p.write_bytes(data)
    valid=inspect_tdb3_header(p)
    assert valid['verified'] and valid['valid_header_crc'] and valid['superblocks'][0]['valid_crc'],valid
    data[39]^=1
    p.write_bytes(data)
    invalid=inspect_tdb3_header(p)
    assert invalid['verified'] is False and invalid['valid_header_crc'] is False,invalid
print('PASS: 2 extra synthetic TDB3 RC1 header CRC checks')
