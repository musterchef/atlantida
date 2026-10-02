# DESNIVEL — Architettura musicale

> Documento fondativo del sistema audio generativo.
> Le sezioni estetiche descrivono un profilo compositivo possibile, non vincoli universali del motore o degli adattatori. Architettura e stato operativo: [DECISIONE-ARCHITETTURA-AUDIO.md](../DECISIONE-ARCHITETTURA-AUDIO.md). Aggiornato il 2026-10-02.

---

## 1. Principio guida

> **Il GPX non suona note. Il GPX modula il comportamento di un sistema musicale che vive di vita propria.**

Il paesaggio è inteso come **organismo musicale**, non come sorgente di eventi da convertire in MIDI.
Il sistema sonoro è un ecosistema autonomo: ha un proprio ritmo, una propria armonia, un proprio silenzio. I dati del viaggio entrano come **clima**, non come spartito.

Il principio operativo condiviso è separare il tempo del viaggio dal clock musicale. Il motore Python può anche calcolare note e pattern o attivarli su attraversamento di soglie: il profilo continuo qui descritto non esclude queste regole configurabili.

---

## 2. Caratteristiche del sistema

Il profilo compositivo continuo proposto ha queste qualità:

- **Sequencer autonomo modulato dal paesaggio**, non sequencer pilotato dal CSV.
- **Stato più che evento**: il sistema vive in una *condizione* che evolve, non in una sequenza di trigger.
- **Inerzia**: ogni parametro ha memoria e interpolazione, mai reazioni istantanee.
- **Note rare e pensate**, mai una nota per ogni dato.
- **Continuità percettiva** garantita da un layer texture sempre presente.
- **BPM stabile per lunghi tratti**, evolve a scatti rari e morbidi.
- **Mapping espliciti**: una metrica può alimentare più regole e destinazioni; eventuali conflitti sullo stesso controllo devono essere risolti deliberatamente.

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

Queste limitazioni descrivono il profilo continuo storico, salvo la separazione dei clock che resta un vincolo architetturale. Non vietano ad altri profili di attivare pattern o calcolare note in Python.

- Latitudine e longitudine non diventano mai note.
- Direzione e curvatura istantanea non diventano mai trigger.
- La frequenza di campionamento del GPX non è la frequenza del sequencer. I due orologi sono separati.
- Nessun parametro del GPX viene passato al sistema musicale senza essere prima filtrato.
- Nel profilo storico si privilegiavano mapping uno-a-uno; il motore estensibile non impone questo limite.
- Nessuna nota viene generata da un singolo campione di dato.

---

## 7. Il flusso del segnale

Il flusso corrente separa tre responsabilità:

1. **Producer Python:** metriche neutre del viaggio (pilot implementato) e in futuro fatti geografici. Nessuna decisione musicale nel contratto del viaggio.
2. **Motore musicale Python:** stato e regole configurabili, incluse soglie, note e pattern. Produce decisioni indipendenti dal dispositivo; il contratto condiviso è ancora da definire.
3. **Adattatori e destinazioni:** traducono le decisioni nei controlli supportati e ne eseguono il timing musicale. Snake via OSC/M4L è il primo esperimento, non una dipendenza del motore. Altre destinazioni possono usare altri protocolli.

TouchDesigner resta un consumer visuale indipendente. La futura telemetria dell'esecuzione musicale è distinta dai dati del viaggio e non è ancora definita. Vedi la [decisione architetturale](../DECISIONE-ARCHITETTURA-AUDIO.md).

---

## 8. Criteri di verifica

Per valutare il profilo continuo, si propongono queste prove di ascolto:

1. **Test del silenzio dati.** Spegnendo il flusso GPX (valori fermi), il sistema continua a suonare in modo musicalmente coerente per diversi minuti.
2. **Test del congelamento.** Bloccando un singolo parametro per un minuto, la musica continua a evolvere ma in modo riconoscibilmente stabile.
3. **Test dell'accelerazione.** Riproducendo il GPX a velocità 10x, la musica non accelera in modo caotico: gli smoothing assorbono la variazione.
4. **Test della densità.** Nei layer melodici, il numero di note al minuto rientra in una fascia ambient/cinematografica (indicativamente 10–30 note al minuto). Il layer corpo può essere più denso ma con pattern ripetitivo.

Questi criteri non misurano la correttezza universale del motore. Per altri profili, inclusi quelli basati su soglie, definire risultati attesi propri. Il timeout e il comportamento senza dati vanno configurati esplicitamente.

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

Il producer metrico e la prima ricezione M4L sono già presenti. Non ricreare lo scaffolding o i modulatori esistenti. Il prossimo passo è una regola configurabile nel motore Python, una decisione indipendente dal device e un adattatore minimo per Snake.

La guida operativa è [INTEGRAZIONE-SNAKE.md](../INTEGRAZIONE-SNAKE.md); il lavoro residuo è in [TODO.md](../../TODO.md). Il contratto storico `/mod/*` resta un riferimento per riuso, non il contratto finale delle decisioni musicali.

