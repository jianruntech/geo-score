#!/usr/bin/env python3
"""
geo-score — score a site 0-100 on whether AI answer engines can find, parse,
trust and cite it. Implements the open AIV rubric v1.1.

    python3 geo_score.py https://example.com

No dependencies. Python 3.8+. Reads only public URLs.
Rubric: https://github.com/jianruntech/geo-score
"""
import argparse, concurrent.futures as cf, gzip, html, io, json, os, re, sys, time
import urllib.error, urllib.parse, urllib.request
from collections import Counter

__version__ = "1.1.0"
RUBRIC = "v1.1"
UA_BROWSER = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
RETRIEVAL_UAS = [
    ("GPTBot", "GPTBot/1.2 (+https://openai.com/gptbot)"),
    ("OAI-SearchBot", "OAI-SearchBot/1.0 (+https://openai.com/searchbot)"),
    ("ChatGPT-User", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0"),
    ("ClaudeBot", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ClaudeBot/1.0"),
    ("Claude-SearchBot", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; Claude-SearchBot/1.0"),
    ("PerplexityBot", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; PerplexityBot/1.0"),
    ("Perplexity-User", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; Perplexity-User/1.0"),
    ("Google-Extended", "Mozilla/5.0 (compatible; Google-Extended/1.0)"),
    ("Applebot", "Mozilla/5.0 (compatible; Applebot/0.1)"),
    ("Bingbot", "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"),
]
CN_UAS = [("Baiduspider", "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)"),
          ("Sogou", "Sogou web spider/4.0"),
          ("PetalBot", "Mozilla/5.0 (compatible; PetalBot;+https://webmaster.petalsearch.com/site/petalbot)")]

# ── colour ─────────────────────────────────────────────────────────────────
class C:
    on = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    def __getattr__(self, k):
        codes = dict(dim="\033[2m", b="\033[1m", r="\033[0m", green="\033[38;5;35m",
                     amber="\033[38;5;179m", red="\033[38;5;167m", grey="\033[38;5;245m",
                     brass="\033[38;5;137m", pine="\033[38;5;29m")
        return codes.get(k, "") if self.on else ""
c = C()

# ── fetching ───────────────────────────────────────────────────────────────
class Resp:
    __slots__ = ("url", "status", "body", "headers", "err", "elapsed")
    def __init__(self, url, status=0, body=b"", headers=None, err=None, elapsed=0.0):
        self.url, self.status, self.body = url, status, body
        self.headers, self.err, self.elapsed = headers or {}, err, elapsed
    @property
    def text(self):
        cs = "utf-8"
        m = re.search(r'charset=["\']?([\w-]+)', self.headers.get("content-type", ""), re.I)
        if m: cs = m.group(1)
        try: return self.body.decode(cs, "replace")
        except LookupError: return self.body.decode("utf-8", "replace")
    @property
    def ok(self): return 200 <= self.status < 300

UNSAFE = ' <>"{}|\\^`'

def idna(url):
    """A non-ASCII host has to go on the wire as punycode, and a non-ASCII path as
    percent-encoded UTF-8. urllib does neither, so a Chinese domain used to raise
    UnicodeEncodeError before a single request went out."""
    try:
        u = urllib.parse.urlsplit(url)
        host = u.hostname or ""
        if any(ord(ch) > 127 for ch in host):
            enc = host.encode("idna").decode("ascii")
            netloc = enc + (":%d" % u.port if u.port else "")
            if u.username:
                netloc = "%s%s@%s" % (u.username, ":" + u.password if u.password else "", netloc)
            u = u._replace(netloc=netloc)
        if any(ord(ch) > 127 or ch in UNSAFE for ch in u.path + u.query):
            u = u._replace(path=urllib.parse.quote(u.path, safe="/~:@!$&'()*+,;="),
                           query=urllib.parse.quote(u.query, safe="=&/~:@!$'()*+,;"))
        return urllib.parse.urlunsplit(u)
    except Exception:
        return url

def fetch(url, ua=UA_BROWSER, timeout=15, method="GET"):
    url = idna(url)
    req = urllib.request.Request(url, method=method, headers={
        "User-Agent": ua, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Encoding": "gzip", "Accept-Language": "en,zh;q=0.8"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(4_000_000)
            if r.headers.get("Content-Encoding") == "gzip":
                try: raw = gzip.decompress(raw)
                except Exception: pass
            h = {k.lower(): v for k, v in r.headers.items()}
            return Resp(r.geturl(), r.status, raw, h, elapsed=time.time() - t0)
    except urllib.error.HTTPError as e:
        try: raw = e.read(400_000)
        except Exception: raw = b""
        return Resp(url, e.code, raw, {k.lower(): v for k, v in (e.headers or {}).items()},
                    elapsed=time.time() - t0)
    except Exception as e:
        return Resp(url, 0, b"", err=str(e)[:120], elapsed=time.time() - t0)

def pmap(fn, items, workers=8):
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))

# ── html helpers ───────────────────────────────────────────────────────────
TAGSTRIP = re.compile(r"<(script|style|noscript|template|svg)\b.*?</\1>", re.S | re.I)
def visible_text(h):
    h = TAGSTRIP.sub(" ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h)).strip()

def main_html(h):
    m = re.search(r"<main\b[^>]*>(.*?)</main>", h, re.S | re.I) or \
        re.search(r'<article\b[^>]*>(.*?)</article>', h, re.S | re.I)
    return m.group(1) if m else h

def jsonld(h):
    out = []
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', h, re.S | re.I):
        raw = m.group(1).strip()
        try: d = json.loads(raw)
        except Exception:
            try: d = json.loads(re.sub(r",\s*([}\]])", r"\1", raw))
            except Exception: continue
        out.extend(d if isinstance(d, list) else [d])
    flat = []
    def walk(o):
        if isinstance(o, dict):
            if "@graph" in o and isinstance(o["@graph"], list):
                for g in o["@graph"]: walk(g)
            else: flat.append(o)
        elif isinstance(o, list):
            for x in o: walk(x)
    for o in out: walk(o)
    return resolve_refs(flat)

def resolve_refs(objs):
    """Follow {"@id": "..."} references inside a @graph. Sites that use @graph name an
    entity once and point at it everywhere else; a parser that does not follow the
    pointer reports a page with a named author as having none."""
    by_id = {o["@id"]: o for o in objs if isinstance(o.get("@id"), str) and len(o) > 1}
    if not by_id: return objs
    def deref(v, depth=0):
        if depth > 3: return v
        if isinstance(v, dict):
            if set(v) == {"@id"} and v["@id"] in by_id:
                return deref({k: x for k, x in by_id[v["@id"]].items() if k != "@id"}, depth + 1)
            return {k: deref(x, depth + 1) for k, x in v.items()}
        if isinstance(v, list): return [deref(x, depth + 1) for x in v]
        return v
    return [deref(o) for o in objs]

def types_of(objs):
    t = []
    for o in objs:
        v = o.get("@type")
        t.extend(v if isinstance(v, list) else [v] if v else [])
    return set(t)

def headings(h):
    out = [visible_text(m.group(1))[:200]
           for m in re.finditer(r"<h[1-4]\b[^>]*>(.*?)</h[1-4]>", h, re.S | re.I)]
    t = re.search(r"<title\b[^>]*>(.*?)</title>", h, re.S | re.I)
    if t: out.append(visible_text(t.group(1))[:200])
    return [x for x in out if x]

def paragraphs(h):
    return [p for p in (visible_text(m.group(1)) for m in
            re.finditer(r"<p\b[^>]*>(.*?)</p>", main_html(h), re.S | re.I)) if p]

def wc(s):
    cjk = len(re.findall(r"[一-鿿]", s))
    return cjk if cjk > 20 else len(s.split())

def host_stem(root):
    parts = urllib.parse.urlsplit(root).netloc.replace("www.", "").split(".")
    return parts[0].lower()

def is_cjk(s):
    return len(re.findall(r"[一-鿿]", s)) > max(30, len(s) * 0.08)

# ── the rubric ─────────────────────────────────────────────────────────────
SPEC = [
 ("g.robots","Reachable","Crawlers allowed in robots.txt",5,[0,3,5]),
 ("g.reachable","Reachable","Reachable to retrieval agents",5,[0,3,5]),
 ("g.ssr","Reachable","Main content server-rendered",5,[0,3,5]),
 ("p1.sitemap","Understandable","Sitemap discoverable and fresh",4,[0,2,4]),
 ("p1.llms-txt","Understandable","llms.txt present and structured",5,[0,2,4,5]),
 ("p1.organization","Understandable","Organization + WebSite schema",6,[0,3,5,6]),
 ("p1.breadcrumb","Understandable","BreadcrumbList on nested pages",3,[0,2,3]),
 ("p1.page-type","Understandable","Page-type schema (Product, FAQ…)",4,[0,2,4]),
 ("p2.answer-passages","Content Citability","Self-contained answer passages",9,[0,4,7,9]),
 ("p2.question-intent","Content Citability","Headings match how people ask",7,[0,3,5,7]),
 ("p2.freshness","Content Citability","Freshness signal present",6,[0,3,6]),
 ("p2.sourced-stats","Content Citability","Statistics carry a source",7,[0,3,5,7]),
 ("p2.named-author","Content Citability","Named, verifiable authorship",6,[0,3,6]),
 ("p3.listings","Brand Credibility","Third-party listings",4,[0,2,3,4]),
 ("p3.mentions","Brand Credibility","Independent mentions",4,[0,2,3,4]),
 ("p3.knowledge-graph","Brand Credibility","Knowledge-graph entity",4,[0,4]),
 ("p3.sameas","Brand Credibility","sameAs links resolve",3,[0,2,3]),
 ("p3.video","Brand Credibility","Video and multimodal presence",3,[0,2,3]),
 ("p4.answer-shape","Answer Fit","Content shaped for extraction",4,[0,2,4]),
 ("p4.question-coverage","Answer Fit","Covers the questions people ask",4,[0,2,3,4]),
 ("p4.cn-engines","Answer Fit","Chinese engine readiness",2,[0,1,2]),
]
TIERS = {
    "g.robots": [
        [0,
            "robots.txt carries a Disallow that applies to retrieval user-agents"],
        [3,
            "no explicit Disallow, but no explicit Allow either"],
        [5,
            "mainstream retrieval user-agents explicitly allowed"]
    ],
    "g.reachable": [
        [0,
            "most retrieval user-agents are blocked"],
        [3,
            "some are blocked, or the body differs from what a browser receives"],
        [5,
            "all 10 retrieval user-agents return 200 with matching content"]
    ],
    "g.ssr": [
        [0,
            "body copy exists only after JavaScript runs"],
        [3,
            "present on some sampled pages"],
        [5,
            "present in the HTML response on every sampled page"]
    ],
    "p1.sitemap": [
        [0,
            "cannot be discovered, or does not return 200"],
        [2,
            "discoverable and returns 200"],
        [4,
            "and lastmod covers most URLs"]
    ],
    "p1.llms-txt": [
        [0,
            "absent"],
        [2,
            "present and returns 200"],
        [4,
            "carries a site definition passage"],
        [5,
            "and has 2+ topic sections that contain links"]
    ],
    "p1.organization": [
        [0,
            "neither present"],
        [3,
            "one of the two present"],
        [5,
            "both present with name, url and logo"],
        [6,
            "and the logo resolves, with sameAs declared"]
    ],
    "p1.breadcrumb": [
        [0,
            "absent"],
        [2,
            "present on some nested pages"],
        [3,
            "present across nested pages"]
    ],
    "p1.page-type": [
        [0,
            "absent"],
        [2,
            "present on some page types"],
        [4,
            "present across applicable page types with real field values"]
    ],
    "p2.answer-passages": [
        [0,
            "none on the sampled pages"],
        [4,
            "on a few pages"],
        [7,
            "on half the pages"],
        [9,
            "on most pages"]
    ],
    "p2.question-intent": [
        [0,
            "headings are mostly keyword strings or brand labels"],
        [3,
            "a few headings read like a question someone would ask"],
        [5,
            "about half do"],
        [7,
            "most do"]
    ],
    "p2.freshness": [
        [0,
            "no date in the page or in structured data"],
        [3,
            "some pages carry a visible date or datePublished"],
        [6,
            "most pages do, and dateModified agrees with the visible date"]
    ],
    "p2.sourced-stats": [
        [0,
            "figures and claims carry no source"],
        [3,
            "some are attributed"],
        [5,
            "most are attributed"],
        [7,
            "most are attributed and the source is clickable and checkable"]
    ],
    "p2.named-author": [
        [0,
            "no byline, or the byline is the organisation"],
        [3,
            "bylined to a real person"],
        [6,
            "and the name links to a verifiable identity page"]
    ],
    "p3.listings": [
        [0,
            "none"],
        [2,
            "1–2"],
        [3,
            "3–4"],
        [4,
            "5 or more"]
    ],
    "p3.mentions": [
        [0,
            "none"],
        [2,
            "occasional mentions"],
        [3,
            "independent coverage or reviews exist"],
        [4,
            "sustained mentions across channels"]
    ],
    "p3.knowledge-graph": [
        [0,
            "no corresponding entry"],
        [4,
            "an entry exists in Wikidata, Wikipedia, Baidu Baike or similar"]
    ],
    "p3.sameas": [
        [0,
            "not declared, or most do not resolve"],
        [2,
            "declared but some are dead"],
        [3,
            "all resolve and belong to the brand"]
    ],
    "p3.video": [
        [0,
            "no official video"],
        [2,
            "a channel exists but content is sparse"],
        [3,
            "sustained output, with VideoObject on site"]
    ],
    "p4.answer-shape": [
        [0,
            "long paragraphs, no hierarchy"],
        [2,
            "subheadings present but paragraphs run long"],
        [4,
            "subheadings, lists and tables with paragraphs of workable length"]
    ],
    "p4.question-coverage": [
        [0,
            "0–2 of 10 covered"],
        [2,
            "3–5 covered"],
        [3,
            "6–8 covered"],
        [4,
            "9–10 covered"]
    ],
    "p4.cn-engines": [
        [0,
            "crawling blocked, or filing information absent"],
        [1,
            "crawlable"],
        [2,
            "crawlable with ICP filing and entity information complete"]
    ]
}

BONUS = [("b.llms-full","llms-full.txt",2),("b.ai-txt","ai.txt",2),
         ("b.geo-link","GEO link tags",1),("b.speakable","speakable markup",1)]
BANDS = [(83,"Leading"),(66,"Solid"),(51,"Growing"),(31,"Early"),(0,"Not started")]
GATE_CAP, BONUS_CAP = 40, 6
# checks a static fetcher cannot honestly observe — they leave the denominator
NEEDS_JUDGEMENT = {"p3.listings","p3.mentions","p4.question-coverage"}

def band(p): return next(n for t, n in BANDS if p >= t)

def tier_reason(cid, t, mx):
    """The one line worth reading: which tier the evidence reached, and what the next
    one asks for. Generated from the rubric's own tier conditions."""
    ts = TIERS.get(cid)
    if not ts: return ""
    pts = [p for p, _ in ts]
    try: idx = pts.index(t)
    except ValueError: idx = max(i for i, p in enumerate(pts) if p <= t)
    here = "tier %d of %d" % (idx + 1, len(ts))
    if t >= mx: return "%s — top tier: %s" % (here, ts[idx][1])
    nxt = ts[idx + 1]
    return "%s — tier %d (+%d) needs: %s" % (here, idx + 2, nxt[0] - t, nxt[1])

# ── sampling ───────────────────────────────────────────────────────────────
def depth_in_scope(url, scope):
    """How deep a URL sits inside the scope the user gave, not inside the origin.

    For a site at example.com/docs, "docs/guide.html" is a top-level page of that site
    and "docs/a/b.html" is one level down. Counting from the origin marks every page
    nested and then penalises the site for missing breadcrumbs it does not need.
    """
    pth = urllib.parse.urlsplit(url).path
    if scope and pth.startswith(scope):
        pth = pth[len(scope):]
    return pth.strip("/").count("/")


def scope_of(base):
    """A site can live under a path — a project page, a docs subtree, a country folder.
    robots.txt and llms.txt are always at the origin by spec, but sampling has to stay
    inside the path the user actually gave, or every page check scores the wrong site."""
    u = urllib.parse.urlsplit(base if "://" in base else "https://" + base)
    origin = "%s://%s" % (u.scheme or "https", u.netloc)
    origin = idna(origin)
    path = re.sub(r"/+$", "", u.path or "")
    if re.search(r"\.[a-z0-9]{2,5}$", path, re.I):          # a file, not a directory
        path = path.rsplit("/", 1)[0]
    return origin, path

def discover(base, want=8, verbose=False):
    """Pick pages the way a retrieval crawler would meet them: real leaf pages, not
    section indexes. Index pages carry navigation, not prose, and every content check
    depends on the sample being representative."""
    origin, scope = scope_of(base)
    root = origin + scope
    host = urllib.parse.urlsplit(origin).netloc
    home = fetch(root + "/")
    pool, seen = [], {root + "/", root}

    def harvest(text, origin):
        out = []
        for m in re.finditer(r'<a\b[^>]*href=["\']([^"\'#]+)', text, re.I):
            u = urllib.parse.urljoin(origin, m.group(1)).split("#")[0].split("?")[0].rstrip("/")
            pu = urllib.parse.urlsplit(u)
            if pu.netloc != host: continue
            if scope and not pu.path.startswith(scope): continue
            if re.search(r"\.(png|jpe?g|gif|svg|css|js|pdf|zip|ico|xml|txt|woff2?|mp4)$", u, re.I): continue
            if re.search(r"/(login|signin|signup|register|cart|checkout|account|admin|search)(/|$)", u, re.I): continue
            if u in seen: continue
            seen.add(u); out.append(u)
        return out

    pool += harvest(home.text, root + "/")

    # sitemap gives real content URLs, which a homepage nav often does not
    rb = fetch(origin + "/robots.txt")
    sm_urls = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", rb.text if rb.ok else "") \
              or [origin + "/sitemap.xml", origin + "/sitemap_index.xml"]
    sm = next((r for r in pmap(fetch, sm_urls[:2]) if r.ok), None)
    if sm and re.search(r"<sitemapindex", sm.text, re.I):
        kids = [x.strip() for x in re.findall(r"<loc>\s*([^<]+)", sm.text)][:2]
        got = [r for r in pmap(fetch, kids) if r.ok]
        sm = got[0] if got else None
    if sm:
        locs = [x.strip() for x in re.findall(r"<loc>\s*([^<]+)", sm.text)]
        for u in locs[:600]:
            u = u.split("#")[0].split("?")[0].rstrip("/")
            pu2 = urllib.parse.urlsplit(u)
            if pu2.netloc == host and (not scope or pu2.path.startswith(scope)) and u not in seen:
                seen.add(u); pool.append(u)

    # section indexes are where recent posts actually live
    idx = [root + p for p in ("/blog", "/news", "/posts", "/articles", "/insights", "/resources", "/docs", "/learn")]
    for r in pmap(fetch, idx):
        if r.ok and r.body: pool += harvest(r.text, r.url)

    depth = lambda u: urllib.parse.urlsplit(u).path.strip("/").count("/")
    def leafy(pats, n, min_depth=1):
        got = sorted([u for u in pool if re.search(pats, u, re.I) and depth(u) >= min_depth],
                     key=lambda u: (-depth(u), len(u)))[:n]
        for u in got: pool.remove(u)
        return got

    urls = [root + "/"]
    urls += leafy(r"/(blog|news|posts?|articles?|insights?|changelog|release)/", 3)
    urls += leafy(r"/(docs?|guide|learn|tutorial|reference|api|help|kb|handbook)/", 2)
    urls += leafy(r"/(product|pricing|features?|solutions?|services?|platform|use-cases?)", 2, 0)
    if len(urls) < want:                              # anything left, deepest first
        rest = sorted(pool, key=lambda u: (-depth(u), len(u)))
        for u in rest:
            if len(urls) >= want: break
            if u not in urls: urls.append(u)
    return urls[:want]

# ── checks ─────────────────────────────────────────────────────────────────
def run(base, sample=8, verbose=False):
    origin, scope = scope_of(base)
    root = origin + scope
    ev, tier, notes = {}, {}, []
    def say(msg):
        if verbose: print("%s  %s%s" % (c.dim, msg, c.r), file=sys.stderr)

    say("discovering sample pages…")
    urls = discover(base, sample, verbose)
    say("fetching %d pages…" % len(urls))
    pages = dict(zip(urls, pmap(fetch, urls)))
    live = {u: r for u, r in pages.items() if r.ok and r.body}
    if not live:
        why = next((r.err for r in pages.values() if r.err), None)
        codes = sorted({r.status for r in pages.values() if r.status})
        raise RuntimeError("could not fetch %s — %s" % (base,
            why or ("all requests returned %s" % ", ".join(map(str, codes)) if codes else "no response")))
    n = len(live)

    home_html_early = live.get(root + "/", list(live.values())[0]).text

    # ── g.robots ──
    rb = fetch(origin + "/robots.txt")
    txt = rb.text if rb.ok else ""
    groups, cur = {}, None
    for line in txt.splitlines():
        line = line.split("#")[0].strip()
        if not line: continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent": cur = v.lower(); groups.setdefault(cur, [])
        elif cur is not None and k in ("allow", "disallow"): groups[cur].append((k, v))
    names = [u.lower() for u, _ in RETRIEVAL_UAS]
    named = [u for u, _ in RETRIEVAL_UAS if u.lower() in groups]
    def blocked(g):
        return any(k == "disallow" and v in ("/", "/*") for k, v in groups.get(g, []))
    star_block = blocked("*")
    any_block = star_block or any(blocked(u.lower()) for u, _ in RETRIEVAL_UAS)
    # 按 robots 规范，`Disallow:` 的空值就是「全部放行」——它是一条显式许可，不是「未表态」
    star_allow = any((k == "allow" and v in ("/", "/*")) or (k == "disallow" and v == "")
                     for k, v in groups.get("*", []))
    named_allow = [u for u in named if any((k == "allow") or (k == "disallow" and v == "")
                                           for k, v in groups.get(u.lower(), []))]
    if not rb.ok:
        tier["g.robots"] = 3
        ev["g.robots"] = "No robots.txt (HTTP %d). Nothing is disallowed, but nothing is explicitly allowed either." % rb.status
    elif any_block:
        tier["g.robots"] = 0
        ev["g.robots"] = "robots.txt (%d bytes) carries a Disallow that applies to retrieval crawlers." % len(rb.body)
    elif named_allow or star_allow:
        tier["g.robots"] = 5
        ev["g.robots"] = ("robots.txt (%d bytes): %s. No Disallow applies to retrieval crawlers."
                          % (len(rb.body), ("%d retrieval UAs named with an explicit permission" % len(named_allow))
                             if named_allow else "the wildcard group carries an explicit allow-all"))
    else:
        tier["g.robots"] = 3
        ev["g.robots"] = ("robots.txt (%d bytes, %d user-agent groups): none of the 10 retrieval UAs is named, "
                          "and no Allow directive is present — permitted by default, not by declaration."
                          % (len(rb.body), len(groups)))

    # ── g.reachable ──
    say("probing %d retrieval user-agents…" % len(RETRIEVAL_UAS))
    probe = list(live)[:3]
    results = pmap(lambda t: (t[0], fetch(t[1], t[2])),
                   [(name, u, ua) for name, ua in RETRIEVAL_UAS for u in probe])
    per = {}
    for name, r in results: per.setdefault(name, []).append(r)
    okc = sum(1 for name, rs in per.items() if all(x.ok for x in rs))
    base_len = {u: len(visible_text(live[u].text)) for u in probe}
    consistent = 0
    for name, rs in per.items():
        if not all(x.ok for x in rs): continue
        good = all(abs(len(visible_text(r.text)) - base_len[u]) <= max(400, base_len[u] * .25)
                   for u, r in zip(probe, rs))
        consistent += 1 if good else 0
    tier["g.reachable"] = 5 if okc == 10 and consistent == 10 else (0 if okc < 5 else 3)
    ev["g.reachable"] = ("%d of 10 retrieval user-agents returned 200 on %d sampled pages; "
                         "%d of those served content matching what a browser receives."
                         % (okc, len(probe), consistent))

    # ── g.ssr ──
    ssr = sum(1 for r in live.values() if wc(visible_text(main_html(r.text))) >= 120)
    tier["g.ssr"] = 5 if ssr == n else (3 if ssr >= max(1, n // 2) else 0)
    ev["g.ssr"] = "%d of %d sampled pages carry substantive body text in the HTML response with no JavaScript executed." % (ssr, n)

    # ── p1.sitemap ──
    # A site can live under a path — a GitHub Pages project page, a docs subtree, a
    # country folder. The spec puts sitemap.xml and llms.txt at the origin, but the
    # owner of example.com/docs cannot place a file at example.com. Scoring them zero
    # penalises them for something they do not control (open question #9), so fall
    # back to the path they were given. Origin still wins when both exist.
    sm_urls = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", txt) \
              or [origin + "/sitemap.xml", origin + "/sitemap_index.xml"] \
              + ([origin + scope + "/sitemap.xml"] if scope else [])
    sm = next((r for r in pmap(fetch, sm_urls[:4]) if r.ok), None)
    if sm and re.search(r"<sitemapindex", sm.text, re.I):
        child = re.findall(r"<loc>\s*([^<]+)", sm.text)[:1]
        if child:
            sub = fetch(child[0].strip())
            if sub.ok: sm = sub
    if not sm:
        tier["p1.sitemap"] = 0; ev["p1.sitemap"] = "No sitemap found via robots.txt or the conventional paths."
    else:
        locs = len(re.findall(r"<loc>", sm.text)); mods = len(re.findall(r"<lastmod>", sm.text))
        tier["p1.sitemap"] = 4 if locs and mods >= locs * .5 else 2
        ev["p1.sitemap"] = "Sitemap %s (%s): HTTP 200, %d <loc>, %d <lastmod>." % (
            "declared in robots.txt" if re.search(r"(?im)^\s*sitemap:", txt) else "at the conventional path",
            sm.url if hasattr(sm, "url") else "—", locs, mods)

    # ── p1.llms-txt ──
    lt = fetch(origin + "/llms.txt")
    lt_at = "/llms.txt"
    if not lt.ok and scope:
        alt = fetch(origin + scope + "/llms.txt")
        if alt.ok:
            lt, lt_at = alt, scope + "/llms.txt"
    if not lt.ok:
        tier["p1.llms-txt"] = 0
        ev["p1.llms-txt"] = ("/llms.txt returned HTTP %d%s." %
                             (lt.status, " (and none under %s either)" % scope if scope else ""))
    else:
        t = lt.text
        secs = re.findall(r"(?m)^##\s+(.+)$", t)
        with_links = 0
        parts = re.split(r"(?m)^##\s+.+$", t)[1:]
        for p in parts:
            if re.search(r"\[[^\]]+\]\([^)]+\)", p): with_links += 1
        has_def = bool(re.search(r"(?m)^>\s+\S", t)) or (len(parts) and wc(parts[0]) > 15) or wc(t.split("##")[0]) > 25
        tier["p1.llms-txt"] = 5 if (has_def and with_links >= 2) else (4 if has_def else 2)
        ev["p1.llms-txt"] = "%s: HTTP 200, %d bytes, %d '##' sections, %d of them containing links, site definition %s.%s" % (
            lt_at, len(lt.body), len(secs), with_links, "present" if has_def else "absent",
            " Found under the given path, not at the origin — the spec puts it at the origin,"
            " but a site living under a path cannot place a file there." if lt_at != "/llms.txt" else "")

    # ── p1.organization ──
    allld = {u: jsonld(r.text) for u, r in live.items()}
    org_pages = [u for u, o in allld.items() if "Organization" in types_of(o) or
                 any(str(x.get("@type", "")).endswith(("Corporation", "LocalBusiness")) for x in o)]
    site_pages = [u for u, o in allld.items() if "WebSite" in types_of(o)]
    orgs = [x for o in allld.values() for x in o
            if str(x.get("@type")) in ("Organization", "Corporation") or
               (isinstance(x.get("@type"), list) and "Organization" in x["@type"])]
    logo = next((o.get("logo") for o in orgs if o.get("logo")), None)
    logo_url = logo.get("url") if isinstance(logo, dict) else logo
    same = next((o.get("sameAs") for o in orgs if o.get("sameAs")), None)
    logo_ok = bool(logo_url) and fetch(urllib.parse.urljoin(root, logo_url), method="GET").ok
    if not org_pages and not site_pages:
        tier["p1.organization"] = 0; ev["p1.organization"] = "Neither Organization nor WebSite JSON-LD found on any sampled page."
    elif not (org_pages and site_pages):
        tier["p1.organization"] = 3
        ev["p1.organization"] = "Only %s found (%d of %d pages)." % (
            "Organization" if org_pages else "WebSite", len(org_pages or site_pages), n)
    elif logo_ok and same:
        tier["p1.organization"] = 6
        ev["p1.organization"] = "Organization + WebSite on %d of %d pages; logo resolves (HTTP 200); %d sameAs declared." % (
            len(org_pages), n, len(same) if isinstance(same, list) else 1)
    else:
        tier["p1.organization"] = 5
        ev["p1.organization"] = "Organization + WebSite on %d of %d pages; %s." % (
            len(org_pages), n, "logo does not resolve" if logo_url and not logo_ok
            else ("no sameAs declared" if not same else "logo absent"))

    # ── p1.breadcrumb ──
    # Nesting is relative to the scope the user gave, not to the origin. For a site at
    # example.com/docs, "docs/guide.html" is a top-level page of that site, not a nested
    # one — counting the prefix as hierarchy marks every page nested and then penalises
    # the site for missing breadcrumbs it does not need (open question #9).
    nested = [u for u in live if depth_in_scope(u, scope) >= 1]
    bc = [u for u in nested if "BreadcrumbList" in types_of(allld.get(u, []))]
    if not nested:
        tier["p1.breadcrumb"] = None; ev["p1.breadcrumb"] = "No nested pages in the sample — the check leaves the denominator."
    else:
        tier["p1.breadcrumb"] = 3 if len(bc) >= len(nested) * .5 else (2 if bc else 0)
        ev["p1.breadcrumb"] = "BreadcrumbList on %d of %d nested pages." % (len(bc), len(nested))

    # ── p1.page-type ──
    # Dataset belongs here: a page whose subject *is* a published dataset is stating its
    # type as precisely as a Product page does. Leaving it out silently penalised an
    # entire class of site — open data portals, research and government publishers.
    want_t = {"Product","Offer","FAQPage","HowTo","SoftwareApplication","Course","Recipe",
              "Event","JobPosting","Dataset"}
    hit = {u for u, o in allld.items() if types_of(o) & want_t}
    art = {u for u, o in allld.items() if types_of(o) & {"Article","BlogPosting","NewsArticle","TechArticle"}}
    tier["p1.page-type"] = 4 if len(hit | art) >= max(2, n * .5) else (2 if (hit or art) else 0)
    ev["p1.page-type"] = "Page-type schema (Product/Offer, FAQPage, HowTo, Article…) on %d of %d sampled pages." % (len(hit | art), n)

    # ── p2.answer-passages ──
    lo, hi = (50, 200) if any(is_cjk(r.text) for r in live.values()) else (25, 120)
    passed, examples = 0, []
    for u, r in live.items():
        for p in paragraphs(r.text)[:6]:
            if lo <= wc(p) <= hi and re.search(r"[.。!?！？]", p):
                passed += 1; examples.append((u, wc(p), p[:90])); break
    tier["p2.answer-passages"] = 9 if passed >= n * .75 else (7 if passed >= n * .5 else (4 if passed else 0))
    ev["p2.answer-passages"] = "%d of %d pages open with a self-contained passage of %d–%d %s.%s" % (
        passed, n, lo, hi, "characters" if lo == 50 else "words",
        (" e.g. “%s…”" % examples[0][2]) if examples else "")

    # ── p2.question-intent ──
    # a heading matches question intent if a person would phrase their question that way:
    # a question, a task, or an explanation. Not whether it carries a question mark.
    QP = re.compile(r"\b(how|what|why|when|where|which|who)\b|[?？]"
                    r"|^(get|getting|set|setting|add|adding|build|building|create|creating|use|using|"
                    r"install|installing|deploy|deploying|configure|connect|accept|send|manage|migrate|"
                    r"write|writing|run|running|test|testing|choose|handle|customi[sz]e)\b"
                    r"|怎么|如何|什么|为什么|是否|多少|入门|教程|指南", re.I)
    NAV = re.compile(r"^\s*(\w+\s*[|｜·]\s*\w+|\w{1,12})\s*$")
    qi = 0
    for u, r in live.items():
        hs = [h for h in headings(r.text) if 3 <= len(h) <= 120]
        if any(QP.search(h) and not NAV.match(h) for h in hs): qi += 1
    tier["p2.question-intent"] = 7 if qi >= n * .75 else (5 if qi >= n * .5 else (3 if qi else 0))
    ev["p2.question-intent"] = "%d of %d pages carry at least one heading phrased as a question, a task or an explanation." % (qi, n)

    # ── p2.freshness ──
    fr = 0
    for u, r in live.items():
        o = allld.get(u, [])
        if any(x.get("dateModified") or x.get("datePublished") for x in o) or \
           re.search(r'<time[^>]+datetime=', r.text, re.I) or \
           re.search(r'property=["\']article:(published|modified)_time', r.text, re.I) or \
           re.search(r"\b(20[12]\d)[-/年]\s*\d{1,2}[-/月]\s*\d{1,2}", visible_text(main_html(r.text))[:3000]):
            fr += 1
    dm = sum(1 for o in allld.values() if any(x.get("dateModified") for x in o))
    tier["p2.freshness"] = 6 if (fr >= n * .75 and dm) else (3 if fr else 0)
    ev["p2.freshness"] = "%d of %d pages carry a date a reader or a crawler can see; %d declare dateModified." % (fr, n, dm)

    # ── p2.sourced-stats ──
    pages_with_nums = pages_sourced = tot_num = cited = 0
    for u, r in live.items():
        body = main_html(r.text)
        vis = visible_text(body)
        nums = re.findall(r"(?<![\w-])(\d[\d,.]*\s?%|[$€£¥]\s?\d[\d,.]*|\d[\d,.]{2,})(?![\w-])", vis)
        # attribution near a figure: an outbound link, a cite/blockquote, a footnote marker,
        # or an explicit source phrase
        att = (len(re.findall(r"<(cite|blockquote)\b", body, re.I))
               + len(re.findall(r"(?:source|sources|study|studies|report|research|survey|"
                                r"according to|数据来源|来源|资料来源|据.{0,6}报告)\s*[::]?", vis, re.I))
               + len(re.findall(r'<a\b[^>]+href=["\']https?://(?!%s)' % re.escape(host_stem(root)), body, re.I)))
        tot_num += len(nums); cited += att
        if len(nums) >= 3:
            pages_with_nums += 1
            if att >= 2: pages_sourced += 1
    if pages_with_nums == 0:
        tier["p2.sourced-stats"] = 3
        ev["p2.sourced-stats"] = "Few numeric claims in the sample (%d figures), so there is little to attribute." % tot_num
    else:
        f = pages_sourced / pages_with_nums
        tier["p2.sourced-stats"] = 7 if f >= .75 else (5 if f >= .5 else (3 if pages_sourced else 0))
        ev["p2.sourced-stats"] = ("%d figures across the sample; of the %d pages carrying several, "
                                  "%d place a source, citation or outbound reference beside them."
                                  % (tot_num, pages_with_nums, pages_sourced))

    # ── p2.named-author ──
    BRANDY = re.compile(r"^(team|staff|editор|editorial|admin|support|the .+ team|.*官方|.*团队|.*小编)$", re.I)
    named, linked = 0, 0
    for u, r in live.items():
        auth = None
        for x in allld.get(u, []):
            a = x.get("author")
            if isinstance(a, list): a = a[0] if a else None
            if isinstance(a, dict) and a.get("name"): auth = a; break
            if isinstance(a, str) and a.strip(): auth = {"name": a}; break
        if not auth:
            m = re.search(r'(?:rel=["\']author["\'][^>]*>|by\s+)([A-Z][\w.\-]+(?:\s+[A-Z][\w.\-]+){0,2})', r.text)
            if m: auth = {"name": m.group(1)}
        if auth and auth.get("name") and not BRANDY.match(auth["name"].strip()):
            named += 1
            if auth.get("url") or auth.get("sameAs"): linked += 1
    tier["p2.named-author"] = 6 if linked >= max(1, named * .5) and named else (3 if named else 0)
    ev["p2.named-author"] = "%d of %d pages carry a personal byline; %d link that name to a verifiable identity page." % (named, n, linked)

    # ── p3.sameas ──
    sa = same if isinstance(same, list) else ([same] if same else [])
    if not sa:
        tier["p3.sameas"] = 0; ev["p3.sameas"] = "No sameAs declared on the Organization entity."
    else:
        res = pmap(lambda u: fetch(u, method="GET"), sa[:8])
        good = sum(1 for r in res if r.ok)
        tier["p3.sameas"] = 3 if good == len(res) else (2 if good else 0)
        ev["p3.sameas"] = "%d sameAs declared, %d of the first %d resolve to HTTP 200." % (len(sa), good, len(res))

    # ── p3.video ──
    blob = " ".join(r.text for r in live.values())
    vt = sum(1 for o in allld.values() if "VideoObject" in types_of(o))
    chan = len(re.findall(r"(?:youtube\.com/(?:@|c/|channel/|user/)|bilibili\.com/\d{4,}|"
                          r"space\.bilibili\.com/|vimeo\.com/[a-z0-9-]{3,})", blob, re.I))
    embeds = len(re.findall(r"(youtube\.com/embed|youtu\.be/|player\.vimeo\.com|player\.bilibili)", blob, re.I))
    tier["p3.video"] = 3 if (vt and (chan or embeds)) else (2 if (chan or embeds or vt) else 0)
    ev["p3.video"] = ("%d pages declare VideoObject; %d official channel links and %d embedded players "
                      "in the sample." % (vt, chan, embeds))

    # ── p4.answer-shape ──
    shaped = 0
    for u, r in live.items():
        b = main_html(r.text)
        hs = len(re.findall(r"<h[23]\b", b, re.I)); li = len(re.findall(r"<li\b", b, re.I))
        tb = len(re.findall(r"<table\b", b, re.I))
        ps = [wc(p) for p in paragraphs(r.text)] or [0]
        avg = sum(ps) / len(ps)
        if hs >= 2 and (li >= 3 or tb) and avg <= (160 if lo == 50 else 90): shaped += 1
        elif hs >= 2: shaped += 0.5
    tier["p4.answer-shape"] = 4 if shaped >= n * .6 else (2 if shaped else 0)
    ev["p4.answer-shape"] = "%.0f of %d pages carry subheadings plus lists or tables, with paragraphs of workable length." % (shaped, n)

    # ── p4.cn-engines ──
    cjk_site = any(is_cjk(r.text) for r in live.values()) or ".cn" in root
    if not cjk_site:
        tier["p4.cn-engines"] = None
        ev["p4.cn-engines"] = "Site does not address the Chinese market — the check leaves the denominator."
    else:
        cn = pmap(lambda t: fetch(root + "/", t[1]), CN_UAS)
        okc2 = sum(1 for r in cn if r.ok)
        icp = bool(re.search(r"ICP备|京ICP|沪ICP|粤ICP", " ".join(r.text for r in live.values())))
        tier["p4.cn-engines"] = 2 if okc2 == len(CN_UAS) and icp else (1 if okc2 else 0)
        ev["p4.cn-engines"] = "%d of %d Chinese crawlers reached the home page; ICP filing %s." % (
            okc2, len(CN_UAS), "shown" if icp else "not shown")

    # ── p3.knowledge-graph (Wikidata + Wikipedia, both public APIs, no key) ──
    stem = host_stem(root)
    cands = []
    for o in orgs:
        for k in ("legalName", "name", "alternateName"):
            v = o.get(k)
            if isinstance(v, list): v = v[0] if v else None
            if isinstance(v, str) and v.strip(): cands.append(v.strip())
    m = re.search(r'property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)', home_html_early, re.I) \
        or re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:site_name', home_html_early, re.I)
    if m: cands.append(html.unescape(m.group(1)).strip())
    m = re.search(r"<title\b[^>]*>(.*?)</title>", home_html_early, re.S | re.I)
    if m:
        title = visible_text(m.group(1))
        # a title is usually "Brand | tagline" or "Page \ Brand" — try every segment,
        # and prefer whichever one the domain itself is named after
        segs = [x.strip() for x in re.split(r"[|｜·•·\\/—–:»<>~]+|\s[-–]\s", title) if x.strip()]
        segs.sort(key=lambda x: (stem not in x.lower().replace(" ", ""), len(x)))
        cands += segs[:3]
    cands.append(stem.capitalize())
    seen_c, brands = set(), []
    for x in cands:
        k = x.lower()
        if k in seen_c or len(x) > 60 or len(x) < 2: continue
        seen_c.add(k); brands.append(x)
    brands = brands[:3]

    langs = ["zh", "en"] if lo == 50 else ["en"]
    kg_where, brand, kg_queries, kg_ok = [], brands[0] if brands else stem, 0, 0
    for cand in brands:
        q = urllib.parse.quote(cand)
        for lg in langs:
            wd = fetch("https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json"
                       "&language=%s&uselang=%s&limit=5&search=%s" % (lg, lg, q))
            kg_queries += 1; kg_ok += 1 if wd.ok else 0
            if wd.ok:
                try:
                    for it in json.loads(wd.text).get("search", []):
                        if (it.get("label", "") or "").strip().lower() == cand.lower():
                            kg_where.append("Wikidata %s (%s)" % (it.get("id"), it.get("description", "")[:40]))
                            break
                except Exception: pass
            wp = fetch("https://%s.wikipedia.org/w/api.php?action=query&format=json&list=search"
                       "&srlimit=3&srsearch=%s" % (lg, q))
            kg_queries += 1; kg_ok += 1 if wp.ok else 0
            if wp.ok:
                try:
                    for it in json.loads(wp.text).get("query", {}).get("search", []):
                        if (it.get("title", "") or "").strip().lower() == cand.lower():
                            kg_where.append("%s.wikipedia: %s" % (lg, it.get("title"))); break
                except Exception: pass
        if kg_where: brand = cand; break
    also = "" if len(brands) < 2 else " (also tried %s)" % ", ".join(repr(x) for x in brands if x != brand)
    if kg_where:
        tier["p3.knowledge-graph"] = 4
        ev["p3.knowledge-graph"] = "Brand read as %r%s. Entity found — %s" % (brand, also, "; ".join(kg_where[:2]))
    elif kg_ok == 0 and kg_queries:
        # every lookup failed — that is our blind spot, not an absent entity
        tier["p3.knowledge-graph"] = None
        ev["p3.knowledge-graph"] = ("Brand read as %r%s. All %d Wikidata and Wikipedia lookups failed to "
                                    "respond, so this check is unobservable rather than zero." % (brand, also, kg_queries))
    else:
        tier["p3.knowledge-graph"] = 0
        ev["p3.knowledge-graph"] = ("Brand read as %r%s. No entity whose label matches exactly, in Wikidata "
                                    "or Wikipedia (%s); %d of %d lookups answered."
                                    % (brand, also, "/".join(langs), kg_ok, kg_queries))

    # ── judgement-bound checks ──
    for k in NEEDS_JUDGEMENT:
        tier[k] = None
        ev[k] = "Not observable without off-site search — run the Claude Code skill or score it by hand."

    # ── bonus ──
    bon = {}
    # Same subpath rule as p1.llms-txt: origin first, then the path the user gave.
    # robots.txt deliberately stays origin-only — it genuinely is origin-scoped, and a
    # site under a path has no robots.txt of its own to offer. That asymmetry is real
    # and documented in rubric/open-questions.md #9.
    def at_origin_or_scope(rel):
        r = fetch(origin + rel)
        if not r.ok and scope:
            alt = fetch(origin + scope + rel)
            if alt.ok:
                return alt
        return r
    lf = at_origin_or_scope("/llms-full.txt"); bon["b.llms-full"] = 2 if lf.ok else 0
    at = at_origin_or_scope("/ai.txt")
    at2 = at_origin_or_scope("/.well-known/ai.txt") if not at.ok else at
    bon["b.ai-txt"] = 2 if at2.ok else 0
    home_html = home_html_early
    bon["b.geo-link"] = 1 if re.search(r'<link[^>]+rel=["\'](?:llms|ai-content|alternate)["\'][^>]*type=["\']text/(?:plain|markdown)', home_html, re.I) else 0
    bon["b.speakable"] = 1 if any("SpeakableSpecification" in json.dumps(o) for o in allld.values()) else 0

    return dict(root=root, urls=list(live), tier=tier, ev=ev, bonus=bon,
                lang="zh-CN" if lo == 50 else "en", robots_bytes=len(rb.body))

# ── scoring & output ───────────────────────────────────────────────────────
def score(res):
    got = den = 0; gate_zero = False
    rows = []
    for cid, pil, name, pts, tiers in SPEC:
        t = res["tier"].get(cid)
        if t is None:
            rows.append((cid, pil, name, None, pts, res["ev"].get(cid, ""))); continue
        got += t; den += pts
        if cid.startswith("g.") and t == 0: gate_zero = True
        rows.append((cid, pil, name, t, pts, res["ev"].get(cid, "")))
    b = min(sum(res["bonus"].values()), BONUS_CAP)
    total = got + b
    norm = round(100 * total / den) if den else 0
    if gate_zero: norm = min(norm, GATE_CAP)
    return rows, total, den, b, norm, band(norm), gate_zero

def bar(t, mx, w=18):
    if t is None: return c.grey + "·" * w + c.r
    f = round(w * t / mx)
    col = c.green if t == mx else (c.amber if t else c.red)
    return col + "█" * f + c.grey + "░" * (w - f) + c.r

def write_badge(res, path):
    """An SVG anyone can commit next to their own README. Shields-shaped so it sits
    happily beside the build badges people already have."""
    _, _, _, _, norm, bd, _ = score(res)
    col = ("#2f8f52" if norm >= 66 else "#a08020" if norm >= 51 else
           "#b06b30" if norm >= 31 else "#a33")
    right = "%d/100 %s" % (norm, bd)
    lw = 88                                  # "AIV readiness" at 11px Verdana
    rw = int(6.4 * len(right)) + 16
    w = lw + rw
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%(w)d" height="20" role="img"'
        ' aria-label="AIV readiness: %(right)s">'
        '<title>AIV readiness: %(right)s</title>'
        '<linearGradient id="s" x2="0" y2="100%%">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".7"/>'
        '<stop offset=".1" stop-color="#aaa" stop-opacity=".1"/>'
        '<stop offset=".9" stop-color="#000" stop-opacity=".3"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".5"/></linearGradient>'
        '<clipPath id="c"><rect width="%(w)d" height="20" rx="3" fill="#fff"/></clipPath>'
        '<g clip-path="url(#c)">'
        '<rect width="%(lw)d" height="20" fill="#1E5C46"/>'
        '<rect x="%(lw)d" width="%(rw)d" height="20" fill="%(col)s"/>'
        '<rect width="%(w)d" height="20" fill="url(#s)"/></g>'
        '<g fill="#fff" text-anchor="middle"'
        ' font-family="Verdana,DejaVu Sans,Geneva,sans-serif" font-size="11">'
        '<text x="%(lx)d" y="15" fill="#010101" fill-opacity=".3">AIV readiness</text>'
        '<text x="%(lx)d" y="14">AIV readiness</text>'
        '<text x="%(rx)d" y="15" fill="#010101" fill-opacity=".3">%(right)s</text>'
        '<text x="%(rx)d" y="14">%(right)s</text></g></svg>'
    ) % dict(w=w, lw=lw, rw=rw, col=col, right=right, lx=lw // 2, rx=lw + rw // 2)
    io.open(path, "w", encoding="utf-8").write(svg)
    return path, norm, bd

def share_line(res):
    """One line someone can paste somewhere. Short enough for a post, specific enough
    to mean something — the score, the band, and the single biggest gap."""
    rows, total, den, b, norm, bd, capped = score(res)
    host = urllib.parse.urlsplit(res["root"]).netloc.replace("www.", "") + \
           urllib.parse.urlsplit(res["root"]).path
    gaps = sorted([(mx - t, name) for _, _, name, t, mx, _ in rows
                   if t is not None and t < mx], reverse=True)
    top = gaps[0] if gaps else None
    line = "%s scores %d/100 (%s) for AI answer-engine readiness." % (host, norm, bd)
    if capped:
        line += " Gate-capped — a retrieval crawler cannot reach the content at all."
    elif top:
        line += " Biggest gap: %s (+%d)." % (top[1].lower(), top[0])
    return line + " Measured with the open AIV rubric — github.com/jianruntech/geo-score"

def brief(res):
    """Pillar totals and the three biggest gaps. What fits in a screenshot."""
    rows, total, den, b, norm, bd, capped = score(res)
    nxt = [(t, n) for t, n in BANDS if t > norm]
    gap = (min(nxt)[0] - norm, min(nxt, key=lambda x: x[0])[1]) if nxt else None
    big = c.green if norm >= 66 else (c.amber if norm >= 31 else c.red)
    print()
    print("  %s%sAIV READINESS%s  %s" % (c.b, c.brass, c.r, res["root"]))
    print(c.grey + "─" * 58 + c.r)
    print("  %s%s%d / 100%s   %s%s%s%s" % (c.b, big, norm, c.r, c.b, big, bd, c.r)
          + ("%s          %d points to %s%s" % (c.grey, gap[0], gap[1], c.r) if gap else ""))
    if capped: print("  %sGATE CAPPED — a gate check scored zero%s" % (c.red, c.r))
    print()
    for pil in dict.fromkeys(r[1] for r in rows):
        rs = [r for r in rows if r[1] == pil]
        got = sum(r[3] for r in rs if r[3] is not None)
        mx = sum(r[4] for r in rs if r[3] is not None)
        marks = "".join((c.grey + "⊘" + c.r) if r[3] is None else
                        (c.green + "✓" + c.r if r[3] == r[4] else
                         (c.red + "✗" + c.r if r[3] == 0 else c.amber + "◐" + c.r)) for r in rs)
        print("  %-20s %s%6s%s   %s" % (pil, c.dim, ("%d/%d" % (got, mx)) if mx else "—", c.r, marks))
    gaps = sorted([(mx - t, name) for _, _, name, t, mx, _ in rows
                   if t is not None and t < mx], reverse=True)[:3]
    if gaps:
        print()
        print("  %sBiggest gaps%s" % (c.b, c.r))
        for d, name in gaps:
            print("   %s+%-2d%s  %s" % (c.brass, d, c.r, name))
    print()

def report(res, args):
    rows, total, den, b, norm, bd, capped = score(res)
    nxt = [(t, n) for t, n in BANDS if t > norm]
    gap = (min(nxt)[0] - norm, min(nxt, key=lambda x: x[0])[1]) if nxt else None
    W = 74
    print()
    print("%s%s  AIV READINESS  %s%s" % (c.b, c.brass, res["root"], c.r))
    print(c.grey + "─" * W + c.r)
    big = c.green if norm >= 66 else (c.amber if norm >= 31 else c.red)
    print("  %s%s%d%s%s / 100%s   %s%s%s%s" % (c.b, big, norm, c.r, c.grey, c.r, c.b, big, bd, c.r))
    if gap: print("  %s%d points to %s%s" % (c.grey, gap[0], gap[1], c.r))
    if capped: print("  %sGATE CAPPED — a gate check scored zero%s" % (c.red, c.r))
    print()
    cur = None
    for cid, pil, name, t, mx, e in rows:
        if pil != cur:
            cur = pil
            sub = sum(r[3] for r in rows if r[1] == pil and r[3] is not None)
            smx = sum(r[4] for r in rows if r[1] == pil and r[3] is not None)
            print("  %s%s%s %s%s%s" % (c.b, pil, c.r, c.grey, "%d/%d" % (sub, smx) if smx else "—", c.r))
        mark = (c.grey + "⊘" + c.r) if t is None else (
            c.green + "✓" + c.r if t == mx else (c.red + "✗" + c.r if t == 0 else c.amber + "◐" + c.r))
        print("   %s %-32s %s %s%s%s" % (mark, name[:32], bar(t, mx),
              c.grey, ("  —" if t is None else "%2d/%d" % (t, mx)), c.r))
        if args.explain:
            if t is not None:
                tr = tier_reason(cid, t, mx)
                if tr: print("      %s%s%s" % (c.brass, tr[:112], c.r))
            if e: print("      %s%s%s" % (c.dim, e[:112], c.r))
    gaps = sorted([(mx - t, cid, name, tier_reason(cid, t, mx))
                   for cid, pil, name, t, mx, e in rows if t is not None and t < mx],
                  reverse=True)[:3]
    if gaps:
        print("  %sBiggest gaps%s" % (c.b, c.r))
        for d, cid, name, tr in gaps:
            need = tr.split("needs: ", 1)[-1] if "needs: " in tr else ""
            print("   %s+%-2d%s  %-32s %s%s%s" % (c.brass, d, c.r, name, c.grey, need[:60], c.r))
        print()
    if b: print("  %s+%d bonus%s (outside the denominator)" % (c.brass, b, c.r))
    skipped = [r for r in rows if r[3] is None]
    print("  %sScored %d / %d observable · %d checks left the denominator · rubric %s%s"
          % (c.grey, total, den, len(skipped), RUBRIC, c.r))
    if skipped:
        print("  %sNeeds judgement: %s%s" % (c.grey, ", ".join(r[0] for r in skipped), c.r))
    print()
    print("  %sFull rubric and what each tier means:%s" % (c.grey, c.r))
    print("  %shttps://github.com/jianruntech/geo-score%s" % (c.brass, c.r))
    print()

def as_json(res):
    rows, total, den, b, norm, bd, capped = score(res)
    return dict(rubric_version=RUBRIC, tool="geo-score-cli/%s" % __version__,
        audited_at=time.strftime("%Y-%m-%d"),
        target=res["root"], audience_language=res["lang"], sampled_urls=res["urls"],
        readiness=total, observable_max=den, normalised=norm, band=bd,
        gate_capped=capped, bonus_awarded=b,
        checks=[dict(id=cid, state="scored" if t is not None else "unobservable",
                     **({"points": t, "max": mx, "evidence": e,
                         "tier_reason": tier_reason(cid, t, mx)}
                        if t is not None else {"reason": e}))
                for cid, pil, name, t, mx, e in rows]
               + [dict(id=bid, state="scored", points=res["bonus"].get(bid, 0), max=bpts,
                       evidence="Bonus check, outside the denominator.")
                  for bid, bname, bpts in BONUS],
        notes=["Scored by the geo-score CLI, which measures what a static fetch can observe. "
               "Checks needing off-site search or human judgement left the denominator."])

def _try(u, sample):
    try: return run(u, sample)
    except Exception as e:
        print("%s  %s — %s%s" % (c.red, u, e, c.r), file=sys.stderr); return None

def compare(pairs, args):
    """Two or more sites, check by check. The column that matters is the difference."""
    cols = []
    for u, res in pairs:
        rows, total, den, b, norm, bd, capped = score(res)
        cols.append(dict(host=urllib.parse.urlsplit(u).netloc.replace("www.", ""),
                         rows={r[0]: r for r in rows}, norm=norm, band=bd, total=total, den=den))
    w = max(22, max(len(c_["host"]) for c_ in cols) + 2)
    print()
    print("  %s%-35s%s%s" % (c.b, "AIV READINESS", "".join(("%-" + str(w) + "s") % x["host"] for x in cols), c.r))
    print(c.grey + "─" * (35 + w * len(cols)) + c.r)
    best = max(x["norm"] for x in cols)
    line = ""
    for x in cols:
        col = c.green if x["norm"] == best else c.grey
        line += ("%s%-" + str(w) + "s%s") % (col, "%d  %s" % (x["norm"], x["band"]), c.r)
    print("  %-35s%s" % ("", line))
    print()
    cur = None
    for cid, pil, name, _t, mx, _e in [r for r in cols[0]["rows"].values()]:
        if pil != cur:
            cur = pil; print("  %s%s%s" % (c.b, pil, c.r))
        cells = ""
        vals = [x["rows"].get(cid, (None,) * 6)[3] for x in cols]
        top = max([v for v in vals if v is not None], default=None)
        for v in vals:
            if v is None: txt, col = "—", c.grey
            else:
                txt = "%d/%d" % (v, mx)
                col = c.green if v == top and top == mx else (c.grey if v == top else c.red)
            cells += ("%s%-" + str(w) + "s%s") % (col, txt, c.r)
        gap = [v for v in vals if v is not None]
        mark = " " if (not gap or max(gap) == min(gap)) else c.brass + "›" + c.r
        print("   %s %-33s%s" % (mark, name[:32], cells))
    print()
    lead, trail = cols[0], None
    for x in cols[1:]:
        if trail is None or x["norm"] > trail["norm"]: trail = x
    if trail:
        wins = [(cols[0]["rows"][k][4] - (cols[0]["rows"][k][3] or 0)) - (trail["rows"][k][4] - (trail["rows"][k][3] or 0))
                for k in cols[0]["rows"]
                if cols[0]["rows"][k][3] is not None and trail["rows"].get(k, (None,)*6)[3] is not None]
        behind = sorted([(trail["rows"][k][3] - cols[0]["rows"][k][3], cols[0]["rows"][k][2])
                         for k in cols[0]["rows"]
                         if cols[0]["rows"][k][3] is not None and trail["rows"].get(k, (None,)*6)[3] is not None
                         and trail["rows"][k][3] > cols[0]["rows"][k][3]], reverse=True)[:3]
        if behind:
            print("  %sWhere %s is ahead of you%s" % (c.b, trail["host"], c.r))
            for d, nm in behind:
                print("   %s+%-2d%s  %s" % (c.brass, d, c.r, nm))
            print()
    print("  %sBoth scored with rubric %s · https://github.com/jianruntech/geo-score%s" % (c.grey, RUBRIC, c.r))
    print()

def main():
    ap = argparse.ArgumentParser(prog="geo-score",
        description="Score a site 0-100 on whether AI answer engines can find, parse, trust and cite it.")
    ap.add_argument("url")
    ap.add_argument("--json", action="store_true", help="machine-readable output (schema/report.v2.json)")
    ap.add_argument("--explain", "-e", action="store_true", help="show the evidence behind every check")
    ap.add_argument("--brief", action="store_true", help="pillar totals and the three biggest gaps only")
    ap.add_argument("--share", action="store_true",
                    help="print a one-line summary sized for a post, and the badge markdown")
    ap.add_argument("--badge", metavar="FILE", nargs="?", const="aiv-badge.svg",
                    help="also write an embeddable SVG badge (default aiv-badge.svg)")
    ap.add_argument("--sample", type=int, default=8, metavar="N", help="pages to sample (default 8)")
    ap.add_argument("--compare", metavar="URL", action="append",
                    help="also score this site and show the two side by side. Repeatable.")
    ap.add_argument("--fail-under", type=int, metavar="N", help="exit 1 if the score is below N (for CI)")
    ap.add_argument("--quiet", "-q", action="store_true")
    ap.add_argument("--version", action="version", version="geo-score %s (rubric %s)" % (__version__, RUBRIC))
    a = ap.parse_args()
    url = a.url if "://" in a.url else "https://" + a.url
    if not a.json and not a.quiet:
        print("%s  scoring %s …%s" % (c.dim, url, c.r), file=sys.stderr)
    targets = [url] + [(u if "://" in u else "https://" + u) for u in (a.compare or [])]
    if len(targets) > 1:
        done = pmap(lambda u: (u, _try(u, a.sample)), targets, workers=min(4, len(targets)))
        ok = [(u, r) for u, r in done if r is not None]
        if not ok: raise RuntimeError("none of the given sites could be fetched")
        if a.json:
            print(json.dumps([as_json(r) for _, r in ok], ensure_ascii=False, indent=2))
        else:
            compare(ok, a)
        res = ok[0][1]
    else:
        res = run(url, a.sample, verbose=not a.quiet and not a.json)
        if a.json:
            print(json.dumps(as_json(res), ensure_ascii=False, indent=2))
        elif a.brief:
            brief(res)
        else:
            report(res, a)
    if a.share:
        line = share_line(res)
        if not a.json:
            print("  %sShare this%s" % (c.b, c.r))
            print("  %s%s%s" % (c.dim, line, c.r))
            print()
            print("  %sBadge for your README:%s" % (c.grey, c.r))
            print("  %s![AIV readiness](aiv-badge.svg)%s  "
                  "%s(generate it with --badge)%s" % (c.dim, c.r, c.grey, c.r))
            print()
    if a.badge:
        pth, nrm, bnd = write_badge(res, a.badge)
        if not a.json:
            print("  %sbadge%s %s  —  %d/100 %s" % (c.brass, c.r, pth, nrm, bnd))
            print("  %sMarkdown:%s ![AIV readiness](%s)" % (c.grey, c.r, os.path.basename(pth)))
            print()
    if a.fail_under is not None:
        _, _, _, _, norm, _, _ = score(res)
        if norm < a.fail_under:
            print("%sgeo-score %d is below --fail-under %d%s" % (c.red, norm, a.fail_under, c.r), file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except RuntimeError as e:
        print("%s%s%s" % (c.red, e, c.r), file=sys.stderr)
        sys.exit(2)
