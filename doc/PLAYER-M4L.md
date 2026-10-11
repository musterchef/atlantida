# Player di frasi M4L

Python compone e invia frasi. JS valida e prepara gli eventi; gli oggetti Max `pipe`, `flush` e `noteout` gestiscono la coda temporale e le note MIDI. Non c'è polling del clock.

## Creare il device

1. Copiare `m4l/desnivel_phrase_player.js` e `m4l/desnivel_phrase_player.maxpat` nella cartella dove si salverà il device.
2. In Live inserire un **Max MIDI Effect** prima dello strumento e aprirlo nell'editor Max.
3. Aprire anche il `.maxpat`, sbloccarlo e copiarne tutti gli oggetti nel MIDI Effect. Rimuovere prima gli oggetti del template per non duplicare l'uscita MIDI.
4. Salvare il device come `desnivel-phrase-player.amxd`, accanto al JS. Chiudere l'editor.

La patch è predisposta per porta 9002 e voce `bass`. Sono impostazioni modificabili negli oggetti `udpreceive` e `route`, non dipendenze del player. Un'altra istanza deve usare una porta diversa.

## Collegamenti

La patch fornita contiene:

```text
OSC → route della voce → prepend phrase → JS
JS eventi → unpack pitch velocity ticks → pipe → pack → route -1
  eventi MIDI → unpack → flush → noteout
  fine ciclo → deferlow → messaggio cycle → JS
```

`unpack` invia prima il ritardo alla porta destra di `pipe`, poi velocity e infine pitch. I ritardi sono liste `<numero> ticks`. Il valore convenzionale -1 marca la fine del ciclo e non arriva a `noteout`. JS ordina note-off prima dei note-on alla stessa posizione e accoda il marcatore dopo gli ultimi note-off.

`live.path` risolve `live_set`; `live.observer is_playing` informa JS di avvio e stop. Non vengono salvati ID Live. Allo stop JS invia prima `clear` alla coda, poi un bang a `flush` per spegnere le note attive.

- `panic`: cancella eventi, spegne note, svuota frase attiva e successiva.
- `restart`: cancella eventi e riparte dalla frase, se Live è in riproduzione.
- `closebang`: richiama panic alla chiusura.
- `print phrase_player`: mostra ricezione e attivazione.

## Prova

```sh
source .venv/bin/activate
python -m desnivel.cli.send_phrase --phrase presets/phrases/bass_sustained.json --voice bass
```

Atteso: `queued 3`. Avviare Live: atteso `active 8`, frase di otto semiminime in loop.

Durante il loop:

```sh
python -m desnivel.cli.send_phrase --phrase presets/phrases/bass_rhythmic.json --voice bass
```

Atteso: `queued 5`, poi `active 8` alla fine della frase corrente. Fermare Live durante una nota lunga: deve spegnersi. Ripartire e provare panic. Dopo panic reinviare una frase.

Provare poi cambio BPM, loop del trasporto e più istanze. Prima di collegare il viaggio, registrare l'uscita MIDI per controllare durata dei cicli, note-off e continuità su almeno 32 ripetizioni.

`--dry-run` stampa senza rete. `--host`, `--port`, `--voice` selezionano il destinatario.

## Confini della versione

Gli eventi dentro ogni ciclo sono accodati in tick musicali negli oggetti nativi. JS interviene alla ricezione e al confine di frase. Il passaggio di fine ciclo attraverso `deferlow` mantiene JS fuori dal percorso delle singole note, ma può aggiungere ritardo tra cicli: la continuità e l'eventuale deriva devono essere misurate in Live. Non è dichiarata precisione al campione né prontezza per performance.

La prima frase parte quando il player rileva il trasporto attivo, oppure quando riceve la prima frase a trasporto già avviato. Non è ancora quantizzata a battuta. Il player esegue cicli relativi: non riallinea automaticamente la frase ai salti o al loop della posizione del brano. Usare stop/ripartenza o restart. Questi sono i prossimi requisiti temporali da risolvere, prima di aggiungere altre voci.

Cambi tempo, ordine effettivo degli eventi simultanei, notifica dello stop e scaricamento del device richiedono verifica in Live. I test simulati non verificano lo scheduler di Max.

## Protocollo

Un datagramma OSC: `/desnivel/v1/player/<voce>/phrase`, seguito da:

```text
1, lunghezza_beat, numero_note,
beat, pitch, durata_beat, velocity, ...
```

