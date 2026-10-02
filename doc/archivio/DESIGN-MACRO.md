# DESIGN — MacroModulator

**Stato (2026-10-02)**: design del prototipo già implementato in `src/desnivel/modulators/macro.py` e `macro_policies.py`. Il testo seguente conserva le scelte di quel prototipo, non definisce il futuro contratto musicale.
**Collocazione target**: regole riutilizzabili nel motore musicale Python, separate dal producer del viaggio. Vedi [decisione corrente](../DECISIONE-ARCHITETTURA-AUDIO.md).
**Vincolo trasversale**: gli output devono essere **client-agnostici**
(decisioni musicali indipendenti dallo strumento). Questo non le rende metriche neutre del viaggio: scala e palette restano interpretazioni musicali.

---

## 1. Cosa decide

I canali macro descrivono il **mondo sonoro corrente**: tonalita',
timbro, registro, ampiezza dello spazio, brillantezza. Cambiano
**lentamente** (frequenza di emissione 1 Hz) e per **sezioni**
(idealmente decine di secondi - minuti).

| Canale | Tipo | Range | Significato |
|---|---|---|---|
| `macro_scale` | int | 0-5 | Modo musicale corrente |
| `macro_palette` | int | 0-4 | Famiglia timbrica |
| `macro_register` | float | 0-1 | Centro di registro (grave→acuto) |
| `macro_space` | float | 0-1 | Apertura/riverbero |
| `macro_brightness` | float | 0-1 | Brillantezza spettrale |

Codici di `scale` e `palette` dal contratto (vedi `CONTRATTO-MODULAZIONI.md` §2.1).

---

## 2. Da cosa li deriviamo

