class_name Gate
extends AnimatableBody3D
## Solid until `flag` is set, then slides up out of the way (and stays open on revisit).

@export var flag := "switch_x"
@export var lift := 3.2
@export var open_time := 0.6

var _closed_y := 0.0
var _open := false


func _ready() -> void:
	_closed_y = position.y
	if Game.has(flag):
		_open = true
		position.y = _closed_y + lift
	Game.flag_granted.connect(func(id: String) -> void:
		if id == flag:
			_open_now())


func _open_now() -> void:
	if not _open:
		_open = true
		Sfx.play("break")
		create_tween().tween_property(self, "position:y", _closed_y + lift, open_time).set_trans(Tween.TRANS_BACK)
