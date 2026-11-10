#!/usr/bin/env python3
"""Packs the catalog as logix-catalog, the package Logix Engine downloads
(docs/design.md, "Logix Engine and the catalog").

    tools/package.py --out _out [--package-tag yyyymmdd]

The package holds boards/, fpgas/, schemas/, the licenses and
logix-catalog.json, at the archive's top. It's reproducible: fixed file
order, times and owners, and nothing that changes from build to build, so
the same files give the same bytes and SHA-256 and an engine can tell an
unchanged catalog from a new one. The build details (commit, date) go in
the release's BUILD-INFO.json, beside the package.
"""

import argparse
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FOLDERS = ("boards", "fpgas", "schemas")
FILES = ("LICENSE-MIT", "LICENSE-APACHE")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entries() -> list[tuple[str, bytes]]:
    """(path in the package, content), sorted by path."""
    out = []
    for folder in FOLDERS:
        for p in (REPO / folder).rglob("*"):
            if p.is_file() and p.suffix in (".json", ".md"):
                out.append((p.relative_to(REPO).as_posix(), p.read_bytes()))
    for name in FILES:
        out.append((name, (REPO / name).read_bytes()))
    boards = sorted(p.stem for p in (REPO / "boards").glob("*.json"))
    meta = {
        "format": 1,
        "note": "Logix Catalog, as Logix Engine downloads it. Tools are intended to get "
                "this data through Logix Engine's API; the files' layout may change.",
        "repo": "https://github.com/openlogix/logix-catalog",
        "boards": len(boards),
    }
    out.append(("logix-catalog.json", (json.dumps(meta, indent=2) + "\n").encode()))
    return sorted(out)


def pack(items: list[tuple[str, bytes]]) -> bytes:
    raw = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
            folders = sorted({str(Path(n).parent) for n, _ in items} - {"."})
            for d in folders:
                info = tarfile.TarInfo(d)
                info.type, info.mode = tarfile.DIRTYPE, 0o755
                tar.addfile(info)
            for name, data in items:
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(data), 0o644
                tar.addfile(info, io.BytesIO(data))
    return raw.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="folder for the .tgz and its .json")
    ap.add_argument("--package-tag", default="", help="yyyymmdd for the file name")
    args = ap.parse_args()

    data = pack(entries())
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tag = f"-{args.package_tag}" if args.package_tag else ""
    tgz = out / f"logix-catalog{tag}.tgz"
    tgz.write_bytes(data)
    info = {"file": tgz.name, "size": len(data), "sha256": sha256(data)}
    (out / "logix-catalog.json").write_text(json.dumps(info, indent=2) + "\n")
    print(f"{tgz.name}: {info['size']} bytes, sha256 {info['sha256']}")


if __name__ == "__main__":
    main()
