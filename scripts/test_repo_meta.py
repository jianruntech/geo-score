#!/usr/bin/env python3
"""Check the contributor-facing files against each other, offline.

    python3 scripts/test_repo_meta.py

The issue forms, the label list and the sync script only work together: GitHub drops a label an issue
form applies when the repository does not have it, so the issue arrives unlabelled and nobody notices.
This reads the forms without a YAML library and checks every label they apply is in .github/labels.json,
which scripts/sync_labels.py carries to GitHub.
"""
import importlib.util, io, json, os, re, sys

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
    said = re.findall(r"(\d+/100 [A-Z][a-z]+(?: [a-z]+)*)( \(gate capped\))?", svg)
    ok(len(said) >= 2 and all(s == want for s, _ in said), "the SVG reads %r everywhere, as the report does (%s)"
       % (want, sorted({s for s, _ in said})))
    ok(all(rep.get("gate_capped") is True for _, capped in said if capped), "the SVG says gate capped only when the report is")
    ok(bool(rep.get("audited_at")) and bool(rep.get("tool")), "the report records when (%s) and with what (%s) it was measured"
       % (rep.get("audited_at"), rep.get("tool")))
    m = re.search(r"\[!\[([^\]]*)\]\(docs/aiv-badge\.svg\)\]\(([^)\s]+)\)", rd("README.md"))
    ok(m is not None, "README.md shows the badge as a link")
    if m:
        alt, link = m.groups()
        ok(link.rstrip("/") == rep["target"].rstrip("/"), "the badge links to the page it measured (%s; report: %s)"
           % (link, rep["target"]))
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", alt)
        ok(all(d == rep["audited_at"] for d in dates), "a date in the badge's alt text is the report's audited_at (%s)"
           % (", ".join(dates) or "none named"))


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
    # every absolute link into this repository from the chooser, the forms and SUPPORT.md must resolve
    texts = [(".github/ISSUE_TEMPLATE/" + f, rd(".github/ISSUE_TEMPLATE/" + f)) for f in forms() + ["config.yml"]]
    texts += [("SUPPORT.md", rd("SUPPORT.md")), (".github/PULL_REQUEST_TEMPLATE.md", rd(".github/PULL_REQUEST_TEMPLATE.md"))]
    seen = 0
    for name, text in texts:
        for path, anchor in re.findall(r"https://github\.com/jianruntech/geo-score(?:/blob/main/([^\s)#\]]+))?(?:#([\w-]+))?", text):
            path = path or "README.md"
            if not os.path.exists(os.path.join(ROOT, path)):
                ok(False, "%s: links %s, which does not exist" % (name, path))
                continue
            if anchor and path.endswith(".md"):
                seen += 1
                ok(anchor_exists(path, anchor), "%s: %s#%s is a heading there" % (name, path, anchor))
    sup = rd("SUPPORT.md")
    for path, anchor in re.findall(r"\]\(([\w./-]+\.md)#([\w-]+)\)", sup):
        seen += 1
        ok(os.path.exists(os.path.join(ROOT, path)) and anchor_exists(path, anchor), "SUPPORT.md: %s#%s is a heading there"
           % (path, anchor))
    ok(seen >= 6, "the chooser, the forms and SUPPORT.md link %d headings, all checked" % seen)
    linked = set(re.findall(r"issues/new\?template=([\w.-]+)", sup))
    ok(linked == set(forms()), "SUPPORT.md links every issue form and only those (%s)" % ", ".join(sorted(linked)))
    ok("README.md#scope--what-this-does-not-do" in sup, "SUPPORT.md says remediation is out of scope, linked to Scope")


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


def main():
    check_labels()
    check_forms()
    check_badge()
    check_support()
    check_pr_template()
    check_sync_script()
    if fails:
        print("\nFAIL: %d repository metadata check(s)" % len(fails))
        sys.exit(1)
    print("\nOK: the issue forms, labels.json and the sync script agree")


if __name__ == "__main__":
    main()
