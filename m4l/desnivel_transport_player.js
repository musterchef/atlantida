// Piani assoluti: gli attacchi sono eseguiti da timepoint nativi, non da JS.
inlets=1;outlets=1;
var plans={}, groups={}, nodes=[], nodeSerial=0, nowTicks=0, lastTick=-1, playing=0, session=null, lastError='';
var patch=this.patcher, retired={}, lastSerial=-1, pool=[];
function status(s) {outlet(0,s);}
function removeGroup(g) {g.gate.message(0);pool.push(g);}
function removeNodes() {for(var key in groups)removeGroup(groups[key]);groups={};nodes=[];}
function object() {
    var args=arrayfromargs(arguments), o=patch.newdefault.apply(patch,[800,600].concat(args));
    o.varname='desnivel_runtime_'+(++nodeSerial);nodes.push(o);return o;
}
function flush() {var f=patch.getnamed('notes_flush');if(f)f.message('bang');}
function clear() {removeNodes();plans={};flush();}
function clock(ticks, running) {
    ticks=Number(ticks);running=Number(running);
    if(ticks<lastTick || (!running && playing))clear();
    nowTicks=ticks;lastTick=ticks;playing=running;
}
function running(v) {if(!Number(v))clear();playing=Number(v);}
function now(ticks) {nowTicks=Number(ticks);}
function compile() {
    var events={};
    for(var key in plans) {
        var p=plans[key];
        if((p.start+p.phrase.length_beats)*480<nowTicks){delete plans[key];continue;}
        for(var j=0;j<p.phrase.notes.length;j++) {
            var n=p.phrase.notes[j], on=Math.round((p.start+n.beat)*480), off=Math.round((p.start+n.beat+n.duration)*480);
            if(off<=on)throw new Error('durata inferiore alla risoluzione di un tick');
            if(on>nowTicks){if(!events[on])events[on]=[];events[on].push([n.pitch,n.velocity]);}
            if(off>nowTicks){if(!events[off])events[off]=[];events[off].push([n.pitch,0]);}
        }
    }
    for(var old in groups)if(!events[old]){removeGroup(groups[old]);delete groups[old];}
    var output=patch.getnamed('notes_unpack');
    for(var tick in events) {
        var values=events[tick];values.sort(function(a,b){return a[1]-b[1] || a[0]-b[0];});
        var signature=JSON.stringify(values);
        if(groups[tick] && groups[tick].signature===signature)continue;
        if(groups[tick])removeGroup(groups[tick]);
        var g=pool.pop();
        if(!g){
            nodes=[];
            var tp=object('timepoint',0), gate=object('gate',1,0);
            var close=object('t','b','b'), zero=object('int',0);
            var input=object('t','l'), memory=object('zl','reg','@zlmaxsize',512), pairs=object('zl','iter',2,'@zlmaxsize',512);
            patch.connect(tp,0,gate,1);patch.connect(gate,0,close,0);
            patch.connect(close,1,zero,0);patch.connect(zero,0,gate,0);
            patch.connect(close,0,memory,0);patch.connect(input,0,memory,1);
            patch.connect(memory,0,pairs,0);patch.connect(pairs,0,output,0);
            g={nodes:nodes,tp:tp,gate:gate,input:input};
        }
        var flat=[];for(var z=0;z<values.length;z++)flat.push(values[z][0],values[z][1]);
        g.gate.message(0);
        g.input.message.apply(g.input,flat);
        g.tp.message(Number(tick));
        g.signature=signature;g.gate.message(1);groups[tick]=g;
    }
}
function planbytes(){
    try{var bytes=arrayfromargs(arguments), binary='';for(var i=0;i<bytes.length;i++){
        if(bytes[i]<0||bytes[i]>255||Math.floor(bytes[i])!==bytes[i])throw new Error('byte non valido');
        binary+=String.fromCharCode(bytes[i]);
    }plan(decodeURIComponent(escape(binary)));}catch(e){status(String(e));}
}
function plan(text) {
    try {
        var p=JSON.parse(String(text));
        if(p.version!==1 || typeof p.session!=='string')throw new Error('protocollo non valido');
        if(!isFinite(p.serial) || Math.floor(p.serial)!==p.serial)throw new Error('seriale non valido');
        if(retired[p.session] || (session===p.session && p.serial<=lastSerial))return;
        if(p.reset){if(session && session!==p.session)retired[session]=true;clear();session=p.session;lastSerial=p.serial;status('reset');return;}
        if(!isFinite(p.start) || p.start<0 || !p.phrase || !isFinite(p.phrase.length_beats) || p.phrase.length_beats<=0 || !(p.phrase.notes instanceof Array))throw new Error('finestra non valida');
        if(!isFinite(p.revision) || Math.floor(p.revision)!==p.revision)throw new Error('revisione non valida');
        if(p.start*480<=nowTicks+24)throw new Error('piano arrivato tardi');
        var ends={};
        p.phrase.notes.sort(function(a,b){return a.beat-b.beat;});
        for(var i=0;i<p.phrase.notes.length;i++) {
            var n=p.phrase.notes[i];
            if(!isFinite(n.beat)||n.beat<0||!isFinite(n.duration)||n.duration<=0||n.beat+n.duration>p.phrase.length_beats ||
                Math.floor(n.pitch)!==n.pitch||n.pitch<0||n.pitch>127||Math.floor(n.velocity)!==n.velocity||n.velocity<1||n.velocity>127 ||
                n.beat<(ends[n.pitch]||0))throw new Error('nota non valida');
            if(Math.round((p.start+n.beat+n.duration)*480)<=Math.round((p.start+n.beat)*480))throw new Error('durata inferiore a un tick');
            ends[n.pitch]=n.beat+n.duration;
        }
        if(session!==p.session){if(session)retired[session]=true;clear();session=p.session;}
        lastSerial=p.serial;
        var key=String(p.start), previous=plans[key];
        if(previous && previous.revision>=p.revision)return;
        for(var other in plans)if(other!==key && p.start<plans[other].start+plans[other].phrase.length_beats && plans[other].start<p.start+p.phrase.length_beats)throw new Error('finestre sovrapposte');
        plans[key]=p;compile();status('pronto');
    }catch(e){var msg=String(e);if(msg!==lastError){status(msg);lastError=msg;}}
}
function panic(){clear();status('stop');}
function notifydeleted(){clear();for(var i=0;i<pool.length;i++)for(var j=0;j<pool[i].nodes.length;j++)patch.remove(pool[i].nodes[j]);pool=[];}

function loadbang() {
    groups={};plans={};pool=[];nodes=[];
    var o=patch.firstobject;
    while(o){var next=o.nextobject;if(String(o.varname).indexOf('desnivel_runtime_')===0)patch.remove(o);o=next;}
}
