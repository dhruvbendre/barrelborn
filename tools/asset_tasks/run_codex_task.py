"""Run one Codex image/asset task file non-interactively.

Usage: python tools/asset_tasks/run_codex_task.py <task.md> [<task.md> ...]

Each task is prefixed with _common.md, piped to `codex exec` over stdin (no shell
interpolation), and logged to art_source/generation_records/<task>.log.
Afterwards the expected outputs listed in the task's `EXPECT:` lines are checked
for existence and PNG/JPEG/WEBP magic bytes.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASKS = ROOT / "tools" / "asset_tasks"
RECORDS = ROOT / "art_source" / "generation_records"
# npm installs codex as a .cmd shim on Windows; CreateProcess needs the extension.
CODEX = (shutil.which("codex.cmd") or shutil.which("codex")
         or str(pathlib.Path(os.environ.get("APPDATA", "")) / "npm" / "codex.cmd"))
# The user's global default model is rejected for ChatGPT-account auth; override per run.
MODEL = os.environ.get("CODEX_MODEL", "gpt-6-astra")
MAGIC = (b"\x89PNG", b"\xff\xd8\xff", b"RIFF")


def check(path: pathlib.Path) -> str:
    if not path.exists():
        return "MISSING"
    head = path.read_bytes()[:4]
    return "ok" if head.startswith(MAGIC) else f"NOT AN IMAGE ({head!r})"


def run(task_file: pathlib.Path) -> bool:
    body = task_file.read_text(encoding="utf-8")
    prompt = (TASKS / "_common.md").read_text(encoding="utf-8") + "\n\n" + body
    RECORDS.mkdir(parents=True, exist_ok=True)
    log = RECORDS / f"{task_file.stem}.log"
    last = RECORDS / f"{task_file.stem}.report.md"
    started = time.time()
    # `REFERENCE: path` lines attach identity reference images (codex exec -i).
    refs = []
    for l in body.splitlines():
        if l.startswith("REFERENCE:"):
            refs += ["-i", str(ROOT / l.split(":", 1)[1].strip())]
    with log.open("w", encoding="utf-8") as out:
        proc = subprocess.run(
            [CODEX, "exec", "-m", MODEL, "--sandbox", "workspace-write", "--skip-git-repo-check",
             "-C", str(ROOT), "-o", str(last), *refs, "-"],
            input=prompt, text=True, encoding="utf-8", stdout=out, stderr=subprocess.STDOUT,
        )
    expected = [ROOT / l.split(":", 1)[1].strip() for l in body.splitlines() if l.startswith("EXPECT:")]
    results = {str(p.relative_to(ROOT)): check(p) for p in expected}
    ok = proc.returncode == 0 and all(v == "ok" for v in results.values())
    print(f"[{task_file.stem}] exit={proc.returncode} {time.time() - started:.0f}s ok={ok}")
    for k, v in results.items():
        print(f"    {k}: {v}")
    return ok


if __name__ == "__main__":
    files = [pathlib.Path(a) for a in sys.argv[1:]]
    sys.exit(0 if all([run(f if f.is_absolute() else ROOT / f) for f in files]) else 1)
