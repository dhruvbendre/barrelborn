class_name PlayerTuning
extends Resource
## All player feel numbers live here (edit resources/tuning/player_tuning.tres in the inspector).

@export_group("Run")
@export var run_speed := 5.5
@export var ground_accel := 60.0
@export var ground_decel := 70.0
@export var air_accel := 38.0
@export var attack_move_mult := 0.35

@export_group("Jump")
@export var jump_height := 2.4
@export var time_to_apex := 0.4
@export var double_jump_height := 1.6
@export var fall_gravity_mult := 1.6
@export var jump_cut := 0.45
@export var max_fall_speed := 20.0
@export var coyote_time := 0.10
@export var jump_buffer := 0.12

@export_group("Slash")
@export var slash_startup := 0.06
@export var slash_active := 0.10
@export var slash_recovery := 0.16
@export var slash_damage := 1
@export var slash_knockback := 3.0
@export var attack_buffer := 0.12

@export_group("Hurt")
@export var hurt_stun := 0.25
@export var hurt_invuln := 0.8
@export var hurt_knockback := Vector2(6.0, 5.0)
@export var hitstop := 0.05


## Derived so height and apex time stay consistent: h = g t^2 / 2, v0 = g t.
func gravity() -> float:
	return 2.0 * jump_height / (time_to_apex * time_to_apex)


func jump_velocity() -> float:
	return 2.0 * jump_height / time_to_apex


func double_jump_velocity() -> float:
	return sqrt(2.0 * gravity() * double_jump_height)
