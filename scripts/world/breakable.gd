class_name Breakable
extends StaticBody3D
## Crate/barrel. Breaks on any hit, scatters debris, optionally pays coins once per reward_id.

@export var coins := 0
@export var reward_id := ""  # non-empty => breaking is permanent and the payout happens once
@export var wind_only := false  # cracked boulders: only the Gale wind slash breaks them


func _ready() -> void:
	if reward_id != "" and Game.has(reward_id):
		queue_free()


func apply_hit(hit: Hit) -> bool:
	if wind_only and hit.kind != Hit.Kind.WIND:
		Sfx.play("land")
		Game.toast.emit("Too solid for a cutlass alone.")
		return false
	_break()
	return true


func _break() -> void:
	Sfx.play("break")
	if reward_id == "" or Game.grant(reward_id):
		if coins > 0:
			Game.add_coins(coins)
			Sfx.play("coin")
	_spawn_debris()
	queue_free()


func _spawn_debris() -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("8a5a36")
	for i in 6:
		var m := MeshInstance3D.new()
		var b := BoxMesh.new()
		b.size = Vector3(0.25, 0.08, 0.25)
		m.mesh = b
		m.material_override = mat
		get_parent().add_child(m)
		m.global_position = global_position + Vector3(randf_range(-0.3, 0.3), 0.5, randf_range(-0.3, 0.3))
		var tw := m.create_tween()
		var to := m.global_position + Vector3(randf_range(-1.2, 1.2), randf_range(0.4, 1.2), 0)
		tw.tween_property(m, "global_position", to, 0.18).set_ease(Tween.EASE_OUT)
		tw.tween_property(m, "global_position:y", global_position.y - 0.4, 0.35).set_ease(Tween.EASE_IN)
		tw.parallel().tween_property(m, "scale", Vector3.ZERO, 0.35)
		tw.tween_callback(m.queue_free)
