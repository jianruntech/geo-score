"""Turn one geo-score JSON report into a GitHub job summary, step outputs and annotations.

Used by action.yml, which runs the CLI once and hands the report here, so the summary, the
annotations and the uploaded files all describe the same fetch. Not part of the CLI contract.

    python3 action/summary.py REPORT [true|false] [BASELINE]
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cli"))
import geo_score as gs  # noqa: E402  (names and the rubric version come from the same release)

NAMES = {c[0]: c[2] for c in gs.SPEC}
NAMES.update({b[0]: b[1] for b in gs.BONUS})
# GitHub shows at most 10 annotations of each level per step; the rest are dropped silently
PER_LEVEL = 10


def _cmd(s):
    return str(s).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _prop(s):
    return _cmd(s).replace(":", "%3A").replace(",", "%2C")


def _cut(s, n):
    s = " ".join(str(s).split())
    if len(s) <= n:
        return s
    # cut on a word boundary: a summary line ending mid-word reads like the tool broke
    out = s[:n].rsplit(" ", 1)[0].rstrip(",.;:") + " …"
    # and never leave a «site text: …» fence open
    return out + "»" if out.rfind("«") > out.rfind("»") else out


def _md(s):
    """Evidence quotes the audited site. In a job summary, GitHub renders Markdown and some HTML, so a
    page could add links, images or an entity such as &raquo; that closes the fence early: escape it."""
    s = html.escape(s, quote=False)
    return re.sub(r"([\\`*_\[\]()!|<>#~])", r"\\\1", s)


# a check id as the tool writes it: g.robots, p2.sourced-stats, b.llms-full
_ID = re.compile(r"[a-z0-9][a-z0-9.-]*")


def _check_id(cid):
    """A check id as a code span. A baseline file is not the tool's own output: an id in it that is not a plain id
    is escaped outside a code span, where a backtick could otherwise close the span and render Markdown."""
    cid = str(cid)
    return "`%s`" % cid if _ID.fullmatch(cid) else _md(cid)


def main(path, annotate, baseline=None):
    d = json.load(open(path, encoding="utf-8"))
    url, norm, band = d["target"], d["normalised"], d["band"]
    checks = [c for c in d["checks"] if not c["id"].startswith("b.")]
    zero = [c for c in checks if c["state"] == "scored" and c["points"] == 0]
    gates = [c for c in zero if c["id"].startswith("g.")]
    others = sorted((c for c in zero if not c["id"].startswith("g.")), key=lambda c: -c["max"])

    # with a baseline (action.yml's copy of it), the CLI already read and checked it before scoring: here it only
    # compares
    diff = gs.diff_reports(gs.load_report(baseline, "baseline"), d, baseline, None) if baseline else None

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write("score=%d\nband=%s\ngate-capped=%s\n" % (norm, band, str(d["gate_capped"]).lower()))
            f.write("report<<GEOEOF\n%s\nGEOEOF\n" % json.dumps(d, ensure_ascii=False))
            if diff is not None:
                f.write("delta=%d\ndropped-checks=%s\n" % (diff["normalised_delta"], ",".join(gs.dropped_checks(diff))))

    if annotate:
        dropped = 0
        for level, rows in (("error", gates), ("warning", others)):
            for c in rows[:PER_LEVEL]:
                why = c.get("evidence") or ""
                print("::%s title=%s::%s" % (level, _prop("geo-score · %s · 0/%d" % (NAMES.get(c["id"], c["id"]), c["max"])),
                                             _cmd(("%s: %s %s" % (url, why, c.get("tier_reason") or "")).strip())))
            dropped += max(0, len(rows) - PER_LEVEL)
        if dropped:
            print("::notice title=geo-score::%d more checks at zero are listed in the job summary" % dropped)

    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summ:
        return
    lines = ["## AI visibility · %s" % url, "",
             "**%d / 100 · %s**%s" % (norm, band, " · capped: a gate check is at zero" if d["gate_capped"] else ""), "",
             "%d of %d checks at zero%s. Rubric %s, %s, %d page%s sampled." % (
                 len(zero), len(checks), " (%d gate)" % len(gates) if gates else "",
                 d["rubric_version"], d["tool"], len(d.get("sampled_urls") or []),
                 "" if len(d.get("sampled_urls") or []) == 1 else "s"), ""]
    if diff is not None:
        lines += baseline_section(diff)
    lines += ["| Check | Score | Why |", "|---|:-:|---|"]
    for c in checks:
        s = "%d/%d" % (c["points"], c["max"]) if c["state"] == "scored" else "—"
        why = _md(_cut(c.get("evidence") or c.get("reason") or "", 150))
        lines.append("| %s %s | %s | %s |" % (NAMES.get(c["id"], ""), _check_id(c["id"]), s, why))
    # observations outside the score, in the CLI's own words: every value from the site is in a code span there
    acc = gs.access_lines(d.get("access"), "md", gs.shown_origin(url))
    if acc:
        lines += ["", "### Outside the score (observed, never scored)", ""] + acc
    lines += ["", "— means the CLI cannot observe the check; it leaves the denominator instead of scoring 0.",
              "Scored against the open [AIV rubric %s](https://github.com/jianruntech/geo-score/blob/main/rubric/%s.md)."
              % (d["rubric_version"], d["rubric_version"]), ""]
    with open(summ, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def baseline_section(diff):
    """'Changes since baseline': the score, the band and the gate cap before and after, then only the checks that
    moved. The CLI's log carries the full table."""
    b, a = diff["before"], diff["after"]
    delta = diff["normalised_delta"]
    head = "**%d → %d** (%s)" % (b["normalised"], a["normalised"], "%+d" % delta if delta else "no change")
    if diff["within_spread"] and delta:
        head += ", within the measured spread"
    head += " · %s" % (_md(a["band"]) if a["band"] == b["band"] else "%s → %s" % (_md(b["band"]), _md(a["band"])))
    head += " · gate capped: %s → %s" % ("yes" if b["gate_capped"] else "no", "yes" if a["gate_capped"] else "no")
    lines = ["### Changes since baseline", "", head, ""]
    moved = [x for x in diff["checks"] if x["state"] not in ("same", "unobservable")]
    if moved:
        lines += ["| Check | Before | After | Change |", "|---|:-:|:-:|---|"]
        for x in moved:
            before, after = ("—" if v is None else "%d/%s" % (v, x["max"]) for v in (x["before"], x["after"]))
            change = x["state"] + (" %+d" % (x["after"] - x["before"]) if x["state"] in ("up", "down") else "")
            lines.append("| %s %s | %s | %s | %s |" % (NAMES.get(x["id"], ""), _check_id(x["id"]), before, after, change))
    else:
        lines.append("No check moved.")
    lines.append("")
    pages = ["%d %s" % (len(urls), label) for label, urls in (("added", diff["pages_added"]),
                                                             ("removed", diff["pages_removed"])) if urls]
    if pages:
        lines += ["Pages since the baseline: %s." % ", ".join(pages), ""]
    for n in diff["notes"]:
        lines += [_md(n), ""]
    return lines


def assertion_errors(path):
    """One ::error per failed fail-on-gate or assert check, for the step that already failed on them. The
    expressions come from the action's inputs through the environment, one per line; the CLI refused any
    malformed one before it scored, so here they parse."""
    d = json.load(open(path, encoding="utf-8"))
    exprs = ([("fail-on-gate", "g.*>0")] if os.environ.get("GEO_FAIL_ON_GATE") == "true" else []) \
        + [("assert " + x.strip(), x.strip()) for x in os.environ.get("GEO_ASSERT", "").splitlines() if x.strip()]
    ev = {c["id"]: c.get("evidence", "") for c in d["checks"]}
    for label, expr in exprs:
        for _e, cid, got, mx, passed in gs.check_assertions(d, [gs.parse_assert(expr)]):
            if passed is False:
                print("::error title=%s::%s" % (_prop("geo-score · %s" % label),
                                                _cmd("%s: %s is %d/%d. %s" % (d["target"], cid, got, mx, _cut(ev.get(cid, ""), 200)))))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--assertions"]:
        assertion_errors(sys.argv[2])
    else:
        main(sys.argv[1], sys.argv[2:3] != ["false"], (sys.argv[3:4] or [""])[0])
