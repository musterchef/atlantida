# Contratto OSC dei dati di viaggio — pilot metrico implementato

- Stato: metriche approvate e producer OSC implementato; fatti puntuali fuori dalla prima prova
- Aggiornato: 2026-10-02
- Decisione di architettura collegata: [DECISIONE-ARCHITETTURA-AUDIO.md](DECISIONE-ARCHITETTURA-AUDIO.md)
- Inventario dei dati sorgente: [STATO-CONTRATTO-OSC.md](STATO-CONTRATTO-OSC.md)

## Scopo

Il producer Python pubblica misure relative alla tappa; la pubblicazione dei fatti neutrali è ancora da definire. Non decide come questi segnali diventino musica o immagini. Il motore musicale Python, Max for Live, TouchDesigner e altri consumer possono leggere gli stessi messaggi e applicare interpretazioni indipendenti.

Questo sostituisce come interfaccia target il contratto musicale `/mod/*` e `/event/major|minor/*`, che resta documentazione del prototipo corrente finche' la migrazione non e' completata.

## Namespace metrico approvato e namespace fattuale proposto

```text
/desnivel/v1/trip/metric/<nome>
/desnivel/v1/trip/fact/<tipo>
```

`metric` identifica una serie misurata/derivata lungo la tappa; `fact` identifica un fatto puntuale rilevato. Gli indirizzi non contengono gruppi musicali come `journey`, `macro`, `meso` o `body`, ne' destinazioni come `pitch`, `filter` o `euclid`.

## Messaggi metrici

Ogni messaggio metrico ha due argomenti OSC numerici:

```text
/desnivel/v1/trip/metric/<nome>  elapsed_s  value
```

`elapsed_s` e' il tempo relativo alla tappa, in secondi, alla fine dell'intervallo di misura. `value` usa l'unita' indicata qui sotto. Il consumer puo' usare il timestamp sorgente anche se il playback e' accelerato o sospeso.

### Frequenza approvata per il primo test

La frequenza OSC iniziale e' **1 Hz** per tutte le metriche qui elencate. La griglia interna resta quella di `TimingConfig` (default attuale 10 Hz); i dati vengono aggregati per intervallo di un secondo. Non si invia un campione interno isolato fingendo che rappresenti un secondo.

- `distance_delta_m`: somma delle distanze interne nell'intervallo appena concluso.
- `distance_total_m`: distanza cumulata interpolata al tempo di fine intervallo.
- `elevation_m`: quota filtrata interpolata al tempo di fine intervallo.
- `speed_kmh`: `distance_delta_m / durata_intervallo * 3.6`.
- `slope_ratio`: variazione della quota filtrata nell'intervallo divisa per `distance_delta_m`; se la distanza e' zero, la metrica non e' disponibile per quell'intervallo.
- `effort_estimate`: stima calcolata da velocita' e pendenza dell'intervallo con riferimenti e pesi `GpxConfig`; non e' una misura fisiologica.

Formula implementata per `effort_estimate`, usando i parametri centralizzati in `GpxConfig`:

```text
speed_norm = clip(speed_kmh / speed_reference_kmh, 0, 1)
slope_norm = clip(max(slope_ratio, 0) / slope_reference, 0, 1)
effort_estimate = clip(effort_weight_speed * speed_norm
					 + effort_weight_slope * slope_norm, 0, 1)
```

Al tempo `elapsed_s=0` possono essere inviati solo campi definibili senza intervallo precedente (quota e distanza cumulata). Velocita', pendenza, distanza dell'intervallo e stima effort non vengono inizializzate a zero: sono omesse finche' non esiste un intervallo completo.

| Campo pilot | Unita' | Origine esistente | Note |
|---|---|---|---|
| `distance_delta_m` | m per intervallo | `dist_m` | Pubblicato solo dopo un intervallo completo di un secondo. |
| `distance_total_m` | m cumulati | `cum_dist_m` | Progressione spaziale dall'inizio. |
| `elevation_m` | m | `ele` | Elevazione con mediana raw gia' applicata dal loader. |
| `speed_kmh` | km/h | `speed_kmh` | Calcolata dalla distanza per intervallo e dal delta temporale. |
| `slope_ratio` | rapporto | `slope` | Variazione quota/distanza sull'intervallo; `0.08` equivale a 8%. |
| `effort_estimate` | `[0, 1]` | `effort` | Stima composita configurata in `GpxConfig`, non misura fisiologica. Il consumer puo' ignorarla e interpretare velocita'/pendenza separatamente. |

