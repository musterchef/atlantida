# DESNIVEL — Contratto delle modulazioni e degli eventi

> Specifica precisa di ciò che esce dalla pipeline Python e di ciò che entra in Ableton attraverso TouchDesigner.
> Questo documento è il **contratto** tra i tre stadi del sistema. Finché non viene modificato qui, nessuno dei tre stadi cambia ciò che produce o consuma.
>
> Riferimento concettuale: [ARCHITETTURA-MUSICALE.md](ARCHITETTURA-MUSICALE.md)

---

## 1. Principi del contratto

1. **Due bus separati.** Le modulazioni continue e gli eventi rari viaggiano su due canali OSC distinti. Non si mescolano mai.
2. **Tutto è già pronto all'uso.** Ogni valore inviato è già filtrato, già nel range musicalmente utile, già nella scala temporale corretta. Il ricevitore non deve fare smoothing.
3. **Frequenza coerente con il contenuto.** Una modulazione macro non viene inviata a 60 Hz. Ogni canale ha la sua frequenza di aggiornamento.
4. **Nessuna nota in questo contratto.** Il contratto descrive condizioni, non note. Le note nascono in Ableton.

---

## 2. Il bus delle modulazioni continue

Indirizzo radice: `/mod/`
Trasporto: OSC su UDP
Tipo dei valori: `float` salvo dove indicato `int`
Range nominale: `[0.0, 1.0]` salvo dove indicato

### 2.0 Modulazioni di arco di tappa

Frequenza di invio: **0.2 Hz** (un messaggio ogni 5 secondi è più che sufficiente)
Inerzia interna: nessun smoothing necessario, sono curve già lisce per costruzione.
Validità: l'intera durata della tappa.

| Canale | Tipo | Significato musicale | Sorgente dal viaggio |
|---|---|---|---|
| `/mod/journey/phase` | `float` | Posizione lungo la tappa, da 0 (inizio) a 1 (fine) | Tempo di esecuzione / distanza percorsa |
| `/mod/journey/energy` | `float` | Tensione di lungo periodo, indipendente da `meso/tension` | Integratore lentissimo sullo sforzo accumulato dell'intera tappa |
| `/mod/journey/openness` | `float` | Apertura progressiva del sistema (densità di layer attivi, ampiezza spettrale media) | Curva narrativa basata su `phase` e profilo della tappa |

Questi canali modulano in modo **molto sottile** tutti gli altri. Non hanno transizioni: evolvono monotonamente o quasi.

### 2.1 Modulazioni di macrotempo

Frequenza di invio: **1 Hz**
Inerzia interna: smoothing con memoria di **60–120 secondi**, permanenza minima **60 secondi**.

| Canale | Tipo | Significato musicale | Sorgente dal viaggio |
|---|---|---|---|
| `/mod/macro/scale` | `int` | Indice della scala musicale corrente (0=pentatonica, 1=dorian, 2=phrygian, 3=mixolydian, 4=lydian, 5=whole-tone) | Tipo di terreno aggregato |
| `/mod/macro/palette` | `int` | Famiglia timbrica corrente (0=pad, 1=strings, 2=bells, 3=granular, 4=brass) | Carattere del territorio |
| `/mod/macro/register` | `float` | Centro di registro, dal grave (0) all'acuto (1) | Altitudine media |
| `/mod/macro/space` | `float` | Quantità di riverbero e larghezza stereo | Apertura del paesaggio, vicinanza al mare |
| `/mod/macro/brightness` | `float` | Brillantezza spettrale generale | Luce stimata, ora del giorno |

### 2.2 Modulazioni di mesotempo

Frequenza di invio: **4 Hz**
Inerzia interna: smoothing con memoria di **5–10 secondi**, banda morta moderata.

