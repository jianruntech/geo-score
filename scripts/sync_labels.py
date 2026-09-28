#!/usr/bin/env python3
"""Bring the repository's GitHub labels in line with .github/labels.json.

    python3 scripts/sync_labels.py              # dry run: list what would be created or updated
    python3 scripts/sync_labels.py --apply      # create the missing labels, update colour and description
    python3 scripts/sync_labels.py --check      # exit 1 when a label in labels.json is missing on GitHub

An issue form that names a label the repository does not have files its issues unlabelled, so the
forms and labels.json are checked against each other offline (scripts/test_repo_meta.py), and this
script carries labels.json to GitHub. It shells out to the gh CLI, which must be logged in for
--apply. gh reads HTTPS_PROXY from the environment, which is passed through unchanged. A label on
GitHub that labels.json does not list is reported and kept: this script never deletes a label.
Stdlib only, Python 3.8+.
"""
import argparse, io, json, os, shutil, subprocess, sys, urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LABELS = os.path.join(ROOT, ".github", "labels.json")
REPO = "jianruntech/geo-score"


def load_local(path=LABELS):
    return json.load(io.open(path, encoding="utf-8"))["labels"]


def plan(local, remote):
    """(to create, to update, extra on GitHub). Names match case-insensitively, as GitHub's do.
    Each update is (label, [(field, now, want), ...])."""
    have = {r["name"].lower(): r for r in remote}
    create, update = [], []
    for lab in local:
        r = have.get(lab["name"].lower())
        if r is None:
            create.append(lab)
            continue
        diff = [(f, r.get(f) or "", lab[f]) for f in ("color", "description")
                if (r.get(f) or "").lower() != lab[f].lower()]
        if diff:
            update.append((lab, diff))
    names = {lab["name"].lower() for lab in local}
    extra = [r for r in remote if r["name"].lower() not in names]
    return create, update, extra


def proxy_shown(url):
    """The proxy's host and port for the summary line, without the user:password@ a proxy URL can carry:
    this line ends up in terminals and CI logs."""
    u = urllib.parse.urlsplit(url if "://" in url else "http://" + url)
    try:
        port = u.port
    except ValueError:
        port = None
    return (u.hostname or "?") + (":%d" % port if port else "")


def gh(args):
    # the environment, HTTPS_PROXY included, goes to gh as it is
    p = subprocess.run(["gh"] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if p.returncode:
        sys.exit("gh %s failed: %s" % (args[0] + " " + args[1], (p.stderr or p.stdout).strip()[-400:]))
    return p.stdout


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sync .github/labels.json to the repository's GitHub labels (never deletes).")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="create and update labels (default: dry run)")
    mode.add_argument("--check", action="store_true", help="exit 1 when a label in labels.json is missing on GitHub")
    ap.add_argument("--repo", default=REPO, help="OWNER/NAME (default %s)" % REPO)
    a = ap.parse_args(argv)
    if not shutil.which("gh"):
        print("gh not found: install the GitHub CLI (https://cli.github.com/)", file=sys.stderr)
        return 2
    local = load_local()
    remote = json.loads(gh(["label", "list", "--repo", a.repo, "--json", "name,color,description", "--limit", "1000"]))
    create, update, extra = plan(local, remote)
    print("%s: %d labels · %s: %d labels%s" % (os.path.relpath(LABELS, ROOT), len(local), a.repo, len(remote),
                                              " (via %s)" % proxy_shown(os.environ["HTTPS_PROXY"])
                                              if os.environ.get("HTTPS_PROXY") else ""))
    for lab in create:
        print("  missing  %-16s #%s  %s" % (lab["name"], lab["color"], lab["description"]))
    for lab, diff in update:
        print("  differs  %-16s %s" % (lab["name"], "; ".join("%s %r -> %r" % d for d in diff)))
    for r in extra:
        print("  kept     %-16s on GitHub, not in labels.json (never deleted)" % r["name"])
    if a.check:
        if create:
            print("FAIL: %d label(s) missing on %s: %s" % (len(create), a.repo, ", ".join(x["name"] for x in create)))
            return 1
        print("OK: every label in labels.json exists on %s" % a.repo)
        return 0
    if not a.apply:
        print("dry run: %d to create, %d to update, nothing changed. Run with --apply to write." % (len(create), len(update)))
        return 0
    for lab in create:
        gh(["label", "create", lab["name"], "--repo", a.repo, "--color", lab["color"], "--description", lab["description"]])
        print("  created  %s" % lab["name"])
    for lab, _ in update:
        gh(["label", "edit", lab["name"], "--repo", a.repo, "--color", lab["color"], "--description", lab["description"]])
        print("  updated  %s" % lab["name"])
    print("applied: %d created, %d updated, none deleted" % (len(create), len(update)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
