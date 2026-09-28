#!/usr/bin/env python3
"""Score every site in sites.json and write results.json + README.md.

    python3 benchmark/run.py            # score everything
    python3 benchmark/run.py --limit 5  # a quick subset
    python3 benchmark/run.py --out ~/geo-runs/b --vantage "LABEL" [--urls-from-dir ~/geo-runs/a/raw]
                                        # a retest run for retest.py; the published files are left alone

Runs the CLI in-process. Live sites change, so re-running gives slightly different
numbers; every result records the date it was measured, the tool and Python versions,
and the vantage the operator declared.
"""
import urllib.parse
import argparse, concurrent.futures as cf, csv, importlib.util, inspect, io, json, os, platform, re, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gs", os.path.join(HERE, "..", "cli", "geo_score.py"))
gs = importlib.util.module_from_spec(spec); spec.loader.exec_module(gs)
gs.c.on = False

RAW = os.path.join(HERE, "raw")
# --urls-from-dir: re-read the pages an earlier run sampled, DIR/<site>.json, through the CLI's --urls-from reader
PIN_DIR = None
SAMPLE = 8                  # pages asked of the CLI per site; a site with fewer reachable pages is scored on fewer
WORKERS = 4                 # sites measured at a time

# The most requests one site costs, as cli/geo_score.py's discover() and run() make them. The user-agent lists and
# the thread count come from the CLI itself; these mirror literals in those two functions (the pages the crawler
# probes read, the section indexes discovery tries, the sameAs profiles checked, the brand names looked up), and
# test_benchmark.py drives the CLI against a synthetic site to hold every row to what it actually sends.
PROBE_PAGES, SECTION_INDEXES, SAMEAS_MAX, KG_NAMES = 3, 8, 8, 3
CORRECTION_FORM = "https://github.com/jianruntech/geo-score/issues/new?template=benchmark_correction.yml"

def fetch_budget():
    """Rows of (key, what, requests, user-agent) sent to the site, then (key, what, requests) sent elsewhere."""
    r, cn = len(gs.RETRIEVAL_UAS), len(gs.CN_UAS)
    site = [("home_robots", "The homepage, and `robots.txt` twice (to find sitemaps, then for `g.robots`)", 3, "browser"),
            ("sitemaps", "Sitemaps: up to 3 candidates and 2 child sitemaps while sampling, up to 4 and 1 for "
                         "`p1.sitemap`", 10, "browser"),
            ("sections", "Section index pages (`/blog`, `/news`, …) while sampling", SECTION_INDEXES, "browser"),
            ("sampled", "Sampled pages, the homepage first", SAMPLE, "browser"),
            ("retrieval", "%d retrieval-crawler user-agents × up to %d sampled pages (`g.reachable`)"
                          % (r, PROBE_PAGES), r * PROBE_PAGES, "crawler"),
            ("cn", "%d Chinese-crawler user-agents on the homepage, only for a site that addresses the Chinese "
                   "market (`p4.cn-engines`)" % cn, cn, "crawler"),
            ("text_files", "`llms.txt`, `llms-full.txt`, `ai.txt` and `/.well-known/ai.txt`", 4, "browser"),
            ("logo", "The Organization logo", 1, "browser")]
    elsewhere = [("sameas", "The `sameAs` profiles the site declares, up to %d" % SAMEAS_MAX, SAMEAS_MAX),
                 ("kg", "Wikidata and Wikipedia searches: up to %d brand names, in Chinese and English for a "
                        "Chinese-language site and in English otherwise" % KG_NAMES, KG_NAMES * 2 * 2)]
    return site, elsewhere

