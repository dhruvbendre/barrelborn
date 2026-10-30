class_name Player
extends CharacterBody3D
## Kito. Locomotion (run/jump/fall) is independent of the action state
## (slash/cast/hurt/dead), so the two never multiply into one giant state machine.

signal died

enum Action { NONE, SLASH, CAST, HURT, DEAD }

@export var tuning: PlayerTuning = preload("res://resources/tuning/player_tuning.tres")
@export var can_double_jump := true
## Debug/test override; in the chapter the cutlass must be picked up first.
@export var force_sword := false

const WIND_SLASH := preload("res://scenes/player/wind_slash.tscn")
const SPIRIT_COST := 1.0
const SPIRIT_REGEN := 0.35  # per second; gates can never softlock on an empty meter

@onready var visual: Node3D = $Visual
@onready var attack_area: Area3D = $AttackArea

var facing := 1.0
var action := Action.NONE
var action_time := 0.0
var control_enabled := true
var last_safe_position := Vector3.ZERO

var _coyote := 0.0
var _jump_buffer := 0.0
var _attack_buffer := 0.0
var _air_jumps := 1
var _invuln := 0.0
var _swing_id := 0
var _hit_this_swing: Dictionary = {}
var _was_on_floor := true
var _anim: AnimationPlayer
var _current_anim := ""
var _interactables: Array[Interactable] = []
var carried: Carryable = null
var _trail: MeshInstance3D
var _cutlass: Node3D


func _ready() -> void:
	last_safe_position = global_position
	_anim = visual.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if _anim:
		for loop_name in ["idle", "run", "fall"]:
			if _anim.has_animation(loop_name):
				_anim.get_animation(loop_name).loop_mode = Animation.LOOP_LINEAR
	_trail = _make_trail()
	# The model carries the cutlass; show it only once Kito actually owns one.
	_cutlass = visual.find_child("Cutlass", true, false) as Node3D
	_sync_cutlass()
	Game.flag_granted.connect(func(_id: String) -> void: _sync_cutlass())


func _physics_process(delta: float) -> void:
	var t := tuning
	_tick_timers(delta)
	var on_floor := is_on_floor()

	# --- input ---
	var input_x := 0.0
	if control_enabled and not Game.in_dialogue and action != Action.HURT and action != Action.DEAD:
		input_x = Input.get_axis("move_left", "move_right")
		if Input.is_action_just_pressed("jump"):
			_jump_buffer = t.jump_buffer
		if Input.is_action_just_pressed("attack"):
			if carried:
				_throw()
			elif has_sword():
				_attack_buffer = t.attack_buffer
		if Input.is_action_just_pressed("power"):
			_try_wind_slash()
		if Input.is_action_just_pressed("interact"):
			_try_interact()
	Game.regen_spirit(SPIRIT_REGEN * delta)

	# --- horizontal ---
	if action != Action.HURT:
		var speed := t.run_speed
		if (action == Action.SLASH or action == Action.CAST) and on_floor:
			speed *= t.attack_move_mult
		var accel := t.ground_accel if on_floor else t.air_accel
		if on_floor and is_zero_approx(input_x):
			accel = t.ground_decel
		velocity.x = move_toward(velocity.x, input_x * speed, accel * delta)
		if not is_zero_approx(input_x) and action != Action.SLASH and action != Action.CAST:
			facing = signf(input_x)

	# --- vertical ---
	if on_floor:
		_coyote = t.coyote_time
		_air_jumps = 1 if can_double_jump else 0
	else:
		var g := t.gravity() * (t.fall_gravity_mult if velocity.y < 0.0 else 1.0)
		velocity.y = maxf(velocity.y - g * delta, -t.max_fall_speed)

	if _jump_buffer > 0.0 and action != Action.DEAD and action != Action.HURT and not Game.in_dialogue:
		if _coyote > 0.0:
			_do_jump(t.jump_velocity())
		elif _air_jumps > 0:
			_air_jumps -= 1
			_do_jump(t.double_jump_velocity())

	if Input.is_action_just_released("jump") and velocity.y > 0.0:
		velocity.y *= t.jump_cut

	# --- actions ---
	if _attack_buffer > 0.0 and (action == Action.NONE or _slash_in_recovery()):
		_start_slash()
	_update_action(delta)

	move_and_slide()
	# Enforce the gameplay plane: contacts must never push actors out of the lane.
	position.z = 0.0
	velocity.z = 0.0
	if is_on_ceiling() and velocity.y > 0.0:
		velocity.y = 0.0

	if is_on_floor():
		if not _was_on_floor:
			_on_landed()
		if get_platform_velocity().is_zero_approx():
			last_safe_position = global_position
	_was_on_floor = is_on_floor()
	_update_visual(delta)


