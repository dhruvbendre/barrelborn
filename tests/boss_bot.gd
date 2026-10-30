extends Node
## Plays the Chainhook fight with real input actions, reacting only to the boss's visible
## telegraphs (state), to prove the fight is winnable with the intended reads:
## jump LOW sweeps, stay grounded for HIGH sweeps, close in and slash while STUCK,
## Gale-slash from range, slash shots back. Reports damage taken and fight duration.
## Run: tools\godot.cmd --headless --path . res://tests/boss_bot.tscn

var room: Node
var player: Player
var boss: Chainhook
var _t := 0.0
var _hits_taken := 0


func _ready() -> void:
	Game.save_path = "user://test_boss_bot.json"
	Game.scene_changes_enabled = false
	Game.reset_state()
	Game.grant("item_cutlass")
	Game.grant("ability_wind_slash")
	Game.max_hp = 8  # extra margin: the bot has no human anticipation
	Game.heal_full()
	room = load("res://scenes/rooms/boss_deck.tscn").instantiate()
	add_child(room)
	player = room.get_node("Player")
	boss = room.get_node("Level/Boss")
	Game.health_changed.connect(func(h: int, _m: int) -> void: _hits_taken = Game.max_hp - h)
	get_tree().create_timer(200.0, true, false, true).timeout.connect(func() -> void:
		print("BOSS BOT: TIMEOUT boss_state=%d boss_hp=%d hp=%d" % [boss.state if is_instance_valid(boss) else -1, boss.hp if is_instance_valid(boss) else -1, Game.hp])
		get_tree().quit(2))
	_run()


func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func press(a: String, n := 3) -> void:
	Input.action_press(a)
	await frames(n)
	Input.action_release(a)


func _physics_process(d: float) -> void:
	_t += d


func _run() -> void:
	await frames(10)
	Input.action_press("move_right")
	while player.global_position.x < 9.5 and not Game.in_dialogue:
		await frames(1)
	Input.action_release("move_right")
	await frames(5)
	await frames(3)
	while Game.in_dialogue:
		Game.dialogue_finished.emit()  # dialogue is not under test here
		await frames(6)
	print("bot: fight started, boss state=%d" % boss.state)
	var start := _t
	while is_instance_valid(boss) and boss.state != Chainhook.State.DEAD and _t - start < 120.0 and Game.hp > 0:
		var dx := boss.global_position.x - player.global_position.x
		var toward := "move_right" if dx > 0 else "move_left"
		var away := "move_left" if dx > 0 else "move_right"
		match boss.state:
			Chainhook.State.SWEEP_TELL:
				if not boss._sweep_high and boss._t > 0.62 and player.is_on_floor():
					Input.action_press("jump")  # full jump timed to the visible windup
					await frames(24)
					Input.action_release("jump")
				else:
					await frames(1)
			Chainhook.State.STUCK, Chainhook.State.STUNNED:
				if absf(dx) > 1.6:
					if absf(dx) < 9.0 and Game.spirit >= 1.0 and absf(dx) > 4.0:
						player.facing = signf(dx)
						await press("power")
					Input.action_press(toward)
					await frames(4)
					Input.action_release(toward)
				else:
					await press(toward, 2)
					await press("attack")
					await frames(12)
			Chainhook.State.SHOT, Chainhook.State.SHOT_TELL, Chainhook.State.IDLE:
				# Slash incoming shots back (reflect) when one is close.
				var shot := _nearest_shot()
				if shot and absf(shot.global_position.x - player.global_position.x) < 1.7:
					player.facing = signf(shot.global_position.x - player.global_position.x)
					await press("attack")
					await frames(10)
				elif absf(dx) < 3.5:
					await press(away, 6)
				else:
					await frames(1)
			_:
				await frames(1)
	var won := not is_instance_valid(boss) or boss.state == Chainhook.State.DEAD or Game.has("boss_chainhook_defeated")
	print("BOSS BOT: won=%s time=%.1fs hits_taken=%d hp_left=%d phase_reached=%d" % [
		won, _t - start, _hits_taken, Game.hp, boss.phase if is_instance_valid(boss) else 2])
	SaveFile.erase(Game.save_path)
	get_tree().quit(0 if won else 1)


func _nearest_shot() -> Projectile:
	var best: Projectile = null
	for n in room.get_node("Level").get_children():
		if n is Projectile and not n.reflected:
			if best == null or absf(n.global_position.x - player.global_position.x) < absf(best.global_position.x - player.global_position.x):
				best = n
	return best
