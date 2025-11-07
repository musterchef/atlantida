# **DESNIVEL — Documento di Ricerca**
### *dal viaggio al suono, dal terreno al gesto audiovisivo*  

---

## **1. Abstract**

**Desnivel** è un progetto di traduzione sensoriale e audiovisiva che trasforma un viaggio reale — da *Torino a Castel del Monte* — in una composizione generativa di suono e immagine.  
Attraverso l’analisi dei dati GPS (GPX) e la loro reinterpretazione come parametri musicali e visivi, il progetto esplora la possibilità di comporre a partire dal paesaggio, dalla fatica e dal tempo umano.  
Desnivel indaga come la lentezza, la continuità e la durata possano diventare materia compositiva: non per rappresentare il viaggio, ma per **ascoltarlo**.

---

## **2. Introduzione — Il corpo come metronomo**

L’origine di Desnivel risiede in un’esperienza fisica: pedalare per otto ore al giorno, per giorni consecutivi, attraversando paesaggi che mutano lentamente.  
Il tempo del corpo, scandito da gesti ripetuti, diventa un sistema di misura del mondo. Ogni curva, pendenza o variazione di luce è un micro-evento che si inscrive nella durata.

In un’epoca dominata dalla velocità e dalla compressione temporale, Desnivel propone un approccio opposto: la **lentezza come ascolto**, come modo di percepire la continuità e la trasformazione.  
L’obiettivo della ricerca è sviluppare una grammatica audiovisiva capace di **tradurre la durata fisica in forma sensoriale**, trasformando i dati del movimento in suono e immagine senza perdere la loro natura organica.

Domande guida:
- È possibile comporre con la lentezza?  
- Come può il paesaggio diventare struttura musicale?  
- In che modo il corpo, il terreno e il tempo dialogano all’interno di un sistema generativo?

---

## **3. Fondamenti teorici — Paesaggio, durata, percezione**

### **3.1 Il paesaggio come partitura**
Ogni territorio possiede un ritmo interno: una distribuzione di salite, curve, cambi di luce e densità.  
Registrare una traccia GPX significa catturare quella struttura temporale e spaziale, una *partitura latente* che attende di essere suonata.  
Desnivel considera il paesaggio non come scenario, ma come **sorgente musicale**, un insieme di relazioni geometriche e temporali che si manifestano come suono.

### **3.2 La lentezza come forma di ascolto**
La lentezza è il contrario della stasi: è movimento espanso.  
Attraverso la lentezza, l’ascolto diventa profondo, capace di cogliere micro-variazioni che altrimenti sfuggirebbero.  
Nel progetto, la lentezza non viene corretta né accelerata, ma reinterpretata attraverso *time-warp percettivi* che mantengono la densità emotiva del gesto originario.

### **3.3 Il corpo come interfaccia**
Il corpo è il primo sensore, il primo convertitore di energia in segno.  
La pedalata, il respiro, la fatica: tutti elementi che, anche se non esplicitamente registrati, informano la logica del suono generato.  
Desnivel assume il corpo come **metronomo naturale**: ogni sua oscillazione diventa una fonte di modulazione, un riferimento temporale non artificiale.

---

## **4. Metodologia — Dal terreno al suono, dal dato al gesto**

Il cuore metodologico del progetto è la traduzione dei dati spaziali e temporali del viaggio in eventi audiovisivi coerenti.  
L’approccio combina strumenti di analisi numerica (Python, TouchDesigner) e ambienti di composizione musicale (Ableton Live), articolandosi in quattro fasi principali.

### **4.1 Raccolta e preprocessamento**
- Dati GPX registrati tramite dispositivo GPS (latitudine, longitudine, altitudine, velocità, tempo).  
- Calcolo di parametri derivati: pendenza, curvatura, entropia altimetrica, variazioni di flusso.  
- Filtraggio e normalizzazione per ridurre il rumore dei sensori.

### **4.2 Analisi semantica**
I dati vengono interpretati per generare **indici sensoriali**:
- *terrain_index*: tipo di paesaggio (pianura, collina, montagna, costa).  
- *difficulty_index*: intensità fisica percepita.  
- *flow_index*: continuità del movimento.  
- *time_of_day*: colore della luce e tono emozionale.  
Questi indici costituiscono la base narrativa e guidano la generazione musicale.

### **4.3 Temporalità adattiva**
La durata reale del viaggio (circa otto ore al giorno) viene compressa secondo una logica **non lineare**:  
- zone di sforzo vengono dilatate,  
- tratti fluidi vengono compressi,  
- eventi chiave (curve, vette, pause) diventano nodi musicali.  

