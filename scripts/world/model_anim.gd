class_name ModelAnim
extends RefCounted
## Thin wrapper over an imported model's AnimationPlayer: safe when the model is a proxy
## (no player / missing clip), sets looping for clips glTF can't flag, blends by default.

var player: AnimationPlayer
var current := ""


static func find(root: Node, loops: Array = ["idle", "walk", "run", "fall", "stuck", "stunned", "talk"]) -> ModelAnim:
	var m := ModelAnim.new()
	m.player = root.find_child("AnimationPlayer", true, false) as AnimationPlayer if root else null
	if m.player:
		for n in loops:
			if m.player.has_animation(n):
				m.player.get_animation(n).loop_mode = Animation.LOOP_LINEAR
	return m


func has(clip: String) -> bool:
	return player != null and player.has_animation(clip)


## Returns false when there is no such clip, so callers can fall back to procedural motion.
func play(clip: String, restart := false, blend := 0.1) -> bool:
	if not has(clip):
		return false
	if clip == current and not restart:
		return true
	current = clip
	player.play(clip, blend)
	if restart:
		player.seek(0.0, true)
	return true
