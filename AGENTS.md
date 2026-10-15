# Regole di lavoro

## Repository e commit

- Scrivere i titoli dei commit in forma nominale, per esempio «Aggiunta di…», «Aggiornamento di…», «Correzione di…» o «Unificazione di…». Evitare forme verbali come «Aggiunge», «Aggiorna», «Corregge» o «Unifica» e indicare concretamente l'oggetto della modifica.
- Committare solo ciò che serve al funzionamento, alla manutenzione o all'uso del sistema: codice, configurazioni necessarie e documentazione essenziale.
- Includere test automatici pertinenti quando verificano comportamenti reali. Non aggiungere test superflui o duplicati.
- Tenere fuori dalla repository script usa e getta, dump, log, output generati, copie di debug, preset dimostrativi e guide di prove temporanee. Usare una directory temporanea esterna alla repository per questi materiali.
- Un esempio o fixture va conservato solo se necessario per un test mantenuto o per l'uso documentato del sistema.
- Prima del commit, esaminare ogni file del diff e selezionare esplicitamente quelli necessari. Non includere automaticamente tutto ciò che è stato creato durante la sessione.
- Quando l'utente chiede una pulizia, verificare anche quali file servono davvero, non soltanto formattazione e messaggi di debug. Preservare il percorso funzionante e aggiornare gli eventuali riferimenti ai file rimossi.
- Non cancellare modifiche altrui o riscrivere commit esistenti senza autorizzazione.

## Linee guida per la documentazione

- Scrivere documentazione chiara, concisa, oggettiva e autonoma, nella stessa lingua della richiesta (italiano se si parla in italiano, inglese se si parla in inglese, spagnolo se si parla in spagnolo e così via).
- Descrivere il sistema come esiste attualmente o come esplicitamente definito nell'architettura approvata.
- Scrivere per lettori che non conoscono le conversazioni precedenti o la storia dello sviluppo.
- Concentrarsi su componenti, responsabilità, interfacce e comportamento effettivo.
- Evitare affermazioni difensive, giustificazioni inutili e riferimenti a soluzioni scartate o correzioni precedenti.
- Non introdurre funzionalità speculative, astrazioni inutili o decisioni architetturali non confermate.
- Usare un linguaggio tecnico preciso. Evitare formulazioni generiche generate dall'IA, riempitivi e ripetizioni.
- Preservare i dettagli tecnici utili senza rendere la documentazione inutilmente lunga.
- Quando si revisiona la documentazione, modificare soltanto ciò che richiede effettivamente una correzione.
- Conservare sempre il nome originale del file. Non aggiungere mai suffissi come FINAL, CLEAN, UPDATED o REVISION, salvo richiesta esplicita.
- Se informazioni essenziali mancano o sono ambigue, chiedere chiarimenti prima di fare assunzioni architetturali.
- Scrivere nella lingua scelta in modo chiaro e conciso, con frasi concrete e titoli brevi.
- Tenere le istruzioni correnti separate dai percorsi superati: questi vanno in `archivio/`, con collegamenti aggiornati.
- Documentare solo comandi esistenti. Segnalare brevemente ciò che manca in sezioni apposite, senza inventare interfacce future.
- Aggiornare i documenti interessati quando cambia una decisione, evitando di duplicare la stessa spiegazione in ogni file.
