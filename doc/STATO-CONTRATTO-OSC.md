# Stato dell'integrazione

Aggiornato il 2026-10-04.

| Parte | Stato |
|---|---|
| Producer GPX | Implementato: sei metriche con timestamp, inviate via OSC. |
| Ricezione M4L | Verificata dall'utente in Ableton. |
| Controllo manuale Snake | Verificato con `live.object` sul parametro `Note_01`, range 0–83. |
| Motore musicale separato | Soglia con isteresi e interpretazioni pesate movimento/sforzo. |
| Contratto delle decisioni musicali | Pattern con note e gate, cambi con timestamp e stato. |
| Adattatori di destinazione | Snake: note, gate e Shape; player M4L: frasi MIDI. |
| Comandi OSC verso M4L | Controllo per nome verificato dall’utente su note e gate. |
| Pattern dal viaggio | Test Python e dry-run verificati; ascolto in Live da eseguire. Timing a battuta assente. |

## File disponibili

Il producer usa `src/desnivel/trip_metrics.py` e `src/desnivel/sinks/trip_metrics_osc.py`. Il comando è `desnivel-stream-metrics`.

`m4l/desnivel-bridge.amxd` riceve le metriche (porta 9000) e i comandi di controllo `/desnivel/v1/control/snake/set <nome> <valore>` (porta 9001).

## Limiti

- Il producer esporta metriche; i fatti geografici neutrali sono ancora da definire.
- Il receiver dimostrativo mantiene l'ultimo valore ricevuto: il timeout è da implementare.
- La ricostruzione delle quote mancanti non è accompagnata da un flag di qualità.
- L'assegnazione del parametro a `live.remote~` ha causato crash durante la prova. Il controllo verificato usa `live.object`.

[Contratto dati](CONTRATTO-DATI-VIAGGIO.md) · [Guida Snake](INTEGRAZIONE-SNAKE.md) · [Inventario precedente](archivio/INVENTARIO-PROTOTIPO.md)

[Prima regola e prova di ascolto](TEST-VIAGGIO-SNAKE.md).

## Preset del viaggio

Disponibili movimento, sforzo e misto, con percorso armonico per tappa. [Comandi e configurazione](TEST-PRESET-MUSICALI.md). Test Python e generazione verificati; ascolto in Live da eseguire.

## Player M4L

Ricezione e riproduzione confermate dall’utente in Live. Frasi di prova indipendenti dal viaggio; sincronizzazione avanzata ancora da validare. [Guida](PLAYER-M4L.md).
