class_name Chainhook
extends CharacterBody3D
## Captain Varga Chainhook. Two readable patterns + a recovery window:
##   Hook Sweep: winds the chain (hook glows orange, 0.8 s) then sweeps the deck. LOW = jump it.
##     Phase 2 alternates LOW / HIGH; HIGH passes overhead (stay grounded). The hook then
##     bites into the deck: STUCK (vulnerable) while he heaves it free.
##   Chain Shot: aims (teal ring, 0.6 s), fires a reflectable shot. Reflect it back -> STUNNED.
##     Phase 2 fires a 3-shot fan.
## He is armored outside STUCK/STUNNED ("Clang!"), so timing matters, but the Gale slash
## can punish STUCK from range. Defeat is saved and never respawns.

signal defeated

enum State { WAIT, INTRO, IDLE, SWEEP_TELL, SWEEP, STUCK, SHOT_TELL, SHOT, STUNNED, DEAD }

const SHOT := preload("res://scenes/enemies/projectile.tscn")
const FLAG := "boss_chainhook_defeated"

@export var max_hp := 30
@export var arena_min_x := 6.0
@export var arena_max_x := 31.0
@export var sweep_reach := 9.0

@onready var visual: Node3D = $Visual
@onready var hook: Area3D = $Hook
@onready var hook_mesh: MeshInstance3D = $Hook/Mesh
@onready var chain: MeshInstance3D = $Chain
@onready var aim_ring: MeshInstance3D = $Visual/AimRing

var state := State.WAIT
var hp := 30
var facing := -1.0
var phase := 1
var _t := 0.0
var _sweep_high := false
var _cycle := 0
var _hook_mat: StandardMaterial3D
var _gravity := 30.0
var _anim: ModelAnim

const CLIPS := {State.IDLE: "idle", State.SWEEP_TELL: "sweep_tell", State.SWEEP: "sweep", State.STUCK: "stuck",
	State.SHOT_TELL: "shot_tell", State.SHOT: "shot", State.STUNNED: "stunned", State.DEAD: "death"}


func _ready() -> void:
	hp = max_hp
	if Game.has(FLAG):
		queue_free()
		return
	_anim = ModelAnim.find(visual)
	_anim.play("idle")
	_hook_mat = StandardMaterial3D.new()
	_hook_mat.albedo_color = Color("3a3a42")
	_hook_mat.metallic = 0.6
	hook_mesh.material_override = _hook_mat
	aim_ring.visible = false
	hook.body_entered.connect(_on_hook_body)
	hook.monitoring = false
	_rest_hook()


func _player() -> Player:
	return get_tree().get_first_node_in_group("player") as Player


## Called by the arena trigger.
func start_fight() -> void:
	if state != State.WAIT:
		return
	_enter(State.INTRO)
	Game.boss_changed.emit("Captain Varga Chainhook", hp, max_hp)
	await Game.say("Chainhook", PackedStringArray([
		"A barrel brat on MY deck? Gullhaven pays its tax, boy. In coin, or in teeth!",
		"Kito: Then I'll pay you in neither. I'm gonna be Pirate King!",
		"Chainhook: Ha! Then let's see you dodge a king's ransom of iron!",
	]))
	_enter(State.IDLE)


func _physics_process(delta: float) -> void:
	if state == State.WAIT or state == State.DEAD:
		_apply_gravity(delta)
		return
	_t += delta
	var p := _player()
	if Game.in_dialogue:
		_apply_gravity(delta)
		return
	match state:
		State.IDLE:
			if p:
				facing = signf(p.global_position.x - global_position.x)
				var dist := absf(p.global_position.x - global_position.x)
				# Drift toward a comfortable mid range so the player can't camp a corner.
				if dist > 7.0:
					velocity.x = facing * 2.0
				elif dist < 3.0:
					velocity.x = -facing * 1.5
				else:
					velocity.x = 0.0
			if _t >= (0.9 if phase == 1 else 0.6):
				velocity.x = 0.0
				_cycle += 1
				if _cycle % 3 == 0:
					_enter(State.SHOT_TELL)
				else:
					_sweep_high = phase == 2 and _cycle % 2 == 0
					_enter(State.SWEEP_TELL)
		State.SWEEP_TELL:
			_wind_hook(delta)
			if _t >= 0.8:
				_enter(State.SWEEP)
		State.SWEEP:
			var k := clampf(_t / 0.45, 0.0, 1.0)
			var y := 2.1 if _sweep_high else 0.45
			_place_hook(Vector3(facing * lerpf(1.0, sweep_reach, k), y, 0))
			if _t >= 0.45:
				_enter(State.STUCK)
		State.STUCK:
			# Hook bitten into the deck; he strains to pull it free.
			visual.position.x = sin(_t * 40.0) * 0.04
			_place_hook(Vector3(facing * sweep_reach, 0.15, 0))
			var stuck_time := 1.6 if phase == 1 else 1.15
			if _t >= stuck_time:
				visual.position.x = 0.0
				_rest_hook()
				_enter(State.IDLE)
		State.SHOT_TELL:
			if p:
				facing = signf(p.global_position.x - global_position.x)
			aim_ring.visible = fmod(_t, 0.14) < 0.09
			if _t >= 0.6:
				_enter(State.SHOT)
		State.SHOT:
			_fire(p)
			_enter(State.IDLE)
		State.STUNNED:
			visual.rotation.z = sin(_t * 12.0) * 0.12
			if _t >= 1.8:
				visual.rotation.z = 0.0
				_enter(State.IDLE)
	_apply_gravity(delta)
	position.x = clampf(position.x, arena_min_x, arena_max_x)
	visual.rotation.y = lerp_angle(visual.rotation.y, PI * 0.5 * facing, minf(delta * 8.0, 1.0))
	_draw_chain()


