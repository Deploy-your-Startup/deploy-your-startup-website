"""Advance only the installer's CLI pin to a newer stable GitHub release."""

import argparse
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--installer", type=Path, default=Path("frontend/public/install.sh"))
    args = parser.parse_args()
    release = json.loads(args.release.read_text())
    tag = release.get("tag_name", "")
    version = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag)
    if release.get("draft") or release.get("prerelease") or not version:
        print("changed=false")
        return
    content = args.installer.read_text()
    pattern = r'^startup_cli_version="v(\d+)\.(\d+)\.(\d+)"$'
    pins = list(re.finditer(pattern, content, re.MULTILINE))
    if len(pins) != 1:
        raise SystemExit("Expected exactly one stable CLI installer pin.")
    current = tuple(map(int, pins[0].groups()))
    target = tuple(map(int, version.groups()))
    if target <= current:
        print("changed=false")
        return
    updated = content[:pins[0].start()] + f'startup_cli_version="{tag}"' + content[pins[0].end():]
    args.installer.write_text(updated)
    print("changed=true")
    print(f"tag={tag}")


if __name__ == "__main__":
    main()
