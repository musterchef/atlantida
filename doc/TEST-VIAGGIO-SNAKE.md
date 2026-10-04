# Quota e pattern

Prima regola musicale: la quota sceglie tra due pattern in La pentatonica minore.

- All'avvio: pattern basso sotto 200 m, alto da 200 m.
- In seguito: alto da 215 m, basso sotto 185 m. Il margine evita oscillazioni vicino alla soglia.
- Basso: 4 gate su 16. Alto: 8 gate su 16 e melodia diversa.
- Un pattern viene inviato all'avvio e a ogni cambio di stato. Dati mancanti o non finiti mantengono lo stato; un nuovo avvio riparte senza stato.

## Ascolto

In Live caricare il bridge e Snake già provati, con uno strumento a valle. Per confrontare i pattern impostare manualmente 16 step e percorso per righe; disattivare eventuali quantizzatori Scale a valle. Avviare il trasporto di Live.

```sh
source .venv/bin/activate
python -m desnivel.cli.trip_music --gpx gpx/tappa04_Levanto_La_Spezia.gpx --rules presets/quota.json --speed 50
```

Non occorre avviare `stream_metrics`: il comando riusa le metriche neutre direttamente in Python. Invia solo controlli sulla porta 9001; i display metrici della patch non vengono aggiornati.

Con `--dry-run` stampa le decisioni senza inviare né attendere. Sul GPX indicato, a velocità 50×, i cambi sono a 0, 36,0, 163,5, 184,3 e 220,7 secondi dal principio del replay. Il riepilogo viene stampato prima dell'invio.

BPM e avanzamento di Snake restano in Live. I comandi aggiornano subito i parametri: non sono atomici né quantizzati a battuta. A fine invio o con Ctrl+C Snake continua con l'ultimo pattern; fermarlo dal trasporto di Live.

## Modifiche

- `presets/quota.json`: metrica, soglia, margine, scala, tonica, gradi e gate dei due pattern. I gradi partono da 0; possono estendersi su più ottave.
- `src/desnivel/music.py`: regola e pattern indipendenti dal device; calcolo delle scale.
- `src/desnivel/adapters/snake.py`: traduce note e gate in parametri Snake, richiede 16 elementi e note 0–83.
- `src/desnivel/cli/trip_music.py`: carica il viaggio e riproduce i cambi attraverso l'adattatore.

Il pattern musicale contiene note espresse in semitoni e gate. Snake usa per ora gli stessi valori numerici verificati nelle prove precedenti; l'ottava MIDI effettiva resta da misurare. Nessun controllo di velocity in questa prova.

Verificati 14 test Python su regola, adattatore e metriche, e il dry-run sul GPX. L'ascolto della regola in Live resta da eseguire.
