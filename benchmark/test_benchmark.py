#!/usr/bin/env python3
"""Offline tests for the benchmark scripts: retest.py on synthetic run directories, and the pieces of
build_page.py, stats.py and validity.py that turn committed data into published sentences.

    python3 benchmark/test_benchmark.py

No network. Synthetic runs are written to a temporary directory; nothing in the repository is modified.
"""
import contextlib, io, json, os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_page  # noqa: E402
import retest      # noqa: E402
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
        res["pinned_from"] = os.path.join(dirs[0], "raw")
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
