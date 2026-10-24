#!/usr/bin/env python3
"""Cross-check seven real RC1 synthetic databases with the independent public root inspector."""
from pathlib import Path
import json
import subprocess
import sys
from tdb3_root_probe import inspect

HERE=Path(__file__).parent
cases=json.loads((HERE/'vectors/real_rc1_manifest.json').read_text('utf8'))['cases']
assert len(cases)==7
for name,expect in cases.items():
    path=HERE/'vectors'/name
    got=inspect(path)
    assert got['verified'] is expect['root_sha256_valid'],(name,got)
    assert got['reason']==expect['reason'],(name,got)
    if expect['active_sequence'] is not None:assert got['active_sequence']==expect['active_sequence'],(name,got)
    result=subprocess.run([sys.executable,str(HERE/'softcad_format_probe.py'),'--strict','--tdb3-root',str(path)],capture_output=True,text=True)
    assert result.returncode==(0 if got['verified'] else 2),(name,result.returncode,result.stdout,result.stderr)
    report=json.loads(result.stdout)
    assert report[0]['tdb3_root']['verified']==got['verified'],name
    assert report[0]['tdb3_root']['reason']==got['reason'],name
    if name=='tdb3_real_uncommitted_tail.tdb3':assert got['uncommitted_tail_bytes']>0
    if name=='tdb3_real_recover_older_slot.tdb3':assert got['active_sequence']=='1'
    if name=='tdb3_real_zlib_root.tdb3':assert got['chunk_codec']==1
print('PASS: 7 real TDB3 0.5.0 RC1 fixtures + CLI strict + SHA root integrity')
