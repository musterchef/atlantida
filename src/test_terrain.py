"""Quick test dei 3 metodi terrain su punti reali del percorso."""
from terrain_classify import classify_terrain, terrain_to_label

# Punti reali dalle 12 tappe (start/end di ciascuna)
pts = [
    {"lat": 45.081, "lon": 7.657,  "ele": 258},   # Torino (partenza)
    {"lat": 44.519, "lon": 7.993,  "ele": 532},   # Dogliani (collina Langhe)
    {"lat": 44.402, "lon": 8.939,  "ele": 46},    # Genova
    {"lat": 44.176, "lon": 9.635,  "ele": 74},    # Levanto (costa ligure)
    {"lat": 44.111, "lon": 9.814,  "ele": 18},    # La Spezia (costa)
    {"lat": 43.814, "lon": 11.267, "ele": 198},   # Firenze
    {"lat": 42.724, "lon": 12.127, "ele": 127},   # Orvieto
    {"lat": 41.880, "lon": 12.516, "ele": 49},    # Roma
    {"lat": 41.316, "lon": 13.001, "ele": 4},     # Sabaudia (costa)
    {"lat": 40.847, "lon": 14.276, "ele": 9},     # Napoli costa
    {"lat": 41.074, "lon": 14.822, "ele": 370},   # San Nicola Manfredi
    {"lat": 41.685, "lon": 15.393, "ele": 77},    # San Severo (Tavoliere)
    {"lat": 41.947, "lon": 16.017, "ele": 93},    # Peschici (Gargano costa)
    {"lat": 41.711, "lon": 16.051, "ele": 77},    # Mattinata (costa)
    {"lat": 41.085, "lon": 16.271, "ele": 538},   # Castel del Monte (arrivo)
]

names = [
    "Torino", "Dogliani", "Genova", "Levanto", "La Spezia",
    "Firenze", "Orvieto", "Roma", "Sabaudia", "Napoli",
    "S.Nicola Manfredi", "San Severo", "Peschici", "Mattinata",
    "Castel del Monte",
]

for method in ["elevation", "coastline", "srtm"]:
    print(f"\n{'='*50}")
    try:
        vals = classify_terrain(pts, method=method)
        print()
        for name, p, v in zip(names, pts, vals):
            print(f"  {name:<20s} ele={p['ele']:>4}m  -> {v:.3f} ({terrain_to_label(v)})")
    except Exception as e:
        print(f"  ERRORE: {e}")
