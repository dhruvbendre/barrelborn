extends Node
## Overall game state: progression, checkpoint, save/load, room changes, hit-stop.
## UI listens to the signals; nothing here scans the scene tree.

signal health_changed(hp: int, max_hp: int)
signal spirit_changed(sp: float, max_sp: float)
signal coins_changed(coins: int)
signal objective_changed(text: String)
signal toast(text: String)
signal paused_changed(paused: bool)
signal prompt_changed(text: String)
signal dialogue_requested(speaker: String, lines: PackedStringArray)
signal dialogue_finished
signal flag_granted(id: String)
signal boss_changed(boss_name: String, hp: int, max_hp: int)

const PROLOGUE := "res://scenes/cinematics/prologue.tscn"
const FIRST_ROOM := "res://scenes/rooms/harbor.tscn"  # safe chapter start; prologue skip lands here
const TITLE := "res://scenes/ui/title.tscn"

var save_path := "user://save.json"

# Persistent progress. `flags` holds stable content IDs (rewards, story beats, abilities).
var flags: Dictionary = {}
var coins := 0
var max_hp := 5
var max_spirit := 3.0
var checkpoint := {"room": FIRST_ROOM, "x": 0.0, "y": 0.5}
var objective := ""

# Runtime-only.
var hp := 5
var spirit := 3.0
var pending_spawn: Variant = null  # Vector3 or spawn-marker name, consumed by Room
var in_dialogue := false
# Test hooks: headless flow tests record room requests instead of swapping scenes.
var scene_changes_enabled := true
var last_room_request := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	InputSetup.register()


## Show lines in the HUD dialogue box and wait until the player has read them.
## Player control is suspended while `in_dialogue` is true.
func say(speaker: String, lines: PackedStringArray) -> void:
	in_dialogue = true
	dialogue_requested.emit(speaker, lines)
	await dialogue_finished
	# Swallow the closing press so it doesn't also jump/slash.
	await get_tree().physics_frame
	await get_tree().physics_frame
	in_dialogue = false


# --- progression -----------------------------------------------------------

func has(id: String) -> bool:
	return flags.has(id)


## Idempotent grant. Returns true only the first time, so rewards never duplicate.
func grant(id: String) -> bool:
	if flags.has(id):
		return false
	flags[id] = true
	flag_granted.emit(id)
	return true


func add_coins(n: int) -> void:
	coins += n
	coins_changed.emit(coins)


func set_objective(text: String) -> void:
	objective = text
	objective_changed.emit(text)


func damage(n: int) -> int:
	hp = maxi(hp - n, 0)
	health_changed.emit(hp, max_hp)
	return hp


func heal_full() -> void:
	hp = max_hp
	spirit = max_spirit
	health_changed.emit(hp, max_hp)
	spirit_changed.emit(spirit, max_spirit)


func use_spirit(cost: float) -> bool:
	if spirit < cost:
		return false
	spirit -= cost
	spirit_changed.emit(spirit, max_spirit)
	return true


func regen_spirit(amount: float) -> void:
	if spirit >= max_spirit:
		return
	spirit = minf(spirit + amount, max_spirit)
	spirit_changed.emit(spirit, max_spirit)


# --- checkpoint / rooms ----------------------------------------------------

func set_checkpoint(room: String, pos: Vector3) -> void:
	checkpoint = {"room": room, "x": pos.x, "y": pos.y}
	heal_full()
	save_game()


func respawn() -> void:
	heal_full()
	pending_spawn = Vector3(checkpoint.x, checkpoint.y, 0)
	_go(checkpoint.room)


func change_room(path: String, spawn_name: String) -> void:
	pending_spawn = spawn_name
	_go(path)


func _go(path: String) -> void:
	set_paused(false)
	Engine.time_scale = 1.0
	last_room_request = path
	if scene_changes_enabled:
		get_tree().call_deferred("change_scene_to_file", path)


# --- new / continue / save -------------------------------------------------

func reset_state() -> void:
	flags = {}
	coins = 0
	max_hp = 5
	max_spirit = 3.0
	checkpoint = {"room": FIRST_ROOM, "x": 0.0, "y": 0.5}
	objective = ""
	heal_full()


func new_game() -> void:
	reset_state()
	SaveFile.erase(save_path)
	pending_spawn = null
	save_game()
	_go(PROLOGUE)


func has_save() -> bool:
	return not SaveFile.read(save_path).is_empty()


func continue_game() -> bool:
	if not load_game():
		return false
	respawn()
	return true


func to_dict() -> Dictionary:
	return {"flags": flags, "coins": coins, "max_hp": max_hp, "max_spirit": max_spirit,
		"checkpoint": checkpoint, "objective": objective}


func from_dict(d: Dictionary) -> void:
	reset_state()
	flags = d.get("flags", {})
	coins = int(d.get("coins", 0))
	max_hp = int(d.get("max_hp", 5))
	max_spirit = float(d.get("max_spirit", 3.0))
	var cp: Dictionary = d.get("checkpoint", {})
	if ResourceLoader.exists(str(cp.get("room", ""))):
		checkpoint = {"room": cp.room, "x": float(cp.get("x", 0)), "y": float(cp.get("y", 0.5))}
	objective = str(d.get("objective", ""))
	heal_full()


func save_game() -> bool:
	return SaveFile.write(save_path, to_dict())


func load_game() -> bool:
	var d := SaveFile.read(save_path)
	if d.is_empty():
		return false
	from_dict(d)
	return true


# --- feel ------------------------------------------------------------------

## Brief global slow-down for impact. Uses a real-time timer so it always restores,
## and gameplay timers keep consistent game-time because physics delta is scaled.
func hitstop(duration := 0.05) -> void:
	Engine.time_scale = 0.05
	await get_tree().create_timer(duration, true, false, true).timeout
	Engine.time_scale = 1.0


func _notification(what: int) -> void:
	# Focus loss: pause and release held actions so nothing sticks.
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		for a in InputSetup.ACTIONS:
			Input.action_release(a)
		if get_tree().current_scene is Room:
			set_paused(true)


## Development-build shortcuts: F1-F4 jump to chapter rooms, F5 grants sword + Gale slash.
func _unhandled_key_input(e: InputEvent) -> void:
	if not OS.is_debug_build() or not e.is_pressed() or e.is_echo():
		return
	var rooms := {KEY_F1: [FIRST_ROOM, "Start"], KEY_F2: ["res://scenes/rooms/cave.tscn", "FromHarbor"],
		KEY_F3: ["res://scenes/rooms/boss_deck.tscn", "Start"], KEY_F4: ["res://scenes/rooms/dock_test.tscn", "Start"]}
	var k: int = (e as InputEventKey).keycode
	if rooms.has(k):
		change_room(rooms[k][0], rooms[k][1])
	elif k == KEY_F5:
		grant("item_cutlass")
		grant("ability_wind_slash")
		toast.emit("DEBUG: cutlass + Gale slash granted")


func set_paused(p: bool) -> void:
	get_tree().paused = p
	paused_changed.emit(p)
