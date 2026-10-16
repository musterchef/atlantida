# Stato dell'integrazione

Collegamenti e porte delle integrazioni presenti. Risultati delle prove: [Stato del progetto](../SESSIONE.md).

## Percorsi disponibili

| Percorso | Funzione |
|---|---|
| GPX → metriche | Sei misure con timestamp, disponibili in Python e via OSC. |
| Metriche → pattern | Regola a soglia e interpretazioni pesate di movimento e sforzo. |
| Frase → generatore | Produzione di una frase di accompagnamento nel generatore del basso. |
| Pattern → adattatore | Controllo di note, gate e Shape nel collegamento Snake. |
| Frase o piano → player | Riproduzione MIDI in Max for Live. |
| Stato del sequencer → frase | Previsione usata nel collegamento live presente. |

## Porte e formati

| Porta predefinita | Contenuto | Riferimento |
|---|---|---|
| 9000 | Metriche del viaggio. | [Contratto dati](../CONTRATTO-DATI-VIAGGIO.md) |
| 9001 | Comandi dei parametri del sequencer. | [Integrazione Snake](../INTEGRAZIONE-SNAKE.md) |
| 9002 | Frasi per il player ciclico. | [Player M4L](../PLAYER-M4L.md#protocollo) |
| 9003 | Snapshot del sequencer e controlli del basso, su indirizzi distinti. | [Export](../EXPORT-SNAKE.md), [controlli](../CONTROLLI-BASSO.md) |
| 9004 | Piani per il player sul trasporto. | [Player M4L](../PLAYER-M4L.md#basso-collegato-a-snake) |

Acquisizione degli snapshot e basso live sono ricevitori alternativi sulla porta 9003: non avviarli insieme sulla stessa porta.

## Limiti

- Il producer pubblica metriche; il contratto dei fatti geografici resta da definire.
- Le quote ricostruite dal loader non hanno un flag di qualità distinto.
- Il ricevitore dimostrativo delle metriche conserva l'ultimo valore senza timeout.
- I cambi dei parametri del sequencer non sono atomici né quantizzati a battuta.
- Il mittente dei controlli del basso non è implementato.
- Direzione musicale e coordinamento condivisi restano da implementare secondo l'[architettura](../TODO-ARCHITECTURE.md).
