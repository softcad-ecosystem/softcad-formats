/* Node cross-check: RC1 commit ancestry, Python parity and read-only fixtures. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),cp=require('node:child_process');
const crypto=require('node:crypto'),api=require('./softcad-tdb3-history.js');
const base=__dirname;
const current=JSON.parse(fs.readFileSync(path.join(base,'vectors/tdb3_history_manifest.json'),'utf8')).cases;
const old=JSON.parse(fs.readFileSync(path.join(base,'vectors/real_rc1_manifest.json'),'utf8')).cases;
(async()=>{
  let count=0;
  for(const [name,meta] of Object.entries(current)){
    const buf=fs.readFileSync(path.join(base,'vectors',name));
    assert.equal(crypto.createHash('sha256').update(buf).digest('hex'),meta.sha256,name);
    const report=await api.inspect(new Blob([buf]));
    assert.equal(report.reason,meta.reason,name);
    assert.equal(report.commit_count,meta.commit_count,name);
    assert.equal(report.verified,meta.verified,name);
    const py=cp.spawnSync(process.env.SOFTCAD_PYTHON||'python',['tdb3_commit_chain.py',path.join('vectors',name)],{cwd:base,encoding:'utf8'});
    assert.equal(py.status,0,py.stderr);
    const p=JSON.parse(py.stdout);
    for(const key of ['reason','commit_count','verified','complete','checked','commits'])assert.deepEqual(report[key],p[key],name+': '+key);
    count++;
  }
  for(const [name,meta] of Object.entries(old)){
    const report=await api.inspect(new Blob([fs.readFileSync(path.join(base,'vectors',name))]));
    if(meta.root_sha256_valid){assert.equal(report.verified,true,name);assert.equal(report.complete,true,name);}
    else assert.equal(report.reason,'history_root_not_verified',name);
    count++;
  }
  console.log('PASS: '+count+' real RC1 fixtures with Python/Node parity, including parent-corruption cases');
})().catch(e=>{console.error(e);process.exitCode=1});
