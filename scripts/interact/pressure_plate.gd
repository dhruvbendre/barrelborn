class_name PressurePlate
extends Area3D
## Needs something heavy (a Carryable). Once weighted it locks down and sets `flag` for good,
## so the puzzle can never be undone into a softlock.

@export var flag := "plate_x"
@export var toast_text := "Click! Something opened."

@onready var _top: Node3D = get_node_or_null("Top")


func _ready() -> void:
	collision_layer = 0
	collision_mask = 3
	body_entered.connect(_on_body)
	if Game.has(flag) and _top:
		_top.position.y = -0.08


func _on_body(b: Node3D) -> void:
	if Game.has(flag):
		return
	if b is Carryable:
		Game.grant(flag)
		Game.save_game()
		Sfx.play("checkpoint")
		Game.toast.emit(toast_text)
		if _top:
			create_tween().tween_property(_top, "position:y", -0.08, 0.2)
	elif b is Player:
		Game.toast.emit("The plate barely moves. Something heavier?")