func _apply_gravity(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= _gravity * delta
	move_and_slide()
	position.z = 0.0
	velocity.z = 0.0


func _enter(s: State) -> void:
	state = s
	_t = 0.0
	if _anim:
		_anim.play(CLIPS.get(s, "idle"), true)
	aim_ring.visible = false
	hook.monitoring = s == State.SWEEP
	match s:
		State.SWEEP_TELL:
			_hook_mat.albedo_color = Color("ff7a2f")
			_hook_mat.emission_enabled = true
			_hook_mat.emission = Color("ff7a2f")
			Sfx.play("enemy_windup", 0.0)
		State.SWEEP:
			Sfx.play("swing", 0.0)
		State.STUCK:
			_hook_mat.albedo_color = Color("3a3a42")
			_hook_mat.emission_enabled = false
			Sfx.play("land", 0.0)
			Game.toast.emit("The hook is stuck - strike now!" if _cycle < 3 else "")
		State.SHOT_TELL:
			Sfx.play("enemy_windup", 0.0)


func _wind_hook(_delta: float) -> void:
	# Hook circles overhead (high sweep) or low at his side (low sweep): readable silhouette.
	var a := _t * 14.0
	var center := Vector3(-facing * 0.3, 3.1 if _sweep_high else 1.0, 0)
	_place_hook(center + Vector3(cos(a) * 0.9, sin(a) * 0.5, 0))


func _rest_hook() -> void:
	_place_hook(Vector3(facing * 0.9, 1.3, 0))


func _place_hook(local: Vector3) -> void:
	hook.position = local


func _draw_chain() -> void:
	var hand := Vector3(facing * 0.7, 1.6, 0)
	var to := hook.position
	var mid := (hand + to) * 0.5
	var length := hand.distance_to(to)
	chain.position = mid
	chain.scale = Vector3(1, maxf(length, 0.01), 1)
	var dir := (to - hand).normalized()
	chain.rotation = Vector3(0, 0, atan2(-dir.x, dir.y))


func _on_hook_body(b: Node3D) -> void:
	if b is Player:
		b.apply_hit(Hit.make(1, Vector3(facing * 7.0, 6.0, 0), Hit.Kind.ENEMY, self))


func _fire(p: Player) -> void:
	var angles := [0.0] if phase == 1 else [-0.18, 0.0, 0.2]
	Sfx.play("hurt", 0.0)
	for a in angles:
		var shot: Projectile = SHOT.instantiate()
		get_parent().add_child(shot)
		shot.global_position = global_position + Vector3(facing * 1.2, 1.5, 0)
		var target := p.global_position + Vector3(0, 0.8, 0) if p else global_position + Vector3(facing, 0, 0)
		var dir := (target - shot.global_position).normalized().rotated(Vector3.FORWARD, a)
		shot.speed = 8.0
		shot.fire(dir, self)


func is_vulnerable() -> bool:
	return state == State.STUCK or state == State.STUNNED


func apply_hit(hit: Hit) -> bool:
	if state == State.DEAD or state == State.WAIT or state == State.INTRO:
		return false
	if hit.kind == Hit.Kind.PROJECTILE and hit.source is Player:
		# Reflected shot: stun + damage.
		_damage(hit.damage)
		if state != State.DEAD:
			_rest_hook()
			_enter(State.STUNNED)
			Game.toast.emit("Stunned!")
		return true
	if not is_vulnerable():
		Sfx.play("land", 0.0)
		Game.toast.emit("Clang! Wait for an opening.")
		return false
	_damage(hit.damage)
	return true


func _damage(n: int) -> void:
	hp -= n
	Sfx.play("hit")
	Game.boss_changed.emit("Captain Varga Chainhook", maxi(hp, 0), max_hp)
	var tw := create_tween()
	tw.tween_property(visual, "scale", Vector3(1.08, 0.92, 1.08), 0.05)
	tw.tween_property(visual, "scale", Vector3.ONE, 0.1)
	if hp <= 0:
		_die()
	elif phase == 1 and hp <= max_hp / 2:
		phase = 2
		_rest_hook()
		_enter(State.IDLE)
		Game.toast.emit("Chainhook is furious!")


func _die() -> void:
	_enter(State.DEAD)
	hook.monitoring = false
	Game.grant(FLAG)
	Game.add_coins(50)
	Game.save_game()
	Game.boss_changed.emit("", 0, 0)
	Sfx.play("enemy_die")
	var tw := create_tween()
	tw.tween_property(visual, "rotation:z", -facing * 1.4, 0.6)
	tw.parallel().tween_property(visual, "position:y", -0.5, 0.6)
	await tw.finished
	await Game.say("Chainhook", PackedStringArray([
		"Beaten... by a barrel brat... my HAT! Mind the hat!",
	]))
	defeated.emit()
	var tw2 := create_tween()
	tw2.tween_property(self, "position:x", position.x + facing * -12.0, 1.2)
	tw2.parallel().tween_property(self, "position:y", position.y - 4.0, 1.2)
	tw2.tween_callback(queue_free)
