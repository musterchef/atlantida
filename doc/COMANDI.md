# Comandi DESNIVEL

Cheat sheet. Tutti i comandi vogliono il venv attivo:

```sh
cd /Users/marco/ogni-tanto-programmo/desnivel
source .venv/bin/activate
```

---

## Pipeline (calcola e salva su file)

### `desnivel-run`
Calcola modulazioni + eventi di **una** tappa, salva CSV/JSON in `output/`.
```sh
desnivel-run --stage tappa_04
```

### `desnivel-all`
Come sopra ma su **tutte** le tappe.
```sh
desnivel-all
```

### `desnivel-plot`
Disegna i grafici dei canali di una tappa (PNG in `output/viz/`).
```sh
desnivel-plot --stage tappa_04
```

---

## Live OSC (per TouchDesigner o M4L futuro)

### `desnivel-play`
Esegue la pipeline e **invia OSC in tempo reale** sulla porta 9000.

```sh
desnivel-play --stage tappa_04
desnivel-play --stage tappa_04 --speed 30          # 30x più veloce
desnivel-play --stage tappa_04 --speed 30 --loop   # in loop infinito
desnivel-play --stage tappa_04 --dry-run           # stampa schedule, non invia
```

Flag utili:
- `--speed N` velocità (1.0 = tempo reale, 30 = un giro in ~6 min su tappa lunga).
- `--loop` riavvia all'infinito (Ctrl+C per uscire).
- `--osc-host` / `--osc-port` (default `127.0.0.1:9000`).

---

## Bridge OSC → MIDI (per Ableton, provvisorio)

### `desnivel-bridge-midi`
Riceve OSC dal `desnivel-play` e lo traduce in MIDI CC/Note su una porta MIDI virtuale (es. IAC Bus 1).

```sh
desnivel-bridge-midi --midi-port "IAC Driver Bus 1"
desnivel-bridge-midi --list-midi-ports         # elenca porte disponibili
desnivel-bridge-midi --show-mapping            # stampa mappa canale -> CC
```

Lascialo in un terminale dedicato. Ctrl+C per fermarlo.

### `desnivel-midi-sweep`
Tool di servizio per **mappare in Ableton senza far girare la tappa**. Manda CC continui sull'IAC.

```sh
# Modalità assistita (un CC alla volta, INVIO per il prossimo)
desnivel-midi-sweep --midi-port "IAC Driver Bus 1" --solo

# Solo un CC specifico
desnivel-midi-sweep --midi-port "IAC Driver Bus 1" --cc 21

# Tutti i CC insieme (sweep 0->127->0 ogni 4 secondi)
desnivel-midi-sweep --midi-port "IAC Driver Bus 1"
```

Mapping CC attivi adesso:
- **CC 20** = `journey/phase` (0→1 lineare nella tappa)
- **CC 21** = `journey/energy` (sforzo locale)
- **CC 22** = `journey/openness` (varianza altimetria)
- **CC 23** = `macro/scale` (modalita' musicale, int)
- **CC 24** = `macro/palette` (famiglia timbrica, int)
- **CC 25** = `meso/root` (nota MIDI della fondamentale, int)
- **CC 26** = `meso/tension` (cambi di pendenza)
- **CC 29** = `macro/register` (registro grave→acuto, 0..1)
- **CC 30** = `macro/space` (riverbero/ampiezza, 0..1)
- **CC 31** = `macro/brightness` (brillantezza, 0..1)

Note degli eventi (canale MIDI 16):
- C4 (60) = start
- C#4 (61) = end
- D4 (62) = summit
- D#4 (63) = sea first view
- E4 (64) = poi

---

## POI

### `desnivel-discover-poi`
Pre-popola candidati POI da OpenStreetMap (Overpass). Richiede `pip install -e .[discover]`.

```sh
desnivel-discover-poi --gpx gpx/ --buffer-km 1.0 --output data/poi_candidates.json
```

Poi rivedi a mano, cancella i POI inutili, e rinomina in `data/poi.json`.

---

## Workflow tipico per ascoltare

Terminale 1:
```sh
desnivel-bridge-midi --midi-port "IAC Driver Bus 1"
```

Terminale 2 (per mappare la prima volta):
```sh
desnivel-midi-sweep --midi-port "IAC Driver Bus 1" --solo
# in Ableton: Cmd+M, clicca knob, INVIO al terminale, ripeti
# Ctrl+C quando hai finito di mappare
```

Terminale 2 (per ascoltare la tappa vera):
```sh
desnivel-play --stage tappa_04 --speed 30 --loop
```

In Ableton serve:
- *Settings → Link, Tempo & MIDI → Input IAC Driver Bus 1*: **Track ✓ Remote ✓**.
- Track con uno strumento, **MIDI From: IAC Driver (Bus 1)**, **Monitor: In**.
- Una clip MIDI in loop con almeno una nota tenuta, premi Play.

---

## Test

```sh
pytest -q              # tutti i test
pytest tests/test_osc_to_midi.py -q   # solo bridge
```
