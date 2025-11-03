# GPX → SOUND DESIGN MAP  
*Fase 1: Design concettuale e relazionale*  

Questo documento definisce come i dati di un file GPX vengono interpretati, elaborati e mappati in parametri musicali all’interno di Ableton (e successivamente visualizzati in TouchDesigner).  
Obiettivo: trasformare la traccia di un viaggio in una canzone, dove ogni variazione geografica e temporale diventa un gesto sonoro.

---

## 🧩 Livello 1 – Dati Grezzi

| Nome | Descrizione | Unità | Fonte GPX | Note |
|------|--------------|-------|------------|------|
| `time_utc` | Timestamp registrato dal dispositivo | ISO8601 | `<time>` | base temporale di tutto |
| `lat` | Latitudine | ° | `<trkpt lat>` | usato per posizione e direzione |
| `lon` | Longitudine | ° | `<trkpt lon>` | usato per direzione e mappature spaziali |
| `elev` | Altitudine sopra il livello del mare | m | `<ele>` | principale driver per pitch / spazio |
| `speed` | Velocità istantanea | m/s | calcolata o da GPX | influenza BPM e densità ritmica |
| `course` | Direzione (azimut) | ° | derivata da lat/lon | utile per panning e movimenti stereo |

---

## 🧮 Livello 2 – Derivati (numerici)

| Nome | Formula / Metodo | Unità | Significato | Range tipico | Note |
|------|------------------|-------|--------------|---------------|------|
| `distance_total` | somma dei Δdist | km | lunghezza della tappa | 20–150 km | usata per durata totale musicale |
| `dz` | Δelev | m | variazione di quota tra due punti | ±10 | base per pendenza |
| `grade_smooth` | mean(Δelev/Δdist, window=10s) | % | pendenza lisciata | -15 → +15 | energia e tensione |
| `curvature` | Δbearing/Δdist | 1/m | misura quanto cambia direzione | 0–0.1 | groove, “instabilità” |
| `acceleration` | Δspeed/Δtime | m/s² | variazione di velocità | ±2 | transizioni dinamiche |
| `alt_var` | var(elev, window=1min) | m² | oscillazione altimetrica locale | 0–50 | distingue salita continua vs saliscendi |
| `entropy_grade` | entropia su istogramma di pendenza | 0–1 | complessità morfologica | 0.1–0.8 | alto = percorso frastagliato |

---

## 🧭 Livello 3 – Indici Semantici (interpretazione del terreno e del momento)

| Nome | Metodo di stima | Range / Tipo | Significato narrativo | Uso musicale | Peso narrativo |
|------|-----------------|---------------|------------------------|---------------|----------------|
| `terrain_class` | basato su varianza quota + alt_media | {pianura, collina, montagna, costa} | tipo di paesaggio | seleziona palette timbrica | 🔵 Alto |
| `difficulty_index` | mix normalizzato di pendenza+, alt_var, v_smooth basso | 0–1 | intensità fisica percepita | volume, saturazione | 🔵 Alto |
| `flow_index` | 1 - varianza(v, grade) | 0–1 | continuità del movimento | groove, pattern costanti | 🟢 Medio |
| `time_of_day` | timestamp + offset locale | {dawn, day, dusk, night} | luce e atmosfera | scelta di tonalità e riverbero | 🟡 Medio |
| `effort_index` | v_smooth × (1 + k·grade_pos) | 0–1 | energia del ciclista / performer | attack, dinamica | 🔵 Alto |
| `event_flag` | regole (stop, vetta, curva, sprint) | bool | momenti salienti | cue musicali / drop | 🔴 Molto alto |

---

## 🕰️ Livello 4 – Tempo Musicale (time-warp)

| Nome | Descrizione | Formula / Logica | Unità | Note |
|------|--------------|------------------|--------|------|
| `weight_raw` | peso locale del campione | funzione di grade, curv, event | adimensionale | definisce importanza musicale |
| `weight_norm` | normalizzato sulla somma totale | 0–1 | usato per costruire tempo musicale |  |
| `t_scaled` | tempo musicale compresso | integrazione cumulata(weight_norm) | s | ascissa per Ableton |

---

## 🎛️ Livello 5 – Mappatura Musicale (prima bozza)

| Dato | Parametro Ableton | Tipo di mappa | Range (data → suono) | Descrizione estetica |
|------|--------------------|----------------|----------------------|----------------------|
| `altitude` | pitch / filtro cutoff | lineare o log | 0–2000m → C2–C6 | più sali → suono più aperto e brillante |
| `grade_smooth` | intensità / drive | log | 0–10% → 0–1 | salita = tensione |
| `curvature` | densità ritmica | exp | 0–0.05 → 0–100% | curve = groove, microbeat |
| `speed` | BPM / tempo base | lin | 10–35 km/h → 90–130 BPM | ritmo naturale del viaggio |
| `difficulty_index` | volume globale | lin | 0–1 → -10dB/+3dB | fatica = presenza sonora |
| `flow_index` | reverb/delay feedback | inv | 0–1 → 80%–20% | fluido = meno spazio |
| `time_of_day` | timbro / scala | discreta | dawn/day/dusk/night | variazione tonale di luce |
| `event_flag` | marker / trigger | n/a | boolean | drop, break, o accento visivo |

---

## 🧩 Livello 6 – Casi Studio (esempio concettuale)
### **Tappa A – Salita continua**
- *Forma*: progressiva, un unico “buildup”.  
- *Parametri dominanti*: `grade_smooth`, `prog (alt_rel)`, `difficulty_index`.  
- *Tempo musicale*: compresso all’inizio, espanso verso la vetta.  
- *Mood sonoro*: ascendente, catartico, arioso.

### **Tappa B – Saliscendi ritmato**
- *Forma*: ciclica, frammentata, dinamica.  
- *Parametri dominanti*: `alt_var`, `entropy_grade`, `curvature`, `flow_index`.  
- *Tempo musicale*: micro-dilatazioni continue, groove ondulato.  
- *Mood sonoro*: vivace, meccanico, quasi tribale.

---

## 🧠 Idee future (fase 2)
- Aggiungere layer esterni (mare, città, punti notevoli via OSM).  
- Integrare dati astronomici per colore della luce.  
- Tradurre `terrain_class` in **preset sonori** e **shader visivi**.  
- Costruire un dizionario JSON di “mappature parametriche”.

---

**Autore:** Marco — *Sound / Data Design Project*  
**Versione:** 0.1 (Fase 1)  
**Data:** Ottobre 2025
