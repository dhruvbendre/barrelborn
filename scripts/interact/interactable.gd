class_name Interactable
extends Area3D
## Player-facing "press Use" object. Registers itself with the player on overlap; the
## player calls interact() on the Use action. Subclasses override _on_interact().

@export var prompt := "Use"
@export var enabled := true

var _player: Player


func _ready() -> void:
	collision_layer = 8
	collision_mask = 2
	monitorable = false
	body_entered.connect(_on_enter)
	body_exited.connect(_on_exit)


func _on_enter(body: Node3D) -> void:
	if body is Player and enabled:
		_player = body
		body.set_interactable(self)


func _on_exit(body: Node3D) -> void:
	if body is Player:
		_player = null
		body.clear_interactable(self)


func interact(player: Player) -> void:
	if enabled:
		_on_interact(player)


func _on_interact(_player_: Player) -> void:
	pass


func disable() -> void:
	enabled = false
	if _player:
		_player.clear_interactable(self)
