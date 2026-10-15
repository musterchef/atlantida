# Controlli del basso durante l'esecuzione

Il basso può ricevere nuovi valori mentre `live_bass` è in esecuzione. Questa parte riceve, valida e applica i controlli alle finestre future; il componente che decide quando inviarli verrà sviluppato separatamente. L'analisi della tappa e il replay non inviano questi messaggi.

I launcher 07/08 mantengono i valori iniziali scelti dall'utente. Senza messaggi di controllo, il funzionamento resta quello corrente.

## Ingresso

Il ricevitore OSC di `live_bass` ascolta su `127.0.0.1`, porta **9003** o quella scelta con `--listen-port`. Sulla stessa porta riceve due indirizzi distinti:

| Indirizzo | Contenuto |
|---|---|
| `/desnivel/v1/snake/state` | Stato e fase di Snake. |
| `/desnivel/v1/bass/control` | Cambi dei parametri musicali del basso. |

Il controllo contiene un unico argomento OSC: una stringa JSON. Esempio del suo contenuto:

```json
{
  "version": 1,
  "serial": 1,
  "parameters": {
    "density": 0.9,
    "articulation": 0.65
  },
  "transition_windows": 4
}
```

Questo è il formato da usare nel futuro mittente, non un comando da incollare nel terminale. Oggi non è presente una CLI per inviarlo.

| Campo | Regola |
|---|---|
| `version` | Intero 1. |
| `serial` | Intero non negativo, crescente per ogni nuovo controllo. Separato dal seriale di Snake. |
| `parameters` | Oggetto non vuoto con uno o più valori di destinazione. |
| `transition_windows` | Intero non negativo; valore predefinito 4. Zero richiede un cambio senza interpolazione. |

Il ricevitore ammette un solo flusso di controllo: il futuro mittente deve mantenere la numerazione crescente finché quel processo `live_bass` resta aperto. Stop e ripartenza di Live non azzerano il seriale dei controlli; riavviare `live_bass` lo azzera. Un seriale duplicato o minore dell'ultimo accettato viene ignorato. Un messaggio rifiutato non consuma il seriale.

UDP non conferma la consegna. La numerazione scarta duplicati e comandi superati, ma non recupera quelli persi. Un futuro mittente che deve garantire la convergenza potrà inviare periodicamente tutti i valori desiderati con un nuovo seriale.

## Parametri ammessi

I nomi JSON usano underscore, mentre le opzioni CLI usano trattini. Per esempio `rhythm_follow` corrisponde a `--rhythm-follow`.

- `density`, `syncopation`, `rhythm_follow`, `melody_follow`, `mobility`, `variation`;
- `lowest`, `highest`, `min_spacing`;
- `articulation`, `velocity_ratio`, `max_hold`;
- `grid`, `seed`, `variation_period`.

Valgono gli stessi [intervalli dei parametri musicali](PLAYER-M4L.md#generare-il-basso). `lowest`, `highest`, `seed` e `variation_period` richiedono interi. Gli altri valori devono essere numerici e finiti. Null, booleani, nomi sconosciuti e valori fuori intervallo vengono rifiutati. Il registro viene validato considerando insieme tutti i cambi ricevuti: per spostare entrambi i limiti, inviarli nello stesso messaggio.

Il cambio viene validato per intero prima di applicarlo. Se un valore è sbagliato, nessuna parte del messaggio viene applicata e il basso conserva il piano corrente. I preset restano valori iniziali: `preset` e `strategy` non sono parametri del controllo live.

## Cambi parziali

Un campo omesso conserva la destinazione già richiesta, anche quando il basso sta ancora interpolando verso di essa. Per esempio, dopo aver richiesto densità 0,9, questo secondo messaggio cambia soltanto la mobilità:

```json
{
  "version": 1,
  "serial": 2,
  "parameters": {"mobility": 0.4},
  "transition_windows": 2
}
```

La densità di destinazione resta 0,9. Il nuovo passaggio parte dagli ultimi valori pianificati e procede verso la destinazione aggiornata; non fa ripartire il basso dai valori iniziali.

## Quando si sente il cambio

Il messaggio viene accettato durante l'esecuzione, ma il piano viene aggiornato con il successivo snapshot Snake valido. Si agisce sulle finestre ancora future: una frase iniziata non viene riscritta. Non è un controllo audio istantaneo.

Con `--window 4`, una finestra contiene quattro beat. Una transizione di quattro finestre distribuisce il passaggio su sedici beat di pianificazione, oltre all'anticipo già previsto dal sistema. Aumentare la durata della transizione rende il cambio più lento; ridurla rende il cambio più rapido.

L'interpolazione riguarda densità, legami, sincopazione, mobilità, variazione, durate, dinamica e limiti del registro. Le altezze dei limiti vengono arrotondate a interi. Griglia, seed e periodo cambiano in modo discreto. Numero di note e scelte di altezza restano discreti: piccoli cambi possono produrre lo stesso piano.

A un cambio di epoca del trasporto, la transizione riparte dall'ultimo valore pianificato, usando la nuova posizione. Prima che esista una finestra di riferimento, i nuovi valori vengono adottati direttamente. Con `transition_windows: 0` non si interpola, ma si attende comunque lo snapshot e si aggiorna una finestra futura.

## Codice e acquisizione

| File | Responsabilità |
|---|---|
| [control.py](../src/desnivel/music/bass/control.py) | Contratto e validazione dei cambi parziali, senza dipendenze da OSC o Snake. |
| [live_bass.py](../src/desnivel/cli/live_bass.py) | Ricezione OSC, ordine dei comandi e acquisizione. |
| [snake_live.py](../src/desnivel/adapters/snake_live.py) | Destinazione dei controlli, transizioni e pianificazione. |
| [generator.py](../src/desnivel/music/bass/generator.py) | Interpolazione dei valori e composizione da una frase. |

Con `--capture`, i controlli accettati e quelli rifiutati vengono conservati nel JSONL insieme agli stati e ai piani. I rifiuti hanno `decode_error` e `raw_args`; per argomenti non testuali si conserva la rappresentazione diagnostica. Duplicati e comandi superati vengono segnalati nel terminale e non aggiunti all'archivio. Le acquisizioni restano fuori dalla repository.

Il producer rimane agnostico. Il futuro componente che dirige il basso userà il contratto dei controlli, senza introdurre logica della tappa nel generatore o nel device Snake.
