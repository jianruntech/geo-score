#!/usr/bin/env python3
"""
geo-score levels 2 and 3. Level 1, the score, says whether AI engines *can* cite a site;
levels 2 (`--ask`) and 3 (`watch`) measure whether they *do*.

It asks ChatGPT, Perplexity, Gemini and Claude the questions your buyers ask, through their
search-enabled APIs with your own keys, and records who the answers cite: you, your
competitors, or the third-party pages the engines lean on. Run it through geo_score.py:

    python3 geo_score.py watch init --brand Acme --domain acme.com
    python3 geo_score.py watch run --dry-run     # the plan and the caps, no calls
    python3 geo_score.py watch run               # questions x engines, saved under .geo-score/watch/runs/
    python3 geo_score.py watch report --format md
    python3 geo_score.py watch diff              # latest two runs, with a significance test
    python3 geo_score.py watch ask "best free AI video generator"
    python3 geo_score.py mcp                     # score and watch over MCP (stdio)

No dependencies. Python 3.8+. API keys are read from the environment and never written
anywhere. https://github.com/jianruntech/geo-score
"""
import argparse, contextlib, csv, datetime, hashlib, http.client, importlib.util, io, ipaddress, json, math, os
import random, re, socket, sys, threading, time, unicodedata
import urllib.error, urllib.parse, urllib.request
from collections import Counter

__version__ = "1.2.0"
RUN_FORMAT = "geo-score/watch.v1"
CONFIG_NAME = "geo-score-watch.json"
STATE_DIR = os.path.join(".geo-score", "watch")
QUERY_COLS = ["query_id", "query", "intent_tier", "target_url"]
BRANDED_VALUES = ("auto", "yes", "no")   # the optional `branded` column of queries.csv
CSV_COLS = ["week", "query_id", "query", "intent_tier", "engine", "cited", "quoted_url",
            "rank", "other_domains_cited", "note", "branded"]
UA = "geo-score-watch/%s (+https://github.com/jianruntech/geo-score)" % __version__
HTTP_TIMEOUT = 120
MAX_BODY = 8 << 20
MAX_ANSWER = 20000
MAX_QUERY_LEN = 500
MAX_QUERIES = 200
MAX_RUNS = 10
MAX_RESOLVE = 12
DEFAULT_MAX_CALLS = 120
BOOTSTRAP_REPS = 2000
ALPHA = 0.05
MIN_PAIRED = 6        # with 5 questions, all 5 flipping the same way gives exact p = 2/2^5 = 0.0625: no test can call it
BRANDED_WARN = 0.3    # `watch check` warns above this share of questions that name the brand
RETRY_STATUS = (429, 500, 502, 503, 504, 529)
FATAL_STATUS = (400, 401, 403, 404)
ENGINE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
QUERY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,39}$")
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,99}$")
ENV_RE = re.compile(r"^[A-Z_][A-Z0-9_]{0,63}$")
RUN_ID_RE = re.compile(r"^(\d{8}T\d{6}Z)(?:-(\d{1,3}))?$")
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
DOMAIN_RE = re.compile(r"^(?=.{3,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
REDIRECT_HOSTS = ("vertexaisearch.cloud.google.com",)
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

PROVIDERS = {
    "openai":     {"env": ("OPENAI_API_KEY",), "model": "gpt-6-luna", "reports_cost": False,
                   "url": "https://api.openai.com/v1/responses"},
    "perplexity": {"env": ("PERPLEXITY_API_KEY",), "model": "sonar", "reports_cost": True,
                   "url": "https://api.perplexity.ai/chat/completions"},
    "gemini":     {"env": ("GEMINI_API_KEY", "GOOGLE_API_KEY"), "model": "gemini-3.8-flash", "reports_cost": False,
                   "url": "https://generativelanguage.googleapis.com/v1beta/interactions"},
    "anthropic":  {"env": ("ANTHROPIC_API_KEY",), "model": "claude-sonnet-5", "reports_cost": False,
                   "url": "https://api.anthropic.com/v1/messages"},
    "openrouter": {"env": ("OPENROUTER_API_KEY",), "model": "openai/gpt-6-luna", "reports_cost": True,
                   "url": "https://openrouter.ai/api/v1/chat/completions"},
}
DEFAULT_ENGINES = [
    {"id": "chatgpt-api", "provider": "openai"},
    {"id": "perplexity-api", "provider": "perplexity"},
    {"id": "gemini-api", "provider": "gemini"},
    {"id": "claude-api", "provider": "anthropic"},
]
NOTES = [
    "API channel. Answers come from each provider's search-enabled API, which is not the consumer app. "
    "Compare runs with runs; never pool them with answers sampled by hand in the apps.",
    "The same question gets different answers from one ask to the next, and answers to one question move "
    "together. Rates carry a 95% interval: Wilson when each question was answered once, a bootstrap over "
    "questions when a question has several answers. diff pairs the questions both runs answered and calls a "
    "change a change only when an exact paired test (McNemar), Holm-corrected across engines, says so (p < 0.05).",
    "A question that names the brand invites an answer that cites it. Those questions are kept out of the "
    "headline rate and reported on a line of their own.",
    "Engines without a key, calls that failed and calls skipped by a cap count as not measured, never as zero.",
    "This measures citations. It does not predict traffic, rankings or revenue.",
]

# Swapped out by the tests; nothing else should touch these.
NOW = lambda: datetime.datetime.now(datetime.timezone.utc)
SLEEP = time.sleep


class ConfigError(Exception):
    pass


class TransportError(Exception):
    pass


class EngineError(Exception):
    def __init__(self, msg, status=None):
        Exception.__init__(self, msg)
        self.status = status

    @property
    def fatal(self):
        # Bad key, bad model, unsupported tool: every later call would fail the same way.
        return self.status in FATAL_STATUS


# ── small helpers ─────────────────────────────────────────────────────────
def _int(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        return 0
    return int(x)


def _num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0:
        return None
    return float(x)


def _strs(x):
    if isinstance(x, str):
        return [x]
    if isinstance(x, list):
        return [v for v in x if isinstance(v, str)]
    return []


def _uniq(items):
    out, seen = [], set()
    for v in items:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(p["text"] for p in content if isinstance(p, dict) and isinstance(p.get("text"), str))
    return ""


def redact(s, secret):
    """Remove a key from text in every form an error message may carry it: as is, escaped, or in pieces."""
    s = str(s)
    if secret and len(secret) >= 8:
        forms = {secret, repr(secret)[1:-1], secret.encode("unicode_escape").decode("ascii", "replace")}
        forms.update(f for f in re.split(r"\s+", secret) if len(f) >= 8)
        for form in sorted(forms, key=len, reverse=True):
            s = s.replace(form, "[redacted]")
    return s[:400]


def host_of(u):
    if not isinstance(u, str) or not u.strip():
        return ""
    u = u.strip()
    if "://" not in u:
        u = "https://" + u
    try:
        h = urllib.parse.urlsplit(u).hostname or ""
    except ValueError:
        return ""
    h = h.lower().rstrip(".")
    if h.startswith("*."):
        h = h[2:]
    try:
        h = h.encode("idna").decode("ascii")   # 例子.cn and xn--fsqu00a.cn are the same host
    except UnicodeError:
        pass
    return h[4:] if h.startswith("www.") else h


def prefix_key(u):
    """host + path, lowercased, no trailing slash: the unit url_prefixes are matched on."""
    h = host_of(u)
    if not h:
        return ""
    if "://" not in u:
        u = "https://" + u.strip()
    try:
        path = urllib.parse.urlsplit(u.strip()).path
    except ValueError:
        path = ""
    return (h + path.lower()).rstrip("/")


def clean_url(u):
    """http(s) only, fragment and utm_* dropped (OpenAI tags every citation with utm_source)."""
    if not isinstance(u, str):
        return ""
    try:
        p = urllib.parse.urlsplit(u.strip())
        host = p.hostname
    except ValueError:
        return ""
    if p.scheme.lower() not in ("http", "https") or not host:
        return ""
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
         if not k.lower().startswith("utm_")]
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc, p.path or "/", urllib.parse.urlencode(q), ""))


def wilson(k, n, z=1.96):
    if not n:
        return None
    lo, hi = _wilson_raw(k, n, z)
    return [round(lo, 4), round(hi, 4)]


def two_prop_p(k1, n1, k2, n2):
    """Two-sided p-value for 'the two citation rates differ'."""
    if not n1 or not n2:
        return None
    p = (k1 + k2) / float(n1 + n2)
    se = math.sqrt(p * (1 - p) * (1.0 / n1 + 1.0 / n2))
    if se == 0:
        return 1.0
    z = (k2 / float(n2) - k1 / float(n1)) / se
    return math.erfc(abs(z) / math.sqrt(2))


def rate(k, n):
    return round(k / float(n), 4) if n else None


# ── statistics: clustered intervals, paired tests ─────────────────────────
def _seed(*parts):
    """Resampling seed from run ids, so a run always reports the same intervals. The -N suffix save_run may
    add is dropped: renaming a run does not move its numbers."""
    key = "|".join(RUN_ID_RE.sub(r"\1", str(p)) for p in parts)
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16)


def _central(stats):
    """2.5th and 97.5th percentiles of bootstrap replicates."""
    stats.sort()
    i = len(stats) * 25 // 1000
    return stats[i], stats[len(stats) - 1 - i]


def _wilson_raw(k, n, z=1.96):
    p = k / float(n)
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4.0 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def cluster_ci(groups, seed, reps=None):
    """95% interval for a rate whose answers come in clusters, one per question. groups: (cited, answered) per
    question. Questions are resampled with replacement; the interval is never narrower than Wilson over the
    answers, which a bootstrap on a handful of questions can be (three questions each cited in half their
    answers resample to a zero-width interval)."""
    groups = [(k, n) for k, n in groups if n]
    N = sum(n for _, n in groups)
    if not N:
        return None
    w = wilson(sum(k for k, _ in groups), N)
    if len(groups) < 2:
        return w
    rng, m, stats = random.Random(seed), len(groups), []
    for _ in range(reps or BOOTSTRAP_REPS):
        draw = rng.choices(groups, k=m)
        stats.append(sum(g[0] for g in draw) / float(sum(g[1] for g in draw)))
    lo, hi = _central(stats)
    return [round(min(lo, w[0]), 4), round(max(hi, w[1]), 4)]


def mcnemar_p(gained, lost):
    """Exact two-sided McNemar test on the questions that flipped: is one direction more common than a fair
    coin would make it?"""
    b = gained + lost
    if not b:
        return 1.0
    tail = sum(math.comb(b, i) for i in range(min(gained, lost) + 1))
    return min(1.0, 2 * tail / 2 ** b)


def signflip_p(changes):
    """Exact two-sided sign-flip test on per-question net changes. With no change, each question's net change
    is as likely to point up as down; the answers to one question move together. With one pair per question
    every change is -1, 0 or +1 and this is McNemar's test."""
    ds = [abs(d) for d in changes if d]
    if not ds:
        return 1.0
    obs = abs(sum(changes))
    dist = {0: 1}
    for d in ds:
        nxt = {}
        for s, c in dist.items():
            nxt[s + d] = nxt.get(s + d, 0) + c
            nxt[s - d] = nxt.get(s - d, 0) + c
        dist = nxt
    return min(1.0, sum(c for s, c in dist.items() if abs(s) >= obs) / 2 ** len(ds))


def holm(ps):
    """Holm step-down adjusted p-values, in the order given."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, top = [None] * len(ps), 0.0
    for rank, i in enumerate(order):
        top = max(top, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = top
    return out


def newcombe_paired(both, lost, gained, neither):
    """95% interval for after - before on paired yes/no data (Newcombe 1998, hybrid score): the two Wilson
    intervals, combined through the correlation of the pairs. Treats the pairs as independent."""
    n = both + lost + gained + neither
    if not n:
        return None
    p1, p2 = (both + lost) / float(n), (both + gained) / float(n)
    l1, u1 = _wilson_raw(both + lost, n)
    l2, u2 = _wilson_raw(both + gained, n)
    num = float(both * neither - lost * gained)
    if num > 0:
        num = max(num - n / 2.0, 0.0)
    den = math.sqrt(float((both + lost) * (gained + neither) * (both + gained) * (lost + neither)))
    phi = num / den if den else 0.0
    d = p2 - p1
    lo = d - math.sqrt(max(0.0, (p2 - l2) ** 2 - 2 * phi * (p2 - l2) * (u1 - p1) + (u1 - p1) ** 2))
    hi = d + math.sqrt(max(0.0, (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2))
    return max(-1.0, lo), min(1.0, hi)


def paired_ci(by_question, table, seed, reps=None):
    """95% interval, in points, for the paired change: questions resampled with replacement (each with all its
    pairs), never narrower than Newcombe's interval, which counts every pair as independent."""
    units = list(by_question)
    if not units:
        return None
    lo, hi = newcombe_paired(*table)
    if len(units) >= 2:
        rng, m, stats = random.Random(seed), len(units), []
        for _ in range(reps or BOOTSTRAP_REPS):
            draw = rng.choices(units, k=m)
            stats.append(sum(u[0] for u in draw) / float(sum(u[1] for u in draw)))
        blo, bhi = _central(stats)
        lo, hi = min(lo, blo), max(hi, bhi)
    return [round(100 * lo, 1), round(100 * hi, 1)]


