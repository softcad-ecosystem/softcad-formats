# SoftCAD TCAD 2.0 — public OBSERVED-SUBSET reference / referință observată

Updated 2026-10-23. Do not interpret this as a complete normative spec.

## RO — ce este verificat

Motorul nativ inclus în distribuția sursă FileCommander 4.4.3 a generat din două parcele WKT **fictive** un fișier text UTF-8 `TCAD 2.0`. Fișierul a fost redeschis cu același motor, iar numărul de parcele și CRS-ul au fost reconfirmate. Codul binar nativ NU este inclus în această distribuție.

Proba a confirmat numai antetul, metadatele (`meta`: `crs`, `profile`) și parcela simplă (`parcel`, `cadgen`, `area`, `owner`, `intravilan`, `ring`). Ringul observat este exterior, închis, cu 4 zecimale. `area` este observată numeric, verificată orientativ față de aria geometrică.

Detectorul de fișiere recunoaște atât familia istorică `TCAD 1.x`, cât și `TCAD 2.0`. **Parserul de subset acceptă doar TCAD 2.0.** Pentru alte tipuri de entități și compatibilitate între ediții sunt necesare codecurile aprobate și fixture-uri versionate. Rezultatul `verified_subset` NU semnifică validitate completă a fișierului.

## EN — verified scope

The native engine shipped in the FileCommander 4.4.3 source distribution wrote a synthetic two-parcel, UTF-8 `TCAD 2.0` file and reopened it successfully. Its proprietary binary is NOT included in this reference kit. Observed lines include `meta` / `crs` / `profile`, and `parcel` / `cadgen` / `area` / `owner` / `intravilan` / `ring`. The single exterior ring is closed. No complete normative grammar has been asserted.

`TCAD 1.x` remains recognizable as a historical identity; the independent structural subset parser handles `TCAD 2.0` only. `verified_subset` is not a legal cadastral validation or complete roundtrip guarantee.

## Engine-generated fixture / exemplul real generat

```text
TCAD 2.0

meta
  crs:     "EPSG:3844"
  profile: "cadastral"

parcel P001
  cadgen:     P001
  area:       200.0
  owner:      Fictiv A
  intravilan: 0
  ring:       0.0000,0.0000|20.0000,0.0000|20.0000,10.0000|0.0000,10.0000|0.0000,0.0000

parcel P002
  cadgen:     P002
  area:       35.0
  owner:      Fictiv B
  intravilan: 0
  ring:       35.0000,20.0000|40.0000,20.0000|40.0000,27.0000|35.0000,27.0000|35.0000,20.0000
```

## Test / probe

```sh
python test_tcad20.py
node test_tcad20.cjs
python softcad_format_probe.py --tcad20 --strict vectors/tcad20_two_parcels_real_engine.tcad
```

The independent parser refuses unknown sections rather than ignoring them; its checks are bounded to 8 MiB, 2,000 parcels and 16,000 ring vertices per parcel. The browser and Python reports provide aggregate counts and CRS but not owner names or parcel identifiers. No upload takes place.

## Not established / nespecificat

Buildings, roads, special cadastral boundaries, interior rings, optional metadata, escaping rules, historic formats, cross-version migration, codecuri TCB/CGB/TXB, all `.tvw` declarative grammar, complete GIS accuracy / legal acceptance.
