"""Build the Windows executable and retain its build log. Does not publish."""

import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
env = dict(os.environ, PYTHONUTF8="1")
with (root / "evidence/build_output.txt").open("w", encoding="utf-8") as log:
    result = subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile",
                             "--windowed", "--name", "ArrowGame", "ArrowGame.py"],
                            cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
if result.returncode:
    raise SystemExit(result.returncode)
print(root / "dist/ArrowGame.exe")