| Canale | Tipo | Significato musicale | Sorgente dal viaggio |
|---|---|---|---|
| `/mod/meso/density` | `float` | Quanto è popolato il pattern | Sforzo |
| `/mod/meso/probability` | `float` | Probabilità media che uno step suoni | Sforzo, accumulo di tensione |
| `/mod/meso/gate` | `float` | Lunghezza delle note (da staccato a tenuto) | Scorrevolezza del movimento |
| `/mod/meso/root` | `int` | Scostamento in semitoni della root rispetto al riferimento della tappa | Pendenza filtrata |
| `/mod/meso/cutoff` | `float` | Apertura del filtro principale | Velocità filtrata |
| `/mod/meso/tension` | `float` | Tensione accumulata, da rilasciare in modulazioni armoniche | Integratore con decadimento (vedi §4) |

### 2.3 Modulazioni di microtempo

Frequenza di invio: **10–20 Hz**
Inerzia interna: smoothing leggero, memoria **100–300 ms**.

| Canale | Tipo | Significato musicale | Sorgente dal viaggio |
|---|---|---|---|
| `/mod/micro/lfo_depth` | `float` | Profondità delle modulazioni cicliche | Variabilità locale del segnale |
| `/mod/micro/jitter` | `float` | Quantità di sfasamento dei timing | Rugosità del terreno |
| `/mod/micro/detune` | `float` | Micro-variazioni di intonazione | Vibrazione del movimento |
| `/mod/micro/pan_drift` | `float` | Movimento stereo lento | Direzione del cammino (smussata) |

### 2.4 Modulazioni del layer corpo

Frequenza di invio: **2 Hz**
Inerzia interna: pesante. Il BPM e la struttura del pattern cambiano raramente.

| Canale | Tipo | Significato musicale | Sorgente dal viaggio |
|---|---|---|---|
| `/mod/body/bpm` | `float` | BPM corrente, già stabilizzato | Velocità (catena di smoothing già esistente) |
| `/mod/body/euclid_k` | `int` | Numero di pulse del pattern euclideo (su 16 step) | Sforzo |
| `/mod/body/euclid_rot` | `int` | Rotazione del pattern | Cadenza del movimento, se disponibile |
| `/mod/body/swing` | `float` | Quantità di swing applicato | Scorrevolezza |

---

## 3. Il bus degli eventi

Indirizzo radice: `/event/`
Trasporto: OSC su UDP

Gli eventi si dividono in **due categorie distinte**, su sotto-namespace separati. Le due categorie hanno significato e comportamento musicale diversi e non si confondono.

### 3.1 Eventi maggiori — `/event/major/*`

Massimo **3–5 per tappa intera**. Sono i momenti memorabili del viaggio.
Producono un gesto musicale identificabile (singola nota tenuta, campanellino, apertura del riverbero, ingresso di un sub-layer raro). Il gesto specifico è deciso da Ableton in base allo stato corrente, non dal contratto.

Cooldown obbligatorio: **almeno 10 minuti** tra un evento maggiore e il successivo. Se la stessa tappa avesse più vette candidate, ne passa **solo quella con la prominenza topografica maggiore**.

| Evento | Significato musicale | Condizione di trigger |
|---|---|---|
| `/event/major/start` | Apertura della tappa: introduzione progressiva dei layer | Inizio della tappa, una sola volta |
| `/event/major/summit` | Apertura del riverbero, palette rarefatta, eventuale nota tenuta | Vetta principale della tappa: picco interno con prominenza massima, sopra soglia (default 50 m) |
| `/event/major/sea` | Attivazione del sub-layer marino con coda infinita | Prima volta che la distanza dalla costa scende sotto soglia |
| `/event/major/city_arrival` | Introduzione di un timbro più ricco e definito | Ingresso nella città di arrivo della tappa |
| `/event/major/end` | Chiusura: rarefazione progressiva fino al silenzio | Fine della tappa, una sola volta |

Ogni evento maggiore porta un **payload** con il valore numerico significativo (es. quota della vetta, distanza dalla costa) per consentire all'esecutore di scegliere il gesto con sfumature.

### 3.1.1 Varianti di `start` e `end`

