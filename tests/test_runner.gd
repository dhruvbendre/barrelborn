extends Node3D
## Headless logic tests. Run:
##   tools\godot.cmd --headless --path . res://tests/test_runner.tscn
## Exit code 0 = all passed. Uses user://test_save.json, never the player's real save.

const PLAYER := preload("res://scenes/player/player.tscn")

var _fails := 0
var _passes := 0


class Dummy:
	extends StaticBody3D
	var hits := 0
	func apply_hit(_h: Hit) -> bool:
		hits += 1
		return true


func _ready() -> void:
	Game.save_path = "user://test_save.json"
	await _run()
	print("TESTS: %d passed, %d failed" % [_passes, _fails])
	SaveFile.erase(Game.save_path)
	get_tree().quit(1 if _fails > 0 else 0)


func check(cond: bool, label: String) -> void:
	if cond:
		_passes += 1
		print("  PASS ", label)
	else:
		_fails += 1
		print("  FAIL ", label)


func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _floor(x0: float, x1: float) -> StaticBody3D:
	var b := StaticBody3D.new()
	var s := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(x1 - x0, 1, 4)
	s.shape = box
	b.add_child(s)
	b.position = Vector3((x0 + x1) / 2.0, -0.5, 0)
	add_child(b)
	return b


func _spawn(pos: Vector3) -> Player:
	var p: Player = PLAYER.instantiate()
	p.force_sword = true
	p.position = pos
	add_child(p)
	return p


## Scripted presses are seen by the controller one physics frame after the press
## (harness timing), so a tap is held for 2 frames like a real 33 ms key press.
func tap(action: String) -> void:
	Input.action_press(action)
	await frames(2)
	Input.action_release(action)


func _release_all() -> void:
	for a in InputSetup.ACTIONS:
		Input.action_release(a)


