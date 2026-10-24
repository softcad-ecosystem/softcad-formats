/* SoftCAD CGB1 independent observed-subset verifier. Read-only/local, no private code.
 * Covers 140-byte header and Land/Person/Point section spans of native tests.
 * NOT a full CGB decoder, semantic validator or version-stable specification.
 */
(function(root, factory){
  'use strict';
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.SoftCADCGB1=api;
})(typeof window==='undefined'?null:window,function(){
  'use strict';
  const HEADER_BYTES=140,MAX_BYTES=8*1024*1024;
  const countLabels=['lands','parcels','buildings','persons','points'];
  const sectionLabels=['lands','parcels','buildings','persons','points','strings'];
  function parseBytes(bytes,totalSize){
    const size=(totalSize===undefined)?bytes.length:totalSize;
    const r={layout:'CGB1 observed native subset (2026-10-23)',checked:false,
      verified_subset:false,file_size:size,
      scope:'Header counts and bounded section positions only; parcels/buildings and inner records not decoded.'};
    const fail=reason=>{r.reason=reason;return r;};
    if(size>MAX_BYTES)return fail('file_limit_8_mib');
    if(size<HEADER_BYTES||bytes.length<HEADER_BYTES)return fail('truncated_cgb1_header_140');
    if(!(bytes[0]===67&&bytes[1]===71&&bytes[2]===66&&bytes[3]===49))return fail('not_cgb1');
    r.checked=true;
    const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
    const version=v.getUint32(4,true);r.version=version;
    if(version!==1)return fail('unsupported_cgb_version');
    const counts=Object.fromEntries(countLabels.map((key,i)=>[key,v.getUint32(8+i*4,true)]));
    const offsets=Object.fromEntries(sectionLabels.map((key,i)=>[key,v.getBigUint64(28+i*8,true).toString()]));
    r.counts=counts;
    // Every offset must be representable precisely and bounded by the file.
    const values=Object.values(offsets).map(x=>BigInt(x));
    if(values[0]!==BigInt(HEADER_BYTES))return fail('unexpected_first_section_offset');
    if(values.some(x=>x<BigInt(HEADER_BYTES)||x>BigInt(size)))return fail('section_offset_outside_file');
    r.section_offsets=Object.fromEntries(Object.entries(offsets).map(([k,val])=>[k,Number(val)]));
    if(values.some((x,i)=>i>0&&x<values[i-1]))return fail('section_offsets_not_monotonic');
    if(Object.values(counts).some(n=>n>100000))return fail('section_count_safety_limit');
    if(counts.parcels||counts.buildings)return fail('parcel_building_record_layout_not_yet_covered');
    if(values[1]-values[0]!==BigInt(counts.lands*44))return fail('land_section_span_count_mismatch');
    if(values[1]!==values[2]||values[2]!==values[3])return fail('unexpected_nonempty_parcel_or_building_section');
    if(values[4]-values[3]!==BigInt(counts.persons*40))return fail('person_section_span_count_mismatch');
    if(values[5]-values[4]!==BigInt(counts.points*24))return fail('point_section_span_count_mismatch');
    const totalArea=v.getFloat64(84,true);
    if(!Number.isFinite(totalArea)||totalArea<0)return fail('nonfinite_or_negative_aggregate_area');
    r.verified_subset=true;
    r.reason='observed_section_layout_consistent';
    r.warning='CGB1 subset structure, NOT native openability, semantic validity, checksum validation or complete binary conformance.';
    return r;
  }
  async function inspect(file){
    const bytes=new Uint8Array(await file.slice(0,HEADER_BYTES).arrayBuffer());
    return parseBytes(bytes,file.size);
  }
  return Object.freeze({parseBytes,inspect,HEADER_BYTES,MAX_BYTES});
});
