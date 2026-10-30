extends Control
## Draws HP as hearts (shape + fill, not color alone).

var hp := 5
var max_hp := 5


func _ready() -> void:
	Game.health_changed.connect(func(h: int, m: int) -> void:
		hp = h
		max_hp = m
		custom_minimum_size = Vector2(m * 34, 30)
		queue_redraw())
	hp = Game.hp
	max_hp = Game.max_hp
	custom_minimum_size = Vector2(max_hp * 34, 30)


func _draw() -> void:
	for i in max_hp:
		var c := Vector2(16 + i * 34, 15)
		_heart(c, 13.0, Color("1a1a24"))
		_heart(c, 10.5, Color("e2483d") if i < hp else Color("3a3a48"))


func _heart(c: Vector2, r: float, col: Color) -> void:
	draw_circle(c + Vector2(-r * 0.5, -r * 0.2), r * 0.55, col)
	draw_circle(c + Vector2(r * 0.5, -r * 0.2), r * 0.55, col)
	draw_colored_polygon(PackedVector2Array([c + Vector2(-r * 1.03, 0), c + Vector2(r * 1.03, 0), c + Vector2(0, r * 1.05)]), col)
