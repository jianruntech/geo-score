#!/usr/bin/env python3
"""Cut a release the same way every time.

    python3 scripts/release.py 1.3.0            # preflight only: prints what is out of step and the plan
    python3 scripts/release.py 1.3.0 --bump     # rewrite versions, install pins and changelog headings
    python3 scripts/release.py 1.3.0 --execute  # after the bump is committed: build, checksum, tag, push, release
    python3 scripts/release.py 1.3.0 --execute --pypi   # the same, then upload the wheel and sdist to PyPI
    python3 scripts/release.py 1.3.0 --publish-pypi     # after the GitHub release: only the PyPI upload and its check
    python3 scripts/release.py 1.3.0 --pack     # only build dist/geo-score-1.3.0.mcpb and dist/server.json, to try them

Hosted Actions have never run on this organisation, so nothing here happens automatically, and the
moving `v1` tag in particular has fallen behind main before. The steps are in RELEASING.md.
"""
import argparse, datetime, hashlib, http.client, io, json, os, re, shutil, subprocess, sys, time, zipfile
import urllib.error, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = "https://github.com/jianruntech/geo-score"
RAW = "https://raw.githubusercontent.com/jianruntech/geo-score/"
# packaging manifests whose "version" is the release: bump() rewrites them, preflight() checks them
MANIFESTS = ["server.json", "mcpb/manifest.json", ".claude-plugin/plugin.json", "gemini-extension.json"]
# files whose one-line install or download is pinned to a release tag
# (scripts/test_packaging.py fails when a tracked file names a release and is not listed here)
PINNED = ["README.md", "README.zh-CN.md", "cli/README.md", "cli/README.zh-CN.md", "examples/ci/README.md", "examples/ci/watch-weekly.yml",
          "examples/ci/gitlab-ci.yml", ".github/ISSUE_TEMPLATE/add_site.yml", "benchmark/_page_tpl.py", "SECURITY.md",
          "STABILITY.md", "guide/troubleshooting.md", "guide/troubleshooting.zh-CN.md", "guide/mcp.md",
          "guide/mcp.zh-CN.md"] + MANIFESTS
# every way a document pins a release, as (pattern, prefix): group 1 is kept, and the version after it is rewritten
# to prefix + version. A tag carries a "v"; the wheel's file name, which follows the tag in a download URL, does not
PINS = [(re.compile(r"(raw\.githubusercontent\.com/jianruntech/geo-score/)(?:v\d+\.\d+\.\d+|main)(?=/cli[/\s\"'])"), "v"),
        (re.compile(r"(jianruntech/geo-score/releases/download/)v\d+\.\d+\.\d+"), "v"),
        (re.compile(r"(jianruntech/geo-score@)v\d+\.\d+\.\d+"), "v"),
        (re.compile(r"(git\+https://github\.com/jianruntech/geo-score@)v\d+\.\d+\.\d+"), "v"),
        (re.compile(r"(?m)(^v=)v\d+\.\d+\.\d+"), "v"),
        (re.compile(r"(jianruntech/geo-score --ref )v\d+\.\d+\.\d+"), "v"),
        (re.compile(r"(?<![\w.-])(geo_score-)\d+\.\d+\.\d+(?=-py3-none-any\.whl)"), ""),
        # the package on PyPI: uvx's geo-score@X.Y.Z and pip's geo-score==X.Y.Z. No "v", and never the Action's
        # jianruntech/geo-score@v1 or the plugin's geo-score@jianruntech, which have no digits after the @
        (re.compile(r"(?<![\w./-])(geo-score@)\d+\.\d+\.\d+"), ""),
        (re.compile(r"(?<![\w./-])(geo-score==)\d+\.\d+\.\d+"), "")]
# a wheel the install lines download from a release, by its file name
WHEEL_URL_RX = re.compile(r"jianruntech/geo-score/releases/download/v\d+\.\d+\.\d+/([\w.-]+\.whl)")
# rewrites the generated MCP blocks (tool table, install buttons) in README*/guide/mcp*; --check exits 1 on drift.
# PINS cannot see the version inside a URL-encoded or base64 install link, so bump() regenerates them instead.
MCP_DOCS = "scripts/mcp_docs.py"
# what the Claude Desktop bundle holds besides its manifest: (path in the .mcpb, path in the repository)
MCPB_FILES = [("server/geo_score.py", "cli/geo_score.py"), ("server/geo_watch.py", "cli/geo_watch.py"),
              ("LICENSE", "LICENSE")]
