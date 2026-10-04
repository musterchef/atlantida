# Decisione architetturale — audio e visualizzazione

- Stato: accettata, aggiornata il 2026-10-02.

## Percorso scelto

```text
GPX → producer Python → dati del viaggio agnostici
                            ├→ motore musicale Python ← configurazione
                            │        ↓ decisioni musicali indipendenti dalla destinazione
                            │        ├→ adattatore Snake → OSC → M4L → Snake / Live
                            │        ├→ adattatore altro sequencer → sua destinazione
                            │        └→ ulteriori adattatori → rispettive destinazioni
                            └→ altri consumer indipendenti
```

Sono responsabilità separate, non processi obbligatoriamente separati. Il producer resta indipendente dai consumer e dal sequencer. Snake è il primo esperimento, non una dipendenza del modello del viaggio.

Anche il motore musicale è indipendente da Snake: espone decisioni musicali condivise a una famiglia estensibile di adattatori. Aggiungere o sostituire una destinazione non richiede modificare il producer o introdurre condizioni specifiche del device nelle regole musicali. M4L, Live e OSC appartengono al percorso Snake scelto, non sono requisiti per ogni adattatore. La prima implementazione usa pattern con note e gate e cambi con timestamp e stato; non esiste un framework di adattatori.

## Responsabilità

- **Producer Python:** carica GPX, pulisce e deriva metriche, gestisce il replay. Il contratto neutrale contiene misure e fatti del viaggio con tempi e unità, senza note, scale, parametri Snake o ID Live. Il pilot metrico è già implementato; i fatti neutrali sono ancora da definire.
- **Motore musicale Python:** interpreta metriche e fatti mediante regole configurabili, mantiene lo stato e decide pattern, note, gate e velocity. Può calcolare le note di una sequenza; non deve scandirne ogni esecuzione tramite il timing di arrivo di OSC. Non conosce ID Live o nomi dei parametri Snake.
- **Adattatori di destinazione:** traducono le decisioni musicali condivise nei controlli e protocolli supportati dalla propria destinazione. Nomi, range e limiti del device restano nell'adattatore. Funzioni non supportate vanno dichiarate, senza alterare silenziosamente le decisioni del motore. Snake è la prima implementazione di questo ruolo, non il modello di tutti gli adattatori.
- **M4L:** riceve comandi di controllo e li applica ai parametri associati. L'eventuale applicazione sincronizzata a battuta o step va implementata e verificata in Live. Non contiene le regole geografiche/compositive.
- **Snake / Live:** esegue la sequenza con il clock musicale e produce l'audio tramite gli strumenti.
- **TouchDesigner:** resta un consumer visuale; non è un intermediario necessario per l'audio. La futura telemetria musicale da Live, se necessaria, avrà un contratto separato ancora da definire.

Soglie, intervalli, scale e comportamenti vanno configurati esplicitamente. Nessun ID Live persistito come numero hardcoded. Definire il comportamento a dati mancanti, attraversamenti ripetuti, stop e nuovo replay prima di estendere le regole.

## Interfacce

Il [contratto dati](CONTRATTO-DATI-VIAGGIO.md) descrive le metriche del viaggio. Le decisioni musicali e i comandi degli adattatori sono separati: la [prima prova](TEST-VIAGGIO-SNAKE.md) implementa pattern e traduzione per Snake.

Il tempo del replay stabilisce quanto rapidamente attraversiamo il viaggio. Il clock della destinazione stabilisce quando eseguire le note. Le regole devono dichiarare se operano sul tempo del viaggio o sul tempo musicale.

Lo [stato dell'integrazione](STATO-CONTRATTO-OSC.md) riporta le funzionalità disponibili. I passi per il primo adattatore sono nella [guida Snake](INTEGRAZIONE-SNAKE.md).
