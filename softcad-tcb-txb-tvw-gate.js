/* SoftCAD public TCB/TXB/TVW identity + text plausibility checks; NO codecs. */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.SoftCADInteroperabilityGate=api;})
(typeof window==='undefined'?null:window,function(){'use strict';
 const MAX=65536;
 const begins=(data,arr)=>data.length>=arr.length&&arr.every((b,i)=>data[i]===b);
 const nameExt=name=>{let i=name.lastIndexOf('.');return i<0?'':name.slice(i).toLowerCase();};
 function inspectBytes(name,data,size=data.length){
  const ext=nameExt(name);if(!['.tcb','.txb','.dxb','.txbi','.tvw'].includes(ext))return null;
  const r={checked:true,format_authenticity:'UNVERIFIED',can_write:false,codec_included:false,normative_spec_covered:false,
   validation_scope:'IDENTITY_AND_TEXT_PLAUSIBILITY_ONLY',status:'unknown',detail:'Not a full file-format or language validator'};
  const tcb=begins(data,[84,67,66,1]),txb=begins(data,[84,88,66,49]),dxb=begins(data,[68,88,66,49]);
  if(ext==='.txbi'){r.status='auxiliary_index';r.detail='TXBI is an optional TXB index, not a standalone drawing';return r;}
  if(ext==='.dxb'){
   r.status=dxb?'ambiguous_dxb_collision':txb?'extension_collision':'external_dxb_outside_scope';
   r.detail=dxb?'DXB1 can denote historical SoftCAD data; .dxb belongs to Autodesk and is not automatically TXB':txb?'TXB1 under Autodesk .dxb extension; do not write or convert automatically':'Autodesk DXB: not parsed or recognized by this SoftCAD gate';return r;
  }
  if(ext==='.tcb'){
   r.status=tcb?'signature_only':txb||dxb?'signature_conflict':'signature_missing';
   r.detail=tcb?'TCB\\x01 signature matches; full binary layout unavailable':txb||dxb?'TXB/DXB signature conflicts with .tcb extension':'No full TCB\\x01 prefix; cannot establish TCB identity';return r;
  }
  if(ext==='.txb'){
   r.status=txb?'signature_only':dxb?'legacy_read_only':tcb?'signature_conflict':'signature_missing';
   r.detail=txb?'TXB1 prefix found, payload not decoded':dxb?'Historical DXB1 in .txb: reading may be supported; writing DXB1 or Autodesk .dxb is not supported':tcb?'TCB signature conflicts with .txb extension':'No TXB1/DXB1 prefix; cannot establish TXB identity';return r;
  }
  if(size===0){r.status='empty_source';r.detail='No content to examine';return r;}
  if(size>MAX){r.checked=false;r.status='source_size_limit';r.detail='TVW text-plausibility probe limited to 64 KiB';return r;}
  let source;
  try{source=new TextDecoder('utf-8',{fatal:true}).decode(data);}
  catch(e){r.status='not_utf8_text';r.detail='Does not decode as UTF-8 source text';return r;}
  if([...source].some(c=>{let v=c.codePointAt(0);return v<32&&v!==9&&v!==10&&v!==13;})){
   r.status='binary_controls';r.detail='Contains binary control characters; not plausible UTF-8 source';return r;
  }
  r.status='utf8_text_candidate';r.detail='Text is valid UTF-8; this does not parse or validate TVW syntax';
  r.text_lines=source.replace(/^\uFEFF/,'').split(/\r\n|\r|\n/).length-(source.endsWith('\n')||source.endsWith('\r')?1:0);
  return r;
 }
 async function inspectFile(file){return inspectBytes(file.name,new Uint8Array(await file.slice(0,MAX+1).arrayBuffer()),file.size);}
 return Object.freeze({inspectBytes,inspectFile});
});
