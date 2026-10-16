# Architettura musicale

## Sistema corrente

```text
GPX → metriche → generazione musicale → adattatori → strumenti
```

| Parte | Responsabilità | Codice |
|---|---|---|
| Analisi del viaggio | Carica il GPX, ricampiona e calcola le metriche. | `desnivel.trip` |
| Generazione musicale | Produce pattern e frasi secondo regole configurabili. | `desnivel.music` |
| Adattatori | Converte pattern, frasi e stati nei formati delle destinazioni. | `desnivel.adapters` |
| Trasporto | Pubblica i messaggi e salva le acquisizioni. | `desnivel.sinks` |
| Comandi | Collega i componenti per le operazioni disponibili. | `desnivel.cli` |

L'analisi produce misure con tempi e unità. Le scelte musicali appartengono ai generatori; protocolli, nomi e limiti degli strumenti appartengono agli adattatori.

## Modelli musicali

- `Pattern`: note e gate. `PatternChange` associa il pattern al tempo del viaggio.
- `Phrase`: note con attacco relativo in beat, altezza MIDI, durata e velocity. Ogni nota termina entro la frase.
- Piano di esecuzione: aggiunge sessione, posizione assoluta e revisione alla frase.

`music.journey.compose` genera cambi di pattern da movimento, sforzo e sezioni della tappa. I generatori che ricevono una `Phrase` possono lavorare su materiale proveniente da sorgenti diverse.

Il replay dei dati e il clock musicale sono separati: accelerare il viaggio non cambia i BPM dello strumento.

## Architettura definita, da implementare

| Componente | Responsabilità |
|---|---|
| Music Director | Contesto armonico ed espressivo comune; regole di arrangiamento. |
| Music Coordinator | Voci attive, dipendenze, finestre temporali e revisioni dei piani. |

Il Director definisce tonalità, scala, progressione, energia, tensione e relazioni tra le voci. Le preferenze di arrangiamento hanno pesi configurabili, separati dai vincoli tecnici.

Il Coordinator passa ai generatori il contesto e le eventuali frasi da cui dipendono, nell'ordine necessario. La prima configurazione prevede una sorgente melodica attiva; la gestione delle dipendenze deve consentirne anche più di una.

Criteri armonici, contratti dei piani e rapporto tra tempo del viaggio e beat sono ancora da definire: [TODO](../TODO.md).

## Cartelle

I test seguono i componenti in `tests/`. Builder in `tools/`, sorgenti Max in `m4l/`, launcher macOS in `comandi/`. I generatori specifici hanno una propria cartella in `music/`.

[Stato](SESSIONE.md) · [Dati del viaggio](CONTRATTO-DATI-VIAGGIO.md) · [Comandi](COMANDI.md)
