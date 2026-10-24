# TDB3 0.5.0 RC1 — verified storage layout (historical technical draft)

**Status:** informational versioned reference; the TDB3 runtime remains HOLD. This is not a stable compatibility standard and does not authorize publishing the engine or private datasets.

Verified against `tdb3/stocare.py` in the archival `SoftCAD_TDB3_Format_0_5_0_RC1.zip` reference implementation.

## Fixed header and slots

| Property | 0.5.0 RC1 |
|---|---|
| magic, 8 bytes | `TDB3\x00\r\n\x1a` |
| storage version | `1` |
| reserved header area | 4096 bytes |
| header field layout (big-endian) | `>8sHHd16sI` |
| CRC | CRC32 over 36-byte header body, stored in trailing `I` |
| superblock offsets | 4096 and 8192 |
| superblock structure | `>8sQQI32sQI` |
| superblock magic | `TDB3SUPR` |
| journal/data start | 12288 |
| chunk header layout | `>4sBBHIII` |
| chunk magic | bytes `d7 54 42 33` |
| chunk encodings | `0` raw; `1` zlib |

The two superblocks are alternative commit roots. In the archived reader, only entries with matching magic and CRC are candidates, and the highest valid sequence is selected. Canonical chunk payloads are checked against SHA-256 in the archived reference reader.

## Use of this information

This is enough for a **read-only family/header probe**. It is not enough to implement the data model, transaction log, Merkle verification or concurrent writers. Source-level data parsing and write support remain pending their own distribution approval.

Run `python softcad_format_probe.py --tdb3-header your_database.tdb3` with the reference Python inspector. Do not use release candidate layout rules to rewrite a production database.

## Provenance / privacy

Only format constants and layout fields were transcribed here. The original engineering draft contains development benchmarks and sample names that are intentionally omitted from this public reference. No proprietary core, keys, or operational records are bundled.
