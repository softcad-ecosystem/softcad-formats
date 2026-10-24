# SOFTCAD Formats — public recognition kit 1.30.12 / Kit de identificare

This ZIP is an open informational resource, **not a binary codec SDK**.
Acest ZIP este pentru identificarea fisierelor, **nu un SDK de scriere/citire a formatelor**.

## Run / Utilizare

```bash
python softcad_format_probe.py desen.tcb sector.txb date.tdb
python softcad_format_probe.py --tdb3-header baza.tdb3
python test_softcad_format_probe.py
```

- Reads headers and optionally ZIP member names; does not upload, decrypt or modify your files.
- `confidence` measures **family recognition only**. Even signature recognition never proves the file is complete or structurally valid.
- For `.tsx`, only the `TSSX\x00` signature identifies the SoftCAD container. A React/TypeScript file with `.tsx` is never classified as SoftCAD merely because of its extension.
- A `.tdba` file shares the `TDB1` container, so deeper content-specific checks require a licensed codec.
- `.txbi` is an auxiliary index; legacy `DXB1` is recognized as TXB predecessor **read-only**, never authored as Autodesk `.dxb`.
- TDB3 RC1 header CRC checks do **not** validate Merkle data, records, transactions, or compatibility with future versions.
- Existing proprietary algorithms, Shield internals, keys and private executables are not distributed.

## Version / source

Registry extracted from 4.80.1 identity audit dated 2026-10-17 and TDB3 RC1 implementation metadata.
TCAD/TCB/CGB/TXB reference codecs remain held for rights, conformance and platform validation.
TSS 2.5 source runtime and TDB3 release remain HOLD. TVW graphical API `libtitangfx/path2` is owner-approved under LGPL-3.0-or-later; its full canonical archive is hosted separately after upload verification.

The independent format inspector is provided under Apache-2.0 (LICENSE/NOTICE included). This does not license other SoftCAD components. The TDB3 RC1 material is a technical draft; never rely on it to write production data.

## New in 1.30.11 / Nou in 1.30.11

- `RECOGNITION_CONTRACT_RO_EN.md`: field-level API and confidence contract.
- `softcad-format-core.js`: self-contained browser/Node 20+ signature matcher and historical TDB3 RC1 header CRC.
- `vectors/`: 22 deterministic **synthetic signature-only samples**, none a real valid file format.
- `test_synthetic_vectors.py`, `test_format_core.cjs`: Python/JavaScript parity checks.
- `generate_synthetic_vectors.py`: deterministic generator for the fixtures.
- `--json-output <path>`, `--strict` on the Python command-line inspector.
- ZIP-format candidate checks only inspect the central-directory `FORMAT` name, never inflate entries.

```bash
python generate_synthetic_vectors.py
python test_softcad_format_probe.py
python test_synthetic_vectors.py
node test_format_core.cjs
python softcad_format_probe.py --strict --tdb3-header --json-output report.json vectors/valid_crc_only.tdb3
```

**Important:** The synthetic `.tdb3` fixture only passes a header/superblock CRC sanity check. It is not a usable database. The `softcad_format_probe.py` does not validate real document structure. Reference docs and example code are bilingual; test case identifiers remain stable in English.

## New in 1.30.12 / Nou in 1.30.12

- Seven actual historical **TDB3 0.5.0 RC1** databases with generic synthetic values and positive/negative root SHA-256 cases.
- Independent read-only verification of active root, zlib/raw, canonical payload SHA-256, 8 MiB cap. No engine, no writer, no Merkle tree parser.
- Python: `--tdb3-root --strict`. Offline browser SHA-256 works without WebCrypto.
- Run `python test_real_tdb3.py` and `node test_real_tdb3.cjs`.

ROOT PASS is NOT certification of the entire database.

## New in 1.30.13 / Nou in 1.30.13

- Independent read-only `tdb3_commit_chain.py` and `softcad-tdb3-history.js`: verify active K commit ancestry, SHA-256 parent pointers and strictly descending sequences. Bounded to 64 records, 8 MiB per chunk and 32 MiB cumulative reads. **Not a full database/Merkle verification.**
- Five new authentic RC1 file structures containing only synthetic generic test data, including a corrupted parent which still has a valid active-root digest.
- `--tdb3-history --strict` CLI mode. Reproducible Python and Node parity (`test_tdb3_history.py`, `test_tdb3_history.cjs`).
- Bilingual public reference pages and local browser inspector reporting ROOT and HISTORY independently.

## New in 1.30.15 / Nou in 1.30.15

- CGB1 real native CGXML -> CGB -> CGXML roundtrip, using fully synthetic records (two lands, one sample person, four vertices). No private engine or real cadastral data distributed.
- Public read-only `softcad_cgb1_probe.py` + `softcad-cgb1.js`: observed 140-byte header, section counts/offsets, bounded section spans (8 MiB maximum), no record-body decoder or checksum.
- `--cgb1 --strict` command-line mode and `cgb_vectors/`: 15 positive/negative cases with identical Python/Node results.
- Bilingual reference pages, in-browser probe and JSON reporting.
- For Parcel/Building rows, the verifier returns an explicit unsupported-scope result, not a claim that the file is invalid.

```bash
python softcad_format_probe.py --cgb1 --strict cgb_vectors/native_cgb1_two_lands_one_person_four_points.cgb
python test_cgb1.py
node test_cgb1.cjs
```

**Note:** TCAD 2.0 and CGB1 are limited observed subsets. TCB and TXB full codecs and the TVW declarative parser are still outside the verified public package.
