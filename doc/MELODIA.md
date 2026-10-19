# Generazione melodica da motivo

`music/melodic/generator.py` produce frasi dalla tonica e dalla scala della sezione e da un motivo configurato in gradi. Il registro è determinato dall'altezza di riferimento e da `octave`.

Nel ruolo `melody`, `development > 0` attiva lo sviluppo del motivo implementato in `music/melodic/development.py`. Con `development = 0` il generatore ripete letteralmente i gradi configurati su passi regolari.

## Sviluppo delle frasi

Il generatore organizza il materiale su un periodo di più finestre musicali:

1. **Presentazione:** conserva le prime tre note del motivo, o l'intero motivo se più corto, quando la finestra consente di eseguirle.
2. **Sviluppo:** sposta il riferimento melodico verso gradi superiori della scala e favorisce un arco nel registro.
3. **Contrasto:** usa il motivo con ordine degli indici invertito come riferimento per la selezione delle altezze.
4. **Conclusione:** orienta il materiale verso il basso e conclude sulla tonica con una nota più lunga. La tonica è scelta nel registro di base quando vicina, altrimenti nell'ottava disponibile più prossima.

Con quattro finestre le fasi compaiono una volta ciascuna. Con due finestre si hanno presentazione e conclusione; con periodi più lunghi vengono estese le fasi intermedie. Non è dichiarato un metro: una finestra di quattro beat non equivale di per sé a una battuta di 4/4.

Le altezze sono selezionate tra i gradi della scala. Il punteggio bilancia vicinanza al motivo, movimento dalla nota precedente, profilo del periodo e ripetizioni. Dopo un salto ampio è penalizzato un ulteriore movimento nella stessa direzione. Le note variate ordinarie sono selezionate entro sette semitoni dalla precedente; le note iniziali conservate del motivo e la chiusura seguono le regole specifiche descritte sopra.

Il ritmo usa durate di riferimento pari a metà, uno, uno e mezzo o due passi. I relativi pesi dipendono da `activity`, `development` e fase. Sono possibili pause interne. Articolazione e velocity variano all'interno della frase: gli inizi sono accentati e gli attacchi fra beat interi sono attenuati. La chiusura lascia un breve spazio prima della finestra successiva.

La prima richiesta dopo `reset()` stabilisce l'inizio del periodo, indipendentemente dal numero di beat assoluto di Live. La generazione ricostruisce il periodo con seed, indice di ciclo e indice di sezione: stesse richieste e impostazioni producono le stesse frasi, senza usare uno stato casuale globale. Il runtime esegue reset a Stop e alle discontinuità della pianificazione.

## Controlli

| Parametro | Significato |
|---|---|
| `octave` | Trasposizione in ottave rispetto all'altezza di riferimento |
| `step_beats` | Durata di riferimento per il ritmo |
| `articulation` | Proporzione di durata occupata dalle note articolate |
| `velocity` | Intensità di riferimento; con sviluppo attivo le note ricevono accenti e variazioni attorno a questo valore |
| `development` | Attivazione e intensità delle variazioni: `0` usa il motivo letterale |
| `activity` | Peso di suddivisioni brevi, durate lunghe e pause |
| `phrase_windows` | Numero di finestre per periodo, da 2 a 8 |
| `seed` | Identificativo intero per riprodurre le variazioni |

`presets/organico.json` usa `development = 0.7`, `activity = 0.75`, quattro finestre e seed `7`. Il menu espone `literal` per la ripetizione regolare, `developed` per lo sviluppo, `spacious` per una configurazione più diradata, oltre ai preset ritmici e di registro presenti nella configurazione.

Nel ruolo `bass_line` questo generatore usa il motivo letterale. Nel ruolo `sustained_texture` produce una nota sostenuta per finestra. I nuovi controlli di sviluppo riguardano il ruolo `melody`.

## Lettura nella vista globale

Dopo ogni chiamata il generatore espone metodo, fase, numero della finestra, indice del ciclo e seed. Il Coordinator conserva queste informazioni insieme alle note effettivamente restituite. Il terminale mostra la fase compositiva accanto al piano; il dettaglio è disponibile in `decisions.coordinator.voices.<id>.composition` nello stato JSON della sessione.

## Verifiche

I test controllano riproducibilità, conservazione del frammento iniziale, fasi del periodo, chiusure, varietà di attacchi e altezze, rispetto della scala e ripartenza del periodo dopo reset. Verificano inoltre che minore e dorico possano produrre il rispettivo colore modale e che il modo letterale resti disponibile.

L'efficacia musicale del primo sviluppo richiede confronto all'ascolto tra i preset, a parità di suono e sezione.

## Riferimento compositivo

[Ableton — Creating Melodies 1: Contour](https://makingmusic.ableton.com/creating-melodies-1-contour) discute equilibrio del profilo, movimento per grado e salti. I pesi, i limiti e la struttura del periodo qui descritti sono scelte implementate in Desnivel per questo primo sviluppo.
