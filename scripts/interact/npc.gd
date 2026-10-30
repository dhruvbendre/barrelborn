class_name Npc
extends Interactable
## Talk to show lines. `after_flag`/`after_lines` let the same NPC say something new later.
## `grant_on_talk` grants a flag the first time the lines are finished.

@export var speaker := "Bastian"
@export_multiline var lines := ""
@export var after_flag := ""
@export_multiline var after_lines := ""
@export var grant_on_talk := ""


var _anim: ModelAnim


func _ready() -> void:
	super()
	if prompt == "Use":
		prompt = "Talk" if speaker != "" else "Read"
	_anim = ModelAnim.find(self)
	_anim.play("idle")


func _on_interact(player: Player) -> void:
	var text := after_lines if after_flag != "" and Game.has(after_flag) and after_lines != "" else lines
	player.face_toward(global_position.x)
	_anim.play("talk")
	await Game.say(speaker, PackedStringArray(text.split("\n", false)))
	_anim.play("idle")
	if grant_on_talk != "":
		Game.grant(grant_on_talk)
