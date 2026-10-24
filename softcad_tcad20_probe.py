#!/usr/bin/env python3
"""Read-only SoftCAD TCAD 2.0 *observed single-ring parcel subset* probe.

This is NOT the production engine or a complete TCAD grammar. It examines only
records seen in canonical synthetic output from the historic ts_tcad engine.
No native binaries, write path, encrypted formats or personal data exported.
"""
from __future__ import annotations

import math
from pathlib import Path
import re

MAX_BYTES = 8 * 1024 * 1024
MAX_PARCELS = 2000
MAX_POINTS = 16000
HEADER = 'TCAD 2.0'
PARCEL_FIELDS = {'cadgen', 'area', 'owner', 'intravilan', 'ring'}
META_FIELDS = {'crs', 'profile'}
PAIR = re.compile(r'\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*,\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*\Z')

class TCADSubsetError(ValueError):
    """Observed TCAD 2.0 subset not satisfied (not a complete-format diagnosis)."""


def parse_bytes(data: bytes) -> dict:
    """Return privacy-minimal metrics; no owners or parcel IDs in result."""
    result = {
        'layout': 'TCAD 2.0 observed parcel subset',
        'checked': True, 'verified_subset': False,
        'scope': 'UTF-8 meta + single exterior ring parcels only; not a normative grammar or full native validation',
        'parcel_count': 0,
    }
    try:
        if len(data) > MAX_BYTES:
            raise TCADSubsetError('file_limit_8_mib')
        try:
            lines = data.decode('utf-8', errors='strict').splitlines()
        except UnicodeDecodeError as exc:
            raise TCADSubsetError('not_utf8') from exc
        if not lines or lines[0] != HEADER:
            raise TCADSubsetError('not_tcad_2_0')
        section = None
        seen_parcels: set[str] = set()
        metadata: dict[str, str] = {}
        fields: dict[str, str] = {}
        parcels = 0
        points_total = 0
        sum_reported = 0.0
        sum_geometric = 0.0
        area_warnings = 0
        def finish_parcel() -> None:
            nonlocal parcels, points_total, sum_reported, sum_geometric, area_warnings
            if not fields:
                raise TCADSubsetError('empty_parcel')
            if set(fields) != PARCEL_FIELDS:
                raise TCADSubsetError('parcel_fields_not_observed_subset')
            try:
                area = float(fields['area'])
            except ValueError as exc:
                raise TCADSubsetError('invalid_area') from exc
            if not math.isfinite(area) or area < 0:
                raise TCADSubsetError('invalid_area')
            if fields['intravilan'] not in ('0', '1'):
                raise TCADSubsetError('unrecognized_intravilan')
            points = []
            tokens = fields['ring'].split('|')
            if not 4 <= len(tokens) <= MAX_POINTS:
                raise TCADSubsetError('ring_vertex_limit_or_too_short')
            for token in tokens:
                m = PAIR.fullmatch(token)
                if not m:
                    raise TCADSubsetError('invalid_ring_point')
                xy = tuple(map(float, m.groups()))
                if not all(math.isfinite(v) and abs(v) <= 1e12 for v in xy):
                    raise TCADSubsetError('coordinate_not_finite_or_out_of_bounds')
                points.append(xy)
            if points[0] != points[-1]:
                raise TCADSubsetError('ring_not_closed')
            geometrical = abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points, points[1:]))) / 2
            if not math.isfinite(geometrical) or geometrical <= 0:
                raise TCADSubsetError('ring_zero_or_invalid_area')
            # A serializer was observed reporting 1 decimal of area; tolerance
            # is only a diagnostic hint, not a full cadastral area test.
            if abs(geometrical-area) > max(0.11, geometrical*1e-6):
                area_warnings += 1
            parcels += 1
            points_total += len(points)
            if parcels > MAX_PARCELS:
                raise TCADSubsetError('parcel_limit_2000')
            sum_reported += area
            sum_geometric += geometrical
        for line in lines[1:]:
            if not line.strip():
                continue
            if line == 'meta':
                if section is not None:
                    raise TCADSubsetError('duplicate_or_late_meta')
                section = 'meta'
                continue
            if line.startswith('parcel '):
                if section == 'parcel':
                    finish_parcel()
                elif section != 'meta':
                    raise TCADSubsetError('missing_meta_section')
                pid = line[7:]
                if not (1 <= len(pid) <= 128) or pid in seen_parcels or any(ch.isspace() for ch in pid):
                    raise TCADSubsetError('invalid_or_duplicate_parcel_id')
                seen_parcels.add(pid)
                section = 'parcel'
                fields = {}
                continue
            m = re.fullmatch(r'  ([a-z_]+):\s*(.*)', line)
            if not m or section not in ('meta', 'parcel'):
                raise TCADSubsetError('line_outside_observed_subset')
            name, value = m.groups()
            if section == 'meta':
                if name not in META_FIELDS or name in metadata:
                    raise TCADSubsetError('meta_fields_not_observed_subset')
                q = re.fullmatch(r'"([^"\r\n]*)"', value)
                if not q:
                    raise TCADSubsetError('meta_value_not_observed_quoted_form')
                metadata[name] = q.group(1)
            else:
                if name not in PARCEL_FIELDS or name in fields:
                    raise TCADSubsetError('parcel_fields_not_observed_subset')
                fields[name] = value
        if section == 'parcel':
            finish_parcel()
        if set(metadata) != META_FIELDS:
            raise TCADSubsetError('meta_fields_not_observed_subset')
        result.update({
            'verified_subset': True,
            'crs': metadata['crs'], 'profile': metadata['profile'],
            'parcel_count': parcels, 'ring_point_count': points_total,
            'sum_reported_area': round(sum_reported, 9),
            'sum_geometrical_area': round(sum_geometric, 9),
            'area_discrepancies': area_warnings,
            'warning': 'Only the observed TCAD 2.0 subset is recognized; native interoperability and cadastral validity require separate checks.',
        })
    except TCADSubsetError as exc:
        result['reason'] = str(exc)
    return result


def inspect(path: Path) -> dict:
    if path.stat().st_size > MAX_BYTES:
        return parse_bytes(b' ' * (MAX_BYTES + 1))
    return parse_bytes(path.read_bytes())

if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', type=Path, nargs='+')
    parser.add_argument('--strict', action='store_true')
    ns = parser.parse_args()
    rows = []
    for p in ns.files:
        if not p.is_file(): parser.error('not a regular file: '+str(p))
        rows.append({'file':p.name,**inspect(p)})
    print(json.dumps(rows,indent=2,ensure_ascii=False))
    if ns.strict and any(not r['verified_subset'] for r in rows):
        raise SystemExit(2)
