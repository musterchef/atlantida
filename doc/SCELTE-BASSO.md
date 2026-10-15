# Scelte del basso

Questo documento spiega le regole presenti in [generator.py](../src/desnivel/music/bass/generator.py) e dove modificarle. Per comandi, intervalli dei parametri e confronti all'ascolto usare [Regolare il basso](PLAYER-M4L.md#regolare-il-basso-allascolto).

## Percorso musicale

Snake fornisce stato e fase. L'adattatore Python prevede una frase melodica; il generatore riceve soltanto quella `Phrase`, i controlli, la nota precedente e l'indice musicale. Produce una nuova `Phrase`, eseguita dal player. Il producer resta agnostico, il motore indipendente dalla destinazione e Snake un adattatore.

La composizione segue tre passaggi: scegliere gli istanti, scegliere le altezze, assegnare durate e velocity. I preset cambiano i valori iniziali dello stesso percorso. Non selezionano algoritmi separati.

## Perché questi assetti

I valori sono ipotesi compositive da verificare all'ascolto. La tabella completa è in [Generare il basso](PLAYER-M4L.md#generare-il-basso).

| Assetto | Scelta | Risultato cercato |
|---|---|---|
| `responsive` | Densità moderata, preferenza per i beat, legami parziali con la melodia, mobilità bassa e articolazione lunga. | Un accompagnamento con appoggi riconoscibili e movimento contenuto, che possa anche rispondere negli spazi. |
| `follow` | Entrambi i legami a 1, variazione e mobilità a 0. Densità alta, limitata dagli attacchi sorgenti e dalla distanza minima di un beat. | Selezionare attacchi della melodia, conservarne le classi di altezza e il respiro, evitando salti superflui fra ottave. Non raddoppia tutte le note se sono troppo vicine. |
| `slap` | Densità maggiore, preferenza per i levare, poco legame ritmico, mobilità alta e articolazione corta. | Alternare appoggi e risposte più acute e separate. Il nome descrive il gesto cercato; il timbro dipende dallo strumento. |
| Primo assetto d'ascolto | Preset `slap`, registro 28–59, densità ridotta a 1,2 e mobilità ridotta a 0,6. | Dare spazio alla melodia, lasciando abbastanza registro per risposte acute senza spingere subito al massimo i salti. |

Per cambiare un assetto personale basta modificare le opzioni del comando. Per cambiare i valori iniziali del progetto intervenire nel dizionario `PRESETS`. `BassSettings.__post_init__` applica quei valori soltanto ai campi non specificati: un'opzione esplicita prevale sempre. I valori comuni, come registro e griglia, sono nella dataclass `BassSettings`.

In Python, `dataclasses.replace(settings, density=...)` conserva gli altri valori già risolti. Cambiare soltanto `strategy` con `replace` non carica un altro preset: per quello costruire nuove `BassSettings(strategy='slap')` con gli override desiderati.

## Scegliere gli attacchi

La funzione `_rhythm` considera gli attacchi melodici e, se `rhythm_follow < 1`, aggiunge posizioni sulla griglia dal primo attacco fino alla fine della frase. Il basso non anticipa il primo ingresso melodico. Può proseguire negli spazi successivi; una frase completamente vuota produce silenzio.

Il numero cercato è:

```text
round(min(numero di posizioni candidate, density × tempo dal primo attacco alla fine))
```

È un obiettivo: la distanza minima può impedire di raggiungerlo. `round` usa l'arrotondamento Python al pari nei casi esattamente a metà. Non esiste un minimo obbligatorio di una nota: anche una densità positiva molto bassa può produrre silenzio.

Ogni posizione riceve un punteggio:

```text
preferenza metrica + 2 × relazione con la melodia + casualità × variation
```

- La preferenza metrica vale `1 − syncopation` sui beat interi, `syncopation` altrove.
- La relazione vale `rhythm_follow` sugli attacchi melodici, `1 − rhythm_follow` negli spazi.
- La casualità è un valore fra 0 e 1, generato in modo ripetibile.
- Il primo attacco riceve un bonus di 4 per rendere riconoscibile l'ingresso.

Si scelgono prima le posizioni con punteggio maggiore, scartando quelle troppo vicine a una già selezionata. A parità di punteggio prevale la posizione precedente. Infine si riordinano gli attacchi nel tempo. Questa selezione semplice non garantisce il massimo numero possibile di note.

Il coefficiente 2 dà al dialogo con la melodia più peso della sola preferenza metrica. Per rendere le sincopi più decisive a parità di controlli, ridurre quel coefficiente in `_rhythm`; per indebolire l'appoggio iniziale, ridurre il bonus di 4. Prima provare i parametri esistenti, poi cambiare una regola se il risultato resta insufficiente.

