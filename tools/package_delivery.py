"""Create a reviewed delivery from Git-tracked files, EXE and complete history."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="Package a new reviewed delivery without overwriting older copies")
parser.add_argument("--output-name", default=f"一箭又一箭_作业交付_{datetime.now():%Y%m%d}")
args = parser.parse_args()
if Path(args.output_name).name != args.output_name or args.output_name in (".", ".."):
    raise SystemExit("Use a folder name, not a path")
DELIVERY = ROOT.parent / args.output_name
ARCHIVE = DELIVERY.with_suffix(".zip")
if DELIVERY.exists() or ARCHIVE.exists():
    raise SystemExit("Delivery already exists; inspect it before selecting a new output path")
if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):
    raise SystemExit("Commit the reviewed files before packaging")
DELIVERY.mkdir()
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
for name in filter(None, tracked):
    src, dest = ROOT / name, DELIVERY / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
shutil.copy2(ROOT / "dist/ArrowGame.exe", DELIVERY / "ArrowGame.exe")
subprocess.run(["git", "bundle", "create", str(DELIVERY / "ArrowGame-history.bundle"), "--all"], cwd=ROOT, check=True)
history = subprocess.check_output(["git", "log", "--reverse", "--format=%h %ad %s", "--date=iso-strict"], cwd=ROOT).decode("utf-8")
(DELIVERY / "evidence/git_history.txt").write_text(history, encoding="utf-8")
manifest = {}
for path in sorted(DELIVERY.rglob("*")):
    if path.is_file():
        manifest[path.relative_to(DELIVERY).as_posix()] = {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
(DELIVERY / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
    for path in sorted(DELIVERY.rglob("*")):
        if path.is_file():
            archive.write(path, Path(DELIVERY.name) / path.relative_to(DELIVERY))
with zipfile.ZipFile(ARCHIVE) as archive:
    assert archive.testzip() is None
print(json.dumps({"folder": str(DELIVERY), "zip": str(ARCHIVE), "files": len(manifest) + 1,
                  "zip_bytes": ARCHIVE.stat().st_size}, ensure_ascii=False, indent=2))
