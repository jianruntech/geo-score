#!/usr/bin/env python3
"""Round 0 of the preregistered validation study: categories and their sampling frames.

Writes benchmark/prereg/round0/categories.json from fixed English Wikipedia revisions and Wikidata, as
PREREGISTRATION.md section 5.1 asks: for each category, the vendors with their own website that a public list or
comparison article names, plus the benchmark/sites.json sites that sell in the category, deduplicated, with every
exclusion and its reason; a frame above 15 candidates is cut to 15 by a seeded draw.

    python3 benchmark/prereg/round0/build_frames.py --cache DIR        # fetch (or reuse DIR) and write the file
    python3 benchmark/prereg/round0/build_frames.py --cache DIR --check  # rebuild in memory and compare

Articles are read at the revision recorded in SPECS, so the rows are fixed. Websites come from Wikidata's official
website (P856) of the item each row links to; each item's revision is recorded (`wd_lastrevid`) because Wikidata
moves. Only names, domains and sectors are read from benchmark/sites.json, never a score. Standard library only.
"""
import argparse, hashlib, io, json, os, random, re, sys, time, urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, "categories.json")
API = "https://en.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"
UA = "geo-score-prereg/round0 (https://github.com/jianruntech/geo-score; preregistered study frames)"
MAX_FRAME = 15
SEED_TEXT = "geo-score prereg round0 frame|%s"
# hosts that are not a vendor's own website (PREREGISTRATION.md section 5.1: "vendors with their own website")
NOT_OWN = ("github.com", "gitlab.com", "sourceforge.net", "bitbucket.org", "web.archive.org", "sites.google.com",
           "wiki.gnome.org", "projects.gnome.org", "savannah.nongnu.org", "apps.apple.com", "play.google.com",
           "facebook.com", "twitter.com", "x.com", "linkedin.com")
SKIP_SECTIONS = ("See also", "References", "Notes", "External links", "Further reading", "Bibliography", "Sources")
GENERIC_CC = ("us", "io", "ai", "co", "me", "tv", "app", "fm", "ly", "gg", "so", "to", "md", "sh", "cc")
ENGLISH = ("Q1860", "Q20923490")        # Wikidata: English; multiple languages
# Where Wikidata's only website is a country site of a company whose site for buyers in the US is another domain
WEBSITE_OVERRIDES = {
    "Q1357556": ("https://www.rosettastone.com/", "Wikidata lists only rosettastone.fr, the French site of a US company"),
    "Q3347505": ("https://www.occstrategy.com/", "Wikidata lists only occstrategy.fr, one office of a firm whose main "
                                                 "site is occstrategy.com"),
}
# public suffixes that geo_watch.site_domain does not know: a host under one is owned at three labels
EXTRA_SUFFIXES = ("napoli.it",)

