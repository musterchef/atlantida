# Integrazione Snake

L'adattatore converte i pattern musicali in comandi OSC. Il bridge Max for Live applica i parametri; il clock delle note è gestito da Live.

## Bridge

Copiare `m4l/desnivel-bridge.amxd` e `m4l/desnivel_snake_params.js` nella stessa cartella e caricare il device in Live.

Il bridge riceve metriche sulla porta 9000 e comandi sulla 9001:

```text
/desnivel/v1/control/snake/set  nome_parametro  valore
```

La ricezione delle metriche serve alla diagnostica. Il replay musicale carica il GPX direttamente e invia i comandi. [Avvio del replay](TEST-PRESET-MUSICALI.md#avvio).

`desnivel_snake_params.js` cerca la prima istanza di Snake e risolve i parametri per nome con `live.object`. Per `Note_01` il range del parametro è 0–83. Nella configurazione Chromatic/C, i valori 36–51 producono MIDI 60–75.

## Sequenza di riferimento

Il launcher `04 - Snake - sequenza di riferimento.command` imposta Note 36–51, Chromatic/C, gate attivi, velocity 64, Swing 0, Length 100 ms e Gates Shape 0. Lascia invariata Notes Shape.

Prima dell'invio fermare il replay. Impostare manualmente Speed 16n, Steps 16, Direction forwards e Shift 1 nei tre banchi.

```sh
bash 'comandi/04 - Snake - sequenza di riferimento.command' --dry-run
```

## Shape

Il messaggio Max `shapes`, collegato a `js desnivel_snake_params.js`, elenca forme e indici; `shapes <indice>` legge un parametro. Le celle sono numerate per righe da 1 a 16.

Il comando `gate_shape` risolve `Gate_Shape` per nome nella mod; sul vanilla a 152 parametri usa l'indice 90. È accettato anche l'alias `test_shape_90`.

Nel replay a sezioni, l'adattatore estrae un valore 0–13 a ogni ingresso di sezione, inclusa la prima. `--seed` rende ripetibile l'estrazione. Gli aggiornamenti nella stessa sezione non cambiano Shape.

## Banco Length

`tools/build_snake_length.py` aggiunge al vanilla 3.2.3 un banco Length, conservando Notes, Gates, Velocities e Custom. Il sorgente accettato è verificato tramite SHA256.

```sh
python3 tools/build_snake_length.py   --source "$HOME/Music/Ableton/User Library/MaxForLive/MDD___SNAKE_V3.2.3.amxd"   --output /tmp/desnivel-snake-length/MDD_SNAKE_LengthBank.amxd
```

L'output deve essere nuovo. Length ha 16 valori 0–127, associati alle celle Notes e convertiti tra Min e Max in millisecondi; i limiti iniziali sono 50–500 ms. La durata è acquisita all'attacco. `makenote` chiude la nota precedente al riattacco della stessa altezza.

Per aggiungere anche Export e il player usare il [builder live](PLAYER-M4L.md#basso-collegato-a-snake).

## Problemi

- Nessun dato OSC: verificare porta e presenza di altri ricevitori.
- Parametro inatteso: leggere il nome prima di scrivere; gli ID Live non sono persistenti.
- Crash con `live.remote~`: il controllo verificato usa `live.object`.

[Stato](SESSIONE.md) · [Export](EXPORT-SNAKE.md)
