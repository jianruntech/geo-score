#!/usr/bin/env python3
"""Run the copyable CI examples the way their CI would, against local fixture sites.

    python3 scripts/test_ci_examples.py

examples/ci/README.md ('Anything else') and examples/ci/gitlab-ci.yml go into CIs this repository never
runs, so nothing else would notice when one of them breaks. This reads the README's fenced block and the
job's `script:` items (no YAML library) and checks that each downloads from a pinned release, verifies the
file against SHA256SUMS before running it, and calls geo_score.py exactly once. Then it swaps the download
for a local copy of cli/geo_score.py and a generated SHA256SUMS and runs the commands with bash against the
fixture server from cli/test_geo_score_e2e.py, as scripts/test_action.py does for action.yml. Each runs in the
weakest shell its CI promises: the README block without errexit or pipefail (an Azure Pipelines script step),
the GitLab job with errexit only, so a check that only holds under `set -e` or pipefail fails here.
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
    pick = [i for i, ln in enumerate(lines) if re.search(r"\bgrep\b.*geo_score\\?\.py.*\bSHA256SUMS\b", ln)]
    ver = [i for i, ln in enumerate(lines) if re.search(r"\bsha256sum -c\b", ln)]
    ok(bool(pick) and bool(ver) and bool(runs) and pick[0] <= ver[0] < runs[0],
       "%s: checks the file against its SHA256SUMS line before running it" % name)
    # without pipefail a pipe reports sha256sum's status only, and some sha256sum builds (macOS) pass empty input
    ok(not re.search(r"\|\s*(?:sha256sum|shasum)\b", text), "%s: the checksum line is not piped into sha256sum" % name)
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


def steps(text):
    """The steps of a workflow's one job, each as its block of text (no YAML library)."""
    m = re.search(r"^( *)steps:[ \t]*\n", text, re.M)
    return re.split(r"^%s  - " % m.group(1), text[m.end():], flags=re.M)[1:] if m else []


def gated_checks():
    """A step whose if: runs it after a failure (always(), !cancelled(), failure()) also runs after a failed
    checksum step, so if it runs the downloaded geo_score.py it must also require that step's success."""
    for f in sorted(x for x in os.listdir(CI) if x.endswith(".yml") and x != "gitlab-ci.yml"):
        st = steps(rd(os.path.join("examples", "ci", f)))
        fetch = [s for s in st if re.search(r"\bsha256sum -c\b", s)]
        if not fetch:
            continue
        sid = re.search(r"^\s*id: ([\w-]+)\s*$", fetch[0], re.M)
        late = [s for s in st if s is not fetch[0] and "geo_score.py" in s
                and re.search(r"^\s*if:.*\b(?:always|cancelled|failure)\(\)", s, re.M)]
        bad = [s.split("\n", 1)[0] for s in late
               if not (sid and "steps.%s.outcome == 'success'" % sid.group(1) in s)]
        ok(not bad, "%s: %d step(s) that also run after a failure run geo_score.py only once the checksum step passed%s"
           % (f, len(late), (": not " + "; ".join(bad)) if bad else ""))


