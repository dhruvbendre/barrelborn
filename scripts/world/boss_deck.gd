extends Room
## The Gilded Gullet: checkpoint -> arena trigger -> Chainhook -> free Sol -> raise flag -> depart.
## Every step is a saved flag, so reloading at any point resumes correctly:
## a defeated boss never respawns, Sol stays recruited, and the departure is saved
## BEFORE its cutscene plays (skipping or quitting mid-cutscene loses nothing).

const COMPLETE := "res://scenes/ui/chapter_complete.tscn"

@onready var boss: Node = get_node_or_null("Level/Boss")
@onready var wall: StaticBody3D = $Level/ArenaWall
@onready var trigger: Area3D = $Level/ArenaTrigger
@onready var raise_flag: Interactable = $Level/RaiseFlag
@onready var cam: SideCamera = $Camera

var _departing := false
var _framing := false
var _base_distance := 10.5


## Boss framing: keep both fighters on screen, pulling the camera back as they separate.
func _physics_process(_d: float) -> void:
	if not _framing or not is_instance_valid(boss):
		return
	var mid: Vector3 = (player.global_position + boss.global_position) * 0.5
	cam.frame_override = Vector3(mid.x, 0.0, 0)
	var sep := absf(player.global_position.x - boss.global_position.x)
	cam.distance = lerpf(cam.distance, clampf(sep * 0.62 + 6.0, _base_distance, 17.0), 0.08)


func _ready() -> void:
	super()
	_base_distance = cam.distance
	_set_wall(false)
	trigger.body_entered.connect(_on_trigger)
	if boss:
		boss.defeated.connect(_on_boss_defeated)
	raise_flag.enabled = Game.has("crew_sol")
	Game.flag_granted.connect(_on_flag)
	if Game.has("boss_chainhook_defeated"):
		Game.set_objective("Talk to Sol" if not Game.has("crew_sol") else "Raise your flag at the mast")


func _on_trigger(b: Node3D) -> void:
	if not b is Player or Game.has("boss_chainhook_defeated") or boss == null or boss.state != Chainhook.State.WAIT:
		return
	_set_wall(true)
	_framing = true
	boss.start_fight()


func _on_boss_defeated() -> void:
	_set_wall(false)
	_framing = false
	cam.frame_override = null
	cam.distance = _base_distance
	Game.set_objective("Free Sol from the cage")


func _on_flag(id: String) -> void:
	match id:
		"crew_sol":
			raise_flag.enabled = true
			Game.toast.emit("Sol joined your crew!")
			Game.set_objective("Raise your flag at the mast")
			Game.save_game()
		"flag_raised":
			_depart()


func _set_wall(on: bool) -> void:
	wall.collision_layer = 1 if on else 0
	wall.visible = on


func _depart() -> void:
	if _departing:
		return
	_departing = true
	Game.grant("chapter1_complete")
	Game.set_objective("Set sail for the Broken Lighthouse")
	# Resume point after the chapter: back on Gullhaven's pier, everything earned kept.
	Game.checkpoint = {"room": Game.FIRST_ROOM, "x": 72.0, "y": 0.1}
	Game.save_game()
	player.control_enabled = false
	player.play_victory()
	await get_tree().create_timer(1.2).timeout
	# The Brine Dream sails off with its captain aboard.
	var ship := $Decor.get_children().filter(func(n: Node) -> bool: return n.name.begins_with("Brine"))
	player.visible = false
	cam.frame_override = Vector3(40, 0.0, 0)
	cam.limit_max.x = 80
	var tw := create_tween().set_parallel(true)
	for n in ship:
		tw.tween_property(n, "position:x", n.position.x + 30.0, 4.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	tw.tween_method(func(x: float) -> void: cam.frame_override = Vector3(x, 0.0, 0), 40.0, 62.0, 4.0)
	await get_tree().create_timer(4.2).timeout
	_finish()


func _unhandled_input(e: InputEvent) -> void:
	if _departing and (e.is_action_pressed("pause") or e.is_action_pressed("jump")):
		get_viewport().set_input_as_handled()
		_finish()


func _finish() -> void:
	if not is_inside_tree():
		return
	Game.set_paused(false)
	get_tree().change_scene_to_file(COMPLETE)