# Each category: a one-sentence definition for a buyer in the US, the article and revision that is its public list,
# which rows of it name the vendors (rule), and the benchmark/sites.json sites matched to it by hand (sites_in: the
# site sells the category's product to buyers in the US; sites_out: considered and left out, with the reason).
# `same_vendor` names a sites.json site that is a listed vendor's own site under another domain: the two are one
# candidate, scored at the sites.json site, with both domains counting as the vendor's.
SPECS = [
    {"id": "large-language-models", "name": "Large language models",
     "definition": "Large language models that people and businesses in the US use through an app or an API, and "
                   "the companies that develop them.",
     "article": "List of large language models", "revid": 1378988796,
     "rule": {"mode": "table", "col": 2, "describe": "every table; the Developer column (third)"},
     "sites_in": ["anthropic.com", "cohere.com", "mistral.ai", "openai.com", "deepseek.com", "01.ai", "deepmind.google",
                  "huggingface.co", "cursor.com", "perplexity.ai", "stepfun.com"],
     "same_vendor": {"cursor.com": "anysphere.inc"},
     "sites_out": {"moonshot.cn": "the China-market site; Moonshot AI is listed with moonshot.ai",
                   "minimaxi.com": "the China-market site; MiniMax is listed with minimax.io",
                   "bigmodel.cn": "the China-market site of Zhipu; Z.ai is listed with z.ai",
                   "zhipuai.cn": "the China-market site of Zhipu; Z.ai is listed with z.ai",
                   "baichuan-ai.com": "sells its models in the China market only",
                   "iflytek.com": "no language model offered to US buyers",
                   "sensetime.com": "no language model offered to US buyers",
                   "megvii.com": "no language model offered to US buyers",
                   "unisound.com": "no language model offered to US buyers",
                   "together.ai": "hosts other developers' models", "fireworks.ai": "hosts other developers' models",
                   "groq.com": "hosts other developers' models", "openrouter.ai": "routes to other developers' models",
                   "replicate.com": "hosts other developers' models", "baseten.co": "hosts other developers' models",
                   "modal.com": "compute platform, no model of its own",
                   "windsurf.com": "a code editor; its models are listed under Cognition AI (cognition.ai)"}},
    {"id": "ai-video-generators", "name": "AI video generators",
     "definition": "AI models and apps that generate video from text or images, offered to creators and businesses "
                   "in the US.",
     "article": "Text-to-video model", "revid": 1378271382,
     "rule": {"mode": "table", "col": 1, "sections": ["Comparison of models"],
              "describe": "section 'Comparison of models'; the Company column (second)"},
     "sites_in": ["runway.com", "pika.art", "lumalabs.ai", "midjourney.com", "deepmind.google", "openai.com",
                  "bytedance.com", "alibabagroup.com"],
     "same_vendor": {"runway.com": "runwayml.com", "deepmind.google": "about.google"},
     "sites_out": {"minimaxi.com": "the China-market site of MiniMax, which the table does not list",
                   "ideogram.ai": "images only", "elevenlabs.io": "audio", "suno.com": "music"}},
    {"id": "vector-databases", "name": "Vector databases",
     "definition": "Databases that store and search vector embeddings, offered to developers and businesses in "
                   "the US.",
     "article": "Vector database", "revid": 1374243120,
     "rule": {"mode": "table", "col": 0, "sections": ["Implementations"],
              "describe": "section 'Implementations'; the Name column (first)"},
     "sites_in": ["pinecone.io", "weaviate.io", "upstash.com", "supabase.com", "clickhouse.com", "llamaindex.ai"],
     "sites_out": {"neon.com": "a Postgres service; vector search is an extension, not a product of its own",
                   "turso.tech": "a SQLite service; vector search is a feature, not a product of its own",
                   "tigerdata.com": "a Postgres service; vector search is an extension, not a product of its own",
                   "planetscale.com": "a MySQL and Postgres service; vector search is a feature"}},
    {"id": "cloud-infrastructure", "name": "Cloud infrastructure",
     "definition": "Public cloud infrastructure (virtual machines, storage and networking) that businesses in the US "
                   "rent.",
     "article": "Cloud-computing comparison", "revid": 1365802661,
     "rule": {"mode": "table", "col": 0, "sections": ["General"], "section_occurrence": 0, "table_index": [0],
              "describe": "the first section 'General', its first table; the Provider column (first)"},
     "sites_in": ["digitalocean.com"],
     "sites_out": {"aliyun.com": "the China-market site; Alibaba Cloud is listed with intl.aliyun.com",
                   "baidubce.com": "China-market cloud", "ctyun.cn": "China-market cloud",
                   "huaweicloud.com": "not offered to buyers in the US", "jdcloud.com": "China-market cloud",
                   "qcloud.com": "the China-market site of Tencent Cloud", "ucloud.cn": "China-market cloud",
                   "volcengine.com": "the China-market site of ByteDance's cloud", "qiniu.com": "China-market cloud",
                   "upyun.com": "China-market cloud", "vercel.com": "an application platform, not rented infrastructure",
                   "netlify.com": "an application platform, not rented infrastructure",
                   "render.com": "an application platform, not rented infrastructure",
                   "fly.io": "an application platform, not rented infrastructure",
                   "railway.com": "an application platform, not rented infrastructure",
                   "koyeb.com": "an application platform, not rented infrastructure",
                   "porter.run": "an application platform, not rented infrastructure",
                   "cloudflare.com": "network and edge services, not rented machines"}},
    {"id": "javascript-web-frameworks", "name": "JavaScript web frameworks",
     "definition": "JavaScript and TypeScript frameworks for building websites and web applications, which developers "
                   "in the US choose for a project.",
     "article": "Comparison of JavaScript-based web frameworks", "revid": 1374992173,
     "rule": {"mode": "table", "col": 0, "sections": ["General information"],
              "describe": "section 'General information'; the Framework column (first)"},
     "sites_in": ["nextjs.org", "svelte.dev", "nuxt.com", "solidjs.com", "qwik.dev", "astro.build", "vuejs.org",
                  "hono.dev", "elysiajs.com", "remix.run", "tanstack.com"],
     "same_vendor": {"remix.run": "reactrouter.com"},
     "sites_out": {"deno.com": "a runtime", "bun.sh": "a runtime", "vite.dev": "a build tool",
                   "nitro.build": "a server toolkit used by frameworks", "shadcn.com": "a component library",
                   "radix-ui.com": "a component library", "tailwindcss.com": "a CSS framework",
                   "panda-css.com": "a CSS library", "unocss.dev": "a CSS engine", "effect.website": "a library",
                   "zod.dev": "a library", "valibot.dev": "a library", "drizzle.team": "an ORM",
                   "orm.drizzle.team": "an ORM", "prisma.io": "an ORM"}},
    {"id": "ecommerce-platforms", "name": "E-commerce platforms",
     "definition": "Software and hosted platforms that merchants in the US use to run an online store.",
     "article": "Comparison of shopping cart software", "revid": 1378625961,
     "rule": {"mode": "table", "col": 0, "sections": ["General information"],
              "describe": "section 'General information'; the Name column (first)"},
     "sites_in": ["shopify.com", "woocommerce.com", "bigcommerce.com", "wix.com", "squarespace.com", "webflow.com",
                  "shopline.com", "shoplazza.com"],
     "same_vendor": {"bigcommerce.com": "commerce.com"},
     "sites_out": {"ueeshop.com": "a Chinese-language site for Chinese exporters"}},
    {"id": "crm-software", "name": "CRM software",
     "definition": "Customer relationship management software that companies in the US use to manage contacts, deals "
                   "and customer communication.",
     "article": "Comparison of CRM systems", "revid": 1365891310,
     "rule": {"mode": "table", "col": 0, "table_index": [0], "describe": "the first table; the first column"},
     "sites_in": ["hubspot.com", "attio.com"],
     "sites_out": {"intercom.com": "customer service software", "customer.io": "marketing messaging",
                   "braze.com": "marketing messaging", "klaviyo.com": "marketing messaging",
                   "mailchimp.com": "email marketing"}},
    {"id": "web-analytics", "name": "Web analytics",
     "definition": "Software that measures visits to a website, used by site owners and marketers in the US.",
     "article": "List of web analytics software", "revid": 1361857790,
     "rule": {"mode": "table", "col": 0, "describe": "the table; the Name column (first)"},
     "sites_in": ["plausible.io", "posthog.com"],
     "sites_out": {"june.so": "product analytics for software companies, not website visits",
                   "fathom.ai": "a meeting notetaker", "ahrefs.com": "SEO software", "semrush.com": "SEO software",
                   "moz.com": "SEO software"}},
    {"id": "online-payment-providers", "name": "Online payment providers",
     "definition": "Services that let businesses in the US accept payments online.",
     "article": "List of online payment service providers", "revid": 1367307700,
     "rule": {"mode": "table", "col": 0, "screen_col": 2,
              "screen_re": r"United States|North America|\bglobal\b|worldwide",
              "describe": "the table; the Company column (first), rows whose Location names the United States or "
                          "North America or says global or worldwide"},
     "sites_in": ["stripe.com", "adyen.com", "payoneer.com", "checkout.com", "airwallex.com"],
     "sites_out": {"wise.com": "money transfer; its row's Location is the United Kingdom",
                   "klarna.com": "buy now, pay later (its own category)", "revolut.com": "banking",
                   "mercury.com": "banking", "brex.com": "corporate cards", "ramp.com": "corporate cards",
                   "plaid.com": "bank data", "marqeta.com": "card issuing",
                   "oceanpayment.com": "serves Chinese exporters; its row's Location is Hong Kong",
                   "pingpongx.com": "serves Chinese exporters", "lianlianpay.com": "serves Chinese exporters",
                   "worldfirst.com": "serves exporters' collections", "xtransfer.com": "serves Chinese exporters",
                   "payoneer.cn": "the China-market site of Payoneer"}},
    {"id": "buy-now-pay-later", "name": "Buy now, pay later",
     "definition": "Services that let shoppers in the US split a purchase into installments at checkout.",
     "article": "Buy now, pay later", "revid": 1376383699,
     "rule": {"mode": "bullets", "sections": ["United States"],
              "describe": "section 'Noted providers by country', subsection 'United States'; each bullet's first link"},
     "sites_in": ["klarna.com"],
     "sites_out": {}},
    {"id": "online-course-platforms", "name": "Online course platforms",
     "definition": "Websites that offer online courses to learners in the US.",
     "article": "List of MOOC providers", "revid": 1363722387,
     "rule": {"mode": "table", "col": 0, "sections": [""],
              "describe": "the table before 'No longer available'; the Name column (first)"},
     "sites_in": ["coursera.org", "edx.org", "udemy.com", "khanacademy.org", "skillshare.com", "pluralsight.com",
                  "codecademy.com", "datacamp.com", "brilliant.org", "freecodecamp.org"],
     "sites_out": {"exercism.org": "coding exercises with mentoring, not courses",
                   "roadmap.sh": "learning roadmaps, not courses", "chegg.com": "homework help",
                   "duolingo.com": "language learning (its own category)",
                   "nostarch.com": "a book publisher", "pragprog.com": "a book publisher"}},
    {"id": "language-learning", "name": "Language learning",
     "definition": "Apps, courses and self-study programs that learners in the US use to learn a foreign language.",
     "article": "List of language self-study programs", "revid": 1377422426,
     "rule": {"mode": "table", "col": 0, "sections": ["List"],
              "describe": "section 'List'; the Self-study program column (first)"},
     "sites_in": ["duolingo.com"],
     "sites_out": {}},
    {"id": "container-shipping-lines", "name": "Container shipping lines",
     "definition": "Ocean carriers that move shipping containers for importers and exporters in the US.",
     "article": "List of largest container shipping companies", "revid": 1354275764,
     "rule": {"mode": "table", "col": 1, "describe": "the table; the Company name column (second)"},
     "sites_in": ["maersk.com", "cma-cgm.com", "hapag-lloyd.com"],
     "sites_out": {"dhl.com": "parcel and express carrier", "fedex.com": "parcel and express carrier",
                   "ups.com": "parcel and express carrier", "sf-express.com": "parcel and express carrier",
                   "jtexpress.com": "parcel carrier", "yunexpress.com": "parcel carrier", "4px.com": "parcel carrier",
                   "flexport.com": "freight forwarder", "expeditors.com": "freight forwarder",
                   "dsv.com": "freight forwarder", "kuehne-nagel.com": "freight forwarder"}},
    {"id": "management-consulting", "name": "Management consulting firms",
     "definition": "Firms that companies in the US hire for management consulting.",
     "article": "List of management consulting firms", "revid": 1379170443,
     "rule": {"mode": "bullets", "describe": "the list; each bullet's first link"},
     "sites_in": ["mckinsey.com", "bcg.com", "accenture.com", "deloitte.com", "pwc.com", "ey.com", "kpmg.com"],
     "sites_out": {}},
    {"id": "project-management-software", "name": "Project management software",
     "definition": "Software that teams in the US use to plan, assign and track project work.",
     "article": "Comparison of project management software", "revid": 1364585119,
     "rule": {"mode": "table", "col": 0, "sections": ["General information"],
              "describe": "section 'General information'; the Software column (first)"},
     "sites_in": ["asana.com", "monday.com", "clickup.com", "linear.app", "height.app"],
     "sites_out": {"teambition.com": "the China-market site", "tapd.cn": "China-market software",
                   "airtable.com": "a database and app builder", "notion.com": "a notes and docs workspace",
                   "coda.io": "a docs workspace", "slack.com": "team chat", "miro.com": "whiteboard",
                   "figma.com": "design"}},
    {"id": "note-taking-apps", "name": "Note-taking apps",
     "definition": "Apps that people in the US use to write, organize and search their notes.",
     "article": "Comparison of note-taking software", "revid": 1367074056,
     "rule": {"mode": "table", "col": 0, "sections": ["General information"],
              "describe": "section 'General information'; the Name column (first)"},
     "sites_in": ["notion.com", "obsidian.md"],
     "sites_out": {"yuque.com": "the China-market site", "coda.io": "a docs workspace",
                   "readwise.io": "reading highlights"}},
    {"id": "3d-printers", "name": "3D printers",
     "definition": "3D printers sold to hobbyists and businesses in the US.",
     "article": "List of 3D printer manufacturers", "revid": 1367768236,
     "rule": {"mode": "bullets", "describe": "the list; each bullet's first link"},
     "sites_in": ["bambulab.com", "creality.com", "elegoo.com"],
     "sites_out": {}},
    {"id": "us-airlines", "name": "US airlines",
     "definition": "Airlines that fly passengers within and from the US.",
     "article": "List of largest airlines in North America", "revid": 1367374301,
     "rule": {"mode": "table", "col": 0, "sections": ["By passengers carried"], "screen_col": 1,
              "screen_re": r"United States",
              "describe": "section 'By passengers carried'; the Airlines column (first), rows whose Country is "
                          "the United States"},
     "sites_in": ["delta.com", "united.com"],
     "sites_out": {}},
    {"id": "accounting-software", "name": "Accounting software",
     "definition": "Accounting software that small and midsize businesses in the US use for bookkeeping, invoicing and "
                   "financial reports.",
     "article": "Comparison of accounting software", "revid": 1374376033,
     "rule": {"mode": "table", "col": 0, "sections": ["Free and open source software", "Proprietary software"],
              "describe": "sections 'Free and open source software' and 'Proprietary software'; the Package column "
                          "(first)"},
     "sites_in": [],
     "sites_out": {"kingdee.com": "China-market software", "yonyou.com": "China-market software"}},
    {"id": "online-marketplaces", "name": "Online marketplaces",
     "definition": "Online marketplaces where shoppers in the US buy consumer goods from many sellers.",
     "article": "List of online marketplaces", "revid": 1373521726,
     "rule": {"mode": "table", "col": 0, "screen_col": 2, "screen_re": r"product|fashion|clothing",
              "describe": "the table; the Name column (first), rows whose Industry names products, fashion or "
                          "clothing"},
     "sites_in": ["amazon.com", "ebay.com", "etsy.com", "walmart.com", "temu.com", "shein.com", "aliexpress.com"],
     "same_vendor": {"ebay.com": "ebayinc.com"},
     "sites_out": {"mercadolibre.com": "does not sell to shoppers in the US", "coupang.com": "does not sell to "
                   "shoppers in the US", "jumia.com": "does not sell to shoppers in the US",
                   "noon.com": "does not sell to shoppers in the US", "ozon.ru": "does not sell to shoppers in the US",
                   "wildberries.ru": "does not sell to shoppers in the US",
                   "shopee.com": "does not sell to shoppers in the US",
                   "lazada.com": "does not sell to shoppers in the US",
                   "allegro.pl": "does not sell to shoppers in the US",
                   "rakuten.com": "a cashback site in the US, not a marketplace",
                   "cider.com": "a single-brand retailer", "miniso.com": "a single-brand retailer"}},
]


