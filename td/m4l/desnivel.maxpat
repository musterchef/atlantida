{
	"patcher" : 	{
		"fileversion" : 1,
		"appversion" : 		{
			"major" : 9,
			"minor" : 0,
			"revision" : 10,
			"architecture" : "x64",
			"modernui" : 1
		}
,
		"classnamespace" : "box",
		"rect" : [ 100.0, 100.0, 640.0, 480.0 ],
		"bglocked" : 0,
		"openinpresentation" : 0,
		"default_fontsize" : 12.0,
		"default_fontface" : 0,
		"default_fontname" : "Arial",
		"gridonopen" : 1,
		"gridsize" : [ 15.0, 15.0 ],
		"gridsnaponopen" : 1,
		"objectsnaponopen" : 1,
		"statusbarvisible" : 2,
		"toolbarvisible" : 1,
		"lefttoolbarpinned" : 0,
		"toptoolbarpinned" : 0,
		"righttoolbarpinned" : 0,
		"bottomtoolbarpinned" : 0,
		"toolbars_unpinned_last_save" : 0,
		"tallnewobj" : 0,
		"boxanimatetime" : 200,
		"enablehscroll" : 1,
		"enablevscroll" : 1,
		"devicewidth" : 0.0,
		"description" : "",
		"digest" : "",
		"tags" : "",
		"style" : "",
		"subpatcher_template" : "",
		"assistshowspatchername" : 0,
		"boxes" : [
			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 50.0, 130.0, 22.0 ],
					"text" : "udpreceive 9001"
				}
			},
			{
				"box" : 				{
					"id" : "obj-2",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 5,
					"outlettype" : [ "", "", "", "", "" ],
					"patching_rect" : [ 30.0, 90.0, 540.0, 22.0 ],
					"text" : "OSC-route /desnivel/pitch /desnivel/scale /desnivel/density /desnivel/voice"
				}
			},
			{
				"box" : 				{
					"id" : "obj-3",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "bang" ],
					"patching_rect" : [ 130.0, 150.0, 70.0, 22.0 ]
,
					"text" : "loadbang"
				}
			},
			{
				"box" : 				{
					"id" : "obj-4",
					"maxclass" : "toggle",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "int" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 30.0, 150.0, 24.0, 24.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-5",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "bang" ],
					"patching_rect" : [ 30.0, 185.0, 100.0, 22.0 ],
					"text" : "metro 250"
				}
			},
			{
				"box" : 				{
					"id" : "obj-6",
					"maxclass" : "newobj",
					"numinlets" : 5,
					"numoutlets" : 4,
					"outlettype" : [ "", "", "", "" ],
					"patching_rect" : [ 30.0, 230.0, 165.0, 22.0 ],
					"saved_object_attributes" : 					{
						"filename" : "desnivel_notes.js",
						"parameter_enable" : 0
					}
,
					"text" : "js desnivel_notes.js"
				}
			},
			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "newobj",
					"numinlets" : 3,
					"numoutlets" : 2,
					"outlettype" : [ "float", "float" ],
					"patching_rect" : [ 30.0, 285.0, 80.0, 22.0 ],
					"text" : "makenote 100 250"
				}
			},
			{
				"box" : 				{
					"id" : "obj-8",
					"maxclass" : "newobj",
					"numinlets" : 3,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 340.0, 60.0, 22.0 ],
					"text" : "noteout"
				}
			},
			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "number",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 220.0, 230.0, 50.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"format" : 6,
					"id" : "obj-10",
					"maxclass" : "flonum",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 285.0, 230.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-11",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 20.0, 320.0, 22.0 ],
					"text" : "DESNIVEL — GPS to MIDI (TD port 9001)"
				}
			}
		],
		"lines" : [
			{ "patchline" : { "source" : [ "obj-1", 0 ], "destination" : [ "obj-2", 0 ] } },
			{ "patchline" : { "source" : [ "obj-2", 0 ], "destination" : [ "obj-6", 1 ] } },
			{ "patchline" : { "source" : [ "obj-2", 1 ], "destination" : [ "obj-6", 2 ] } },
			{ "patchline" : { "source" : [ "obj-2", 2 ], "destination" : [ "obj-6", 3 ] } },
			{ "patchline" : { "source" : [ "obj-2", 2 ], "destination" : [ "obj-10", 0 ] } },
			{ "patchline" : { "source" : [ "obj-2", 3 ], "destination" : [ "obj-6", 4 ] } },
			{ "patchline" : { "source" : [ "obj-3", 0 ], "destination" : [ "obj-4", 0 ] } },
			{ "patchline" : { "source" : [ "obj-4", 0 ], "destination" : [ "obj-5", 0 ] } },
			{ "patchline" : { "source" : [ "obj-5", 0 ], "destination" : [ "obj-6", 0 ] } },
			{ "patchline" : { "source" : [ "obj-6", 0 ], "destination" : [ "obj-7", 0 ] } },
			{ "patchline" : { "source" : [ "obj-6", 0 ], "destination" : [ "obj-9", 0 ] } },
			{ "patchline" : { "source" : [ "obj-6", 1 ], "destination" : [ "obj-7", 1 ] } },
			{ "patchline" : { "source" : [ "obj-6", 2 ], "destination" : [ "obj-7", 2 ] } },
			{ "patchline" : { "source" : [ "obj-6", 3 ], "destination" : [ "obj-8", 2 ] } },
			{ "patchline" : { "source" : [ "obj-7", 0 ], "destination" : [ "obj-8", 0 ] } },
			{ "patchline" : { "source" : [ "obj-7", 1 ], "destination" : [ "obj-8", 1 ] } }
		]
	}
}
