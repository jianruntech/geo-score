#!/usr/bin/env python3
"""Run the copyable CI examples the way their CI would, against local fixture sites.

    python3 scripts/test_ci_examples.py

examples/ci/README.md ('Anything else') and examples/ci/gitlab-ci.yml go into CIs this repository never
runs, so nothing else would notice when one of them breaks. This reads the README's fenced block and the
job's `script:` items (no YAML library) and checks that each downloads from a pinned release, verifies the
file against SHA256SUMS before running it, and calls geo_score.py exactly once. Then it swaps the download
for a local copy of cli/geo_score.py and a generated SHA256SUMS and runs the commands with bash against the
fixture server from cli/test_geo_score_e2e.py, as scripts/test_action.py does for action.yml.
"""
import hashlib, io, json, os, re, shutil, subprocess, sys, tempfile, xml.dom.minidom

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "cli"))
import test_geo_score_e2e as e2e  # noqa: E402  (the fixture server; importing it clears proxy variables)

CI = os.path.join(ROOT, "examples", "ci")
PIN = re.compile(r"jianruntech/geo-score/releases/download/(v\d+\.\d+\.\d+)(?=[/\s\"']|$)")
RUN = re.compile(r"(?:^|[;&|(]\s*)python3?\s+geo_score\.py\b")
DOWNLOAD = re.compile(r"\bcurl\s|urlretrieve|urlopen|\bwget\s")

fails = []


