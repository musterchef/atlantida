# Sequencer melodico (Snake)

Come primo banco di prova operativo per ascoltare la linea melodica generata dalle metriche del viaggio, il sistema si interfaccia con il sequencer **MDD Snake** in Ableton Live tramite un bridge Max for Live dedicato.

---

## Bridge di controllo e parametri

Il bridge Max for Live (`m4l/desnivel-bridge.amxd` con `m4l/desnivel_snake_params.js`) riceve comandi OSC sulla porta **9001**:

```text
/desnivel/v1/control/snake/set  <nome_parametro>  <valore>
```

Lo script JavaScript individua l'istanza di Snake nella traccia e aggiorna i parametri tramite l'API `live.object`.

### Configurazione delle note e scale
- Il parametro `Note_01` accetta valori da `0` a `83`.
- Nella configurazione di riferimento (scala *Chromatic*, tonica *C*), i valori `36–51` generano note MIDI tra `60` e `75` (Do centrale e ottava successiva).
- **Shape dei Gate**: definisce il percorso geometrico attraverso la matrice 4×4 dei passi (valori da `0` a `13`). Durante il replay, il motore estrae una Shape all'ingresso di ciascuna sezione della tappa.

---

## Banco Length personalizzato

Lo script `tools/build_snake_length.py` estende il device vanilla MDD Snake (versione 3.2.3) aggiungendo un quarto banco dedicato alla durata delle note (**Length**), preservando i banchi *Notes*, *Gates*, *Velocities* e *Custom*.

```sh
python3 tools/build_snake_length.py \
  --source "$HOME/Music/Ableton/User Library/MaxForLive/MDD___SNAKE_V3.2.3.amxd" \
  --output /tmp/desnivel-snake-length/MDD_SNAKE_LengthBank.amxd
```

Il banco Length gestisce 16 valori (0–127) convertiti in millisecondi tra i valori configurati di minimo e massimo (tipicamente 50–500 ms).

---

## Telemetria dello stato ed Export

Per consentire ad altri strumenti (come il basso generativo) di ascoltare e prevedere la melodia, il device esporta periodicamente lo stato interno del sequencer verso Python.

- **Porta**: UDP **9003**
- **Indirizzo**: `/desnivel/v1/snake/state`
- **Payload**: stringa JSON contenente posizione corrente del trasporto, stato Play/Stop, BPM e stato dei banchi.

### Campi principali del messaggio
```json
{
  "version": 1,
  "serial": 12,
  "epoch": 1,
  "beat": 16.0,
  "playing": true,
  "state": {
    "notes": [...],
    "gates": [...],
    "velocities": [...],
    "lengths_ms": [...],
    "bpm": 94.0,
    "notes_lane": {"shape": 1, "speed": 4, "steps": 16, "direction": "forwards", "phase_beats": 0.0},
    "gates_lane": {"shape": 1, "speed": 4, "steps": 16, "direction": "forwards", "phase_beats": 0.0}
  }
}
```

### Previsione melodica (`snake_sequence.predict`)
Il modulo Python `src/desnivel/adapters/snake_sequence.py` usa questi snapshot per calcolare con precisione gli attacchi, le altezze e le durate delle note future generate da Snake su una finestra temporale (es. 4 beat). In questo modo il generatore del basso conosce in anticipo gli eventi melodici e può comporre linee di risposta e contrappunto sincronizzate.

---

## Acquisizione delle sessioni

È possibile salvare gli stati del sequencer e i piani generati in formato JSONL per analisi e verifica:

```sh
python -m desnivel.cli.capture_snake --seconds 180 --label "sessione_studio"
```

I dati vengono salvati in una directory temporanea esterna alla repository, preservando la cronologia degli eventi e dei beat.

