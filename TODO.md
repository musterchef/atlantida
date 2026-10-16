# Prossimi passi

## Sistema

- [ ] Definire e implementare le interfacce di Music Director e Music Coordinator secondo l'[architettura](doc/ARCHITETTURA.md).
- [ ] Definire criteri armonici, regole di arrangiamento e trasformazioni tra sezioni.
- [ ] Definire tempi, revisioni e dipendenze dei piani per più voci.
- [ ] Stabilire il rapporto tra tempo del viaggio e beat e il comportamento a Stop, salti, loop e ripartenza.
- [ ] Definire i fatti geografici neutrali e la gestione dei dati mancanti o scaduti.
- [ ] Valutare le regole musicali confrontando lo stesso tratto e modificando un aspetto per volta.

## Generatore di accompagnamento presente

- [ ] Valutare se limitare `rhythm_follow` agli attacchi; oggi influenza anche durate e accenti.
- [ ] Distinguere la propensione ai salti dall'alternanza basso/acuto introdotta da `mobility`.
- [ ] Verificare intervalli, dissonanze e pesi delle preferenze armoniche.
- [ ] Calibrare bonus d'appoggio, salti, ripetizioni e risposta dei controlli.

[Stato](doc/STATO.md) · [Regole del generatore](doc/BASSO.md)
