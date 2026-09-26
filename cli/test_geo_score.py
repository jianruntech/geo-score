#!/usr/bin/env python3
"""Offline tests for the pure parts of geo_score. No network.

    python3 cli/test_geo_score.py

Every case here is a bug that actually shipped, or a rule the rubric states in prose
and the code has to honour. Add one when you fix a heuristic.
"""
import importlib.util, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gs", os.path.join(HERE, "geo_score.py"))
gs = importlib.util.module_from_spec(spec); spec.loader.exec_module(gs)
gs.c.on = False

fails = []
def eq(got, want, why):
    if got != want: fails.append("%s\n      got  %r\n      want %r" % (why, got, want))
def ok(cond, why):
    if not cond: fails.append(why)

# ── scope_of: a site can live under a path. Getting this wrong scored the wrong site. ──
eq(gs.scope_of("example.com"), ("https://example.com", ""), "bare host")
eq(gs.scope_of("https://example.com/"), ("https://example.com", ""), "trailing slash is not a path")
eq(gs.scope_of("https://u.github.io/proj"), ("https://u.github.io", "/proj"), "project page keeps its path")
eq(gs.scope_of("https://u.github.io/proj/"), ("https://u.github.io", "/proj"), "trailing slash trimmed")
eq(gs.scope_of("https://x.com/docs/index.html"), ("https://x.com", "/docs"), "a file resolves to its directory")
eq(gs.scope_of("http://x.com/a/b"), ("http://x.com", "/a/b"), "scheme preserved, nested path kept")


# ── idna: 非 ASCII 域名此前在发出请求之前就崩了。深圳跨境客群里中文域名不罕见。 ──
eq(gs.idna("https://中文.tw"), "https://xn--fiq228c.tw", "a Chinese host becomes punycode")
eq(gs.idna("https://例.cn:8443/x"), "https://xn--fsq.cn:8443/x", "the port survives")
eq(gs.idna("https://例え.テスト/パス"), "https://xn--r8jz45g.xn--zckzah/%E3%83%91%E3%82%B9",
   "a non-ASCII path is percent-encoded as UTF-8")
eq(gs.idna("https://example.com/a b"), "https://example.com/a%20b", "a space in the path is encoded")
eq(gs.idna("https://x.com/ok"), "https://x.com/ok", "a plain ASCII URL is left untouched")
ok(isinstance(gs.idna("::: not a url :::"), str), "a malformed URL returns a string, never raises")
eq(gs.idna(gs.idna("https://中文.tw/パス")), gs.idna("https://中文.tw/パス"),
   "encoding twice is the same as encoding once")
eq(gs.scope_of("中文.tw"), ("https://xn--fiq228c.tw", ""), "scope_of hands back a wire-safe origin")

# ── resolve_refs: @graph nodes point at each other. Not following cost 6 points. ──
g = gs.resolve_refs([
    {"@id": "#p", "@type": "Person", "name": "Real Person", "url": "https://x.test/p"},
    {"@type": "WebPage", "author": {"@id": "#p"}},
])
eq(g[1]["author"]["name"], "Real Person", "author reference is followed")
eq(g[1]["author"].get("url"), "https://x.test/p", "the whole referenced node comes across")
loop = gs.resolve_refs([{"@id": "#a", "@type": "T", "x": {"@id": "#b"}},
                        {"@id": "#b", "@type": "T", "x": {"@id": "#a"}}])
ok(isinstance(loop, list) and len(loop) == 2, "a reference cycle terminates instead of hanging")
bare = gs.resolve_refs([{"@type": "WebPage", "author": {"@id": "#missing"}}])
eq(bare[0]["author"], {"@id": "#missing"}, "a dangling reference is left alone, not invented")

# ── jsonld: @graph is flattened, malformed blocks are skipped, not fatal ──
html = ('<script type="application/ld+json">{"@context":"x","@graph":'
        '[{"@type":"Organization","name":"A"},{"@type":"WebSite"}]}</script>'
        '<script type="application/ld+json">{ this is not json }</script>')
