# DESNIVEL  
### del viatge al so, del terreny al gest audiovisual  

---

## I. Declaració

Un cos en moviment mesura el món.  
Cada metre de desnivell és un batec, cada corba una respiració.  
El traçat esdevé partitura, el paisatge es fa so, i la fatiga troba la seva pròpia harmonia en la vibració de l’aire.  

**Desnivel** és un projecte de traducció sensorial: un viatge real — de **Torí a Castel del Monte** — es transforma en una experiència audiovisual generativa.

El GPS registra, però el so interpreta.  
La trajectòria geogràfica esdevé gest sonor; la durada, matèria de composició.  
No es tracta de representar un recorregut, sinó d’**escoltar-ne la forma i veure’n la respiració**.

---

## II. Poètica del temps

### 1. Vuit hores de lentitud

Desnivel neix d’una experiència física i prolongada: **vuit hores de pedalada al dia**, un temps que flueix d’una manera densa, gairebé mineral.  

No és un projecte sobre la velocitat, sinó sobre la **durada** — sobre la capacitat del cos d’habitar el temps a través de la repetició i la resistència.

La lentitud no és monotonia: és **estratificació**.  
Cada respiració, cada variació de llum, cada petita corba esdevé una micro-modulació sonora i visual.  

Desnivel construeix la seva arquitectura sobre la **diferència interna de la lentitud**:

- El cos genera ritme  
- El terreny genera harmonia  
- El paisatge genera textura  
- La llum genera color  

Cada nivell evoluciona en una escala diferent: el batec en segons, el terreny en metres, el dia en hores.  

La música i la imatge neixen com una **lent d’augment del temps**, una manera de transformar la fatiga en presència i la durada en forma perceptiva.

---

## III. Arquitectura del sistema

### Entrada

- Traça GPX: latitud, longitud, altitud, velocitat, temps  
- Capes addicionals: vídeo (GoPro), dades meteorològiques, posició solar, mapes OSM  

### Processament

- Anàlisi numèrica → pendent, curvatura, variació altimètrica, entropia del terreny  
- Càlcul d’índexs semàntics → flow, dificultat, esforç, terreny, hora del dia  
- Conversió temporal mitjançant *time-warp* dinàmic basat en el pes narratiu dels punts  
- Normalització de dades per a mapeig audiovisual coherent  

### Sortida

- **Ableton Live** → traducció de les dades en paràmetres sonors (pitch, BPM, drive, reverberació, volum)  
- **TouchDesigner** → traducció de les mateixes dades en paràmetres visuals (geometria, llum, moviment, densitat, matèria)

El sistema actua com **un organisme relacional**, on cada variació geogràfica produeix una resposta coherent entre so i imatge en temps real.

---

## IV. Traducció sonora

Desnivel no genera música “a partir de les dades”, sinó que **reconeix música dins de les dades**.

| Dada            | Paràmetre sonor                       | Efecte perceptiu                           |
|-----------------|----------------------------------------|--------------------------------------------|
| Altitud        | Alçada de les notes / obertura filtre | Més alçada → més brillantor i tensió       |
| Curvatura      | Densitat rítmica / groove              | Corbes = microbeats, inestabilitat         |
| Velocitat      | BPM / pulsació                         | Ritme natural del cos                      |
| Dificultat     | Volum / saturació                      | Fatiga = presència sonora                  |
| Flow Index     | Reverberació / delay                   | Continuïtat = espai obert                  |
| Hora del dia   | Timbre / tonalitat                     | Llum = tonalitat harmònica                 |
| Esdeveniments  | Trigger / automatitzacions             | Clímax, drop, silencis                     |

---

## V. Traducció visual amb TouchDesigner

La visualització no il·lustra el paisatge: **en construeix una morfologia abstracta**.

TouchDesigner rep dades via OSC/MIDI i les converteix en sistemes visuals generatius.

