#!/bin/bash
cd -- "$(dirname -- "$0")/.." || exit 1

usage() {
    cat <<'HELP'
Uso: ./comandi/08\ -\ Scegli\ assetto\ basso.command [sobrio|dialogo|ritmico] [opzioni basso]

  sobrio   Poche note, registro basso e movimento contenuto. Partire da qui.
  dialogo  Più risposte e movimento, senza riempire tutti gli spazi.
  ritmico  Note corte, più levare e risposte acute.

Senza argomenti mostra il menu. Le opzioni aggiuntive prevalgono sull'assetto.
Esempio: ./comandi/08\ -\ Scegli\ assetto\ basso.command dialogo --density .8

Richiede Set funzionante, Export attivo e player del basso caricato.
Chiudere 05/06/07 e altri ricevitori sulla porta 9003.
Avviare il replay in un secondo terminale. Ctrl+C ferma il basso.
HELP
}

if [[ $# -eq 0 ]]; then
    printf '1) Sobrio: poche note, registro basso\n2) Dialogo: risposte e movimento moderato\n3) Ritmico: note corte e levare\n'
    read -r -p 'Assetto [1]: ' choice || exit 1
    choice=${choice:-1}
else
    choice=$1
    shift
fi

case "$choice" in
    1|sobrio)
        name=sobrio
        options=(--preset responsive --highest 47 --density .6 --mobility .15 --articulation .85)
        ;;
    2|dialogo)
        name=dialogo
        options=(--preset responsive --highest 55 --density 1 --min-spacing .5
                 --syncopation .45 --rhythm-follow .3 --melody-follow .35
                 --mobility .3 --articulation .7)
        ;;
    3|ritmico)
        name=ritmico
        options=(--preset slap --highest 59 --density 1.2 --mobility .6)
        ;;
    -h|--help)
        usage
        exit 0
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac

printf 'Assetto: %s\nOpzioni: ' "$name"
printf '%q ' "${options[@]}" --seed 0 "$@"
printf '\n'
exec /bin/bash './comandi/07 - Basso e acquisizione.command' "${options[@]}" --seed 0 "$@"
