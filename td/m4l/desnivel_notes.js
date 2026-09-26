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
 *   3 — int   : channel   → noteout  inlet 2OK
 */

var VERSION = "2026-05-10 v7";
post("[desnivel_notes] loaded — " + VERSION + "\n");

inlets  = 5;
outlets = 6;   // 0=pitch1 1=vel1 2=dur 3=ch  4=pitch2 5=vel2

// ══════════════════════════════════════════════════════════════════════════
// CONFIG — tutti i parametri editabili in un posto solo
// ══════════════════════════════════════════════════════════════════════════
var CONFIG = {

    // ── Timing ───────────────────────────────────────────────────────────
    // Il metro interval si imposta nel maxpat (oggetto "metro NNN").
    // Valori orientativi: 250 = sparso / 180 = medio / 110 = denso

    // ── Probabilità nota ─────────────────────────────────────────────────
    playProb_min:    0.40,   // prob a density=0.0  (0.0 = mai, 1.0 = sempre)
    playProb_max:    0.90,   // prob a density=1.0

    // ── Tessitura: soglie density ─────────────────────────────────────────
    density_sparse:  0.25,   // sotto: tonica+quinta solo (paesaggio piatto/lento)
    density_mid:     0.55,   // sotto: usa scale_mid_ratio (terreno medio)
    scale_mid_ratio: 0.60,   // frazione della scala in zona mid (es. 0.6 = 4/7 gradi)

    // ── Ottava displacement ───────────────────────────────────────────────
    octave_threshold: 0.65,  // density minima per salire di un'ottava
    octave_prob:      0.25,  // probabilità di displacement

    // ── Contorno melodico (direzione di frase) ────────────────────────────
    phrase_len_min:   3,     // note minime per frase prima di cambiare direzione
    phrase_len_max:   7,     // note massime per frase
    contour_strength: 0.60,  // prob di seguire la direzione (0=random, 1=sempre)

    // ── Pesi gradi stabili ────────────────────────────────────────────────
    stable_weight:   2.5,    // tonica e quinta appaiono 2.5× più degli altri gradi

    // ── Anti-ripetizione ──────────────────────────────────────────────────
    antirepeat_prob: 0.75,   // se stessa nota: prob di spostare al grado adiacente

    // ── Velocity ──────────────────────────────────────────────────────────
    vel_base:      45,       // velocity minima (density=0)  — MIDI 0–127
    vel_range:     50,       // escursione verso density=1   (45+50=95 max medio)
    vel_humanize:  14,       // ± randomizzazione (±7 per nota)

    // ── Duration (ms) ─────────────────────────────────────────────────────
    dur_max:    550,         // durata a density=0 (note lunghe, sparso)
    dur_range:  320,         // escursione (a density=1: 550-320=230ms)
    dur_jitter:  60,         // ± randomizzazione

    // ── Accordi (voce armonica) ───────────────────────────────────────────
    chord_prob:        0.25, // prob di aggiungere una seconda voce per ogni nota
    chord_threshold:   0.35, // density minima per accordi
    chord_degree_offset: 2,  // gradi di scala sopra la nota principale (terza)
    chord_vel_ratio:   0.70, // velocity voce armonica = principale × ratio

    // ── Note sostenute ────────────────────────────────────────────────────
    sustain_prob:      0.12, // prob di suonare una nota lunga (drone/pad)
    sustain_threshold: 0.40, // density MASSIMA per sostenute (solo zone sparse)
    sustain_dur_min:  1500,  // durata minima nota sostenuta (ms)
    sustain_dur_max:  4000,  // durata massima nota sostenuta (ms)

    // ── Ornamento (grace note) ────────────────────────────────────────────
    grace_threshold:   0.50, // density minima per ornamenti (solo in zone dense)
    grace_prob:        0.35, // probabilità ornamento per nota principale
    grace_vel_ratio:   0.60, // velocity ornamento = principale × ratio
    grace_dur_min:     80,   // durata minima ornamento (ms)
    grace_dur_jitter:  60,   // ± randomizzazione durata ornamento
    grace_degree_offset: 2   // offset gradi di scala (2 = terza della scala)

};
// ══════════════════════════════════════════════════════════════════════════

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
var lastIdx   = 0;                 // ultimo indice di scala (per contorno)
var contourDir   = 1;             // +1 = ascendente, -1 = discendente
var contourSteps = 0;             // bang rimanenti nella direzione corrente
var bangCount = 0;                 // contatore per debug log

