"""
README — Sonic Timeline Visualization
======================================

Questo modulo genera visualizzazioni della narrazione sonora di Desnivel:
come il viaggio si trasforma in parametri musicali (pitch, BPM, drive, reverb…).

QUICK START
===========

1. Genera visualizzazione per UNA tappa:
   
   .venv/bin/python src/visualize_sonic.py 1
   → output/viz/tappa_01_sonic.png

2. Genera ALL 12 tappe:
   
   .venv/bin/python src/visualize_all_sonic.py
   → output/viz/tappa_NN_sonic.png (×12)

3. Genera indice HTML interattivo:
   
   .venv/bin/python src/generate_sonic_index.py
   → output/viz/index.html (apri nel browser)

COSA VEDI NEI PLOT
==================

Ogni plot ha 4 righe di dati, condivise sull'asse X (tempo della tappa):

┌─────────────────────────────────────────────────────────┐
│ ROW 1: PITCH (note musicali in MIDI)                    │
├─────────────────────────────────────────────────────────┤
│  • Altitudine tappa → altezza note                       │
│  • Colori scala armonica:                               │
│    - Cyan: major (alba/mattina)                         │
│    - Yellow: pentatonic_major (meriggio)                │
│    - Orange: dorian (tramonto)                          │
│    - Purple: phrygian (notte)                           │
│  • Marker = voce timbrica (drone, pad, pluck, brass)   │
├─────────────────────────────────────────────────────────┤
│ ROW 2: BPM (pulsazione)                                 │
├─────────────────────────────────────────────────────────┤
│  • Velocità corpo → ritmo                               │
│  • 0 km/h = 60 BPM (fermo)                              │
│  • 30 km/h = 140 BPM (ritmo massimo)                    │
├─────────────────────────────────────────────────────────┤
│ ROW 3: MODULAZIONI DINAMICHE                            │
├─────────────────────────────────────────────────────────┤
│  • Drive (rosso): sforzo, pendenze positive             │
│  • Reverb (blu): flow, continuità movimento             │
│  • Volume (verde): sempre presente (0.4–1.0)            │
│  • Cutoff (arancio sfumato): apertura filtro            │
├─────────────────────────────────────────────────────────┤
│ ROW 4: DENSITY (densità ritmica)                        │
├─────────────────────────────────────────────────────────┤
│  • Curvatura strada → complessità ritmica               │
│  • Strade dritte = sparse                               │
│  • Curve frequenti = pattern fitta                      │
└─────────────────────────────────────────────────────────┘

BACKGROUND: Sfumatura di colore alba→tramonto (cold→warm).

INTERPRETAZIONE MUSICALE
=========================

Leggi il plot come una partitura:

  ALBA (Cyan):        Apertura tonale, tonica major, volume moderato
  ↓
  MATTINA (Cyan):     Volume aumenta, BPM stabile, terrain pianura
  ↓
  MERIGGIO (Yellow):  Scala pentatonic, BPM picchi, compressione luminosa
  ↓
  POMERIGGIO (Orange):Dorian, transizione, terrain collina/montagna
  ↓
  TRAMONTO (Orange):  Colore caldo, drive alto (ultime salite), volume crescente
  ↓
  SERA (Purple):      Phrygian, introspezione, terra montagnosa

Se vedi:
  • Pitch che sale da destra a sinistra → salita in quota
  • BPM piatto → strada regolare in piano
  • Drive improvviso → pendenza ripida
  • Reverb basso → terreno discontinuo (curves)

… il mappaggio sta funzionando correttamente!

OPZIONI AVANZATE
================

Visualizza una tappa con MOSTRA (plt.show()):
  .venv/bin/python src/visualize_sonic.py 3 --show

Salva con DPI diverso (più veloce per preview, più nitido per stampa):
  .venv/bin/python src/visualize_sonic.py 5 --dpi 100    # veloce
  .venv/bin/python src/visualize_sonic.py 5 --dpi 300    # stampa

Salva in cartella custom:
  .venv/bin/python src/visualize_sonic.py 2 --output /tmp/tappa02.png

Batch con DPI custom:
  .venv/bin/python src/visualize_all_sonic.py --dpi 100 --start 1 --end 6

DIPENDENZE
==========

  matplotlib      (visualizzazione)
  numpy           (operazioni numeriche)
  (install automaticamente con: pip install -r requirements.txt)

Se manca matplotlib:
  .venv/bin/pip install matplotlib numpy

PERFORMANCE
===========

  • Un plot: ~5 secondi
  • 12 tappe: ~60 secondi
  • Singolo PNG: 550–650 KB
  • Indice HTML: 22 KB
  • Totale: 7–8 MB

VALIDAZIONE
===========

Dopo generare i plot, controlla:

  1. ✓ Pitch scala continuamente con altitudine (vedi nei dati source)
  2. ✓ BPM segue velocità corpo (compara con CSV speed_kmh)
  3. ✓ Scala armonica cambia con ora del giorno (aurora → tramonto)
  4. ✓ Drive alto in salite ripide
  5. ✓ Reverb alto in zone di flow continuo
  6. ✓ Terrain voice cambia con pendenza (coast→plain→hill→mountain)

Se qualcosa non torna → verifica i dati in `desnivel_summary.json`.

NEXT: OSC OUTPUT
================

Una volta validato il plot, il passo dopo è inviare i parametri
sonori in tempo reale ad Ableton Live via OSC.

  → src/osc_sender.py (prossimo step)

---
Autore: Marco Musto
Data: 2026-05-09
Versione: 0.1
"""
# Questo file è documentazione, non codice.
# Salva come: doc/VISUALIZATION_README.md