# ── fetching ──────────────────────────────────────────────────────────────
class Fetcher(object):
    def __init__(self, cache):
        self.cache = cache
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        handlers = [urllib.request.ProxyHandler({"https": proxy})] if proxy else []
        self.opener = urllib.request.build_opener(*handlers)

    def get(self, url, params):
        q = url + "?" + urllib.parse.urlencode(params)
        path = os.path.join(self.cache, hashlib.sha256(q.encode()).hexdigest()[:24] + ".json") if self.cache else ""
        if path and os.path.exists(path):
            with io.open(path, encoding="utf-8") as f:
                return json.load(f)
        req = urllib.request.Request(q, headers={"User-Agent": UA, "Api-User-Agent": UA})
        time.sleep(1.5)
        for attempt in range(4):
            try:
                with self.opener.open(req, timeout=30) as r:
                    js = json.loads(r.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                if attempt == 3 or e.code not in (429, 500, 502, 503):
                    raise
                ra = e.headers.get("Retry-After") if e.headers else None
                time.sleep(min(30.0, float(ra)) if ra and ra.isdigit() else 10.0 * (attempt + 1))
            except (urllib.error.URLError, OSError):
                if attempt == 3:
                    raise
                time.sleep(3)
        if path:
            os.makedirs(self.cache, exist_ok=True)
            with io.open(path, "w", encoding="utf-8") as f:
                json.dump(js, f)
        return js


def page(fx, revid):
    js = fx.get(API, {"action": "query", "prop": "revisions", "rvprop": "ids|timestamp|content", "rvslots": "main",
                      "revids": revid, "format": "json", "formatversion": 2})
    p = js["query"]["pages"][0]
    r = p["revisions"][0]
    return {"title": p["title"], "revid": r["revid"], "timestamp": r["timestamp"], "text": r["slots"]["main"]["content"]}


# ── reading the article ───────────────────────────────────────────────────
LINK = re.compile(r"\[\[([^\]|#]+)(#[^\]|]*)?(?:\|([^\]]*))?\]\]")


def sections(text):
    """[(heading, body)], '' for the lead."""
    out, cur, buf = [], "", []
    for line in text.split("\n"):
        m = re.match(r"^(=+)\s*(.*?)\s*\1\s*$", line)
        if m:
            out.append((cur, "\n".join(buf)))
            cur, buf = m.group(2), []
        else:
            buf.append(line)
    out.append((cur, "\n".join(buf)))
    return out


def strip_refs(s):
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    return re.sub(r"<!--.*?-->", "", s, flags=re.S)


def tables(body):
    """Each top-level wikitable as rows of cell strings (header cells included)."""
    out, depth, cur, row = [], 0, None, None
    for line in strip_refs(body).split("\n"):
        st = line.strip()
        if st.startswith("{|"):
            depth += 1
            if depth == 1:
                cur, row = [], []
            continue
        if st.startswith("|}"):
            depth -= 1
            if depth == 0 and cur is not None:
                if row:
                    cur.append(row)
                out.append(cur)
                cur = None
            continue
        if depth != 1 or cur is None:
            continue
        if st.startswith("|-"):
            if row:
                cur.append(row)
            row = []
            continue
        if st.startswith("|+"):
            continue
        if st.startswith("!") or st.startswith("|"):
            sep = "!!" if st.startswith("!") and "!!" in st else "||"
            parts = st[1:].split(sep) if sep in st else [st[1:]]
            for p in parts:
                m = re.match(r'^\s*((?:[a-z\-]+\s*=\s*("[^"]*"|\S+)\s*)+|\{\{rh2?\}\}\s*)\|(?!\|)(.*)$', p, re.S)
                row.append((m.group(3) if m else p).strip())
        elif row:
            row[-1] += "\n" + line
    return out


def first_link(cell):
    for m in LINK.finditer(cell):
        t = m.group(1).strip()
        if ":" in t and t.split(":")[0].lower() in ("file", "image", "category", "wikt", "wiktionary", "w"):
            continue
        return t, (m.group(3) or t).strip()
    return None


def listed(text, rule):
    """[(section, link title, label)] of the rows the rule reads, in article order."""
    out, seen_heads = [], {}
    want = rule.get("sections")
    for head, body in sections(text):
        k = seen_heads[head] = seen_heads.get(head, -1) + 1
        if want is not None and head not in want:
            continue
        if want is None and head in SKIP_SECTIONS:
            continue
        if "section_occurrence" in rule and k != rule["section_occurrence"]:
            continue
        if rule["mode"] == "table":
            for ti, tb in enumerate(tables(body)):
                if "table_index" in rule and ti not in rule["table_index"]:
                    continue
                for row in tb[1:]:
                    if len(row) <= rule["col"]:
                        continue
                    if "screen_col" in rule:
                        cell = row[rule["screen_col"]] if len(row) > rule["screen_col"] else ""
                        if not re.search(rule["screen_re"], cell, re.I):
                            continue
                    fl = first_link(row[rule["col"]])
                    if fl:
                        out.append((head, fl[0], fl[1]))
        else:
            for line in strip_refs(body).split("\n"):
                if line.startswith("*"):
                    fl = first_link(line)
                    if fl:
                        out.append((head, fl[0], fl[1]))
    return out


# ── Wikidata ──────────────────────────────────────────────────────────────
def resolve(fx, titles):
    out, titles = {}, list(dict.fromkeys(titles))
    for i in range(0, len(titles), 50):
        js = fx.get(API, {"action": "query", "titles": "|".join(titles[i:i + 50]), "redirects": 1,
                          "prop": "pageprops", "ppprop": "wikibase_item", "format": "json", "formatversion": 2})
        q = js["query"]
        nm = {r["from"]: r["to"] for r in q.get("normalized", [])}
        rd = {r["from"]: r["to"] for r in q.get("redirects", [])}
        pages = {p["title"]: p for p in q["pages"]}
        for t in titles[i:i + 50]:
            t3 = rd.get(nm.get(t, t), nm.get(t, t))
            p = pages.get(t3, {})
            out[t] = (t3, None if p.get("missing") else (p.get("pageprops") or {}).get("wikibase_item"))
    return out


def entities(fx, ids):
    out, ids = {}, [x for x in dict.fromkeys(ids) if x]
    for i in range(0, len(ids), 50):
        js = fx.get(WD, {"action": "wbgetentities", "ids": "|".join(ids[i:i + 50]), "props": "info|claims|labels",
                         "languages": "en", "format": "json"})
        out.update(js["entities"])
    return out


def claims(ent, prop):
    out = []
    for c in (ent.get("claims") or {}).get(prop, []):
        dv = (c.get("mainsnak") or {}).get("datavalue")
        if c.get("rank") == "deprecated" or not dv:
            continue
        quals = c.get("qualifiers") or {}
        out.append({"value": dv["value"], "rank": c.get("rank"), "ended": "P582" in quals,
                    "langs": [((q.get("datavalue") or {}).get("value") or {}).get("id") for q in quals.get("P407", [])]})
    return out


def host(u):
    h = (urllib.parse.urlsplit(u if "://" in u else "https://" + u).hostname or "").lower().rstrip(".")
    return h[4:] if h.startswith("www.") else h


def official_site(ent):
    """P856: http(s), not .onion, not deprecated, no end date. English- or multilingual-qualified first, then
    unqualified, then any;
    within each, preferred rank first, then a generic top-level domain before a country code, then statement order."""
    def cc(u):
        tld = host(u).rsplit(".", 1)[-1]
        return len(tld) == 2 and tld not in GENERIC_CC
    vals = [v for v in claims(ent, "P856") if not v["ended"] and isinstance(v["value"], str)
            and v["value"].lower().startswith(("http://", "https://")) and not host(v["value"]).endswith(".onion")]
    if not vals:
        return None
    return sorted(vals, key=lambda v: (0 if any(x in ENGLISH for x in v["langs"]) else 1 if not v["langs"] else 2,
                                       0 if v["rank"] == "preferred" else 1, 1 if cc(v["value"]) else 0))[0]["value"]


def domain_of(gw, h):
    """The part of a host a vendor owns: geo_watch's site_domain, at three labels under EXTRA_SUFFIXES."""
    d = gw.site_domain(h)
    return ".".join(h.split(".")[-3:]) if d in EXTRA_SUFFIXES else d


def load_watch():
    import importlib.util
    spec = importlib.util.spec_from_file_location("geo_watch", os.path.join(ROOT, "cli", "geo_watch.py"))
    gw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gw)
    return gw


