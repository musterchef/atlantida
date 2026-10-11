# Stato del progetto

Aggiornato l’11 ottobre 2026.

## Base verificata in Live

L’utente ha confermato i tre launcher in `comandi/`: Shape Gates 0, Shape Gates 13 e Firenze–San Gimignano a 150×. Snake suona e il replay funziona nella configurazione attuale. Questa conferma non misura la corrispondenza della previsione Python con il MIDI reale né la sincronizzazione del basso.

Usare il Set funzionante dell’utente. Il consolidamento non modifica Set, device installati o impostazioni di Ableton.

## Architettura e sorgenti

`GPX → metriche neutre → motore musicale Python → adattatori → strumenti`

- `journey_music.py` e i preset di tappa decidono motivo, armonia e densità. Il tempo del replay è distinto dal BPM di Live.
- `adapters/snake.py` traduce i pattern; `m4l/desnivel_snake_params.js` controlla il primo Snake trovato. Gates è risolto per nome `Gate_Shape` nella mod; l’indice 90 resta un ripiego per il vanilla a 152 parametri.
- `tools/build_snake_length.py` aggiunge Length al vanilla senza togliere Custom. Ogni durata segue la corrispondente cella Notes.
- `tools/build_live_bass.py` aggiunge la lettura dello stato e genera il player del basso. I device generati restano fuori dalla repository.
- `adapters/snake_sequence.py` ricostruisce una `Phrase`; `bass.py` genera il basso da una frase indipendente dalla sorgente; il player esegue piani sul trasporto Live.

## Confronto con i file installati

Cartella: `~/Music/Ableton/User Library/MaxForLive/desnivel`.

- `MDD_SNAKE_LengthBank.amxd`: oggetti, collegamenti e parametri coincidono con il builder, confrontati per ID indipendentemente dall’ordine nel JSON. Il JS incorporato coincide con il sorgente.
- `Desnivel_Bass.amxd`: documento generato e JS incorporato coincidono con i sorgenti.
- `desnivel_snake_params.js`: copia installata identica al sorgente.
- Bridge: il file installato aggiunge soltanto il messaggio diagnostico manuale `shapes 90` e relativo collegamento, oltre a metadati di finestra e percorso. Il sorgente mantiene la dipendenza JS relativa alla propria cartella; il messaggio diagnostico non viene importato.
- Vecchio player di frasi: eliminato dal sorgente un carattere iniziale spurio, allineandolo al JS installato. Il player assoluto del basso è un percorso distinto.

Il confronto riguarda i file su disco, non eventuali modifiche non salvate nel Set aperto.

## Implementato, da verificare

Previsione Snake e basso live sono conservati con i test pertinenti, ma non fanno parte delle tre prove confermate. La previsione supporta clock e Shape indipendenti, forwards/backwards, Shift visualizzato 1 e Swing 0. La telemetria legge le altezze già quantizzate e le fasi effettive; non anticipa modifiche future dello stato.

Il basso offre `responsive` e `follow`. Non deduce accordi certi dalla scala e non dispone ancora di un’armonia condivisa esplicita con il viaggio. I test automatici verificano il comportamento del modello; confronto con MIDI registrato, timing reale e qualità musicale restano aperti.

Sabaudia–Formia e Peschici–Mattinata sono preset d’uso richiesti dall’utente, verificati in generazione ma ancora da valutare all’ascolto.

## Verifiche e prossimo passo

Suite Python: 212 test passati, incluso il test UDP locale eseguito fuori dal sandbox. Quattro test JavaScript e sintassi dei tre launcher verificati. Nessun comando musicale inviato a Live durante il consolidamento.

Prossimo passo, quando richiesto: confrontare una breve registrazione MIDI di Snake con la previsione Python. Solo dopo valutare il basso sulla sequenza verificata.

## Istruzioni

- [Comandi e launcher](COMANDI.md)
- [Preset musicali](TEST-PRESET-MUSICALI.md)
- [Integrazione Snake e Length](INTEGRAZIONE-SNAKE.md)
- [Player e basso](PLAYER-M4L.md)
- [Architettura](DECISIONE-ARCHITETTURA-AUDIO.md)