t = gs.types_of(gs.jsonld(html))
ok("Organization" in t and "WebSite" in t, "@graph is flattened into its members")
eq(len(gs.jsonld(html)), 2, "the malformed block is skipped, the good one survives")

# ── word counting: the rubric's Chinese conversion is a rule, not a guess ──
ok(gs.wc("one two three four five") == 5, "English counts words")
ok(gs.wc("这是一段中文句子" * 5) > 20, "Chinese counts characters once past the threshold")
ok(gs.is_cjk("中文内容" * 40), "a Chinese page is detected as Chinese")
ok(not gs.is_cjk("An English page with plenty of words in it. " * 20), "an English page is not")

# ── tier_reason: the line a reader acts on ──
r = gs.tier_reason("p1.llms-txt", 0, 5)
ok("tier 1 of 4" in r and "needs" in r, "a bottom tier says what the next one needs: %r" % r)
ok("top tier" in gs.tier_reason("p1.llms-txt", 5, 5), "the top tier says so")
ok(gs.tier_reason("nope.not-a-check", 1, 2) == "", "an unknown id yields nothing rather than crashing")

# ── gzip bomb: the read cap is on the compressed stream, so inflation needs its own cap ──
import gzip as _gz
bomb = _gz.compress(b"\0" * 64_000_000)                      # ~62 KB on the wire
out = gs.gunzip(bomb, limit=1_000_000)
ok(len(bomb) < 200_000 and len(out) == 1_000_000, "a gzip bomb inflates to the cap, not to 64 MB")
ok(gs.gunzip(_gz.compress(b"<html>ok</html>")) == b"<html>ok</html>", "a normal gzip body round-trips")
ok(gs.gunzip(b"not gzip at all") == b"not gzip at all", "a mislabelled body is returned as-is")

# ── a network that cannot see a host is not evidence the host is gone ──
eq(gs.sameas_tier([200, 200, 200])[0], 3, "all sameAs resolve → top tier")
eq(gs.sameas_tier([200, 404])[0], 2, "one profile gone (404) → middle tier")
eq(gs.sameas_tier([404, 410])[0], 0, "every profile gone → zero")
eq(gs.sameas_tier([200, 0, 451, 999, 403, 429])[0], 3, "timeouts, 451 and bot walls are left out, not counted dead")
eq(gs.sameas_tier([0, 0, 451, 403])[0], None, "nothing checkable from here → unobservable, not zero")
eq(gs.kg_tier(True, 1, 6), 4, "an entity found on any lookup scores, even if others timed out")
eq(gs.kg_tier(False, 6, 6), 0, "zero only when every lookup answered and none matched")
eq(gs.kg_tier(False, 3, 6), None, "a partial answer with no match is unobservable — the missing lookup may be where it is")
eq(gs.kg_tier(False, 0, 6), None, "no answers at all → unobservable")

# ── the requests that decide the sample are retried, so one drop does not swap the sample ──
_calls = []
def _flaky(url, **kw):
    _calls.append(url)
    return gs.Resp(url, 200 if len(_calls) >= 3 else 0, b"<html></html>")
_orig_fetch, _orig_sleep = gs.fetch, gs.time.sleep
gs.fetch, gs.time.sleep = _flaky, (lambda s: None)
try:
    r = gs.fetch_steady("https://example.com/sitemap.xml")
    ok(r.ok and len(_calls) == 3, "a sitemap that fails twice then answers is fetched on the third try")
    _calls.clear(); gs.fetch = lambda url, **kw: (_calls.append(url), gs.Resp(url, 404, b""))[1]
    r = gs.fetch_steady("https://example.com/nope")
    ok(r.status == 404 and len(_calls) == 1, "a definite 404 is not retried")
finally:
    gs.fetch, gs.time.sleep = _orig_fetch, _orig_sleep

# ── bands and the gate cap ──
eq(gs.band(100), "Leading", "100 is Leading");  eq(gs.band(83), "Leading", "the band edge is inclusive")
eq(gs.band(82), "Solid", "just below the edge");  eq(gs.band(0), "Not started", "zero has a band")
ok(all(gs.band(n) for n in range(101)), "every score from 0 to 100 lands in a band")

