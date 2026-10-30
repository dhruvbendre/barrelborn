extends Control
## Title: New Game (destructive, confirms if a save exists), Continue (only when valid).

@onready var cont: Button = %Continue
@onready var new_btn: Button = %NewGame
@onready var status: Label = %Status

var _confirm_new := false


func _ready() -> void:
	cont.disabled = not Game.has_save()
	cont.pressed.connect(_on_continue)
	new_btn.pressed.connect(_on_new)
	%Quit.pressed.connect(func() -> void: get_tree().quit())
	(cont if not cont.disabled else new_btn).grab_focus()
	if OS.has_feature("web"):
		%Quit.visible = false


func _on_continue() -> void:
	Sfx.play("ui")
	if not Game.continue_game():
		status.text = "Save data could not be read. Start a New Game."
		cont.disabled = true


func _on_new() -> void:
	Sfx.play("ui")
	if Game.has_save() and not _confirm_new:
		_confirm_new = true
		new_btn.text = "Overwrite save? Press again"
		return
	Game.new_game()
