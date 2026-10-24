from pathlib import Path
import hashlib,json,unittest
from softcad_cgb1_probe import inspect_header,inspect
V=Path(__file__).parent/'cgb_vectors'
class TestCGB1(unittest.TestCase):
 def test_manifest_cases(self):
  m=json.loads((V/'cgb_cases.json').read_text())
  for name,ex in m['cases'].items():
   b=(V/name).read_bytes()
   self.assertEqual(hashlib.sha256(b).hexdigest(),ex['sha256'],name)
   actual=inspect_header(b)
   for k in ('checked','verified_subset','reason'):
    self.assertEqual(actual[k],ex[k],(name,k))
    self.assertEqual(inspect(V/name)[k],ex[k],(name,k,'disk'))
 def test_fixture_semantics_aggregate(self):
  b=(V/'native_cgb1_two_lands_one_person_four_points.cgb').read_bytes()
  r=inspect_header(b)
  self.assertEqual(r['counts'],dict(lands=2,parcels=0,buildings=0,persons=1,points=4))
  self.assertEqual(r['section_offsets'],dict(lands=140,parcels=228,buildings=228,persons=228,points=268,strings=364))
 def test_binary_payload_mutation_not_detected(self):
  self.assertTrue(inspect(V/'tampered_record_content.cgb')['verified_subset'], 'Scope MUST remain header-only')
if __name__=='__main__':unittest.main()
