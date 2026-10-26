"""Build only the public static website; no source downloads or research assembly."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DIST = ROOT / "dist"
PUBLIC_DATA = (
    "findings.json",
    "unresolved-leads.json",
    "rejected-candidates.json",
    "source-registry.json",
    "documents.json",
    "issue.schema.json",
)


def main():
    # Build in a fresh directory so removed findings cannot leave stale pages.
    with tempfile.TemporaryDirectory(prefix="lobby-fact-checks-site-") as temporary:
        output = Path(temporary)
        subprocess.run(
            [sys.executable, str(HERE / "build.py"), str(output / "index.html")],
            check=True,
        )
        subprocess.run(
            [sys.executable, str(HERE / "build_evidence.py"), str(output / "evidence")],
            check=True,
        )
        for name in ("about.html", "evidence.css", "favicon.svg"):
            shutil.copyfile(HERE / name, output / name)
        (output / "data").mkdir()
        for name in PUBLIC_DATA:
            shutil.copyfile(ROOT / "data" / name, output / "data" / name)
        (output / ".nojekyll").touch()
        subprocess.run(
            [sys.executable, str(HERE / "validate_static.py"), str(output)], check=True
        )
        if DIST.is_symlink():
            raise ValueError("Refusing to replace a symlink at dist/")
        if DIST.exists():
            shutil.rmtree(DIST)
        shutil.copytree(output, DIST)
    print(f"Static website ready in {DIST}")


if __name__ == "__main__":
    main()
