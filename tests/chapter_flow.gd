extends Node3D
## Chapter progression tests (headless). Run:
##   tools\godot.cmd --headless --path . res://tests/chapter_flow.tscn
## Rooms are instanced as children; Game records room requests instead of changing scene.

var _fails := 0
var _passes := 0


func _ready() -> void:
	Game.save_path = "user://test_flow_save.json"
	Game.scene_changes_enabled = false
	await _run()
	print("FLOW TESTS: %d passed, %d failed" % [_passes, _fails])
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


func load_room(path: String) -> Node:
	var r: Node = load(path).instantiate()
	add_child(r)
	await frames(3)
	return r


func free_room(r: Node) -> void:
	r.queue_free()
	await frames(2)


func _snapshot() -> Dictionary:
	return {"flags": Game.flags.duplicate(), "cp": Game.checkpoint.duplicate(), "obj": Game.objective,
		"req": Game.last_room_request}


func _run() -> void:
	print("[prologue: skipped == watched]")
	Game.reset_state()
	var pro := await load_room("res://scenes/cinematics/prologue.tscn")
	await frames(10)
	pro._finish()  # Skip button / Esc path
	await frames(3)
	var skipped := _snapshot()
	await free_room(pro)
	Game.reset_state()
	pro = await load_room("res://scenes/cinematics/prologue.tscn")
	# Watch it: advance every dialogue box as it appears until the prologue ends itself.
	var guard := 0
	while not pro._done and guard < 2400:
		if Game.in_dialogue:
			Game.dialogue_finished.emit()
		await frames(5)
		guard += 5
	var watched := _snapshot()
	await free_room(pro)
	check(skipped == watched, "skip and watch give identical flags/checkpoint/objective/room")
	check(watched.req == Game.FIRST_ROOM and Game.pending_spawn == "Arrival", "prologue lands at harbor Arrival")

	print("[harbor gating]")
	Game.reset_state()
	var harbor := await load_room("res://scenes/rooms/harbor.tscn")
	var player: Player = harbor.get_node("Player")
	check(not player.has_sword(), "no sword before the cutlass pickup")
	var pier: Door = harbor.get_node("Level/PierDoor")
	Game.last_room_request = ""
	pier.interact(player)
	check(Game.last_room_request == "", "pier to boss is locked before the wind slash")
	var cutlass: Pickup = harbor.get_node("Level/Cutlass")
	cutlass.interact(player)
	await frames(2)
	if Game.in_dialogue:
		Game.dialogue_finished.emit()
	await frames(4)
	check(player.has_sword() and Game.has("item_cutlass"), "cutlass pickup grants the sword")
	# Pickup immediately followed by death: permanent rewards survive (saved on pickup).
	Game.reset_state()
	check(Game.load_game() and Game.has("item_cutlass"), "cutlass survives death/reload (saved on pickup)")
	await free_room(harbor)
	harbor = await load_room("res://scenes/rooms/harbor.tscn")
	check(not harbor.has_node("Level/Cutlass") or harbor.get_node("Level/Cutlass").is_queued_for_deletion(), "cutlass does not respawn on revisit")
	await free_room(harbor)

	print("[wind slash: Spirit never softlocks]")
	Game.reset_state()
	Game.grant("ability_wind_slash")
	Game.spirit = 0.0
	check(not Game.use_spirit(1.0), "cannot cast at zero Spirit")
	var cave := await load_room("res://scenes/rooms/cave.tscn")
	await frames(200)  # ~3.3 s of passive regen via the player
	check(Game.spirit >= 1.0, "Spirit regenerates to castable (%.2f)" % Game.spirit)
	# Wind slash trips the distant bridge switch across the pit.
	var p: Player = cave.get_node("Player")
	p.global_position = Vector3(26.5, 0.1, 0)
	p.facing = 1.0
	await frames(5)
	Game.spirit = Game.max_spirit
	p._try_wind_slash()
	await frames(60)
	check(Game.has("cave_bridge_switch"), "Gale slash from the near edge trips the bridge switch")
	var bridge := cave.get_node("Level/Bridge") as Node3D
	await frames(70)
	check(absf(bridge.position.y - (-0.2)) < 0.15, "bridge rose to walking height (y %.2f)" % bridge.position.y)
	# Normal slash cannot trip a wind-only switch.
	Game.flags.erase("cave_bridge_switch")
	var sw: HitSwitch = cave.get_node("Level/BridgeSwitch")
	check(not sw.apply_hit(Hit.make(1, Vector3.ZERO, Hit.Kind.SLASH, p)), "cutlass alone cannot trip a wind switch")
	Game.grant("cave_bridge_switch")
	# Ranged enemy on the shelf: its aimed shot reaches a grounded player; a reflect sends it back.
	var gunner: PowderGull = cave.get_node("Level/Gunner")
	p.global_position = Vector3(40.0, 0.1, 0)  # out of the shelf edge's cover
	p.facing = 1.0
	Game.heal_full()
	var hp_before := Game.hp
	gunner._fire(p)
	var shot: Projectile = null
	for n in cave.get_node("Level").get_children():
		if n is Projectile:
			shot = n
	await frames(90)
	check(Game.hp < hp_before, "Powder Gull's aimed shot hits a player below its shelf")
	await frames(60)
	gunner._fire(p)
	for n in cave.get_node("Level").get_children():
		if n is Projectile and not n.reflected:
			shot = n
	var g_hp := gunner.hp
	shot.reflect(1.0, p)
	await frames(90)
	check(not is_instance_valid(gunner) or gunner.hp < g_hp, "reflected shot flies back and hits the gunner")
	# Carry puzzle: barrel lost in the channel returns home; on the plate it opens the gate for good.
	var barrel: Carryable = cave.get_node("Level/Barrel")
	var home := barrel.global_position
	barrel.global_position = Vector3(61, -3, 0)
	await frames(3)
	check(barrel.global_position.distance_to(home) < 0.6, "barrel lost below the room returns home")
	barrel.global_position = Vector3(66.5, 3.0, 0)
	await frames(90)
	check(Game.has("cave_shortcut_plate"), "barrel on the plate opens the tunnel")
	await free_room(cave)
	cave = await load_room("res://scenes/rooms/cave.tscn")
	var gate := cave.get_node("Level/TunnelGate") as Node3D
	check(gate.position.y > 2.5, "tunnel gate stays open on revisit")
	await free_room(cave)

	print("[boss: defeat is permanent]")
	Game.reset_state()
	Game.grant("item_cutlass")
	Game.grant("ability_wind_slash")
	var deck := await load_room("res://scenes/rooms/boss_deck.tscn")
	var boss: Chainhook = deck.get_node("Level/Boss")
	check(not boss.apply_hit(Hit.make(1, Vector3.ZERO, Hit.Kind.SLASH, null)), "boss ignores hits before the fight starts")
	boss.start_fight()
	await frames(2)
	while Game.in_dialogue:
		Game.dialogue_finished.emit()
		await frames(3)
	boss._enter(Chainhook.State.IDLE)
	check(not boss.apply_hit(Hit.make(1, Vector3.ZERO, Hit.Kind.SLASH, null)), "boss is armored outside recovery")
	boss._enter(Chainhook.State.STUCK)
	check(boss.apply_hit(Hit.make(1, Vector3.ZERO, Hit.Kind.SLASH, null)), "boss takes damage while the hook is stuck")
	boss.hp = 7
	boss._enter(Chainhook.State.STUCK)
	boss.apply_hit(Hit.make(1, Vector3.ZERO, Hit.Kind.SLASH, null))
	check(boss.phase == 2, "phase 2 at half health")
	boss._enter(Chainhook.State.STUCK)
	boss.hp = 1
	var coins_before := Game.coins
	boss.apply_hit(Hit.make(1, Vector3.ZERO, Hit.Kind.SLASH, null))
	await frames(60)
	while Game.in_dialogue:
		Game.dialogue_finished.emit()
		await frames(3)
	check(Game.has("boss_chainhook_defeated"), "defeat flag granted")
	check(Game.coins == coins_before + 50, "boss reward paid once")
	await free_room(deck)
	Game.reset_state()
	Game.load_game()
	deck = await load_room("res://scenes/rooms/boss_deck.tscn")
	check(not deck.has_node("Level/Boss") or deck.get_node("Level/Boss").is_queued_for_deletion(), "boss does not respawn after reload")
	check(Game.coins == coins_before + 50, "no duplicate boss reward on reload")
	var cage := deck.get_node("Level/CageGate") as Node3D
	check(cage.position.y > 3.0, "Sol's cage is open after reload")
	var sol: Npc = deck.get_node("Level/Sol")
	sol.interact(deck.get_node("Player"))
	await frames(2)
	while Game.in_dialogue:
		Game.dialogue_finished.emit()
		await frames(3)
	await frames(3)
	check(Game.has("crew_sol"), "talking to Sol recruits her")
	var raise: Npc = deck.get_node("Level/RaiseFlag")
	check(raise.enabled, "flag can be raised once Sol has joined")
	Game.last_room_request = ""
	deck._depart()
	await frames(5)
	check(Game.has("chapter1_complete"), "chapter completion saved before the departure cutscene")
	Game.reset_state()
	Game.load_game()
	check(Game.has("chapter1_complete") and Game.checkpoint.room == Game.FIRST_ROOM, "Continue after the chapter resumes at Gullhaven with completion kept")
	await free_room(deck)
