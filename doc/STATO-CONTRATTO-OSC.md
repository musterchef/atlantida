# Stato dell'integrazione

Riepilogo dei percorsi implementati. Per risultati e configurazioni delle prove vedere lo [stato del progetto](SESSIONE.md).

| Parte | Stato |
|---|---|
| Producer GPX | Implementato: sei metriche con timestamp, inviate via OSC. |
| Ricezione M4L | Verificata dall'utente in Ableton. |
| Controllo manuale Snake | Verificato con `live.object` sul parametro `Note_01`, range 0–83. |
| Motore musicale separato | Soglia con isteresi e interpretazioni pesate movimento/sforzo. |
| Contratto delle decisioni musicali | Pattern con note e gate, cambi con timestamp e stato. |
| Adattatori di destinazione | Snake: note, gate e Shape; player M4L: frasi MIDI. |
| Comandi OSC verso M4L | Controllo per nome verificato dall’utente su note e gate. |
| Pattern dal viaggio | Replay Firenze confermato in Live. Cambi dei parametri immediati, senza quantizzazione a battuta. |
| Export e basso live | Previsione Snake e piani del basso confrontati con MIDI nelle configurazioni documentate. |
| Controlli del basso | Ricevitore OSC e transizioni implementati; mittente e andamento musicale della tappa da implementare. |
| Director e Coordinator | Definiti nell’[architettura musicale](TODO-ARCHITECTURE.md), da implementare come componenti condivisi. |

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

Disponibili movimento, sforzo e misto, con percorso armonico per tappa. [Comandi e configurazione](TEST-PRESET-MUSICALI.md). Replay Firenze confermato in Live; gli altri preset e gli assetti del basso richiedono valutazione musicale. Dettagli nello [stato del progetto](SESSIONE.md).

## Player M4L

Il player ciclico di frasi e il player dei piani assoluti del basso sono percorsi distinti. L’esecuzione dei piani del basso è stata confrontata con tre registrazioni MIDI; Stop/ripartenza, seek e cambi di tempo richiedono ulteriori verifiche. [Guida](PLAYER-M4L.md).
