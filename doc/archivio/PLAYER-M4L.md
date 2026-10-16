# Player M4L

Sono disponibili un player ciclico di frasi e un player di piani sul trasporto Live.

## Player ciclico

Copiare `m4l/desnivel_phrase_player.js` e `.maxpat` nella stessa cartella. In Live aprire un Max MIDI Effect, sostituire gli oggetti del template con quelli del `.maxpat` e salvare il device accanto al JS.

La patch usa porta 9002 e voce `bass`, modificabili in `udpreceive` e `route`. Ogni istanza deve avere una porta distinta.

```sh
python -m desnivel.cli.send_phrase --phrase presets/phrases/bass_sustained.json --voice bass
```

La console mostra `queued 3`; avviando Live, `active 8`: tre note in un ciclo di otto beat. Durante il loop si può inviare `bass_rhythmic.json`: cinque note attivate al ciclo successivo. `--dry-run` stampa senza rete; `--host`, `--port`, `--voice` scelgono il destinatario.

### Esecuzione

JS valida le frasi e prepara gli eventi. `pipe` gestisce i ritardi in tick, `flush` chiude le note e `noteout` invia il MIDI. I note-off precedono i note-on simultanei. Il valore −1 marca la fine ciclo e passa attraverso `deferlow` per richiamare JS.

`live.observer is_playing` rileva Play/Stop. A Stop si cancella la coda e si spengono le note. `panic` svuota anche le frasi; `restart` riparte dalla frase se Live suona; `closebang` richiama panic.

La prima frase parte quando viene rilevato Play o arriva a trasporto attivo. Il player non è quantizzato a battuta e non si riallinea ai salti o al loop del trasporto. Il passaggio tra cicli via `deferlow` può introdurre ritardo: deriva e cambi BPM richiedono misure in Live.

## Protocollo

Datagramma OSC `/desnivel/v1/player/<voce>/phrase`:

```text
1, lunghezza_beat, numero_note,
beat, pitch, durata_beat, velocity, ...
```

Un beat è una semiminima; Max usa 480 tick per beat. Limiti: 32 note, MIDI 0–127, velocity 1–127, note interamente entro la frase. Sono ammesse sovrapposizioni di altezze diverse. Le sovrapposizioni della stessa altezza sono rifiutate.

La validazione precede la sostituzione del buffer. L'ultima frase ricevuta diventa la successiva; una frase vuota produce silenzio al cambio. UDP non garantisce consegna o ordine e non è implementato un ACK.

## Generare il basso

Da una melodia JSON:

```sh
.venv/bin/python -m desnivel.cli.compose_bass --melody /tmp/melodia.json --output /tmp/basso.json --preset responsive
```

L'output deve essere nuovo. `--previous-pitch` mantiene un riferimento di registro tra sezioni. Per generare dalla previsione di uno stato esplicito usare `--snake-state /tmp/stato.json --beats 8` al posto di `--melody`.

[Controlli e preset](SCELTE-BASSO.md#controlli-e-preset) · [Formato dello stato](EXPORT-SNAKE.md#messaggi)

## Basso collegato a Snake

Costruire i device dal vanilla ispezionato, in una cartella nuova:

```sh
python tools/build_live_bass.py   --source "$HOME/Music/Ableton/User Library/MaxForLive/MDD___SNAKE_V3.2.3.amxd"   --output /tmp/desnivel-live-bass
```

Caricare `MDD_SNAKE_LengthBank.amxd` sulla melodia e `Desnivel_Bass.amxd` prima dello strumento di accompagnamento. I JS sono incorporati. Attivare Export su una sola istanza e avviare:

```sh
python -m desnivel.cli.live_bass
```

`BassSession` prevede la frase e invia il piano sulla porta 9004, indirizzo `/desnivel/v1/player/bass/plan`. Il piano contiene sessione, seriale, revisione, beat iniziale e frase.

Con `--window 4 --lead 1`, l'ingresso è `ceil((beat + 1) / 4) × 4`. Il device mostra `pronto beat …` alla ricezione. `--window` e `--lead` regolano finestra e anticipo. Ctrl+C invia lo stop; dopo la ricarica del sequencer riavviare il ricevitore Python.

Il player ignora duplicati e piani superati, programma gli eventi con `timepoint` e li chiude con `flush` a Stop. Gli aggiornamenti riguardano finestre future e conservano i note-off già programmati.

[Vincoli della previsione](EXPORT-SNAKE.md#errori-e-limiti-attuali) · [Acquisizione](EXPORT-SNAKE.md#acquisizione) · [Controlli live](CONTROLLI-BASSO.md)

## Regolare il basso all'ascolto

Usare gli [assetti del launcher 08](TEST-PRESET-MUSICALI.md#firenze-con-il-basso). Confrontare lo stesso tratto modificando un controllo per volta, mantenendo Set, strumento, BPM, configurazione iniziale, velocità del replay e seed.

Le opzioni CLI valgono dall'avvio: fermare replay e ricevitore con Ctrl+C prima di cambiarle. Per aggiornamenti OSC usare il [contratto dei controlli](CONTROLLI-BASSO.md).

## Sorgenti

Modello: `music/phrases.py`. Protocollo: `adapters/phrase_player.py`. Player: `m4l/desnivel_phrase_player.js`, `m4l/desnivel_phrase_player.maxpat`, `m4l/desnivel_transport_player.js`.
