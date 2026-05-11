# DESNIVEL — Architettura musicale

> Documento fondativo del sistema audio generativo.
> È la base concettuale e operativa su cui si costruiscono tutti gli sviluppi successivi (codice Python, patch TouchDesigner, strumenti Ableton/Max for Live).

---

## 1. Principio guida

> **Il GPX non suona note. Il GPX modula il comportamento di un sistema musicale che vive di vita propria.**

Il paesaggio è inteso come **organismo musicale**, non come sorgente di eventi da convertire in MIDI.
Il sistema sonoro è un ecosistema autonomo: ha un proprio ritmo, una propria armonia, un proprio silenzio. I dati del viaggio entrano come **clima**, non come spartito.

Da questo principio derivano tutte le decisioni progettuali del documento.

---

## 2. Caratteristiche del sistema

Il sistema musicale che vogliamo costruire ha queste qualità distintive:

- **Sequencer autonomo modulato dal paesaggio**, non sequencer pilotato dal CSV.
- **Stato più che evento**: il sistema vive in una *condizione* che evolve, non in una sequenza di trigger.
- **Inerzia**: ogni parametro ha memoria e interpolazione, mai reazioni istantanee.
- **Note rare e pensate**, mai una nota per ogni dato.
- **Continuità percettiva** garantita da un layer texture sempre presente.
- **BPM stabile per lunghi tratti**, evolve a scatti rari e morbidi.
- **Una sorgente, una destinazione**: niente mappature multiple sovrapposte.

---

## 3. Le quattro scale temporali

Il sistema è organizzato su quattro orizzonti temporali distinti. Ogni parametro musicale appartiene a una sola scala e si muove con la lentezza propria di quella scala.

### 3.1 Arco di tappa — l'intera tappa (ore)
La narrazione complessiva. È il senso di **dove siamo dentro il viaggio**: l'inizio, lo sviluppo, la fine.
Controlla in modo molto sottile:
- la tendenza generale di densità e tensione lungo la tappa
- l'apertura progressiva o la rarefazione dei layer
- l'inclinazione complessiva della palette (es. più calda all'alba, più cristallina al tramonto)

Questa scala non si percepisce come cambiamento, ma come **direzione**. È ciò che trasforma il sistema da "un viaggio che suona" a "una composizione che racconta un viaggio".
Non ha transizioni: è una curva monotona o quasi, calcolata sulla durata complessiva della tappa.

### 3.2 Macrotempo — 90 a 300 secondi
La cornice. Definisce il **mondo** in cui la musica vive in un dato momento.
Controlla:
- tonalità e scala
- palette timbrica (famiglia di synth)
- carattere del riverbero e dello spazio
- registro generale (grave / acuto)

Il macrotempo cambia raramente. Le sue transizioni sono morbide, non percettibili come tagli. In una tappa di sei ore ci si aspettano poche decine di cambi macro, non centinaia.

### 3.3 Mesotempo — 5 a 30 secondi
Il respiro. Definisce **come si comporta il sequencer** dentro la cornice macro.
Controlla:
- densità di note
- probabilità che uno step suoni
- lunghezza delle note (gate)
- root note all'interno della scala
- apertura del filtro
- brillantezza e registro fine

Il mesotempo è la scala dove si percepiscono le evoluzioni musicali principali.

### 3.4 Microtempo — sotto il secondo
Il movimento interno. **Non genera mai note nuove.**
Controlla solo:
- LFO e modulazioni cicliche
- jitter di timing
- micro-detune e variazioni di intonazione
- variazioni leggere di volume e pan
- leggere variazioni timbriche

Il microtempo dà la sensazione di organicità e respiro. Nessun parametro percepito come "evento" appartiene a questa scala.

---

## 4. I quattro layer

Il suono è composto da quattro voci sovrapposte. Ogni layer è un sequencer indipendente, con il proprio carattere e le proprie modulazioni.

### Layer 1 — Corpo (pulse)
Il battito di fondo. Sequencer ritmico a bassa frequenza.
**Modulato da:** velocità, sforzo, qualità del movimento.
La velocità influenza il BPM; lo sforzo influenza la densità del pattern; non si trasformano mai in note dirette.

### Layer 2 — Territorio (armonia)
Sequencer armonico lento. Cambia nota raramente, mai a ogni step.
**Modulato da:** altitudine, pendenza, tipo di terreno.
L'altitudine sposta il registro. La pendenza modifica la tensione armonica. Il tipo di terreno cambia la scala disponibile.
Il GPX sceglie **l'insieme delle note possibili**, non quale nota suonare: la nota viene scelta dal sequencer.