### **4.4 Traduzione e sintesi**
I valori risultanti controllano parametri sonori (pitch, densità ritmica, timbro, riverbero) e visivi (luce, forma, materia).  
Il sistema agisce come un **interprete automatico**, dove i dati non sono comandi ma suggestioni, trasformate in gesto audiovisivo.

---

## **5. Architettura del sistema — Un organismo relazionale**

### **5.1 Input**
- Traccia GPX (coordinate, altitudine, velocità, tempo).  
- Layer aggiuntivi: dati meteorologici, ora solare, video GoPro sincronizzati.  

### **5.2 Processing**
- Analisi numerica e derivazione di indici.  
- Calcolo di pesi narrativi per ogni campione (importanza musicale/visiva).  
- Mappatura dei dati in spazi semantici: ritmo, armonia, intensità, colore.

### **5.3 Output**
- **Ableton Live**: modulazione di parametri musicali via MIDI/OSC.  
- **TouchDesigner**: generazione di forme, luci e movimenti coerenti con l’andamento del percorso.  
- Sincronizzazione tra suono e immagine tramite timeline comune.

### **5.4 Logica di comportamento**
Il sistema funziona come un **organismo relazionale**: non riproduce un evento, ma reagisce a esso.  
Ogni punto della traccia genera una risposta contestuale; la composizione è quindi **procedurale**, mai identica a se stessa.

---

## **6. Traduzione sonora e visiva — Musica dentro i dati**

### **6.1 Mappature sensoriali**
| Dato geografico | Parametro sensoriale | Effetto percettivo |
|------------------|----------------------|--------------------|
| Altitudine | Altezza delle note / apertura del filtro | Più sali → più brillantezza, tensione |
| Curvatura | Densità ritmica / microbeat | Curve = instabilità, groove |
| Velocità | Pulsazione / BPM | Ritmo corporeo naturale |
| Pendenza | Timbro / saturazione | Salita = tensione, discesa = rilascio |
| Flow Index | Riverbero / spazialità | Continuità = respiro |
| Time of Day | Timbro armonico / colore visivo | Luce = tonalità emotiva |

### **6.2 Tempo e durata**
La lentezza viene trattata come una dimensione attiva:  
non un limite, ma una scala.  
La durata fisica del viaggio diventa materiale ritmico e narrativo.  
Le otto ore di pedalata si traducono in cicli di ascolto, variazioni di densità e tensione, forme che respirano nel tempo lungo.

### **6.3 Stratificazione percettiva**
Desnivel organizza i suoni in quattro layer principali:
1. **Corpo** – ritmo e pulsazione (velocità, sforzo).  
2. **Terreno** – armonia e texture (altitudine, pendenza).  
3. **Paesaggio** – spazio e luce (flow, time of day).  
4. **Evento** – accenti e rotture (curve, vette, pause).  

L’interazione tra questi strati genera un continuum narrativo, un equilibrio tra forma e variabilità.

---

## **7. Interazione e performance — Dialogo con la macchina**

Il performer non “suona” Desnivel, ma lo **ascolta e lo modula**.  
L’intervento umano avviene su livelli globali:
- variazione di timbro e tonalità generale,  
- modulazione della densità visiva,  
- transizioni tra stati del paesaggio.  

L’artista diventa un **interprete della durata**, un mediatore tra il corpo originario del viaggio e il sistema generativo.  
La performance non è ripetizione ma *ri-ascolto del tempo*.

---

## **8. Risultati e prospettive — La durata come paesaggio**

Desnivel produce una composizione audiovisiva non lineare, basata su relazioni tra corpo, terreno e luce.  
L’obiettivo non è la fedeltà geografica, ma la **fedeltà percettiva**:  
rendere udibile e visibile la qualità sensoriale di un viaggio.

Prospettive future:
- Estendere il sistema a viaggi multipli o collettivi (rete di ciclisti / performer).  
- Integrare dati meteorologici e astronomici come fonti di modulazione.  
- Trasformare il progetto in **installazione interattiva** o **concerto generativo**.

---

## **9. Nota metodologica**

Le logiche di mappatura, i calcoli numerici e gli algoritmi di derivazione sono integrati concettualmente in questo documento e non rimandano a materiali esterni.  
Eventuali script o dataset di supporto vengono trattati come strumenti di laboratorio, non come allegati teorici.  
Desnivel è un progetto unico e autosufficiente, in cui tecnica e poetica si fondono in un’unica architettura di senso.

---

**Autore:** Marco Musto  
**Titolo:** *Desnivel — dal viaggio al suono, dal terreno al gesto audiovisivo*  
**Versione:** Research Document vA  
**Data:** Novembre 2025  
**Luoghi:** Torino → Castel del Monte  

---
