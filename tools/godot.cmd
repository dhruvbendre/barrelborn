@echo off
rem Pinned Godot 4.7.2-stable (winget install). Override with the GODOT env var.
if "%GODOT%"=="" set "GODOT=%LOCALAPPDATA%\Microsoft\WinGet\Packages\GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_win64.exe"
"%GODOT%" %*

