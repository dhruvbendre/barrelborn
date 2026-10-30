extends Node
## TEMPORARY procedural sound effects, synthesized at startup (no external files, no licensing
## risk). Replace each id with an authored AudioStream later; call sites stay `Sfx.play(id)`.

const RATE := 22050
const VOICES := 8

## id -> [kind, duration, start_hz, end_hz, volume]
const DEFS := {
	"swing": ["noise_sweep", 0.12, 2400.0, 600.0, 0.35],
	"hit": ["thump", 0.10, 220.0, 70.0, 0.8],
	"hurt": ["square", 0.18, 520.0, 180.0, 0.35],
	"jump": ["sine", 0.10, 300.0, 620.0, 0.25],
	"land": ["thump", 0.06, 140.0, 60.0, 0.4],
	"break": ["noise_sweep", 0.22, 900.0, 120.0, 0.6],
	"coin": ["sine", 0.12, 1320.0, 1760.0, 0.3],
	"checkpoint": ["sine", 0.35, 440.0, 880.0, 0.35],
	"enemy_windup": ["square", 0.25, 160.0, 320.0, 0.2],
	"enemy_die": ["square", 0.35, 300.0, 60.0, 0.35],
	"ui": ["sine", 0.05, 900.0, 900.0, 0.2],
}

var music_volume := 0.8
var sfx_volume := 1.0
var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for id in DEFS:
		_streams[id] = _synth(DEFS[id])
	for i in VOICES:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)


func play(id: String, pitch_jitter := 0.08) -> void:
	if not _streams.has(id):
		return
	var p := _players[_next]
	_next = (_next + 1) % VOICES
	p.stream = _streams[id]
	p.volume_db = linear_to_db(maxf(sfx_volume, 0.0001))
	p.pitch_scale = 1.0 + randf_range(-pitch_jitter, pitch_jitter)
	p.play()


func _synth(def: Array) -> AudioStreamWAV:
	var kind: String = def[0]
	var n := int(RATE * float(def[1]))
	var data := PackedByteArray()
	data.resize(n * 2)
	var phase := 0.0
	var lp := 0.0
	for i in n:
		var k := float(i) / n
		var hz := lerpf(def[2], def[3], k)
		phase += hz / RATE
		var env := (1.0 - k) * (1.0 - k) * minf(1.0, i / 40.0)
		var s := 0.0
		match kind:
			"sine": s = sin(TAU * phase)
			"square": s = 1.0 if fmod(phase, 1.0) < 0.5 else -1.0
			"thump": s = sin(TAU * phase) + randf_range(-0.3, 0.3) * (1.0 - k)
			"noise_sweep":
				lp = lerpf(lp, randf_range(-1.0, 1.0), clampf(hz / RATE * 4.0, 0.02, 1.0))
				s = lp * 2.0
		data.encode_s16(i * 2, int(clampf(s * env * float(def[4]), -1.0, 1.0) * 32000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.data = data
	return w
