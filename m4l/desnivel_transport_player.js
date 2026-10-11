// Piani assoluti: gli attacchi sono eseguiti da timepoint nativi, non da JS.
inlets=1;outlets=1;
var plans={}, groups={}, nodes=[], nodeSerial=0, nowTicks=0, lastTick=-1, playing=0, session=null, lastError='';
var patch=this.patcher, retired={}, lastSerial=-1;
function status(s) {outlet(0,s);}
function removeGroup(g) {for(var i=0;i<g.nodes.length;i++)patch.remove(g.nodes[i]);}
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
        nodes=[];
        var tp=object('timepoint',Number(tick)), gate=object('gate',1,1);
        var close=object('t','b','b'), zero=object('int',0);
        var spec=['t'];for(var k=0;k<values.length;k++)spec.push('b');
        var trigger=object.apply(null,spec);
        patch.connect(tp,0,gate,1);patch.connect(gate,0,close,0);
        patch.connect(close,1,zero,0);patch.connect(zero,0,gate,0);
        patch.connect(close,0,trigger,0);
        for(var z=0;z<values.length;z++) {
            var msg=object('pack',values[z][0],values[z][1]);
            patch.connect(trigger,values.length-1-z,msg,0);patch.connect(msg,0,output,0);
        }
        groups[tick]={signature:signature,nodes:nodes};
    }
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
        plans[key]=p;compile();status('pronto beat '+p.start);
    }catch(e){var msg=String(e);if(msg!==lastError){status(msg);lastError=msg;}}
}
function panic(){clear();status('stop');}
function notifydeleted(){clear();}

function loadbang() {
    var o=patch.firstobject;
    while(o){var next=o.nextobject;if(String(o.varname).indexOf('desnivel_runtime_')===0)patch.remove(o);o=next;}
}
