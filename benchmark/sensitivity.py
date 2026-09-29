#!/usr/bin/env python3
"""How much of the leaderboard is the rubric's weights?

    python3 benchmark/sensitivity.py           # writes sensitivity.json, SENSITIVITY.md and SENSITIVITY.zh-CN.md
    python3 benchmark/sensitivity.py --check   # exit 1 when the committed files are not what the data gives

Offline, from benchmark/results.json, the per-site reports in benchmark/raw/ and rubric/v1.1.json. It first
recomputes every published score from the per-check points with the rubric's arithmetic and stops on any mismatch,
so every figure after that is about the weights and nothing else. Then it re-scores every site under other
weightings (equal weights, an illustrative evidence-basis weighting, each check left out, and seeded random draws)
and reports the rank correlation, band changes, rank moves and top-20 overlap against the published scores, plus
how each check spreads the field. Seeded: the same data gives the same files byte for byte.

Nothing here changes v1.1. The weights stay as published; this is input for v1.2.
"""
import io, json, math, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from stats import MIN_N, SEED, raw_path  # noqa: E402

OUT_JSON = os.path.join(HERE, "sensitivity.json")
OUT_MD = {"en": os.path.join(HERE, "SENSITIVITY.md"), "zh": os.path.join(HERE, "SENSITIVITY.zh-CN.md")}
DRAWS, SPREAD = 300, (0.5, 1.5)
# illustrative only: checks whose basis is published research or vendor documentation keep their weight, checks
# resting on field observation or convention get half (rubric/evidence-v1.1.md defines the four bases)
BASIS_FACTOR = {"research": 1.0, "vendor-doc": 1.0, "field-observation": 0.5, "convention": 0.5}
TOP = 20
FLAT = 0.9           # one tier holding this share of the observed sites carries little information


def _read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def _write(path, text):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ── the data, shared with percentiles.py ───────────────────────────────────

def load():
    """(rubric, results, sites): each scored row of results.json with its per-check points from raw/ (None where
    the check was unobservable). Stops when a scored row has no report."""
    rub = json.loads(_read(os.path.join(ROOT, "rubric", "v1.1.json")))
    res = json.loads(_read(os.path.join(HERE, "results.json")))
    sites = []
    for r in res["results"]:
        if r.get("normalised") is None:
            continue
        fp = raw_path(r["site"])
        if not os.path.exists(fp):
            raise SystemExit("no raw report for %s (%s)" % (r["site"], fp))
        rep = json.loads(_read(fp))
        sites.append({"site": r["site"], "sector": r["sector"], "normalised": r["normalised"], "band": r["band"],
                      "readiness": r["readiness"], "observable_max": r["observable_max"],
                      "gate_capped": bool(r.get("gate_capped")),
                      "points": {c["id"]: (c.get("points") if c.get("state") == "scored" else None)
                                 for c in rep["checks"]}})
    return rub, res, sites


def band_of(score, rub):
    return next(b["name"] for b in rub["bands"] if score >= b["min_pct"])


def uncapped(site):
    """The percentage before the gate cap: readiness over the observable maximum, at most 100."""
    return min(100, round(100 * site["readiness"] / site["observable_max"])) if site["observable_max"] else 0


