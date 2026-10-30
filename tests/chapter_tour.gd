extends Node
## Chapter visual QA. Plays the harbor opening with real input actions (proves the route is
## reachable), then visits later beats and saves screenshots to qa/screens/chapter/.
## Run windowed: tools\godot.cmd --path . res://tests/chapter_tour.tscn

var out_dir := "res://qa/screens/chapter"
var room: Node
var player: Player
var _log: Array[String] = []


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out_dir))
	Game.save_path = "user://tour_chapter_save.json"
	Game.scene_changes_enabled = false
	get_tree().create_timer(240.0, true, false, true).timeout.connect(get_tree().quit.bind(2))
	_run()


func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func tap(action: String, hold := 3) -> void:
	Input.action_press(action)
	await frames(hold)
	Input.action_release(action)


func skip_dialogue() -> void:
	await frames(2)
	var guard := 0
	while Game.in_dialogue and guard < 40:
		await frames(14)
		await tap("interact")
		guard += 1
	await frames(4)


func shot(name: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	img.save_png(ProjectSettings.globalize_path("%s/%s.png" % [out_dir, name]))
	var pos := player.global_position if player else Vector3.ZERO
	_log.append("%s  x=%.1f y=%.1f hp=%d coins=%d obj='%s'" % [name, pos.x, pos.y, Game.hp, Game.coins, Game.objective])
	print("shot ", name)


func open_room(path: String, spawn: Variant = null) -> void:
	if room:
		room.queue_free()
		await frames(2)
	Game.pending_spawn = spawn
	room = load(path).instantiate()
	add_child(room)
	player = room.get_node_or_null("Player")
	await frames(20)


func run_to(target: float, jumps: Array = [], timeout := 8.0) -> void:
	var dir := "move_right" if target > player.global_position.x else "move_left"
	Input.action_press(dir)
	var t := 0
	var pending := jumps.duplicate()
	while (player.global_position.x < target if dir == "move_right" else player.global_position.x > target) and t < timeout * 60:
		if not pending.is_empty() and player.global_position.x >= pending[0]:
			pending.pop_front()
			Input.action_press("jump")
			await frames(26)
			Input.action_release("jump")
		await frames(1)
		t += 1
	Input.action_release(dir)
	await frames(6)


func teleport(x: float, y: float, facing := 1.0) -> void:
	player.global_position = Vector3(x, y, 0)
	player.velocity = Vector3.ZERO
	player.facing = facing
	room.get_node("Camera").snap()
	await frames(20)


func _run() -> void:
	Game.reset_state()
	# --- prologue ---
	room = load("res://scenes/cinematics/prologue.tscn").instantiate()
	add_child(room)
	await frames(150)
	await shot("01_prologue_storm")
	room._finish()
	await frames(2)
	# --- harbor, played with input ---
	await open_room("res://scenes/rooms/harbor.tscn", "Arrival")
	await shot("02_harbor_arrival")
	await run_to(10.6, [4.4])
	await tap("interact")  # talk to Bastian
	await frames(6)
	await shot("03_bastian_dialogue")
	await skip_dialogue()
	await run_to(14.4)
	await tap("interact")  # take the cutlass
	await skip_dialogue()
	await shot("04_cutlass")
	await run_to(16.9)
	for i in 6:
		await tap("attack")
		await frames(14)
	await run_to(19.5)
	await shot("05_barricade_broken")
	await run_to(24.0)
	for i in 10:
		var e := room.get_node_or_null("Level/Brute1") as Node3D
		if e == null or not is_instance_valid(e):
			break
		await tap("move_right" if e.global_position.x > player.global_position.x else "move_left", 2)
		await tap("attack")
		if i == 1:
			await frames(3)
			await shot("06_brute_fight")
		await frames(16)
	await run_to(28.3)
	await tap("interact")  # fisher's chest
	await frames(20)
	await shot("07_chest")
	await run_to(36.0, [29.6])
	await shot("08_checkpoint_dock2")
	await run_to(43.0, [36.4, 38.6, 40.6])
	await frames(20)
	await shot("09_lookout_promise")
	_log.append("route check: lookout reached = %s (y=%.1f)" % [player.global_position.y > 4.0, player.global_position.y])
	# --- cave (teleport between beats) ---
	await open_room("res://scenes/rooms/cave.tscn", "FromHarbor")
	await teleport(6.5, 0.1)
	await shot("10_cave_conch")
	Game.grant("ability_wind_slash")
	Game.grant("item_cutlass")
	await teleport(12.0, 0.1)
	await tap("power")
	await frames(6)
	await shot("11_gale_slash")
	await frames(40)
	await teleport(26.5, 0.1)
	await tap("power")
	await frames(90)
	await shot("12_bridge_raised")
	await teleport(44.0, 0.1)
	await frames(50)
	await shot("13_powder_gull")
	await teleport(59.5, 0.1)
	await shot("14_barrel_puzzle")
	# --- harbor shortcut + treasure ---
	await open_room("res://scenes/rooms/harbor.tscn", "FromShortcut")
	await teleport(48.8, 4.7)
	Game.spirit = Game.max_spirit
	await tap("power")
	await frames(70)
	await shot("15_drawbridge_switch")
	_log.append("treasure switch tripped from roof = %s" % Game.has("harbor_drawbridge_switch"))
	# --- boss ---
	await open_room("res://scenes/rooms/boss_deck.tscn", "Start")
	await run_to(10.0)
	await frames(10)
	await skip_dialogue()
	await frames(60)
	await shot("16_boss_idle")
	var boss := room.get_node("Level/Boss")
	boss._cycle = 0
	boss._enter(Chainhook.State.SWEEP_TELL)
	await frames(30)
	await shot("17_boss_sweep_telegraph")
	await frames(40)
	await shot("18_boss_stuck")
	boss._enter(Chainhook.State.SHOT_TELL)
	await frames(45)
	await shot("19_boss_chain_shot")
	Game.set_paused(true)
	await frames(2)
	await shot("20_pause_menu")
	Game.set_paused(false)
	# Narrow aspect check.
	get_window().size = Vector2i(720, 900)
	await frames(30)
	await shot("21_narrow_aspect")
	get_window().size = Vector2i(1280, 720)
	var f := FileAccess.open(ProjectSettings.globalize_path(out_dir + "/tour_log.txt"), FileAccess.WRITE)
	f.store_string("\n".join(_log) + "\n")
	f.close()
	print("CHAPTER TOUR DONE\n" + "\n".join(_log))
	SaveFile.erase(Game.save_path)
	get_tree().quit()
