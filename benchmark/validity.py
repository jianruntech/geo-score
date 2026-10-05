#!/usr/bin/env python3
"""How closely does the CLI agree with a hand audit of the same pages?

    python3 benchmark/validity.py            # re-score every hand audit, write validity.json
    python3 benchmark/validity.py --md-only  # regenerate VALIDITY*.md from validity.json; no re-scoring

For each published hand audit in examples/audits/v1.1/, the CLI re-scores the same pages
(`urls=` pinned to the audit's sampled_urls on the audited host) and every check both of them
scored is compared tier for tier. Two things are mixed into every difference and cannot be pulled
apart here: the CLI's heuristics versus a human reading, and whatever changed on the site since the
audit date. Both are reported as they are; nothing is tuned against this file.
"""
import datetime, glob, importlib.util, io, json, os, statistics, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("gs", os.path.join(ROOT, "cli", "geo_score.py"))
gs = importlib.util.module_from_spec(spec); spec.loader.exec_module(gs)
gs.c.on = False
OUT_DIR = os.path.join(HERE, "validity")
JUDGEMENT = sorted(gs.NEEDS_JUDGEMENT)          # the CLI never scores these; a hand audit does
# How the CLI reads each check. "rule" = parses a file, a status code or markup and applies the
# rubric's count; "heuristic" = approximates a judgement the rubric describes in prose.
METHOD = {"rule": ["g.robots", "p1.sitemap", "p1.llms-txt", "p1.organization", "p1.breadcrumb", "p1.page-type",
                   "p3.knowledge-graph", "p3.sameas", "p4.cn-engines"],
          "heuristic": ["g.reachable", "g.ssr", "p2.answer-passages", "p2.question-intent", "p2.freshness",
                        "p2.sourced-stats", "p2.named-author", "p3.video", "p4.answer-shape"]}


def rescore(audit):
    target = audit["target"]
    host = urllib.parse.urlsplit(target).netloc.lower()
    same = [u for u in audit["sampled_urls"] if urllib.parse.urlsplit(u).netloc.lower() == host]
    dropped = [u for u in audit["sampled_urls"] if u not in same]
    res = gs.run(target, urls=same)
    rep = gs.as_json(res)
    rep["validity_note"] = {"pinned_from": "examples/audits/v1.1 sampled_urls on %s" % host,
                            "dropped_other_hosts": dropped}
    return rep


def compare(audit, cli):
    human = {c["id"]: c for c in audit["checks"]}
    rows = []
    for c in cli["checks"]:
        h = human.get(c["id"])
        if c["id"].startswith("b.") or not h or h.get("state") != "scored" or c.get("state") != "scored":
            continue
        rows.append({"id": c["id"], "max": c["max"], "human": h["points"], "cli": c["points"]})
    return rows


def common_checks(sites):
    """CLI minus hand per site, each as a share of the points of the checks both of them scored. This is the
    like-for-like difference. The full normalised scores also differ because the hand audits score three
    judgement checks that the CLI leaves out of its denominator."""
    d = [s["common_checks_cli_pct"] - s["common_checks_human_pct"] for s in sites
         if s["common_checks_cli_pct"] is not None and s["common_checks_human_pct"] is not None]
    if not d:
        return None
    mean = statistics.mean(d)
    sd = statistics.stdev(d) if len(d) > 1 else 0.0
    return {"what": "per site, common_checks_cli_pct minus common_checks_human_pct",
            "n": len(d), "mean": round(mean, 1), "min": min(d), "max": max(d),
            "mean_abs": round(statistics.mean(abs(x) for x in d), 1),
            # bias and 95% limits of agreement; with n this small the limits are themselves very uncertain
            "bland_altman": {"label": "n=%d" % len(d), "n": len(d), "bias": round(mean, 1), "sd": round(sd, 1),
                             "loa_95": [round(mean - 1.96 * sd, 1), round(mean + 1.96 * sd, 1)]}}