def _fetch_block():
    """'How the benchmark fetches': the per-site budget from fetch_budget() and who the crawler probes come from."""
    from build_page import num_words
    site, elsewhere = fetch_budget()
    threads = inspect.signature(gs.pmap).parameters["workers"].default
    retries = inspect.signature(gs.fetch_steady).parameters["tries"].default - 1
    L = ["## How the benchmark fetches\n",
         "Each site is measured by the CLI in this repository, which [run.py](run.py) runs in-process, %d sites at a"
         % WORKERS,
         "time and up to %d requests at a time within a site. Per site it sends at most **%d requests to the site**"
         % (threads, sum(x[2] for x in site)),
         "and **%d elsewhere**, counted before redirects and before the %s retries a sampling request gets after a"
         % (sum(x[2] for x in elsewhere), num_words(retries, "en")),
         "timeout, a 429 or a 5xx:\n",
         "| Requests | At most | User-agent |", "|---|:-:|---|"]
    L += ["| %s | %d | %s |" % (what, n, ua) for _, what, n, ua in site]
    L += ["| %s | %d | browser, to other hosts |" % (what, n) for _, what, n in elsewhere]
    L += ["\nA site that fails outright is tried once more on its `www` host. The crawler user-agents are sent from",
          "the operator's own address, not from the addresses their vendors publish, so a server that verifies",
          "crawlers by IP range or reverse DNS sees an unverified client. That is why a 403 to those probes is",
          "reported as the server refusing crawler user-agents, not as proof that it blocks the crawlers themselves.\n"]
    return "\n".join(L)

def _corrections_block():
    return "\n".join([
        "## Corrections\n",
        "If a row is wrong — a score, a gate reason, a label such as *deliberate*, or a not-scored reason — report it",
        "with the [benchmark correction form](%s), with the output of" % CORRECTION_FORM,
        "`geo_score.py SITE --json-out` from your own network. A confirmed tool error is fixed in the CLI and shipped",
        "as a patch release. Published scores change only when a site is measured again, and every row keeps the",
        "date and the tool version it was measured with.\n"])

# The CLI's error when every sampled page was a bot challenge (the string is its contract with this script).
# Such a site cannot be measured by a static fetch, which is a different thing from refusing crawlers.
BOT_CHALLENGE = "bot challenge served to a browser user-agent"
NOT_SCORED = [("bot challenge", "**Bot challenge** — a browser user-agent was served a challenge page, so a static "
                                "fetch cannot measure the site"),
              ("refused", "**Refused** — no request came back 200 (each site's statuses are listed below)"),
              ("timed out", "**Timed out**"),
              ("connection failed", "**Connection failed** — a TLS or network error before any answer"),
              ("other", "Other")]

def not_scored_reason(error):
    """The reason a listed site has no score, from the error run.py recorded for it."""
    e = error or ""
    if e.startswith(BOT_CHALLENGE):
        return "bot challenge"
    if "all requests returned" in e:
        return "refused"
    if "timed out" in e:
        return "timed out"
    if "urlopen error" in e or "ssl" in e.lower():
        return "connection failed"
    return "other"

def raw_name(site_url):
    """benchmark/raw/<site>.json; a site given with a path keeps it, with / as __."""
    return re.sub(r"[^A-Za-z0-9.\-]+", "__", site_url.strip("/")) + ".json"

