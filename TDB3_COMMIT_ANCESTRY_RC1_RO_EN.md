# TDB3 0.5.0 RC1 - Commit ancestry / Istoricul commiturilor

This is **read-only experimental verification**, not a format specification for writing TDB3 files.
Aceasta este **verificare experimentala doar pentru citire**, nu un standard pentru scrierea TDB3.

## Evidence / Dovezi

From the historical 0.5.0 RC1 code: the commit K chunk contains a canonical dictionary
with `parinte`, `catalog`, `timp`, `autor`, `mesaj`, `secventa`.
Ref SHA-256 bytes are part of the canonical value, while `offset:uint64 BE, length:uint32 BE`
are stored as out-of-band locators in the same chunk. The superblock points at the current K chunk.

The independent tools verify header/root CRC/SHA, then follow only `parinte` refs,
verifying per-record SHA-256, chunk type, bounds and strictly descending sequences.
They stop after 64 K records or 32 MiB of total chunk reads. Any incomplete walk is NOT PASS.

## Quick start

```sh
python softcad_format_probe.py --tdb3-history --strict vectors/tdb3_history_valid_4_commits.tdb3
python test_tdb3_history.py
node test_tdb3_history.cjs
```

A corrupted parent and a parent locator with impossible length both keep a valid current
root SHA-256. An ancestry check catches those errors. All fixtures contain fictional test data.

## Out of scope / In afara verificarii

- Catalog tree, nested node contents, row values, journals, full Merkle DAG.
- Concurrent transaction guarantees, repair or conversion.
- Production write compatibility; formats TCAD/TCB/CGB/TXB remain signature-only until
  canonical codecs are available for full conformance testing.
- Declaration-language `.tvw` parser grammar; this is different from the already-approved
  `libtitangfx/path2` graphics API licensed LGPL-3.0-or-later.

The independent inspector code in this kit is Apache-2.0. The held TDB3 runtime/source
and all proprietary engines are excluded from the published kit.
