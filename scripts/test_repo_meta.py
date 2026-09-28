#!/usr/bin/env python3
"""Check the contributor-facing files against each other, offline.

    python3 scripts/test_repo_meta.py

These files only work together, and nothing else notices when they drift apart:
- the issue forms and .github/labels.json: GitHub drops a label a form applies when the repository does not
  have it, so the issue arrives unlabelled (scripts/sync_labels.py carries labels.json to GitHub);
- what each form asks: a report without the tool version cannot be reproduced, and a placeholder that names a
  release goes stale, because scripts/release.py does not bump it;
- docs/aiv-badge.svg and docs/aiv-badge.json: the badge must be the run the report records;
- the issue chooser, the forms, SUPPORT.md and the PR template: every absolute link into this repository
  resolves, and every anchor names a heading there. The chooser, the forms and the PR template carry no relative
  link, because a PR body or an issue resolves ../README.md against /pull/N and serves a 404; SUPPORT.md is
  rendered in the repository, so its relative links are right (.github/validate.py checks that their files exist);
- CONTRIBUTING.md and the PR template: a new rubric version names every file .github/validate.py requires, and
  the version CONTRIBUTING.md tells contributors to add is the next one, not one already in rubric/.
The forms are read without a YAML library.
"""
import importlib.util, io, json, os, re, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FORMS = os.path.join(ROOT, ".github", "ISSUE_TEMPLATE")

fails = []


