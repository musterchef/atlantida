# Sessione multivoce Python

Il comando `desnivel.cli.ensemble` esegue nello stesso processo il replay GPX, il Music Director, il Music Coordinator, i generatori e il server dei dispositivi di voce. La configurazione seleziona esplicitamente generatori, ruoli, parametri e organico delle sezioni.

## Avvio

Chiudere con Ctrl+C il ricevitore diagnostico `desnivel.cli.voice_device`, che usa la stessa porta.

Dalla radice del repository:

```sh
.venv/bin/python -m desnivel.cli.ensemble \
  --gpx gpx/tappa05_Firenze_San_Gimignano.gpx \
  --config presets/organico.json \
  --speed 50
```

Per verificare configurazione e generazione delle sezioni senza aprire porte o inviare note, aggiungere `--dry-run`.

Per usare le macrosezioni del percorso e i relativi assetti musicali:

```sh
.venv/bin/python -m desnivel.cli.ensemble \
  --gpx gpx/tappa05_Firenze_San_Gimignano.gpx \
  --config presets/organico.json \
  --direction presets/direzione-viaggio.json \
  --speed 50
```

Con `--direction`, il comando analizza il GPX e prepara le sezioni musicali
all'avvio. I confini derivano dalle macrosezioni; ciascuna famiglia riceve
l'assetto definito nel JSON di direzione. Senza questa opzione vengono usate
le sezioni manuali di `organico.json`.

Nella configurazione fornita:

| Parte | Configurazione in Live |
|---|---|
| `voice_01` | `Desnivel_Voice` prima del synth, Receive `9101`, Python `9006` |
| `voice_02` | `Desnivel_Voice` prima dello strumento della seconda parte, Receive `9102`, Python `9006` |
| `voice_03` | `Desnivel_Voice` prima dello strumento atmosferico, Receive `9103`, Python `9006` |
| `voice_04` | `Desnivel_Voice` prima del Drum Rack, Receive `9104`, Python `9006` |

Impostare l'identificativo in **Part** e premere **Connect** sulle istanze,
quindi avviare il trasporto di Live. Il Drum Rack deve avere cassa sulla
nota MIDI 36, rullante su 38 e charleston su 42, come configurato in
`generators.percussion.lanes`. Lo strumento atmosferico riceve una nota
sostenuta monofonica per finestra: il suono si sceglie nello strumento Live.
Tutte le voci attive devono essere collegate, altrimenti la sessione attende
in `waiting_for_devices`.

Il dispositivo descritto in [VOCE-M4L.md](VOCE-M4L.md) invia la posizione
musicale ogni 125 ms oltre al messaggio periodico di collegamento. Le nuove
voci usano lo stesso dispositivo; i menu vengono forniti da Python.

`voice_01` è la sorgente del trasporto scelta dal campo `transport_voice`. Questo assegna la lettura del clock, non un privilegio compositivo. Il dispositivo continua a comunicare il trasporto anche quando la parte è inattiva nell'organico.

## Replay e pianificazione

Il viaggio avanza in secondi, moltiplicati per `--speed`, quando la sessione sta suonando. La distanza cumulativa interpolata del GPX determina la progressione usata per selezionare le sezioni. Il GPX controlla il contesto e l'organico delle sezioni; questo comando non applica la mappatura velocità/sforzo ai gate di `journey.compose`.

Live fornisce beat e stato Play/Stop. Stop spegne le note, cancella i piani e mette in pausa il viaggio. Play lo riprende dal punto raggiunto. Salti all'indietro e discontinuità comunicate dal dispositivo cancellano e ripianificano le note senza riportare il viaggio a una posizione ricavata dalle battute.

`window_beats` indica la durata delle frasi; `lead_beats` l'anticipo minimo rispetto al beat ricevuto. Le frasi iniziano a multipli della finestra. Ogni intervallo viene pianificato una volta: cambi di ruolo e parametri si applicano alle finestre ancora da pianificare.

Il cambio di sezione modifica le assegnazioni alla successiva pianificazione. Alle parti uscenti viene inviata una frase vuota per la nuova finestra, lasciando terminare quella precedente. Se manca una parte attiva o la sorgente del trasporto perde il collegamento, la sessione cancella i piani dei dispositivi raggiungibili e attende, sospendendo il replay. I dispositivi non raggiungibili eseguono il proprio Panic per mancata conferma.

Al termine del GPX la sessione spegne le note e mostra `finished`. Ctrl+C chiude il server e scrive lo stato `closed`. Un errore di generazione porta allo stato `error` e richiede il riavvio della sessione.

## Configurazione

Il [riferimento dei campi e dei parametri](CONFIGURAZIONE.md) riporta unità,
limiti e precedenze. L'[indice dei preset](../presets/README.md) distingue
i file per responsabilità e comando che li utilizza.

