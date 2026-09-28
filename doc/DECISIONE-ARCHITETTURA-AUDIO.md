# Decisione architetturale — audio e visualizzazione

- Stato: accettata
- Data: 2026-09-28
- Ambito: flusso dati GPX, generazione audio e visualizzazione

## Decisione

Il percorso audio principale e':

```text
GPX -> Python DESNIVEL -> OSC (metriche e fatti del viaggio) -> Max for Live / Ableton -> audio
                                                                    |
                                                                    +-> telemetria musicale -> TouchDesigner -> visual
```

Il contratto in uscita da Python e' agnostico rispetto ai consumer: descrive metriche derivate dal viaggio e fatti/eventi con unita', range, qualita' e tempi definiti, non intenzioni musicali o istruzioni visive. Il pilot metrico e' specificato in [CONTRATTO-DATI-VIAGGIO.md](CONTRATTO-DATI-VIAGGIO.md) e il publisher e' implementato; M4L non e' ancora collegato.

TouchDesigner non e' un passaggio intermedio per i dati GPX diretti ad Ableton. Il suo ruolo nel percorso scelto e' visualizzare lo stato o l'attivita' musicale. Se per rappresentare cio' che sta effettivamente suonando servono dati dal motore audio, M4L/Ableton inviera' telemetria a TD su un'interfaccia separata. Formato, indirizzi e frequenza di tale telemetria restano da progettare.

## Responsabilita'

### Python DESNIVEL

- Carica e deriva le metriche dal GPX.
- Pulisce, ricampiona e deriva metriche con semantica di viaggio; produce fatti/eventi geografici senza scegliere scale, root, palette, pattern o destinazioni audio/visuali.
- Non assegna ai fatti geografici priorita' compositive `MAJOR`/`MINOR` come parte del contratto neutrale; ogni consumer puo' classificare localmente la loro rilevanza.
- Gestisce il playback della tappa e la velocita' di riproduzione.
- Non genera singole note MIDI nel percorso audio principale.

### Max for Live / Ableton

- Riceve direttamente da Python il contratto neutrale delle metriche e dei fatti del viaggio.
- Decide localmente come interpretare i segnali, mantiene i sequencer e genera note, durate e velocity.
- Esegue il sound design e l'uscita audio.
- Non duplica le trasformazioni GPX e gli smoothing gia' assegnati a Python.

### TouchDesigner

- Riceve telemetria musicale dal motore audio quando necessaria alla visualizzazione.
- Visualizza stato e attivita' musicale.
- Non inoltra i dati GPX ad Ableton e non e' necessario per l'esecuzione audio.

## Percorsi esistenti e stato

- `desnivel-play` -> OSC su `127.0.0.1:9000`: prototipo attuale che invia `/mod/*` e `/event/*`; `/mod/*` contiene gia' decisioni musicali e non e' il contratto target agnostico.
- `python -m desnivel.cli.stream_metrics --gpx <file>` -> primo publisher del pilot neutrale su porta `9000`; invia metriche a 1 Hz, senza eventi.
- `desnivel-bridge-midi`: adattatore provvisorio OSC-to-MIDI. Rimane uno strumento di test/ascolto del percorso di controllo, non il generatore audio definitivo.
- `td/frame_execute.py` -> `/desnivel/*` su porta `9001` -> `td/m4l/desnivel.maxpat` / `desnivel_notes.js`: percorso precedente TD-to-M4L, da considerare legacy rispetto alla decisione corrente. Non rimuoverlo finche' non e' completata la prova verticale del nuovo percorso.
- Le modifiche non committate al patch Max che aggiungono la seconda voce restano associate a quel percorso legacy e non costituiscono integrazione del nuovo contratto OSC.

## Contratto e cambi

Il contratto OSC neutrale e' l'interfaccia condivisa fra producer e consumer, non un vincolo immutabile. Se l'implementazione o la prova mostrano una lacuna, si puo' modificarlo deliberatamente: documentare il motivo, aggiornare producer e consumer insieme, e coprire il cambiamento con test. Evitare canali, conversioni o mapping paralleli introdotti solo per compensare un consumer non allineato.

## Prova verticale minima

La prima integrazione non deve migrare tutti i canali o i layer. Il consumer va costruito per piccoli confini verificabili:

1. **Contratto neutrale:** approvare/correggere la bozza [CONTRATTO-DATI-VIAGGIO.md](CONTRATTO-DATI-VIAGGIO.md): catalogo di metriche/fatti, unita', range, qualita'/missingness, tempi e indirizzi OSC. Lo snapshot dei dati disponibili e' in [STATO-CONTRATTO-OSC.md](STATO-CONTRATTO-OSC.md).
2. **Scelta del layer consumer:** scegliere un layer audio e dichiarare come M4L interpreta i segnali neutrali; non chiedere a Python di produrre `root`, `scale` o `euclid_k` per quel consumer.
3. **Ricezione:** un device M4L riceve direttamente gli indirizzi OSC del nuovo contratto. Prima si verifica ricezione e parsing senza generazione audio.
4. **Generazione minima:** aggiungere un solo sequencer autonomo che mappa localmente i segnali ricevuti in note. Riutilizzare un sequencer/oggetto affidabile se compatibile con Max e Live; evitare di riscrivere un motore ritmico senza necessita'.
5. **Parametri:** ogni default del sequencer non fornito dai dati deve essere un parametro M4L esplicito e nominato, non un numero nascosto nel patch.
6. **Test:** verificare separatamente ricezione OSC, comportamento del sequencer con input controllati, e ascolto end-to-end della tappa. La prova audio non dipende da TouchDesigner.
7. **Visualizzazione:** solo dopo avere audio stabile, definire la telemetria minima M4L -> TD necessaria a rappresentare la musica effettivamente generata.

La prima voce non verra' implementata finche' layer, canali consumati e comportamento di fallback non sono specificati. Se emergono requisiti non coperti dal contratto, modificarlo prima di codificare il workaround.

## Criterio per dismettere il legacy

Il percorso legacy TD -> `/desnivel/*` -> M4L si puo' rimuovere o archiviare solo dopo che la prova verticale Python -> OSC -> M4L -> audio e' ripetibile e documentata. Fino ad allora va etichettato come legacy, non confuso con il workflow attivo.
