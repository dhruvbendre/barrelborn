extends Node
## Measures FPS / frame time / draw calls per room on THIS machine (windowed, vsync off).
## Run: tools\godot.cmd --path . res://tests/perf_probe.tscn
## Numbers describe the dev machine only; they are not device-test results.

const ROOMS := ["res://scenes/rooms/harbor.tscn", "res://scenes/rooms/cave.tscn", "res://scenes/rooms/boss_deck.tscn"]


func _ready() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Game.scene_changes_enabled = false
	var out: Array[String] = ["GPU: " + RenderingServer.get_video_adapter_name(), "Renderer: " + RenderingServer.get_video_adapter_api_version()]
	for path in ROOMS:
		var t0 := Time.get_ticks_usec()
		var room: Node = load(path).instantiate()
		add_child(room)
		var load_ms := (Time.get_ticks_usec() - t0) / 1000.0
		for i in 30:
			await get_tree().process_frame
		var worst := 0.0
		var total := 0.0
		var n := 0
		var draws := 0
		var start := Time.get_ticks_msec()
		while Time.get_ticks_msec() - start < 5000:
			await get_tree().process_frame
			var dt := get_process_delta_time()
			worst = maxf(worst, dt)
			total += dt
			n += 1
			draws = maxi(draws, int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)))
		out.append("%s: avg %.0f fps (%.2f ms), worst frame %.1f ms, max draw calls %d, instantiate %.0f ms, mem %.0f MB" % [
			path.get_file(), n / total, total / n * 1000.0, worst * 1000.0, draws, load_ms,
			Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0])
		room.queue_free()
		await get_tree().process_frame
	print("PERF\n" + "\n".join(out))
	var f := FileAccess.open(ProjectSettings.globalize_path("res://qa/perf.txt"), FileAccess.WRITE)
	f.store_string("\n".join(out) + "\n")
	f.close()
	get_tree().quit()
