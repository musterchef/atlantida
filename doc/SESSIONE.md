# Stato del progetto

Stato aggiornato al 15 ottobre 2026.

## Base verificata in Live

L’utente ha confermato i tre launcher in `comandi/`: Shape Gates 0, Shape Gates 13 e Firenze–San Gimignano a 150×. Snake suona e il replay funziona nella configurazione attuale. Questa conferma non misura la corrispondenza della previsione Python con il MIDI reale né la sincronizzazione del basso.

Per le prove usare il Set con bridge, Snake con Export e player del basso descritti nelle guide operative.

## Architettura e sorgenti

`GPX → metriche neutre → motore musicale Python → adattatori → strumenti`

- `journey_music.py` e i preset di tappa decidono motivo, armonia e densità. Il tempo del replay è distinto dal BPM di Live.
- `adapters/snake.py` traduce i pattern; `m4l/desnivel_snake_params.js` controlla il primo Snake trovato. Gates è risolto per nome `Gate_Shape` nella mod; l’indice 90 resta un ripiego per il vanilla a 152 parametri.
- `tools/build_snake_length.py` aggiunge Length al vanilla senza togliere Custom. Ogni durata segue la corrispondente cella Notes.
- `tools/build_live_bass.py` aggiunge la lettura dello stato e genera il player del basso. I device generati restano fuori dalla repository.
- `adapters/snake_sequence.py` ricostruisce una `Phrase`; `bass.py` genera il basso da una frase indipendente dalla sorgente; il player esegue piani sul trasporto Live.

## Confronto dei file dell’11 ottobre

Cartella: `~/Music/Ableton/User Library/MaxForLive/desnivel`.

- `MDD_SNAKE_LengthBank.amxd`: oggetti, collegamenti e parametri coincidono con il builder, confrontati per ID indipendentemente dall’ordine nel JSON. Il JS incorporato coincide con il sorgente.
- `Desnivel_Bass.amxd`: documento generato e JS incorporato coincidono con i sorgenti.
- `desnivel_snake_params.js`: copia installata identica al sorgente.
- Bridge: il file installato aggiunge soltanto il messaggio diagnostico manuale `shapes 90` e relativo collegamento, oltre a metadati di finestra e percorso. Il sorgente mantiene la dipendenza JS relativa alla propria cartella; il messaggio diagnostico non viene importato.
- Vecchio player di frasi: eliminato dal sorgente un carattere iniziale spurio, allineandolo al JS installato. Il player assoluto del basso è un percorso distinto.

Il confronto riguarda i file su disco, non eventuali modifiche non salvate nel Set aperto.

## Stato del basso

La previsione Snake è stata confrontata con registrazioni MIDI e stati Export nelle configurazioni descritte sotto. Il basso live riceve lo stato e le fasi di Snake, prevede la frase e invia piani al player M4L. La corrispondenza di esecuzione è stata verificata nelle tre registrazioni descritte sotto; questo non valuta la qualità musicale. La previsione supporta clock e Shape indipendenti, forwards/backwards, Shift visualizzato 1 e Swing 0. La telemetria legge le altezze già quantizzate e le fasi effettive; non anticipa modifiche future dello stato.