def ok(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def rd(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def readme_snippet():
    """The commands in the first ```bash block under '## Anything else', continuation lines joined."""
    text = rd("examples/ci/README.md")
    sec = text[text.index("## Anything else"):]
    block = re.search(r"```bash\n(.*?)```", sec, re.S).group(1)
    return [ln for ln in block.replace("\\\n", " ").splitlines() if ln.strip()]


def gitlab_job():
    """(variables, script items) of the one job in gitlab-ci.yml. Items must be plain scalars."""
    text = rd("examples/ci/gitlab-ci.yml")
    variables, script, section = {}, [], None
    for ln in text.splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        key = re.match(r"^  ([a-z_]+):\s*$", ln)
        if key or not ln.startswith("    "):
            section = key.group(1) if key else None
            continue
        if section == "variables":
            m = re.match(r"^    ([A-Z_][A-Z0-9_]*):\s*(.*?)(?:\s+#.*)?$", ln)
            if m:
                variables[m.group(1)] = m.group(2).strip("\"'")
        elif section == "script":
            m = re.match(r"^    - (.*)$", ln)
            if m:
                script.append(m.group(1))
    return variables, script


def static_checks(name, lines, text):
    runs = [i for i, ln in enumerate(lines) if RUN.search(ln)]
    ok(len(runs) == 1, "%s: calls geo_score.py exactly once (found %d)" % (name, len(runs)))
    pins = set(PIN.findall(text))
    ok(len(pins) == 1, "%s: downloads from one pinned vX.Y.Z release (%s)" % (name, ", ".join(sorted(pins)) or "none"))
    ok("/main/" not in text and "/latest/" not in text, "%s: nothing is fetched from main or latest" % name)
    ver = [i for i, ln in enumerate(lines) if "SHA256SUMS" in ln and re.search(r"sha256sum -c\b", ln)]
    ok(bool(ver) and bool(runs) and ver[0] < runs[0], "%s: checks the file against SHA256SUMS before running it" % name)
    run = lines[runs[0]] if runs else ""
    ok(all(f in run for f in ("--json-out", "--junit", "--fail-under")),
       "%s: the one run writes --json-out and --junit and applies --fail-under" % name)
    ok(any(DOWNLOAD.search(ln) for ln in lines), "%s: has a download step to replace" % name)
    return pins


def pinning_checks():
    """Workflows people copy: third-party actions by full SHA with the release as a comment, and no token left
    behind unless the job pushes."""
    for f in sorted(x for x in os.listdir(CI) if x.endswith(".yml") and x != "gitlab-ci.yml"):
        text = rd(os.path.join("examples", "ci", f))
        uses = re.findall(r"^\s*(?:- )?uses: (\S+)(.*)$", text, re.M)
        third = [(u, rest) for u, rest in uses if not u.startswith("jianruntech/geo-score@")]
        bad = [u for u, rest in third if not (re.match(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$", u)
                                             and re.match(r"^\s+# v\d+\.\d+\.\d+\b", rest))]
        ok(bool(third) and not bad, "%s: %d third-party actions pinned to a commit SHA with a '# vX.Y.Z' comment%s"
           % (f, len(third), (": not " + ", ".join(bad)) if bad else ""))
        ok(not re.search(r"^\s*(?:- )?run: .*\$\{\{", text, re.M), "%s: no ${{ }} expression is pasted into a run: line" % f)
        pushes = re.search(r"^\s+git push\b", text, re.M) is not None
        co = re.search(r"^\s*- uses: actions/checkout@.*\n(?:\s+with: (.*)\n)?", text, re.M)
        if pushes:
            ok(co is not None and "zizmor: ignore[artipacked]" in co.group(0) and "persist-credentials: false" not in co.group(0),
               "%s: pushes, so the checkout keeps its credentials, marked for zizmor" % f)
        else:
            ok(co is not None and "persist-credentials: false" in (co.group(1) or ""),
               "%s: does not push, so the checkout sets persist-credentials: false" % f)


def local_script(lines, fail_under=None):
    """The same commands with the download replaced by a copy from $GEO_TEST_SRC."""
    out, copied = [], False
    for ln in lines:
        if DOWNLOAD.search(ln):
            if not copied:
                out.append('cp "$GEO_TEST_SRC/geo_score.py" "$GEO_TEST_SRC/SHA256SUMS" .')
                copied = True
            continue
        if fail_under is not None and RUN.search(ln):
            ln = re.sub(r"--fail-under\s+\S+", "--fail-under %d" % fail_under, ln)
        out.append(ln)
    return "\n".join(out) + "\n"


def make_src(tmp, tamper=False):
    """A release-shaped folder: geo_score.py and a SHA256SUMS that also lists a file the CI does not fetch,
    so the grep that picks the one line has to work."""
    src = os.path.join(tmp, "release")
    os.makedirs(src)
    sums = []
    for f in ("geo_score.py", "geo_watch.py"):
        body = io.open(os.path.join(ROOT, "cli", f), "rb").read()
        sums.append("%s  %s\n" % (hashlib.sha256(body).hexdigest(), f))
        if f == "geo_score.py":
            io.open(os.path.join(src, f), "wb").write(body + (b"# not the released file\n" if tamper else b""))
    io.open(os.path.join(src, "SHA256SUMS"), "w", encoding="utf-8").write("".join(sums))
    return src


def shims(tmp):
    """python3 is the interpreter running this test; sha256sum falls back to shasum -a 256 (macOS)."""
    d = os.path.join(tmp, "bin")
    os.makedirs(d)
    tools = {"python3": 'exec "%s" "$@"' % sys.executable}
    if not shutil.which("sha256sum"):
        tools["sha256sum"] = 'exec shasum -a 256 "$@"'
    for n, body in tools.items():
        p = os.path.join(d, n)
        io.open(p, "w").write("#!/bin/sh\n" + body + "\n")
        os.chmod(p, 0o755)
    return d


def run(script, work, src, bindir, env):
    e = dict(os.environ)
    # the fixture is on loopback; every off-site lookup goes to a proxy port nothing listens on, so it fails
    # at once and reads as not measured instead of waiting for a network timeout
    e.update(PATH=bindir + os.pathsep + e.get("PATH", ""), GEO_TEST_SRC=src,
             HTTPS_PROXY="http://127.0.0.1:9", HTTP_PROXY="http://127.0.0.1:9",
             https_proxy="http://127.0.0.1:9", http_proxy="http://127.0.0.1:9",
             NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    e.update(env)
    return subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script], cwd=work, env=e,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=300)


def junit_normalised(path):
    doc = xml.dom.minidom.parse(path)
    props = {p.getAttribute("name"): p.getAttribute("value") for p in doc.getElementsByTagName("property")}
    return props.get("normalised"), len(doc.getElementsByTagName("testcase"))


def execute(name, lines, env, good, blocked, tmp):
    bindir = shims(os.path.join(tmp, name.split()[0]))
    base = os.path.join(tmp, name.split()[0])
    for case, origin, fail_under, tamper, want in (("good", good, None, False, 0),
                                                   ("robots-blocks", blocked, 41, False, 1),
                                                   ("tampered", good, None, True, None)):
        work = os.path.join(base, case)
        os.makedirs(work)
        src = make_src(work, tamper)
        p = run(local_script(lines, fail_under), work, src, bindir, dict(env, SITE_URL=origin))
        rep, xml_ = os.path.join(work, "geo-score.json"), os.path.join(work, "geo-score.xml")
        tail = "" if p.returncode == want else ": " + p.stdout[-400:]
        if tamper:
            ok(p.returncode != 0 and not os.path.exists(rep),
               "%s: a file that does not match SHA256SUMS stops the job before scoring (exit %d)%s"
               % (name, p.returncode, "" if p.returncode else ": " + p.stdout[-400:]))
            continue
        ok(p.returncode == want, "%s on %s%s: exit %d (got %d)%s"
           % (name, case, " --fail-under %d" % fail_under if fail_under else "", want, p.returncode, tail))
        if not (os.path.exists(rep) and os.path.exists(xml_)):
            ok(False, "%s on %s: writes geo-score.json and geo-score.xml" % (name, case))
            continue
        r = json.load(io.open(rep, encoding="utf-8"))
        norm, cases = junit_normalised(xml_)
        ok(norm == str(r["normalised"]) and cases > 0,
           "%s on %s: the JSON (%s/100) and the JUnit file (%s, %d tests) come from the same run"
           % (name, case, r["normalised"], norm, cases))
        if case == "robots-blocks":
            ok(r["normalised"] == 40 and r.get("gate_capped") is True, "%s on %s: scored 40, gate capped" % (name, case))


def main():
    print("static: the examples pin a release, verify it, and score once")
    snippet = readme_snippet()
    readme_pins = static_checks("README 'Anything else'", snippet, "\n".join(snippet))
    variables, script = gitlab_job()
    gl = rd("examples/ci/gitlab-ci.yml")
    gitlab_pins = static_checks("gitlab-ci.yml", script, gl)
    ok(re.search(r"^  image: python:3\.12-slim\s*$", gl, re.M) is not None, "gitlab-ci.yml: image python:3.12-slim")
    arts = re.search(r"^  artifacts:\n((?:    .*\n?)+)", gl, re.M)
    arts = [ln.split(" #")[0].strip() for ln in arts.group(1).splitlines()] if arts else []
    ok({"when: always", "paths: [geo-score.json]", "reports:", "junit: geo-score.xml"} <= set(arts),
       "gitlab-ci.yml: keeps geo-score.json and reports geo-score.xml as JUnit, also when the job fails")
    ok('$CI_PIPELINE_SOURCE == "schedule"' in gl and "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH" in gl,
       "gitlab-ci.yml: runs on schedules and on the default branch")
    ok(set(variables) >= {"SITE_URL"}, "gitlab-ci.yml: SITE_URL is a variable")
    others = set()
    for f in sorted(os.listdir(CI)):
        if f.endswith((".yml", ".md")) and f not in ("gitlab-ci.yml", "README.md"):
            others |= set(PIN.findall(rd(os.path.join("examples", "ci", f))))
    allpins = readme_pins | gitlab_pins | others
    ok(len(allpins) == 1, "every example in examples/ci pins the same release (%s)" % ", ".join(sorted(allpins)))
    pinning_checks()
    table = rd("examples/ci/README.md")
    for ci, directive in (("Bitbucket", "test-results/"), ("Azure", "PublishTestResults@2"),
                          ("Jenkins", "junit 'geo-score.xml'"), ("CircleCI", "store_test_results")):
        ok(directive in table, "README: the JUnit table gives %s's directive (%s)" % (ci, directive))

    print("\n  running both with bash against the fixture sites")
    good, blocked = e2e.start_server("good"), e2e.start_server("robots-blocks")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            execute("README", snippet, {}, good.origin, blocked.origin, tmp)
            execute("gitlab-ci.yml", script, variables, good.origin, blocked.origin, tmp)
    finally:
        for s in (good, blocked):
            s.shutdown()
            s.server_close()
    if fails:
        print("\nFAIL: %d CI example check(s)" % len(fails))
        sys.exit(1)
    print("\nOK: the CI examples download a pinned, verified release and score once")


if __name__ == "__main__":
    main()