def validation_set(audits):
    """What the comparison ran on, read from the audit files, so nobody mistakes it for a held-out test."""
    cal = io.open(os.path.join(ROOT, "rubric", "calibration-v1.1.md"), encoding="utf-8").read()
    langs = {}
    for a in audits:
        k = a.get("audience_language") or "und"
        langs[k] = langs.get(k, 0) + 1
    scores = [a["normalised"] for a in audits]

    def host(a):
        h = urllib.parse.urlsplit(a["target"]).netloc.lower()
        return h[4:] if h.startswith("www.") else h
    return {"n": len(audits),
            # sites whose v1.0 audits failed calibration and shaped v1.1: development data by construction
            "calibration_sites": sum(1 for a in audits if "| %s |" % host(a) in cal),
            "held_out": False,
            "hand_score_range": [min(scores), max(scores)] if scores else None,
            "audience_languages": dict(sorted(langs.items())),
            "gate_capped": sum(1 for a in audits if a.get("gate_capped")),
            # the audit format has no rater field: who scored, and whether they saw CLI output, is not recorded
            "rater_recorded": sum(1 for a in audits if a.get("rater"))}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sites, pairs, audits = [], [], []
    for fp in sorted(glob.glob(os.path.join(ROOT, "examples", "audits", "v1.1", "*.json"))):
        audit = json.load(io.open(fp, encoding="utf-8"))
        audits.append(audit)
        name = os.path.basename(fp)[:-5]
        print("re-scoring %s on %d pinned pages…" % (name, len(audit["sampled_urls"])), file=sys.stderr)
        cli = rescore(audit)
        with io.open(os.path.join(OUT_DIR, name + ".cli.json"), "w", encoding="utf-8") as f:
            json.dump(cli, f, ensure_ascii=False, indent=1)
        rows = compare(audit, cli)
        pairs += [dict(r, site=name) for r in rows]
        common_h = sum(r["human"] for r in rows); common_c = sum(r["cli"] for r in rows)
        common_max = sum(r["max"] for r in rows)
        sites.append({
            "site": name, "audited_at": audit["audited_at"],
            "human_normalised": audit["normalised"], "cli_normalised": cli["normalised"],
            "difference": cli["normalised"] - audit["normalised"],
            "pages_compared": len(cli["sampled_urls"]),
            "pages_dropped_other_host": len(cli["validity_note"]["dropped_other_hosts"]),
            "checks_compared": len(rows),
            "common_checks_human_pct": round(100 * common_h / common_max) if common_max else None,
            "common_checks_cli_pct": round(100 * common_c / common_max) if common_max else None,
            "tiers_equal": sum(1 for r in rows if r["human"] == r["cli"]),
        })
    per_check = []
    for cid in [c[0] for c in gs.SPEC]:
        ps = [p for p in pairs if p["id"] == cid]
        if not ps:
            per_check.append({"id": cid, "n": 0, "note": "not compared: the CLI does not score it"
                              if cid in JUDGEMENT else "not compared: unobservable in every pair"})
            continue
        diffs = [p["cli"] - p["human"] for p in ps]
        per_check.append({
            "id": cid, "n": len(ps), "max": ps[0]["max"],
            "exact_agreement": round(sum(1 for d in diffs if d == 0) / len(ps), 2),
            "mean_signed_diff": round(statistics.mean(diffs), 2),
            "kappa": "n too small" if len(ps) < 10 else None,
            "disagreements": [{"site": p["site"], "human": p["human"], "cli": p["cli"]}
                              for p in ps if p["human"] != p["cli"]],
        })
    d = [s["difference"] for s in sites]
    groups = {}
    for g, ids in METHOD.items():
        ps = [p for p in pairs if p["id"] in ids]
        groups[g] = {"checks": len(ids), "n_pairs": len(ps),
                     "exact_agreement": round(sum(1 for p in ps if p["human"] == p["cli"]) / len(ps), 2) if ps else None}
    groups["judgement"] = {"checks": len(JUDGEMENT), "n_pairs": 0, "exact_agreement": None}
    out = {
        "measured_at": datetime.date.today().isoformat(),
        "tool": "geo-score-cli/%s" % gs.__version__, "rubric": gs.RUBRIC,
        "n_sites": len(sites), "n_check_pairs": len(pairs),
        "exact_tier_agreement": round(sum(1 for p in pairs if p["human"] == p["cli"]) / len(pairs), 2) if pairs else None,
        "normalised_difference": {"mean": round(statistics.mean(d), 1), "min": min(d), "max": max(d)} if d else None,
        "common_checks": common_checks(sites),
        "validation_set": validation_set(audits),
        "caveats": [
            "n=%d sites, each hand-scored once by one auditor; this is a first measurement, not a validation study" % len(sites),
            "the hand audits are dated; the CLI re-scored the live pages later, so site changes are inside every difference",
            "the CLI samples only the audited host; hand-sampled pages on other hosts were dropped",
            "the three judgement checks (%s) are never scored by the CLI and are not compared; p4.cn-engines is "
            "compared only where both the CLI and the auditor scored it" % ", ".join(JUDGEMENT),
        ],
        "by_method": groups, "sites": sites, "per_check": per_check,
    }
    with io.open(os.path.join(HERE, "validity.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    write_md(out)
    print(json.dumps({k: out[k] for k in ("n_sites", "n_check_pairs", "exact_tier_agreement", "normalised_difference",
                                          "common_checks")}))
    for s in sites:
        print("%-16s human %3d  cli %3d  diff %+3d  tiers equal %d/%d  common checks human %s%% cli %s%%" % (
            s["site"], s["human_normalised"], s["cli_normalised"], s["difference"], s["tiers_equal"],
            s["checks_compared"], s["common_checks_human_pct"], s["common_checks_cli_pct"]))


def pct(x):
    return "—" if x is None else "%d%%" % round(100 * x)


def moved(x, lang):
    """A signed difference in words: '6 lower', '9 higher' / '低 6 分', '高 9 分'."""
    if x == 0:
        return "no different" if lang == "en" else "持平"
    if lang == "en":
        return "%d %s" % (abs(x), "lower" if x < 0 else "higher")
    return "%s %d 分" % ("低" if x < 0 else "高", abs(x))


def set_caveats(vs, lang):
    """What the validation set is and is not, in both languages, from validity.json's validation_set."""
    if not vs:
        return []
    lo, hi = vs["hand_score_range"]
    zh_n = sum(n for k, n in vs["audience_languages"].items() if k.startswith("zh"))
    dev = vs["calibration_sites"] == vs["n"]
    if lang == "en":
        return ((["the %d sites are the ones whose v1.0 audits calibrated v1.1 ([calibration record]"
                  "(../rubric/calibration-v1.1.md)), so this is development data, not a held-out set" % vs["n"]]
                 if dev else [])
                + ["the hand scores run from %d to %d; %d of the %d sites %s Chinese-language and %d %s gate-capped, "
                   "so low-scoring and capped sites are not represented"
                   % (lo, hi, zh_n, vs["n"], "is" if zh_n == 1 else "are", vs["gate_capped"],
                      "is" if vs["gate_capped"] == 1 else "are")]
                + (["the audit files do not record who scored them, or whether the scorer had seen the CLI's output"]
                   if vs["rater_recorded"] < vs["n"] else []))
    return ((["这 %d 个站正是当初用 v1.0 审计来校准 v1.1 的那几个站（[校准记录](../rubric/calibration-v1.1.zh-CN.md)），"
              "所以这是开发数据，不是留出的检验集" % vs["n"]] if dev else [])
            + ["%d 个站的人工分都在 %d 到 %d 之间，其中 %d 个是中文站，%d 个被门槛封顶，所以低分站和被封顶的站都没有代表"
               % (vs["n"], lo, hi, zh_n, vs["gate_capped"])]
            + (["审计文件没有记录是谁打的分，也没有记录打分的人是否看过 CLI 的输出"]
               if vs["rater_recorded"] < vs["n"] else []))


def headline(v, lang):
    """The score-difference bullets. The like-for-like figure on the checks both scored leads; the
    full-denominator figure follows, with the reason the two differ."""
    nd, cc = v["normalised_difference"], v.get("common_checks")
    judge = [c["id"] for c in v["per_check"] if not c["n"] and "does not score" in c.get("note", "")]
    if lang == "en":
        full = ("**%s %.1f points %s on average**, ranging from %s to %s."
                % ("On the full normalised score the CLI read" if cc else "The CLI's normalised score was",
                   abs(nd["mean"]), "lower" if nd["mean"] < 0 else "higher", moved(nd["min"], "en"), moved(nd["max"], "en")))
        if not cc:
            return ["- " + full]
        ba = cc["bland_altman"]
        return ["- **On the checks both of them scored, the CLI read %.1f points %s on average.** Per site, the CLI's "
                "share of those checks' points minus the auditor's ranged from %s to %s (mean absolute difference "
                "%.1f). Bland-Altman (%s): bias %+.1f, 95%% limits of agreement %+.1f to %+.1f."
                % (abs(cc["mean"]), "lower" if cc["mean"] < 0 else "higher", moved(cc["min"], "en"),
                   moved(cc["max"], "en"), cc["mean_abs"], ba["label"], ba["bias"], ba["loa_95"][0], ba["loa_95"][1]),
                "- " + full + " The two figures differ because the auditor also scored %s, which the CLI leaves out "
                "of its denominator." % (", ".join(judge[:-1]) + " and " + judge[-1])]
    full = ("**%s平均%s %.1f 分**，范围从%s到%s。"
            % ("按完整的归一化分算，CLI " if cc else "CLI 的归一化分", "低" if nd["mean"] < 0 else "高", abs(nd["mean"]),
               moved(nd["min"], "zh"), moved(nd["max"], "zh")))
    if not cc:
        return ["- " + full]
    ba = cc["bland_altman"]
    return ["- **只看两边都打了分的检查项，CLI 平均%s %.1f 分。** 逐站看，CLI 在这些检查项上的得分率减去审计者的，"
            "范围从%s到%s（平均绝对差 %.1f 分）。Bland-Altman（%s）：偏差 %+.1f，95%% 一致性界限 %+.1f 到 %+.1f。"
            % ("低" if cc["mean"] < 0 else "高", abs(cc["mean"]), moved(cc["min"], "zh"), moved(cc["max"], "zh"),
               cc["mean_abs"], ba["label"], ba["bias"], ba["loa_95"][0], ba["loa_95"][1]),
            "- " + full + "两个数不同，是因为审计者还给 %s 打了分，而 CLI 把这 %d 项退出了分母。" % ("、".join(judge), len(judge))]


def write_md(v):
    """VALIDITY.md and VALIDITY.zh-CN.md are generated from validity.json, so the prose cannot drift."""
    by = v["by_method"]
    names = {c[0]: c[2] for c in gs.SPEC}
    def per_check_rows(lang):
        rows = []
        for c in v["per_check"]:
            if not c["n"]:
                note = c["note"] if lang == "en" else ("CLI 不打分，未比较" if "does not score" in c["note"] else "每一对都测不到，未比较")
                rows.append("| `%s` | %s | — | — | — | %s |" % (c["id"], names[c["id"]], note))
                continue
            dis = ", ".join("%s %d→%d" % (x["site"], x["human"], x["cli"]) for x in c["disagreements"]) or ("none" if lang == "en" else "无")
            rows.append("| `%s` | %s | %d | %s | %+.1f | %s |" % (c["id"], names[c["id"]], c["n"], pct(c["exact_agreement"]),
                                                               c["mean_signed_diff"], dis))
        return rows
    site_rows = ["| %s | %s | %d | %d | %+d | %d/%d | %d |" % (s["site"], s["audited_at"], s["human_normalised"],
                 s["cli_normalised"], s["difference"], s["tiers_equal"], s["checks_compared"], s["pages_compared"])
                 for s in v["sites"]]
    en = ["# CLI versus hand audit",
          "",
          "Generated by `benchmark/validity.py` on %s with %s (rubric %s). Do not edit by hand; re-run the script."
          % (v["measured_at"], v["tool"], v["rubric"]),
          "中文版：[VALIDITY.zh-CN.md](VALIDITY.zh-CN.md)",
          "",
          "## What was measured",
          "",
          "Each of the %d published hand audits in [examples/audits/v1.1](../examples/audits/v1.1/) was re-scored by the CLI "
          "on the same pages (`--urls` pinned to the audit's `sampled_urls`), and every check both of them scored was "
          "compared tier for tier: %d check pairs." % (v["n_sites"], v["n_check_pairs"]),
          "",
          "This compares the CLI with a human reading of the same rubric. Whether the readiness score goes with being "
          "cited is a separate question, set out before any data in the "
          "[preregistered validation plan](PREREGISTRATION.md).",
          "",
          "## Result",
          ""] + headline(v, "en") + [
          "- **Same tier on %s of check pairs.** Checks read by rule agreed on %s (%d pairs); checks the CLI approximates "
          "with a heuristic agreed on %s (%d pairs). The %d judgement checks are never scored by the CLI."
          % (pct(v["exact_tier_agreement"]), pct(by["rule"]["exact_agreement"]), by["rule"]["n_pairs"],
             pct(by["heuristic"]["exact_agreement"]), by["heuristic"]["n_pairs"], by["judgement"]["checks"]),
          "",
          "## Read this before quoting it",
          ""] + ["- %s%s." % (x[0].upper(), x[1:]) for x in v["caveats"] + set_caveats(v.get("validation_set"), "en")] + [
          "",
          "## By site",
          "",
          "| Site | Hand audit | Hand score | CLI score | Difference | Same tier | Pages |",
          "|---|---|--:|--:|--:|--:|--:|"] + site_rows + [
          "",
          "## By check",
          "",
          "| Check | Name | Pairs | Same tier | Mean CLI − hand | Disagreements (hand→CLI) |",
          "|---|---|--:|--:|--:|---|"] + per_check_rows("en") + [
          "",
          "A negative mean means the CLI scores the check lower than the auditor did. Kappa is not reported: "
          "with fewer than 10 pairs per check it would not mean anything.",
          ""]
    cav_zh = ["样本只有 %d 个站，每个站由一位审计者人工打分一次；这是第一次测量，不是效度研究" % v["n_sites"],
              "人工审计有日期，CLI 是之后在线重评的，所以每一处差异里都混有网站自身的变化",
              "CLI 只在被审计的域名内抽样，人工抽到的其他域名页面没有参与比较",
              "三个需要判断的检查项 CLI 从不打分，不在比较之内；p4.cn-engines 只在 CLI 和审计者都打了分时才比较"]
    zh = ["# CLI 与人工审计的一致程度",
          "",
          "由 `benchmark/validity.py` 于 %s 用 %s（量表 %s）生成。请勿手改，重跑脚本即可。" % (v["measured_at"], v["tool"], v["rubric"]),
          "English: [VALIDITY.md](VALIDITY.md)",
          "",
          "## 测了什么",
          "",
          "[examples/audits/v1.1](../examples/audits/v1.1/) 里公开的 %d 份人工审计，逐一用 CLI 在相同页面上重评"
          "（`--urls` 固定为审计的 `sampled_urls`），两边都打了分的检查项逐档比较，共 %d 对。" % (v["n_sites"], v["n_check_pairs"]),
          "",
          "这里比较的是 CLI 与人工按同一量表的读数。就绪度分数和被不被引用有没有关系是另一个问题，"
          "在收集任何数据之前写定在[预注册的验证方案](PREREGISTRATION.zh-CN.md)里。",
          "",
          "## 结果",
          ""] + headline(v, "zh") + [
          "- **%s 的检查项两边档位完全一致。** 按规则读取的检查项一致率 %s（%d 对）；CLI 用启发式近似的检查项一致率 %s（%d 对）。"
          "%d 个需要判断的检查项 CLI 从不打分。"
          % (pct(v["exact_tier_agreement"]), pct(by["rule"]["exact_agreement"]), by["rule"]["n_pairs"],
             pct(by["heuristic"]["exact_agreement"]), by["heuristic"]["n_pairs"], by["judgement"]["checks"]),
          "",
          "## 引用之前先读这几条",
          ""] + ["- %s。" % x for x in cav_zh + set_caveats(v.get("validation_set"), "zh")] + [
          "",
          "## 按站点",
          "",
          "| 站点 | 人工审计日期 | 人工分 | CLI 分 | 差值 | 档位一致 | 页面数 |",
          "|---|---|--:|--:|--:|--:|--:|"] + site_rows + [
          "",
          "## 按检查项",
          "",
          "| 检查项 | 名称 | 对数 | 档位一致 | CLI − 人工 平均 | 分歧（人工→CLI） |",
          "|---|---|--:|--:|--:|---|"] + per_check_rows("zh") + [
          "",
          "平均值为负，表示 CLI 在这一项上打得比审计者低。不报告 kappa：每项不足 10 对时它没有意义。",
          ""]
    for fn, lines in (("VALIDITY.md", en), ("VALIDITY.zh-CN.md", zh)):
        with io.open(os.path.join(HERE, fn), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


if __name__ == "__main__":
    if sys.argv[1:] == ["--md-only"]:
        write_md(json.load(io.open(os.path.join(HERE, "validity.json"), encoding="utf-8")))
    else:
        main()
