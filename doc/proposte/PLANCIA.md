# Proposta: plancia globale

La plancia è il punto di osservazione globale richiesto per la composizione. L'interfaccia grafica non è implementata.

La sessione Python espone già uno snapshot con `EnsembleRuntime.snapshot()` e lo salva in JSON. La plancia dovrà leggere lo stato del processo esistente, senza avviare copie di Director, Coordinator o generatori.

## Informazioni da mostrare

- Posizione nel viaggio e sezione corrente.
- Stato Play/Stop ricevuto da Live e collegamento della sorgente del trasporto.
- Parti configurate, attive, collegate o mancanti.
- Ruolo della sezione e ruolo manuale per ciascuna parte.
- Controlli effettivi e frasi pianificate, distinguendoli dall'esecuzione sonora.
- Errori e motivo dell'attesa della sessione.

La prima versione della sessione mantiene il viaggio indipendente dalla numerazione delle battute di Live. Stop sospende replay e suono; Play riprende dal punto raggiunto.

## Decisioni aperte

- Tecnologia dell'interfaccia e modalità di accesso allo stato del processo.
- Controlli globali da offrire nella plancia oltre all'osservazione.
- Gestione della selezione di tappa e configurazione prima dell'avvio.
