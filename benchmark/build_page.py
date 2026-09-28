#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the public leaderboard from benchmark/results.json, in both languages.

    python3 benchmark/build_page.py

Writes docs/index.html (English) and docs/zh.html (Chinese). The page is generated so it
can never drift from the data: add a site to sites.json, run run.py, then run this, and
commit all of it together.
"""
import io, json, os, re, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from _page_tpl import TPL

BAND_COL = {"Leading": "var(--green)", "Solid": "var(--green)", "Growing": "var(--dim)",
            "Early": "var(--amber)", "Not started": "var(--red)", "Not scored": "var(--mute)"}
BAND_ZH = {"Leading": "领先", "Solid": "基础扎实", "Growing": "成长期",
           "Early": "起步期", "Not started": "未起步", "Not scored": "未打分"}

REPO = "https://github.com/jianruntech/geo-score"
# the page is rebuilt at every release (RELEASING.md step 4), so its downloads point at that release's tag: a file
# at a tag never moves, where a blob/main link moves with every run. The tool version recorded in results.json
# would be the wrong tag, because the data can predate the release that publishes it.
_CLI = io.open(os.path.join(ROOT, "cli", "geo_score.py"), encoding="utf-8").read()
VERSION = re.search(r'^__version__ = "([^"]+)"', _CLI, re.M).group(1)
DOWNLOAD = "https://raw.githubusercontent.com/jianruntech/geo-score/v%s/benchmark/" % VERSION
# the Dataset's data dictionary: each name is a key of every scored row in results.json (validate.py checks it)
VARIABLES = [
    ("normalised", "0-100 percentage: readiness over observable_max, capped at 100, and capped at 40 when a gate "
                   "check scores zero",
     "0–100 的百分比：readiness 除以 observable_max，最高 100；任一门槛项得 0 分时封顶 40"),
    ("readiness", "raw points earned on the observable checks, plus the bonus (at most +6)",
     "在可观测检查项上拿到的原始分，加上加分项（最多 +6）"),
    ("observable_max", "the points the observable checks carry: the denominator, less the checks that could not "
                       "be observed",
     "可观测检查项的满分之和，即分母；观测不到的检查项不计入"),
    ("band", "Not started / Early / Growing / Solid / Leading, from normalised",
     "未起步 / 起步期 / 成长期 / 基础扎实 / 领先，由 normalised 决定"),
    ("gate_capped", "true when a gate check (g.robots, g.reachable or g.ssr) scored zero, which caps normalised at 40",
     "任一门槛项（g.robots、g.reachable 或 g.ssr）得 0 分时为 true，此时 normalised 封顶 40")]
# the maintained mirror. The old GitHub Pages copy stopped updating at 229 sites, and a canonical
# pointing there handed engines the stale numbers.
DEFAULT_SITE = "https://www.jianruntech.com/leaderboard"
# the Chinese page lives at <SITE>/zh; the mirror answers <SITE>/zh.html with a 308 to it
ZH_PATH = "/zh"
# where the pages will be served; canonical, og:url, og:image, hreflang, llms.txt and the sitemap all follow it
SITE = os.environ.get("GEO_SITE_BASE", DEFAULT_SITE).rstrip("/")
# each page's own URL, without a trailing slash: the form the mirror declares canonical and the READMEs link
PAGE = {"en": SITE, "zh": SITE + ZH_PATH}

def _hosted(text):
    """Map any default-host URL a template still spells out onto SITE. The Chinese page has two forms,
    <base>/zh and the <base>/zh.html that redirects to it, and both land on PAGE["zh"]."""
    return text.replace(DEFAULT_SITE + "/zh.html", PAGE["zh"]).replace(DEFAULT_SITE, SITE)

# 1.5.0 took training crawlers and opt-out tokens off the list g.robots scores. Data measured with an older
# tool still counts them as retrieval crawlers, so every label built on it says so until the data is re-run,
# and the qualifier drops out by itself once results.json records 1.5.0 or later.
CRAWLER_FIX = (1, 5, 0)
# 1.5.0 also tells a bot-challenge page from a JavaScript shell: a site that serves a browser user-agent a
# challenge is not scored, where it used to read as g.ssr 0. Older data files such sites under "content needs
# JavaScript", so that group carries its own qualifier on the same terms.
CHALLENGE_FIX = (1, 5, 0)

def old_crawler_reading(tool, fix=CRAWLER_FIX):
    """The version in results.json's tool string ('geo-score-cli/1.3.0' gives '1.3.0') when it predates the
    fix, else None."""
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", tool or "")
    return m.group(0) if m and tuple(int(x) for x in m.groups()) < fix else None

def crawler_note(tool, lang):
    """The qualifier on the robots.txt group ("en", "zh", or "short" for llms.txt), or "" when the data was
    measured with the fixed reading."""
    v = old_crawler_reading(tool)
    if not v:
        return ""
    if lang == "short":
        return ("counted with the %s reading, which treated GPTBot, ClaudeBot and Google-Extended as retrieval "
                "crawlers; fixed in 1.5.0, re-run pending" % v)
    if lang == "en":
        return ("The %s reading counted GPTBot, ClaudeBot and Google-Extended as retrieval crawlers, so this "
                "count includes sites that block only training crawlers or an opt-out token (fixed in 1.5.0, "
                "re-run pending)." % v)
    return ("%s 版的读法把 GPTBot、ClaudeBot 和 Google-Extended 也算作检索爬虫，所以这个数里包括只屏蔽训练爬虫"
            "或只声明退出令牌的站（1.5.0 已修正，榜单待重跑）。" % v)

def challenge_note(tool, lang):
    """The qualifier on the "content needs JavaScript" group ("en", "zh", or "short" for llms.txt), or "" when
    the data was measured with a tool that tells bot challenges apart."""
    v = old_crawler_reading(tool, CHALLENGE_FIX)
    if not v:
        return ""
    if lang == "short":
        return ("counted with the %s reading, which could not tell a bot-challenge page from a JavaScript shell; "
                "fixed in 1.5.0, re-run pending" % v)
    if lang == "en":
        return ("The %s reading could not tell a bot-challenge page from a JavaScript shell, so this group can "
                "include sites that served a challenge page instead of their content (fixed in 1.5.0, re-run "
                "pending)." % v)
    return ("%s 版的读法分不出人机验证页和 JavaScript 空壳，所以这一组里可能有返回人机验证页、而不是正文的站"
            "（1.5.0 已修正，榜单待重跑）。" % v)

def thin_words(n_thin, lang):
    """How many rows of a group rest on a thin sample, as a sentence, or "" when none does."""
    if not n_thin:
        return ""
    import stats as bstats
    if lang == "en":
        return "%d of them were scored on fewer than %d pages." % (n_thin, bstats.THIN_N)
    return "其中 %d 个站实际评分的页面不足 %d 个。" % (n_thin, bstats.THIN_N)

# what a 403 group can and cannot show: the probes carry crawler user-agent strings but come from the
# auditor's address, so a server that verifies crawlers by IP may refuse them and still serve the real bot
REFUSED = {"en": "the server refuses crawler user-agents (unverified probes from the auditor's address)",
           "zh": "服务器拒绝爬虫 user-agent（探测来自审计方自己的地址，未经爬虫身份验证）"}

def num_words(n, lang):
    """Small counts as words ('five' / '五'), anything else as digits."""
    en = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
    zh = {2: "两", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}
    return (en if lang == "en" else zh).get(n, str(n))

def share_words(pct, lang):
    """A share as words when it is close to a simple fraction, else as a percentage: the headline has to
    stay true when the benchmark is re-run, so it is derived from the data, never written by hand."""
    for frac, en, zh in ((1 / 5.0, "A fifth", "五分之一"), (1 / 4.0, "A quarter", "四分之一"),
                         (1 / 3.0, "A third", "三分之一"), (1 / 2.0, "Half", "一半")):
        if abs(pct / 100.0 - frac) <= 0.02:
            return en if lang == "en" else zh
    return ("%d%%" % pct) if lang == "en" else ("%d%%" % pct)

def _fmt(x):
    """中位数与四分位数取整。

    插值出来的分位数会带小数（上四分位 71.8）。但我们公开的复现区间是 ±5 分——
    在一个 0–100 的分数上印一位小数，是在声称这套方法不具备的精度。
    """
    return int(round(float(x)))


def jsonld(lang, v):
    """The leaderboard is a dataset. Saying so is the single highest-leverage thing
    this page can do to be cited — engines treat a declared Dataset very differently
    from an undeclared table."""
    page = PAGE[lang]
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
       "measurementTechnique": ("AIV rubric v1.1 — 21 tiered checks over a sample of up to 8 pages, "
                                "10 retrieval user-agents probed live"),
       "variableMeasured": [{"@type": "PropertyValue", "name": name, "description": zd if zh else en}
                            for name, en, zd in VARIABLES],
       "distribution": [{"@type": "DataDownload", "name": f, "encodingFormat": fmt, "contentUrl": DOWNLOAD + f}
                        for f, fmt in (("results.json", "application/json"), ("results.csv", "text/csv"),
                                       ("checks.csv", "text/csv"))],
       "citation": REPO + "/blob/main/rubric/v1.1.md"},
      {"@type": "WebSite", "@id": SITE + "/#website", "url": PAGE["en"],
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
            canon=PAGE["en"], oglocale="en_US",
            ogimg=SITE + "/og.png",
            ogalt="Share card: %(cappct)d%% of %(n)d well-known sites are unreadable to AI answer "
                   "engines' crawlers. Median %(med)s, range %(mn)d-%(mx)d." % v,
            t_title="The state of AI visibility — %(n)d sites scored" % v,
            t_desc="%(n)d well-known sites scored on whether AI answer engines can find, parse, "
                   "trust and cite them. Open rubric, reproducible, median %(med)s." % v,
            t_ogtitle="The state of AI visibility",
            t_ogdesc=share_words(v["cappct"], "en") + (" of %(n)d well-known sites are unreadable to AI answer engines' "
                     "crawlers. Open rubric, one command, reproducible." % v),
            t_h1="The state of<br>AI visibility",
            t_sub="%(n)d well-known sites, scored on whether an AI answer engine can find, parse, "
                  "trust and cite them. One open rubric, one public tool, up to eight pages per site: "
                  "%(nthin)d sites were scored on fewer than %(thin_en)s and are marked thin sample. Nothing here is a "
                  'black box — <a href="%(repo)s">re-run it yourself</a>.' % dict(v, repo=REPO),
            l_sites="SITES", l_median="MEDIAN", l_uq="UPPER QUARTILE", l_range="RANGE",
            l_cap="UNREADABLE TO AI",
            t_h2gate=share_words(v["cappct"], "en") + " of the field is unreadable to AI crawlers",
            t_pgate="%(cap)d sites have a gate check at zero — a retrieval crawler cannot get the "
                    "content, so nothing else on the page matters. Two very different problems "
                    "live inside that number." % v,
            l_delib="DELIBERATE", l_accid="ACCIDENTAL",
            t_delib="Their <code>robots.txt</code> disallows AI retrieval crawlers by name. A site "
                    "that does not want to be quoted is not misconfigured, and this rubric reports "
                    "it as it is." + (" " + crawler_note(v["tool"], "en") if crawler_note(v["tool"], "en") else ""),
            t_accid=" ".join(x for x in (
                    "Body copy only exists after JavaScript runs. The content is there and a browser "
                    "sees it; a retrieval crawler gets an empty shell. This group almost certainly "
                    "did not choose it.", thin_words(v["njs_thin"], "en"), challenge_note(v["tool"], "en")) if x),
            t_china=("<b>Sites in the %(ncs_en)s China sectors score %(gap)d points lower</b> — median %(cn)s "
                     "against %(row)s for everyone else." % v) + ((
                     " Grouped by the language a site serves instead, Chinese-language sites score %(lgap)d "
                     "lower; within matched sector families the gap runs from %(flo)d to %(fhi)d points. Up to "
                     "%(hshare)d%% of it sits in checks the tool reads with a heuristic, so part of it may be "
                     "the tool reading Chinese pages conservatively rather than the sites." % v) if v["lgap"] is not None else ""),
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
            l_fcap="Unreadable to AI", l_ftop="Solid or better", l_flow="Below 50", l_fthin="Thin sample",
            l_site="SITE", l_score="SCORE", l_band="BAND", l_sector="SECTOR",
            l_gaps="BIGGEST GAPS", l_pill="UNREADABLE", l_thin="THIN SAMPLE",
            l_count='"{a} of {b} sites"',
            t_h2sec="By sector",
            t_footer=('Scored with <a href="%(repo)s/blob/main/rubric/v1.1.md">AIV rubric v1.1</a> on '
                     '%(date)s · <a href="%(repo)s/blob/main/benchmark/results.json">raw data</a> '
                     '(<a href="%(repo)s/blob/main/benchmark/results.csv">CSV</a>) · '
                     '<a href="%(repo)s/blob/main/benchmark/run.py">the script</a> · '
                     '<a href="%(repo)s/blob/main/benchmark/REPRODUCIBILITY.md">how reproducible a single run is</a> · '
                     '<a href="%(repo)s">the repository</a><br><br>'
                     "We ran the whole benchmark twice on %(rp_date)s, with %(rp_tool)s, and compared every site: <strong>%(rp_w5)d%% of sites land within &plusmn;5</strong> and %(rp_same)d%% land identically, so read one site's number as &plusmn;5 rather than as exact. Medians are stable. "
                     + ("The unstable part is the gate checks &mdash; %(rp_flips_en)s sites flipped because their bot protection answered a crawler differently between the two runs, which is a property of those sites rather than of the measurement. "
                        if v["rp_legacy"] else "The gate-cap state flipped on %(rp_flips)d sites between the two runs. ") +
                     "This measures readiness, not outcomes: whether an engine <em>can</em> cite a "
                     "site. Whether one <em>does</em> depends on competition and query intent, which "
                     "no site-side audit can observe. Four checks needing off-site search are left "
                     "out of the denominator rather than guessed, so these run lower than a "
                     "hand-scored audit. Sites change; every number carries the date it was "
                     'measured.<br><br>Built by <a href="https://www.jianruntech.com">Jianrun Tech</a>. MIT.')
                     % dict(v, repo=REPO))
    return dict(
        htmllang="zh-CN", on_en="", on_zh="on",
        canon=PAGE["zh"], oglocale="zh_CN",
        ogimg=SITE + "/og.zh.png",
        ogalt="分享卡：%(n)d 个知名网站里 %(cappct)d%% 的内容 AI 回答引擎的爬虫读不到，"
              "中位数 %(med)s，区间 %(mn)d-%(mx)d。" % v,
        t_title="AI 可见度现状 — %(n)d 个站点实测" % v,
        t_desc="%(n)d 个知名网站的实测评分，衡量 AI 回答引擎能不能找到、读懂、信任并引用它们。"
               "口径公开、结果可复现，中位数 %(med)s。" % v,
        t_ogtitle="AI 可见度现状",
        t_ogdesc=("%(n)d 个知名网站里，" % v) + share_words(v["cappct"], "zh") + (" AI 回答引擎的爬虫读不到。"
                 "口径公开，一行命令，结果可复现。"),
        t_h1="AI 可见度<br>现状",
        t_sub="%(n)d 个知名网站，实测 AI 回答引擎能不能找到、读懂、信任并引用它们。"
              "同一套公开口径、同一个公开工具，每个站最多抽 8 个页面；其中 %(nthin)d 个站实际评分的页面不足 %(thin_n)d 个，"
              "表中标为「样本少」。"
              '这里没有黑箱——<a href="%(repo)s">你可以自己重跑</a>。' % dict(v, repo=REPO),
        l_sites="站点数", l_median="中位数", l_uq="上四分位", l_range="区间",
        l_cap="AI 读不到",
        t_h2gate=share_words(v["cappct"], "zh") + "的站，AI 爬虫读不到",
        t_pgate="%(cap)d 个站有门槛项得 0 分——检索爬虫压根拿不到内容，"
                "页面上其余的事都不再重要。而这个数字里装着两件性质完全不同的事。" % v,
        l_delib="主动屏蔽", l_accid="无意失效",
        t_delib="它们的 <code>robots.txt</code> 点名禁止了 AI 检索爬虫。"
                "一个不希望被引用的站不是配置错了，量表照实记录即可。" + crawler_note(v["tool"], "zh"),
        t_accid="正文只在 JavaScript 跑完之后才存在。内容是有的，浏览器看得见；"
                "检索爬虫拿到的是一个空壳。这一组几乎肯定不是有意的。"
                + thin_words(v["njs_thin"], "zh") + challenge_note(v["tool"], "zh"),
        t_china=("<b>%(ncs_zh)s个中国行业的站比其余站低 %(gap)d 分</b>——中位数 %(cn)s 对 %(row)s。" % v) + ((
                "改按站点面向的语言分组，中文站低 %(lgap)d 分；在相近的行业之间一一对比，差距在 %(flo)d 到 %(fhi)d 分之间。"
                "其中最多 %(hshare)d%% 落在工具靠启发式判断的检查项上，所以有一部分可能是工具对中文页面判得偏严，"
                "而不是网站本身。" % v) if v["lgap"] is not None else ""),
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
        l_fcap="AI 读不到", l_ftop="基础扎实及以上", l_flow="低于 50 分", l_fthin="样本少",
        l_site="站点", l_score="分数", l_band="档", l_sector="行业",
        l_gaps="最大缺口", l_pill="读不到", l_thin="样本少",
        l_count='"共 {b} 个，当前显示 {a} 个"',
        t_h2sec="分行业",
        t_footer=('按 <a href="%(repo)s/blob/main/rubric/v1.1.zh-CN.md">AIV 量表 v1.1</a> 于 '
                 '%(date)s 实测 · <a href="%(repo)s/blob/main/benchmark/results.json">原始数据</a>'
                 '（<a href="%(repo)s/blob/main/benchmark/results.csv">CSV</a>）· '
                 '<a href="%(repo)s/blob/main/benchmark/run.py">跑分脚本</a> · '
                 '<a href="%(repo)s/blob/main/benchmark/REPRODUCIBILITY.md">单次重跑的精度</a> · '
                 '<a href="%(repo)s">仓库</a> · '
                 '<a href="https://www.jianruntech.com/geo-score">中文说明页</a><br><br>'
                 "整个榜单我们于 %(rp_date)s 用%(rp_tool_zh)s跑了两遍并逐站比对：<strong>%(rp_w5)d%% 的站落在 &plusmn;5 以内</strong>，%(rp_same)d%% 完全一致。所以单个站的分数请按 &plusmn;5 读，不要当成精确值；中位数是稳的。"
                 + ("不稳的是门槛检查——两次之间有%(rp_flips_zh)s个站翻转，因为它们的 bot 防护对爬虫的答复变了，那是那些站点的属性，不是测量的毛病。"
                    if v["rp_legacy"] else "两次之间有 %(rp_flips)d 个站的门槛封顶状态翻转。") +
                 "这里测的是就绪度，不是结果：引擎<em>能不能</em>引用一个站。"
                 "它<em>会不会</em>引用，取决于竞争与提问意图，任何站外审计都观察不到。"
                 "四项需要站外检索的检查退出了分母而不是靠猜，所以这些分比人工逐项审计略低。"
                 "站点会变；每个数字都带着它被测量的日期。"
                 '<br><br>由<a href="https://www.jianruntech.com">见润科技</a>构建。MIT 许可。')
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
    # a sector with too few scored sites gets no median: it would print like a real one (stats.py)
    sys.path.insert(0, HERE)
    import stats as bstats
    u = bstats.compute(d)
    thin = {k for k, v in u["sectors"].items() if v["median"] is None}
    # the reproducibility figures the footer quotes, from reproducibility.json (retest.py): the latest study,
    # or the two runs of 2026-09-09 and the 1.1.x build that made them
    import retest
    h = retest.headline()
    rp = dict(rp_date=h["measured_at"], rp_w5=int(round(h["within_5_pct"])), rp_same=int(round(h["identical_pct"])),
              rp_flips=h["gate_flips"], rp_flips_en=num_words(h["gate_flips"], "en"),
              rp_flips_zh=num_words(h["gate_flips"], "zh"), rp_legacy=h["legacy"],
              rp_tool=h["tool"], rp_tool_zh=(" 1.1.2 修正波动之前的 1.1.x 版本" if h["legacy"] else " %s " % h["tool"]))
    # the China gap taken apart (stats.py china_gap_detail), so the page never states the gap without it
    cd = u.get("china_gap_detail") or {}
    fam = (cd.get("families") or {}).get("range") or [None, None]
    cgap = dict(lgap=(cd.get("by_language") or {}).get("gap"), flo=fam[0], fhi=fam[1],
                hshare=(cd.get("by_method") or {}).get("heuristic_share_pct"))
    if None in cgap.values():
        cgap["lgap"] = None
    ncs = len({r["sector"] for r in ok if r["sector"].startswith("China")})
    cgap.update(ncs_en=num_words(ncs, "en"), ncs_zh=num_words(ncs, "zh"))
    sec = sorted(d["sectors"].items(), key=lambda kv: (kv[0] in thin, -kv[1]["median"]))
    bins = [0] * 10
    for r in ok:
        bins[min(9, r["normalised"] // 10)] += 1
    # pages each row was scored on (raw/ for rows that predate the field); fewer than THIN_N is a thin sample
    sn = {r["site"]: bstats.sample_of(r)[0] for r in ok}
    thin_rows = sorted(x for x, k in sn.items() if k is not None and k < bstats.THIN_N)
    rows = [dict(s=r["site"], n=r["normalised"], b=r["band"], k=r["sector"],
                 c=bool(r.get("gate_capped")), w=r.get("gate_reason") or "",
                 g=r.get("top_gaps", []), r=r["readiness"], m=r["observable_max"], t=sn[r["site"]]) for r in ok]
    rows += [dict(s=r["site"], n=None, b="Not scored", k=r["sector"], c=False,
                  w=r.get("error", ""), g=[], r=None, m=None, t=None) for r in err]
    return dict(
        n=s["n"], med=_fmt(s["median"]), p75=_fmt(s["p75"]), mn=s["min"], mx=s["max"], cap=len(cap),
        cappct=int(round(100.0 * len(cap) / s["n"])),
        nerr=sum(1 for r in cap if r.get("gate_reason") == "serves crawlers an error"),
        nblk=len(blk), njs=len(js), blk=", ".join(blk), js=", ".join(js),
        nthin=len(thin_rows), thin_n=bstats.THIN_N, thin_en=num_words(bstats.THIN_N, "en"), njs_thin=sum(1 for x in js if x in thin_rows),
        js_note=(" (%s)" % challenge_note(d.get("tool"), "short")) if challenge_note(d.get("tool"), "short") else "",
        gap=round(row - cn), cn=cn, row=row, date=d["measured_at"], url_en=PAGE["en"], url_zh=PAGE["zh"],
        tool=d.get("tool"), refused=REFUSED["en"], **dict(cgap, **rp),
        blk_note=(" (%s)" % crawler_note(d.get("tool"), "short")) if crawler_note(d.get("tool"), "short") else "",
        css=io.open(os.path.join(HERE, "page.css"), encoding="utf-8").read(),
        bandcol=json.dumps(BAND_COL), bandmap=json.dumps(BAND_ZH, ensure_ascii=False),
        hist="".join('<div class="%s" style="height:%d%%"><span>%s</span></div>'
                     % ("hot" if v == max(bins) else "", max(3, round(100 * v / max(bins))), v or "")
                     for v in bins),
        histx="".join("<div>%d</div>" % (i * 10) for i in range(10)),
        secopts="".join("<option>%s</option>" % k for k, _ in sec),
        sectbl="".join(('<tr><td>%s</td><td class="num">%d</td><td class="num">—</td>'
                        '<td class="bar"><small>n &lt; %d</small></td></tr>' % (k, v["n"], bstats.MIN_N))
                       if k in thin else
                       ('<tr><td>%s</td><td class="num">%d</td>'
                        '<td class="num" style="color:var(--green)">%s</td>'
                        '<td class="bar"><i style="width:%d%%"></i></td></tr>'
                        % (k, v["n"], v["median"], v["median"])) for k, v in sec),
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

- [The state of AI visibility](%(url_en)s): %(n)d well-known sites scored. Median %(med)s, range %(mn)d\u2013%(mx)d. %(cappct)d%% of them are unreadable to AI crawlers \u2014 %(nblk)d block AI crawlers by name%(blk_note)s, %(njs)d serve a page whose body only exists after JavaScript runs%(js_note)s, and at %(nerr)d %(refused)s.
- [\u7b80\u4f53\u4e2d\u6587\u7248](%(url_zh)s): the same data and findings in Chinese.
- [Raw data](https://github.com/jianruntech/geo-score/blob/main/benchmark/results.json): every site, every score, machine-readable. The same rows flat, one column per check: [results.csv](https://github.com/jianruntech/geo-score/blob/main/benchmark/results.csv); one row per site and check: [checks.csv](https://github.com/jianruntech/geo-score/blob/main/benchmark/checks.csv).

## The rubric

- [AIV rubric v1.1](https://github.com/jianruntech/geo-score/blob/main/rubric/v1.1.md): the full specification, tier by tier.
- [\u7b80\u4f53\u4e2d\u6587](https://github.com/jianruntech/geo-score/blob/main/rubric/v1.1.zh-CN.md): the same specification in Chinese.
- [Machine-readable rubric](https://github.com/jianruntech/geo-score/blob/main/rubric/v1.1.json): stable check ids, tier conditions, bands.
- [Report schema](https://github.com/jianruntech/geo-score/blob/main/schema/report.v2.json): emit this and results from different implementations are comparable.
- [Calibration record](https://github.com/jianruntech/geo-score/blob/main/rubric/calibration-v1.1.md): how the thresholds were set, against four public benchmarks.

## The tool

- [CLI](https://github.com/jianruntech/geo-score/tree/main/cli): level 1 is one file, standard library only, Python 3.8+. `curl -sL .../cli/geo_score.py | python3 - yoursite.com`. Levels 2 and 3 (`--ask`, `watch`, and an MCP server) check whether AI engines actually cite a site, through their APIs with your own keys, and never add that to the score.
- [MCP server](https://github.com/jianruntech/geo-score/blob/main/guide/mcp.md): `geo-score-mcp` (stdio) gives an agent the same three levels. `score_site` is free and needs no key; `ask` and `run` spend the user's own API credits, and `--read-only` removes them. Setup for Claude Code, Claude Desktop, Cursor, VS Code, Codex, Gemini CLI and Zed is in the guide.
- [GitHub Action](https://github.com/jianruntech/geo-score/blob/main/action.yml): score on every push, fail the build on regression.
- [Five hand-scored audits](https://github.com/jianruntech/geo-score/tree/main/examples/audits/v1.1): all 21 checks scored by hand with reproducible evidence.

## Scope

This measures readiness \u2014 whether an engine *can* cite a site. Whether one *does*
depends on competition and query intent, which no site-side audit can observe.
Remediation is deliberately out of scope: the rubric names the gap and what the next
tier requires; it does not ship fix templates.

Maintained by [Jianrun Tech](https://www.jianruntech.com) (\u89c1\u6da6\u79d1\u6280), Shenzhen. MIT.
"""

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>%(url_en)s</loc>
    <lastmod>%(date)s</lastmod>
    <xhtml:link rel="alternate" hreflang="en" href="%(url_en)s"/>
    <xhtml:link rel="alternate" hreflang="zh" href="%(url_zh)s"/>
  </url>
  <url>
    <loc>%(url_zh)s</loc>
    <lastmod>%(date)s</lastmod>
    <xhtml:link rel="alternate" hreflang="en" href="%(url_en)s"/>
    <xhtml:link rel="alternate" hreflang="zh" href="%(url_zh)s"/>
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
        io.open(out, "w", encoding="utf-8").write(_hosted(TPL % vals))
        print("wrote docs/%s — %d sites, median %s" % (name, v["n"], v["med"]))
    # llms.txt and sitemap.xml are generated for the same reason the pages are: the
    # numbers in them went stale the moment the benchmark grew, and llms.txt is the
    # one file an AI crawler actually reads — a stale number there is a wrong answer
    # handed to every engine.
    for name, tpl in (("llms.txt", LLMS), ("sitemap.xml", SITEMAP)):
        io.open(os.path.join(ROOT, "docs", name), "w", encoding="utf-8").write(_hosted(tpl % v))
        print("wrote docs/%s" % name)
