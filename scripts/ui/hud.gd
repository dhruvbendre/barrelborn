extends CanvasLayer
## HUD + pause menu. Listens to Game signals only.

@onready var spirit: ProgressBar = %Spirit
@onready var coins: Label = %Coins
@onready var objective: Label = %Objective
@onready var toast: Label = %Toast
@onready var pause_menu: Control = %PauseMenu
@onready var prompt: Label = %Prompt
@onready var dialogue: Control = %Dialogue

var _lines: PackedStringArray = []
var _line_i := 0
var _dlg_guard := 0.0
var _speaker := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	Game.spirit_changed.connect(_on_spirit)
	Game.coins_changed.connect(func(c: int) -> void: coins.text = "%d" % c)
	Game.objective_changed.connect(func(t: String) -> void: objective.text = t)
	Game.toast.connect(_on_toast)
	Game.paused_changed.connect(_on_paused)
	Game.prompt_changed.connect(func(t: String) -> void: prompt.text = t)
	Game.dialogue_requested.connect(_on_dialogue)
	Game.boss_changed.connect(_on_boss)
	%Boss.visible = false
	prompt.text = ""
	# Cinematics show dialogue only, no gameplay HUD.
	%TopLeft.visible = owner == null or owner is Room
	_on_spirit(Game.spirit, Game.max_spirit)
	coins.text = "%d" % Game.coins
	objective.text = Game.objective
	toast.modulate.a = 0.0
	pause_menu.visible = false
	%Resume.pressed.connect(func() -> void: Game.set_paused(false))
	%Restart.pressed.connect(func() -> void: Game.respawn())
	%Quit.pressed.connect(func() -> void:
		Game.set_paused(false)
		get_tree().change_scene_to_file(Game.TITLE))


func _unhandled_input(event: InputEvent) -> void:
	# Cinematics use Pause as Skip; only gameplay rooms open the pause menu.
	if event.is_action_pressed("pause") and get_tree().current_scene is Room:
		Game.set_paused(not get_tree().paused)
		get_viewport().set_input_as_handled()


func _on_dialogue(speaker: String, lines: PackedStringArray) -> void:
	_lines = lines
	_line_i = 0
	_speaker = speaker
	_show_line(lines[0] if lines.size() > 0 else "")
	dialogue.visible = true
	prompt.visible = false
	_dlg_guard = 0.2


## A line may start with "Name: " to switch speaker for that line.
func _show_line(line: String) -> void:
	var who := _speaker
	var i := line.find(": ")
	if i > 0 and i < 16:
		who = line.substr(0, i)
		line = line.substr(i + 2)
	%Speaker.text = who
	%Speaker.visible = who != ""
	%Line.text = line


func _process(delta: float) -> void:
	if not dialogue.visible or get_tree().paused:
		return
	_dlg_guard -= delta
	if _dlg_guard > 0.0:
		return
	if Input.is_action_just_pressed("interact") or Input.is_action_just_pressed("attack") or Input.is_action_just_pressed("jump"):
		_line_i += 1
		Sfx.play("ui")
		if _line_i >= _lines.size():
			dialogue.visible = false
			prompt.visible = true
			Game.dialogue_finished.emit()
		else:
			_show_line(_lines[_line_i])
			_dlg_guard = 0.12


func _on_spirit(sp: float, m: float) -> void:
	spirit.max_value = m
	spirit.value = sp
	spirit.visible = Game.has("ability_wind_slash")


func _on_toast(text: String) -> void:
	toast.text = text
	var tw := create_tween()
	tw.tween_property(toast, "modulate:a", 1.0, 0.15)
	tw.tween_interval(1.6)
	tw.tween_property(toast, "modulate:a", 0.0, 0.4)


func _on_paused(p: bool) -> void:
	pause_menu.visible = p
	if p:
		%Resume.grab_focus()


func _on_boss(boss_name: String, hp: int, max_hp: int) -> void:
	%Boss.visible = boss_name != ""
	%BossName.text = boss_name
	%BossBar.max_value = max_hp
	%BossBar.value = hp
