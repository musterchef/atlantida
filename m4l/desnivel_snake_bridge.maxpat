{
  "patcher": {
    "fileversion": 1,
    "appversion": {
      "major": 9,
      "minor": 0,
      "revision": 10,
      "architecture": "x64",
      "modernui": 1
    },
    "classnamespace": "box",
    "rect": [
      100,
      100,
      720,
      570
    ],
    "openinpresentation": 0,
    "default_fontsize": 12,
    "default_fontname": "Arial",
    "boxes": [
      {
        "box": {
          "id": "title",
          "maxclass": "comment",
          "patching_rect": [
            25,
            15,
            650,
            25
          ],
          "fontsize": 18,
          "text": "DESNIVEL / Snake bridge — 01: ricezione OSC"
        }
      },
      {
        "box": {
          "id": "intro",
          "maxclass": "comment",
          "patching_rect": [
            25,
            48,
            660,
            40
          ],
          "text": "Mostra dati neutri del viaggio. Il controllo di Snake verra aggiunto qui nel passo successivo."
        }
      },
      {
        "box": {
          "id": "portlabel",
          "maxclass": "comment",
          "patching_rect": [
            25,
            100,
            140,
            22
          ],
          "text": "Porta OSC (default 9000)"
        }
      },
      {
        "box": {
          "id": "port",
          "maxclass": "number",
          "patching_rect": [
            190,
            100,
            80,
            22
          ],
          "minimum": 1024,
          "maximum": 65535
        }
      },
      {
        "box": {
          "id": "init",
          "maxclass": "newobj",
          "patching_rect": [
            300,
            100,
            100,
            22
          ],
          "text": "loadmess 9000"
        }
      },
      {
        "box": {
          "id": "prepend",
          "maxclass": "newobj",
          "patching_rect": [
            190,
            140,
            90,
            22
          ],
          "text": "prepend port"
        }
      },
      {
        "box": {
          "id": "udp",
          "maxclass": "newobj",
          "patching_rect": [
            190,
            185,
            210,
            22
          ],
          "text": "udpreceive 9000 @defer 1"
        }
      },
      {
        "box": {
          "id": "route",
          "maxclass": "newobj",
          "patching_rect": [
            190,
            230,
            350,
            22
          ],
          "text": "route /desnivel/v1/trip/metric/elevation_m"
        }
      },
      {
        "box": {
          "id": "unpack",
          "maxclass": "newobj",
          "patching_rect": [
            190,
            285,
            90,
            22
          ],
          "text": "unpack f f"
        }
      },
      {
        "box": {
          "id": "time",
          "maxclass": "flonum",
          "patching_rect": [
            190,
            340,
            110,
            22
          ],
          "ignoreclick": 1
        }
      },
      {
        "box": {
          "id": "value",
          "maxclass": "flonum",
          "patching_rect": [
            370,
            340,
            110,
            22
          ],
          "ignoreclick": 1
        }
      },
      {
        "box": {
          "id": "tl",
          "maxclass": "comment",
          "patching_rect": [
            190,
            370,
            160,
            22
          ],
          "text": "Tempo viaggio (secondi)"
        }
      },
      {
        "box": {
          "id": "vl",
          "maxclass": "comment",
          "patching_rect": [
            370,
            370,
            140,
            22
          ],
          "text": "Quota (metri)"
        }
      },
      {
        "box": {
          "id": "testlabel",
          "maxclass": "comment",
          "patching_rect": [
            25,
            420,
            630,
            22
          ],
          "text": "Test locale: clicca il messaggio. Deve mostrare tempo 12.5 e quota 345. Non prova la rete."
        }
      },
      {
        "box": {
          "id": "test",
          "maxclass": "message",
          "patching_rect": [
            25,
            455,
            455,
            22
          ],
          "text": "/desnivel/v1/trip/metric/elevation_m 12.5 345."
        }
      },
      {
        "box": {
          "id": "note",
          "maxclass": "comment",
          "patching_rect": [
            25,
            500,
            650,
            40
          ],
          "text": "Altre metriche ignorate. I display mantengono l’ultimo valore: timeout e mapping non ancora implementati."
        }
      },
      {
        "box": {
          "id": "mi",
          "maxclass": "newobj",
          "patching_rect": [
            590,
            185,
            55,
            22
          ],
          "text": "midiin"
        }
      },
      {
        "box": {
          "id": "mo",
          "maxclass": "newobj",
          "patching_rect": [
            590,
            230,
            55,
            22
          ],
          "text": "midiout"
        }
      },
      {
        "box": {
          "id": "midilabel",
          "maxclass": "comment",
          "patching_rect": [
            560,
            270,
            120,
            55
          ],
          "text": "MIDI pass-through per uso in un Max MIDI Effect."
        }
      }
    ],
    "lines": [
      {
        "patchline": {
          "source": [
            "init",
            0
          ],
          "destination": [
            "port",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "port",
            0
          ],
          "destination": [
            "prepend",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "prepend",
            0
          ],
          "destination": [
            "udp",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "udp",
            0
          ],
          "destination": [
            "route",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "route",
            0
          ],
          "destination": [
            "unpack",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "unpack",
            0
          ],
          "destination": [
            "time",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "unpack",
            1
          ],
          "destination": [
            "value",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "test",
            0
          ],
          "destination": [
            "route",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "mi",
            0
          ],
          "destination": [
            "mo",
            0
          ]
        }
      }
    ]
  }
}
