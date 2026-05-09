/**
 * DESNIVEL — GPS-driven generative note engine for Max4Live
 * ==========================================================
 * Riceve parametri OSC da TouchDesigner e genera note MIDI sincronizzate
 * al transport di Live. Scala e voce seguono il terreno del percorso GPS.
 *
 * Inlets:
 *   0 — bang  : trigger da live.metro (ogni 8ina)
 *   1 — int   : root pitch MIDI (36–84, es. 62 = D4)
 *   2 — symbol: nome scala (es. "dorian", "pentatonic_major")
 *   3 — float : density 0.0–1.0 (controlla densità e probabilità note)
 *   4 — symbol: voce timbrica (es. "pluck_hill", "brass_mountain")
 *
 * Outlets:
 *   0 — int   : pitch     → makenote inlet 0 (hot, triggers)
 *   1 — int   : velocity  → makenote inlet 1
 *   2 — int   : duration  → makenote inlet 2
 *   3 — int   : channel   → noteout  inlet 2
 */

inlets  = 5;
outlets = 4;

// ── Scale definitions — specchio di src/constants.py SCALES ──────────────
var SCALES = {
    "major":            [0, 2, 4, 5, 7, 9, 11],
    "minor":            [0, 2, 3, 5, 7, 8, 10],
    "dorian":           [0, 2, 3, 5, 7, 9, 10],
    "lydian":           [0, 2, 4, 6, 7, 9, 11],
    "phrygian":         [0, 1, 3, 5, 7, 8, 10],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "pentatonic_major": [0, 2, 4, 7, 9]
};

// ── Voice → MIDI channel — specchio di src/constants.py TERRAIN_VOICES ───
var VOICE_CHANNELS = {
    "drone_water":    1,   // mare/costa
    "pad_plain":      2,   // pianura
    "pluck_hill":     3,   // collina
    "brass_mountain": 4    // montagna
};

// ── Stato (aggiornato dagli inlets 1–4) ──────────────────────────────────
var root      = 62;                // D4 — tonica di default
var scaleName = "pentatonic_major";
var density   = 0.5;
var voice     = "pluck_hill";
var lastPitch = -1;                // anti-repetition

// ── Generazione nota (chiamata dal bang di live.metro) ───────────────────
function bang() {
    if (inlet !== 0) return;

    var scale = SCALES[scaleName] || SCALES["pentatonic_major"];

    // Probabilità di suonare una nota: 0.15 (density=0) → 0.85 (density=1)
    var playProb = 0.15 + density * 0.70;
    if (Math.random() > playProb) return;

    // Selezione grado di scala in base alla densità
    var idx;
    if (density < 0.25) {
        // Sparso: solo tonica e quinta (stabilità armonica)
        var stable = [0, Math.min(4, scale.length - 1)];
        idx = stable[Math.floor(Math.random() * stable.length)];
    } else if (density < 0.55) {
        // Medio: metà inferiore della scala (melodia leggibile)
        idx = Math.floor(Math.random() * Math.ceil(scale.length * 0.6));
    } else {
        // Denso: scala completa
        idx = Math.floor(Math.random() * scale.length);
    }

    // Dislocazione ottava per texture ad alta densità
    var octave = (density > 0.65 && Math.random() > 0.72) ? 12 : 0;

    var pitch = Math.min(84, Math.max(36, root + scale[idx] + octave));

    // Anti-ripetizione: sposta al grado adiacente con probabilità 0.75
    if (pitch === lastPitch && Math.random() > 0.25) {
        idx   = (idx + 1) % scale.length;
        pitch = Math.min(84, Math.max(36, root + scale[idx] + octave));
    }
    lastPitch = pitch;

    // Velocity: proporzionale alla densità + humanizzazione ±6
    var velocity = Math.min(127, Math.max(1,
        Math.round(40 + density * 55 + (Math.random() - 0.5) * 12)
    ));

    // Duration: inversamente proporzionale alla densità (sparso = note lunghe)
    var duration = Math.round(600 - density * 350 + (Math.random() - 0.5) * 80);

    var channel = VOICE_CHANNELS[voice] || 1;

    // ORDINE CRITICO: i cold inlets devono essere settati PRIMA del pitch (hot)
    outlet(3, channel);   // noteout channel
    outlet(2, duration);  // makenote duration
    outlet(1, velocity);  // makenote velocity
    outlet(0, pitch);     // makenote pitch — ULTIMO, triggera la nota
}

// ── Inlet handlers ────────────────────────────────────────────────────────
function msg_int(v) {
    if (inlet === 1) root = Math.min(84, Math.max(36, v));
}

function msg_float(v) {
    if (inlet === 3) density = Math.min(1.0, Math.max(0.0, v));
}

function anything() {
    var sym = messagename;
    if      (inlet === 2 && SCALES[sym])         scaleName = sym;
    else if (inlet === 4 && VOICE_CHANNELS[sym])  voice     = sym;
}