# ── one category ──────────────────────────────────────────────────────────
def build(fx, spec, sites, gw):
    p = page(fx, spec["revid"])
    rows = listed(p["text"], spec["rule"])
    res = resolve(fx, [t for _, t, _ in rows])
    ents = entities(fx, [res[t][1] for _, t, _ in rows if res[t][1]])
    frame_rows, vendors = [], {}          # vendors: registrable domain -> candidate
    for sec, t, label in rows:
        title, qid = res[t]
        e = ents.get(qid) or {}
        r = {"section": sec, "listed_as": label, "link": t, "article": title, "wikidata": qid,
             "wd_lastrevid": e.get("lastrevid"), "wd_label": ((e.get("labels") or {}).get("en") or {}).get("value")}
        site = official_site(e) if e else None
        if qid in WEBSITE_OVERRIDES:
            r["website_wikidata"], r["website_override"] = site, WEBSITE_OVERRIDES[qid][1]
            site = WEBSITE_OVERRIDES[qid][0]
        r["website"] = site
        if not qid:
            r["status"] = "out: the link has no Wikipedia article or Wikidata item, so no recorded website"
        elif claims(e, "P576") or claims(e, "P2669"):
            r["status"] = "out: Wikidata records it as dissolved or discontinued"
        elif not site:
            r["status"] = "out: no official website in Wikidata"
        elif any(host(site) == h or host(site).endswith("." + h) for h in NOT_OWN):
            r["status"] = "out: its website is a page on another site (%s)" % host(site)
        else:
            dom = domain_of(gw, host(site))
            if dom in vendors:
                r["status"] = "same candidate as %s" % dom
                if qid not in vendors[dom]["wikidata"]:
                    vendors[dom]["wikidata"].append(qid)
            else:
                r["status"] = "candidate"
                vendors[dom] = {"id": dom, "site": host(site), "domains": [dom], "source": "list",
                                "listed_as": label, "wikidata": [qid], "wd_label": r["wd_label"]}
            r["candidate"] = dom
        frame_rows.append(r)
    added, merged = [], []
    for s in spec["sites_in"]:
        if s not in sites:
            raise SystemExit("%s: %s is not in benchmark/sites.json" % (spec["id"], s))
        dom = domain_of(gw, host(s))
        alt = (spec.get("same_vendor") or {}).get(s)
        alt_dom = domain_of(gw, alt) if alt else None
        if dom in vendors or alt_dom in vendors:
            v = vendors.pop(dom if dom in vendors else alt_dom)
            v["domains"] = sorted(set(v["domains"] + [dom]))
            v.update(id=dom, site=s, source="list and sites.json", sector=sites[s])
            vendors[dom] = v
            merged.append(s)
        else:
            vendors[dom] = {"id": dom, "site": s, "domains": [dom], "source": "sites.json", "sector": sites[s],
                            "wikidata": [], "wd_label": None, "listed_as": None}
            added.append(s)
        if alt_dom and alt_dom not in vendors[dom]["domains"]:
            vendors[dom]["domains"] = sorted(set(vendors[dom]["domains"] + [alt_dom]))
    # a candidate whose registrable domain is another's subdomain would share its citations: none may remain
    doms = sorted(vendors)
    for a in doms:
        for b in doms:
            if a != b and a.endswith("." + b):
                raise SystemExit("%s: %s is inside %s" % (spec["id"], a, b))
    cands = [vendors[k] for k in sorted(vendors)]
    seed = int(hashlib.sha256((SEED_TEXT % spec["id"]).encode()).hexdigest()[:16], 16)
    out = {k: spec[k] for k in ("id", "name", "definition")}
    # the benchmark sectors the category spans: those of its benchmark/sites.json sites
    out["sectors"] = sorted({sites[s] for s in spec["sites_in"]})
    out["frame"] = {"article": p["title"], "revid": p["revid"], "revision_timestamp": p["timestamp"],
                    "url": "https://en.wikipedia.org/w/index.php?oldid=%d" % p["revid"],
                    "rule": spec["rule"]["describe"], "rows": frame_rows,
                    "sites_json_in": spec["sites_in"], "sites_json_merged_with_listed_vendor": merged,
                    "sites_json_added": added,
                    "sites_json_out": [{"site": k, "reason": v} for k, v in sorted(spec["sites_out"].items())]}
    out["n_candidates"] = len(cands)
    if len(cands) < 6:
        out["status"] = "dropped: fewer than 6 candidates (%d)" % len(cands)
        out["candidates"] = cands
        return out
    if len(cands) > MAX_FRAME:
        drawn = sorted(random.Random(seed).sample([c["id"] for c in cands], MAX_FRAME))
        out["draw"] = {"seed": seed, "seed_from": "int(sha256(%r).hexdigest()[:16], 16)" % (SEED_TEXT % spec["id"]),
                       "method": "random.Random(seed).sample(candidate ids sorted, 15), Python 3",
                       "drawn": drawn}
        for c in cands:
            c["drawn"] = c["id"] in drawn
    else:
        for c in cands:
            c["drawn"] = True
    out["status"] = "kept"
    out["candidates"] = cands
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cache", help="directory for API responses (reused when present)")
    ap.add_argument("--check", action="store_true", help="rebuild and compare with categories.json")
    a = ap.parse_args(argv)
    gw = load_watch()
    with io.open(os.path.join(ROOT, "benchmark", "sites.json"), encoding="utf-8") as f:
        sites = {s["url"]: s["sector"] for s in json.load(f)["sites"]}
    fx = Fetcher(a.cache)
    cats = [build(fx, s, sites, gw) for s in SPECS]
    doc = {"format": "geo-score/prereg-round0-categories.v1",
           "plan": "benchmark/PREREGISTRATION.md, sections 4 and 5.1",
           "built_by": "benchmark/prereg/round0/build_frames.py",
           "max_frame": MAX_FRAME, "min_frame": 6,
           "sites_json": "only url and sector are read; no score, results file or raw report was opened",
           "categories": cats}
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    if a.check:
        with io.open(OUT, encoding="utf-8") as f:
            same = f.read() == text
        print("categories.json is %s" % ("what build_frames.py derives" if same else "NOT what build_frames.py derives"))
        return 0 if same else 1
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    for c in cats:
        print("%-28s %-9s %3d candidates%s" % (c["id"], c["status"][:9], c["n_candidates"],
                                              ", 15 drawn" if "draw" in c else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
