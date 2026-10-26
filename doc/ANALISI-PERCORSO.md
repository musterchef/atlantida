# Analisi delle zone del percorso

`desnivel.trip.analysis.analyze_track` analizza quota e distanza cumulata di un
`Track`. Il comando `desnivel.cli.analyze_trip` carica il GPX tramite il loader
esistente, stampa le zone e può esportare l'analisi in JSON e come report HTML. Non genera musica
e non modifica le assegnazioni della sessione multivoce.

```bash
cd /Users/marco/ogni-tanto-programmo/desnivel
.venv/bin/python -m desnivel.cli.analyze_trip \
  --gpx gpx/tappa05_Firenze_San_Gimignano.gpx \
  --config presets/analisi-percorso.json \
  --grouping presets/macrosezioni-percorso.json \
  --output output/analisi-percorso.json \
  --html output/analisi-percorso.html
```

## Metodo e configurazione

La configurazione JSON richiede quattro campi:

| Campo | Significato |
|---|---|
| `sample_distance_m` | Distanza fra i confini degli intervalli osservati. L'ultimo intervallo termina alla fine del percorso. |
| `slope_window_m` | Ampiezza della finestra centrata sul punto medio di ciascun intervallo. La pendenza è il dislivello fra gli estremi diviso per la distanza. La finestra viene accorciata ai bordi del percorso. |
| `min_zone_distance_m` | Estensione consecutiva nella stessa nuova fascia necessaria per confermare un cambio. |
| `bands` | Fasce ordinate con nome e limite inferiore `from_slope_ratio`, incluso. La prima parte da `null`, senza limite inferiore; l'ultima non ha limite superiore. |

I valori numerici devono essere positivi e finiti; le soglie delle fasce possono
essere negative e devono essere strettamente crescenti. Le pendenze sono frazioni:
`0.06` significa 6%. I nomi delle fasce sono dati di configurazione.

Il file `presets/analisi-percorso.json` contiene una prima taratura da revisionare:
intervalli di 100 m, osservazione di 300 m, persistenza di 300 m; fasce delimitate
da −6%, −1,5%, +1,5% e +6%. Questi valori non sono soglie ciclistiche validate.

La prima osservazione inizializza la zona. Ogni cambio successivo richiede la
persistenza configurata; una fascia diversa interrompe la sequenza candidata.
Quando il cambio è confermato, il suo confine viene posto all'inizio della
sequenza candidata. Si tratta quindi di un'analisi offline, che usa anche dati
successivi al punto classificato. La prima zona può essere più corta del minimo.

I cambi brevi, compresa una coda finale non confermata, rimangono nella zona
precedente. Per questo il nome della zona può differire dalla classificazione
della sua pendenza media. Il report espone entrambe le misure e la concordanza:
la frazione di distanza le cui osservazioni appartengono alla fascia assegnata.
La concordanza descrive l'effetto del raggruppamento, non l'affidabilità del GPS.

## Risultato e dati richiesti

Il JSON conserva configurazione, sorgente, distanza totale e tre elenchi:

- `zones`: tipo, confini in metri, avanzamento sulla distanza totale, dislivello
  netto, pendenza media e concordanza. Le zone coprono l'intero percorso.
- `windows`: confini dell'intervallo, quota al centro, pendenza osservata,
  fascia locale prima della conferma e indice della zona assegnata.
- `profile`: quota ai confini e ai centri degli intervalli, interpolata sul
  `Track`, con distanza in metri dall'inizio del percorso.

Quota e distanza devono essere complete, finite e allineate ai campioni del
`Track`; la distanza deve essere non decrescente con estensione positiva.
L'assenza di quota produce un errore. Il loader interpola le lacune parziali
di quota e applica la mediana già prevista nella configurazione GPX.
A distanza identica viene conservata l'ultima quota; le soste non hanno
estensione in questa analisi per distanza.

Finestre troppo piccole per distinguere numericamente i loro estremi ed
estensioni, pendenze o dislivelli non rappresentabili producono un errore.
Il confine finale compare una sola volta anche con passi decimali.

L'analisi descrive il profilo altimetrico: non identifica fatica fisiologica,
scollinamenti come eventi separati o scelte musicali.

## Macrosezioni del percorso

Il modulo `desnivel.trip.sections.group_zones` riceve l'analisi e una
configurazione distinta di famiglie. Raggruppa soltanto zone consecutive
della stessa famiglia, con confini adiacenti; mantiene i dati originali
dell'analisi. Il comando attiva questo passaggio con `--grouping`.

`presets/macrosezioni-percorso.json` configura:

```json
{
  "families": {
    "ascent": ["climb", "steep_climb"],
    "descent": ["descent", "steep_descent"],
    "level": ["level"]
  }
}
```

Ogni fascia definita nella configurazione di analisi deve appartenere
esattamente a una famiglia. Assegnazioni mancanti, duplicate o riferite a
fasce sconosciute producono un errore. Nomi e appartenenze delle famiglie
sono configurabili; il raggruppamento non conosce significati musicali.

Un tratto `level` interrompe una `ascent` con questa configurazione, anche
se breve. Non sono previste tolleranze per assorbire interruzioni. Una
famiglia può comparire più volte lungo il percorso in macrosezioni distinte.

Il risultato viene aggiunto dal comando nel campo `grouping`, che contiene
la configurazione utilizzata e l'elenco `sections`. Ogni macrosezione espone
indice, famiglia (`kind`), confini in metri, avanzamento sulla distanza
totale, dislivello netto, pendenza media e `zone_indices`: gli indici delle
zone originali incluse. Gli indici nel JSON partono da zero; report e tabella
nel terminale li mostrano a partire da uno.

