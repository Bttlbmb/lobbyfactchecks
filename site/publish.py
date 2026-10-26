"""Build committed site sources locally and push the result to the gh-pages branch."""

import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(directory, *arguments):
    return subprocess.check_output(["git", "-C", str(directory), *arguments], text=True).strip()


def publish(root=ROOT):
    if git(root, "branch", "--show-current") != "main":
        raise ValueError("Publish from main after committing the site changes")
    if git(root, "status", "--porcelain", "--untracked-files=all", "--", "site", "data"):
        raise ValueError("Commit changes under site/ and data/ before publishing")
    remote = git(root, "remote", "get-url", "--push", "origin")
    commit = git(root, "rev-parse", "HEAD")
    remote_main = git(root, "ls-remote", "--heads", remote, "refs/heads/main")
    if not remote_main or remote_main.split()[0] != commit:
        raise ValueError("Push main to origin before publishing its website")
    archive = subprocess.check_output(["git", "-C", str(root), "archive", "HEAD", "site", "data"])
    with tempfile.TemporaryDirectory(prefix="lobby-fact-checks-publish-") as temporary:
        source = Path(temporary) / "source"
        source.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            for member in bundle.getmembers():
                if member.issym() or member.islnk() or not (source / member.name).resolve().is_relative_to(source.resolve()):
                    raise ValueError("Site source archive must contain only files inside its directory")
            bundle.extractall(source)
        subprocess.run([sys.executable, str(source / "site/build_static.py")], check=True)
        deployment = Path(temporary) / "deployment"
        deployment.mkdir()
        git(deployment, "init", "--quiet", "-b", "gh-pages")
        # Reuse the source repository's identity, including local overrides.
        for key in ("user.name", "user.email"):
            value = git(root, "config", "--get", key)
            git(deployment, "config", key, value)
        git(deployment, "remote", "add", "origin", remote)
        if git(root, "ls-remote", "--heads", remote, "refs/heads/gh-pages"):
            git(deployment, "fetch", "--quiet", "--depth=1", "origin", "gh-pages")
            git(deployment, "reset", "--quiet", "--hard", "FETCH_HEAD")
        for path in deployment.iterdir():
            if path.name == ".git":
                continue
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
        shutil.copytree(source / "dist", deployment, dirs_exist_ok=True)
        git(deployment, "add", "--all")
        changed = subprocess.run(["git", "-C", str(deployment), "diff", "--cached", "--quiet"]).returncode
        if changed == 0:
            print("Published site already matches main; no deployment commit needed.")
            return
        if changed != 1:
            raise ValueError("Could not compare the deployment files")
        git(deployment, "commit", "--quiet", "-m", f"Publish site from main {commit[:12]}")
        subprocess.run(["git", "-C", str(deployment), "push", "origin", "HEAD:refs/heads/gh-pages"], check=True)
    print(f"Published main {commit[:12]} to gh-pages. GitHub Pages serves that branch's root.")


if __name__ == "__main__":
    os.environ.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=15")
    publish()