Tutti gli input vengono da `Track` (gia' caricato, contiene `elevation`,
`slope`, `speed`, `distance_km`, `t`) e da `ModulationFrame` (per
usare canali gia' calcolati, p.es. `journey/openness`).

**Sorgenti grezze per macrotempo:**

1. **Profilo elevazione** (`track.samples["elevation"]`):
   - mediana sezione → mondo "alto/basso";
   - varianza sezione → mondo "mosso/piatto".
2. **Distanza dalla costa** se disponibile (oggi non lo e' come canale
   diretto, ma il `SeaDetector` la calcola; per MVP la deriviamo a
   parte o aspettiamo Binario B).
3. **`journey/openness`** (gia' nel frame): proxy di apertura
   percettiva.

**MVP**: usa solo (1) + (3). La distanza dalla costa entra in una
seconda iterazione.

---

## 3. Segmentazione in macro-sezioni

Le decisioni macro sono **per sezione**, non per campione. Servono
sezioni di durata minima (es. 60 s). Approccio:

1. Calcola elevazione media in finestre scorrevoli da 60 s.
2. Discretizza in bucket (es. 5 livelli di quota: `[0, 200, 500, 800,
   1500, +inf]` m).
3. Una "sezione" inizia quando il bucket cambia in modo **stabile**
   per piu' di `dwell_s` (default 30 s) — hysteresis.
4. Stessa cosa indipendentemente su varianza locale (mosso/piatto).

Output: una lista `[(t_start, t_end, elev_bucket, var_bucket), ...]`.

Per ogni sezione si decide il valore dei 5 canali macro. Poi si
**interpola con rampa morbida** (es. 5-10 s) tra una sezione e la
successiva.

---

## 4. Mappa decisionale (MVP)

Tabella esplicita, modificabile in config. Niente magia.

### `macro_palette` (0=pad, 1=strings, 2=bells, 3=granular, 4=brass)

| Quota mediana | Varianza locale | Palette |
|---|---|---|
| basso (<200m) | piatto | 0 (pad) |
| basso (<200m) | mosso | 1 (strings) |
| medio (200-800m) | piatto | 1 (strings) |
| medio (200-800m) | mosso | 3 (granular) |
| alto (>800m) | qualunque | 4 (brass) |

### `macro_scale` (0=pent, 1=dor, 2=phryg, 3=mix, 4=lyd, 5=whole)

| `journey/openness` corrente | Scale |
|---|---|
| < 0.3 | 2 (phryg, chiuso, minore) |
| 0.3 - 0.6 | 1 (dor) |
| 0.6 - 0.85 | 4 (lyd, aperto, brillante) |
| > 0.85 | 5 (whole-tone, sospeso) |

### `macro_register` (0=grave, 1=acuto)

`register = clip(elev_mediana_sezione / 1500, 0, 1)`. Sezione alta →
registro acuto.

### `macro_space` (0=secco, 1=riverberato)

`space = openness_medio_sezione` (riusa il canale gia' presente).
Sezioni aperte → spazio ampio.

### `macro_brightness` (0=scuro, 1=brillante)

MVP: combinazione lineare di `register` e `palette` (palette brass=alta,
pad=bassa). Versione 2: stima da ora del giorno se i timestamp GPX
hanno tz coerenti.

---

## 5. Smoothing / continuita'

- `scale` e `palette` sono **int**: cambiano discretamente. La rampa
  e' fra sezioni: 5 s prima del cambio comincia ad alternare il
  vecchio valore col nuovo (NON un'interpolazione lineare di int, che
  non avrebbe senso musicale). MVP semplificato: cambio istantaneo
  al confine di sezione, eventuale dwell time per evitare flicker.
- `register`, `space`, `brightness`: float, rampa lineare 5-10 s ai
  confini di sezione.
- Internal rate 10 Hz come gli altri modulator. Il sink OSC decima
  a 1 Hz (gia' configurato in `config.osc.rates_hz["macro"]`).

---

## 6. API e wiring

File nuovi:
- `src/desnivel/modulators/macro.py` — classe `MacroModulator`.

File modificati:
- `src/desnivel/config.py` — nuova `MacroConfig` con: bucket di quota,
  bucket di varianza, dwell_s, tabella decisionale (default dal §4),
  rampe.
- `src/desnivel/cli/run_stage.py`, `run_all.py`, `cli/play.py` —
  aggiungere `MacroModulator(config)` allo stack (dopo `Journey` e
  `Tension`).

Firma:
```python
class MacroModulator:
    def __init__(self, config: Config = DEFAULT_CONFIG) -> None: ...
    output_channels = ("macro_scale", "macro_palette",
                       "macro_register", "macro_space", "macro_brightness")
    def process(self, track: Track, frame: ModulationFrame) -> ModulationFrame:
        ...
```

Conforme a `Modulator` Protocol (gli altri due lo seguono).

---

## 7. Test

`tests/test_macro_modulator.py`:

1. Track sintetico piatto a 100m → tutte le sezioni stesso bucket →
   `macro_palette` costante, `macro_register` ~0.07, `macro_scale`
   dipende solo da `openness`.
2. Track con due sezioni nette (50m per 5 min, poi 1000m per 5 min) →
   `macro_register` deve passare da ~0.03 a ~0.67 con rampa.
3. Track piccolo (10 s) → niente sezioni valide, fallback a un valore
   default (`scale=1`, `palette=0`, register/space/brightness=0.5).
4. Invarianti: tutti i canali nel range corretto, `scale`/`palette`
   sono int.
5. Determinismo: due esecuzioni stesso track → output identici.

---

## 8. Cosa NON facciamo in questa iterazione

- Niente `brightness` da ora del giorno (richiede tz nel GPX).
- Niente distanza dalla costa come input (aspetta che il `SeaDetector`
  esponga un canale continuo o aspetta un `CoastalProximity` modulator
  futuro).
- Niente apprendimento: tabella decisionale statica in config.
- Niente eventi `territory_change` emessi qui: quello e' del
  `TerrainDetector` (Binario B priorita' 2).

---

## 9. Test di accettazione manuale

Dopo l'implementazione, lanciare:
```sh
desnivel-play --stage tappa_06 --speed 30 --loop
```
e con bridge MIDI mappare CC 23 (palette) e CC 24 (scale) su due
parametri di un Wavetable (es. preset selector via Macro su rack di 4
preset). Output atteso: durante un giro la "scena timbrica" cambia
nettamente in 2-4 punti (sezioni della tappa).

Se non si sente cambiare: i bucket di quota sono troppo stretti per
quella tappa, oppure la dwell_s e' troppo lunga. Da regolare in
config, non nel codice.
