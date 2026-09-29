#!/usr/bin/env python3
"""Offline tests for the benchmark scripts: retest.py on synthetic run directories, and the pieces of
build_page.py, stats.py and validity.py that turn committed data into published sentences.

    python3 benchmark/test_benchmark.py

No network. Synthetic runs are written to a temporary directory; nothing in the repository is modified.
"""
import contextlib, io, json, os, re, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_page  # noqa: E402
import retest      # noqa: E402
import run         # noqa: E402
import stats       # noqa: E402

CHECKS = [c["id"] for c in retest._rubric()["checks"] if c["kind"] != "bonus"]
BANDS = retest._rubric()["bands"]


def write_run(root, scores, capped=(), unobservable=(), tool="geo-score-cli/1.5.0", pinned_from=None):
    """A run directory as run.py --out writes one: results.json plus raw/<site>.json."""
    os.makedirs(os.path.join(root, "raw"))
    rows = []
    for site, score in sorted(scores.items()):
        cap = site in capped
        rows.append({"site": site, "sector": "Test", "normalised": score, "band": retest.band_of(score, BANDS),
                     "gate_capped": cap, "gate_reason": "blocks crawlers" if cap else None})
        checks = [{"id": cid, "state": "unobservable"} if (site, cid) in unobservable else
                  {"id": cid, "state": "scored", "points": 0 if (cap and cid == "g.robots") else 2}
                  for cid in CHECKS]
        with io.open(os.path.join(root, "raw", retest.raw_name(site)), "w", encoding="utf-8") as f:
            json.dump({"checks": checks}, f)
    with io.open(os.path.join(root, "results.json"), "w", encoding="utf-8") as f:
        json.dump({"tool": tool, "measured_at": "2026-10-01", "python": "3.12.0", "measured_from": "test bench",
                   "pinned_from": pinned_from, "results": rows}, f)
    return root


@contextlib.contextmanager
def fake_web(fetch):
    """The CLI fetches through `fetch` and never the network, and run.one writes its raw report to a temporary
    directory instead of benchmark/raw/."""
    gs = run.gs
    saved = gs.fetch, getattr(gs, "preflight_host", None), run.time.sleep, run.RAW
    tmp = tempfile.mkdtemp()
    gs.fetch, run.time.sleep, run.RAW = fetch, (lambda s: None), os.path.join(tmp, "raw")
    if saved[1]:
        gs.preflight_host = lambda *a, **k: None          # the test hosts have no DNS; fetch never leaves the process
    try:
        yield
    finally:
        gs.fetch, run.time.sleep, run.RAW = saved[0], saved[2], saved[3]
        if saved[1]:
            gs.preflight_host = saved[1]
        shutil.rmtree(tmp)


def cli_predates(fix):
    """The CLI's version when it is older than `fix`, the release a published sentence says has a fix, else None."""
    return build_page.old_crawler_reading(run.gs.__version__, fix)


def study(dirs, labels):
    runs, recs = [], {}
    for d, lb in zip(dirs, labels):
        meta, rr = retest.load_run(d, lb, CHECKS)
        runs.append(meta); recs[lb] = rr
    st = {"checks": CHECKS, "record_fields": retest.RECORD_FIELDS, "runs": runs, "records": recs}
    st["analysis"] = retest.analyse_study(st, BANDS)
    return st


