# Stato del progetto

## Funzionalità operative

### 1. Dati del viaggio e telemetria
- Lettura dei file GPX con interpolazione e calcolo continuo delle metriche (distanza, quota, pendenza, velocità, stima di sforzo).
- Ricampionamento dei dati a 10 Hz e pubblicazione OSC delle metriche ogni secondo del viaggio. La frequenza di pubblicazione è configurabile.
- Replay accelerato del viaggio per l'ascolto in tempo reale.

### 2. Generazione melodica (Snake)
- Generazione di pattern melodici in base all'avanzamento del viaggio e alla combinazione di velocità e sforzo.
- Transizioni tra sezioni della tappa con modulazione di scale e altezze di riferimento.
- Controllo in tempo reale dei parametri di Snake in Ableton Live tramite bridge Max for Live.
- Telemetria e previsione dello stato del sequencer (`/snake/state`) per la sincronizzazione delle altre voci.

### 3. Generatore del basso
- Composizione autonoma di linee di basso a partire dalla melodia (sostegno, dialogo o contrappunto ritmico).
- Sincronizzazione con il trasporto di Ableton Live tramite player dedicato a eventi programmati (`timepoint`).
- Tre assetti sonori calibrati: `sobrio` (appoggio minimale), `dialogo` (risposte negli spazi) e `ritmico` (slap e accenti sui levare).
- Aggiornamento dinamico dei parametri durante l'esecuzione tramite messaggi OSC (`/desnivel/v1/bass/control`) con transizioni fluide interpolate su finestre temporali.

---

## Aspetti in sviluppo

- **Music Director e Coordinator**: architettura a più livelli per gestire armonia comune e dipendenze tra più voci.
- **Quantizzazione metrica su Snake**: allineamento dei cambi di pattern a inizio battuta.
- **Calibrazione all'ascolto**: affinamento dei pesi armonici del generatore del basso durante le sessioni musicali.

Per il dettaglio delle attività aperte, consultare [TODO.md](../TODO.md).

