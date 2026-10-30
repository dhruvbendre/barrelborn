extends Node2D
## On-screen touch controls built on TouchScreenButton, which tracks each finger's
## index independently: releasing one button never releases another, and canceled
## touches release their action. Shown only on touchscreen devices (or with force_show).

@export var force_show := false
@export var button_radius := 58.0
@export var margin := 36.0

var _buttons := {}  # action -> TouchScreenButton
const LAYOUT := {
	# action: [anchor_right?, offset from bottom corner, label]
	"move_left": [false, Vector2(0, 0), "<"],
	"move_right": [false, Vector2(1.25, 0), ">"],
	"jump": [true, Vector2(0, 0), "JUMP"],
	"attack": [true, Vector2(1.25, 0.15), "SLASH"],
	"power": [true, Vector2(0.55, 1.15), "GALE"],
	"interact": [true, Vector2(1.8, 1.1), "USE"],
	"pause": [true, Vector2(0, 5.2), "II"],
}


func _ready() -> void:
	visible = force_show or DisplayServer.is_touchscreen_available()
	for action in LAYOUT:
		var b := TouchScreenButton.new()
		var shape := CircleShape2D.new()
		shape.radius = button_radius
		b.shape = shape
		b.action = action
		b.passby_press = action.begins_with("move_")
		add_child(b)
		_buttons[action] = b
	get_viewport().size_changed.connect(_layout)
	_layout()


func _layout() -> void:
	var size := get_viewport().get_visible_rect().size
	var step := button_radius * 2.0
	for action in LAYOUT:
		var spec: Array = LAYOUT[action]
		var off: Vector2 = spec[1] * step
		var x: float = (size.x - margin - button_radius - off.x) if spec[0] else (margin + button_radius + off.x)
		var y: float = size.y - margin - button_radius - off.y
		_buttons[action].position = Vector2(x, y)
	queue_redraw()


func _draw() -> void:
	var font := ThemeDB.fallback_font
	for action in _buttons:
		var b: TouchScreenButton = _buttons[action]
		var pressed := b.is_pressed()
		draw_circle(b.position, button_radius, Color(1, 1, 1, 0.28 if pressed else 0.14))
		draw_arc(b.position, button_radius, 0, TAU, 40, Color(1, 1, 1, 0.5), 2.0)
		var label: String = LAYOUT[action][2]
		var sz := font.get_string_size(label, HORIZONTAL_ALIGNMENT_CENTER, -1, 20)
		draw_string(font, b.position + Vector2(-sz.x * 0.5, 7), label, HORIZONTAL_ALIGNMENT_CENTER, -1, 20)


func _process(_d: float) -> void:
	if visible:
		queue_redraw()