class Retest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.scores = {"site%02d.test" % i: 30 + 3 * i for i in range(20)}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_identical_runs_agree_perfectly(self):
        a = write_run(os.path.join(self.tmp, "a"), self.scores)
        b = write_run(os.path.join(self.tmp, "b"), self.scores)
        p = study([a, b], ["A", "B"])["analysis"]["pairs"][0]
        self.assertEqual(p["icc_a1"], 1.0)
        self.assertEqual(p["sem"], 0.0)
        self.assertEqual((p["identical_pct"], p["within_2_pct"], p["within_5_pct"]), (100.0, 100.0, 100.0))
        self.assertEqual((p["band_changes"], p["gate_flips"], p["moved_over_5"]), (0, [], []))
        self.assertTrue(all(f["flips"] == 0 for f in p["tier_flips"].values()))

    def test_planted_shift_is_reported(self):
        shifted = sorted(self.scores)[::2]                     # half the sites, +10
        a = write_run(os.path.join(self.tmp, "a"), self.scores)
        b = write_run(os.path.join(self.tmp, "b"), {s: v + (10 if s in shifted else 0) for s, v in self.scores.items()})
        p = study([a, b], ["A", "B"])["analysis"]["pairs"][0]
        self.assertEqual(p["within_5_pct"], 50.0)
        self.assertEqual(p["identical"], 10)
        self.assertEqual(p["mean_difference"], 5.0)
        self.assertEqual(sorted(s for s, _, _ in p["moved_over_5"]), shifted)
        self.assertTrue(all(y - x == 10 for _, x, y in p["moved_over_5"]))
        self.assertLess(p["icc_a1"], 1.0)
        self.assertGreater(p["sem"], 0.0)
        self.assertGreater(p["band_changes"], 0)

    def test_gate_flips_tier_flips_and_unobservable_rates(self):
        site = sorted(self.scores)[0]
        a = write_run(os.path.join(self.tmp, "a"), self.scores)
        b = write_run(os.path.join(self.tmp, "b"), self.scores, capped={site},
                      unobservable={(site, "p3.knowledge-graph")})
        st = study([a, b], ["A", "B"])
        p = st["analysis"]["pairs"][0]
        self.assertEqual(p["gate_flips"], [[site, "not capped", "capped — blocks crawlers"]])
        self.assertEqual(p["tier_flips"]["g.robots"]["matrix"], {"2→0": 1, "2→2": 19})
        self.assertEqual(p["tier_flips"]["p3.knowledge-graph"]["matrix"], {"2→2": 19, "2→unobservable": 1})
        self.assertEqual(st["analysis"]["unobservable"]["p3.knowledge-graph"], {"A": 0.0, "B": 5.0})

    def test_three_runs_and_a_pinned_run_named_by_its_label(self):
        dirs = [write_run(os.path.join(self.tmp, x), self.scores) for x in "abc"]
        res = json.loads(retest._read(os.path.join(dirs[2], "results.json")))
        res["pinned_from"] = run.pin_source(os.path.join(dirs[0], "raw"), dirs[2])      # "../a/raw", as run.py writes it
        with io.open(os.path.join(dirs[2], "results.json"), "w", encoding="utf-8") as f:
            json.dump(res, f)
        doc = json.loads(retest._read(retest.OUT_JSON))
        saved = (retest.OUT_JSON, retest.OUT_MD)
        out_json, out_md = os.path.join(self.tmp, "r.json"), os.path.join(self.tmp, "R.md")
        shutil.copy(retest.OUT_MD, out_md)
        retest._write(out_json, json.dumps(doc))
        retest.OUT_JSON, retest.OUT_MD = out_json, out_md
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(retest.main(dirs), 0)
            self.assertEqual(retest.main(["--check"]), 0)       # the written files are what the records give
            got = json.loads(retest._read(out_json))
            md = retest._read(out_md)
        finally:
            retest.OUT_JSON, retest.OUT_MD = saved
        self.assertEqual([(p["a"], p["b"]) for p in got["study"]["analysis"]["pairs"]],
                         [("A", "B"), ("A", "C"), ("B", "C")])
        self.assertEqual(got["study"]["runs"][2]["pinned_from"], "A")
        self.assertIn("pinned to A's pages", md)
        self.assertEqual(got["study"]["analysis"]["all_runs"]["icc_a1"], 1.0)
        self.assertEqual(got["legacy"]["analysis"]["compared"], 229)

    def test_a_pin_names_a_run_and_never_a_path(self):
        dirs = [os.path.join(self.tmp, x) for x in "abc"]
        runs = [{"label": "A", "pinned_from": None},
                {"label": "B", "pinned_from": os.path.join(dirs[0], "raw")},
                {"label": "C", "pinned_from": "/Users/operator/geo-runs/old/raw"}]
        retest.name_pins(runs, dirs)
        self.assertEqual([r["pinned_from"] for r in runs], [None, "A", retest.OUTSIDE])
        self.assertEqual(run.pin_source(os.path.join(dirs[0], "raw"), dirs[1]), "../a/raw")
        self.assertEqual(run.pin_source(os.path.join(HERE, "raw"), HERE), "raw")
        self.assertIsNone(run.pin_source(None, HERE))

    def test_legacy_runs_reproduce_their_published_counts(self):
        doc = retest.derive(json.loads(retest._read(retest.OUT_JSON)))
        la = doc["legacy"]["analysis"]
        self.assertEqual((la["compared"], la["identical"], la["within_2"], la["within_5"]), (229, 103, 179, 219))
        self.assertEqual(la["within_5_pct"], 95.6)
        self.assertEqual(retest.headline(doc)["legacy"], doc.get("study") is None)

    def test_icc_matches_a_worked_example(self):
        # Shrout & Fleiss (1979) table: 6 targets, 4 judges; ICC(2,1) = ICC(A,1) = 0.29
        rows = [[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6], [10, 5, 6, 9], [6, 2, 4, 7]]
        self.assertAlmostEqual(retest.icc_a1(rows), 0.29, places=2)


