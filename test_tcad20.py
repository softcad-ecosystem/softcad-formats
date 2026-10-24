from pathlib import Path
import tempfile
from softcad_tcad20_probe import parse_bytes,inspect
P=Path(__file__).parent/'vectors'/'tcad20_two_parcels_real_engine.tcad'
data=P.read_bytes()
correct=inspect(P)
assert correct['verified_subset'] and correct['parcel_count']==2 and correct['crs']=='EPSG:3844' and correct['profile']=='cadastral',correct
assert correct['sum_reported_area']==235 and correct['sum_geometrical_area']==235,correct
cases={
 'valid':data,
 'crlf':data.replace(b'\n',b'\r\n'),
 'old_version':data.replace(b'TCAD 2.0',b'TCAD 1.2',1),
 'wrong_crs_label':data.replace(b'  crs:',b'  bogus:',1),
 'duplicate_parcel_id':data.replace(b'parcel P002',b'parcel P001',1),
 'missing_ring':data.replace(b'  ring:',b'  unknown:',1),
 'bad_ring':data.replace(b'40.0000,20.0000',b'40.0000,BAD',1),
 'unclosed_ring':data.replace(b'35.0000,20.0000\n\n',b'30.0000,20.0000\n\n',1),
 'bad_area':data.replace(b'area:       200.0',b'area:       -1.0',1),
 'unknown_section':data+b'building XX\n',
 'invalid_utf8':data+b'\xff',
 'huge':data+(b' '*((8*1024*1024)-len(data)+1)),
}
expected={'valid':True,'crlf':True}
for name,blob in cases.items():
 result=parse_bytes(blob)
 assert result['verified_subset'] is expected.get(name,False),(name,result)
 print('PASS',name,result.get('reason','verified_subset'))
print('TCAD 2.0 observed-subset probes:',len(cases),'PASS')
