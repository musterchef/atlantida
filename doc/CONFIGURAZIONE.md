# Configurazione della sessione multivoce

L'[indice dei preset](../presets/README.md) distingue tutti i JSON operativi
per funzione e comando. Questa guida descrive i campi della sessione
`desnivel.cli.ensemble` e dei generatori registrati in `cli/generators.py`.

## Organico e pianificazione

In `presets/organico.json`:

| Campo | Significato e vincoli |
|---|---|
| `selection_mode` | `manual`: le voci vengono assegnate esplicitamente |
| `transport_voice` | Identificativo della voce da cui leggere Play, Stop e beat di Live; deve essere registrata in `voices` |
| `window_beats` | Lunghezza delle frasi pianificate, positiva e finita |
| `lead_beats` | Anticipo minimo della prossima frase rispetto al beat ricevuto, positivo e finito |
| `generators` | Definizioni dei generatori, identificate da un nome locale |
| `voices` | Voci della composizione, identificate dal valore da impostare in **Part** sul dispositivo |
| `sections` | Assetti musicali con confini manuali; sostituiti dalle macrosezioni quando si usa `--direction` |

Un beat è una semiminima. `window_beats: 4` non definisce da solo un metro.
La velocità di replay si sceglie con `--speed`, non con il tempo musicale.

Ogni voce in `voices` contiene:

| Campo | Significato |
|---|---|
| `name` | Nome descrittivo mostrato nella vista globale; opzionale |
| `generator` | Nome di una definizione presente in `generators` |
| `destination` | Identificativo della destinazione; nella sessione ogni voce ne richiede una distinta |
| `dependencies` | Identificativi delle voci le cui frasi vengono fornite al generatore; lista opzionale |

`destination` non è una porta MIDI o UDP. Le porte **Receive** vengono
comunicate dai dispositivi al collegamento: devono essere distinte.
Ogni voce riceve un'istanza indipendente del proprio generatore.

Ogni definizione in `generators` contiene `type`, gli ingressi richiesti dal
tipo, `settings` opzionale e `presets` opzionale. Ogni preset è una mappa di
controlli: i valori omessi vengono completati con quelli iniziali del
generatore, non con l'assetto della macrosezione attraversata.

## Assetti musicali

Una sezione manuale contiene `name`, `from_progress`, `root`, `scale` e
`assignments`. Le progressioni sono frazioni della distanza totale: partono
da zero, sono strettamente crescenti e inferiori a uno. L'ultima sezione
copre la fine del viaggio.

Con `--direction`, `presets/direzione-viaggio.json` definisce:

| Campo | Significato |
|---|---|
| `analysis` | File dei criteri di analisi del percorso |
| `grouping` | File delle famiglie di macrosezioni |
| `families` | Un assetto musicale per ogni famiglia configurata, senza famiglie aggiuntive |

I due percorsi sono relativi al file di direzione. Ogni assetto di famiglia
richiede `root`, `scale` e `assignments`.

| Campo dell'assetto | Significato |
|---|---|
| `root` | Altezza MIDI intera di riferimento, non soltanto una classe di altezza; i generatori verificano il registro delle note prodotte |
| `scale` | Nome della scala in `music.patterns.SCALES` |
| `assignments` | Voci attive, ciascuna con `role` e una mappa opzionale `parameters` |
| `role` | Ruolo fra quelli supportati dal generatore della voce |
| `parameters` | Valori dei controlli di quel generatore applicati nella sezione |

Le scale disponibili sono `chromatic`, `major`, `minor`, `pentatonic_minor`,
`pentatonic_major`, `dorian`, `phrygian`, `lydian`, `mixolydian` e `blues`.
Una voce assente dalle assegnazioni è inattiva. Le sue dipendenze devono
essere presenti nell'organico quando viene attivata. Gli assetti sono
completi per sezione: non ereditano le assegnazioni della precedente.

I criteri di analisi, la persistenza delle fasce e il raggruppamento sono
descritti in [Analisi del percorso](ANALISI-PERCORSO.md).

## Parametri del generatore `motif`

