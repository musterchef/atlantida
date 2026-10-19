const vm=require('vm'),fs=require('fs'),assert=require('assert');
let output=[],uiMessages={};
const patch={getnamed:name=>({message:(...a)=>(uiMessages[name]??=[]).push(a)})};
const c={patcher:patch,outlet:(...a)=>output.push(a),arrayfromargs:a=>Array.from(a)};
vm.createContext(c);vm.runInContext(fs.readFileSync('m4l/desnivel_voice.js','utf8'),c);
c.voice('part_a');c.receiveport(9101);c.connect();
let hello=JSON.parse(output.find(a=>a[0]===0)[2]);
assert.equal(hello.voice,'part_a');assert.equal(hello.reply_port,9101);
const state={version:1,kind:'state',voice:'part_a',instance:c.instance,serial:1,
 role:'melody',preset:null,presets:['soft'],controls:{velocity:{minimum:1,maximum:127,integer:true,value:80}}};
c.receive(JSON.stringify({...state,instance:'other'}));assert.equal(c.state,null);
c.receive(JSON.stringify(state));assert.equal(c.state.role,'melody');
// Connect ripetuto conserva identità, seriali e note già pianificate.
const identity=c.instance, beforeSerial=c.serial;
const panics=output.filter(a=>a[0]===1&&a[1]==='panic').length;
c.connect();
const reconnect=JSON.parse(output.at(-1)[2]);
assert.equal(reconnect.instance,identity);assert(reconnect.serial>beforeSerial);
assert.equal(output.filter(a=>a[0]===1&&a[1]==='panic').length,panics);
c.receive(JSON.stringify({...state,serial:2,supported_roles:['melody','sustained_texture'],role_mode:'section',active:true}));
c.receive(JSON.stringify({...state,serial:2,supported_roles:['melody'],role_mode:'section',active:false,next_entry_progress:.3}));
assert(uiMessages.role_display.at(-1)[1].includes('enters at 30%'));
c.receive(JSON.stringify({...state,serial:2,supported_roles:['melody','sustained_texture'],role_mode:'section',active:true,next_entry_progress:null}));
c.choose_role(2);assert.equal(JSON.parse(output.at(-1)[2]).role,'sustained_texture');
c.receive(JSON.stringify({...state,serial:3,supported_roles:['melody','sustained_texture'],role:'sustained_texture',role_mode:'manual',active:true}));
assert.deepStrictEqual(uiMessages.role_menu.at(-1),['set',2]);
c.choose_role(0);assert.equal(JSON.parse(output.at(-1)[2]).role,null);
c.receive(JSON.stringify({version:1,kind:'error',voice:'part_a',instance:c.instance,error:'unsupported'}));
assert.deepStrictEqual(uiMessages.role_menu.at(-1),['set',2]); // Ripristina la scelta confermata.
c.preset(0);assert.equal(JSON.parse(output.at(-1)[2]).preset,'soft');
c.value(50);assert.equal(JSON.parse(output.at(-1)[2]).value,50);
let count=output.filter(a=>a[0]===0).length;c.value(999);
assert.equal(output.filter(a=>a[0]===0).length,count);
let plan={version:1,kind:'plan',voice:'part_a',instance:c.instance,plan:{version:1,reset:true}};
c.receive(JSON.stringify({...plan,voice:'part_b'}));assert.notEqual(output.at(-1)[1],'plan');
c.receive(JSON.stringify(plan));assert.equal(output.at(-1)[1],'plan');
c.lastReply=0;c.heartbeat();assert(output.some(a=>a[0]===1&&a[1]==='panic'));
c.disconnect();assert(!c.connected);c.receive(JSON.stringify(plan));assert.notEqual(output.at(-1)[1],'plan');
console.log('OK: identity, menus, validated values, plan routing, timeout and disconnect');
