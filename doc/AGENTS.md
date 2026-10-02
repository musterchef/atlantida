# Regole per la documentazione

- Scrivere in italiano chiaro e conciso, con frasi concrete e titoli brevi.
- Descrivere cosa serve fare e perché. Evitare formule da assistente, ripetizioni, cronache della conversazione e precisazioni difensive tra parentesi.
- Tenere le istruzioni correnti separate dai percorsi superati: questi vanno in `archivio/`, con collegamenti aggiornati.
- Documentare solo comandi esistenti. Segnalare brevemente ciò che manca, senza inventare interfacce future.
- Distinguere decisioni, codice presente e prove eseguite. Non presentare l'architettura scelta come già implementata.
- Mantenere coerenti producer agnostico, motore musicale Python indipendente dalla destinazione e adattatori estensibili. Snake è un adattatore, non il centro del sistema.
- Aggiornare i documenti interessati quando cambia una decisione, evitando di duplicare la stessa spiegazione in ogni file.
