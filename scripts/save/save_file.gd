class_name SaveFile
extends RefCounted
## Versioned JSON save with safe write (tmp -> rename) and previous-valid backup.

const VERSION := 1


static func write(path: String, data: Dictionary) -> bool:
	var payload := data.duplicate(true)
	payload["version"] = VERSION
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		push_warning("Save failed to open %s: %s" % [tmp, FileAccess.get_open_error()])
		return false
	f.store_string(JSON.stringify(payload, "\t"))
	f.close()
	# Keep the last good save as .bak before replacing it.
	if FileAccess.file_exists(path) and read_one(path).size() > 0:
		DirAccess.copy_absolute(path, path + ".bak")
	return DirAccess.rename_absolute(tmp, path) == OK


## Returns {} if neither the main save nor its backup is valid.
static func read(path: String) -> Dictionary:
	var d := read_one(path)
	if d.is_empty():
		d = read_one(path + ".bak")
	return d


static func read_one(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var json := JSON.new()  # instance parse reports corruption via return code, not error spam
	if json.parse(FileAccess.get_file_as_string(path)) != OK:
		return {}
	var parsed: Variant = json.data
	if not parsed is Dictionary or not parsed.has("version"):
		return {}
	return migrate(parsed)


## Upgrade older schemas here. Unknown future versions are rejected.
static func migrate(d: Dictionary) -> Dictionary:
	var v := int(d.get("version", 0))
	if v > VERSION or v < 1:
		return {}
	return d


static func erase(path: String) -> void:
	for p in [path, path + ".bak", path + ".tmp"]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)