Oggi ogni beat intero è trattato allo stesso modo e ogni posizione non intera come levare. Non c'è una gerarchia esplicita fra primo e terzo beat o fra ottavi e sedicesimi. Per introdurla, cambiare il calcolo di `metric` nella stessa funzione.

## Scegliere le altezze

### Materiale e appoggio

`_salience` somma, per ogni classe di altezza:

```text
durata × velocity × accento
```

L'accento è 1,5 sugli attacchi a beat interi, 1 altrove. La classe col peso maggiore diventa l'appoggio; in caso di parità prevale la classe numericamente più bassa. È una rilevanza osservata, non una tonica armonica certa.

`_pitches` considera soltanto le altezze nel registro configurato appartenenti alle classi presenti nella frase. Il registro deve contenere almeno dodici altezze consecutive per rappresentare tutte le classi possibili. Non vengono aggiunte note di passaggio estranee al materiale osservato.

### Legame melodico e compatibilità

Per ogni attacco si cercano la nota melodica più vicina e le note ancora attive. In caso di uguale distanza, prevalgono velocity maggiore e poi altezza minore. La nota vicina può trovarsi anche dopo l'attacco: la frase è prevista, non ricevuta nota per nota.

Il punteggio indipendente combina rilevanza normalizzata, compatibilità con le note attive e bonus d'appoggio. Il punteggio locale vale +4 se la classe coincide con la nota vicina, −4 altrimenti. `melody_follow` miscela i due:

```text
(1 − melody_follow) × punteggio indipendente + melody_follow × punteggio locale
```

La compatibilità attuale assegna +1 agli intervalli modulo 12 in `(0, 3, 4, 5, 7, 8, 9)`, −2 agli altri, e fa la media sulle note attive. Sono intervalli calcolati come `(nota melodica − basso) % 12`: il verso conta. Questa è una preferenza compositiva semplice, non un riconoscimento di accordi. Per cambiare il trattamento delle dissonanze intervenire su quella lista e sui due pesi in `_pitches`.

Il bonus d'appoggio è 2,5 sulla prima nota; nell'ultima nota delle frasi di chiusura è `2,5 × variation`. `variation_period` determina ogni quante frasi avviene questa preferenza di chiusura. Con variazione zero la chiusura periodica non modifica il risultato.

### Continuità e registro

Al punteggio vengono sottratti:

- `distanza dalla nota precedente × 0,1 × (1 − mobility)`;
- `distanza dal registro desiderato × 0,15 × mobility`;
- una penalità di ripetizione di `0,5 × (1 − melody_follow)` se la nota è identica alla precedente.

Il registro desiderato è il centro dei limiti MIDI meno `6 × mobility` sui beat, più `6 × mobility` sui levare. Questo contrasto favorisce risposte acute, senza imporre un salto d'ottava. Una perturbazione fino a `variation` diversifica i punteggi. A parità prevale l'altezza più bassa.

Il valore 6 definisce quanto separare le zone basse e acute. I coefficienti 0,1 e 0,15 bilanciano continuità e apertura del registro. Per cambiare il comportamento generale della mobilità intervenire qui; per regolare un singolo assetto usare prima `--mobility` e i limiti MIDI.

In assenza di nota precedente il riferimento è il centro del registro. Nel live, quando esiste, si usa l'ultima nota del piano della finestra precedente.

## Durate e dinamica

`_articulate` calcola la durata disponibile fino al prossimo attacco o al bordo della frase, limitandola con `max_hold`. La durata della nota sorgente è limitata alla stessa disponibilità. Poi:

```text
respiro = disponibile × (1 − rhythm_follow) + durata sorgente × rhythm_follow
durata = respiro × articulation
```

Il legame ritmico influenza quindi anche le durate: a 1 il basso riprende il respiro della sorgente, a 0 sfrutta il proprio spazio. Per renderli due controlli indipendenti servirebbe un parametro dedicato; oggi non c'è.

La velocity parte dalla nota melodica vicina. L'accento è 1 sulla prima nota, 0,92 sugli altri beat, 0,75 sui levare; viene miscelato verso 1 aumentando `rhythm_follow`. Il risultato è moltiplicato per `velocity_ratio`, arrotondato e limitato a 1–127. Per cambiare il contrasto dinamico fra appoggi e risposte intervenire su 0,92 e 0,75. L'articolazione modifica le durate, non la velocity.

## Variazioni e cambi graduali

`generate_bass` costruisce un generatore casuale locale con `seed + phrase_index × 104729`. Il moltiplicatore separa le sequenze fra indici; non è un parametro musicale. Stessi dati, controlli, nota precedente e indice producono lo stesso piano. `variation_period` regola la preferenza periodica di chiusura.