def one(site):
    base = site["url"] if "://" in site["url"] else "https://" + site["url"]
    host = base.split("://", 1)[1]
    attempts = [base] + ([("https://www." + host)] if not host.startswith("www.") else [])
    pinned = None
    if PIN_DIR:
        # sampling is the largest source of run-to-run variance; a pinned run leaves the site and the network
        try:
            pinned = gs.read_report_urls(os.path.join(PIN_DIR, raw_name(site["url"])))
        except RuntimeError as e:
            return dict(site=site["url"], sector=site["sector"], error=("not pinned: %s" % e)[:120])
        # score the origin those pages were read on, which may be the www host the earlier run landed on
        p0 = urllib.parse.urlsplit(pinned[0])
        attempts = ["%s://%s%s" % (p0.scheme, p0.netloc, urllib.parse.urlsplit(base).path.rstrip("/"))]
    res = err = None
    for u in attempts:                       # some sites only answer on www
        try:
            res = gs.run(u, SAMPLE, urls=pinned) if pinned else gs.run(u, SAMPLE); break
        except Exception as e:
            # a bot challenge on the bare host says more than whatever the www host answers after it
            if err is None or not str(err).startswith(BOT_CHALLENGE):
                err = e
            time.sleep(1)
    try:
        if res is None: raise err or RuntimeError("unreachable")
        rows, total, den, bon, norm, bd, capped = gs.score(res)
        gaps = sorted([(mx - t, cid) for cid, _, _, t, mx, _ in rows if t is not None and t < mx],
                      reverse=True)[:3]
        gates = {cid: t for cid, _, _, t, _, _ in rows if cid.startswith("g.")}
        zero = [cid for cid, t in gates.items() if t == 0]
        reason = None
        if zero:
            # a robots.txt block is an editorial choice; a JS-only page is an accident.
            # Reporting them as the same "capped" is what makes the number useless.
            reason = ("blocks crawlers" if "g.robots" in zero else
                      "serves crawlers an error" if "g.reachable" in zero else
                      "content needs JavaScript")
        def _apex(u):
            h = urllib.parse.urlsplit(u if "://" in u else "https://" + u).netloc.lower()
            h = h.split(":")[0]
            return h[4:] if h.startswith("www.") else h
        landed = res.get("landed") or ""
        resolved = _apex(landed) if landed and _apex(landed) != _apex(site["url"]) else None
        # the full report, so the benchmark can be re-analysed check by check without re-scoring
        os.makedirs(RAW, exist_ok=True)
        with io.open(os.path.join(RAW, raw_name(site["url"])), "w", encoding="utf-8") as f:
            json.dump(gs.as_json(res), f, ensure_ascii=False, indent=1)
            f.write("\n")
        return dict(site=site["url"], sector=site["sector"], tool_version=gs.__version__, readiness=total,
                    observable_max=den, normalised=norm, band=bd, gate_capped=capped,
                    resolved_to=resolved,
                    # how many pages the checks actually read, and where the sample came from
                    sample_n=len(res["urls"]), sample_source=res.get("sample_source"),
                    gates=gates, gate_reason=reason,
                    bonus=bon, top_gaps=[c for _, c in gaps],
                    pillars={p: [sum(r[3] for r in rows if r[1] == p and r[3] is not None),
                                 sum(r[4] for r in rows if r[1] == p and r[3] is not None)]
                             for p in dict.fromkeys(r[1] for r in rows)})
    except Exception as e:
        return dict(site=site["url"], sector=site["sector"], error=str(e)[:120])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int); ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--readme-only", action="store_true",
                    help="rewrite README.md and stats.json from the committed results.json; no scoring, no network")
    ap.add_argument("--out", metavar="DIR",
                    help="write results.json and raw/ to DIR instead of benchmark/, for retest.py; "
                         "README.md and stats.json describe the published run and are left alone")
    ap.add_argument("--urls-from-dir", metavar="DIR",
                    help="pin each site to the pages in DIR/<site>.json (an earlier run's raw/), as --urls-from does")
    ap.add_argument("--vantage", metavar="LABEL",
                    help="where this run is measured from, as the operator declares it (e.g. 'Shenzhen, home "
                         "broadband'); recorded as measured_from, never looked up")
    a = ap.parse_args()
    if a.readme_only:
        write_readme(json.load(io.open(os.path.join(HERE, "results.json"), encoding="utf-8")))
        print("wrote benchmark/README.md, stats.json, results.csv and checks.csv from results.json and raw/",
              file=sys.stderr)
        return
    global RAW, PIN_DIR
    out_dir = os.path.abspath(a.out) if a.out else HERE
    RAW, PIN_DIR = os.path.join(out_dir, "raw"), a.urls_from_dir
    if PIN_DIR and not os.path.isdir(PIN_DIR):
        ap.error("--urls-from-dir %s is not a directory" % PIN_DIR)
    cfg = json.load(io.open(os.path.join(HERE, "sites.json"), encoding="utf-8"))
    sites = cfg["sites"][:a.limit] if a.limit else cfg["sites"]
    print("scoring %d sites…" % len(sites), file=sys.stderr)
    out = []
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for i, r in enumerate(ex.map(one, sites), 1):
            out.append(r)
            print("  %2d/%d  %-20s %s" % (i, len(sites), r["site"],
                  r.get("error") or "%3d  %s" % (r["normalised"], r["band"])), file=sys.stderr)
    ok = [r for r in out if "error" not in r]
    ok.sort(key=lambda r: -r["normalised"])
    scores = [r["normalised"] for r in ok]
    stats = dict(n=len(ok), mean=round(statistics.mean(scores), 1),
                 median=statistics.median(scores), p25=_q(scores, .25), p75=_q(scores, .75),
                 min=min(scores), max=max(scores))
    by_sector = {}
    for r in ok: by_sector.setdefault(r["sector"], []).append(r["normalised"])
    payload = dict(rubric_version=gs.RUBRIC, tool="geo-score-cli/%s" % gs.__version__,
                   measured_at=time.strftime("%Y-%m-%d"),
                   # what retest.py needs to tell runs apart: the vantage is declared, not detected
                   measured_from=a.vantage, python=platform.python_version(), pinned_from=a.urls_from_dir,
                   stats=stats,
                   sectors={k: dict(n=len(v), median=statistics.median(v)) for k, v in sorted(by_sector.items())},
                   results=ok + [r for r in out if "error" in r])
    io.open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8").write(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print("\n%d sites · mean %s · median %s · range %d-%d"
          % (stats["n"], stats["mean"], stats["median"], stats["min"], stats["max"]), file=sys.stderr)
    if out_dir != HERE:
        print("wrote %s; compare runs with python3 benchmark/retest.py DIR_A DIR_B …" % out_dir, file=sys.stderr)
        return
    write_readme(payload)
    print("next: python3 benchmark/build_page.py   (regenerates the public pages)", file=sys.stderr)