class Labels(unittest.TestCase):
    def test_crawler_qualifier_only_for_data_older_than_the_fix(self):
        for tool in ("geo-score-cli/1.3.0", "geo-score-cli/1.4.0"):
            self.assertIn("GPTBot, ClaudeBot and Google-Extended", build_page.crawler_note(tool, "en"))
            self.assertIn("GPTBot", build_page.crawler_note(tool, "zh"))
        for tool in ("geo-score-cli/1.5.0", "geo-score-cli/1.10.0", "geo-score-cli/2.0.0", None, ""):
            self.assertEqual(build_page.crawler_note(tool, "en"), "")

    def test_canonical_urls_and_both_chinese_forms(self):
        self.assertEqual(build_page.PAGE["zh"], build_page.PAGE["en"] + build_page.ZH_PATH)
        saved = (build_page.SITE, build_page.PAGE)
        build_page.SITE = "https://example.org/lb"
        build_page.PAGE = {"en": build_page.SITE, "zh": build_page.SITE + build_page.ZH_PATH}
        try:
            d = build_page.DEFAULT_SITE
            self.assertEqual(build_page._hosted(d + "/zh.html " + d + "/zh " + d + "/og.png " + d),
                             "https://example.org/lb/zh https://example.org/lb/zh https://example.org/lb/og.png "
                             "https://example.org/lb")
        finally:
            build_page.SITE, build_page.PAGE = saved


class Stats(unittest.TestCase):
    def test_gap_is_suppressed_below_min_n(self):
        import random
        rng = random.Random(1)
        few, many = list(range(stats.MIN_N - 1)), list(range(40))
        g = stats._gap(few, many, rng, "few", "many")
        self.assertEqual((g["gap"], g["ci"], g["n_group"]), (None, None, stats.MIN_N - 1))
        g = stats._gap(list(range(10, 10 + stats.MIN_N)), many, rng, "a", "b")
        self.assertIsNotNone(g["gap"])

    def test_china_detail_adds_up(self):
        res = json.loads(retest._read(os.path.join(HERE, "results.json")))
        ok = [r for r in res["results"] if r.get("normalised") is not None]
        import random
        d = stats.china_detail(ok, random.Random(stats.SEED))
        x = d["crosstab"]
        self.assertEqual(x["china"]["zh"] + x["china"]["other"] + x["rest"]["zh"] + x["rest"]["other"], len(ok))
        m = d["by_method"]
        self.assertAlmostEqual(m["rule"] + m["heuristic"], m["total"], delta=0.11)
        kg = d["knowledge_graph"]["by_language"]
        self.assertEqual(kg["zh"]["n"] + kg["other"]["n"], len(ok))


class Sample(unittest.TestCase):
    def test_sample_size_comes_from_the_row_else_raw(self):
        self.assertEqual(stats.sample_of({"site": "x.test", "sample_n": 3, "sample_source": "sitemap"}), (3, "sitemap"))
        tmp = tempfile.mkdtemp()
        try:
            with io.open(os.path.join(tmp, "x.test.json"), "w", encoding="utf-8") as f:
                json.dump({"sampled_urls": ["https://x.test/"], "sample_source": "pinned"}, f)
            self.assertEqual(stats.sample_of({"site": "x.test"}, tmp), (1, "pinned"))
            self.assertEqual(stats.sample_of({"site": "y.test"}, tmp), (None, None))
        finally:
            shutil.rmtree(tmp)

    def test_thin_rows_leave_the_second_median(self):
        ok = [{"site": "s%d.test" % i, "normalised": 10 * i, "sample_n": 1 if i < 3 else 8} for i in range(12)]
        t = stats.thin_sample(ok)
        self.assertEqual((t["n_thin"], t["n_single_page"], t["with_thin"]["n"], t["without_thin"]["n"]), (3, 3, 12, 9))
        self.assertEqual(t["without_thin"]["median"], 70)
        self.assertIsNone(stats.thin_sample(ok + [{"site": "nowhere.test", "normalised": 5}]))

    def test_the_committed_counts(self):
        res = json.loads(retest._read(os.path.join(HERE, "results.json")))
        ok = [r for r in res["results"] if r.get("normalised") is not None]
        n = [stats.sample_of(r)[0] for r in ok]
        t = stats.thin_sample(ok)
        self.assertEqual(t["n_thin"], sum(1 for k in n if k < stats.THIN_N))
        self.assertEqual(t["n_single_page"], n.count(1))


