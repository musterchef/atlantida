# Architettura del sistema

Desnivel adotta un'architettura a pipeline modulare con separazione rigorosa tra:
1. **Dati fisici del viaggio** (oggettivi, neutrali e indipendenti dall'estetica).
2. **Interpretazione compositiva** (regole musicali, scale, contrappunto e dinamica).
3. **Adattamento e trasporto** (traduzione nei formati e protocolli di destinazione).
4. **Esecuzione sonora** (sintesi, campionamento e clock musicale in Ableton Live).

---

## Flusso generale

```text
Traccia GPX ──► [trip] Metriche neutre ──► [music] Generazione musicale ──► [adapters] ──► [sinks / OSC] ──► Ableton Live / M4L
```

| Modulo | Responsabilità | Package |
|---|---|---|
| **Analisi del viaggio** | Carica le tracce GPX, ricampiona a tempo costante e calcola le metriche fisiche (distanza, quota, pendenza, velocità, sforzo). | `src/desnivel/trip/` |
| **Generazione musicale** | Applica le scelte compositive: traduce metriche in pattern, modula scale e sezioni, genera frasi di accompagnamento (basso). | `src/desnivel/music/` |
| **Adattatori** | Converte strutture musicali astratte (`Pattern`, `Phrase`) nei parametri specifici dei dispositivi (Snake, player M4L). | `src/desnivel/adapters/` |
| **Trasporto** | Gestisce la trasmissione dei messaggi via rete OSC e il salvataggio dei log di acquisizione. | `src/desnivel/sinks/` |
| **Interfaccia CLI** | Entry point eseguibili da riga di comando o tramite launcher macOS per orchestrare replay e analisi. | `src/desnivel/cli/` |
| **Device Max for Live** | Ricevono i messaggi OSC all'interno di Ableton Live e controllano sequencer e strumenti sonori. | `m4l/` |

---

## Principi architetturali fondamentali

### 1. Separazione tra tempo del viaggio e tempo musicale
La velocità di scorrimento del viaggio (replay) e il tempo musicale (BPM) sono completamente indipendenti:
- Il replay della traccia può essere accelerato (es. a 30× o 50×) per condensare ore di pedalata in pochi minuti di ascolto.
- I BPM e la griglia ritmica (16th, terzine, beat) rimangono controllati dal trasporto di Ableton Live, garantendo stabilità metrica e perfetta sincronizzazione audio.

### 2. Neutralità delle metriche
Il modulo `trip` non produce note, accordi o parametri synth. Calcola solo grandezze fisiche scalari e continue. Le decisioni estetiche (come mappare una pendenza a una scala minore o a un aumento di densità) risiedono interamente in `music`.

### 3. Modelli musicali condivisi
La generazione musicale si basa su due strutture dati fondamentali:
- **`Pattern`**: sequenza discreta di passi (note e gate) associata a un intervallo temporale del viaggio.
- **`Phrase`**: insieme polifonico di eventi sonori, in cui ogni nota specifica attacco relativo (in beat), altezza MIDI (0–127), durata (in beat) e velocity (1–127).
- **`Plan`**: estensione di una `Phrase` che specifica beat assoluto di ingresso nel trasporto di Live, revisione del piano e sessione attiva, consentendo la pianificazione anticipata senza interruzioni sonore.

---

## Evoluzione: Director e Coordinator

Per orchestrare un organico con più voci indipendenti ma coerenti, l'architettura prevede due ruoli di coordinamento:

- **Music Director**: definisce il contesto espressivo comune della sezione (tonalità, percorsi modali, livello complessivo di tensione o densità ed equilibrio tra le voci).
- **Music Coordinator**: gestisce l'ordine di pianificazione, risolvendo le dipendenze tra strumenti (ad esempio passando al generatore del basso la melodia pianificata per consentirgli di dialogare o rispondere negli spazi).

---

## Organizzazione delle cartelle

- `src/desnivel/`: codice sorgente Python del pacchetto.
  - `music/<voce>/`: ogni voce o strumento ha una sottocartella dedicata (es. `music/bass/`).
- `tests/`: test automatici, speculari alla struttura di `src/`.
- `m4l/`: sorgenti e patch Max for Live (`.amxd`, `.js`, `.maxpat`).
- `tools/`: script per la costruzione e l'ispezione dei device Max for Live.
- `presets/`: configurazioni musicali delle tappe e delle regole.
- `comandi/`: launcher macOS per l'avvio rapido delle sessioni di ascolto.
- `doc/`: documentazione del sistema. I documenti storici o superati sono conservati in `doc/archivio/`.

---

## Riferimenti

- [Dati del viaggio e metriche GPX](DATI-VIAGGIO.md)
- [Sequencer Snake e ponte M4L](SNAKE.md)
- [Generatore del basso e controlli](BASSO.md)
- [Setup e comandi operativi](COMANDI.md)

