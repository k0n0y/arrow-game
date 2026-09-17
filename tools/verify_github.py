"""Verify public GitHub contents and retained commit history without credentials."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "k0n0y/arrow-game"
API = f"https://api.github.com/repos/{REPOSITORY}"


def read_url(url):
    request = Request(url, headers={"User-Agent": "ArrowGame-coursework-verifier", "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=40) as response:
        return response.status, response.read()


def get_json(suffix):
    status, payload = read_url(API + suffix)
    assert status == 200
    return json.loads(payload)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").strip()


def main():
    parser = argparse.ArgumentParser(description="Verify public source, images and original history")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/github_publication.json")
    args = parser.parse_args()
    head = git("rev-parse", "HEAD")
    local_history = git("rev-list", "HEAD").splitlines()
    local_files = {}
    for item in subprocess.check_output(["git", "ls-tree", "-r", "-z", "HEAD"], cwd=ROOT).decode("utf-8").split("\0"):
        if item:
            metadata, path = item.split("\t", 1)
            mode, kind, sha = metadata.split()
            local_files[path] = (mode, sha)
    repository = get_json("")
    assert not repository["private"]
    remote_head = get_json("/git/ref/heads/main")["object"]["sha"]
    assert remote_head == head, (remote_head, head)
    tree = get_json(f"/git/trees/{head}?recursive=1")
    assert not tree["truncated"]
    remote_files = {item["path"]: (item["mode"], item["sha"])
                    for item in tree["tree"] if item["type"] == "blob"}
    assert remote_files == local_files, "Remote files do not exactly match the local commit"
    remote_history = [item["sha"] for item in get_json("/commits?sha=main&per_page=100")]
    assert len(local_history) <= 100 and remote_history == local_history

    # Read actual public raw assets, not only metadata.
    def check_image(path):
        url = f"https://raw.githubusercontent.com/{REPOSITORY}/{head}/{quote(path)}"
        status, data = read_url(url)
        actual = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        assert status == 200 and actual == local_files[path][1]
        return {"path": path, "status": status, "bytes": len(data), "git_blob_sha": actual}

    paths = sorted(p for p in local_files if p.startswith("docs/images/"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        images = list(pool.map(check_image, paths))
    executable = check_image("ArrowGame.exe") if "ArrowGame.exe" in local_files else None
    result = {"status": "verified", "verified_at_utc": datetime.now(timezone.utc).isoformat(),
              "repository": f"https://github.com/{REPOSITORY}", "visibility": "public",
              "verified_commit": head, "commit_count": len(remote_history),
              "original_history_preserved": True, "tracked_files_match": len(local_files),
              "image_checks": images,
              "executable_check": executable,
              "blog_publication": "not completed", "class_submission": "not completed"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "image_checks"}, ensure_ascii=False, indent=2))
    print(f"Verified {len(images)} public image files")


if __name__ == "__main__":
    main()
