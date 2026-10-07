#!/usr/bin/env python3
"""Check the packaging manifests against the code they package.

    python3 scripts/test_packaging.py

mcpb/manifest.json (Claude Desktop), server.json (the MCP Registry), .claude-plugin/ (Claude Code),
gemini-extension.json (Gemini CLI) and the Dockerfile each restate something the code already says: the
version, the tool names, the key variables, the entry point. Nothing else would notice when one of them
falls behind, so this compares each with the code, then builds the .mcpb the way release.py does, starts the
bundled server and asks it for its tools.
"""
import contextlib, importlib.util, inspect, io, json, os, re, shutil, subprocess, sys, tempfile, zipfile
import urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import release  # noqa: E402  (MANIFESTS, version_fields, pack: the same code a release runs)
import mcp_docs  # noqa: E402  (the install block's command and its wheel fallback)

# tracked files that may name a release although --bump does not rewrite them: the changelogs (history), raw
# benchmark reports, build output, the pages build_page.py regenerates from the PINNED benchmark/_page_tpl.py,
# and validate.py, whose rule 27 holds the pattern's text
PIN_EXEMPT = re.compile(r"^(?:CHANGELOG[^/]*|benchmark/raw/.*|dist/.*|docs/[^/]*\.html|\.github/validate\.py)$")
# a wheel download: (the release tag, the version in the wheel's file name)
WHEEL_URL = re.compile(r"releases/download/v(\d+\.\d+\.\d+)/geo_score-(\d+\.\d+\.\d+)-py3-none-any\.whl")
SERVER_SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
NAME_RE = re.compile(r"^[a-zA-Z0-9.-]+/[a-zA-Z0-9._-]+$")     # server.json schema 2025-12-11, `name`
WATCH_ENV = "GEO_SCORE_WATCH_CONFIG"
JSON_FILES = release.MANIFESTS + [".claude-plugin/marketplace.json"]

fails = []


