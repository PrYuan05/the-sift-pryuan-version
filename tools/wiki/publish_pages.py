"""Publish docs/wiki to the gh-pages branch (GitHub Pages: Settings > Pages > Deploy from a branch > gh-pages / root).

  python -I tools/wiki/publish_pages.py            # commit the site onto gh-pages and push it
  python -I tools/wiki/publish_pages.py --dry-run  # only build the commit and print it

The site files are committed with a temporary index, so the working tree, the current branch and its index are not
touched. The gh-pages branch keeps its own history (one commit per publish). Run build_wiki.py first."""
import os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "docs/wiki"
FILES = ["index.html", "wiki.css", "wiki.js", "data.zh.js", "data.en.js", ".nojekyll"]


def git(*args, env=None, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, env=env, check=check, capture_output=True, text=True).stdout.strip()


def main():
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    paths = FILES + sorted(p.relative_to(SITE).as_posix() for p in (SITE / "img").rglob("*") if p.is_file()
                           and p.suffix in (".png", ".jpg"))
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
        subprocess.run(["git", f"--work-tree={SITE}", "add", "-f", "--", *paths], cwd=ROOT, env=env, check=True)
        tree = git("write-tree", env=env)
    parent = git("rev-parse", "--verify", "-q", "refs/remotes/origin/gh-pages", check=False)
    source = git("rev-parse", "--short", "HEAD")
    args = ["commit-tree", tree, "-m", f"wiki: publish from {source}"] + (["-p", parent] if parent else [])
    commit = git(*args)
    print(f"gh-pages commit {commit} ({len(paths)} files, tree {tree[:10]})")
    if "--dry-run" in sys.argv:
        return
    print(git("push", "origin", f"{commit}:refs/heads/gh-pages"))
    git("fetch", "-q", "origin", "gh-pages")
    print("pushed: https://pryuan05.github.io/the-sift-pryuan-version/ (once Pages is set to the gh-pages branch)")


if __name__ == "__main__":
    main()