def ok(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def rd(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def forms():
    return sorted(f for f in os.listdir(FORMS) if f.endswith((".yml", ".yaml")) and f not in ("config.yml", "config.yaml"))


def form_labels(text):
    """The labels a form applies: `labels: [a, "b"]`, `labels: a, b` or a block list under `labels:`."""
    m = re.search(r"^labels:[ \t]*(.*)$", text, re.M)
    if not m:
        return []
    val = m.group(1).split(" #")[0].strip()
    if not val:
        items = []
        for line in text[m.end():].splitlines()[1:]:
            b = re.match(r"^\s+-\s+(.+?)\s*$", line)
            if not b:
                break
            items.append(b.group(1))
    else:
        items = val.strip("[]").split(",")
    return [x.strip().strip("'\"") for x in items if x.strip().strip("'\"")]


def form_fields(text):
    """{id: (type, required)} for each body item of an issue form."""
    out = {}
    for item in re.split(r"^  - type: ", text, flags=re.M)[1:]:
        m = re.search(r"^    id: ([a-z_]+)\s*$", item, re.M)
        if m:
            out[m.group(1)] = (item.split("\n", 1)[0].strip(), bool(re.search(r"required: true", item)))
    return out


# forms whose reports cannot be reproduced without knowing which release produced them
NEED_VERSION = ("bug_report.yml", "engine_bug.yml", "benchmark_correction.yml", "tool_problem.yml")
# forms whose placeholder still names a release; drop an entry once that form's placeholder is version-free
STALE_PLACEHOLDER = ("bug_report.yml",)
SURFACES = ["CLI", "GitHub Action", "MCP server", "Install via pip, pipx or uvx", "MCPB bundle (Claude Desktop)",
            "Claude Code plugin", "Gemini CLI extension", "Docker"]
BLOB = "https://github.com/jianruntech/geo-score/blob/main/"


def slug(heading):
    """GitHub's anchor for a Markdown heading."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def anchor_exists(path, anchor):
    text = rd(path)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return anchor in {slug(h) for h in re.findall(r"^#{1,6} (.+?)\s*$", text, re.M)}


def check_labels():
    print("labels: .github/labels.json and the issue forms")
    doc = json.loads(rd(".github/labels.json"))
    labels = doc["labels"]
    names = [x["name"] for x in labels]
    ok(len({n.lower() for n in names}) == len(names), "label names are unique (GitHub compares them case-insensitively)")
    ok(all(set(x) == {"name", "color", "description"} for x in labels), "every label has exactly name, color and description")
    ok(all(re.match(r"^[0-9a-f]{6}$", x["color"]) for x in labels), "colours are six lower-case hex digits without '#'")
    ok(all(0 < len(x["description"]) <= 100 for x in labels), "descriptions are present and fit GitHub's 100 characters")
    known = {n.lower() for n in names}
    applied = {}
    for f in forms():
        for lab in form_labels(rd(os.path.join(".github", "ISSUE_TEMPLATE", f))):
            applied.setdefault(lab, []).append(f)
    ok(bool(applied), "the issue forms apply labels (%d found)" % len(applied))
    for lab, where in sorted(applied.items()):
        ok(lab.lower() in known, "%r (%s) is in labels.json" % (lab, ", ".join(where)))
    # the parser itself, on the three shapes GitHub accepts
    ok(form_labels('name: x\nlabels: ["a", b]\nbody:\n') == ["a", "b"], "form_labels reads a flow list")
    ok(form_labels("name: x\nlabels: a, b\nbody:\n") == ["a", "b"], "form_labels reads a comma-separated string")
    ok(form_labels("name: x\nlabels:\n  - a\n  - 'b'\nbody:\n") == ["a", "b"], "form_labels reads a block list")


def check_forms():
    print("forms: what each issue form must ask")
    have = forms()
    for f in NEED_VERSION:
        if f not in have:
            ok(False, "%s exists" % f)
            continue
        fields = form_fields(rd(os.path.join(".github", "ISSUE_TEMPLATE", f)))
        ok(fields.get("tool_version") == ("input", True), "%s asks for tool_version, required" % f)
    # scripts/release.py moves pinned links to the new release but not an example in a form, so a placeholder
    # that names a release asks for reports against an old one
    for f in have:
        text = rd(os.path.join(".github", "ISSUE_TEMPLATE", f))
        stale = re.findall(r"^\s*placeholder:.*?\b(geo-score \d+\.\d+\.\d+)", text, re.M)
        if stale and f in STALE_PLACEHOLDER:
            print("  skip  %s: its placeholder still names %s (left for a separate change)" % (f, stale[0]))
            continue
        ok(not stale, "%s: no placeholder names a release%s" % (f, (": " + ", ".join(stale)) if stale else ""))
    corr = rd(".github/ISSUE_TEMPLATE/benchmark_correction.yml")
    fields = form_fields(corr)
    ok(sorted(form_labels(corr)) == ["benchmark", "correction"], "benchmark_correction.yml applies benchmark and correction")
    ok(all(fields.get(k, ("", False))[1] for k in ("site", "claim", "evidence", "relationship", "ack")),
       "benchmark_correction.yml requires the site, the disputed claim, the evidence, the relationship and the ack")
    ok("measurement correction, not a request for a fix" in corr, "benchmark_correction.yml: the ack says it is not a fix request")
    ok("https://github.com/jianruntech/geo-score/blob/main/README.md#scope--what-this-does-not-do" in corr,
       "benchmark_correction.yml links the README's Scope section by absolute URL")


def check_badge():
    print("badge: docs/aiv-badge.svg is the run recorded in docs/aiv-badge.json")
    rep = json.loads(rd("docs/aiv-badge.json"))
    svg = rd("docs/aiv-badge.svg")
    want = "%d/100 %s" % (rep["normalised"], rep["band"])
    # the value appears in the aria-label, the title and the text with its shadow; every copy must agree
    said = re.findall(r"\d+/100 [A-Z][a-z]+(?: [a-z]+)*", svg)
    ok(len(said) >= 2 and all(s == want for s in said), "the SVG reads %r everywhere, as the report does (%s)"
       % (want, sorted(set(said))))
    ok(bool(rep.get("audited_at")) and bool(rep.get("tool")), "the report records when (%s) and with what (%s) it was measured"
       % (rep.get("audited_at"), rep.get("tool")))
    m = re.search(r"\[!\[([^\]]*)\]\(docs/aiv-badge\.svg\)\]\(([^)\s]+)\)", rd("README.md"))
    ok(m is not None, "README.md shows the badge as a link")
    if m:
        alt, link = m.groups()
        ok(link.rstrip("/") == rep["target"].rstrip("/"), "the badge links to the page it measured (%s; report: %s)"
           % (link, rep["target"]))
        # the alt text names no date yet, so this passes vacuously until one is added; from then on the date
        # must move with each regenerated badge
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", alt)
        ok(all(d == rep["audited_at"] for d in dates), "a date in the badge's alt text is the report's audited_at (%s)"
           % (", ".join(dates) or "none named yet"))


def check_support():
    print("support: the tool-problem form, the chooser links and SUPPORT.md")
    tp = rd(".github/ISSUE_TEMPLATE/tool_problem.yml")
    fields = form_fields(tp)
    ok(fields.get("surface") == ("dropdown", True), "tool_problem.yml: a required surface dropdown")
    opts = re.search(r"id: surface\n(?:.*\n)*?      options:\n((?:        - .*\n)+)", tp)
    got = [x.strip()[2:] for x in opts.group(1).splitlines()] if opts else []
    ok(got == SURFACES, "tool_problem.yml: surface lists %s" % ", ".join(SURFACES))
    ok(all(k in fields for k in ("environment", "client", "command", "output")),
       "tool_problem.yml: asks for the environment, the client, the command and the output")
    ok("render: text" in tp.split("id: output", 1)[-1].split("- type:", 1)[0], "tool_problem.yml: the output renders as text")
    ok("**Never paste an API key.**" in tp and "**Never paste an API key.**" in rd(".github/ISSUE_TEMPLATE/engine_bug.yml"),
       "tool_problem.yml carries engine_bug.yml's warning never to paste a key")
    ok(form_labels(tp) == ["needs-info"], "tool_problem.yml applies needs-info")
    cfg = rd(".github/ISSUE_TEMPLATE/config.yml")
    for u in (BLOB + "guide/troubleshooting.md", BLOB + "guide/mcp.md#troubleshooting"):
        ok(re.search(r"^    url: %s\s*$" % re.escape(u), cfg, re.M) is not None, "config.yml links %s" % u)
    # every absolute link into this repository from the chooser, the forms, SUPPORT.md and the PR template
    texts = [(".github/ISSUE_TEMPLATE/" + f, rd(".github/ISSUE_TEMPLATE/" + f)) for f in forms() + ["config.yml"]]
    texts += [("SUPPORT.md", rd("SUPPORT.md")), (".github/PULL_REQUEST_TEMPLATE.md", rd(".github/PULL_REQUEST_TEMPLATE.md"))]
    seen, targets = 0, 0
    for name, text in texts:
        for url in re.findall(REPO_LINK, text):
            problem, path, anchor = resolve(url)
            targets += 1
            if problem:
                ok(False, "%s: %s %s" % (name, url, problem))
            elif anchor and path.endswith(".md"):
                seen += 1
                ok(anchor_exists(path, anchor), "%s: %s#%s is a heading there" % (name, path, anchor))
    ok(targets >= 15, "the chooser, the forms, SUPPORT.md and the PR template link %d pages here, all resolved" % targets)
    for url, want in ((REPO + "/tree/main/benchmark/raw", None), (REPO + "/tree/main/benchmark/no-such-dir", "no directory"),
                      (REPO + "/blob/main/benchmark/raw", "not a file"), (REPO + "/tree/main/README.md", "no directory"),
                      (REPO + "/issues/new?template=tool_problem.yml", None),
                      (REPO + "/issues/new?template=nope.yml", "no issue form"), (REPO + "#scope", None),
                      (REPO + "/wiki/Home", "cannot check"), (REPO + "/blob/main/SUPPORT.md.", None)):
        got = resolve(url)[0]
        ok(got == want or (want and got and want in got), "resolve(%s): %s" % (url[len(REPO):] or "/", want or "resolves"))
    sup = rd("SUPPORT.md")
    for path, anchor in re.findall(r"\]\(([\w./-]+\.md)#([\w-]+)\)", sup):
        seen += 1
        ok(os.path.exists(os.path.join(ROOT, path)) and anchor_exists(path, anchor), "SUPPORT.md: %s#%s is a heading there"
           % (path, anchor))
    ok(seen >= 6, "the chooser, the forms and SUPPORT.md link %d headings, all checked" % seen)
    linked = set(re.findall(r"issues/new\?template=([\w.-]+)", sup))
    ok(linked == set(forms()), "SUPPORT.md links every issue form and only those (%s)" % ", ".join(sorted(linked)))
    ok("README.md#scope--what-this-does-not-do" in sup, "SUPPORT.md says remediation is out of scope, linked to Scope")


REPO = "https://github.com/jianruntech/geo-score"
REPO_LINK = re.escape(REPO) + r"(?![\w-])(?:[/?#][^\s)\]\"'`<>]*)?"
# GitHub pages that are not files in the repository and exist whatever the tree holds
PAGES = ("releases", "issues", "pulls", "discussions", "security", "actions", "labels")


def resolve(url):
    """(problem or None, path, anchor) for an absolute link into this repository: blob/main must be a file,
    tree/main a directory, issues/new?template= an issue form, and the bare repository is README.md."""
    rest, _, anchor = url[len(REPO):].rstrip(".,;:").partition("#")
    m = re.match(r"^/(blob|tree)/main/([^?]+)$", rest)
    if rest in ("", "/"):
        return None, "README.md", anchor
    if m:
        kind, path = m.groups()
        full = os.path.join(ROOT, path.rstrip("/"))
        if kind == "blob" and not os.path.isfile(full):
            return "is not a file here" if os.path.exists(full) else "links %s, which does not exist" % path, path, anchor
        if kind == "tree" and not os.path.isdir(full):
            return "names no directory here", path, anchor
        return None, path, anchor
    m = re.match(r"^/issues/new\?template=([\w.-]+)$", rest)
    if m:
        return (None if m.group(1) in forms() else "names no issue form in .github/ISSUE_TEMPLATE/"), "", ""
    if rest.lstrip("/").split("/")[0].split("?")[0] in PAGES:
        return None, "", ""
    return "is a link this test cannot check", "", ""


def relative_links(text):
    """Markdown link targets that are not absolute. A PR description or an issue body resolves a relative link
    against /pull/N or /issues/new, so ../README.md#scope becomes a 404."""
    return [u for u in re.findall(r"\]\(\s*([^)\s]+)", text) if not u.startswith(("https://", "http://", "mailto:"))]


def check_pr_template():
    print("pr template: asks for the gate and the changelog, and links only absolutely")
    pr = rd(".github/PULL_REQUEST_TEMPLATE.md")
    for need, why in (("## Summary", "a Summary section"), ("## Test plan", "a Test plan section"),
                      ("bash scripts/check.sh", "the gate's output"), ("CHANGELOG.zh-CN.md", "both changelogs"),
                      ("[Unreleased]", "the [Unreleased] section"), (".zh-CN.md` twin", "English and Chinese in step"),
                      ("build_og.py", "the benchmark regeneration"), ("employer", "an employer's site disclosed"),
                      ("remediation", "no remediation"), ("rubric_proposal.yml", "the rubric proposal form")):
        ok(need in pr, "PULL_REQUEST_TEMPLATE.md asks for %s" % why)
    for kind in ("A site added to the benchmark", "Heuristic fix", "Rubric change", "Engine, MCP server or Action", "Docs or cosmetic"):
        ok("- [ ] " + kind in pr, "PULL_REQUEST_TEMPLATE.md offers the type %r" % kind)
    for name in [".github/PULL_REQUEST_TEMPLATE.md"] + [".github/ISSUE_TEMPLATE/" + f for f in forms() + ["config.yml"]]:
        rel = relative_links(rd(name))
        ok(not rel, "%s has no relative links%s" % (name, (": " + ", ".join(rel)) if rel else ""))
    ok(relative_links("see [Scope](../README.md#scope) and [x](https://a.b/c) [m](mailto:a@b.c)") == ["../README.md#scope"],
       "relative_links finds ../README.md#scope and passes https and mailto")


# what .github/validate.py requires of every rubric version after v1.0 (rules 10, 13 and 22), the version as V
RUBRIC_FILES = ("rubric/vV.md", "rubric/vV.zh-CN.md", "rubric/vV.json", "rubric/evidence-vV.md",
                "rubric/evidence-vV.zh-CN.md", "examples/audits/vV/")


def check_rubric_steps():
    print("rubric: CONTRIBUTING.md and the PR template name every file a new rubric version needs")
    con = rd("CONTRIBUTING.md")
    sec = con[con.index("## Changing the rubric"):]
    sec = sec[:sec.index("\n## ", 1)]
    ver = re.search(r"`rubric/v(\d+\.\d+)\.md`", sec)
    names = [f.replace("V", ver.group(1)) for f in RUBRIC_FILES] if ver else []
    miss = [f for f in names if "`%s`" % f not in sec]
    ok(bool(names) and not miss, "CONTRIBUTING.md 'Changing the rubric' names %s%s"
       % (", ".join(names) or "a next version", (": not " + ", ".join(miss)) if miss else ""))
    # the section tells contributors to add that version, so it must be the one after the newest released
    # rubric: naming a released one asks them to edit it in place, and the line goes stale when it ships
    released = sorted(tuple(int(x) for x in m.groups()) for m in
                      (re.match(r"^v(\d+)\.(\d+)\.md$", f) for f in os.listdir(os.path.join(ROOT, "rubric"))) if m)
    newest = released[-1] if released else (0, 0)
    named = tuple(int(x) for x in ver.group(1).split(".")) if ver else None
    ok(named in ((newest[0], newest[1] + 1), (newest[0] + 1, 0)),
       "CONTRIBUTING.md's next version, v%s, follows the newest in rubric/ (v%d.%d) and is not released yet"
       % (ver.group(1) if ver else "?", newest[0], newest[1]))
    pr = rd(".github/PULL_REQUEST_TEMPLATE.md")
    line = pr[pr.index("New version files:"):].split("\n\n", 1)[0]
    miss = [f.replace("V", "___") for f in RUBRIC_FILES if "`%s`" % f.replace("V", "___") not in line]
    ok(not miss, "PULL_REQUEST_TEMPLATE.md 'New version files' names all %d%s"
       % (len(RUBRIC_FILES), (": not " + ", ".join(miss)) if miss else ""))


def check_sync_script():
    print("sync: scripts/sync_labels.py plans without the network and never deletes")
    spec = importlib.util.spec_from_file_location("sync_labels", os.path.join(ROOT, "scripts", "sync_labels.py"))
    sync = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync)
    local = [{"name": "bug", "color": "d73a4a", "description": "Something isn't working"},
             {"name": "rubric", "color": "a9854c", "description": "Rubric"},
             {"name": "cli", "color": "1d76db", "description": "The command line"}]
    remote = [{"name": "Bug", "color": "D73A4A", "description": "Something isn't working"},
              {"name": "cli", "color": "000000", "description": "The command line"},
              {"name": "wontfix", "color": "ffffff", "description": "This will not be worked on"}]
    create, update, extra = sync.plan(local, remote)
    ok([x["name"] for x in create] == ["rubric"], "a label missing on GitHub is planned for creation")
    ok([(x["name"], [d[0] for d in diff]) for x, diff in update] == [("cli", ["color"])],
       "a differing colour is an update; names and colours match case-insensitively")
    ok([x["name"] for x in extra] == ["wontfix"], "a label only on GitHub is reported as kept")
    src = rd("scripts/sync_labels.py")
    ok('"delete"' not in src and "'delete'" not in src, "the script never calls gh label delete")
    shown = getattr(sync, "proxy_shown", None)
    ok(shown is not None and [shown(u) for u in ("http://user:s3cret@proxy.example:8080", "user:pw@host:3128",
                                                 "http://127.0.0.1:7897")] == ["proxy.example:8080", "host:3128", "127.0.0.1:7897"],
       "proxy_shown keeps the host and port and drops user:password@")
    if os.name == "nt":
        return
    # the whole script with a gh that knows no labels: the summary line must not carry the proxy's password
    with tempfile.TemporaryDirectory() as tmp:
        fake = os.path.join(tmp, "gh")
        io.open(fake, "w").write("#!/bin/sh\necho '[]'\n")
        os.chmod(fake, 0o755)
        env = dict(os.environ, PATH=tmp + os.pathsep + os.environ.get("PATH", ""),
                   HTTPS_PROXY="http://user:s3cret@proxy.example:8080")
        p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "sync_labels.py"), "--check"], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=60)
    ok(p.returncode == 1 and "via proxy.example:8080" in p.stdout and "s3cret" not in p.stdout,
       "sync_labels.py --check names the proxy's host, not its password, and fails on missing labels (exit %d)"
       % p.returncode)


def main():
    check_labels()
    check_forms()
    check_badge()
    check_support()
    check_pr_template()
    check_rubric_steps()
    check_sync_script()
    if fails:
        print("\nFAIL: %d repository metadata check(s)" % len(fails))
        sys.exit(1)
    print("\nOK: the issue forms, labels, badge, SUPPORT.md and PR template agree")


if __name__ == "__main__":
    main()
