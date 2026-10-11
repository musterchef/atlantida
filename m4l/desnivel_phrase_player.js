// JS prepara eventi; pipe in ticks li esegue. Nessun polling.
// Out 0: pitch velocity ritardo_ticks; out 1: clear/flush; out 2: diagnostica.
inlets = 1;
outlets = 3;
var active = null, pending = null, playing = 0, scheduled = false;
var PPQ = 480; // unità ticks Max: una semiminima = 480 ticks

function phrase() {
    var a = arrayfromargs(arguments), notes = [], ends = {};
    if (a[0] !== 1 || !isFinite(a[1]) || a[1] <= 0 ||
        a[2] < 0 || a[2] > 32 || Math.floor(a[2]) !== a[2] || a.length !== 3 + 4*a[2]) {
        outlet(2, 'error', 'invalid_header'); return;
    }
    for (var i = 3; i < a.length; i += 4) {
        var n = {beat:a[i], pitch:a[i+1], duration:a[i+2], velocity:a[i+3], id:i};
        if (!isFinite(n.beat) || !isFinite(n.duration) || n.beat < 0 || n.duration <= 0 ||
            n.beat+n.duration > a[1] || Math.floor(n.pitch) !== n.pitch || n.pitch < 0 || n.pitch > 127 ||
            Math.floor(n.velocity) !== n.velocity || n.velocity < 1 || n.velocity > 127) {
            outlet(2, 'error', 'invalid_note'); return;
        }
        notes.push(n);
    }
    notes.sort(function(x,y) {return x.beat-y.beat;});
    for (var j=0; j<notes.length; j++) {
        var v=notes[j];
        if (v.beat < (ends[v.pitch] || 0)) {outlet(2,'error','overlap'); return;}
        ends[v.pitch]=v.beat+v.duration;
    }
    pending = {length:a[1], notes:notes};
    outlet(2, 'queued', notes.length);
    if (playing && !scheduled) cycle();
}
function cancel() {
    outlet(1, "clear");
    outlet(1, "flush");
    scheduled = false;
}
function running(v) {
    var next = Number(v) !== 0;
    if (next === Boolean(playing)) return;
    playing = next;
    if (!playing) cancel();
    else cycle();
}
function cycle() {
    if (!playing) return;
    // Il sentinel arriva dopo i note-off al confine del ciclo.
    if (pending) {active = pending; pending = null;}
    if (!active) {scheduled = false; return;}
    var events = [];
    for (var i=0; i<active.notes.length; i++) {
        var n=active.notes[i];
        events.push([n.pitch, n.velocity, n.beat*PPQ]);
        events.push([n.pitch, 0, (n.beat+n.duration)*PPQ]);
    }
    events.sort(function(a,b) {return a[2]-b[2] || a[1]-b[1] || a[0]-b[0];});
    scheduled = true;
    for (var j=0; j<events.length; j++) outlet(0, events[j]);
    outlet(0, [-1, 0, active.length*PPQ]);
    outlet(2, "active", active.length);
}
function panic() {cancel(); active=null; pending=null;}
function restart() {cancel(); if (playing) cycle();}
function notifydeleted() {cancel();}
