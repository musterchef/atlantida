#!/bin/bash
# Avvio da Finder: usa il progetto che contiene questa cartella.
cd -- "$(dirname -- "$0")/.." || exit 1
if [[ ! -x .venv/bin/python ]]; then
    echo "Ambiente Python assente: manca .venv/bin/python nel progetto."
    read -r -p "Premi Invio per chiudere. "
    exit 1
fi
echo "Firenze–San Gimignano · 150× · circa 3 minuti e 36 secondi"
echo "Avvia il trasporto Live. Un solo viaggio alla volta; Ctrl+C interrompe il replay."
./.venv/bin/python -m desnivel.cli.trip_music --gpx gpx/tappa05_Firenze_San_Gimignano.gpx --stage-music presets/tappe/firenze_san_gimignano.json --preset presets/misto.json --speed 150 --seed 7
result=$?
if [[ $result -ne 0 ]]; then
    echo "Comando terminato con codice $result. Leggi il messaggio sopra."
fi
read -r -p "Premi Invio per chiudere. "
exit "$result"
