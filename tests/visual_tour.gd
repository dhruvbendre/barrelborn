extends Node
## Scripted play-through for visual QA. Loads a room, drives the player with the same
## input actions a human uses, and saves real viewport screenshots to qa/screens/.
## Run (windowed, not headless):
##   tools\godot.cmd --path . res://tests/visual_tour.tscn -- room=res://scenes/rooms/dock_test.tscn

var room_path := "res://scenes/rooms/dock_test.tscn"
var out_dir := "res://qa/screens"
var room: Node
var player: Player
var _shots := {}
var _t := 0.0
var _log: Array[String] = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("room="):
			room_path = a.substr(5)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out_dir))
	Game.reset_state()
	Game.save_path = "user://tour_save.json"
	# Watchdog: never hang a QA run.
	# Bound to the SceneTree, so it still fires if a respawn replaces this scene.
	get_tree().create_timer(150.0, true, false, true).timeout.connect(get_tree().quit.bind(2))
	player_died_guard()
	room = load(room_path).instantiate()
	add_child(room)
	player = room.get_node("Player")
	player.force_sword = true
	_run()


func player_died_guard() -> void:
	await get_tree().process_frame
	player.died.connect(func() -> void:
		print("TOUR NOTE: player died at x=%.1f (respawn would leave the tour)" % player.global_position.x)
		_log.append("DIED at x=%.1f" % player.global_position.x)
		_write_log()
		get_tree().quit(3))


func _physics_process(delta: float) -> void:
	_t += delta


func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func hold(action: String, on: bool) -> void:
	if on:
		Input.action_press(action)
	else:
		Input.action_release(action)


func tap(action: String) -> void:
	Input.action_press(action)
	await frames(3)
	Input.action_release(action)


func shot(name: String) -> void:
	print("shot ", name)
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	var path := ProjectSettings.globalize_path("%s/%s.png" % [out_dir, name])
	img.save_png(path)
	_log.append("%s  x=%.1f y=%.1f hp=%d coins=%d" % [name, player.global_position.x, player.global_position.y, Game.hp, Game.coins])


## Run right until x >= target (or timeout), jumping at listed x positions.
func run_to(target: float, jumps: Array = [], timeout := 8.0) -> void:
	hold("move_right", true)
	var start := _t
	var pending := jumps.duplicate()
	while player.global_position.x < target and _t - start < timeout:
		if not pending.is_empty() and player.global_position.x >= pending[0]:
			pending.pop_front()
			hold("jump", true)
			await frames(26)
			hold("jump", false)
		await frames(1)
	hold("move_right", false)


func _run() -> void:
	await frames(30)
	await shot("01_start")
	await run_to(5.0)
	await frames(10)
	for i in 4:
		await tap("attack")
		if i == 1:
			await frames(3)
			await shot("02_slash_crate")
		await frames(16)
	await run_to(10.6)
	await frames(5)
	await run_to(16.8, [10.8, 12.6])
	await shot("03_ledge")
	await run_to(23.0, [17.3])
	await frames(30)
	await shot("04_checkpoint")
	await run_to(31.0)
	for i in 8:
		await face_enemy()
		await tap("attack")
		if i == 2:
			await frames(4)
			await shot("05_combat")
		await frames(18)
	await frames(30)
	await shot("06_after_fight")
	await run_to(39.6)
	# Wait for the moving platform to come close, then jump on.
	var mp := room.get_node("Level/MovingPlatform") as Node3D
	var guard := 0
	while mp.global_position.x > 41.8 and guard < 400:
		await frames(1)
		guard += 1
	await run_to(44.0, [39.6], 4.0)
	await frames(20)
	await shot("07_platform")
	await run_to(60.0, [46.5, 54.0], 10.0)
	await frames(20)
	await shot("08_end")
	var f := FileAccess.open(ProjectSettings.globalize_path(out_dir + "/tour_log.txt"), FileAccess.WRITE)
	f.store_string("\n".join(_log) + "\n")
	f.close()
	print("TOUR DONE\n" + "\n".join(_log))
	SaveFile.erase(Game.save_path)
	get_tree().quit()


func _write_log() -> void:
	var f := FileAccess.open(ProjectSettings.globalize_path(out_dir + "/tour_log.txt"), FileAccess.WRITE)
	f.store_string("\n".join(_log) + "\n")
	f.close()


func face_enemy() -> void:
	var e := get_tree().get_first_node_in_group("enemies") as Node3D
	if e == null:
		return
	var a := "move_right" if e.global_position.x > player.global_position.x else "move_left"
	await tap(a)
