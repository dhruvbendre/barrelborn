class_name Pickup
extends Interactable
## Permanent item/ability pickup. Grants `flag` once; never respawns after that.
## Story rewards are saved immediately so death right after pickup keeps them.

@export var flag := "item_cutlass"
@export var toast_text := "Got the Cutlass!"
@export_multiline var hint := ""
@export var auto_collect := false
@export var objective_after := ""


func _ready() -> void:
	super()
	prompt = "Take"
	if Game.has(flag):
		queue_free()
		return
	if auto_collect:
		body_entered.connect(func(b: Node3D) -> void:
			if b is Player:
				_on_interact(b))


func _process(delta: float) -> void:
	rotate_y(delta * 1.5)


func _on_interact(player: Player) -> void:
	if not Game.grant(flag):
		return
	disable()
	Sfx.play("checkpoint")
	Game.toast.emit(toast_text)
	Game.save_game()
	player.play_victory()
	if hint != "":
		await Game.say("", PackedStringArray(hint.split("\n", false)))
	if objective_after != "":
		Game.set_objective(objective_after)
	queue_free()
