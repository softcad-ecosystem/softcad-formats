"""Read-only CGB1 observed-subset header verifier, independent of the proprietary codec.

Layout observed from native FileCommander 4.4.3 CGB <-> CGXML examples on Linux,
2026-10-23. Recognition and bounded section checks only. NOT a full decoder.
"""
from __future__ import annotations
from pathlib import Path
import math
import struct

MAX_BYTES = 8 * 1024 * 1024
HEADER_BYTES = 140
# Only three record layouts are measured against native-generated fixtures.
RECORD_BYTES = {"lands": 44, "persons": 40, "points": 24}
COUNTS = ("lands", "parcels", "buildings", "persons", "points")
SECTIONS = ("lands", "parcels", "buildings", "persons", "points", "strings")


def inspect_header(data: bytes, file_size: int | None = None) -> dict:
    """Inspect first 140 bytes. file_size is the full size if data is a prefix."""
    size = len(data) if file_size is None else file_size
    result = {
        "layout": "CGB1 observed native subset (2026-10-23)",
        "checked": False,
        "verified_subset": False,
        "file_size": size,
        "scope": "Header counts and bounded section positions only; parcels/buildings and inner records not decoded.",
    }
    def fail(reason: str) -> dict:
        result["reason"] = reason
        return result
    if size > MAX_BYTES:
        return fail("file_limit_8_mib")
    if size < HEADER_BYTES or len(data) < HEADER_BYTES:
        return fail("truncated_cgb1_header_140")
    if data[:4] != b"CGB1":
        return fail("not_cgb1")
    result["checked"] = True
    version, = struct.unpack_from("<I", data, 4)
    result["version"] = version
    if version != 1:
        return fail("unsupported_cgb_version")
    counts = dict(zip(COUNTS, struct.unpack_from("<5I", data, 8)))
    offsets = dict(zip(SECTIONS, struct.unpack_from("<6Q", data, 28)))
    result["counts"] = counts
    result["section_offsets"] = offsets
    values = list(offsets.values())
    if values[0] != HEADER_BYTES:
        return fail("unexpected_first_section_offset")
    if any(v > size or v < HEADER_BYTES for v in values):
        return fail("section_offset_outside_file")
    if any(x > y for x, y in zip(values, values[1:])):
        return fail("section_offsets_not_monotonic")
    if any(count > 100_000 for count in counts.values()):
        return fail("section_count_safety_limit")
    # The native writer's layout for CGB1 without Parcel/Building rows has
    # fixed Land/Person/Points spans. Do not extrapolate to other variants.
    if counts["parcels"] or counts["buildings"]:
        return fail("parcel_building_record_layout_not_yet_covered")
    if (values[1] - values[0]) != counts["lands"] * RECORD_BYTES["lands"]:
        return fail("land_section_span_count_mismatch")
    if values[1] != values[2] or values[2] != values[3]:
        return fail("unexpected_nonempty_parcel_or_building_section")
    if (values[4] - values[3]) != counts["persons"] * RECORD_BYTES["persons"]:
        return fail("person_section_span_count_mismatch")
    if (values[5] - values[4]) != counts["points"] * RECORD_BYTES["points"]:
        return fail("point_section_span_count_mismatch")
    # Header's numeric aggregate fields are observed, not normative; only
    # ensure basic sanity. Omit geographic coordinates from exported reports.
    total_area = struct.unpack_from("<d", data, 84)[0]
    if not math.isfinite(total_area) or total_area < 0:
        return fail("nonfinite_or_negative_aggregate_area")
    result["verified_subset"] = True
    result["reason"] = "observed_section_layout_consistent"
    result["warning"] = "CGB1 subset structure, NOT native openability, semantic validity, checksum validation or complete binary conformance."
    return result


def inspect(path: Path) -> dict:
    path = Path(path)
    with path.open("rb") as reader:
        prefix = reader.read(HEADER_BYTES)
    return inspect_header(prefix, path.stat().st_size)