### Layer 3 — Paesaggio (texture)
Drone e granulare. Continuamente presente, mai silente: è il tessuto su cui tutto poggia.
**Modulato da:** scorrevolezza del movimento, luce, ora del giorno, vicinanza al mare o alla costa.
Questo layer è il principale responsabile della **continuità percettiva** del sistema.

### Layer 4 — Eventi
Gli eventi non sono note. Sono **discontinuità intenzionali** dentro un sistema altrimenti continuo. Per rispettare la coerenza concettuale del sistema state-based, gli eventi si dividono in due categorie chiaramente distinte.

#### 4.1 Eventi maggiori — 3 a 5 per tappa
Sono i momenti **memorabili** del viaggio: la vetta più alta, l'arrivo al mare, l'ingresso nella città di destinazione, la partenza, l'arrivo. Massimo cinque per tappa intera.
Un evento maggiore può permettersi un gesto musicale identificabile: una nota tenuta, un campanellino lontano, l'apertura improvvisa di una riverberazione molto lunga.
La loro rarità è ciò che li rende musicali.

#### 4.2 Eventi minori — transizioni di stato accelerate
Sono i cambi di terreno, l'ingresso in una piccola città, una sosta, una curva importante. Non producono mai un gesto musicale autonomo: **accelerano transizioni che il macro starebbe già facendo**.
In pratica un evento minore dice al sistema: "la transizione che stavi preparando in 60 secondi, falla in 15". Nessuna nota, nessun campanellino, solo una curva più ripida nelle modulazioni macro.
Questo li mantiene perfettamente dentro la logica state-based: non sono interruzioni, sono **inviti a cambiare stato più in fretta**.

---

## 5. Le regole dell'inerzia

Tutti i parametri musicali si muovono con quattro meccanismi combinati, applicati a cascata:

1. **Smoothing.** Ogni dato grezzo viene filtrato con una media mobile la cui memoria è proporzionale alla scala del parametro. Un parametro macro ha una memoria di decine di secondi.
2. **Banda morta.** Il parametro non si muove finché la variazione non supera una soglia minima. Evita il tremolio costante.
3. **Limite di velocità.** L'uscita non può cambiare più di una certa quantità al secondo. Forza l'evoluzione graduale.
4. **Permanenza minima.** I parametri categoriali (scala, palette, territorio) restano fissi per un tempo minimo prima di poter cambiare. Evita oscillazioni avanti-indietro.

Esiste inoltre un quinto meccanismo, di natura compositiva:

5. **Accumulo e rilascio.** Alcune grandezze (es. la "tensione" generata da una salita lunga) non sono il valore istantaneo ma una memoria che si carica nel tempo e si scarica lentamente. È il meccanismo che dà al sistema il senso di **respirare**.

---

## 6. Cosa non si fa

Queste regole negative sono importanti quanto quelle positive. Il sistema le rispetta sempre.

- Latitudine e longitudine non diventano mai note.
- Direzione e curvatura istantanea non diventano mai trigger.
- La frequenza di campionamento del GPX non è la frequenza del sequencer. I due orologi sono separati.
- Nessun parametro del GPX viene passato al sistema musicale senza essere prima filtrato.
- Una sorgente di dato controlla **una sola** destinazione musicale. Niente mappature multiple sovrapposte.
- Nessuna nota viene generata da un singolo campione di dato.

---

## 7. Il flusso del segnale

Il sistema è organizzato in tre stadi, con responsabilità chiare.

### Stadio 1 — Python (preparazione)
Legge il GPX, calcola le metriche del viaggio (velocità, pendenza, terreno, luce, ecc.), applica gli smoothing di lungo periodo e produce tre flussi distinti:

- un **flusso continuo di modulazioni** (arco di tappa, macro, meso), già completamente filtrato;
- un **flusso di eventi maggiori**, al massimo 3–5 per tappa, con payload significativo;
- un **flusso di eventi minori**, sporadici, con tempo di attesa minimo tra l'uno e l'altro.

### Stadio 2 — TouchDesigner (distribuzione)
Riceve i due flussi, gestisce il tempo di esecuzione e li distribuisce via OSC ad Ableton/Max for Live, eventualmente aggiungendo modulazioni di microtempo (LFO, jitter) che non hanno bisogno di essere calcolate a monte.

### Stadio 3 — Ableton / Max for Live (suono)
Contiene **tutti i sequencer**. È qui che le note nascono. Riceve solo modulazioni e eventi, mai note pronte. Ogni layer è un dispositivo indipendente con il proprio sequencer interno.

---

## 8. Criteri di verifica