class NotScored(unittest.TestCase):
    def test_reasons(self):
        self.assertEqual(run.not_scored_reason(run.BOT_CHALLENGE + " (AWS WAF): a static fetch cannot measure this site"),
                         "bot challenge")
        self.assertEqual(run.not_scored_reason("could not fetch https://x.test — all requests returned 403"), "refused")
        self.assertEqual(run.not_scored_reason("could not fetch https://x.test — The read operation timed out"), "timed out")
        self.assertEqual(run.not_scored_reason("could not fetch https://x.test — <urlopen error EOF occurred in "
                                               "violation of protocol (_ssl.c:1129)>"), "connection failed")
        self.assertEqual({k for k, _ in run.NOT_SCORED} >= {"bot challenge", "refused", "timed out", "other"}, True)

    def test_a_bot_challenge_on_the_bare_host_is_what_the_row_keeps(self):
        calls = []

        def fake_run(url, sample, **kw):
            calls.append(url)
            if url == "https://x.test":
                raise RuntimeError(run.BOT_CHALLENGE + " (Akamai): a static fetch cannot measure this site")
            raise RuntimeError("could not fetch %s — all requests returned 403" % url)
        saved = (run.gs.run, run.time.sleep)
        run.gs.run, run.time.sleep = fake_run, lambda s: None
        try:
            row = run.one({"url": "x.test", "sector": "Test"})
        finally:
            run.gs.run, run.time.sleep = saved
        self.assertEqual(calls, ["https://x.test", "https://www.x.test"])
        self.assertEqual(run.not_scored_reason(row["error"]), "bot challenge")

    def test_the_cli_error_carries_the_prefix_run_py_matches(self):
        """The string contract with the CLI, and the claim the published qualifier makes: a site that serves every
        page as an AWS WAF challenge (202 with a challenge body) is not scored, and its row files under "bot
        challenge". Skipped while the CLI is older than build_page.CHALLENGE_FIX and still scores such a site; from
        that version on, a CLI that scores it, or words its error differently, fails here."""
        gs = run.gs
        page = (b'<html><head><title>Human Verification</title><script>window.awsWafCookieDomainList = [];'
                b'window.gokuProps = {};</script><script src="https://x.token.awswaf.com/challenge.js"></script>'
                b'</head><body><div id="challenge-container"></div><script>AwsWafIntegration.checkForceRefresh()'
                b'.then(function () {}).catch(reportChallengeError);</script></body></html>')

        def fake_fetch(url, ua=gs.UA_BROWSER, *a, **kw):
            if run.urllib.parse.urlsplit(url).path.endswith((".txt", ".xml")):
                return gs.Resp(url, 404, b"", {})
            return gs.Resp(url, 202, page, {"content-type": "text/html; charset=utf-8"})
        with fake_web(fake_fetch):
            row = run.one({"url": "challenge.test", "sector": "Test"})
        fix = build_page._v(build_page.CHALLENGE_FIX)
        if "error" not in row:
            older = cli_predates(build_page.CHALLENGE_FIX)
            if older:
                self.skipTest("the %s CLI still scores a challenge page (%d/100, %s); the qualifier dates the fix to %s"
                              % (older, row["normalised"], row["gate_reason"], fix))
            self.fail("the published qualifier says %s tells a bot-challenge page apart, and the %s CLI scored one: "
                      "%d/100, %s" % (fix, gs.__version__, row["normalised"], row["gate_reason"]))
        self.assertEqual(run.not_scored_reason(row["error"]), "bot challenge",
                         "the CLI's error no longer starts with %r: %s" % (run.BOT_CHALLENGE, row["error"]))

    def test_a_pinned_report_without_pages_is_a_row_not_a_crash(self):
        tmp = tempfile.mkdtemp()
        saved = run.PIN_DIR
        try:
            for site, urls in (("x.test", []), ("y.test", ["/relative/page"])):
                with io.open(os.path.join(tmp, run.raw_name(site)), "w", encoding="utf-8") as f:
                    json.dump({"sampled_urls": urls}, f)
            run.PIN_DIR = tmp
            rows = [run.one({"url": s, "sector": "Test"}) for s in ("x.test", "y.test", "z.test")]
        finally:
            run.PIN_DIR = saved
            shutil.rmtree(tmp)
        self.assertEqual([r["error"].split(":")[0] for r in rows], ["not pinned"] * 3)
        self.assertIn("lists no page to re-read", rows[0]["error"])

    def test_challenge_qualifier_only_for_data_older_than_the_fix(self):
        self.assertIn("bot-challenge page", build_page.challenge_note("geo-score-cli/1.3.0", "en"))
        self.assertIn("人机验证", build_page.challenge_note("geo-score-cli/1.4.0", "zh"))
        for tool in ("geo-score-cli/1.5.0", "geo-score-cli/2.0.0", None):
            self.assertEqual(build_page.challenge_note(tool, "en"), "")


