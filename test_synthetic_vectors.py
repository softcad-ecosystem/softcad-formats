#!/usr/bin/env python3
"""Independent checks for public v1.30.11 synthetic family-identification samples."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from softcad_format_probe import classify,inspect_tdb3_header

HERE=Path(__file__).resolve().parent
MAN=json.loads((HERE/'vectors/manifest.json').read_text('utf8'))
assert len(MAN['cases'])>=20
for name,expected in MAN['cases'].items():
 file=HERE/'vectors'/name
 assert file.is_file(),name
 got=classify(file)
 assert (got['identified'] or 'UNKNOWN')==expected['identified'],(name,got)
 assert got['confidence']==expected['confidence'],(name,got)
 if name=='extension_conflict.tcb':assert got['mismatch']
 if name=='react_source.tsx':assert got['identified'] is None
 if name=='zip_format_member.tdocb':assert got['confidence']=='container_candidate'
 if name=='zip_without_format.tdocb':assert got['confidence']=='unverified_extension'
 if name=='valid_crc_only.tdb3':assert inspect_tdb3_header(file)['verified']
 if name=='bad_header_crc.tdb3':assert not inspect_tdb3_header(file)['verified']
 if name=='future_version_2.tdb3':assert not inspect_tdb3_header(file)['verified']
with tempfile.TemporaryDirectory() as tmp:
 output=Path(tmp)/'report.json'
 good=HERE/'vectors/header_only.tcb'
 bad=HERE/'vectors/extension_conflict.tcb'
 tool=HERE/'softcad_format_probe.py'
 a=subprocess.run([sys.executable,str(tool),'--strict','--json-output',str(output),str(good)],capture_output=True,text=True)
 assert a.returncode==0,(a.stdout,a.stderr)
 assert output.is_file() and json.loads(output.read_text('utf8'))[0]['identified']=='TCB'
 b=subprocess.run([sys.executable,str(tool),'--strict',str(bad)],capture_output=True,text=True)
 assert b.returncode==2,(b.returncode,b.stdout,b.stderr)
 c=subprocess.run([sys.executable,str(tool),'--strict','--tdb3-header',str(HERE/'vectors/bad_header_crc.tdb3')],capture_output=True,text=True)
 assert c.returncode==2,(c.returncode,c.stdout,c.stderr)
print('PASS:',len(MAN['cases']),'synthetic identity vectors + 3 CLI strict/export scenarios')
