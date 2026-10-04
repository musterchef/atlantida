# Passaggio di sessione

Aggiornato il 2026-10-04.

## Direzione

`GPX → metriche neutre → regole musicali Python → adattatori → strumenti`

Python decide la musica; le destinazioni eseguono sul clock di Live. Il tempo del replay è distinto dal BPM. Il motore non conosce parametri Snake, ID Live o synth. Timbri e impostazioni di Ableton sono scelte dell'utente.

## Implementato

- Producer: sei metriche neutre, `desnivel-stream-metrics`, OSC 9000.
- Regola quota con isteresi: `music.py`, `presets/quota.json`.
- Movimento, sforzo e misto: `journey_music.py`, preset pesati e configurazione della tappa. Motivo stabile, densità dei gate, tre sezioni armoniche per distanza.
- Adattatore Snake: note, gate e Shape casuale 0–13 all'ingresso di ogni sezione. `--seed` rende ripetibili le estrazioni. Indice parametro 90 confermato dall'utente per Gates; alias `gate_shape`, alias diagnostico precedente conservato.
- Secondo adattatore: `phrases.py`, `adapters/phrase_player.py`, CLI `send_phrase`. Frasi complete con posizione, altezza MIDI, durata e velocity; due esempi di basso in `presets/phrases/`.
- Player M4L: JS prepara eventi, `pipe` li esegue in tick, `flush` gestisce note-off. Nessun polling. Frase successiva applicata al ciclo seguente.

## Risultato verificato

L'utente conferma che il player suona in Live. Confermate ricezione OSC e notifiche Stop/Play dell'osservatore. Correzioni presenti nella patch del progetto e nel device salvato: `pipe 0 0 0 @delaytime 0 ticks`, `live.thisdevice`, `live.observer is_playing`.

194 test Python passati: 193 nella suite in sandbox e il test UDP separatamente fuori sandbox. Test JS simulato passato per ordinamento eventi, confine ciclo, cambio frase, stop, ripartenza, panic e silenzio. La prova Live non equivale a una validazione completa del timing.

## File e comandi

- [Comandi](COMANDI.md)
- [Preset musicali](TEST-PRESET-MUSICALI.md)
- [Player M4L: patch e prova](PLAYER-M4L.md)
- [Test quota](TEST-VIAGGIO-SNAKE.md)
- [Architettura](DECISIONE-ARCHITETTURA-AUDIO.md)

Il player si costruisce da `m4l/desnivel_phrase_player.maxpat`, con il JS omonimo accanto al device. Il device dell'utente è in `~/Music/Ableton/User Library/Presets/MIDI Effects/Max MIDI Effect/desnivel-send-phrase.amxd`. Il repository conserva sorgenti editabili; nessuna modifica diretta al device installato durante la pulizia.

Porta player 9002, indirizzo `/desnivel/v1/player/bass/phrase`; porta Snake 9001, indirizzo `/desnivel/v1/control/snake/set`. Una sola ricezione per porta. Dopo modifiche al JS aggiornare la copia accanto al device e ricaricare.

## Limiti e prossimi passi

1. Verificare cambio frase durante la riproduzione e note-off durante note lunghe.
2. Misurare almeno 32 cicli: deferlow/JS al confine può introdurre ritardo. Quantizzazione iniziale e riallineamento a seek/loop non implementati.
3. Collegare regole del basso e armonia condivisa al viaggio, dopo la verifica del player.
4. Destinazioni multiple Snake e controllo effetti ancora da implementare. Snake trova la prima istanza per nome.

Player: massimo 32 note, nessuna sovrapposizione della stessa altezza e nessuna nota oltre il ciclo. UDP senza ACK. Velocity Snake e ottava MIDI effettiva dei suoi parametri restano da verificare. Non usare `live.remote~`: ha causato crash nelle prove precedenti.

## Metodo

Documentazione concisa, stato attuale e limiti espliciti. Trattare l'utente come collaboratore esperto. Diagnosticare dal device salvato e dai dati, senza far ripetere verifiche generiche. Non alterare il percorso funzionante durante pulizie. Conservare implementazioni precedenti; documentazione storica in `doc/archivio/`.