Il basso usa un generatore parametrico unico, con preset `responsive`, `follow` e `slap`. Controlli e valori sono descritti in [Player M4L](PLAYER-M4L.md#generare-il-basso). Non dispone ancora di un’armonia condivisa esplicita con il viaggio. I controlli e i pesi musicali restano da valutare all’ascolto.

Sabaudia–Formia e Peschici–Mattinata sono preset d’uso richiesti dall’utente, verificati in generazione ma ancora da valutare all’ascolto.

## Verifiche e prossimo passo

Le verifiche automatiche più recenti registrate sono riportate nella sezione [Controlli del basso durante l’esecuzione](#controlli-del-basso-durante-lesecuzione).

Prossimo passo: ascoltare il generatore parametrico con Snake, a parità di Set e melodia, modificando un controllo per volta. Le prove di seek, cambi di stato e combinazioni rare restano secondarie finché non servono all’uso concreto.

## Istruzioni

- [Comandi e launcher](COMANDI.md)
- [Preset musicali](TEST-PRESET-MUSICALI.md)
- [Integrazione Snake e Length](INTEGRAZIONE-SNAKE.md)
- [Player e basso](PLAYER-M4L.md)
- [Architettura](TODO-ARCHITECTURE.md)

## Verifica Export e MIDI del 12 ottobre

Confrontati 85 snapshot Export con la registrazione simultanea MIDI a 94 BPM: Notes Shape 3, 5 Steps, backwards a 8n; Gates Shape 1 a 16n con seconda cella spenta; Velocities Shape 1 a 8n con quattro livelli; Length 265 ms.

Il confronto ha rilevato un errore numerico nel modello ai confini di step: il modulo dei cicli produceva fasi float differenti di circa 1e-16 beat. `Lane.cell_at` ora riconosce un confine entro 1e-9 beat; un test verifica che gli istanti realmente precedenti restino nella cella precedente. Nessuna modifica ai device o ai dati registrati.

Dopo la correzione, 585 confronti su finestre future coprono 60 note distinte senza differenze di attacco, altezza o velocity; durate entro un tick del MIDI a 96 PPQ. La prima nota precede il primo snapshot e l’ultima, al bordo dello stop, è esclusa dal confronto. Nessun riallineamento della fase ricavato dal MIDI. Passati 19 test pertinenti di acquisizione, previsione e basso. Questa prova verifica Export nella configurazione indicata, non cambi di stato, seek o comportamento del player.

Le prove MIDI precedenti confermano Shape Notes 1 e 3, pause dei Gates, clock indipendenti Notes/Velocities a 8n e Gates a 16n, Length per cella, velocity variabili, Notes con 5 Steps forwards/backwards e riattacchi con durata 265 ms. La deriva temporale della prima registrazione resta non spiegata e non riprodotta. File MIDI, acquisizioni e script di confronto temporanei restano fuori dalla repository.

## Confronto del player del basso

Analizzate tre coppie MIDI Snake/basso con l’acquisizione più recente del launcher 07. I contenuti corrispondono all’epoca 57 con origini locali delle clip ai beat assoluti 0, 20 e 36. Queste origini sono dedotte dal confronto, non contenute nei MIDI: la corrispondenza è confermata separatamente dalle note, velocity e durate di Snake e dai piani del basso.

Risultato: 31/31 note del basso e 129/130 note Snake compatibili con i piani/stati, entro un tick MIDI a 96 PPQ, considerando i tagli ai bordi delle registrazioni. La prima nota Snake precede il primo snapshot. Le coppie 2 e 3 includono note iniziate prima del bordo sinistro; non sono note extra del player. Non rilevata deriva progressiva nei segmenti confrontati.

Conclusione: esecuzione dei piani del basso verificata nelle tre registrazioni, con il limite temporale di un tick (circa 6,65 ms a 94 BPM). Non è una verifica indipendente della posizione assoluta delle clip, né certifica Stop/ripartenza: l’utente non ha dichiarato di aver effettuato quei comandi. Le transizioni di trasporto nel log non vengono attribuite ad azioni dell’utente.

## Basso parametrico

Il generatore usa un percorso unico: selezione degli attacchi, scelta delle altezze e articolazione. I preset inizializzano controlli sovrascrivibili; le CLI offline e live condividono le opzioni musicali. Previsione Snake e protocollo del player restano invariati. `BassSession.set_settings` interpola i controlli nelle finestre future; le opzioni CLI definiscono i valori iniziali.

La verifica MIDI precedente riguarda l'esecuzione dei piani, non certifica la qualità musicale del nuovo generatore. Per ascoltarlo usare il launcher 07 e il replay Firenze, senza altri ricevitori sulla porta 9003. Parametri ed esempio corrente in [Player M4L](PLAYER-M4L.md#generare-il-basso). Modificare un controllo per volta e raccogliere il feedback musicale dell'utente.

Verifica automatica: 240 test Python passati, escluso `test_trip_metrics_wire.py`, che usa un socket UDP reale e riguarda il contratto delle metriche del viaggio. Verificati anche parametri espliciti nel launcher live tramite client simulato, metadati risolti dell'acquisizione, transizioni per finestre ed epoche e limiti comuni ai preset. Nessun ascolto o nuova registrazione in Live.

Disponibile anche l'[analisi della tappa su richiesta](TEST-PRESET-MUSICALI.md#suggerire-il-basso-dalla-tappa): genera automaticamente un suggerimento da provare, senza applicarlo al basso live. Verifica mirata dell'aggiunta: 40 test passati su analisi, composizione del viaggio e generazione del basso. Gli assetti del launcher 08 restano il percorso principale d'ascolto.


## Controlli del basso durante l'esecuzione

`live_bass` riceve aggiornamenti parziali dei parametri su un indirizzo OSC distinto dallo stato Snake, usando la stessa porta. Il contratto è indipendente dalla sorgente e il cambio viene validato per intero. Le transizioni conservano le destinazioni già richieste; messaggi duplicati o superati vengono ignorati e quelli non validi lasciano i piani invariati. [Formato e tempi di applicazione](CONTROLLI-BASSO.md).

Il mittente dei controlli e l'andamento musicale della tappa restano da implementare. Verifica automatica: 274 test Python passati, escluso il test UDP reale delle metriche del viaggio. Il ricevitore dei nuovi controlli è verificato con client e server simulati, inclusi cambi graduali e senza interpolazione, rifiuti, ordine e acquisizione. Nessun controllo inviato a Live dall'assistente; l'effetto musicale resta da ascoltare.


## Verifica del 15 ottobre

Passati tutti i 275 test Python: 274 nel sandbox e il test UDP locale eseguito separatamente con i permessi di rete necessari. Verificati la sintassi Bash del launcher 08, i collegamenti locali della documentazione e l’assenza di errori di spaziatura nel diff. Nessuna nuova prova in Live.

## Riordino per lo sviluppo

La pipeline `/mod/*`, il bridge MIDI CC, le utility geografiche, i prototipi GoPro/TouchDesigner e i rispettivi test sono raccolti in [archivio/](../archivio/README.md). Il pacchetto corrente mantiene loader GPX, metriche neutrali, composizione del viaggio, generatore del basso, adattatori Snake e player M4L. Configurazione e dipendenze di sviluppo sono ridotte ai componenti attivi.

Dopo il riordino passano 119 test Python: 118 nel sandbox e il test UDP locale eseguito separatamente con i permessi necessari. Passano anche i quattro controlli JavaScript in `tests/js/`. I 156 test della pipeline precedente sono conservati nell’archivio, esclusi dalla suite corrente. Director e Coordinator restano da implementare; nessuna nuova prova in Live.

Verificati senza invii di rete il producer su Levanto–La Spezia e il replay Firenze con il preset misto: 99 pattern e 3271 comandi OSC generati. I 151 file versionati spostati coincidono byte per byte con gli originali.
