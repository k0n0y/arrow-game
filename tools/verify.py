"""Run checks and save original outputs with portable environment information."""

import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence"
OUT.mkdir(exist_ok=True)
env = dict(os.environ, PYTHONUTF8="1", PYGAME_HIDE_SUPPORT_PROMPT="1")
run = subprocess.run([sys.executable, "-m", "pytest", "-v", "--junitxml=evidence/tests.xml"],
                     cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
(OUT / "test_output.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
print(run.stdout)
if run.returncode:
    print(run.stderr)
    raise SystemExit(run.returncode)
root = ET.parse(OUT / "tests.xml").getroot()
cases = root.findall(".//testcase")
result = {"python": platform.python_version(), "os": platform.platform(),
          "tests": len(cases), "failures": sum(c.find("failure") is not None for c in cases),
          "errors": sum(c.find("error") is not None for c in cases),
          "skipped": sum(c.find("skipped") is not None for c in cases),
          "suite_time_seconds": sum(float(s.get("time", "0")) for s in root.findall("testsuite")),
          "cases": [c.get("name") for c in cases]}
(OUT / "test_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
for file_name in ("tests.xml", "test_output.txt"):
    path = OUT / file_name
    content = path.read_text(encoding="utf-8")
    for variant in (str(ROOT), ROOT.as_posix()):
        content = content.replace(variant, "<PROJECT_ROOT>")
    path.write_text(content, encoding="utf-8")