# ── score(): arithmetic, exclusions, bonus cap, and the cap firing only at tier zero ──
def mk(tiers):
    return dict(root="https://x.test", urls=["https://x.test/"], lang="en",
                tier=tiers, ev={k: "" for k in tiers}, bonus={}, robots_bytes=0)
full = {c[0]: c[3] for c in gs.SPEC}                      # everything at full marks
rows, total, den, b, norm, bd, capped = gs.score(mk(full))
eq((total, den, norm, bd, capped), (100, 100, 100, "Leading", False), "all full marks is a clean 100")

part = dict(full); part["p2.freshness"] = 0
ok(gs.score(mk(part))[4] == 94, "a 6-point miss costs exactly 6")

gate_mid = dict(full); gate_mid["g.robots"] = 3
_, _, _, _, norm2, _, cap2 = gs.score(mk(gate_mid))
ok(not cap2, "a gate at a middle tier does NOT cap — this was v1.1's own bug")
ok(norm2 == 98, "it is a plain 2-point deduction, got %s" % norm2)

gate_zero = dict(full); gate_zero["g.ssr"] = 0
_, _, _, _, norm3, _, cap3 = gs.score(mk(gate_zero))
ok(cap3 and norm3 == gs.GATE_CAP, "a gate at zero caps at %d, got %s" % (gs.GATE_CAP, norm3))

excl = dict(full); excl["p4.cn-engines"] = None
_, tot4, den4, _, norm4, _, _ = gs.score(mk(excl))
eq((den4, norm4), (98, 100), "an excluded check leaves the denominator and does not lower the score")

bon = mk(full); bon["bonus"] = {k: v for k, _, v in gs.BONUS}
ok(gs.score(bon)[3] == gs.BONUS_CAP, "bonus is capped at +%d" % gs.BONUS_CAP)


# ── share_line: 一行能贴出去的东西。空洞的分享文案没人会贴。 ──
sl = gs.share_line(mk(full))
ok("100/100" in sl and "Leading" in sl, "the share line carries the score and the band")
ok("github.com/jianruntech/geo-score" in sl, "and a way back to the rubric")
ok(len(sl) < 260, "it fits in a post, got %d chars" % len(sl))
gapped = dict(full); gapped["p2.answer-passages"] = 0
ok("biggest gap" in gs.share_line(mk(gapped)).lower(), "a site with a gap names its biggest one")
capline = gs.share_line(mk(gate_zero))
ok("cannot reach" in capline, "a gate-capped site says why, instead of naming a content gap")
ok("Biggest gap" not in capline, "and does not also claim a content gap — the cap is the story")


# ── 路径型站点：前缀不是层级 ──
# GitHub 项目页、文档子目录、国家目录都活在一个路径下面。按原点数斜杠，
# 它们每一页都算「嵌套页」，然后因为没有面包屑被扣分——扣的是它们改不了的东西。
ok(gs.depth_in_scope("https://x.io/geo-score/zh.html", "/geo-score") == 0,
   "a sibling page under the given path is top-level, not nested")
ok(gs.depth_in_scope("https://x.io/geo-score/a/b.html", "/geo-score") == 1,
   "one real level below the given path counts as nested")
ok(gs.depth_in_scope("https://x.io/a/b.html", "") == 1,
   "with no path given, nesting is counted from the origin as before")
ok(gs.depth_in_scope("https://x.io/geo-score/", "/geo-score") == 0,
   "the scope root itself is depth 0")
ok(gs.depth_in_scope("https://x.io/other/p.html", "/geo-score") == 1,
   "a URL outside the scope falls back to origin-relative depth")


# ── 308 必须被当成重定向 ──
# Python 3.11 之前 urllib 对 308 直接抛 HTTPError，而 redirect_request 又显式拒绝它，
# 所以只给 http_error_308 起别名是不够的——第一版修补就是这么漏的。
# 后果不只是丢站：3.11+ 会跟过去并给出分数，3.8–3.10 报「抓不到」，
# 同一个站的分数取决于谁的 Python 在跑。
import urllib.request as _ur
_h = gs._Redirects()
_req = _ur.Request("https://example.com/", method="GET")
class _FakeFp:
    def read(self, *a): return b""
    def close(self): pass
