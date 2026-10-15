// DESNIVEL — Terrain GLSL Pixel Shader
// =====================================
// Visualizza una "mappa di calore" del terreno
// che si evolve con i dati GPS in tempo reale.
//
// Va in un GLSL TOP separato.
// Utile come sfondo o layer composito.

uniform float uLat;
uniform float uLon;
uniform float uEle;
uniform float uSpeed;
uniform float uSlope;
uniform float uCurvature;
uniform float uEffort;
uniform float uProgress;

out vec4 fragColor;

// Simplex noise 2D (semplificato)
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    
    return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x),
               mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 5; i++) {
        v += a * noise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}

void main()
{
    vec2 uv = vUV.st;
    
    // Offset del noise basato sulla posizione GPS → il terreno "viaggia"
    vec2 offset = vec2(uLon * 10.0, uLat * 10.0);
    
    // Noise terreno
    float terrain = fbm(uv * 4.0 + offset);
    
    // Modulato da altitudine reale
    terrain = mix(terrain, uEle, 0.3);
    
    // Palette terreno
    vec3 low  = vec3(0.05, 0.1, 0.15);   // fondovalle — scuro
    vec3 mid  = vec3(0.15, 0.35, 0.2);   // collina — verde scuro
    vec3 high = vec3(0.8, 0.75, 0.65);   // montagna — chiaro
    vec3 peak = vec3(1.0, 0.95, 0.9);    // vetta — quasi bianco
    
    vec3 col;
    if (terrain < 0.33) {
        col = mix(low, mid, terrain / 0.33);
    } else if (terrain < 0.66) {
        col = mix(mid, high, (terrain - 0.33) / 0.33);
    } else {
        col = mix(high, peak, (terrain - 0.66) / 0.34);
    }
    
    // Effort → vignette rossa (fatica)
    float vignette = length(uv - 0.5) * 2.0;
    col = mix(col, vec3(0.6, 0.05, 0.0), uEffort * vignette * 0.4);
    
    // Speed → "righe di velocità" orizzontali
    float speedLines = sin(uv.y * 200.0 + uProgress * 100.0) * 0.5 + 0.5;
    speedLines = pow(speedLines, 20.0) * uSpeed * 0.15;
    col += vec3(speedLines);
    
    // Curvatura → distorsione leggera
    float curvEffect = abs(uCurvature) * 0.02;
    col += vec3(curvEffect * sin(uv.x * 50.0));
    
    // Barra di progresso in basso
    float bar = step(uv.y, 0.01) * step(uv.x, uProgress);
    col = mix(col, vec3(1.0, 0.8, 0.2), bar);
    
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
