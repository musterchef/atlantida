# Dati del viaggio — contratto OSC

Il producer Python carica il GPX, ricampiona i dati e pubblica le misure della tappa. L'interpretazione musicale appartiene al motore.

## Messaggi metrici

Ogni messaggio ha due argomenti OSC numerici:

```text
/desnivel/v1/trip/metric/<nome>  elapsed_s  value
```

`elapsed_s` è il tempo relativo alla tappa, in secondi, alla fine dell'intervallo di misura. Mantiene il tempo del viaggio anche quando il replay è accelerato. `value` usa l'unità del campo.

### Aggregazione a 1 Hz

Il ricampionamento interno è a 10 Hz (`TimingConfig.internal_rate_hz`); la pubblicazione è a 1 Hz (`OscConfig.trip_metrics_rate_hz`). Le misure sono calcolate su intervalli completi di un secondo.

| Campo | Unità | Calcolo |
|---|---|---|
| `distance_delta_m` | m | Distanza percorsa nell'intervallo. |
| `distance_total_m` | m | Distanza cumulata, interpolata alla fine dell'intervallo. |
| `elevation_m` | m | Quota filtrata, interpolata alla fine dell'intervallo. Il loader applica una mediana ai dati grezzi. |
| `speed_kmh` | km/h | `distance_delta_m / durata_intervallo × 3.6`. |
| `slope_ratio` | rapporto | Variazione di quota filtrata divisa per la distanza dell'intervallo. `0.08` equivale a 8%. Assente se la distanza è zero. |
| `effort_estimate` | [0, 1] | Stima da velocità e pendenza, con riferimenti e pesi di `GpxConfig`; non è una misura fisiologica. |

```text
speed_norm = clip(speed_kmh / speed_reference_kmh, 0, 1)
slope_norm = clip(max(slope_ratio, 0) / slope_reference, 0, 1)
effort_estimate = clip(effort_weight_speed * speed_norm
                       + effort_weight_slope * slope_norm, 0, 1)
```

A `elapsed_s=0` si inviano quota e distanza cumulata, se disponibili. Le altre misure attendono il primo intervallo completo. Latitudine e longitudine non sono pubblicate da questo contratto.

Per aumentare la frequenza, aggiornare la configurazione centrale e definire l'aggregazione per intervallo.

### Dati mancanti

- I valori non disponibili o non finiti vengono omessi. L'assenza di un messaggio non equivale a zero.
- Senza quote nel GPX sono assenti `elevation_m`, `slope_ratio` ed `effort_estimate`.
- Se esistono quote valide, il loader interpola le lacune sull'indice e prolunga i valori estremi ai bordi. Non viene trasmesso un flag per distinguere quote misurate e ricostruite.
- Il timeout è una scelta del consumer. Va ancora implementato nei ricevitori che conservano l'ultimo valore senza scadenza.

## Fatti geografici — da definire

È proposto il namespace `/desnivel/v1/trip/fact/<tipo>`, ma tipi, payload e pubblicazione non sono implementati. I fatti dovranno descrivere osservazioni geografiche; la loro interpretazione musicale appartiene al motore.

## Codice e verifiche

Il catalogo delle metriche è in `src/desnivel/trip/metrics.py`; frequenze e parametri sono in `src/desnivel/trip/config.py`. Sink e CLI usano questo catalogo. I test controllano indirizzi, unità, timestamp, aggregazione e valori mancanti.

Comando: `python -m desnivel.cli.stream_metrics`. [Uso](COMANDI.md#leggere-un-viaggio) · [Porte](COMANDI.md#porte-predefinite) · [Architettura](TODO-ARCHITECTURE.md)
