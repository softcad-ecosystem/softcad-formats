/* SoftCAD developer file-family inspector v1.30.11
 * Identification only: no proprietary codecs, keys, conversion or execution.
 * All parsing stays local and read-only. TDB3 layout applies ONLY to 0.5.0 RC1.
 */
(function(root, build) {
  'use strict';
  const core = build();
  if (typeof module === 'object' && module.exports) module.exports = core;
  if (root) root.SoftCADFormatCore = core;
})(typeof window === 'undefined' ? null : window, function() {
  'use strict';
  const SIGNATURES = [
    ['TDB3', [0x54,0x44,0x42,0x33,0x00,0x0d,0x0a,0x1a]],
    ['TDOCB', [0x54,0x44,0x4f,0x43,0x42,0x01]],
    ['TSX', [0x54,0x53,0x53,0x58,0x00]],
    ['TCB', [0x54,0x43,0x42,0x01]],
    ['CGB', [0x43,0x47,0x42,0x31]],
    ['TXB', [0x54,0x58,0x42,0x31]],
    ['TDB', [0x54,0x44,0x42,0x31]]
  ];
  const EXT = Object.freeze({
    '.tcad':'TCAD','.tcb':'TCB','.cgb':'CGB','.txb':'TXB','.tdb':'TDB',
    '.tdoc':'TDOC','.tdocb':'TDOCB','.tss':'TSS','.tsx':'TSX','.tvw':'TVW',
    '.tdba':'TDBA','.tdb3':'TDB3','.tcbg':'TCBG','.tvcs':'TVCS',
    '.tvsc':'TVSC','.tvdb':'TVDB','.cgxml':'CGXML','.dwg':'DWG',
    '.dxf':'DXF','.gpkg':'GPKG','.pdf':'PDF'
  });
  const bytesEqual = (data, values, off=0) => data.length >= off+values.length && values.every((v,i)=>data[off+i]===v);
  const begins = (data, str, off=0) => bytesEqual(data, Array.from(str, c=>c.charCodeAt(0)), off);
  const extension = name => {const i=name.lastIndexOf('.');return i<0?'':name.slice(i).toLowerCase();};
  const hex = (data, len=32) => Array.from(data.subarray(0,len),b=>b.toString(16).padStart(2,'0')).join(' ');
  const CRC_TABLE = new Uint32Array(256);
  for (let n=0;n<256;n++) {let c=n;for(let j=0;j<8;j++)c=c&1?0xedb88320^(c>>>1):c>>>1;CRC_TABLE[n]=c>>>0;}
  function crc32(bytes) {
    let c=0xffffffff;
    for(const b of bytes)c=(CRC_TABLE[(c^b)&255]^(c>>>8))>>>0;
    return (c^0xffffffff)>>>0;
  }
  function tdb3RC1(bytes) {
    if(!bytesEqual(bytes,SIGNATURES[0][1]))return {layout:'TDB3 0.5.0 RC1',checked:false,verified:false,reason:'missing_magic'};
    if(bytes.length<12288)return {layout:'TDB3 0.5.0 RC1',checked:false,verified:false,reason:'truncated_before_superblock_B'};
    const dv=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
    const version=dv.getUint16(8,false);
    const reserved=dv.getUint16(10,false);
    const savedCRC=dv.getUint32(36,false);
    const validHeaderCRC=crc32(bytes.subarray(0,36))===savedCRC;
    const superblocks=[];
    for(const offset of [4096,8192]) {
      const saved=dv.getUint32(offset+68,false);
      const validMagic=begins(bytes,'TDB3SUPR',offset);
      const validCRC=validMagic && crc32(bytes.subarray(offset,offset+68))===saved;
      superblocks.push({offset,sequence:dv.getBigUint64(offset+8,false).toString(),valid_magic:validMagic,valid_crc:validCRC});
    }
    const verified=version===1&&validHeaderCRC&&superblocks.some(b=>b.valid_crc);
    return {layout:'TDB3 0.5.0 RC1',checked:true,version,reserved,valid_header_crc:validHeaderCRC,superblocks,verified,
      limit:'RC1 header/commit-root sanity only. Does not validate transactions, payloads, data model or current-version compatibility.'};
  }
  function sniff(name,bytes,size=bytes.length) {
    const suffix=extension(name), expected=EXT[suffix]||null;
    let identified=null,confidence='extension_only',evidence='Filename extension only';
    for(const [kind,magic] of SIGNATURES) {
      if(bytesEqual(bytes,magic)){identified=kind;confidence='signature';evidence='File header signature';break;}
    }
    if(!identified&&begins(bytes,'DXB1')) {
      if(suffix==='.dxb'){confidence='ambiguous_legacy_dxb';evidence='Ambiguous DXB1 + Autodesk .dxb extension; no automatic SoftCAD classification';}
      else {identified='TXB';confidence='legacy_signature';evidence='Legacy DXB1 (read only; not Autodesk .dxb)';}
    }
    if(!identified&&begins(bytes,'TCAD 1.')){identified='TCAD';confidence='text_prefix';evidence='TCAD 1.x historical text prefix';}
    if(!identified&&(begins(bytes,'TCAD 2.0\n')||begins(bytes,'TCAD 2.0\r\n'))){identified='TCAD';confidence='text_prefix';evidence='TCAD 2.0 engine-observed text prefix';}
    const utf8BOM=bytesEqual(bytes,[0xef,0xbb,0xbf]);let k=utf8BOM?3:0;
    while(k<bytes.length&&[9,10,13,32].includes(bytes[k]))k++;
    if(!identified&&(begins(bytes,'@tdoc',k)||begins(bytes,'@version',k)||begins(bytes,'%TDOC',k))) {
      identified='TDOC';confidence='text_prefix';evidence='TDOC text directive';
    }
    if(!identified&&begins(bytes,'%PDF-')){identified='PDF';confidence='signature';evidence='PDF header';}
    if(!identified&&begins(bytes,'SQLite format 3\0')&&begins(bytes,'GPKG',68)) {
      identified='GPKG';confidence='signature';evidence='SQLite application_id GPKG';
    }
    if(!identified&&begins(bytes,'AC10')&&bytes.length>=6&&bytes[4]>=48&&bytes[4]<=57&&bytes[5]>=48&&bytes[5]<=57){
      identified='DWG';confidence='signature';evidence='DWG AC10xx header';
    }
    if(identified==='TDB'&&suffix==='.tdba'){
      identified='TDBA';confidence='container_candidate';evidence='Shared TDB1 container; TDBA internal section unverified';
    }
    if(suffix==='.txbi'){identified=null;confidence='auxiliary_index';evidence='Optional TXB index (.txbi), not a standalone TXB document';}
    let result={file:name,size_bytes:size,expected_by_extension:expected,
      identified:identified||((expected&&suffix!=='.tsx')?expected:null),
      confidence:identified?confidence:(confidence==='ambiguous_legacy_dxb'||confidence==='auxiliary_index'?confidence:expected&&suffix!=='.tsx'?'unverified_extension':'unknown'),
      evidence:identified?evidence:(confidence==='ambiguous_legacy_dxb'||confidence==='auxiliary_index'?evidence:expected&&suffix!=='.tsx'?'Extension only; content unverified':'No matching signature'),
      mismatch:Boolean(identified&&expected&&identified!==expected),valid_document:null,header_hex:hex(bytes)};
    if(identified==='TDB3')result.tdb3_rc1=tdb3RC1(bytes);
    result.warning='Family identification is NOT complete format validation or a security scan.';
    return result;
  }
  // ZIP central-directory recognition only, never inflate untrusted entries.
  async function hasZipFormatMember(file) {
    if(file.size<22)return {checked:false,found:false,reason:'short_file'};
    const start=Math.max(0,file.size-65557);
    const tail=new Uint8Array(await file.slice(start).arrayBuffer());
    const dv=new DataView(tail.buffer,tail.byteOffset,tail.byteLength);
    let eocd=-1;
    for(let i=tail.length-22;i>=0;i--) {
      if(dv.getUint32(i,true)===0x06054b50&&i+22+dv.getUint16(i+20,true)===tail.length){eocd=i;break;}
    }
    if(eocd<0)return {checked:false,found:false,reason:'EOCD_absent_or_comment_trailer'};
    if(dv.getUint16(eocd+4,true)!==0||dv.getUint16(eocd+6,true)!==0)return {checked:false,found:false,reason:'multidisk_not_supported'};
    const entries=dv.getUint16(eocd+10,true),dirSize=dv.getUint32(eocd+12,true),dirOff=dv.getUint32(eocd+16,true);
    if(entries===65535||dirOff===0xffffffff||dirSize===0xffffffff)return {checked:false,found:false,reason:'zip64_not_supported'};
    if(dirSize>262144||entries>5000||dirOff+dirSize>file.size)return {checked:false,found:false,reason:'directory_outside_safety_limit'};
    const data=new Uint8Array(await file.slice(dirOff,dirOff+dirSize).arrayBuffer());
    const view=new DataView(data.buffer,data.byteOffset,data.byteLength);
    let offset=0,processed=0;
    while(offset+46<=data.length&&processed<entries) {
      if(view.getUint32(offset,true)!==0x02014b50)return {checked:false,found:false,reason:'malformed_central_directory'};
      const nameLen=view.getUint16(offset+28,true),extraLen=view.getUint16(offset+30,true),commentLen=view.getUint16(offset+32,true);
      if(offset+46+nameLen+extraLen+commentLen>data.length)return {checked:false,found:false,reason:'truncated_central_directory'};
      if(nameLen===6&&begins(data,'FORMAT',offset+46))return {checked:true,found:true,evidence:'ZIP central directory contains FORMAT; payload not parsed'};
      offset+=46+nameLen+extraLen+commentLen;processed++;
    }
    return {checked:processed===entries,found:false,reason:'FORMAT_member_absent'};
  }
  async function inspectFile(file) {
    const prefix=new Uint8Array(await file.slice(0,12288).arrayBuffer());
    const result=sniff(file.name,prefix,file.size);
    if(extension(file.name)==='.tdocb'&&result.identified==='TDOCB'&&result.confidence==='unverified_extension') {
      const zip=await hasZipFormatMember(file);
      if(zip.found){result.confidence='container_candidate';result.evidence=zip.evidence;}
      result.zip_probe=zip;
    }
    return result;
  }
  return Object.freeze({sniff,inspectFile,tdb3RC1,crc32,hasZipFormatMember,extension});
});