`degrees` è una lista obbligatoria, non vuota, di interi non negativi.
I gradi partono da zero: `0` è la tonica, `1` il grado successivo della
scala; oltre l'ultimo grado si sale nell'ottava successiva.

I seguenti valori possono comparire in `settings`, nei preset e nei
`parameters` delle assegnazioni. I limiti riportati sono quelli del registro
della sessione e dei controlli esposti dal dispositivo.

| Parametro | Predefinito | Intervallo | Effetto |
|---|---:|---|---|
| `octave` | 0 | Intero −5…5 | Trasposizione di ottave rispetto a `root` |
| `step_beats` | 1 | 0,25…8 beat | Passo regolare nel motivo letterale; durata di riferimento nello sviluppo |
| `articulation` | 0,8 | 0,05…1 | Frazione della durata disponibile occupata dalla nota articolata |
| `velocity` | 85 | Intero 1…127 | Intensità MIDI di riferimento, con accenti nello sviluppo; non è un volume in dB |
| `development` | 0 | 0…1 | Zero ripete il motivo; sopra zero attiva e regola lo sviluppo |
| `activity` | 0,75 | 0…1 | Pesi di durate brevi, lunghe e pause nello sviluppo |
| `phrase_windows` | 4 | Intero 2…8 | Finestre che compongono un periodo melodico |
| `seed` | 0 | Intero 0…2147483647 | Riproducibilità delle variazioni |

Ruoli supportati:

- `melody`: motivo letterale o sviluppato, secondo `development`.
- `bass_line`: motivo letterale, senza lo sviluppo melodico.
- `sustained_texture`: una nota per finestra dal primo grado di `degrees`;
  usa registro e velocity. Gli altri controlli ritmici e di sviluppo non
  modificano questa nota sostenuta.

I valori predefiniti del codice possono essere sovrascritti dal file.
Per esempio, `organico.json` imposta `development: 0.7` e `seed: 7`.
L'algoritmo è descritto in [Generazione melodica](MELODIA.md).

## Parametri del generatore `responsive_line`

Richiede una dipendenza musicale e supporta il ruolo `bass_line`.
I sette controlli della sessione sono:

| Parametro | Intervallo | Effetto |
|---|---|---|
| `density` | 0…4 | Numero desiderato di attacchi per beat, limitato dai posti disponibili e da `min_spacing` |
| `syncopation` | 0…1 | Preferenza fra beat interi e posizioni intermedie |
| `rhythm_follow` | 0…1 | Preferenza per attacchi coincidenti con quelli della frase sorgente; influenza anche durate e accenti |
| `melody_follow` | 0…1 | Peso dell'altezza sorgente locale rispetto agli appoggi complessivi della frase |
| `mobility` | 0…1 | Peso del movimento e delle preferenze di registro |
| `variation` | 0…1 | Peso delle variazioni riproducibili di attacchi e altezze |
| `articulation` | 0,05…1 | Frazione di durata disponibile occupata dalle note |

Ulteriori impostazioni accettate in `settings`, ma non esposte nel menu:

| Parametro | Predefinito | Significato e vincoli |
|---|---:|---|
| `lowest`, `highest` | 28, 47 | Limiti MIDI inclusivi 0…127; almeno 12 altezze consecutive |
| `strategy` | `responsive` | Preset iniziale del generatore: `responsive`, `follow` o `slap` |
| `min_spacing` | Dal preset | Distanza minima positiva fra attacchi, in beat |
| `velocity_ratio` | 0,9 | Fattore della velocity sorgente, maggiore di zero e al massimo uno |
| `seed` | 0 | Intero per le variazioni riproducibili |
| `variation_period` | 4 | Intero positivo; periodo in frasi della preferenza di risoluzione |
| `max_hold` | 2 | Durata disponibile massima prima dell'articolazione, in beat, positiva |
| `grid` | 0,5 | Passo positivo della griglia delle posizioni candidate, in beat |

I valori iniziali dei sette controlli dipendono da `strategy` e dagli
eventuali valori espliciti di `settings`. La tabella dei tre preset e
l'algoritmo sono in [Generatore del basso](BASSO.md).