def _load(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)

def _rubric():
    return _load(os.path.join(HERE, "..", "rubric", "v1.1.json"))

def _q(xs, q):
    xs = sorted(xs); i = (len(xs) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 1)

def _uncertainty(p):
    """95% intervals for the medians this README quotes (benchmark/stats.py), written alongside it."""
    sys.path.insert(0, HERE)
    import stats as bstats
    u = bstats.compute(p)
    io.open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8").write(json.dumps(u, ensure_ascii=False, indent=1) + "\n")
    return u

def _gap_drivers(ok):
    """Checks that separate the China-market sites from the rest: mean points, rest minus China, from the
    per-site reports in raw/. Empty when those are missing."""
    groups = {True: {}, False: {}}
    for r in ok:
        fp = os.path.join(RAW, raw_name(r["site"]))
        if not os.path.exists(fp):
            return []
        rep = json.load(io.open(fp, encoding="utf-8"))
        g = groups[r["sector"].startswith("China")]
        for c in rep["checks"]:
            if c["state"] == "scored" and not c["id"].startswith("b."):
                g.setdefault(c["id"], []).append(c["points"])
    diffs = [(cid, statistics.mean(groups[False][cid]) - statistics.mean(groups[True][cid]))
             for cid in groups[True] if cid in groups[False] and len(groups[True][cid]) >= 10]
    return sorted([d for d in diffs if d[1] > 0], key=lambda d: -d[1])

def _cjk_caveat(check_ids):
    """Where a check that drives the China gap is one the CLI read lower than a human on a Chinese site in
    the hand-audit comparison (validity.json), say so: part of the gap may be the heuristic, not the sites."""
    vp = os.path.join(HERE, "validity.json")
    if not os.path.exists(vp):
        return ""
    v = json.load(io.open(vp, encoding="utf-8"))
    hits = []
    for c in v["per_check"]:
        if c["id"] not in check_ids:
            continue
        for d in c.get("disagreements", []):
            ap = os.path.join(HERE, "..", "examples", "audits", "v1.1", d["site"] + ".json")
            if os.path.exists(ap) and str(json.load(io.open(ap, encoding="utf-8")).get("audience_language", "")).startswith("zh") \
                    and d["cli"] < d["human"]:
                hits.append("`%s` on %s (%d by hand, %d by the CLI)" % (c["id"], d["site"], d["human"], d["cli"]))
    if not hits:
        return ""
    return ("Read the first two with care: they are heuristics, and on the Chinese site in the CLI-vs-hand-audit "
            "comparison the CLI scored %s ([VALIDITY.md](VALIDITY.md)). Part of this gap may be the heuristics "
            "reading Chinese pages conservatively rather than the sites." % "; ".join(hits))