def ok(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def rd(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def load_watch():
    spec = importlib.util.spec_from_file_location("geo_watch_under_test", os.path.join(ROOT, "cli", "geo_watch.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tracked():
    """The repository's tracked files, or None outside a git checkout."""
    try:
        r = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return None
    return [p for p in r.stdout.decode("utf-8").split("\0") if p] if r.returncode == 0 else None


def check_pins(version):
    """Every tracked file that pins a release is one release.py rewrites, and every wheel URL names this release."""
    print("\n  release pins: every tracked file that names a release is in release.py's PINNED")
    files = tracked()
    if files is None:
        print("  skip  not a git checkout, so there is no list of tracked files")
        return
    listed, bad, wheels = set(release.PINNED), 0, 0
    for p in files:
        full = os.path.join(ROOT, p)
        if PIN_EXEMPT.match(p) or not os.path.isfile(full):
            continue
        text = io.open(full, encoding="utf-8", errors="replace").read()
        for m in WHEEL_URL.finditer(text):
            wheels += 1
            if not m.group(1) == m.group(2) == version:
                ok(False, "%s downloads %s; tag and wheel must both be %s" % (p, m.group(0), version))
        if p in listed:
            continue
        hits = sorted({m.group(0) for rx, _ in release.PINS for m in rx.finditer(text)})
        if hits:
            bad += 1
            ok(False, "%s names %s but is not in PINNED, so --bump would leave it behind" % (p, ", ".join(hits)))
    if not bad:
        ok(True, "%d tracked files: each one that names a release is in PINNED or exempt" % len(files))
    ok(wheels > 0, "%d wheel URLs, each releases/download/v%s/%s" % (wheels, version, release.wheel_name(version)))

    print("\n  the install lines: PyPI first, the wheel without PyPI, and what --bump and preflight do to them")
    url = "%s/releases/download/v%s/%s" % (release.REPO, version, release.wheel_name(version))
    pin = release.PYPI_PROJECT + "@" + version
    ok(mcp_docs.cfg_for(version) == {"command": "uvx", "args": [pin, "mcp"]}, "mcp_docs.py runs uvx %s mcp" % pin)
    ok(mcp_docs.WHEEL_URL.format(v=version) == url, "its no-PyPI line downloads %s" % url)
    # built from parts, so this file does not itself name a release
    old = "uvx --from %s/releases/download/v%s/%s geo-score" % (release.REPO, "1.2.3", release.wheel_name("1.2.3"))
    ok(release.repin(old, "9.9.9") == old.replace("1.2.3", "9.9.9"), "--bump rewrites the tag and the wheel's version")
    ok(release.stale_pins(old.replace("v1.2.3", "v9.9.9"), "9.9.9") == ["geo_score-1.2.3"],
       "preflight names a wheel whose version is not the tag's")
    # the PyPI pins, beside the tags that look like them and must not move: the Action's moving v1 and the plugin
    pkg, at, eq = "geo-score", "@", "=="
    old = ("uvx %s%s1.2.3 example.com; pipx install %s%s1.2.3; uses: jianruntech/%s%sv1; jianruntech/%s%sv1.2.3; "
           "claude plugin install %s%sjianruntech" % (pkg, at, pkg, eq, pkg, at, pkg, at, pkg, at))
    ok(release.repin(old, "9.9.9") == old.replace("1.2.3", "9.9.9"),
       "--bump rewrites %s%sX.Y.Z and %s%sX.Y.Z, and leaves %s%sv1 and %s%sjianruntech" % (pkg, at, pkg, eq, pkg, at, pkg, at))
    ok(release.stale_pins(old, "9.9.9") == sorted([pkg + eq + "1.2.3", pkg + at + "1.2.3", "jianruntech/%s%sv1.2.3" % (pkg, at)]),
       "preflight names each PyPI pin that is not the release (%s)" % release.stale_pins(old, "9.9.9"))
    clone = "git clone --branch v1.2.3 --depth 1 https://github.com/jianruntech/%s && cd %s/cli" % (pkg, pkg)
    ok(release.repin(clone, "9.9.9") == clone.replace("v1.2.3", "v9.9.9"), "--bump rewrites the tag a clone line checks out")
    ok(release.stale_pins(clone, "9.9.9") == ["git clone --branch v1.2.3"], "preflight names a clone line on an old tag")
    with tempfile.TemporaryDirectory() as tmp:
        io.open(os.path.join(tmp, release.wheel_name(version)), "wb").close()
        ok(release.wheel_problem(version, tmp) is None, "--execute goes on when the build made %s" % release.wheel_name(version))
        os.rename(os.path.join(tmp, release.wheel_name(version)), os.path.join(tmp, "geo_score-%s-cp312-cp312-any.whl" % version))
        ok(release.wheel_problem(version, tmp) is not None, "--execute stops when the build names the wheel differently")


def check_pypi_publish(version):
    """--publish-pypi uploads exactly the wheel and sdist in dist/SHA256SUMS, and only when they are what the GitHub
    release attached; afterwards PyPI must serve each with that SHA-256. PyPI, GitHub and twine are faked here."""
    print("\n  the PyPI step: what --publish-pypi uploads, and what it checks before and after")
    names = [release.wheel_name(version), release.sdist_name(version)]
    ok(release.read_sums("%s  a.whl\n%s *b.tar.gz\nnot a line\n" % ("0" * 64, "f" * 64)) == {"a.whl": "0" * 64, "b.tar.gz": "f" * 64},
       "SHA256SUMS lines are read in both of shasum's modes")
    saved_env, saved = dict(os.environ), (release.pypi_files, release.released_sums, release.PYPI_WAIT)
    printed = []

    def attempt(pypi_answers, released=None, sums_drop=None, file_edit=None, twine_rc="0"):
        """Run publish_pypi on a fake dist/. pypi_answers is what each read of PyPI's JSON returns, in turn (the last
        one repeats), and an exception there, or as released, is raised by that read. Returns (finished without
        stopping, what stopped it, the twine command lines); what it printed goes into printed."""
        with tempfile.TemporaryDirectory() as tmp:
            dist = os.path.join(tmp, "dist")
            os.makedirs(dist)
            for n in names + ["geo_score.py"]:
                io.open(os.path.join(dist, n), "wb").write(("bytes of " + n).encode("utf-8"))
            sums = {n: release.sha256(os.path.join(dist, n)) for n in names + ["geo_score.py"]}
            io.open(os.path.join(dist, "SHA256SUMS"), "w", encoding="utf-8").write(
                "".join("%s  %s\n" % (sums[n], n) for n in sorted(sums) if n != sums_drop))
            if file_edit:
                io.open(os.path.join(dist, file_edit), "ab").write(b"!")
            answers = list(pypi_answers)

            def fake_pypi(v, timeout=30):
                a = answers.pop(0) if len(answers) > 1 else answers[0]
                if isinstance(a, Exception):
                    raise a
                return None if a is None else dict((n, sums[n] if h == "same" else h) for n, h in a.items())

            def fake_released(v):
                if isinstance(released, Exception):
                    raise released
                return dict(sums, **(released or {}))
            release.pypi_files = fake_pypi
            release.released_sums = fake_released
            release.PYPI_WAIT = (2, 0)
            os.environ["PATH"] = fake_bin(tmp, {"uvx": 'echo "$*" >> "$HOME/calls"; exit "$FAKE_TWINE_RC"'})
            os.environ.update(HOME=tmp, FAKE_TWINE_RC=twine_rc)
            out, why = io.StringIO(), None
            try:
                with contextlib.redirect_stdout(out):
                    release.publish_pypi(version, dist)
            except SystemExit as e:
                why = str(e.code)
            printed[:] = [out.getvalue()]
            log = os.path.join(tmp, "calls")
            calls = io.open(log, encoding="utf-8").read().splitlines() if os.path.exists(log) else []
            return why is None, why or "", [" ".join(os.path.basename(w) for w in c.split()) for c in calls]

    twine = "twine@" + release.TWINE_VERSION
    ok(re.match(r"^\d+\.\d+\.\d+$", release.TWINE_VERSION) is not None,
       "the upload runs a pinned twine (%s), as check.sh pins its tools" % twine)
    upload = twine + " upload --non-interactive " + " ".join(names)
    both = dict((n, "same") for n in names)
    cut = OSError("EOF occurred in violation of protocol (_ssl.c:1129)")
    try:
        done, why, calls = attempt([None, both])
        ok(done and calls == [upload], "a new version: %s uploads the wheel and the sdist, nothing else, and PyPI "
           "serves both with SHA256SUMS's SHA-256 (%s; %s)" % (twine, calls, why))
        ok("mcp-publisher publish" in printed[0], "and it ends with the MCP Registry step, which needs the package on PyPI")
        done, why, calls = attempt([None, None, both])
        ok(done and calls == [upload], "PyPI's JSON lagging the upload: the check waits for it (%s)" % why)
        done, why, calls = attempt([None, dict(both, **{names[1]: "0" * 64})])
        ok(not done and "does not serve exactly" in why and names[1] in why,
           "PyPI serving an sdist with another SHA-256 after the upload stops it, naming the file")
        done, why, calls = attempt([None, None])
        ok(not done and "missing" in why and "--publish-pypi" in why, "PyPI never listing the upload stops it, with the command to rerun")
        done, why, calls = attempt([both])
        ok(done and calls == [], "PyPI already has both files with the right SHA-256: nothing is uploaded (%s)" % calls)
        done, why, calls = attempt([{names[0]: "same"}, both])
        ok(done and calls == [twine + " upload --non-interactive " + names[1]],
           "PyPI has the wheel only: just the sdist is uploaded (%s)" % calls)
        done, why, calls = attempt([{names[0]: "0" * 64}])
        ok(not done and calls == [] and "never be replaced" in why and "--publish-pypi" not in why,
           "PyPI has the wheel with another SHA-256: nothing is uploaded, and no rerun is suggested")
        done, why, calls = attempt([dict(both, **{"geo_score-%s-py3-none-any.whl.extra" % version: "0" * 64})])
        ok(not done and calls == [] and "not in SHA256SUMS" in why, "PyPI has a file SHA256SUMS does not name: it stops")
        done, why, calls = attempt([None, both], released={names[0]: "0" * 64})
        ok(not done and calls == [] and "GitHub release" in why,
           "a dist/ that is not what the GitHub release attached: nothing is uploaded")
        done, why, calls = attempt([None, both], sums_drop=names[1])
        ok(not done and calls == [] and names[1] in why and "--publish-pypi" in why,
           "dist/SHA256SUMS without the sdist: nothing is uploaded, and the stop names the command to rerun")
        done, why, calls = attempt([None, both], released=cut)
        ok(not done and calls == [] and "GitHub release" in why and "--publish-pypi" in why,
           "GitHub out of reach: nothing is uploaded, and the stop names the command to rerun")
        done, why, calls = attempt([cut])
        ok(not done and calls == [] and "cannot ask PyPI" in why and "--publish-pypi" in why,
           "PyPI out of reach before the upload: nothing is uploaded, and the stop names the command to rerun")
        done, why, calls = attempt([None, both], file_edit=names[0])
        ok(not done and calls == [] and names[0] in why, "a wheel that is not the one SHA256SUMS names: nothing is uploaded")
        done, why, calls = attempt([None], twine_rc="1")
        ok(not done and calls == [upload] and "--publish-pypi" in why, "twine failing stops it, with the command to rerun")
        release.pypi_files = lambda v, timeout=30: None
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PATH"] = fake_bin(tmp, {})
            ok("uvx is not installed" in (release.pypi_problem(version) or ""), "--execute stops first without uvx")
        os.environ["PATH"] = saved_env["PATH"]
        release.pypi_files = lambda v, timeout=30: {}
        ok(shutil.which("uvx") is None or "already has" in (release.pypi_problem(version) or ""),
           "--execute stops first when PyPI already has the version")
        ok(inspect.signature(release.execute).parameters["pypi"].default is True, "--execute ends with the PyPI upload unless --no-pypi")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "release.py"), "9.9.9", "--no-pypi"],
                           cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        ok(r.returncode == 2 and "--no-pypi goes with --execute" in r.stderr, "--no-pypi is refused without --execute")
    finally:
        os.environ.clear()
        os.environ.update(saved_env)
        release.pypi_files, release.released_sums, release.PYPI_WAIT = saved


def check_fetch_retries():
    """A request to PyPI or GitHub that fails is tried again before the step that made it stops; a 404 is an
    answer, asked once."""
    print("\n  release.py's requests: a dropped connection or a 5xx is tried again, a 404 is not")
    saved, seen = (release.urllib.request.urlopen, release.FETCH_TRIES), []

    def answers(outcomes):
        def urlopen(req, timeout=30):
            seen.append(req.full_url)
            o = outcomes.pop(0) if len(outcomes) > 1 else outcomes[0]
            if isinstance(o, Exception):
                raise o
            return io.BytesIO(o)
        return urlopen

    def status(code):
        return urllib.error.HTTPError("https://pypi.org/pypi/x/json", code, "status %d" % code, {}, io.BytesIO(b""))

    def fetch(outcomes):
        del seen[:]
        release.urllib.request.urlopen = answers(list(outcomes))
        try:
            return release.fetch("https://pypi.org/pypi/x/json")
        except release.NET_ERRORS as e:
            return e
    drop = urllib.error.URLError("EOF occurred in violation of protocol (_ssl.c:1129)")
    try:
        release.FETCH_TRIES = (3, 0)
        ok(fetch([drop, drop, b"body"]) == b"body" and len(seen) == 3,
           "two dropped handshakes, then the answer: fetch returns it (%d tries)" % len(seen))
        ok(fetch([status(503), b"body"]) == b"body" and len(seen) == 2, "a 503, then the answer: fetch returns it")
        ok(isinstance(fetch([drop]), urllib.error.URLError) and len(seen) == 3,
           "a connection that drops every time: fetch raises after 3 tries (%d)" % len(seen))
        ok(fetch([status(404), b"body"]) is None and len(seen) == 1, "a 404 is an answer: None, after 1 try")
    finally:
        release.urllib.request.urlopen, release.FETCH_TRIES = saved


def check_pythons():
    """pyproject.toml's requires-python and classifiers say what check.sh tests, PY_OLDEST to PY_NEWEST; the
    workflow's matrix and RELEASING.md's Windows run and --strict hint name those two ends."""
    print("\n  Python versions: pyproject.toml, validate.yml and RELEASING.md against check.sh's PY_OLDEST and PY_NEWEST")
    gate, pp = rd("scripts/check.sh"), rd("pyproject.toml")
    lo, hi = (re.search(r"^%s=3\.(\d+)$" % k, gate, re.M) for k in ("PY_OLDEST", "PY_NEWEST"))
    ok(lo is not None and hi is not None, "check.sh sets PY_OLDEST and PY_NEWEST")
    if lo is None or hi is None:
        return
    lo, hi = int(lo.group(1)), int(hi.group(1))
    ok(re.search(r'^requires-python = ">=3\.%d"$' % lo, pp, re.M) is not None, "requires-python is >=3.%d" % lo)
    got = sorted(int(x) for x in re.findall(r'"Programming Language :: Python :: 3\.(\d+)"', pp))
    ok(got == list(range(lo, hi + 1)),
       "a classifier for each of 3.%d to 3.%d (%s)" % (lo, hi, ", ".join("3.%d" % x for x in got)))
    ok('"Programming Language :: Python :: 3 :: Only"' in pp, "the '3 :: Only' classifier")
    ends = ["3.%d" % lo, "3.%d" % hi]
    wf = rd(".github/workflows/validate.yml")
    mx = re.search(r"^\s*matrix:\s*\{py:\s*\[([^\]]*)\]", wf, re.M)
    got = re.findall(r'"([^"]*)"', mx.group(1)) if mx else None
    ok(got == ends, "validate.yml's matrix is %s (%s)" % (ends, got))
    # setup-python builds each Python for particular images, and 3.8 stops at ubuntu-24.04
    got = re.findall(r"^\s*runs-on:\s*(\S+)", wf, re.M)
    ok(bool(got) and not [r for r in got if r.endswith("-latest")],
       "validate.yml runs on a named image, not a moving -latest one (%s)" % ", ".join(got))
    rel = rd("RELEASING.md")
    got = sorted(set(re.findall(r"\bpy -(3\.\d+)", rel)), key=lambda x: int(x[2:]))
    ok(got == ends, "RELEASING.md's Windows run uses py -%s and py -%s (%s)" % (ends[0], ends[1], ", ".join(got)))
    got = re.search(r"uv python install (3\.\d+) (3\.\d+)", rel)
    ok(got is not None and list(got.groups()) == ends, "RELEASING.md's --strict hint is uv python install %s" % " ".join(ends))
    got = {v for pair in re.findall(r"Python (3\.\d+)(?: and (3\.\d+))?", rel) for v in pair if v}
    ok(got <= set(ends), "RELEASING.md names no other Python (%s)" % ", ".join(sorted(got, key=lambda x: int(x[2:]))))


def loose_uses(text):
    """The `uses:` in a workflow that are not pinned: an action needs a full commit SHA and a '# vX.Y.Z' comment.
    A local action (./path) is this repository at the commit under test, and a docker:// image pinned by its
    digest is already immutable, so neither needs one."""
    out = []
    for u, rest in re.findall(r"^\s*(?:-\s+)?uses:\s*(\S+)(.*)$", text, re.M):
        if u.startswith("./") or re.match(r"^docker://\S+@sha256:[0-9a-f]{64}$", u):
            continue
        if not (re.search(r"@[0-9a-f]{40}$", u) and re.match(r"\s+#\s*v\d", rest)):
            out.append(u)
    return out


def check_gate_pins():
    """The workflow runs the gate with the tool versions check.sh pins, on actions pinned by commit."""
    print("\n  the gate's pins: tools in check.sh and the workflows, actions by commit")
    gate = rd("scripts/check.sh")
    for var, pkg in (("RUFF_VERSION", "ruff"), ("JSONSCHEMA_VERSION", "jsonschema")):
        m = re.search(r"^%s=(\S+)$" % var, gate, re.M)
        ok(m is not None, "check.sh sets %s" % var)
        if m:
            wf = rd(".github/workflows/validate.yml")
            ok("%s==%s" % (pkg, m.group(1)) in wf, "validate.yml installs %s==%s, as check.sh pins" % (pkg, m.group(1)))
    wdir = os.path.join(ROOT, ".github", "workflows")
    for f in sorted(os.listdir(wdir)):
        if not f.endswith((".yml", ".yaml")):
            continue
        text = rd(os.path.join(".github", "workflows", f))
        loose = loose_uses(text)
        ok(not loose, "%s: every action is pinned by commit with a '# vX.Y.Z' comment%s"
           % (f, " (not: %s)" % ", ".join(loose) if loose else ""))
        ok(re.search(r"^permissions:", text, re.M) is not None, "%s: sets top-level permissions" % f)
        checkouts = len(re.findall(r"uses:\s*actions/checkout@", text))
        ok(len(re.findall(r"persist-credentials:\s*false", text)) >= checkouts,
           "%s: no checkout keeps the token (persist-credentials: false)" % f)
    sha, digest = "0123456789abcdef" * 2 + "01234567", "0" * 64
    ok(loose_uses("steps:\n  - uses: ./\n  - uses: ./.github/actions/x\n  - uses: docker://alpine@sha256:%s\n"
                  "  - uses: actions/checkout@%s  # v7.0.1\n" % (digest, sha)) == [],
       "a local action, a docker image by digest and an action by commit count as pinned")
    ok(loose_uses("steps:\n  - uses: actions/checkout@v7\n  - uses: docker://alpine:3.20\n"
                  "  - uses: actions/setup-python@%s\n" % sha)
       == ["actions/checkout@v7", "docker://alpine:3.20", "actions/setup-python@" + sha],
       "a tag, a docker tag and a commit with no '# vX.Y.Z' comment do not")


def gate_block(start, end):
    """The lines of check.sh from the one matching start up to (not including) the one matching end."""
    m = re.search(r"^%s.*?(?=^%s)" % (start, end), rd("scripts/check.sh"), re.M | re.S)
    return m.group(0) if m else None


def fake_bin(tmp, fakes):
    """A directory holding python3 (the real one unless fakes has its own) and the fake commands
    {name: sh body}, and nothing else, for PATH."""
    d = os.path.join(tmp, "bin")
    os.makedirs(d)
    for name, body in dict({"python3": 'exec "%s" "$@"' % sys.executable}, **fakes).items():
        path = os.path.join(d, name)
        io.open(path, "w", encoding="utf-8").write(u"#!/bin/sh\n%s\n" % body)
        os.chmod(path, 0o755)
    return d


def run_block(bash, block, fakes, env=None, files=None):
    """Runs a block cut from check.sh under bash -euo pipefail, as check.sh does, in an empty directory with
    only the fakes on PATH. A fake may log each call to "$HOME/calls", even one whose output the block throws
    away. Returns (exit code, output, the calls in order)."""
    with tempfile.TemporaryDirectory() as tmp:
        for rel, text in (files or {}).items():
            os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
            io.open(os.path.join(tmp, rel), "w", encoding="utf-8").write(text)
        prelude = "step() { printf '\\n== %s\\n' \"$*\"; }\n"
        r = subprocess.run([bash, "-euo", "pipefail", "-c", prelude + block], cwd=tmp,
                           env=dict(env or {}, PATH=fake_bin(tmp, fakes), HOME=tmp),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=60)
        log = os.path.join(tmp, "calls")
        calls = io.open(log, encoding="utf-8").read().splitlines() if os.path.exists(log) else []
        return r.returncode, r.stdout, calls


def check_gate_steps():
    """check.sh's steps that depend on the machine: each one skips, or falls back, instead of failing the gate
    for something the change under test did not cause."""
    print("\n  the gate on other machines: the Pythons, lint without the pinned ruff, the pinned jsonschema,"
          " the --live label step, gh for --execute")
    bash = shutil.which("bash")
    if bash is None or os.name == "nt":
        print("  skip  no bash here")
        return
    gate = rd("scripts/check.sh")
    # the Pythons: --strict needs PY_OLDEST to PY_NEWEST under --all, and the minor after PY_NEWEST is optional,
    # so its note names no install; without uv, --all says that only python3 runs
    ends = [re.search(r"^%s=3\.(\d+)$" % k, gate, re.M) for k in ("PY_OLDEST", "PY_NEWEST")]
    pys = gate_block(r"# Which Pythons the tests run on", r'step "structure:')
    ok(None not in ends and pys is not None, "check.sh chooses the Pythons before its first step")
    if None not in ends and pys is not None:
        lo, hi = (int(m.group(1)) for m in ends)
        stable = " ".join("3.%d" % m for m in range(lo, hi + 1))
        nxt = "3.%d" % (hi + 1)
        uv = ('[ "$1 $2" = "python find" ] || exit 2\n'
              'case " $FAKE_UV_PYS " in *" $4 "*) echo "/fake/python$4"; exit 0 ;; esac; exit 2')

        def pick(fakes, all_, strict, found=""):
            block = ("PY_OLDEST=3.%d PY_NEWEST=3.%d ALL=%d STRICT=%d\n%s\necho \"PYS=${PYS[*]}\"\n"
                     % (lo, hi, all_, strict, pys))
            return run_block(bash, block, fakes, {"FAKE_UV_PYS": found})[:2]
        rc, out = pick({"uv": uv}, 1, 1, stable)
        ok(rc == 0 and "python %s (optional" % nxt in out and "uv python install %s" % nxt not in out
           and "PYS=" + " ".join("/fake/python" + v for v in stable.split()) in out,
           "--all --strict: every stable Python runs, and a missing %s is optional, with no install hint (rc %d)" % (nxt, rc))
        rc, out = pick({"uv": uv}, 1, 1, stable.replace("3.%d " % (lo + 1), ""))
        ok(rc == 1 and "uv python install 3.%d" % (lo + 1) in out and "PYS=" not in out,
           "--all --strict with 3.%d missing: the gate stops and names uv python install 3.%d (rc %d)" % (lo + 1, lo + 1, rc))
        rc, out = pick({"uv": uv}, 0, 0, "3.%d 3.%d" % (lo, hi))
        ok(rc == 0 and "python 3.12 not found by uv: skipped (uv python install 3.12)" in out,
           "by default a missing 3.12 is skipped with its install hint (rc %d)" % rc)
        rc, out = pick({}, 1, 0)
        ok(rc == 0 and "--all needs uv" in out and "PYS=python3" in out,
           "--all without uv: says that the tests run on python3 only (rc %d)" % rc)
        rc, out = pick({}, 0, 0)
        ok(rc == 0 and "needs uv" not in out and "PYS=python3" in out, "no uv, no flag: python3, as before (rc %d)" % rc)
        rc, out = pick({}, 0, 1)
        ok(rc == 1 and "--strict needs uv" in out, "--strict without uv: the gate stops (rc %d)" % rc)
    # lint: the pinned ruff from PATH, or from uvx's cache, or fetched by uvx, in that order, so a warm cache
    # never touches the network; offline and uncached with another ruff, that one with a warning; lint errors
    # fail the gate whichever ruff found them
    pin = re.search(r"^RUFF_VERSION=(\S+)$", gate, re.M)
    lint = gate_block(r'step "lint:', r"for py in ")
    ok(pin is not None and lint is not None, "check.sh has the lint step")
    if pin is not None and lint is not None:
        v = pin.group(1)
        lint = "RUFF_VERSION=%s\n%s" % (v, lint)
        ruff = ('[ "$1" = --version ] && { echo "ruff $FAKE_RUFF"; exit 0; }\n'
                'echo "path ruff $*"; exit "$FAKE_RUFF_RC"')
        uvx = ('a="$*"; echo "uvx $a" >> "$HOME/calls"\n'
               'off=; [ "$1" = --offline ] && { off=1; shift; }\n'
               'if [ "$2" = --version ]; then [ -n "$off" ] && exit "$FAKE_UVX_CACHED"; exit "$FAKE_UVX_FETCH"; fi\n'
               'echo "uvx $a"; exit "$FAKE_UVX_RC"')
        both = {"ruff": ruff, "uvx": uvx}
        env = {"FAKE_RUFF": "0.0.1", "FAKE_RUFF_RC": "0", "FAKE_UVX_CACHED": "0", "FAKE_UVX_FETCH": "0", "FAKE_UVX_RC": "0"}
        online = "uvx ruff@%s --version" % v
        rc, out, calls = run_block(bash, lint, both, env)
        ok(rc == 0 and "uvx --offline ruff@%s check" % v in out and "path ruff" not in out and online not in calls,
           "another ruff on PATH, the pin in uv's cache: uvx runs it offline, with no fetch (rc %d)" % rc)
        rc, out, calls = run_block(bash, lint, both, dict(env, FAKE_UVX_CACHED="1"))
        ok(rc == 0 and "uvx ruff@%s check" % v in out and calls[:2] == ["uvx --offline ruff@%s --version" % v, online],
           "the pin not cached: uvx fetches it, after looking in the cache (rc %d, %s)" % (rc, calls[:2]))
        rc, out, calls = run_block(bash, lint, both, dict(env, FAKE_UVX_RC="1"))
        ok(rc != 0, "lint errors found by uvx's ruff fail the gate (rc %d)" % rc)
        rc, out, calls = run_block(bash, lint, both, dict(env, FAKE_UVX_CACHED="1", FAKE_UVX_FETCH="1"))
        ok(rc == 0 and "warning: ruff 0.0.1" in out and "path ruff check" in out and "uvx ruff" not in out,
           "offline (uvx has no cached pin and cannot fetch it): the PATH ruff runs, with a warning (rc %d)" % rc)
        rc, out, calls = run_block(bash, lint, both, dict(env, FAKE_UVX_CACHED="1", FAKE_UVX_FETCH="1", FAKE_RUFF_RC="1"))
        ok(rc != 0, "lint errors found by the PATH ruff fail the gate (rc %d)" % rc)
        rc, out, calls = run_block(bash, lint, {"uvx": uvx}, dict(env, FAKE_UVX_CACHED="1", FAKE_UVX_FETCH="1"))
        ok(rc == 0 and "skipped" in out, "offline with no ruff on PATH: lint is skipped (rc %d)" % rc)
        rc, out, calls = run_block(bash, lint, both, dict(env, FAKE_RUFF=v))
        ok(rc == 0 and "path ruff check" in out and "uvx" not in out and not calls,
           "the pinned ruff on PATH runs as it is, and uvx is not asked (rc %d)" % rc)
    # the schema check: the pinned jsonschema from python3, or from uv's cache, or fetched by uv, in that order;
    # failing those, python3's other jsonschema, and with none at all the step is skipped
    js = re.search(r"^JSONSCHEMA_VERSION=(\S+)$", gate, re.M)
    schema = gate_block(r'JS="jsonschema==', r'if \[ -n "\$SCHEMA_PY" \]; then')
    ok(js is not None and schema is not None, "check.sh chooses a jsonschema for the schema step")
    if js is not None and schema is not None:
        v = js.group(1)
        block = 'JSONSCHEMA_VERSION=%s\n%s\necho "SCHEMA_PY=$SCHEMA_PY;"\n' % (v, schema)
        py = ('case "$*" in *importlib.metadata*) [ -n "$FAKE_JS" ] || exit 1; echo "$FAKE_JS"; exit 0 ;; esac\n'
              'exec "%s" "$@"' % sys.executable)
        uv = ('echo "uv $*" >> "$HOME/calls"\n'
              'case " $* " in *" --offline "*) exit "$FAKE_UV_CACHED" ;; esac; exit "$FAKE_UV_FETCH"')
        both = {"python3": py, "uv": uv}
        env = {"FAKE_JS": "0.0.1", "FAKE_UV_CACHED": "0", "FAKE_UV_FETCH": "0"}
        offline = "uv run --offline --no-project --with jsonschema==%s python" % v
        rc, out, calls = run_block(bash, block, both, dict(env, FAKE_JS=v))
        ok(rc == 0 and "SCHEMA_PY=python3;" in out and not calls, "python3 has the pinned jsonschema: it runs, uv is not asked (rc %d)" % rc)
        rc, out, calls = run_block(bash, block, both, env)
        ok(rc == 0 and "SCHEMA_PY=%s;" % offline in out and len(calls) == 1,
           "the pin in uv's cache: uv runs it offline, with no fetch (rc %d, %s)" % (rc, calls))
        rc, out, calls = run_block(bash, block, both, dict(env, FAKE_UV_CACHED="1"))
        ok(rc == 0 and "SCHEMA_PY=uv run --no-project --with jsonschema==%s python;" % v in out
           and len(calls) == 2 and "--offline" in calls[0],
           "the pin not cached: uv fetches it, after looking in the cache (rc %d, %s)" % (rc, calls))
        rc, out, calls = run_block(bash, block, both, dict(env, FAKE_UV_CACHED="1", FAKE_UV_FETCH="1"))
        ok(rc == 0 and "SCHEMA_PY=python3;" in out, "offline and uncached: python3's own jsonschema runs (rc %d)" % rc)
        rc, out, calls = run_block(bash, block, {"python3": py}, dict(env, FAKE_JS=""))
        ok(rc == 0 and "SCHEMA_PY=;" in out, "no jsonschema and no uv: the step is skipped, not failed (rc %d)" % rc)
    # the label step needs a logged-in gh: the workflow has none, and a release checks gh itself (gh_problem)
    labels = gate_block(r"  if \[ -f scripts/sync_labels\.py \]; then$", r"  fi$")
    ok(labels is not None, "check.sh has the sync_labels.py step")
    if labels is not None:
        labels += "  fi\n"
        gh = 'case "$1" in auth) exit "$FAKE_GH_AUTH" ;; esac; exit 0'
        sync = {"scripts/sync_labels.py": "import os, sys\nprint('fake sync ' + ' '.join(sys.argv[1:]))\n"
                                          "sys.exit(int(os.environ['FAKE_SYNC_RC']))\n"}
        rc, out, _ = run_block(bash, labels, {"gh": gh}, {"FAKE_GH_AUTH": "1", "FAKE_SYNC_RC": "1"}, sync)
        ok(rc == 0 and "gh not authenticated: skipped" in out and "fake sync" not in out,
           "gh logged out: the label step is skipped, not failed (rc %d)" % rc)
        rc, out, _ = run_block(bash, labels, {}, {"FAKE_SYNC_RC": "1"}, sync)
        ok(rc == 0 and "gh not installed: skipped" in out, "no gh: the label step is skipped (rc %d)" % rc)
        rc, out, _ = run_block(bash, labels, {"gh": gh}, {"FAKE_GH_AUTH": "0", "FAKE_SYNC_RC": "1"}, sync)
        ok(rc != 0 and "fake sync --check" in out and "sync_labels.py --apply" in out,
           "gh logged in and a label missing: the gate stops and names --apply (rc %d)" % rc)
        rc, out, _ = run_block(bash, labels, {"gh": gh}, {"FAKE_GH_AUTH": "0", "FAKE_SYNC_RC": "0"}, sync)
        ok(rc == 0 and "fake sync --check" in out, "gh logged in and every label there: the step passes (rc %d)" % rc)
        rc, out, _ = run_block(bash, labels, {"gh": gh}, {"FAKE_GH_AUTH": "0", "FAKE_SYNC_RC": "1"})
        ok(rc == 0 and "labels" not in out, "no scripts/sync_labels.py: no label step (rc %d)" % rc)

    saved = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PATH"] = fake_bin(tmp, {})
            ok("not installed" in (release.gh_problem() or ""), "--execute stops first when there is no gh")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PATH"] = fake_bin(tmp, {"gh": 'case "$1" in auth) exit "$FAKE_GH_AUTH" ;; esac; exit 0'})
            os.environ["FAKE_GH_AUTH"] = "1"
            ok("not logged in" in (release.gh_problem() or ""), "--execute stops first when gh is logged out")
            os.environ["FAKE_GH_AUTH"] = "0"
            ok(release.gh_problem() is None, "--execute goes on when gh is logged in")
    finally:
        os.environ.clear()
        os.environ.update(saved)

def mcp_session(cmd, cwd, env):
    """initialize then tools/list over stdio; returns (serverInfo, tool names)."""
    lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}}},
             {"jsonrpc": "2.0", "method": "notifications/initialized"},
             {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
    r = subprocess.run(cmd, cwd=cwd, env=env, input="".join(json.dumps(m) + "\n" for m in lines),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
    by_id = {m.get("id"): m for m in (json.loads(x) for x in r.stdout.splitlines() if x.strip())}
    info = by_id.get(1, {}).get("result", {}).get("serverInfo", {})
    return info, [t["name"] for t in by_id.get(2, {}).get("result", {}).get("tools", [])]


def main():
    version = re.search(r'^__version__ = "([^"]+)"', rd("cli/geo_score.py"), re.M).group(1)
    watch = load_watch()
    ok(watch.__version__ == version, "cli/geo_score.py and cli/geo_watch.py are both %s" % version)
    check_pins(version)
    check_pypi_publish(version)
    check_fetch_retries()

    print("\n  every manifest parses, in the layout release.py writes, at the CLI's version")
    m = {}
    for p in JSON_FILES:
        try:
            text = rd(p)
            m[p] = json.loads(text)
        except (IOError, OSError, ValueError) as e:
            ok(False, "%s parses (%s)" % (p, e))
            continue
        # bump() rewrites these with json.dumps(indent=2): any other layout would turn a version bump into a reformat
        ok(text == json.dumps(m[p], indent=2, ensure_ascii=False) + "\n", "%s is in release.py's JSON layout" % p)
    if len(m) != len(JSON_FILES):
        return
    for p in release.MANIFESTS:
        for field, now, want in release.version_fields(m[p], version):
            ok(now == want, "%s %s is %s" % (p, field, want))
    for e in m[".claude-plugin/marketplace.json"]["plugins"]:
        ok(e.get("version") in (None, version), "marketplace.json names no other version for %s" % e.get("name"))

    print("\n  server.json (MCP Registry, schema 2025-12-11)")
    s = m["server.json"]
    ok(s.get("$schema") == SERVER_SCHEMA, "$schema is the 2025-12-11 server schema")
    ok(s.get("name") == "io.github.jianruntech/geo-score" and bool(NAME_RE.match(s.get("name", ""))),
       "name is io.github.jianruntech/geo-score and matches the schema's pattern")
    ok(0 < len(s.get("description", "")) <= 100, "description is 1-100 characters (%d)" % len(s.get("description", "")))
    ok(len(s.get("title", "")) <= 100, "title is at most 100 characters")
    pk = [x for x in s.get("packages", []) if x.get("registryType") == "mcpb"]
    ok(len(pk) == 1, "one mcpb package")
    ok(bool(pk) and pk[0].get("fileSha256") == "${MCPB_SHA256}",
       "the template's fileSha256 is the ${MCPB_SHA256} placeholder (release.py fills it in dist/server.json)")
    ok(bool(pk) and pk[0].get("transport") == {"type": "stdio"}, "the mcpb package speaks stdio")
    pp = [x for x in s.get("packages", []) if x.get("registryType") == "pypi"]
    dist_name = re.search(r'^name = "([^"]+)"', rd("pyproject.toml"), re.M).group(1)
    ok(len(pp) == 1, "one pypi package")
    ok(bool(pp) and pp[0].get("identifier") == dist_name == release.PYPI_PROJECT,
       "the pypi package is pyproject.toml's name, the one release.py uploads (%s)" % dist_name)
    ok(bool(pp) and pp[0].get("runtimeHint") == "uvx" and pp[0].get("transport") == {"type": "stdio"}
       and pp[0].get("packageArguments") == [{"type": "positional", "value": "mcp"}] and "fileSha256" not in pp[0],
       "the pypi package runs as uvx geo-score@%s mcp over stdio" % version)
    ok(bool(pp) and bool(pk) and pp[0].get("environmentVariables") == pk[0].get("environmentVariables"),
       "the pypi package asks for the same variables as the mcpb one")
    ok(bool(pp) and ["%s@%s" % (pp[0].get("identifier"), version)] + [a.get("value") for a in pp[0].get("packageArguments", [])]
       == mcp_docs.cfg_for(version)["args"], "the registry's pypi package runs what the install buttons run")
    # the registry accepts a pypi package only when its description, README.md here, names the server
    ok(re.search(r'^readme = "README\.md"$', rd("pyproject.toml"), re.M) is not None
       and "<!-- mcp-name: %s -->" % s.get("name") in rd("README.md").split("\n## ")[0],
       "README.md, the package's description on PyPI, carries mcp-name: %s near its top" % s.get("name"))

    print("\n  tools: the MCPB manifest lists exactly what tools/list serves")
    served = [t["name"] for t in watch.MCPServer("/nonexistent/geo-score-watch.json").handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]]
    listed = [t["name"] for t in m["mcpb/manifest.json"].get("tools", [])]
    ok(sorted(listed) == sorted(served), "mcpb/manifest.json tools %s == tools/list %s" % (sorted(listed), sorted(served)))

    print("\n  key variables: every manifest asks for the provider keys in PROVIDERS, and only those")
    # the first variable of each provider; an alias such as GOOGLE_API_KEY still works from the environment,
    # but a form that asked for it too would ask for the same key twice
    keys = {p["env"][0] for p in watch.PROVIDERS.values()}
    every = {e for p in watch.PROVIDERS.values() for e in p["env"]}
    man = m["mcpb/manifest.json"]
    env, uc = man["server"]["mcp_config"].get("env", {}), man.get("user_config", {})
    ok(set(env) == keys | {WATCH_ENV}, "mcpb env maps %s plus %s" % (sorted(keys), WATCH_ENV))
    for var, val in sorted(env.items()):
        opt = re.match(r"^\$\{user_config\.([a-z_]+)\}$", val)
        o = uc.get(opt.group(1)) if opt else None
        ok(o is not None, "mcpb %s comes from a declared user_config option" % var)
        if o is None:
            continue
        # an optional field left empty must reach the server as "" (no key), never as the literal ${user_config...}
        ok(o.get("required") is False and o.get("default") == "", "mcpb %s is optional with default \"\"" % var)
        ok(bool(o.get("sensitive")) == (var in keys), "mcpb %s is %s" % (var, "sensitive" if var in keys else "not sensitive"))
    reg = {e["name"]: e for e in pk[0].get("environmentVariables", [])} if pk else {}
    ok(set(reg) == keys | {WATCH_ENV}, "server.json environmentVariables are the keys plus %s" % WATCH_ENV)
    ok(all(reg[n].get("isSecret") is (n in keys) and reg[n].get("isRequired") is False for n in reg),
       "server.json: keys are secret, nothing is required")
    gem = m["gemini-extension.json"].get("settings", [])
    ok({x.get("envVar") for x in gem} == keys and all(x.get("sensitive") is True for x in gem),
       "gemini-extension.json has one sensitive setting per key")
    plug = m[".claude-plugin/plugin.json"]
    penv = {v for srv in plug.get("mcpServers", {}).values() for v in srv.get("env", {})}
    # Claude Code substitutes "" for an optional userConfig value left empty, which would blank an exported key
    ok(not (penv & every) and not plug.get("userConfig"),
       "plugin.json leaves the keys to the environment Claude Code runs in (no env or userConfig mapping)")

    print("\n  entry points name files that exist")
    srv = man["server"]
    ok(srv["entry_point"] in [a for a, _ in release.MCPB_FILES], "mcpb entry_point %s is in the bundle" % srv["entry_point"])
    ok(srv["mcp_config"]["args"][0] == "${__dirname}/" + srv["entry_point"], "mcpb runs its entry_point")
    for p, prefix, sep in ((".claude-plugin/plugin.json", "${CLAUDE_PLUGIN_ROOT}/", "/"),
                           ("gemini-extension.json", "${extensionPath}${/}", "${/}")):
        for cfg in m[p].get("mcpServers", {}).values():
            a0 = cfg.get("args", [""])[0]
            rel = a0[len(prefix):].replace(sep, "/") if a0.startswith(prefix) else None
            ok(rel == "cli/geo_score.py" and cfg.get("args", [])[1:] == ["mcp"], "%s runs cli/geo_score.py mcp" % p)
            ok("cwd" not in cfg, "%s sets no cwd, so ./geo-score-watch.json is the user's project" % p)
    mk = m[".claude-plugin/marketplace.json"]
    ok([(e.get("name"), e.get("source")) for e in mk.get("plugins", [])] == [(plug["name"], "./")],
       "marketplace.json offers this repository's plugin")
    dock = rd("Dockerfile")
    ok(re.search(r'io\.modelcontextprotocol\.server\.name="%s"' % re.escape(s["name"]), dock) is not None,
       "the Dockerfile's server-name label is server.json's name")
    ok(re.search(r"^COPY cli/geo_score\.py cli/geo_watch\.py /app/$", dock, re.M) is not None,
       "the image copies the two CLI files")
    ok([x for x in rd(".dockerignore").splitlines() if x and not x.startswith("#")]
       == ["*", "!cli/geo_score.py", "!cli/geo_watch.py"], ".dockerignore lets in the two CLI files only")
    ok(re.search(r"^FROM python:[\w.-]+@sha256:[0-9a-f]{64}$", dock, re.M) is not None,
       "the Dockerfile's base image is pinned by digest")
    check_gate_pins()
    check_pythons()
    check_gate_steps()

    print("\n  the .mcpb release.py builds")
    with tempfile.TemporaryDirectory() as tmp:
        mcpb, sj = release.pack(version, os.path.join(tmp, "a"))
        again, _ = release.pack(version, os.path.join(tmp, "b"))
        digest = release.sha256(mcpb)
        ok(digest == release.sha256(again), "two builds give one SHA-256 (%s…)" % digest[:12])
        with zipfile.ZipFile(mcpb) as z:
            ok(z.namelist() == ["manifest.json"] + [a for a, _ in release.MCPB_FILES],
               "the bundle holds manifest.json, %s" % ", ".join(a for a, _ in release.MCPB_FILES))
            inner = json.loads(z.read("manifest.json").decode("utf-8"))
            z.extractall(os.path.join(tmp, "x"))
        ok(inner == dict(man, version=version), "the bundled manifest is mcpb/manifest.json at %s" % version)
        built = json.loads(io.open(sj, encoding="utf-8").read())
        bp = [x for x in built.get("packages", []) if x.get("registryType") == "mcpb"]
        ok(bool(bp) and bp[0].get("fileSha256") == digest and bp[0].get("identifier") == release.mcpb_url(version),
           "dist/server.json names the bundle's URL and SHA-256")
        ok("${" not in io.open(sj, encoding="utf-8").read(), "dist/server.json has no placeholder left")
        bpp = [x for x in built.get("packages", []) if x.get("registryType") == "pypi"]
        ok([x.get("version") for x in bpp] == [version] and built.get("version") == version,
           "dist/server.json names geo-score %s on PyPI" % version)
        env = {k: v for k, v in os.environ.items() if k not in every and not k.startswith("GEO_SCORE")}
        info, names = mcp_session([sys.executable, os.path.join(tmp, "x", "server", "geo_score.py"), "mcp"], tmp, env)
        ok(info.get("name") == "geo-score" and info.get("version") == version,
           "the bundled server starts and says geo-score %s" % version)
        ok(sorted(names) == sorted(listed), "the bundled server serves the manifest's tools")

    if fails:
        print("\nFAIL: %d packaging check(s)" % len(fails))
        sys.exit(1)
    print("\nOK: the manifests match the code, and the .mcpb builds, starts and serves its tools")


if __name__ == "__main__":
    main()
