// DESNIVEL — GLSL Pixel Shader per TouchDesigner
// ================================================
// Questo va in un GLSL TOP (Multi-line → Pixel Shader)
//
// Visualizza il percorso come una linea luminosa che 
// si costruisce frame per frame, con colore basato 
// su velocità/pendenza/curvatura.
//
// INPUT UNIFORMS (da collegare via Constant CHOP → GLSL):
//   uLat, uLon       — posizione normalizzata corrente (0→1)
//   uEle              — altitudine normalizzata (0→1)
//   uSpeed            — velocità normalizzata (0→1)
//   uSlope            — pendenza (-1→1)
//   uCurvature        — curvatura (-1→1)
//   uDifficulty       — difficoltà (0→1)
//   uProgress         — td_time_norm (0→1) progresso totale
//   uTrailLength      — lunghezza scia (es. 0.05)

uniform float uLat;
uniform float uLon;
uniform float uEle;
uniform float uSpeed;
uniform float uSlope;
uniform float uCurvature;
uniform float uDifficulty;
uniform float uProgress;
uniform float uTrailLength;

// Feedback TOP come input (sTD2DInputs[0])
// permette di accumulare il percorso frame dopo frame

out vec4 fragColor;

// ─── Palette colori per pendenza ───
vec3 colorFromSlope(float slope) {
    // Discesa = blu/cyan, pianura = verde, salita = arancio/rosso
    float t = slope * 0.5 + 0.5; // remap -1→1 a 0→1
    vec3 downhill = vec3(0.1, 0.5, 0.9);   // blu
    vec3 flat_col = vec3(0.2, 0.9, 0.3);   // verde
    vec3 uphill   = vec3(0.95, 0.3, 0.1);  // rosso
    
    if (t < 0.5) {
        return mix(downhill, flat_col, t * 2.0);
    } else {
        return mix(flat_col, uphill, (t - 0.5) * 2.0);
    }
}

void main()
{
    vec2 uv = vUV.st;
    
    // Posizione corrente del punto GPS nello spazio UV
    vec2 gpsPos = vec2(uLon, 1.0 - uLat); // lon = X, lat invertito = Y
    
    // Distanza dal punto corrente
    float dist = length(uv - gpsPos);
    
    // Punto luminoso nella posizione corrente
    float pointSize = 0.008 + uSpeed * 0.006; // più veloce = punto più grande
    float glow = pointSize / (dist + 0.001);
    glow = pow(glow, 2.2); // falloff
    glow = clamp(glow, 0.0, 1.0);
    
    // Colore basato su pendenza
    vec3 trailColor = colorFromSlope(uSlope);
    
    // Aggiungi tinta basata su curvatura (viola nelle curve strette)
    float curvAbs = abs(uCurvature);
    trailColor = mix(trailColor, vec3(0.7, 0.2, 0.9), curvAbs * 0.5);
    
    // Intensità basata su difficulty
    float intensity = 0.6 + uDifficulty * 0.4;
    trailColor *= intensity;
    
    // Leggi il feedback (frame precedente) per accumulare la scia
    vec4 prev = texture(sTD2DInputs[0], uv);
    
    // Fade graduale del feedback (scia che svanisce)
    float fadeRate = 0.997; // più alto = scia più lunga
    prev.rgb *= fadeRate;
    
    // Componi: feedback + nuovo punto
    vec3 finalColor = prev.rgb + trailColor * glow;
    
    // Altitudine come luminosità di fondo sottile
    float bgEle = uEle * 0.03;
    finalColor += vec3(bgEle * 0.5, bgEle * 0.3, bgEle * 0.8);
    
    fragColor = TDOutputSwizzle(vec4(finalColor, 1.0));
}
