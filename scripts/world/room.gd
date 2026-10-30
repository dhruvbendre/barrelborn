class_name Room
extends Node3D
## Room root. Places the player from Game.pending_spawn (checkpoint position or a named
## Marker3D under SpawnPoints) and owns room-local objective text.

@export var objective := ""
@export var room_id := ""

@onready var player: Player = $Player


func _ready() -> void:
	var s: Variant = Game.pending_spawn
	Game.pending_spawn = null
	if s is Vector3:
		player.global_position = s
	elif s is String and has_node("SpawnPoints/" + s):
		player.global_position = get_node("SpawnPoints/" + s).global_position
	player.last_safe_position = player.global_position
	var cam := get_node_or_null("Camera") as SideCamera
	if cam:
		cam.snap()
	# A room's objective applies on the first visit; later progress text is kept on revisits.
	if objective != "" and room_id != "" and Game.grant("visited_" + room_id):
		Game.set_objective(objective)
	elif objective != "" and Game.objective == "":
		Game.set_objective(objective)
