{
  "patcher": {
    "fileversion": 1,
    "appversion": {
      "major": 8,
      "minor": 1,
      "revision": 2,
      "architecture": "x64",
      "modernui": 1
    },
    "classnamespace": "box",
    "rect": [
      0,
      0,
      1300,
      1020
    ],
    "openinpresentation": 1,
    "devicewidth": 650,
    "default_fontsize": 12,
    "boxes": [
      {
        "box": {
          "id": "title",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "fontsize": 14,
          "text": "DESNIVEL \u00b7 VOICE",
          "presentation": 1,
          "presentation_rect": [
            10,
            4,
            180,
            22
          ]
        }
      },
      {
        "box": {
          "id": "voice_label",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "Part",
          "presentation": 1,
          "presentation_rect": [
            10,
            35,
            35,
            20
          ]
        }
      },
      {
        "box": {
          "id": "voice_id",
          "maxclass": "textedit",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "varname": "voice_id",
          "outputmode": 1,
          "keymode": 1,
          "text": "voice_01",
          "presentation": 1,
          "presentation_rect": [
            48,
            34,
            145,
            23
          ]
        }
      },
      {
        "box": {
          "id": "persist",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            650,
            190,
            22
          ],
          "text": "autopattr @autoname 0"
        }
      },
      {
        "box": {
          "id": "listen_label",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "Receive",
          "presentation": 1,
          "presentation_rect": [
            205,
            35,
            55,
            20
          ]
        }
      },
      {
        "box": {
          "id": "receive_port",
          "maxclass": "live.numbox",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "varname": "receive_port",
          "parameter_enable": 1,
          "presentation": 1,
          "presentation_rect": [
            263,
            35,
            62,
            20
          ],
          "saved_attribute_attributes": {
            "valueof": {
              "parameter_longname": "Receive_Port",
              "parameter_shortname": "Receive_Port",
              "parameter_type": 0,
              "parameter_mmin": 1024,
              "parameter_mmax": 65535,
              "parameter_initial": [
                9101
              ],
              "parameter_initial_enable": 1,
              "parameter_unitstyle": 0
            }
          }
        }
      },
      {
        "box": {
          "id": "server_label",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "Python",
          "presentation": 1,
          "presentation_rect": [
            337,
            35,
            50,
            20
          ]
        }
      },
      {
        "box": {
          "id": "server_port",
          "maxclass": "live.numbox",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "varname": "server_port",
          "parameter_enable": 1,
          "presentation": 1,
          "presentation_rect": [
            391,
            35,
            62,
            20
          ],
          "saved_attribute_attributes": {
            "valueof": {
              "parameter_longname": "Python_Port",
              "parameter_shortname": "Python_Port",
              "parameter_type": 0,
              "parameter_mmin": 1024,
              "parameter_mmax": 65535,
              "parameter_initial": [
                9006
              ],
              "parameter_initial_enable": 1,
              "parameter_unitstyle": 0
            }
          }
        }
      },
      {
        "box": {
          "id": "connect_button",
          "maxclass": "message",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "Connect",
          "presentation": 1,
          "presentation_rect": [
            470,
            34,
            78,
            23
          ]
        }
      },
      {
        "box": {
          "id": "panic_button",
          "maxclass": "message",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "panic",
          "presentation": 1,
          "presentation_rect": [
            562,
            34,
            76,
            23
          ]
        }
      },
      {
        "box": {
          "id": "role_label",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "Role",
          "presentation": 1,
          "presentation_rect": [
            10,
            69,
            35,
            20
          ]
        }
      },
      {
        "box": {
          "id": "role_display",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "varname": "role_display",
          "text": "Unassigned",
          "presentation": 1,
          "presentation_rect": [
            200,
            4,
            438,
            22
          ]
        }
      },
      {
        "box": {
          "id": "preset_label",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "Preset",
          "presentation": 1,
          "presentation_rect": [
            263,
            69,
            50,
            20
          ]
        }
      },
      {
        "box": {
          "id": "preset_menu",
          "maxclass": "umenu",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "varname": "preset_menu",
          "items": [],
          "presentation": 1,
          "presentation_rect": [
            317,
            68,
            321,
            23
          ]
        }
      },
      {
        "box": {
          "id": "parameter_label",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "Parameter",
          "presentation": 1,
          "presentation_rect": [
            10,
            102,
            72,
            20
          ]
        }
      },
      {
        "box": {
          "id": "parameter_menu",
          "maxclass": "umenu",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "varname": "parameter_menu",
          "items": [],
          "presentation": 1,
          "presentation_rect": [
            86,
            101,
            190,
            23
          ]
        }
      },
      {
        "box": {
          "id": "parameter_value",
          "maxclass": "flonum",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "varname": "parameter_value",
          "format": 6,
          "presentation": 1,
          "presentation_rect": [
            288,
            102,
            82,
            22
          ]
        }
      },
      {
        "box": {
          "id": "range_display",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "varname": "range_display",
          "text": "No controls",
          "presentation": 1,
          "presentation_rect": [
            385,
            103,
            253,
            20
          ]
        }
      },
      {
        "box": {
          "id": "status",
          "maxclass": "comment",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "Disconnected",
          "presentation": 1,
          "presentation_rect": [
            10,
            140,
            628,
            20
          ]
        }
      },
      {
        "box": {
          "id": "receive",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            300,
            190,
            22
          ],
          "text": "udpreceive 9101 @defer 1"
        }
      },
      {
        "box": {
          "id": "route",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            340,
            300,
            22
          ],
          "text": "route /desnivel/v1/voice/message"
        }
      },
      {
        "box": {
          "id": "incoming",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            380,
            190,
            22
          ],
          "text": "t l b"
        }
      },
      {
        "box": {
          "id": "when",
          "maxclass": "newobj",
          "patching_rect": [
            240,
            420,
            190,
            22
          ],
          "text": "when"
        }
      },
      {
        "box": {
          "id": "now",
          "maxclass": "newobj",
          "patching_rect": [
            240,
            460,
            190,
            22
          ],
          "text": "prepend now"
        }
      },
      {
        "box": {
          "id": "receive_prefix",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            460,
            190,
            22
          ],
          "text": "prepend receive"
        }
      },
      {
        "box": {
          "id": "interface",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            500,
            190,
            22
          ],
          "text": "js desnivel_voice.js"
        }
      },
      {
        "box": {
          "id": "send",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            545,
            190,
            22
          ],
          "text": "udpsend 127.0.0.1 9006"
        }
      },
      {
        "box": {
          "id": "player",
          "maxclass": "newobj",
          "patching_rect": [
            460,
            500,
            300,
            22
          ],
          "text": "js desnivel_transport_player.js"
        }
      },
      {
        "box": {
          "id": "notes_unpack",
          "maxclass": "newobj",
          "patching_rect": [
            460,
            550,
            190,
            22
          ],
          "varname": "notes_unpack",
          "text": "unpack 0 0"
        }
      },
      {
        "box": {
          "id": "notes_flush",
          "maxclass": "newobj",
          "patching_rect": [
            460,
            590,
            190,
            22
          ],
          "varname": "notes_flush",
          "text": "flush"
        }
      },
      {
        "box": {
          "id": "midi_pack",
          "maxclass": "newobj",
          "patching_rect": [
            460,
            630,
            190,
            22
          ],
          "text": "pack 0 0"
        }
      },
      {
        "box": {
          "id": "midi_format",
          "maxclass": "newobj",
          "patching_rect": [
            460,
            670,
            190,
            22
          ],
          "text": "midiformat"
        }
      },
      {
        "box": {
          "id": "midi_out",
          "maxclass": "newobj",
          "patching_rect": [
            460,
            710,
            190,
            22
          ],
          "text": "midiout"
        }
      },
      {
        "box": {
          "id": "status_prefix",
          "maxclass": "newobj",
          "patching_rect": [
            250,
            545,
            190,
            22
          ],
          "text": "prepend set"
        }
      },
      {
        "box": {
          "id": "clock_metro",
          "maxclass": "newobj",
          "patching_rect": [
            900,
            300,
            190,
            22
          ],
          "text": "qmetro 125"
        }
      },
      {
        "box": {
          "id": "clock_trigger",
          "maxclass": "newobj",
          "patching_rect": [
            900,
            340,
            190,
            22
          ],
          "text": "t b b"
        }
      },
      {
        "box": {
          "id": "clock_transport",
          "maxclass": "newobj",
          "patching_rect": [
            1050,
            380,
            190,
            22
          ],
          "text": "transport"
        }
      },
      {
        "box": {
          "id": "clock_time",
          "maxclass": "newobj",
          "patching_rect": [
            900,
            420,
            190,
            22
          ],
          "text": "f"
        }
      },
      {
        "box": {
          "id": "clock_pack",
          "maxclass": "newobj",
          "patching_rect": [
            900,
            460,
            190,
            22
          ],
          "text": "pack 0. 0"
        }
      },
      {
        "box": {
          "id": "clock_prefix",
          "maxclass": "newobj",
          "patching_rect": [
            900,
            500,
            190,
            22
          ],
          "text": "prepend clock"
        }
      },
      {
        "box": {
          "id": "ready",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            700,
            190,
            22
          ],
          "text": "live.thisdevice"
        }
      },
      {
        "box": {
          "id": "start_clock",
          "maxclass": "message",
          "patching_rect": [
            240,
            700,
            190,
            22
          ],
          "text": "1"
        }
      },
      {
        "box": {
          "id": "path",
          "maxclass": "message",
          "patching_rect": [
            20,
            740,
            190,
            22
          ],
          "text": "path live_set"
        }
      },
      {
        "box": {
          "id": "resolve",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            780,
            190,
            22
          ],
          "text": "live.path"
        }
      },
      {
        "box": {
          "id": "observe",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            820,
            190,
            22
          ],
          "text": "live.observer is_playing"
        }
      },
      {
        "box": {
          "id": "running",
          "maxclass": "newobj",
          "patching_rect": [
            20,
            860,
            190,
            22
          ],
          "text": "prepend running"
        }
      },
      {
        "box": {
          "id": "heartbeat_metro",
          "maxclass": "newobj",
          "patching_rect": [
            240,
            740,
            190,
            22
          ],
          "text": "qmetro 1000"
        }
      },
      {
        "box": {
          "id": "heartbeat",
          "maxclass": "message",
          "patching_rect": [
            240,
            780,
            190,
            22
          ],
          "text": "heartbeat"
        }
      },
      {
        "box": {
          "id": "voice_route",
          "maxclass": "newobj",
          "patching_rect": [
            780,
            600,
            220,
            22
          ],
          "text": "route text"
        }
      },
      {
        "box": {
          "id": "voice_prefix",
          "maxclass": "newobj",
          "patching_rect": [
            1030,
            600,
            220,
            22
          ],
          "text": "prepend voice"
        }
      },
      {
        "box": {
          "id": "port_prefix",
          "maxclass": "newobj",
          "patching_rect": [
            780,
            655,
            220,
            22
          ],
          "text": "prepend receiveport"
        }
      },
      {
        "box": {
          "id": "port_set",
          "maxclass": "newobj",
          "patching_rect": [
            1030,
            655,
            220,
            22
          ],
          "text": "prepend port"
        }
      },
      {
        "box": {
          "id": "server_set",
          "maxclass": "newobj",
          "patching_rect": [
            780,
            710,
            220,
            22
          ],
          "text": "prepend port"
        }
      },
      {
        "box": {
          "id": "server_prefix",
          "maxclass": "newobj",
          "patching_rect": [
            1030,
            710,
            220,
            22
          ],
          "text": "prepend backendport"
        }
      },
      {
        "box": {
          "id": "preset_prefix",
          "maxclass": "newobj",
          "patching_rect": [
            780,
            765,
            220,
            22
          ],
          "text": "prepend preset"
        }
      },
      {
        "box": {
          "id": "parameter_prefix",
          "maxclass": "newobj",
          "patching_rect": [
            1030,
            765,
            220,
            22
          ],
          "text": "prepend parameter"
        }
      },
      {
        "box": {
          "id": "value_prefix",
          "maxclass": "newobj",
          "patching_rect": [
            780,
            820,
            220,
            22
          ],
          "text": "prepend value"
        }
      },
      {
        "box": {
          "id": "connect_trigger",
          "maxclass": "newobj",
          "patching_rect": [
            1030,
            820,
            220,
            22
          ],
          "text": "t b b b b"
        }
      },
      {
        "box": {
          "id": "connect_message",
          "maxclass": "message",
          "patching_rect": [
            780,
            875,
            220,
            22
          ],
          "text": "connect"
        }
      },
      {
        "box": {
          "id": "role_menu",
          "maxclass": "umenu",
          "varname": "role_menu",
          "patching_rect": [
            800,
            950,
            220,
            22
          ],
          "presentation": 1,
          "presentation_rect": [
            48,
            68,
            190,
            23
          ],
          "items": []
        }
      },
      {
        "box": {
          "id": "role_prefix",
          "maxclass": "newobj",
          "text": "prepend choose_role",
          "patching_rect": [
            1050,
            950,
            190,
            22
          ]
        }
      }
    ],
    "lines": [
      {
        "patchline": {
          "source": [
            "receive",
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
            "incoming",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "incoming",
            0
          ],
          "destination": [
            "receive_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "receive_prefix",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "now",
            0
          ],
          "destination": [
            "player",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "midi_pack",
            0
          ],
          "destination": [
            "midi_format",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "midi_format",
            0
          ],
          "destination": [
            "midi_out",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "incoming",
            1
          ],
          "destination": [
            "when",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "when",
            1
          ],
          "destination": [
            "now",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "interface",
            0
          ],
          "destination": [
            "send",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "interface",
            1
          ],
          "destination": [
            "player",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "interface",
            2
          ],
          "destination": [
            "status_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "status_prefix",
            0
          ],
          "destination": [
            "status",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "player",
            0
          ],
          "destination": [
            "status_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "notes_unpack",
            0
          ],
          "destination": [
            "notes_flush",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "notes_unpack",
            1
          ],
          "destination": [
            "notes_flush",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "notes_flush",
            0
          ],
          "destination": [
            "midi_pack",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "notes_flush",
            1
          ],
          "destination": [
            "midi_pack",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "clock_metro",
            0
          ],
          "destination": [
            "clock_trigger",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "clock_trigger",
            0
          ],
          "destination": [
            "clock_time",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "clock_time",
            0
          ],
          "destination": [
            "clock_pack",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "clock_pack",
            0
          ],
          "destination": [
            "clock_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "clock_prefix",
            0
          ],
          "destination": [
            "player",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "ready",
            0
          ],
          "destination": [
            "path",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "path",
            0
          ],
          "destination": [
            "resolve",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "observe",
            0
          ],
          "destination": [
            "running",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "running",
            0
          ],
          "destination": [
            "player",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "ready",
            0
          ],
          "destination": [
            "start_clock",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "start_clock",
            0
          ],
          "destination": [
            "clock_metro",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "start_clock",
            0
          ],
          "destination": [
            "heartbeat_metro",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "heartbeat_metro",
            0
          ],
          "destination": [
            "heartbeat",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "heartbeat",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "clock_trigger",
            1
          ],
          "destination": [
            "clock_transport",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "clock_transport",
            7
          ],
          "destination": [
            "clock_time",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "clock_transport",
            6
          ],
          "destination": [
            "clock_pack",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "resolve",
            0
          ],
          "destination": [
            "observe",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "voice_id",
            0
          ],
          "destination": [
            "voice_route",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "voice_route",
            0
          ],
          "destination": [
            "voice_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "voice_prefix",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "receive_port",
            0
          ],
          "destination": [
            "port_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "port_prefix",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "receive_port",
            0
          ],
          "destination": [
            "port_set",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "port_set",
            0
          ],
          "destination": [
            "receive",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "server_port",
            0
          ],
          "destination": [
            "server_set",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "server_set",
            0
          ],
          "destination": [
            "send",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "server_port",
            0
          ],
          "destination": [
            "server_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "server_prefix",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "preset_menu",
            0
          ],
          "destination": [
            "preset_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "preset_prefix",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "parameter_menu",
            0
          ],
          "destination": [
            "parameter_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "parameter_prefix",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "parameter_value",
            0
          ],
          "destination": [
            "value_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "value_prefix",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "connect_button",
            0
          ],
          "destination": [
            "connect_trigger",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "connect_message",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "panic_button",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "connect_trigger",
            3
          ],
          "destination": [
            "receive_port",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "connect_trigger",
            2
          ],
          "destination": [
            "server_port",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "connect_trigger",
            1
          ],
          "destination": [
            "voice_id",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "connect_trigger",
            0
          ],
          "destination": [
            "connect_message",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "clock_prefix",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "role_menu",
            0
          ],
          "destination": [
            "role_prefix",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "role_prefix",
            0
          ],
          "destination": [
            "interface",
            0
          ]
        }
      }
    ],
    "parameters": {
      "receive_port": [
        "Receive_Port",
        "Receive_Port",
        0
      ],
      "server_port": [
        "Python_Port",
        "Python_Port",
        0
      ]
    },
    "dependency_cache": [
      {
        "name": "desnivel_voice.js",
        "type": "TEXT",
        "implicit": 1
      },
      {
        "name": "desnivel_transport_player.js",
        "type": "TEXT",
        "implicit": 1
      }
    ],
    "autosave": 0,
    "latency": 0
  }
}
