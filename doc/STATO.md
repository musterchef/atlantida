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

### 4. Sessione multivoce condivisa
- Avvio unico con `desnivel.cli.ensemble`: replay GPX, selezione del contesto delle sezioni, coordinamento dei generatori e invio delle frasi alle destinazioni.
- Organico e ruoli configurati per sezione; selezione manuale del ruolo e ritorno a `Follow section` dal dispositivo comune `Desnivel_Voice`.
- Generazione melodica da motivo con sviluppo su più finestre, ritmo variabile, pause, dinamica e conclusioni sulla tonica; preset letterale per il confronto.
- Collegamento delle parti al trasporto di Live e controlli compositivi esposti dal motore Python.
- Vista globale nel terminale e snapshot JSON con avanzamento, collegamenti, ruoli e decisioni effettive di Director e Coordinator.
- Esecuzione di melodia e accompagnamento verificata all'ascolto in Live.

[Sessione multivoce](SESSIONE-MULTIVOCE.md) · [Melodia](MELODIA.md) · [Dispositivo MIDI](VOCE-M4L.md)

---

## Aspetti in sviluppo

- **Proposte di sviluppo**: [plancia grafica globale](proposte/PLANCIA.md) e [catalogo delle voci e ruoli musicali](proposte/RUOLI-MUSICALI.md), separati dalle funzionalità operative.
- **Quantizzazione metrica su Snake**: allineamento dei cambi di pattern a inizio battuta.
- **Calibrazione all'ascolto**: affinamento dei pesi armonici del generatore del basso durante le sessioni musicali.

Per il dettaglio delle attività aperte, consultare [TODO.md](../TODO.md).