---

## Appendice A — Proposta storica di modalità Live (non implementata)

I namespace e i vincoli di questa appendice sono ipotesi del prototipo precedente, da rivalutare nel consumer musicale. Non sono un protocollo attivo né richiedono ora un framework multiutente.

Il sistema è progettato per due modalità operative coesistenti:

- **Automatica**: i dati del viaggio modulano il sistema, come descritto in tutto il documento.
- **Live**: uno o più utenti interagiscono in tempo reale con il sistema, contribuendo modulazioni ed eventi.

La modalità live **non è in implementazione in questa fase**: l'architettura la rende possibile senza riscritture future, e questa appendice ne fissa i vincoli di design da rispettare fin da subito.

### A.1 Principio cardine

> **Anche l'utente non suona note. L'utente modula condizioni.**

Vale per l'utente la stessa regola del GPX: non si introducono trigger MIDI diretti, ma contributi a `/mod/*` e `/event/*`. Questa scelta preserva la coerenza dello stato e garantisce che il sistema resti musicalmente continuo anche durante l'interazione.

### A.2 Convivenza tra automatico e live

Le sorgenti automatiche e live convergono sugli **stessi bus**. Ogni canale `/mod/*` può ricevere contributi da più sorgenti contemporaneamente, fusi secondo una di queste modalità (dichiarate per canale, non globali):

- **Blend**: media pesata. Lo stato finale è la combinazione delle sorgenti.
- **Override**: l'utente prevale temporaneamente. Al termine dell'interazione, il sistema ritorna in modo graduale al valore automatico (con un fade configurato).
- **Offset**: l'utente aggiunge una variazione al valore automatico (utile per gesti espressivi sopra il sistema base).
- **Additive su soglia**: l'utente può solo *aumentare* o *aggiungere*, mai sottrarre (utile per non interferire con la narrazione automatica).

La scelta della modalità per ciascun canale è una decisione musicale: alcuni canali (tonalità) non andranno mai in override utente, altri (cutoff, jitter) sono naturalmente espressivi.

### A.3 Eventi prodotti dall'utente

Gli eventi possono nascere anche dall'utente. Il modello dati è già compatibile: `EventSource` prevede una terza origine `USER` (o `LIVE`) oltre a `DERIVED` ed `EXTERNAL`. Un evento `USER` ha la stessa struttura degli altri (kind, category, t, location, payload) e attraversa lo stesso filtro di cooldown e cap della pipeline.

L'autore di un'azione live può scegliere `kind` esistenti o crearne di nuovi nel registry, esattamente come per gli eventi esterni.

### A.4 Identità delle sorgenti

In modalità multi-utente serve poter distinguere chi ha prodotto cosa. Per questo:

- Gli eventi avranno un campo opzionale `source_id: str | None` (es. ``"marco"``, ``"gpx_auto"``, ``"user_42"``).
- I contributi a `/mod/*`, quando arriveranno da più sorgenti, saranno taggati con la stessa convenzione.

`source_id` ha tre usi:
1. **Visualizzazione**: vedere chi sta modulando cosa.
2. **Registrazione**: ricostruire una performance dopo l'evento.
3. **Risoluzione di conflitti**: regole come "l'utente A vince sull'utente B su questo canale".

### A.5 Trasporto in ingresso

Il sistema è già OSC-centrico in uscita. L'ingresso live userà gli **stessi protocolli OSC**, in direzione opposta, con un namespace dedicato:

- `/live/mod/<canale> <valore> [source_id]` per contribuire a un canale.
- `/live/event/<category>/<kind> <payload> [source_id]` per emettere un evento.

Ciò significa che ogni dispositivo che parla OSC (Lemur, TouchOSC, una webapp con OSC over WebSocket, un sensore custom) può diventare un client live senza modifiche al cuore del sistema.

### A.6 Cosa cambia *adesso* in vista del futuro

Per non dover stravolgere nulla quando la modalità live verrà attivata, oggi si introducono solo queste minime predisposizioni:

1. `EventSource` include il valore `USER` (anche se nessun detector lo produce ancora).
2. `Event` ha il campo opzionale `source_id: str | None = None`, lasciato a `None` per gli eventi automatici.
3. La pipeline si comporta in modo identico a prescindere dal `source_id`: è solo un'etichetta.

Nessuna logica di fusione, nessun trasporto in ingresso, nessun mixer vengono implementati in questa fase. Verranno aggiunti come **nuovi moduli** quando sarà il momento, senza toccare il codice esistente.

### A.7 Cosa non si fa ora

- Non si progetta la UI di un eventuale client live.
- Non si definisce il vocabolario completo dei messaggi `/live/...`.
- Non si implementa il mixer di canali multi-sorgente.
- Non si discute la modalità di sincronizzazione fra più utenti.

Tutto questo è demandato a una fase successiva, quando si avranno requisiti chiari dalla pratica.
