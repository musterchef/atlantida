// Controlla i parametri di MDD Snake per nome.
// Messaggi: "dump" (elenca i parametri), "refresh" (rilegge l'indice),
// "set <nome> <valore>" (imposta il parametro, limitato al suo range).
inlets = 1;
outlets = 0;

var DEVICE_MATCH = "snake";

var paramPaths = null;
var paramRanges = {};

function get1(api, prop) {
    var v = api.get(prop);
    return v.length ? v[0] : v;
}

function findSnake() {
    var liveSet = new LiveAPI(null, "live_set");
    var nTracks = liveSet.getcount("tracks");
    for (var t = 0; t < nTracks; t++) {
        var track = new LiveAPI(null, "live_set tracks " + t);
        var nDevices = track.getcount("devices");
        for (var d = 0; d < nDevices; d++) {
            var path = "live_set tracks " + t + " devices " + d;
            var name = String(get1(new LiveAPI(null, path), "name"));
            if (name.toLowerCase().indexOf(DEVICE_MATCH) !== -1) {
                return path;
            }
        }
    }
    return null;
}

function dump() {
    var devicePath = findSnake();
    if (devicePath === null) {
        post("Snake non trovato\n");
        return;
    }
    var n = new LiveAPI(null, devicePath).getcount("parameters");
    post("Snake: " + devicePath + ", " + n + " parametri\n");
    for (var i = 0; i < n; i++) {
        var p = new LiveAPI(null, devicePath + " parameters " + i);
        post(
            i + "\t" + get1(p, "name") +
            "\tmin=" + get1(p, "min") +
            "\tmax=" + get1(p, "max") +
            "\tquantized=" + get1(p, "is_quantized") +
            "\tvalue=" + get1(p, "value") + "\n"
        );
    }
}

// I nomi che compaiono piu' volte (Steps, Shapes...) sono esclusi.
function buildIndex() {
    paramPaths = {};
    paramRanges = {};
    var duplicates = {};
    var devicePath = findSnake();
    if (devicePath === null) {
        post("Snake non trovato\n");
        return;
    }
    var n = new LiveAPI(null, devicePath).getcount("parameters");
    for (var i = 0; i < n; i++) {
        var path = devicePath + " parameters " + i;
        var p = new LiveAPI(null, path);
        var name = String(get1(p, "name"));
        if (paramPaths[name] !== undefined || duplicates[name]) {
            delete paramPaths[name];
            delete paramRanges[name];
            duplicates[name] = true;
            continue;
        }
        paramPaths[name] = path;
        paramRanges[name] = [get1(p, "min"), get1(p, "max")];
    }
}

function refresh() {
    buildIndex();
    post("indice: " + Object.keys(paramPaths).length + " parametri univoci\n");
}

// Parametro 90: Shape Gates confermata in Live su Snake 3.2.3.
function testShape90(value) {
    var devicePath = findSnake();
    if (devicePath === null) {
        post("Snake non trovato\n");
        return;
    }
    if (new LiveAPI(null, devicePath).getcount("parameters") <= 90) {
        post("Shape test: indice 90 assente\n");
        return;
    }
    var p = new LiveAPI(null, devicePath + " parameters 90");
    if (String(get1(p, "name")) !== "Shapes" ||
        Number(get1(p, "min")) !== 0 || Number(get1(p, "max")) !== 13) {
        post("Shape test: parametro 90 diverso dal dump, invio annullato\n");
        return;
    }
    var v = Number(value);
    if (!isFinite(v) || Math.floor(v) !== v || v < 0 || v > 13) {
        post("Shape test: serve un intero 0..13\n");
        return;
    }
    var before = get1(p, "value");
    p.set("value", v);
    post("Shape test: parametro 90, precedente=" + before + ", richiesto=" + v + "\n");
}

function set(name, value) {
    if (name === "gate_shape" || name === "test_shape_90") {
        testShape90(value);
        return;
    }
    if (paramPaths === null) {
        buildIndex();
    }
    var path = paramPaths[name];
    if (path === undefined) {
        post("parametro sconosciuto o ambiguo: " + name + "\n");
        return;
    }
    var range = paramRanges[name];
    var v = Math.min(Math.max(Number(value), range[0]), range[1]);
    new LiveAPI(null, path).set("value", v);
}

// "get <nome>": scrive nella console il valore attuale del parametro.
function get(name) {
    if (paramPaths === null) {
        buildIndex();
    }
    var path = paramPaths[name];
    if (path === undefined) {
        post("parametro sconosciuto o ambiguo: " + name + "\n");
        return;
    }
    post(name + " = " + get1(new LiveAPI(null, path), "value") + "\n");
}
