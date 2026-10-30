extends Control
## Real end-of-chapter state (saved before this screen). Next island is honestly marked unbuilt.


func _ready() -> void:
	var treasure := 1 if Game.has("harbor_secret_chest") else 0
	%Summary.text = "Coins: %d     Hearts: %d     Secret treasure: %d / 1\nCrew: Kito (captain), Sol (navigator)" % [Game.coins, Game.max_hp, treasure]
	%Return.pressed.connect(func() -> void: Game.respawn())
	%Title.pressed.connect(func() -> void: get_tree().change_scene_to_file(Game.TITLE))
	%Return.grab_focus()
	Sfx.play("checkpoint")
