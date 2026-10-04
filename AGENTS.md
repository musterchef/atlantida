# Regole di lavoro

## Repository e commit

- Committare solo ciò che serve al funzionamento, alla manutenzione o all'uso del sistema: codice, configurazioni necessarie e documentazione essenziale.
- Includere test automatici pertinenti quando verificano comportamenti reali. Non aggiungere test superflui o duplicati.
- Tenere fuori dalla repository script usa e getta, dump, log, output generati, copie di debug, preset dimostrativi e guide di prove temporanee. Usare una directory temporanea esterna alla repository per questi materiali.
- Un esempio o fixture va conservato solo se necessario per un test mantenuto o per l'uso documentato del sistema.
- Prima del commit, esaminare ogni file del diff e selezionare esplicitamente quelli necessari. Non includere automaticamente tutto ciò che è stato creato durante la sessione.
- Quando l'utente chiede una pulizia, verificare anche quali file servono davvero, non soltanto formattazione e messaggi di debug. Preservare il percorso funzionante e aggiornare gli eventuali riferimenti ai file rimossi.
- Non cancellare modifiche altrui o riscrivere commit esistenti senza autorizzazione.

## Documentazione

- Scrivere in italiano chiaro e conciso, con frasi concrete e titoli brevi.
- Descrivere cosa serve fare e perché. Evitare formule da assistente, ripetizioni, cronache della conversazione e precisazioni difensive tra parentesi.
- Tenere le istruzioni correnti separate dai percorsi superati: questi vanno in `archivio/`, con collegamenti aggiornati.
- Documentare solo comandi esistenti. Segnalare brevemente ciò che manca, senza inventare interfacce future.
- Distinguere decisioni, codice presente e prove eseguite. Non presentare l'architettura scelta come già implementata.
- Mantenere coerenti producer agnostico, motore musicale Python indipendente dalla destinazione e adattatori estensibili. Snake è un adattatore, non il centro del sistema.
- Aggiornare i documenti interessati quando cambia una decisione, evitando di duplicare la stessa spiegazione in ogni file.
