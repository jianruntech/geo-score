#!/usr/bin/env python3
"""Round 0: from the sampling run to the frozen sample (benchmark/PREREGISTRATION.md sections 5.2 to 5.4, 5.6 and 6,
and the amendment of 2026-10-12).

Run in the clone score_candidates.sh made, after it finished:

    OPENAI_COMPAT_MODEL=<model id> python3 benchmark/prereg/round0/vm/draw.py

1. Out: a remaining candidate the CLI could not score (no report), or scored on fewer than 4 sampled pages.
2. Strata from the rubric's own band cuts: low below 51, mid 51 to 65, high 66 and above.
3. In each category, up to 2 sites per stratum, drawn with a recorded seed (random.Random(seed).sample over the
   stratum's site ids in sorted order; the seed is the first 16 hex digits of SHA-256 of
   "geo-score prereg round0 draw|<category id>").
4. A category left with fewer than 4 sites, or with sites in one stratum only, is dropped.
5. Fewer than 12 categories left: the study stops before any answer is collected (exit 3; sample.json says why).
   More than 18 left: 18 are drawn with the seed of "geo-score prereg round0 categories", because Gemini's free tier
   answers about 500 grounded questions a day and the wave has 3 days (amendment of 2026-10-12).
6. The popularity covariate: each sampled site's rank in the current Tranco list, whose id is recorded (a site outside
   it gets no rank, which the analysis reads as 1,000,001, and a flag).
7. The frozen configs: sample/<category>/geo-score-watch.json with the sampled sites only (the first by name as
   brand), the step-2 questions unchanged, and the OpenAI-compatible engine's model set to OPENAI_COMPAT_MODEL.

Writes benchmark/prereg/round0/sample.json and sample/. No API is called; the only fetch is the Tranco list.
Standard library only.
"""
import argparse, datetime, hashlib, importlib.util, io, json, os, random, re, shutil, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = os.path.dirname(HERE)
ROOT = os.path.normpath(os.path.join(ROUND, "..", "..", ".."))
MIN_PAGES = 4                   # section 5.2: fewer sampled pages is a thin sample
PER_STRATUM = 2
MIN_SITES = 4
MIN_CATEGORIES, MAX_CATEGORIES = 12, 18
STRATA = (("low", None, 51), ("mid", 51, 66), ("high", 66, None))
TRANCO_ID = "https://tranco-list.eu/top-1m-id"
TRANCO_CSV = "https://tranco-list.eu/download/{id}/1000000"
TRANCO_META = "https://tranco-list.eu/api/lists/id/{id}"
GEMINI_PER_DAY = 6              # categories a day: 6 x 10 questions x 8 asks = 480 Gemini answers


def load_watch():
    spec = importlib.util.spec_from_file_location("geo_watch", os.path.join(ROOT, "cli", "geo_watch.py"))
    gw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gw)
    return gw


def seed_of(text):
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def stratum_of(score):
    for name, lo, hi in STRATA:
        if (lo is None or score >= lo) and (hi is None or score < hi):
            return name
    return None


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "geo-score-prereg/round0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def tranco(list_id=None, path=None):
    """(list id, metadata, {domain: rank}) of the Tranco list: the current one, or the one named."""
    lid = list_id or fetch(TRANCO_ID).strip()
    if not re.fullmatch(r"[A-Z0-9]{3,8}", lid):
        raise SystemExit("unexpected Tranco list id %r" % lid)
    text = io.open(path, encoding="utf-8").read() if path else fetch(TRANCO_CSV.format(id=lid), timeout=300)
    ranks = {}
    for line in text.splitlines():
        r, _, dom = line.partition(",")
        if r.strip().isdigit() and dom.strip():
            ranks.setdefault(dom.strip().lower(), int(r))
    try:
        meta = json.loads(fetch(TRANCO_META.format(id=lid)))
    except Exception as e:      # the ranks are what matter; the metadata is a record
        meta = {"error": str(e)[:200]}
    return lid, meta, ranks