Gli eventi `start` e `end` sono *framing* obbligatori della tappa: cadono sempre, e una sola volta. Il loro carattere musicale specifico (chiusura con pad luminoso conquistato, chiusura nella natura, apertura in cascina all'alba, apertura urbana, ecc.) non è codificato come evento separato, ma come **varianti del payload**:

```
payload: {
  "variants": ["climb", "natural"],
  "climb_delta_m": 323.1,
  "final_ele_m": 531.6,
  ...
}
```

Il campo `variants` è una **lista** di etichette: la stessa chiusura può essere sia `climb` sia `sunset`. Ogni variante contribuisce i propri campi specifici al payload.

Varianti previste (lista estendibile senza modifiche al contratto OSC):

| Variante | Significato | Campi aggiuntivi |
|---|---|---|
| `standard` | Default, niente di particolare da segnalare. | `final_ele_m` |
| `climb` | Termina in salita significativa. | `climb_delta_m`, `final_ele_m` |
| `descent` | Termina dopo lunga discesa. | `descent_delta_m`, `final_ele_m` |
| `coastal` | Termina vicino al mare. | `coast_distance_m` |
| `urban` | Termina in città conosciuta. | `city_name` |
| `natural` | Termina lontano da centri abitati. | `nearest_city_km` |
| `dawn` | Inizia/termina nei minuti dell'alba. | `sun_delta_s` |
| `sunset` | Inizia/termina nei minuti del tramonto. | `sun_delta_s` |
| `night` | Inizia/termina in notturna. | `sun_delta_s` |
| `manual` | Marcato esplicitamente dall'autore (es. "saluto con Lollo"). | `note` |

Le varianti sono prodotte da **classificatori pluggabili** (vedi IMPLEMENTAZIONE.md): ogni classifier osserva l'evento e il `Track`, e decide se aggiungere la propria etichetta al `variants` e i propri campi al payload. L'aggiunta di una nuova variante non richiede modifiche al contratto OSC: l'esecutore (TouchDesigner/Ableton) può anche ignorare le varianti che non riconosce.

### 3.2 Eventi minori — `/event/minor/*`

Non producono un gesto musicale autonomo. **Accelerano una transizione di stato** che il macro starebbe già facendo lentamente. In pratica dicono al sistema: "la transizione che stavi preparando in 60 secondi, falla in 15".

Frequenza: occasionale, mai più di **un evento minore ogni 90 secondi**.

Formato del messaggio: `/event/minor/<tipo> <intensità_accelerazione 0..1>`

| Evento | Cosa accelera | Condizione di trigger |
|---|---|---|
| `/event/minor/territory_change` | La transizione di `/mod/macro/scale` e `/mod/macro/palette` | Cambio classificato del terreno, stabile per N secondi |
| `/event/minor/city_enter` | La transizione di `/mod/macro/brightness` e `/mod/macro/palette` | Ingresso in area urbana (città minore o di passaggio) |
| `/event/minor/city_exit` | Ritorno della palette di territorio | Uscita dall'area urbana |
| `/event/minor/stop` | Rallentamento di `/mod/meso/density` verso il silenzio del layer corpo | Velocità sotto soglia per oltre N secondi |
| `/event/minor/resume` | Rientro graduale del layer corpo | Ripresa del movimento dopo `stop` |
| `/event/minor/local_summit` | Leggero scostamento di `/mod/macro/register` verso l'acuto | Massimo locale di altitudine, non globale |

Un evento minore **non produce mai una nota**. È un puro modulatore della curvatura di transizione del macro.

---

## 4. L'integratore di tensione

`/mod/meso/tension` non è la lettura di un singolo dato. È una **memoria con decadimento** che accumula nel tempo le componenti faticose del paesaggio e le rilascia lentamente.

Comportamento:
- Si carica quando lo sforzo è alto (salita, pendenza positiva, velocità bassa con effort alto).
- Si scarica con costante di tempo lenta (dell'ordine del minuto) quando la condizione cessa.
- È limitato a `[0, 1]`.
- Esce dal lato Python già completamente filtrato.

Effetto musicale tipico: dà al sistema il senso di **carica e rilascio**, l'arco drammatico tipico delle composizioni che respirano.

---

## 5. Frequenze e larghezza di banda

Il volume di traffico OSC complessivo resta basso (poche decine di messaggi al secondo). Questo è intenzionale: il sistema deve **sembrare lento anche dal lato dei dati**, non solo nel suono.

| Bus | Frequenza tipica | Note |
|---|---|---|
| `/mod/journey/*` | 0.2 Hz | Cambia molto lentamente, una curva continua |
| `/mod/macro/*` | 1 Hz | Cambia poco, può essere inviato anche solo on-change |
| `/mod/meso/*` | 4 Hz | Sufficiente per modulazioni armoniche e timbriche |
| `/mod/body/*` | 2 Hz | Il pattern non si ridisegna a frame-rate |
| `/mod/micro/*` | 10–20 Hz | L'unico canale "veloce", ma di valori sempre smussati |
| `/event/major/*` | 3–5 per tappa | Cooldown 10 minuti |
| `/event/minor/*` | sporadica | Cooldown 90 secondi |

---

## 6. Responsabilità per stadio

### Stadio Python
- Calcola tutte le metriche derivate dal GPX.
- Applica **tutti** gli smoothing macro, meso e di tensione.
- Produce i canali a tutte le frequenze indicate, in tempo reale o pre-renderizzati su un file di curve.
- Mantiene lo stato per applicare permanenza minima e cooldown degli eventi.

### Stadio TouchDesigner
- Riceve i canali Python (o li legge da file di curve).
- Aggiunge le modulazioni di microtempo (LFO, jitter) se non sono pre-calcolate.
- Si occupa del **tempo di esecuzione**: scrubbing, pausa, riproduzione di una tappa.
- Inoltra tutto via OSC ad Ableton.

### Stadio Ableton / Max for Live
- Riceve `/mod/*` e `/event/*`.
- Contiene i quattro sequencer (uno per layer).
- Non applica smoothing aggiuntivo: si fida del contratto.
- Non genera mai note a partire da un canale `/mod/*` direttamente. Le note nascono dai sequencer, modulati dai canali.

---

## 7. Cosa NON è in questo contratto

Per chiarezza, queste cose non viaggiano sui bus `/mod/` e `/event/`:

- Note MIDI di alcun tipo.
- Coordinate geografiche grezze.
- Heading, bearing, curvatura istantanea.
- Timestamp assoluti del viaggio (sono gestiti da TouchDesigner come tempo di esecuzione).
- Dati per la visualizzazione video (vivono su un bus separato non oggetto di questo documento).

---

## 8. Versione del contratto

Versione **0.4** — introduce le **varianti del payload** per `start` e `end` (`payload.variants: list[str]`) prodotte da classificatori pluggabili, e ritira `arrival_climb` come evento autonomo (ora è la variante `climb` di `end`). Razionale: la chiusura di una tappa è sempre una sola, ma il suo carattere (in salita, al tramonto, in cascina, in città) si compone da più osservazioni indipendenti senza moltiplicare i tipi di evento. Permette di aggiungere nuove varianti senza modifiche al contratto OSC.

Storico:
- **0.3** — chiarisce la selezione della vetta principale (prominenza topografica, non altezza assoluta) e introduce l'evento maggiore `arrival_climb` per le tappe che terminano in salita (es. Dogliani, Castel del Monte). Modifica additiva, ma cambia la *definizione* del trigger di `summit` (da "massimo globale" a "picco con prominenza massima").
- **0.2** — introduce la scala `journey` (arco di tappa) e la suddivisione degli eventi in **maggiori** (gesto musicale) e **minori** (transizioni di stato accelerate, nessuna nota).
- **0.1** — bozza iniziale, tre scale temporali, un solo bus eventi.

Ogni modifica al contratto richiede l'aggiornamento di tutti e tre gli stadi. Le modifiche additive (nuovi canali) sono compatibili all'indietro; le modifiche al significato di un canale esistente sono **breaking** e richiedono un cambio di versione minore.
