# Dati del viaggio e metriche OSC

Il modulo `desnivel.trip` carica le tracce GPX, ricampiona i punti a intervalli regolari e pubblica le grandezze fisiche del percorso via OSC.

---

## Formato dei messaggi OSC

Ogni misura viene trasmessa con due argomenti numerici:

```text
/desnivel/v1/trip/metric/<nome>  elapsed_s  value
```

- **`elapsed_s`**: tempo relativo dall'inizio della tappa (in secondi), corrispondente alla fine dell'intervallo di misura. Rimane coerente con il tempo reale del viaggio anche durante replay accelerati.
- **`value`**: valore numerico della grandezza, nell'unità specificata.

### Frequenza di campionamento e aggregazione
- **Campionamento interno**: 10 Hz (`TimingConfig.internal_rate_hz`), per calcolare con precisione differenze di quota e velocità istantanee.
- **Pubblicazione OSC**: 1 Hz (`OscConfig.trip_metrics_rate_hz`, porta predefinita **9000**). Le metriche vengono aggregate e inviate su finestre di un secondo.

---

## Catalogo delle metriche

| Metrica | Unità | Descrizione e calcolo |
|---|---|---|
| `distance_delta_m` | m | Distanza percorsa nel secondo trascorso. |
| `distance_total_m` | m | Distanza complessiva percorsa dall'inizio della tappa. |
| `elevation_m` | m | Quota sul livello del mare, filtrata con mediana sui dati grezzi. |
| `speed_kmh` | km/h | Velocità oraria calcolata come `distance_delta_m / durata × 3.6`. |
| `slope_ratio` | rapporto | Pendenza del terreno (rapporto dislivello / distanza percorsa). Un valore di `0.08` indica una salita dell'8%. |
| `effort_estimate` | 0.0 – 1.0 | Indice composito di sforzo, ottenuto combinando velocità normalizzata e pendenza positiva. |

### Calcolo dell'indice di sforzo

L'indice sintetico di sforzo combina la spinta della velocità e la resistenza della pendenza:

```text
speed_norm      = clip(speed_kmh / speed_reference_kmh, 0, 1)
slope_norm      = clip(max(slope_ratio, 0) / slope_reference, 0, 1)
effort_estimate = clip(weight_speed * speed_norm + weight_slope * slope_norm, 0, 1)
```

I pesi e le velocità di riferimento sono configurabili in `src/desnivel/trip/config.py`.

---

## Gestione dei valori mancanti

- I campi non disponibili nella traccia originale (ad esempio quote assenti) non vengono trasmessi; l'assenza di un messaggio non equivale a zero.
- Se la traccia contiene solo alcune quote, le lacune intermedie vengono interpolate linearmente sulla distanza percorsa.

---

## Riferimenti nel codice e uso

- **Catalogo metriche**: `src/desnivel/trip/metrics.py`
- **Configurazioni e parametri**: `src/desnivel/trip/config.py`
- **Comando per lo streaming delle metriche**:
  ```sh
  python -m desnivel.cli.stream_metrics --gpx gpx/tappa04_Levanto_La_Spezia.gpx --speed 30
  ```

Per le opzioni complete e la modalità `--dry-run`, vedere [COMANDI.md](COMANDI.md).

