# Rack DESNIVEL — costruzione e mappatura

Questa è la **guida ufficiale** per preparare Ableton a ricevere il
flusso musicale di DESNIVEL. Si costruisce **una volta sola**: dopo,
qualsiasi preset si lascia cadere dentro la *instrument chain* del
rack e funziona.

Fonte di verità del mapping: [src/desnivel/bridges/rack_spec.py](../src/desnivel/bridges/rack_spec.py).
Tabella tecnica OSC→CC: [src/desnivel/bridges/osc_to_midi.py](../src/desnivel/bridges/osc_to_midi.py).
Le due fonti sono tenute in sincrono dai test ([tests/test_rack_spec.py](../tests/test_rack_spec.py)).

Per vedere la mappa attiva in qualsiasi momento:

```sh
desnivel-bridge-midi --show-mapping
```

---

## Architettura

Il rack contiene **3 catene logiche**, in ordine di segnale:

```
DESNIVEL Voice (Instrument Rack)
├── MIDI chain — manipolazione note in ingresso
│   • Instrument internal pitch   ← macro 1: Root
│   • Scale (opzionale)     ← (modalita' impostata dalla catena attiva)
│   • Instrument internal pitch   ← macro 7: Register
│
├── Instrument chain — la voce. Multi-catena, una per modalità.
│   • Chain 0 (Ionian)     ┐
│   • Chain 1 (Dorian)     │
│   • Chain 2 (Phrygian)   ├─ Chain Selector ← macro 2: Mode
│   • Chain 3 (Lydian)     │
│   • Chain 4 (Mixolydian) │
│   • Chain 5 (Whole-tone) ┘
│   In ognuna: lo STESSO strumento + un device Scale configurato
│   con la griglia di quella modalità.
│
└── Audio chain — colore e dinamica
    • Auto Filter (LP)      ← macro 3: Brightness (Freq) + 5: Tension (Res)
    • Auto Filter (BP)      ← macro 8: Openness  (Freq)
    • Saturator             ← macro 6: Energy    (Drive)
    • Reverb                ← macro 4: Space     (Dry/Wet)
```

Le **8 macro** del rack ricevono i CC dal bridge OSC→MIDI:

| # | Macro | CC | Sorgente OSC | Significato |
|---|---|---|---|---|
| 1 | Root | 25 | `/mod/meso/root` | Fondamentale, cambia ogni ~8 km |
| 2 | Mode | 23 | `/mod/macro/scale` | Modalità musicale (chain selector) |
| 3 | Brightness | 31 | `/mod/macro/brightness` | Apertura del filtro |
| 4 | Space | 30 | `/mod/macro/space` | Riverbero |
| 5 | Tension | 26 | `/mod/meso/tension` | Risonanza (salite) |
| 6 | Energy | 21 | `/mod/journey/energy` | Drive (sforzo) |
| 7 | Register | 29 | `/mod/macro/register` | Ottava (quota) |
| 8 | Openness | 22 | `/mod/journey/openness` | Secondo filtro |

I CC `20, 24, 27, 28` restano **fuori dal rack** (ausiliari): si
usano per un secondo rack ritmico o per automazioni libere.

---

## Procedura di costruzione

### 1. Crea il rack vuoto

1. Nuovo MIDI track.
2. Crea un **Instrument Rack** vuoto: drag&drop *Instruments → Instrument Rack* sulla traccia.
3. Aprilo (click sulla freccia in alto a destra del titolo).

### 2. Pitch interno dello strumento

Per il drone sostenuto, Root e Register devono controllare il pitch interno
dello strumento, non il device MIDI **Pitch**: i MIDI effect ricevono il
nuovo valore solo al successivo Note On.

1. Inserisci lo strumento nella catena e individua il suo parametro interno
   **Coarse / Transpose**.
2. Mappalo alla macro **Root** con **Min −12 / Max +12 semitoni**.
3. Mappa un secondo parametro di trasposizione, oppure lo stesso parametro
   nel rack scelto, alla macro **Register** con **Min −12 / Max +12 semitoni**.

I due offset si sommano: Root muove la fondamentale armonica (CC 25),
Register muove il registro del momento (CC 29). Il valore di `meso_root`
è già uno scostamento in semitoni rispetto alla tonica di riferimento.

### 3. Instrument chain — 6 modalità