`elapsed_s` e' il timestamp di ogni campione, non una metrica ripetuta con un proprio indirizzo. `lat` e `lon` non fanno parte del primo flusso audio; potranno essere esposti separatamente se un consumer geospaziale ne avra' bisogno.

### Valori mancanti e validita'

- Non inviare `NaN` o infinito come valore di una metrica.
- Un campione non disponibile viene omesso; la mancanza di un messaggio non equivale a zero.
- Se il GPX non contiene quota, `elevation_m`, `slope_ratio` ed `effort_estimate` sono assenti; quando esistono quote valide il loader interpola le lacune sull'indice e prolunga i valori estremi ai bordi. Non viene attualmente trasmesso un flag che distingua quote misurate e ricostruite.
- Il consumer mantiene l'ultimo valore solo per un timeout configurato localmente; scaduto il timeout, il dato e' non disponibile.
- Il timeout con cui un consumer considera stale un dato e' configurazione locale del consumer; non viene imposto dal producer.

### Frequenza

I dati interni sono ricampionati a `TimingConfig.internal_rate_hz` (default attuale 10 Hz), ma il contratto OSC non obbliga a trasmettere tutti i campioni. La frequenza iniziale approvata per il pilot e' 1 Hz; non si eredita dai vecchi rate per gruppi `/mod/*`.

Se una prova mostra che un consumer necessita' di piu' dettaglio, aumentare la frequenza solo tramite configurazione centrale e definire l'aggregazione per intervallo; non cambiare in silenzio unita' o significato.

## Fatti del viaggio — fuori dal primo test

Formato da definire dopo il primo test metrico:

```text
/desnivel/v1/trip/fact/<tipo>  json_payload
```

Il JSON include `elapsed_s`, `payload` descrittivo e `location` quando il fatto e' localizzato. Il `tipo` descrive l'osservazione (per esempio `summit`, `coast_threshold_crossed`, `poi_entered`), non il suo effetto musicale.

Il formato futuro non trasmettera' `MAJOR`/`MINOR`, cap di eventi musicali o cooldown compositivi. I detector possono avere soglie fisiche motivate e configurabili; la scelta di quale fatto diventa climax, nota o transizione appartiene al consumer.

La corrispondenza esatta dei tipi fattuali e dei payload va definita insieme alla migrazione di `Event` e del filtro eventi: non riutilizzare automaticamente i kind del prototipo quando codificano gia' una scelta compositiva.

## Responsabilita'

### Python producer

- Parse GPX, ricampionamento, unita' e metriche derivate.
- Filtri necessari alla qualita' della misura, documentati per campo.
- Fatti geografici con timestamp e payload descrittivo.
- Nessuna scala musicale, root, palette, densita' ritmica o priorita' sonora.

### Consumer

- Ogni consumer decide autonomamente come combinare i segnali, quali ignorare e come gestire dati mancanti o stale.
- Il motore musicale Python decide i mapping sonori; l’adattatore traduce le decisioni per il device e la destinazione esegue i controlli e il timing musicale (M4L/Ableton nel primo esperimento Snake).
- TouchDesigner decide mapping visivo.
- Le impostazioni del singolo consumer sono locali al consumer e non cambiano il significato OSC.

## Sorgente unica e test

Il catalogo implementato in `src/desnivel/trip_metrics.py` e la frequenza in `OscConfig.trip_metrics_rate_hz` sono le fonti operative per nomi, unita' e rate. Test dedicati verificano route, timestamp, aggregazione e validita'; sink e CLI consumano questo catalogo invece di mantenere mapping separati.

Test minimi del producer:

1. ogni messaggio usa un indirizzo presente nel catalogo;
2. tipo OSC, unita' e timestamp rispettano la specifica;
3. nessun valore trasmesso e' NaN/infinito;
4. unita' e valori restano invariati al cambiare del consumer;
5. dati mancanti non vengono convertiti implicitamente in zero.

## Stato e prossime decisioni

Approvati per il primo pilot: namespace `/desnivel/v1/trip/metric/<nome>`, argomenti `elapsed_s, value`, frequenza 1 Hz, campi elencati e `effort_estimate` come stima opzionale.

Restano da decidere/implementare:

1. Il timeout locale di ciascun consumer per valori non aggiornati.
2. Frequenze superiori, solo se richieste da una prova concreta.
3. Schema dei fatti/eventi neutrali; non e' incluso nella prima prova audio.

Questa specifica e' implementata dal publisher `python -m desnivel.cli.stream_metrics`; la ricezione in M4L è stata verificata dall’utente. Restano da verificare la gestione dei dati stale e il nuovo flusso di comandi musicali separato dalle metriche.
