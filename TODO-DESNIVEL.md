# TODO Desnivel

Questo elenco raccoglie interventi da valutare e integrare. Le voci aperte non sono decisioni già implementate.

## Basso

Il generatore parametrico usa un percorso unico per ritmo, altezze e articolazione; i preset forniscono valori iniziali. Conservare questa struttura, il producer agnostico, il motore Python indipendente dalla destinazione e Snake come adattatore. Le regole musicali e i pesi attuali sono ipotesi da verificare all'ascolto: i test ne verificano il comportamento tecnico.

### Revisioni da valutare

- [ ] **Limitare le responsabilità di `rhythm_follow`.** Oggi influenza attacchi, durate e accenti. Valutare se limitarlo alla scelta degli attacchi, rendendo il risultato più leggibile. Introdurre un controllo separato sulle durate soltanto se emerge un'esigenza musicale concreta. Criterio: modificare il legame ritmico deve avere effetti riconoscibili, senza cambiare involontariamente sostegno e dinamica.
- [ ] **Distinguere mobilità e alternanza di registro.** Oggi `mobility` favorisce note basse sui beat e acute sui levare. Valutare una mobilità riferita principalmente alla propensione ai salti; trattare l'alternanza basso/acuto come una scelta distinta, se serve mantenerla. Criterio: aumentare la mobilità non deve imporre un gesto specifico quando si cerca soltanto maggiore movimento.
- [ ] **Rivedere la compatibilità armonica.** La lista degli intervalli premiati e penalizzati è una convenzione semplice, non un riconoscimento di accordi. Verificare il verso degli intervalli, il trattamento delle dissonanze e il rapporto con le note simultanee. Criterio: motivare le preferenze con esempi musicali concreti e confronti all'ascolto, senza dedurre una tonica certa dal solo materiale melodico.
- [ ] **Calibrare i pesi e la risposta dei controlli.** Bonus d'ingresso e d'appoggio, penalità dei salti, ripetizioni e legame melodico possono dominarsi a vicenda. Valutare variazioni progressive dei parametri sullo stesso materiale e individuare soglie o controlli poco efficaci. Criterio: ottenere cambiamenti comprensibili e graduali per quanto consentito da note e attacchi discreti; documentare i limiti reali.

### Metodo

Partire dall'ascolto dell'assetto corrente sul replay Firenze. Scegliere un problema concreto, modificare un parametro o una regola per volta e confrontare lo stesso tratto. Aggiungere parametri o astrazioni solo quando i controlli presenti non risolvono il problema. Il giudizio musicale spetta all'utente.

Non ripetere la verifica MIDI dell'esecuzione dei piani già conclusa, salvo modifiche che interessino quel percorso. Per ogni revisione mantenere test dei comportamenti realmente cambiati e aggiornare la documentazione interessata.

### Riferimenti

- [Guida all'ascolto](doc/PLAYER-M4L.md#regolare-il-basso-allascolto): comandi, valori e confronti.
- [Scelte del basso](doc/SCELTE-BASSO.md): regole presenti e punti del codice da modificare.
- [Sessione](doc/SESSIONE.md#basso-parametrico): implementazione e verifiche eseguite.
