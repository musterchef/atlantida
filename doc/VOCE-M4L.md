# Dispositivo MIDI di voce

`Desnivel_Voice.amxd` è un effetto MIDI da collocare prima dello strumento su una traccia Live. Il dispositivo riceve frasi dal motore Python e le esegue sul trasporto di Live. La logica compositiva rimane in Python.

## Componenti

| Sorgente | Responsabilità |
|---|---|
| `m4l/desnivel_voice.maxpat` | Interfaccia, rete locale, lettura del trasporto e uscita MIDI |
| `m4l/desnivel_voice.js` | Identificazione dell'istanza, menu, controlli e collegamento con Python |
| `m4l/desnivel_transport_player.js` | Esecuzione dei piani in beat assoluti con oggetti `timepoint` |
| `src/desnivel/adapters/voice_device.py` | Validazione dei controlli e collegamento tra voci Python e dispositivi |
| `src/desnivel/cli/voice_device.py` | Server OSC locale e prova di esecuzione da file |
| `tools/build_voice_device.py` | Confezionamento dal template MIDI ufficiale di Live |

Il percorso delle note generate termina in `midiformat` e `midiout`. Il dispositivo non inoltra il MIDI in ingresso. Non carica strumenti o preset sonori.

## Costruzione

Dalla radice del repository, usando una cartella di output nuova:

```sh
.venv/bin/python tools/build_voice_device.py --output /tmp/desnivel-voice
```

Il builder usa il template `Max MIDI Effect.amxd` dell'installazione Live in `/Applications/Ableton Live 12 Suite.app`. `--template` permette di indicarne un altro percorso. Non modifica il template.

Per aggiornare direttamente la cartella installata:

```sh
.venv/bin/python tools/build_voice_device.py \
  --output "$HOME/Music/Ableton/User Library/MaxForLive/desnivel/Desnivel_Voice" \
  --update
```

`--update` riscrive `Desnivel_Voice.amxd` e i due script del dispositivo, mantenendo gli altri file della cartella. Dopo l'aggiornamento ricaricare il dispositivo in Live per usare la nuova versione.

La cartella generata contiene il device e i due script JavaScript. Conservare i tre file insieme: il device non è congelato con risorse incorporate. Il sorgente modificabile è `m4l/desnivel_voice.maxpat`.

## Interfaccia

- **Part**: identificativo della parte registrata in Python, per esempio `voice_01`.
- **Receive**: porta UDP di questa istanza, inizialmente `9101`. Ogni istanza richiede una porta distinta.
- **Python**: porta del server locale, inizialmente `9006`.
- **Connect**: legge identificativo e porte e apre il collegamento. Se già collegato, rinnova la richiesta mantenendo identità e piani della stessa istanza.
- **Role**: menu dei ruoli supportati dal generatore collegato. `Follow section` segue il ruolo assegnato alla sezione; scegliendo un ruolo si passa alla modalità manuale. Il ruolo effettivo è mostrato in alto; per una parte esclusa dall’organico sono mostrati il prossimo ingresso configurato (`enters at ...%`) oppure `not in this section` se non sono previsti altri ingressi. Senza un collegamento ai ruoli della sessione, il menu mostra `No roles available`.
- **Preset**: preset compositivi dichiarati dal componente Python.
- **Parameter** e valore: modifica di uno dei controlli esposti da Python. L'intervallo ammesso è mostrato accanto al valore.
- **panic**: cancella i piani e spegne le note generate.

I menu sono riempiti dalla risposta Python. Il dispositivo non contiene nomi di strumenti, ruoli prestabiliti o parametri di un generatore specifico.

## Sessione continua

Per la composizione con Director, Coordinator e più parti usare il comando descritto in [SESSIONE-MULTIVOCE.md](SESSIONE-MULTIVOCE.md). Il ricevitore diagnostico seguente usa la stessa porta e va chiuso prima di avviare la sessione.

## Prima prova di esecuzione

Avviare il ricevitore con una frase già presente nel progetto:

```sh
.venv/bin/python -m desnivel.cli.voice_device \
  --voice voice_01 \
  --phrase presets/phrases/bass_sustained.json
```

1. Caricare il device prima dello strumento su una traccia MIDI.
2. Impostare `Part` a `voice_01`, `Receive` a `9101` e `Python` a `9006`, quindi premere **Connect**.
3. Avviare il trasporto di Live.

La prova invia la frase una volta per avvio o discontinuità rilevata del trasporto, a un multiplo di quattro beat con almeno due beat di anticipo rispetto alla posizione ricevuta. Usa il file senza modificarne il contenuto musicale. Non pianifica una tappa GPX. In questa modalità il ruolo è non assegnato e i menu sono vuoti.

Senza `--phrase`, il comando verifica soltanto il collegamento. Più parti possono essere registrate ripetendo `--voice`; la prova da file ammette una sola parte.

## Collegamento al motore condiviso

`VoiceDeviceServer` riceve una mappa di identificativi a oggetti `DeviceVoice`. Ogni oggetto contiene i controlli esposti, i valori iniziali, i preset disponibili, il ruolo e la funzione `apply` che applica le modifiche al motore Python.

`Control` definisce minimo, massimo e l'eventuale vincolo intero. Ogni preset definisce tutti i controlli esposti dalla voce. Un controllo fuori intervallo è rifiutato; il nuovo stato viene confermato soltanto dopo il completamento di `apply`.

