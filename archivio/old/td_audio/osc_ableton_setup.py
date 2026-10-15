"""
DESNIVEL — OSC Setup per Ableton Live
======================================
Questo file NON va incollato in TD. È la documentazione del setup OSC
e uno script di test per verificare che i messaggi arrivino ad Ableton.

── ARCHITETTURA ──────────────────────────────────────────────────────────

  TouchDesigner (master)
    frame_execute.py
         │  OSC UDP
         ▼  127.0.0.1:9000
  Ableton Live + Max for Live
    [OSC receiver device] su ogni traccia


── SETUP TOUCHDESIGNER ────────────────────────────────────────────────────

1. Crea un OSC Out DAT chiamato "osc_out"
   - Network Address:  127.0.0.1
   - Network Port:     9000
   - Protocol:         UDP

2. Crea un File In DAT chiamato "file_csv"
   - File: /percorso/output/tappa_01.csv
   - DAT Active: ON

3. Crea un Execute DAT (Frame Execute)
   - Incolla il contenuto di frame_execute.py
   - Active: ON
   - Execute on Frame Start: ON

4. FPS di TD deve essere 30 (matches RESAMPLE_FPS del pipeline)


── SETUP ABLETON LIVE ─────────────────────────────────────────────────────

Opzione A — Max for Live (consigliata):
  Usa il device "Max MIDI Effect" o "MIDI Monitor" con un patch
  che riceve OSC e mappa su parametri Live.

  Patch minimo in Max (da incollare in un Max for Live device):
  
    [udpreceive 9000]
    |
    [route /desnivel/bpm /desnivel/pitch /desnivel/drive
           /desnivel/reverb /desnivel/volume /desnivel/cutoff
           /desnivel/density /desnivel/scale /desnivel/voice
           /desnivel/progress /desnivel/color_temp]
    |         |         |
    [print]  [print]  [print]   <- per debug; sostituire con Live API

  Per cambiare il BPM di Live in tempo reale:
    [route /desnivel/bpm] → [live.set "song" "tempo"]

  Per controllare un parametro di un device:
    [route /desnivel/drive] → [live.set "device" "chain_selector" ...]


Opzione B — OSC Control Surface (più semplice):
  Installa il MIDI Remote Script "AbletonOSC" (open source):
  https://github.com/ideoforms/AbletonOSC

  Poi manda direttamente messaggi come:
    /live/song/set/tempo  [bpm_value]
    /live/track/1/device/1/parameter/1/value  [drive_value]


── MESSAGGI OSC INVIATI DA TD ────────────────────────────────────────────

  /desnivel/bpm         float   BPM target (120.0 – 160.0)
  /desnivel/pitch       int     Pitch MIDI (36 – 84)
  /desnivel/drive       float   Saturazione (0.0 – 1.0)
  /desnivel/reverb      float   Riverbero (0.0 – 1.0)
  /desnivel/volume      float   Volume (0.4 – 1.0)
  /desnivel/cutoff      float   Filter cutoff (0.05 – 1.0)
  /desnivel/density     float   Densità ritmica (0.0 – 1.0)
  /desnivel/color_temp  float   Temperatura colore (0.0 – 1.0)
  /desnivel/scale       string  Scale name (major, dorian, phrygian...)
  /desnivel/voice       string  Timbre (drone_water, pad_plain, ...)
  /desnivel/progress    float   Avanzamento tappa (0.0 – 1.0)


── SCRIPT DI TEST PYTHON (fuori da TD) ────────────────────────────────────

Esegui questo script per verificare che Ableton riceva i messaggi OSC
prima di avviare TD.

Richiede: pip install python-osc
"""

# ── Test sender (esegui da terminale, non da TD) ─────────────────────────

def run_test():
    """
    Manda 5 messaggi OSC di test ad Ableton.
    Richiede: pip install python-osc
    Esegui: python osc_ableton_setup.py
    """
    try:
        from pythonosc import udp_client
    except ImportError:
        print("Installa prima: pip install python-osc")
        return

    client = udp_client.SimpleUDPClient("127.0.0.1", 9000)

    test_frames = [
        {"bpm": 128.0, "pitch": 62, "drive": 0.3, "reverb": 0.5,
         "volume": 0.8, "cutoff": 0.7, "density": 0.4,
         "color_temp": 0.3, "scale": "dorian", "voice": "pad_plain",
         "t_norm": 0.0},
        {"bpm": 132.0, "pitch": 65, "drive": 0.6, "reverb": 0.3,
         "volume": 0.9, "cutoff": 0.9, "density": 0.7,
         "color_temp": 0.5, "scale": "phrygian", "voice": "pluck_hill",
         "t_norm": 0.25},
        {"bpm": 140.0, "pitch": 72, "drive": 0.9, "reverb": 0.15,
         "volume": 1.0, "cutoff": 1.0, "density": 0.9,
         "color_temp": 0.7, "scale": "minor", "voice": "brass_mountain",
         "t_norm": 0.5},
        {"bpm": 136.0, "pitch": 68, "drive": 0.5, "reverb": 0.6,
         "volume": 0.7, "cutoff": 0.6, "density": 0.5,
         "color_temp": 0.9, "scale": "dorian", "voice": "pad_plain",
         "t_norm": 0.75},
        {"bpm": 124.0, "pitch": 58, "drive": 0.1, "reverb": 0.8,
         "volume": 0.5, "cutoff": 0.4, "density": 0.2,
         "color_temp": 0.4, "scale": "major", "voice": "drone_water",
         "t_norm": 1.0},
    ]

    print("Invio messaggi OSC a 127.0.0.1:9000 (Ableton)...")
    for i, params in enumerate(test_frames):
        client.send_message('/desnivel/bpm',       params['bpm'])
        client.send_message('/desnivel/pitch',      params['pitch'])
        client.send_message('/desnivel/drive',      params['drive'])
        client.send_message('/desnivel/reverb',     params['reverb'])
        client.send_message('/desnivel/volume',     params['volume'])
        client.send_message('/desnivel/cutoff',     params['cutoff'])
        client.send_message('/desnivel/density',    params['density'])
        client.send_message('/desnivel/color_temp', params['color_temp'])
        client.send_message('/desnivel/scale',      params['scale'])
        client.send_message('/desnivel/voice',      params['voice'])
        client.send_message('/desnivel/progress',   params['t_norm'])
        print(f"  [{i+1}/5] BPM={params['bpm']} pitch={params['pitch']} "
              f"scale={params['scale']} drive={params['drive']:.1f}")

    print("Fatto. Controlla Ableton / Max for Live per conferma ricezione.")


if __name__ == "__main__":
    run_test()
