# Sequencer melodico (Snake)

Come primo banco di prova operativo per ascoltare la linea melodica generata dalle metriche del viaggio, il sistema si interfaccia con il sequencer **MDD Snake** in Ableton Live tramite un bridge Max for Live dedicato.

---

## Bridge di controllo e parametri

Il bridge Max for Live (`m4l/desnivel-bridge.amxd` con `m4l/desnivel_snake_params.js`) riceve comandi OSC sulla porta **9001**:

```text
/desnivel/v1/control/snake/set  <nome_parametro>  <valore>
```

Lo script JavaScript cerca il primo device il cui nome contiene `snake` tra le tracce del Set e ne aggiorna i parametri tramite la Live API.

### Configurazione delle note e scale
- Il parametro `Note_01` accetta valori da `0` a `83`.
- Nella configurazione di riferimento (scala *Chromatic*, tonica *C*), i valori `36–51` generano note MIDI tra `60` e `75` (Do centrale e ottava successiva).
- **Shape dei Gate**: definisce il percorso geometrico attraverso la matrice 4×4 dei passi (valori da `0` a `13`). Durante il replay, il motore estrae una Shape all'ingresso di ciascuna sezione della tappa.

---

## Banco Length personalizzato

Lo script `tools/build_snake_length.py` estende il device vanilla MDD Snake (versione 3.2.3) aggiungendo un banco dedicato alla durata delle note (**Length**), preservando i banchi *Notes*, *Gates*, *Velocities* e *Custom*.

```sh
python3 tools/build_snake_length.py \
  --source "$HOME/Music/Ableton/User Library/MaxForLive/MDD___SNAKE_V3.2.3.amxd" \
  --output /tmp/desnivel-snake-length/MDD_SNAKE_LengthBank.amxd
```

Il banco Length gestisce 16 valori (0–127) convertiti in millisecondi tra i valori configurati di minimo e massimo (tipicamente 50–500 ms).

---

## Telemetria dello stato ed Export

La variante costruita da `tools/build_live_bass.py` aggiunge il controllo **Export** al banco Length e invia lo stato del sequencer verso Python.

- **Porta**: UDP **9003**
- **Indirizzo**: `/desnivel/v1/snake/state`
- **Payload**: stringa JSON contenente posizione corrente del trasporto, stato Play/Stop, BPM e stato dei banchi.

### Campi principali del messaggio
```json
{
  "version": 1,
  "source": "snake-source",
  "serial": 12,
  "epoch": 1,
  "beat": 16.0,
  "playing": 1,
  "state": {
    "notes": [60, 62, 64, 65, 67, 69, 71, 72, 60, 62, 64, 65, 67, 69, 71, 72],
    "gates": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    "velocities": [90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 90],
    "lengths_ms": [200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200],
    "bpm": 94.0,
    "midi_offset": 0,
    "swing": 0,
    "notes_lane": {"shape": 1, "speed": "16n", "steps": 16, "direction": "forwards", "phase_beats": 0.0},
    "gates_lane": {"shape": 1, "speed": "16n", "steps": 16, "direction": "forwards", "phase_beats": 0.0},
    "velocities_lane": {"shape": 1, "speed": "16n", "steps": 16, "direction": "forwards", "phase_beats": 0.0}
  }
}
```

### Previsione melodica (`snake_sequence.predict`)
Il modulo Python `src/desnivel/adapters/snake_sequence.py` usa questi snapshot per prevedere gli attacchi, le altezze e le durate delle note future generate da Snake su una finestra temporale (es. 4 beat). In questo modo il generatore del basso conosce in anticipo gli eventi melodici e può comporre linee di risposta e contrappunto sincronizzate.

---

La previsione richiede swing zero, Shift = 1 sulle tre lane, direzioni `forwards` o `backwards` e velocità `32n`, `16n`, `8n`, `4n` o `2n`. Il calcolo presuppone che BPM e parametri di Snake restino invariati durante i beat previsti.

## Acquisizione delle sessioni

Per salvare gli snapshot del sequencer in JSONL:

```sh
python -m desnivel.cli.capture_snake --seconds 180 --label "sessione_studio"
```

Per acquisire anche i piani del basso usare `python -m desnivel.cli.live_bass --capture`. Non avviare `capture_snake` e `live_bass` insieme: usano entrambi la porta 9003.

I dati vengono salvati in una directory temporanea esterna alla repository, preservando la cronologia degli eventi e dei beat.

