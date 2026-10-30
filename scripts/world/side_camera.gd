class_name SideCamera
extends Camera3D
## Stable side camera: horizontal look-ahead + dead zone, bounded vertical tracking
## (re-centres on landing, not on every hop), room limits, optional boss framing.

@export var target_path: NodePath
@export var distance := 10.5
@export var height := 2.8
@export var pitch_deg := -11.0
@export var look_ahead := 2.0
@export var dead_zone_x := 0.5
@export var follow_x := 5.0
@export var follow_y := 3.0
@export var air_band_up := 2.6
@export var air_band_down := 1.4
@export var limit_min := Vector2(-INF, -INF)
@export var limit_max := Vector2(INF, INF)

var frame_override: Variant = null  # Vector3 focus for boss framing, or null

var _target: Node3D
var _focus := Vector3.ZERO
var _ahead := 0.0


func _ready() -> void:
	_target = get_node_or_null(target_path)
	if _target:
		_focus = _target.global_position
	rotation_degrees = Vector3(pitch_deg, 0, 0)
	snap()


func snap() -> void:
	if _target:
		_focus = _target.global_position
	_apply(1.0)


func _physics_process(delta: float) -> void:
	if _target == null:
		return
	var tp := _target.global_position
	if frame_override is Vector3:
		tp = frame_override
	else:
		var f: float = _target.get("facing") if _target.get("facing") != null else 1.0
		_ahead = move_toward(_ahead, f * look_ahead, delta * 3.0)
		tp.x += _ahead
	# Horizontal dead zone.
	var dx := tp.x - _focus.x
	if absf(dx) > dead_zone_x:
		_focus.x = lerpf(_focus.x, tp.x - signf(dx) * dead_zone_x, minf(delta * follow_x, 1.0))
	# Vertical: follow when grounded or when leaving the band.
	var grounded: bool = _target is CharacterBody3D and (_target as CharacterBody3D).is_on_floor()
	var dy := tp.y - _focus.y
	if grounded or dy > air_band_up or dy < -air_band_down:
		_focus.y = lerpf(_focus.y, tp.y, minf(delta * follow_y, 1.0))
	_apply(delta)


func _apply(_delta: float) -> void:
	var p := _focus
	p.x = clampf(p.x, limit_min.x, limit_max.x)
	p.y = clampf(p.y, limit_min.y, limit_max.y)
	global_position = Vector3(p.x, p.y + height, distance)
