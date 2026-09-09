#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the public leaderboard from benchmark/results.json, in both languages.

    python3 benchmark/build_page.py

Writes docs/index.html (English) and docs/zh.html (Chinese). The page is generated so it
can never drift from the data: add a site to sites.json, run run.py, then run this, and
commit all of it together.
"""
import io, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _page_tpl import TPL

BAND_COL = {"Leading": "var(--green)", "Solid": "var(--green)", "Growing": "var(--dim)",
            "Early": "var(--amber)", "Not started": "var(--red)", "Not scored": "var(--mute)"}
BAND_ZH = {"Leading": "领先", "Solid": "基础扎实", "Growing": "成长期",
           "Early": "起步期", "Not started": "未起步", "Not scored": "未打分"}

REPO = "https://github.com/jianruntech/geo-score"
SITE = "https://jianruntech.github.io/geo-score"

def _fmt(x):
    """同理：中位数与上四分位数是整数时不要印小数点。"""
    return int(x) if float(x).is_integer() else x


def jsonld(lang, v):
    """The leaderboard is a dataset. Saying so is the single highest-leverage thing
    this page can do to be cited — engines treat a declared Dataset very differently
    from an undeclared table."""
    page = SITE + ("/" if lang == "en" else "/zh.html")
    zh = lang == "zh"
    return json.dumps({"@context": "https://schema.org", "@graph": [
      {"@type": "Organization", "@id": SITE + "/#org", "name": "见润科技" if zh else "Jianrun Tech",
       "alternateName": ["Jianrun Tech", "见润科技"], "url": "https://www.jianruntech.com/",
       "logo": "https://www.jianruntech.com/icon-192.png",
       "sameAs": [REPO, "https://www.jianruntech.com/"]},
      {"@type": "Person", "@id": SITE + "/#author", "name": "多祝" if zh else "Duozhu",
       "affiliation": {"@id": SITE + "/#org"}, "url": "https://www.jianruntech.com/"},
      {"@type": "Dataset", "@id": page + "#dataset",
       "name": ("AI 可见度公开基准：%d 个站点的实测评分" % v["n"]) if zh
               else "The state of AI visibility: %d sites scored" % v["n"],
       "description": (
         "用同一套开源口径（AIV 量表 v1.1，21 项阶梯式检查）对 %d 个知名网站实测的 AI 可见度评分，"
         "含分行业中位数、门槛失效归因与逐站最大缺口。中位数 %s，区间 %d–%d。" % (v["n"], v["med"], v["mn"], v["mx"])
         if zh else
         "AI answer-engine readiness scores for %d well-known websites, measured with one open "
         "rubric (AIV v1.1, 21 tiered checks) and one public tool. Includes sector medians, "
         "gate-failure attribution and each site's largest gaps. Median %s, range %d-%d."
         % (v["n"], v["med"], v["mn"], v["mx"])),
       "url": page, "license": "https://opensource.org/licenses/MIT",
       "isAccessibleForFree": True, "dateModified": v["date"], "datePublished": v["date"],
       "creator": {"@id": SITE + "/#org"}, "author": {"@id": SITE + "/#author"},
       "publisher": {"@id": SITE + "/#org"},
       "inLanguage": "zh-CN" if zh else "en",
       "keywords": ["generative engine optimization", "GEO", "AEO", "AI search visibility",
                    "llms.txt", "structured data", "AI crawlers"],
       "measurementTechnique": ("AIV rubric v1.1 — 21 tiered checks over an 8-page sample, "
                                "10 retrieval user-agents probed live"),
       "variableMeasured": [
         {"@type": "PropertyValue", "name": "readiness", "description": "0-100 normalised score"},
         {"@type": "PropertyValue", "name": "band", "description": "Not started / Early / Growing / Solid / Leading"},
         {"@type": "PropertyValue", "name": "gate_capped", "description": "whether a retrieval crawler can reach the content at all"}],
       "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json",
                         "contentUrl": REPO + "/blob/main/benchmark/results.json"}],
       "citation": REPO + "/blob/main/rubric/v1.1.md"},
      {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/",
       "name": "geo-score", "publisher": {"@id": SITE + "/#org"}},
      {"@type": "WebPage", "@id": page + "#webpage", "url": page,
       "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": page + "#dataset"},
       "author": {"@id": SITE + "/#author"}, "dateModified": v["date"],
       "inLanguage": "zh-CN" if zh else "en"}]}, ensure_ascii=False, separators=(",", ":"))

def strings(lang, v):
    """All page copy. Both languages say the same things — if you change one, change both."""
    if lang == "en":
        return dict(
            htmllang="en", on_en="on", on_zh="",
            canon="https://jianruntech.github.io/geo-score/", oglocale="en_US",
            ogimg="https://jianruntech.github.io/geo-score/og.png",
            ogalt="Share card: %(cappct)d%% of %(n)d well-known sites cannot be cited by an AI "
                   "answer engine at all. Median %(med)s, range %(mn)d-%(mx)d." % v,
            t_title="The state of AI visibility — %(n)d sites scored" % v,
            t_desc="%(n)d well-known sites scored on whether AI answer engines can find, parse, "
                   "trust and cite them. Open rubric, reproducible, median %(med)s." % v,
            t_ogtitle="The state of AI visibility",
            t_ogdesc="A quarter of %(n)d well-known sites cannot be cited by an AI answer engine "
                     "at all. Open rubric, one command, reproducible." % v,
            t_h1="The state of<br>AI visibility",
            t_sub="%(n)d well-known sites, scored on whether an AI answer engine can find, parse, "
                  "trust and cite them. One open rubric, one public tool, the same eight-page "
                  'sample for every site. Nothing here is a black box — <a href="%(repo)s">'
                  "re-run it yourself</a>." % dict(v, repo=REPO),
            l_sites="SITES", l_median="MEDIAN", l_uq="UPPER QUARTILE", l_range="RANGE",
            l_cap="CANNOT BE CITED",
            t_h2gate="A quarter of the field cannot be cited at all",
            t_pgate="%(cap)d sites have a gate check at zero — a retrieval crawler cannot get the "
                    "content, so nothing else on the page matters. Two very different problems "
                    "live inside that number." % v,
            l_delib="DELIBERATE", l_accid="ACCIDENTAL",
            t_delib="Their <code>robots.txt</code> disallows AI retrieval crawlers by name. A site "
                    "that does not want to be quoted is not misconfigured, and this rubric reports "
                    "it as it is.",
            t_accid="Body copy only exists after JavaScript runs. The content is there and a browser "
                    "sees it; a retrieval crawler gets an empty shell. This group almost certainly "
                    "did not choose it.",
            t_china="<b>Sites built for the Chinese market score %(gap)d points lower</b> — median "
                    "%(cn)s against %(row)s for everyone else. The gap is not content quality. It is "
                    "<code>llms.txt</code>, <code>Organization</code> schema, visible dates and real "
                    "bylines — conventions that spread through the English web first and have not "
                    "crossed over." % v,
            t_h2dist="Where everyone lands",
            t_pdist="Bars are counts of sites per ten-point band. The rubric is not graded on a "
                    "curve; this is the distribution that falls out of it.",
            t_h2check="Check your own site",
            t_pcheck="No install, no dependencies, no account. Python 3.8+ and about twenty seconds.",
            t_flags='Add <code style="color:var(--brass)">--explain</code> for the evidence behind '
                    "every check and what the next tier asks for, or "
                    '<code style="color:var(--brass)">--compare competitor.com</code> to see the two '
                    "side by side.",
            t_h2all="Every site",
            t_pall="Click a column to sort. The score is <em>readiness</em> — whether an engine "
                   "<em>can</em> cite the site, not whether one does.",
            l_search="Find a site or sector…", l_allsec="All sectors", l_allsites="All sites",
            l_fcap="Cannot be cited", l_ftop="Solid or better", l_flow="Below 50",
            l_site="SITE", l_score="SCORE", l_band="BAND", l_sector="SECTOR",
            l_gaps="BIGGEST GAPS", l_pill="NOT CITABLE",
            l_count='"{a} of {b} sites"',
            t_h2sec="By sector",
            t_footer='Scored with <a href="%(repo)s/blob/main/rubric/v1.1.md">AIV rubric v1.1</a> on '
                     '%(date)s · <a href="%(repo)s/blob/main/benchmark/results.json">raw data</a> · '
                     '<a href="%(repo)s/blob/main/benchmark/run.py">the script</a> · '
                     '<a href="%(repo)s/blob/main/benchmark/REPRODUCIBILITY.md">how reproducible a single run is</a> · '
                     '<a href="%(repo)s">the repository</a><br><br>'
                     "We ran the whole benchmark twice and compared every site: <strong>96%% of sites land within &plusmn;5</strong> and 45%% land identically, so read one site's number as &plusmn;5 rather than as exact. Medians are stable. The unstable part is the gate checks &mdash; five sites flipped because their bot protection answered a crawler differently between the two runs, which is a property of those sites rather than of the measurement. "
                     "This measures readiness, not outcomes: whether an engine <em>can</em> cite a "
                     "site. Whether one <em>does</em> depends on competition and query intent, which "
                     "no site-side audit can observe. Four checks needing off-site search are left "
                     "out of the denominator rather than guessed, so these run lower than a "
                     "hand-scored audit. Sites change; every number carries the date it was "
                     'measured.<br><br>Built by <a href="https://www.jianruntech.com">Jianrun Tech</a>. MIT.'
                     % dict(v, repo=REPO))
    return dict(
        htmllang="zh-CN", on_en="", on_zh="on",
        canon="https://jianruntech.github.io/geo-score/zh.html", oglocale="zh_CN",
        ogimg="https://jianruntech.github.io/geo-score/og.zh.png",
        ogalt="分享卡：%(n)d 个知名网站里 %(cappct)d%% 根本无法被 AI 回答引擎引用，"
              "中位数 %(med)s，区间 %(mn)d-%(mx)d。" % v,
        t_title="AI 可见度现状 — %(n)d 个站点实测" % v,
        t_desc="%(n)d 个知名网站的实测评分，衡量 AI 回答引擎能不能找到、读懂、信任并引用它们。"
               "口径公开、结果可复现，中位数 %(med)s。" % v,
        t_ogtitle="AI 可见度现状",
        t_ogdesc="%(n)d 个知名网站里，四分之一根本无法被 AI 回答引擎引用。"
                 "口径公开，一行命令，结果可复现。" % v,
        t_h1="AI 可见度<br>现状",
        t_sub="%(n)d 个知名网站，实测 AI 回答引擎能不能找到、读懂、信任并引用它们。"
              "同一套公开口径、同一个公开工具、每个站同样抽 8 个页面。"
              '这里没有黑箱——<a href="%(repo)s">你可以自己重跑</a>。' % dict(v, repo=REPO),
        l_sites="站点数", l_median="中位数", l_uq="上四分位", l_range="区间",
        l_cap="无法被引用",
        t_h2gate="四分之一的站根本无法被引用",
        t_pgate="%(cap)d 个站有门槛项得 0 分——检索爬虫压根拿不到内容，"
                "页面上其余的事都不再重要。而这个数字里装着两件性质完全不同的事。" % v,
        l_delib="主动屏蔽", l_accid="无意失效",
        t_delib="它们的 <code>robots.txt</code> 点名禁止了 AI 检索爬虫。"
                "一个不希望被引用的站不是配置错了，量表照实记录即可。",
        t_accid="正文只在 JavaScript 跑完之后才存在。内容是有的，浏览器看得见；"
                "检索爬虫拿到的是一个空壳。这一组几乎肯定不是有意的。",
        t_china="<b>面向中文市场的站比其余站低 %(gap)d 分</b>——中位数 %(cn)s 对 %(row)s。"
                "差的不是内容质量，是 <code>llms.txt</code>、<code>Organization</code> 结构化数据、"
                "页面上的可见日期、文章署名到人——这些约定先在英文网络里扩散，还没有传过来。" % v,
        t_h2dist="大家都落在哪",
        t_pdist="每根柱子是该十分段内的站点数。这套口径不按曲线给分，这就是它跑出来的分布。",
        t_h2check="测测你自己的站",
        t_pcheck="不用装、无依赖、不用注册。Python 3.8+，大约二十秒。",
        t_flags='加 <code style="color:var(--brass)">--explain</code> 看每一项背后的证据'
                '与上一档的要求，或 <code style="color:var(--brass)">--compare competitor.com</code> '
                "和竞品并排比。",
        t_h2all="全部站点",
        t_pall="点列头排序。分数是<em>就绪度</em>——引擎<em>能不能</em>引用你，不是它有没有引用你。",
        l_search="搜站点或行业…", l_allsec="全部行业", l_allsites="全部站点",
        l_fcap="无法被引用", l_ftop="基础扎实及以上", l_flow="低于 50 分",
        l_site="站点", l_score="分数", l_band="档", l_sector="行业",
        l_gaps="最大缺口", l_pill="无法引用",
        l_count='"共 {b} 个，当前显示 {a} 个"',
        t_h2sec="分行业",
        t_footer='按 <a href="%(repo)s/blob/main/rubric/v1.1.zh-CN.md">AIV 量表 v1.1</a> 于 '
                 '%(date)s 实测 · <a href="%(repo)s/blob/main/benchmark/results.json">原始数据</a> · '
                 '<a href="%(repo)s/blob/main/benchmark/run.py">跑分脚本</a> · '
                 '<a href="%(repo)s/blob/main/benchmark/REPRODUCIBILITY.md">单次重跑的精度</a> · '
                 '<a href="%(repo)s">仓库</a><br><br>'
                 "整个榜单我们跑了两遍并逐站比对：<strong>96%% 的站落在 &plusmn;5 以内</strong>，45%% 完全一致。所以单个站的分数请按 &plusmn;5 读，不要当成精确值；中位数是稳的。不稳的是门槛检查——两次之间有五个站翻转，因为它们的 bot 防护对爬虫的答复变了，那是那些站点的属性，不是测量的毛病。"
                 "这里测的是就绪度，不是结果：引擎<em>能不能</em>引用一个站。"
                 "它<em>会不会</em>引用，取决于竞争与提问意图，任何站外审计都观察不到。"
                 "四项需要站外检索的检查退出了分母而不是靠猜，所以这些分比人工逐项审计略低。"
                 "站点会变；每个数字都带着它被测量的日期。"
                 '<br><br>由<a href="https://www.jianruntech.com">见润科技</a>构建。MIT 许可。'
                 % dict(v, repo=REPO))

def data():
    d = json.load(io.open(os.path.join(HERE, "results.json"), encoding="utf-8"))
    ok = [r for r in d["results"] if "error" not in r]
    err = [r for r in d["results"] if "error" in r]
    s = d["stats"]
    cap = [r for r in ok if r.get("gate_capped")]
    blk = sorted(r["site"] for r in cap if r.get("gate_reason") == "blocks crawlers")
    js = sorted(r["site"] for r in cap if r.get("gate_reason") == "content needs JavaScript")
    def _med(xs):
        """statistics.median 在样本数为偶数时返回浮点，页面上会印成「60.0」。
        整数就按整数印。"""
        m = st.median(xs)
        return int(m) if float(m).is_integer() else m
    cn = _med([r["normalised"] for r in ok if r["sector"].startswith("China")])
    row = _med([r["normalised"] for r in ok if not r["sector"].startswith("China")])
    sec = sorted(d["sectors"].items(), key=lambda kv: -kv[1]["median"])
    bins = [0] * 10
    for r in ok:
        bins[min(9, r["normalised"] // 10)] += 1
    rows = [dict(s=r["site"], n=r["normalised"], b=r["band"], k=r["sector"],
                 c=bool(r.get("gate_capped")), w=r.get("gate_reason") or "",
                 g=r.get("top_gaps", []), r=r["readiness"], m=r["observable_max"]) for r in ok]
    rows += [dict(s=r["site"], n=None, b="Not scored", k=r["sector"], c=False,
                  w=r.get("error", ""), g=[], r=None, m=None) for r in err]
    return dict(
        n=s["n"], med=_fmt(s["median"]), p75=_fmt(s["p75"]), mn=s["min"], mx=s["max"], cap=len(cap),
        cappct=int(round(100.0 * len(cap) / s["n"])),
        nerr=sum(1 for r in cap if r.get("gate_reason") == "serves crawlers an error"),
        nblk=len(blk), njs=len(js), blk=", ".join(blk), js=", ".join(js),
        gap=round(row - cn), cn=cn, row=row, date=d["measured_at"],
        css=io.open(os.path.join(HERE, "page.css"), encoding="utf-8").read(),
        bandcol=json.dumps(BAND_COL), bandmap=json.dumps(BAND_ZH, ensure_ascii=False),
        hist="".join('<div class="%s" style="height:%d%%"><span>%s</span></div>'
                     % ("hot" if v == max(bins) else "", max(3, round(100 * v / max(bins))), v or "")
                     for v in bins),
        histx="".join("<div>%d</div>" % (i * 10) for i in range(10)),
        secopts="".join("<option>%s</option>" % k for k, _ in sec),
        sectbl="".join('<tr><td>%s</td><td class="num">%d</td>'
                       '<td class="num" style="color:var(--green)">%s</td>'
                       '<td class="bar"><i style="width:%d%%"></i></td></tr>'
                       % (k, v["n"], v["median"], v["median"]) for k, v in sec),
        data=json.dumps(rows, ensure_ascii=False, separators=(",", ":")))

LLMS = """# geo-score