def scorer(rub, sites):
    """score(weights) -> [normalised per site] under {check: weight}, with the rubric's arithmetic: each observable
    check adds its tier's share of its points times its weight, over the weights of the observable checks; the
    bonus (at most bonus_cap) is added on top, the result capped at 100, and at gate_cap when a gate scored zero."""
    checks = [c for c in rub["checks"] if c["kind"] != "bonus"]
    bonus = [c["id"] for c in rub["checks"] if c["kind"] == "bonus"]
    gates = [c["id"] for c in checks if c["kind"] == "gate"]
    rows = []
    for s in sites:
        obs = [(c["id"], s["points"][c["id"]] / float(c["points"])) for c in checks if s["points"].get(c["id"]) is not None]
        b = min(sum(s["points"].get(x) or 0 for x in bonus), rub["bonus_cap"])
        rows.append((obs, b, any(s["points"].get(g) == 0 for g in gates)))

    # the float sums are math.fsum, which is correctly rounded on every Python: from 3.12 the builtin sum()
    # compensates float additions, so a score near x.5 would round the other way and move a band with the version
    def score(w):
        out = []
        for obs, b, capped in rows:
            got = math.fsum(w[cid] * f for cid, f in obs)
            den = math.fsum(w[cid] for cid, _ in obs)
            n = min(100, round(100 * (got + b) / den)) if den else 0
            out.append(min(n, rub["gate_cap"]) if capped else n)
        return out
    return score


# ── comparing two orderings ────────────────────────────────────────────────

def ranks(xs):
    """Average ranks, 1 for the highest score; ties share the mean of their places."""
    order = sorted(range(len(xs)), key=lambda i: -xs[i])
    r, i = [0.0] * len(xs), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return r


def pearson(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    va = math.fsum((x - ma) ** 2 for x in a)
    vb = math.fsum((y - mb) ** 2 for y in b)
    if not va or not vb:
        return None
    return math.fsum((x - ma) * (y - mb) for x, y in zip(a, b)) / (va * vb) ** 0.5


def compare(base, alt, names, rub, base_ranks=None):
    """Spearman rho, band changes, median absolute rank move and top-TOP overlap of alt against base."""
    rb, ra = base_ranks or ranks(base), ranks(alt)
    top = lambda xs: {names[i] for i in sorted(range(len(xs)), key=lambda i: (-xs[i], names[i]))[:TOP]}  # noqa: E731
    return {"spearman": round(pearson(rb, ra), 3),
            "band_changes": sum(1 for x, y in zip(base, alt) if band_of(x, rub) != band_of(y, rub)),
            "median_rank_move": statistics.median(abs(x - y) for x, y in zip(rb, ra)),
            "top20_overlap": len(top(base) & top(alt))}


def spread(xs):
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]  # noqa: E731
    return {"min": xs[0], "p5": q(.05), "median": q(.5), "p95": q(.95), "max": xs[-1]}


def to_100(w):
    t = math.fsum(w.values())
    return {k: 100.0 * v / t for k, v in w.items()}


# ── the study ──────────────────────────────────────────────────────────────

