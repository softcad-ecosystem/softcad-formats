"""Identity/guardrail parity vectors. Not validity of document contents."""
from pathlib import Path
import json,hashlib
from softcad_tcb_txb_tvw_gate import inspect
from softcad_format_probe import classify
M=json.loads((Path(__file__).parent/'interop_vectors/manifest.json').read_text('utf8'))
for name,case in M['cases'].items():
    p=Path(__file__).parent/'interop_vectors'/name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==case['sha256']
    got=inspect(p)
    assert got and got['status']==case['status'],(name,got)
    assert got['format_authenticity']=='UNVERIFIED' and not got['can_write']
    if name=='dxb_legacy_collision.dxb':
        assert classify(p)['identified'] is None and classify(p)['confidence']=='ambiguous_legacy_dxb'
    if name=='txbi_auxiliary.txbi':
        assert classify(p)['identified'] is None and classify(p)['confidence']=='auxiliary_index'
    if name=='txb_legacy.txb':
        assert classify(p)['identified']=='TXB' and classify(p)['confidence']=='legacy_signature'
print('PASS: 20 synthetic TCB/TXB/TVW guardrail vectors (Python)')
