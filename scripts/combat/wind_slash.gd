class_name WindSlash
extends Area3D
## Gale wind slash: a fast crescent that flies straight, hits the first target
## (enemies, wind switches), cancels enemy shots, and dissipates on walls.

@export var speed := 15.0
@export var life := 0.75
@export var damage := 2

var dir := 1.0
var source: Node
var _t := 0.0
var _done := false


func _ready() -> void:
	collision_layer = 0
	collision_mask = 1 | 4 | 16
	body_entered.connect(_on_body)
	area_entered.connect(_on_area)


func launch(direction: float, src: Node) -> void:
	dir = direction
	source = src
	rotation.y = 0.0 if dir > 0 else PI


func _physics_process(delta: float) -> void:
	_t += delta
	global_position.x += dir * speed * delta
	global_position.z = 0.0
	var k := _t / life
	scale = Vector3.ONE * (1.0 + k * 0.3)
	if _t >= life:
		_finish()


func _on_body(b: Node3D) -> void:
	if _done or b == source:
		return
	if b.has_method("apply_hit"):
		b.apply_hit(Hit.make(damage, Vector3(dir * 7.0, 3.0, 0), Hit.Kind.WIND, source, Hit.new_swing_id()))
		Sfx.play("hit")
	_finish()


func _on_area(a: Area3D) -> void:
	if a is Projectile and not a.reflected:
		a.pop()


func _finish() -> void:
	if _done:
		return
	_done = true
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector3(1.6, 0.2, 1.6), 0.08)
	tw.tween_callback(queue_free)