for _code in (307, 308):
    _new = _h.redirect_request(_req, _FakeFp(), _code, "", {}, "https://example.org/")
    ok(_new is not None and _new.full_url == "https://example.org/",
       "%d is followed, not raised" % _code)
    ok(_new.get_method() == "GET", "%d preserves the method" % _code)
ok(hasattr(gs, "_OPENER"), "fetch goes through the redirect-aware opener")

# ── as_json(): the published schema is a contract ──
rep = gs.as_json(mk(full))
for k in ("rubric_version", "audited_at", "target", "readiness", "observable_max",
          "normalised", "band", "gate_capped", "checks", "tool"):
    ok(k in rep, "the report carries %s" % k)
ids = {c["id"] for c in rep["checks"]}
spec_ids = {c[0] for c in gs.SPEC} | {b[0] for b in gs.BONUS}
eq(ids - spec_ids, set(), "no check id is emitted that the rubric does not define")
for c in rep["checks"]:
    if c["state"] == "scored" and not c["id"].startswith("b."):
        ok(c.get("tier_reason"), "%s carries a tier_reason" % c["id"])
ok("failed" not in {c["state"] for c in rep["checks"]},
   "there is no `failed` state under tiered scoring — a bottom tier is scored 0")

# ── the badge is valid SVG and carries the score ──
import tempfile, xml.dom.minidom
pth = os.path.join(tempfile.mkdtemp(), "b.svg")
gs.write_badge(mk(full), pth)
svg = io.open(pth, encoding="utf-8").read()
xml.dom.minidom.parseString(svg)
ok("100/100" in svg and "Leading" in svg, "the badge shows the score and the band")
ok('role="img"' in svg and "<title>" in svg, "the badge is labelled for screen readers")

# ── html helpers ──
eq(gs.visible_text("<p>a<script>junk()</script>b</p>"), "a b", "scripts are stripped, not read")
ok("h2" not in " ".join(gs.headings("<h2>Real heading</h2>")).lower(), "headings come back as text")
ok("Real heading" in gs.headings("<h2>Real heading</h2>"), "and the text is intact")

# ── p2.question-intent: \w matches CJK, so the nav-label filter must not swallow short Chinese headings ──
def _intent(h): return bool(gs.QP_INTENT.search(h)) and not gs.NAV_LABEL.match(h)
ok(_intent("怎么定价"), "a 4-char Chinese question heading counts as question intent")
ok(_intent("为什么可以信这个分"), "a 9-char Chinese why-heading counts")
ok(_intent("How pricing works"), "a latin how-heading counts")
ok(not _intent("价格"), "a bare Chinese nav label does not count")
ok(not _intent("怎么买"), "a 3-char Chinese label is still treated as nav")
ok(not _intent("Pricing"), "a single latin word is still a nav label")
ok(not _intent("首页 · 价格"), "an a · b nav pattern does not count")

# ── is_cjk judges the visible text, not the markup ──
_zh_page = "<html><head><style>" + ("body{margin:0}" * 400) + "</style><script>" + ("var a=1;" * 400) + "</script></head><body><p>" + ("见润科技面向跨境电商与出海企业提供人工智能落地服务。" * 6) + "</p></body></html>"
ok(gs.is_cjk(_zh_page), "a Chinese page stays Chinese even when its HTML is mostly CSS/JS")
ok(not gs.is_cjk("<html><body><p>" + ("An English page with a 中文 word. " * 20) + "</p></body></html>"), "a stray CJK word does not make a page Chinese")