def analyse(rub, res, sites):
    checks = [c for c in rub["checks"] if c["kind"] != "bonus"]
    pts = {c["id"]: c["points"] for c in checks}
    names = [s["site"] for s in sites]
    score = scorer(rub, sites)
    bonus = [c["id"] for c in rub["checks"] if c["kind"] == "bonus"]

    def totals(s):
        """(readiness, observable_max) as the rubric adds them up from the site's points."""
        got = sum(s["points"][c] for c in pts if s["points"].get(c) is not None)
        return (got + min(sum(s["points"].get(c) or 0 for c in bonus), rub["bonus_cap"]),
                sum(pts[c] for c in pts if s["points"].get(c) is not None))
    base = score(dict(pts))
    bad = [(s["site"], s["normalised"], x) for s, x in zip(sites, base) if x != s["normalised"]]
    bad += [(s["site"], (s["readiness"], s["observable_max"]), totals(s)) for s in sites
            if totals(s) != (s["readiness"], s["observable_max"])]
    if bad:
        raise SystemExit("%d published scores are not what the rubric's arithmetic gives from raw/, e.g. %s"
                         % (len(bad), bad[:3]))
    rb = ranks(base)
    alt = {"equal": {c: 100.0 / len(checks) for c in pts},
           "evidence_basis": to_100({c["id"]: c["points"] * BASIS_FACTOR[c["evidence"]["basis"]] for c in checks})}
    out = {"generated_by": "benchmark/sensitivity.py",
           "source": {"measured_at": res["measured_at"], "tool": res["tool"], "rubric_version": rub["rubric_version"],
                      "n_scored": len(sites)},
           "method": {"arithmetic": "each observable check: its tier's share of its points times its weight, over the "
                                    "weights of the observable checks; plus the bonus (at most %d); capped at 100, and "
                                    "at %d when a gate scored zero, in every weighting" % (rub["bonus_cap"], rub["gate_cap"]),
                      "equal": "every scored check weighs 100/%d" % len(checks),
                      "evidence_basis": "illustrative: points x %s by the check's evidence basis, rescaled to 100"
                                        % ", ".join("%s %s" % kv for kv in sorted(BASIS_FACTOR.items())),
                      "leave_one_out": "the check is treated as unobservable on every site; a gate left out still caps",
                      "draws": "%d draws, each weight = points x U(%s, %s), rescaled to 100; seed %d"
                               % (DRAWS, SPREAD[0], SPREAD[1], SEED),
                      "ranks": "average ranks, 1 for the highest score; top %d ordered by score, then site name" % TOP},
           "recompute": {"n": len(sites), "mismatches": 0},
           "weights": {k: {c: round(v, 3) for c, v in w.items()} for k, w in alt.items()},
           "alternatives": {k: compare(base, score(w), names, rub, rb) for k, w in alt.items()}}
    # random draws: how far the order and the bands move when every weight is off by up to half
    rng = random.Random(SEED)
    runs, moved = [], [0] * len(sites)
    for _ in range(DRAWS):
        s2 = score(to_100({c: p * rng.uniform(*SPREAD) for c, p in sorted(pts.items())}))
        runs.append(compare(base, s2, names, rub, rb))
        for i, (x, y) in enumerate(zip(base, s2)):
            moved[i] += band_of(x, rub) != band_of(y, rub)
    out["draws"] = {k: spread([r[k] for r in runs]) for k in ("spearman", "band_changes", "median_rank_move", "top20_overlap")}
    out["draws"].update(n=DRAWS, sites_band_changed_any=sum(1 for m in moved if m),
                        sites_band_changed_half=sum(1 for m in moved if 2 * m >= DRAWS))
    # leave one check out; a check the CLI never observed cannot move anything
    loo, never = [], []
    for c in checks:
        n_obs = sum(1 for s in sites if s["points"].get(c["id"]) is not None)
        if not n_obs:
            never.append(c["id"])
            continue
        w = dict(pts, **{c["id"]: 0})
        loo.append(dict(check=c["id"], points=c["points"], observed=n_obs, **compare(base, score(w), names, rub, rb)))
    out["leave_one_out"] = sorted(loo, key=lambda x: (-x["band_changes"], x["check"]))
    out["never_observed"] = never
    out["items"] = items(rub, sites)
    return out


def items(rub, sites):
    """Per check: how the observed sites spread over its tiers, the floor and ceiling shares, and (scored checks) the
    item-rest correlation: its tier share against the uncapped percentage of the other observed checks."""
    scored = [c for c in rub["checks"] if c["kind"] != "bonus"]
    out = []
    for c in rub["checks"]:
        obs = [s for s in sites if s["points"].get(c["id"]) is not None]
        tiers = {}
        for s in obs:
            tiers[s["points"][c["id"]]] = tiers.get(s["points"][c["id"]], 0) + 1
        row = {"check": c["id"], "kind": c["kind"], "points": c["points"], "observed": len(obs),
               "tiers": {str(k): tiers[k] for k in sorted(tiers)}, "floor_pct": None, "ceiling_pct": None,
               "modal_pct": None, "item_rest_r": None}
        if obs:
            row.update(floor_pct=round(100.0 * tiers.get(0, 0) / len(obs), 1),
                       ceiling_pct=round(100.0 * tiers.get(c["points"], 0) / len(obs), 1),
                       modal_pct=round(100.0 * max(tiers.values()) / len(obs), 1))
        if c["kind"] != "bonus" and len(obs) >= MIN_N:
            frac, rest = [], []
            for s in obs:
                o = [(d["points"], s["points"][d["id"]]) for d in scored
                     if d["id"] != c["id"] and s["points"].get(d["id"]) is not None]
                if o:
                    frac.append(s["points"][c["id"]] / float(c["points"]))
                    rest.append(100.0 * sum(p for _, p in o) / sum(m for m, _ in o))
            r = pearson(frac, rest)
            row["item_rest_r"] = round(r, 2) if r is not None else None
        out.append(row)
    return out