> An open, versioned rubric for Generative Engine Optimization \u2014 score any site 0\u2013100
> on whether AI answer engines can find, parse, trust and cite it. MIT licensed,
> machine-readable, with a zero-dependency Python CLI and a public benchmark of %(n)d
> well-known sites.

The rubric it publishes is the AIV score: 21 tiered checks totalling 100 points, plus
4 bonus checks worth up to +6 outside the denominator. Every tier states a count out of
the 8 sampled pages, so two people scoring the same site agree on the arithmetic.
Three checks are gates \u2014 score zero on crawler access, live reachability or
server-rendered content and the result caps at 40.

## The benchmark

- [The state of AI visibility](https://jianruntech.github.io/geo-score/): %(n)d well-known sites scored. Median %(med)s, range %(mn)d\u2013%(mx)d. %(cappct)d%% of them cannot be cited at all \u2014 %(nblk)d block AI crawlers by name, %(njs)d serve a page whose body only exists after JavaScript runs, %(nerr)d hand a crawler an outright error.
- [\u7b80\u4f53\u4e2d\u6587\u7248](https://jianruntech.github.io/geo-score/zh.html): the same data and findings in Chinese.
- [Raw data](https://github.com/jianruntech/geo-score/blob/main/benchmark/results.json): every site, every score, machine-readable.

## The rubric

- [AIV rubric v1.1](https://github.com/jianruntech/geo-score/blob/main/rubric/v1.1.md): the full specification, tier by tier.
- [\u7b80\u4f53\u4e2d\u6587](https://github.com/jianruntech/geo-score/blob/main/rubric/v1.1.zh-CN.md): the same specification in Chinese.
- [Machine-readable rubric](https://github.com/jianruntech/geo-score/blob/main/rubric/v1.1.json): stable check ids, tier conditions, bands.
- [Report schema](https://github.com/jianruntech/geo-score/blob/main/schema/report.v2.json): emit this and results from different implementations are comparable.
- [Calibration record](https://github.com/jianruntech/geo-score/blob/main/rubric/calibration-v1.1.md): how the thresholds were set, against four public benchmarks.

## The tool

- [CLI](https://github.com/jianruntech/geo-score/tree/main/cli): one file, standard library only, Python 3.8+. `curl -sL .../cli/geo_score.py | python3 - yoursite.com`
- [GitHub Action](https://github.com/jianruntech/geo-score/blob/main/action.yml): score on every push, fail the build on regression.
- [Five hand-scored audits](https://github.com/jianruntech/geo-score/tree/main/examples/audits/v1.1): all 21 checks scored by hand with reproducible evidence.

## Scope

This measures readiness \u2014 whether an engine *can* cite a site. Whether one *does*
depends on competition and query intent, which no site-side audit can observe.
Remediation is deliberately out of scope: the rubric names the gap and what the next
tier requires; it does not ship fix templates.

Maintained by [Jianrun Tech](https://www.jianruntech.com) (\u89c1\u6f66\u79d1\u6280), Shenzhen. MIT.
"""

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://jianruntech.github.io/geo-score/</loc>
    <lastmod>%(date)s</lastmod>
    <xhtml:link rel="alternate" hreflang="en" href="https://jianruntech.github.io/geo-score/"/>
    <xhtml:link rel="alternate" hreflang="zh" href="https://jianruntech.github.io/geo-score/zh.html"/>
  </url>
  <url>
    <loc>https://jianruntech.github.io/geo-score/zh.html</loc>
    <lastmod>%(date)s</lastmod>
    <xhtml:link rel="alternate" hreflang="en" href="https://jianruntech.github.io/geo-score/"/>
    <xhtml:link rel="alternate" hreflang="zh" href="https://jianruntech.github.io/geo-score/zh.html"/>
  </url>
</urlset>
"""


if __name__ == "__main__":
    v = data()
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    io.open(os.path.join(ROOT, "docs", ".nojekyll"), "a", encoding="utf-8").close()
    for lang, name in (("en", "index.html"), ("zh", "zh.html")):
        vals = dict(v, **strings(lang, v), jsonld=jsonld(lang, v))
        # bandmap only translates on the Chinese page
        if lang == "en":
            vals["bandmap"] = "{}"
        out = os.path.join(ROOT, "docs", name)
        io.open(out, "w", encoding="utf-8").write(TPL % vals)
        print("wrote docs/%s — %d sites, median %s" % (name, v["n"], v["med"]))
    # llms.txt and sitemap.xml are generated for the same reason the pages are: the
    # numbers in them went stale the moment the benchmark grew, and llms.txt is the
    # one file an AI crawler actually reads — a stale number there is a wrong answer
    # handed to every engine.
    for name, tpl in (("llms.txt", LLMS), ("sitemap.xml", SITEMAP)):
        io.open(os.path.join(ROOT, "docs", name), "w", encoding="utf-8").write(tpl % v)
        print("wrote docs/%s" % name)
