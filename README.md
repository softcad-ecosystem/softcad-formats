# SoftCAD Formats — public identification and read-only reference toolkit

[**Română**](README_RO.md) · [Official documentation](https://softcad.ro/documentatie-dezvoltatori) · [File formats](https://softcad.ro/referinta-formate)

This repository is a **public, read-only identification toolkit**, built from the developer resources already distributed by SoftCAD. It does **not** contain the private binary format codecs, the commercial CAD/GIS engines, Shield/TSX, passwords, private datasets, or a production format writer.

## What is included

- The SoftCAD file-family identity registry (`softcad-file-registry-1.30.16.json`): ten native families with clearly scoped recognition evidence, plus external-format references.
- `softcad_format_probe.py` and `softcad-format-core.js`: conservative format/signature identification in Python and JavaScript.
- Independent **limited read-only** probes for the observed TCAD 2.0 / CGB1 subsets and TDB3 0.5.0 RC1 root/history cases.
- TCB/TXB/TVW interoperability gates, reference notes and deterministic positive/negative fixtures.
- Python and Node tests. Fixtures contain **synthetic sample data**, including native-shaped structures; they are not user datasets or universal valid documents.

## Start here

Python 3.10+ and Node.js 20+ are supported targets for the supplied scripts; they do not require a commercial SoftCAD application.

```bash
python softcad_format_probe.py vectors/header_only.tcb
python test_softcad_format_probe.py
python test_synthetic_vectors.py
node test_format_core.cjs
```

To run all included checks, use `python` for each `test_*.py` file and `node` for each `test_*.cjs` file. CI runs the same checks.

## Scope and status

| Family | Public scope | Not included |
| --- | --- | --- |
| TCB / TXB | Signature and conservative envelope detection | Full entity/geometry codecs |
| TVW | Text candidate/signature checks | Normative language grammar and runtime |
| TCAD 2.0 | Observed, bounded read-only subset | General format authoring and full CAD compatibility |
| CGB1 | Observed header/subset checks | Full cadastral record decoder or topology engine |
| TDB3 RC1 | Header, root and limited ancestry checks | Full database validator, query engine or writer |
| Other registered formats | Identity-level recognition where evidenced | Unreleased commercial implementations |

**Recognition is not validation or compatibility certification.** Do not use these tools to modify production CAD, cadastral, PDF or database files. TDB3 RC1 is experimental. Use the detailed scope notes in `README_RO_EN.md`, `RECOGNITION_CONTRACT_RO_EN.md`, and the other reference documents.

## Licensing and origin

The independent public reference tools and included sample/reference material are distributed under **Apache License 2.0**, subject to the original `NOTICE.md` and per-file attribution. This grant does **not** license any unbundled SoftCAD proprietary products, engines or codecs. `SOURCE_PROVENANCE.json` records the exact source archive and SHA-256 of each imported file.

Security issues: see [SECURITY.md](SECURITY.md). Contributions: see [CONTRIBUTING.md](CONTRIBUTING.md).