Un beat è una semiminima; i tick Max sono 480 per semiminima. La validazione avviene prima di cambiare il buffer in attesa. Ultima frase ricevuta vince. UDP non garantisce ordine o consegna; nessun ACK implementato. La console Max conferma la ricezione.

Limite del player: 32 note per datagramma, MIDI 0–127, velocity 1–127. Accordi e sovrapposizioni di altezze diverse ammessi; sovrapposizioni della stessa altezza e note oltre il ciclo rifiutate. Frase vuota significa silenzio al prossimo cambio.

## Codice e verifica

- `src/desnivel/phrases.py`: modello musicale.
- `src/desnivel/adapters/phrase_player.py`: protocollo e limiti della destinazione.
- `src/desnivel/cli/send_phrase.py`: invio di una frase JSON.
- `m4l/desnivel_phrase_player.js`: validazione, buffer e preparazione eventi.
- `m4l/desnivel_phrase_player.maxpat`: scheduling e MIDI.
- `presets/phrases/`: esempi, senza regole del viaggio.

Sei test Python passati. Test JS simulato: ordinamento degli eventi, note-off prima dei note-on, cambio frase, stop, ripartenza, panic e silenzio. Ricezione, notifiche Stop/Play e riproduzione della frase confermate dall’utente in Live il 2026-10-04. Restano da verificare sistematicamente cambio frase, deriva, cambi tempo e scaricamento del device.

