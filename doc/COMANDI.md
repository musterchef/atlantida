# Comandi e configurazione

## Ambiente di sviluppo

Dalla radice del progetto:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

---

## Streaming e lettura delle metriche

Visualizzazione delle metriche a terminale (senza invio di rete):

```sh
desnivel-stream-metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --dry-run
```

Trasmissione continua via OSC a velocità 30×:

```sh
desnivel-stream-metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --speed 30
```

Opzioni utili:
- `--loop`: ripete il viaggio ciclicamente.
- `--osc-host` e `--osc-port`: configurano host e porta di trasmissione (predefinito: `127.0.0.1:9000`).

---

## Porte di rete predefinite

| Porta UDP | Flusso dati | Riferimento |
|---|---|---|
| **9000** | Pubblicazione delle metriche fisiche del viaggio. | [Dati del viaggio](DATI-VIAGGIO.md) |
| **9001** | Controllo dei parametri di Snake in Live. | [Sequencer Snake](SNAKE.md) |
| **9002** | Invio di frasi predefinite per il player ciclico. | [Player M4L](BASSO.md) |
| **9003** | Telemetria dello stato di Snake (`/snake/state`) e controlli live del basso (`/bass/control`). | [Snake](SNAKE.md), [Basso](BASSO.md) |
| **9004** | Piani di esecuzione per il basso sincronizzato al trasporto di Live. | [Basso in Live](BASSO.md) |

---

## Operazioni e launcher principali

I launcher a doppio clic per macOS si trovano in `comandi/` e usano automaticamente l'ambiente virtuale `.venv`:

- **`08 - Scegli assetto basso.command`**: avvia il generatore del basso con scelta interattiva tra gli assetti `sobrio`, `dialogo` e `ritmico`.
- **`05 - Acquisisci Export Snake.command`**: registra gli stati esportati da Snake in un file JSONL temporaneo.
- **`04 - Snake - sequenza di riferimento.command`**: imposta una sequenza neutra di partenza su Snake.

Per l'ascolto completo delle tappe e dei percorsi modali, consultare la [Guida alle tappe e preset](TAPPE-E-PRESET.md).

---

## Suite di test

Verifica completa dei componenti Python e degli script JavaScript di Max for Live:

```sh
# Test suite Python
pytest -q

# Test unitari JavaScript Max for Live
node tests/js/phrase_player.cjs
node tests/js/snake_params.cjs
node tests/js/snake_state.cjs
node tests/js/transport_player.cjs
```