# the package on PyPI (pyproject.toml's name) and its JSON API for one version
PYPI_PROJECT = "geo-score"
PYPI_JSON = "https://pypi.org/pypi/%s/%s/json"
# PyPI's JSON API can lag an upload by a minute: (tries, seconds between them) before the hash check gives up
PYPI_WAIT = (12, 10)
# what a request to PyPI or GitHub can fail with: a network error, an HTTP error, a body that is not JSON
NET_ERRORS = (OSError, ValueError, http.client.HTTPException)


def rd(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def wr(p, text):
    io.open(os.path.join(ROOT, p), "w", encoding="utf-8").write(text)


def rdj(p):
    return json.loads(rd(p))


def wrj(p, obj):
    # the manifests are kept in exactly this layout (scripts/test_packaging.py checks it), so a bump is a one-line diff
    wr(p, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def mcpb_url(v):
    return "%s/releases/download/v%s/geo-score-%s.mcpb" % (REPO, v, v)


def wheel_name(v):
    """The file name the build gives the wheel, and the one the no-PyPI install lines download."""
    return "geo_score-%s-py3-none-any.whl" % v


def sdist_name(v):
    return "geo_score-%s.tar.gz" % v


def stale_pins(text, v):
    """The pins in text that name a release other than v (or main)."""
    return sorted({m.group(0) for rx, pre in PINS for m in rx.finditer(text) if m.group(0) != m.group(1) + pre + v})


def repin(text, v):
    """text with every pin pointed at release v."""
    for rx, pre in PINS:
        text = rx.sub(lambda m, pre=pre: m.group(1) + pre + v, text)
    return text


def named_wheels():
    """{wheel file name: [pinned files whose install lines download it]}."""
    out = {}
    for p in PINNED:
        if os.path.exists(os.path.join(ROOT, p)):
            for m in WHEEL_URL_RX.finditer(rd(p)):
                out.setdefault(m.group(1), []).append(p)
    return out


def wheel_problem(v, dist):
    """Why the wheel built into dist cannot ship as v, or None. The install lines download it by name, so a build
    that names it differently would leave every one of them broken."""
    built = sorted(n for n in os.listdir(dist) if n.endswith(".whl"))
    named = named_wheels()
    if built == [wheel_name(v)] and not set(named) - set(built):
        return None
    return "the build made %s; the install lines need %s%s" % (
        ", ".join(built) or "no wheel", wheel_name(v),
        "".join("\n  %s: %s" % (n, ", ".join(sorted(set(ps)))) for n, ps in sorted(named.items()) if n not in built))


def gh_problem():
    """Why gh cannot publish the release, or None. It runs last, after main, the tag and v1 are pushed, and
    check.sh skips its label check when gh is logged out, so --execute asks first."""
    if not shutil.which("gh"):
        return "gh is not installed (https://cli.github.com); it creates the GitHub release"
    r = subprocess.run(["gh", "auth", "status"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "gh is not logged in (gh auth login); it creates the GitHub release" if r.returncode else None


def version_fields(obj, v):
    """Every field of a packaging manifest that names the release, as (field, what it says, what it should say)."""
    out = [("version", obj.get("version"), v)]
    for i, pkg in enumerate(obj.get("packages") or []):
        if pkg.get("registryType") == "mcpb":
            out.append(("packages[%d].identifier" % i, pkg.get("identifier"), mcpb_url(v)))
        elif "version" in pkg:      # a pypi package; an oci one leaves version out so clients do not add the tag twice
            out.append(("packages[%d].version" % i, pkg.get("version"), v))
    return out


def set_version_fields(obj, v):
    obj["version"] = v
    for pkg in obj.get("packages") or []:
        if pkg.get("registryType") == "mcpb":
            pkg["identifier"] = mcpb_url(v)
        elif "version" in pkg:
            pkg["version"] = v
    return obj


def read_sums(text):
    """{file name: SHA-256} from the lines of a SHA256SUMS file."""
    return {m.group(2): m.group(1) for m in re.finditer(r"(?m)^([0-9a-f]{64}) [ *](\S+)$", text)}


def fetch(url, timeout=30):
    """The body at url, or None on a 404. Anything else that goes wrong raises one of NET_ERRORS.
    urllib honours HTTPS_PROXY."""
    req = urllib.request.Request(url, headers={"User-Agent": "geo-score-release"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        e.close()
        if e.code == 404:
            return None
        raise


def pypi_files(v, timeout=30):
    """{file name: SHA-256} of every file PyPI serves for geo-score v, or None when PyPI has no such version."""
    body = fetch(PYPI_JSON % (PYPI_PROJECT, v), timeout)
    if body is None:
        return None
    return {f["filename"]: f["digests"]["sha256"] for f in json.loads(body.decode("utf-8")).get("urls") or []}


def released_sums(v):
    """{file name: SHA-256} from the SHA256SUMS attached to GitHub release v, or None when it has none."""
    body = fetch("%s/releases/download/v%s/SHA256SUMS" % (REPO, v))
    return None if body is None else read_sums(body.decode("utf-8"))


def files_differ(want, got):
    """How got ({name: SHA-256}) differs from want, one line per file; empty when they are the same files."""
    out = []
    for n in sorted(set(want) | set(got)):
        if n not in got:
            out.append("%s: missing" % n)
        elif n not in want:
            out.append("%s: not in SHA256SUMS" % n)
        elif got[n] != want[n]:
            out.append("%s: SHA-256 %s, SHA256SUMS says %s" % (n, got[n], want[n]))
    return out


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
        bad = stale_pins(rd(p), v)
        if bad:
            problems.append("%s: %s, not v%s" % (p, ", ".join(bad), v))
    for p in MANIFESTS:
        try:
            obj = rdj(p)
        except (IOError, OSError, ValueError) as e:
            problems.append("%s: %s" % (p, e))
            continue
        for field, now, want in version_fields(obj, v):
            if now != want:
                problems.append("%s: %s is %s, not %s" % (p, field, now, want))
    if not os.path.exists(os.path.join(ROOT, MCP_DOCS)):
        problems.append("%s is missing: the generated MCP docs cannot be checked" % MCP_DOCS)
    elif subprocess.run([sys.executable, MCP_DOCS, "--check"], cwd=ROOT, capture_output=True, text=True).returncode:
        problems.append("the generated MCP blocks in README*/guide/mcp* are stale: run python3 %s" % MCP_DOCS)
    minor = ".".join(v.split(".")[:2])
    if "| %s.x (latest) | Yes |" % minor not in rd("SECURITY.md"):
        problems.append("SECURITY.md: the supported-versions table does not say '| %s.x (latest) | Yes |'" % minor)
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
    # a version on PyPI can never be uploaded again, so the install lines' geo-score@X.Y.Z must be new there
    try:
        if pypi_files(v, timeout=15) is not None:
            problems.append("PyPI already has geo-score %s (https://pypi.org/project/%s/%s/)" % (v, PYPI_PROJECT, v))
    except NET_ERRORS as e:
        notes.append("could not ask PyPI whether geo-score %s exists (%s); --execute --pypi asks again" % (v, e))
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
            wr(p, repin(rd(p), v))
    for p in MANIFESTS:
        wrj(p, set_version_fields(rdj(p), v))
    # before the changelog, which a second --bump would rewrite twice: a failure here can simply be rerun
    print("$ python3 " + MCP_DOCS)
    if not os.path.exists(os.path.join(ROOT, MCP_DOCS)) or subprocess.run([sys.executable, MCP_DOCS], cwd=ROOT).returncode:
        sys.exit("stopped: %s failed or is missing. Versions, pins and manifests are rewritten, the changelog is not; "
                 "fix it and run --bump again" % MCP_DOCS)
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


def build_mcpb(v, out_dir):
    """geo-score-X.Y.Z.mcpb, the Claude Desktop bundle: a zip of the MCPB manifest with the version filled in, the two
    CLI files under server/ and the licence. Fixed timestamps, modes and order, so one tree always gives one SHA-256."""
    for _, src in MCPB_FILES[:2]:
        m = re.search(r'^__version__ = "([^"]+)"', rd(src), re.M)
        if not m or m.group(1) != v:
            sys.exit("stopped: %s is %s, not %s; a bundle must serve the version its manifest names"
                     % (src, m.group(1) if m else "unversioned", v))
    man = rdj("mcpb/manifest.json")
    man["version"] = v
    entries = [("manifest.json", (json.dumps(man, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))]
    entries += [(arc, open(os.path.join(ROOT, src), "rb").read()) for arc, src in MCPB_FILES]
    path = os.path.join(out_dir, "geo-score-%s.mcpb" % v)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, data in entries:
            info = zipfile.ZipInfo(arc, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    return path


def write_server_json(v, out_dir, mcpb_sha256):
    """server.json for the MCP Registry: the template pointed at release v, with the bundle's real SHA-256."""
    s = set_version_fields(rdj("server.json"), v)
    for pkg in s.get("packages") or []:
        if pkg.get("registryType") == "mcpb":
            pkg["fileSha256"] = mcpb_sha256
    text = json.dumps(s, indent=2, ensure_ascii=False) + "\n"
    if "${" in text:
        sys.exit("stopped: server.json still has a ${...} placeholder after filling it in")
    path = os.path.join(out_dir, "server.json")
    io.open(path, "w", encoding="utf-8").write(text)
    return path


def pack(v, out_dir):
    """The .mcpb and the server.json that names its checksum. Returns both paths."""
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    mcpb = build_mcpb(v, out_dir)
    return mcpb, write_server_json(v, out_dir, sha256(mcpb))


def pypi_problem(v):
    """Why --execute --pypi could not end with geo-score v on PyPI, or None. Asked before anything is pushed:
    the upload runs last, and a version PyPI already has can never be uploaded again."""
    if not shutil.which("uvx"):
        return "uvx is not installed (https://docs.astral.sh/uv/); it runs twine for the PyPI upload"
    try:
        if pypi_files(v) is not None:
            return "PyPI already has geo-score %s, and a version there can never be uploaded again" % v
    except NET_ERRORS as e:
        return "cannot ask PyPI whether geo-score %s exists (%s)" % (v, e)
    return None


def publish_pypi(v, dist=None):
    """Upload the wheel and sdist named in dist/SHA256SUMS to PyPI, then check that PyPI serves exactly those files,
    each with the SHA-256 that SHA256SUMS gives it. Runs after the GitHub release, and only uploads the files that
    release attached: a dist/ rebuilt since then would put other bytes on PyPI for good. Safe to rerun: what PyPI
    already has with the right SHA-256 is not uploaded again. twine finds its own credentials (~/.pypirc or
    TWINE_* variables); this script never reads or prints them."""
    dist = dist or os.path.join(ROOT, "dist")
    again = "python3 scripts/release.py %s --publish-pypi" % v
    sums_path = os.path.join(dist, "SHA256SUMS")
    if not os.path.exists(sums_path):
        sys.exit("stopped: no dist/SHA256SUMS: --execute writes it, with the files PyPI gets")
    sums = read_sums(io.open(sums_path, encoding="utf-8").read())
    want = {}
    for n in (wheel_name(v), sdist_name(v)):
        if n not in sums:
            sys.exit("stopped: dist/SHA256SUMS does not name %s" % n)
        if not os.path.exists(os.path.join(dist, n)):
            sys.exit("stopped: dist/%s is missing" % n)
        if sha256(os.path.join(dist, n)) != sums[n]:
            sys.exit("stopped: dist/%s is not the file dist/SHA256SUMS names" % n)
        want[n] = sums[n]
    try:
        rel = released_sums(v)
    except NET_ERRORS as e:
        sys.exit("stopped: cannot read the SHA256SUMS of GitHub release v%s (%s)" % (v, e))
    if rel is None:
        sys.exit("stopped: GitHub release v%s has no SHA256SUMS; PyPI gets the files a release attached" % v)
    diff = files_differ(want, {n: rel[n] for n in want if n in rel})
    if diff:
        sys.exit("stopped: dist/ is not what GitHub release v%s attached:\n  %s" % (v, "\n  ".join(diff)))
    try:
        got = pypi_files(v) or {}
    except NET_ERRORS as e:
        sys.exit("stopped: cannot ask PyPI what geo-score %s has (%s)" % (v, e))
    clash = [x for x in files_differ(want, got) if not x.endswith(": missing")]
    if clash:
        sys.exit("stopped: PyPI already has geo-score %s with other files, and a file there can never be replaced:\n  %s"
                 % (v, "\n  ".join(clash)))
    missing = [n for n in want if n not in got]
    if not missing:
        print("PyPI already has geo-score %s: %s; nothing to upload" % (v, ", ".join(want)))
    else:
        if not shutil.which("uvx"):
            sys.exit("stopped: uvx is not installed (https://docs.astral.sh/uv/); it runs twine")
        step = ["uvx", "twine", "upload", "--non-interactive"] + [os.path.join(dist, n) for n in missing]
        print("$ " + " ".join(step[:4] + [os.path.relpath(x, ROOT) for x in step[4:]]))
        if subprocess.run(step, cwd=ROOT).returncode:
            sys.exit("stopped: twine upload failed; fix it, then: " + again)
    tries, wait = PYPI_WAIT
    for i in range(tries):
        try:
            diff = files_differ(want, pypi_files(v) or {})
        except NET_ERRORS as e:
            diff = ["cannot read %s (%s)" % (PYPI_JSON % (PYPI_PROJECT, v), e)]
        if not diff:
            break
        if i < tries - 1:
            time.sleep(wait)
    if diff:
        sys.exit("stopped: PyPI does not serve exactly the files in dist/SHA256SUMS:\n  %s\nwhen PyPI has caught up: %s"
                 % ("\n  ".join(diff), again))
    for n in sorted(want):
        print("PyPI serves %s  %s, as SHA256SUMS says" % (want[n], n))
    print("on PyPI: https://pypi.org/project/%s/%s/" % (PYPI_PROJECT, v))


def execute(v, pypi=False):
    why = gh_problem() or (pypi_problem(v) if pypi else None)
    if why:
        sys.exit("stopped: " + why)
    dist = os.path.join(ROOT, "dist")
    shutil.rmtree(dist, ignore_errors=True)
    os.makedirs(dist)
    # --strict: a release is tested on the oldest and the newest Python, never on whatever happens to be installed
    for step in (["bash", "scripts/check.sh", "--live", "--strict"],
                 ["uv", "build", "--out-dir", "dist"] if shutil.which("uv") else [sys.executable, "-m", "build", "--outdir", "dist"]):
        print("$ " + " ".join(step))
        if subprocess.run(step, cwd=ROOT).returncode:
            sys.exit("stopped: %s failed" % step[0])
    why = wheel_problem(v, dist)
    if why:
        sys.exit("stopped: " + why)
    for f in ("geo_score.py", "geo_watch.py"):
        shutil.copy(os.path.join(ROOT, "cli", f), os.path.join(dist, f))
    for p in pack(v, dist):
        print("built " + os.path.relpath(p, ROOT))
    # an explicit list: build tools leave other files in dist/ (uv writes a .gitignore)
    names = sorted(n for n in os.listdir(dist) if n.endswith((".whl", ".tar.gz", ".mcpb"))
                   or n in ("geo_score.py", "geo_watch.py", "server.json"))
    with io.open(os.path.join(dist, "SHA256SUMS"), "w", encoding="utf-8") as f:
        for n in names:
            f.write("%s  %s\n" % (sha256(os.path.join(dist, n)), n))
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
    if pypi:
        publish_pypi(v)
    else:
        print("PyPI, which the install lines and the MCP Registry listing name: python3 scripts/release.py %s --publish-pypi" % v)
    print("MCP Registry (an Owner of the jianruntech org), once PyPI has %s: "
          "cd dist && mcp-publisher validate && mcp-publisher publish" % v)


def main():
    ap = argparse.ArgumentParser(description="Cut a geo-score release.")
    ap.add_argument("version")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--bump", action="store_true", help="rewrite versions, pins and changelog headings")
    g.add_argument("--execute", action="store_true", help="build, checksum, tag, push and publish")
    g.add_argument("--pack", action="store_true", help="only build dist/geo-score-X.Y.Z.mcpb and dist/server.json "
                   "(no checks, no git), e.g. to install the bundle in Claude Desktop before a release")
    g.add_argument("--publish-pypi", action="store_true", help="after the GitHub release: upload the wheel and sdist "
                   "named in dist/SHA256SUMS to PyPI with twine, and check PyPI's SHA-256 of each")
    ap.add_argument("--pypi", action="store_true", help="with --execute: end with the --publish-pypi step")
    a = ap.parse_args()
    if not re.match(r"^\d+\.\d+\.\d+$", a.version):
        sys.exit("version must look like 1.3.0")
    if a.pypi and not a.execute:
        ap.error("--pypi goes with --execute; after a release, --publish-pypi does the PyPI step alone")
    if a.publish_pypi:
        return publish_pypi(a.version)
    if a.bump:
        return bump(a.version)
    if a.pack:
        for p in pack(a.version, os.path.join(ROOT, "dist")):
            print("built " + os.path.relpath(p, ROOT))
        return
    problems, notes = preflight(a.version)
    for n in notes:
        print("note: " + n)
    if problems:
        print("\nnot ready for %s:" % a.version)
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    if not a.execute:
        print("\nready for %s. Plan: stop unless gh is logged in, check.sh --live --strict, build sdist + wheel "
              "(stopping unless the wheel is the file the install lines name), the .mcpb and dist/server.json, "
              "SHA256SUMS over them and the two CLI files, push main, tag v%s and push it, move v1 and push it, "
              "gh release create with the changelog section; with --pypi, then twine upload of the wheel and sdist and "
              "a check of PyPI's SHA-256 of each.\nRun again with --execute (and --pypi)." % (a.version, a.version))
        return
    execute(a.version, a.pypi)


if __name__ == "__main__":
    main()
