/* TDB3 0.5.0 RC1 root chunk verification, browser/Node, read-only.
 * Verifies exactly one active commit root, not the full database or history.
 */
(function(root,build){
  'use strict';const moduleValue=build();
  if(typeof module==='object'&&module.exports)module.exports=moduleValue;
  if(root)root.SoftCADTDB3Root=moduleValue;
})(typeof window==='undefined'?null:window,function(){
'use strict';
const LIMIT=8*1024*1024;
const text=new TextEncoder();
function eq(data,literal,off=0){return data.length>=off+literal.length&&Array.from(literal).every((v,i)=>data[off+i]===v);}
const sig=literal=>Array.from(text.encode(literal));
const magic=[84,68,66,51,0,13,10,26];
const chunkmagic=[0xd7,84,66,51];
const table=new Uint32Array(256);
for(let i=0;i<256;i++){let v=i;for(let k=0;k<8;k++)v=(v&1)?(0xedb88320^(v>>>1)):(v>>>1);table[i]=v>>>0;}
function crc32(bytes){let c=0xffffffff;for(const b of bytes)c=(table[(c^b)&255]^(c>>>8))>>>0;return(c^0xffffffff)>>>0;}
async function inflateBounded(blob,max){
  if(typeof DecompressionStream==='undefined')return {data:null,reason:'DecompressionStream_unavailable'};
  const reader=blob.stream().pipeThrough(new DecompressionStream('deflate')).getReader();
  const parts=[];let total=0;
  try{
    for(;;){const {value,done}=await reader.read();if(done)break;total+=value.byteLength;
      if(total>max){await reader.cancel();return {data:null,reason:'root_decompressed_size_limit'};}
      parts.push(value);
    }
  }catch(err){return {data:null,reason:'zlib_root_decompression_failed'};}
  const out=new Uint8Array(total);let off=0;
  for(const part of parts){out.set(part,off);off+=part.length;}
  return {data:out};
}
const SHA_K=[
  0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
  0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
  0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
  0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
  0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
  0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
  0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
  0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
];
function sha256Fallback(data){
  // Independent SHA-256 on a bounded <=8 MiB payload for opaque/offline origins.
  const n=data.length;
  if(n>LIMIT)throw new Error('SHA-256 fallback input limit exceeded');
  const total=(n+9+63)&~63,padded=new Uint8Array(total);
  padded.set(data);padded[n]=0x80;
  const view=new DataView(padded.buffer);
  const bitLength=n*8;
  view.setUint32(total-8,Math.floor(bitLength/0x100000000),false);
  view.setUint32(total-4,bitLength>>>0,false);
  const state=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  const w=new Uint32Array(64);
  const r=(x,k)=>(x>>>k)|(x<<(32-k));
  for(let off=0;off<total;off+=64){
    for(let j=0;j<16;j++)w[j]=view.getUint32(off+j*4,false);
    for(let j=16;j<64;j++){
      const a=w[j-15],b=w[j-2];
      w[j]=((w[j-16]+(r(a,7)^r(a,18)^(a>>>3)))+(w[j-7]+(r(b,17)^r(b,19)^(b>>>10))))>>>0;
    }
    let [a,b,c,d,e,f,g,h]=state;
    for(let j=0;j<64;j++){
      const s1=r(e,6)^r(e,11)^r(e,25),ch=(e&f)^(~e&g);
      const t1=(h+s1+ch+SHA_K[j]+w[j])>>>0;
      const s0=r(a,2)^r(a,13)^r(a,22),maj=(a&b)^(a&c)^(b&c);
      const t2=(s0+maj)>>>0;
      h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
    }
    [a,b,c,d,e,f,g,h].forEach((v,i)=>state[i]=(state[i]+v)>>>0);
  }
  return state.map(v=>v.toString(16).padStart(8,'0')).join('');
}
async function hashHex(bytes){
  if(typeof crypto!=='undefined'&&crypto.subtle){
    const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));
    return Array.from(digest,v=>v.toString(16).padStart(2,'0')).join('');
  }
  return sha256Fallback(bytes);
}
async function inspect(file){
  const size=file.size;
  const result={layout:'TDB3 0.5.0 RC1',checked:false,verified:false,
    scope:'active commit root only; not the complete Merkle tree or database'};
  if(size<12288)return {...result,reason:'not_tdb3_or_short_file'};
  const header=new Uint8Array(await file.slice(0,12288).arrayBuffer());
  if(!eq(header,magic))return {...result,reason:'not_tdb3_or_short_file'};
  const dv=new DataView(header.buffer,header.byteOffset,header.byteLength);
  result.storage_version=dv.getUint16(8,false);
  result.header_crc_valid=crc32(header.subarray(0,36))===dv.getUint32(36,false);
  if(result.storage_version!==1||!result.header_crc_valid)return {...result,checked:true,reason:'unsupported_version_or_header_crc'};
  const slots=[];
  for(const off of [4096,8192]){
    const seq=dv.getBigUint64(off+8,false);
    const sha=Array.from(header.subarray(off+28,off+60),v=>v.toString(16).padStart(2,'0')).join('');
    slots.push({slot_offset:off,sequence:seq,root_offset:Number(dv.getBigUint64(off+16,false)),
      root_length:dv.getUint32(off+24,false),root_sha256:sha,
      committed_end:Number(dv.getBigUint64(off+60,false)),
      valid_crc:eq(header,sig('TDB3SUPR'),off)&&crc32(header.subarray(off,off+68))===dv.getUint32(off+68,false)});
  }
  result.superblocks=slots.map(s=>({slot_offset:s.slot_offset,sequence:s.sequence.toString(),valid_crc:s.valid_crc}));
  const valid=slots.filter(s=>s.valid_crc);
  if(!valid.length)return {...result,checked:true,reason:'no_valid_superblock'};
  const active=valid.reduce((a,b)=>b.sequence>a.sequence?b:a);
  Object.assign(result,{active_slot_offset:active.slot_offset,active_sequence:active.sequence.toString(),
    root_offset:active.root_offset,root_length:active.root_length,expected_sha256:active.root_sha256,
    committed_end:active.committed_end,physical_end:size,
    uncommitted_tail_bytes:Math.max(0,size-active.committed_end),checked:true});
  const off=active.root_offset,ln=active.root_length,end=active.committed_end;
  if(!Number.isSafeInteger(end)||end>size||end<12288)return {...result,reason:'commit_boundary_outside_file'};
  if(!Number.isSafeInteger(off)||off<12288||ln<20||off+ln>end)return {...result,reason:'root_reference_outside_commit'};
  if(ln>LIMIT)return {...result,checked:false,reason:'root_chunk_exceeds_read_limit'};
  const body=new Uint8Array(await file.slice(off,off+ln).arrayBuffer());
  if(body.length!==ln)return {...result,reason:'short_root_chunk'};
  const bdv=new DataView(body.buffer,body.byteOffset,body.byteLength);
  const kind=body[4],codec=body[5],canonicalLen=bdv.getUint32(8,false),storedLen=bdv.getUint32(12,false),nloc=bdv.getUint32(16,false);
  Object.assign(result,{chunk_kind:String.fromCharCode(kind),chunk_codec:codec,
    canonical_length:canonicalLen,stored_length:storedLen,locator_count:nloc});
  if(!eq(body,chunkmagic)||kind!==75||(codec!==0&&codec!==1))return {...result,reason:'root_chunk_magic_type_or_codec'};
  if(20+storedLen+12*nloc!==ln)return {...result,reason:'root_chunk_length_mismatch'};
  if(canonicalLen>LIMIT)return {...result,checked:false,reason:'canonical_payload_exceeds_limit'};
  const payload=body.subarray(20,20+storedLen);
  let canonical;
  if(codec===0)canonical=payload;
  else{
    const inflated=await inflateBounded(new Blob([payload]),LIMIT);
    if(!inflated.data)return {...result,checked:inflated.reason==='DecompressionStream_unavailable'?false:true,reason:inflated.reason};
    canonical=inflated.data;
  }
  if(canonical.length!==canonicalLen)return {...result,reason:'root_canonical_length_mismatch'};
  const digest=await hashHex(canonical);
  if(!digest)return {...result,checked:false,reason:'WebCrypto_SHA256_unavailable'};
  result.actual_sha256=digest;
  result.verified=digest===active.root_sha256;
  result.reason=result.verified?'root_sha256_match':'root_sha256_mismatch';
  return result;
}
return Object.freeze({inspect,crc32,sha256Fallback});
});