Senza `--grouping` vengono prodotte soltanto le zone dell'analisi.

## Report visuale

Aprire `output/analisi-percorso.html` nel browser. Il file incorpora dati, stile
e JavaScript; funziona localmente senza server o risorse esterne. Le cartelle
di output vengono create dal comando se assenti. `--html` e `--output` sono
indipendenti e, quando usati insieme, devono indicare file distinti.

Il modulo `desnivel.reports.trip.render_trip_report` riceve il risultato
di `analyze_track` e restituisce l'HTML. Le risorse di presentazione sono
separate in `trip.html`, `trip.css` e `trip.js`, incluse nel pacchetto Python.
Il renderer non legge il GPX e non ricalcola zone o soglie.

I due grafici condividono la distanza: quota con sfondi delle zone confermate
e pendenza osservata con soglie tratteggiate prese dalla configurazione.
La fascia sotto il profilo mostra la classificazione locale; un tratteggio
segnala dove differisce dalla zona assegnata. La legenda usa i nomi delle
fasce configurate, anche quando vengono rinominate o cambiano di numero.

Il puntatore mostra i dettagli dell'intervallo osservato. I campi «Da km» e
«A km» selezionano una porzione; i pulsanti delle zone nella tabella la
inquadrano con un piccolo margine. «Tutto il percorso» ripristina la vista
completa. Lo zoom modifica soltanto la vista; per modificare l'analisi occorre
cambiare il JSON dei criteri e rieseguire il comando.

Quando il risultato contiene `grouping`, il report aggiunge una fascia delle
macrosezioni sopra il profilo, una legenda delle famiglie e una tabella
dedicata. Selezionare una macrosezione ingrandisce il tratto ed evidenzia le
sue zone originali nella tabella di dettaglio. Il puntatore mostra insieme
macrosezione, zona e fascia osservata. La configurazione delle famiglie è
consultabile accanto ai criteri di analisi. Il report visualizza il
raggruppamento ricevuto senza ricalcolarlo nel browser.

L'opzione `--timeline-session presets/organico.json` aggiunge al report
l'[anteprima della timeline musicale in beat](TIMELINE.md), utilizzando le
stesse macrosezioni. Richiede `--grouping` e non modifica zone o profilo.

## Pianure tra salite o discese: confronto locale

Con `--grouping`, l'opzione `--pause-context ascent level` aggiunge una
misura delle macrosezioni `level` immediatamente precedute e seguite da
`ascent`. Ripetendo l'opzione con `--pause-context descent level` si
misurano anche le pianure tra due discese nello stesso report. Le pianure
tra una salita e una discesa non corrispondono a nessuna delle due terne.
I due nomi sono argomenti espliciti e devono appartenere alle
famiglie configurate; il calcolo è disponibile anche per altre coppie.

`trip.sections.measure_section_bridges(sections, flank_kind=..., middle_kind=...)`
legge le macrosezioni originali e restituisce, per ogni terna:

- gli indici delle tre macrosezioni;
- le loro lunghezze in metri;
- il riferimento locale `2 × prima × dopo / (prima + dopo)`;
- il rapporto `lunghezza intermedia / riferimento locale`.

I risultati sono esportati nella lista `section_context`, un elemento per
ogni coppia richiesta, nel JSON e incorporati
nell'HTML. Il report mostra una tabella con la famiglia dei tratti adiacenti: selezionare una riga inquadra i tre
tratti nel profilo. Anche i rapporti superiori al 100% sono mostrati. Se non
ci sono terne corrispondenti, il report indica zero sezioni.

Non viene applicata una soglia né effettuato un nuovo raggruppamento.
Zone, macrosezioni, timeline e ascolto mantengono il comportamento corrente.
Il confronto serve a valutare una futura soglia per le pause interne.

```sh
.venv/bin/python -m desnivel.cli.analyze_trip \
  --gpx gpx/tappa05_Firenze_San_Gimignano.gpx \
  --config presets/analisi-percorso.json \
  --grouping presets/macrosezioni-percorso.json \
  --pause-context ascent level \
  --pause-context descent level \
  --timeline-session presets/organico.json \
  --output output/analisi-percorso.json \
  --html output/analisi-percorso.html
```

## Report di tutte le tappe

Il comando `cli.analyze_trips` analizza i file `.gpx` presenti direttamente
nella cartella indicata, ordinati per nome. Riutilizza la stessa funzione
`cli.analyze_trip.analyze_trip` del comando singolo, con identiche
configurazioni e misure.

```sh
.venv/bin/python -m desnivel.cli.analyze_trips \
  --gpx-dir gpx \
  --config presets/analisi-percorso.json \
  --grouping presets/macrosezioni-percorso.json \
  --pause-context ascent level \
  --pause-context descent level \
  --timeline-session presets/organico.json \
  --output-dir output/tappe
```

La cartella di uscita contiene:

- `index.html`: selettore della tappa, report incorporato e collegamento per
  aprire il report completo in un'altra scheda;
- `report-<nome GPX>.html`: report autonomo di ciascuna tappa;
- `report-<nome GPX>.json`: dati della stessa analisi.

Aprire `output/tappe/index.html` nel browser. La selezione cambia il report
visualizzato; non avvia una sessione musicale. Le pagine si leggono da file
locale senza server o connessione a Internet. Per aggiornare le analisi dopo
una modifica ai parametri, rilanciare il comando e ricaricare la pagina.
La generazione sovrascrive i file corrispondenti alle tappe presenti; non
elimina eventuali report di tappe rimosse dalla cartella GPX.
