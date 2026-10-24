/* Node 20+: cross-language synthetic identity tests, no network. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const core=require('./softcad-format-core.js');
const root=path.join(__dirname,'vectors');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
(async()=>{
 for(const [name,expected] of Object.entries(manifest.cases)){
   const bytes=fs.readFileSync(path.join(root,name));
   assert.equal(require('node:crypto').createHash('sha256').update(bytes).digest('hex'),expected.sha256,name);
   const sniff=core.sniff(name,bytes,bytes.length);
   assert.equal(sniff.identified||'UNKNOWN',expected.identified,name);
   const isZip=name.startsWith('zip_');
   if(!isZip)assert.equal(sniff.confidence,expected.confidence,name);
   if(name==='valid_crc_only.tdb3')assert.equal(sniff.tdb3_rc1.verified,true);
   if(name==='bad_header_crc.tdb3'||name==='future_version_2.tdb3')assert.equal(sniff.tdb3_rc1.verified,false);
   if(isZip){
     const file=new File([bytes],name);
     const report=await core.inspectFile(file);
     assert.equal(report.confidence,expected.confidence,name);
   }
 }
 assert.equal(core.crc32(Buffer.from('123456789')),0xcbf43926);
 console.log('PASS:',Object.keys(manifest.cases).length,'matching Python/JS family vectors + CRC32');
})().catch(e=>{console.error(e);process.exitCode=1;});

// TCAD 2.0 engine-observed fixture (not just a synthetic magic header).
const fsTCAD20=require('fs').readFileSync(__dirname+'/vectors/tcad20_two_parcels_real_engine.tcad');
const tcad20Result=core.sniff('two-parcels.tcad',fsTCAD20,fsTCAD20.length);
if(tcad20Result.identified!=='TCAD'||tcad20Result.confidence!=='text_prefix')throw new Error('TCAD 2.0 native fixture identity regression');
