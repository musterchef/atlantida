# Indice della documentazione

Guida alla documentazione di **Desnivel**, organizzata per aree tematiche.

---

## Panoramica e sistema

| Documento | Argomento |
|---|---|
| [Presentazione](../README.md) | Origine del progetto, viaggio da Torino a Castel del Monte e i tre livelli di lettura. |
| [Architettura](ARCHITETTURA.md) | Pipeline modulare, flusso dei dati, modelli musicali e organizzazione del codice. |
| [Sessione multivoce Python](SESSIONE-MULTIVOCE.md) | Comando unico, replay, generatori, dispositivi e stato globale. |
| [Configurazione](CONFIGURAZIONE.md) | Campi JSON, unità, limiti dei controlli, ruoli e precedenze. |
| [Voci e contesto musicale](RUOLI-MUSICALI.md) | Strutture esistenti per voci, dipendenze, richieste di pianificazione e contesto di sezione. |
| [Stato del progetto](STATO.md) | Funzionalità operative verificate e sviluppi aperti. |
| [Passaggio di consegne](PASSAGGIO-CONSEGNE.md) | Stato della prova a quattro voci, architettura, configurazioni, comandi e lavoro aperto per riprendere il progetto. |
| [Comandi e setup](COMANDI.md) | Ambiente virtuale, porte di rete, streaming delle metriche, launcher e test suite. |
| [TODO](../TODO.md) | Roadmap delle attività di ricerca e sviluppo. |

---

## Dati del viaggio e integrazioni attive

| Documento | Argomento |
|---|---|
| [Dispositivo MIDI di voce](VOCE-M4L.md) | Device comune, collegamento Python, controlli e prova di esecuzione. |
| [Dati del viaggio](DATI-VIAGGIO.md) | Lettura GPX, calcolo continuo delle metriche (quota, pendenza, sforzo) e formato OSC. |
| [Analisi del percorso](ANALISI-PERCORSO.md) | Zone del profilo altimetrico, macrosezioni configurabili, report visuale e misure di verifica. |
| [Sequencer Snake](SNAKE.md) | Banco di prova per la linea melodica: integrazione del sequencer Snake, bridge M4L e telemetria. |
| [Generazione melodica](MELODIA.md) | Motivo, sviluppo delle frasi, controlli e riproducibilità. |
| [Generatore del basso](BASSO.md) | Banco di prova per l'accompagnamento: logica di contrappunto e dialogo con la melodia, controlli live e player. |
| [Tappe e percorsi modali](TAPPE-E-PRESET.md) | Caratterizzazione modale delle tappe (Levanto, Firenze, Sabaudia, Peschici) e ascolto. |

---

## Proposte di sviluppo

Materiale di progettazione separato dalla documentazione del sistema attuale.

- [Ruoli musicali e organico](proposte/RUOLI-MUSICALI.md): impostazione condivisa, vocabolario proposto e decisioni aperte.
- [Catalogo e assegnazioni per sezione](proposte/CATALOGO-E-SEZIONI.md): bozza JSON di vocabolario, strumenti e organico manuale.
- [Plancia globale](proposte/PLANCIA.md): informazioni da mostrare e decisioni aperte sull’interfaccia.
- [Sezioni guidate dal viaggio](proposte/SEZIONI-GUIDATE-DAL-VIAGGIO.md): assetti delle macrosezioni operativi e variazioni interne ancora da definire.

---

## Materiali storici

I documenti e i codici relativi a versioni precedenti, pipeline prototipali e decisioni superate sono conservati in:
- [Archivio della documentazione](archivio/README.md)
- [Archivio del codice e dei prototipi](../archivio/README.md)
