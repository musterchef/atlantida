# Player di frasi M4L

Sono disponibili due percorsi: il player ciclico per frasi inviate con `send_phrase` e il player a piani assoluti usato dal [basso live](#basso-collegato-a-snake). Le sezioni fino a «Codice e verifica» descrivono il player ciclico.

Nel player ciclico Python invia frasi, JS valida e prepara gli eventi e gli oggetti Max `pipe`, `flush` e `noteout` gestiscono la coda temporale e le note MIDI.

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

Per verificare il player ciclico, registrare l’uscita MIDI e controllare durata dei cicli, note-off e continuità su almeno 32 ripetizioni; provare anche cambi BPM e più istanze.

`--dry-run` stampa senza rete. `--host`, `--port`, `--voice` selezionano il destinatario.

## Confini della versione

Gli eventi dentro ogni ciclo sono accodati in tick musicali negli oggetti nativi. JS interviene alla ricezione e al confine di frase. Il passaggio di fine ciclo attraverso `deferlow` mantiene JS fuori dal percorso delle singole note, ma può aggiungere ritardo tra cicli: la continuità e l'eventuale deriva devono essere misurate in Live. Non è dichiarata precisione al campione né prontezza per performance.

La prima frase parte quando il player rileva il trasporto attivo, oppure quando riceve la prima frase a trasporto già avviato. Non è ancora quantizzata a battuta. Il player esegue cicli relativi: non riallinea automaticamente la frase ai salti o al loop della posizione del brano. Usare stop/ripartenza o restart.

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

`desnivel.bass.generate_bass` riceve una `Phrase` da qualunque sorgente e restituisce una frase di basso. Un solo percorso seleziona gli attacchi, sceglie le altezze e determina durate e velocity. Snake, OSC e player restano fuori dal generatore.

`--preset responsive`, `follow` e `slap` forniscono valori iniziali; `--strategy` resta un alias. I controlli espliciti prevalgono sul preset. Il MIDI non definisce il timbro slap dello strumento.

| Controllo | Effetto |
|---|---|
| `--density` | Attacchi desiderati per beat nella parte di frase successiva al primo attacco melodico. Zero produce silenzio; griglia e distanza minima limitano il numero realizzabile. |
| `--syncopation` | Da 0 a 1: preferenza dagli appoggi sui beat ai levare, conservando un primo appoggio. |
| `--rhythm-follow` | Da 0 a 1: risposte negli spazi oppure attacchi condivisi con la melodia. A 1 si usano solo gli attacchi melodici e si riprendono le durate sorgenti entro i limiti. |
| `--melody-follow` | Da 0 a 1: linea costruita sulle altezze rilevanti della frase oppure nota melodica più vicina. |
| `--lowest`, `--highest` | Limiti MIDI inclusivi; almeno dodici altezze consecutive. |
| `--mobility` | Da 0 a 1: movimento vicino alla nota precedente oppure maggiore apertura del registro, con risposte acute sui levare. Non impone ottave. |
| `--articulation` | Frazione della durata disponibile, maggiore di 0 e fino a 1. |
| `--variation` | Da 0 a 1: ampiezza delle variazioni nelle preferenze ritmiche e nelle altezze. A 0 gli stessi dati producono la stessa frase a ogni indice. |

Densità e sincopazione hanno compiti distinti: la prima regola quante note cercare, la seconda dove collocarle. I legami ritmico e melodico sono indipendenti. Tutti i preset rispettano `--min-spacing` in beat, `--grid` per le posizioni candidate, `--max-hold` per la durata massima e `--velocity-ratio` per la dinamica. Le durate non oltrepassano l'attacco successivo o il bordo della frase.

| Preset | Densità | Sincopi | Legame ritmico | Legame melodico | Mobilità | Variazione | Distanza minima | Articolazione |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `responsive` | 0,8 | 0,25 | 0,35 | 0,25 | 0,15 | 0,35 | 1 beat | 0,9 |
| `follow` | 4 | 0 | 1 | 1 | 0 | 0 | 1 beat | 0,9 |
| `slap` | 1,8 | 0,7 | 0,15 | 0,5 | 0,85 | 0,5 | 0,5 beat | 0,5 |

Una frase melodica vuota produce silenzio. Le altezze restano nelle classi osservate; l'appoggio è stimato da durata e accenti, senza dedurre una tonica o accordi certi.

Esempio live, con registro aperto e densità ridotta rispetto al preset:

```sh
./comandi/07\ -\ Basso\ e\ acquisizione.command --preset slap --highest 59 --density 1.2 --mobility .6
```

Da una melodia JSON nel formato del player:

```sh
.venv/bin/python -m desnivel.cli.compose_bass --melody /tmp/melodia.json --output /tmp/basso.json --preset responsive --syncopation .6
```

`--previous-pitch`, disponibile in `compose_bass`, mantiene la continuità di registro fra sezioni. L'output deve essere un file nuovo. La generazione non invia MIDI e non eredita il limite di 32 note del protocollo del player.

## Regolare il basso all'ascolto

Per motivazioni dei preset, pesi musicali e punti del codice da modificare: [Scelte del basso](SCELTE-BASSO.md).

Partire dall'assetto del comando live sopra. I valori effettivi sono: registro 28–59, densità 1,2, sincopazione 0,7, legame ritmico 0,15, legame melodico 0,5, mobilità 0,6, variazione 0,5, articolazione 0,5. La distanza minima è 0,5 beat, la griglia 0,5 beat, la durata massima 2 beat e il rapporto velocity 0,9. Un beat è una semiminima, indipendentemente dai BPM.

Questi sono punti di partenza per il confronto, non valori già validati musicalmente.

### Come confrontare

1. Ascoltare un tratto del replay Firenze e scegliere un solo problema concreto: troppe note, poco movimento, note troppo lunghe o eccessivo legame con la melodia.
2. Fermare replay e launcher 07 con Ctrl+C. Riavviare il launcher con il parametro modificato, poi lo stesso replay dall'inizio. Lasciare invariati Set, suono del basso, BPM, configurazione iniziale Snake, velocità del replay e seed.
3. Confrontare lo stesso tratto. Conservare la modifica se aiuta, altrimenti tornare al valore precedente. Solo dopo passare a un altro controllo.

Le opzioni si leggono all'avvio: scriverle nel terminale mentre il ricevitore gira non le aggiorna. Nel comando, sostituire il valore già presente oppure aggiungere un'opzione assente. Usare il punto per i decimali: `--density 1.2`. Tenere spenti i ricevitori 05/06, che condividono la porta 9003.

### Quale controllo muovere

| Se all'ascolto… | Prima prova | Cosa confrontare |
|---|---|---|
| Il basso riempie troppo | `--density .8` invece di `1.2` | Più spazio fra gli attacchi, senza cercare un nuovo registro. |
| Il basso è troppo rarefatto | `--density 1.6` | Più attacchi; oltre il limite della distanza minima l'aumento può non produrre altre note. |
| I levare sono troppo insistenti | `--syncopation .3` invece di `.7` | Più preferenza per gli appoggi sui beat, a densità invariata. |
| Il ritmo è troppo appoggiato | `--syncopation .9` | Più preferenza per i levare; il primo appoggio resta. |
| Vuoi condividere più attacchi con Snake | `--rhythm-follow .6` invece di `.15` | Maggiore coincidenza degli attacchi e durate più legate alla melodia. |
| Vuoi più risposte fra gli attacchi di Snake | `--rhythm-follow 0` | Maggiore preferenza per gli spazi disponibili sulla griglia. |
| Le altezze raddoppiano troppo la melodia | `--melody-follow .2` invece di `.5` | Più peso agli appoggi della frase e alla compatibilità con le note simultanee. |
| Vuoi seguire di più le altezze locali | `--melody-follow .8` | Più peso alla classe di altezza della nota melodica vicina. |
| I salti sono troppo evidenti | `--mobility .2` invece di `.6` | Movimento più vicino alla nota precedente, mantenendo il registro disponibile. |
| Vuoi aprire le risposte acute | `--mobility .9` | Maggiore contrasto di registro fra appoggi e levare, quando le altezze disponibili lo consentono. |
| Le note sono troppo lunghe | `--articulation .3` invece di `.5` | Attacchi più separati; il numero di note resta uguale. |
| Le note sono troppo secche | `--articulation .8` | Maggiore sostegno fra gli attacchi, entro la durata massima. |
| Le scelte fra frasi cambiano troppo | `--variation .2` invece di `.5` | Preferenze più stabili; a 0 si elimina la variazione fra indici per gli stessi dati e nota precedente. |
| Il disegno resta troppo prevedibile | `--variation .8` | Più varietà nelle scelte, senza aumentare direttamente la densità. |
| La dinamica è troppo forte rispetto a Snake | `--velocity-ratio .7` invece di `.9` | Velocity MIDI più basse; il volume dipende anche dallo strumento. |

### Limiti e interazioni

La densità è un obiettivo, non un conteggio garantito: `1.2` cerca circa cinque attacchi in quattro beat se la melodia entra subito. Con `--min-spacing .5` non si possono superare otto attacchi in quattro beat. Il numero viene arrotondato, quindi piccoli cambiamenti possono lasciare invariato il risultato.

La griglia aggiunge posizioni candidate e non sposta gli attacchi originali della melodia. `--grid .5` propone gli ottavi; `.25` propone i sedicesimi. Per consentire note più vicine di mezzo beat occorre ridurre anche `--min-spacing`, per esempio a `.25`. Prima regolare la densità; cambiare griglia e distanza solo se serve una suddivisione più fine.

Sincopazione e legame ritmico possono spingere in direzioni diverse. Con `--rhythm-follow 1` restano solo gli attacchi della melodia: la sincopazione può scegliere fra quelli disponibili, ma non inventare levare assenti. Se tutte le posizioni disponibili sono già occupate dal basso, cambiare la sincopazione può non cambiare gli attacchi.

Il registro definisce dove il basso può suonare; la mobilità decide quanto sfruttarlo. Per un confronto più raccolto provare `--highest 47`, lasciando `--lowest 28`: le risposte acute avranno meno spazio. Aumentare `--highest` non impone salti d'ottava e non traspone tutte le note. I numeri MIDI evitano le diverse convenzioni di nomi delle ottave: 36 è Do, 48 è il Do un'ottava sopra, 59 è Si.

`--max-hold` limita la durata disponibile prima dell'articolazione. Con `--max-hold 2 --articulation .5` una nota dura al massimo un beat; l'attacco successivo o il legame ritmico possono accorciarla ancora. Articolazione e velocity non cambiano il timbro dello strumento.

Durante il replay, Snake può cambiare la frase: variazione 0 non congela questi cambiamenti. Per ripetere il confronto mantenere `--seed 0`, il valore predefinito del basso. Cambiare seed sceglie altre variazioni, senza modificare il significato dei controlli; farlo dopo aver trovato un equilibrio utile.

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

Verificati con test: percorsi, clock distinti, fasi, pause, durate e retrigger. La corrispondenza con il MIDI reale è stata verificata nelle configurazioni descritte in [Export Snake](EXPORT-SNAKE.md#verifiche-concluse). Il collegamento live descritto sotto acquisisce stato e fase dalla mod. La previsione resta basata sullo stato osservato: non anticipa modifiche manuali future o comandi del viaggio non ancora applicati.

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

`--min-spacing` regola la distanza fra gli attacchi del basso; `--lowest` e `--highest` il registro. `--articulation` e `--velocity-ratio` regolano durata e dinamica. `--window` cambia la lunghezza delle frasi e `--lead` l'anticipo minimo. Sono impostazioni della pianificazione live, non vincoli del modello musicale.

Lo stato passa sulla porta 9003 e i piani sulla 9004. Le porte sono configurabili sia nel builder sia nella CLI. Ogni piano contiene sessione, seriale, revisione, beat iniziale e frase. Il player ignora duplicati e pacchetti superati; un nuovo piano non riavvia quello in corso. Gli eventi sono programmati da `timepoint` sul trasporto Live e chiusi da `flush` allo stop. L'aggiornamento non sostituisce i note-off già programmati con gli stessi valori.

Verificati con test Python, simulazioni JS e controllo dei container: previsione, generazione, pacchetti fuori ordine, stop, conservazione dei note-off e risorse incorporate. Il confronto MIDI del basso è descritto in [Sessione](SESSIONE.md#confronto-del-player-del-basso). Cambi di tempo durante una nota e seek vicino a un evento richiedono misure reali. Le modifiche ai parametri influenzano le finestre future ancora programmabili, non riscrivono il passato o la frase già iniziata.

Riferimenti: [timepoint](https://docs.cycling74.com/reference/timepoint/) per gli eventi assoluti; [when](https://docs.cycling74.com/reference/when/) per la lettura del tempo in tick dall'uscita destra.

## Variazioni e transizioni

L'indice della finestra musicale e `--seed` determinano le variazioni ripetibili. Reinviare lo stesso stato non cambia casualmente la frase. `--variation-period` indica ogni quante frasi favorire una chiusura sull'appoggio osservato quando la variazione è attiva; il valore predefinito è quattro.

Le opzioni CLI impostano i controlli iniziali. Durante l'esecuzione `live_bass` riceve aggiornamenti OSC parziali e usa `BassSession.set_settings` per distribuirli sulle finestre future. Formato dei messaggi, transizioni e tempi di applicazione sono descritti in [Controlli del basso](CONTROLLI-BASSO.md). Il mittente dei controlli verrà sviluppato separatamente.

I test verificano controlli, limiti, ripetibilità e transizioni. Il risultato musicale del generatore parametrico resta da valutare all'ascolto.
