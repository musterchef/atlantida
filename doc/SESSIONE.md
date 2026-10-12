# Stato del progetto

Aggiornato il 12 ottobre 2026.

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

La previsione Snake è stata confrontata con registrazioni MIDI e stati Export nelle configurazioni descritte sotto. La sincronizzazione del basso live resta da verificare. La previsione supporta clock e Shape indipendenti, forwards/backwards, Shift visualizzato 1 e Swing 0. La telemetria legge le altezze già quantizzate e le fasi effettive; non anticipa modifiche future dello stato.

Il basso offre `responsive` e `follow`. Non deduce accordi certi dalla scala e non dispone ancora di un’armonia condivisa esplicita con il viaggio. Per il basso restano aperti il confronto con MIDI registrato, il timing reale e la qualità musicale.

Sabaudia–Formia e Peschici–Mattinata sono preset d’uso richiesti dall’utente, verificati in generazione ma ancora da valutare all’ascolto.

## Verifiche e prossimo passo

Al consolidamento dell’11 ottobre: 212 test Python passati, incluso il test UDP locale eseguito fuori dal sandbox. Quattro test JavaScript e sintassi dei tre launcher verificati. Nessun comando musicale inviato a Live durante il consolidamento.

Prossime verifiche: cambi di stato, stop/ripartenza e seek nel collegamento live; poi sincronizzazione del basso.

## Istruzioni

- [Comandi e launcher](COMANDI.md)
- [Preset musicali](TEST-PRESET-MUSICALI.md)
- [Integrazione Snake e Length](INTEGRAZIONE-SNAKE.md)
- [Player e basso](PLAYER-M4L.md)
- [Architettura](DECISIONE-ARCHITETTURA-AUDIO.md)

## Verifica Export e MIDI del 12 ottobre

Confrontati 85 snapshot Export con la registrazione simultanea MIDI a 94 BPM: Notes Shape 3, 5 Steps, backwards a 8n; Gates Shape 1 a 16n con seconda cella spenta; Velocities Shape 1 a 8n con quattro livelli; Length 265 ms.

Il confronto ha rilevato un errore numerico nel modello ai confini di step: il modulo dei cicli produceva fasi float differenti di circa 1e-16 beat. `Lane.cell_at` ora riconosce un confine entro 1e-9 beat; un test verifica che gli istanti realmente precedenti restino nella cella precedente. Nessuna modifica ai device o ai dati registrati.

Dopo la correzione, 585 confronti su finestre future coprono 60 note distinte senza differenze di attacco, altezza o velocity; durate entro un tick del MIDI a 96 PPQ. La prima nota precede il primo snapshot e l’ultima, al bordo dello stop, è esclusa dal confronto. Nessun riallineamento della fase ricavato dal MIDI. Passati 19 test pertinenti di acquisizione, previsione e basso. Questa prova verifica Export nella configurazione indicata, non ancora cambi di stato, seek o sincronizzazione del player del basso.

Le prove MIDI precedenti confermano Shape Notes 1 e 3, pause dei Gates, clock indipendenti Notes/Velocities a 8n e Gates a 16n, Length per cella, velocity variabili, Notes con 5 Steps forwards/backwards e riattacchi con durata 265 ms. La deriva temporale della prima registrazione resta non spiegata e non riprodotta. File MIDI, acquisizioni e script di confronto temporanei restano fuori dalla repository.
