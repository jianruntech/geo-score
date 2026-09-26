#!/usr/bin/env python3
"""How closely does the CLI agree with a hand audit of the same pages?

    python3 benchmark/validity.py          # re-score every hand audit, write validity.json

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


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sites, pairs = [], []
    for fp in sorted(glob.glob(os.path.join(ROOT, "examples", "audits", "v1.1", "*.json"))):
        audit = json.load(io.open(fp, encoding="utf-8"))
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
        "caveats": [
            "n=%d sites, each hand-scored once by one auditor; this is a first measurement, not a validation study" % len(sites),
            "the hand audits are dated; the CLI re-scored the live pages later, so site changes are inside every difference",
            "the CLI samples only the audited host; hand-sampled pages on other hosts were dropped",
            "the four judgement checks (%s) are never scored by the CLI and are not compared" % ", ".join(JUDGEMENT + ["p4.cn-engines where not applicable"]),
        ],
        "by_method": groups, "sites": sites, "per_check": per_check,
    }
    with io.open(os.path.join(HERE, "validity.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    write_md(out)
    print(json.dumps({k: out[k] for k in ("n_sites", "n_check_pairs", "exact_tier_agreement", "normalised_difference")}))
    for s in sites:
        print("%-16s human %3d  cli %3d  diff %+3d  tiers equal %d/%d  common checks human %s%% cli %s%%" % (
            s["site"], s["human_normalised"], s["cli_normalised"], s["difference"], s["tiers_equal"],
            s["checks_compared"], s["common_checks_human_pct"], s["common_checks_cli_pct"]))


def pct(x):
    return "—" if x is None else "%d%%" % round(100 * x)


def write_md(v):
    """VALIDITY.md and VALIDITY.zh-CN.md are generated from validity.json, so the prose cannot drift."""
    nd = v["normalised_difference"]
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
          "## Result",
          "",
          "- **Same tier on %s of check pairs.** Checks read by rule agreed on %s (%d pairs); checks the CLI approximates "
          "with a heuristic agreed on %s (%d pairs). The %d judgement checks are never scored by the CLI."
          % (pct(v["exact_tier_agreement"]), pct(by["rule"]["exact_agreement"]), by["rule"]["n_pairs"],
             pct(by["heuristic"]["exact_agreement"]), by["heuristic"]["n_pairs"], by["judgement"]["checks"]),
          "- **The CLI's normalised score was %.1f points lower on average**, ranging from %d lower to %d %s."
          % (-nd["mean"], -nd["min"], abs(nd["max"]), "higher" if nd["max"] > 0 else "lower"),
          "",
          "## Read this before quoting it",
          ""] + ["- %s%s." % (x[0].upper(), x[1:]) for x in v["caveats"]] + [
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
              "四个需要判断的检查项 CLI 从不打分，不在比较之内"]
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
          "## 结果",
          "",
          "- **%s 的检查项两边档位完全一致。** 按规则读取的检查项一致率 %s（%d 对）；CLI 用启发式近似的检查项一致率 %s（%d 对）。"
          "%d 个需要判断的检查项 CLI 从不打分。"
          % (pct(v["exact_tier_agreement"]), pct(by["rule"]["exact_agreement"]), by["rule"]["n_pairs"],
             pct(by["heuristic"]["exact_agreement"]), by["heuristic"]["n_pairs"], by["judgement"]["checks"]),
          "- **CLI 的归一化分平均低 %.1f 分**，范围从低 %d 分到%s %d 分。"
          % (-nd["mean"], -nd["min"], "高" if nd["max"] > 0 else "低", abs(nd["max"])),
          "",
          "## 引用之前先读这几条",
          ""] + ["- %s。" % x for x in cav_zh] + [
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