# ── HTTP ──────────────────────────────────────────────────────────────────
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # An API endpoint that redirects is misconfigured, and following it would carry the key to
    # whatever host it names. A redirect surfaces as an HTTP error instead.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_post(url, headers, body, timeout=HTTP_TIMEOUT):
    """POST JSON. Returns (status, headers, raw bytes); raises TransportError only when no HTTP answer came."""
    h = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": UA}
    h.update(headers)
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=h, method="POST")
    try:
        with _OPENER.open(req, timeout=timeout) as r:
            return r.status, dict(r.headers.items()), r.read(MAX_BODY)
    except urllib.error.HTTPError as e:
        try:
            raw = e.read(MAX_BODY)
        except Exception:
            raw = b""
        return e.code, dict(e.headers.items()) if e.headers else {}, raw
    except ValueError as e:
        # http.client quotes the offending header, key included, in this message: never pass it on.
        raise TransportError("invalid request (%s)" % e.__class__.__name__)
    except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
        raise TransportError(str(getattr(e, "reason", "") or e) or e.__class__.__name__)


def resolve_redirect(url, timeout=10):
    """Gemini cites through a redirect host. One GET, not followed, reads where it points."""
    if not url.startswith("https://"):
        return None
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with _OPENER.open(req, timeout=timeout):
            return None
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location") if e.headers is not None and 300 <= e.code < 400 else None
        return urllib.parse.urljoin(url, loc) if loc else None
    except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError):
        return None


TRANSPORT = http_post
RESOLVER = resolve_redirect


def _retry_after(hdrs, attempt):
    v = {str(k).lower(): v for k, v in (hdrs or {}).items()}.get("retry-after", "")
    try:
        s = float(v)
    except (TypeError, ValueError):
        s = 2.0 * 2 ** (attempt - 1)
    return max(0.5, min(s, 30.0))


def _err_text(js, raw):
    if isinstance(js, list) and js and isinstance(js[0], dict):
        js = js[0]
    if isinstance(js, dict):
        e = js.get("error")
        if isinstance(e, dict):
            e = e.get("message") or e.get("type") or json.dumps(e)[:300]
        if e:
            return str(e)
        if js.get("message"):
            return str(js["message"])
    return (raw or b"").decode("utf-8", "replace").strip()[:300] or "empty response"


def api_post(url, headers, body, secret):
    """POST with up to two retries on 429/5xx. Timeouts are not retried: the provider may have billed them.
    Returns (json, attempts)."""
    attempt = 0
    while True:
        attempt += 1
        try:
            st, hdrs, raw = TRANSPORT(url, headers, body)
        except TransportError as e:
            raise EngineError("network: " + redact(e, secret))
        if st in RETRY_STATUS and attempt < 3:
            SLEEP(_retry_after(hdrs, attempt))
            continue
        break
    try:
        js = json.loads(raw.decode("utf-8", "replace")) if raw else None
    except ValueError:
        js = None
    if not (200 <= st < 300) or not isinstance(js, dict):
        raise EngineError("HTTP %s: %s" % (st, redact(_err_text(js, raw), secret)), st)
    return js, attempt


# ── engines ───────────────────────────────────────────────────────────────
def _result(answer, citations, searches, tin, tout, nsearch, cost=None, calls=1, attempts=1):
    return {"answer": answer or "", "citations": citations,
            "search_queries": [q for q in searches if isinstance(q, str) and q.strip()],
            "usage": {"input_tokens": _int(tin), "output_tokens": _int(tout),
                      "search_calls": _int(nsearch), "api_calls": calls},
            "reported_cost": _num(cost), "attempts": attempts}


def _endpoint(eng):
    return eng.get("base_url") or PROVIDERS[eng["provider"]]["url"]


def call_openai(eng, key, question, country):
    tool = {"type": eng.get("tool") or "web_search"}
    if country:
        tool["user_location"] = {"type": "approximate", "country": country}
    body = {"model": eng["model"], "input": question, "tools": [tool]}
    js, n = api_post(_endpoint(eng), {"Authorization": "Bearer " + key}, body, key)
    text, cites, searches, nsearch = [], [], [], 0
    for item in js.get("output") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "web_search_call":
            a = item.get("action") if isinstance(item.get("action"), dict) else {}
            if a.get("type", "search") == "search":
                nsearch += 1
            searches.append(a.get("query"))
            if isinstance(a.get("queries"), list):
                searches.extend(a["queries"])
        elif item.get("type") == "message":
            for part in item.get("content") or []:
                if not isinstance(part, dict) or part.get("type") != "output_text":
                    continue
                text.append(part.get("text") or "")
                for an in part.get("annotations") or []:
                    if isinstance(an, dict) and an.get("type") == "url_citation":
                        cites.append((an.get("url"), an.get("title")))
    u = js.get("usage") if isinstance(js.get("usage"), dict) else {}
    return _result("".join(text), cites, searches, u.get("input_tokens"), u.get("output_tokens"),
                   nsearch, attempts=n)


def call_perplexity(eng, key, question, country):
    body = {"model": eng["model"], "messages": [{"role": "user", "content": question}]}
    if country:
        body["web_search_options"] = {"user_location": {"country": country}}
    js, n = api_post(_endpoint(eng), {"Authorization": "Bearer " + key}, body, key)
    msg = ((js.get("choices") or [{}])[0] or {}).get("message") or {}
    text = _text(msg.get("content"))
    cites = [(r.get("url"), r.get("title")) for r in js.get("search_results") or [] if isinstance(r, dict)]
    if not cites:
        cites = [(u, "") for u in js.get("citations") or [] if isinstance(u, str)]
    # Sonar numbers its sources [1], [2]… When the answer uses the markers, only the numbered ones were cited.
    used = set(int(m) for m in re.findall(r"\[(\d{1,3})\]", text))
    kept = [c for i, c in enumerate(cites, 1) if i in used]
    if kept:
        cites = kept
    u = js.get("usage") if isinstance(js.get("usage"), dict) else {}
    cost = u.get("cost")
    if isinstance(cost, dict):
        cost = cost.get("total_cost")
    return _result(text, cites, [], u.get("prompt_tokens"), u.get("completion_tokens"), 1,
                   cost=cost, attempts=n)


def call_gemini(eng, key, question, country):
    """Interactions API by default (Google's recommended API since June 2026); "api": "generate_content" in the
    engine config uses the older, still supported generateContent endpoint instead."""
    if eng.get("api") == "generate_content":
        return _gemini_generate_content(eng, key, question)
    body = {"model": eng["model"], "input": question, "tools": [{"type": "google_search"}], "store": False}
    js, n = api_post(_endpoint(eng), {"x-goog-api-key": key}, body, key)
    text, cites, searches = [], [], []
    for step in js.get("steps") or []:
        if not isinstance(step, dict):
            continue
        if step.get("type") == "google_search_call":
            a = step.get("arguments") if isinstance(step.get("arguments"), dict) else {}
            if isinstance(a.get("queries"), list):
                searches.extend(a["queries"])
            searches.append(a.get("query"))
        elif step.get("type") == "model_output":
            for part in step.get("content") or []:
                if not isinstance(part, dict) or part.get("type") != "text":
                    continue
                text.append(part.get("text") or "")
                for an in part.get("annotations") or []:
                    if isinstance(an, dict) and an.get("type") == "url_citation":
                        cites.append((an.get("url"), an.get("title")))
    u = js.get("usage") if isinstance(js.get("usage"), dict) else {}
    tin = _int(u.get("prompt_tokens") or u.get("input_tokens") or u.get("total_input_tokens"))
    tout = _int(u.get("completion_tokens") or u.get("output_tokens") or u.get("total_output_tokens"))
    if _int(u.get("total_tokens")) > tin + tout:
        tout = _int(u.get("total_tokens")) - tin      # thinking tokens are billed as output
    searches = [q for q in searches if isinstance(q, str) and q.strip()]
    return _result("\n".join(t for t in text if t), cites, searches, tin, tout, len(searches), attempts=n)


def _gemini_generate_content(eng, key, question):
    url = (eng.get("base_url") or GEMINI_GENERATE_URL).replace("{model}", urllib.parse.quote(eng["model"], safe=""))
    body = {"contents": [{"role": "user", "parts": [{"text": question}]}], "tools": [{"google_search": {}}]}
    js, n = api_post(url, {"x-goog-api-key": key}, body, key)
    cand = (js.get("candidates") or [{}])[0] or {}
    parts = (cand.get("content") or {}).get("parts") or []
    text = "".join(p.get("text") or "" for p in parts if isinstance(p, dict) and not p.get("thought"))
    gm = cand.get("groundingMetadata") if isinstance(cand.get("groundingMetadata"), dict) else {}
    cites = []
    for ch in gm.get("groundingChunks") or []:
        w = (ch or {}).get("web") if isinstance(ch, dict) else None
        if isinstance(w, dict):
            cites.append((w.get("uri"), w.get("title")))
    searches = [q for q in gm.get("webSearchQueries") or [] if isinstance(q, str)]
    um = js.get("usageMetadata") if isinstance(js.get("usageMetadata"), dict) else {}
    tout = _int(um.get("candidatesTokenCount")) + _int(um.get("thoughtsTokenCount"))
    return _result(text, cites, searches, um.get("promptTokenCount"), tout, len(searches), attempts=n)


def call_anthropic(eng, key, question, country):
    tool = {"type": eng.get("tool") or "web_search_20250305", "name": "web_search",
            "max_uses": int(eng.get("max_searches") or 5)}
    if country:
        tool["user_location"] = {"type": "approximate", "country": country}
    hdr = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    msgs = [{"role": "user", "content": question}]
    text, cites, searches = [], [], []
    tin = tout = nsearch = calls = attempts = 0
    for _ in range(3):   # a long search can pause the turn; send it back to continue, at most twice
        body = {"model": eng["model"], "max_tokens": int(eng.get("max_tokens") or 2048),
                "messages": msgs, "tools": [tool]}
        js, n = api_post(_endpoint(eng), hdr, body, key)
        calls += 1
        attempts += n
        content = js.get("content") if isinstance(js.get("content"), list) else []
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                text.append(b.get("text") or "")
                for c in b.get("citations") or []:
                    if isinstance(c, dict) and c.get("url"):
                        cites.append((c.get("url"), c.get("title")))
            elif b.get("type") == "server_tool_use" and b.get("name") == "web_search":
                searches.append((b.get("input") or {}).get("query"))
        u = js.get("usage") if isinstance(js.get("usage"), dict) else {}
        tin += _int(u.get("input_tokens"))
        tout += _int(u.get("output_tokens"))
        nsearch += _int((u.get("server_tool_use") or {}).get("web_search_requests"))
        if js.get("stop_reason") != "pause_turn":
            break
        msgs = msgs + [{"role": "assistant", "content": content}]
    return _result("".join(text), cites, searches, tin, tout, nsearch, calls=calls, attempts=attempts)


def call_openrouter(eng, key, question, country):
    body = {"model": eng["model"], "messages": [{"role": "user", "content": question}],
            "plugins": [{"id": "web", "max_results": int(eng.get("max_results") or 5)}]}
    hdr = {"Authorization": "Bearer " + key, "HTTP-Referer": "https://github.com/jianruntech/geo-score",
           "X-Title": "geo-score"}
    js, n = api_post(_endpoint(eng), hdr, body, key)
    msg = ((js.get("choices") or [{}])[0] or {}).get("message") or {}
    cites = []
    for an in msg.get("annotations") or []:
        if isinstance(an, dict) and an.get("type") == "url_citation":
            c = an.get("url_citation") if isinstance(an.get("url_citation"), dict) else an
            cites.append((c.get("url"), c.get("title")))
    u = js.get("usage") if isinstance(js.get("usage"), dict) else {}
    return _result(_text(msg.get("content")), cites, [], u.get("prompt_tokens"), u.get("completion_tokens"),
                   1, cost=u.get("cost"), attempts=n)


CALLERS = {"openai": call_openai, "perplexity": call_perplexity, "gemini": call_gemini,
           "anthropic": call_anthropic, "openrouter": call_openrouter}


KEY_RE = re.compile(r"[\x21-\x7e]+")   # printable ASCII, no spaces: every provider key looks like this


def _key_names_list(eng):
    return [eng["key_env"]] if eng.get("key_env") else list(PROVIDERS[eng["provider"]]["env"])


def key_for(eng):
    """The key, or "" when it is missing or malformed. A malformed key is never used, so it can never end up in
    an error message, a run file or a commit."""
    for name in _key_names_list(eng):
        v = os.environ.get(name, "").strip()
        if v:
            return v if KEY_RE.fullmatch(v) else ""
    return ""


def key_issue(eng):
    """Why key_for gave nothing, without ever echoing the value."""
    for name in _key_names_list(eng):
        v = os.environ.get(name, "").strip()
        if v and not KEY_RE.fullmatch(v):
            return "%s contains spaces, line breaks or other characters a key cannot have; copy it again" % name
        if v:
            return ""
    return "set %s" % key_names(eng)


def key_names(eng):
    return eng["key_env"] if eng.get("key_env") else " or ".join(PROVIDERS[eng["provider"]]["env"])


# ── who owns a citation ───────────────────────────────────────────────────
_CJK_CHARS = "\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff"
_CJK = re.compile("[%s]" % _CJK_CHARS)
_WORD_NOT_CJK = "[^\\W%s]" % _CJK_CHARS


def _mention_re(term):
    """Chinese, Japanese and Korean names match anywhere (no spaces between words); everything else, accented
    Latin included, matches whole words only, so "Lumo" does not match "Lumos". A CJK character beside a Latin
    name is a word break: "Lumo" matches in "用Lumo做视频"."""
    if _CJK.search(term):
        return re.compile(re.escape(term), re.I)
    return re.compile("(?<!%s)%s(?!%s)" % (_WORD_NOT_CJK, re.escape(term), _WORD_NOT_CJK), re.I)


