// Interfaccia della voce. Le scelte compositive restano nel motore Python.
inlets=1;outlets=4; // UDP, player, diagnostica, API del trasporto Live
var voiceId='', replyPort=9101, instance='', serial=0, acknowledged=-1;
var backendPort=9006, beat=0, playing=0, epoch=0, lastTick=-1;
var connected=false, lastReply=0, state=null, snapshot='', parameterNames=[], presetNames=[];
var selectedParameter=0, patch=this.patcher;
var lastTransportSerial=-1, backendSession='';
var presetDraft='';
// I payload variabili restano byte numerici, senza simboli Max per ogni JSON.
function utf8bytes(text){var binary=unescape(encodeURIComponent(text)), out=[];for(var i=0;i<binary.length;i++)out.push(binary.charCodeAt(i));return out;}
function utf8text(bytes){var binary='';for(var i=0;i<bytes.length;i++){if(bytes[i]<0||bytes[i]>255||Math.floor(bytes[i])!==bytes[i])throw new Error('byte non valido');binary+=String.fromCharCode(bytes[i]);}return decodeURIComponent(escape(binary));}
function status(text){outlet(2,String(text));}
function ui(name){return patch.getnamed(name);}
function playerReset(){outlet(1,'panic');}
function disconnect(){connected=false;state=null;snapshot='';playerReset();ui('role_display').message('set','Unassigned');ui('role_menu').message('clear');status('Disconnected');}
function voice(){var name=arrayfromargs(arguments).join(' ');if(name!==voiceId){disconnect();voiceId=name;}}
function receiveport(value){var n=Number(value);if(n!==replyPort){disconnect();replyPort=n;}}
function backendport(value){var n=Number(value);if(n!==backendPort){disconnect();backendPort=n;}}
function connect(){
    if(connected){request('hello',{});return;}
    disconnect();
    if(!/^[A-Za-z0-9_-]+$/.test(voiceId)){status('Enter a voice ID');return;}
    instance='device_'+new Date().getTime()+'_'+Math.floor(Math.random()*1000000000);
    serial=0;acknowledged=-1;lastTransportSerial=-1;backendSession='';lastReply=new Date().getTime();connected=true;request('hello',{});
}
function request(action, extra){
    if(!connected)return;
    var m={version:1,voice:voiceId,instance:instance,reply_port:replyPort,serial:++serial,action:action,capabilities:['transport_control'],transport:{beat:beat,playing:playing,epoch:epoch}};
    for(var key in extra)m[key]=extra[key];
    outlet(0,['/desnivel/v1/voice/control'].concat(utf8bytes(JSON.stringify(m))));
}
function clock(ticks,running){
    ticks=Number(ticks);running=Number(running);
    if(ticks<lastTick || running!==playing)epoch++;
    lastTick=ticks;beat=ticks/480;playing=running;
    if(connected)request('transport',{});
}
function heartbeat(){
    if(!connected)return;
    if(new Date().getTime()-lastReply>3000){playerReset();status('Python not responding');}
    request('hello',{});
}
function receive(){
    try{
        var m=JSON.parse(utf8text(arrayfromargs(arguments)));
        if(!connected || m.version!==1 || m.voice!==voiceId || m.instance!==instance)return;
        if(m.kind==='transport'){
            if(!backendSession||m.session!==backendSession)return;
            if(typeof m.serial!=='number'||!isFinite(m.serial)||Math.floor(m.serial)!==m.serial||m.serial<0||m.serial<=lastTransportSerial)return;
            if(m.action==='pause'){playerReset();outlet(3,'call','stop_playing');}
            else if(m.action==='resume')outlet(3,'call','continue_playing');
            else if(m.action==='restart'){
                playerReset();outlet(3,'call','stop_playing');
                outlet(3,'set','current_song_time',0);outlet(3,'call','continue_playing');
            }else return;
            lastTransportSerial=m.serial;return;
        }
        if(m.kind==='error'){reflectRole();status(m.error);return;}
        if(m.kind==='plan'){if(new Date().getTime()-lastReply>3000)return;outlet(1,['planbytes'].concat(utf8bytes(JSON.stringify(m.plan))));return;}
        if(m.kind!=='state' || m.serial<acknowledged)return;
        if(typeof m.session==='string' && m.session!==backendSession){backendSession=m.session;lastTransportSerial=-1;}
        acknowledged=m.serial;lastReply=new Date().getTime();
        var signature=JSON.stringify([m.role,m.role_mode,m.supported_roles,m.active,m.next_entry_progress,m.section_role,m.preset,m.presets,m.controls,m.can_save_presets,m.editable_presets]);
        if(signature!==snapshot){
            state=m;snapshot=signature;
            reflectRole();
            var previous=parameterNames[selectedParameter];
            presetNames=m.presets;parameterNames=[];
            ui('preset_menu').message('clear');
            for(var i=0;i<presetNames.length;i++)ui('preset_menu').message('append',presetNames[i]);
            if(m.preset!==null)ui('preset_menu').message('set',presetNames.indexOf(m.preset));
            else ui('preset_menu').message('set',-1);
            for(var key in m.controls)parameterNames.push(key);
            ui('parameter_menu').message('clear');
            for(var j=0;j<parameterNames.length;j++)ui('parameter_menu').message('append',parameterNames[j]);
            selectedParameter=Math.max(0,parameterNames.indexOf(previous));
            ui('parameter_menu').message('set',selectedParameter);parameter(selectedParameter);
        }
        status(m.notice||'Python connected');
    }catch(e){status('Invalid Python message: '+e);}
}
function reflectRole(){
    if(!state)return;
    var roles=state.supported_roles||[], menu=ui('role_menu');
    menu.message('clear');menu.message('append',roles.length?'Follow section':'No roles available');
    for(var i=0;i<roles.length;i++)menu.message('append',roles[i]);
    menu.message('set',state.role_mode==='manual'?roles.indexOf(state.role)+1:0);
    var activity='';
    if(state.active===false)activity=state.next_entry_progress!==null && state.next_entry_progress!==undefined
        ?' (enters at '+Math.round(state.next_entry_progress*100)+'%)':' (not in this section)';
    ui('role_display').message('set',(state.role||'Unassigned')+activity);
}
function choose_role(index){
    if(!state)return;
    var roles=state.supported_roles||[];
    if(!roles.length)return;
    if(index===0)request('role',{role:null});
    else if(roles[index-1]!==undefined)request('role',{role:roles[index-1]});
}
function preset(index){
    if(state && presetNames[index]!==undefined){
        presetDraft=presetNames[index];ui('preset_name').message('set',presetDraft);
        request('preset',{preset:presetDraft});
    }
}
function preset_name(){presetDraft=arrayfromargs(arguments).join(' ').replace(/^\s+|\s+$/g,'');}
function save_preset(overwrite){
    if(!state || !state.can_save_presets){status('Preset library unavailable');return;}
    if(!presetDraft){status('Enter a preset name');return;}
    request('save_preset',{preset:presetDraft,overwrite:!!overwrite});
}
function parameter(index){
    selectedParameter=Number(index);
    var name=parameterNames[selectedParameter];
    if(state && name!==undefined){
        var c=state.controls[name];ui('parameter_value').message('set',c.value);
        ui('parameter_slider').message('set',c.maximum===c.minimum?0:Math.round((c.value-c.minimum)/(c.maximum-c.minimum)*1000));
        ui('range_display').message('set',c.minimum+' .. '+c.maximum+(c.integer?' (integer)':''));
    }else ui('range_display').message('set','No controls');
}
function slidervalue(v){
    var name=parameterNames[selectedParameter];
    if(!state || name===undefined)return;
    var c=state.controls[name], fraction=Math.max(0,Math.min(1000,Number(v)))/1000;
    var n=c.minimum+fraction*(c.maximum-c.minimum);
    if(c.integer)n=Math.round(n);
    else n=Math.round(n*1000000)/1000000;
    ui('parameter_value').message('set',n);
    value(n);
}
function value(v){
    var name=parameterNames[selectedParameter];
    if(!state || name===undefined)return;
    var c=state.controls[name], n=Number(v);
    if(!isFinite(n)||n<c.minimum||n>c.maximum||(c.integer&&Math.floor(n)!==n)){
        ui('parameter_value').message('set',c.value);status('Value outside allowed range');return;
    }
    request('parameter',{parameter:name,value:n});
}
function panic(){playerReset();request('panic',{});}
function notifydeleted(){playerReset();}
