#!/usr/bin/env python3
"""Offline tests for analysis.py on synthetic rounds: one with a known association between readiness and citation,
which the analysis must recover, and one with none, which it must not call.

    python3 benchmark/prereg/test_analysis.py

Synthetic sample, watch run files and CLI reports are written to a temporary directory in the shapes draw.py,
`watch run` and `geo_score.py --json-out` write them. No network; nothing in the repository is modified.
"""
import io, json, math, os, random, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analysis as an  # noqa: E402

GW = an.GW
PERMS = BOOTS = 2000
QUESTIONS, RUNS = 10, 4
BASE_X = (34, 46, 57, 72, 84)            # two low, one mid, two high: the strata draw.py would give


def site_entry(cid, i, x, ordinary=False):
    name = "Site%s%d" % (cid.upper(), i)
    return {"id": "%s-%d.example" % (cid, i), "site": "%s-%d.example" % (cid, i), "name": name,
            "domains": ["%s-%d.example" % (cid, i)], "aliases": [], "url_prefixes": [], "ordinary_word": ordinary,
            "stratum": an.stratum_of(x), "sampling_score": x, "tranco_rank": None}


def answer_for(sites, cited_ids, with_spans):
    """An answer naming and citing the sites in cited_ids, one sentence each, a [n] marker closing each sentence, and
    one third-party source; with_spans gives the markers' places as watch saves them."""
    text, spans, cites = "", [], [{"url": "https://reviews.example/best", "domain": "reviews.example", "title": "x"}]
    for s in sites:
        if s["id"] not in cited_ids:
            continue
        url = "https://%s/product" % s["domains"][0]
        sentence = "%s is a sound choice for most buyers. " % s["name"]
        start = len(text) + len(sentence) - 1
        text += sentence[:-1] + "[%d] " % (len(cites))
        spans.append({"start": start, "end": start + len("[%d]" % len(cites)), "urls": [url], "kind": "marker"})
        cites.append({"url": url, "domain": s["domains"][0], "title": s["name"]})
    text += "Compare prices before you buy.[0]"
    spans.append({"start": len(text) - 3, "end": len(text), "urls": ["https://reviews.example/best"], "kind": "marker"})
    return text, (spans if with_spans else None), cites