class Entity(object):
    """A brand or a competitor: a name, the domains and URL prefixes it owns, the names it goes by."""

    def __init__(self, d, you=False):
        d = d if isinstance(d, dict) else {}
        self.name = str(d.get("name") or "").strip()
        self.domains = _uniq(host_of(x) for x in _strs(d.get("domains")))
        self.url_prefixes = _uniq(prefix_key(x) for x in _strs(d.get("url_prefixes")))
        self.aliases = _uniq(x.strip() for x in _strs(d.get("aliases")))
        self.you = you
        self._pats = [_mention_re(t) for t in _uniq([self.name] + self.aliases + self.domains)]

    def owns_domain(self, dom):
        return bool(dom) and any(dom == x or dom.endswith("." + x) for x in self.domains)

    def owns(self, url, dom):
        if self.owns_domain(dom):
            return True
        k = prefix_key(url) if self.url_prefixes else ""
        return bool(k) and any(k == p or k.startswith(p + "/") for p in self.url_prefixes)

    def named_in(self, text):
        return any(p.search(text or "") for p in self._pats)

    def as_json(self):
        return {"name": self.name, "domains": self.domains, "url_prefixes": self.url_prefixes,
                "aliases": self.aliases}


def normalize_citations(raw, entities, resolve=True):
    out, seen, resolved = [], set(), 0
    for item in raw:
        url, title = (item + (None, None))[:2] if isinstance(item, tuple) else (None, None)
        title = title.strip() if isinstance(title, str) else ""
        u = clean_url(url)
        dom = host_of(u) if u else ""
        if dom in REDIRECT_HOSTS:
            t = title.lower()
            t = t[4:] if t.startswith("www.") else t
            tdom = t if DOMAIN_RE.match(t) else ""
            # Resolve only when the exact page matters (a tracked brand) or the title names no domain.
            if resolve and resolved < MAX_RESOLVE and (not tdom or any(e.owns_domain(tdom) for e in entities)):
                resolved += 1
                real = clean_url(RESOLVER(u) or "")
                if real and host_of(real) not in REDIRECT_HOSTS:
                    u, dom = real, host_of(real)
                else:
                    dom = tdom
            else:
                dom = tdom
        if not u or not dom or u in seen:
            continue
        seen.add(u)
        out.append({"url": u, "domain": dom, "title": title[:200]})
    return out


def evaluate(res, brand, rivals, resolve=True):
    cites = normalize_citations(res["citations"], [brand] + rivals, resolve)
    answer = res["answer"]

    def place(ent):
        seen = []
        for c in cites:
            if ent.owns(c["url"], c["domain"]):
                return len(seen) + 1, c["url"]
            if c["domain"] not in seen:
                seen.append(c["domain"])
        return None, None

    rank, url = place(brand)
    comps = {}
    for r in rivals:
        rr, _ = place(r)
        comps[r.name] = {"cited": rr is not None, "rank": rr, "mentioned": r.named_in(answer)}
    return {"cited": rank is not None, "rank": rank, "quoted_url": url, "mentioned": brand.named_in(answer),
            "competitors": comps, "citations": cites,
            "search_queries": _uniq(q.strip() for q in res["search_queries"])[:20],
            "answer": answer[:MAX_ANSWER], "answer_truncated": len(answer) > MAX_ANSWER}


def flag_query(q, brand, rivals):
    """Mark a question that names the brand or a competitor, with the matcher the answers get: name, aliases
    and domains; whole words for Latin script, anywhere for Chinese, Japanese and Korean."""
    text = q.get("query") or ""
    return dict(q, branded=q.get("branded") or "auto", brand_in_query=brand.named_in(text),
                competitor_in_query=any(r.named_in(text) for r in rivals))


def is_branded(q, brand=None):
    """The `branded` column decides when it says yes or no; auto follows brand_in_query, found from the
    question text when the run predates the flag."""
    v = str(q.get("branded") or "auto").strip().lower()
    if v in ("yes", "no"):
        return v == "yes"
    if "brand_in_query" in q:
        return bool(q["brand_in_query"])
    return brand is not None and brand.named_in(q.get("query") or "")


# ── config ────────────────────────────────────────────────────────────────
def _read_csv(path):
    """utf-8 (BOM or not) first, then gb18030 — what Excel writes on a Chinese Windows machine."""
    with io.open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "gb18030"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ConfigError("%s: not UTF-8 or GB18030 text" % path)
    rd = csv.DictReader(io.StringIO(text))
    rd.fieldnames = [(h or "").strip() for h in (rd.fieldnames or [])]
    return rd.fieldnames, list(rd)


class Config(object):
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.dir = os.path.dirname(self.path)
        self.errors, self.warnings = [], []
        try:
            with io.open(self.path, encoding="utf-8-sig") as f:
                raw = json.load(f)
        except (OSError, IOError) as e:
            raise ConfigError("cannot read %s: %s (run `geo_score.py watch init` to create one)" % (path, e.strerror or e))
        except ValueError as e:
            raise ConfigError("%s is not valid JSON: %s" % (path, e))
        if not isinstance(raw, dict):
            raise ConfigError("%s must hold a JSON object" % path)
        self.raw = raw
        err, warn = self.errors.append, self.warnings.append

        self.brand = Entity(raw.get("brand"), you=True)
        if not self.brand.name:
            err("brand.name is required")
        if not self.brand.domains and not self.brand.url_prefixes:
            warn("brand has no domains or url_prefixes: citations can never count as yours")
        self.competitors = []
        names = {self.brand.name.lower()}
        for i, c in enumerate(raw.get("competitors") or []):
            e = Entity(c)
            if not e.name:
                err("competitors[%d].name is required" % i)
            elif e.name.lower() in names:
                err("competitor name %r is used twice (or equals the brand)" % e.name)
            names.add(e.name.lower())
            self.competitors.append(e)
        for e in [self.brand] + self.competitors:
            for a in [e.name] + e.aliases:
                if a and len(a) < 3 and not re.search(r"[^\x00-\x7f]", a):
                    warn("%r is shorter than 3 letters and will match inside unrelated answers" % a)

        self.engines = []
        seen = set()
        engines = raw.get("engines") if raw.get("engines") is not None else DEFAULT_ENGINES
        for i, e in enumerate(engines if isinstance(engines, list) else []):
            if not isinstance(e, dict) or e.get("provider") not in PROVIDERS:
                err("engines[%d].provider must be one of: %s" % (i, ", ".join(sorted(PROVIDERS))))
                continue
            eng = dict(e)
            eng["id"] = str(e.get("id") or e["provider"])
            eng["model"] = str(e.get("model") or PROVIDERS[e["provider"]]["model"])
            if not ENGINE_ID_RE.match(eng["id"]) or eng["id"] in seen:
                err("engines[%d].id %r must be unique, lowercase letters, digits and dashes" % (i, eng["id"]))
            if not MODEL_RE.match(eng["model"]):
                err("engines[%d].model %r is not a model name" % (i, eng["model"]))
            bu = e.get("base_url")
            if bu is not None and not (isinstance(bu, str) and re.match(
                    r"^(https://[^\s/]+|http://(localhost|127\.0\.0\.1)(:\d+)?)(/\S*)?$", bu)):
                err("engines[%d].base_url must be https:// (or http://localhost)" % i)
            if e.get("api") is not None and not (e["provider"] == "gemini" and
                                                 e.get("api") in ("interactions", "generate_content")):
                err("engines[%d].api is only for gemini: \"interactions\" or \"generate_content\"" % i)
            ke = e.get("key_env")
            if ke is not None and not (isinstance(ke, str) and ENV_RE.match(ke)):
                err("engines[%d].key_env must name an environment variable" % i)
            seen.add(eng["id"])
            self.engines.append(eng)
        if not self.engines:
            err("no engines configured")

        self.country = raw.get("country") or None
        if self.country is not None and not (isinstance(self.country, str) and COUNTRY_RE.match(self.country)):
            err("country must be a two-letter ISO code such as US, or null")
        self.runs = raw.get("runs", 1)
        if isinstance(self.runs, bool) or not isinstance(self.runs, int) or not 1 <= self.runs <= MAX_RUNS:
            err("runs must be an integer from 1 to %d" % MAX_RUNS)
            self.runs = 1
        self.max_calls = raw.get("max_calls", DEFAULT_MAX_CALLS)
        if isinstance(self.max_calls, bool) or not isinstance(self.max_calls, int) or self.max_calls < 1:
            err("max_calls must be a positive integer")
            self.max_calls = DEFAULT_MAX_CALLS
        self.budget_usd = raw.get("budget_usd")
        if self.budget_usd is not None and _num(self.budget_usd) is None:
            err("budget_usd must be a non-negative number, or null")
            self.budget_usd = None
        self.prices = raw.get("prices") if isinstance(raw.get("prices"), dict) else {}
        for eid, p in self.prices.items():
            if not isinstance(p, dict) or any(v is not None and _num(v) is None for v in p.values()):
                err("prices.%s must map input_per_mtok / output_per_mtok / per_search / per_call to numbers" % eid)
        q = raw.get("queries", "queries.csv")
        self.queries_path = os.path.join(self.dir, q) if isinstance(q, str) and q else ""
        if not self.queries_path:
            err("queries must name a CSV file")

    def runs_dir(self):
        return os.path.join(self.dir, STATE_DIR, "runs")

    def load_queries(self):
        if not os.path.isfile(self.queries_path):
            raise ConfigError("no question list at %s" % self.queries_path)
        names, rows = _read_csv(self.queries_path)
        if "query_id" not in names or "query" not in names:
            raise ConfigError("%s needs the columns %s" % (self.queries_path, ",".join(QUERY_COLS)))
        out, ids, problems = [], set(), []
        for n, r in enumerate(rows, 2):
            vals = {k: (r.get(k) or "").strip() if isinstance(r.get(k), str) else "" for k in QUERY_COLS}
            if not any(vals.values()):
                continue
            qid, q = vals["query_id"], vals["query"]
            if not QUERY_ID_RE.match(qid):
                problems.append("line %d: query_id %r — letters, digits, _ . - only" % (n, qid))
            elif qid in ids:
                problems.append("line %d: query_id %s is used twice" % (n, qid))
            if not q:
                problems.append("line %d: empty query" % n)
            elif re.search(r"<[^>]*>", q):
                problems.append("line %d: replace the <placeholder> with a real question" % n)
            elif len(q) > MAX_QUERY_LEN:
                problems.append("line %d: query longer than %d characters" % (n, MAX_QUERY_LEN))
            b = r.get("branded")
            b = b.strip().lower() if isinstance(b, str) else ""
            if b and b not in BRANDED_VALUES:
                problems.append("line %d: branded must be auto, yes or no, not %r" % (n, b))
            vals["branded"] = b or "auto"
            ids.add(qid)
            out.append(vals)
        if problems:
            raise ConfigError("%s:\n  %s" % (self.queries_path, "\n  ".join(problems)))
        if not out:
            raise ConfigError("%s has no questions" % self.queries_path)
        if len(out) > MAX_QUERIES:
            raise ConfigError("%s has %d questions; the limit is %d" % (self.queries_path, len(out), MAX_QUERIES))
        return out


def has_price(cfg_prices, eng):
    if PROVIDERS[eng["provider"]]["reports_cost"]:
        return True
    p = cfg_prices.get(eng["id"]) if isinstance(cfg_prices, dict) else None
    return isinstance(p, dict) and _num(p.get("input_per_mtok")) is not None \
        and _num(p.get("output_per_mtok")) is not None


def cost_of(cfg_prices, eng, usage, reported):
    """Provider-reported cost wins. Otherwise tokens x the prices in geo-score-watch.json; None when unknown."""
    if reported is not None:
        return round(reported, 6)
    p = cfg_prices.get(eng["id"]) if isinstance(cfg_prices, dict) else None
    if not isinstance(p, dict):
        return None
    pin, pout = _num(p.get("input_per_mtok")), _num(p.get("output_per_mtok"))
    if pin is None or pout is None:
        return None
    total = usage["input_tokens"] / 1e6 * pin + usage["output_tokens"] / 1e6 * pout
    total += usage["search_calls"] * (_num(p.get("per_search")) or 0.0)
    total += usage["api_calls"] * (_num(p.get("per_call")) or 0.0)
    return round(total, 6)


# ── running ───────────────────────────────────────────────────────────────
class Ledger(object):
    """Every call is counted before it is made. max_calls is exact; the budget is checked against spend so far
    plus the dearest call seen on that engine, so it can only be overrun by what an engine's first call costs."""

    def __init__(self, max_calls, budget):
        self.lock = threading.Lock()
        self.max_calls, self.budget = max_calls, budget
        self.samples = self.api_calls = self.attempts = self.errors = 0
        self.input_tokens = self.output_tokens = self.search_calls = self.unpriced = 0
        self.cost = self.reserved = 0.0
        self.peak = {}

    def acquire(self, eid):
        with self.lock:
            if self.samples >= self.max_calls:
                return None, "max_calls"
            est = self.peak.get(eid, 0.0)
            if self.budget is not None and (self.cost + self.reserved >= self.budget or
                                            self.cost + self.reserved + est > self.budget):
                return None, "budget"
            self.samples += 1
            self.reserved += est
            return est, None

    def settle(self, eid, est, attempts, usage=None, cost=None):
        with self.lock:
            self.reserved -= est
            self.attempts += attempts
            if usage is None:
                self.errors += 1
                return
            self.api_calls += usage["api_calls"]
            self.input_tokens += usage["input_tokens"]
            self.output_tokens += usage["output_tokens"]
            self.search_calls += usage["search_calls"]
            if cost is None:
                self.unpriced += 1
            else:
                self.cost += cost
                self.peak[eid] = max(self.peak.get(eid, 0.0), cost)

    def as_json(self):
        return {"questions_asked": self.samples, "api_requests": self.api_calls, "http_attempts": self.attempts,
                "errors": self.errors, "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
                "search_calls": self.search_calls, "cost_usd": round(self.cost, 4),
                "unpriced_answers": self.unpriced, "cost_complete": self.unpriced == 0}


