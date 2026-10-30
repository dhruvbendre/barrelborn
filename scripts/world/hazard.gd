class_name Hazard
extends Area3D
## Water / void / spikes. Player loses `damage` and returns to last safe ground.

@export var damage := 1


func _ready() -> void:
	body_entered.connect(_on_body)


func _on_body(body: Node3D) -> void:
	if body is Player:
		body.fall_into_hazard(damage)
	elif body.has_method("kill"):
		body.kill()