func _tick_timers(delta: float) -> void:
	_coyote -= delta
	_jump_buffer -= delta
	_attack_buffer -= delta
	_invuln -= delta
	action_time += delta


func _do_jump(v: float) -> void:
	velocity.y = v
	_coyote = 0.0
	_jump_buffer = 0.0
	_play("jump", true)


func _on_landed() -> void:
	visual.scale = Vector3(1.15, 0.85, 1.15)  # squash; eased back in _update_visual


# --- slash -----------------------------------------------------------------

func _slash_window() -> float:
	return tuning.slash_startup + tuning.slash_active + tuning.slash_recovery


func _slash_in_recovery() -> bool:
	return action == Action.SLASH and action_time >= tuning.slash_startup + tuning.slash_active


func _start_slash() -> void:
	_attack_buffer = 0.0
	action = Action.SLASH
	action_time = 0.0
	_swing_id = Hit.new_swing_id()
	_hit_this_swing.clear()
	attack_area.position.x = facing * absf(attack_area.position.x)
	_play("air_slash" if not is_on_floor() else "slash", true)
	Sfx.play("swing")
	_show_trail()


func _update_action(_delta: float) -> void:
	match action:
		Action.SLASH:
			var t := tuning
			if action_time >= t.slash_startup and action_time < t.slash_startup + t.slash_active:
				_apply_slash_hits()
			if action_time >= _slash_window():
				action = Action.NONE
		Action.HURT:
			if action_time >= tuning.hurt_stun:
				action = Action.NONE
		Action.CAST:
			if action_time >= 0.3:
				action = Action.NONE


## One hit per target per swing, however many physics frames the overlap lasts.
func _apply_slash_hits() -> void:
	for area in attack_area.get_overlapping_areas():
		if area.has_method("reflect") and not _hit_this_swing.has(area):
			_hit_this_swing[area] = true
			area.reflect(facing, self)
			Game.hitstop(tuning.hitstop)
	for body in attack_area.get_overlapping_bodies():
		if body == self or _hit_this_swing.has(body) or not body.has_method("apply_hit"):
			continue
		_hit_this_swing[body] = true
		var kb := Vector3(facing * tuning.slash_knockback, 2.0, 0.0)
		if body.apply_hit(Hit.make(tuning.slash_damage, kb, Hit.Kind.SLASH, self, _swing_id)):
			Game.hitstop(tuning.hitstop)
			Sfx.play("hit")


func swing_hit_count() -> int:
	return _hit_this_swing.size()


# --- abilities / interaction ----------------------------------------------

func has_sword() -> bool:
	return force_sword or Game.has("item_cutlass")


func _sync_cutlass() -> void:
	if _cutlass:
		_cutlass.visible = has_sword()


func _try_wind_slash() -> void:
	if carried or not Game.has("ability_wind_slash"):
		return
	if action != Action.NONE and not _slash_in_recovery():
		return
	if not Game.use_spirit(SPIRIT_COST):
		Game.toast.emit("Not enough Spirit - it refills over time")
		return
	action = Action.CAST
	action_time = 0.0
	_play("cast", true)
	Sfx.play("swing", 0.0)
	var w: Node3D = WIND_SLASH.instantiate()
	get_parent().add_child(w)
	w.global_position = global_position + Vector3(facing * 0.7, 0.85, 0)
	w.launch(facing, self)


func set_interactable(i: Interactable) -> void:
	if not _interactables.has(i):
		_interactables.append(i)
	_refresh_prompt()


func clear_interactable(i: Interactable) -> void:
	_interactables.erase(i)
	_refresh_prompt()


func _refresh_prompt() -> void:
	var p := ""
	if carried:
		p = "Use: put down   Slash: throw"
	elif not _interactables.is_empty():
		p = "Use: " + _interactables.back().prompt
	Game.prompt_changed.emit(p)


func _try_interact() -> void:
	if carried:
		_place()
		return
	_interactables = _interactables.filter(func(i: Interactable) -> bool: return is_instance_valid(i) and i.enabled)
	if _interactables.is_empty():
		_refresh_prompt()
		return
	var target: Interactable = _interactables.back()
	_play("interact", true)
	if target is Carryable.Handle:
		_pick_up(target.body)
	else:
		target.interact(self)
	_refresh_prompt()


func _pick_up(c: Carryable) -> void:
	carried = c
	c.carry(self)
	_refresh_prompt()


