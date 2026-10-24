#!/usr/bin/env python3
"""Verify 5 new + 7 retained RC1 fixtures and CLI exit codes. No engine import."""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from tdb3_commit_chain import inspect
from tdb3_root_probe import inspect as root_inspect

P=Path(__file__).resolve().parent
cases=json.loads((P/'vectors/tdb3_history_manifest.json').read_text('utf8'))['cases']
assert len(cases)==5
for name,meta in cases.items():
    p=P/'vectors'/name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256'],name
    r=inspect(p)
    assert r['reason']==meta['reason'],(name,r)
    assert r['verified']==meta['verified'],name
    assert r['commit_count']==meta['commit_count'],name
    assert root_inspect(p)['verified']==meta['root_verified'],name
    cli=subprocess.run([sys.executable,str(P/'softcad_format_probe.py'),'--tdb3-history','--strict',str(p)],capture_output=True,text=True)
    assert cli.returncode==(0 if meta['verified'] else 2),(name,cli.stderr,cli.stdout)
    report=json.loads(cli.stdout)[0]['tdb3_history']
    assert report['reason']==r['reason'],name
    assert report['commit_count']==r['commit_count'],name
    if name=='tdb3_history_over_64_commits.tdb3':
        assert not r['checked'] and not r['complete'],name

old=json.loads((P/'vectors/real_rc1_manifest.json').read_text('utf8'))['cases']
assert len(old)==7
for name,meta in old.items():
    report=inspect(P/'vectors'/name)
    if meta['root_sha256_valid']:
        assert report['verified'] is True and report['complete'] is True,(name,report)
    else:
        assert report['reason']=='history_root_not_verified',name
print('PASS: 5 new real RC1 synthetic fixtures + 7 retained fixtures; CLI strict, chain SHA/locators')
