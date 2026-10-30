class_name Hit
extends RefCounted
## One damage event. Targets implement `apply_hit(hit: Hit) -> bool`.

enum Kind { SLASH, WIND, ENEMY, HAZARD, PROJECTILE }

static var _next_swing := 0

var damage := 1
var knockback := Vector3.ZERO
var kind := Kind.SLASH
var source: Node = null
var swing_id := 0


static func new_swing_id() -> int:
	_next_swing += 1
	return _next_swing


static func make(dmg: int, kb: Vector3, k: Kind, src: Node, swing := 0) -> Hit:
	var h := Hit.new()
	h.damage = dmg
	h.knockback = kb
	h.kind = k
	h.source = src
	h.swing_id = swing
	return h
