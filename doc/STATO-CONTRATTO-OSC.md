# Stato dell'integrazione

Aggiornato il 2026-10-02.

| Parte | Stato |
|---|---|
| Producer GPX | Implementato: sei metriche con timestamp, inviate via OSC. |
| Ricezione M4L | Verificata dall'utente in Ableton. |
| Controllo manuale Snake | Verificato con `live.object` sul parametro `Note_01`, range 0–83. |
| Motore musicale separato | Da implementare. |
| Contratto delle decisioni musicali | Da definire. |
| Adattatori di destinazione | Da implementare, iniziando da Snake. |
| Comandi OSC verso M4L | Da definire e collegare alla patch. |
| Pattern completi e timing | Da verificare. |

## File disponibili

Il producer usa `src/desnivel/trip_metrics.py` e `src/desnivel/sinks/trip_metrics_osc.py`. Il comando è `desnivel-stream-metrics`.

`m4l/desnivel_snake_bridge.maxpat` contiene il receiver iniziale. Le modifiche fatte manualmente in Live, compreso il controllo del parametro, devono ancora essere salvate nel repository.

## Limiti

- Il producer esporta metriche; i fatti geografici neutrali sono ancora da definire.
- Il receiver dimostrativo mantiene l'ultimo valore ricevuto: il timeout è da implementare.
- La ricostruzione delle quote mancanti non è accompagnata da un flag di qualità.
- L'assegnazione del parametro a `live.remote~` ha causato crash durante la prova. Il controllo verificato usa `live.object`.

[Contratto dati](CONTRATTO-DATI-VIAGGIO.md) · [Guida Snake](INTEGRAZIONE-SNAKE.md) · [Inventario precedente](archivio/INVENTARIO-PROTOTIPO.md)