def select_engines(engines, only):
    if not only:
        return list(engines)
    want = [x.strip() for x in only if x.strip()]
    ids = [e["id"] for e in engines]
    bad = [x for x in want if x not in ids]
    if bad:
        raise ConfigError("unknown engine %s (configured: %s)" % (", ".join(bad), ", ".join(ids)))
    return [e for e in engines if e["id"] in want]


def plan(engines, prices, budget, allow_unpriced):
    """Which engines will run, and why the others will not."""
    active, status = [], {}
    for e in engines:
        key = key_for(e)
        if not key:
            status[e["id"]] = "no_key"
        elif budget is not None and not allow_unpriced and not has_price(prices, e):
            status[e["id"]] = "no_price"
        else:
            status[e["id"]] = "measured"
            active.append((e, key))
    return active, status


def execute(brand, rivals, engines, queries, runs=1, country=None, prices=None, max_calls=DEFAULT_MAX_CALLS,
            budget=None, allow_unpriced=False, progress=None, stop=None, resolve=True):
    prices = prices or {}
    started = NOW()
    queries = [flag_query(q, brand, rivals) for q in queries]
    active, status = plan(engines, prices, budget, allow_unpriced)
    slots = [(r, q, e) for r in range(1, runs + 1) for q in queries for e, _ in active]
    samples = [None] * len(slots)
    lanes = dict((e["id"], []) for e, _ in active)
    for i, (_, _, e) in enumerate(slots):
        lanes[e["id"]].append(i)
    ledger = Ledger(max_calls, budget)
    stop = stop or threading.Event()
    stopped = {}
    done = [0]
    done_lock = threading.Lock()

    def finish(i, s):
        samples[i] = s
        with done_lock:
            done[0] += 1
            n = done[0]
        if progress:
            progress(n, len(slots), s)

    def lane(e, key):
        fails = 0
        for i in lanes[e["id"]]:
            r, q, _ = slots[i]
            base = {"query_id": q["query_id"], "engine": e["id"], "run": r}
            if stop.is_set():
                finish(i, dict(base, status="skipped", skip_reason="interrupted"))
                continue
            if e["id"] in stopped:
                finish(i, dict(base, status="skipped", skip_reason=stopped[e["id"]][0]))
                continue
            est, why = ledger.acquire(e["id"])
            if why:
                finish(i, dict(base, status="skipped", skip_reason=why))
                continue
            t0 = time.time()
            try:
                res = CALLERS[e["provider"]](e, key, q["query"], country)
            except EngineError as err:
                ledger.settle(e["id"], est, 1)
                fails += 1
                if err.fatal or fails >= 3:
                    stopped[e["id"]] = ("engine_failed", str(err))
                finish(i, dict(base, status="error", error=str(err)))
                continue
            except Exception as err:   # an answer shape we did not expect: record it, keep going
                ledger.settle(e["id"], est, 1)
                fails += 1
                if fails >= 3:
                    stopped[e["id"]] = ("engine_failed", redact("unexpected: %s" % err, key))
                finish(i, dict(base, status="error", error=redact("unexpected: %r" % err, key)))
                continue
            fails = 0
            cost = cost_of(prices, e, res["usage"], res["reported_cost"])
            ledger.settle(e["id"], est, res["attempts"], res["usage"], cost)
            if cost is None and budget is not None and not allow_unpriced:
                stopped[e["id"]] = ("unpriced", "the provider did not report this call's cost, so the budget "
                                                "cannot cover this engine")
            try:
                s = dict(base, status="ok", **evaluate(res, brand, rivals, resolve))
            except Exception as err:   # the call was paid for; keep the fact that it failed to parse
                finish(i, dict(base, status="error", error=redact("unexpected: %r" % err, key)))
                continue
            s.update(usage=res["usage"], cost_usd=cost, seconds=round(time.time() - t0, 1))
            finish(i, s)

    interrupted = False
    threads = [threading.Thread(target=lane, args=(e, k), daemon=True) for e, k in active]
    for t in threads:
        t.start()
    try:
        for t in threads:
            while t.is_alive():
                t.join(0.2)
    except KeyboardInterrupt:
        interrupted = True
        stop.set()
        print("\ninterrupted — letting in-flight calls finish, then saving what was answered", file=sys.stderr)
        for t in threads:
            t.join()
    interrupted = interrupted or stop.is_set()
    for i, s in enumerate(samples):   # a lane that died must not leave a hole in the run
        if s is None:
            r, q, e = slots[i]
            samples[i] = {"query_id": q["query_id"], "engine": e["id"], "run": r, "status": "error",
                          "error": "internal: no result recorded"}

    eng_rows = []
    for e in engines:
        row = {"id": e["id"], "provider": e["provider"], "model": e["model"], "status": status[e["id"]]}
        if e["id"] in stopped:
            row["stopped"] = stopped[e["id"]][0]
            row["error"] = stopped[e["id"]][1]
        if status[e["id"]] == "no_key":
            row["error"] = key_issue(e)
        elif status[e["id"]] == "no_price":
            row["error"] = "a budget is set but geo-score-watch.json has no prices for this engine"
        eng_rows.append(row)
    run = {"format": RUN_FORMAT, "tool": "geo-score-watch/" + __version__, "channel": "api",
           "run_id": started.strftime("%Y%m%dT%H%M%SZ"),
           "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "finished_at": NOW().strftime("%Y-%m-%dT%H:%M:%SZ"),
           "interrupted": interrupted, "brand": brand.as_json(),
           "competitors": [r.as_json() for r in rivals], "country": country, "runs": runs,
           "engines": eng_rows, "queries": queries,
           "caps": {"max_calls": max_calls, "budget_usd": budget},
           "ledger": ledger.as_json(), "samples": samples, "notes": NOTES}
    run["summary"] = summarize(run)
    return run


# ── reading a run ─────────────────────────────────────────────────────────
def summarize(run):
    brand = Entity(run["brand"], you=True)
    rivals = [Entity(c) for c in run.get("competitors") or []]
    samples = run["samples"]
    ok = [s for s in samples if s["status"] == "ok"]
    qtext = dict((q["query_id"], q) for q in run["queries"])
    rid = run.get("run_id") or ""

    def block(rows, label, hit=lambda s: s["cited"], named=lambda s: s["mentioned"]):
        k = sum(1 for s in rows if hit(s))
        m = sum(1 for s in rows if named(s))
        per_q = {}
        for s in rows:
            c = per_q.setdefault(s["query_id"], [0, 0])
            c[0] += 1 if hit(s) else 0
            c[1] += 1
        return {"answered": len(rows), "cited": k, "cited_rate": rate(k, len(rows)), "cited_ci": wilson(k, len(rows)),
                "cited_ci_clustered": cluster_ci([tuple(per_q[q]) for q in sorted(per_q)], _seed(rid, label)),
                "n_questions": len(per_q), "mentioned": m, "mentioned_rate": rate(m, len(rows))}

    engines = []
    for e in run["engines"]:
        es = [s for s in samples if s["engine"] == e["id"]]
        eo = [s for s in es if s["status"] == "ok"]
        ranks = [s["rank"] for s in eo if s["rank"]]
        row = dict(block(eo, "engine:" + e["id"]), id=e["id"], model=e["model"], status=e["status"],
                   errors=sum(1 for s in es if s["status"] == "error"),
                   skipped=sum(1 for s in es if s["status"] == "skipped"),
                   avg_rank=round(sum(ranks) / float(len(ranks)), 1) if ranks else None)
        engines.append(row)

    everything = block(ok, "overall")
    share = [dict(everything, name=brand.name, you=True)]
    for r in rivals:
        share.append(dict(block(ok, "rival:" + r.name,
                                hit=lambda s, n=r.name: bool(s["competitors"].get(n, {}).get("cited")),
                                named=lambda s, n=r.name: bool(s["competitors"].get(n, {}).get("mentioned"))),
                          name=r.name, you=False))

    counts, owners = Counter(), {}
    for s in ok:
        for c in s["citations"]:
            if brand.owns(c["url"], c["domain"]):
                continue
            owners.setdefault(c["domain"], next((r.name for r in rivals if r.owns(c["url"], c["domain"])), None))
        counts.update(set(c["domain"] for c in s["citations"] if not brand.owns(c["url"], c["domain"])))
    sources = [{"domain": d, "answers": n, "share": rate(n, len(ok)), "owner": owners.get(d)}
               for d, n in counts.most_common(15)]

    per_q = {}
    for s in ok:
        per_q.setdefault(s["query_id"], []).append(s)
    gaps, yours = [], 0
    for qid, rows in per_q.items():
        if any(s["cited"] for s in rows):
            yours += 1
            continue
        rivals_hit = _uniq(n for s in rows for n, v in s["competitors"].items() if v.get("cited"))
        if rivals_hit:
            gaps.append({"query_id": qid, "query": qtext.get(qid, {}).get("query", ""),
                         "competitors": rivals_hit, "answered": len(rows)})

    tiers = {}
    for s in ok:
        t = qtext.get(s["query_id"], {}).get("intent_tier") or ""
        tiers.setdefault(t, []).append(s)
    by_tier = [dict(block(rows, "tier:" + t), tier=t) for t, rows in sorted(tiers.items()) if t]

    # The headline leaves out questions that name the brand: "acme vs rival" all but guarantees an Acme citation.
    stored = all("brand_in_query" in q for q in run["queries"])
    named_ids = sorted(q["query_id"] for q in run["queries"] if is_branded(q, brand))
    headline = block([s for s in ok if s["query_id"] not in named_ids], "headline") if named_ids else dict(everything)
    branded = dict(block([s for s in ok if s["query_id"] in named_ids], "branded"), question_ids=named_ids)
    notes = []
    if not stored:
        notes.append("This run was saved before questions were flagged at run time. Questions that name the brand "
                      "were found when this report was made, from the saved question text and the run's brand "
                      "name, aliases and domains.")

    exposed = [s for s in ok if s["search_queries"]]
    searched = Counter(re.sub(r"\s+", " ", q.lower()).strip() for s in exposed for q in s["search_queries"])
    return {"overall": dict(everything, planned=len(samples),
                            errors=sum(1 for s in samples if s["status"] == "error"),
                            skipped=sum(1 for s in samples if s["status"] == "skipped")),
            "headline": headline, "branded": branded, "brand_flags": "run" if stored else "computed",
            "engines": engines, "share_of_voice": share, "top_sources": sources,
            "questions": {"asked": len(per_q), "cited_somewhere": yours}, "gaps": gaps, "by_tier": by_tier,
            "searches": {"answers_exposing": len(exposed),
                         "top": [{"query": q, "count": n} for q, n in searched.most_common(15)]},
            "notes": notes}


def summary_of(run):
    """The stored summary, or a fresh one for a run saved before the clustered intervals and the branded
    split existed. Summaries are derived from the samples, so recomputing one changes no measurement."""
    sm = run.get("summary")
    if isinstance(sm, dict) and "headline" in sm and "n_questions" in (sm.get("overall") or {}):
        return sm
    return summarize(run)


def _asks(run, common_q, engines):
    """(query_id, engine) -> whether each answered ask cited the brand, in ask order."""
    out = {}
    rows = [s for s in run["samples"] if s["status"] == "ok" and s["engine"] in engines and s["query_id"] in common_q]
    for s in sorted(rows, key=lambda s: s.get("run") or 1):
        out.setdefault((s["query_id"], s["engine"]), []).append(bool(s["cited"]))
    return out


def _paired(pairs, seed):
    """pairs: {(query_id, engine): (cited on each ask before, cited on each ask after)}, over the asks both runs
    made. The paired comparison of one diff row."""
    by_q = {}
    for (q, _), (xs, ys) in pairs.items():
        u = by_q.setdefault(q, [0, 0])
        u[0] += sum(ys) - sum(xs)
        u[1] += len(xs)
    asks = [(x, y) for xs, ys in pairs.values() for x, y in zip(xs, ys)]
    n = len(asks)
    both = sum(1 for x, y in asks if x and y)
    lost = sum(1 for x, y in asks if x and not y)
    gained = sum(1 for x, y in asks if y and not x)
    out = {"n_pairs": len(pairs), "n_questions": len(by_q), "n_asks": n, "before_paired": rate(both + lost, n),
           "after_paired": rate(both + gained, n), "delta_pp": round(100.0 * (gained - lost) / n, 1) if n else None,
           "delta_ci": None, "p_paired": None, "p_adjusted": None}
    if not n:
        return out
    # One ask on one engine per question: McNemar. Otherwise the same exact test on each question's net change
    # in cited answers, so repeated asks and several engines add evidence without being counted as independent.
    p = mcnemar_p(gained, lost) if n == len(by_q) else signflip_p([u[0] for u in by_q.values()])
    out["p_paired"] = round(p, 4)
    out["_p"] = p
    if len(by_q) >= MIN_PAIRED:
        out["delta_ci"] = paired_ci([tuple(by_q[q]) for q in sorted(by_q)], (both, lost, gained, n - both - lost - gained),
                                    seed)
    return out