`presets/organico.json` contiene:

- `transport_voice`, `window_beats`, `lead_beats`;
- `generators`: definizioni dei generatori con tipo, impostazioni e preset;
- `voices`: identificativo, nome descrittivo, generatore, destinazione e dipendenze;
- `sections`: nome, progressione iniziale, altezza di riferimento, scala e assegnazioni delle parti.

Ogni voce riceve una propria istanza del generatore, anche quando più voci fanno riferimento alla stessa definizione. Le implementazioni concrete vengono collegate da `cli/generators.py`; Director e Coordinator lavorano con le interfacce musicali comuni.

I preset dei generatori sono insiemi di parametri. Le modifiche manuali persistono tra sezioni. Il menu **Role** permette di seguire la sezione o mantenere un ruolo manuale tra quelli supportati dal generatore. Il ruolo manuale non attiva una voce esclusa dall'organico.

### Direzione dalle macrosezioni

`presets/direzione-viaggio.json` contiene tre campi:

| Campo | Contenuto |
|---|---|
| `analysis` | Percorso del JSON dei criteri di analisi |
| `grouping` | Percorso del JSON delle famiglie di macrosezioni |
| `families` | Assetto musicale completo per ciascuna famiglia: `root`, `scale`, `assignments` |

I due percorsi sono relativi al file di direzione. Ogni famiglia del
raggruppamento richiede un assetto musicale; famiglie mancanti o aggiuntive
producono un errore. Ruoli, parametri e dipendenze delle sezioni prodotte
sono verificati tramite la validazione della sessione esistente.

`cli/trip_direction.py` collega analisi, raggruppamento e assetti musicali,
producendo le sezioni che il Director già accetta. Il Director seleziona il
contesto e le assegnazioni; il Coordinator continua a pianificare le voci
secondo le loro dipendenze. Il campo `selection_mode: manual` di `organico.json`
indica che le voci sono assegnate esplicitamente, anche quando i confini
delle sezioni derivano dal viaggio.

La configurazione d'ascolto fornita mantiene le quattro voci in tutte le
macrosezioni. Le voci intonate condividono root MIDI 57 e scala `minor`;
la parte percussiva usa le note configurate in `lanes`. Le differenze sono scelte musicali
esplicite del preset, modificabili nel JSON:

| Famiglia | `voice_01`: attività / passo in beat / articolazione / velocity | `voice_02`: densità / sincopazione / articolazione |
|---|---|---|
| `level` | 0,4 / 1,5 / 0,9 / 75 | 0,5 / 0,05 / 0,9 |
| `ascent` | 0,55 / 1 / 0,8 / 88 | 0,8 / 0,1 / 0,85 |
| `descent` | 0,85 / 0,5 / 0,65 / 82 | 1,2 / 0,35 / 0,65 |

| Famiglia | `voice_03`: ruolo / velocity | `voice_04`: pattern / rapporto velocity |
|---|---|---|
| `level` | `sustained_texture` / 45 | `sparse` (0) / 0,75 |
| `ascent` | `sustained_texture` / 55 | `steady` (1) / 0,85 |
| `descent` | `sustained_texture` / 48 | `driving` (2) / 0,9 |

`voice_03` usa un'istanza indipendente di `motif` con `degrees: [0]` e
`octave: 1`: con il contesto fornito produce la nota MIDI 69. La durata è
quella della finestra e la nota viene riarticolata nella finestra seguente.
Il registro e la dinamica sono configurabili; i preset `soft` e `present`
impostano rispettivamente velocity 40 e 65.

I parametri non specificati usano le impostazioni del generatore; le
regolazioni manuali hanno precedenza. Gli assetti vengono copiati per ogni
macrosezione: tornando alla stessa famiglia si riprendono i valori configurati,
senza accumulare modifiche della macrosezione precedente. Il cambio entra
nella prossima finestra ancora da pianificare, senza cancellare lo stato dei
generatori. Non viene applicata un'interpolazione graduale dei parametri.

Le fasce interne non modificano l'assetto: `climb` e `steep_climb` nella
stessa `ascent` mantengono contesto e parametri di sezione identici. La
generazione continua a sviluppare le frasi secondo il proprio algoritmo.
I controlli della prova agiscono su note e ritmo, non sui parametri timbrici
degli strumenti in Live.

## Generatori disponibili nel registro

### `motif`

Implementato in `music/melodic/generator.py`. Riceve un motivo di gradi non negativi (`degrees`) e il contesto di tonica e scala della sezione. Espone registro, ritmo, articolazione, velocity, sviluppo, attività, lunghezza del periodo e seed.

- `melody`: con `development > 0` sviluppa il motivo su più finestre con presentazione, elaborazione, contrasto e conclusione. Con valore `0` ripete il motivo su passi regolari.
- `bass_line`: articola il motivo letterale nel registro assegnato.
- `sustained_texture`: produce una sola nota, dal primo grado configurato, sostenuta per tutta la finestra.