| Dada            | Paràmetre visual                        | Comportament visual                          |
|-----------------|-------------------------------------------|-----------------------------------------------|
| Altitud        | Escala vertical / deformació geomètrica  | Més alçada → estructures més allargades      |
| Pendent        | Intensitat lumínica / contrast            | Pujades = augment de brillantor              |
| Curvatura      | Distorsió / fragmentació                  | Corbes = torsions i micro-fractures visuals  |
| Velocitat      | Velocitat de moviment / partícules       | Acceleració → major flux de matèria          |
| Flow Index     | Fluïdesa de shaders / suavitat transició | Continuïtat = superfícies orgàniques         |
| Hora del dia   | Paleta cromàtica                          | Matí fred → migdia neutre → capvespre càlid  |
| Dificultat     | Densitat de volum / gra                   | Fatiga = augment de matèria visual           |

### Sistemes visuals utilitzats

- **SOP networks** → deformació de malles segons altitud i pendent  
- **Particle systems** → representació del flux i moviment corporal  
- **Noise shaders** → textura del terreny i irregularitat  
- **Feedback loops** → persistència del paisatge en el temps  
- **Instancing** → multiplicació de punts GPS com a arquitectura abstracta  

El paisatge es converteix en una **escultura dinàmica**, que respira amb el ritme del cos.

---

## VI. Sincronització so–imatge

El sistema utilitza:

- OSC bidireccional per sincronització de paràmetres  
- Clock compartit per coherència temporal  
- Trigger visuals associats a esdeveniments sonors  
- Mòdul de “macro-states” per definir escenes narratives (ascens, plana, descens)

So i imatge no són paral·lels: són **interdependents**.  
Un canvi en la intensitat sonora pot reconfigurar la llum; una variació cromàtica pot influir en la densitat sonora.

---

## VII. Intervenció humana i performance

El performer actua com a **mediador sensible** entre sistema i públic.

Pot intervenir sobre:

- Macro-densitat visual  
- Saturació sonora  
- Velocitat global del time-warp  
- Transicions cromàtiques  
- Emergència o dissolució de capes  

La performance és un acte d’escolta expandida:  
no es tracta de controlar, sinó d’**acompanyar el viatge mentre es revela**.

---

## VIII. Dimensió espacial

Desnivel pot presentar-se en:

- Format escènic audiovisual (pantalla frontal)  
- Instal·lació immersiva amb projecció envoltant  
- Mapping arquitectònic adaptat a l’espai  
- Versió multicanal amb so espacialitzat  

La visualització pot adaptar-se a superfícies irregulars, convertint l’espai físic en extensió del relleu geogràfic.

---

## IX. Full de ruta

| Fase   | Descripció                                                     | Estat        |
|--------|----------------------------------------------------------------|-------------|
| Fase 1 | Disseny conceptual i definició de mapeigs                      | ✅ Completada |
| Fase 2 | Implementació Ableton ↔ TouchDesigner via OSC/MIDI             | 🔄 En curs    |
| Fase 3 | Desenvolupament sistema visual paramètric complet              | 🔄 En curs    |
| Fase 4 | Composició audiovisual (Torí → Castel del Monte)               | ⏳ Planificada |
| Fase 5 | Instal·lació / performance immersiva                           | 🌀 Expansió futura |

---

## X. Apèndix tècnic

Document de referència:  
`GPX_to_Sound_Design_Map_v0.1.md`

Extensions previstes:

- Diccionari JSON de mapeigs paramètrics  
- Sistema modular TouchDesigner amb components reutilitzables  
- Shader personalitzat basat en altitud i pendent  
- Motor de narrativa temporal (macro-escenes)  
- Sincronització amb vídeo enregistrat per correlació imatge-so  

---

**Autor:** Marco Musto — i la seva bici  
**Títol:** Desnivel  
**Versió:** 0.4  
**Data:** Novembre 2025  
**Llocs:** Torí → Castel del Monte  
