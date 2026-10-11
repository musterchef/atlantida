const vm=require('vm'),fs=require('fs'),assert=require('assert');
let writes=[],logs=[],params=Array.from({length:171},(_,i)=>({name:'p'+i,min:0,max:127,value:0}));
params[12]={name:'Gate_Shape',min:0,max:13,value:0};
params[90]={name:'Shapes',min:0,max:13,value:0};
function LiveAPI(cb,path){
 this.getcount=kind=>kind==='parameters'?params.length:1;
 this.get=key=>path.includes(' parameters ')?[params[Number(path.split(' parameters ')[1])][key]]:['MDD_Snake'];
 this.set=(key,v)=>{let i=Number(path.split(' parameters ')[1]);params[i][key]=v;writes.push([i,v]);};
}
const c={LiveAPI,post:s=>logs.push(s)};vm.createContext(c);
vm.runInContext(fs.readFileSync('m4l/desnivel_snake_params.js','utf8'),c);
c.set('gate_shape',13);assert.deepStrictEqual(writes,[[12,13]]);
[params[12],params[160]]=[params[160],params[12]];
c.set('gate_shape',5);assert.deepStrictEqual(writes[1],[160,5]);
c.set('gate_shape',14);assert.equal(writes.length,2);
params[160].name='Other';c.set('gate_shape',6);assert.equal(writes.length,2);
console.log('OK: Shape Gates risolta per nome dopo riordino; nessuna scrittura indice 90 sulle mod');
