const vm=require('vm'), fs=require('fs'), assert=require('assert');
let all=[],edges=[],midi=[],log=[],flushes=0;
const output={kind:'output'}, flush={message:()=>flushes++};
const patch={
 getnamed:n=>n==='notes_unpack'?output:flush,
 newdefault:(x,y,kind,...args)=>{let o={kind,args,alive:true,message(...values){input(this,0,values.length===1?values[0]:values);}};all.push(o);return o;},
 connect:(a,ao,b,bi)=>edges.push([a,ao,b,bi]),
 remove:o=>{o.alive=false;edges=edges.filter(e=>e[0]!==o&&e[2]!==o);}
};
function emit(o,index,value){for(const e of edges.filter(e=>e[0]===o&&e[1]===index))input(e[2],e[3],value);}
function input(o,inlet,value){
 if(o===output){midi.push(value);return;}
 if(o.kind==='gate'){if(inlet===0)o.args[1]=value;else if(o.args[1])emit(o,0,value);}
 else if(o.kind==='t'){for(let i=o.args.length-1;i>=0;i--)emit(o,i,o.args[i]==='b'?'bang':value);}
 else if(o.kind==='timepoint')o.args[0]=Number(value);
 else if(o.kind==='zl'){
  if(o.args[0]==='iter'){for(let i=0;i<value.length;i+=o.args[1])emit(o,0,value.slice(i,i+o.args[1]));}
  else if(o.args[0]==='reg'){if(inlet===1)o.stored=value;else emit(o,0,o.stored);}
  else throw Error('modalità zl non simulata');
 }
 else if(o.kind==='int')emit(o,0,o.args[0]);
 else if(o.kind==='pack')emit(o,0,o.args);
 else throw Error('mock object '+o.kind);
}
const c={patcher:patch,outlet:(...args)=>log.push(args),arrayfromargs:a=>Array.from(a)};
vm.createContext(c);vm.runInContext(fs.readFileSync('m4l/desnivel_transport_player.js','utf8'),c);
function send(start,revision,serial,pitch=36,session='s'){
 c.plan(JSON.stringify({version:1,session,serial,start,revision,phrase:{length_beats:4,notes:[{beat:0,pitch,duration:1,velocity:90}]}}));
}
c.clock(0,1);send(4,1,1);
let on=all.find(o=>o.kind==='timepoint'&&o.args[0]===1920&&o.alive);
assert(on);assert.deepStrictEqual(midi,[]);
let count=all.length;send(4,1,2);assert.equal(all.length,count); // no restart/rebuild
emit(on,0,'bang');assert.deepStrictEqual(midi,[[36,90]]);
emit(on,0,'bang');assert.equal(midi.length,1); // one shot, including transport loop
c.now(2000);
let off=all.find(o=>o.kind==='timepoint'&&o.args[0]===2400&&o.alive);
send(8,2,3,38);assert(off.alive); // adding a future window preserves the active note-off
emit(off,0,'bang');assert.deepStrictEqual(midi[1],[36,0]);
send(8,3,4,40);assert.equal(c.plans['8'].phrase.notes[0].pitch,40);
send(8,2,3,38);assert.equal(c.plans['8'].phrase.notes[0].pitch,40);
c.plan(JSON.stringify({version:1,session:'s2',serial:5,reset:true}));assert(flushes>0);
send(12,8,99,45,'s');assert.equal(Object.keys(c.plans).length,0); // retired session
c.clock(0,1);send(4,1,6,36,'s2');assert.equal(Object.keys(c.plans).length,1);
c.running(0);assert.equal(Object.keys(c.plans).length,0);
console.log('OK: future timing, duplicate/reordered UDP, native note-off retained, one-shot, stop, sessions');

// Una sessione lunga riutilizza gli oggetti, senza nuovi nomi a ogni finestra.
c.plan(JSON.stringify({version:1,session:'stress',serial:0,reset:true}));
let plateau=0;
for(let i=1;i<=1000;i++){
 c.clock((i*4-2)*480,1);send(i*4,i,i,36,'stress');
 if(i===10)plateau=all.length;
 if(i>10)assert.equal(all.length,plateau);
 assert(Object.keys(c.plans).length<=2);
 assert(Object.keys(c.groups).length<=4);
}
c.running(0);assert.equal(Object.keys(c.groups).length,0);
assert(c.pool.every(g=>g.gate.args[1]===0));
c.notifydeleted();assert(all.every(o=>!o.alive));
console.log('OK: 1000 finestre, oggetti stabili dopo il riscaldamento, piani limitati e pulizia finale');
// Riattacco della stessa nota: note-off e note-on mantengono l'ordine nativo.
c.clock(0,1);
c.planbytes(...Buffer.from(JSON.stringify({version:1,session:'ordered',serial:1,start:4,revision:1,
 phrase:{length_beats:4,notes:[{beat:0,pitch:60,duration:4,velocity:90}]}})));
c.planbytes(...Buffer.from(JSON.stringify({version:1,session:'ordered',serial:2,start:8,revision:2,
 phrase:{length_beats:4,notes:[{beat:0,pitch:60,duration:1,velocity:70}]}})));
const boundary=all.find(o=>o.kind==='timepoint'&&o.args[0]===8*480&&o.alive);
const previousMidi=midi.length;
emit(boundary,0,'bang');
assert.deepStrictEqual(midi.slice(previousMidi),[[60,0],[60,70]]);
console.log('OK: piano a byte e note-off prima del riattacco allo stesso tick');
