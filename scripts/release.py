#!/usr/bin/env python3
"""Cut a release the same way every time.

    python3 scripts/release.py 1.3.0            # preflight only: prints what is out of step and the plan
    python3 scripts/release.py 1.3.0 --bump     # rewrite versions, install pins and changelog headings
    python3 scripts/release.py 1.3.0 --execute  # after the bump is committed: build, checksum, tag, push, release

Hosted Actions have never run on this organisation, so nothing here happens automatically, and the
moving `v1` tag in particular has fallen behind main before. The steps are in RELEASING.md.
"""
import argparse, datetime, hashlib, io, json, os, re, shutil, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = "https://github.com/jianruntech/geo-score"
RAW = "https://raw.githubusercontent.com/jianruntech/geo-score/"
# files whose one-line install or download is pinned to a release tag
PINNED = ["README.md", "README.zh-CN.md", "cli/README.md", "examples/ci/README.md", "examples/ci/watch-weekly.yml",
          ".github/ISSUE_TEMPLATE/add_site.yml", "benchmark/_page_tpl.py", "SECURITY.md", "STABILITY.md",
          "guide/troubleshooting.md", "guide/troubleshooting.zh-CN.md"]
# every way a document pins a release; group 1 is kept, the version after it is rewritten
PINS = [re.compile(r"(raw\.githubusercontent\.com/jianruntech/geo-score/)(?:v\d+\.\d+\.\d+|main)(?=/cli[/\s\"'])"),
        re.compile(r"(jianruntech/geo-score/releases/download/)v\d+\.\d+\.\d+"),
        re.compile(r"(jianruntech/geo-score@)v\d+\.\d+\.\d+"),
        re.compile(r"(git\+https://github\.com/jianruntech/geo-score@)v\d+\.\d+\.\d+"),
        re.compile(r"(?m)(^v=)v\d+\.\d+\.\d+")]