func _place() -> void:
	var c := carried
	carried = null
	c.drop(global_position + Vector3(facing * 0.9, 0.2, 0), Vector3.ZERO)
	_refresh_prompt()


func _throw() -> void:
	var c := carried
	carried = null
	c.drop(global_position + Vector3(facing * 0.7, 1.3, 0), Vector3(facing * 7.0, 4.0, 0))
	Sfx.play("swing")
	_refresh_prompt()


func face_toward(x: float) -> void:
	if absf(x - global_position.x) > 0.05:
		facing = signf(x - global_position.x)


func play_victory() -> void:
	_play("victory", true)


# --- damage ----------------------------------------------------------------

func is_invulnerable() -> bool:
	return _invuln > 0.0 or action == Action.DEAD


func apply_hit(hit: Hit) -> bool:
	if is_invulnerable():
		return false
	if carried:
		_place()
	var left := Game.damage(hit.damage)
	Sfx.play("hurt")
	var dir := signf(global_position.x - hit.source.global_position.x) if hit.source is Node3D else -facing
	if dir == 0.0:
		dir = -facing
	velocity = Vector3(dir * tuning.hurt_knockback.x, tuning.hurt_knockback.y, 0.0)
	_invuln = tuning.hurt_invuln
	action = Action.HURT
	action_time = 0.0
	_play("hurt", true)
	if left <= 0:
		_die()
	return true


## Water/void: take damage and return to the last safe ground, or die.
func fall_into_hazard(dmg: int) -> void:
	if action == Action.DEAD:
		return
	if Game.damage(dmg) <= 0:
		_die()
		return
	Sfx.play("hurt")
	global_position = last_safe_position + Vector3(0, 0.1, 0)
	velocity = Vector3.ZERO
	_invuln = tuning.hurt_invuln


func _die() -> void:
	if carried:
		_place()
	action = Action.DEAD
	action_time = 0.0
	control_enabled = false
	_play("death", true)
	died.emit()
	await get_tree().create_timer(1.2).timeout
	Game.respawn()


# --- presentation ----------------------------------------------------------

func _update_visual(delta: float) -> void:
	# Model is authored facing +Z; yaw it toward the facing direction with a quick turn.
	var target_yaw := PI * 0.5 * facing
	visual.rotation.y = lerp_angle(visual.rotation.y, target_yaw, minf(delta * 18.0, 1.0))
	visual.scale = visual.scale.lerp(Vector3.ONE, minf(delta * 12.0, 1.0))
	# Flicker while invulnerable (non-color feedback).
	visual.visible = _invuln <= 0.0 or action == Action.DEAD or fmod(_invuln, 0.12) > 0.05
	if _trail.visible:
		_trail.position.x = facing * 0.55
		_trail.rotation.y = 0.0 if facing > 0 else PI
	if action == Action.NONE:
		if carried and is_on_floor():
			_play("carry_move" if absf(velocity.x) > 0.5 else "carry_idle")
		elif not is_on_floor():
			_play("jump" if velocity.y > 0.0 else "fall")
		elif absf(velocity.x) > 0.5:
			_play("run")
		else:
			_play("idle")


func _play(anim_name: String, restart := false) -> void:
	if _anim == null or not _anim.has_animation(anim_name):
		return
	if anim_name == _current_anim and not restart:
		return
	_current_anim = anim_name
	_anim.play(anim_name, 0.08)
	if restart:
		_anim.seek(0.0, true)


## Restrained slash trail: a thin additive crescent shown only during the active window.
func _make_trail() -> MeshInstance3D:
	var arc := ImmediateMesh.new()
	arc.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
	for i in 13:
		var a := lerpf(-1.1, 1.2, i / 12.0)
		var fade := sin(PI * i / 12.0)
		arc.surface_set_color(Color(1, 1, 1, 0.0))
		arc.surface_add_vertex(Vector3(cos(a) * 0.55, sin(a) * 0.55, 0))
		arc.surface_set_color(Color(0.85, 0.97, 1.0, 0.75 * fade))
		arc.surface_add_vertex(Vector3(cos(a) * 1.0, sin(a) * 1.0, 0))
	arc.surface_end()
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.vertex_color_use_as_albedo = true
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	var mi := MeshInstance3D.new()
	mi.mesh = arc
	mi.material_override = m
	mi.position = Vector3(0.55, 0.85, 0.05)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.visible = false
	add_child(mi)
	return mi


func _show_trail() -> void:
	_trail.visible = true
	_trail.scale = Vector3(1, -1 if not is_on_floor() else 1, 1)
	await get_tree().create_timer(tuning.slash_startup + tuning.slash_active + 0.04, false).timeout
	_trail.visible = false
