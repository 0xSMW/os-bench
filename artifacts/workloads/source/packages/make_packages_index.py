#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import pathlib
import subprocess
import sys


repository = pathlib.Path(sys.argv[1]) / "repository"
rows = []
for package in sorted(repository.glob("*.deb")):
    fields = subprocess.check_output(
        ["dpkg-deb", "-f", str(package)], text=True
    ).strip()
    size = package.stat().st_size
    sha256 = hashlib.sha256(package.read_bytes()).hexdigest()
    rows.append(
        f"{fields}\nFilename: {package.name}\nSize: {size}\nSHA256: {sha256}\n"
    )

(repository / "Packages").write_text("\n".join(rows), encoding="utf-8")