def diff_runs(a, b):
    """What changed from run a to run b, on the questions and engines both runs measured. Answers are paired
    by question, engine and ask (the asks both runs made); the verdict comes from an exact paired test with
    Holm's correction across the rows."""
    common_q = set(q["query_id"] for q in a["queries"]) & set(q["query_id"] for q in b["queries"])
    ea = dict((e["id"], e) for e in a["engines"])
    eb = dict((e["id"], e) for e in b["engines"])
    notes, rows = [], []
    if a.get("channel") != b.get("channel"):
        notes.append("the runs come from different channels; they are not comparable")
    if a["brand"].get("domains") != b["brand"].get("domains") or \
            a["brand"].get("url_prefixes") != b["brand"].get("url_prefixes"):
        notes.append("the brand's domains changed between runs, so 'cited' was judged differently")
    dropped = len(set(q["query_id"] for q in a["queries"]) ^ set(q["query_id"] for q in b["queries"]))
    if dropped:
        notes.append("%d questions appear in only one run and are left out" % dropped)
    if a.get("runs") != b.get("runs"):
        notes.append("the runs asked each question %s and %s times; the paired test uses the asks both made "
                     "(the first %s)" % (a.get("runs"), b.get("runs"), min(a.get("runs") or 1, b.get("runs") or 1)))
    common_e = [e for e in ea if e in eb]
    asks_a, asks_b = _asks(a, common_q, set(common_e)), _asks(b, common_q, set(common_e))
    pairs = {}
    for u, xs in asks_a.items():
        ys = asks_b.get(u)
        if ys:
            k = min(len(xs), len(ys))
            pairs[u] = (xs[:k], ys[:k])

    def pick(run, eid):
        return [s for s in run["samples"] if s["status"] == "ok" and s["engine"] == eid and s["query_id"] in common_q]

    def compare(label, sa, sb, sub, model_note=None):
        # before, after, delta and p_value are unpaired, every answer counted, as in 1.2.0; the verdict is not
        k1, n1 = sum(1 for s in sa if s["cited"]), len(sa)
        k2, n2 = sum(1 for s in sb if s["cited"]), len(sb)
        p = two_prop_p(k1, n1, k2, n2)
        row = {"engine": label, "before": rate(k1, n1), "after": rate(k2, n2), "before_n": n1, "after_n": n2,
               "delta": None if p is None else round(k2 / float(n2) - k1 / float(n1), 4),
               "p_value": None if p is None else round(p, 4)}
        row.update(_paired(sub, _seed(a["run_id"], b["run_id"], label)))
        if p is None:
            row["verdict"] = "not measured"
        elif row["n_questions"] < MIN_PAIRED:
            row["verdict"] = "too few questions to tell"
        row["note"] = model_note
        return row

    all_a, all_b = [], []
    for eid in common_e:
        note = None
        if ea[eid]["model"] != eb[eid]["model"]:
            note = "model changed: %s -> %s" % (ea[eid]["model"], eb[eid]["model"])
        sa, sb = pick(a, eid), pick(b, eid)
        all_a += sa
        all_b += sb
        rows.append(compare(eid, sa, sb, dict((u, v) for u, v in pairs.items() if u[1] == eid), note))
    overall = compare("all engines", all_a, all_b, pairs)

    # Holm over the engines plus the overall row. With one engine the overall row is that engine's test again.
    with_pairs = [r for r in rows if r["n_pairs"]]
    family = [r for r in rows + [overall] if "verdict" not in r]
    if len(with_pairs) == 1 and overall in family:
        family.remove(overall)
    for r, pa in zip(family, holm([r["_p"] for r in family])):
        r["p_adjusted"] = round(pa, 4)
        r["verdict"] = "change" if pa < ALPHA else "within noise"
    if "verdict" not in overall:
        overall["p_adjusted"] = with_pairs[0]["p_adjusted"]
        overall["verdict"] = with_pairs[0]["verdict"]
    for r in rows + [overall]:
        r.pop("_p", None)

    def cited_where(run):
        out = {}
        for s in run["samples"]:
            if s["status"] == "ok" and s["query_id"] in common_q and s["engine"] in eb and s["engine"] in ea:
                cur = out.setdefault((s["query_id"], s["engine"]), [False, None])
                if s["cited"]:
                    cur[0], cur[1] = True, cur[1] or s["quoted_url"]
        return out

    ca, cb = cited_where(a), cited_where(b)
    qtext = dict((q["query_id"], q["query"]) for q in b["queries"])
    lost = [{"query_id": q, "engine": e, "query": qtext.get(q, ""), "was": ca[(q, e)][1]}
            for (q, e) in sorted(ca) if ca[(q, e)][0] and (q, e) in cb and not cb[(q, e)][0]]
    gained = [{"query_id": q, "engine": e, "query": qtext.get(q, ""), "now": cb[(q, e)][1]}
              for (q, e) in sorted(cb) if cb[(q, e)][0] and (q, e) in ca and not ca[(q, e)][0]]
    return {"from": a["run_id"], "to": b["run_id"], "overall": overall, "engines": rows,
            "lost": lost, "gained": gained, "notes": notes, "alpha": ALPHA, "min_questions": MIN_PAIRED}


def drops(d):
    """Rows whose verdict is a change for the worse."""
    return [r["engine"] for r in [d["overall"]] + d["engines"]
            if r["verdict"] == "change" and (r.get("delta_pp") or 0) < 0]


# ── rendering ─────────────────────────────────────────────────────────────
def _w(s):
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def _pad(s, w):
    s = str(s)
    return s + " " * max(0, w - _w(s))


_CTRL = re.compile("[\x00-\x08\x0b-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]")


def _cut(s, n):
    # model answers are untrusted text: strip terminal escapes and bidi controls before printing
    s = re.sub(r"\s+", " ", _CTRL.sub("", str(s or ""))).strip()
    if _w(s) <= n:
        return s
    out = ""
    for ch in s:
        if _w(out + ch) > n - 1:
            break
        out += ch
    return out + "…"


def pct(x):
    return "—" if x is None else "%d%%" % round(x * 100)


def ci_s(c):
    return "—" if not c else "%d–%d%%" % (round(c[0] * 100), round(c[1] * 100))


def head_ci(b):
    """The interval to quote: the bootstrap over questions when some question has several answers, else Wilson."""
    if b.get("cited_ci_clustered") and b["answered"] > b.get("n_questions", b["answered"]):
        return b["cited_ci_clustered"]
    return b.get("cited_ci")


def _n(k, word):
    return "%d %s%s" % (k, word, "" if k == 1 else "s")


def table(headers, rows, fmt):
    rows = [[str(c) for c in r] for r in rows]
    if fmt == "md":
        esc = lambda c: c.replace("|", "\\|")
        out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
        return "\n".join(out + ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows])
    widths = [max([_w(h)] + [_w(r[i]) for r in rows]) for i, h in enumerate(headers)]
    lines = ["  " + "  ".join(_pad(h, widths[i]) for i, h in enumerate(headers)).rstrip()]
    lines += ["  " + "  ".join(_pad(c, widths[i]) for i, c in enumerate(r)).rstrip() for r in rows]
    return "\n".join(lines)


def _h(title, fmt):
    return "\n## %s\n" % title if fmt == "md" else "\n%s" % title


def money(x):
    if not x:
        return "$0"
    return "$%.4f" % x if x < 0.01 else "$%.2f" % x


def render(run, fmt="text"):
    sm = summary_of(run)
    o, L = sm["overall"], []
    engines_n = sum(1 for e in run["engines"] if e["status"] == "measured")
    head = "geo-score watch · %s · run %s · %s channel" % (run["brand"]["name"] or "(no brand)", run["run_id"], run["channel"])
    L.append("# " + head if fmt == "md" else head)
    L.append("")
    L.append("%d questions × %d engines × %d = %d planned · %d answered · %d failed · %d skipped%s" % (
        len(run["queries"]), engines_n, run["runs"], o["planned"], o["answered"], o["errors"], o["skipped"],
        " · interrupted" if run.get("interrupted") else ""))
    name = run["brand"]["name"] or "the brand"
    h, br = sm["headline"], sm["branded"]
    if o["answered"]:
        L.append("")
        if not br["question_ids"]:
            line = "Cited in %s of answers (%d of %d, 95%% CI %s) · mentioned in %s" % (
                pct(o["cited_rate"]), o["cited"], o["answered"], ci_s(head_ci(o)), pct(o["mentioned_rate"]))
        elif h["answered"]:
            line = "Cited in %s of answers to questions that do not name %s (%d of %d, %s, 95%% CI %s) · " \
                   "mentioned in %s" % (pct(h["cited_rate"]), name, h["cited"], h["answered"],
                                        _n(h["n_questions"], "question"), ci_s(head_ci(h)), pct(h["mentioned_rate"]))
        else:
            line = "No headline rate: no question that leaves out %s was answered" % name
        L.append("**%s**" % line if fmt == "md" else line)
        if br["question_ids"]:
            L.append("Questions that name %s (%d, kept out of the headline): %s" % (
                name, len(br["question_ids"]), "no answers" if not br["answered"] else
                "cited in %s (%d of %d, 95%% CI %s) · mentioned in %s" % (
                    pct(br["cited_rate"]), br["cited"], br["answered"], ci_s(head_ci(br)), pct(br["mentioned_rate"]))))
        L.append("Your site was cited somewhere for %d of %d questions." % (
            sm["questions"]["cited_somewhere"], sm["questions"]["asked"]))

    L.append(_h("By engine", fmt))
    rows = []
    for e in sm["engines"]:
        if e["status"] != "measured":
            err = next((x.get("error") for x in run["engines"] if x["id"] == e["id"]), "")
            rows.append([e["id"], e["model"], "not measured", "", "", "", e["status"] + (": " + err if err else "")])
            continue
        extra = []
        if e["errors"]:
            extra.append("%d failed" % e["errors"])
        if e["skipped"]:
            extra.append("%d skipped" % e["skipped"])
        stop = next((x for x in run["engines"] if x["id"] == e["id"] and x.get("stopped")), None)
        if stop:
            extra.append("stopped: " + _cut(stop.get("error", ""), 60))
        rows.append([e["id"], e["model"], "%d/%d %s" % (e["cited"], e["answered"], pct(e["cited_rate"])),
                     ci_s(head_ci(e)), pct(e["mentioned_rate"]), e["avg_rank"] or "—", ", ".join(extra)])
    L.append(table(["engine", "model", "cited", "95% CI", "mentioned", "avg rank", ""], rows, fmt))
    if br["question_ids"]:
        L.append("")   # a line right under a markdown table would be read as another row
        L.append("These rows, and the tables below, count every question, the %d that name %s included." % (
            len(br["question_ids"]), name))

    if len(sm["share_of_voice"]) > 1:
        L.append(_h("Share of voice", fmt))
        L.append(table(["", "cited", "95% CI", "mentioned"],
                       [[s["name"] + (" (you)" if s["you"] else ""), pct(s["cited_rate"]), ci_s(head_ci(s)),
                         pct(s["mentioned_rate"])] for s in sm["share_of_voice"]], fmt))

    if sm["top_sources"]:
        L.append(_h("Sources the engines cite most (not yours)", fmt))
        L.append(table(["domain", "answers", "share", "owner"],
                       [[s["domain"], s["answers"], pct(s["share"]), s["owner"] or ""] for s in sm["top_sources"]], fmt))

    if sm["gaps"]:
        L.append(_h("Questions where a competitor is cited and you are not (%d)" % len(sm["gaps"]), fmt))
        L.append(table(["id", "question", "cited instead"],
                       [[g["query_id"], _cut(g["query"], 60), ", ".join(g["competitors"])] for g in sm["gaps"]], fmt))

    if sm["by_tier"]:
        L.append(_h("By question type", fmt))
        L.append(table(["type", "cited", "95% CI", "mentioned"],
                       [[t["tier"], "%d/%d %s" % (t["cited"], t["answered"], pct(t["cited_rate"])), ci_s(head_ci(t)),
                         pct(t["mentioned_rate"])] for t in sm["by_tier"]], fmt))

    if sm["searches"]["top"]:
        L.append(_h("What the engines searched for (from %d answers that show it)" % sm["searches"]["answers_exposing"], fmt))
        L.append(table(["times", "search"], [[s["count"], _cut(s["query"], 70)] for s in sm["searches"]["top"]], fmt))

    lg = run["ledger"]
    L.append(_h("Ledger", fmt))
    cost = money(lg["cost_usd"])
    if not lg["cost_complete"]:
        cost += " + %d answers with no price (add prices to geo-score-watch.json)" % lg["unpriced_answers"]
    L.append("%d questions asked · %d API requests · %s in / %s out tokens · %d searches · %s" % (
        lg["questions_asked"], lg["api_requests"], "{:,}".format(lg["input_tokens"]),
        "{:,}".format(lg["output_tokens"]), lg["search_calls"], cost))
    caps = run["caps"]
    L.append("Caps: at most %d questions%s." % (caps["max_calls"],
                                                "" if caps["budget_usd"] is None else ", budget " + money(caps["budget_usd"])))
    L.append(_h("Read this before quoting the numbers", fmt))
    L.extend("- " + n for n in NOTES + sm.get("notes", []))   # the numbers above are this release's arithmetic
    return "\n".join(L) + "\n"


