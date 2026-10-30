class_name Door
extends Interactable
## Press Use to go through (cave mouths, tunnels, gangplanks). Optional `requires` flag.

@export_file("*.tscn") var target_room := ""
@export var target_spawn := "Start"
@export var requires := ""
@export var locked_text := ""


func _ready() -> void:
	super()
	if prompt == "Use":
		prompt = "Enter"


func _on_interact(_p: Player) -> void:
	if requires != "" and not Game.has(requires):
		Game.toast.emit(locked_text if locked_text != "" else "It won't budge.")
		return
	Game.change_room(target_room, target_spawn)
