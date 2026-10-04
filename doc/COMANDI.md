# Comandi

## Preparare il terminale

Dalla cartella del progetto:

```sh
source .venv/bin/activate
```

## Leggere un viaggio

Mostrare un campione delle metriche senza inviarle:

```sh
desnivel-stream-metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --dry-run
```

Inviare le metriche via OSC:

```sh
desnivel-stream-metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --speed 30
```

| Opzione | Effetto |
|---|---|
| `--speed 30` | Riproduce il viaggio a velocità 30×. |
| `--loop` | Ripete il viaggio fino a Ctrl+C. |
| `--osc-host` | Destinatario; predefinito `127.0.0.1`. |
| `--osc-port` | Porta; predefinita `9000`. |

I messaggi contengono tempo e misure del viaggio, indipendenti dallo strumento musicale. Il formato è descritto nel [contratto dati](CONTRATTO-DATI-VIAGGIO.md).

## Provare Snake

La [guida Snake](INTEGRAZIONE-SNAKE.md) descrive la ricezione in Max e il controllo manuale di un parametro in Live.

Prima prova dal viaggio: [quota e pattern](TEST-VIAGGIO-SNAKE.md).

```sh
python -m desnivel.cli.trip_music --gpx gpx/tappa04_Levanto_La_Spezia.gpx --rules presets/quota.json --speed 50
```

## Eseguire i test

```sh
pytest -q
```

Le istruzioni della pipeline precedente sono nei [comandi archiviati](archivio/COMANDI-PROTOTIPO.md).

## Preset del viaggio

Disponibili movimento, sforzo e misto, con percorso armonico per tappa. [Comandi e configurazione](TEST-PRESET-MUSICALI.md). Test Python e generazione verificati; ascolto in Live da eseguire.

## Inviare una frase al player

```sh
python -m desnivel.cli.send_phrase --phrase presets/phrases/bass_sustained.json --voice bass
```

Richiede il [player M4L](PLAYER-M4L.md); `--dry-run` prova il formato senza rete.