def _china_block(u):
    """The China-gap paragraph. Every figure comes from stats.json (stats.py), and validate.py holds the block
    between the markers to that file, so the headline cannot drift from its decomposition."""
    from build_page import num_words
    g, d = u["china_gap"], u.get("china_gap_detail")
    L = ["<!-- china-gap: generated by run.py from stats.json -->",
         "**Sites in the %sChina sectors score %d points lower** (95%% CI %d–%d): median %d against %d for the"
         % (num_words(len(d["china_sectors"]), "en") + " " if d else "", g["gap"],
            g["ci"][0], g["ci"][1], g["median_china"], g["median_rest"]),
         "other %d scored sites." % g["n_rest"]]
    if d:
        lg, x, f, m, kg = d["by_language"], d["crosstab"], d["families"], d["by_method"], d["knowledge_graph"]["by_language"]
        other = "English" if list(x["other_languages"]) == ["en"] else "another language"
        L.append("By the language a site serves rather than its sector label, the %d Chinese-language sites score %d "
                 "points lower than the %d others (95%% CI %d–%d): %d of the %d China-sector sites were read as "
                 "serving %s, and %d sites in other sectors serve Chinese."
                 % (lg["n_group"], lg["gap"], lg["n_vs"], lg["ci"][0], lg["ci"][1], x["china"]["other"],
                    x["china"]["zh"] + x["china"]["other"], other, x["rest"]["zh"]))
        if f["range"]:
            shown = [p for p in f["pairs"] if p["gap"] is not None]
            lo = min(shown, key=lambda p: p["gap"]); hi = max(shown, key=lambda p: p["gap"])
            L.append("Within matched sector families the gap runs from %d points (%s against %s) to %d (%s against %s)%s."
                     % (lo["gap"], lo["group"], lo["vs"], hi["gap"], hi["group"], hi["vs"],
                        "; %s %s too few scored sites to compare" % (" and ".join(f["suppressed"]),
                                                                      "has" if len(f["suppressed"]) == 1 else "have")
                        if f["suppressed"] else ""))
        if m["heuristic_share_pct"] is not None:
            L.append("Counted in raw points check by check, the gap is %.1f points, and %.1f of them sit in checks the CLI "
                     "reads with a heuristic: at most %d%% of the gap could be a heuristic misreading Chinese pages "
                     "rather than the sites." % (m["total"], m["heuristic"], m["heuristic_share_pct"]))
        L.append("`%s` could not be observed on %d of %d Chinese-language sites against %d of %d others: a Chinese "
                 "site is looked up in both languages, and absence needs every lookup to answer. Scored %s wherever "
                 "it was unobservable, the gap would be %s points."
                 % (d["knowledge_graph"]["check"], kg["zh"]["unobservable"], kg["zh"]["n"], kg["other"]["unobservable"],
                    kg["other"]["n"], " or ".join(sorted(d["kg_imputed"], key=int)),
                    " or ".join(str(d["kg_imputed"][k]["gap"]) for k in sorted(d["kg_imputed"], key=int))))
        L.append("The breakdown is in [stats.json](stats.json) under `china_gap_detail`.")
    L.append("<!-- /china-gap -->\n")
    return "\n".join(L)

# results.csv: one row per listed site, then one column per check holding its points (blank when unobservable);
# checks.csv: one row per scored site and check. Flat files for a spreadsheet, pandas or Datasette, written with
# README.md from the same results.json and raw/, so validate.py can hold them to both.
RESULT_COLUMNS = ["site", "sector", "measured_at", "tool_version", "normalised", "readiness", "observable_max", "band",
                  "gate_capped", "gate_reason", "resolved_to", "sample_n", "sample_source", "not_scored_reason", "error"]
CHECK_COLUMNS = ["site", "check_id", "state", "points", "max"]

def _cell(v):
    return "" if v is None else ("true" if v is True else "false" if v is False else v)

def _write_csv(path, header, rows):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow([_cell(x) for x in r])

