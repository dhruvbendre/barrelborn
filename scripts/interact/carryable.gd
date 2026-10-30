class_name Carryable
extends RigidBody3D
## Barrel that can be lifted (Use), put down (Use) or thrown (Slash).
## Recovery: if it is lost below the room or left far off its lane, it returns home.

class Handle:
	extends Interactable
	var body: Carryable

@export var lost_below_y := -1.5

var handle: Handle
var _home := Vector3.ZERO
var _holder: Player


func _ready() -> void:
	_home = global_position
	axis_lock_linear_z = true
	axis_lock_angular_x = true
	axis_lock_angular_y = true
	freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
	mass = 4.0
	handle = Handle.new()
	handle.body = self
	handle.prompt = "Lift"
	var cs := CollisionShape3D.new()
	var sh := SphereShape3D.new()
	sh.radius = 0.95
	cs.shape = sh
	cs.position.y = 0.45
	handle.add_child(cs)
	add_child(handle)


func carry(p: Player) -> void:
	_holder = p
	freeze = true
	collision_layer = 0
	handle.disable()


func drop(pos: Vector3, vel: Vector3) -> void:
	_holder = null
	global_position = Vector3(pos.x, pos.y, 0)
	freeze = false
	collision_layer = 1
	linear_velocity = vel
	handle.enabled = true


func _physics_process(_d: float) -> void:
	if _holder:
		global_position = _holder.global_position + Vector3(0, 1.6, 0)
		return
	if global_position.y < lost_below_y:
		reset_home()


func reset_home() -> void:
	linear_velocity = Vector3.ZERO
	angular_velocity = Vector3.ZERO
	global_position = _home
	Game.toast.emit("The barrel bobbed back to where it started.")