def write_round(root, effect, seed=7, n_cats=14, stop_and_rerun=True, extra_silent_engine=False):
    """A round directory: sample.json, runs/wave0/<category>/*.json, readiness/wave0/run{1,2}/<site>.json."""
    rng = random.Random(seed)
    cats = []
    for k in range(n_cats):
        cid = "c%02d" % k
        xs = [x + rng.randint(-2, 2) for x in BASE_X]
        sites = [site_entry(cid, i, x, ordinary=(k == 0 and i == 2)) for i, x in enumerate(xs)]
        for s in sites:
            s["tranco_rank"] = rng.choice([None, rng.randint(1000, 900000)])
        cats.append({"id": cid, "sites": sites})
    with io.open(os.path.join(root, "sample.json"), "w", encoding="utf-8") as f:
        json.dump({"format": "geo-score/prereg-round0-sample.v1", "categories": cats}, f)
    for c in cats:
        sites = sorted(c["sites"], key=lambda s: s["name"])
        order = sorted(range(len(sites)), key=lambda i: sites[i]["sampling_score"])
        if effect:          # the citation probability rises with the site's readiness rank in its category
            prob = {sites[i]["id"]: 0.05 + 0.15 * r for r, i in enumerate(order)}
        else:               # unrelated to readiness
            prob = {s["id"]: rng.uniform(0.05, 0.65) for s in sites}
        brand, rivals = sites[0], sites[1:]
        engines = ["openai", "gemini"] + (["silent"] if extra_silent_engine else [])
        files = [("20261020T010000Z", engines, {})]
        if stop_and_rerun and c["id"] == "c01":
            files = [("20261020T010000Z", engines, {"gemini": "engine_failed"}),
                     ("20261020T050000Z", ["gemini"], {})]
        for rid, engs, stopped in files:
            samples = []
            for e in engs:
                for q in range(1, QUESTIONS + 1):
                    for run in range(1, RUNS + 1):
                        base = {"query_id": "q%02d" % q, "engine": e, "run": run}
                        if stopped.get(e) and q > 3:
                            samples.append(dict(base, status="skipped", skip_reason="engine_failed"))
                            continue
                        cited = {s["id"] for s in sites if rng.random() < prob[s["id"]]}
                        text, spans, cites = answer_for(sites, cited, with_spans=(e == "openai"))
                        if e == "silent":
                            cites, spans = [], None
                        smp = dict(base, status="ok", answer=text, citations=cites,
                                   cited=brand["id"] in cited, mentioned=brand["id"] in cited,
                                   competitors={r["name"]: {"cited": r["id"] in cited, "rank": None,
                                                            "mentioned": r["id"] in cited} for r in rivals})
                        if spans:
                            smp["spans"] = spans
                            ent = GW.Entity({"name": brand["name"], "domains": brand["domains"]})
                            share = GW.answer_support(text, spans, GW.owner_test(ent, cites))
                            if share:
                                smp["supported_share"] = share
                        samples.append(smp)
            run_doc = {"format": GW.RUN_FORMAT, "run_id": rid, "started_at": rid, "interrupted": False,
                       "brand": {"name": brand["name"], "domains": brand["domains"], "url_prefixes": [], "aliases": []},
                       "competitors": [{"name": r["name"], "domains": r["domains"], "url_prefixes": [], "aliases": []}
                                       for r in rivals],
                       "engines": [dict({"id": e, "provider": "openai", "model": "m", "status": "measured"},
                                        **({"stopped": stopped[e]} if e in stopped else {})) for e in engs],
                       "samples": samples}
            d = os.path.join(root, "runs", "wave0", c["id"])
            os.makedirs(d, exist_ok=True)
            with io.open(os.path.join(d, rid + ".json"), "w", encoding="utf-8") as f:
                json.dump(run_doc, f)
        for s in c["sites"]:
            for k in (1, 2):
                d = os.path.join(root, "readiness", "wave0", "run%d" % k)
                os.makedirs(d, exist_ok=True)
                if c["id"] == "c02" and s["sampling_score"] == max(x["sampling_score"] for x in c["sites"]) and k == 2:
                    rep = {"error": {"kind": "timeout", "message": "could not fetch"}}       # a run the CLI could not score
                else:
                    capped = c["id"] == "c03" and s["sampling_score"] == min(x["sampling_score"] for x in c["sites"])
                    rep = {"normalised": s["sampling_score"] + (1 if k == 1 else -1), "gate_capped": capped,
                           "sampled_urls": ["https://%s/" % s["site"]] * 8, "audited_at": "2026-10-2%dT00:00:00Z" % k,
                           "checks": [{"id": "g.robots", "state": "scored", "points": 0 if capped else 5},
                                      {"id": "p2.answer-passages", "state": "scored", "points": s["sampling_score"] // 12}]}
                with io.open(os.path.join(d, s["site"] + ".json"), "w", encoding="utf-8") as f:
                    json.dump(rep, f)
    return cats


class Statistics(unittest.TestCase):
    def test_tau_b_with_ties(self):
        self.assertAlmostEqual(an.kendall_tau_b([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(an.kendall_tau_b([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        # five concordant pairs, one tied in x: 5 / sqrt((6 - 1) * (6 - 0))
        self.assertAlmostEqual(an.kendall_tau_b([1, 2, 2, 3], [1, 3, 2, 4]), 5 / math.sqrt(30))
        self.assertIsNone(an.kendall_tau_b([1, 2, 3], [0, 0, 0]))       # every site the same R: no tau

    def test_holm_matches_watch(self):
        ps = [0.012, 0.20, 0.020, 0.04]
        self.assertEqual([round(v, 10) for v in an.holm(ps)], [round(v, 10) for v in GW.holm(ps)])
        self.assertEqual([round(v, 3) for v in an.holm([0.012, 0.20, 0.020])], [0.036, 0.2, 0.04])

    def test_permutation_p_counts_the_observed(self):
        # one category of three sites in perfect order: |T| = 1 is reached by 2 of the 6 orderings
        r = an.association([("c", [{"X": 1, "R": 0.1}, {"X": 2, "R": 0.2}, {"X": 3, "R": 0.3}])], "X", "R", 6000, 10)
        self.assertEqual(r["T"], 1.0)
        self.assertAlmostEqual(r["p"], 2 / 6.0, delta=0.03)

    def test_strata_use_the_rubric_cuts(self):
        self.assertEqual([an.stratum_of(x) for x in (0, 50, 51, 65, 66, 100)], ["low", "low", "mid", "mid", "high", "high"])


class Recovery(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="prereg-test-")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_analysis(self, **kw):
        return an.analyze(self.dir, 0, PERMS, BOOTS, 11, power_t=0.31, **kw)

    def test_a_planted_association_is_recovered(self):
        write_round(self.dir, effect=True)
        res = self.run_analysis()
        p1 = res["P1"]
        self.assertEqual(p1["n_categories"], 14)
        self.assertTrue(p1["minimum_met"])
        self.assertGreater(p1["T"], 0.5)
        self.assertLess(p1["p"], 0.01)
        self.assertGreater(p1["ci"][0], 0)
        self.assertGreater(p1["D"]["D"], 0.2)
        for k in ("S1", "S2", "S4"):
            self.assertLess(res[k]["p_holm"], ALPHA_TEST, k)
        self.assertTrue(res["S3"]["estimable"])
        self.assertEqual(res["holm_family"], ["S1", "S2", "S3", "S4"])
        self.assertEqual(res["wording"][0], an.WORDING["positive"])

    def test_no_association_is_not_called(self):
        write_round(self.dir, effect=False)
        res = self.run_analysis()
        p1 = res["P1"]
        self.assertEqual(p1["n_categories"], 14)
        self.assertLess(abs(p1["T"]), 0.25)
        self.assertGreaterEqual(p1["p"], 0.05)
        self.assertLessEqual(p1["ci"][0], 0)
        self.assertGreaterEqual(p1["ci"][1], 0)
        self.assertTrue(res["wording"][0].startswith("No association was detected"))
        self.assertIn("(T = 0.31)", res["wording"][0])

    def test_reruns_exclusions_and_measures(self):
        write_round(self.dir, effect=True, extra_silent_engine=True)
        res = self.run_analysis()
        # an engine whose answers never carry a citation failed for the wave and leaves every count
        self.assertEqual(res["failed_engines"], ["silent"])
        cats = {c["id"]: c for c in res["categories"]}
        self.assertTrue(all("silent" not in s["by_engine"] for c in cats.values() for s in c["sites"]))
        # the engine stopped in c01's first run is read from the rerun, the other from the first file
        self.assertEqual(res["run_files"]["c01"]["used"], {"openai": "20261020T010000Z", "gemini": "20261020T050000Z",
                                                           "silent": "20261020T010000Z"})
        self.assertEqual(cats["c01"]["sites"][0]["answered"], 2 * QUESTIONS * RUNS)
        # a site whose name is an ordinary word has no N; its R is measured
        flagged = [s for s in cats["c00"]["sites"] if s["ordinary_word"]][0]
        self.assertIsNone(flagged["N"])
        self.assertIsNotNone(flagged["R"])
        # X is the mean of the runs the CLI scored; a site with one failed run keeps the other
        top = max(cats["c02"]["sites"], key=lambda s: s["X"] or 0)
        self.assertEqual(len(top["readiness_runs"]), 1)
        # S1 leaves out the site with a gate at zero
        self.assertEqual(sum(1 for c in cats.values() for s in c["sites"] if s["gate_zero"]), 1)
        self.assertEqual(len(res["S1"]["tau"]), 14)
        # A is read only from answers that cite the site and carry spans (here, only openai's): every A in [0, 1]
        a_vals = [s["A"] for c in cats.values() for s in c["sites"] if s["A"] is not None]
        self.assertTrue(a_vals and all(0 < v < 1 for v in a_vals))
        self.assertTrue(all(s["by_engine"]["gemini"]["A"] is None for c in cats.values() for s in c["sites"]))

    def test_answer_share_for_a_competitor_is_watchs_rule(self):
        sites = [site_entry("z", i, x) for i, x in enumerate((40, 70))]
        text, spans, cites = answer_for(sites, {sites[0]["id"], sites[1]["id"]}, True)
        smp = {"answer": text, "spans": spans, "citations": cites, "_brand": sites[0]["name"]}
        ent = GW.Entity({"name": sites[1]["name"], "domains": sites[1]["domains"]})
        want = GW.answer_support(text, spans, GW.owner_test(ent, cites))["chars"]
        self.assertEqual(an.answer_share(smp, ent), want)
        self.assertGreater(want, 0)
        self.assertIsNone(an.answer_share(dict(smp, spans=None), ent))     # no spans: not measured, never 0

    def test_absorption_leaves_the_family_without_spans(self):
        write_round(self.dir, effect=True)
        for p in [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(self.dir, "runs")) for f in fs]:
            with io.open(p, encoding="utf-8") as f:
                doc = json.load(f)
            for s in doc["samples"]:
                s.pop("spans", None)
                s.pop("supported_share", None)
            with io.open(p, "w", encoding="utf-8") as f:
                json.dump(doc, f)
        res = self.run_analysis()
        self.assertFalse(res["S3"]["estimable"])
        self.assertEqual(res["holm_family"], ["S1", "S2", "S4"])

    def test_power_rises_with_the_effect(self):
        design = [[34, 46, 57, 72, 84]] * 6
        res = an.power(design, [0.0, 2.0], sims=30, perms=99, seed=3)
        self.assertLess(res["grid"][0]["power"], 0.3)
        self.assertGreater(res["grid"][1]["power"], 0.8)
        self.assertGreater(res["grid"][1]["mean_T"], res["grid"][0]["mean_T"])


ALPHA_TEST = 0.05

if __name__ == "__main__":
    unittest.main(verbosity=1)
