class_name BilgeBrute
extends CharacterBody3D
## Melee deckhand: patrol -> detect -> approach -> telegraph (club raised) -> strike -> recover.
## Never walks off platform edges or through walls; detection needs line of sight.

enum State { PATROL, APPROACH, TELEGRAPH, STRIKE, RECOVER, HURT, DEAD }

@export var max_hp := 3
@export var walk_speed := 1.4
@export var chase_speed := 2.4
@export var patrol_range := 3.0
@export var detect_range := 7.0
@export var attack_range := 1.5
@export var telegraph_time := 0.5
@export var strike_time := 0.15
@export var recover_time := 0.7
@export var hurt_time := 0.3
@export var coins := 2

@onready var visual: Node3D = $Visual
@onready var strike_area: Area3D = $StrikeArea
@onready var edge_ray: RayCast3D = $EdgeRay
@onready var club: Node3D = get_node_or_null("Visual/Club")

var state := State.PATROL
var hp := 3
var facing := -1.0
var _t := 0.0
var _home := 0.0
var _struck := false
var _gravity := 30.0


const CLIPS := {State.PATROL: "walk", State.APPROACH: "walk", State.TELEGRAPH: "windup",
	State.STRIKE: "strike", State.RECOVER: "recover", State.HURT: "hurt", State.DEAD: "death"}

var _anim: ModelAnim


func _ready() -> void:
	hp = max_hp
	_anim = ModelAnim.find(visual)
	_home = global_position.x


func _player() -> Player:
	return get_tree().get_first_node_in_group("player") as Player


func _physics_process(delta: float) -> void:
	_t += delta
	var p := _player()
	var target_vx := 0.0
	match state:
		State.PATROL:
			if global_position.x > _home + patrol_range:
				facing = -1.0
			elif global_position.x < _home - patrol_range:
				facing = 1.0
			target_vx = facing * walk_speed
			if _can_see(p):
				_enter(State.APPROACH)
		State.APPROACH:
			if p == null or not _can_see(p, detect_range * 1.4):
				_enter(State.PATROL)
			else:
				var dx := p.global_position.x - global_position.x
				facing = signf(dx) if dx != 0.0 else facing
				if absf(dx) <= attack_range:
					_enter(State.TELEGRAPH)
				else:
					target_vx = facing * chase_speed
		State.TELEGRAPH:
			if _t >= telegraph_time:
				_enter(State.STRIKE)
		State.STRIKE:
			if not _struck:
				_strike()
			if _t >= strike_time:
				_enter(State.RECOVER)
		State.RECOVER:
			if _t >= recover_time:
				_enter(State.APPROACH)
		State.HURT:
			if _t >= hurt_time:
				_enter(State.APPROACH)
		State.DEAD:
			pass

	# Edge/wall guard: stop rather than walk off a ledge.
	edge_ray.position.x = facing * 0.6
	if target_vx != 0.0 and (not edge_ray.is_colliding() or is_on_wall()):
		target_vx = 0.0
		if state == State.PATROL:
			facing = -facing
	if state != State.HURT:
		velocity.x = move_toward(velocity.x, target_vx, 20.0 * delta)
	else:
		velocity.x = move_toward(velocity.x, 0.0, 25.0 * delta)
	if not is_on_floor():
		velocity.y -= _gravity * delta
	move_and_slide()
	position.z = 0.0
	velocity.z = 0.0
	_present(delta)


func _can_see(p: Player, range_m := detect_range) -> bool:
	if p == null or p.action == Player.Action.DEAD:
		return false
	var d := p.global_position - global_position
	if absf(d.x) > range_m or absf(d.y) > 2.5:
		return false
	var q := PhysicsRayQueryParameters3D.create(global_position + Vector3.UP, p.global_position + Vector3.UP, 1)
	return get_world_3d().direct_space_state.intersect_ray(q).is_empty()


func _enter(s: State) -> void:
	state = s
	_t = 0.0
	_struck = false
	_anim.play(CLIPS.get(s, "idle"), true)
	if s == State.TELEGRAPH:
		Sfx.play("enemy_windup")


func _strike() -> void:
	_struck = true
	strike_area.position.x = facing * absf(strike_area.position.x)
	for body in strike_area.get_overlapping_bodies():
		if body is Player:
			body.apply_hit(Hit.make(1, Vector3(facing * 6, 5, 0), Hit.Kind.ENEMY, self))


func apply_hit(hit: Hit) -> bool:
	if state == State.DEAD:
		return false
	hp -= hit.damage
	velocity = Vector3(hit.knockback.x, maxf(hit.knockback.y, 0.0), 0)
	if hp <= 0:
		_die()
	else:
		_enter(State.HURT)
	return true


func kill() -> void:
	if state != State.DEAD:
		_die()


func _die() -> void:
	_enter(State.DEAD)
	Sfx.play("enemy_die")
	collision_layer = 0
	if coins > 0:
		Game.add_coins(coins)
		Sfx.play("coin")
	var tw := create_tween()
	tw.tween_property(visual, "rotation:z", -facing * PI * 0.5, 0.35)
	tw.parallel().tween_property(visual, "position:y", -0.3, 0.35)
	tw.tween_interval(0.6)
	tw.tween_property(visual, "scale", Vector3(0.01, 0.01, 0.01), 0.25)
	tw.tween_callback(queue_free)


func _present(delta: float) -> void:
	if state != State.DEAD:
		visual.rotation.y = lerp_angle(visual.rotation.y, PI * 0.5 * facing, minf(delta * 10.0, 1.0))
	if _anim.player and (state == State.PATROL or state == State.APPROACH):
		_anim.play("walk" if absf(velocity.x) > 0.2 else "idle")
	# Telegraph cue readable without color: club rises and body leans back; flash on top.
	# (Procedural club only on the proxy; a rigged model animates its own weapon.)
	if club and _anim.player == null:
		var target := 0.0
		match state:
			State.TELEGRAPH: target = -1.0
			State.STRIKE: target = 1.7
			State.RECOVER: target = 1.5
		club.rotation.x = lerp_angle(club.rotation.x, target, minf(delta * 16.0, 1.0))
	var flash := state == State.TELEGRAPH and fmod(_t, 0.16) < 0.08
	visual.scale = Vector3.ONE * (1.08 if flash else 1.0)
	if state == State.HURT:
		visual.position.x = sin(_t * 80.0) * 0.05
	else:
		visual.position.x = 0.0
