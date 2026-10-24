/* TCB/TXB/TVW synthetic identity-only vectors, not canonical document fixtures */
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const core=require('./softcad-format-core.js'),gate=require('./softcad-tcb-txb-tvw-gate.js');
const root=path.join(__dirname,'interop_vectors'),m=JSON.parse(fs.readFileSync(path.join(root,'manifest.json')));
for(const [name,caseInfo] of Object.entries(m.cases)){
 const b=fs.readFileSync(path.join(root,name));
 assert.equal(crypto.createHash('sha256').update(b).digest('hex'),caseInfo.sha256,name);
 const result=gate.inspectBytes(name,b,b.length);
 assert.equal(result.status,caseInfo.status,name);
 assert.equal(result.format_authenticity,'UNVERIFIED',name);
 assert.equal(result.can_write,false,name);
 if(name==='dxb_legacy_collision.dxb'){
  const s=core.sniff(name,b,b.length);assert.equal(s.identified,null);assert.equal(s.confidence,'ambiguous_legacy_dxb');
 }
 if(name==='txbi_auxiliary.txbi'){
  const s=core.sniff(name,b,b.length);assert.equal(s.identified,null);assert.equal(s.confidence,'auxiliary_index');
 }
 if(name==='txb_legacy.txb'){
  const s=core.sniff(name,b,b.length);assert.equal(s.identified,'TXB');assert.equal(s.confidence,'legacy_signature');
 }
}
console.log('PASS: 20 synthetic TCB/TXB/TVW guardrail vectors (Node)');