def write_csvs(p, reports, out_dir=HERE):
    """results.csv and checks.csv in out_dir, sorted by site. `reports` maps a scored site to its raw report."""
    ids = [c["id"] for c in _rubric()["checks"]]
    tool = (p.get("tool") or "").rsplit("/", 1)[-1] or None
    res, chk = [], []
    for r in sorted(p["results"], key=lambda x: x["site"]):
        rep = reports.get(r["site"])
        if rep is None:
            res.append([r["site"], r["sector"], p["measured_at"], r.get("tool_version") or tool] + [None] * 9
                       + [not_scored_reason(r.get("error")) if "error" in r else None, r.get("error")] + [None] * len(ids))
            continue
        st = {c["id"]: c for c in rep["checks"]}
        pts = [st[c].get("points") if c in st and st[c].get("state") == "scored" else None for c in ids]
        res.append([r["site"], r["sector"], rep.get("audited_at") or p["measured_at"], r.get("tool_version") or tool,
                    r["normalised"], r["readiness"], r["observable_max"], r["band"], bool(r.get("gate_capped")),
                    r.get("gate_reason"), r.get("resolved_to"), len(rep.get("sampled_urls") or []),
                    rep.get("sample_source"), None, None] + pts)
        for c in ids:
            if c in st:
                scored = st[c].get("state") == "scored"
                chk.append([r["site"], c, st[c].get("state"), st[c].get("points") if scored else None,
                            st[c].get("max") if scored else None])
    _write_csv(os.path.join(out_dir, "results.csv"), RESULT_COLUMNS + ids, res)
    _write_csv(os.path.join(out_dir, "checks.csv"), CHECK_COLUMNS, chk)

# The adoption table: shares of scored sites, each over the sites where its check was observed, from raw/.
ADOPTION = [("An `llms.txt` served as text", "p1.llms-txt", lambda c: c["points"] > 0),
            ("Organization and WebSite markup with name, url and logo (`p1.organization` at 5 or more)",
             "p1.organization", lambda c: c["points"] >= 5),
            ("BreadcrumbList on at least one nested page", "p1.breadcrumb", lambda c: c["points"] > 0),
            ("A sitemap with `<lastmod>` on most of its URLs (`p1.sitemap` at 4)", "p1.sitemap",
             lambda c: c["points"] == c["max"]),
            ("A personal byline on at least half the sampled pages", "p2.named-author",
             lambda c: _half_bylined(c.get("evidence")))]

def _half_bylined(evidence):
    """True or False from the check's evidence ('N of M pages carry a personal byline'); None when it does not say."""
    m = re.search(r"(\d+) of (\d+) pages carry a personal byline", evidence or "")
    return None if not m else 2 * int(m.group(1)) >= int(m.group(2))

def _adoption_block(reports):
    L = ["## How common each practice is\n",
         "Shares of the scored sites, each over the sites where the check could be observed, from the",
         "[per-site reports](raw/):\n",
         "| Practice | Sites | Share |", "|---|:-:|:-:|"]
    for what, cid, test in ADOPTION:
        got = [test(c) for rep in reports.values() for c in rep["checks"] if c["id"] == cid and c["state"] == "scored"]
        got = [g for g in got if g is not None]
        if got:
            L.append("| %s | %d of %d | %d%% |" % (what, sum(got), len(got), round(100.0 * sum(got) / len(got))))
    L += ["\nFor comparison, the [Web Almanac 2025](https://almanac.httparchive.org/en/2025/seo) found `llms.txt` on",
          "2.13% of desktop sites. The populations differ: the Almanac crawls millions of sites, this list is a few",
          "hundred prominent ones picked for sector and language coverage, so neither share estimates the other.\n"]
    return "\n".join(L)

def _sample_sentence(u):
    """The opening sentence: the sample is up to eight pages, and the rows that got fewer than THIN_N are counted
    from raw/ and named. validate.py holds it to raw/."""
    ts = u.get("thin_sample")
    if not ts:
        return "Every site below scored with the same open rubric and the same public tool, on up to eight pages per site."
    s = ("Every site below scored with the same open rubric and the same public tool, on up to eight pages per site; "
         "%d sites were scored on fewer than %d pages (%d of them on a single page) and are marked *thin sample*."
         % (ts["n_thin"], ts["threshold"], ts["n_single_page"]))
    if ts["n_thin"] and ts["without_thin"]:
        s += (" A site gets fewer pages when its sample cannot be filled: no sitemap was reachable and the homepage "
              "links to few pages, or sampled pages failed to load. Without those rows the median is %d (95%% CI "
              "%d–%d) rather than %d." % (ts["without_thin"]["median"], ts["without_thin"]["ci"][0],
                                          ts["without_thin"]["ci"][1], ts["with_thin"]["median"]))
    return s

