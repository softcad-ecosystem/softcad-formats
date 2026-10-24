'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,vectors=path.join(root,'cgb_vectors');
const cgb=require('./softcad-cgb1.js');
const m=JSON.parse(fs.readFileSync(path.join(vectors,'cgb_cases.json'),'utf8'));
for(const [name,e] of Object.entries(m.cases)){
 const b=fs.readFileSync(path.join(vectors,name));
 assert.equal(crypto.createHash('sha256').update(b).digest('hex'),e.sha256,name);
 const r=cgb.parseBytes(b);
 for(const k of ['checked','verified_subset','reason'])assert.deepEqual(r[k],e[k],name+' '+k);
}
assert.equal(cgb.parseBytes(fs.readFileSync(path.join(vectors,'tampered_record_content.cgb'))).verified_subset,true);
console.log('PASS CGB1 cross-language native/subset vectors:',Object.keys(m.cases).length);