// ── Selezione indice di scala con peso armonico + contorno melodico ────────
function pickIdx(scale, maxIdx) {
    // Aggiorna contorno di frase
    contourSteps--;
    if (contourSteps <= 0) {
        contourDir   = (Math.random() > 0.5) ? 1 : -1;
        contourSteps = CONFIG.phrase_len_min +
            Math.floor(Math.random() * (CONFIG.phrase_len_max - CONFIG.phrase_len_min + 1));
    }

    // Costruisci pesi: tonica (i=0) e quinta (semitono 7) sono più forti
    var weights = [];
    var totalW  = 0;
    for (var i = 0; i < maxIdx; i++) {
        var w = 1.0;
        if (i === 0 || scale[i] === 7) w = CONFIG.stable_weight;
        // Bias verso la direzione del contorno corrente
        if (Math.random() < CONFIG.contour_strength) {
            if (contourDir > 0 && i > lastIdx) w *= 2.0;
            if (contourDir < 0 && i < lastIdx) w *= 2.0;
        }
        weights.push(w);
        totalW += w;
    }

    // Pick pesato
    var r = Math.random() * totalW;
    var cum = 0;
    for (var j = 0; j < weights.length; j++) {
        cum += weights[j];
        if (r <= cum) { lastIdx = j; return j; }
    }
    lastIdx = weights.length - 1;
    return lastIdx;
}

// ── Generazione nota (chiamata dal bang di metro) ────────────────────────
function bang() {
    if (inlet !== 0) return;

    bangCount++;
    if (bangCount % 20 === 0) {
        post("[desnivel] root=" + root + " scale=" + scaleName +
             " density=" + density.toFixed(2) + " voice=" + voice + "\n");
    }

    var scale = SCALES[scaleName] || SCALES["pentatonic_major"];

    var playProb = CONFIG.playProb_min + density * (CONFIG.playProb_max - CONFIG.playProb_min);
    if (Math.random() > playProb) return;

    var maxIdx;
    if (density < CONFIG.density_sparse) {
        // Solo tonica + quinta: usa pickIdx su 2 gradi
        maxIdx = Math.min(2, scale.length);
    } else if (density < CONFIG.density_mid) {
        maxIdx = Math.ceil(scale.length * CONFIG.scale_mid_ratio);
    } else {
        maxIdx = scale.length;
    }
    var idx = pickIdx(scale, maxIdx);

    var octave = (density > CONFIG.octave_threshold && Math.random() < CONFIG.octave_prob) ? 12 : 0;
    var pitch  = Math.min(84, Math.max(36, root + scale[idx] + octave));

    if (pitch === lastPitch && Math.random() < CONFIG.antirepeat_prob) {
        idx   = (idx + 1) % scale.length;
        pitch = Math.min(84, Math.max(36, root + scale[idx] + octave));
    }
    lastPitch = pitch;

    var velocity = Math.min(127, Math.max(1,
        Math.round(CONFIG.vel_base + density * CONFIG.vel_range + (Math.random() - 0.5) * CONFIG.vel_humanize)
    ));

    // Nota sostenuta: a bassa density, prob di durata lunga (drone/pad)
    var duration;
    if (density < CONFIG.sustain_threshold && Math.random() < CONFIG.sustain_prob) {
        duration = Math.round(CONFIG.sustain_dur_min +
            Math.random() * (CONFIG.sustain_dur_max - CONFIG.sustain_dur_min));
    } else {
        duration = Math.round(CONFIG.dur_max - density * CONFIG.dur_range + (Math.random() - 0.5) * CONFIG.dur_jitter);
    }

    var channel  = VOICE_CHANNELS[voice] || 1;

    outlet(3, channel);
    outlet(2, duration);
    outlet(1, velocity);
    outlet(0, pitch);

    // Accordo: seconda voce alla terza della scala (outlet 4+5)
    if (density > CONFIG.chord_threshold && Math.random() < CONFIG.chord_prob) {
        var ci  = (idx + CONFIG.chord_degree_offset) % scale.length;
        var cp  = Math.min(84, Math.max(36, root + scale[ci] + octave));
        var cv  = Math.max(1, Math.round(velocity * CONFIG.chord_vel_ratio));
        outlet(3, channel);
        outlet(2, duration);
        outlet(5, cv);
        outlet(4, cp);   // hot — triggera il secondo makenote
    }

    // Ornamento (grace note): brevissima nota aggiuntiva a density alta
    if (density > CONFIG.grace_threshold && Math.random() < CONFIG.grace_prob) {
        var gi = (idx + CONFIG.grace_degree_offset) % scale.length;
        var gp = Math.min(84, Math.max(36, root + scale[gi] + octave));
        var gv = Math.max(1, Math.round(velocity * CONFIG.grace_vel_ratio));
        var gd = Math.round(CONFIG.grace_dur_min + Math.random() * CONFIG.grace_dur_jitter);
        outlet(3, channel);
        outlet(2, gd);
        outlet(1, gv);
        outlet(0, gp);
    }
}

// ── Inlet handlers ────────────────────────────────────────────────────────
function msg_int(v) {
    if (inlet === 1) {
        root = Math.min(84, Math.max(36, v));
        post("[desnivel] ← pitch=" + root + "\n");
    }
}

function msg_float(v) {
    if (inlet === 3) {
        density = Math.min(1.0, Math.max(0.0, v));
        post("[desnivel] ← density=" + density.toFixed(2) + "\n");
    }
}

function anything() {
    var sym = messagename;
    post("[desnivel] ← inlet" + inlet + " msg=" + sym + "\n");
    if      (inlet === 2 && SCALES[sym])         scaleName = sym;
    else if (inlet === 4 && VOICE_CHANNELS[sym])  voice     = sym;
}