`interpolate_settings` miscela linearmente i controlli musicali; i limiti MIDI vengono arrotondati. Seed, griglia e periodo sono presi dalla configurazione destinazione e cambiano in modo discreto. Le note sono eventi discreti: interpolare i controlli non garantisce cambiamenti udibili a ogni piccolo passo.

Nel live, [BassSession](../src/desnivel/adapters/snake_live.py) espone `set_settings(settings, transition_windows=4)`. La transizione avanza con le finestre musicali future, non con la frequenza degli snapshot. Una nuova epoca riparte dall'ultimo valore pianificato. Il ricevitore accetta cambi parziali attraverso il [contratto OSC dei controlli](CONTROLLI-BASSO.md); il componente che li decide e invia resta da sviluppare.

## Dove intervenire

| Esigenza | Punto del codice |
|---|---|
| Cambiare il carattere iniziale di un preset | `PRESETS` in [generator.py](../src/desnivel/music/bass/generator.py). |
| Cambiare priorità di beat, spazi e ingresso | `_rhythm`. |
| Cambiare quali note diventano appoggi | `_salience`. |
| Cambiare compatibilità, salti o ripetizioni | `_pitches`. |
| Cambiare accenti e rapporto fra durate | `_articulate`. |
| Aggiungere un controllo | `BassSettings`, la funzione musicale interessata e [bass_options.py](../src/desnivel/cli/bass_options.py); valutare anche `interpolate_settings`. |
| Cambiare progressione delle transizioni live | `set_settings` e `_settings_at` in [snake_live.py](../src/desnivel/adapters/snake_live.py). |

La regolazione musicale non richiede modifiche a Export o al player M4L. Conservare il contratto `Phrase → Phrase` e aggiungere test del comportamento realmente cambiato. I riferimenti sono [test_bass.py](../tests/music/bass/test_bass.py) per generazione e [test_snake_live.py](../tests/adapters/test_snake_live.py) per transizioni e piani.

## Stato delle prove

I test verificano parametri, limiti, ripetibilità e transizioni. Le verifiche automatiche e MIDI sono descritte nello [stato del progetto](SESSIONE.md). I valori e i pesi di questa versione restano da valutare musicalmente dall'utente. Annotare una modifica come scelta confermata soltanto dopo il confronto all'ascolto.

## Suggerimento automatico dalla tappa

[analysis.recommend_bass](../src/desnivel/music/bass/analysis.py) genera automaticamente un suggerimento dai cambi musicali già composti e dal tempo finale della tappa. L'utente avvia l'analisi su richiesta tramite la CLI [analyze_bass](../src/desnivel/cli/analyze_bass.py), che carica il GPX, riusa il producer e `music.journey.compose`, poi stampa un comando. L'applicazione del suggerimento resta manuale: l'utente decide se eseguire quel comando. L'analisi non viene chiamata dal basso live né dai launcher; gli assetti esistenti restano il percorso principale.

Ogni pattern viene pesato per il tempo durante il quale rimane attivo, fino al cambio successivo o alla fine dei campioni del viaggio. L'attesa prima del primo pattern è esclusa. Questo evita che tanti aggiornamenti brevi contino più di una lunga sezione stabile. Gli intervalli senza nuove decisioni conservano il pattern precedente, come il replay.

Si calcolano media `m` e deviazione standard `s` della frazione di gate aperti. Da un assetto `responsive` si sovrascrivono quattro controlli, arrotondati a tre decimali:

| Controllo | Formula | Scelta compositiva |
|---|---|---|
| Densità | `1 − 0,5 × m` | Da 1 a 0,5 attacchi desiderati per beat: lasciare più spazio quando la melodia ha più gate aperti. |
| Sincopazione | `0,4 − 0,2 × m` | Ridurre la preferenza per i levare quando il materiale melodico è più fitto. |
| Articolazione | `0,85 − 0,25 × m` | Accorciare il sostegno del basso con più attività melodica. |
| Variazione | `0,2 + 0,6 × s` | Da 0,2 a 0,5: maggiore varietà di scelte se l'attività melodica varia nel viaggio. |

Gli altri controlli restano quelli di `responsive`, incluso registro 28–47, mobilità 0,15 e distanza minima di un beat. Le formule esprimono un accompagnamento prudente; non sono una misura della correttezza musicale. Per cambiare la proposta intervenire sulle quattro formule in `recommend_bass`, senza modificare la generazione live. Un registro diverso può essere scelto nel comando stampato.

L'analisi non deduce accordi, BPM o registro dal paesaggio. Non misura la densità MIDI reale di Snake: la frazione di gate aperti non tiene conto dei percorsi e dei clock impostati nel Set. Una tappa senza decisioni musicali utilizzabili produce un errore anziché un suggerimento inventato. Per l'uso vedere [Suggerire il basso dalla tappa](TEST-PRESET-MUSICALI.md#suggerire-il-basso-dalla-tappa).
