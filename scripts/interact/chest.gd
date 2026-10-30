class_name Chest
extends Interactable
## Opens once per reward_id; stays open on revisit. Reward is coins and/or a flag.

@export var reward_id := "chest_x"
@export var coins := 10
@export var grant_flag := ""
@export var toast_text := ""
@export var lid_path: NodePath = ^"Lid"
@export var heart_upgrade := false
@export var objective_after := ""


func _ready() -> void:
	super()
	prompt = "Open"
	if Game.has(reward_id):
		_show_open()
		enabled = false


func _on_interact(_p: Player) -> void:
	if not Game.grant(reward_id):
		return
	disable()
	_show_open()
	Sfx.play("coin")
	if coins > 0:
		Game.add_coins(coins)
	if grant_flag != "":
		Game.grant(grant_flag)
	if heart_upgrade:
		Game.max_hp += 1
		Game.heal_full()
	if objective_after != "":
		Game.set_objective(objective_after)
	Game.toast.emit(toast_text if toast_text != "" else "+%d coins" % coins)
	Game.save_game()


func _show_open() -> void:
	var lid := get_node_or_null(lid_path) as Node3D
	if lid:
		lid.rotation.x = -1.9
