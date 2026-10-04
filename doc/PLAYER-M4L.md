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

