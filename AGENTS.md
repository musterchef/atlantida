# Regole di lavoro

## Repository e commit

- Scrivere i titoli dei commit in forma nominale, per esempio «aggiunta di…», «aggiornamento di…», «correzione di…» o «unificazione di…». Iniziare sempre con la lettera minuscola, evitando forme verbali come «aggiunge», «aggiorna», «corregge» o «unifica». Indicare concretamente l'oggetto della modifica.
- Committare solo ciò che serve al funzionamento, alla manutenzione o all'uso del sistema: codice, configurazioni necessarie e documentazione essenziale.
- Includere test automatici pertinenti quando verificano comportamenti reali. Non aggiungere test superflui o duplicati.
- Tenere fuori dal repository script usa e getta, dump, log, output generati, copie di debug, preset dimostrativi e guide di prove temporanee. Usare una directory temporanea esterna al repository per questi materiali.
- Un esempio o fixture va conservato solo se necessario per un test mantenuto o per l'uso documentato del sistema.
- Prima del commit, esaminare ogni file del diff e selezionare esplicitamente quelli necessari. Non includere automaticamente tutto ciò che è stato creato durante la sessione.
- Quando l'utente chiede una pulizia, verificare anche quali file servono davvero, non soltanto formattazione e messaggi di debug. Preservare il percorso funzionante e aggiornare gli eventuali riferimenti ai file rimossi.
- Non cancellare modifiche altrui o riscrivere commit esistenti senza autorizzazione.
- Mantenere i commit coerenti e circoscritti a una modifica logica. Evitare di raggruppare interventi indipendenti nello stesso commit.
- Non eseguire commit automaticamente se non richiesto esplicitamente.

## Linee guida per la scrittura del codice

- Scrivere codice pulito, ordinato e leggibile, con nomi precisi, flussi espliciti e responsabilità ben definite.
- Scegliere la soluzione più semplice che risolve il problema reale e rispetta l'architettura del progetto. Ogni aggiunta deve avere uno scopo concreto.
- Mantenere il codice modulare, con componenti coesi e interfacce essenziali. Evitare sia funzioni che mescolano responsabilità diverse sia frammentazioni e livelli di indirezione inutili.
- Leggere il codice interessato e comprenderne il comportamento prima di modificarlo. Riutilizzare le soluzioni già presenti quando adatte, mantenendo le convenzioni del progetto.
- Correggere la causa del problema. Evitare workaround, patch sovrapposte, condizioni speciali e fallback che nascondono errori o aggirano un difetto senza risolverlo.
- Non introdurre astrazioni premature, framework interni, configurazioni, dipendenze o estensioni per esigenze ipotetiche.
- Non aggiungere codice per riempire una risposta o mostrare attività. Se non serve una modifica, non farla.
- Gestire errori e casi limite reali nei punti appropriati. Evitare controlli difensivi ridondanti, eccezioni ignorate e recuperi silenziosi che rendono il comportamento ambiguo.
- Limitare le modifiche allo scopo richiesto. Eliminare il codice reso inutile dalla modifica, senza riscrivere parti estranee al problema.
- Usare commenti per spiegare motivazioni e vincoli non evidenti, senza ripetere ciò che il codice esprime già.
- Prima di concludere, rileggere il diff ed eliminare duplicazioni, complessità accidentale e aggiunte non necessarie. Verificare i comportamenti modificati con controlli pertinenti.
- Preservare i comportamenti e i contratti esistenti non coinvolti dalla modifica. Valutare l'impatto sui componenti collegati ed evitare regressioni nelle funzionalità già operative.
- Evitare la duplicazione di logiche, dati e stati condivisi. Definire chiaramente dove risiede ogni responsabilità e mantenere coerenti le informazioni tra i componenti.
- Mantenere espliciti i flussi di dati e le dipendenze tra componenti. Evitare accoppiamenti nascosti, effetti collaterali non evidenti e modifiche implicite dello stato condiviso.
- Considerare le prestazioni quando sono rilevanti per il comportamento reale del sistema. Evitare ottimizzazioni premature e complessità aggiuntiva senza benefici verificabili.

## Organizzazione di file e package

