class_name RoomExit
extends Area3D
## Walk into it to change room. Optional `requires` flag; shows `locked_text` otherwise.

@export_file("*.tscn") var target_room := ""
@export var target_spawn := "Start"
@export var requires := ""
@export var locked_text := ""

var _used := false


func _ready() -> void:
	collision_layer = 0
	collision_mask = 2
	body_entered.connect(_on_body)


func _on_body(body: Node3D) -> void:
	if not body is Player or _used:
		return
	if requires != "" and not Game.has(requires):
		if locked_text != "":
			Game.toast.emit(locked_text)
		return
	_used = true
	Game.change_room(target_room, target_spawn)