# ── the CLI's embedded rubric must equal the published rubric/v1.1.json ──
# 「CLI 实现的就是公开量表」这句话以前只是口头承诺：两份表今天一致，但没有任何东西保证明天也一致。
_rub = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rubric", "v1.1.json"), encoding="utf-8"))
eq(gs.RUBRIC, "v%s" % _rub["rubric_version"], "the CLI names the rubric version it implements")
_scored = [c for c in _rub["checks"] if c["kind"] in ("gate", "scored")]
eq([c[0] for c in gs.SPEC], [c["id"] for c in _scored], "SPEC lists the rubric's scored checks, in order")
for c in _scored:
    sp = next((x for x in gs.SPEC if x[0] == c["id"]), None)
    if sp is None:
        continue
    eq((sp[1], sp[3]), (c["pillar"], c["points"]), "%s pillar and max points match the rubric" % c["id"])
    eq(sp[4], [t["points"] for t in c["tiers"]], "%s tier points in SPEC match the rubric" % c["id"])
    eq([[t[0], t[1]] for t in gs.TIERS[c["id"]]], [[t["points"], t["condition"]] for t in c["tiers"]],
       "%s tier points and conditions in TIERS match the rubric" % c["id"])
eq(set(gs.TIERS), {c["id"] for c in _scored}, "TIERS covers exactly the scored checks")
eq([(b[0], b[2]) for b in gs.BONUS], [(c["id"], c["points"]) for c in _rub["checks"] if c["kind"] == "bonus"],
   "bonus ids and points match the rubric")
eq([list(b) for b in gs.BANDS], [[b["min_pct"], b["name"]] for b in _rub["bands"]], "band thresholds and names match")
eq((gs.GATE_CAP, gs.BONUS_CAP), (_rub["gate_cap"], _rub["bonus_cap"]), "gate cap and bonus cap match")
eq(sum(c["points"] for c in _scored), 100, "scored checks sum to 100")

# ── CI outputs: SARIF 2.1.0 and JUnit from the same run as the report ──
# 一次抓取、多种输出。分数单跑本来就有 ±5 的波动，跑两遍再拼出来的摘要和日志可能对不上。
mixed = dict(full); mixed["g.ssr"] = 0; mixed["p2.freshness"] = 0; mixed["p2.answer-passages"] = 2
mixed["p4.cn-engines"] = None
sar = gs.as_sarif(mk(mixed))
json.loads(json.dumps(sar))
eq(sar["version"], "2.1.0", "SARIF declares 2.1.0")
drv = sar["runs"][0]["tool"]["driver"]
eq(len(drv["rules"]), len(gs.SPEC), "one SARIF rule per rubric check")
eq(drv["version"], gs.__version__, "the SARIF driver carries the tool version")
by = {r["ruleId"]: r for r in sar["runs"][0]["results"]}
eq(by["g.ssr"]["level"], "error", "a gate at zero is a SARIF error")
eq(by["p2.freshness"]["level"], "warning", "a non-gate check at zero is a warning")
eq(by["p2.answer-passages"]["level"], "note", "partial credit is a note")
ok("p4.cn-engines" not in by, "an unobservable check is not reported as a problem")
ok("p1.robots-ai" not in by and "g.robots" not in by, "a check at full marks produces no result")
ok(all(r["ruleId"] in {x["id"] for x in drv["rules"]} for r in sar["runs"][0]["results"]),
   "every result points at a declared rule")
ok(all(r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "https://x.test"
       for r in sar["runs"][0]["results"]), "results are located at the scored URL")
eq(sar["runs"][0]["properties"]["normalised"], gs.score(mk(mixed))[4], "SARIF carries the same score as the report")
eq(len({r["partialFingerprints"]["geoScoreCheck/v1"] for r in sar["runs"][0]["results"]}),
   len(sar["runs"][0]["results"]), "fingerprints are unique, so code scanning can track a check across runs")

