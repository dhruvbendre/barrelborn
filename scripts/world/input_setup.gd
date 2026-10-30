class_name InputSetup
extends RefCounted
## Registers default keyboard + gamepad bindings in code (version-proof, editable in one place).
## Touch buttons fire the same action names.

const ACTIONS := ["move_left", "move_right", "jump", "attack", "power", "interact", "pause"]


static func register() -> void:
	_bind("move_left", [KEY_A, KEY_LEFT], [JOY_BUTTON_DPAD_LEFT], [[JOY_AXIS_LEFT_X, -1.0]])
	_bind("move_right", [KEY_D, KEY_RIGHT], [JOY_BUTTON_DPAD_RIGHT], [[JOY_AXIS_LEFT_X, 1.0]])
	_bind("jump", [KEY_SPACE, KEY_W, KEY_UP, KEY_K], [JOY_BUTTON_A], [])
	_bind("attack", [KEY_J, KEY_X], [JOY_BUTTON_X], [])
	_bind("power", [KEY_L, KEY_C], [JOY_BUTTON_Y], [])
	_bind("interact", [KEY_E, KEY_S, KEY_DOWN], [JOY_BUTTON_B], [])
	_bind("pause", [KEY_ESCAPE, KEY_P], [JOY_BUTTON_START], [])


static func _bind(action: String, keys: Array, buttons: Array, axes: Array) -> void:
	if InputMap.has_action(action):
		return
	InputMap.add_action(action, 0.3)
	for k in keys:
		var e := InputEventKey.new()
		e.physical_keycode = k
		InputMap.action_add_event(action, e)
	for b in buttons:
		var e := InputEventJoypadButton.new()
		e.button_index = b
		InputMap.action_add_event(action, e)
	for a in axes:
		var e := InputEventJoypadMotion.new()
		e.axis = a[0]
		e.axis_value = a[1]
		InputMap.action_add_event(action, e)
