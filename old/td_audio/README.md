# Archivio del prototipo TouchDesigner → audio

Archiviato il 2026-10-02: questo percorso non è quello di sviluppo corrente.

- `frame_execute.py`: legge CSV/sonic JSON, aggiorna shader e invia controlli audio da TD.
- `osc_ableton_setup.py`: istruzioni e sender di test del precedente protocollo.
- `m4l/desnivel.maxpat` e `m4l/desnivel_notes.js`: receiver e generatore di note autonomo con regole musicali in JavaScript.

I quattro file sono stati spostati insieme senza modificarne il contenuto. Il JS è una dipendenza della patch archiviata; non è usato dalla patch Snake in `m4l/`.

I progetti `.toe`, shader e loader visuali restano in `td/`. Eventuali riferimenti esterni nei `.toe` ai vecchi percorsi non sono stati aggiornati né verificati: per rieseguire questo prototipo occorre puntarli ai file di questo archivio. Il callback archiviato contiene anche aggiornamenti visuali, per questo è conservato interamente.

Per il percorso corrente vedere [la decisione architetturale](../../doc/DECISIONE-ARCHITETTURA-AUDIO.md).