Il generatore controlla il registro MIDI e limita gli eventi per finestra. Le regole e i controlli sono descritti in [MELODIA.md](MELODIA.md).

### `responsive_line`

Collega il generatore presente in `music/bass/` attraverso `music/bass/voice.py`. Supporta `bass_line` e richiede una sola dipendenza: la frase da accompagnare. Conserva l'ultima altezza fra finestre contigue e cancella tale continuità quando il runtime riparte dalla pianificazione.

I controlli esposti sono `density`, `syncopation`, `rhythm_follow`, `melody_follow`, `mobility`, `variation` e `articulation`. Le altre impostazioni del generatore, incluso il registro, si configurano in `settings`. Le regole compositive sono descritte in [BASSO.md](BASSO.md).

### `percussion_pattern`

Implementato in `music/percussion/generator.py`. Supporta il ruolo
`percussion` e ripete pattern espliciti del JSON, con mappa delle note
separata dagli attacchi. Espone selezione del pattern, rapporto di velocity
e durata MIDI massima delle note. Le definizioni e i vincoli sono nel
[riferimento di configurazione](CONFIGURAZIONE.md#parametri-del-generatore-percussion_pattern).
I nomi dei pad, le note MIDI e gli attacchi della prova risiedono nel JSON;
Director, Coordinator e dispositivo continuano a usare le interfacce comuni.

## Stato globale

La vista del terminale si aggiorna ogni secondo anche durante Play, mostrando posizione, beat, sezione, collegamenti, ruoli e controlli. In un terminale interattivo ridisegna la vista nello stesso spazio; quando l’output è rediretto scrive un nuovo blocco ogni secondo. Lo snapshot completo è scritto atomicamente, al massimo ogni 250 ms, in:

```text
/tmp/desnivel-session/state.json
```

`--status-file` cambia il percorso. Lo snapshot contiene:

| Campo | Contenuto |
|---|---|
| `state`, `error` | Stato della sessione ed eventuale errore di esecuzione |
| `trip` | Tappa, secondi raggiunti, durata, distanza, progressione e velocità di replay |
| `section` | Contesto della sezione alla posizione corrente del viaggio |
| `transport` | Sorgente, ultimo Play/Stop ricevuto, beat e contatore delle discontinuità |
| `planning` | Ultimo inizio pianificato, relativa sezione e durata della finestra |
| `voices` | Nomi, generatori, dipendenze, collegamenti, ruoli, controlli, motivo dell’esclusione dall’organico, prossimo ingresso configurato e ultimo piano inviato |
| `decisions` | Selezione attuale del Director e dettaglio dell’ultimo piano inviato dal Coordinator |

Il Director espone l'intervallo di progressione che seleziona la sezione e le assegnazioni con origine `section` o `manual`. Il Coordinator registra l'ordine effettivo delle chiamate, le dipendenze, il ruolo e i parametri passati a ciascun generatore e le note restituite. Il terminale mostra un riepilogo delle note come `altezza MIDI@beat relativo`; lo snapshot conserva l'elenco completo con durata e velocity. Dopo Stop o cancellazione dei piani, il dettaglio del piano viene svuotato.

Con `--direction`, `section.trip` descrive la macrosezione corrente: indice,
famiglia, confini, zone originali incluse e misure del raggruppamento.
`decisions.coordinator.trip` identifica la macrosezione dell'ultimo piano
inviato. Il terminale mostra separatamente posizione corrente e assetto del
piano; quest'ultimo può appartenere alla macrosezione precedente finché non
viene pianificata una nuova finestra. Nella modalità manuale questi campi
valgono `null`.

Una parte può essere collegata al server ma esclusa dall'organico della sezione. In `presets/organico.json`, `voice_02` entra al 30% della distanza: prima di quel punto la vista indica il motivo dell'attesa e la soglia d'ingresso. La selezione manuale del ruolo non modifica questa attivazione.

Lo stato dei piani descrive ciò che Python ha inviato, non una conferma audio dello strumento. La scrittura JSON è separata dal motore; in questa versione non esiste un'interfaccia grafica globale.

## Verifiche

I test automatici coprono pianificazione ripetuta, passaggi di sezione, Stop,
ripartenza, discontinuità, dispositivi mancanti, ruoli, controlli e scrittura
dello stato. La configurazione fornita è verificata anche con `--dry-run`
sul GPX Firenze–San Gimignano. La prova in Live ha confermato l'esecuzione
delle parti melodica e di accompagnamento; Marco ha inoltre confermato
l'ascolto di atmosfera e drums nella prova a quattro voci. Configurazione
e comportamenti musicali costituiscono un banco di prova da affinare.
