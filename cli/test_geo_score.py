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

if fails:
    print("FAIL — %d" % len(fails))
    for f in fails: print("  · " + f)
    sys.exit(1)
print("OK — geo_score offline checks pass")
