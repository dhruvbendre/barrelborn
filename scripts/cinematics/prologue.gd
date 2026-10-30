extends Node3D
## Prologue: a storm at sea, a barrel, a kid with an enormous dream.
## Watched or skipped (Esc / Start / the Skip button), it ends in _finish(), which sets
## exactly the same story state and drops the player at the safe harbor arrival point.

const HARBOR_SPAWN := "Arrival"

@onready var barrel: Node3D = $Barrel
@onready var cam: Camera3D = $Camera
@onready var sun: DirectionalLight3D = $Sun
@onready var env: WorldEnvironment = $WorldEnvironment
@onready var island: Node3D = $Island
@onready var skip_btn: Button = %Skip

var _t := 0.0
var _done := false
var _calm := 0.0  # 0 = storm, 1 = calm morning


func _ready() -> void:
	skip_btn.pressed.connect(_finish)
	var anim := barrel.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if anim and anim.has_animation("idle"):
		anim.get_animation("idle").loop_mode = Animation.LOOP_LINEAR
		anim.play("idle")
	_play()


func _process(delta: float) -> void:
	_t += delta
	var storm := 1.0 - _calm
	# Bob and roll on the swell; harder in the storm.
	barrel.position.y = sin(_t * 1.7) * (0.35 * storm + 0.08) - 0.25
	barrel.rotation.z = sin(_t * 1.3) * (0.25 * storm + 0.04)
	barrel.rotation.x = sin(_t * 0.9 + 1.0) * 0.12 * storm
	# Lightning: brief flashes while stormy.
	var flash := storm > 0.5 and fmod(_t, 3.7) < 0.08
	sun.light_energy = (2.6 if flash else lerpf(0.35, 1.0, _calm))
	var e := env.environment
	e.background_color = Color("1d2f4a").lerp(Color("8fd0f0"), _calm)
	e.ambient_light_color = Color("3c5873").lerp(Color("cfe9f2"), _calm)
	e.fog_light_color = e.ambient_light_color
	cam.position.z = lerpf(9.0, 7.0, minf(_t / 12.0, 1.0))


func _play() -> void:
	await get_tree().create_timer(1.6).timeout
	if _done:
		return
	await Game.say("Kito", PackedStringArray([
		"Day nine in the barrel. Still floating. Still alive!",
		"No ship, no crew, no map... yet.",
		"Someday I'll have a ship, a crew who'd follow me anywhere - and the whole sea will call me PIRATE KING!",
	]))
	if _done:
		return
	# The storm breaks; an island rises out of the morning haze.
	var tw := create_tween().set_parallel(true)
	tw.tween_property(self, "_calm", 1.0, 3.0)
	tw.tween_property(island, "position:x", 9.0, 5.0).set_trans(Tween.TRANS_SINE)
	await get_tree().create_timer(3.5).timeout
	if _done:
		return
	await Game.say("Kito", PackedStringArray(["...Land? LAND! Hold on, barrel!"]))
	_finish()


func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("pause"):
		get_viewport().set_input_as_handled()
		_finish()


func _finish() -> void:
	if _done:
		return
	_done = true
	if Game.in_dialogue:
		Game.dialogue_finished.emit()  # close any open box so nothing waits forever
	Game.grant("story_prologue_seen")
	Game.set_objective("Explore Gullhaven harbor")
	Game.checkpoint = {"room": Game.FIRST_ROOM, "x": 1.5, "y": 0.1}
	Game.save_game()
	Game.change_room(Game.FIRST_ROOM, HARBOR_SPAWN)