def rd(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def wr(p, text):
    io.open(os.path.join(ROOT, p), "w", encoding="utf-8").write(text)


def git(*args, capture=True):
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    cmd = ["git"] + (["-c", "http.proxy=" + proxy] if proxy else []) + list(args)
    return subprocess.run(cmd, cwd=ROOT, capture_output=capture, text=True)


def section(changelog, v):
    m = re.search(r"^## \[%s\][^\n]*\n(.*?)(?=^## \[|^\[Unreleased\]:)" % re.escape(v), rd(changelog), re.S | re.M)
    return m.group(1).strip() if m else None


def preflight(v):
    problems, notes = [], []
    for p in ("cli/geo_score.py", "cli/geo_watch.py"):
        m = re.search(r'^__version__ = "([^"]+)"', rd(p), re.M)
        if not m or m.group(1) != v:
            problems.append("%s: __version__ is %s" % (p, m.group(1) if m else "missing"))
    m = re.search(r"^\s+version: (\S+)", rd("SKILL.md"), re.M)
    if not m or m.group(1) != v:
        problems.append("SKILL.md: metadata version is %s" % (m.group(1) if m else "missing"))
    for p in PINNED:
        if not os.path.exists(os.path.join(ROOT, p)):
            continue
        t = rd(p)
        bad = sorted({m.group(0) for rx in PINS for m in rx.finditer(t) if not m.group(0).endswith("v" + v)})
        if bad:
            problems.append("%s: %s, not v%s" % (p, ", ".join(bad), v))
    rub = re.search(r'^RUBRIC = "v([^"]+)"', rd("cli/geo_score.py"), re.M).group(1)
    cff = re.search(r'^version: "([^"]+)"', rd("CITATION.cff"), re.M)
    if not cff or cff.group(1) != rub:
        problems.append("CITATION.cff cites rubric %s, the CLI implements %s" % (cff.group(1) if cff else "?", rub))
    for c in ("CHANGELOG.md", "CHANGELOG.zh-CN.md"):
        if not section(c, v):
            problems.append("%s: no '## [%s]' section with content" % (c, v))
        if section(c, "Unreleased"):
            problems.append("%s: [Unreleased] still has entries; move them under [%s]" % (c, v))
        if "[%s]: %s/compare/" % (v, REPO) not in rd(c):
            problems.append("%s: no compare link for [%s]" % (c, v))
    if git("status", "--porcelain").stdout.strip():
        problems.append("the working tree has uncommitted changes")
    if git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() != "main":
        problems.append("not on main")
    if git("tag", "-l", "v" + v).stdout.strip():
        problems.append("tag v%s already exists" % v)
    res = json.loads(rd("benchmark/results.json"))
    notes.append("benchmark/results.json was measured with %s on %s; the README says so, and re-running it is "
                 "the owner's call" % (res["tool"], res["measured_at"]))
    return problems, notes


def bump(v):
    today = datetime.date.today().isoformat()
    for p in ("cli/geo_score.py", "cli/geo_watch.py"):
        wr(p, re.sub(r'^__version__ = "[^"]+"', '__version__ = "%s"' % v, rd(p), count=1, flags=re.M))
    wr("SKILL.md", re.sub(r"^(\s+version: )\S+", r"\g<1>" + v, rd("SKILL.md"), count=1, flags=re.M))
    for p in PINNED:
        if os.path.exists(os.path.join(ROOT, p)):
            t = rd(p)
            for rx in PINS:
                t = rx.sub(lambda m: m.group(1) + "v" + v, t)
            wr(p, t)
    for c in ("CHANGELOG.md", "CHANGELOG.zh-CN.md"):
        t = rd(c)
        prev = re.search(r"^## \[(\d+\.\d+\.\d+)\]", t, re.M).group(1)
        if "## [%s]" % v not in t:
            t = t.replace("## [Unreleased]\n", "## [Unreleased]\n\n## [%s] — %s\n" % (v, today), 1)
        t = re.sub(r"^\[Unreleased\]: .*$", "[Unreleased]: %s/compare/v%s...HEAD\n[%s]: %s/compare/v%s...v%s"
                   % (REPO, v, v, REPO, prev, v), t, count=1, flags=re.M)
        wr(c, t)
    print("bumped to %s; now run bash scripts/check.sh, rebuild the pages (python3 benchmark/build_page.py),\n"
          "commit as 'chore(release): %s', then python3 scripts/release.py %s --execute" % (v, v, v))


def execute(v):
    dist = os.path.join(ROOT, "dist")
    shutil.rmtree(dist, ignore_errors=True)
    os.makedirs(dist)
    for step in (["bash", "scripts/check.sh", "--live"],
                 ["uv", "build", "--out-dir", "dist"] if shutil.which("uv") else [sys.executable, "-m", "build", "--outdir", "dist"]):
        print("$ " + " ".join(step))
        if subprocess.run(step, cwd=ROOT).returncode:
            sys.exit("stopped: %s failed" % step[0])
    for f in ("geo_score.py", "geo_watch.py"):
        shutil.copy(os.path.join(ROOT, "cli", f), os.path.join(dist, f))
    # an explicit list: build tools leave other files in dist/ (uv writes a .gitignore)
    names = sorted(n for n in os.listdir(dist) if n.endswith((".whl", ".tar.gz")) or n in ("geo_score.py", "geo_watch.py"))
    with io.open(os.path.join(dist, "SHA256SUMS"), "w", encoding="utf-8") as f:
        for n in names:
            f.write("%s  %s\n" % (hashlib.sha256(open(os.path.join(dist, n), "rb").read()).hexdigest(), n))
    notes = os.path.join(dist, "NOTES.md")
    io.open(notes, "w", encoding="utf-8").write(
        section("CHANGELOG.md", v) + "\n\n---\n\nVerify downloads: `shasum -a 256 -c SHA256SUMS`.\n"
        "中文更新日志：%s/blob/v%s/CHANGELOG.zh-CN.md\n" % (REPO, v))
    # main first: if the push is rejected, no tag exists yet and the whole step can simply be rerun
    for args in (["push", "origin", "main"], ["tag", "-a", "v" + v, "-m", "geo-score %s" % v],
                 ["push", "origin", "v" + v], ["tag", "-f", "v1", "v" + v], ["push", "--force", "origin", "v1"]):
        print("$ git " + " ".join(args))
        r = git(*args)
        if r.returncode:
            if args[0] == "push" and args[-1] == "v" + v:
                git("tag", "-d", "v" + v)          # never strand a local tag the remote does not have
            sys.exit("stopped: git %s failed\n%s" % (" ".join(args), r.stderr))
    assets = [os.path.join(dist, n) for n in names] + [os.path.join(dist, "SHA256SUMS")]
    r = subprocess.run(["gh", "release", "create", "v" + v, "--title", "geo-score %s" % v, "--notes-file", notes]
                       + assets, cwd=ROOT)
    if r.returncode:
        sys.exit("stopped: gh release create failed (tag and push are done; rerun that step by hand)")
    print("released v%s: %s/releases/tag/v%s" % (v, REPO, v))


def main():
    ap = argparse.ArgumentParser(description="Cut a geo-score release.")
    ap.add_argument("version")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--bump", action="store_true", help="rewrite versions, pins and changelog headings")
    g.add_argument("--execute", action="store_true", help="build, checksum, tag, push and publish")
    a = ap.parse_args()
    if not re.match(r"^\d+\.\d+\.\d+$", a.version):
        sys.exit("version must look like 1.3.0")
    if a.bump:
        return bump(a.version)
    problems, notes = preflight(a.version)
    for n in notes:
        print("note: " + n)
    if problems:
        print("\nnot ready for %s:" % a.version)
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    if not a.execute:
        print("\nready for %s. Plan: check.sh --live, build sdist + wheel, SHA256SUMS over them and the two CLI "
              "files, tag v%s, move v1, push main and tags, gh release create with the changelog section.\n"
              "Run again with --execute." % (a.version, a.version))
        return
    execute(a.version)


if __name__ == "__main__":
    main()
