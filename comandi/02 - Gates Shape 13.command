#!/bin/bash
# Avvio da Finder: usa il progetto che contiene questa cartella.
cd -- "$(dirname -- "$0")/.." || exit 1
if [[ ! -x .venv/bin/python ]]; then
    echo "Ambiente Python assente: manca .venv/bin/python nel progetto."
    read -r -p "Premi Invio per chiudere. "
    exit 1
fi
echo "Imposta la Shape dei Gates a 13"
./.venv/bin/python -m desnivel.cli.snake_test --param gate_shape --value 13
result=$?
if [[ $result -ne 0 ]]; then
    echo "Comando terminato con codice $result. Leggi il messaggio sopra."
fi
read -r -p "Premi Invio per chiudere. "
exit "$result"