# ── the two generated documents ────────────────────────────────────────────

def _n(x):
    return ("%.1f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def _pct(n, of):
    return "%d%%" % round(100.0 * n / of) if of else "—"


T = {
 "en": dict(
  title="# Weight sensitivity · AIV rubric v1.1\n",
  twin="简体中文：[SENSITIVITY.zh-CN.md](SENSITIVITY.zh-CN.md)\n",
  intro=("How much does the leaderboard depend on the rubric's weights? This re-scores the %(n)d sites of the "
         "%(date)s run (%(tool)s) offline, from [results.json](results.json) and the [per-site reports](raw/), with "
         "[sensitivity.py](sensitivity.py). **Nothing here changes v1.1**: the weights stay as published, and any "
         "change ships as a new rubric version. This is input for v1.2.\n"),
  recompute=("First the script recomputes every published score from the per-check points with the rubric's "
             "arithmetic: each observable check adds its tier's points, over the points of the observable checks, "
             "plus the bonus (at most +%(bonus)d), capped at 100 and at %(cap)d when a gate scores zero. "
             "%(n)d of %(n)d match, so every difference below comes from the weights alone. Every weighting keeps "
             "that arithmetic and the gate cap.\n"),
  h_alt="## Other weightings\n",
  alt_intro=("Each row re-scores all %(n)d sites and compares them with the published scores: Spearman's rank "
             "correlation, how many sites change band, the median number of places a site moves, and how many of "
             "the top %(top)d stay in the top %(top)d.\n"),
  alt_head="| Weighting | Spearman ρ | Band changes | Median rank move | Top-%(top)d overlap |",
  equal="Equal: every scored check weighs 100/%(k)d",
  basis="Evidence basis, illustrative: research and vendor-doc checks keep their points, field-observation and "
        "convention checks get half",
  draws="%(draws)d random draws, every weight × U(%(lo)s, %(hi)s): median (5th–95th percentile)",
  draws_note=("Across the random draws, %(any)d sites change band in at least one draw and %(half)d in half of them "
              "or more.\n"),
  h_loo="## Leaving one check out\n",
  loo_intro=("Each row treats one check as unobservable on every site, which is what the rubric does when a check "
             "cannot be observed. A gate left out still caps. Sorted by band changes.\n"),
  loo_head="| Check | Points | Observed on | Spearman ρ | Band changes | Median rank move | Top-%(top)d overlap |",
  never="The CLI observed %(list)s on no site, so leaving them out changes nothing here.\n",
  h_items="## How each check spreads the field\n",
  items_intro=("Over the sites where each check was observed: the share at zero, the share at full points, the "
               "largest share any one tier holds, and the item-rest correlation, the check's tier share against "
               "the uncapped percentage of the other observed checks (no figure below %(min_n)d sites). "
               "The [calibration record](../rubric/calibration-v1.1.md#four-structural-problems-the-audits-exposed) "
               "found checks that scored the same on all five calibration sites and so carried no information; "
               "here a check is flagged ⚑ when one tier holds %(flat)d%% or more of the sites.\n"),
  items_head="| Check | Points | Observed on | At zero | At full | Largest tier | Item-rest r | Sites per tier (points: sites) |",
  flat_mark=" ⚑",
  h_v12="## Input for v1.2\n",
  v12_rank=("**Rank order is robust to the weights.** Spearman's ρ is at least %(min_rho)s under every weighting "
            "above, and at least %(p5_rho)s in 95%% of the random draws."),
  v12_rank_weak=("**Rank order depends on the weights.** Spearman's ρ falls to %(min_rho)s under one of the "
                 "weightings above."),
  v12_band=("**Bands are where the weights matter.** Equal weights change the band of %(eq)d sites (%(eq_pct)s), "
            "the evidence-basis weighting %(ev)d, and the random draws a median of %(med)d (%(p5)d–%(p95)d); "
            "%(any)d sites change band in at least one draw."),
  v12_loo="**Most bands move when one of these is left out:** %(list)s.",
  v12_flat="**One tier holds %(flat)d%% or more of the sites** for %(list)s: on this field they carry little information.",
  v12_low="**Item-rest correlation below %(low)s** for %(list)s: they rank sites differently from the rest of the rubric.",
  v12_end="No weight in v1.1 changes. A change to a weight or a tier ships as a new rubric version.",
 ),
 "zh": dict(
  title="# 权重敏感性 · AIV 量表 v1.1\n",
  twin="English: [SENSITIVITY.md](SENSITIVITY.md)\n",
  intro=("榜单有多大程度取决于量表的权重？这里用 [sensitivity.py](sensitivity.py)，离线读 [results.json](results.json) "
         "和[逐站报告](raw/)，把 %(date)s 那一轮（%(tool)s）的 %(n)d 个站重新打分。**这里不改 v1.1**："
         "权重保持发布时的样子，任何改动都作为新版本量表发布。本文是 v1.2 的输入。\n"),
  recompute=("脚本先用量表的算法从逐项分数重算每个公开分数：每个可观测检查项计入它所在档的分数，除以可观测检查项的满分之和，"
             "再加加分项（最多 +%(bonus)d），封顶 100；任一门槛项得 0 分时封顶 %(cap)d。%(n)d 个站里 %(n)d 个一致，"
             "所以下面的每一处差别都只来自权重。每种权重都沿用这套算法和门槛封顶。\n"),
  h_alt="## 换一套权重\n",
  alt_intro=("每一行把 %(n)d 个站全部重新打分，与公开分数比较：Spearman 秩相关、换档的站数、名次移动的中位数，"
             "以及前 %(top)d 名里有几个仍在前 %(top)d。\n"),
  alt_head="| 权重 | Spearman ρ | 换档站数 | 名次移动中位数 | 前 %(top)d 重合 |",
  equal="等权：每个计分检查项 100/%(k)d",
  basis="按证据依据加权（示意）：research 与 vendor-doc 的检查项保持原分值，field-observation 与 convention 减半",
  draws="%(draws)d 次随机抽样，每项权重 × U(%(lo)s, %(hi)s)：中位数（第 5–95 百分位）",
  draws_note="随机抽样中，%(any)d 个站至少在一次抽样里换档，%(half)d 个站在一半及以上的抽样里换档。\n",
  h_loo="## 逐项拿掉一个检查项\n",
  loo_intro=("每一行把一个检查项在所有站上都当作不可观测——检查项观测不到时量表本来就这么处理。"
             "被拿掉的门槛项仍然封顶。按换档站数排序。\n"),
  loo_head="| 检查项 | 分值 | 可观测站数 | Spearman ρ | 换档站数 | 名次移动中位数 | 前 %(top)d 重合 |",
  never="CLI 在所有站上都观测不到 %(list)s，所以拿掉它们在这里没有任何影响。\n",
  h_items="## 每个检查项怎样拉开差距\n",
  items_intro=("统计口径是该检查项可观测的站：得 0 分的比例、拿满分的比例、单一档位占的最大比例，以及项目-其余相关"
               "（该项的得分率与其余可观测检查项未封顶百分比之间的相关；不足 %(min_n)d 个站不给数）。"
               "[标定记录](../rubric/calibration-v1.1.zh-CN.md#逐项表现暴露的四个结构问题)发现有些检查项在五个标定站上"
               "得分完全相同，因此不携带信息；这里某一档占到 %(flat)d%% 及以上的检查项标 ⚑。\n"),
  items_head="| 检查项 | 分值 | 可观测站数 | 得 0 分 | 满分 | 最大一档 | 项目-其余 r | 各档站数（分值: 站数） |",
  flat_mark=" ⚑",
  h_v12="## 给 v1.2 的输入\n",
  v12_rank="**名次对权重不敏感。** 上面每一种权重下 Spearman ρ 都不低于 %(min_rho)s，95%% 的随机抽样不低于 %(p5_rho)s。",
  v12_rank_weak="**名次取决于权重。** 上面有一种权重下 Spearman ρ 降到 %(min_rho)s。",
  v12_band=("**权重真正影响的是档位。** 等权让 %(eq)d 个站换档（%(eq_pct)s），按证据依据加权 %(ev)d 个，"
            "随机抽样的中位数是 %(med)d 个（%(p5)d–%(p95)d）；%(any)d 个站至少在一次抽样里换档。"),
  v12_loo="**拿掉这几项时换档最多：**%(list)s。",
  v12_flat="**某一档占到 %(flat)d%% 及以上的检查项：**%(list)s——在这批站上它们携带的信息很少。",
  v12_low="**项目-其余相关低于 %(low)s 的检查项：**%(list)s——它们给站点的排序与量表其余部分不同。",
  v12_end="v1.1 的权重一项都不改。任何权重或档位的改动都作为新版本量表发布。",
 )}
LOW_R = 0.2


def render(doc, lang):
    t, s, a, d = T[lang], doc["source"], doc["alternatives"], doc["draws"]
    n = s["n_scored"]
    k = len(doc["weights"]["equal"])
    v = dict(n=n, date=s["measured_at"], tool=s["tool"], top=TOP, k=k, draws=d["n"], lo=_n(SPREAD[0]), hi=_n(SPREAD[1]),
             any=d["sites_band_changed_any"], half=d["sites_band_changed_half"], min_n=MIN_N, flat=int(FLAT * 100))
    rub = json.loads(_read(os.path.join(ROOT, "rubric", "v1.1.json")))
    v.update(bonus=rub["bonus_cap"], cap=rub["gate_cap"])
    sep = "、" if lang == "zh" else ", "
    L = [t["title"], t["twin"], t["intro"] % v, t["recompute"] % v, t["h_alt"], t["alt_intro"] % v,
         t["alt_head"] % v, "|---|:-:|:-:|:-:|:-:|"]
    for key in ("equal", "evidence_basis"):
        x = a[key]
        L.append("| %s | %.3f | %d (%s) | %s | %d |" % ((t["equal"] if key == "equal" else t["basis"]) % v, x["spearman"],
                 x["band_changes"], _pct(x["band_changes"], n), _n(x["median_rank_move"]), x["top20_overlap"]))
    L.append("| %s | %.3f (%.3f–%.3f) | %d (%d–%d) | %s (%s–%s) | %d (%d–%d) |" % (
        t["draws"] % v, d["spearman"]["median"], d["spearman"]["p5"], d["spearman"]["p95"],
        d["band_changes"]["median"], d["band_changes"]["p5"], d["band_changes"]["p95"],
        _n(d["median_rank_move"]["median"]), _n(d["median_rank_move"]["p5"]), _n(d["median_rank_move"]["p95"]),
        d["top20_overlap"]["median"], d["top20_overlap"]["p5"], d["top20_overlap"]["p95"]))
    L += ["", t["draws_note"] % v, t["h_loo"], t["loo_intro"], t["loo_head"] % v, "|---|:-:|:-:|:-:|:-:|:-:|:-:|"]
    for x in doc["leave_one_out"]:
        L.append("| `%s` | %d | %d | %.3f | %d | %s | %d |" % (x["check"], x["points"], x["observed"], x["spearman"],
                                                             x["band_changes"], _n(x["median_rank_move"]), x["top20_overlap"]))
    L.append("")
    if doc["never_observed"]:
        L.append(t["never"] % dict(list=sep.join("`%s`" % c for c in doc["never_observed"])))
    L += [t["h_items"], t["items_intro"] % v, t["items_head"], "|---|:-:|:-:|:-:|:-:|:-:|:-:|---|"]
    flat, low = [], []
    for x in doc["items"]:
        if not x["observed"]:
            continue
        is_flat = x["modal_pct"] >= 100 * FLAT
        if is_flat:
            flat.append(x["check"])
        if x["item_rest_r"] is not None and x["item_rest_r"] < LOW_R:
            low.append(x["check"])
        L.append("| `%s`%s | %d | %d | %s%% | %s%% | %s%% | %s | %s |" % (
            x["check"], t["flat_mark"] if is_flat else "", x["points"], x["observed"], _n(x["floor_pct"]),
            _n(x["ceiling_pct"]), _n(x["modal_pct"]), "—" if x["item_rest_r"] is None else "%.2f" % x["item_rest_r"],
            " · ".join("%s: %d" % kv for kv in x["tiers"].items())))
    L += ["", t["h_v12"]]
    rhos = [a[key]["spearman"] for key in a] + [x["spearman"] for x in doc["leave_one_out"]] + [d["spearman"]["min"]]
    rv = dict(min_rho="%.3f" % min(rhos), p5_rho="%.3f" % d["spearman"]["p5"])
    bullets = [(t["v12_rank"] if min(rhos) >= 0.9 else t["v12_rank_weak"]) % rv,
               t["v12_band"] % dict(eq=a["equal"]["band_changes"], eq_pct=_pct(a["equal"]["band_changes"], n),
                                    ev=a["evidence_basis"]["band_changes"], med=d["band_changes"]["median"],
                                    p5=d["band_changes"]["p5"], p95=d["band_changes"]["p95"], any=d["sites_band_changed_any"])]
    top_loo = [x for x in doc["leave_one_out"] if x["band_changes"]][:3]
    if top_loo:
        bullets.append(t["v12_loo"] % dict(list=sep.join("`%s` (%d)" % (x["check"], x["band_changes"]) for x in top_loo)))
    if flat:
        bullets.append(t["v12_flat"] % dict(flat=int(FLAT * 100), list=sep.join("`%s`" % c for c in flat)))
    if low:
        bullets.append(t["v12_low"] % dict(low=LOW_R, list=sep.join("`%s`" % c for c in low)))
    bullets.append(t["v12_end"])
    L += ["- " + b for b in bullets]
    return "\n".join(L) + "\n"


def outputs():
    """{path: text} for sensitivity.json and the two documents, and the study they came from."""
    rub, res, sites = load()
    doc = analyse(rub, res, sites)
    files = {OUT_JSON: json.dumps(doc, ensure_ascii=False, indent=1) + "\n"}
    files.update({OUT_MD[lang]: render(doc, lang) for lang in OUT_MD})
    return files, doc


def main(argv):
    files, doc = outputs()
    if "--check" in argv:
        bad = [p for p, text in files.items() if not os.path.exists(p) or _read(p) != text]
        for p in bad:
            print("%s is not what sensitivity.py derives from results.json and raw/ (python3 benchmark/sensitivity.py)"
                  % os.path.relpath(p, ROOT), file=sys.stderr)
        return 1 if bad else 0
    for p, text in files.items():
        _write(p, text)
    e = doc["alternatives"]["equal"]
    print("%d of %d published scores recomputed exactly; equal weights: rho %.3f, %d band changes; random draws: "
          "median %d band changes" % (doc["recompute"]["n"], doc["recompute"]["n"], e["spearman"], e["band_changes"],
                                      doc["draws"]["band_changes"]["median"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
