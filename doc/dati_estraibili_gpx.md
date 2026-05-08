# DESNIVEL — Dati estraibili dai GPX per TouchDesigner

## Stato attuale

I 12 file GPX (Strava, tipo `cycling`) contengono **solo dati base**: `lat`, `lon`, `ele`, `time`.  
Nessuna estensione Strava (HR, cadence, power, temperatura).

Lo script `src/desnivel_gpx_to_td.py` estrae **16 canali per frame** a 30 fps, esportati in CSV (`output/tappa_XX.csv`).

### Canali attuali

| Canale | Tipo | Range | Uso in TD |
|---|---|---|---|
| `lat_norm` | Posizione | 0→1 | Posizione punto, offset noise shader |
| `lon_norm` | Posizione | 0→1 | Posizione punto, offset noise shader |
| `ele_norm` | Posizione | 0→1 | Altezza Y, luminosità sfondo |
| `speed_kmh` | Istantaneo | 0→~120 | Dimensione punto, righe velocità |
| `slope` | Istantaneo | -1→1 | Palette colore (blu discesa → verde piano → rosso salita) |
| `curvature` | Istantaneo | -1→1 | Tinta viola nelle curve strette |
| `bearing_deg` | Istantaneo | 0→360 | Disponibile ma non usato negli shader |
| `difficulty` | Derivato (rolling) | 0→1 | Intensità visiva |
| `flow_index` | Derivato (rolling) | 0→1 | Ritmicità / continuità del movimento |
| `effort` | Derivato (rolling) | 0→1 | Vignette rossa (fatica) |
| `cum_dist_m` | Cumulativo | 0→max | Non usato visualmente |
| `cum_ele_gain_norm` | Cumulativo | 0→1 | Non usato visualmente |
| `cum_ele_loss_norm` | Cumulativo | 0→1 | Non usato visualmente |
| `ele_delta` | Istantaneo | variabile | Variazione altimetrica puntuale |
| `td_time` | Tempo mappato | 0→durata | Tempo riscalato (tappa più lunga = 600s) |
| `td_time_norm` | Progresso | 0→1 | Barra progresso |

---

## Dati aggiuntivi estraibili

Tutto ciò che segue è calcolabile dai 4 campi raw (`lat`, `lon`, `ele`, `time`) senza dati esterni.

### 1. Accelerazione (`accel`)

Derivata della velocità tra frame consecutivi.

- **Calcolo**: `accel = (speed[i] - speed[i-1]) / dt`
- **Range**: normalizzabile 0→1
- **Rileva**: scatti, frenate, partenze dopo sosta
- **Uso TD**: intensità particelle, screen shake, flash al cambio brusco

### 2. Jerk (`jerk`)

Derivata dell'accelerazione — variazione di secondo ordine.

- **Calcolo**: `jerk = (accel[i] - accel[i-1]) / dt`
- **Rileva**: impatti, buche, cambi di ritmo improvvisi
- **Uso TD**: glitch shader, distorsione audio, haptic pulse

### 3. Velocità angolare (`angular_velocity`)

Quanto cambia il bearing per unità di tempo.

- **Calcolo**: `angular_vel = delta_bearing / dt` (con wrap-around ±180°)
- **Rileva**: curve dolci vs tornanti stretti
- **Uso TD**: rotazione camera, trail width, spirale di particelle

### 4. Sinuosità (`sinuosity`)

Rapporto tra distanza percorsa e distanza in linea d'aria su una finestra di N punti.

- **Calcolo**: `sinuosity = cum_dist_window / straight_line_dist_window`
- **Range**: 1.0 = perfettamente dritto, >2.0 = tornanti
- **Rileva**: rettilineo vs montagna tortuosa
- **Uso TD**: complessità frattale del noise, densità mesh, vibrazione

### 5. Stabilità della direzione (`heading_var`)

Varianza del bearing su una finestra rolling.

- **Calcolo**: varianza circolare di `bearing_deg` su ~30 punti
- **Range**: 0 = rettilineo, alto = switchback
- **Rileva**: calma vs caos direzionale
- **Uso TD**: blur/sharpness, ampiezza ondulazione, calma vs caos visivo

### 6. Micro-rugosità del terreno (`terrain_roughness`)

Varianza alta-frequenza dell'elevazione su finestra corta.

- **Calcolo**: varianza di `ele` su ~10 punti
- **Range**: normalizzabile 0→1
- **Rileva**: strade lisce vs sterrato/irregolare
- **Uso TD**: displacement map intensity, texture grain, audio granularity

### 7. Potenza stimata (`power_est_w`)

Modello fisico semplificato per ciclismo:

```
P = (m·g·v·sin(θ)) + (0.5·Cd·A·ρ·v³) + (Cr·m·g·v)
```

