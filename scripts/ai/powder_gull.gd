class_name PowderGull
extends CharacterBody3D
## Ranged gunner: waits -> aims (teal sight line, 0.7 s) -> fires a reflectable shot ->
## reloads (1.4 s). Hops back when the player gets close, but never off a ledge.

enum State { IDLE, AIM, FIRE, RELOAD, HOP, HURT, DEAD }

const SHOT := preload("res://scenes/enemies/projectile.tscn")

@export var max_hp := 2
@export var sight_range := 11.0
@export var aim_time := 0.7
@export var reload_time := 1.4
@export var flee_range := 2.6
@export var coins := 3

@onready var visual: Node3D = $Visual
@onready var sight: MeshInstance3D = $Visual/Sight
@onready var edge_ray: RayCast3D = $EdgeRay

var state := State.IDLE
var hp := 2
var facing := -1.0
var _t := 0.0
var _gravity := 30.0


const CLIPS := {State.IDLE: "idle", State.AIM: "aim", State.FIRE: "fire", State.RELOAD: "reload",
	State.HOP: "hop", State.HURT: "hurt", State.DEAD: "death"}

var _anim: ModelAnim


func _ready() -> void:
	hp = max_hp
	_anim = ModelAnim.find(visual)
	sight.visible = false


func _player() -> Player:
	return get_tree().get_first_node_in_group("player") as Player


func _physics_process(delta: float) -> void:
	_t += delta
	var p := _player()
	var see := _can_see(p)
	if p and state != State.DEAD:
		var dx := p.global_position.x - global_position.x
		if state in [State.IDLE, State.RELOAD, State.AIM]:
			facing = signf(dx) if dx != 0.0 else facing
	match state:
		State.IDLE:
			if see:
				if absf(p.global_position.x - global_position.x) < flee_range:
					_hop()
				else:
					_enter(State.AIM)
		State.AIM:
			sight.visible = fmod(_t, 0.14) < 0.09
			if not see:
				_enter(State.IDLE)
			elif _t >= aim_time:
				_enter(State.FIRE)
		State.FIRE:
			_fire(p)
			_enter(State.RELOAD)
		State.RELOAD:
			if _t >= reload_time:
				_enter(State.IDLE)
		State.HOP:
			if is_on_floor() and _t > 0.2:
				velocity.x = 0.0
				_enter(State.IDLE)
		State.HURT:
			if _t >= 0.35:
				_enter(State.IDLE)
	if state != State.HOP:
		velocity.x = move_toward(velocity.x, 0.0, 12.0 * delta)
	edge_ray.position.x = signf(velocity.x) * 0.5 if velocity.x != 0.0 else 0.0
	if state == State.HOP and is_on_floor() and _t > 0.05 and not edge_ray.is_colliding():
		velocity.x = 0.0
	if not is_on_floor():
		velocity.y -= _gravity * delta
	move_and_slide()
	position.z = 0.0
	velocity.z = 0.0
	if state != State.DEAD:
		visual.rotation.y = lerp_angle(visual.rotation.y, PI * 0.5 * facing, minf(delta * 10.0, 1.0))


func _can_see(p: Player) -> bool:
	if p == null or p.action == Player.Action.DEAD:
		return false
	var d := p.global_position - global_position
	if absf(d.x) > sight_range or absf(d.y) > 4.0:
		return false
	var q := PhysicsRayQueryParameters3D.create(global_position + Vector3.UP * 1.2, p.global_position + Vector3.UP, 1)
	return get_world_3d().direct_space_state.intersect_ray(q).is_empty()


func _enter(s: State) -> void:
	state = s
	_t = 0.0
	_anim.play(CLIPS.get(s, "idle"), s != State.IDLE)
	sight.visible = false
	if s == State.AIM:
		Sfx.play("enemy_windup")


func _hop() -> void:
	# Only hop if there is ground behind us.
	edge_ray.position.x = -facing * 1.2
	edge_ray.force_raycast_update()
	if edge_ray.is_colliding():
		velocity = Vector3(-facing * 4.0, 6.0, 0)
		_enter(State.HOP)
	else:
		_enter(State.AIM)


func _fire(p: Player) -> void:
	if p == null:
		return
	Sfx.play("hurt", 0.0)
	var shot: Projectile = SHOT.instantiate()
	get_parent().add_child(shot)
	shot.global_position = global_position + Vector3(facing * 0.8, 1.45, 0)
	# Aim at the player's chest (he often stands on a ledge above or below), forward only.
	var dir := (p.global_position + Vector3(0, 0.8, 0)) - shot.global_position
	dir.x = facing * maxf(absf(dir.x), 0.5)
	shot.fire(dir, self)


func apply_hit(hit: Hit) -> bool:
	if state == State.DEAD:
		return false
	hp -= hit.damage
	velocity = Vector3(hit.knockback.x * 0.6, 2.0, 0)
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
	var tw := create_tween()
	tw.tween_property(visual, "rotation:z", -facing * PI * 0.5, 0.3)
	tw.tween_interval(0.5)
	tw.tween_property(visual, "scale", Vector3.ONE * 0.01, 0.25)
	tw.tween_callback(queue_free)