def write_readme(p):
    s, L = p["stats"], []
    A = L.append
    u = _uncertainty(p)
    A("# The state of AI visibility\n")
    A(_sample_sentence(u))
    A("No private data, no vendor dashboards — [re-run it yourself](run.py).\n")
    A("**%d sites · median %s (95%% CI %d–%d) · mean %s · upper quartile %s · range %d–%d** · rubric %s · measured %s\n"
      % (s["n"], s["median"], u["overall"]["ci"][0], u["overall"]["ci"][1], s["mean"], s["p75"], s["min"], s["max"],
         p["rubric_version"], p["measured_at"]))
    ok = [x for x in p["results"] if "error" not in x]
    cn = [x["normalised"] for x in ok if x["sector"].startswith("China")]
    row = [x["normalised"] for x in ok if not x["sector"].startswith("China")]
    from collections import Counter
    gap = Counter(g for x in ok for g in x["top_gaps"])
    capped = [x for x in ok if x.get("gate_capped")]
    sys.path.insert(0, HERE)
    from build_page import share_words, crawler_note, challenge_note, thin_words, REFUSED
    import stats as bstats
    reports = {}
    for x in ok:
        fp = bstats.raw_path(x["site"])
        if os.path.exists(fp):
            reports[x["site"]] = _load(fp)
    write_csvs(p, reports)
    sample_n = {x["site"]: bstats.sample_of(x)[0] for x in ok}
    thin = {x["site"] for x in ok if sample_n[x["site"]] is not None and sample_n[x["site"]] < bstats.THIN_N}
    A("## %s of the field is unreadable to AI crawlers\n" % share_words(int(round(100.0 * len(capped) / len(ok))), "en"))
    A("**%d of %d sites have a gate check at zero** — a crawler cannot get the content, so"
      % (len(capped), len(ok)))
    A("nothing else on the page matters. These are two very different problems, and reporting")
    A("them as one number is what makes such a number useless:\n")
    _r = {}
    for x in capped: _r.setdefault(x.get("gate_reason") or "other", []).append(x["site"])
    A("| Why | Sites | Which |"); A("|---|:-:|---|")
    note = crawler_note(p.get("tool"), "en")
    LBL = {"blocks crawlers": "**Deliberate** — `robots.txt` disallows retrieval crawlers" + (". " + note if note else ""),
           "serves crawlers an error": "**Deliberate or accidental** — " + REFUSED["en"],
           "content needs JavaScript": " ".join(x for x in (
               "**Accidental** — body copy only exists after JS runs.",
               thin_words(sum(1 for x in _r.get("content needs JavaScript", []) if x in thin), "en"),
               challenge_note(p.get("tool"), "en")) if x),
           "other": "Other"}
    for k in ("blocks crawlers", "serves crawlers an error", "content needs JavaScript", "other"):
        if k in _r:
            A("| %s | %d | %s |" % (LBL[k], len(_r[k]), ", ".join(sorted(_r[k]))))
    A("\nThe first group made a choice. Several news and health publishers block AI crawlers by")
    A("name, and this rubric reports that as it is — a site that does not want to be quoted is")
    A("not misconfigured. The last group almost certainly did not choose it: their content is")
    A("there, a browser can see it, and a retrieval crawler gets an empty shell.\n")
    A("## What the spread shows\n")
    A("**Half the field sits between %s and %s.** The rubric is not grading on a curve — these"
      % (s["p25"], s["p75"]))
    A("are the scores that fall out of it, and they are consistent with the public benchmarks")
    A("it was [calibrated against](../rubric/calibration-v1.1.md).\n")
    if cn and row:
        A(_china_block(u))
        drivers = _gap_drivers(ok)
        if drivers:
            A("Check by check, the largest differences are %s (average points behind, from the"
              % ", ".join("`%s` (%.1f)" % d for d in drivers[:4]))
            A("[per-site reports](raw/)).")
            caveat = _cjk_caveat([d[0] for d in drivers[:2]])
            A((caveat + "\n") if caveat else "")
        else:
            A("")
    A("**The same few things are missing almost everywhere.** Counting only each site's three")
    A("largest gaps:\n")
    A("| Missing | Sites | What it costs |"); A("|---|:-:|:-:|")
    RBP = {c["id"]: c["points"] for c in _rubric()["checks"]}
    for k, v in gap.most_common(6):
        A("| `%s` | %d of %d | %d pts |" % (k, v, len(ok), RBP.get(k, 0)))
    top3 = [k for k, _ in gap.most_common(3)]
    A("\nThe top three, %s, are worth %d points between them.\n"
      % (", ".join("`%s`" % k for k in top3), sum(RBP.get(k, 0) for k in top3)))
    A(_adoption_block(reports))
    A("## By sector\n")
    A("Each median carries a 95%% interval (bootstrap, [stats.py](stats.py)). A sector with fewer than %d"
      % u["min_n"])
    A("scored sites gets no median: the number would print like a real one and mean much less.\n")
    A("| Sector | Sites | Median | 95% CI |"); A("|---|:-:|:-:|:-:|")
    us = u["sectors"]
    for k, v in sorted(p["sectors"].items(), key=lambda kv: (us[kv[0]]["median"] is None, -kv[1]["median"])):
        if us[k]["median"] is None:
            A("| %s | %d | — | fewer than %d sites |" % (k, v["n"], u["min_n"]))
        else:
            A("| %s | %d | **%s** | %d–%d |" % (k, v["n"], v["median"], us[k]["ci"][0], us[k]["ci"][1]))
    A("\n## Every site\n")
    A("The same rows, flat: [results.csv](results.csv) has one row per listed site and one column per check,")
    A("[checks.csv](checks.csv) one row per scored site and check. The full reports are in [raw/](raw/).\n")
    A("| # | Site | Score | Band | Sector | Biggest gaps |")
    A("|:-:|---|:-:|---|---|---|")
    for i, r in enumerate([x for x in p["results"] if "error" not in x], 1):
        mark = (" *(thin sample: %d page%s)*" % (sample_n[r["site"]], "" if sample_n[r["site"]] == 1 else "s")
                if r["site"] in thin else "")
        A("| %d | %s%s | **%d** | %s | %s | %s |" % (i, r["site"], mark, r["normalised"], r["band"],
          r["sector"], " · ".join("`%s`" % g for g in r["top_gaps"])))
    errs = [r for r in p["results"] if "error" in r]
    if errs:
        A("\n### Not scored\n")
        why = {}
        for r in errs: why.setdefault(not_scored_reason(r["error"]), []).append(r)
        A("| Why | Sites |"); A("|---|:-:|")
        for k, label in NOT_SCORED:
            if k in why:
                A("| %s | %d |" % (label, len(why[k])))
        A("")
        for k, _ in NOT_SCORED:
            for r in why.get(k, []): A("- **%s** — %s" % (r["site"], r["error"]))
        A("\nA 403 to every client, a browser user-agent included, is bot protection working at the")
        A("TLS layer rather than on the user-agent string. It means a static fetch cannot observe")
        A("the site — not that the site blocks AI crawlers, which is a separate question this tool")
        A("cannot answer from outside.")
    A("\n## What this is not\n")
    A("These are **readiness** scores from a static fetch: whether an answer engine *can*")
    A("find, parse and cite the site. They do not measure whether one *does* — that depends")
    A("on competition and query intent, and no site-side audit can observe it.\n")
    A("Four checks worth 12 points need off-site search or human judgement and are left out")
    A("of the denominator, so these run a little lower than a full audit. The")
    A("[five reference audits](../examples/audits/v1.1/) score all 21 checks by hand.\n")
    A("Sites change. Every number here carries the date it was measured, and re-running")
    A("gives slightly different results — which is the point of publishing the tool alongside")
    A("the table.\n")
    A(_fetch_block())
    A(_corrections_block())
    io.open(os.path.join(HERE, "README.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

if __name__ == "__main__":
    main()