Parametri default:
- `m` = 80 kg (ciclista + bici)
- `Cd·A` = 0.5 m² (resistenza aerodinamica)
- `ρ` = 1.225 kg/m³ (densità aria)
- `Cr` = 0.005 (attrito rotolamento)

- **Range**: 0→~800W, normalizzabile
- **Rileva**: sforzo fisico reale — più espressivo di `effort`
- **Uso TD**: colore fuoco/energia, emissione particelle, volume audio

### 8. Classificazione zona (`zone`)

Speed zones basate su percentili della velocità nella tappa.

| Zona | Etichetta | Range |
|---|---|---|
| 0 | Fermo | < 2 km/h |
| 1 | Easy | < P25 |
| 2 | Moderate | P25–P50 |
| 3 | Hard | P50–P75 |
| 4 | Sprint | > P75 |

- **Uso TD**: palette discreta, cambio scena, trigger eventi

### 9. Rilevamento soste (`is_stopped`, `stop_duration_s`)

- **Logica**: velocità < 2 km/h per > 30s consecutivi
- `is_stopped` = 0 o 1
- `stop_duration_s` = durata della sosta attuale (cresce finché fermo)
- **Uso TD**: fade to black, pausa narrativa, transizione, respiro

### 10. Ora del giorno (`hour_of_day`, `sun_elevation`)

Ricavabile direttamente dai timestamp GPS.

- `hour_of_day` = ora decimale (es. 14.5 = 14:30)
- `sun_elevation` = angolo solare approssimato (formula semplificata con lat + ora)
- **Uso TD**: colore luce ambiente, ombre, atmosfera giorno/notte/alba/tramonto

### 11. Distanza da inizio/fine (`progress_dist`, `remaining_km`)

Progresso in chilometri reali.

- `progress_dist` = `cum_dist_m / 1000` in km
- `remaining_km` = `total_dist_km - progress_dist`
- **Uso TD**: UI alternativa alla barra tempo, senso di vicinanza alla meta

### 12. Segmenti salita/discesa (`segment_type`)

Classifica automatica in segmenti continui.

- **Valori**: `climb` (slope > +2%), `descent` (slope < -2%), `flat`
- Calcolo su finestra rolling per evitare rumore
- **Uso TD**: trigger cambio modalità visiva, colonna sonora adattiva, colore dominante

### 13. Densità punti GPS (`point_density`)

Quanti punti GPS per metro percorso.

- **Calcolo**: `1 / dist_m` (punti per metro) o media rolling
- **Rileva**: alta densità = bassa velocità o percorso tecnico
- **Uso TD**: livello di dettaglio, zoom camera

### 14. Coordinate assolute (`lat_abs`, `lon_abs`)

Le coordinate originali (non normalizzate).

- Utili per overlay su mappa o per calcolo distanza tra tappe
- **Uso TD**: texture map lookup, posizione su mappa Italia

---

## Priorità consigliate

I canali più impattanti per TouchDesigner con il minimo sforzo di implementazione:

| Priorità | Canali | Motivazione |
|---|---|---|
| **Alta** | `accel`, `jerk` | Danno vita e dinamica alle visualizzazioni |
| **Alta** | `sinuosity`, `heading_var` | Distinguono rettilineo da montagna |
| **Alta** | `is_stopped`, `stop_duration_s` | Momenti narrativi chiave (pause, soste) |
| **Media** | `hour_of_day` | Luce ambientale gratis dai timestamp |
| **Media** | `power_est_w` | Indicatore fisico più espressivo |
| **Bassa** | `zone`, `segment_type` | Utili per eventi discreti |
| **Bassa** | `terrain_roughness`, `point_density` | Dettaglio aggiuntivo |

---

## Struttura file

```
Desnivel/
├── gpx/                  ← 12 GPX Strava (lat, lon, ele, time)
├── src/
│   └── desnivel_gpx_to_td.py   ← pipeline GPX → CSV
├── output/
│   ├── tappa_01..12.csv         ← CSV a 30fps per TD
│   └── desnivel_summary.json    ← metadati globali
├── td/
│   ├── desnivel_loader.py       ← loader per TD (Table DAT → CHOP)
│   ├── frame_execute.py         ← aggiorna shader ogni frame
│   ├── trail_pixel.glsl         ← shader scia GPS
│   ├── terrain_pixel.glsl       ← shader terreno noise
│   └── primordiale.toe          ← progetto TD
└── doc/
    └── dati_estraibili_gpx.md   ← questo file
```

## Note tecniche

- I GPX sono registrati a **~1 punto/secondo** da Strava
- Il resample a **30 fps** usa interpolazione lineare (con wrap-around per bearing)
- Il tempo è riscalato proporzionalmente: **tappa più lunga = 600s** (10 min), le altre in proporzione
- Tutti i valori normalizzati sono **per-tappa** (0→1 relativo alla singola tappa)