- Prima di creare un file, individuare la responsabilità che svolge e il componente a cui appartiene. Leggere la struttura esistente e l’architettura documentata, quindi collocarlo nel package appropriato.
- Raggruppare i moduli della stessa funzionalità e separare componenti con responsabilità distinte. La struttura delle directory deve rendere riconoscibile questa separazione: non accumulare file nella radice del package e non usare prefissi ripetuti come sostituto di un package dedicato.
- Ogni strumento deve avere una propria sottocartella in `src/desnivel/music/`, denominata con il nome dello strumento e contenente i moduli musicali che gli appartengono. Nella radice di `music/` mantenere soltanto le responsabilità condivise tra le voci. Protocolli e integrazioni di destinazione appartengono agli adattatori; i comandi alle CLI.
- Riutilizzare i package adatti. Creare un nuovo package o sottopackage quando rappresenta una responsabilità concreta e coesa, senza predisporre directory per funzionalità ipotetiche. Evitare contenitori generici come `misc`, `common` o `utils` che raccolgano funzioni prive di una responsabilità comune, e gerarchie che aggiungano soltanto livelli di navigazione.
- Scegliere nomi che descrivano il contenuto nel contesto del package, evitando di ripetere inutilmente il nome del componente. Mantenere la logica nel componente responsabile: il codice musicale indipendente dalla destinazione non deve finire nelle CLI o nei moduli di trasporto per comodità.
- Organizzare i test secondo i componenti verificati, seguendo la struttura di `tests/`. Conservare builder, sorgenti Max e launcher rispettivamente in `tools/`, `m4l/` e `comandi/`.
- Quando si creano, rinominano o spostano moduli, aggiornare gli import e gli eventuali entry point, launcher, test e riferimenti documentali interessati. Verificare gli import, i comandi coinvolti e i comportamenti esistenti con controlli pertinenti.
- Prima di concludere, verificare anche la collocazione dei file aggiunti o modificati. Correggere il disordine introdotto dall’intervento senza estendere il riordino a componenti estranei alla richiesta.

## Linee guida per la documentazione

- Nella documentazione di presentazione, descrivere identità, obiettivi e capacità del progetto senza identificarlo con singoli componenti, strumenti, integrazioni o scelte attuali di implementazione. Riservare i dettagli specifici agli approfondimenti pertinenti.

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
- Tenere le istruzioni correnti separate dai percorsi superati: questi vanno in archivio/, con collegamenti aggiornati.
- Documentare solo comandi esistenti. Segnalare brevemente ciò che manca in sezioni apposite, senza inventare interfacce future.
- Aggiornare i documenti interessati quando cambia una decisione, evitando di duplicare la stessa spiegazione in ogni file.
- Mantenere coerenti documentazione e implementazione. Verificare che nomi, parametri, percorsi, esempi e comportamenti descritti corrispondano al sistema effettivo.

## Modalità di lavoro

- Comprendere la richiesta e individuare i componenti interessati prima di intervenire.
- Interpretare l’intento della richiesta e distinguere i principi generali dagli esempi usati per chiarirli. Quando si formula una regola, esprimere il criterio applicabile anche ad altri casi, senza trasformare ogni dettaglio citato dall’utente in un obbligo o ripeterne meccanicamente le parole. Usare gli esempi solo quando aggiungono chiarezza e lasciare le conseguenze ovvie all’applicazione del principio.
- Procedere autonomamente quando la soluzione è chiara e coerente con l'architettura esistente. Chiedere chiarimenti soltanto quando un'ambiguità influisce concretamente sul risultato.
- Non interpretare una richiesta circoscritta come autorizzazione a riprogettare o ampliare il sistema.
- Privilegiare modifiche concrete e verificabili rispetto a lunghe analisi, proposte speculative o implementazioni non richieste.
- Non dichiarare completate verifiche, test o modifiche che non sono stati effettivamente eseguiti.
- Comunicare sinteticamente il risultato del lavoro, indicando cosa è stato modificato, cosa è stato verificato ed eventuali problemi rimasti.
- Evitare riepiloghi prolissi, spiegazioni delle scelte ovvie e descrizioni passo per passo di operazioni ordinarie. Approfondire soltanto quando necessario o richiesto.

## Sviluppo incrementale e scalabilità
- Partire dall'implementazione più semplice che permetta di verificare il comportamento reale richiesto, mantenendo una struttura coerente con l'architettura prevista.
- Progettare ogni implementazione iniziale come nucleo funzionante del sistema definitivo, non come prototipo temporaneo destinato a essere sostituito.
- Procedere per incrementi successivi, estendendo e perfezionando il codice esistente senza ricominciare da zero a ogni nuova esigenza.
- Distinguere la semplicità iniziale dalla semplificazione architetturale: ridurre le funzionalità implementate, non compromettere la possibilità di evoluzione.
- Introdurre nuove responsabilità, componenti e livelli di complessità soltanto quando diventano necessari per raggiungere gli obiettivi concreti del progetto.
- Utilizzare prove e verifiche per validare funzionalità destinate a rimanere nel sistema. Evitare implementazioni dimostrative isolate che non contribuiscono allo sviluppo effettivo.
- Mantenere stabili le interfacce e i contratti fondamentali quando possibile, permettendo alle funzionalità di evolvere senza richiedere continue riscritture.
- Quando si propone una soluzione, considerare sia il comportamento immediato sia la sua evoluzione prevista, senza implementare anticipatamente funzionalità future.