Riferimenti ufficiali: [pipe](https://docs.cycling74.com/reference/pipe/) per code, tick e cancellazione; [Live Object Model](https://docs.cycling74.com/apiref/lom/song/) per lo stato del trasporto. L’osservatore usa l’argomento posizionale `live.observer is_playing`, come documentato in [live.observer](https://docs.cycling74.com/reference/live.observer/).


## Generare il basso

`desnivel.bass.generate_bass` riceve una `Phrase` da qualunque sorgente. La regola predefinita `responsive` costruisce appoggi e risposte ritmiche, usa le classi di altezza presenti nella melodia e mantiene la continuità di registro. Sceglie una nota di appoggio dalla durata e dagli accenti osservati, senza dichiararla tonica o dedurre accordi certi. Una frase melodica vuota produce silenzio. La regola `follow` conserva il comportamento iniziale, con attacchi e durate derivati dalla melodia. Registro, distanza minima fra attacchi, articolazione e rapporto di velocity sono configurabili. Una regola diversa può usare lo stesso contratto `Phrase → Phrase`, senza modificare il player o Snake.

Da una melodia JSON nel formato del player:

```sh
python -m desnivel.cli.compose_bass --melody /tmp/melodia.json --output /tmp/basso.json
```

Opzioni: `--lowest`, `--highest`, `--min-spacing` in beat, `--articulation`, `--velocity-ratio`, `--previous-pitch`, `--strategy`, `--seed`, `--variation-period`, `--max-hold` e `--grid`. `--previous-pitch` mantiene la continuità di registro fra sezioni. L'output deve essere un file nuovo. La generazione non invia MIDI e non eredita il limite di 32 note del protocollo del player.

## Previsione Snake

`adapters.snake_sequence.predict` traduce uno stato esplicito in una `Phrase`. Le 14 Shape sono state confrontate con il vanilla. Per generare un basso da quello stato:

```sh
python -m desnivel.cli.compose_bass --snake-state /tmp/snake-state.json --beats 8 --output /tmp/basso.json
```

Il JSON richiede:

- `notes`, `gates`, `velocities`, `lengths_ms`: 16 valori ciascuno, ordinati per cella. Le durate sono già convertite in millisecondi.
- `notes_lane`, `gates_lane`, `velocities_lane`: ciascuno contiene `shape` da 1 a 14, `speed` fra `32n`, `16n`, `8n`, `4n`, `2n`, `steps`, `direction` e `phase_beats`. La fase è il tempo musicale già trascorso nel ciclo all'inizio della finestra.
- `bpm` e `midi_offset`: tempo costante e differenza esplicita fra parametro Note e altezza MIDI.
- `swing`: al momento deve essere zero. Snake deve essere in Chromatic.

Il modello supporta forwards e backwards. Le altre direzioni e lo swing vengono rifiutati, senza approssimarli. Ogni attacco Gates legge le celle correnti di Notes e Velocity; Length usa la cella Notes. In caso di avanzamenti simultanei il modello legge i nuovi valori. Tronca le code al confine della finestra e chiude una nota se la stessa altezza viene riattaccata.

Verificati con test: percorsi, clock distinti, fasi, pause, durate e retrigger. La corrispondenza temporale con l'uscita MIDI reale resta da misurare. Il collegamento live descritto sotto acquisisce stato e fase dalla mod. La previsione resta basata sullo stato osservato: non anticipa modifiche manuali future o comandi del viaggio non ancora applicati.

## Basso collegato a Snake

Il percorso live usa due device: `MDD_SNAKE_LengthBank.amxd` sulla melodia e `Desnivel_Bass.amxd` prima dello strumento del basso. Il secondo sostituisce il player relativo per questa modalità. I JS sono incorporati nei device.

Per costruirli dal vanilla ispezionato, scegliendo una cartella di output nuova:

```sh
python tools/build_live_bass.py \
  --source "$HOME/Music/Ableton/User Library/MaxForLive/MDD___SNAKE_V3.2.3.amxd" \
  --output /tmp/desnivel-live-bass
```

Caricare i due device, attivare **Export** nel banco Length e avviare:

```sh
python -m desnivel.cli.live_bass
```

Avviare Live. Python annuncia il beat dal quale ha preparato il basso; il device mostra `pronto beat …` quando riceve il piano. Il primo ingresso avviene su un multiplo di quattro semiminime, con almeno una semiminima di anticipo per il calcolo. Il basso continua a ricevere nuove frasi mentre il programma rimane aperto. Ctrl+C invia lo stop al basso.

Per questa versione usare Direction forwards/backwards, Shift 1 e Swing 0 nei banchi Notes, Gates e Velocities. Le Shape e le velocità possono essere diverse. Le altezze esportate sono quelle già quantizzate da Snake: il collegamento live non presume la scala o l'offset MIDI. Attivare Export su una sola istanza; dopo aver ricaricato il device, riavviare il comando Python.

`--min-spacing` regola la distanza fra gli attacchi del basso; `--lowest` e `--highest` il registro. `--articulation` e `--velocity-ratio` regolano durata e dinamica. `--window` cambia la lunghezza delle frasi e `--lead` l'anticipo minimo. Sono impostazioni della prima regola, non vincoli del modello musicale.

Lo stato passa sulla porta 9003 e i piani sulla 9004. Le porte sono configurabili sia nel builder sia nella CLI. Ogni piano contiene sessione, seriale, revisione, beat iniziale e frase. Il player ignora duplicati e pacchetti superati; un nuovo piano non riavvia quello in corso. Gli eventi sono programmati da `timepoint` sul trasporto Live e chiusi da `flush` allo stop. L'aggiornamento non sostituisce i note-off già programmati con gli stessi valori.

Verificati con test Python, simulazioni JS e controllo dei container: previsione, generazione, pacchetti fuori ordine, stop, conservazione dei note-off e risorse incorporate. La verifica della sincronizzazione del basso in Live resta aperta. Cambi di tempo durante una nota e seek vicino a un evento richiedono misure reali. Le modifiche ai parametri influenzano le finestre future ancora programmabili, non riscrivono il passato o la frase già iniziata.

Riferimenti: [timepoint](https://docs.cycling74.com/reference/timepoint/) per gli eventi assoluti; [when](https://docs.cycling74.com/reference/when/) per la lettura del tempo in tick dall'uscita destra.

## Sviluppo del basso

La strategia `responsive` è attiva anche nel comando `live_bass`. Non richiede un nuovo device. L'indice della finestra musicale determina la variazione: reinviare lo stesso stato non cambia casualmente la frase. Il ciclo predefinito comprende quattro finestre; l'ultima favorisce il ritorno alla nota di appoggio. La melodia può cambiare note e densità durante il ciclo.

Il ritmo combina posizioni metriche e spazi fra gli attacchi melodici. Le durate del basso dipendono dai suoi attacchi successivi, con un massimo regolabile, anziché copiare automaticamente le note brevi di Snake. Appoggi e risposte hanno articolazioni e velocity diverse. Le note rimangono nelle classi di altezza osservate: questa strategia non dispone ancora di accordi dichiarati o di una tonica condivisa dal motore del viaggio.

```sh
python -m desnivel.cli.live_bass --strategy responsive
```

`--strategy follow` consente il confronto con la regola precedente. `--variation-period` regola il numero di finestre nel ciclo, `--seed` rende ripetibile la scelta ritmica, `--grid` la griglia candidata in beat e `--max-hold` la durata massima prima dell'articolazione. `--min-spacing` rimane la distanza minima fra gli attacchi. Il risultato musicale va valutato all'ascolto; i test verificano ripetibilità, variazioni, registro, dinamica e assenza di sovrapposizioni nel basso.
