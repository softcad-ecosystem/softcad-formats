/* SoftCAD TCAD 2.0 observed subset probe. Read-only, no native/proprietary engines.
 * Does not implement a full TCAD grammar; do not use to validate legal geometry.
 */
(function(root, factory){
  'use strict'; const obj=factory();
  if(typeof module==='object'&&module.exports)module.exports=obj;
  if(root)root.SoftCADTCAD20=obj;
})(typeof window==='undefined'?null:window,function(){
  'use strict';
  const MAX_BYTES=8*1024*1024,MAX_PARCELS=2000,MAX_POINTS=16000;
  const parcelFields=new Set(['cadgen','area','owner','intravilan','ring']);
  const metaFields=new Set(['crs','profile']);
  const pair=/^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*,\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*$/;
  const bad=code=>{throw new Error(code);};
  function parseBytes(data){
    const result={layout:'TCAD 2.0 observed parcel subset',checked:true,verified_subset:false,
      scope:'UTF-8 meta + single exterior ring parcels only; not a normative grammar or full native validation',parcel_count:0};
    try{
      if(data.byteLength>MAX_BYTES)bad('file_limit_8_mib');
      let content;
      try{content=new TextDecoder('utf-8',{fatal:true}).decode(data);}catch(e){bad('not_utf8');}
      const lines=content.split(/\r\n|\n|\r/);
      if(lines.length===0||lines[0]!=='TCAD 2.0')bad('not_tcad_2_0');
      let section=null,fields={},parcels=0,pointsTotal=0,sumArea=0,sumGeom=0,areaWarnings=0;
      const seen=new Set(),meta={};
      function finishParcel(){
        if(!Object.keys(fields).length)bad('empty_parcel');
        if(Object.keys(fields).length!==parcelFields.size||Object.keys(fields).some(x=>!parcelFields.has(x)))bad('parcel_fields_not_observed_subset');
        const area=Number(fields.area);
        if(fields.area.trim()===''||!Number.isFinite(area)||area<0)bad('invalid_area');
        if(!['0','1'].includes(fields.intravilan))bad('unrecognized_intravilan');
        const tokens=fields.ring.split('|');
        if(tokens.length<4||tokens.length>MAX_POINTS)bad('ring_vertex_limit_or_too_short');
        const points=[];
        for(const token of tokens){
          const m=token.match(pair);if(!m)bad('invalid_ring_point');
          const xy=[Number(m[1]),Number(m[2])];
          if(xy.some(v=>!Number.isFinite(v)||Math.abs(v)>1e12))bad('coordinate_not_finite_or_out_of_bounds');
          points.push(xy);
        }
        if(points[0][0]!==points.at(-1)[0]||points[0][1]!==points.at(-1)[1])bad('ring_not_closed');
        let total=0;for(let i=0;i<points.length-1;i++)total+=points[i][0]*points[i+1][1]-points[i][1]*points[i+1][0];
        const geo=Math.abs(total)/2;
        if(!Number.isFinite(geo)||geo<=0)bad('ring_zero_or_invalid_area');
        if(Math.abs(geo-area)>Math.max(.11,geo*1e-6))areaWarnings++;
        parcels++;if(parcels>MAX_PARCELS)bad('parcel_limit_2000');
        pointsTotal+=points.length;sumArea+=area;sumGeom+=geo;
      }
      for(const line of lines.slice(1)){
        if(!line.trim())continue;
        if(line==='meta'){
          if(section!==null)bad('duplicate_or_late_meta');section='meta';continue;
        }
        if(line.startsWith('parcel ')){
          if(section==='parcel')finishParcel();else if(section!=='meta')bad('missing_meta_section');
          const id=line.slice(7);
          if(!id||id.length>128||seen.has(id)||/\s/.test(id))bad('invalid_or_duplicate_parcel_id');
          seen.add(id);section='parcel';fields={};continue;
        }
        const m=line.match(/^  ([a-z_]+):\s*(.*)$/);
        if(!m||!['meta','parcel'].includes(section))bad('line_outside_observed_subset');
        const name=m[1],value=m[2];
        if(section==='meta'){
          if(!metaFields.has(name)||Object.hasOwn(meta,name))bad('meta_fields_not_observed_subset');
          const q=value.match(/^"([^"\r\n]*)"$/);if(!q)bad('meta_value_not_observed_quoted_form');
          meta[name]=q[1];
        } else {
          if(!parcelFields.has(name)||Object.hasOwn(fields,name))bad('parcel_fields_not_observed_subset');
          fields[name]=value;
        }
      }
      if(section==='parcel')finishParcel();
      if(Object.keys(meta).length!==metaFields.size||Object.keys(meta).some(k=>!metaFields.has(k)))bad('meta_fields_not_observed_subset');
      Object.assign(result,{verified_subset:true,crs:meta.crs,profile:meta.profile,parcel_count:parcels,
        ring_point_count:pointsTotal,sum_reported_area:Number(sumArea.toFixed(9)),sum_geometrical_area:Number(sumGeom.toFixed(9)),
        area_discrepancies:areaWarnings,
        warning:'Only the observed TCAD 2.0 subset is recognized; native interoperability and cadastral validity require separate checks.'});
    }catch(e){result.reason=String(e.message||e);}
    return result;
  }
  async function inspect(file){
    if(file.size>MAX_BYTES)return parseBytes(new Uint8Array(MAX_BYTES+1));
    return parseBytes(new Uint8Array(await file.arrayBuffer()));
  }
  return Object.freeze({parseBytes,inspect,MAX_BYTES});
});
