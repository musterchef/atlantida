# Generatore del basso

`music.bass.generator.generate_bass` riceve una `Phrase`, controlli, altezza precedente e indice della frase. Restituisce una `Phrase`. Una sorgente vuota o densità zero produce silenzio.

## Controlli e preset

| Controllo | Effetto |
|---|---|
| `--density` | Attacchi desiderati per beat nella parte di frase successiva al primo attacco melodico. Zero produce silenzio; griglia e distanza minima limitano il numero realizzabile. |
| `--syncopation` | Da 0 a 1: preferenza dagli appoggi sui beat ai levare, conservando un primo appoggio. |
| `--rhythm-follow` | Da 0 a 1: risposte negli spazi oppure attacchi condivisi con la melodia. A 1 si usano solo gli attacchi melodici e si riprendono le durate sorgenti entro i limiti. |
| `--melody-follow` | Da 0 a 1: linea costruita sulle altezze rilevanti della frase oppure nota melodica più vicina. |
| `--lowest`, `--highest` | Limiti MIDI inclusivi; almeno dodici altezze consecutive. |
| `--mobility` | Da 0 a 1: movimento vicino alla nota precedente oppure maggiore apertura del registro, con risposte acute sui levare. Non impone ottave. |
| `--articulation` | Frazione della durata disponibile, maggiore di 0 e fino a 1. |
| `--variation` | Da 0 a 1: ampiezza delle variazioni nelle preferenze ritmiche e nelle altezze. A 0 gli stessi dati producono la stessa frase a ogni indice. |

Densità e sincopazione hanno compiti distinti: la prima regola quante note cercare, la seconda dove collocarle. I legami ritmico e melodico sono indipendenti. Tutti i preset rispettano `--min-spacing` in beat, `--grid` per le posizioni candidate, `--max-hold` per la durata massima e `--velocity-ratio` per la dinamica. Le durate non oltrepassano l'attacco successivo o il bordo della frase.

| Preset | Densità | Sincopi | Legame ritmico | Legame melodico | Mobilità | Variazione | Distanza minima | Articolazione |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `responsive` | 0,8 | 0,25 | 0,35 | 0,25 | 0,15 | 0,35 | 1 beat | 0,9 |
| `follow` | 4 | 0 | 1 | 1 | 0 | 0 | 1 beat | 0,9 |
| `slap` | 1,8 | 0,7 | 0,15 | 0,5 | 0,85 | 0,5 | 0,5 beat | 0,5 |

Le opzioni esplicite prevalgono sul preset. `--strategy` è un alias di `--preset`. In Python, `BassSettings` risolve i valori iniziali; `dataclasses.replace` conserva quelli già risolti.

## Attacchi

`_rhythm` considera gli attacchi sorgenti e, con `rhythm_follow < 1`, aggiunge la griglia dal primo attacco alla fine. Il numero cercato è:

```text
round(min(posizioni candidate, density × tempo dal primo attacco alla fine))
```

Il punteggio combina preferenza metrica, `2 × relazione con la melodia` e un valore casuale 0–1 moltiplicato per `variation`. La relazione vale `rhythm_follow` sugli attacchi sorgenti e `1 − rhythm_follow` negli spazi. Il primo attacco ha un bonus di 4.

Si scelgono i punteggi maggiori rispettando `min_spacing`; a parità prevale la posizione precedente. La preferenza metrica vale `1 − syncopation` sui beat interi, `syncopation` altrove. Il numero realizzato può essere inferiore all'obiettivo.

## Altezze

`_salience` pesa ogni classe di altezza con `durata × velocity × accento` (1,5 sui beat, 1 altrove). La classe più pesante è l'appoggio osservato; in parità prevale la classe più bassa.

`_pitches` usa le classi presenti nella frase entro il registro. Per ogni attacco considera la nota sorgente più vicina e quelle attive; a pari distanza prevalgono velocity maggiore e poi altezza minore.

```text
punteggio = (1 − melody_follow) × punteggio indipendente
            + melody_follow × punteggio locale
```

Il punteggio locale è +4 sulla classe della nota vicina, −4 sulle altre. Quello indipendente combina rilevanza, appoggio e compatibilità con le note attive: +1 per gli intervalli `(0, 3, 4, 5, 7, 8, 9)`, −2 per gli altri, calcolati come `(melodia − basso) % 12` e mediati sulle note attive.

Il bonus d'appoggio è 2,5 all'ingresso e `2,5 × variation` sulla chiusura periodica. Si sottraggono:

- Distanza dalla nota precedente × `0,1 × (1 − mobility)`.
- Distanza dal registro desiderato × `0,15 × mobility`.
- Ripetizione della stessa nota: `0,5 × (1 − melody_follow)`.

Il registro desiderato è il centro del registro meno `6 × mobility` sui beat, più `6 × mobility` sui levare. Si aggiunge una perturbazione fino a `variation`; in parità prevale l'altezza più bassa. Senza nota precedente si parte dal centro del registro.

## Durate, dinamica e variazioni

`_articulate` limita lo spazio al prossimo attacco, al bordo della frase e a `max_hold`:

```text
durata = (spazio × (1 − rhythm_follow)
          + durata sorgente limitata × rhythm_follow) × articulation
```

La velocity sorgente è pesata con accento 1 all'ingresso, 0,92 sui beat e 0,75 altrove. `rhythm_follow` miscela l'accento verso 1. Il risultato, moltiplicato per `velocity_ratio`, è arrotondato e limitato a 1–127.

La casualità usa `seed + phrase_index × 104729`. `variation_period` indica ogni quante frasi favorire la chiusura sull'appoggio.

## Suggerimento automatico dalla tappa

`analysis.recommend_bass` calcola media `m` e deviazione standard `s` della frazione di gate aperti, pesando ogni pattern per la durata. Esclude l'attesa prima del primo pattern. Dal preset `responsive` ricava:

| Controllo | Valore, arrotondato a tre decimali |
|---|---|
| Densità | `1 − 0,5 × m` |
| Sincopazione | `0,4 − 0,2 × m` |
| Articolazione | `0,85 − 0,25 × m` |
| Variazione | `0,2 + 0,6 × s` |

Gli altri valori sono quelli del preset. La frazione di gate non misura la densità MIDI effettiva, che dipende anche dai clock e dai percorsi del sequencer. [Comando di analisi](TEST-PRESET-MUSICALI.md#suggerire-il-basso-dalla-tappa).

Aggiornamenti durante l'esecuzione e interpolazione sono descritti nel [contratto dei controlli](CONTROLLI-BASSO.md).
