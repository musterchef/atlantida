# Regole di lavoro

## Repository e commit
- Titoli commit in forma nominale, lettera iniziale minuscola (es. «aggiunta di…», «correzione di…»). Indicare chiaramente l'oggetto.
- Committare solo file necessari (codice, configurazioni, documentazione essenziale). No script usa e getta, log, dump o output temporanei.
- Esaminare il diff prima di committare. Mai commit automatici senza richiesta esplicita.
- Mantenere i commit atomici e circoscritti a una modifica logica.

## Scrittura del codice e architettura
- Codice semplice, modulare, leggibile e privo di astrazioni premature o workaround.
- Correggere la causa reale del problema, non aggiungere fallback difensivi silenziosi.
- Separare le responsabilità:
  - `src/desnivel/trip/`: lettura GPX e metriche neutre.
  - `src/desnivel/music/`: logica compositiva multivoce agnostica. Ogni voce ha una propria cartella (es. `music/bass/`).
  - `src/desnivel/adapters/`: traduzione verso destinazioni e device specifici.
  - `src/desnivel/sinks/`: trasporto (OSC, file di cattura).
  - `src/desnivel/cli/`: entry point per comandi e sessioni.
  - `m4l/`, `tools/`, `comandi/`: rispettivamente sorgenti Max, builder e launcher macOS.
- Mantenere i modelli musicali (`Pattern`, `Phrase`) indipendenti dai dispositivi di destinazione.

## Principi di sistema e banchi di prova
- Desnivel è un motore di musica generativa multivoce agnostico basato su dati GPX.
- Non identificare mai il sistema con i singoli strumenti o le prove specifiche all'interno di Ableton Live (es. Snake o il generatore del basso): sono solo un banco di prova iniziale per l'ascolto e la verifica del dialogo polifonico, non il confine del sistema.

## Documentazione
- Chiara, concisa, oggettiva, nella lingua richiesta.
- Descrivere il sistema reale, non ipotesi future o cronologia di soluzioni scartate.
- Evitare formulazioni difensive, ridondanze e gergo stereotipato da AI.
- Preservare i nomi originali dei file (mai suffissi come FINAL o UPDATED). Spostare i file superati in `doc/archivio/` aggiornando i relativi riferimenti.

## Modalità operativa
- Interpretare l'intento ed estrarre il principio generale senza riprogettare o estendere il sistema oltre la richiesta.
- Privilegiare modifiche concrete e verificabili; comunicare sinteticamente cosa è stato fatto ed esito dei controlli.