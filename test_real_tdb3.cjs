/* Node.js v20+: real RC1 root check and Python/JS parity. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),hash=require('node:crypto');
const impl=require('./softcad-tdb3-root.js');
const cases=JSON.parse(fs.readFileSync(path.join(__dirname,'vectors/real_rc1_manifest.json'),'utf8')).cases;
(async()=>{
 let count=0;
 for(const [name,expected] of Object.entries(cases)){
   const b=fs.readFileSync(path.join(__dirname,'vectors',name));
   assert.equal(hash.createHash('sha256').update(b).digest('hex'),expected.sha256,name);
   const report=await impl.inspect(new Blob([b]));
   assert.equal(report.verified,expected.root_sha256_valid,name);
   assert.equal(report.reason,expected.reason,name);
   if(expected.active_sequence!==null)assert.equal(report.active_sequence,expected.active_sequence,name);
   if(name==='tdb3_real_uncommitted_tail.tdb3')assert.ok(report.uncommitted_tail_bytes>0,name);
   if(name==='tdb3_real_recover_older_slot.tdb3')assert.equal(report.active_sequence,'1',name);
   if(name==='tdb3_real_zlib_root.tdb3')assert.equal(report.chunk_codec,1,name);
   count++;
 }
 console.log('PASS: '+count+' real RC1 samples, SHA check, root fallback and zlib parity');
})().catch(err=>{console.error(err);process.exitCode=1;});
