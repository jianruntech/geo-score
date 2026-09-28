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
    check_sync_script()
    if fails:
        print("\nFAIL: %d repository metadata check(s)" % len(fails))
        sys.exit(1)
    print("\nOK: the issue forms, labels.json and the sync script agree")


if __name__ == "__main__":
    main()
