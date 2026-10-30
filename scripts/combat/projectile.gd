class_name Projectile
extends Area3D
## Enemy shot. Teal-white with a ring = reflectable: a well-timed slash sends it back
## and it then damages enemies (and stuns the boss). Hits the world -> pops.

@export var speed := 7.0
@export var damage := 1
@export var life := 4.0

var velocity := Vector3.ZERO
var reflected := false
var source: Node
var _t := 0.0


func _ready() -> void:
	collision_layer = 16
	collision_mask = 1 | 2 | 4
	body_entered.connect(_on_body)


func fire(dir: Vector3, src: Node) -> void:
	velocity = dir.normalized() * speed
	velocity.z = 0.0
	source = src


func _physics_process(delta: float) -> void:
	_t += delta
	global_position += velocity * delta
	global_position.z = 0.0
	rotate_z(delta * 6.0)
	if _t > life:
		queue_free()


## Called by the player's slash during its active window.
func reflect(facing: float, by: Node) -> void:
	if reflected:
		return
	reflected = true
	# Send it back along its incoming line, faster, so a reflected shot returns to the shooter.
	velocity = Vector3(facing * absf(velocity.x), -velocity.y, 0.0).normalized() * speed * 1.8
	source = by
	Sfx.play("coin", 0.0)
	Game.toast.emit("Reflected!")
	modulate_color(Color("fff3a0"))


func modulate_color(col: Color) -> void:
	for c in get_children():
		if c is MeshInstance3D:
			var m := StandardMaterial3D.new()
			m.albedo_color = col
			m.emission_enabled = true
			m.emission = col
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			c.material_override = m


func _on_body(b: Node3D) -> void:
	if b == source:
		return
	if b is Player:
		if not reflected:
			b.apply_hit(Hit.make(damage, Vector3(signf(velocity.x) * 5.0, 4.0, 0), Hit.Kind.PROJECTILE, self))
			pop()
		return
	if reflected and b.has_method("apply_hit") and not (b is Player):
		b.apply_hit(Hit.make(2, Vector3(signf(velocity.x) * 6.0, 3.0, 0), Hit.Kind.PROJECTILE, source, Hit.new_swing_id()))
		pop()
		return
	if not b.has_method("apply_hit"):
		pop()


func pop() -> void:
	set_deferred("monitoring", false)
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector3.ONE * 1.8, 0.08)
	tw.tween_callback(queue_free)