func _run() -> void:
	var t: PlayerTuning = load("res://resources/tuning/player_tuning.tres")
	print("[jump math]")
	check(is_equal_approx(t.gravity(), 30.0), "gravity derived from 2.4m / 0.4s = 30")
	check(is_equal_approx(t.jump_velocity(), 12.0), "launch velocity = 12 m/s")
	# Discrete integration of the full jump reaches ~2.4 m.
	var v := t.jump_velocity()
	var y := 0.0
	var peak := 0.0
	for i in 120:
		v -= t.gravity() * (1.0 / 60.0)
		y += v / 60.0
		peak = maxf(peak, y)
	check(absf(peak - t.jump_height) < 0.15, "simulated apex %.2f m ~ 2.4 m" % peak)

	_floor(-20, 20)
	await frames(2)

	print("[slash: one hit per target per swing]")
	var p := _spawn(Vector3(0, 0.05, 0))
	var d := Dummy.new()
	var ds := CollisionShape3D.new()
	var db := BoxShape3D.new()
	db.size = Vector3(0.6, 1.4, 0.6)
	ds.shape = db
	d.add_child(ds)
	d.collision_layer = 4
	d.position = Vector3(0.8, 0.7, 0)
	add_child(d)
	await frames(10)
	await tap("attack")
	await frames(40)
	check(d.hits == 1, "first swing hits exactly once (got %d)" % d.hits)
	await tap("attack")
	await frames(40)
	check(d.hits == 2, "second swing hits once more (got %d)" % d.hits)
	d.queue_free()
	p.queue_free()
	await frames(2)

	print("[slash kills a Bilge Brute in 3 hits]")
	p = _spawn(Vector3(0, 0.05, 0))
	var brute: BilgeBrute = load("res://scenes/enemies/bilge_brute.tscn").instantiate()
	brute.position = Vector3(1.2, 0.1, 0)
	add_child(brute)
	await frames(10)
	for i in 3:
		p.facing = 1.0
		await tap("attack")
		await frames(30)
		print("    brute hp=%d state=%d dist=%.2f player_hp=%d" % [brute.hp, brute.state, brute.global_position.x - p.global_position.x, Game.hp])
	check(brute.state == BilgeBrute.State.DEAD, "brute dead after 3 slashes (hp %d)" % brute.hp)
	p.queue_free()
	await frames(60)

	print("[jump buffer + coyote + double jump]")
	p = _spawn(Vector3(0, 0.05, 0))
	await frames(10)
	check(p.is_on_floor(), "player settles on floor")
	await tap("jump")
	check(p.velocity.y > 5.0, "ground jump launches")
	# Wait until falling close to floor, then buffer a press before landing.
	var guard := 0
	while not (p.velocity.y < 0.0 and p.global_position.y < 0.6) and guard < 200:
		await frames(1)
		guard += 1
	# Air jump is still available here, so consume it first to isolate the buffer test.
	p._air_jumps = 0
	await tap("jump")
	guard = 0
	var rejumped := false
	while guard < 20:
		await frames(1)
		guard += 1
		if p.velocity.y > 5.0:
			rejumped = true
			break
	check(rejumped, "jump pressed just before landing is buffered and fires on landing")
	await frames(90)
	# Double jump: jump, then press again mid-air.
	await tap("jump")
	await frames(20)
	var vy_before := p.velocity.y
	await tap("jump")
	check(p.velocity.y > vy_before + 3.0, "double jump adds upward velocity mid-air (%.1f -> %.1f, floor=%s)" % [vy_before, p.velocity.y, p.is_on_floor()])
	p.queue_free()
	await frames(2)

	# Coyote: walk off a ledge and jump within 0.1 s.
	var ledge := _floor(30, 32)
	ledge.position.y = 2.0 - 0.5
	p = _spawn(Vector3(31.7, 2.05, 0))
	p.can_double_jump = false
	await frames(10)
	Input.action_press("move_right")
	guard = 0
	while p.is_on_floor() and guard < 120:
		await frames(1)
		guard += 1
	Input.action_release("move_right")
	await frames(3)  # 0.05 s after leaving the edge
	await tap("jump")
	check(p.velocity.y > 4.0, "coyote jump works 0.05 s after leaving ledge (vy %.1f)" % p.velocity.y)
	await frames(60)
	# Without coyote: walk off, wait 0.3 s, jump should do nothing (double jump disabled).
	p.queue_free()
	p = _spawn(Vector3(31.7, 2.05, 0))
	p.can_double_jump = false
	await frames(10)
	Input.action_press("move_right")
	guard = 0
	while p.is_on_floor() and guard < 120:
		await frames(1)
		guard += 1
	Input.action_release("move_right")
	await frames(18)
	await tap("jump")
	check(p.velocity.y < 0.0, "no jump after coyote window expires")
	p.queue_free()
	_release_all()
	await frames(2)

	print("[rewards are idempotent]")
	Game.reset_state()
	check(Game.grant("chest_test"), "first grant succeeds")
	check(not Game.grant("chest_test"), "second grant is refused")
	var coins_before := Game.coins
	var crate: Breakable = load("res://scenes/interactables/crate.tscn").instantiate()
	crate.reward_id = "crate_reward_test"
	crate.coins = 5
	add_child(crate)
	crate.apply_hit(Hit.make(1, Vector3.ZERO, Hit.Kind.SLASH, null))
	await frames(1)
	check(Game.coins == coins_before + 5, "reward crate pays once")
	var crate2: Breakable = load("res://scenes/interactables/crate.tscn").instantiate()
	crate2.reward_id = "crate_reward_test"
	crate2.coins = 5
	add_child(crate2)
	await frames(1)
	check(not is_instance_valid(crate2) or crate2.is_queued_for_deletion(), "already-broken reward crate does not respawn")
	check(Game.coins == coins_before + 5, "no duplicate payout on re-entry")

	print("[save / load / recovery]")
	Game.reset_state()
	Game.grant("ability_wind_slash")
	Game.coins = 42
	check(Game.save_game(), "save writes")
	Game.reset_state()
	check(Game.load_game() and Game.coins == 42 and Game.has("ability_wind_slash"), "load restores coins + flags")
	Game.coins = 43
	Game.save_game()  # previous valid save (42) becomes .bak
	var f := FileAccess.open(Game.save_path, FileAccess.WRITE)
	f.store_string("{ corrupt")
	f.close()
	Game.reset_state()
	check(Game.load_game() and Game.coins == 42, "corrupt save falls back to previous valid save")
	f = FileAccess.open(Game.save_path, FileAccess.WRITE)
	f.store_string(JSON.stringify({"version": 999, "coins": 1}))
	f.close()
	check(SaveFile.read_one(Game.save_path).is_empty(), "future schema version is rejected")
	SaveFile.erase(Game.save_path)
	check(not Game.has_save(), "no save -> Continue unavailable")