## Parametri del generatore `percussion_pattern`

Supporta `percussion` e non richiede dipendenze. Legge pattern espliciti
configurati, senza dedurre ritmo o altezze dalla scala del contesto.

| Campo della definizione | Contenuto |
|---|---|
| `lanes` | Mappa di nomi locali a note MIDI intere 0…127, distinte |
| `patterns` | Lista non vuota di pattern; l'ordine determina l'indice del controllo `pattern` |
| `patterns[].name` | Nome non vuoto e distinto, mostrato nelle decisioni del generatore |
| `patterns[].length_beats` | Lunghezza positiva e finita del ciclo, in beat |
| `patterns[].hits` | Lista di massimo 128 attacchi, anche vuota per un pattern silenzioso |
| `hits[].beat` | Posizione nel ciclo, da zero incluso alla lunghezza esclusa |
| `hits[].lane` | Nome presente in `lanes` |
| `hits[].velocity` | Intensità MIDI intera 1…127 |

Attacchi duplicati sulla stessa nota e alla stessa posizione sono rifiutati.
I controlli usabili in `settings`, preset e assegnazioni sono:

| Parametro | Predefinito | Intervallo nella sessione | Effetto |
|---|---:|---|---|
| `pattern` | 0 | Intero 0…numero di pattern meno uno | Selezione del pattern nell'ordine della lista |
| `velocity_ratio` | 1 | 0,05…1 | Moltiplica le velocity degli attacchi, arrotondando e limitando il risultato a 1…127 |
| `gate_beats` | 0,1 | 0,01…1 beat | Durata MIDI massima di ogni nota; accorciata prima della nota successiva della stessa altezza e alla fine della frase |

Il ciclo è ancorato al beat zero del trasporto: richieste di lunghezza
diversa ne selezionano la porzione corrispondente. La stessa richiesta e
gli stessi parametri producono le stesse note. Una finestra non può
contenere più di 128 attacchi. Il generatore produce una `Phrase` che usa
lo stesso adattatore e lo stesso dispositivo delle altre voci.

Nel preset fornito, `lanes` associa `kick` a 36, `snare` a 38 e `hat` a 42.
Sono le note da predisporre nel Drum Rack della prova. Per cambiare i pad
si modifica questa mappa; il codice non contiene tali note o nomi.

| Indice | Nome | Attacchi per ciclo di quattro beat |
|---|---|---:|
| 0 | `sparse` | 7 |
| 1 | `steady` | 12 |
| 2 | `driving` | 22 |

I preset omonimi selezionano gli indici corrispondenti. Se si riordina la
lista `patterns`, occorre aggiornare i riferimenti numerici nei preset e
nelle assegnazioni musicali.

## Precedenza e applicazione delle modifiche

Per una voce attiva i parametri vengono risolti in questo ordine:

1. Impostazioni iniziali del generatore.
2. Parametri dell'assegnazione della sezione corrente.
3. Valori manuali mantenuti nella sessione Python.

Le scelte manuali di ruolo hanno precedenza sul ruolo della sezione, ma
non attivano una voce esclusa dall'organico. `Follow section` ripristina il
ruolo assegnato; non cancella i parametri manuali.

Il comando **Preset** applica tutti i controlli iniziali completati con i
valori del preset. Nell'attuale protocollo del dispositivo, modificare un
singolo **Parameter** invia al motore l'intero insieme dei valori correnti:
anche questi valori restano manuali nelle sezioni successive.
`EnsembleSession.clear_parameters(voice)` elimina gli override di parametri;
non esiste ancora un comando equivalente nell'interfaccia del dispositivo.
Riavviare il processo Python ripristina i valori dei file.

Le modifiche manuali non riscrivono i JSON. Le nuove assegnazioni entrano
nelle finestre ancora da pianificare; i piani già inviati rimangono validi.
Le macrosezioni non interpolano gradualmente i parametri e le loro fasce
interne non applicano variazioni musicali aggiuntive.
