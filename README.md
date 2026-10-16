# Desnivel

*Ascoltare la forma di un viaggio.*

Desnivel è un progetto di musica generativa che trasforma i dati di un viaggio reale in composizione sonora.  
Nasce da un percorso in bicicletta compiuto nel **2025 da Torino a Castel del Monte**: giorni di pedalata, lentezza, fatica fisica e paesaggi che mutano da nord a sud dell'Italia.

L'idea alla base del progetto è semplice: **il corpo in movimento misura il mondo**. La traccia registrata durante il cammino non è un semplice archivio di coordinate geografiche, ma una **partitura latente** che racchiude ritmi, gradienti di sforzo, pause e cambiamenti di territorio. Desnivel non illustra il viaggio con una musica di sottofondo: ne ascolta la struttura interna e la traduce in suono.

---

## I tre livelli di Desnivel

### 1. Dal cammino al suono (L'esperienza umana)
Pedalare per ore al giorno trasforma la percezione del tempo: la velocità si riduce e ogni dislivello diventa fatica corporea, ogni discesa respiro, ogni sosta silenzio o sospensione.  
Desnivel cattura questi contrasti:
- **La salita e lo sforzo** aumentano la densità musicale e la tensione armonica.
- **La pianura e la velocità** aprono lo spazio ritmico e distendono le durate.
- **Le soste** diradano gli eventi sonori, lasciando risuonare solo gli echi o il registro grave.

### 2. Le voci e il dialogo musicale (La composizione)
Il paesaggio sonoro è affidato a più voci che interagiscono in tempo reale:
- **La voce melodica del territorio**: un sequencer melodico attraversa le scale musicali scelte per ogni tappa (scale doriche, frigie, l了两pentatoniche o minori), cambiando colore man mano che il percorso avanza tra colline, litorali o altipiani.
- **Il basso generativo**: una linea di basso autonoma che ascolta la melodia e decide come accompagnarla. Può limitarsi a un sostegno sobrio e radicato, inserirsi con risposte contrappuntistiche negli spazi lasciati liberi dalla melodia, oppure muoversi su accenti sincopati e slap ritmici.
- **Intervento dal vivo**: durante l'esecuzione è possibile intervenire sui parametri espressivi del basso (densità, mobilità, articolazione, registro) per modulare la risposta musicale in corsa.

### 3. Sotto il cofano (L'architettura tecnica)
Il sistema è progettato in moduli indipendenti e riutilizzabili:
1. **Analisi del viaggio (`trip`)**: legge i file GPX, ricampiona i punti a tempo costante e calcola metriche fisiche oggettive (velocità, quota, pendenza, stima di sforzo).
2. **Motore musicale (`music`)**: traduce le metriche del viaggio e le relazioni tra le voci in eventi, altezze, durate e dinamiche.
3. **Adattatori e trasporto (`adapters`, `sinks`)**: converte le frasi e i pattern nei protocolli di destinazione e li trasmette via OSC a bassa latenza.
4. **Esecuzione in Ableton Live (`m4l`)**: device dedicati Max for Live ricevono i comandi e pilotano synth e campionatori, mantenendo il clock audio rigorosamente ancorato al tempo musicale (BPM), indipendente dalla velocità di replay del viaggio.

---

## Per iniziare

- [Comandi rapidi e installazione](doc/COMANDI.md): come configurare l'ambiente, avviare il replay di una tappa e provare gli assetti musicali.
- [Le tappe e i percorsi modali](doc/TAPPE-E-PRESET.md): guida all'ascolto delle tappe (Firenze, Sabaudia, Peschici) e delle loro evoluzioni armoniche.
- [Architettura del sistema](doc/ARCHITETTURA.md): organizzazione dei package, flusso dati e contratti.
- [Indice completo della documentazione](doc/README.md).
