class_name MovingPlatform
extends AnimatableBody3D
## Ping-pongs between its start position and start + offset. sync_to_physics lets
## CharacterBody3D riders inherit its motion.

@export var offset := Vector3(6, 0, 0)
@export var period := 4.0

var _origin := Vector3.ZERO
var _t := 0.0


func _ready() -> void:
	_origin = position
	sync_to_physics = true


func _physics_process(delta: float) -> void:
	_t += delta
	var k := 0.5 - 0.5 * cos(TAU * _t / period)
	position = _origin + offset * k
