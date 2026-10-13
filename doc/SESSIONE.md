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

## Stato del basso

La previsione Snake è stata confrontata con registrazioni MIDI e stati Export nelle configurazioni descritte sotto. Il basso live riceve lo stato e le fasi di Snake, prevede la frase e invia piani al player M4L. La corrispondenza di esecuzione è stata verificata nelle tre registrazioni descritte sotto; questo non valuta la qualità musicale. La previsione supporta clock e Shape indipendenti, forwards/backwards, Shift visualizzato 1 e Swing 0. La telemetria legge le altezze già quantizzate e le fasi effettive; non anticipa modifiche future dello stato.

Il basso offre tre strategie selezionabili: `responsive`, `follow` e `slap`. Quest’ultima aggiunge un groove più fitto, con colpi bassi sugli appoggi, risposte sincopate e possibili salti d’ottava nel registro configurato. Le altre due strategie restano disponibili. Nessuna strategia deduce accordi certi dalla scala né usa ancora un’armonia condivisa esplicita con il viaggio. La valutazione musicale di `slap` in Ableton resta da fare all’ascolto.

Sabaudia–Formia e Peschici–Mattinata sono preset d’uso richiesti dall’utente, verificati in generazione ma ancora da valutare all’ascolto.

## Verifiche e prossimo passo

Al consolidamento dell’11 ottobre: 212 test Python passati, incluso il test UDP locale eseguito fuori dal sandbox. Quattro test JavaScript e sintassi dei tre launcher verificati. Nessun comando musicale inviato a Live durante il consolidamento.

Prossimo passo: ascoltare in Live la strategia `slap` con Snake e confrontarla, a parità di Set e melodia, con `responsive` e `follow`. Le prove di seek, cambi di stato e combinazioni rare restano secondarie finché non servono all’uso concreto.

## Istruzioni

- [Comandi e launcher](COMANDI.md)
- [Preset musicali](TEST-PRESET-MUSICALI.md)
- [Integrazione Snake e Length](INTEGRAZIONE-SNAKE.md)
- [Player e basso](PLAYER-M4L.md)
- [Architettura](DECISIONE-ARCHITETTURA-AUDIO.md)

## Verifica Export e MIDI del 12 ottobre

Confrontati 85 snapshot Export con la registrazione simultanea MIDI a 94 BPM: Notes Shape 3, 5 Steps, backwards a 8n; Gates Shape 1 a 16n con seconda cella spenta; Velocities Shape 1 a 8n con quattro livelli; Length 265 ms.

Il confronto ha rilevato un errore numerico nel modello ai confini di step: il modulo dei cicli produceva fasi float differenti di circa 1e-16 beat. `Lane.cell_at` ora riconosce un confine entro 1e-9 beat; un test verifica che gli istanti realmente precedenti restino nella cella precedente. Nessuna modifica ai device o ai dati registrati.

Dopo la correzione, 585 confronti su finestre future coprono 60 note distinte senza differenze di attacco, altezza o velocity; durate entro un tick del MIDI a 96 PPQ. La prima nota precede il primo snapshot e l’ultima, al bordo dello stop, è esclusa dal confronto. Nessun riallineamento della fase ricavato dal MIDI. Passati 19 test pertinenti di acquisizione, previsione e basso. Questa prova verifica Export nella configurazione indicata, non cambi di stato, seek o comportamento del player.

Le prove MIDI precedenti confermano Shape Notes 1 e 3, pause dei Gates, clock indipendenti Notes/Velocities a 8n e Gates a 16n, Length per cella, velocity variabili, Notes con 5 Steps forwards/backwards e riattacchi con durata 265 ms. La deriva temporale della prima registrazione resta non spiegata e non riprodotta. File MIDI, acquisizioni e script di confronto temporanei restano fuori dalla repository.

## Confronto del player del basso

Analizzate tre coppie MIDI Snake/basso con l’acquisizione più recente del launcher 07. I contenuti corrispondono all’epoca 57 con origini locali delle clip ai beat assoluti 0, 20 e 36. Queste origini sono dedotte dal confronto, non contenute nei MIDI: la corrispondenza è confermata separatamente dalle note, velocity e durate di Snake e dai piani del basso.

Risultato: 31/31 note del basso e 129/130 note Snake compatibili con i piani/stati, entro un tick MIDI a 96 PPQ, considerando i tagli ai bordi delle registrazioni. La prima nota Snake precede il primo snapshot. Le coppie 2 e 3 includono note iniziate prima del bordo sinistro; non sono note extra del player. Non rilevata deriva progressiva nei segmenti confrontati.

Conclusione: esecuzione dei piani del basso verificata nelle tre registrazioni, con il limite temporale di un tick (circa 6,65 ms a 94 BPM). Non è una verifica indipendente della posizione assoluta delle clip, né certifica Stop/ripartenza: l’utente non ha dichiarato di aver effettuato quei comandi. Le transizioni di trasporto nel log non vengono attribuite ad azioni dell’utente.

## Passaggio di consegne: prova slap

Il 12 ottobre è stata aggiunta `slap` in `bass.py`, esposta da `live_bass` e `compose_bass`; `responsive` e `follow` non sono state modificate. Il groove usa suddivisioni a ottavi, varia il disegno ogni quattro beat e accorcia le risposte sincopate. Quando il registro lo consente, alterna note basse e risposte un’ottava sopra. Il MIDI definisce le note, non il timbro slap dello strumento.

Verifiche mirate: 12 test passati fra basso, acquisizione live e device; diagnostica Python senza errori. Su una frase artificiale di quattro beat, `slap` genera 6–8 attacchi contro 3 con `responsive` e 4 con `follow`. Sono verifiche del codice e del ritmo generato, non dell’ascolto in Ableton.

Per riprendere la prova dal vivo, con il Set funzionante e Export attivo, avviare il launcher 07 con:

```sh
./comandi/07\ -\ Basso\ e\ acquisizione.command --strategy slap --highest 59
```

Poi avviare il replay Firenze già documentato in [Comandi](COMANDI.md) o [Preset musicali](TEST-PRESET-MUSICALI.md). Per confrontare le strategie, fermare replay e launcher e riavviarli con `--strategy responsive` e poi `--strategy follow`, lasciando invariati Set, configurazione Snake e replay. Il valore `--highest 59` amplia il registro per rendere possibili le risposte d’ottava. Non avviare insieme i ricevitori 05/06: condividono la porta 9003 con `live_bass`.

Il 13 ottobre lo stato è stato consolidato con acquisizione JSONL, modalità keep-open, launcher 06/07 e strategia slap. Verifica del consolidamento: 22 test mirati passati su basso, acquisizione, pianificazione live e device; sintassi dei launcher 06/07 verificata. Non è un’esecuzione dell’intera suite. Acquisizioni e MIDI restano fuori dalla repository.
