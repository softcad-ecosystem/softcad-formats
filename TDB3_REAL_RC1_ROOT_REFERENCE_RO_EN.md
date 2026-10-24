# TDB3 RC1 authentic root integrity reference / Referinta pentru inscrierea-radacina

Status: historical 0.5.0 RC1 ONLY. The base engine is NOT distributed.

## Python CLI

```bash
python softcad_format_probe.py --tdb3-root --strict vectors/tdb3_real_valid.tdb3
python test_real_tdb3.py
node test_real_tdb3.cjs
```

## Verified from tdb3/stocare.py (archival implementation)

- Header: 40 bytes, `>8sHHd16sI`, CRC32 of the first 36; reserved header area 4096.
- Slot A=4096, B=8192; superblock `>8sQQI32sQI` (72 bytes), CRC32 first 68.
- Active slot = greatest valid sequence. A corrupt new slot may yield valid older commit.
- Root chunk begins at active slot's `root_offset` with total length `root_length`; must be >=12288 and wholly inside `committed_end <= physical_file_size`.
- Chunk header: `>4sBBHIII` (20 bytes), magic `d7 54 42 33`, type K, codec 0=raw / 1=zlib.
- Root layout length = 20 + stored_length + locator_count*12.
- SHA-256 comparison uses the canonical UNCOMPRESSED bytes, not compressed bytes.
- Historical root reader checks content hashes for chunks; this public verifier intentionally checks only the active commit root, not the Merkle graph, record contents or journal.
- Memory cap: 8 MiB stored and canonical payload. Unsupported API features are reported as SKIPPED instead of PASS.

## Seven real structural fixtures

The files under `vectors/tdb3_real_*.tdb3` were created using the historical RC1 reference implementation with only generic synthetic values. No proprietary engine source, personal records, secrets, keys, Shield runtime, private CAD codecs or operational database are included.

Fixture verification is public Apache-2.0 independent inspector code and does not imply the TDB3 runtime itself is cleared for publication.
