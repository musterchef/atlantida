# Materiali archiviati

Questa cartella raccoglie i componenti esclusi dal percorso di sviluppo corrente.
I nomi dei file e la struttura relativa dei gruppi sono conservati.

| Percorso | Contenuto |
|---|---|
| `src/desnivel/` | Pipeline `/mod/*`, modulatori, detector, classifier, geografia, bridge MIDI e CLI precedenti. Include le versioni storiche di configurazione, Track e sink OSC condivisi. |
| `tests/` | Test dei componenti archiviati. |
| `old/` | Prototipi precedenti, estrazione GoPro, sonificazione e integrazione TD/audio. |
| `td/` | Progetti TouchDesigner, shader, loader CSV e backup locali. |
| `data/coastline/` | Shapefile usato dalla pipeline geografica archiviata. |
| `gpx/gopro/` | Tracce parziali delle riprese GoPro. |
| `requirements.txt` | Dipendenze del vecchio ambiente. |
| `ciao` | Presentazione storica in catalano. |
| `output-locale/` | Output generati già presenti sul computer, esclusi da Git. |

Il codice è conservato per consultazione e recupero: non costituisce un pacchetto autonomo eseguibile. I vecchi entry point non sono installati e i test qui raccolti non fanno parte della suite corrente. Per riattivare un componente occorre verificarne dipendenze, percorsi e contratti rispetto al sistema attuale.

La documentazione storica resta in [doc/archivio](../doc/archivio/README.md).
Per lo sviluppo usare [i comandi correnti](../doc/COMANDI.md) e l’[architettura musicale](../doc/TODO-ARCHITECTURE.md).
