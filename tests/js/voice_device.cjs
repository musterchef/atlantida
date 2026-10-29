const vm=require('vm'),fs=require('fs'),assert=require('assert');
let output=[],uiMessages={};
const patch={getnamed:name=>({message:(...a)=>(uiMessages[name]??=[]).push(a)})};
const c={patcher:patch,outlet:(...a)=>output.push(a),arrayfromargs:a=>Array.from(a)};
vm.createContext(c);vm.runInContext(fs.readFileSync('m4l/desnivel_voice.js','utf8'),c);
function packet(message){return [...Buffer.from(JSON.stringify(message),'utf8')];}
function control(entry){
 assert.equal(entry[1][0],'/desnivel/v1/voice/control');
 const bytes=Array.from(entry[1]).slice(1);assert(bytes.every(n=>Number.isInteger(n)&&n>=0&&n<=255));
 return JSON.parse(Buffer.from(bytes).toString('utf8'));
}
// Il test usa oggetti leggibili; il confine Max riceve soltanto byte.
const receiveBytes=c.receive;
c.receive=text=>receiveBytes.apply(c,packet(JSON.parse(text)));
c.voice('part_a');c.receiveport(9101);c.connect();
let hello=control(output.find(a=>a[0]===0));
assert.equal(hello.voice,'part_a');assert.equal(hello.reply_port,9101);
const state={version:1,kind:'state',voice:'part_a',instance:c.instance,serial:1,session:'python-1',
 role:'melody',preset:null,presets:['soft'],controls:{velocity:{minimum:1,maximum:127,integer:true,value:80}}};
c.receive(JSON.stringify({...state,instance:'other'}));assert.equal(c.state,null);
c.receive(JSON.stringify(state));assert.equal(c.state.role,'melody');
// Connect ripetuto conserva identità, seriali e note già pianificate.
const identity=c.instance, beforeSerial=c.serial;
const panics=output.filter(a=>a[0]===1&&a[1]==='panic').length;
c.connect();
const reconnect=control(output.at(-1));
assert.equal(reconnect.instance,identity);assert(reconnect.serial>beforeSerial);
assert.equal(output.filter(a=>a[0]===1&&a[1]==='panic').length,panics);
c.receive(JSON.stringify({...state,serial:2,supported_roles:['melody','sustained_texture'],role_mode:'section',active:true}));
c.receive(JSON.stringify({...state,serial:2,supported_roles:['melody'],role_mode:'section',active:false,next_entry_progress:.3}));
assert(uiMessages.role_display.at(-1)[1].includes('enters at 30%'));
c.receive(JSON.stringify({...state,serial:2,supported_roles:['melody','sustained_texture'],role_mode:'section',active:true,next_entry_progress:null}));
c.choose_role(2);assert.equal(control(output.at(-1)).role,'sustained_texture');
c.receive(JSON.stringify({...state,serial:3,supported_roles:['melody','sustained_texture'],role:'sustained_texture',role_mode:'manual',active:true}));
assert.deepStrictEqual(uiMessages.role_menu.at(-1),['set',2]);
c.choose_role(0);assert.equal(control(output.at(-1)).role,null);
c.receive(JSON.stringify({version:1,kind:'error',voice:'part_a',instance:c.instance,error:'unsupported'}));
assert.deepStrictEqual(uiMessages.role_menu.at(-1),['set',2]); // Ripristina la scelta confermata.
c.preset(0);assert.equal(control(output.at(-1)).preset,'soft');
c.value(50);assert.equal(control(output.at(-1)).value,50);
c.receive(JSON.stringify({...state,serial:4,can_save_presets:true,editable_presets:[]}));
c.preset_name('my','groove');c.save_preset(0);
assert.equal(control(output.at(-1)).preset,'my groove');
assert.equal(control(output.at(-1)).overwrite,false);
c.save_preset(1);assert.equal(control(output.at(-1)).overwrite,true);
c.slidervalue(500);assert.equal(control(output.at(-1)).value,64);
c.slidervalue(0);assert.equal(control(output.at(-1)).value,1);
c.slidervalue(1000);assert.equal(control(output.at(-1)).value,127);
let count=output.filter(a=>a[0]===0).length;c.value(999);
assert.equal(output.filter(a=>a[0]===0).length,count);
let plan={version:1,kind:'plan',voice:'part_a',instance:c.instance,plan:{version:1,reset:true}};
c.receive(JSON.stringify({...plan,voice:'part_b'}));assert.notEqual(output.at(-1)[1][0],'planbytes');
c.receive(JSON.stringify(plan));assert.equal(output.at(-1)[1][0],'planbytes');
const liveCommand={version:1,kind:'transport',voice:'part_a',instance:c.instance,session:'python-1',serial:100,action:'restart'};
c.receive(JSON.stringify(liveCommand));
assert.deepStrictEqual(output.filter(a=>a[0]===3).slice(-3),[
 [3,'call','stop_playing'],[3,'set','current_song_time',0],[3,'call','continue_playing']]);
const liveCount=output.filter(a=>a[0]===3).length;
c.receive(JSON.stringify(liveCommand));assert.equal(output.filter(a=>a[0]===3).length,liveCount);
c.receive(JSON.stringify({...liveCommand,serial:101,action:'pause'}));
assert.deepStrictEqual(output.at(-1),[3,'call','stop_playing']);
c.receive(JSON.stringify({...state,serial:5,session:'python-2'}));
c.receive(JSON.stringify({...liveCommand,session:'python-2',serial:1,action:'resume'}));
assert.deepStrictEqual(output.at(-1),[3,'call','continue_playing']);
const afterNewSession=output.filter(a=>a[0]===3).length;
c.receive(JSON.stringify({...liveCommand,serial:102,action:'pause'}));
assert.equal(output.filter(a=>a[0]===3).length,afterNewSession);
c.lastReply=0;c.heartbeat();assert(output.some(a=>a[0]===1&&a[1]==='panic'));
c.disconnect();assert(!c.connected);c.receive(JSON.stringify(plan));assert.notEqual(output.at(-1)[1][0],'planbytes');
console.log('OK: identity, menus, validated values, plan routing, timeout and disconnect');

c.connect();
for(let i=0;i<1000;i++)c.clock(i*60,1);
const controls=output.filter(a=>a[0]===0);
assert(controls.every(entry=>entry[1][0]==='/desnivel/v1/voice/control'&&Array.from(entry[1]).slice(1).every(Number.isInteger)));
assert.equal(control(controls.at(-1)).transport.beat,999*60/480);
console.log('OK: 1000 clock con payload numerico, senza JSON come simboli Max');