class ChineseLexicon(unittest.TestCase):
    """rubric/v1.1.json's note on p2.question-intent says which release adds the Chinese task and explanation
    headings to the CLI's lexicon. From that release on, a Chinese site whose headings take only those forms earns
    the check's points; before it, the test is skipped."""
    HOST = "zh-headings.test"
    NOTE = re.compile(r"(\d+)\.(\d+)\.(\d+) adds those forms")

    def points(self, heading):
        """p2.question-intent's points for a Chinese site whose every sampled page has this one heading."""
        gs = run.gs
        text = "这是一个用来测试标题意图的中文段落，内容足够长，读起来也像正文。" * 6
        body = ('<html lang="zh-CN"><head><title>标题测试</title></head><body><main><h2>%s</h2><p>%s</p></main>'
                "</body></html>" % (heading, text)).encode("utf-8")

        def fake_fetch(url, ua=gs.UA_BROWSER, *a, **kw):
            u = run.urllib.parse.urlsplit(url)
            if u.netloc != self.HOST or u.path.endswith((".txt", ".xml")):
                return gs.Resp(url, 404, b"", {})
            return gs.Resp(url, 200, body, {"content-type": "text/html; charset=utf-8"})
        urls = ["https://%s/docs/page-%d" % (self.HOST, i) for i in range(run.SAMPLE)]
        with fake_web(fake_fetch):
            res = gs.run("https://" + self.HOST, run.SAMPLE, urls=urls)
        return next(r[3] for r in gs.score(res)[0] if r[0] == "p2.question-intent")

    def test_task_and_explanation_headings_count(self):
        note = next(c for c in retest._rubric()["checks"] if c["id"] == "p2.question-intent")["evidence"]["note"]
        m = self.NOTE.search(note)
        self.assertIsNotNone(m, "the p2.question-intent note no longer says which release adds the Chinese forms")
        fix = tuple(int(x) for x in m.groups())
        # the harness on every CLI: a question heading earns the points, a keyword string does not
        self.assertEqual(self.points("如何创建第一个应用"), 7)
        self.assertEqual(self.points("企业级云服务器"), 0)
        # the note's own examples, 'create your first app' and 'how workflows work', with no question word
        missed = [h for h in ("创建你的第一个应用", "工作流的工作原理") if self.points(h) != 7]
        older = cli_predates(fix)
        if missed and older:
            self.skipTest("the %s CLI does not count %s yet; rubric/v1.1.json dates that to %s"
                          % (older, "、".join(missed), m.group(0).split()[0]))
        self.assertEqual(missed, [], "rubric/v1.1.json says %s, and the %s CLI does not count these headings"
                         % (m.group(0), run.gs.__version__))