def pinned_flags_check(name, lines, pins, tmp):
    """This test runs the working-tree CLI, but a user runs the release the example pins, and that release
    rejects a flag it does not know (exit 2). So every flag of the one run must be in the pinned release's
    --help. The release's geo_score.py comes from the local tag; a clone without it (a shallow CI checkout,
    or a release not tagged yet) skips this."""
    run = [ln for ln in lines if RUN.search(ln)]
    flags = sorted(set(re.findall(r"(?<![\w-])--[a-z][a-z0-9-]*", run[0]))) if run else []
    for tag in sorted(pins):
        try:
            p = subprocess.run(["git", "-C", ROOT, "show", "%s:cli/geo_score.py" % tag],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            p = None
        if p is None or p.returncode:
            print("  skip  %s: %s is not tagged in this clone, so its flags are not compared" % (name, tag))
            continue
        path = os.path.join(tmp, "geo_score-%s.py" % tag)
        io.open(path, "wb").write(p.stdout)
        h = subprocess.run([sys.executable, path, "--help"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True, timeout=60).stdout
        unknown = [x for x in flags if not re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(x), h)]
        ok(bool(flags) and not unknown, "%s: %s's --help knows every flag the run uses (%s)%s"
           % (name, tag, " ".join(flags), (": not " + " ".join(unknown)) if unknown else ""))


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


def make_src(tmp, case=None):
    """A release-shaped folder: geo_score.py and a SHA256SUMS that also lists a file the CI does not fetch,
    so the grep that picks the one line has to work. case "tampered" changes geo_score.py after it was summed;
    "unlisted" leaves its line out of SHA256SUMS, so the grep finds nothing."""
    src = os.path.join(tmp, "release")
    os.makedirs(src)
    sums = []
    for f in ("geo_score.py", "geo_watch.py"):
        body = io.open(os.path.join(ROOT, "cli", f), "rb").read()
        if not (f == "geo_score.py" and case == "unlisted"):
            sums.append("%s  %s\n" % (hashlib.sha256(body).hexdigest(), f))
        if f == "geo_score.py":
            io.open(os.path.join(src, f), "wb").write(body + (b"# not the released file\n" if case == "tampered" else b""))
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


def run(shell, script, work, src, bindir, env):
    e = dict(os.environ)
    # the fixture is on loopback; every off-site lookup goes to a proxy port nothing listens on, so it fails
    # at once and reads as not measured instead of waiting for a network timeout
    e.update(PATH=bindir + os.pathsep + e.get("PATH", ""), GEO_TEST_SRC=src,
             HTTPS_PROXY="http://127.0.0.1:9", HTTP_PROXY="http://127.0.0.1:9",
             https_proxy="http://127.0.0.1:9", http_proxy="http://127.0.0.1:9",
             NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    e.update(env)
    return subprocess.run(shell + ["-c", script], cwd=work, env=e,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=300)


def junit_normalised(path):
    doc = xml.dom.minidom.parse(path)
    props = {p.getAttribute("name"): p.getAttribute("value") for p in doc.getElementsByTagName("property")}
    return props.get("normalised"), len(doc.getElementsByTagName("testcase"))


def execute(name, shell, lines, env, good, blocked, tmp):
    base = os.path.join(tmp, name.split()[0])
    bindir = shims(base)
    for case, origin, fail_under, want in (("good", good, None, 0), ("robots-blocks", blocked, 41, 1),
                                           ("tampered", good, None, None), ("unlisted", good, None, None)):
        work = os.path.join(base, case)
        os.makedirs(work)
        src = make_src(work, case)
        p = run(shell, local_script(lines, fail_under), work, src, bindir, dict(env, SITE_URL=origin))
        rep, xml_ = os.path.join(work, "geo-score.json"), os.path.join(work, "geo-score.xml")
        if want is None:
            what = ("a file that does not match SHA256SUMS" if case == "tampered"
                    else "a SHA256SUMS without a geo_score.py line")
            ok(p.returncode != 0 and not os.path.exists(rep),
               "%s under %s: %s stops the job before scoring (exit %d)%s"
               % (name, " ".join(shell), what, p.returncode, "" if p.returncode else ": " + p.stdout[-400:]))
            continue
        ok(p.returncode == want, "%s on %s%s: exit %d (got %d)%s"
           % (name, case, " --fail-under %d" % fail_under if fail_under else "", want, p.returncode,
              "" if p.returncode == want else ": " + p.stdout[-400:]))
        if not (os.path.exists(rep) and os.path.exists(xml_)):
            ok(False, "%s on %s: writes geo-score.json and geo-score.xml" % (name, case))
            continue
        r = json.load(io.open(rep, encoding="utf-8"))
        norm, cases = junit_normalised(xml_)
        ok(norm == str(r["normalised"]) and cases > 0,
           "%s on %s: the JSON (%s/100) and the JUnit file (%s, %d tests) come from the same run"
           % (name, case, r["normalised"], norm, cases))
        if case == "robots-blocks":
            ok(r["normalised"] <= 40 and r.get("gate_capped") is True, "%s on %s: gate capped (%d)" % (name, case, r["normalised"]))


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
    gated_checks()
    with tempfile.TemporaryDirectory() as tmp:
        pinned_flags_check("README 'Anything else'", snippet, readme_pins, tmp)
        pinned_flags_check("gitlab-ci.yml", script, gitlab_pins, tmp)
    table = rd("examples/ci/README.md")
    for ci, directive in (("Bitbucket", "test-results/"), ("Azure", "PublishTestResults@2"),
                          ("Jenkins", "junit 'geo-score.xml'"), ("CircleCI", "store_test_results")):
        ok(directive in table, "README: the JUnit table gives %s's directive (%s)" % (ci, directive))

    print("\n  running both with bash against the fixture sites")
    good, blocked = e2e.start_server("good"), e2e.start_server("robots-blocks")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            # Azure Pipelines script steps and Travis run bash with neither errexit nor pipefail
            execute("README", ["bash"], snippet, {}, good.origin, blocked.origin, tmp)
            # the GitLab runner sets errexit, and pipefail only when the job's shell has it
            execute("gitlab-ci.yml", ["bash", "-e"], script, variables, good.origin, blocked.origin, tmp)
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
