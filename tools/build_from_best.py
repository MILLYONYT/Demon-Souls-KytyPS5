#!/usr/bin/env python3
"""Reproduce the known-good Build 32 archive or apply guarded binary patches."""

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BASELINE_URL = (
    "https://github.com/MILLYONYT/Demon-Souls-KytyPS5/releases/download/"
    "DemonSoulsKytyPS5/KytyPS5-Build32-LTO-BEST.zip"
)
BASELINE_SHA256 = "b4c9aad01b22886beef0dda58d1978b8acfc5fe39577ed1a348fd34abc502dea"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def patch_archive(source, output, patch_file):
    spec = json.loads(patch_file.read_text(encoding="utf-8"))
    patches = spec["patches"]
    if not isinstance(patches, list) or not patches:
        raise ValueError("patches must be a nonempty list")
    by_member = {}
    for patch in patches:
        member = patch["member"]
        if member not in ("kyty_emulator.exe", "launcher.exe"):
            raise ValueError(f"unsupported patch target: {member}")
        by_member.setdefault(member, []).append(patch)

    with zipfile.ZipFile(source) as original, zipfile.ZipFile(output, "w") as changed:
        if original.testzip() is not None:
            raise ValueError("baseline archive failed ZIP integrity check")
        existing = set(original.namelist())
        if not by_member.keys() <= existing:
            raise ValueError("patch target absent from baseline")
        for item in original.infolist():
            content = bytearray(original.read(item.filename))
            for patch in by_member.get(item.filename, []):
                offset = patch["offset"]
                before = bytes.fromhex(patch["before"])
                after = bytes.fromhex(patch["after"])
                if not isinstance(offset, int) or offset < 0 or not before or len(before) != len(after):
                    raise ValueError("patch needs a nonnegative offset and equal-length hex bytes")
                if content[offset : offset + len(before)] != before:
                    raise ValueError(f"original bytes differ at {item.filename}+0x{offset:x}")
                content[offset : offset + len(before)] = after
            changed.writestr(item, content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", type=Path, help="local copy of the Build 32 release ZIP")
    parser.add_argument("--patch", type=Path, help="JSON file with guarded binary patches")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        source = args.source or Path(directory) / "baseline.zip"
        if args.source is None:
            with urllib.request.urlopen(BASELINE_URL, timeout=120) as response, source.open("wb") as stream:
                shutil.copyfileobj(response, stream)
        actual = digest(source)
        if actual != BASELINE_SHA256:
            raise ValueError(f"wrong baseline SHA-256: {actual}")
        if args.patch is None:
            shutil.copyfile(source, args.output)
            assert digest(args.output) == BASELINE_SHA256
        else:
            with tempfile.TemporaryDirectory() as patched_directory:
                staged = Path(patched_directory) / "patched.zip"
                patch_archive(source, staged, args.patch)
                shutil.copyfile(staged, args.output)
        print(f"{digest(args.output)}  {args.output}")


if __name__ == "__main__":
    main()