class FetchBudget(unittest.TestCase):
    """The README's per-site request budget against what the CLI actually sends, on a synthetic site built to
    take every branch that fetches: a sitemap index, section indexes, Chinese text, an Organization with a logo
    and more sameAs profiles than are checked, and brand names no knowledge base matches."""
    HOST = "budget.test"

    def site(self, url, ua):
        gs = run.gs
        u = run.urllib.parse.urlsplit(url)
        root = "https://" + self.HOST
        if u.netloc == "www.wikidata.org":
            return gs.Resp(url, 200, b'{"search": []}', {"content-type": "application/json"})
        if u.netloc.endswith("wikipedia.org"):
            return gs.Resp(url, 200, b'{"query": {"search": []}}', {"content-type": "application/json"})
        if u.netloc != self.HOST or u.path in ("/logo.png",):
            return gs.Resp(url, 200, b"ok", {"content-type": "text/plain"})
        if u.path == "/robots.txt":
            body = "User-agent: *\nAllow: /\n" + "".join("Sitemap: %s/sm-%d.xml\n" % (root, i) for i in range(5))
            return gs.Resp(url, 200, body.encode(), {"content-type": "text/plain"})
        if u.path == "/sm-0.xml":
            kids = "".join("<sitemap><loc>%s/child-%d.xml</loc></sitemap>" % (root, i) for i in range(3))
            return gs.Resp(url, 200, ("<sitemapindex>%s</sitemapindex>" % kids).encode(), {"content-type": "text/xml"})
        if u.path.endswith(".xml"):
            locs = "".join("<url><loc>%s/blog/2026/09/post-%d</loc><lastmod>2026-09-01</lastmod></url>" % (root, i)
                           for i in range(40))
            return gs.Resp(url, 200, ("<urlset>%s</urlset>" % locs).encode(), {"content-type": "text/xml"})
        if u.path.endswith(".txt"):
            return gs.Resp(url, 404, b"", {})
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "Organization", "name": "Budget Org", "legalName": "Budget Legal Name", "url": root,
             "logo": root + "/logo.png", "sameAs": ["https://profiles.test/p%d" % i for i in range(12)]},
            {"@type": "WebSite", "name": "Budget", "url": root}]}
        links = "".join('<a href="/%s/a/b/page-%d">x</a>' % (d, i) for d in ("blog", "docs", "product") for i in range(6))
        body = ("<html><head><title>Budget Title | Budget Tagline</title>"
                '<meta property="og:site_name" content="Budget Site Name">'
                '<script type="application/ld+json">%s</script></head><body><main><h2>一</h2><p>%s</p>%s</main>'
                "</body></html>" % (json.dumps(ld), "这是一个用来测试请求预算的中文页面。" * 30, links))
        return gs.Resp(url, 200, body.encode("utf-8"), {"content-type": "text/html; charset=utf-8"})

    def test_budget_rows_hold_what_the_cli_sends(self):
        gs, sent = run.gs, []
        retrieval = {ua for _, ua in gs.RETRIEVAL_UAS}
        chinese = {ua for _, ua in gs.CN_UAS}
        sections = ("/blog", "/news", "/posts", "/articles", "/insights", "/resources", "/docs", "/learn")

        def fake_fetch(url, ua=gs.UA_BROWSER, *a, **kw):
            sent.append((url, ua))
            return self.site(url, ua)
        saved = gs.fetch, getattr(gs, "preflight_host", None)
        gs.fetch = fake_fetch
        if saved[1]:
            gs.preflight_host = lambda *a, **k: None          # budget.test has no DNS; fetch never leaves the process
        try:
            res = gs.run("https://" + self.HOST, run.SAMPLE)
        finally:
            gs.fetch = saved[0]
            if saved[1]:
                gs.preflight_host = saved[1]
        got = dict.fromkeys(["home_robots", "sitemaps", "sections", "sampled", "retrieval", "cn", "text_files",
                             "logo", "sameas", "kg"], 0)
        for url, ua in sent:
            u = run.urllib.parse.urlsplit(url)
            if u.netloc == "www.wikidata.org" or u.netloc.endswith("wikipedia.org"):
                got["kg"] += 1
            elif u.netloc != self.HOST:
                got["sameas"] += 1
            elif ua in retrieval:
                got["retrieval"] += 1
            elif ua in chinese:
                got["cn"] += 1
            elif u.path in ("", "/", "/robots.txt"):
                got["home_robots"] += 1
            elif u.path.endswith(".xml"):
                got["sitemaps"] += 1
            elif u.path in sections:
                got["sections"] += 1
            elif u.path.endswith(".txt"):
                got["text_files"] += 1
            elif u.path == "/logo.png":
                got["logo"] += 1
            else:
                got["sampled"] += 1
        self.assertEqual(len(res["urls"]), run.SAMPLE)
        site, elsewhere = run.fetch_budget()
        want = {k: n for k, _, n, *_ in site + elsewhere}
        # the homepage is read in discovery and again as sampled page one (a run that remembers it reads it once)
        got["home_robots"], got["sampled"] = got["home_robots"] - 1, got["sampled"] + 1
        for k, n in want.items():
            self.assertLessEqual(got[k], n, "%s: the CLI sent %d, the README budget says at most %d (all: %s)"
                                 % (k, got[k], n, got))
        # every other sampled page is its own request, and the crawler rows are the CLI's own lists, reached in full
        self.assertEqual(got["sampled"], run.SAMPLE)
        self.assertEqual((got["retrieval"], want["retrieval"]), (len(gs.RETRIEVAL_UAS) * run.PROBE_PAGES,) * 2)
        self.assertEqual((got["cn"], want["cn"]), (len(gs.CN_UAS),) * 2)
        self.assertLessEqual(len(sent), sum(want.values()))

    def test_readme_quotes_the_budget(self):
        site, elsewhere = run.fetch_budget()
        block = " ".join(run._fetch_block().split())
        self.assertIn("at most **%d requests to the site** and **%d elsewhere**"
                      % (sum(x[2] for x in site), sum(x[2] for x in elsewhere)), block)
        readme = " ".join(retest._read(os.path.join(HERE, "README.md")).split())
        self.assertIn(block.strip(), readme)
        self.assertIn(run.CORRECTION_FORM, readme)


