# DESNIVEL — Architettura musicale

Questo documento definisce l’architettura di riferimento. Music Director e Music Coordinator sono da implementare; i percorsi operativi e le verifiche sono descritti nello [stato del progetto](SESSIONE.md).

## Scopo

Generare musica a partire dai dati di un viaggio GPX. Le variazioni del percorso influenzano l'evoluzione del brano attraverso trasformazioni percepibili e musicalmente coerenti. I dati descrivono il viaggio; l'interpretazione espressiva è una scelta compositiva.

## Componenti

| Componente | Responsabilità |
|---|---|
| **GPX Analyzer** | Elabora le metriche del viaggio, tra cui velocità, pendenza e soste. |
| **Music Director** | Definisce il contesto armonico ed espressivo comune e le regole di arrangiamento delle voci. |
| **Generatori** | Producono frasi musicali secondo la propria strategia, il contesto ricevuto e le relazioni previste con altre voci. |
| **Music Coordinator** | Gestisce voci attive, dipendenze, finestre temporali e aggiornamenti dei piani musicali. |
| **Adattatori e player** | Trasmettono ed eseguono i piani nella destinazione musicale. |

## Confini

Il producer Python pubblica metriche del viaggio con tempi e unità, senza note, scale o parametri dei device. Il GPX Analyzer corrisponde al caricamento e all’elaborazione dei dati del producer. I fatti geografici neutrali restano da definire nel [contratto dati](CONTRATTO-DATI-VIAGGIO.md).

Il motore musicale Python comprende Director, generatori e Coordinator. Queste sono responsabilità logiche e possono restare nello stesso processo. Le regole musicali non dipendono da ID Live o nomi dei parametri Snake.

Gli adattatori contengono protocolli, nomi, range e limiti della destinazione. Le funzioni non supportate devono essere dichiarate. Snake è il primo adattatore; Ableton Live è la destinazione attuale. TouchDesigner resta un consumer visuale indipendente del producer.

## Organizzazione del codice

| Package | Responsabilità |
|---|---|
| `desnivel.trip` | Modello `Track`, configurazione del producer, loader GPX e metriche neutrali. |
| `desnivel.music` | Pattern, scale, frasi e composizione della voce melodica dal viaggio. |
| `desnivel.music.bass` | Generatore del basso, contratto dei controlli e analisi dei pattern per suggerire un assetto. |
| `desnivel.adapters` | Traduzione verso Snake e player M4L, previsione dello stato Snake e sessione live del basso. |
| `desnivel.sinks` | Client e pianificazione OSC, pubblicazione delle metriche e acquisizioni JSONL. |
| `desnivel.cli` | Comandi eseguibili e opzioni condivise dei comandi. |

I test Python seguono gli stessi gruppi in `tests/`; `tests/devices/` verifica i builder dei device e `tests/js/` gli script Max. I builder restano in `tools/`, i sorgenti Max in `m4l/` e i launcher macOS in `comandi/`.

## Direzione musicale

Il Music Director costruisce un contesto condiviso composto da:

- **Armonia:** tonalità, scala e progressione armonica.
- **Espressività:** indicazioni comuni, inizialmente energia e tensione.
- **Arrangiamento:** ruoli delle voci, registri, priorità e relazioni musicali.

Il contesto armonico è configurabile: tonalità, scala e progressione possono restare costanti oppure evolvere durante il viaggio. I criteri musicali per scegliere e collegare i cambi armonici sono ancora da definire.

### Regole di arrangiamento

Le regole si applicano ai ruoli e alle relazioni tra voci, indipendentemente dallo strumento impiegato. Possono riguardare, per esempio, complementarità ritmica, distribuzione dei registri e raddoppi.

Ogni preferenza ha un peso configurabile che ne determina l'influenza sulle scelte del generatore. I vincoli tecnici obbligatori sono distinti dalle preferenze musicali. Le regole non garantiscono da sole l'assenza di conflitti: per considerare una frase già composta, il generatore interessato deve poterla ricevere come input.

La logica di arrangiamento è organizzata in funzioni del Music Director, con input e output espliciti e testabili separatamente.

## Generazione e coordinamento

Ogni generatore produce il materiale della propria voce. Le relazioni tra voci sono dichiarate nella configurazione della composizione. Quando una voce dipende da un'altra, il Coordinator prepara e distribuisce le frasi nell'ordine necessario.

La prima configurazione prevede una sorgente melodica attiva per volta. La gestione delle voci e delle dipendenze deve consentire anche più sorgenti melodiche simultanee.

Le frasi sono associate a un contesto musicale e a una finestra temporale condivisi. Il Coordinator gestisce gli aggiornamenti in modo che le voci dipendenti utilizzino versioni coerenti del materiale.

## Flusso dei dati

```text
GPX → GPX Analyzer → Music Director
                           │
                  Contesto musicale
                           │
                           ▼
                   Music Coordinator
                           │
                 Generatori delle voci
                           │
                  Frasi musicali
                           │
                   Adattatori / Player
                           │
                      Ableton Live
```

Il Coordinator organizza le richieste ai generatori e passa loro il contesto musicale e, quando previsto, le frasi delle altre voci.

## Tempo e continuità

Il tempo del viaggio e il tempo musicale sono distinti. Il rapporto tra secondi del GPX e beat musicali deve essere definito per la riproduzione.

Il Coordinator gestisce le finestre temporali e gli aggiornamenti. Il Music Director aggiorna il contesto condiviso; ciascun generatore determina come trasformare nel tempo il proprio materiale musicale.


## Interfacce presenti

`music.patterns.Pattern` contiene note e gate; `PatternChange` associa un pattern al tempo del viaggio. `music.journey.compose` interpreta movimento e sforzo e produce questi cambi per il percorso Snake.

`music.phrases.Phrase` contiene note con attacco relativo in beat, altezza MIDI, durata e velocity. Ogni nota termina entro la frase. Sessione, posizione assoluta e revisione appartengono al piano esterno.

Il basso riceve una `Phrase`, i propri controlli, l’eventuale altezza precedente e l’indice musicale. Rimane indipendente dalla sorgente melodica. Attualmente l’adattatore Snake prevede la frase dagli snapshot e `BassSession` prepara i piani del basso; il beat del trasporto arriva dagli snapshot Snake. Una frase melodica vuota produce basso silenzioso.

## Da definire

- Intenzioni condivise, criteri armonici e tempi delle trasformazioni.
- Contratto dei piani per più voci, selezione del materiale da accompagnare e revisioni delle dipendenze.
- Relazione fra tempo del viaggio e beat, riferimento di trasporto comune e scadenze degli aggiornamenti.
- Comportamento con dati mancanti, Stop, seek, loop e ripartenza.
- Continuità delle note oltre il confine delle finestre.