Il sistema è considerato musicalmente valido quando supera questi test:

1. **Test del silenzio dati.** Spegnendo il flusso GPX (valori fermi), il sistema continua a suonare in modo musicalmente coerente per diversi minuti.
2. **Test del congelamento.** Bloccando un singolo parametro per un minuto, la musica continua a evolvere ma in modo riconoscibilmente stabile.
3. **Test dell'accelerazione.** Riproducendo il GPX a velocità 10x, la musica non accelera in modo caotico: gli smoothing assorbono la variazione.
4. **Test della densità.** Nei layer melodici, il numero di note al minuto rientra in una fascia ambient/cinematografica (indicativamente 10–30 note al minuto). Il layer corpo può essere più denso ma con pattern ripetitivo.

Se uno qualunque di questi test fallisce, il sistema è ancora troppo event-driven.

---

## 9. Linguaggio condiviso

Glossario dei termini ricorrenti, usati nello stesso senso in tutto il progetto.

- **Modulazione**: un valore continuo che influenza un parametro musicale, mai una nota.
- **Evento maggiore**: uno dei 3–5 momenti memorabili della tappa. Può permettersi un gesto musicale.
- **Evento minore**: un'accelerazione di una transizione di stato già in corso. Non produce note.
- **Layer**: una delle quattro voci (corpo, territorio, paesaggio, eventi).
- **Stato**: la configurazione corrente del sistema musicale (tonalità, palette, ecc.).
- **Inerzia**: l'insieme dei meccanismi che impediscono al sistema di reagire istantaneamente.
- **Tensione**: una grandezza accumulata nel tempo che misura quanto il paesaggio sta "spingendo".
- **Arco di tappa**: la curva narrativa che attraversa l'intera tappa, indipendente dal dato locale.
- **Continuità**: la presenza ininterrotta del layer paesaggio, che garantisce la coesione percettiva.

---

## 10. Come procediamo

Questo documento è la base. Da qui si costruisce tutto il resto, in questo ordine:

1. **Contratto delle modulazioni e degli eventi.** — *Fatto, v0.2.*
   Definito in [CONTRATTO-MODULAZIONI.md](CONTRATTO-MODULAZIONI.md).

2. **Specifica di implementazione.** — *Fatto.*
   Definita in [IMPLEMENTAZIONE.md](IMPLEMENTAZIONE.md).

3. **Scaffolding minimo.**
   Struttura della cartella `src/desnivel/`, `config.py`, `track.py`, `events.py` con registry, `pipeline.py`, `FileSink`, CLI `run_stage.py`. End-to-end vuoto, ma eseguibile.

4. **Modulo `journey`.**
   Curve di arco di tappa (`phase`, `energy`, `openness`). Il più semplice e indipendente: valida l'intera pipeline con un canale visibile.

5. **Sink OSC.**
   `OscSink` e `ReplaySink`. A questo punto i canali `journey` arrivano in TouchDesigner/Ableton.

6. **Modulo `tension`.**
   Integratore con carica/decadimento, produce `/mod/meso/tension`.

7. **Modulo `state`.**
   Macchina a stati con dwell time, produce i canali `/mod/macro/*`.

8. **Detector degli eventi.**
   Maggiori (con limite globale per tappa) e minori (con cooldown derivato dalla durata). Include `ExternalEventDetector` per gli eventi dichiarati nel JSON.

9. **Moduli `meso`, `body`, `micro`.**
   Si chiudono i canali rimanenti del contratto.

10. **Adeguamento della patch Ableton/Max for Live.**
    Trasformare i dispositivi in sequencer autonomi, riceventi solo modulazioni ed eventi secondo il contratto.

---

## 11. Consiglio per partire

Le basi documentali sono pronte:
[CONTRATTO-MODULAZIONI.md](CONTRATTO-MODULAZIONI.md) v0.2 + [IMPLEMENTAZIONE.md](IMPLEMENTAZIONE.md).

Il prossimo passo è il **branch git dedicato** (es. `feat/musical-architecture`) e lo **scaffolding minimo**: cartella `src/desnivel/`, `config.py`, `track.py`, `events.py` con registry, `pipeline.py`, `FileSink`, CLI `run_stage.py`. Eseguibile end-to-end ma vuoto: produce un CSV con la sola colonna `t`.

Subito dopo: il modulo `journey`. È il più semplice, è indipendente dagli altri, e permette di validare l'intera catena (Python → file → OSC → ricezione) con un singolo canale che si muove in modo lento e prevedibile. Una volta che `journey/phase` arriva correttamente in Ableton, tutto il resto si aggancia con sicurezza.