jx = gs.as_junit(mk(mixed))
jd = xml.dom.minidom.parseString(jx.encode("utf-8"))
suites = jd.getElementsByTagName("testsuites")[0]
eq(int(suites.getAttribute("tests")), len(gs.SPEC), "one JUnit test per rubric check")
eq(int(suites.getAttribute("failures")), 2, "only checks at zero fail")
eq(int(suites.getAttribute("skipped")), 1, "an unobservable check is skipped, never failed")
eq(len(jd.getElementsByTagName("failure")), 2, "the failure count matches the failure elements")
fl = [f.getAttribute("type") for f in jd.getElementsByTagName("failure")]
ok("gate" in fl and "check" in fl, "a failing gate is typed apart from a failing check")
nasty = mk(full); nasty["tier"] = dict(full, **{"p2.freshness": 0}); nasty["ev"]["p2.freshness"] = 'dates <none> & "quotes" ]]>'
xml.dom.minidom.parseString(gs.as_junit(nasty).encode("utf-8"))
ok(True, "evidence with markup characters still yields well-formed JUnit")

# 三个输出参数只接单站，和 --compare 一起用要报错而不是只写第一个站
import subprocess
_cli = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo_score.py")
for flag in ("--json-out", "--sarif", "--junit"):
    pr = subprocess.run([sys.executable, _cli, "a.invalid", "--compare", "b.invalid", flag, os.devnull, "--quiet"],
                        capture_output=True, text=True, timeout=60)
    ok(pr.returncode == 2 and "one site at a time" in pr.stderr, "%s with --compare is refused, got %s" % (flag, pr.returncode))

# ── --urls / --urls-from: a pinned re-score reads exactly the given pages ──
# 抽样是分数波动的主要来源；固定页面重跑才能把「站变了」和「抽到的页不同」分开。
def _raises(fn, *a):
    try: fn(*a)
    except RuntimeError as e: return str(e)
    return None
eq(gs.pin_urls("https://x.test", ["https://x.test/a", "/b", "c", "https://x.test/a#frag"]),
   ["https://x.test/a", "https://x.test/b", "https://x.test/c"], "relative paths resolve, duplicates and fragments collapse")
ok("not on" in (_raises(gs.pin_urls, "https://x.test", ["https://evil.test/a"]) or ""), "an off-site URL is refused")
ok("not on" in (_raises(gs.pin_urls, "https://x.test", ["http://x.test/a"]) or ""), "a different scheme is refused")
ok("outside" in (_raises(gs.pin_urls, "https://x.test/docs", ["https://x.test/blog/a"]) or ""), "a URL outside the scored path is refused")
ok(_raises(gs.pin_urls, "https://x.test/docs", ["https://x.test/docs", "https://x.test/docs/a"]) is None, "the scope root and pages under it are accepted")
ok("at most 8" in (_raises(gs.pin_urls, "https://x.test", ["/p%d" % i for i in range(9)]) or ""), "nine pages are refused")
ok("empty" in (_raises(gs.pin_urls, "https://x.test", ["", "  "]) or ""), "an empty list is refused")
_d = tempfile.mkdtemp()
io.open(os.path.join(_d, "u.txt"), "w", encoding="utf-8").write("https://x.test/a  # home\n\n# comment\n/b\n")
eq(gs.read_url_list(os.path.join(_d, "u.txt")), ["https://x.test/a", "/b"], "the URL file skips blanks and comments")
_rep = gs.as_json(mk(full)); _rep["sampled_urls"] = ["https://x.test/", "https://x.test/p"]
io.open(os.path.join(_d, "r.json"), "w", encoding="utf-8").write(json.dumps(_rep))
eq(gs.read_report_urls(os.path.join(_d, "r.json")), ["https://x.test/", "https://x.test/p"], "--urls-from reads sampled_urls back")
ok("not JSON" in (_raises(gs.read_report_urls, os.path.join(_d, "u.txt")) or ""), "a non-JSON file is refused with a hint")
ok("cannot read" in (_raises(gs.read_report_urls, os.path.join(_d, "nope.json")) or ""), "a missing file is a clear error")
pr = subprocess.run([sys.executable, _cli, "a.invalid", "--compare", "b.invalid", "--urls-from", os.path.join(_d, "r.json")],
                    capture_output=True, text=True, timeout=60)
ok(pr.returncode == 2 and "one site at a time" in pr.stderr, "--urls-from with --compare is refused")

if fails:
    print("FAIL — %d" % len(fails))
    for f in fails: print("  · " + f)
    sys.exit(1)
print("OK — geo_score offline checks pass")