def sampling(site, out):
    """(report or None, reason it is out or None, the URL scored, the error kind)."""
    rep_p, err_p = os.path.join(out, "reports", site + ".json"), os.path.join(out, "errors", site + ".json")
    if os.path.exists(rep_p):
        rep = read(rep_p)
        if not isinstance(rep.get("normalised"), (int, float)):
            return None, "the CLI's report has no score", None, None
        pages = len(rep.get("sampled_urls") or [])
        if pages < MIN_PAGES:
            return rep, "scored on %d sampled page%s, fewer than %d (a thin sample)" % (
                pages, "" if pages == 1 else "s", MIN_PAGES), rep.get("target"), None
        return rep, None, rep.get("target"), None
    if os.path.exists(err_p):
        err = (read(err_p).get("error") or {})
        return None, "the CLI could not score it (%s)" % (err.get("kind") or "unknown"), err.get("target"), err.get("kind")
    return None, "not scored in the sampling run", None, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--openai-model", default=os.environ.get("OPENAI_COMPAT_MODEL"),
                    help="the OpenAI-compatible endpoint's model id (default: $OPENAI_COMPAT_MODEL)")
    ap.add_argument("--tranco-id", help="use this Tranco list instead of the current one")
    ap.add_argument("--tranco-file", help="the list's CSV (rank,domain), already downloaded")
    ap.add_argument("--force", action="store_true", help="overwrite an existing sample.json")
    a = ap.parse_args(argv)
    gw = load_watch()
    if not a.openai_model or not gw.MODEL_RE.match(a.openai_model):
        raise SystemExit("set OPENAI_COMPAT_MODEL (or --openai-model) to the model id the endpoint serves")
    out_p = os.path.join(ROUND, "sample.json")
    if os.path.exists(out_p) and not a.force:
        raise SystemExit("%s exists: the sample is drawn once (--force replaces it)" % out_p)
    sdir = os.path.join(ROUND, "sampling")
    cli = io.open(os.path.join(sdir, "cli.txt"), encoding="utf-8").read().splitlines()
    cand = read(os.path.join(ROUND, "candidates.json"))
    cats = {c["id"]: c for c in read(os.path.join(ROUND, "categories.json"))["categories"]}

    result, kept = [], []
    for c in cand["categories"]:
        cid = c["id"]
        sites, excluded = [], []
        for v in c["candidates"]:
            if v["status"] != "remaining":
                excluded.append({"id": v["id"], "site": v["site"], "reason": v["status"]})
                continue
            rep, why, url, _ = sampling(v["site"], sdir)
            if why:
                excluded.append({"id": v["id"], "site": v["site"], "reason": why})
                continue
            score = rep["normalised"]
            sites.append({"id": v["id"], "site": v["site"], "name": v["entry"]["name"], "aliases": v["entry"]["aliases"],
                          "domains": v["entry"]["domains"], "url_prefixes": v["entry"]["url_prefixes"],
                          "ordinary_word": v["ordinary_word"], "ordinary_word_reasons": v["ordinary_word_reasons"],
                          "sampling_url": url, "sampling_score": score, "sampling_pages": len(rep["sampled_urls"]),
                          "sampling_gate_capped": bool(rep.get("gate_capped")), "sampling_band": rep.get("band"),
                          "stratum": stratum_of(score)})
        seed = seed_of("geo-score prereg round0 draw|%s" % cid)
        rng = random.Random(seed)
        drawn = []
        for name, _, _ in STRATA:
            pool = sorted(s["id"] for s in sites if s["stratum"] == name)
            drawn += rng.sample(pool, min(PER_STRATUM, len(pool)))
        chosen = sorted([s for s in sites if s["id"] in drawn], key=lambda s: s["name"].casefold())
        strata = sorted({s["stratum"] for s in chosen})
        row = {"id": cid, "name": cats[cid]["name"], "definition": cats[cid]["definition"],
               "eligible": len(sites), "by_stratum": {n: sum(1 for s in sites if s["stratum"] == n) for n, _, _ in STRATA},
               "draw": {"seed": seed, "seed_from": "geo-score prereg round0 draw|%s" % cid,
                        "method": "per stratum (low, mid, high), random.Random(seed).sample(sorted ids, min(2, n))"},
               "excluded": excluded, "sites": chosen, "questions": c["questions"], "questions_hash": c["questions_hash"]}
        if len(chosen) < MIN_SITES or len(strata) < 2:
            row["status"] = "dropped: %d sites drawn, in %s" % (len(chosen), ", ".join(strata) or "no stratum")
        else:
            row["status"] = "kept"
            kept.append(cid)
        result.append(row)

    cut = None
    if len(kept) > MAX_CATEGORIES:
        cseed = seed_of("geo-score prereg round0 categories")
        keep = sorted(random.Random(cseed).sample(sorted(kept), MAX_CATEGORIES))
        cut = {"seed": cseed, "seed_from": "geo-score prereg round0 categories", "from": sorted(kept), "kept": keep,
               "why": "Gemini's free tier answers about 500 grounded questions a day; 3 days hold 18 categories"}
        for r in result:
            if r["id"] in kept and r["id"] not in keep:
                r["status"] = "dropped: not among the 18 categories drawn (amendment of 2026-10-12)"
        kept = keep
    doc = {"format": "geo-score/prereg-round0-sample.v1", "plan": "benchmark/PREREGISTRATION.md",
           "drawn_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "cli": cli, "cli_version": (cli[0].split()[1] if cli and len(cli[0].split()) > 1 else None),
           "cli_tag": next((ln.split(" ", 1)[1] for ln in cli if ln.startswith("tag ")), None),
           "rubric": "v1.1", "strata": {n: [lo, hi] for n, lo, hi in STRATA}, "min_pages": MIN_PAGES,
           "category_cut": cut,
           "results_not_read": "benchmark/results.json, benchmark/results.csv and benchmark/raw/ were not read to draw "
                               "this sample; only the sampling run's reports were"}
    if len(kept) < MIN_CATEGORIES:
        doc.update(status="stopped: %d categories left, fewer than %d (section 5.4); no answer is collected"
                   % (len(kept), MIN_CATEGORIES), categories=[], all_categories=result)
        with io.open(out_p, "w", encoding="utf-8") as f:
            f.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print(doc["status"])
        return 3

    lid, meta, ranks = tranco(a.tranco_id, a.tranco_file)
    for r in result:
        for s in r["sites"]:
            rank = ranks.get(s["id"]) or ranks.get(s["site"])
            s["tranco_rank"], s["tranco_listed"] = rank, rank is not None

    base = read(os.path.join(ROUND, "watch", result[0]["id"], "geo-score-watch.json"))
    engines = [dict(e, model=a.openai_model) if e["provider"] == "openai" else dict(e) for e in base["engines"]]
    shutil.rmtree(os.path.join(ROUND, "sample"), ignore_errors=True)
    for r in result:
        if r["id"] not in kept:
            continue
        d = os.path.join(ROUND, "sample", r["id"])
        os.makedirs(d)
        ents = [{"name": s["name"], "domains": s["domains"], "url_prefixes": s["url_prefixes"], "aliases": s["aliases"]}
                for s in r["sites"]]
        cfg = dict(base, brand=ents[0], competitors=ents[1:], engines=engines)
        with io.open(os.path.join(d, "geo-score-watch.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
        shutil.copyfile(os.path.join(ROUND, "watch", r["id"], "queries.csv"), os.path.join(d, "queries.csv"))
        conf = gw.Config(os.path.join(d, "geo-score-watch.json"))
        qs = conf.load_queries()
        if conf.errors or gw.questions_hash(qs) != r["questions_hash"]:
            raise SystemExit("%s: the frozen config does not validate, or its questions changed: %s" % (r["id"], conf.errors))
        flagged = [q["query_id"] for q in qs if gw.flag_query(q, conf.brand, conf.competitors)["brand_in_query"]
                   or gw.flag_query(q, conf.brand, conf.competitors)["competitor_in_query"]]
        if flagged:
            raise SystemExit("%s: questions %s name a sampled site" % (r["id"], flagged))
        r["config"] = "sample/%s/geo-score-watch.json" % r["id"]
    order = [r["id"] for r in result if r["id"] in kept]
    doc.update(status="frozen", tranco={"list_id": lid, "metadata": meta, "unlisted_rank": 1000001},
               engines=engines, runs=base["runs"], country=base["country"],
               openai_endpoint="an OpenAI-compatible endpoint given at run time (OPENAI_COMPAT_BASE_URL); not "
                               "api.openai.com",
               collection_schedule={"per_day": GEMINI_PER_DAY,
                                    "days": [order[i:i + GEMINI_PER_DAY] for i in range(0, len(order), GEMINI_PER_DAY)]},
               categories=[r for r in result if r["id"] in kept],
               dropped_categories=[{"id": r["id"], "status": r["status"], "eligible": r["eligible"],
                                    "by_stratum": r["by_stratum"], "excluded": r["excluded"],
                                    "sites": [s["id"] for s in r["sites"]]} for r in result if r["id"] not in kept])
    with io.open(out_p, "w", encoding="utf-8") as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    for r in result:
        print("%-28s %-8s eligible %2d (low %d, mid %d, high %d) -> %d sampled" % (
            r["id"], r["status"].split(":")[0], r["eligible"], r["by_stratum"]["low"], r["by_stratum"]["mid"],
            r["by_stratum"]["high"], len(r["sites"]) if r["id"] in kept else 0))
    print("%d categories frozen; Tranco list %s; OpenAI-compatible model %s" % (len(kept), lid, a.openai_model))
    print("collection: %s" % "; ".join("day %d: %s" % (i + 1, ", ".join(d)) for i, d in
                                       enumerate(doc["collection_schedule"]["days"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
