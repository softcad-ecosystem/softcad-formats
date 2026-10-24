/* SoftCAD TDB3 0.5.0 RC1 independent bounded commit-chain inspector.
 * Read-only, local and restricted to K commit chunks (not the full Merkle DAG).
 * No application engine, Shield or proprietary codec is included.
 */
(function(root,build){
  'use strict';const api=build();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.SoftCADTDB3History=api;
})(typeof window==='undefined'?null:window,function(){
'use strict';
const MAX_CHUNK=8*1024*1024,MAX_CANON=8*1024*1024,MAX_TOTAL=32*1024*1024,MAX_COMMITS=64;
const UTF8=new TextDecoder('utf-8',{fatal:true});
const REAL_REF=Symbol('TDB3_RC1_BINARY_REF');
const hex=b=>Array.from(b,v=>v.toString(16).padStart(2,'0')).join('');
class FormatError extends Error{constructor(code){super(code);this.code=code;}}
function fail(code){throw new FormatError(code);}
function take(bytes,off,n){if(!Number.isSafeInteger(off)||!Number.isSafeInteger(n)||n<0||off<0||off+n>bytes.length)fail('commit_canonical_truncated');return bytes.subarray(off,off+n);}
function u32(bytes,off){take(bytes,off,4);return new DataView(bytes.buffer,bytes.byteOffset+off,4).getUint32(0,false);}
function u64(bytes,off){take(bytes,off,8);const v=new DataView(bytes.buffer,bytes.byteOffset+off,8).getBigUint64(0,false);if(v>BigInt(Number.MAX_SAFE_INTEGER))fail('history_offset_out_of_range');return Number(v);}
function vi(bytes,at){let n=0n,off=at;for(let k=0;k<10;k++){
  const oct=take(bytes,off++,1)[0];n|=BigInt(oct&127)<<BigInt(k*7);
  if(oct<128){if(n>BigInt(Number.MAX_SAFE_INTEGER))fail('commit_varint_out_of_range');return {value:Number(n),off};}
}fail('commit_varint_out_of_range');}
function text(bytes){try{return UTF8.decode(bytes);}catch(_){fail('commit_invalid_utf8');}}
function cmpBytes(a,b){const n=Math.min(a.length,b.length);for(let i=0;i<n;i++)if(a[i]!==b[i])return a[i]-b[i];return a.length-b.length;}
function parseValue(bytes,off,loc,state,depth=0){
  if(depth>8)fail('commit_decode_depth_limit');
  const tag=take(bytes,off++,1)[0];
  if(tag<3){return {value:tag===0?null:tag===2,off};}
  if(tag===3){const v=vi(bytes,off);return {value:(v.value%2===0?v.value/2:-(v.value+1)/2),off:v.off};}
  if(tag===4){const b=take(bytes,off,8),value=new DataView(b.buffer,b.byteOffset,8).getFloat64(0,false);return {value,off:off+8};}
  if(tag===5||tag===6){const l=vi(bytes,off),n=l.value;if(n>MAX_CANON)fail('commit_string_limit');const val=take(bytes,l.off,n);return {value:tag===5?text(val):val,off:l.off+n};}
  if(tag===9){const digest=hex(take(bytes,off,32));const count=vi(bytes,off+32);const idx=state.idx++;
    if(idx>=loc.length)fail('commit_missing_locator');
    return {value:{[REAL_REF]:true,sha256:digest,offset:loc[idx].offset,length:loc[idx].length,count:count.value,locator_index:idx},off:count.off};}
  if(tag===7||tag===8){const o=vi(bytes,off),n=o.value;if(n>2048)fail('commit_collection_limit');off=o.off;
    if(tag===7){const values=[];for(let i=0;i<n;i++){const v=parseValue(bytes,off,loc,state,depth+1);values.push(v.value);off=v.off;}return {value:values,off};}
    const values=Object.create(null),seen=new Set();let prev=null;
    for(let i=0;i<n;i++){const k=vi(bytes,off),count=k.value;if(count>MAX_CANON)fail('commit_key_limit');const kb=take(bytes,k.off,count);
      if(prev!==null&&cmpBytes(kb,prev)<=0)fail('commit_noncanonical_keys');prev=kb;
      const key=text(kb);if(seen.has(key))fail('commit_noncanonical_keys');seen.add(key);off=k.off+count;
      const v=parseValue(bytes,off,loc,state,depth+1);values[key]=v.value;off=v.off;}
    return {value:values,off};
  }
  fail('commit_unknown_value_tag');
}
async function decompress(payload,max){
  if(typeof DecompressionStream==='undefined')fail('history_zlib_unavailable');
  const reader=new Blob([payload]).stream().pipeThrough(new DecompressionStream('deflate')).getReader();
  const parts=[];let total=0;
  try{for(;;){const {value,done}=await reader.read();if(done)break;total+=value.length;
      if(total>max){await reader.cancel();fail('history_invalid_zlib_chunk');}parts.push(value);}}
  catch(e){if(e instanceof FormatError)throw e;fail('history_invalid_zlib_chunk');}
  const out=new Uint8Array(total);let off=0;
  for(const part of parts){out.set(part,off);off+=part.length;}return out;
}
async function sha256(bytes){
  if(typeof crypto!=='undefined'&&crypto.subtle){return hex(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)));}
  const root=typeof window!=='undefined'?window.SoftCADTDB3Root:null;
  if(root&&root.sha256Fallback)return root.sha256Fallback(bytes);
  if(typeof module==='object'&&module.exports){const previous=require('./softcad-tdb3-root.js');return previous.sha256Fallback(bytes);}
  fail('history_sha256_unavailable');
}
async function readCommit(file,ref,end,budget){
  const off=ref.offset,len=ref.length;
  if(!Number.isSafeInteger(off)||!Number.isSafeInteger(len)||off<12288||len<20||off+len>end)fail('history_parent_outside_commit');
  if(len>MAX_CHUNK||budget.bytes+len>MAX_TOTAL)fail('history_read_limit');
  const raw=new Uint8Array(await file.slice(off,off+len).arrayBuffer());
  if(raw.length!==len)fail('history_short_chunk');budget.bytes+=len;
  const kind=raw[4],codec=raw[5],canonLen=u32(raw,8),storedLen=u32(raw,12),count=u32(raw,16);
  if(raw[0]!==0xd7||raw[1]!==84||raw[2]!==66||raw[3]!==51||kind!==75||(codec!==0&&codec!==1))fail('history_commit_chunk_type');
  if(count>4096)fail('history_locator_limit');
  if(20+storedLen+count*12!==len)fail('history_chunk_length_mismatch');
  if(canonLen>MAX_CANON)fail('history_read_limit');
  const packed=raw.subarray(20,20+storedLen),canonical=codec===0?packed:await decompress(packed,MAX_CANON);
  if(canonical.length!==canonLen)fail('history_canonical_length_mismatch');
  if(await sha256(canonical)!==ref.sha256)fail('history_parent_sha256_mismatch');
  const loc=[],start=20+storedLen;
  for(let i=0;i<count;i++)loc.push({offset:u64(raw,start+i*12),length:u32(raw,start+i*12+8)});
  const state={idx:0};const parsed=parseValue(canonical,0,loc,state);
  if(parsed.off!==canonical.length||state.idx!==loc.length)fail('history_commit_encoding_mismatch');
  const obj=parsed.value;
  if(!obj||typeof obj!=='object'||Array.isArray(obj)||!Number.isSafeInteger(obj.secventa))fail('history_commit_metadata_invalid');
  if(obj.parinte!==null&&obj.parinte!==undefined&&(!obj.parinte||obj.parinte[REAL_REF]!==true))fail('history_parent_type_invalid');
  if(obj.catalog!==null&&obj.catalog!==undefined&&(!obj.catalog||obj.catalog[REAL_REF]!==true))fail('history_catalog_type_invalid');
  return {sequence:obj.secventa,parent:obj.parinte||null,catalog_exists:obj.catalog!=null};
}
async function inspect(file,maxCommits=MAX_COMMITS){
  if(!Number.isInteger(maxCommits)||maxCommits<1||maxCommits>MAX_COMMITS)throw new RangeError('maxCommits must be 1..64');
  const root=typeof window!=='undefined'?window.SoftCADTDB3Root:require('./softcad-tdb3-root.js');
  if(!root)throw new Error('SoftCAD root inspector is missing');
  const first=await root.inspect(file),result={layout:'TDB3 0.5.0 RC1',scope:'active commit ancestry (K chunks) only; no catalog, Merkle, or row validation',
    checked:false,verified:false,complete:false,commit_count:0,max_commits:maxCommits,commits:[]};
  if(!first.verified)return {...result,reason:'history_root_not_verified'};
  const end=first.committed_end,budget={bytes:0},seen=new Set();
  let ref={offset:first.root_offset,length:first.root_length,sha256:first.expected_sha256};
  let expectedSeq=Number(first.active_sequence);
  try{
    for(let level=0;level<maxCommits;level++){
      const id=[ref.offset,ref.length,ref.sha256].join(':');if(seen.has(id))fail('history_cycle_detected');seen.add(id);
      const commit=await readCommit(file,ref,end,budget),seq=commit.sequence;
      if(level===0?(seq!==expectedSeq||seq<1):(seq>=expectedSeq||seq<1))fail('history_sequence_invalid');
      const parent=commit.parent;
      result.commits.push({sequence:String(seq),sha256:ref.sha256,offset:ref.offset,parent_exists:parent!==null,catalog_exists:commit.catalog_exists});
      result.commit_count=result.commits.length;expectedSeq=seq;
      if(parent===null)return {...result,checked:true,verified:true,complete:true,read_bytes:budget.bytes,reason:'history_chain_valid_complete'};
      if(parent.offset>=ref.offset)fail('history_parent_not_older');
      ref=parent;
    }
  }catch(e){if(e instanceof FormatError)return {...result,checked:true,read_bytes:budget.bytes,reason:e.code};throw e;}
  return {...result,checked:false,verified:false,complete:false,read_bytes:budget.bytes,reason:'history_chain_limit_reached'};
}
return Object.freeze({inspect});
});