class Csv(unittest.TestCase):
    def test_flat_files(self):
        import csv
        ids = [c["id"] for c in retest._rubric()["checks"]]
        p = {"tool": "geo-score-cli/1.5.0", "measured_at": "2026-10-01", "results": [
            {"site": "b.test", "sector": "Test", "tool_version": "1.5.0", "normalised": 40, "readiness": 30,
             "observable_max": 60, "band": "Early", "gate_capped": True, "gate_reason": "blocks crawlers",
             "resolved_to": None},
            {"site": "a.test", "sector": "Test", "error": run.BOT_CHALLENGE + " (Cloudflare): a static fetch cannot "
                                                          "measure this site"}]}
        checks = [{"id": c, "state": "unobservable"} if c == "p3.listings" else
                  {"id": c, "state": "scored", "points": 1, "max": 2} for c in ids]
        reports = {"b.test": {"audited_at": "2026-10-02", "sampled_urls": ["https://b.test/"], "sample_source": "pinned",
                              "checks": checks}}
        tmp = tempfile.mkdtemp()
        try:
            run.write_csvs(p, reports, tmp)
            with io.open(os.path.join(tmp, "results.csv"), encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            with io.open(os.path.join(tmp, "checks.csv"), encoding="utf-8", newline="") as f:
                long = list(csv.reader(f))
        finally:
            shutil.rmtree(tmp)
        self.assertEqual([r["site"] for r in rows], ["a.test", "b.test"])
        a, b = rows
        self.assertEqual((a["not_scored_reason"], a["normalised"], a["tool_version"], a["p1.llms-txt"]),
                         ("bot challenge", "", "1.5.0", ""))
        self.assertEqual((b["gate_capped"], b["resolved_to"], b["sample_n"], b["measured_at"], b["p3.listings"],
                          b["p1.llms-txt"]), ("true", "", "1", "2026-10-02", "", "1"))
        self.assertEqual(long[0], run.CHECK_COLUMNS)
        self.assertEqual(len(long), 1 + len(ids))
        self.assertIn(["b.test", "p3.listings", "unobservable", "", ""], long)

    def test_byline_share_reads_the_evidence(self):
        self.assertTrue(run._half_bylined("4 of 8 pages carry a personal byline; 0 link that name"))
        self.assertFalse(run._half_bylined("3 of 8 pages carry a personal byline; 0 link that name"))
        self.assertIsNone(run._half_bylined("something else"))


class Sensitivity(unittest.TestCase):
    def test_ranks_share_ties(self):
        import sensitivity
        self.assertEqual(sensitivity.ranks([10, 20, 20, 5]), [3.0, 1.5, 1.5, 4.0])

    def test_rubric_arithmetic(self):
        import sensitivity
        rub = retest._rubric()
        full = {c["id"]: c["points"] for c in rub["checks"]}
        site = {"points": dict(full)}
        capped = {"points": dict(full, **{"g.ssr": 0})}
        half = {"points": {c: (None if c.startswith("p4.") else (p if c.startswith("b.") else 0)) for c, p in full.items()}}
        got = sensitivity.scorer(rub, [site, capped, half])({c["id"]: c["points"] for c in rub["checks"] if c["kind"] != "bonus"})
        # full marks plus a bonus stay at 100; a gate at zero caps at 40; the bonus counts at most bonus_cap
        den = sum(c["points"] for c in rub["checks"] if c["kind"] != "bonus" and not c["id"].startswith("p4."))
        self.assertEqual(got, [100, rub["gate_cap"], min(rub["gate_cap"], round(100.0 * rub["bonus_cap"] / den))])

    def test_published_weights_reproduce_the_leaderboard(self):
        import sensitivity
        rub, res, sites = sensitivity.load()
        pts = {c["id"]: c["points"] for c in rub["checks"] if c["kind"] != "bonus"}
        base = sensitivity.scorer(rub, sites)(pts)
        self.assertEqual(base, [s["normalised"] for s in sites])
        same = sensitivity.compare(base, list(base), [s["site"] for s in sites], rub)
        self.assertEqual((same["spearman"], same["band_changes"], same["median_rank_move"], same["top20_overlap"]),
                         (1.0, 0, 0, 20))

    def test_the_study_does_not_depend_on_how_python_adds_floats(self):
        """From Python 3.12 the builtin sum() compensates float additions, and on this data that moved two sites
        across a band edge under the evidence-basis weighting, so the committed files depended on the Python that
        wrote them. The study has to come out the same with a plain left fold (sum() before 3.12) and with a
        correctly rounded sum."""
        import math
        import sensitivity
        rub, res, sites = sensitivity.load()

        def plain(xs, start=0):
            for x in xs:
                start = start + x
            return start

        def rounded(xs, start=0):
            xs = list(xs)
            return start + math.fsum(xs) if any(isinstance(x, float) for x in xs) else plain(xs, start)
        out = []
        for add in (plain, rounded):
            sensitivity.sum = add          # a module global shadows the builtin inside sensitivity.py
            try:
                out.append(sensitivity.analyse(rub, res, sites))
            finally:
                del sensitivity.sum
        self.assertEqual(out[0], out[1])


class SameOnEveryPython(unittest.TestCase):
    def test_the_study_files_on_the_oldest_and_newest_python(self):
        """check.sh runs this file on python3 alone. The generated study files have to come out byte for byte on
        the oldest and the newest Python the gate tests the CLI on too, found by uv as check.sh finds them."""
        import subprocess
        if not shutil.which("uv"):
            self.skipTest("uv not installed: the study files were checked on this Python only")
        gate = retest._read(os.path.join(HERE, "..", "scripts", "check.sh"))
        ran = []
        for v in (re.search(r"^%s=(\S+)" % k, gate, re.M).group(1) for k in ("PY_OLDEST", "PY_NEWEST")):
            py = subprocess.run(["uv", "python", "find", "--no-project", v], capture_output=True,
                                universal_newlines=True).stdout.strip()
            if not py:
                continue
            for script in ("sensitivity.py", "percentiles.py", "retest.py"):
                r = subprocess.run([py, os.path.join(HERE, script), "--check"], capture_output=True,
                                   universal_newlines=True)
                self.assertEqual(r.returncode, 0, "python %s: benchmark/%s --check: %s" % (v, script, r.stderr.strip()))
            ran.append(v)
        if not ran:
            self.skipTest("uv finds neither the oldest nor the newest Python the gate names")


class Percentiles(unittest.TestCase):
    def test_ranks_cuts_and_rounding(self):
        import percentiles
        xs = [10, 20, 20, 30, 40]
        self.assertEqual([percentiles.pct_rank(xs, s) for s in (5, 10, 20, 40, 50)], [0.0, 10.0, 40.0, 90.0, 100.0])
        self.assertEqual(percentiles.cut_for(xs, 40), 30)       # 30 and 40: two of five sites
        self.assertEqual(percentiles.cut_for(xs, 100), 10)
        self.assertEqual(percentiles.share(271, 317), "85%")    # 85.49, never 86 by way of a rounded 85.5

    def test_committed_shares(self):
        import percentiles
        d = percentiles.compute()
        o = d["overall"]
        self.assertEqual([percentiles.share(o["at_or_above"][c]["n"], o["n"]) for c in sorted(d["cuts"], key=int)],
                         ["85%", "58%", "34%", "10%"])
        self.assertEqual(d["candidates"]["v1.1"]["cuts"], [31, 51, 66, 83])
        self.assertEqual(d["gate_cap"]["capped"], sum(d["gate_cap"]["capped_by_band_before_cap"].values()))


class Validity(unittest.TestCase):
    def test_common_checks_arithmetic(self):
        import validity
        sites = [{"common_checks_human_pct": h, "common_checks_cli_pct": c}
                 for h, c in ((67, 70), (67, 64), (81, 76), (74, 83), (72, 66))]
        cc = validity.common_checks(sites)
        self.assertEqual((cc["mean"], cc["min"], cc["max"], cc["mean_abs"]), (-0.4, -6, 9, 5.2))
        self.assertEqual(cc["bland_altman"]["label"], "n=5")
        self.assertEqual(cc["bland_altman"]["loa_95"], [-12.8, 12.0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