def render_ask(run, fmt="text"):
    brand = run["brand"]["name"]
    L = ["# " + run["queries"][0]["query"] if fmt == "md" else "Q: " + run["queries"][0]["query"], ""]
    for e in run["engines"]:
        if e["status"] != "measured":
            L.append("%s — not measured (%s)" % (e["id"], e.get("error") or e["status"]))
            continue
        s = next((x for x in run["samples"] if x["engine"] == e["id"]), None)
        if s is None or s["status"] != "ok":
            L.append("%s — %s" % (e["id"], (s or {}).get("error") or (s or {}).get("skip_reason") or "no answer"))
            continue
        verdict = []
        if brand:
            verdict.append("cited #%d (%s)" % (s["rank"], s["quoted_url"]) if s["cited"] else "not cited")
            verdict.append("mentioned" if s["mentioned"] else "not mentioned")
        rivals = [n for n, v in s["competitors"].items() if v["cited"]]
        if rivals:
            verdict.append("competitors cited: " + ", ".join(rivals))
        title = "%s (%s)" % (e["id"], e["model"])
        L.append(("## " + title if fmt == "md" else title) + (" — " + " · ".join(verdict) if verdict else ""))
        doms = _uniq(c["domain"] for c in s["citations"])
        L.append("  sources: " + (", ".join(doms[:8]) + (" …" if len(doms) > 8 else "") if doms else "none"))
        if s["search_queries"]:
            L.append("  searched: " + " | ".join(_cut(q, 60) for q in s["search_queries"][:4]))
        L.append("  answer: " + _cut(s["answer"], 280))
        L.append("")
    L.append("(api channel — not the consumer apps; one ask per engine, so treat it as an anecdote, not a rate)")
    return "\n".join(L) + "\n"


def render_diff(d, fmt="text"):
    L = ["# Changes %s → %s" % (d["from"], d["to"]) if fmt == "md" else "Changes %s -> %s" % (d["from"], d["to"])]
    rows, verdicts = [], set()
    for r in [d["overall"]] + d["engines"]:
        ci, p = r["delta_ci"], r["p_adjusted"]
        verdicts.add(r["verdict"])
        rows.append([r["engine"], "%s (n=%d)" % (pct(r["before_paired"]), r["n_asks"]),
                     "%s (n=%d)" % (pct(r["after_paired"]), r["n_asks"]),
                     "—" if r["delta_pp"] is None else "%+d pts" % round(r["delta_pp"]),
                     "%+d to %+d" % (round(ci[0]), round(ci[1])) if ci else "—",
                     "—" if p is None else "%.3f" % p, r["verdict"], r["note"] or ""])
    L.append("")
    L.append(table(["", "before", "after", "change", "95% CI", "p (Holm)", "verdict", ""], rows, fmt))
    L.append("")
    L.append("before / after: share of answers citing you, over the asks both runs made of the questions both "
             "answered (n = answers per run). p: exact paired test (McNemar), Holm-adjusted across the rows; a change "
             "needs p < %.2f." % d.get("alpha", ALPHA))
    if "too few questions to tell" in verdicts:
        L.append("too few questions to tell: fewer than %d questions were answered in both runs, so even if every "
                 "one of them flipped the same way the change would still be within noise." % d.get("min_questions",
                                                                                                  MIN_PAIRED))
    if d["lost"]:
        L.append(_h("Citations lost (%d)" % len(d["lost"]), fmt))
        L.append(table(["id", "engine", "question", "was citing"],
                       [[x["query_id"], x["engine"], _cut(x["query"], 50), x["was"] or ""] for x in d["lost"]], fmt))
    if d["gained"]:
        L.append(_h("Citations gained (%d)" % len(d["gained"]), fmt))
        L.append(table(["id", "engine", "question", "now citing"],
                       [[x["query_id"], x["engine"], _cut(x["query"], 50), x["now"] or ""] for x in d["gained"]], fmt))
    L.append("")
    for n in d["notes"]:
        L.append("note: " + n)
    L.append("A single question flipping is normal variation; read the verdict column, not the lists, for trends.")
    return "\n".join(L) + "\n"


def _csv_safe(v):
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def render_csv(run):
    started = datetime.datetime.strptime(run["started_at"], "%Y-%m-%dT%H:%M:%SZ")
    week = "%d-W%02d" % started.isocalendar()[:2]
    brand = Entity(run["brand"], you=True)
    models = dict((e["id"], e["model"]) for e in run["engines"])
    qs = dict((q["query_id"], q) for q in run["queries"])
    named = set(q["query_id"] for q in run["queries"] if is_branded(q, brand))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for s in run["samples"]:
        q = qs.get(s["query_id"], {})
        if s["status"] == "ok":
            others = _uniq(c["domain"] for c in s["citations"] if not brand.owns(c["url"], c["domain"]))[:3]
            row = ["Y" if s["cited"] else "N", s["quoted_url"] or "", s["rank"] or "", ",".join(others),
                   "api · %s" % models.get(s["engine"], "")]
        else:
            row = ["", "", "", "", "%s: %s" % (s["status"], s.get("error") or s.get("skip_reason") or "")]
        w.writerow([_csv_safe(v) for v in [week, s["query_id"], q.get("query", ""), q.get("intent_tier", ""),
                                            s["engine"]] + row + ["Y" if s["query_id"] in named else "N"]])
    return buf.getvalue()


# ── storage ───────────────────────────────────────────────────────────────
def _run_sort_key(name):
    m = RUN_ID_RE.match(name)
    return (m.group(1), int(m.group(2) or 1)) if m else ("", 0)


def list_run_ids(cfg):
    d = cfg.runs_dir()
    if not os.path.isdir(d):
        return []
    ids = [f[:-5] for f in os.listdir(d) if f.endswith(".json") and RUN_ID_RE.match(f[:-5])]
    return sorted(ids, key=_run_sort_key)


