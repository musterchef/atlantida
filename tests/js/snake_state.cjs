const vm=require('vm'),fs=require('fs'),assert=require('assert');
let out=[],controls={},lengths={};
for(let i=1;i<=16;i++){
 const s=String(i).padStart(2,'0');controls['desnivel_pitch_'+s]=60+i-1;
 controls['Gate_'+s]=1;controls['Velocity_'+s]=90;lengths['Length_'+s]=64;
}
lengths.Length_Min_ms=50;lengths.Length_Max_ms=500;controls.swing=0;
for(const bank of ['Notes','Gates','Velocities']){
 const pre=bank+'_Sequencer_';controls[pre+'Speed']=1;controls[pre+'Direction']=0;
 controls[pre+'Length']=16;controls[pre+'Steps_Shift']=0;controls[pre+'Snake_Shape']=0;
}
for(const lane of ['notes','gates','velocities'])controls['desnivel_shift_'+lane]=1;
const wrap=data=>({getnamed:n=>n in data?{getvalueof:()=>[data[n]]}:null});
const c={patcher:{getnamed:n=>({subpatcher:()=>wrap(n==='Length_Bank'?lengths:controls)})},
 outlet:(...a)=>out.push(a),post:()=>{}};
vm.createContext(c);vm.runInContext(fs.readFileSync('m4l/desnivel_snake_state.js','utf8'),c);
for(const name of ['notes','gates','velocities'])c.phase(name,4,480);
c.snapshot(540,120,1);
let p=JSON.parse(out.pop()[2]);assert(!p.error,p.error);
assert.equal(p.state.notes[0],60);assert.equal(p.state.notes_lane.phase_beats,1.125);
assert.equal(p.state.lengths_ms[0],50+64/127*450);
controls.Notes_Sequencer_Direction=1;c.phase('notes',11,480);c.snapshot(540,120,1);
p=JSON.parse(out.pop()[2]);assert.equal(p.state.notes_lane.phase_beats,1.125);
controls.desnivel_shift_notes=2;c.snapshot(540,120,1);
p=JSON.parse(out.pop()[2]);assert(p.error.includes('Shift'));
c.snapshot(540,120,0);p=JSON.parse(out.pop()[2]);assert.equal(p.playing,0);assert.equal(Object.keys(c.phases).length,0);
console.log('OK: pitch reale, fase osservata, durata, stato non supportato, stop');