1. Dentro la *instrument chain* del rack, **duplica la catena 6 volte** (drag&drop sull'intestazione catena, o copia/incolla).
2. In ogni catena metti **lo stesso strumento** (es. Wavetable con un preset pad). Più tardi cambierai preset una volta sola e si propaga.
3. In ogni catena, **davanti** allo strumento, aggiungi un **Scale** (Live device, *MIDI Effects → Scale*). Configura la griglia secondo la modalità:

   | Catena | Modalità | Griglia (note out per ogni nota in C..B) |
   |---|---|---|
   | 0 | Ionian      | C D E F G A B |
   | 1 | Dorian      | C D E♭ F G A B♭ |
   | 2 | Phrygian    | C D♭ E♭ F G A♭ B♭ |
   | 3 | Lydian      | C D E F# G A B |
   | 4 | Mixolydian  | C D E F G A B♭ |
   | 5 | Whole tone  | C D E F# G# A# |

   Trascinami: per disegnare la griglia, attiva *Fold* in basso a destra del device Scale per vedere solo le 12 note, poi clicca le celle in modo che ogni nota di ingresso vada sulla nota di uscita più vicina della modalità.

4. Apri il **Chain List** (icona "≡" a sinistra del rack). Click su "Chain" per mostrare lo **Zone Editor**. Imposta le zone così che ogni catena occupi UN valore (0, 1, 2, ...):
   - Chain 0: zona da 0 a 0
   - Chain 1: zona da 1 a 1
   - ...
   - Chain 5: zona da 5 a 5
5. Click destro sul **Chain Selector** (il triangolino blu in alto al Chain List) → **Map to Macro 2**. Rinomina "Mode". Min 0 / Max 5.

> Risultato: quando arriva CC 23 = 2, si attiva solo la catena Phrygian. Tutti gli altri strumenti restano in silenzio.

### 4. Audio chain — Filter, Saturator, Reverb

Dopo le instrument chain, nella *audio chain* del rack:

1. **Auto Filter** (filtro principale, low-pass).
   - Knob *Frequency* → Map to Macro 3 **"Brightness"**. Min 400 Hz / Max 12 kHz.
   - Knob *Resonance* → Map to Macro 5 **"Tension"**. Min 0% / Max 55%.

2. **Auto Filter** secondo (band-pass o secondo low-pass, in serie).
   - Knob *Frequency* → Map to Macro 8 **"Openness"**. Min 200 Hz / Max 6 kHz.

3. **Saturator**.
   - Knob *Drive* → Map to Macro 6 **"Energy"**. Min 0 dB / Max 12 dB.

4. **Reverb**.
   - Knob *Dry/Wet* → Map to Macro 4 **"Space"**. Min 0% / Max 45%.

### 5. Salva il preset

Click destro sul titolo del rack → **Save As Preset…** → nome `DESNIVEL Voice`. Da ora è disponibile in Browser come preset riutilizzabile.

---

## Prima prova di ascolto

1. Sulla traccia, crea una **clip MIDI di 4 misure** con UNA SOLA nota: **C2 lunga 4 misure**, legata in loop.
2. In due terminali (entrambi col venv attivo):

   ```sh
   # T1
   desnivel-bridge-midi --midi-port "IAC Driver Bus 1"
   ```

   ```sh
   # T2
   desnivel-play --stage tappa_04 --speed 100
   ```

3. Premi Play sulla clip in Ableton. Senti:
   - una nota che **trasla** ogni ~5 secondi (Root, sequenza modale)
   - la **modalità** che cambia tra catene (Mode)
   - il **filtro** che respira (Brightness, Openness)
   - il **riverbero** che si apre nei tratti panoramici (Space)
   - **drive** che cresce nelle salite (Energy, Tension)

---

## Cosa NON mappare (errori comuni)

- **NON** mappare CC 27/28 (Density/Rotation) su parametri audio
  continui: sono **interi ritmici**. Vanno su un sequencer
  (EuclidStep, M4L step sequencer) o ignorati.
- **NON** mappare CC 24 (Palette) su un knob singolo: sarebbe
  un chain selector di un secondo rack. Per ora ignoralo.
- **NON** lasciare i range MIDI Map ai valori di default
  (0..127 in unità del device): `Pitch` andrebbe a ±48 semitoni
  e farebbe saltare ottave a caso. Stringi sempre Min/Max secondo
  la tabella sopra.

---

## Riferimenti

- Specifica macchina-leggibile: [rack_spec.py](../src/desnivel/bridges/rack_spec.py)
- Tabella tecnica OSC→CC: [osc_to_midi.py](../src/desnivel/bridges/osc_to_midi.py)
- Test di sincronia tra le due: [test_rack_spec.py](../tests/test_rack_spec.py)
- Cheat sheet comandi: [COMANDI.md](COMANDI.md)