`EnsembleSession.set_parameters(voice, values)` applica valori manuali alle prossime frasi della voce. Questi prevalgono sui parametri di sezione e persistono tra sezioni; `clear_parameters(voice)` ripristina i valori delle sezioni. La validazione dei valori è eseguita dal componente che espone i controlli.

`DeviceVoice.for_session(session, voice, progress, **controls)` collega il dispositivo alla sessione: `progress` è una funzione del chiamante che restituisce la progressione corrente della tappa. Il collegamento espone i ruoli dichiarati dal generatore, legge il ruolo della sezione e applica la scelta manuale tramite `EnsembleSession.set_role`.

La scelta manuale del ruolo persiste tra sezioni nella stessa sessione Python; `Follow section` la elimina e ripristina il ruolo della sezione corrente. Non attiva voci escluse dall'organico, non modifica i parametri e non riscrive la configurazione JSON. Agisce sulle successive chiamate di pianificazione, senza sostituire le frasi già inviate. Ruoli non supportati vengono rifiutati prima dell'applicazione; il dispositivo torna a mostrare l'ultima scelta confermata da Python.

`server.bridge.destination(voice)` restituisce una funzione compatibile con le destinazioni di `EnsembleSession`: riceve beat iniziale e `Phrase` e invia un piano all'istanza collegata. Con `DeviceVoice.for_session` il ruolo viene letto dal Director a ogni risposta; nei collegamenti costruiti direttamente con `DeviceVoice` il chiamante ne gestisce lo stato. Il ciclo di pianificazione è gestito dal chiamante. Il server è bloccante: richieste di controllo e pianificazione vanno serializzate nello stesso thread, usando il callback `on_message` o governando esplicitamente il ciclo del server.

## Protocollo e arresto

I messaggi sono OSC con il JSON versione `1` codificato in UTF-8,
un argomento intero OSC per ciascun byte:

- dispositivo → Python: `/desnivel/v1/voice/control`;
- Python → dispositivo: `/desnivel/v1/voice/message`.

Il dispositivo usa `udpsend` e `udpreceive` nel formato ordinario dei
messaggi OSC. Gli script convertono gli argomenti numerici in JSON e
viceversa. Anche il passaggio dei piani dall'interfaccia al player usa byte
numerici. I payload JSON variabili non diventano simboli Max a ogni
aggiornamento del trasporto. Il server limita il JSON in uscita a 12.000
byte per mantenere il pacchetto OSC sotto il limite UDP.

Le richieste contengono voce, identificativo dell'istanza, seriale, porta di risposta e azione (`hello`, `transport`, `role`, `preset`, `parameter`, `panic`). L’azione `role` contiene l’identificativo del ruolo manuale oppure `null` per seguire la sezione. Lo stato restituisce ruoli supportati, ruolo effettivo, ruolo della sezione, modalità (`section` o `manual`) e stato di attivazione della parte. La lettura del trasporto aggiunge beat, stato di riproduzione e contatore locale delle discontinuità. Le risposte distinguono stato, errore e piano.

Il dispositivo invia `hello` ogni secondo. Dopo oltre tre secondi senza conferma cancella i piani e spegne le note. Python rifiuta due istanze attive con la stessa voce o la stessa porta di ricezione; un collegamento scaduto può essere sostituito. I piani sono indirizzati anche all'identificativo dell'istanza.

Il player riutilizza gruppi di oggetti nativi per i timestamp degli eventi.
Ogni gruppo contiene `timepoint`, gate a singola esecuzione e memoria delle
coppie MIDI. Gli eventi allo stesso timestamp vengono emessi in ordine,
con note-off prima dei note-on. I gruppi scaduti vengono disarmati e
riutilizzati, mantenendo gli oggetti necessari ai note-off ancora futuri.
Il numero di gruppi cresce solo quando aumenta il picco di timestamp
contemporaneamente pianificati. Stop e Panic svuotano i piani e disarmano
i gruppi; la rimozione del dispositivo elimina anche gli oggetti conservati.
La ricompilazione del JavaScript rimuove gli oggetti dinamici residui.

Il player cancella i piani a Stop, arretramento del trasporto e Panic. Rifiuta piani tardivi e sovrapposizioni della stessa altezza all'interno della frase. Il passo temporale è un tick Max, pari a 1/480 di semiminima.

## Verifiche

I test Python verificano controlli, destinazioni separate, duplicati, conflitti tra istanze e collegamento con `EnsembleSession`. I test JavaScript simulano messaggi e player, compresi 1.000 aggiornamenti
del trasporto a byte e 1.000 finestre con numero di oggetti stabile dopo
il riscaldamento. Questi controlli non misurano il jitter audio in Live. I test del builder verificano contenitore e connessioni del sorgente.

La prova manuale in Live ha confermato l'invio della frase da file e la produzione di suono. La correzione di Connect ripetuto è verificata dal test JavaScript; la relativa prova manuale in Live resta da eseguire.

## Riferimenti tecnici

- [Cycling '74 — udpreceive](https://docs.cycling74.com/reference/udpreceive/): ricezione OSC e rinvio alla coda a bassa priorità.
- [Cycling '74 — timepoint](https://docs.cycling74.com/reference/timepoint/): esecuzione su trasporto e aggiornamento del timestamp.
- [Cycling '74 — udpsend](https://docs.cycling74.com/reference/udpsend/): trasmissione dei messaggi Max come pacchetti OSC compatibili.
- [Cycling '74 — textedit](https://docs.cycling74.com/reference/textedit/): ingresso dell'identificativo della parte.
- [Cycling '74 — MIDI](https://docs.cycling74.com/userguide/midi/): formattazione e uscita dei messaggi MIDI.