def save_run(cfg, run):
    d = cfg.runs_dir()
    os.makedirs(d, exist_ok=True)
    base, n = run["run_id"], 1
    while True:
        rid = base if n == 1 else "%s-%d" % (base, n)
        path = os.path.join(d, rid + ".json")
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            break
        except FileExistsError:
            n += 1
    run["run_id"] = rid
    with io.open(fd, "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return path


def load_run(cfg, rid="latest"):
    ids = list_run_ids(cfg)
    if rid in ("latest", "previous", None, ""):
        need = 2 if rid == "previous" else 1
        if len(ids) < need:
            raise ConfigError("no %s run in %s" % ("earlier" if need == 2 else "saved", cfg.runs_dir()))
        rid = ids[-need]
    if not RUN_ID_RE.match(str(rid)):
        raise ConfigError("run ids look like 20260926T083000Z; got %r" % rid)
    path = os.path.join(cfg.runs_dir(), rid + ".json")
    try:
        with io.open(path, encoding="utf-8") as f:
            run = json.load(f)
    except (OSError, IOError):
        raise ConfigError("no run %s in %s" % (rid, cfg.runs_dir()))
    except ValueError:
        raise ConfigError("%s is not valid JSON" % path)
    if not isinstance(run, dict) or run.get("format") != RUN_FORMAT:
        raise ConfigError("%s is not a %s file" % (path, RUN_FORMAT))
    return run


GEO_SCORE = None   # set by geo_score.py when it hands a command to this module


def load_geo_score():
    """The score half. geo_score.py passes itself in; otherwise $GEO_SCORE_PY, the geo_score.py next to this
    file, or an importable module."""
    if GEO_SCORE is not None:
        return GEO_SCORE
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo_score.py")
    for p in (os.environ.get("GEO_SCORE_PY"), here):
        if p and os.path.isfile(p):
            try:
                spec = importlib.util.spec_from_file_location("geo_score", p)
                mod = importlib.util.module_from_spec(spec)
                with contextlib.redirect_stdout(sys.stderr):
                    spec.loader.exec_module(mod)
                return mod if callable(getattr(mod, "run", None)) and callable(getattr(mod, "as_json", None)) else None
            except (Exception, SystemExit):
                return None
    try:
        with contextlib.redirect_stdout(sys.stderr):
            import geo_score
        return geo_score if callable(getattr(geo_score, "run", None)) else None
    except (Exception, SystemExit):
        return None


# ── level 2: the score's --ask ────────────────────────────────────────────
MAX_ASK = 5
ASK_NOTE = ("API channel, not the consumer apps. One ask per engine is an anecdote, not a rate, and it is never "
            "summed into readiness. Track a fixed question set weekly with `geo_score.py watch`.")


# Hosts shared by many unrelated sites: the brand owns its own subdomain there, never the whole suffix.
SHARED_HOSTS = ("github.io", "vercel.app", "netlify.app", "pages.dev", "myshopify.com", "herokuapp.com",
                "wordpress.com", "blogspot.com", "substack.com", "medium.com", "notion.site", "webflow.io",
                "framer.website", "wixsite.com", "squarespace.com", "carrd.co", "gitbook.io", "readthedocs.io")
_SECOND_LEVEL = ("co", "com", "net", "org", "gov", "edu", "ac", "or", "ne", "go")


def site_domain(host):
    """The part of a host a brand owns: stripe.com for docs.stripe.com, acme.co.uk for shop.acme.co.uk,
    but acme.github.io stays acme.github.io."""
    labels = [x for x in host.split(".") if x]
    if len(labels) < 2:
        return host
    for suffix in SHARED_HOSTS:
        if host == suffix or host.endswith("." + suffix):
            n = suffix.count(".") + 2
            return ".".join(labels[-n:]) if len(labels) >= n else host
    if len(labels) >= 3 and labels[-2] in _SECOND_LEVEL and len(labels[-1]) == 2:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def citation_check(target_url, questions, brand=None, domains=None, landed_url=None, progress=None):
    """Level 2: ask each engine that has a key each question once. Nothing is saved.
    Returns (run or None, citation), where citation fits the `citation` object of schema/report.v2.json.
    Engines that produced no answer are named in the note and never reported as zeros."""
    qs = [q.strip() for q in questions if isinstance(q, str) and q.strip()]
    if not qs or len(qs) > MAX_ASK or any(len(q) > MAX_QUERY_LEN for q in qs):
        raise ConfigError("--ask takes 1 to %d questions of up to %d characters" % (MAX_ASK, MAX_QUERY_LEN))
    hosts = _uniq(host_of(x) for x in [target_url, landed_url] if x)
    owned = _uniq([site_domain(h) for h in hosts] + [host_of(d) for d in (domains or [])])
    notes = []
    name = (brand or "").strip()
    if not name and owned:
        first = owned[0].split(".")[0]
        if len(first) >= 3:
            name = first
            notes.append("Brand name taken from the domain: '%s' (pass --brand to change it)." % name)
        else:
            notes.append("No brand name matched in answer text: '%s' is too short to guess from (pass --brand)." % first)
    you = Entity({"name": name, "domains": owned}, you=True)
    engines = [dict(e, model=PROVIDERS[e["provider"]]["model"]) for e in DEFAULT_ENGINES]
    active, _ = plan(engines, {}, None, True)
    base = {"channel": "api", "queries": qs}
    if not active:
        return None, dict(base, measured=False, engines=[],
                          note="Not measured: no API key found. Set OPENAI_API_KEY, PERPLEXITY_API_KEY, GEMINI_API_KEY "
                               "(or GOOGLE_API_KEY), ANTHROPIC_API_KEY or OPENROUTER_API_KEY to run the citation check.")
    rows = [{"query_id": "q%d" % (i + 1), "query": q, "intent_tier": "", "target_url": ""} for i, q in enumerate(qs)]
    run = execute(you, [], engines, rows, 1, None, {}, len(active) * len(rows), progress=progress)
    sm, lg = run["summary"], run["ledger"]
    answered = [e for e in sm["engines"] if e["status"] == "measured" and e["answered"]]
    failed = [e["id"] for e in sm["engines"] if e["status"] == "measured" and e["errors"]]
    if failed:
        notes.append("No answer from: %s." % ", ".join(failed))
    named = [q["query_id"] for q in run["queries"] if q.get("brand_in_query")]
    if named:
        notes.append("%s %s the brand, which invites answers that cite it; read %s apart from the rest." % (
            ", ".join(named), "names" if len(named) == 1 else "name", "it" if len(named) == 1 else "them"))
    notes.append(ASK_NOTE)
    if not answered:
        return run, dict(base, measured=False, engines=[], note="Not measured: every engine call failed. " + " ".join(notes))
    rows_ok = [x for x in run["samples"] if x["status"] == "ok"]
    cit = dict(base, measured=True, engines=[e["id"] for e in answered],
               answered=len(rows_ok), cited_count=sum(1 for x in rows_ok if x["cited"]),
               mentioned_count=sum(1 for x in rows_ok if x["mentioned"]),
               per_engine=[{"engine": e["id"], "model": e["model"], "answered": e["answered"], "cited": e["cited"],
                            "mentioned": e["mentioned"]} for e in answered],
               top_sources=[x["domain"] for x in sm["top_sources"][:5]],
               # unknown when any call failed (a timeout may have been billed) or was not priced
               cost_usd=lg["cost_usd"] if lg["cost_complete"] and not failed else None,
               note=" ".join(notes))
    return run, cit


def citation_lines(run, cit):
    """Plain lines for the score's text report. geo_score.py adds the colour."""
    L = []
    if run is None:
        return [cit["note"]]
    by = {}
    for smp in run["samples"]:
        by.setdefault(smp["engine"], []).append(smp)
    for e in run["engines"]:
        if e["status"] != "measured":
            L.append("%-15s not measured (%s)" % (e["id"], _cut(e.get("error") or e["status"], 70)))
            continue
        marks = []
        for smp in sorted(by.get(e["id"], []), key=lambda x: x["query_id"]):
            if smp["status"] == "error":
                marks.append("%s failed (%s)" % (smp["query_id"], _cut(smp.get("error", ""), 60)))
            elif smp["status"] != "ok":
                marks.append("%s skipped (%s)" % (smp["query_id"], smp.get("skip_reason", "")))
            elif smp["cited"]:
                marks.append("%s cited #%d" % (smp["query_id"], smp["rank"]))
            else:
                marks.append("%s %s" % (smp["query_id"], "named, not cited" if smp["mentioned"] else "not cited"))
        L.append("%-15s %-18s %s" % (e["id"], _cut(e["model"], 18), " · ".join(marks)))
    for i, q in enumerate(cit["queries"], 1):
        L.append("q%d  %s" % (i, _cut(q, 70)))
    if cit.get("measured"):
        L.append("Cited in %d of %d answers · named in %d" % (cit["cited_count"], cit["answered"], cit["mentioned_count"]))
        if cit.get("top_sources"):
            L.append("Sources the answers leaned on: " + ", ".join(cit["top_sources"]))
    L.append(cit["note"])
    return L


# ── CLI ───────────────────────────────────────────────────────────────────
CONFIG_TEMPLATE = {
    "brand": {"name": "Acme", "domains": ["acme.com"], "aliases": [], "url_prefixes": []},
    "competitors": [],
    "queries": "queries.csv",
    # models written out, so a later geo-score release cannot switch them under a running series
    "engines": [dict(e, model=PROVIDERS[e["provider"]]["model"]) for e in DEFAULT_ENGINES],
    "country": None,
    "runs": 1,
    "max_calls": DEFAULT_MAX_CALLS,
    "budget_usd": None,
    "prices": {},
}


def cmd_init(args):
    d = os.path.abspath(args.dir)
    cfg_path, q_path = os.path.join(d, CONFIG_NAME), os.path.join(d, "queries.csv")
    if not args.force:
        for p in (cfg_path, q_path):
            if os.path.exists(p):
                print("%s already exists (use --force to overwrite)" % p, file=sys.stderr)
                return 1
    cfg = json.loads(json.dumps(CONFIG_TEMPLATE))
    if args.brand:
        cfg["brand"]["name"] = args.brand
    if args.domain:
        cfg["brand"]["domains"] = args.domain
    for c in args.competitor or []:
        name, _, dom = c.partition("=")
        if not name.strip() or not dom.strip():
            print("--competitor takes Name=domain.com, got %r" % c, file=sys.stderr)
            return 1
        cfg["competitors"].append({"name": name.strip(), "domains": [x.strip() for x in dom.split(",") if x.strip()]})
    if args.country:
        cfg["country"] = args.country.upper()
    os.makedirs(d, exist_ok=True)
    with io.open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with io.open(q_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(QUERY_COLS)
        w.writerow(["q01", "<a question your buyers ask an AI assistant, in their words>", "list", ""])
        w.writerow(["q02", "<a pricing or comparison question in your category>", "pricing", ""])
        w.writerow(["q03", "<an 'alternative to <competitor>' question>", "alternative", ""])
    print("wrote %s and %s" % (cfg_path, q_path))
    print("next: put real questions in queries.csv, export API keys, then `geo_score.py watch run --dry-run`")
    return 0


def _load(args):
    cfg = Config(args.config)
    for w in cfg.warnings:
        print("warning: " + w, file=sys.stderr)
    if cfg.errors:
        raise ConfigError("%s:\n  %s" % (args.config, "\n  ".join(cfg.errors)))
    return cfg


def cmd_check(args):
    cfg = Config(args.config)
    for e in cfg.errors:
        print("✗ " + e)
    for w in cfg.warnings:
        print("! " + w)
    try:
        qs = cfg.load_queries()
        print("✓ %d questions in %s" % (len(qs), os.path.relpath(cfg.queries_path)))
        named = [q["query_id"] for q in qs if is_branded(flag_query(q, cfg.brand, cfg.competitors))]
        if named:
            msg = "%d of %d questions (%d%%) name %s (%s): they are reported on their own line, not in the " \
                  "headline rate" % (len(named), len(qs), round(100.0 * len(named) / len(qs)), cfg.brand.name or
                                     "the brand", ", ".join(named[:8]) + (", …" if len(named) > 8 else ""))
            if len(named) > BRANDED_WARN * len(qs):
                print("! %s, which then rests on %s. Mark a false match with branded=no in the "
                      "question file" % (msg, _n(len(qs) - len(named), "question")))
            else:
                print("· " + msg)
    except ConfigError as e:
        cfg.errors.append(str(e))
        print("✗ %s" % e)
    for e in cfg.engines:
        k = "key set" if key_for(e) else "no key — set %s" % key_names(e)
        p = "cost reported by provider" if PROVIDERS[e["provider"]]["reports_cost"] else (
            "priced" if has_price(cfg.prices, e) else "no prices (cost shown as unknown)")
        print("%s %-16s %-10s %-22s %s · %s" % ("✓" if key_for(e) else "·", e["id"], e["provider"], e["model"], k, p))
    return 1 if cfg.errors else 0


def _progress_printer(quiet):
    def show(n, total, s):
        if quiet:
            return
        if s["status"] == "ok":
            mark = "cited #%d" % s["rank"] if s["cited"] else ("mentioned" if s["mentioned"] else "—")
        else:
            mark = "%s: %s" % (s["status"], _cut(s.get("error") or s.get("skip_reason") or "", 70))
        print("[%d/%d] %-16s %-10s %s" % (n, total, s["engine"], s["query_id"], mark), file=sys.stderr)
    return show


def cmd_run(args):
    for flag, v, lo in (("--limit", args.limit, 1), ("--max-calls", args.max_calls, 1), ("--runs", args.runs, 1),
                        ("--budget-usd", args.budget_usd, 0)):
        if v is not None and v < lo:
            raise ConfigError("%s must be at least %s" % (flag, lo))
    cfg = _load(args)
    queries = cfg.load_queries()
    if args.limit:
        queries = queries[:args.limit]
    engines = select_engines(cfg.engines, args.engines.split(",") if args.engines else None)
    runs = args.runs or cfg.runs
    if not 1 <= runs <= MAX_RUNS:
        raise ConfigError("--runs must be from 1 to %d" % MAX_RUNS)
    max_calls = args.max_calls or cfg.max_calls
    budget = args.budget_usd if args.budget_usd is not None else cfg.budget_usd
    active, status = plan(engines, cfg.prices, budget, args.allow_unpriced)
    planned = len(queries) * len(active) * runs
    print("plan: %d questions × %d engines × %d = %d questions to ask (cap %d%s)" % (
        len(queries), len(active), runs, planned, max_calls, "" if budget is None else ", budget " + money(budget)))
    for e in engines:
        if status[e["id"]] == "no_key":
            print("  %s: not measured — %s" % (e["id"], key_issue(e)))
        elif status[e["id"]] == "no_price":
            print("  %s: not measured — a budget is set but there are no prices for it "
                  "(add prices, or pass --allow-unpriced)" % e["id"])
        elif not has_price(cfg.prices, e):
            print("  %s: cost will show as unknown (no prices in geo-score-watch.json)" % e["id"])
    if planned > max_calls:
        raise ConfigError("the plan needs %d questions but the cap is %d; raise --max-calls or ask fewer "
                          "questions (--limit, --engines)" % (planned, max_calls))
    if args.dry_run:
        if not active:
            print("nothing would be measured: export at least one API key")
        return 0
    if not active:
        print("error: nothing can be measured — export at least one API key", file=sys.stderr)
        return 3
    run = execute(cfg.brand, cfg.competitors, engines, queries, runs, cfg.country, cfg.prices, max_calls, budget,
                  args.allow_unpriced, progress=_progress_printer(args.quiet))
    path = save_run(cfg, run)
    print(render(run, args.format if args.format in ("text", "md") else "text"))
    print("saved %s" % os.path.relpath(path))
    return 0 if run["summary"]["overall"]["answered"] else 3


def cmd_ask(args):
    brand, rivals, engines, country = Entity({}), [], None, None
    if os.path.isfile(args.config):
        cfg = _load(args)
        brand, rivals, engines, country = cfg.brand, cfg.competitors, cfg.engines, cfg.country
    if args.brand or args.domain:
        brand = Entity({"name": args.brand or "", "domains": args.domain or []}, you=True)
    if engines is None:
        engines = [dict(e, model=PROVIDERS[e["provider"]]["model"]) for e in DEFAULT_ENGINES]
    engines = select_engines(engines, args.engines.split(",") if args.engines else None)
    q = args.question.strip()
    if not q or len(q) > MAX_QUERY_LEN:
        raise ConfigError("the question must be 1–%d characters" % MAX_QUERY_LEN)
    active, _ = plan(engines, {}, None, True)
    if not active:
        print("error: nothing can be measured — export at least one API key", file=sys.stderr)
        return 3
    run = execute(brand, rivals, engines, [{"query_id": "ask", "query": q, "intent_tier": "", "target_url": ""}],
                  1, country, {}, len(active))
    if args.format == "json":
        print(json.dumps(run, ensure_ascii=False, indent=1))
    else:
        print(render_ask(run, args.format))
    return 0 if run["summary"]["overall"]["answered"] else 3


def _out(text, path):
    if path:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print("wrote %s" % path, file=sys.stderr)
    else:
        sys.stdout.write(text)


def cmd_report(args):
    cfg = _load(args)
    run = load_run(cfg, args.run or "latest")
    if args.format == "json":
        text = json.dumps(dict(run, summary=summary_of(run)), ensure_ascii=False, indent=1) + "\n"
    elif args.format == "csv":
        text = render_csv(run)
    else:
        text = render(run, args.format)
    _out(text, args.output)
    return 0


def cmd_diff(args):
    cfg = _load(args)
    a = load_run(cfg, args.a or "previous")
    b = load_run(cfg, args.b or "latest")
    d = diff_runs(a, b)
    _out(json.dumps(d, ensure_ascii=False, indent=1) + "\n" if args.format == "json" else render_diff(d, args.format),
         None)
    if args.fail_on_drop and drops(d):
        print("citation rate dropped beyond noise: %s" % ", ".join(drops(d)), file=sys.stderr)
        return 4
    return 0


def cmd_runs(args):
    cfg = _load(args)
    rows = []
    for rid in list_run_ids(cfg):
        try:
            r = load_run(cfg, rid)
        except ConfigError as e:
            rows.append([rid, "unreadable", "", "", str(e)[:40]])
            continue
        sm = summary_of(r)
        o, h = sm["overall"], sm["headline"]
        rows.append([rid, "%d/%d" % (o["answered"], o["planned"]), pct(h["cited_rate"]), ci_s(head_ci(h)),
                     ",".join(e["id"] for e in r["engines"] if e["status"] == "measured")])
    print(table(["run", "answered", "cited (headline)", "95% CI", "engines"], rows, "text") if rows else "no runs yet")
    return 0


# ── MCP (stdio, JSON-RPC 2.0, one message per line) ───────────────────────
MCP_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")


def _public_host(host):
    """An agent may be steered by a page it read: never let it point the scorer at this machine or the intranet."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError, OSError):
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return True


class MCPServer(object):
    def __init__(self, config_path, out=None):
        self.config_path = config_path
        self.out = out or sys.stdout
        self.lock = threading.Lock()
        self.geo_score = load_geo_score()

    def send(self, obj):
        with self.lock:
            self.out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            self.out.flush()

    def tools(self):
        eng = {"type": "array", "items": {"type": "string"},
               "description": "Engine ids from geo-score-watch.json; omit for all."}
        t = [
            {"name": "ask", "title": "Ask the AI engines one question (level 2)",
             "description": "Ask one question to each configured AI engine through its search-enabled API and report, "
                            "per engine, whether the brand is cited (and at which rank), whether it is mentioned, which "
                            "sources were cited and what the engine searched for. One paid API call per engine.",
             "inputSchema": {"type": "object", "properties": {
                 "question": {"type": "string", "maxLength": MAX_QUERY_LEN},
                 "engines": eng,
                 "brand": {"type": "string", "description": "Override the configured brand name."},
                 "domains": {"type": "array", "items": {"type": "string"},
                             "description": "Override the configured brand domains."}},
                 "required": ["question"]},
             "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}},
            {"name": "run", "title": "Run the tracked question set",
             "description": "Ask every question in queries.csv to every engine, save the run under .geo-score/watch/runs/ "
                            "and return the report. Spends the user's API credits; use dry_run first to see the plan. "
                            "max_calls and budget_usd can only tighten the caps in geo-score-watch.json, never loosen them.",
             "inputSchema": {"type": "object", "properties": {
                 "dry_run": {"type": "boolean"}, "engines": eng,
                 "limit": {"type": "integer", "minimum": 1, "description": "Only the first N questions."},
                 "max_calls": {"type": "integer", "minimum": 1},
                 "budget_usd": {"type": "number", "minimum": 0}}},
             "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}},
            {"name": "list_runs", "title": "List saved runs",
             "description": "Saved runs with their headline citation rate.",
             "inputSchema": {"type": "object", "properties": {}},
             "annotations": {"readOnlyHint": True, "openWorldHint": False}},
            {"name": "report", "title": "Report on a saved run",
             "description": "The report for a saved run: citation rate per engine with 95% intervals, share of voice, "
                            "most-cited third-party sources, questions a competitor wins, observed searches, cost.",
             "inputSchema": {"type": "object", "properties": {
                 "run": {"type": "string", "description": "A run id, or 'latest' (default)."},
                 "format": {"type": "string", "enum": ["md", "json"]}}},
             "annotations": {"readOnlyHint": True, "openWorldHint": False}},
            {"name": "diff", "title": "Compare two runs",
             "description": "Citation rate before and after, per engine, on the questions both runs answered: the "
                            "change in points with a 95% interval and an exact paired test (McNemar), Holm-adjusted "
                            "across engines. The verdict is 'change' only when the adjusted p < 0.05. Lists citations "
                            "lost and gained. Defaults to the latest two runs.",
             "inputSchema": {"type": "object", "properties": {
                 "from": {"type": "string"}, "to": {"type": "string"},
                 "format": {"type": "string", "enum": ["md", "json"]}}},
             "annotations": {"readOnlyHint": True, "openWorldHint": False}},
        ]
        if self.geo_score is not None:
            t.append({"name": "score_site", "title": "Score a site's AI readiness (geo-score)",
                      "description": "Score a URL 0-100 against the open AIV rubric (geo-score): can AI engines reach, "
                                     "parse, trust and cite it. Reads public pages only; no API key needed.",
                      "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}},
                                      "required": ["url"]},
                      "annotations": {"readOnlyHint": True, "openWorldHint": True}})
        return t

    def handle(self, msg):
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or not isinstance(msg.get("method"), str):
            if isinstance(msg, dict) and "method" not in msg and ("result" in msg or "error" in msg):
                return None   # a reply to a request we never send
            return {"jsonrpc": "2.0", "id": msg.get("id") if isinstance(msg, dict) else None,
                    "error": {"code": -32600, "message": "invalid request"}}
        method, mid, note = msg["method"], msg.get("id"), "id" not in msg
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        if note:
            return None
        if method == "initialize":
            want = params.get("protocolVersion")
            result = {"protocolVersion": want if want in MCP_VERSIONS else MCP_VERSIONS[0],
                      "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "geo-score", "title": "geo-score", "version": __version__},
                      "instructions": "Measures AI visibility at three levels. `score_site` is free and reproducible: can AI engines "
                                      "reach, parse, trust and cite the site (0-100). `ask` (level 2) and `run` (level 3) measure whether they "
                                      "actually cite a brand, through search-enabled APIs (not the consumer apps), and spend "
                                      "the user's API credits: show the plan (run with dry_run) before a full run. Report "
                                      "rates with their intervals; do not turn one answer into a trend."}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": self.tools()}
        elif method == "tools/call":
            result = self.call(params)
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "method not found: " + method}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def call(self, params):
        name, args = params.get("name"), params.get("arguments")
        args = args if isinstance(args, dict) else {}
        token = (params.get("_meta") or {}).get("progressToken") if isinstance(params.get("_meta"), dict) else None
        fn = getattr(self, "tool_" + name, None) if isinstance(name, str) and re.match(r"^[a-z_]+$", name) else None
        if fn is None or name not in [t["name"] for t in self.tools()]:
            return {"content": [{"type": "text", "text": "unknown tool: %s" % name}], "isError": True}
        try:
            text = fn(args, token)
            return {"content": [{"type": "text", "text": text}], "isError": False}
        except ConfigError as e:
            return {"content": [{"type": "text", "text": str(e)}], "isError": True}
        except Exception as e:
            return {"content": [{"type": "text", "text": "geo-score watch failed: %r" % e}], "isError": True}

    def _cfg(self):
        cfg = Config(self.config_path)
        if cfg.errors:
            raise ConfigError("%s:\n  %s" % (self.config_path, "\n  ".join(cfg.errors)))
        return cfg

    def _progress(self, token):
        if token is None or not isinstance(token, (str, int)) or isinstance(token, bool):
            return None

        def show(n, total, s):
            self.send({"jsonrpc": "2.0", "method": "notifications/progress",
                       "params": {"progressToken": token, "progress": n, "total": total,
                                  "message": "%s %s %s" % (s["engine"], s["query_id"], s["status"])}})
        return show

    @staticmethod
    def _engines_arg(args):
        v = args.get("engines")
        if v is None:
            return None
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise ConfigError("engines must be a list of engine ids")
        return v

    def tool_ask(self, args, token):
        q = args.get("question")
        if not isinstance(q, str) or not q.strip() or len(q) > MAX_QUERY_LEN:
            raise ConfigError("question must be 1-%d characters" % MAX_QUERY_LEN)
        brand, rivals, country = Entity({}), [], None
        engines = [dict(e, model=PROVIDERS[e["provider"]]["model"]) for e in DEFAULT_ENGINES]
        if os.path.isfile(self.config_path):
            cfg = self._cfg()
            brand, rivals, engines, country = cfg.brand, cfg.competitors, cfg.engines, cfg.country
        if args.get("brand") is not None or args.get("domains") is not None:
            brand = Entity({"name": args.get("brand") if isinstance(args.get("brand"), str) else "",
                            "domains": _strs(args.get("domains"))}, you=True)
        engines = select_engines(engines, self._engines_arg(args))
        active, _ = plan(engines, {}, None, True)
        if not active:
            raise ConfigError("no engine can run — the MCP server's environment has no API keys")
        run = execute(brand, rivals, engines,
                      [{"query_id": "ask", "query": q.strip(), "intent_tier": "", "target_url": ""}],
                      1, country, {}, len(active), progress=self._progress(token))
        return render_ask(run, "md")

    def tool_run(self, args, token):
        cfg = self._cfg()
        queries = cfg.load_queries()
        lim = args.get("limit")
        if isinstance(lim, int) and not isinstance(lim, bool) and lim > 0:
            queries = queries[:lim]
        engines = select_engines(cfg.engines, self._engines_arg(args))
        mc = args.get("max_calls")
        max_calls = min(mc, cfg.max_calls) if isinstance(mc, int) and not isinstance(mc, bool) and mc > 0 \
            else cfg.max_calls
        budget = cfg.budget_usd
        b = _num(args.get("budget_usd"))
        if b is not None:
            budget = b if budget is None else min(b, budget)
        active, status = plan(engines, cfg.prices, budget, False)
        planned = len(queries) * len(active) * cfg.runs
        lines = ["plan: %d questions × %d engines × %d = %d (cap %d%s)" % (
            len(queries), len(active), cfg.runs, planned, max_calls,
            "" if budget is None else ", budget " + money(budget))]
        lines += ["- %s: not measured (%s)" % (e["id"], status[e["id"]]) for e in engines
                  if status[e["id"]] != "measured"]
        if args.get("dry_run"):
            return "\n".join(lines) + "\n"
        if not active:
            raise ConfigError("\n".join(lines + ["no engine can run"]))
        if planned > max_calls:
            raise ConfigError("\n".join(lines + ["the plan exceeds the cap; pass limit or engines to ask fewer"]))
        run = execute(cfg.brand, cfg.competitors, engines, queries, cfg.runs, cfg.country, cfg.prices, max_calls,
                      budget, False, progress=self._progress(token))
        path = save_run(cfg, run)
        return render(run, "md") + "\nsaved `%s`\n" % os.path.relpath(path, cfg.dir)

    def tool_list_runs(self, args, token):
        cfg = self._cfg()
        rows = []
        for rid in list_run_ids(cfg):
            try:
                sm = summary_of(load_run(cfg, rid))
                o, h = sm["overall"], sm["headline"]
                rows.append([rid, "%d/%d" % (o["answered"], o["planned"]), pct(h["cited_rate"]), ci_s(head_ci(h))])
            except ConfigError:
                rows.append([rid, "unreadable", "", ""])
        return table(["run", "answered", "cited (headline)", "95% CI"], rows, "md") if rows else "no runs yet"

    def tool_report(self, args, token):
        run = load_run(self._cfg(), args.get("run") or "latest")
        if args.get("format") == "json":
            return json.dumps(summary_of(run), ensure_ascii=False, indent=1)
        return render(run, "md")

    def tool_diff(self, args, token):
        cfg = self._cfg()
        d = diff_runs(load_run(cfg, args.get("from") or "previous"), load_run(cfg, args.get("to") or "latest"))
        return json.dumps(d, ensure_ascii=False, indent=1) if args.get("format") == "json" else render_diff(d, "md")

    def tool_score_site(self, args, token):
        url = args.get("url")
        m = re.match(r"^(?:https?://)?([^/\s:?#@]+)(?::(\d{1,5}))?(?:[/?#]\S*)?$", url.strip()) if isinstance(url, str) else None
        host = host_of(m.group(1)) if m else ""
        if not host or "." not in host or not _public_host(host):
            raise ConfigError("url must be an http(s) URL on a public host (not localhost, private or reserved addresses)")
        url = url.strip() if "://" in url else "https://" + url.strip()
        gs = self.geo_score
        with contextlib.redirect_stdout(sys.stderr):
            res = gs.run(url, 8)
            j = gs.as_json(res)
        weak = sorted((c for c in j["checks"] if c.get("state") == "scored" and c.get("max")),
                      key=lambda c: c["points"] / float(c["max"]))[:6]
        L = ["# AIV readiness: %s" % j["target"], "",
             "**%s / 100 · %s**%s (%s, rubric %s)" % (
                 j["normalised"], j["band"], " · gate-capped" if j.get("gate_capped") else "",
                 j["tool"], j["rubric_version"]), "", "Weakest checks:"]
        L += ["- `%s` %s/%s — %s" % (c["id"], c["points"], c["max"], _cut(c.get("evidence", ""), 140)) for c in weak]
        L.append("\nReadiness says whether AI *can* cite the site; `run` measures whether it *does*.")
        return "\n".join(L) + "\n"

    def serve(self, inp=None):
        inp = inp or sys.stdin
        for line in inp:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                self.send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}})
                continue
            if isinstance(msg, list):
                out = [r for r in (self.handle(m) for m in msg) if r is not None]
                if out:
                    self.send(out)
                continue
            r = self.handle(msg)
            if r is not None:
                self.send(r)
        return 0


def cmd_mcp(args):
    return MCPServer(args.config).serve()


def main(argv=None, prog="geo_score.py watch"):
    ap = argparse.ArgumentParser(prog=prog, description="Level 3 of geo-score: track whether AI engines cite you, week "
                                 "over week, through the ChatGPT, Perplexity, Gemini and Claude APIs with your own keys. "
                                 "(Level 2 is `geo_score.py <url> --ask`; `watch ask` is the same without the score.)")
    ap.add_argument("--version", action="version", version="geo-score watch " + __version__)
    sub = ap.add_subparsers(dest="cmd")

    def with_config(p):
        p.add_argument("-c", "--config", default=os.environ.get("GEO_SCORE_WATCH_CONFIG") or CONFIG_NAME,
                       help="path to geo-score-watch.json (default: ./geo-score-watch.json or $GEO_SCORE_WATCH_CONFIG)")
        return p

    p = sub.add_parser("init", help="write geo-score-watch.json and queries.csv")
    p.add_argument("--dir", default=".")
    p.add_argument("--brand")
    p.add_argument("--domain", action="append", help="repeatable")
    p.add_argument("--competitor", action="append", metavar="NAME=DOMAIN", help="repeatable")
    p.add_argument("--country", help="two-letter code, e.g. US")
    p.add_argument("--force", action="store_true")
    with_config(sub.add_parser("check", help="validate the config, the questions and the keys"))
    p = with_config(sub.add_parser("run", help="ask every question to every engine and save the run"))
    p.add_argument("--engines", help="comma-separated engine ids")
    p.add_argument("--runs", type=int, help="asks per question per engine (default from config)")
    p.add_argument("--limit", type=int, help="only the first N questions")
    p.add_argument("--max-calls", type=int, help="hard cap on questions asked")
    p.add_argument("--budget-usd", type=float, help="spend cap, checked before every call (can be exceeded by at most "
                   "one call per engine); needs prices or provider-reported cost")
    p.add_argument("--allow-unpriced", action="store_true", help="with a budget, also run engines with no prices")
    p.add_argument("--dry-run", action="store_true", help="print the plan and exit")
    p.add_argument("--format", choices=["text", "md"], default="text")
    p.add_argument("-q", "--quiet", action="store_true")
    p = with_config(sub.add_parser("ask", help="one question, every engine, not saved"))
    p.add_argument("question")
    p.add_argument("--engines")
    p.add_argument("--brand")
    p.add_argument("--domain", action="append")
    p.add_argument("--format", choices=["text", "md", "json"], default="text")
    p = with_config(sub.add_parser("report", help="report on a saved run"))
    p.add_argument("run", nargs="?", help="run id (default: latest)")
    p.add_argument("--format", choices=["text", "md", "csv", "json"], default="text")
    p.add_argument("-o", "--output")
    p = with_config(sub.add_parser("diff", help="compare two runs (default: the latest two)"))
    p.add_argument("a", nargs="?")
    p.add_argument("b", nargs="?")
    p.add_argument("--format", choices=["text", "md", "json"], default="text")
    p.add_argument("--fail-on-drop", action="store_true", help="exit 4 when a verdict is a change for the worse "
                   "(overall or any engine), for CI")
    with_config(sub.add_parser("runs", help="list saved runs"))
    with_config(sub.add_parser("mcp", help="serve score and watch over MCP (stdio); run it as `geo_score.py mcp`"))

    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 1
    try:
        return {"init": cmd_init, "check": cmd_check, "run": cmd_run, "ask": cmd_ask, "report": cmd_report,
                "diff": cmd_diff, "runs": cmd_runs, "mcp": cmd_mcp}[args.cmd](args)
    except ConfigError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
