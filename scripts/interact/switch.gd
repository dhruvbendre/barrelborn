class_name HitSwitch
extends StaticBody3D
## Struck by a slash or wind slash -> sets `flag` permanently. `wind_only` switches are
## out of reach / armored, so only the Gale wind slash triggers them.

signal activated

@export var flag := "switch_x"
@export var wind_only := false
@export var toast_text := ""

@onready var _gem: MeshInstance3D = get_node_or_null("Gem")


func _ready() -> void:
	_paint(Game.has(flag))


func apply_hit(hit: Hit) -> bool:
	if Game.has(flag):
		return false
	if wind_only and hit.kind != Hit.Kind.WIND:
		Sfx.play("land")
		Game.toast.emit("It's out of reach of a normal slash.")
		return false
	Game.grant(flag)
	Game.save_game()
	Sfx.play("checkpoint")
	if toast_text != "":
		Game.toast.emit(toast_text)
	_paint(true)
	activated.emit()
	return true


func _paint(on: bool) -> void:
	if _gem:
		var m := StandardMaterial3D.new()
		m.albedo_color = Color("7ff3ff") if on else Color("ff7a2f")
		m.emission_enabled = true
		m.emission = m.albedo_color
		m.emission_energy_multiplier = 1.2 if on else 0.5
		_gem.material_override = m
