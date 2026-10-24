# CGB1 — subset observat, citire independenta (RO / EN)

Dovada: FileCommander v4.4.3, biblioteca Linux ts_engines.so; CGXML scris din date integral fictive, convertit in CGB, redeschis si convertit inapoi. Verificarea de mai jos a fost repetata pe 15 vectori independenti Python/JS la 23.10.2026.

## Partea demonstrata in antet

| Offset (octeti) | Tip observat | Descriere |
| --- | --- | --- |
| 0 | ASCII 4 | `CGB1` |
| 4 | uint32 little endian | Versiune `1` in probe |
| 8,12,16,20,24 | 5 x uint32 LE | Numar Land, Parcel, Building, Person, Points |
| 28,36,44,52,60,68 | 6 x uint64 LE | Pozitii sectiuni Land, Parcel, Building, Person, Points si zona de siruri |
| 84 | float64 LE | Suprafata agregata observata, NU valoare cadastrala certificata |
| 0-139 | 140 octeti | Antet observat in probele folosite |

In probele cu Parcel=0, Building=0 s-au observat inregistrari de 44 octeti pentru Land, 40 pentru Person si 24 pentru Points. Aceste dimensiuni NU sunt garantate pentru alte versiuni ori cazuri; campurile interne nu sunt publicate drept contract normativ.

Fixture principal: `cgb_vectors/native_cgb1_two_lands_one_person_four_points.cgb` — doua imobile cu arii 200 si 35, o persoana fictiva, 4 puncte fictive. Inputul CGXML a fost inclus. La redeschiderea CGB, motorul a confirmat 2 imobile, 1 persoana, 4 puncte, cele doua arii si conversia inapoi in CGXML.

## Limite explicite

Verificatorul citeste doar antetul 140B si dimensiunea fizica, accepta maximum 8 MiB si NU decodeaza continutul Land/Person/Points, NU verifica checksum, topologie, drepturi, nume sau compatibilitate generala. Pentru variantele care au Parcel ori Building, intoarce `parcel_building_record_layout_not_yet_covered`, nu spune ca sunt fisiere corupte. O modificare in corp poate sa nu fie detectata: proba `tampered_record_content.cgb` este intentionat un PASS doar structural.

Fara codul motorului, fara Shield, fara chei. Kitul de identificare este Apache-2.0; drepturile asupra formatelor si asupra motorului nu sunt transferate prin kit.

## Rulare / Use

```
python softcad_format_probe.py --cgb1 --strict cgb_vectors/native_cgb1_two_lands_one_person_four_points.cgb
python test_cgb1.py
node test_cgb1.cjs
```

---

## English

**Observed CGB1 subset, not the complete normative format.** The native engine converted a fully synthetic CGXML fixture into CGB, reopened it, and exported it back into CGXML, preserving two lands (areas 200 and 35), one sample person and four synthetic vertices. A 140-byte header is observed in the tested files: 4-byte magic, 32-bit LE version, five 32-bit LE section counts at offset 8 and six 64-bit LE section offsets from byte 28; aggregate area at byte 84. With zero Parcel/Building records, Land/Person/Point spans are respectively 44/40/24 bytes per item in these tests only. The public Python/JS validators inspect the header and bounded offsets; **they do not authenticate or decode the body or guarantee native validity.** Files with populated Parcel/Building sections are explicitly outside the verified subset. Maximum file size: 8 MiB. Synthetic fixture/15 parity vectors/negative tests included. The native engine is not distributed.
