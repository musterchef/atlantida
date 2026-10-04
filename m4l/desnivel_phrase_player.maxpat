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
      173.0,
      262.0,
      950.0,
      580.0
    ],
    "gridsize": [
      15.0,
      15.0
    ],
    "boxes": [
      {
        "box": {
          "id": "udp",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            20.0,
            30.0,
            220.0,
            22.0
          ],
          "saved_object_attributes": {
            "defer": 1
          },
          "text": "udpreceive 9002 @defer 1"
        }
      },
      {
        "box": {
          "id": "route",
          "maxclass": "newobj",
          "numinlets": 2,
          "numoutlets": 2,
          "outlettype": [
            "",
            ""
          ],
          "patching_rect": [
            20.0,
            65.0,
            310.0,
            22.0
          ],
          "text": "route /desnivel/v1/player/bass/phrase"
        }
      },
      {
        "box": {
          "id": "prep",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            20.0,
            100.0,
            180.0,
            22.0
          ],
          "text": "prepend phrase"
        }
      },
      {
        "box": {
          "id": "js",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 3,
          "outlettype": [
            "",
            "",
            ""
          ],
          "patching_rect": [
            20.0,
            150.0,
            240.0,
            22.0
          ],
          "saved_object_attributes": {
            "filename": "desnivel_phrase_player.js",
            "parameter_enable": 0
          },
          "text": "js desnivel_phrase_player.js"
        }
      },
      {
        "box": {
          "id": "unpack",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 3,
          "outlettype": [
            "int",
            "int",
            "float"
          ],
          "patching_rect": [
            20.0,
            205.0,
            180.0,
            22.0
          ],
          "text": "unpack i i f"
        }
      },
      {
        "box": {
          "id": "ticks",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            230.0,
            240.0,
            180.0,
            22.0
          ],
          "text": "append ticks"
        }
      },
      {
        "box": {
          "id": "pipe",
          "maxclass": "newobj",
          "numinlets": 3,
          "numoutlets": 2,
          "outlettype": [
            "",
            ""
          ],
          "patching_rect": [
            20.0,
            280.0,
            240.0,
            22.0
          ],
          "text": "pipe 0 0 0 @delaytime 0 ticks"
        }
      },
      {
        "box": {
          "id": "pack",
          "maxclass": "newobj",
          "numinlets": 2,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            20.0,
            325.0,
            180.0,
            22.0
          ],
          "text": "pack i i"
        }
      },
      {
        "box": {
          "id": "sentinel",
          "maxclass": "newobj",
          "numinlets": 2,
          "numoutlets": 2,
          "outlettype": [
            "",
            ""
          ],
          "patching_rect": [
            20.0,
            365.0,
            180.0,
            22.0
          ],
          "text": "route -1"
        }
      },
      {
        "box": {
          "id": "defer",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            20.0,
            405.0,
            180.0,
            22.0
          ],
          "text": "deferlow"
        }
      },
      {
        "box": {
          "id": "cycle",
          "maxclass": "message",
          "numinlets": 2,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            20.0,
            440.0,
            100.0,
            22.0
          ],
          "text": "cycle"
        }
      },
      {
        "box": {
          "id": "notes",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 2,
          "outlettype": [
            "int",
            "int"
          ],
          "patching_rect": [
            210.0,
            405.0,
            180.0,
            22.0
          ],
          "text": "unpack i i"
        }
      },
      {
        "box": {
          "id": "flush",
          "maxclass": "newobj",
          "numinlets": 2,
          "numoutlets": 2,
          "outlettype": [
            "int",
            "int"
          ],
          "patching_rect": [
            210.0,
            450.0,
            180.0,
            22.0
          ],
          "text": "flush"
        }
      },
      {
        "box": {
          "id": "out",
          "maxclass": "newobj",
          "numinlets": 3,
          "numoutlets": 0,
          "patching_rect": [
            210.0,
            495.0,
            180.0,
            22.0
          ],
          "text": "noteout"
        }
      },
      {
        "box": {
          "id": "controls",
          "maxclass": "newobj",
          "numinlets": 3,
          "numoutlets": 3,
          "outlettype": [
            "",
            "",
            ""
          ],
          "patching_rect": [
            370.0,
            205.0,
            180.0,
            22.0
          ],
          "text": "route clear flush"
        }
      },
      {
        "box": {
          "id": "clear",
          "maxclass": "message",
          "numinlets": 2,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            370.0,
            250.0,
            100.0,
            22.0
          ],
          "text": "clear"
        }
      },
      {
        "box": {
          "id": "bang",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 1,
          "outlettype": [
            "bang"
          ],
          "patching_rect": [
            480.0,
            250.0,
            180.0,
            22.0
          ],
          "text": "t b"
        }
      },
      {
        "box": {
          "id": "print",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 0,
          "patching_rect": [
            620.0,
            205.0,
            180.0,
            22.0
          ],
          "text": "print phrase_player"
        }
      },
      {
        "box": {
          "id": "load",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 3,
          "outlettype": [
            "bang",
            "int",
            "int"
          ],
          "patching_rect": [
            620.0,
            30.0,
            180.0,
            22.0
          ],
          "text": "live.thisdevice"
        }
      },
      {
        "box": {
          "id": "path",
          "maxclass": "message",
          "numinlets": 2,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            620.0,
            65.0,
            100.0,
            22.0
          ],
          "text": "path live_set"
        }
      },
      {
        "box": {
          "id": "livepath",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 3,
          "outlettype": [
            "",
            "",
            ""
          ],
          "patching_rect": [
            620.0,
            100.0,
            180.0,
            22.0
          ],
          "text": "live.path"
        }
      },
      {
        "box": {
          "id": "observer",
          "maxclass": "newobj",
          "numinlets": 2,
          "numoutlets": 2,
          "outlettype": [
            "",
            ""
          ],
          "patching_rect": [
            620.0,
            280.0,
            280.0,
            22.0
          ],
          "saved_object_attributes": {
            "_persistence": 0
          },
          "text": "live.observer is_playing"
        }
      },
      {
        "box": {
          "id": "running",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            620.0,
            325.0,
            180.0,
            22.0
          ],
          "text": "prepend running"
        }
      },
      {
        "box": {
          "id": "panic",
          "maxclass": "message",
          "numinlets": 2,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            370.0,
            365.0,
            100.0,
            22.0
          ],
          "text": "panic"
        }
      },
      {
        "box": {
          "id": "restart",
          "maxclass": "message",
          "numinlets": 2,
          "numoutlets": 1,
          "outlettype": [
            ""
          ],
          "patching_rect": [
            480.0,
            365.0,
            100.0,
            22.0
          ],
          "text": "restart"
        }
      },
      {
        "box": {
          "id": "close",
          "maxclass": "newobj",
          "numinlets": 1,
          "numoutlets": 1,
          "outlettype": [
            "bang"
          ],
          "patching_rect": [
            370.0,
            325.0,
            180.0,
            22.0
          ],
          "text": "closebang"
        }
      }
    ],
    "lines": [
      {
        "patchline": {
          "destination": [
            "flush",
            0
          ],
          "source": [
            "bang",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "pipe",
            0
          ],
          "source": [
            "clear",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "panic",
            0
          ],
          "source": [
            "close",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "bang",
            0
          ],
          "source": [
            "controls",
            1
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "clear",
            0
          ],
          "source": [
            "controls",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "js",
            0
          ],
          "source": [
            "cycle",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "cycle",
            0
          ],
          "source": [
            "defer",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "out",
            1
          ],
          "source": [
            "flush",
            1
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "out",
            0
          ],
          "source": [
            "flush",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "controls",
            0
          ],
          "source": [
            "js",
            1
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "print",
            0
          ],
          "source": [
            "js",
            2
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "unpack",
            0
          ],
          "source": [
            "js",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "observer",
            1
          ],
          "source": [
            "livepath",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "path",
            0
          ],
          "source": [
            "load",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "flush",
            1
          ],
          "source": [
            "notes",
            1
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "flush",
            0
          ],
          "source": [
            "notes",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "running",
            0
          ],
          "source": [
            "observer",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "sentinel",
            0
          ],
          "source": [
            "pack",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "js",
            0
          ],
          "source": [
            "panic",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "livepath",
            0
          ],
          "source": [
            "path",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "pack",
            1
          ],
          "source": [
            "pipe",
            1
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "pack",
            0
          ],
          "source": [
            "pipe",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "js",
            0
          ],
          "source": [
            "prep",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "js",
            0
          ],
          "source": [
            "restart",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "prep",
            0
          ],
          "source": [
            "route",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "js",
            0
          ],
          "order": 1,
          "source": [
            "running",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "defer",
            0
          ],
          "source": [
            "sentinel",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "notes",
            0
          ],
          "source": [
            "sentinel",
            1
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "pipe",
            2
          ],
          "source": [
            "ticks",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "route",
            0
          ],
          "source": [
            "udp",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "pipe",
            1
          ],
          "source": [
            "unpack",
            1
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "pipe",
            0
          ],
          "source": [
            "unpack",
            0
          ]
        }
      },
      {
        "patchline": {
          "destination": [
            "ticks",
            0
          ],
          "source": [
            "unpack",
            2
          ]
        }
      }
    ],
    "dependency_cache": [
      {
        "name": "desnivel_phrase_player.js",
        "bootpath": "~/ogni-tanto-programmo/desnivel/m4l",
        "patcherrelativepath": ".",
        "type": "TEXT",
        "implicit": 1
      }
    ],
    "autosave": 0,
    "oscreceiveudpport": 0
  }
}
