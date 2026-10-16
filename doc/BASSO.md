# Generatore del basso

Il modulo `desnivel.music.bass` implementa una voce di basso generativa e polifonica. A differenza di un semplice arpeggiatore o di un raddoppio, il generatore del basso analizza la frase melodica (estratta da Snake o da un file di note) e compone una linea di risposta musicale coerente.

---

## Logica compositiva

La composizione avviene tramite la funzione `generate_bass` (`src/desnivel/music/bass/generator.py`), che riceve una `Phrase` melodica e produce una nuova `Phrase` per il basso articolata su tre scelte:

### 1. Attacchi e ritmo (`_rhythm`)
- **Densità (`density`)**: numero desiderato di note per beat.
- **Sincopazione (`syncopation`)**: preferenza per gli appoggi sul battere (0.0) o per gli accenti in levare (1.0).
- **Legame ritmico (`rhythm_follow`)**: a valori bassi il basso suona negli spazi lasciati liberi dalla melodia (dialogo/contrappunto); a valori alti suona all'unisono ritmico con la melodia.
- **Spaziatura minima (`min_spacing`)**: garantisce una distanza minima tra note consecutive (es. 0.5 o 1 beat).

### 2. Altezze e salienza armonica (`_salience`, `_pitches`)
- **Salienza**: analizza la frase melodica pesando durata, dinamica e posizione metrica di ogni nota per individuare l'appoggio armonico più solido.
- **Legame melodico (`melody_follow`)**: bilancia la coerenza con l'appoggio armonico generale (valori bassi) e l'attrazione verso l'altezza melodica più vicina (valori alti).
- **Mobilità (`mobility`)**: regola l'ampiezza degli intervalli. A valori bassi il basso si muove per gradi congiunti vicino alla nota precedente; a valori alti si apre a salti di registro e risposte acute sui levare.
- **Registro (`lowest`, `highest`)**: limiti MIDI inclusivi per definire l'estensione dello strumento (es. 28–47 per un registro profondo).

### 3. Durate e dinamica (`_articulate`)
- **Articolazione (`articulation`)**: frazione di durata occupata dal suono prima dell'attacco successivo (staccato vs sostenuto).
- **Variazione (`variation`)**: introduce micro-variazioni controllate nelle altezze e nelle dinamiche a ogni iterazione.

---

## Preset principali

I controlli sono raggruppati in preset di partenza:

| Preset | Densità | Sincopi | Legame ritmico | Legame melodico | Mobilità | Articolazione | Carattere sonoro |
|---|---:|---:|---:|---:|---:|---:|---|
| **`responsive`** | 0.8 | 0.25 | 0.35 | 0.25 | 0.15 | 0.90 | Dialogo naturale, appoggi morbidi, movimento misurato. |
| **`slap`** | 1.8 | 0.70 | 0.15 | 0.50 | 0.85 | 0.50 | Note corte, sincopato, salti verso l'acuto e ritmo incalzante. |
| **`follow`** | 4.0 | 0.00 | 1.00 | 1.00 | 0.00 | 0.90 | Raddoppio stretto della melodia sia nel ritmo che nelle note. |

---

## Assetti operativi di ascolto (Launcher 08)

Per l'ascolto immediato durante il replay delle tappe, il launcher `08 - Scegli assetto basso.command` mette a disposizione tre configurazioni collaudate:

- **`sobrio`**: registro profondo (28–47), densità contenuta (0.6), appoggio solido e non invadente.
- **`dialogo`**: registro esteso (28–55), densità 1.0, risposte contrappuntistiche negli spazi melodici.
- **`ritmico`**: basato sul preset `slap`, registro fino a 59, dinamica percussiva e accenti in levare.

```sh
# Avvio con scelta interattiva da menu
./comandi/08\ -\ Scegli\ assetto\ basso.command

# Oppure avvio diretto con sovrascrittura di un parametro
./comandi/08\ -\ Scegli\ assetto\ basso.command dialogo --density 0.8
```

---

## Controllo in tempo reale (Live OSC)

Durante l'esecuzione, il processo `live_bass` accetta comandi OSC sulla porta **9003** per modificare i parametri musicali al volo senza fermare l'esecuzione:

- **Indirizzo**: `/desnivel/v1/bass/control`
- **Payload**: stringa JSON con numerazione seriale e parametri di destinazione.

```json
{
  "version": 1,
  "serial": 1,
  "parameters": {
    "density": 0.9,
    "articulation": 0.65,
    "mobility": 0.4
  },
  "transition_windows": 4
}
```

### Transizioni fluide
Con `transition_windows` (predefinito: 4), il generatore non cambia i valori bruscamente: interpola gradualmente i parametri sulle finestre future di pianificazione (es. 16 beat complessivi), garantendo una transizione musicale fluida e priva di artefatti.

---

## Esecuzione in Ableton Live (Device M4L)

Per sincronizzare il basso al trasporto di Live:
1. Costruire i device Max for Live:
   ```sh
   python tools/build_live_bass.py \
     --source "$HOME/Music/Ableton/User Library/MaxForLive/MDD___SNAKE_V3.2.3.amxd" \
     --output /tmp/desnivel-live-bass
   ```
2. Caricare `Desnivel_Bass.amxd` sulla traccia del basso prima del sintetizzatore o campionatore.
3. Avviare il ricevitore Python:
   ```sh
   python -m desnivel.cli.live_bass --preset responsive
   ```

Il processo Python ascolta lo stato di Snake sulla porta 9003, genera il piano della frase e lo invia a `Desnivel_Bass.amxd` sulla porta **9004** (`/desnivel/v1/player/bass/plan`). Il device Max for Live programma gli eventi tramite l'oggetto `timepoint`, garantendo precisione ritmica allineata al beat di Live.

