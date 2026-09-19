"""Check links, result evidence, text encoding and the reviewable file set."""

import json
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.paths.append(dict(attrs)["src"])


page = (ROOT / "docs/blog.html").read_text(encoding="utf-8")
images = Images()
images.feed(page)
assert images.paths and all((ROOT / "docs" / p).is_file() for p in images.paths)
checked = []
for pattern in ("*.py", "*.md", "*.html", "*.json", "*.txt", "*.ini", "*.cmd"):
    for path in ROOT.rglob(pattern):
        if any(x in (".venv", ".git", "build", "dist", ".pytest_cache", "__pycache__") for x in path.parts):
            continue
        content = path.read_text(encoding="utf-8-sig")
        assert "\ufffd" not in content, path
        assert not re.search(r"(?:ghp_|github_pat_|hf_)[A-Za-z0-9_]{25,}", content), path
        checked.append(path.relative_to(ROOT).as_posix())
summary = json.loads((ROOT / "evidence/test_summary.json").read_text(encoding="utf-8"))
assert summary["tests"] == 44 and summary["failures"] == summary["errors"] == summary["skipped"] == 0
for name in ("source_smoke.json", "exe_smoke.json"):
    smoke = json.loads((ROOT / "evidence" / name).read_text(encoding="utf-8"))
    assert smoke["status"] == "ok" and smoke["driver"] == "windows"
subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
publication_path = ROOT / "evidence/github_publication.json"
publication = json.loads(publication_path.read_text(encoding="utf-8")) if publication_path.exists() else {}
manual = json.loads((ROOT / "evidence/manual_playtest.json").read_text(encoding="utf-8"))
assert manual["three_levels_cleared"] and [entry["level"] for entry in manual["levels"]] == [1, 2, 3]
for entry in manual["levels"]:
    assert hashlib.sha256((ROOT / entry["screenshot"]).read_bytes()).hexdigest() == entry["sha256"]
result = {"status": "passed", "checked_text_files": len(checked),
          "blog_images_resolved": len(images.paths), "automated_tests": summary["tests"],
          "source_windows_startup": "passed", "exe_windows_startup": "passed",
          "student_personal_playtest": "three level clear screenshots provided",
          "manual_failure_retry": manual["manual_failure_retry"],
          "manual_midgame_restart": manual["manual_midgame_restart"],
          "personal_testing_minutes": manual["personal_testing_minutes"],
          "github_publication": publication.get("status", "not completed"),
          "github_verified_snapshot": publication.get("verified_commit"),
          "blog_publication": "not completed", "class_submission": "not completed"}
(ROOT / "evidence/artifact_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
