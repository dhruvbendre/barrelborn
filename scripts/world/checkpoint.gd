class_name Checkpoint
extends Area3D
## Touch to set respawn + save + full heal. The flag cloth turns coral when active.

@export var flag_path: NodePath = ^"Flag"

var _active := false


func _ready() -> void:
	body_entered.connect(_on_body)
	var room := owner.scene_file_path if owner else ""
	_set_active(Game.checkpoint.room == room and absf(Game.checkpoint.x - global_position.x) < 0.5)


func _on_body(body: Node3D) -> void:
	if body is Player and not _active:
		Game.set_checkpoint(owner.scene_file_path, global_position + Vector3(0, 0.2, 0))
		Game.toast.emit("Checkpoint")
		Sfx.play("checkpoint")
		_set_active(true)


func _set_active(on: bool) -> void:
	_active = on
	var flag := get_node_or_null(flag_path) as MeshInstance3D
	if flag:
		var m := StandardMaterial3D.new()
		m.albedo_color = Color("e2483d") if on else Color("8a8a8a")
		flag.material_override = m
