#!/bin/bash
# Riusa il launcher di acquisizione con chiusura manuale.
exec /bin/bash "$(dirname -- "$0")/05 - Acquisisci Export Snake.command" --keep-open --seconds 600 --label "Stop e ripartenza" "$@"
