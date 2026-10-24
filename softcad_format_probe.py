#!/usr/bin/env python3
"""SoftCAD public file-family recognizer, no private codecs; Python 3.10+.

Reads bounded file headers, ZIP metadata, optional TDB3 RC1 root and commit ancestry.
Does NOT validate, decode, decrypt, or upload input files.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import re
import zlib
import zipfile
from tdb3_root_probe import inspect as inspect_tdb3_root
from tdb3_commit_chain import inspect as inspect_tdb3_history
from softcad_tcad20_probe import inspect as inspect_tcad20
from softcad_cgb1_probe import inspect as inspect_cgb1
from softcad_tcb_txb_tvw_gate import inspect as inspect_interop_gate

NATIVE_EXT={'.tcad':'TCAD','.tcb':'TCB','.cgb':'CGB','.txb':'TXB','.tdb':'TDB','.tdoc':'TDOC','.tdocb':'TDOCB','.tss':'TSS','.tsx':'TSX','.tvw':'TVW','.tdba':'TDBA','.tdb3':'TDB3','.tcbg':'TCBG','.tvcs':'TVCS','.tvsc':'TVSC','.tvdb':'TVDB'}
EXTERNAL_EXT={'.cgxml':'CGXML','.dwg':'DWG','.dxf':'DXF','.gpkg':'GPKG','.pdf':'PDF'}
MAGIC={b'TCB\x01':'TCB',b'CGB1':'CGB',b'TXB1':'TXB',b'TDB1':'TDB',b'TDOCB\x01':'TDOCB',b'TSSX\x00':'TSX',b'TDB3\x00\r\n\x1a':'TDB3'}


def classify(path: Path)->dict:
    suffix=path.suffix.lower()
    expected=NATIVE_EXT.get(suffix) or EXTERNAL_EXT.get(suffix)
    with path.open('rb') as f: data=f.read(12288)
    found=None; evidence='extension only'; confidence='extension_only'
    for magic, tag in sorted(MAGIC.items(),key=lambda x:len(x[0]),reverse=True):
        if data.startswith(magic):
            found=tag;evidence='public byte signature';confidence='signature';break
    if found is None and data.startswith(b'DXB1'):
        if suffix=='.dxb':
            evidence='ambiguous DXB1 with Autodesk .dxb extension; no automatic SoftCAD classification';confidence='ambiguous_legacy_dxb'
        else:
            found='TXB';evidence='legacy DXB1 header (READ ONLY; not Autodesk DXB)';confidence='legacy_signature'
    if found is None and data.startswith(b'TCAD 1.'):
        found='TCAD';evidence='TCAD 1.x historical text prefix';confidence='text_prefix'
    if found is None and (data.startswith(b'TCAD 2.0\n') or data.startswith(b'TCAD 2.0\r\n')):
        found='TCAD';evidence='TCAD 2.0 engine-observed text prefix';confidence='text_prefix'
    stripped=data.removeprefix(b'\xef\xbb\xbf').lstrip()
    if found is None and (stripped.startswith((b'@tdoc',b'@version',b'%TDOC'))):
        found='TDOC';evidence='document text directive';confidence='text_prefix'
    if found is None and data.startswith(b'SQLite format 3\x00') and len(data)>=72 and data[68:72]==b'GPKG':
        found='GPKG';evidence='SQLite application_id GPKG';confidence='signature'
    if found is None and data.startswith(b'%PDF-'):
        found='PDF';evidence='PDF signature';confidence='signature'
    if found is None and len(data)>=6 and re.fullmatch(rb'AC10[0-9]{2}',data[:6]):
        found='DWG';evidence='DWG AC10xx family header';confidence='signature'
    if found is None and suffix=='.tdocb' and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            if 'FORMAT' in z.namelist():
                found='TDOCB';evidence='ZIP with FORMAT member (candidate, not parsed)';confidence='container_candidate'
    if found is None and suffix=='.tdba' and data.startswith(b'TDB1'):
        found='TDBA';evidence='TDB1 shared container + .tdba extension; internal section not verified';confidence='container_candidate'
    if found=='TDB' and suffix=='.tdba':
        found='TDBA';evidence='TDB1 shared container + .tdba extension; internal section not verified';confidence='container_candidate'
    if found is None and suffix in ('.tsx',):
        # The .tsx extension also belongs to TypeScript/React, so never assume Shield.
        pass
    if suffix=='.txbi':
        found=None;confidence='auxiliary_index';evidence='optional TXB index (.txbi), not an independent TXB document'
    mismatch=bool(found and expected and found!=expected)
    return {
        'file':path.name,'size_bytes':path.stat().st_size,
        'expected_by_extension':expected,'identified':found or (expected if suffix!='.tsx' else None),
        'confidence':confidence if found or confidence in ('ambiguous_legacy_dxb','auxiliary_index') else ('unverified_extension' if suffix!='.tsx' and expected else 'unknown'),
        'evidence':evidence if found or confidence in ('ambiguous_legacy_dxb','auxiliary_index') else ('extension only; contents not validated' if expected else 'none'),
        'mismatch':mismatch,'valid_document':None,
        'warning':'Recognition is not a complete conformance check. No decoding or validation performed.'
    }


def inspect_tdb3_header(path:Path)->dict:
    """Strictly read-only header/superblock sanity for RC1 layout. Does not validate tree."""
    with path.open('rb') as file_obj: data=file_obj.read(12288)
    magic=b'TDB3\x00\r\n\x1a'
    if len(data)<12288 or not data.startswith(magic):
        return {'header':'missing_or_truncated','verified':False}
    hs=struct.Struct('>8sHHd16sI')
    head=data[:hs.size]
    _,version,reserved,created,uuid,crc=hs.unpack(head)
    good=(zlib.crc32(head[:-4])&0xffffffff)==crc
    sb=struct.Struct('>8sQQI32sQI')
    blocks=[]
    for pos in (4096,8192):
        raw=data[pos:pos+sb.size]
        sig,seq,root,rootlen,rootsha,end,blockcrc=sb.unpack(raw)
        blocks.append({'offset':pos,'sequence':seq,'valid_crc':sig==b'TDB3SUPR' and (zlib.crc32(raw[:-4])&0xffffffff)==blockcrc,'file_end':end})
    return {'header':'TDB3 0.5.0 RC1 layout','version':version,'reserved':reserved,'version_supported':version==1,'valid_header_crc':good,'superblocks':blocks,'verified':version==1 and good and any(b['valid_crc'] for b in blocks),'warning':'RC1 header sanity only; not data integrity or current version conformance.'}


def main()->None:
    ap=argparse.ArgumentParser(description='Identify SoftCAD file families without opening private formats')
    ap.add_argument('files',nargs='+',type=Path)
    ap.add_argument('--tdb3-root',action='store_true',help='check active root SHA-256 in TDB3 0.5.0 RC1 (read only; limited to 8 MiB)')
    ap.add_argument('--tdb3-history',action='store_true',help='verify up to 64 active K commit records and SHA parent references (not the complete Merkle tree)')
    ap.add_argument('--cgb1',action='store_true',help='validate bounded native-observed CGB1 header/section subset (NOT full CGB conformance)')
    ap.add_argument('--tcad20',action='store_true',help='check the bounded TCAD 2.0 engine-observed parcel subset (NOT full TCAD conformance)')
    ap.add_argument('--tdb3-header',action='store_true',help='check RC1 TDB3 header and superblock CRC (read only)')
    ap.add_argument('--require-normative',action='store_true',help='exit 2 for candidates without a fully verified public codec/parser; TCB/TXB/TVW currently always fail')
    ap.add_argument('--json-output',type=Path,help='save report to a local JSON file; stdout still prints the same results')
    ap.add_argument('--strict',action='store_true',help='exit with status 2 on extension mismatch, unknown family, or failed requested TDB3 RC1 CRC')
    args=ap.parse_args()
    result=[]
    for p in args.files:
        if not p.is_file():ap.error(f'not a regular file: {p}')
        row=classify(p)
        gate=inspect_interop_gate(p)
        if gate is not None: row['interoperability_gate']=gate
        if args.cgb1 and row['identified']=='CGB':row['cgb1']=inspect_cgb1(p)
        if args.tcad20 and row['identified']=='TCAD':row['tcad20']=inspect_tcad20(p)
        if (args.tdb3_header or args.tdb3_root or args.tdb3_history) and row['identified']=='TDB3':row['tdb3_rc1']=inspect_tdb3_header(p)
        if (args.tdb3_root or args.tdb3_history) and row['identified']=='TDB3':row['tdb3_root']=inspect_tdb3_root(p)
        if args.tdb3_history and row['identified']=='TDB3':row['tdb3_history']=inspect_tdb3_history(p)
        result.append(row)
    report=json.dumps(result,ensure_ascii=False,indent=2)
    if args.json_output:
        args.json_output.write_text(report+'\n',encoding='utf-8')
    print(report)
    if args.require_normative and any(row.get('interoperability_gate') and not row['interoperability_gate']['normative_spec_covered'] for row in result):
        raise SystemExit(2)
    if args.strict and any(row['mismatch'] or row['identified'] is None or (row.get('tdb3_rc1') and not row['tdb3_rc1']['verified']) or (row.get('tdb3_root') and not row['tdb3_root']['verified']) or (row.get('tdb3_history') and not row['tdb3_history']['verified']) or (row.get('tcad20') and not row['tcad20']['verified_subset']) or (row.get('cgb1') and not row['cgb1']['verified_subset']) or (row.get('interoperability_gate') and row['interoperability_gate']['status'] in ('signature_missing','signature_conflict','ambiguous_dxb_collision','extension_collision','auxiliary_index','external_dxb_outside_scope','not_utf8_text','binary_controls','empty_source','source_size_limit')) for row in result):
        raise SystemExit(2)

if __name__=='__main__':main()
