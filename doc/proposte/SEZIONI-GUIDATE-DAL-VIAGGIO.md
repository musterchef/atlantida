# Sezioni guidate dal viaggio

Stato: separazione delle responsabilità approvata; analisi del profilo e
raggruppamento delle zone in macrosezioni e assegnazione degli assetti musicali
implementati. Variazioni musicali interne alle macrosezioni da definire.

L'obiettivo è rendere percepibile l'evoluzione del viaggio nella composizione,
mantenendo disponibile la modalità con sezioni manuali.

La struttura concordata separa:

1. Analisi neutra del percorso: zone, posizione e misure che le motivano.
2. Assegnazioni musicali configurabili in JSON: interpretazione delle zone
   mediante voci, ruoli e parametri effettivamente supportati dai generatori.
3. Esecuzione: Director e Coordinator applicano le assegnazioni e coordinano
   le voci attraverso le interfacce musicali generiche.

L'[analisi disponibile](../ANALISI-PERCORSO.md) classifica il profilo per
pendenza e persistenza. Un passaggio separato raggruppa le zone adiacenti
secondo famiglie configurabili; il report mostra macrosezioni e dettaglio.
Il [collegamento alla sessione musicale](../SESSIONE-MULTIVOCE.md) assegna un
assetto configurato a ciascuna famiglia. L'eventuale assorbimento di brevi interruzioni, il riconoscimento di
scollinamenti e altri eventi restano da definire.

Gli assetti delle macrosezioni sono definiti in un JSON separato e applicati
alla prossima finestra da pianificare. La configurazione d'ascolto fornita
propone comportamenti differenti per le famiglie; tali scelte sono modificabili.

La direzione concordata distingue un assetto musicale della macrosezione
(voci, ruoli e impostazioni di base) dalle variazioni interne associate alle
fasce originali. Il primo livello è operativo. Per le variazioni interne sono
ancora da definire precedenza delle impostazioni, ripristino dei valori e
tempi delle transizioni. I cambi locali non devono
implicare automaticamente un cambio di organico o il riavvio della frase.
