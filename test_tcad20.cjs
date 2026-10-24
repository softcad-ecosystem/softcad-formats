const fs=require('fs'),assert=require('assert');
const tcad=require('./softcad-tcad20.js');
const fixture=fs.readFileSync(__dirname+'/vectors/tcad20_two_parcels_real_engine.tcad');
const text=fixture.toString('utf8');
const cases={
 valid:fixture,
 crlf:Buffer.from(text.replace(/\n/g,'\r\n')),
 old_version:Buffer.from(text.replace('TCAD 2.0','TCAD 1.2')),
 wrong_crs_label:Buffer.from(text.replace('  crs:','  bogus:')),
 duplicate_parcel_id:Buffer.from(text.replace('parcel P002','parcel P001')),
 missing_ring:Buffer.from(text.replace('  ring:','  unknown:')),
 bad_ring:Buffer.from(text.replace('40.0000,20.0000','40.0000,BAD')),
 unclosed_ring:Buffer.from(text.replace('35.0000,20.0000\n\n','30.0000,20.0000\n\n')),
 bad_area:Buffer.from(text.replace('area:       200.0','area:       -1.0')),
 unknown_section:Buffer.from(text+'building XX\n'),
 invalid_utf8:Buffer.concat([fixture,Buffer.from([255])]),
 huge:Buffer.concat([fixture,Buffer.alloc(8*1024*1024-fixture.length+1,32)]),
};
for(const [name,blob] of Object.entries(cases)){
 const value=tcad.parseBytes(blob);
 assert.equal(value.verified_subset, ['valid','crlf'].includes(name), name+JSON.stringify(value));
 if(name==='valid'){assert.equal(value.parcel_count,2);assert.equal(value.crs,'EPSG:3844');assert.equal(value.sum_reported_area,235);}
 console.log('PASS',name,value.reason||'verified_subset');
}
console.log('TCAD 2.0 JS probes:',Object.keys(cases).length,'PASS');
