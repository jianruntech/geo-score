#!/usr/bin/env python3
"""
geo-score — score a site 0-100 on whether AI answer engines can find, parse,
trust and cite it. Implements the open AIV rubric v1.1.

    python3 geo_score.py https://example.com                  # level 1: readiness, free
    python3 geo_score.py example.com --ask "best X for Y"     # level 2: + a live citation check (your API keys)
    python3 geo_score.py watch run                            # level 3: track a question set weekly
    python3 geo_score.py mcp                                  # all three levels over MCP (stdio)

Levels 2 and 3 live in geo_watch.py next to this file.

No dependencies. Python 3.8+. Reads only public URLs.
Rubric: https://github.com/jianruntech/geo-score
"""
import argparse, concurrent.futures as cf, datetime, fnmatch, html, io, json, os, re, sys, textwrap, threading, time, zlib
import http.client, ipaddress, socket, urllib.error, urllib.parse, urllib.request
try:
    import ssl
except ImportError:         # a Python built without OpenSSL: https fails, and says so
    ssl = None

__version__ = "1.8.3"
RUBRIC = "v1.1"
UA_BROWSER = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
# The 10 retrieval crawlers of reference/ai-crawlers.md, the agents g.robots scores and g.reachable probes,
# each with the user-agent string its vendor documents. Anthropic documents only the product tokens of
# Claude-SearchBot and Claude-User; their strings follow the form of ClaudeBot's.
RETRIEVAL_UAS = [
    ("OAI-SearchBot", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/131.0.0.0 Safari/537.36; compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot"),
    ("ChatGPT-User", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"),
    ("Claude-SearchBot", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-SearchBot/1.0; "
                         "+Claude-SearchBot@anthropic.com)"),
    ("Claude-User", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-User/1.0; "
                    "+Claude-User@anthropic.com)"),
    ("PerplexityBot", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; "
                      "+https://perplexity.ai/perplexitybot)"),
    ("Perplexity-User", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Perplexity-User/1.0; "
                        "+https://perplexity.ai/perplexity-user)"),
    ("Googlebot", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
    ("Bingbot", "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"),
    ("Applebot", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                 "Version/17.4 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)"),
    ("Amazonbot", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Amazonbot/0.1) "
                  "Chrome/119.0.6045.214 Safari/537.36"),
]
# Training crawlers and opt-out tokens. They are never scored: a robots.txt group that disallows one by name is
# reported in g.robots' evidence, and nothing else. Not scored is not free: Google-Extended also governs grounding in
# Gemini Apps and Vertex AI, Meta documents Meta-ExternalAgent for indexing as well as training, and for the others
# the cost is unknown; no check measures any of it (reference/ai-crawlers.md).
NOT_SCORED_TOKENS = ["GPTBot", "ClaudeBot", "CCBot", "Google-Extended", "Applebot-Extended", "anthropic-ai",
                     "cohere-ai", "Bytespider", "Meta-ExternalAgent"]
CN_UAS = [("Baiduspider", "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)"),
          ("Sogou", "Sogou web spider/4.0"),
          ("PetalBot", "Mozilla/5.0 (compatible; PetalBot;+https://webmaster.petalsearch.com/site/petalbot)")]

# A heading matches question intent if a person would phrase their question that way — a question,
# a task, an explanation or a comparison — not merely if it carries a question mark. The English and the
# Chinese forms match the same kinds of heading (test_geo_score.py holds them to it): "Create your first app"
# and "创建你的第一个应用", "How workflows work" and "工作流的工作原理", "Plans compared" and "版本对比".
# Chinese has no word boundary, so a task verb that opens a noun is excluded by what follows it: 管理团队 is a
# team, 处理器 a processor, 集成电路 a chip, 使用条款 the terms of use. So are two product specs: 对比度 is a contrast
# ratio, 原理图 a schematic.
QP_INTENT = re.compile(r"\b(how|what|why|when|where|which|who)\b|[?？]"
                    r"|^(get|getting|set|setting|add|adding|build|building|create|creating|use|using|"
                    r"install|installing|deploy|deploying|configure|connect|accept|send|manage|migrate|"
                    r"write|writing|run|running|test|testing|choose|handle|customi[sz]e|compare|comparing)\b"
                    r"|\b(vs|versus|compared)\b"
                    r"|怎么|如何|什么|为什么|是否|多少|入门|教程|指南"
                    r"|^(创建|新建|设置|配置|安装|部署|使用|添加|连接|接入|集成|管理|迁移|选择|处理|自定义|编写|运行|"
                    r"测试|构建|搭建|发送|接收|开始|导入|导出|获取|开通|启用)(?!器|员|层|者|团队|电路|条款|协议)"
                    r"|原理(?!图)|运作方式|对比(?!度)|区别|哪个好", re.I)
# Short nav-like labels are not headings. \w matches CJK in Python, so the short-label branch must not
# swallow real CJK headings: "怎么定价" (4 chars) is a question heading, "价格" is a nav label.
NAV_LABEL = re.compile(r"^\s*(\w+\s*[|｜·]\s*\w+|[A-Za-z0-9_]{1,12}|[\u4e00-\u9fff]{1,3})\s*$")

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
def text_file(r):
    """A file answer, not a site's catch-all page. Single-page apps answer every path with 200 and their
    HTML shell, which read as an llms.txt, an llms-full.txt and an ai.txt that do not exist."""
    head = r.body[:2048].lower()
    if re.match(rb"\s*(<!doctype\s+html|<html|<head|<body)", head):
        return False
    # an error or firewall page served as HTML without the usual opening still is not a text file
    if "html" in r.headers.get("content-type", "").lower() and re.search(rb"<(html|head|body|div|script|meta|title)\b", head):
        return False
    return r.ok and bool(r.body.strip())


def is_sitemap(r):
    """A sitemap answer is XML with a <urlset> or <sitemapindex>. A single-page app's catch-all answers
    /sitemap.xml with 200 and its HTML shell, which is not a sitemap."""
    return r.ok and bool(re.search(r"<(urlset|sitemapindex)\b", r.text[:200000], re.I))


class Resp:
    __slots__ = ("url", "status", "body", "headers", "err", "elapsed", "_kind")
    def __init__(self, url, status=0, body=b"", headers=None, err=None, elapsed=0.0, kind=None):
        self.url, self.status, self.body = url, status, body
        self.headers, self.err, self.elapsed, self._kind = headers or {}, err, elapsed, kind
    @property
    def kind(self):
        """Why this answer is no page to score, in schema/error.v1.json's words: with no HTTP answer dns,
        refused, tls, timeout, dropped, no_response (or not_public under the address guard), or slow and
        deadline when fetch() stopped it for time; http_<code> for an HTTP error; no_content for an empty 2xx.
        None for a page with content."""
        if self.status == 0:
            return self._kind or fault_kind(self.err)
        if not self.ok:
            return "http_%d" % self.status
        return None if self.body else "no_content"
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

# Characters that are never legitimate in evidence and are the tools of choice for hiding or reordering
# text an agent reads: C0/C1 controls (CR included, which would start a new CI workflow command), soft
# hyphen, Arabic letter mark, Mongolian vowel separator, zero-width characters, bidi embeddings and
# isolates, line and paragraph separators, interlinear annotation marks, the two non-characters XML
# cannot carry, Unicode tag characters (invisible to people, read by language models), and lone surrogates,
# which a JSON escape can produce and no UTF-8 output can carry.
_UNSAFE = re.compile("[\x00-\x08\x0b-\x1f\x7f-\x9f\u00ad\u061c\u180e\u200b-\u200f\u2028-\u202e"
                     "\u2060-\u2064\u2066-\u2069\ud800-\udfff\ufeff\ufff9-\ufffb\ufffe\uffff\U000e0000-\U000e007f]")

# ── address guard ──
# The CLI fetches whatever its user names, private hosts included. Under the MCP server an agent chooses
# the URL, and the audited site chooses every URL after it (redirects, sameAs, logo, sitemap), so there
# every connection must go to a public address. geo_watch's MCP server switches this on.
ADDRESS_GUARD = False


def public_ip(addr):
    """Globally routable unicast only: this refuses loopback, private, link-local, CGNAT (100.64/10,
    where cloud metadata services such as 100.100.100.200 live), reserved and multicast addresses."""
    ip = ipaddress.ip_address(str(addr).split("%")[0])
    if ip.version == 6:
        if ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        # NAT64 and 6to4 prefixes carry an IPv4 address inside; on a DNS64 network they reach it
        elif any(ip in n for n in _EMBEDS_V4):
            return False
    return ip.is_global and not ip.is_multicast


_EMBEDS_V4 = [ipaddress.ip_network(n) for n in ("64:ff9b::/96", "64:ff9b:1::/48", "2002::/16")]


def resolve_public(host, port):
    """Resolve once; every answer must be public. Returns the addresses to connect to, in order."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as e:
        raise OSError("cannot resolve %s: %s" % (host, e)) from None
    if not infos or not all(public_ip(i[4][0]) for i in infos):
        raise OSError("refused: %s does not resolve to a public address" % host)
    return [i[4][:2] for i in infos]


def _guarded(conn_class, proxied=False):
    """An http.client connection factory whose TCP connect is checked. A direct connection goes to an
    address that passed the check, so a name cannot resolve to something else a moment later. Through
    a proxy the proxy resolves the name: the target was checked before the request (check_url, and on
    every redirect hop), and the proxy itself is the user's own, so its address is not refused."""
    def make(host, **kw):
        until = getattr(_LIMIT, "until", None)
        if until is not None and isinstance(kw.get("timeout"), (int, float)):
            # the connect and the TLS handshake wait no longer than the fetch has left
            left = until - time.monotonic()
            if left <= 0:
                raise OutOfTime("out of time")
            kw["timeout"] = min(kw["timeout"], left)
        c = conn_class(host, **kw)
        c.response_class = _TimedResponse
        orig = c._create_connection

        def create(address, *a, **k):
            if not ADDRESS_GUARD or proxied:
                return orig(address, *a, **k)
            if getattr(c, "_tunnel_host", None):            # HTTPS through a proxy: CONNECT to the target
                resolve_public(c._tunnel_host, c._tunnel_port or 443)
                return orig(address, *a, **k)
            err = None
            for addr in resolve_public(*address):           # every answer was checked; try them in order
                try:
                    return orig(addr, *a, **k)
                except OSError as e:
                    err = e
            raise err
        c._create_connection = create
        return c
    return make


class _GuardedHTTP(urllib.request.HTTPHandler):
    def http_open(self, req):
        # plain http through a proxy sends the absolute URL to the proxy, with no CONNECT tunnel
        return self.do_open(_guarded(http.client.HTTPConnection, proxied=req.has_proxy()), req)


class _GuardedHTTPS(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_guarded(http.client.HTTPSConnection), req, context=self._context)


def check_url(url):
    """Under the guard, a URL whose host does not resolve to a public address is refused before any request."""
    if not ADDRESS_GUARD:
        return
    u = urllib.parse.urlsplit(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise OSError("refused: %s is not an http(s) URL" % url[:80])
    resolve_public(u.hostname, u.port or (443 if u.scheme == "https" else 80))


class _Redirects(urllib.request.HTTPRedirectHandler):
    """Follow 307 and 308 as well as 301/302.

    urllib below Python 3.11 does not treat 307/308 as redirects — it raises HTTPError
    instead. A site whose www-to-apex hop is a 308 then reads as unreachable, which
    dropped openai.com, runwayml.com, neon.tech and others out of the benchmark
    entirely. Worse, it made the score depend on which Python ran the tool: 3.11+
    followed the hop and scored the site, 3.8-3.10 reported it as unfetchable.
    Real retrieval crawlers follow these hops, so the score has to as well.
    """
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            check_url(newurl)           # every hop, not only the first URL
        except OSError as e:
            raise urllib.error.URLError(str(e)) from None
        # The base redirect_request in 3.9 rejects 308 outright, so aliasing
        # http_error_308 is not enough on its own — this was the incomplete first fix.
        if code in (307, 308) and req.get_method() in ("GET", "HEAD"):
            return urllib.request.Request(
                newurl, headers=req.headers, method=req.get_method(),
                origin_req_host=req.origin_req_host, unverifiable=True)
        return urllib.request.HTTPRedirectHandler.redirect_request(
            self, req, fp, code, msg, headers, newurl)

    http_error_307 = urllib.request.HTTPRedirectHandler.http_error_301
    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_301


_OPENER = urllib.request.build_opener(_Redirects, _GuardedHTTP, _GuardedHTTPS)

MAX_BODY = 4_000_000       # bytes read off the wire
MAX_INFLATED = 16_000_000  # bytes after gunzip


def gunzip(raw, limit=MAX_INFLATED):
    """Inflate a gzip body, but never past `limit` bytes.

    The 4 MB read cap applies to the compressed stream. gzip.decompress has no
    output limit, so a few MB of crafted gzip inflates to gigabytes and takes the
    process down — on a GitHub Action runner that is an out-of-memory kill, not a
    score. Truncated output is still parsed; a real page never gets near 16 MB."""
    try:
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        return d.decompress(raw, limit)
    except zlib.error:
        return raw


# Seconds a request may wait for the server, per read. main() sets it from --timeout; run(timeout=…) overrides it.
DEFAULT_TIMEOUT = 15
TIMEOUT = DEFAULT_TIMEOUT
MAX_TIMEOUT = 300
# The time a timeout cannot bound. TIMEOUT limits each read, not their sum: a server that sent one byte every few
# seconds (a tarpit, which some sites keep for crawlers) held a fetch, and with it a CI job or an MCP worker, for
# hours. One request, redirects included, takes at most max(FETCH_BUDGET, 2 × its timeout) seconds; past that it
# is an answer of kind "slow", and it is not retried. One run takes at most RUN_DEADLINE seconds: no request starts
# after it and one in flight stops there, as an answer of kind "deadline", so the checks that needed it are not
# observed. Neither is a flag; the tests set them lower.
FETCH_BUDGET = 30
RUN_DEADLINE = 300
READ_CHUNK = 64 * 1024
# Resolve the host before a run, so a mistyped name fails at once. main() switches this on for the CLI. It is a
# module setting, not a run() parameter, so run() keeps the signature callers and test stubs rely on; the MCP
# server resolves the host itself before it calls run().
PREFLIGHT = False


class OutOfTime(socket.timeout):
    """A fetch whose time is up. fetch() answers it as kind "slow" or "deadline", never as a plain timeout."""


# The fetch this thread is making: when its time is up (a time.monotonic() value) and its wait per read. Set by
# fetch() around the request, so the connection it opens and every read of the answer end by then.
_LIMIT = threading.local()


class _TimedReader(io.RawIOBase):
    """A response's socket reads, each cut to the time its fetch has left. The status line and the headers are
    read through it as well as the body, so a server that drips its headers a byte at a time is stopped too."""
    def __init__(self, raw, sock, until, per_read):
        io.RawIOBase.__init__(self)
        self.raw, self.sock, self.until, self.per_read = raw, sock, until, per_read

    def readable(self):
        return True

    def fileno(self):
        return self.raw.fileno()

    def readinto(self, b):
        left = self.until - time.monotonic()
        if left <= 0:
            raise OutOfTime("out of time")
        self.sock.settimeout(min(self.per_read, left))
        return self.raw.readinto(b)

    def close(self):
        if not self.closed:
            self.raw.close()        # the socket's own reader: closing it lets the connection close
        io.RawIOBase.close(self)


class _TimedResponse(http.client.HTTPResponse):
    """http.client's response, reading through _TimedReader while a fetch() has a time limit set."""
    def __init__(self, sock, *a, **kw):
        http.client.HTTPResponse.__init__(self, sock, *a, **kw)
        until = getattr(_LIMIT, "until", None)
        if until is not None:
            self.fp = io.BufferedReader(_TimedReader(self.fp.detach(), sock, until, _LIMIT.timeout))


def read_body(r, limit, until):
    """Up to `limit` bytes of a response's body, READ_CHUNK at a time: raises OutOfTime once `until` has passed.
    read1 returns what one read brings, so a body sent a byte at a time is checked against the clock each time."""
    read = getattr(r, "read1", None) or r.read
    parts, got = [], 0
    while got < limit:
        if time.monotonic() >= until:
            raise OutOfTime("out of time")
        b = read(min(READ_CHUNK, limit - got))
        if not b:
            break
        parts.append(b)
        got += len(b)
    return b"".join(parts)


def header_map(msg):
    """A response's headers by lower-case name. A field sent on several lines keeps its last line, except Link, whose
    lines are joined with ", ", as RFC 9110 section 5.3 allows for a list field: a page's hreflang annotations may come
    on more than one."""
    h = {}
    for k, v in (msg or {}).items():
        k = k.lower()
        h[k] = h[k] + ", " + v if k == "link" and k in h else v
    return h


def fetch(url, ua=UA_BROWSER, timeout=None, method="GET", *, deadline=None):
    """One request, never retried. It waits `timeout` seconds per read (default TIMEOUT) and
    max(FETCH_BUDGET, 2 × timeout) in all. `deadline`, a time.monotonic() value, is the run's: it stops the
    request sooner, and a request asked for after it is not sent."""
    timeout = timeout or TIMEOUT
    t0, now = time.time(), time.monotonic()
    budget = max(FETCH_BUDGET, 2 * timeout)
    until, kind, why = now + budget, "slow", "exceeded %g s total" % budget
    if deadline is not None and deadline <= until:
        until, kind, why = deadline, "deadline", "run deadline reached"
    if now >= until:
        return Resp(str(url), 0, b"", err=why, kind=kind)
    _LIMIT.until, _LIMIT.timeout = until, timeout
    try:
        # inside the try: a URL the site wrote badly (relative, schemeless, empty) is a failed fetch,
        # never an exception that ends the run
        url = idna(str(url))
        req = urllib.request.Request(url, method=method, headers={
            "User-Agent": ua, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Encoding": "gzip", "Accept-Language": "en,zh;q=0.8"})
        check_url(url)
        with _OPENER.open(req, timeout=timeout) as r:
            raw = read_body(r, MAX_BODY, until)
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gunzip(raw)
            return Resp(r.geturl(), r.status, raw, header_map(r.headers), elapsed=time.time() - t0)
    except urllib.error.HTTPError as e:
        try: raw = read_body(e, 400_000, until)
        except Exception: raw = b""
        h = header_map(e.headers)
        if h.get("content-encoding") == "gzip":
            # an error page is read too, for a bot challenge (Cloudflare's comes back 403, gzipped)
            raw = gunzip(raw)
        return Resp(url, e.code, raw, h, elapsed=time.time() - t0)
    except Exception as e:
        k = fault_kind(e)
        if k == "timeout" and time.monotonic() >= until:
            # the last wait was cut to what was left of the time: the answer ran out of it, not one read
            return Resp(url, 0, b"", err=why, elapsed=time.time() - t0, kind=kind)
        # a server's status line lands in this message: keep it to one clean line
        return Resp(url, 0, b"", err=" ".join(_UNSAFE.sub("", str(e)).split())[:120], elapsed=time.time() - t0,
                    kind=k)
    finally:
        _LIMIT.until = None

# Retries. A timeout, a reset, 408, 429 or a 5xx can change on the next try; any other answer is definite.
# The wait grows by RETRY_BACKOFF seconds a try (the tests set it to 0), or follows a Retry-After of up to
# RETRY_AFTER_MAX seconds.
RETRY_BACKOFF, RETRY_AFTER_MAX = 1.5, 5
STEADY_TRIES = 3
# a crawler probe gets one retry: enough for a dropped connection or a 429 from the burst of probes, and a
# server that drops every bot request costs one extra round, not two
PROBE_TRIES = 2

def transient(status):
    return status in (0, 408, 429) or 500 <= status < 600

# faults the next try meets again at once: a name that does not resolve, a closed port, a failed handshake
DEFINITE = {"dns", "refused", "not_public", "tls"}
# answers that ran out of time: a retry would take as long again, or be refused by the run's deadline
OUT_OF_TIME = {"slow", "deadline"}

def retry_wait(r, i):
    if r.status == 0 and r.kind == "timeout":
        return 0            # a timeout has already waited
    ra = r.headers.get("retry-after", "").strip()
    if ra.isdigit():
        return min(int(ra), RETRY_AFTER_MAX)
    return RETRY_BACKOFF * (i + 1)

class FetchMemo:
    """One run's answers from fetch_steady, keyed by (url, user agent, method), so the homepage, robots.txt
    and the sitemap are fetched once per run. discover() used to read robots.txt with retries and run()
    read it again without: one dropped second request turned a blocking robots.txt into "No robots.txt".
    Made per run, never per module: the MCP server scores several sites at once in one process."""
    def __init__(self):
        self.lock, self.got = threading.Lock(), {}

def fetch_steady(url, tries=STEADY_TRIES, *, memo=None, **kw):
    """fetch() for the requests that decide which pages get sampled — the homepage,
    robots.txt, the sitemap, section indexes, and the sampled pages themselves.

    One dropped request there used to swap the whole sample: a sitemap that timed out
    once sent discovery to homepage links instead, a different eight pages were scored,
    and a site measured 71, 40 and 71 on three consecutive runs from one machine (the
    middle sample fell under the g.ssr gate). Timeouts, resets, 408, 429 and 5xx are
    retried with a short backoff; a definite answer, a DNS, refused or TLS fault, or an
    answer that ran out of time, is returned at once. With a memo,
    an answer already fetched in this run is returned without a request."""
    key = (url, kw.get("ua", UA_BROWSER), kw.get("method", "GET"))
    if memo is not None:
        with memo.lock:
            if key in memo.got:
                return memo.got[key]
    for i in range(tries):
        r = fetch(url, **kw)
        if not transient(r.status) or r.kind in DEFINITE or r.kind in OUT_OF_TIME:
            break
        if i < tries - 1:
            time.sleep(retry_wait(r, i))
    if memo is not None:
        with memo.lock:
            r = memo.got.setdefault(key, r)
    return r

def fault_kind(e):
    """The kind of a fault that left no HTTP answer, from the exception fetch() caught, or from its
    one-line text when only that is left."""
    if isinstance(e, BaseException):
        why = getattr(e, "reason", None)            # URLError wraps the cause
        x = why if isinstance(why, BaseException) else e
        if isinstance(x, (socket.timeout, TimeoutError)):
            return "timeout"
        if isinstance(x, socket.gaierror):
            return "dns"
        if isinstance(x, ConnectionRefusedError):
            return "refused"
        if ssl is not None and isinstance(x, (ssl.SSLEOFError, ssl.SSLZeroReturnError)):
            return "dropped"        # the connection was cut in the middle of the handshake: a drop, retried
        if ssl is not None and isinstance(x, ssl.SSLError):      # certificate failures included
            return "tls" if "UNEXPECTED_EOF" not in str(x) else "dropped"
        if isinstance(x, (ConnectionError, http.client.IncompleteRead)):
            return "dropped"
        e = why if isinstance(why, str) else str(x)
    e = (e or "").lower()
    for keys, kind in ((("timed out", "timeout"), "timeout"), (("refused:",), "not_public"),
                       (("cannot resolve", "getaddrinfo", "nodename", "name or service", "name resolution"), "dns"),
                       (("refused",), "refused"), (("unexpected_eof", "eof occurred in violation"), "dropped"),
                       (("ssl", "certificate", "tls"), "tls"),
                       (("reset", "closed connection", "remote end closed", "broken pipe", "eof"), "dropped")):
        if any(k in e for k in keys):
            return kind
    return "no_response"

class ScoreError(RuntimeError):
    """A site that cannot be scored. `kind` says why in schema/error.v1.json's words; the CLI prints the
    message, and under --json the JSON error as well."""
    def __init__(self, message, kind="error", target=None):
        RuntimeError.__init__(self, message)
        self.kind, self.target = kind, target

# What each kind of failed fetch means, in one plain sentence, and the section of guide/troubleshooting.md that
# explains it (test_geo_score.py checks that every anchor is a heading there)
FAULTS = {
    "dns": ("cannot resolve {host}: check the spelling, or your DNS/proxy settings (HTTPS_PROXY)",
            "dns-the-name-does-not-resolve"),
    "refused": ("{host} refused the connection: nothing accepts connections on that port, or a firewall turned "
                "the request away", "refused-the-connection-was-refused"),
    "not_public": ("the address guard refused {host}: it does not resolve to a public address",
                   "could-not-fetch--and-exit-code-2"),
    "tls": ("the TLS handshake with {host} failed: its certificate is invalid, expired or for another name, or "
            "something between here and the site interferes with HTTPS", "tls-the-https-handshake-failed"),
    "timeout": ("{host} did not answer within {timeout:g} s on any try (--timeout sets the wait)",
                "timeout-no-answer-in-time"),
    "slow": ("{host} kept its answer coming too slowly to finish within {budget:g} s, the most one request may take",
             "slow-the-answer-never-finished"),
    "deadline": ("the run reached its {deadline:g} s limit before a page to score came back",
                 "deadline-the-run-ran-out-of-time"),
    "dropped": ("{host} closed the connection without answering, on every try", "dropped-no_response-no-answer-came-back"),
    "no_response": ("{host} gave no usable HTTP answer", "dropped-no_response-no-answer-came-back"),
    "http": ("every page asked for answered with an HTTP error ({codes})", "http_nnn-the-pages-answered-with-an-http-error"),
    "no_content": ("{host} answered with an empty page", "no_content-the-page-came-back-empty"),
}

def troubleshooting(anchor):
    """A section of the troubleshooting guide, pinned to this release's tag."""
    return "https://github.com/jianruntech/geo-score/blob/v%s/guide/troubleshooting.md#%s" % (__version__, anchor)

def proxy_for(url):
    """The proxy a request to `url` goes through, as host:port (never its credentials), or None."""
    u = urllib.parse.urlsplit(url)
    p = urllib.request.getproxies().get(u.scheme)
    if not p or urllib.request.proxy_bypass(u.hostname or ""):
        return None
    pu = urllib.parse.urlsplit(p if "://" in p else "http://" + p)
    return pu.hostname + (":%d" % pu.port if pu.port else "") if pu.hostname else None

def fetch_failure(base, rs, timeout=None):
    """The error for a site that gave no page to score: the first answer's kind, in one plain sentence that names
    it, with the troubleshooting section for it."""
    # pages the run's deadline stopped are why there is nothing to score, whatever the first page answered
    kind = "deadline" if any(r.kind == "deadline" for r in rs) else rs[0].kind or "no_content"
    codes = sorted({r.status for r in rs if r.status and not r.ok})
    host = urllib.parse.urlsplit(base).hostname or base
    text, anchor = FAULTS["http" if kind.startswith("http_") else kind]
    t = timeout or TIMEOUT
    text = text.format(host=host, timeout=t, codes=", ".join("HTTP %d" % c for c in codes),
                       budget=max(FETCH_BUDGET, 2 * t), deadline=RUN_DEADLINE)
    if kind == "tls" and ssl is not None and not getattr(ssl, "HAS_TLSv1_3", True):
        # macOS's /usr/bin/python3 is built on LibreSSL 2.8, which cannot speak TLS 1.3; many sites require it
        text += ("; this Python's TLS library (%s) cannot speak TLS 1.3, which many sites require, so run the CLI "
                 "with a newer Python" % ssl.OPENSSL_VERSION)
    via = proxy_for(base) if rs[0].status == 0 and kind not in ("not_public", "deadline") else None
    return ScoreError("could not fetch %s (%s): %s%s; see %s" % (
        base, kind, text, "; the request went through the proxy at %s, which may be where it failed" % via if via else "",
        troubleshooting(anchor)), kind, base)

# Bot-challenge pages: what a bot-protection service serves, in place of the page, to a client it has not cleared.
# A static fetch cannot pass one, so a challenge is no page to score: read as content, it scored g.ssr 0 and every
# page check at the bottom, and published a site's bot protection as "content needs JavaScript". Each vendor's
# markers are all ones its challenge page carries and its ordinary pages do not: an ordinary page can carry the
# vendor's sensor script (Cloudflare's /cdn-cgi/challenge-platform/…/jsd/, PerimeterX's _pxAppId, Imperva's
# _Incapsula_Resource script), and that is no challenge. A page with substantive body text is never one.
BOT_CHALLENGE = "bot challenge served to a browser user-agent"
# Akamai's reference number: "Reference #18.5a3c2e17.1790692071.9f00b2c", or the bare number on a newer page
_AKAMAI_REF = r"Reference\s*#|errors\.edgesuite\.net|\b\d{1,3}\.[0-9a-f]{6,8}\.\d{10}\.[0-9a-f]{6,10}\b"
CHALLENGES = [
    # (vendor, the statuses its challenge answers with or None for any, patterns that must all match)
    ("AWS WAF", (202, 405), (re.compile(r"awswaf|reportChallengeError", re.I),)),
    ("Akamai", None, (re.compile(r"Access Denied"), re.compile(_AKAMAI_REF))),
    ("Cloudflare", None, (re.compile(r"cf[-_]chl|/cdn-cgi/challenge-platform/[^\s\"'<>]*orchestrate"
                                     r"|<title>\s*Just a moment", re.I),)),
    ("Fastly", None, (re.compile(r"/_fs-ch-|<title>\s*Client Challenge", re.I),)),
    ("PerimeterX", None, (re.compile(r"px-captcha|_pxJsClientSrc"),)),
    ("DataDome", None, (re.compile(r"captcha-delivery\.com", re.I),)),
    ("Imperva", None, (re.compile(r"_Incapsula_Resource"), re.compile(r"incident_id|Incapsula incident", re.I))),
]
# the most of a page the markers are looked for in: every challenge page is small, and its markers sit near the top
CHALLENGE_SCAN = 64 * 1024

def challenge_kind(resp):
    """The vendor whose bot-challenge page this answer is ("AWS WAF", "Cloudflare", …), or None for a page, an
    error page or an empty answer. Any status: a 403 challenge is a bot challenge, not merely an HTTP error."""
    if not resp.body:
        return None
    # Cloudflare says so in a header when it answered with a challenge
    vendor = "Cloudflare" if resp.headers.get("cf-mitigated", "").strip().lower() == "challenge" else None
    head = None
    for name, statuses, marks in CHALLENGES:
        if vendor:
            break
        if statuses and resp.status not in statuses:
            continue
        if head is None:
            # Akamai writes its reference number as HTML entities ("Reference&#32;&#35;18&#46;…")
            head = html.unescape(resp.body[:CHALLENGE_SCAN].decode("utf-8", "replace"))
        if all(m.search(head) for m in marks):
            vendor = name
    # the same measure as g.ssr: a page a reader could use is scored, whatever scripts it also loads
    return vendor if vendor and wc(visible_text(main_html(resp.text))) < 120 else None

# getaddrinfo's answers for a name that does not exist (EAI_NODATA is missing on some platforms)
NO_SUCH_NAME = {getattr(socket, n) for n in ("EAI_NONAME", "EAI_NODATA") if hasattr(socket, n)}

def preflight_host(url):
    """Resolve the host once before anything is fetched, so a mistyped name fails at once, in plain words.
    Skipped when a proxy will carry the request: behind a proxy local DNS can fail while the proxy resolves
    the name. A temporary resolver failure (EAI_AGAIN) lets the run go ahead."""
    u = urllib.parse.urlsplit(idna(url))
    if not u.hostname or proxy_for(url):
        return
    try:
        socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        if e.errno in NO_SUCH_NAME:
            raise ScoreError("cannot resolve %s: check the spelling, or your DNS/proxy settings (HTTPS_PROXY); see %s"
                             % (u.hostname, troubleshooting(FAULTS["dns"][1])), "dns", url) from None
    except (UnicodeError, ValueError):
        pass

def fault_name(err):
    """A request that got no answer, in the tool's words: the raw error can carry a server's status line."""
    e = (err or "").lower()
    for keys, name in ((("timed out", "timeout"), "timed out"), (("refused",), "connection refused"),
                       (("reset", "closed connection", "remote end closed", "broken pipe"), "connection dropped"),
                       (("ssl", "certificate", "tls"), "TLS failure"),
                       (("resolve", "getaddrinfo", "nodename", "name or service"), "DNS failure")):
        if any(k in e for k in keys):
            return name
    return "no response"

def join_link(base, ref):
    """urljoin for a link the site wrote, which never raises: a malformed one ("http://[::1") is no link,
    where it used to end the run."""
    try:
        return urllib.parse.urljoin(base, ref)
    except ValueError:
        return ""

def pmap(fn, items, workers=8):
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))

# ── html helpers ───────────────────────────────────────────────────────────
# Every scanner here reads a page in one pass. The regexes they replace, such as
# <(script|…)\b.*?</\1> and <p\b[^>]*>(.*?)</p>, retried each unclosed opening to the end of the page, so
# 80 KB of "<script>x " took 1.8 s and the 4 MB a fetch may return would have taken hours: a hostile page
# could hold a CI job or an MCP worker until it was killed. An opening is found with a compiled search from
# the current position, and its close once, with str.find on a lower-cased copy.
_ASCII_LOWER = {c: c + 32 for c in range(ord("A"), ord("Z") + 1)}


def _lower(h):
    """h lower-cased, index for index. str.lower() lengthens a few characters (U+0130 becomes two), which
    would shift every close found in the copy; then only ASCII letters are lowered, which is all a tag name
    needs."""
    low = h.lower()
    return low if len(low) == len(h) else h.translate(_ASCII_LOWER)


def inner_html(h, opening, close, low=None):
    """The content of each element that `opening` finds (a compiled pattern for "<name\b"), from the end of
    its tag to the first `close` after it (a lower-case string such as "</p>", or a compiled pattern run on
    the lower-cased page), in document order: what re.finditer(r"<name\b[^>]*>(.*?)</name>", h, re.S | re.I)
    yields. An opening with no ">" or no close after it ends the scan, because no later one can have one."""
    i = 0
    while True:
        m = opening.search(h, i)
        if not m:
            return
        gt = h.find(">", m.end())
        if gt < 0:
            return
        if low is None:
            low = _lower(h)
        if isinstance(close, str):
            end = low.find(close, gt + 1)
            after = end + len(close)
        else:
            c = close.search(low, gt + 1)
            end, after = (c.start(), c.end()) if c else (-1, -1)
        if end < 0:
            return
        yield h[gt + 1:end]
        i = after


def in_tags(pattern, start, h):
    """pattern.finditer(h), for a pattern that looks inside one tag: it begins with what `start` finds (a
    compiled pattern) and reaches the rest of its match through [^>]* or [^>]+. The regex alone retries every
    start inside a tag that never closes, each time to the end of the page; here a start that does not match
    skips the rest of its tag, where no start can match either."""
    i = 0
    while True:
        a = start.search(h, i)
        if not a:
            return
        m = pattern.match(h, a.start())
        if m:
            yield m
            i = max(m.end(), a.start() + 1)
            continue
        gt = h.find(">", a.end())
        if gt < 0:
            return
        i = gt + 1


_HIDDEN = re.compile(r"<(script|style|noscript|template|svg)\b", re.I)
_TAG = re.compile(r"<[^>]+>")


def strip_hidden(h):
    """h with each script, style, noscript, template and svg element replaced by a space. A script, style,
    noscript or template that is never closed hides the rest of the page, as it does in a browser. An <svg>
    that is never closed hides nothing, as before: a browser shows the text after it."""
    out, i, low, open_svg = [], 0, None, False
    while True:
        m = _HIDDEN.search(h, i)
        if not m:
            out.append(h[i:])
            return "".join(out)
        if low is None:
            low = _lower(h)
        name = m.group(1).lower()
        close = "</%s>" % name
        # once one <svg> has no close, no later one has either: skip the search, which would scan to the end
        end = -1 if name == "svg" and open_svg else low.find(close, m.end())
        if end < 0 and name == "svg":
            open_svg = True
            out.append(h[i:m.end()])
            i = m.end()
            continue
        out.append(h[i:m.start()])
        if end < 0:
            return "".join(out)
        out.append(" ")
        i = end + len(close)


def visible_text(h):
    h = strip_hidden(h)
    # nothing after the last ">" can be a tag, and <[^>]+> would scan to the end of the page from every "<" there
    k = h.rfind(">") + 1
    h = _TAG.sub(" ", h[:k]) + h[k:]
    return re.sub(r"\s+", " ", html.unescape(h)).strip()


_MAIN, _ARTICLE = re.compile(r"<main\b", re.I), re.compile(r"<article\b", re.I)


def main_html(h):
    """The first <main> element's content, else the first <article>'s, else the whole page."""
    low = _lower(h)
    for opening, close in ((_MAIN, "</main>"), (_ARTICLE, "</article>")):
        body = next(inner_html(h, opening, close, low), None)
        if body is not None:
            return body
    return h

_SURROGATE_ESC = re.compile(r"\\u[dD][89a-fA-F]")

_SCRIPT = re.compile(r"<script", re.I)
_LD_TYPE = re.compile(r'type=["\']application/ld\+json["\']', re.I)


def ld_blocks(h):
    r"""The text of each JSON-LD block, as re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>
    (.*?)</script>', h, re.S | re.I) found them, in one pass. A <script> tag that is not JSON-LD is skipped to
    its ">", and an unclosed block ends the scan."""
    i, low = 0, None
    while True:
        m = _SCRIPT.search(h, i)
        if not m:
            return
        gt = h.find(">", m.end())
        if gt < 0:
            return
        # the type attribute sits inside the tag, at least one character after "<script"
        if not _LD_TYPE.search(h, m.end() + 1, gt):
            i = gt + 1
            continue
        if low is None:
            low = _lower(h)
        end = low.find("</script>", gt + 1)
        if end < 0:
            return
        yield h[gt + 1:end]
        i = end + len("</script>")


def jsonld(h):
    out = []
    for block in ld_blocks(h):
        raw = block.strip()
        try: d = json.loads(raw)
        except Exception:
            try: d = json.loads(re.sub(r",\s*([}\]])", r"\1", raw))
            except Exception: continue
        if _SURROGATE_ESC.search(raw):
            # a lone \ud800 escape decodes to a character no UTF-8 output can carry, and the first print of a
            # name holding one ended the run: it becomes "?" here, while a pair (an emoji) comes through whole
            try: d = json.loads(json.dumps(d, ensure_ascii=False).encode("utf-8", "replace"))
            except Exception: continue
        out.extend(d if isinstance(d, list) else [d])
    # flattened in document order with a stack, not by recursion: a page can nest lists or @graph a few
    # thousand deep, which json.loads accepts on newer Pythons and a recursive walk did not survive
    flat, stack = [], out[::-1]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if isinstance(o.get("@graph"), list): stack.extend(o["@graph"][::-1])
            else: flat.append(o)
        elif isinstance(o, list):
            stack.extend(o[::-1])
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
            # an @id that is an object or a list names nothing, and cannot be looked up
            if set(v) == {"@id"} and isinstance(v["@id"], str) and v["@id"] in by_id:
                return deref({k: x for k, x in by_id[v["@id"]].items() if k != "@id"}, depth + 1)
            return {k: deref(x, depth + 1) for k, x in v.items()}
        if isinstance(v, list): return [deref(x, depth + 1) for x in v]
        return v
    return [deref(o) for o in objs]

def types_of(objs):
    """Every type the objects declare. Only a string names a type: an @type that is an object, a number or
    null, alone or in a list, names none (one written as {"@id": "Organization"} used to end the run)."""
    t = set()
    for o in objs:
        v = o.get("@type")
        t.update(x for x in (v if isinstance(v, list) else [v]) if isinstance(x, str) and x)
    return t

# The fields that make a page-type object carry information rather than a bare type: any one of them,
# non-empty, is a "real field value" in the rubric's sense for p1.page-type.
PAGE_TYPE_FIELDS = {
    "Product": ("name",), "Offer": ("price", "priceSpecification"), "FAQPage": ("mainEntity",),
    "HowTo": ("step",), "SoftwareApplication": ("name",), "Course": ("name",), "Recipe": ("name",),
    "Event": ("startDate",), "JobPosting": ("title",), "Dataset": ("name",),
    "Article": ("headline", "name"), "BlogPosting": ("headline", "name"),
    "NewsArticle": ("headline", "name"), "TechArticle": ("headline", "name")}


def substantive(obj, types=PAGE_TYPE_FIELDS):
    """True when a JSON-LD object of one of `types` carries a non-empty value in one of its fields."""
    t = obj.get("@type")
    for name in (t if isinstance(t, list) else [t]):
        if isinstance(name, str) and name in types and any(obj.get(f) not in (None, "", [], {}) for f in types[name]):
            return True
    return False


_MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
# numeric dates must not start inside a longer number; \b fails when a date sits flush against Chinese
# text ("更新于2026年8月28日"), because Python counts CJK characters as word characters
_NUM_DATE = re.compile(r"(?<!\d)(20[12]\d)\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})(?!\d)")
_DMY = re.compile(r"(?<!\d)(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s+(20[12]\d)(?!\d)", re.I)
_MDY = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2}),?\s+(20[12]\d)(?!\d)", re.I)


def _date(y, m, d):
    try:
        return datetime.date(int(y), int(m), int(d))
    except (ValueError, TypeError):
        return None


def iso_date(v):
    """The calendar date at the start of an ISO 8601 string (dateModified, <time datetime>), or None."""
    m = re.match(r"\s*(\d{4})-(\d{2})-(\d{2})", str(v or ""))
    return _date(*m.groups()) if m else None


# tag-attribute patterns, read with in_tags(pattern, start, page)
_TIME, _TIME_DATETIME = re.compile(r"<time", re.I), re.compile(r'<time[^>]+datetime=["\']([^"\']+)', re.I)
_ARTICLE_TIME_PROP = re.compile(r'property=["\']article:(published|modified)_time["\']', re.I)
_ARTICLE_TIME = re.compile(r'property=["\']article:(published|modified)_time["\'][^>]*content=["\']([^"\']+)', re.I)
_A = re.compile(r"<a\b", re.I)
_A_HREF = re.compile(r'<a\b[^>]*href=["\']([^"\'#]+)', re.I)
_REL_AUTHOR = re.compile(r'rel=["\']author["\']')
_REL_AUTHOR_NAME = re.compile(r'rel=["\']author["\'][^>]*>\s*([A-Z][\w.\-]+(?:\s+[A-Z][\w.\-]+){0,2})')
_OG_SITE_PROP = re.compile(r'property=["\']og:site_name["\']', re.I)
_OG_SITE_NAME = re.compile(r'property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)', re.I)
_CONTENT_VALUE = re.compile(r'content=["\']([^"\']+)["\']', re.I)
_OG_SITE_NAME_TAIL = re.compile(r'property=["\']og:site_name', re.I)
_LINK = re.compile(r"<link", re.I)
_LINK_REL = re.compile(r'rel=["\'](?:llms|ai-content|alternate)["\']', re.I)
_LINK_TYPE = re.compile(r'type=["\']text/(?:plain|markdown)', re.I)


def geo_link(h):
    """re.search(r'<link[^>]+rel=["\'](?:llms|ai-content|alternate)["\'][^>]*type=["\']text/(?:plain|markdown)', h,
    re.I), tag by tag: the two [^>]* runs made the regex quadratic within one long tag, as well as across tags."""
    i = 0
    while True:
        a = _LINK.search(h, i)
        if not a:
            return False
        gt = h.find(">", a.end())
        end = gt if gt >= 0 else len(h)
        rel = _LINK_REL.search(h, a.end() + 1, end)
        if rel and _LINK_TYPE.search(h, rel.end(), end):
            return True
        if gt < 0:
            return False
        i = gt + 1


def og_site_name(h):
    """What re.search(r'property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)', h, re.I) captures, or else
    re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:site_name', h, re.I), in one pass each. In the
    second a content value may itself hold ">", so a tag cannot be skipped whole: a value matches when the first
    og:site_name after it comes before the first ">" after it."""
    m = next(in_tags(_OG_SITE_NAME, _OG_SITE_PROP, h), None)
    if m:
        return m.group(1)
    i, gt, prop = 0, -1, -1
    while True:
        a = _CONTENT_VALUE.search(h, i)
        if not a:
            return None
        e = a.end()
        # each value found ends after the one before it, so both positions only move forward
        if gt < e:
            gt = h.find(">", e)
            if gt < 0:
                gt = len(h)
        if prop < e:
            p = _OG_SITE_NAME_TAIL.search(h, e)
            if not p:
                return None
            prop = p.start()
        if prop < gt:
            return a.group(1)
        i = a.start() + 1


def has_md_link(t):
    r"""re.search(r"\[[^\]]+\]\([^)]+\)", t) in one pass: a "[" whose "]" is not followed by "(…)" skips to
    that "]", since every "[" before it meets the same "]"."""
    i = 0
    while True:
        a = t.find("[", i)
        if a < 0:
            return False
        b = t.find("]", a + 1)
        if b < 0:
            return False
        if b > a + 1 and t.startswith("(", b + 1):
            c = t.find(")", b + 2)
            if c < 0:
                return False
            if c > b + 2:
                return True
        i = b + 1


# A Sitemap: line in robots.txt. [^\S\n]* rather than \s*: \s* crossed newlines, so the regex was tried at every
# line start of a run of blank lines and scanned the whole run each time (100 KB of newlines took 45 s). The
# matches are the same, because a match can only begin on the line its "sitemap:" is on or in the blank run
# before it, and it captures the same URL either way.
_SITEMAP_DECL = re.compile(r"(?im)^[^\S\n]*sitemap:\s*(\S+)")


def visible_dates(page_html):
    """Dates a reader or a crawler can see on the page: <time datetime> and dates written in the text."""
    out = [iso_date(m.group(1)) for m in in_tags(_TIME_DATETIME, _TIME, page_html)]
    text = visible_text(main_html(page_html))[:3000]
    out += [_date(*m.groups()) for m in _NUM_DATE.finditer(text)]
    out += [_date(m.group(3), _MONTHS[m.group(2).lower()[:3]], m.group(1)) for m in _DMY.finditer(text)]
    out += [_date(m.group(3), _MONTHS[m.group(1).lower()[:3]], m.group(2)) for m in _MDY.finditer(text)]
    return [d for d in out if d]


def own_dates(page_html, objs):
    """The page's own dates, the ones a dateModified has to agree with: datePublished in its JSON-LD,
    article:published_time / modified_time, and the first date in the main content (a byline or a
    header). Not every date on the page: related-story rails, listings and comments carry dates of
    other content."""
    out = [iso_date(x.get("datePublished")) for x in objs]
    out += [iso_date(m.group(2)) for m in in_tags(_ARTICLE_TIME, _ARTICLE_TIME_PROP, page_html)]
    first = first_date(main_html(page_html)[:20000])
    return [d for d in out + [first] if d]


def first_date(html_part):
    """The first date in document order: a <time> element stands in for its datetime, then the earliest
    written date wins."""
    text = visible_text(re.sub(r'<time[^>]+datetime=["\']([^"\']+)["\'][^>]*>.*?</time>',
                               lambda m: " %s " % (m.group(1)[:10]), html_part, flags=re.S | re.I))
    found = [(m.start(), _date(*m.groups())) for m in _NUM_DATE.finditer(text)]
    found += [(m.start(), _date(m.group(3), _MONTHS[m.group(2).lower()[:3]], m.group(1))) for m in _DMY.finditer(text)]
    found += [(m.start(), _date(m.group(3), _MONTHS[m.group(1).lower()[:3]], m.group(2))) for m in _MDY.finditer(text)]
    found = [f for f in found if f[1]]
    return min(found)[1] if found else None


# a word before "by" that makes it a credit, a sort order or a filter, not a byline
_CREDIT = re.compile(r"(?:powered|built|made|hosted|designed|developed|sponsored|presented|backed|trusted|used|loved|"
                     r"created|brought to you|followed|group|grouped|sort|sorted|filter|filtered|curated|operated|"
                     r"owned|published|translated|funded|supported|inspired)\s*$", re.I)
_BYLINE = re.compile(r"(?<![A-Za-z])[Bb][Yy]\s+((?:(?:Dr|Prof|Mr|Ms|Mrs)\.\s+)?(?:[A-Z]\.|[A-Z][A-Za-z'\u2019\-]+)"
                     r"(?:\s+(?:[A-Z]\.|[A-Z][A-Za-z'\u2019\-]+|van|von|de|da|del|der|den|bin|al|le|la|di|du)){1,3})")


def byline_name(text):
    """The first "By Jane Doe" in `text` that is a byline: two to four name words, not a credit such as
    "Powered by Hugo" or "Sorted by Date", cut before any trailing punctuation."""
    for m in _BYLINE.finditer(text):
        if _CREDIT.search(text[max(0, m.start() - 40):m.start()]):
            continue
        name = m.group(1).rstrip(".,;:!?)'\u2019 ")
        if len(name.split()) >= 2:
            return name
    return None


_HEADING, _HEADING_CLOSE = re.compile(r"<h[1-4]\b", re.I), re.compile(r"</h[1-4]>")
_TITLE, _PARA = re.compile(r"<title\b", re.I), re.compile(r"<p\b", re.I)


def title_html(h, low=None):
    """The first <title> element's content, or None."""
    return next(inner_html(h, _TITLE, "</title>", low), None)

def headings(h):
    low = _lower(h)
    # an <h1>–<h4> runs to the first heading close of any level, as the pattern it replaces did
    out = [visible_text(x)[:200] for x in inner_html(h, _HEADING, _HEADING_CLOSE, low)]
    t = title_html(h, low)
    if t is not None: out.append(visible_text(t)[:200])
    return [x for x in out if x]

def paragraphs(h):
    return [p for p in (visible_text(x) for x in inner_html(main_html(h), _PARA, "</p>")) if p]

# Chinese, Japanese and Korean characters: Han, kana (hiragana, katakana, half-width katakana) and hangul
_KANA = "\u3040-\u30ff\u31f0-\u31ff\uff66-\uff9f"
_HANGUL = "\uac00-\ud7af\u1100-\u11ff\u3130-\u318f"
_CJK = re.compile("[\u4e00-\u9fff%s%s]" % (_KANA, _HANGUL))


def cjk_chars(s):
    return len(_CJK.findall(s))


def wc(s):
    """Words, or characters for text past 20 Chinese, Japanese or Korean characters that outnumber its words: an
    English page's language menu (日本語, 한국어, 简体中文 …) does not make its 1,600 words read as 24 characters."""
    cjk, words = cjk_chars(s), len(s.split())
    return cjk if cjk > 20 and cjk >= words else words

def host_stem(root):
    parts = urllib.parse.urlsplit(root).netloc.replace("www.", "").split(".")
    return parts[0].lower()

def is_cjk(s):
    """Is this page written in Chinese, Japanese or Korean? Judged on what a reader sees, not on raw markup —
    a Chinese page whose HTML is mostly CSS/JS would otherwise fall under the 8% threshold."""
    if "<" in s and ">" in s: s = visible_text(s)
    return script_lang(s) is not None


# ── page language ──────────────────────────────────────────────────────────
# Each page is read in its own language: an English page on a site whose homepage came back in Chinese is
# still read in words, and a Japanese or German page is not read with the English or Chinese lexicon.
CJK_LANGS = ("zh", "ja", "ko")
# code samples: in no natural language, so never read to tell a page's
_CODE_TAGS = ("pre", "code")
# the Chinese, Japanese or Korean characters a page declared in one of those languages keeps its declaration with
CJK_FLOOR = 30
# languages this file has heading, source-phrase and byline lexicons for; "und" is a page whose language could
# not be told, which is read with them as every page was before
LEXICON_LANGS = ("en", "zh", "und")
_HTML_OPEN = re.compile(r"<html\b", re.I)
_LANG_ATTR = re.compile(r"""(?<![\w:.-])(?:xml:)?lang\s*=\s*["']?\s*([A-Za-z]{2,3})(?![A-Za-z])""", re.I)
_LANG_TAG = re.compile(r"\s*([A-Za-z]{2,3})(?![A-Za-z])")
# a few words common in each language and rare in the others, to tell Latin-script text apart
_STOPWORDS = {
    "en": "the and of to is are for with that this you your it be by from",
    "de": "der die das und ist nicht mit ein eine für sie auf den von dem wir ihr ihre sich auch im zu",
    "fr": "le les et est une pour avec dans sur pas vous qui nous au aux ce cette",
    "es": "el los las y una con del su sus más pero muy",
    "pt": "os e é uma com não em você seu sua mas",
}
_STOPWORDS = {k: set(v.split()) for k, v in _STOPWORDS.items()}
_LATIN_WORD = re.compile(r"[a-zà-öø-ÿ]+")


def declared_lang(resp):
    """The primary tag of the page's <html lang>, else of its Content-Language header, lower-cased; or None."""
    h = resp.text
    m = _HTML_OPEN.search(h)
    gt = h.find(">", m.end()) if m else -1
    a = _LANG_ATTR.search(h, m.end(), gt) if gt >= 0 else None
    if a:
        return a.group(1).lower()
    c = _LANG_TAG.match(resp.headers.get("content-language", ""))
    return c.group(1).lower() if c else None


def script_lang(text):
    """ja, ko or zh when the text is written in Chinese, Japanese or Korean (kana is Japanese, hangul Korean,
    Han alone Chinese); None otherwise."""
    han = len(re.findall("[\u4e00-\u9fff]", text))
    kana = len(re.findall("[%s]" % _KANA, text))
    hangul = len(re.findall("[%s]" % _HANGUL, text))
    total = han + kana + hangul
    if total <= max(30, len(text) * 0.08):
        return None
    if hangul * 2 >= total:
        return "ko"
    return "ja" if kana >= max(10, total * 0.05) else "zh"


def latin_lang(text):
    """en, de, fr, es or pt, told by common words, when one language clearly leads; else "und"."""
    counts = dict.fromkeys(_STOPWORDS, 0)
    for w in _LATIN_WORD.findall(text[:20000].lower()):
        for k, words in _STOPWORDS.items():
            if w in words:
                counts[k] += 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    (best, n), (_, second) = ranked[0], ranked[1]
    return best if n >= 5 and n >= 2 * second else "und"


def page_lang(resp):
    """The language a page is written in, as a lower-case primary tag (zh, ja, ko, en, de, fr, es, pt, or any
    other tag the page declares), or "und". <html lang>, else the Content-Language header, says which, unless
    the text contradicts it: a page declared in a Latin-script language whose visible text is Chinese, Japanese
    or Korean is read in that language, and a page declared Chinese, Japanese or Korean with next to none of
    that text (under CJK_FLOOR characters) is told by its words. With no declaration the script decides, and
    Latin-script text is told apart by a few common words. Code (<pre>, <code>) is in no natural language and
    is not read: a docs page's samples, with their English comments, made a Chinese page read as English."""
    text = visible_text(strip_chrome(strip_comments(strip_hidden(resp.text)), _CODE_TAGS, ()))
    script, declared = script_lang(text), declared_lang(resp)
    if declared and (declared in CJK_LANGS) == bool(script):
        return declared
    if declared in CJK_LANGS and cjk_chars(text) >= CJK_FLOOR:
        # a declared Chinese, Japanese or Korean page with that much of its text is one, whatever else it carries
        return declared
    if script:
        return script
    latin = latin_lang(text)
    return latin if latin != "und" else (declared or "und")


def audience_language(langs):
    """The report's audience_language: the most common page language, ties to the page sampled first, as a
    BCP 47 primary tag. Chinese stays "zh-CN", as it was when the field could only be that or "en". "und" when
    no page's language could be told."""
    known = [x for x in langs if x != "und"]
    if not known:
        return "und"
    best = max(dict.fromkeys(known), key=known.count)
    return "zh-CN" if best == "zh" else best


# Wikipedia editions, besides English, that a knowledge-graph lookup may go to: the larger ones
WIKI_LANGS = frozenset("ar bg ca cs da de el es et fa fi fr he hi hr hu id it ja ko lt lv ms nl no pl pt ro ru sk sl "
                       "sr sv th tr uk vi zh".split())


def lexicon_gap(langs):
    """The page languages, in order, that have no lexicon here."""
    return list(dict.fromkeys(x for x in langs if x not in LEXICON_LANGS))

# ── figures and their sources (p2.sourced-stats) ───────────────────────────
# The rubric's attributed figure is one whose source sits beside it. A link, a <cite> or a source word anywhere
# on the page is not that: read page-wide, social icons, partner logos and a "Research" menu item in the chrome
# attributed every figure on the page. Only p2.sourced-stats reads a page this way, so no other check moves.
_CHROME_TAGS = ("header", "nav", "footer", "aside")
_CHROME_ROLES = ("banner", "navigation", "contentinfo", "complementary")
# a role is honoured on these containers only, so at most these names are ever paired open to close
_ROLE_HOSTS = {"div", "section", "ul", "ol", "menu", "span", "p", "form", "table"} | set(_CHROME_TAGS)
_OPEN_TAG = re.compile(r"<([A-Za-z][A-Za-z0-9-]*)")
_ROLE = re.compile(r"""\brole\s*=\s*["']?\s*(%s)\b""" % "|".join(_CHROME_ROLES), re.I)


def strip_comments(h):
    """h with each HTML comment replaced by a space. One that is never closed hides the rest of the page, as it
    does in a browser."""
    out, i = [], 0
    while True:
        a = h.find("<!--", i)
        if a < 0:
            out.append(h[i:])
            return "".join(out)
        out.append(h[i:a])
        b = h.find("-->", a + 4)
        if b < 0:
            return "".join(out)
        out.append(" ")
        i = b + 3


def _closes(low, name):
    """{where each <name> opening starts: where the name of its matching </name> ends}, in one pass over the
    lower-cased page with a stack, so that nested elements of one name pair up. An opening never closed is
    left out."""
    out, stack = {}, []
    for m in re.finditer(r"<(/?)%s\b" % re.escape(name), low):
        if not m.group(1):
            stack.append(m.start())
        elif stack:
            out[stack.pop()] = m.end()
    return out


def strip_chrome(h, tags=_CHROME_TAGS, roles=_CHROME_ROLES):
    """h without each element named in `tags`, or whose role is one of `roles`, and everything inside it. An
    element that is never closed stays, content and all: where a browser would end it is a guess."""
    low, cut, pairs, i = None, [], {}, 0
    while True:
        m = _OPEN_TAG.search(h, i)
        if not m:
            break
        gt = h.find(">", m.end())
        if gt < 0:
            break
        name = m.group(1).lower()
        chrome = name in tags
        if not chrome and name in _ROLE_HOSTS:
            r = _ROLE.search(h, m.end(), gt)
            chrome = bool(r) and r.group(1).lower() in roles
        if chrome:
            if low is None:
                low = _lower(h)
            if name not in pairs:
                pairs[name] = _closes(low, name)
            end = pairs[name].get(m.start())
            if end is not None:
                close = h.find(">", end)
                i = close + 1 if close >= 0 else len(h)
                cut.append((m.start(), i))
                continue
        i = gt + 1
    if not cut:
        return h
    out, at = [], 0
    for a, b in cut:
        out += [h[at:a], " "]
        at = b
    out.append(h[at:])
    return "".join(out)


def _content(clean):
    body = main_html(clean)
    if body is clean:
        return strip_chrome(clean)
    return strip_chrome(body, ("nav", "aside"), ("navigation", "complementary"))


def content_html(h):
    """What p2.sourced-stats reads, and no other check: the first <main>, else the first <article>, without any
    nav or aside inside it; on a page with neither, the whole page without its header, nav, footer and aside and
    the elements whose role is banner, navigation, contentinfo or complementary. No script, style, noscript,
    template, svg or comment either way."""
    return _content(strip_comments(strip_hidden(h)))


# The edges of a block: the elements read as blocks (p, li, tr, td, dd, figcaption, blockquote, caption), and the
# headings and containers around them, so that text outside all of those does not run on into one long block.
_BLOCK_EDGE = re.compile(r"</?(?:p|li|tr|td|th|dd|dt|dl|figcaption|blockquote|caption|h[1-6]|div|section|article|"
                         r"ul|ol|table|thead|tbody|tfoot|figure|header|footer|main|aside|nav|form|details|summary|"
                         r"pre|hr)\b", re.I)


def text_blocks(h):
    """[(html, visible text)] of each block of h in document order, leaving out those with no visible text."""
    out, i, start = [], 0, 0
    while True:
        m = _BLOCK_EDGE.search(h, i)
        gt = h.find(">", m.end()) if m else -1
        piece = h[start:m.start() if gt >= 0 else len(h)]
        t = visible_text(piece)
        if t:
            out.append((piece, t))
        if gt < 0:
            return out
        start = i = gt + 1


# a figure: a percentage, a sum of money, or a number of three or more characters, less the prices and identifiers
# figures() leaves out. Latin letters, digits, a point and a "#" before it bound it (so "v1.2.3" holds no "2.3", and
# "#1928093" is a reference, not a figure); \w would also count Chinese characters, so "占用了61%的" would not be a
# figure at all
_FIGURE = re.compile(r"(?<![A-Za-z0-9_.#-])(\d[\d,.]*\s?%|[$€£¥]\s?\d[\d,.]*|\d[\d,.]{2,})(?![A-Za-z0-9_-])")
# a year, a version number, a dotted date or a run of seven or more bare digits is a number, not a statistic that
# needs a source. The run is a phone, filing or account number: 13800138000, 沪ICP备14017582号, 小红书号：3152645850
_NOT_A_FIGURE = re.compile(r"(?:19|20)\d\d|\d+(?:\.\d+){2,}|\d{7,}")
# and so is a shorter number that a filing or account label introduces, or that 号 follows: 京ICP证030173号. Chinese
# sites carry these in a <div class="footer"> as often as in a <footer>, where they read as the page's figures
_ID_BEFORE = re.compile(r"(?:ICP[备证]|公安备|网安备|号)\s*[:：]?\s*$")
_ID_AFTER = re.compile(r"\s*号")
# a sum of money: a currency sign or code before the number, or 元 or a code after it
_MONEY_BEFORE = re.compile(r"(?:[$€£¥￥]|(?<![A-Za-z])(?:USD|EUR|GBP|CNY|RMB|JPY))\s?$")
_MONEY_AFTER = re.compile(r"\s?(?:元|(?:USD|EUR|GBP|CNY|RMB|JPY)(?![A-Za-z]))")
# A sum of money is a price, the site's own terms rather than a claim someone measured, when it is written the way
# only a price is ("$29/mo", "68元/月", "$15 per user", "¥68起"), a price word comes before it ("每月68元",
# "售价 ¥199") or it is all its block says, with or without a billing period (a pricing card's "$29", a price
# table's "£12 a month"). Read as figures, the prices on a sampled /pricing page kept that page from ever
# attributing most of its figures. Any other sum is a figure: "costs a small firm £22,000 a year", "a £90,000
# threshold", and any sum with a magnitude after it ("$4.5 billion", "3000亿元")
_PERIOD = (r"(?:mo|mth|month|yr|year|annum|wk|week|day|hr|hour|user|seat|member|person|licen[cs]e|"
           r"月|年|天|日|人|次|用户|席位|账号)(?![A-Za-z])")
_PRICE_AFTER = re.compile(r"(?:\s?(?:元|USD|EUR|GBP|CNY|RMB|JPY))?\s*(?:/\s*%s|(?:per|each|a)\s+(?:user|seat|member|"
                          r"licen[cs]e)(?![A-Za-z])|每(?:月|年|人|用户)|起)" % _PERIOD, re.I)
_PRICE_WORD = re.compile(r"(?:每月|每年|月费|年费|月付|年付|起价|低至|售价|仅需)\s*[:：]?\s*[$€£¥￥]?\s*$")
_BARE_MONEY = re.compile(r"[\s$€£¥￥*]*(?:(?:USD|EUR|GBP|CNY|RMB|JPY|US)[\s$€£¥￥*]*)?")
_PRICE_TAIL = re.compile(r"\s*(?:(?:元|USD|EUR|GBP|CNY|RMB|JPY)\s*)?(?:(?:/|a|an|per|each|every|每)\s*%s|(?:billed\s+)?"
                         r"(?:monthly|yearly|annually)|起)?[\s.*]*" % _PERIOD, re.I)
_MAGNITUDE = re.compile(r"[\d.,]*\s?(?:[kmb]n?|thousand|million|billion|trillion|万|亿)(?![A-Za-z])", re.I)


def is_price(text, m):
    """Is the sum of money that match m of _FIGURE found in its block's text a price?"""
    after = text[m.end():m.end() + 24]
    if _MAGNITUDE.match(after):
        return False
    if _PRICE_AFTER.match(after) or _PRICE_WORD.search(text, max(0, m.start() - 12), m.start()):
        return True
    # the whole block, when it is short: a pricing card's figure never shares its block with a sentence
    return len(text) <= 40 and bool(_BARE_MONEY.fullmatch(text, 0, m.start()) and _PRICE_TAIL.fullmatch(text, m.end()))


def figures(text):
    """The figures in a block's text, each without the punctuation after it: "30," in "November 30, 2026" is a
    day, not a three-character number. Years, versions, dotted dates, identifiers and prices are left out."""
    out = []
    for m in _FIGURE.finditer(text):
        f = m.group(1).rstrip(".,")
        if not (f[:1] in "$€£¥" or f.endswith("%") or len(f) >= 3) or _NOT_A_FIGURE.fullmatch(f):
            continue
        if not f.endswith("%"):
            before, after = text[max(0, m.start() - 12):m.start()], text[m.end():m.end() + 16]
            if f[:1] in "$€£¥" or _MONEY_BEFORE.search(before) or _MONEY_AFTER.match(after):
                if is_price(text, m):
                    continue
            elif _ID_BEFORE.search(before) or _ID_AFTER.match(after):
                continue
        out.append(f)
    return out


_HREF_IN_TAG = re.compile(r"""\bhref\s*=\s*["']?\s*([^"'\s>]*)""", re.I)


def anchors(h):
    """(href, the first 300 characters of its text) of each <a href> in h, in document order, in one pass. The
    text runs to the next </a>."""
    low, i, close = None, 0, -1
    while True:
        a = _A.search(h, i)
        if not a:
            return
        gt = h.find(">", a.end())
        if gt < 0:
            return
        m = _HREF_IN_TAG.search(h, a.end(), gt)
        if m:
            if low is None:
                low = _lower(h)
            # the first "</a" after an earlier opening is the first after this one too, while this one is before it
            if close < gt:
                close = low.find("</a", gt + 1)
                close = len(h) if close < 0 else close
            yield m.group(1), h[gt + 1:min(close, gt + 301)]
        i = gt + 1


# second-level labels under a country code: example.co.uk is example's, not co's
_SLD = {"ac", "co", "com", "edu", "gob", "go", "gov", "ne", "net", "or", "org"}
# platforms that give each site a subdomain: there the whole host is the site, not the platform's name
_PLATFORMS = ("github.io", "gitlab.io", "vercel.app", "netlify.app", "pages.dev", "web.app", "firebaseapp.com",
              "herokuapp.com", "blogspot.com", "wordpress.com", "substack.com", "notion.site", "readthedocs.io",
              "gitbook.io", "medium.com")
# social profiles and share buttons: where a site sends its readers, not where its figures come from
_SOCIAL = ("facebook.com", "fb.com", "twitter.com", "x.com", "t.co", "linkedin.com", "instagram.com", "youtube.com",
           "youtu.be", "tiktok.com", "pinterest.com", "threads.net", "bsky.app", "t.me", "telegram.me", "wa.me",
           "whatsapp.com", "discord.gg", "discord.com", "weibo.com", "weixin.qq.com", "douyin.com",
           "xiaohongshu.com", "bilibili.com")
_SHARE = re.compile(r"/share|sharer|/intent/|sharearticle|addtoany|addthis|sharethis|/submit\?|/pin/create", re.I)

# p3.video reads two things in the sampled pages' HTML: links to a video channel, and embedded players.
# The Douyin, Xigua and Kuaishou forms were checked on live pages on 2026-10-02:
# - douyin.com/user/<sec_uid> is an account page, and iesdouyin.com/share/user/<id>, where an expanded share link
#   lands, redirects to it. douyin.com/user/self is the signed-in viewer's own page; the 8-character minimum leaves
#   it out;
# - ixigua.com/home/<id> redirects to m.ixigua.com/user/<id>, a channel page with the account's videos;
# - kuaishou.com/profile/<id> and live.kuaishou.com/profile/<id> are profile pages;
# - open.douyin.com/player/video?vid=<id> is Douyin's open-platform player: it plays the video and sends no header
#   that stops it being framed. ixigua.com/iframe/<id> did not play that day, so it is not read as a player.
# Short links (v.douyin.com, v.kuaishou.com) and single-video URLs (douyin.com/video/<id>, ixigua.com/<id>,
# kuaishou.com/short-video/<id>) are never channels: which account they belong to cannot be read without following
# them. The host must start the match, so v.douyin.com/... and notdouyin.com/... are not read as douyin.com.
VIDEO_CHANNEL = re.compile(
    r"(?:youtube\.com/(?:@|c/|channel/|user/)|bilibili\.com/\d{4,}|space\.bilibili\.com/|vimeo\.com/[a-z0-9-]{3,}"
    r"|(?<![a-z0-9_.-])(?:www\.)?(?:douyin\.com/user|iesdouyin\.com/share/user)/[a-z0-9_-]{8,}"
    r"|(?<![a-z0-9_.-])(?:(?:www\.)?ixigua\.com/home|m\.ixigua\.com/user)/\d{4,}"
    r"|(?<![a-z0-9_.-])(?:www\.|live\.)?kuaishou\.com/profile/[a-z0-9_-]{3,})", re.I)
VIDEO_EMBED = re.compile(r"(?:youtube\.com/embed|youtu\.be/|player\.vimeo\.com|player\.bilibili"
                         r"|(?<![a-z0-9_.-])open\.douyin\.com/player/video)", re.I)


def video_links(text):
    """(channel links, embedded players) in a page's HTML, as p3.video counts them."""
    return len(VIDEO_CHANNEL.findall(text)), len(VIDEO_EMBED.findall(text))


def _host_in(host, domains):
    return any(host == d or host.endswith("." + d) for d in domains)


def site_key(host):
    """The name a site goes by across its hosts: "example" for www.example.com, docs.example.com and
    example.co.uk. An IP address, or a host on a platform such as github.io, is its own key."""
    host = (host or "").lower().rstrip(".")
    host = host[4:] if host.startswith("www.") else host
    if not host or ":" in host or re.fullmatch(r"[\d.]+", host) or _host_in(host, _PLATFORMS):
        return host
    p = host.split(".")
    if len(p) >= 3 and p[-2] in _SLD and len(p[-1]) == 2:
        return p[-3]
    return p[-2] if len(p) >= 2 else host


def profile_of(url):
    """(host, path) of a sameAs profile, to tell a link to the site's own profile from a source."""
    try:
        u = urllib.parse.urlsplit(url.strip())
        host = (u.hostname or "").lower()
    except ValueError:
        return None
    return (host[4:] if host.startswith("www.") else host, u.path.rstrip("/").lower()) if host else None


def source_link(href, own, profiles=()):
    """Does this href lead to a source? An http(s) link off the site (the site_key of its host is not in `own`),
    to none of the site's own sameAs profiles ((host, path) pairs from profile_of), and to no social profile or
    share button."""
    if href.startswith("//"):
        href = "https:" + href
    try:
        u = urllib.parse.urlsplit(href)
        host = (u.hostname or "").lower()
    except ValueError:
        return False
    if u.scheme.lower() not in ("http", "https") or not host:
        return False
    host = host[4:] if host.startswith("www.") else host
    if site_key(host) in own or _host_in(host, _SOCIAL) or _SHARE.search(href):
        return False
    path = u.path.rstrip("/").lower() + "/"
    return not any(p and host == p[0] and path.startswith(p[1] + "/") for p in profiles)


_CITE = re.compile(r"<cite\b", re.I)
_SOURCE_PHRASE = re.compile(r"(?<![A-Za-z])(?:sources?|sourced|stud(?:y|ies)|reports?|reported|research|surveys?|"
                            r"surveyed|according to)(?![A-Za-z])|数据来源|资料来源|来源[:：]|据.{0,6}报告", re.I)
_FOOTNOTE_REF = re.compile(r"\[?\s*(?:\d{1,3}|[*†‡§])\s*\]?")
_ID_ATTR = re.compile(r"""\sid\s*=\s*["']?([^"'\s>]+)""", re.I)
NOTE_SPAN, MAX_NOTES = 1500, 100


def stat_reading(h, own, profiles=(), phrases=True):
    """p2.sourced-stats on one page: (figures, attributed, attributed with a link). A figure is attributed when its
    block of the content (content_html, text_blocks), or the next block, holds a link to a source (source_link),
    a <cite>, a source phrase (when `phrases` is set), or a footnote reference whose note on the page links to a
    source. A link, or a note with one, is the clickable and checkable source the top tier asks for."""
    clean = strip_comments(strip_hidden(h))
    blocks = text_blocks(_content(clean))
    ids, notes, kinds = None, {}, {}

    def note_links(ref):
        # the note is the element that carries the id, up to its first close; the whole page, chrome and all, is
        # searched, because notes often sit in a footer or an aside
        nonlocal ids
        if ref not in notes:
            if ids is None:
                ids = {}
                for m in _ID_ATTR.finditer(clean):
                    ids.setdefault(m.group(1), m.end())
            at = ids.get(ref)
            if at is None or len(notes) >= MAX_NOTES:
                return False
            lt = clean.rfind("<", max(0, at - 300), at)
            tag = _OPEN_TAG.match(clean, lt) if lt >= 0 else None
            span = clean[at:at + NOTE_SPAN]
            end = _lower(span).find("</%s" % tag.group(1).lower()) if tag else -1
            notes[ref] = any(source_link(u, own, profiles) for u, _ in anchors(span[:end] if end >= 0 else span))
        return notes[ref]

    def kind(j):
        if j not in kinds:
            piece, text = blocks[j]
            k = None
            for href, label in anchors(piece):
                if source_link(href, own, profiles) or (
                        href.startswith("#") and _FOOTNOTE_REF.fullmatch(visible_text(label))
                        and note_links(href[1:])):
                    k = "link"
                    break
            if k is None and (_CITE.search(piece) or (phrases and _SOURCE_PHRASE.search(text))):
                k = "named"
            kinds[j] = k
        return kinds[j]

    n = attributed = linked = 0
    for j, (_piece, text) in enumerate(blocks):
        k = len(figures(text))
        if not k:
            continue
        near = {kind(j), kind(j + 1) if j + 1 < len(blocks) else None}
        n += k
        attributed += k if near - {None} else 0
        linked += k if "link" in near else 0
    return n, attributed, linked


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

def sameas_tier(statuses):
    """p3.sameas from the HTTP status of each fetched sameAs link (0 = no response).
    Only 404 / 410 prove a profile is gone; everything else that is not a 2xx is
    something this network could not see, and is left out rather than counted dead.
    Returns (tier or None when nothing could be checked, good, dead, unseen)."""
    good = sum(1 for s in statuses if 200 <= s < 300)
    dead = sum(1 for s in statuses if s in (404, 410))
    unseen = len(statuses) - good - dead
    if good + dead == 0:
        return None, good, dead, unseen
    return (3 if not dead else (2 if good else 0)), good, dead, unseen

def kg_tier(found, answered, asked):
    """p3.knowledge-graph: 4 when an entity was found; 0 only when every lookup answered
    and none matched; otherwise unobservable (None) — the unanswered lookup may be where it is."""
    if found: return 4
    if asked and answered == asked: return 0
    return None

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

def next_tier(cid, t, mx):
    """(points the next tier up adds, what it needs), from the same tier conditions as tier_reason(). At the top
    tier (0, ""); for a check with no tier table, the full headroom and no condition."""
    ts = TIERS.get(cid)
    if t >= mx:
        return 0, ""
    if not ts:
        return mx - t, ""
    nxt = next(p for p in ts if p[0] > t)
    return nxt[0] - t, nxt[1]

# ── sampling ───────────────────────────────────────────────────────────────
def kg_lookups(cand, lg):
    """The Wikidata and the Wikipedia search for one brand candidate in one language: public APIs, no key."""
    q = urllib.parse.quote(cand)
    return ("https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json"
            "&language=%s&uselang=%s&limit=5&search=%s" % (lg, lg, q),
            "https://%s.wikipedia.org/w/api.php?action=query&format=json&list=search"
            "&srlimit=3&srsearch=%s" % (lg, q))

def kg_found(cand, lg, wd, wp):
    """Where the answers to kg_lookups(cand, lg) name an entity labelled exactly cand: at most one Wikidata item
    and one Wikipedia title, as evidence."""
    out = []
    if wd.ok:
        try:
            for it in json.loads(wd.text).get("search", []):
                if (it.get("label", "") or "").strip().lower() == cand.lower():
                    out.append("Wikidata %s %s" % (_UNSAFE.sub("", str(it.get("id")))[:20],
                                                   site_text(it.get("description", ""), 40)))
                    break
        except Exception: pass
    if wp.ok:
        try:
            for it in json.loads(wp.text).get("query", {}).get("search", []):
                if (it.get("title", "") or "").strip().lower() == cand.lower():
                    out.append("%s.wikipedia: %s" % (lg, site_text(it.get("title"), 60))); break
        except Exception: pass
    return out

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



def site_text(s, n=90):
    """Text quoted from the audited site, or from a page about it, is data and never instructions.
    Evidence carries it inside «site text: …» so a reader, or an agent reading the report over MCP,
    can tell the site's words from the tool's."""
    s = " ".join(_UNSAFE.sub("", str(s)).split()).replace("«", "‹").replace("»", "›")
    if len(s) > n:
        s = s[:n].rstrip() + "…"
    return "«site text: %s»" % s

def robots_token(value):
    """The product token a user-agent line names, lower case. "Googlebot/2.1" names Googlebot, the way
    crawlers read it; "*" is the wildcard."""
    v = value.strip().lower()
    if v == "*" or re.match(r"\*\s", v):
        return "*"
    m = re.match(r"[a-z_-]+", v)
    return m.group(0) if m else v

def robots_groups(txt):
    """{product token (lower case): [(allow|disallow, path)]}. Consecutive user-agent lines form one group
    and every rule in it applies to all of them (RFC 9309, section 2.1). Reading only the last line of a
    group let a file that blocks GPTBot, ClaudeBot and PerplexityBot together read as blocking none.
    A leading byte-order mark is not part of the first line: read as one, it hid the group it opened."""
    if txt.startswith("\ufeff"):
        txt = txt[1:]
    groups, cur, in_rules = {}, [], False
    for line in txt.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if in_rules:
                cur, in_rules = [], False
            ua = robots_token(v)
            cur.append(ua)
            groups.setdefault(ua, [])
        elif k in ("allow", "disallow") and cur:
            in_rules = True
            for ua in dict.fromkeys(cur):
                groups[ua].append((k, v))
    return groups

def robots_rules(groups, token):
    """The rules one crawler obeys, chosen as RFC 9309 section 2.2.1 says: the groups naming its product
    token (merged, case-insensitive), otherwise the * groups, otherwise none. Returns (rules, whose):
    whose is the token, "*" or None. A * Disallow never reaches a crawler that has a group of its own."""
    t = token.lower()
    if t in groups:
        return groups[t], t
    if "*" in groups:
        return groups["*"], "*"
    return [], None

def blocks_site(rules):
    """The Disallow that shuts a crawler out of the whole site ("/" or "/*"), or None."""
    return next((v for k, v in rules if k == "disallow" and v in ("/", "/*")), None)

def robots_tier(txt, size):
    """g.robots for a robots.txt that answered 2xx: (tier, evidence). Only the retrieval crawlers are
    scored. A training crawler or an opt-out token disallowed by name is reported, never scored."""
    groups = robots_groups(txt)
    sel = [(name,) + robots_rules(groups, name) for name, _ in RETRIEVAL_UAS]
    blocked = [(name, whose, blocks_site(rules)) for name, rules, whose in sel if blocks_site(rules)]
    # an Allow of any path, or an empty Disallow (robots.txt for "allow everything"), is a declaration
    named_allow = [name for name, rules, whose in sel if whose not in (None, "*")
                   and any(k == "allow" or (k == "disallow" and v == "") for k, v in rules)]
    fallback = [name for name, _rules, whose in sel if whose == "*"]
    star_allow = bool(fallback) and any((k == "allow" and v in ("/", "/*")) or (k == "disallow" and v == "")
                                        for k, v in groups["*"])
    not_scored = [t for t in NOT_SCORED_TOKENS if blocks_site(groups.get(t.lower(), []))]
    also = (" It also disallows %s (training crawlers / opt-out tokens, not scored)." % ", ".join(not_scored)
            if not_scored else "")
    n = len(RETRIEVAL_UAS)
    if blocked:
        own = [name for name, whose, _ in blocked if whose != "*"]
        star = [name for name, whose, _ in blocked if whose == "*"]
        names = lambda xs: "all %d" % n if len(xs) == n else ", ".join(xs)
        how = (["%s, in %s own group" % (names(own), "its" if len(own) == 1 else "their")] if own else []) \
            + (["%s, through the * group, having no group of %s own" % (names(star), "its" if len(star) == 1 else "their")]
               if star else [])
        dirs = " or ".join(sorted({d for _, _, d in blocked}))
        return 0, ("robots.txt (%d bytes): a Disallow: %s applies to %d of the %d retrieval crawlers — %s.%s"
                   % (size, dirs, len(blocked), n, "; ".join(how), also))
    if named_allow or star_allow:
        why = (["%d named with an explicit permission (%s)" % (len(named_allow), ", ".join(named_allow))]
               if named_allow else []) \
            + (["%d fall under the * group, which carries an explicit allow-all" % len(fallback)] if star_allow else [])
        return 5, ("robots.txt (%d bytes): no Disallow applies to retrieval crawlers; %s.%s"
                   % (size, "; ".join(why), also))
    return 3, ("robots.txt (%d bytes, %d user-agent%s named): no Disallow applies to retrieval crawlers, and none is "
               "explicitly allowed in the groups that apply to them — permitted by default, not by declaration.%s"
               % (size, len(groups), "" if len(groups) == 1 else "s", also))

# ── robots.txt, page by page ──
# g.robots reads only the Disallow that shuts a crawler out of the whole site. A rule on a path can close one page
# while every whole-site check reads green, and two readings of one file can disagree on that page: RFC 9309's (the
# longest matching rule wins) and the first-match reading of Python's urllib.robotparser and many older checkers (rules
# in file order, the first plain prefix wins). Both are reported outside the score, for the homepage, the sampled
# pages and the first URLs of the sitemap p1.sitemap read (the first child of a sitemap index), and neither moves a
# tier: g.robots reads the file as it always has.
ROBOTS_PATH_URLS = 200      # sitemap URLs checked against robots.txt, after the homepage and the sampled pages
ACCESS_LIST_MAX = 50        # pages the JSON lists under each observation; the counts cover them all
ACCESS_ROWS = 10            # rows the text and Markdown views show
MAX_URL_CHARS = 2048        # the sitemaps protocol's limit: a longer URL is not checked
# RFC 9309 2.5: a crawler may stop parsing robots.txt after 500 KiB, the least it must read. The page-by-page reading
# stops there too, which also bounds its time on a hostile file
ROBOTS_PARSE_LIMIT = 500 * 1024
# Rule comparisons (a prefix looked up, a pattern tried) the page-by-page reading makes in one run, at most. A file of
# many wildcard rules makes every URL meet every rule; past this the URLs left are counted as not checked, so the
# reading never holds a run up by more than about a second
ROBOTS_WORK_MAX = 1000000
FEW_HOME_LINKS = 3          # a homepage whose server HTML links to fewer pages of the site than this is flagged
_UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_PCT = re.compile(r"%([0-9A-Fa-f]{2})")


def robots_path(s):
    """A URL path (with its query) or a robots.txt pattern in the one form RFC 9309 section 2.2.2 compares them in: a
    percent-encoded unreserved character decoded ("%62" is "b"), every other percent-encoding in upper case, and each
    character outside printable ASCII, and each of ' <>"{}|\\^`', percent-encoded as UTF-8. A "%" that starts no
    encoding is itself encoded. "*" and "$" stay as they are: special in a pattern, ordinary characters in a path."""
    out, i, n = [], 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "%":
            m = _PCT.match(s, i)
            if m:
                d = chr(int(m.group(1), 16))
                out.append(d if d in _UNRESERVED else "%" + m.group(1).upper())
                i += 3
                continue
            out.append("%25")
        elif "!" <= ch <= "~" and ch not in UNSAFE:
            out.append(ch)
        else:
            out.append("".join("%%%02X" % b for b in ch.encode("utf-8", "replace")))
        i += 1
    return "".join(out)


def path_and_query(url):
    """What a robots.txt rule is matched against: the URL's path ("/" when it has none), and "?" and its query."""
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return "/"
    return (u.path or "/") + ("?" + u.query if u.query else "")


def _pattern(pattern):
    """A robots.txt pattern (robots_path form) split for robots_match: (anchored at the end, its literal pieces)."""
    anchored = pattern.endswith("$")
    return anchored, (pattern[:-1] if anchored else pattern).split("*")


def robots_match(pattern, path, split=None):
    """Does a robots.txt pattern match a path from its first character (both in robots_path form)? "*" matches any run
    of characters and a "$" at the end anchors the end (RFC 9309 2.2.3); a "$" anywhere else is a character. Matched
    piece by literal piece, with no backtracking, so a hostile pattern costs no more than a long one. `split` is
    _pattern(pattern), when the caller has it."""
    anchored, parts = split or _pattern(pattern)
    if not path.startswith(parts[0]):
        return False
    at = len(parts[0])
    if len(parts) == 1:
        return at == len(path) if anchored else True
    for piece in parts[1:-1]:
        i = path.find(piece, at)
        if i < 0:
            return False
        at = i + len(piece)
    last = parts[-1]
    if anchored:
        return len(path) - len(last) >= at and path.endswith(last)
    return path.find(last, at) >= 0


def _literal(pattern):
    """The text a path must start with for the pattern to match it: everything before the first "*" (and before a
    final "$")."""
    head = pattern.split("*", 1)[0]
    return head[:-1] if head == pattern and head.endswith("$") else head


def robots_matcher(rules, work=None):
    """A function path_and_query -> (allowed, (kind, value) or None) that reads one crawler's rules (robots_rules) as
    RFC 9309 section 2.2.2 says: of the rules that match, the one with the longest pattern decides, an allow wins a tie
    with a disallow, and a path no rule matches is allowed. An empty pattern matches nothing. The rules are indexed by
    the literal text before their first "*", so a path is held only against the rules that can match it. `work`, a
    one-item list, counts the comparisons made (ROBOTS_WORK_MAX)."""
    by_lit = {}
    for i, (kind, value) in enumerate(rules):
        if kind not in ("allow", "disallow") or not value:
            continue
        pat = robots_path(value)
        by_lit.setdefault(_literal(pat), []).append(((len(pat), kind == "allow", -i), pat, _pattern(pat), kind, value))
    lengths = sorted({len(k) for k in by_lit})

    def allows(pq):
        s = robots_path(pq)
        best, tried = None, 0
        for n in lengths:
            if n > len(s):
                break
            cands = by_lit.get(s[:n], ())
            tried += 1 + len(cands)
            for rank, pat, split, kind, value in cands:
                if (best is None or rank > best[0]) and robots_match(pat, s, split):
                    best = (rank, kind, value)
        if work is not None:
            work[0] += tried
        return (True, None) if best is None else (best[1] == "allow", (best[1], best[2]))
    return allows


def robots_allows(rules, path_and_query):
    """(allowed, the deciding (kind, value) rule or None) for one path, under RFC 9309 (robots_matcher)."""
    return robots_matcher(rules)(path_and_query)


def robots_first_match(rules, work=None):
    """A function path_and_query -> (allowed, (kind, value) or None) that reads one crawler's rules as Python's
    urllib.robotparser and many older checkers do: in file order, the first rule whose path is a plain prefix of the
    URL's decides, "*" and "$" being ordinary characters there, and a path no rule matches is allowed. An empty
    Disallow, like an empty Allow, allows every path from where it stands, as robotparser reads it. Paths are compared
    in robots_path form, as the RFC 9309 reading compares them, so the two readings differ only in how they choose a
    rule. `work` counts the comparisons, as for robots_matcher."""
    first = {}
    for i, (kind, value) in enumerate(rules):
        if kind in ("allow", "disallow"):
            first.setdefault(robots_path(value), (i, kind == "allow" or not value, kind, value))
    lengths = sorted({len(k) for k in first})

    def allows(pq):
        s = robots_path(pq)
        hit, tried = None, 0
        for n in lengths:
            if n > len(s):
                break
            tried += 1
            c = first.get(s[:n])
            if c and (hit is None or c[0] < hit[0]):
                hit = c
        if work is not None:
            work[0] += tried
        return (True, None) if hit is None else (hit[1], (hit[2], hit[3]))
    return allows


def rule_text(rule):
    """A rule as a report shows it, "Disallow: /pricing", in robots_path form (so no character of it can be markup or a
    control) and at most 120 characters long; None for no rule."""
    if rule is None:
        return None
    return clip("%s: %s" % (rule[0].capitalize(), robots_path(rule[1])), 120)


def shown_url(url):
    """A URL as a report lists it: scheme and host as given, path and query in robots_path form."""
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return robots_path(url)
    return "%s://%s%s" % (u.scheme, robots_path(u.netloc), robots_path(path_and_query(url)))


def host_key(netloc):
    """A host (with its port) as the access observations compare hosts: lower case, and an internationalised name in
    punycode, as scope_of() writes the audited host, so "Bücher.example" and "xn--bcher-kva.example" are one host."""
    netloc = (netloc or "").lower()
    if any(ord(ch) > 127 for ch in netloc):
        try:
            netloc = urllib.parse.urlsplit(idna("http://" + netloc)).netloc.lower()
        except ValueError:
            pass
    return netloc


def url_host(url):
    """host_key() of a URL's host, or None for a URL that does not parse."""
    try:
        return host_key(urllib.parse.urlsplit(url).netloc)
    except ValueError:
        return None


def site_path(url, hosts, scope=""):
    """The URL's path in robots_path form when the URL is on this site and inside `scope`, else None. `hosts` is the
    site's host (host_key form), or the set of them when the homepage redirected to another host: any letter case, the
    Unicode or punycode form of the name, and either scheme match it."""
    hosts = (hosts,) if isinstance(hosts, str) else hosts
    try:
        u = urllib.parse.urlsplit(url)
        netloc = host_key(u.netloc)
    except ValueError:
        return None
    if u.scheme.lower() not in ("http", "https") or netloc not in hosts:
        return None
    path, sc = robots_path(u.path or "/"), robots_path(scope)
    return path if not sc or path == sc or path.startswith(sc + "/") else None


def checked_urls(root, origin, scope, sampled, served, sitemap_locs, hosts=None):
    """The URLs the access observations check, none of them fetched for it: the homepage, each sampled page (as the
    server answered it when it only added or dropped a trailing slash) and the first ROBOTS_PATH_URLS of the sitemap's
    URLs on this site (`hosts`, site_path; the origin's host by default) and inside its path, each once (a trailing
    slash aside). Returns (urls, the sitemap's URLs among them): a URL longer than MAX_URL_CHARS is not checked."""
    host = hosts or (url_host(origin),)
    seen, out, from_sitemap = {}, [], []

    def key(u):
        if len(u) > MAX_URL_CHARS:
            return None
        p = site_path(u, host, scope)
        return None if p is None else (p.rstrip("/") or "/", urllib.parse.urlsplit(u).query)
    for u in [root + "/"] + list(sampled):
        r = served.get(u)
        k = key(u)
        if k is None or k in seen:
            continue
        u = r.url if r is not None and r.url and key(r.url) == k else u
        seen[k] = u
        out.append(u)
    for u in sitemap_locs:
        k = key(u)
        if k is None:
            continue
        if k not in seen:
            seen[k] = u
            out.append(u)
        from_sitemap.append(seen[k])
        if len(from_sitemap) >= ROBOTS_PATH_URLS:
            break
    return out, list(dict.fromkeys(from_sitemap))


def robots_paths(txt, urls):
    """For each URL and each retrieval crawler: does robots.txt `txt` close the page to it, under RFC 9309, and does the
    first-match reading say otherwise? The `access.robots_paths` object of schema/report.v2.json, robots_txt aside:
    counts over every URL checked, and the first ACCESS_LIST_MAX pages of each list. Each crawler reads the group
    robots_rules() picks for it, in both readings. Only the first ROBOTS_PARSE_LIMIT bytes of the file are read, and
    once the readings have made ROBOTS_WORK_MAX comparisons the URLs left are not checked (`not_checked`)."""
    raw = txt.encode("utf-8", "replace")
    if len(raw) > ROBOTS_PARSE_LIMIT:
        txt = raw[:ROBOTS_PARSE_LIMIT].decode("utf-8", "ignore")
    groups = robots_groups(txt)
    readers, crawlers, work = {}, [], [0]
    for name, _ua in RETRIEVAL_UAS:
        rules, whose = robots_rules(groups, name)
        if whose not in readers:
            readers[whose] = (robots_matcher(rules, work), robots_first_match(rules, work))
        crawlers.append((name, whose))
    blocked, differ, done, shapes = [], [], 0, set()
    for u in urls:
        if work[0] >= ROBOTS_WORK_MAX:
            break
        done += 1
        pq = path_and_query(u)
        read = {whose: (rfc(pq), first(pq)) for whose, (rfc, first) in readers.items()}
        by_rule, by_reading = {}, {}
        for name, whose in crawlers:
            (ok, rule), (ok_first, rule_first) = read[whose]
            if not ok:
                by_rule.setdefault(rule_text(rule), []).append(name)
            if ok != ok_first:
                by_reading.setdefault((ok, rule_text(rule), ok_first, rule_text(rule_first)), []).append(name)
        if by_rule:
            blocked.append({"url": shown_url(u), "rules": [{"rule": r, "crawlers": names} for r, names in by_rule.items()]})
            shapes.add(tuple((r, tuple(names)) for r, names in by_rule.items()))
        if by_reading:
            differ.append({"url": shown_url(u), "readings": [
                {"crawlers": names, "rfc9309": {"allowed": a, "rule": ra}, "first_match": {"allowed": b, "rule": rb}}
                for (a, ra, b, rb), names in by_reading.items()]})
    return {"checked": done, "not_checked": len(urls) - done, "crawlers": len(RETRIEVAL_UAS), "blocked": len(blocked),
            "one_rule": len(shapes) == 1 and len(next(iter(shapes))) == 1,
            "pages": blocked[:ACCESS_LIST_MAX], "read_differently": len(differ), "differences": differ[:ACCESS_LIST_MAX]}


def crawler_names(names):
    """Crawler names for one row of a view: "all 10" for every retrieval crawler, "all but Googlebot" for more than
    half of them, else the names."""
    every = [n for n, _ua in RETRIEVAL_UAS]
    if len(names) == len(every):
        return "all %d" % len(every)
    if 2 * len(names) > len(every):
        return "all but " + ", ".join(n for n in every if n not in names)
    return ", ".join(names)


# ── links in the server HTML ──
# A crawler that runs no JavaScript follows only the links the server's HTML carries. Navigation a script writes into
# the page is not among them, and a page reached only through it is found, if at all, through the sitemap.
_UNFOLLOWED = re.compile(r"<(script|style|template)\b", re.I)


def link_html(h):
    """h without its comments and its script, style and template elements: the markup a crawler that runs no
    JavaScript reads links from. A link a script writes is not in it; noscript content is, as markup. An element that
    is never closed hides the rest of the page, as it does in a browser."""
    h = strip_comments(h)
    out, i, low = [], 0, None
    while True:
        m = _UNFOLLOWED.search(h, i)
        if not m:
            out.append(h[i:])
            return "".join(out)
        if low is None:
            low = _lower(h)
        close = "</%s>" % m.group(1).lower()
        end = low.find(close, m.end())
        out.append(h[i:m.start()])
        if end < 0:
            return "".join(out)
        out.append(" ")
        i = end + len(close)


def link_key(url, hosts, scope=""):
    """A page on this site as links name it: its path in robots_path form, without a trailing slash, query or fragment
    ("/" for the root), or None for a URL off the host or outside `scope` (site_path). One rule for the links and the
    pages they are held against, as discover() drops the query and the trailing slash."""
    p = site_path(url, hosts, scope)
    return None if p is None else (p.rstrip("/") or "/")


def page_links(h, base, hosts, scope=""):
    """The pages on this site that one page's server HTML links to, as link_key()s: each <a href> outside comments,
    scripts, styles and templates (link_html), resolved against `base`. A rel=nofollow link counts: a crawler still sees
    it. javascript:, mailto:, tel: and every other scheme but http and https name no page, and the page itself (an empty
    href, a fragment, a self link) is left out."""
    out = set()
    for href, _text in anchors(link_html(h)):
        k = link_key(join_link(base, html.unescape(href).strip()).split("#")[0], hosts, scope)
        if k is not None:
            out.add(k)
    out.discard(link_key(base, hosts, scope))
    return out


def server_links(home, pages, sampled, sitemap_urls, hosts, scope=""):
    """The `access.server_links` object of schema/report.v2.json. `home` is the homepage's (url, Resp) or None when it
    was not fetched; `pages` every fetched page searched, as (url, Resp), the homepage among them; `sampled` the sampled
    URLs; `sitemap_urls` the sitemap URLs the access observations check; `hosts` this site's hosts (site_path): the
    audited host, and the one its homepage redirected to. Each page's links are resolved against the URL it was
    answered from. The homepage is where a crawl starts, so it is never held against the links: `sitemap_urls` counts
    the others. Only these pages are searched, so a URL none of them links to is not shown to be orphaned.
    A link counts wherever on the site it points, whatever `scope` the run was given: a crawler that lands on
    /docs/page follows its link to /pricing as readily as one to /docs/other. (1.7.0 kept only links inside the
    scope, so a run started at one page, example.com/product, read its site navigation as no links at all.) `scope`
    still names the page the run started from when `home` is None."""
    scope_key = robots_path(scope).rstrip("/") or "/"
    scope = ""
    links, seen = [], set()
    for u, r in pages:
        k = link_key(r.url or u, hosts, scope) or link_key(u, hosts, scope)
        if k is None or k in seen:
            continue
        seen.add(k)
        found = page_links(r.text, r.url or u, hosts, scope)
        found.discard(link_key(u, hosts, scope))
        links.append(found)
    reached = set().union(*links) if links else set()
    home_key = (link_key(home[1].url or home[0], hosts) or link_key(home[0], hosts) or scope_key) if home else scope_key
    home_links = page_links(home[1].text, home[1].url or home[0], hosts, scope) - {home_key} if home else None
    others = list(dict.fromkeys(k for k in (link_key(u, hosts, scope) for u in sampled) if k and k != home_key))
    sitemap_urls = [u for u in sitemap_urls if link_key(u, hosts, scope) != home_key]
    unlinked = [u for u in sitemap_urls if link_key(u, hosts, scope) not in reached]
    return {"pages_searched": len(links), "home_links": None if home_links is None else len(home_links),
            "few_home_links": home_links is not None and len(home_links) < FEW_HOME_LINKS,
            "other_sampled": len(others),
            "home_links_to_sampled": None if home_links is None else sum(1 for k in others if k in home_links),
            "sitemap_urls": len(sitemap_urls), "sitemap_urls_linked": len(sitemap_urls) - len(unlinked),
            "unlinked_sitemap_urls": [shown_url(u) for u in unlinked[:ACCESS_LIST_MAX]]}


# ── hreflang annotations ──
# What the fetched pages say about their language and region versions: <link rel="alternate" hreflang="…" href="…"> in
# the server HTML, and the same in an HTTP Link header (RFC 8288). Google's hreflang documentation reads these two from
# a page, and a sitemap as a third way, which is not read here
# (https://developers.google.com/search/docs/specialty/international/localized-versions, last updated 2026-09-21, read
# 2026-10-04). It asks each version to list itself and every other version, and ignores a pair of pages that do not
# both name each other; alternate URLs may be on another domain.
#
# A code is held to the subset of BCP 47 (RFC 5646) that the same page supports: an ISO 639-1 language, optionally an
# ISO 15924 script, optionally an ISO 3166-1 alpha-2 region, or x-default, in any letter case. It names es-419 as not
# supported, and EU, UN and UK as without effect. HREFLANG_LANGS are the 184 two-letter language subtags of the IANA Language
# Subtag Registry (https://www.iana.org/assignments/language-subtag-registry, File-Date 2026-09-17, read 2026-10-04) that
# it does not mark deprecated: the codes of ISO 639-1. HREFLANG_DEPRECATED_LANGS are the six it does (in, iw and ji
# since 1989-01-01, jw since 2001-08-13, mo since 2008-11-22, bh since 2026-06-14): a code with one of them is listed as
# "deprecated", as a deprecated region is listed under "region". HREFLANG_REGIONS are the 249
# officially assigned ISO 3166-1 alpha-2 codes: the registry's two-letter regions without the exceptionally reserved AC,
# CP, CQ, DG, EA, EU, EZ, IC, TA and UN, the private-use AA and ZZ, and the eleven it marks deprecated (AN, BU, CS, DD,
# FX, NT, SU, TP, YD, YU, ZR); the same 249 as tzdata's iso3166.tab. A script is checked for its form only.
HREFLANG_LANGS = frozenset(
    "aa ab ae af ak am an ar as av ay az ba be bg bi bm bn bo br bs ca ce ch co cr cs cu cv cy da de dv dz ee el "
    "en eo es et eu fa ff fi fj fo fr fy ga gd gl gn gu gv ha he hi ho hr ht hu hy hz ia id ie ig ii ik io is it "
    "iu ja jv ka kg ki kj kk kl km kn ko kr ks ku kv kw ky la lb lg li ln lo lt lu lv mg mh mi mk ml mn "
    "mr ms mt my na nb nd ne ng nl nn no nr nv ny oc oj om or os pa pi pl ps pt qu rm rn ro ru rw sa sc sd se sg sh "
    "si sk sl sm sn so sq sr ss st su sv sw ta te tg th ti tk tl tn to tr ts tt tw ty ug uk ur uz ve vi vo wa wo xh "
    "yi yo za zh zu".split())
HREFLANG_DEPRECATED_LANGS = frozenset("bh in iw ji jw mo".split())
HREFLANG_REGIONS = frozenset(
    "AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ "
    "CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO "
    "FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE "
    "JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO "
    "MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW "
    "PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM "
    "TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW".split())
# language, then an optional script, then an optional region (two letters, or a UN M.49 area's three digits)
_HREFLANG_FORM = re.compile(r"([A-Za-z]{2,3})(?:-([A-Za-z]{4}))?(?:-([A-Za-z]{2}|[0-9]{3}))?\Z")
HREFLANG_PROBLEMS = {"form": "not language[-Script][-REGION]", "language": "not an ISO 639-1 language",
                     "deprecated": "a language subtag the IANA registry marks deprecated",
                     "region": "not an assigned ISO 3166-1 alpha-2 region"}
HREFLANG_URLS_SHOWN = 10    # URLs the JSON lists for one code that names several on a page
# annotations read on one page, at most; the rest are counted (not_read). Each is resolved as a URL, so a page of 100,000
# would take seconds, and no real page carries a thousand
HREFLANG_PAGE_MAX = 1000
_LINK_TAG = re.compile(r"<link(?=[\s/>])", re.I)
# the rest of a tag after its name, up to the ">" that closes it. A ">" inside a quoted attribute value does not close
# it, as in a browser (href="/?a>b", title="EN > US"); a value starts after "=", so a quote anywhere else is an ordinary
# character. Read in one pass: a quoted value is scanned once, to its closing quote
_TAG_REST = re.compile(r"""(?:[^>=]+|=\s*(?:"[^"]*"|'[^']*'|[^\s>]*))*""")
# where a page's head has ended at the latest: its </head>, or its <body> tag
_HEAD_END = re.compile(r"</head(?![^\s/>])|<body(?![^\s/>])", re.I)
# one attribute of a tag: name, then a value in double quotes, single quotes or none. A quote never closed runs to the
# end of the tag's text, so no value is read twice and a tag is read in one pass
_TAG_ATTR = re.compile(r"""([^\s"'<>/=]+)(?:\s*=\s*(?:"([^"]*)(?:"|\Z)|'([^']*)(?:'|\Z)|([^\s>]+)))?""")
# one parameter of a Link header's link-value (RFC 8288 section 3): ;name, ;name=token or ;name="quoted", a quoted
# string holding backslash-escaped characters (RFC 9110 section 5.6.4: title="a \" b")
_LINK_PARAM = re.compile(r"""\s*;\s*([^\s=;,<]+)\s*(?:=\s*(?:"((?:[^"\\]|\\.)*)(?:"|\\?\Z)|([^\s;,<]*)))?""", re.S)
_QUOTED_PAIR = re.compile(r"\\(.)", re.S)
_ABSOLUTE = re.compile(r"https?://", re.I)


def hreflang_problem(code):
    """None for a code the subset of BCP 47 above holds (x-default included), else why not: "form" (not
    language[-Script][-REGION]), "language" (no ISO 639-1 code), "deprecated" (a language subtag the IANA registry
    marks deprecated, such as iw) or "region" (no officially assigned ISO 3166-1 alpha-2 code). Letter case and
    surrounding white space do not matter."""
    c = code.strip()
    if c.lower() == "x-default":
        return None
    m = _HREFLANG_FORM.match(c)
    if not m:
        return "form"
    lang = m.group(1).lower()
    if lang in HREFLANG_DEPRECATED_LANGS:
        return "deprecated"
    if lang not in HREFLANG_LANGS:
        return "language"
    if m.group(3) and m.group(3).upper() not in HREFLANG_REGIONS:
        return "region"
    return None


def tag_attrs(tag):
    """The attributes in one tag's text (after its name, up to its ">"): names in lower case, values with their
    character references decoded. A name given twice keeps its first value, as a browser does."""
    out = {}
    for m in _TAG_ATTR.finditer(tag):
        k = m.group(1).lower()
        if k not in out:
            v = next((g for g in m.groups()[1:] if g is not None), "")
            out[k] = html.unescape(v)
    return out


def link_header_alternates(value):
    """(href as written, hreflang) of each link-value in an HTTP Link header (RFC 8288) whose rel names "alternate" and
    that carries an hreflang parameter, in order, in one pass."""
    out, i = [], 0
    while True:
        a = value.find("<", i)
        b = value.find(">", a + 1) if a >= 0 else -1
        if b < 0:
            return out
        params, i = {}, b + 1
        while True:
            p = _LINK_PARAM.match(value, i)
            if not p or p.end() == i:
                break
            q = p.group(2)
            params.setdefault(p.group(1).lower(), _QUOTED_PAIR.sub(r"\1", q) if q is not None else p.group(3) or "")
            i = p.end()
        if "alternate" in params.get("rel", "").lower().split() and "hreflang" in params:
            out.append((value[a + 1:b].strip(), params["hreflang"]))


def page_hreflang(r):
    """The hreflang annotations of one fetched page, as (code, href, source): each <link> whose rel names "alternate"
    and that has an hreflang and an href, outside comments, scripts, styles and templates (link_html), in document
    order (source "html", or "body" for one after the page's </head> or <body> tag: Google's hreflang documentation
    reads the <link> tags inside the head), then each one in the response's Link header (source "header"). A link whose
    type names something other than HTML, as a feed's does, announces no language version of the page."""
    out, h = [], link_html(r.text)
    end = _HEAD_END.search(h)
    head_end = end.start() if end else len(h)
    i = 0
    while True:
        m = _LINK_TAG.search(h, i)
        if not m:
            break
        gt = _TAG_REST.match(h, m.end()).end()
        attrs = tag_attrs(h[m.end():gt])
        if "alternate" in attrs.get("rel", "").lower().split() and "hreflang" in attrs and "href" in attrs \
                and "html" in (attrs.get("type") or "html").lower():
            out.append((attrs["hreflang"], attrs["href"].strip(), "html" if m.start() < head_end else "body"))
        if gt >= len(h):
            break
        i = gt + 1
    return out + [(code, href, "header") for href, code in link_header_alternates(r.headers.get("link", ""))]


def alt_host(netloc, scheme=""):
    """host_key() of a URL's host as hreflang annotations are compared: without a trailing dot on the name, nor the
    scheme's default port (80 for http, 443 for https; either one for a host given without its scheme), so
    "https://x.test.:443/" names the host "https://x.test/" does. Any other port stays."""
    user, at, h = host_key(netloc).rpartition("@")
    i = h.rfind(":")
    name, port = (h[:i], h[i + 1:]) if i > h.rfind("]") else (h, None)
    if name.endswith("."):
        name = name[:-1]
    if port is not None and port in {"http": ("", "80"), "https": ("", "443")}.get(scheme.lower(), ("", "80", "443")):
        port = None
    return user + at + name + ("" if port is None else ":" + port)


def alt_key(url):
    """A page as hreflang annotations name it, to tell whether two URLs are one page: its host (alt_host), its path in
    robots_path form without a trailing slash, and its query; the scheme and the fragment do not matter. None for a URL
    that is not an http or https URL with a host."""
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    if u.scheme.lower() not in ("http", "https") or not u.netloc:
        return None
    return alt_host(u.netloc, u.scheme), robots_path(u.path or "/").rstrip("/") or "/", robots_path(u.query)


def shown_code(code):
    """An hreflang value as a report lists it: in robots_path form, so no space, control or bidi character and no `
    or | reaches a view, cut at 64 characters."""
    return clip(robots_path(code.strip()), 64)


def hreflang(pages, hosts):
    """The `access.hreflang` object of schema/report.v2.json. `pages` every fetched page searched, as (url, Resp): the
    homepage, the sampled pages and the section indexes, each once; `hosts` this site's hosts (site_path): the audited
    host, and the one its homepage redirected to. Each page's annotations resolve against the URL it was answered from.
    Return links are checked only between these pages: an annotation naming a page the run did not fetch counts in
    targets_not_fetched, and its return link is not checked. Only the first HREFLANG_PAGE_MAX annotations of a page are
    read; the rest are counted in not_read. Counts cover every page; lists hold the first ACCESS_LIST_MAX."""
    hosts = {alt_host(x) for x in ((hosts,) if isinstance(hosts, str) else hosts)}
    recs, seen, not_read = [], set(), 0
    for u, r in pages:
        own = {k for k in (alt_key(u), alt_key(r.url or u)) if k}
        if not own or own & seen:
            continue
        seen |= own
        base = r.url or u
        anns, found = [], page_hreflang(r)
        not_read += max(0, len(found) - HREFLANG_PAGE_MAX)
        for code, href, src in found[:HREFLANG_PAGE_MAX]:
            target = join_link(base, href).split("#")[0]
            anns.append((code, href, src, target, alt_key(target)))
        recs.append((shown_url(base), own, anns))
    by_key = {}
    for i, (_url, own, _anns) in enumerate(recs):
        for k in own:
            by_key.setdefault(k, i)
    lists = {k: [] for k in ("pages", "outside_head", "no_self", "invalid", "duplicates", "not_absolute", "other_host")}
    counts = dict.fromkeys(lists, 0)

    def add(name, item):
        counts[name] += 1
        if len(lists[name]) < ACCESS_LIST_MAX:
            lists[name].append(item)
    names, not_fetched, total, in_header, header_anns = [], set(), 0, 0, 0
    for i, (url, own, anns) in enumerate(recs):
        named = set()
        names.append(named)
        if not anns:
            continue
        total += len(anns)
        hdr = sum(1 for a in anns if a[2] == "header")
        header_anns += hdr
        in_header += hdr > 0
        add("pages", {"url": url, "annotations": len(anns)})
        after = sum(1 for a in anns if a[2] == "body")
        if after:
            add("outside_head", {"url": url, "annotations": after})
        if not any(a[4] in own for a in anns):
            add("no_self", url)
        bad, codes, written, other = set(), {}, set(), set()
        for code, href, _src, target, key in anns:
            c = code.strip().lower()
            why = hreflang_problem(code)
            if why and c not in bad:
                bad.add(c)
                add("invalid", {"url": url, "hreflang": shown_code(code), "problem": why})
            codes.setdefault(c, (code, {}))[1].setdefault(key or target, target)
            if not _ABSOLUTE.match(href) and href not in written:
                written.add(href)
                add("not_absolute", {"url": url, "href": clip(robots_path(href), MAX_URL_CHARS)})
            if key and key[0] not in hosts and key not in other:
                other.add(key)
                add("other_host", {"url": url, "href": clip(shown_url(target), MAX_URL_CHARS)})
            if key and key not in own:
                j = by_key.get(key)
                if j is None:
                    not_fetched.add(key)
                elif j != i:
                    named.add(j)
        for code, targets in codes.values():
            if len(targets) > 1:
                add("duplicates", {"url": url, "hreflang": shown_code(code), "urls": len(targets),
                                   "hrefs": [clip(shown_url(t), MAX_URL_CHARS)
                                             for t in list(targets.values())[:HREFLANG_URLS_SHOWN]]})
    # a pair of fetched pages, one naming the other: one-way unless the other names it back
    pairs, one_way = set(), []
    for i, named in enumerate(names):
        for j in sorted(named):
            if (min(i, j), max(i, j)) in pairs:
                continue
            pairs.add((min(i, j), max(i, j)))
            if i not in names[j]:
                one_way.append({"from": recs[i][0], "to": recs[j][0]})
    return {"pages_searched": len(recs), "pages_with_hreflang": counts["pages"], "annotations": total,
            "pages_with_link_header": in_header, "annotations_in_link_header": header_anns, "pages": lists["pages"],
            "outside_head": counts["outside_head"], "outside_head_pages": lists["outside_head"],
            "no_self_reference": counts["no_self"], "no_self_reference_pages": lists["no_self"],
            "invalid_codes": counts["invalid"], "invalid": lists["invalid"],
            "duplicate_codes": counts["duplicates"], "duplicates": lists["duplicates"],
            "not_absolute": counts["not_absolute"], "not_absolute_hrefs": lists["not_absolute"],
            "other_host": counts["other_host"], "other_host_hrefs": lists["other_host"],
            "pairs_checked": len(pairs), "one_way": len(one_way), "one_way_pairs": one_way[:ACCESS_LIST_MAX],
            "targets_not_fetched": len(not_fetched), "not_read": not_read}


def shown_origin(root):
    """The scheme and host of a report's target, as shown_url() writes them, so a view can list a page by its path."""
    try:
        u = urllib.parse.urlsplit(root)
    except ValueError:
        return None
    return "%s://%s" % (u.scheme, robots_path(u.netloc))


def access_lines(access, fmt="text", origin=None, start=None):
    """The observations outside the score (schema/report.v2.json, `access`) as lines of plain text or Markdown, the
    same in every view: what they found, and at most ACCESS_ROWS pages of each list. `origin` shortens a URL on it to
    its path; `start` is the URL the run started from, so a run given one page calls that page what it is rather than
    "the homepage". Never part of the score."""
    if not access:
        return []
    md = fmt == "md"
    # the site's own text, a page's path or a robots.txt pattern, is data: a code span in Markdown and a «site text: …»
    # fence in plain text, as evidence quotes it, cut at 120 characters. ("Disallow:" is the tool's word, not the site's)
    quote = (lambda s: "`%s`" % clip(s, 120)) if md else (lambda s: site_text(s, 120))
    page = lambda u: quote(u[len(origin):] if origin and u.startswith(origin + "/") else u)

    def code(rule):
        if md:
            return quote(rule)
        kind, sep, value = rule.partition(": ")
        return "%s: %s" % (kind, quote(value)) if sep else quote(rule)
    out = []
    rp = access.get("robots_paths")
    if rp:
        n, state = rp["checked"], rp.get("robots_txt")
        if state == "unreadable":
            out.append("Pages robots.txt blocks: not observed, because robots.txt could not be read.")
        elif state == "absent":
            out.append("robots.txt blocks none of the %d checked pages: the site has no robots.txt." % n)
        elif not rp["blocked"] and not rp["read_differently"]:
            out.append("robots.txt blocks none of the %d checked pages for any retrieval crawler, and RFC 9309 and a "
                       "first-match reading agree on every one of them." % n)
        elif rp["blocked"] == n and not rp["read_differently"] and rp.get("one_rule"):
            # one rule closes every page to the same crawlers, as a whole-site Disallow does: one line, not a row a page
            r = rp["pages"][0]["rules"][0]
            who = crawler_names(r["crawlers"])
            out.append("robots.txt blocks all %d checked pages for %s%s, by %s." % (
                n, who, " retrieval crawlers" if who.startswith("all ") and who[4:].isdigit() else "", code(r["rule"])))
        else:
            out.append("robots.txt blocks %d of the %d checked pages for at least one retrieval crawler (RFC 9309: the "
                       "longest matching rule decides):" % (rp["blocked"], n) if rp["blocked"] else
                       "robots.txt blocks none of the %d checked pages for any retrieval crawler under RFC 9309 (the "
                       "longest matching rule decides)." % n)
            if rp["blocked"]:
                out += _table(("Page", "Crawlers", "Rule"),
                              [[(page(p["url"]), crawler_names(r["crawlers"]), code(r["rule"])) for r in p["rules"]]
                               for p in rp["pages"]], rp["blocked"], md)
            if rp["read_differently"]:
                out.append("Rules read differently: on %d of the %d checked pages, RFC 9309 and the first-match reading "
                           "of urllib.robotparser and many older checkers (rules in file order, the first plain prefix "
                           "decides) disagree:" % (rp["read_differently"], n))

                def reading(r):
                    word = "allowed" if r["allowed"] else "blocked"
                    return "%s by %s" % (word, code(r["rule"])) if r["rule"] else word + ", no rule matches"
                out += _table(("Page", "Crawlers", "RFC 9309", "First match"),
                              [[(page(p["url"]), crawler_names(r["crawlers"]), reading(r["rfc9309"]),
                                 reading(r["first_match"])) for r in p["readings"]] for p in rp["differences"]],
                              rp["read_differently"], md)
        if rp.get("not_checked"):
            k = rp["not_checked"]
            out.append("%d more page%s not checked against robots.txt: its rules are so many that matching them stopped "
                       "after %d comparisons, to keep the run short." % (k, " was" if k == 1 else "s were",
                                                                         ROBOTS_WORK_MAX))
    sl = access.get("server_links")
    if sl:
        n = sl["home_links"]
        # a run given one page starts there, not at the homepage
        at_root = not start or urllib.parse.urlsplit(start).path in ("", "/")
        first = "the homepage" if at_root else "the page the run started from"
        whose = "The homepage's server HTML" if at_root else "The server HTML of %s, %s," % (page(start.rstrip("/")), first)
        # links count anywhere on the host (server_links): under a path, that is more than the site the run was given
        on = "this site" if at_root else "this host"
        if n is None:
            out.append("Links in the server HTML: %s was not fetched this run, so its links were not read." % first)
        elif sl["few_home_links"]:
            out.append(whose + (" links to %d page%s on %s (fewer than %d): navigation that appears only after "
                                "JavaScript runs cannot be followed by crawlers that do not run it. It links to %d of the "
                                "%d other sampled pages." % (n, "" if n == 1 else "s", on, FEW_HOME_LINKS,
                                                             sl["home_links_to_sampled"], sl["other_sampled"])))
        else:
            out.append(whose + " links to %d pages on %s" % (n, on) + (
                ", %d of the %d other sampled pages among them." % (sl["home_links_to_sampled"], sl["other_sampled"])
                if sl["other_sampled"] else "."))
        m, searched = sl["sitemap_urls"], sl["pages_searched"]
        where = "%d fetched page%s" % (searched, "" if searched == 1 else "s")
        if not m:
            out.append("No sitemap URL was checked for links: the run read no sitemap, or it lists no page on this site.")
        elif sl["sitemap_urls_linked"] == m:
            out.append("All %d checked sitemap URLs are linked from the server HTML of at least one of the %s."
                       % (m, where))
        else:
            out.append("%d of the %d checked sitemap URLs are linked from the server HTML of at least one of the %s "
                       "(%s, the sampled pages and the section indexes). Only those pages were searched, so "
                       "a URL they do not link to is not necessarily orphaned. Not linked from them:"
                       % (sl["sitemap_urls_linked"], m, where, first))
            out += _table(("Page",), [[(page(u),)] for u in sl["unlinked_sitemap_urls"]],
                          m - sl["sitemap_urls_linked"], md)
    hl = access.get("hreflang")
    if hl:
        out += _hreflang_lines(hl, md, quote, page)
    if md:
        # each sentence its own paragraph: Markdown joins lines that no blank line parts, except a table's rows
        spaced = []
        for ln in out:
            if spaced and ln and spaced[-1] and not (ln.startswith("|") and spaced[-1].startswith("|")):
                spaced.append("")
            spaced.append(ln)
        out = spaced
    return out


def _hreflang_lines(hl, md, quote, page):
    """access_lines() for `access.hreflang`: what the fetched pages' annotations say, as found. `quote` and `page` fence
    the site's text as the rest of the section does."""
    n, k = hl["pages_searched"], hl["pages_with_hreflang"]
    if not n:
        return ["hreflang: no page was fetched this run, so no annotation was read."]
    where = "%d fetched page%s" % (n, "" if n == 1 else "s")
    if not k:
        return ["No hreflang annotations on the %s (link elements in the server HTML, or an HTTP Link header)." % where]
    hdr, a, ha = hl["pages_with_link_header"], hl["annotations"], hl["annotations_in_link_header"]
    # how many of the annotations came in a Link header: a page can carry some in its HTML and some there
    in_hdr = "all of them" if ha == a else "%d of them" % ha
    if n == 1:
        first = "hreflang annotations: the 1 fetched page carries %d%s." % (
            a, "" if not ha else ", in an HTTP Link header" if ha == a else ", %s in an HTTP Link header" % in_hdr)
    else:
        first = "hreflang annotations: %d of the %s carr%s them, %d in all%s." % (
            k, where, "ies" if k == 1 else "y", a, "" if not hdr else "; %d page%s carr%s %s in an HTTP Link header"
            % (hdr, "" if hdr == 1 else "s", "ies" if hdr == 1 else "y", in_hdr))
    out = [first]
    tag = (lambda t: "`%s`" % t) if md else (lambda t: t)
    m = hl["outside_head"]
    if m:
        out.append("%s after the end of %s head (after %s or the %s tag in the server HTML). Google's hreflang "
                   "documentation says the %s tags must be inside a well-formed %s section; they are counted here "
                   "with the others:" % (
                       "It carries annotations" if k == 1 else "%d of the %d pages with annotations carr%s some" % (
                           m, k, "ies" if m == 1 else "y"), "its" if k == 1 else "the", tag("</head>"), tag("<body>"),
                       tag("<link>"), tag("<head>")))
        out += _table(("Page", "After the head"), [[(page(x["url"]), str(x["annotations"]))]
                                                   for x in hl["outside_head_pages"]], m, md)
    m = hl["no_self_reference"]
    if m:
        out.append("It does not list itself among its own annotations:" if k == 1 else
                   "%d of the %d pages with annotations %s not list %s among %s own annotations:" % (
                       m, k, "does" if m == 1 else "do", "itself" if m == 1 else "themselves",
                       "its" if m == 1 else "their"))
        out += _table(("Page",), [[(page(u),)] for u in hl["no_self_reference_pages"]], m, md)
    else:
        out.append("Each page with annotations lists itself among its own annotations." if k > 1 else
                   "It lists itself among its own annotations.")
    m = hl["invalid_codes"]
    if m:
        out.append("%d code%s outside the subset of BCP 47 that Google's hreflang documentation supports (an ISO "
                   "639-1 language, optionally an ISO 15924 script and an assigned ISO 3166-1 alpha-2 region, or "
                   "x-default):"
                   % (m, " is" if m == 1 else "s are"))
        out += _table(("Page", "Code", "Why"), [[(page(x["url"]), quote(x["hreflang"]), HREFLANG_PROBLEMS[x["problem"]])]
                                                for x in hl["invalid"]], m, md, "code")
    m = hl["duplicate_codes"]
    if m:
        out.append("%d code%s more than one URL on the same page:" % (m, " names" if m == 1 else "s name"))

        def urls(x):
            shown = [page(u) for u in x["hrefs"][:3]]
            return ", ".join(shown) + (" and %d more" % (x["urls"] - 3) if x["urls"] > 3 else "")
        out += _table(("Page", "Code", "URLs"), [[(page(x["url"]), quote(x["hreflang"]), urls(x))]
                                                 for x in hl["duplicates"]], m, md, "code")
    m = hl["not_absolute"]
    if m:
        out.append("%d URL%s the annotations name %s not absolute (a relative path, no scheme, or a scheme other than "
                   "http and https), each counted once a page, as written:" % (m, "" if m == 1 else "s",
                                                                                "is" if m == 1 else "are"))
        out += _table(("Page", "As written"), [[(page(x["url"]), quote(x["href"]))] for x in hl["not_absolute_hrefs"]],
                      m, md, "URL")
    m = hl["other_host"]
    if m:
        out.append("%d URL%s the annotations name %s on another host, which hreflang allows, each counted once a page:"
                   % (m, "" if m == 1 else "s", "is" if m == 1 else "are"))
        out += _table(("Page", "URL"), [[(page(x["url"]), page(x["href"]))] for x in hl["other_host_hrefs"]],
                      m, md, "URL")
    pc, ow, nf = hl["pairs_checked"], hl["one_way"], hl["targets_not_fetched"]
    if not pc and not nf:
        out.append("The annotations name no page but their own, so there is no return link to check.")
    elif not pc:
        out.append("Return links are checked only between the pages this run fetched, and %s, so none was checked." % (
            "the one other URL the annotations name was not fetched" if nf == 1 else
            "none of the %d other URLs the annotations name was fetched" % nf))
    else:
        if ow:
            out.append("Return links, checked only between the pages this run fetched: %d of the %d pair%s in which "
                       "one page names the other %s one-way (the first page names the second, which does not name it "
                       "back):" % (ow, pc, "" if pc == 1 else "s", "is" if ow == 1 else "are"))
            out += _table(("Page", "Names, not named back by"), [[(page(x["from"]), page(x["to"]))]
                                                                  for x in hl["one_way_pairs"]], ow, md, "pair")
        else:
            out.append("Return links, checked only between the pages this run fetched: in %s %d pair%s in which one "
                       "page names the other, each names the other." % ("the" if pc == 1 else "all", pc,
                                                                         "" if pc == 1 else "s"))
        if nf:
            out.append("%d other URL%s the annotations name %s not fetched this run, so %s return link%s %s not "
                       "checked." % (nf, "" if nf == 1 else "s", "was" if nf == 1 else "were", "its" if nf == 1 else
                                     "their", "" if nf == 1 else "s", "was" if nf == 1 else "were"))
    if hl.get("not_read"):
        k = hl["not_read"]
        out.append("%d more annotation%s not read: a page's first %d are read, and the counts cover those." % (
            k, " was" if k == 1 else "s were", HREFLANG_PAGE_MAX))
    return out


def _table(head, pages, total, md, unit="page"):
    """The rows of the first ACCESS_ROWS pages (each page a list of rows), as a Markdown table or indented text, and a
    line saying how many of the `total` pages (or other `unit`s: codes, annotations, pairs) are not shown."""
    rows = [r for p in pages[:ACCESS_ROWS] for r in p]
    if md:
        out = ["", "| %s |" % " | ".join(head), "|" + "---|" * len(head)] + ["| %s |" % " | ".join(r) for r in rows]
    else:
        w = [min(48, max(len(r[i]) for r in rows)) for i in range(len(head))]
        out = ["  " + "  ".join(c.ljust(w[i]) for i, c in enumerate(r)).rstrip() for r in rows]
    rest = total - min(len(pages), ACCESS_ROWS)
    if md:
        out.append("")      # a line right under a Markdown table would be read as another row
    if rest:
        out.append("%s%d more %s%s; the JSON report lists the first %d." % (
            "" if md else "  ", rest, unit, "" if rest == 1 else "s", ACCESS_LIST_MAX))
    return out


def clip(s, n):
    """Cut text for display without cutting a «site text: …» fence open: a quote that loses its closing »
    would let whatever follows read as the tool's own words."""
    s = str(s or "")
    if len(s) <= n:
        return s
    out = s[:n - 1] + "…"
    return out + "»" if out.rfind("«") > out.rfind("»") else out

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

def under_cn(url):
    """True when the URL's host is under the .cn country domain (example.cn, example.com.cn). A substring test read
    www.cnn.com and www.cnbc.com as Chinese sites."""
    try:
        host = (urllib.parse.urlsplit(url).hostname or "").rstrip(".")
    except ValueError:
        return False
    return host.endswith(".cn")

# A sampled page is a document a person reads. Files (feeds, Markdown, JSON, archives, media) that sitemaps and
# links also list are not; listing pages (pagination, category, tag, author, series and archive pages) carry
# navigation and excerpts, not prose, so they are drawn only when nothing else is left
NOT_A_PAGE = re.compile(r"\.(png|jpe?g|gif|svg|webp|avif|ico|css|js|mjs|json|xml|rss|atom|txt|md|csv|pdf|zip|gz|"
                        r"tgz|docx?|xlsx?|pptx?|woff2?|ttf|mp3|mp4|webm|mov)$", re.I)
LISTING = re.compile(r"/(page|p)/\d+$|/(category|categories|tag|tags|author|authors|series|archives?)(/|$)|/feed$", re.I)


# the section indexes discover() reads for links to recent pages; the access observations search them for links too
SECTION_INDEXES = ("/blog", "/news", "/posts", "/articles", "/insights", "/resources", "/docs", "/learn")


def page_candidate(u):
    """0 for a content page, 1 for a listing page, None for a file that is not a page at all."""
    path = urllib.parse.urlsplit(u).path
    if NOT_A_PAGE.search(path):
        return None
    return 1 if LISTING.search(path.rstrip("/")) else 0


def discover(base, want=8, verbose=False, *, memo=None, timeout=None, deadline=None):
    """Pick pages the way a retrieval crawler would meet them: real leaf pages, not
    section indexes. Index pages carry navigation, not prose, and every content check
    depends on the sample being representative."""
    origin, scope = scope_of(base)
    root = origin + scope
    host = urllib.parse.urlsplit(origin).netloc
    scheme = urllib.parse.urlsplit(origin).scheme
    steady = lambda u: fetch_steady(u, memo=memo, timeout=timeout, deadline=deadline)
    home = steady(root + "/")
    if home.status == 0:
        # no answer at all: every other request to this host would meet the same fault after its own retries,
        # which made a mistyped or dead host take minutes to report
        raise fetch_failure(base, [home], timeout)
    pool, seen = [], {root + "/", root}

    def same_site(u):
        """The URL on this site and inside its path, with the site's scheme, or None. One rule for links,
        sitemap entries and pin_urls(), so a report's sampled_urls can always be pinned again."""
        try:
            pu = urllib.parse.urlsplit(u)
        except ValueError:
            return None
        if pu.netloc != host or pu.scheme not in ("http", "https") or _UNSAFE.search(u):
            return None
        if scope and not (pu.path == scope or pu.path.startswith(scope + "/")):
            return None
        return pu._replace(scheme=scheme).geturl() if pu.scheme != scheme else u

    def harvest(text, origin):
        out = []
        for m in in_tags(_A_HREF, _A, text):
            u = same_site(join_link(origin, m.group(1)).split("#")[0].split("?")[0].rstrip("/"))
            if not u: continue
            if page_candidate(u) is None: continue
            if re.search(r"/(login|signin|signup|register|cart|checkout|account|admin|search)(/|$)", u, re.I): continue
            if u in seen: continue
            seen.add(u); out.append(u)
        return out

    pool += harvest(home.text, root + "/")

    # sitemap gives real content URLs, which a homepage nav often does not
    rb = steady(origin + "/robots.txt")
    # the same places run() looks for p1.sitemap, including the given path, so a sitemap that is scored
    # is also the one the sample comes from
    # a relative Sitemap: line is invalid but common; resolve it against the origin
    sm_urls = [join_link(origin + "/", u) for u in _SITEMAP_DECL.findall(rb.text if rb.ok else "")] \
              or [origin + "/sitemap.xml", origin + "/sitemap_index.xml"] \
              + ([origin + scope + "/sitemap.xml"] if scope else [])
    sm = next((r for r in pmap(steady, sm_urls[:3]) if is_sitemap(r)), None)
    if sm and re.search(r"<sitemapindex", sm.text, re.I):
        kids = [join_link(sm.url, x.strip()) for x in re.findall(r"<loc>\s*([^<]+)", sm.text)][:2]
        got = [r for r in pmap(steady, kids) if is_sitemap(r)]
        sm = got[0] if got else None
    if sm:
        locs = [x.strip() for x in re.findall(r"<loc>\s*([^<]+)", sm.text)]
        for u in locs[:600]:
            u = same_site(u.split("#")[0].split("?")[0].rstrip("/"))
            if u and u not in seen and page_candidate(u) is not None:
                seen.add(u); pool.append(u)

    # section indexes are where recent posts actually live
    idx = [root + p for p in SECTION_INDEXES]
    for r in pmap(steady, idx):
        if r.ok and r.body: pool += harvest(r.text, r.url)

    depth = lambda u: urllib.parse.urlsplit(u).path.strip("/").count("/")
    def leafy(pats, n, min_depth=1):
        got = sorted([u for u in pool if re.search(pats, u, re.I) and depth(u) >= min_depth and not page_candidate(u)],
                     key=lambda u: (-depth(u), len(u)))[:n]
        for u in got: pool.remove(u)
        return got

    urls = [root + "/"]
    urls += leafy(r"/(blog|news|posts?|articles?|insights?|changelog|release)/", 3)
    urls += leafy(r"/(docs?|guide|learn|tutorial|reference|api|help|kb|handbook)/", 2)
    urls += leafy(r"/(product|pricing|features?|solutions?|services?|platform|use-cases?)", 2, 0)
    if len(urls) < want:                              # anything left, deepest first
        rest = sorted(pool, key=lambda u: (page_candidate(u) or 0, -depth(u), len(u)))   # listings last
        for u in rest:
            if len(urls) >= want: break
            if u not in urls: urls.append(u)
    # say where the sample came from, so two runs with different pages can be explained
    source = "sitemap" if sm else "homepage and section links (no sitemap reachable)"
    return urls[:want], source

# ── checks ─────────────────────────────────────────────────────────────────
MAX_PINNED = 8

def pin_urls(base, urls, limit=None):
    """--urls / --urls-from: score exactly these pages instead of drawing a sample.
    Sampling is the main source of run-to-run variance; a pinned re-score removes it.
    Every page must be on the scheme, host and path being scored, or the checks
    would describe a different site under this one's name."""
    origin, scope = scope_of(idna(base if "://" in base else "https://" + base))
    want = urllib.parse.urlsplit(origin)
    out, keys = [], set()
    for raw in urls:
        u = raw.strip()
        if not u:
            continue
        if "://" not in u:
            u = origin + ("" if u.startswith("/") else "/") + u
        if _UNSAFE.search(u):
            raise RuntimeError("pinned URL %r contains control or bidi characters" % raw.strip()[:200])
        u = idna(u.split("#")[0])
        try:
            p = urllib.parse.urlsplit(u)
        except ValueError:
            raise RuntimeError("pinned URL %s is not a valid URL" % raw.strip()[:200]) from None
        if (p.scheme, p.netloc.lower()) != (want.scheme, want.netloc.lower()):
            raise RuntimeError("pinned URL %s is not on %s; every pinned page must be on the site being scored"
                               % (raw.strip()[:200], origin))
        if scope and not (p.path == scope or p.path.startswith(scope + "/")):
            raise RuntimeError("pinned URL %s is outside %s%s" % (raw.strip()[:200], origin, scope))
        key = (p.netloc.lower(), p.path.rstrip("/") or "/", p.query)
        if key not in keys:
            keys.add(key); out.append(u)
    if not out:
        raise RuntimeError("no URLs to pin: the list is empty")
    cap = max(MAX_PINNED, limit or 0)
    if len(out) > cap:
        raise RuntimeError("%d URLs to pin; the rubric samples at most %d pages" % (len(out), cap))
    return out

def read_url_list(path):
    """--urls FILE: one URL per line; blank lines and # comments are ignored."""
    try:
        with io.open(path, encoding="utf-8-sig") as f:
            return [ln.split("#", 1)[0].strip() for ln in f if ln.split("#", 1)[0].strip()]
    except OSError as e:
        raise RuntimeError("cannot read --urls %s: %s" % (path, e.strerror or e)) from None
    except UnicodeDecodeError:
        raise RuntimeError("--urls %s is not UTF-8 text: save it as UTF-8, one URL per line" % path) from None

def read_report_urls(path):
    """--urls-from REPORT.json: the sampled_urls of an earlier report, so a re-score reads the same pages."""
    try:
        with io.open(path, encoding="utf-8") as f:
            d = json.load(f)
    except OSError as e:
        raise RuntimeError("cannot read --urls-from %s: %s" % (path, e.strerror or e)) from None
    except ValueError:
        raise RuntimeError("--urls-from %s is not JSON; pass a report written by --json or --json-out" % path) from None
    urls = d.get("sampled_urls") if isinstance(d, dict) else None
    if not isinstance(urls, list) or not all(isinstance(u, str) for u in urls):
        raise RuntimeError("--urls-from %s has no sampled_urls list; pass a report written by --json or --json-out" % path)
    return urls

def run(base, sample=8, verbose=False, urls=None, *, timeout=None):
    """Score one site. `timeout` is the wait per request (default TIMEOUT, which --timeout sets). The run takes
    at most RUN_DEADLINE seconds: after that no request is sent, and the checks that still needed one are not
    observed; when no sampled page came back by then it raises ScoreError (kind "deadline")."""
    if not urls and not (isinstance(sample, int) and sample >= 1):
        # an empty sample has nothing to score, and no fetch failed to say why
        raise ValueError("sample must be a whole number of pages, 1 or more, got %r" % (sample,))
    timeout = timeout or TIMEOUT
    started = time.monotonic()
    deadline = started + RUN_DEADLINE
    if PREFLIGHT:
        preflight_host(base)
    origin, scope = scope_of(base)
    root = origin + scope
    ev, tier = {}, {}
    def say(msg):
        if verbose: print("%s  %s%s" % (c.dim, msg, c.r), file=sys.stderr)

    # every request goes through this run's memo, so none is sent twice: the ones that decide the sample or a
    # gate are retried (steady), the rest are asked once (get)
    memo = FetchMemo()
    steady = lambda u: fetch_steady(u, memo=memo, timeout=timeout, deadline=deadline)
    get = lambda u, ua=UA_BROWSER, tries=1: fetch_steady(u, tries=tries, memo=memo, ua=ua, timeout=timeout,
                                                         deadline=deadline)

    def late(*rs):
        """True when the run's deadline stopped any of these requests: what they feed was not observed."""
        return any(r.kind == "deadline" for r in rs)

    def not_reached(cid, what):
        tier[cid] = None
        ev[cid] = "The run reached its %g s limit before %s came back; not observed." % (RUN_DEADLINE, what)
    if urls:
        # the caller validated the list and its length (--urls caps at 8, --urls-from at the report's own count)
        urls, sample_source = pin_urls(base, urls, limit=len(urls)), "pinned"
    else:
        say("discovering sample pages…")
        urls, sample_source = discover(base, sample, verbose, memo=memo, timeout=timeout, deadline=deadline)
    say("fetching %d pages (sample from %s)…" % (len(urls), sample_source))
    # robots.txt comes with the pages: it names the sitemaps the next wave asks for. discover() has read it already
    # (a memo hit); a pinned sample has not
    want = list(dict.fromkeys(urls + [origin + "/robots.txt"]))
    pages = {u: r for u, r in zip(want, pmap(steady, want)) if u in urls}
    # a bot-challenge page stands where the page should be: it is dropped like a failed fetch, and counted
    challenged = {u: k for u, k in ((u, challenge_kind(r)) for u, r in pages.items()) if k}
    live = {u: r for u, r in pages.items() if r.ok and r.body and u not in challenged}
    if not live:
        if challenged:
            # never a scored g.ssr 0: every page check would read the challenge page
            kinds = list(challenged.values())
            raise ScoreError("%s (%s): a static fetch cannot measure this site"
                             % (BOT_CHALLENGE, max(dict.fromkeys(kinds), key=kinds.count)), "bot_challenge", base)
        raise fetch_failure(base, [pages[u] for u in urls], timeout)
    n = len(live)
    sampled = dict(asked=sample, drawn=len(urls), errors=len(urls) - n - len(challenged), challenges=len(challenged),
                   pinned=sample_source == "pinned")

    home_html_early = live.get(root + "/", list(live.values())[0]).text
    # each page's language decides its passage unit and whether a lexicon can read it
    langs_of = {u: page_lang(r) for u, r in live.items()}

    # ── what the sample names: the sitemaps, the entity, its logo and profiles, the brand ──
    # read once per run, retries included: fetched with the pages, or by discover() before them
    rb = steady(origin + "/robots.txt")
    txt = rb.text if rb.ok else ""
    # A site can live under a path — a GitHub Pages project page, a docs subtree, a
    # country folder. The spec puts sitemap.xml and llms.txt at the origin, but the
    # owner of example.com/docs cannot place a file at example.com. Scoring them zero
    # penalises them for something they do not control (open question #9), so fall
    # back to the path they were given. Origin still wins when both exist.
    sm_urls = [join_link(origin + "/", u) for u in _SITEMAP_DECL.findall(txt)] \
              or [origin + "/sitemap.xml", origin + "/sitemap_index.xml"] \
              + ([origin + scope + "/sitemap.xml"] if scope else [])
    allld = {u: jsonld(r.text) for u, r in live.items()}
    def is_org(x):
        t = x.get("@type")
        return any(str(v) == "Organization" or str(v).endswith(("Corporation", "LocalBusiness", "Organization"))
                   for v in (t if isinstance(t, list) else [t]))
    org_at = [(u, x) for u, o in allld.items() for x in o if is_org(x)]
    orgs = [x for _, x in org_at]
    logo_page, logo = next(((u, x.get("logo")) for u, x in org_at if x.get("logo")), (None, None))
    logo_url = logo.get("url") if isinstance(logo, dict) else logo
    logo_url = logo_url if isinstance(logo_url, str) else None
    same = next((o.get("sameAs") for o in orgs if o.get("sameAs")), None)
    # a relative IRI in JSON-LD resolves against the page it sits on, not the site root:
    # "logo.png" on /docs/ is /docs/logo.png
    logo_base = (live[logo_page].url or logo_page) if logo_page in live else root + "/"
    logo_at = join_link(logo_base, logo_url) if logo_url else None
    declared = same if isinstance(same, list) else ([same] if same else [])
    # only http(s) URLs can be checked; a bare "www.x.com/acme", an empty string or null is not one
    sa = [x.strip() for x in declared if isinstance(x, str) and re.match(r"https?://", x.strip(), re.I)]
    cjk_site = "zh" in langs_of.values() or under_cn(root)

    # the brand, for p3.knowledge-graph: the Organization's names, og:site_name, then the home page's title
    stem = host_stem(root)
    cands = []
    for o in orgs:
        for k in ("legalName", "name", "alternateName"):
            v = o.get(k)
            if isinstance(v, list): v = v[0] if v else None
            if isinstance(v, str) and v.strip(): cands.append(v.strip())
    og = og_site_name(home_html_early)
    if og is not None: cands.append(html.unescape(og).strip())
    t = title_html(home_html_early)
    if t is not None:
        title = visible_text(t)
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
    # in the most common page language besides English, and in English: two languages at most, as before. Only a
    # Wikipedia edition that exists: a page's own lang tag never names the host a lookup goes to
    other = [x for x in langs_of.values() if x in WIKI_LANGS]
    langs = ([max(dict.fromkeys(other), key=other.count)] if other else []) + ["en"]

    # ── one wave ──
    # Every request whose URL is known by now goes out at once, and the checks below read the answers from the
    # memo: the sitemaps; llms.txt, llms-full.txt, ai.txt and /.well-known/ai.txt, at the origin and under the
    # given path; the logo; the first 8 sameAs profiles; the Chinese crawlers on the home page; the retrieval
    # probes; and the knowledge-graph lookups. They used to go one after another, a lookup at a time. The wave
    # runs in three lanes side by side, so a network that cannot reach one host does not hold up the others:
    # requests to the site share 8 connections, as the probes always did; requests to other hosts (a logo on a
    # CDN, the profiles) have 8 of their own; and the lookups go as p3.knowledge-graph reads them, one brand
    # candidate at a time with its lookups at once, stopping at the first that finds the entity, so Wikidata and
    # Wikipedia get no lookup the check would not read. Only a sitemap index's child is asked for after the
    # wave, and discover() has usually fetched it already.
    # The site's own files and its logo are retried like the sitemaps, and the Chinese crawlers like the retrieval
    # probes: they share the burst now, and a timeout or a 429 from it would read as a missing llms.txt or a
    # blocked crawler. Profiles and lookups on other hosts are asked once, as before: their checks already read a
    # request that got no answer as not measured.
    probe = list(live)[:3]
    plan = {}
    for u, ua, tries in ([(u, UA_BROWSER, STEADY_TRIES) for u in sm_urls[:4]]
                         + [(base_ + rel, UA_BROWSER, STEADY_TRIES) for rel in ("/llms.txt", "/llms-full.txt",
                                                                                "/ai.txt", "/.well-known/ai.txt")
                            for base_ in [origin] + ([origin + scope] if scope else [])]
                         + ([(logo_at, UA_BROWSER, STEADY_TRIES)] if logo_at is not None else [])
                         + [(u, UA_BROWSER, 1) for u in sa[:8]]
                         + ([(root + "/", ua, PROBE_TRIES) for _, ua in CN_UAS] if cjk_site else [])
                         + [(u, ua, PROBE_TRIES) for _, ua in RETRIEVAL_UAS for u in probe]):
        plan.setdefault((u, ua), tries)
    def on_site(u):
        try:
            return urllib.parse.urlsplit(u).netloc == urllib.parse.urlsplit(origin).netloc
        except ValueError:
            return False
    ask = lambda k: get(k[0], ua=k[1], tries=plan[k])
    def kg_search():
        for cand in brands:
            ats = [u for lg in langs for u in kg_lookups(cand, lg)]
            rs = pmap(get, ats, workers=len(ats))
            if any(kg_found(cand, lg, rs[2 * i], rs[2 * i + 1]) for i, lg in enumerate(langs)):
                return
    say("fetching the rest in one wave: %d requests, %d of them retrieval user-agent probes, and the "
        "knowledge-graph lookups…" % (len(plan), len(RETRIEVAL_UAS) * len(probe)))
    pmap(lambda lane: lane(), [lambda: pmap(ask, [k for k in plan if on_site(k[0])]),
                               lambda: pmap(ask, [k for k in plan if not on_site(k[0])]), kg_search], workers=3)

    # ── g.robots ──
    if rb.ok:
        tier["g.robots"], ev["g.robots"] = robots_tier(txt, len(rb.body))
    elif rb.status == 0:
        # a network that cannot read the file is not evidence that it is missing (RFC 9309 2.3.1.4 has
        # crawlers assume a full disallow here; rubric/open-questions.md #10)
        tier["g.robots"] = None
        ev["g.robots"] = ("robots.txt could not be read%s (%s); not observed."
                          % ("" if rb.kind in DEFINITE or rb.kind in OUT_OF_TIME else " after %d tries" % STEADY_TRIES,
                             rb.err if rb.kind in OUT_OF_TIME else fault_name(rb.err)))
    elif transient(rb.status):
        tier["g.robots"] = 3
        ev["g.robots"] = ("robots.txt answered HTTP %d on all %d tries. Nothing readable is disallowed, but nothing "
                          "is explicitly allowed either." % (rb.status, STEADY_TRIES))
    else:
        # 4xx: no robots.txt, and a crawler may fetch anything (RFC 9309 2.3.1.3)
        tier["g.robots"] = 3
        ev["g.robots"] = "No robots.txt (HTTP %d). Nothing is disallowed, but nothing is explicitly allowed either." % rb.status

    # ── g.reachable ──
    # a dropped connection or a 429 is retried; a persistent refusal still counts, because a browser
    # reached the same page moments earlier. A probe that never gets an answer (a timeout or a dropped
    # connection on every try) is not a refusal: from one address it is mostly the network, and otherwise a
    # firewall dropping a crawler's user-agent sent from an address its vendor does not use, which the real
    # crawler never meets. A crawler with no answer on any page therefore leaves the count; one answered on
    # some pages is reached. The tier is read over the crawlers that answered, and with fewer than half of
    # them answering nothing is observed. Only HTTP refusals make "most retrieval user-agents are blocked"
    results = [(name, get(u, ua=ua, tries=PROBE_TRIES)) for name, ua in RETRIEVAL_UAS for u in probe]
    per = {}
    for name, r in results: per.setdefault(name, []).append(r)
    nua = len(RETRIEVAL_UAS)
    # HTTP 429 is "slow down", not "keep out": the burst of probes from one address trips rate limits that
    # a real crawler pacing its own requests does not meet. A crawler that got only 429s leaves the count, as
    # one with no answer does; any other refusal on a page still counts
    refused = [name for name, rs in per.items() if any(x.status and x.status != 429 and not x.ok for x in rs)]
    throttled = [name for name, rs in per.items()
                 if name not in refused and not any(x.ok for x in rs) and any(x.status == 429 for x in rs)]
    silent = [name for name, rs in per.items() if name not in refused and name not in throttled and not any(x.ok for x in rs)]
    reached = [name for name in per if name not in refused and name not in silent and name not in throttled]
    okc = len(reached)
    base_len = {u: len(visible_text(live[u].text)) for u in probe}
    consistent, differ = 0, []
    for name in reached:
        good = all(abs(len(visible_text(r.text)) - base_len[u]) <= max(400, base_len[u] * .25)
                   for u, r in zip(probe, per[name]) if r.ok)
        consistent += 1 if good else 0
        if not good: differ.append(name)
    if okc + len(refused) < (nua + 1) // 2:
        tier["g.reachable"] = None           # fewer than half the crawlers answered: too little was observed
    elif len(refused) > nua // 2:
        tier["g.reachable"] = 0
    elif not refused and consistent == okc:
        tier["g.reachable"] = 5
    else:
        tier["g.reachable"] = 3
    # which agents were refused and how, grouped by what they got, so a reading at zero can be audited
    failed = {}
    for name in refused:
        got = "/".join("HTTP %d" % st if st else "no answer" for st in sorted({x.status for x in per[name] if not x.ok}))
        failed.setdefault(got, []).append(name)
    ev["g.reachable"] = clip("%d of %d retrieval user-agents returned 200 on %d sampled pages; "
                             "%d of those served content matching what a browser receives.%s%s%s%s%s"
                             % (okc, nua, len(probe), consistent,
                                " Not reached — %s." % "; ".join(
                                    "%s: %s" % (got, "all %d" % nua if len(names) == nua else ", ".join(names))
                                    for got, names in failed.items()) if failed else "",
                                " No answer on any page, so not counted: %s." % ", ".join(silent) if silent else "",
                                " Rate-limited (HTTP 429) on every try, so not counted: %s." % ", ".join(throttled)
                                if throttled else "",
                                " Content differed: %s." % ", ".join(differ) if differ else "",
                                " (Unverified probes: vendor user-agent strings sent from this machine's address.)"
                                if failed or silent or throttled else ""), 480)
    if tier["g.reachable"] is None:
        unseen = "; ".join(part for part in ("no answer: " + ", ".join(silent) if silent else "",
                                             "rate-limited, HTTP 429: " + ", ".join(throttled) if throttled else "")
                           if part)
        ev["g.reachable"] = clip("Only %d of %d retrieval user-agents got an answer on any sampled page (%s), "
                                 "so too little was observed; not observed. A browser reached the same pages."
                                 % (okc + len(refused), nua, unseen), 480)
    if late(*(r for _, r in results)):
        # a probe the deadline stopped says nothing about that crawler: the gate is not observed, never zero
        not_reached("g.reachable", "every crawler probe")

    # ── g.ssr ──
    ssr = sum(1 for r in live.values() if wc(visible_text(main_html(r.text))) >= 120)
    tier["g.ssr"] = 5 if ssr == n else (3 if ssr >= max(1, n // 2) else 0)
    ev["g.ssr"] = "%d of %d sampled pages carry substantive body text in the HTML response with no JavaScript executed." % (ssr, n)

    # ── p1.sitemap ──
    # sm_urls: robots.txt's Sitemap lines, else the conventional paths at the origin and under the given path.
    # The first sitemap in the order they are looked for, unless the deadline stopped a request before it
    sm = next((r for r in map(steady, sm_urls[:4]) if is_sitemap(r) or late(r)), None)
    if sm and not late(sm) and re.search(r"<sitemapindex", sm.text, re.I):
        child = re.findall(r"<loc>\s*([^<]+)", sm.text)[:1]
        if child:
            sub = steady(join_link(sm.url, child[0].strip()))
            if is_sitemap(sub) or late(sub): sm = sub
    if sm and late(sm):
        not_reached("p1.sitemap", "the sitemap")
    elif not sm:
        tier["p1.sitemap"] = 0; ev["p1.sitemap"] = "No sitemap found via robots.txt or the conventional paths."
    else:
        locs = len(re.findall(r"<loc>", sm.text)); mods = len(re.findall(r"<lastmod>", sm.text))
        tier["p1.sitemap"] = 4 if locs and mods >= locs * .5 else 2
        ev["p1.sitemap"] = "Sitemap %s (%s): HTTP 200, %d <loc>, %d <lastmod>." % (
            "declared in robots.txt" if _SITEMAP_DECL.search(txt) else "at the conventional path",
            site_text(urllib.parse.urlsplit(sm.url)._replace(query="", fragment="").geturl(), 120)
            if getattr(sm, "url", None) else "—", locs, mods)

    # ── p1.llms-txt ──
    lt = get(origin + "/llms.txt")
    lt_at = "/llms.txt"
    if not text_file(lt) and scope and not late(lt):
        alt = get(origin + scope + "/llms.txt")
        if text_file(alt) or late(alt):
            lt, lt_at = alt, scope + "/llms.txt"
    if late(lt):
        not_reached("p1.llms-txt", lt_at)
    elif lt.status == 0:
        # no answer after its retries says nothing about whether the file exists: not observed, never zero
        tier["p1.llms-txt"] = None
        ev["p1.llms-txt"] = "%s got no answer after its retries (%s); not observed." % (lt_at, fault_name(lt.err))
    elif not text_file(lt):
        tier["p1.llms-txt"] = 0
        ev["p1.llms-txt"] = ("/llms.txt %s%s." % (
            "answered 200 with an HTML page (a catch-all route), not a text file" if lt.ok else "returned HTTP %d" % lt.status,
            " (and none under %s either)" % scope if scope else ""))
    else:
        t = lt.text
        secs = re.findall(r"(?m)^##\s+(.+)$", t)
        with_links = 0
        parts = re.split(r"(?m)^##\s+.+$", t)[1:]
        for p in parts:
            if has_md_link(p): with_links += 1
        has_def = bool(re.search(r"(?m)^>\s+\S", t)) or (len(parts) and wc(parts[0]) > 15) or wc(t.split("##")[0]) > 25
        tier["p1.llms-txt"] = 5 if (has_def and with_links >= 2) else (4 if has_def else 2)
        ev["p1.llms-txt"] = "%s: HTTP 200, %d bytes, %d '##' sections, %d of them containing links, site definition %s.%s" % (
            lt_at, len(lt.body), len(secs), with_links, "present" if has_def else "absent",
            " Found under the given path, not at the origin — the spec puts it at the origin,"
            " but a site living under a path cannot place a file there." if lt_at != "/llms.txt" else "")

    # ── p1.organization ──
    org_pages = [u for u, o in allld.items() if any(is_org(x) for x in o)]
    site_pages = [u for u, o in allld.items() if "WebSite" in types_of(o)]
    logo_r = get(logo_at) if logo_at is not None else None
    logo_ok = bool(logo_r and logo_r.ok)
    org_complete = any(o.get("name") and o.get("url") and o.get("logo") for o in orgs)
    if not org_pages and not site_pages:
        tier["p1.organization"] = 0; ev["p1.organization"] = "Neither Organization nor WebSite JSON-LD found on any sampled page."
    elif not (org_pages and site_pages):
        tier["p1.organization"] = 3
        ev["p1.organization"] = "Only %s found (%d of %d pages)." % (
            "Organization" if org_pages else "WebSite", len(org_pages or site_pages), n)
    elif not org_complete:
        # both types present, but the rubric's middle tier asks for name, url and logo
        tier["p1.organization"] = 3
        ev["p1.organization"] = ("Organization and WebSite both present (%d of %d pages), but no Organization carries "
                                 "all of name, url and logo." % (len(org_pages), n))
    elif logo_r is not None and late(logo_r):
        not_reached("p1.organization", "the logo")
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
    # the top tier needs "real field values": a bare {"@type": "Product"} states a type and nothing else
    real = {u for u in hit | art if any(substantive(x) for x in allld[u])}
    tier["p1.page-type"] = 4 if len(real) >= max(2, n * .5) else (2 if (hit or art) else 0)
    ev["p1.page-type"] = ("Page-type schema (Product/Offer, FAQPage, HowTo, Article…) on %d of %d sampled pages; "
                          "%d of them with real field values." % (len(hit | art), n, len(real)))

    # ── p2.answer-passages ──
    # each page in its own language's unit: 50–200 characters for Chinese, Japanese and Korean, 25–120 words for
    # everything else. One Chinese page no longer holds a site's English pages to the character range.
    passed, examples, in_chars = 0, [], 0
    for u, r in live.items():
        chars = langs_of[u] in CJK_LANGS
        in_chars += chars
        lo, hi = (50, 200) if chars else (25, 120)
        for p in paragraphs(r.text)[:6]:
            k = cjk_chars(p) if chars else len(p.split())
            if lo <= k <= hi and re.search(r"[.。!?！？]", p):
                passed += 1; examples.append((u, k, p)); break
    tier["p2.answer-passages"] = 9 if passed >= n * .75 else (7 if passed >= n * .5 else (4 if passed else 0))
    if in_chars in (0, n):
        unit = "50–200 characters" if in_chars else "25–120 words"
    else:
        unit = ("25–120 words on the %d pages read in words, 50–200 characters on the %d read in characters"
                % (n - in_chars, in_chars))
    ev["p2.answer-passages"] = "%d of %d pages open with a self-contained passage of %s.%s" % (
        passed, n, unit, (" e.g. %s" % site_text(examples[0][2], 90)) if examples else "")

    # ── p2.question-intent ──
    # a heading matches question intent if a person would phrase their question that way:
    # a question, a task, or an explanation. Not whether it carries a question mark.
    QP, NAV = QP_INTENT, NAV_LABEL

    # the lexicon is English and Chinese: a page in another language is not read, and with none left the check
    # is not observed, never zero
    readable = [u for u in live if langs_of[u] in LEXICON_LANGS]
    gap = lexicon_gap(langs_of[u] for u in live)
    qi = 0
    for u in readable:
        hs = [h for h in headings(live[u].text) if 3 <= len(h) <= 120]
        if any(QP.search(h) and not NAV.match(h) for h in hs): qi += 1
    nq = len(readable)
    if not nq:
        tier["p2.question-intent"] = None
        ev["p2.question-intent"] = ("No question-intent lexicon for %s — the check leaves the denominator: the "
                                    "heading lexicon is English and Chinese." % ", ".join(gap))
    else:
        tier["p2.question-intent"] = 7 if qi >= nq * .75 else (5 if qi >= nq * .5 else (3 if qi else 0))
        ev["p2.question-intent"] = ("%d of %d pages carry at least one heading phrased as a question, a task or an "
                                    "explanation.%s" % (qi, nq, " %d page%s in %s not read: no question-intent lexicon "
                                                        "for that language." % (n - nq, "s" if n - nq > 1 else "",
                                                                                ", ".join(gap)) if gap else ""))

    # ── p2.freshness ──
    fr = dm = stale = 0
    for u, r in live.items():
        o = allld.get(u, [])
        shown = visible_dates(r.text)
        if any(x.get("dateModified") or x.get("datePublished") for x in o) or shown or \
           re.search(r'property=["\']article:(published|modified)_time', r.text, re.I):
            fr += 1
        mods = [d for d in (iso_date(x.get("dateModified")) for x in o) if d]
        if any(x.get("dateModified") for x in o):
            dm += 1
            # the top tier asks that dateModified agree with the visible date: a page whose own date
            # (its publication date, its byline) is later than its declared last modification contradicts itself
            own = own_dates(r.text, o)
            if mods and own and max(own) > max(mods) + datetime.timedelta(days=1):
                stale += 1
    # "most pages do, and dateModified agrees": a quarter of the declaring pages may disagree
    tier["p2.freshness"] = 6 if (fr >= n * .75 and dm and stale <= dm * .25) else (3 if fr else 0)
    ev["p2.freshness"] = "%d of %d pages carry a date a reader or a crawler can see; %d declare dateModified%s." % (
        fr, n, dm, (", %d of them earlier than the date the page shows" % stale) if stale else "")

    # ── p2.sourced-stats ──
    # a figure is attributed only by what sits beside it in the content: its own block or the next (stat_reading).
    # Links to the site itself, to its own sameAs profiles and to social profiles or share buttons are not sources.
    own = {site_key(urllib.parse.urlsplit(u).hostname) for u in [root] + [r.url or u for u, r in live.items()]}
    profiles = [p for p in (profile_of(x) for x in (same if isinstance(same, list) else [same])
                            if isinstance(x, str)) if p]
    # source phrases are English and Chinese: on a page in another language a link, a <cite> or a footnote still
    # attributes a figure, and a phrase is not read
    lexed = [langs_of[u] in LEXICON_LANGS for u in live]
    reads = [stat_reading(r.text, own, profiles, phrases=p) for r, p in zip(live.values(), lexed)]
    tot_num, cited, linked = (sum(x[i] for x in reads) for i in range(3))
    on_pages = sum(1 for x in reads if x[0])
    bearing = [x for x in reads if x[0] >= 3]
    # the languages of the pages carrying three or more figures whose source phrases were not read
    unread = lexicon_gap(langs_of[u] for u, x, p in zip(live, reads, lexed) if x[0] >= 3 and not p)
    if not bearing:
        tier["p2.sourced-stats"] = 3
        ev["p2.sourced-stats"] = ("Few numeric claims in the sample (%d figures on %d pages), so there is little to "
                                  "attribute." % (tot_num, on_pages))
    else:
        # a page has most of its figures attributed when more than half are; the top tier asks for a link
        most = sum(1 for f, a, _ in bearing if 2 * a > f)
        most_linked = sum(1 for f, _, k in bearing if 2 * k > f)
        m = len(bearing)
        tier["p2.sourced-stats"] = 7 if most_linked >= m * .75 else (5 if most >= m * .5 else (3 if cited else 0))
        ev["p2.sourced-stats"] = ("%d figures on %d pages; %d attributed in the same block or the next, %d of them "
                                  "with a link. Of the %d pages carrying three or more, %d attribute most of theirs, "
                                  "%d with a link." % (tot_num, on_pages, cited, linked, m, most, most_linked))
        n_unread = sum(1 for x, p in zip(reads, lexed) if x[0] >= 3 and not p)
        if n_unread == m and tier["p2.sourced-stats"] < 5:
            # a source phrase could lift the lower tiers (the top one asks for a link, which is read in any
            # language), and no page carrying figures could be read for one: not measured, never zero
            tier["p2.sourced-stats"] = None
            ev["p2.sourced-stats"] = ("No source-phrase lexicon for %s — the check leaves the denominator: %s, and "
                                      "a source named in words in that language cannot be read." % (
                                          ", ".join(unread), ev["p2.sourced-stats"].split(";")[0]))
        elif n_unread:
            ev["p2.sourced-stats"] += (" Source phrases on the %d of them in %s were not read: no lexicon for that "
                                       "language." % (n_unread, ", ".join(unread)))

    # ── p2.named-author ──
    # a byline that names a role or the organisation is not a person ("editor" was once spelt with
    # Cyrillic letters here, so it never matched)
    BRANDY = re.compile(r"^(team|staff|editors?|editorial( team| staff)?|admin|administrator|support|webmaster|"
                        r"the .+ team|.*官方|.*团队|.*小编|编辑部)$", re.I)
    org_names = {str(o.get("name")).strip().lower() for o in orgs if o.get("name")}
    named, linked, skipped = 0, 0, []
    for u, r in live.items():
        auth = None
        for x in allld.get(u, []):
            a = x.get("author")
            if isinstance(a, list): a = a[0] if a else None
            if isinstance(a, dict) and a.get("name"): auth = a; break
            if isinstance(a, str) and a.strip(): auth = {"name": a}; break
        if not auth:
            m = next(in_tags(_REL_AUTHOR_NAME, _REL_AUTHOR, r.text), None)
            # a byline in the main content, else near the top of the page (an article header outside
            # <main>); never in a footer, where "Powered by …" credits live. A written byline is read only in a
            # language the byline lexicon has
            if m:
                name = m.group(1)
            elif langs_of[u] in LEXICON_LANGS:
                name = byline_name(visible_text(main_html(r.text))) or byline_name(visible_text(r.text)[:4000])
            else:
                name = None
                skipped.append(langs_of[u])
            if name: auth = {"name": name}
        name = str(auth.get("name") or "").strip() if auth else ""
        if name and not BRANDY.match(name) and name.lower() not in org_names:
            named += 1
            if auth.get("url") or auth.get("sameAs"): linked += 1
    tier["p2.named-author"] = 6 if linked >= max(1, named * .5) and named else (3 if named else 0)
    ev["p2.named-author"] = "%d of %d pages carry a personal byline; %d link that name to a verifiable identity page." % (named, n, linked)
    if skipped and len(skipped) == n:
        # no page names an author in markup, and none is in a language whose written byline can be read: not
        # measured, never zero
        tier["p2.named-author"] = None
        ev["p2.named-author"] = ("No byline lexicon for %s — the check leaves the denominator: no page names an "
                                 "author in its structured data or a rel=author link, and a written byline in that "
                                 "language cannot be read." % ", ".join(lexicon_gap(skipped)))
    elif skipped:
        ev["p2.named-author"] += (" A written byline on the %d page%s in %s was not read: no byline lexicon for "
                                  "that language." % (len(skipped), "s" if len(skipped) > 1 else "",
                                                      ", ".join(lexicon_gap(skipped))))

    # ── p3.sameas ──
    if not declared:
        tier["p3.sameas"] = 0; ev["p3.sameas"] = "No sameAs declared on the Organization entity."
    elif not sa:
        tier["p3.sameas"] = 0
        ev["p3.sameas"] = "%d sameAs declared, none of them an http(s) URL that can be checked." % len(declared)
    else:
        # Only 404 / 410 prove a profile is gone. Timeouts, resets and 451 mean this
        # network cannot see the host (LinkedIn, X, YouTube, GitHub and Wikipedia are all
        # unreachable from mainland China); 401 / 403 / 429 / 999 and similar are bot walls
        # in front of pages that exist (Crunchbase, Zhihu, Facebook, LinkedIn). Counting
        # either as dead made the score depend on where and when the tool ran.
        res = [get(u) for u in sa[:8]]
        t, good, dead, unseen = sameas_tier([r.status for r in res])
        if late(*res):
            not_reached("p3.sameas", "every sameAs profile")
        elif t is None:
            tier["p3.sameas"] = None
            ev["p3.sameas"] = ("%d sameAs declared; none of the first %d could be checked from this network "
                               "(timeout, block or bot wall), so this check is unobservable rather than zero."
                               % (len(sa), len(res)))
        else:
            tier["p3.sameas"] = t
            ev["p3.sameas"] = ("%d sameAs declared; of the first %d, %d resolve, %d are gone (404/410)%s."
                               % (len(sa), len(res), good, dead,
                                  ", %d could not be checked from this network and are left out" % unseen if unseen else ""))

    # ── p3.video ──
    blob = " ".join(r.text for r in live.values())
    vt = sum(1 for o in allld.values() if "VideoObject" in types_of(o))
    chan, embeds = video_links(blob)
    tier["p3.video"] = 3 if (vt and (chan or embeds)) else (2 if (chan or embeds or vt) else 0)
    ev["p3.video"] = ("%d pages declare VideoObject; %d channel links and %d embedded players "
                      "in the sample." % (vt, chan, embeds))

    # ── p4.answer-shape ──
    shaped = 0
    for _u, r in live.items():
        b = main_html(r.text)
        hs = len(re.findall(r"<h[23]\b", b, re.I)); li = len(re.findall(r"<li\b", b, re.I))
        tb = len(re.findall(r"<table\b", b, re.I))
        ps = [wc(p) for p in paragraphs(r.text)] or [0]
        avg = sum(ps) / len(ps)
        if hs >= 2 and (li >= 3 or tb) and avg <= (160 if langs_of[_u] in CJK_LANGS else 90): shaped += 1
        elif hs >= 2: shaped += 0.5
    tier["p4.answer-shape"] = 4 if shaped >= n * .6 else (2 if shaped else 0)
    ev["p4.answer-shape"] = "%.0f of %d pages carry subheadings plus lists or tables, with paragraphs of workable length." % (shaped, n)

    # ── p4.cn-engines ──
    if not cjk_site:
        tier["p4.cn-engines"] = None
        ev["p4.cn-engines"] = "Site does not address the Chinese market — the check leaves the denominator."
    else:
        cn = [get(root + "/", ua=ua) for _, ua in CN_UAS]
        okc2 = sum(1 for r in cn if r.ok)
        icp = bool(re.search(r"ICP备|京ICP|沪ICP|粤ICP", " ".join(r.text for r in live.values())))
        tier["p4.cn-engines"] = 2 if okc2 == len(CN_UAS) and icp else (1 if okc2 else 0)
        ev["p4.cn-engines"] = "%d of %d Chinese crawlers reached the home page; ICP filing %s." % (
            okc2, len(CN_UAS), "shown" if icp else "not shown")
        if late(*cn):
            not_reached("p4.cn-engines", "every Chinese crawler's request")

    # ── p3.knowledge-graph (Wikidata + Wikipedia, both public APIs, no key) ──
    # the brand candidates and the languages were read before the wave, whose lookups this reads in the same order
    kg_where, brand, kg_queries, kg_ok, kg_late = [], brands[0] if brands else stem, 0, 0, False
    for cand in brands:
        for lg in langs:
            wd_at, wp_at = kg_lookups(cand, lg)
            wd, wp = get(wd_at), get(wp_at)
            kg_queries += 2; kg_ok += (1 if wd.ok else 0) + (1 if wp.ok else 0); kg_late = kg_late or late(wd, wp)
            kg_where += kg_found(cand, lg, wd, wp)
        if kg_where: brand = cand; break
    also = "" if len(brands) < 2 else " (also tried %s)" % ", ".join(site_text(x, 60) for x in brands if x != brand)
    kt = kg_tier(bool(kg_where), kg_ok, kg_queries)
    if kt == 4:
        tier["p3.knowledge-graph"] = 4
        ev["p3.knowledge-graph"] = "Brand read as %s%s. Entity found — %s" % (site_text(brand, 60), also, "; ".join(kg_where[:2]))
    elif kt is None and kg_late:
        not_reached("p3.knowledge-graph", "every Wikidata and Wikipedia lookup")
    elif kt is None:
        # Absence can only be concluded when every lookup answered. If some timed out
        # (Wikidata and Wikipedia are unreachable from some networks, flaky from others),
        # the entity may be exactly where we could not look — so this is our blind spot,
        # not a zero. Scoring 0 on a partial answer made the same site score differently
        # on consecutive runs from the same machine.
        tier["p3.knowledge-graph"] = None
        ev["p3.knowledge-graph"] = ("Brand read as %s%s. %d of %d Wikidata and Wikipedia lookups failed to "
                                    "respond and none of the rest matched, so this check is unobservable "
                                    "rather than zero." % (site_text(brand, 60), also, kg_queries - kg_ok, kg_queries))
    else:
        tier["p3.knowledge-graph"] = 0
        ev["p3.knowledge-graph"] = ("Brand read as %s%s. No entity whose label matches exactly, in Wikidata "
                                    "or Wikipedia (%s); %d of %d lookups answered."
                                    % (site_text(brand, 60), also, "/".join(langs), kg_ok, kg_queries))

    # ── a homepage that could not be fetched ──
    # The Organization entity, its sameAs and the brand name the knowledge-graph lookup starts from usually sit
    # on the homepage. When it was in the sample but could not be fetched, not finding them on the other pages
    # says nothing about the site: those zeros are not observed
    if root + "/" in urls and root + "/" not in live:
        for cid in ("p1.organization", "p3.sameas", "p3.knowledge-graph"):
            if tier.get(cid) == 0:
                tier[cid] = None
                ev[cid] = clip("%s The homepage, where this usually sits, could not be fetched this run, so this is "
                               "not observed." % ev.get(cid, ""), 480)

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
        r = get(origin + rel)
        if not text_file(r) and scope:
            alt = get(origin + scope + rel)
            if text_file(alt):
                return alt
        return r
    lf = at_origin_or_scope("/llms-full.txt"); bon["b.llms-full"] = 2 if text_file(lf) else 0
    at = at_origin_or_scope("/ai.txt")
    at2 = at_origin_or_scope("/.well-known/ai.txt") if not text_file(at) else at
    bon["b.ai-txt"] = 2 if text_file(at2) else 0
    home_html = home_html_early
    bon["b.geo-link"] = 1 if geo_link(home_html) else 0
    bon["b.speakable"] = 1 if any("SpeakableSpecification" in json.dumps(o) for o in allld.values()) else 0

    # Where the request actually landed. A site can hand back a different origin than
    # the one asked for — a rename (neon.tech to neon.com), or a locale swap driven by
    # the Accept-Language header (aliyun.com to alibabacloud.com, xiaomi.com to mi.com).
    # Scoring the landing page under the requested label hides that; recording it makes
    # the substitution visible to anyone reading the result.
    # ── outside the score: robots.txt page by page ──
    # The homepage, the sampled pages and the first URLs of the sitemap p1.sitemap read (the first child of a sitemap
    # index), held against robots.txt as RFC 9309 and a first-match reading choose a rule (robots_paths). Nothing is
    # fetched for it, nor for the links and the hreflang annotations below: they read the pages this run already has,
    # the homepage, the sampled pages and the section indexes discover() read (in this run's memo; a pinned sample has
    # none).
    with memo.lock:
        got = dict(memo.got)
    fetched = lambda u: pages.get(u) or got.get((u, UA_BROWSER, "GET"))
    is_page = lambda r: r is not None and r.ok and bool(r.body) and not challenge_kind(r)
    home_r = fetched(root + "/")
    # A homepage that redirects to another host (apex to www, or a rename) moved the site there: its links, and the
    # sitemap's URLs, name that host. Its robots.txt rules that host's pages only when robots.txt was answered from
    # there too (the request for it followed the same redirect); otherwise its sitemap URLs are not held against it
    here = url_host(origin)
    there = url_host(home_r.url) if home_r is not None and home_r.ok and home_r.url else None
    site = {here, there} - {None}
    robots_site = site if rb.ok and rb.url and url_host(rb.url) == there else {here}
    locs = []
    if sm and not late(sm) and not re.search(r"<sitemapindex", sm.text, re.I):
        locs = [html.unescape(x.strip()) for x in re.findall(r"<loc>\s*([^<]+)", sm.text)]
    checked, from_sitemap = checked_urls(root, origin, scope, urls, pages, locs, robots_site)
    linked_sitemap = from_sitemap if robots_site == site else checked_urls(root, origin, scope, urls, pages, locs, site)[1]
    if rb.ok:
        rp = dict(robots_txt="read", **robots_paths(txt, checked))
    elif rb.status and not transient(rb.status):
        # no robots.txt: a crawler may fetch anything (RFC 9309 2.3.1.3)
        rp = dict(robots_txt="absent", checked=len(checked), not_checked=0, crawlers=len(RETRIEVAL_UAS), blocked=0,
                  one_rule=False, pages=[], read_differently=0, differences=[])
    else:
        rp = dict(robots_txt="unreadable", checked=len(checked), not_checked=0, crawlers=len(RETRIEVAL_UAS),
                  blocked=None, one_rule=False, pages=[], read_differently=None, differences=[])
    # ── outside the score: links in the server HTML ──
    home = (root + "/", home_r) if is_page(home_r) else None
    searched = ([home] if home else []) + [(u, r) for u, r in live.items()] + \
        [(u, r) for u, r in ((root + p, got.get((root + p, UA_BROWSER, "GET"))) for p in SECTION_INDEXES) if is_page(r)]
    # ── outside the score: hreflang annotations on the same pages, in their HTML and their Link headers ──
    access = {"robots_paths": rp, "server_links": server_links(home, searched, list(live), linked_sitemap, site, scope),
              "hreflang": hreflang(searched, site)}

    landed = next((r.url for u, r in sorted(live.items()) if r.url), root)
    # one last pass: whatever a page managed to put into a string, no control or bidi character leaves here
    ev = {k: _UNSAFE.sub("", v) if isinstance(v, str) else v for k, v in ev.items()}
    landed = _UNSAFE.sub("", landed) if isinstance(landed, str) else landed
    return dict(root=root, landed=landed, urls=list(live), sample_source=sample_source, tier=tier, ev=ev, bonus=bon,
                lang=audience_language(langs_of.values()), robots_bytes=len(rb.body), sampled=sampled, access=access,
                elapsed_s=round(time.monotonic() - started, 1))

# ── scoring & output ───────────────────────────────────────────────────────
def score(res):
    got = den = 0; gate_zero = False
    rows = []
    for cid, pil, name, pts, _tiers in SPEC:
        t = res["tier"].get(cid)
        if t is None:
            rows.append((cid, pil, name, None, pts, res["ev"].get(cid, ""))); continue
        got += t; den += pts
        if cid.startswith("g.") and t == 0: gate_zero = True
        rows.append((cid, pil, name, t, pts, res["ev"].get(cid, "")))
    b = min(sum(res["bonus"].values()), BONUS_CAP)
    total = got + b
    # bonus sits outside the denominator, so a near-perfect site plus bonus would pass 100; the
    # percentage is 0-100 by definition (schema/report.v2.json), and the bonus never takes it past that
    norm = min(100, round(100 * total / den)) if den else 0
    if gate_zero: norm = min(norm, GATE_CAP)
    return rows, total, den, b, norm, band(norm), gate_zero

def bar(t, mx, w=18):
    if t is None: return c.grey + "·" * w + c.r
    f = round(w * t / mx)
    col = c.green if t == mx else (c.amber if t else c.red)
    return col + "█" * f + c.grey + "░" * (w - f) + c.r

BADGE_LABEL = "AIV readiness"
# the badge's right half follows the band, so a regression is visible at a glance
BADGE_COLOUR = {"Leading": "#2f8f52", "Solid": "#2f8f52", "Growing": "#a08020", "Early": "#b06b30", "Not started": "#a33"}

def badge_face(res):
    """(message, colour, normalised, band) for both badges, so the SVG and the shields.io endpoint JSON cannot
    disagree: the score and band, with ' (gate capped)' when a gate at zero capped the score."""
    _, _, _, _, norm, bd, capped = score(res)
    return "%d/100 %s%s" % (norm, bd, " (gate capped)" if capped else ""), BADGE_COLOUR[bd], norm, bd

def write_badge(res, path):
    """An SVG anyone can commit next to their own README. Shields-shaped so it sits
    happily beside the build badges people already have."""
    right, col, norm, bd = badge_face(res)
    lw = 88                                  # "AIV readiness" at 11px Verdana
    rw = int(6.4 * len(right)) + 16
    w = lw + rw
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%(w)d" height="20" role="img"'
        ' aria-label="%(label)s: %(right)s">'
        '<title>%(label)s: %(right)s</title>'
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
        '<text x="%(lx)d" y="15" fill="#010101" fill-opacity=".3">%(label)s</text>'
        '<text x="%(lx)d" y="14">%(label)s</text>'
        '<text x="%(rx)d" y="15" fill="#010101" fill-opacity=".3">%(right)s</text>'
        '<text x="%(rx)d" y="14">%(right)s</text></g></svg>'
    ) % dict(w=w, lw=lw, rw=rw, col=col, right=right, label=BADGE_LABEL, lx=lw // 2, rx=lw + rw // 2)
    _write(path, svg)
    return path, norm, bd

def badge_endpoint(res):
    """The badge as a shields.io endpoint (https://shields.io/badges/endpoint-badge): host this JSON at any URL
    and https://img.shields.io/endpoint?url=<that URL> draws the SVG's label, message and colour. shields caches
    it for cacheSeconds (at least 300); a score moves when the site does, so a day is plenty."""
    message, col, _, _ = badge_face(res)
    return {"schemaVersion": 1, "label": BADGE_LABEL, "message": message, "color": col, "cacheSeconds": 86400}

def write_badge_json(res, path):
    _write(path, json.dumps(badge_endpoint(res), ensure_ascii=False) + "\n")
    return path

def top_gaps(rows, n=3):
    """The gaps every view leads with, in one order (rubric/v1.1.md, Report shape: unlocking fixes come first):
    gates at zero, since they cap the score; then the most points the next tier up adds; then rubric order.
    Each is (cid, name, next-tier gain, gain to full marks, what the next tier needs)."""
    order = {spec[0]: i for i, spec in enumerate(SPEC)}
    gaps = []
    for cid, _pil, name, t, mx, _e in rows:
        if t is None or t >= mx:
            continue
        gain, needs = next_tier(cid, t, mx)
        gaps.append((not (cid.startswith("g.") and t == 0), -gain, order.get(cid, len(order)),
                     (cid, name, gain, mx - t, needs)))
    return [g[-1] for g in sorted(gaps, key=lambda g: g[:3])][:n]

def first_sentence(text):
    """The first sentence of a check's evidence, without its full stop."""
    text = " ".join(str(text or "").split())
    m = re.match(r"(.+?[.!?])(?=\s|$)", text)
    return (m.group(1) if m else text).rstrip(".")

def gate_line(rows):
    """The headline when a gate is at zero: each gate at zero, the first sentence of its evidence, and the cap.
    None when no gate is."""
    zero = [(cid, e) for cid, _pil, _name, t, _mx, e in rows if cid.startswith("g.") and t == 0]
    if not zero:
        return None
    return "GATE AT ZERO — %s; the score cannot exceed %d while a gate is at zero" % (
        "; ".join("%s: %s" % (cid, clip(first_sentence(e), 200)) for cid, e in zero), GATE_CAP)

# what a gate at zero means, in the words a shared line can carry
GATE_SHARE = {"g.robots": "robots.txt disallows AI retrieval crawlers",
              "g.reachable": "AI retrieval crawlers are refused",
              "g.ssr": "crawlers get no server-rendered body text"}

def share_line(res):
    """One line someone can paste somewhere. Short enough for a post, specific enough
    to mean something — the score, the band, and the single biggest gap."""
    rows, total, den, b, norm, bd, capped = score(res)
    host = urllib.parse.urlsplit(res["root"]).netloc.replace("www.", "") + \
           urllib.parse.urlsplit(res["root"]).path
    top = top_gaps(rows, 1)
    line = "%s scores %d/100 (%s) for AI answer-engine readiness." % (host, norm, bd)
    if capped:
        zero = [cid for cid, _pil, _name, t, _mx, _e in rows if cid.startswith("g.") and t == 0]
        line += " Gate-capped — %s." % "; ".join(GATE_SHARE.get(cid, "%s is at zero" % cid) for cid in zero)
    elif top:
        line += " Biggest gap: %s (+%d at the next tier)." % (top[0][1].lower(), top[0][2])
    return line + " Measured with the open AIV rubric — github.com/jianruntech/geo-score"

# why a check that can be observed was not this run, in a few words for the report's footer; the evidence
# carries the whole sentence
UNOBSERVED = {"p1.breadcrumb": "no nested page sampled", "p4.cn-engines": "not a Chinese-language site",
              "p3.sameas": "no profile answered from this network",
              "p3.knowledge-graph": "Wikidata and Wikipedia did not all answer",
              "g.robots": "robots.txt could not be read"}

def unobserved_reason(cid, ev):
    """A few words on why this run did not observe a check, from its evidence."""
    ev = str(ev or "")
    if ev.startswith("The run reached its"):
        return "the run's time limit came first"
    if cid in UNOBSERVED:
        return UNOBSERVED[cid]
    why = clip(re.split(r"\s+—\s+|[;:]\s|\.(?:\s|$)", ev.strip(), maxsplit=1)[0], 60)
    return why[:1].lower() + why[1:] if why[1:2].islower() else why

LEGEND = "✓ full · ◐ partial · ✗ zero · ⊘ not measured (left the denominator)"

def landed_note(res):
    """A one-line note when the site handed back a different origin than the one asked
    for. Silence here is how a reader ends up thinking neon.tech was scored when
    neon.com was, or that aliyun.com was scored when its English edition was."""
    root, landed = res.get("root", ""), res.get("landed") or ""
    if not landed:
        return None
    def apex(u):
        h = urllib.parse.urlsplit(u if "://" in u else "https://" + u).netloc.lower().split(":")[0]
        return h[4:] if h.startswith("www.") else h
    a, b = apex(root), apex(landed)
    return None if a == b else "redirected to %s — that is what was scored" % b

def sample_notes(res):
    """What a report says about its sample (schema/report.v2.json, sampled_urls): fewer pages scored than were
    sampled, and why, and fewer sampled than were asked for. None of it for a full sample."""
    s = res.get("sampled")
    if not s:
        return []
    out, n = [], len(res.get("urls") or [])
    if n < s["drawn"]:
        out.append("Scored on %d of %d sampled pages; %d returned %s, %d %s." % (
            n, s["drawn"], s["errors"], "an error" if s["errors"] == 1 else "errors",
            s["challenges"], "was a bot challenge" if s["challenges"] == 1 else "were bot challenges"))
    if not s["pinned"] and s["drawn"] < s["asked"]:
        out.append("Sampled %d of the %d pages asked for: no more were found (sample source: %s)."
                   % (s["drawn"], s["asked"], res.get("sample_source")))
    return out


def to_next_band(gap):
    """How far the score is from the next band up, gap being (points, band): "12 points to Leading", "1 point to
    Solid"."""
    return "%d point%s to %s" % (gap[0], "" if gap[0] == 1 else "s", gap[1])

def brief(res):
    """Pillar totals and the three biggest gaps. What fits in a screenshot."""
    rows, total, den, b, norm, bd, capped = score(res)
    nxt = [(t, n) for t, n in BANDS if t > norm]
    gap = (min(nxt)[0] - norm, min(nxt, key=lambda x: x[0])[1]) if nxt else None
    big = c.green if norm >= 66 else (c.amber if norm >= 31 else c.red)
    print()
    print("  %s%sAIV READINESS%s  %s" % (c.b, c.brass, c.r, res["root"]))
    _ln = landed_note(res)
    if _ln: print("  %s%s%s" % (c.amber, _ln, c.r))
    print(c.grey + "─" * 58 + c.r)
    print("  %s%s%d / 100%s   %s%s%s%s" % (c.b, big, norm, c.r, c.b, big, bd, c.r)
          + ("%s          %s%s" % (c.grey, to_next_band(gap), c.r) if gap else ""))
    gl = gate_line(rows)
    if gl: print("  %s%s%s" % (c.red, gl, c.r))
    print()
    for pil in dict.fromkeys(r[1] for r in rows):
        rs = [r for r in rows if r[1] == pil]
        got = sum(r[3] for r in rs if r[3] is not None)
        mx = sum(r[4] for r in rs if r[3] is not None)
        marks = "".join((c.grey + "⊘" + c.r) if r[3] is None else
                        (c.green + "✓" + c.r if r[3] == r[4] else
                         (c.red + "✗" + c.r if r[3] == 0 else c.amber + "◐" + c.r)) for r in rs)
        print("  %-20s %s%6s%s   %s" % (pil, c.dim, ("%d/%d" % (got, mx)) if mx else "—", c.r, marks))
    print("  %s%s%s" % (c.grey, LEGEND, c.r))
    gaps = top_gaps(rows)
    if gaps:
        print()
        print("  %sBiggest gaps%s" % (c.b, c.r))
        for _cid, name, gain, full, _needs in gaps:
            print("   %s+%d next tier (+%d to full)%s  %s" % (c.brass, gain, full, c.r, name))
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
    if gap: print("  %s%s%s" % (c.grey, to_next_band(gap), c.r))
    gl = gate_line(rows)
    if gl: print("  %s%s%s" % (c.red, gl, c.r))
    _ln = landed_note(res)
    if _ln: print("  %s%s%s" % (c.amber, _ln, c.r))
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
                if tr: print("      %s%s%s" % (c.brass, clip(tr, 112), c.r))
            if e: print("      %s%s%s" % (c.dim, clip(e, 112), c.r))
            if t is not None and t < mx: print("      %s%s%s" % (c.grey, doc_url(cid), c.r))
    print("  %s%s%s" % (c.grey, LEGEND, c.r))
    print()
    gaps = top_gaps(rows)
    if gaps:
        print("  %sBiggest gaps%s" % (c.b, c.r))
        for _cid, name, gain, full, needs in gaps:
            print("   %s+%d next tier (+%d to full)%s  %-32s %s%s%s" % (
                c.brass, gain, full, c.r, name, c.grey, (" needs: " + clip(needs, 72)) if needs else "", c.r))
        print()
    if b: print("  %s+%d bonus%s (outside the denominator)" % (c.brass, b, c.r))
    skipped = [r for r in rows if r[3] is None]
    took = res.get("elapsed_s")
    print("  %sScored %d / %d observable · %d checks left the denominator · rubric %s%s%s"
          % (c.grey, total, den, len(skipped), RUBRIC, " · took %.1f s" % took if took is not None else "", c.r))
    for note in sample_notes(res):
        print("  %s%s%s" % (c.grey, note, c.r))
    judged = [r[0] for r in skipped if r[0] in NEEDS_JUDGEMENT]
    unseen = ["%s (%s)" % (r[0], unobserved_reason(r[0], r[5])) for r in skipped if r[0] not in NEEDS_JUDGEMENT]
    if judged:
        print("  %sNeeds off-site search or judgement: %s%s" % (c.grey, ", ".join(judged), c.r))
    if unseen:
        print("  %sNot observable this run: %s%s" % (c.grey, ", ".join(unseen), c.r))
    acc = access_lines(res.get("access"), origin=shown_origin(res["root"]), start=res["root"])
    if acc:
        print()
        print("  %sOutside the score%s %s(observed, never scored)%s" % (c.b, c.r, c.grey, c.r))
        for ln in acc:
            # a table row keeps its columns; a sentence wraps
            text = "    " + ln if ln.startswith(" ") else textwrap.fill(ln, W + 20, initial_indent="  ",
                                                                         subsequent_indent="    ")
            print("%s%s%s" % (c.dim, text, c.r))
    print()
    print("  %sFull rubric and what each tier means:%s" % (c.grey, c.r))
    print("  %s%s%s" % (c.brass, RUBRIC_URL, c.r))
    print("  %sScore moved, or a check shows —? %s%s" % (c.grey, TROUBLESHOOTING_URL, c.r))
    print()

# pinned to this release's tag, like doc_url(): the page explains the scorer that printed the link
TROUBLESHOOTING_URL = "https://github.com/jianruntech/geo-score/blob/v%s/guide/troubleshooting.md" % __version__

def as_json(res):
    rows, total, den, b, norm, bd, capped = score(res)
    extra = {"citation": res["citation"]} if res.get("citation") else {}
    return dict(extra, rubric_version=RUBRIC, tool="geo-score-cli/%s" % __version__,
        audited_at=time.strftime("%Y-%m-%d"),
        **({"elapsed_s": res["elapsed_s"]} if res.get("elapsed_s") is not None else {}),
        target=res["root"], audience_language=res["lang"], sampled_urls=res["urls"], sample_source=res.get("sample_source"),
        **({"landed": res["landed"]} if landed_note(res) else {}),
        readiness=total, observable_max=den, normalised=norm, band=bd,
        gate_capped=capped, bonus_awarded=b,
        checks=[dict(id=cid, state="scored" if t is not None else "unobservable",
                     **({"points": t, "max": mx, "evidence": e,
                         "tier_reason": tier_reason(cid, t, mx)}
                        if t is not None else {"reason": e}), doc_url=doc_url(cid))
                for cid, pil, name, t, mx, e in rows]
               + [dict(id=bid, state="scored", points=res["bonus"].get(bid, 0), max=bpts,
                       evidence="Bonus check, outside the denominator.", doc_url=doc_url(bid))
                  for bid, bname, bpts in BONUS],
        notes=["Scored by the geo-score CLI, which measures what a static fetch can observe. "
               "Checks needing off-site search or human judgement left the denominator."] + sample_notes(res),
        **({"access": res["access"]} if res.get("access") else {}))

RUBRIC_URL = "https://github.com/jianruntech/geo-score/blob/v%s/rubric/%s.md" % (__version__, RUBRIC)
# GitHub heading anchors in rubric/v1.1.md; test_geo_score.py checks every one still exists
DOC_ANCHOR = {
    "g.robots": "retrieval-crawlers-allowed-in-robotstxt--5-pts--grobots",
    "g.reachable": "reachable-to-retrieval-user-agents--5-pts--greachable",
    "g.ssr": "main-content-server-rendered--5-pts--gssr",
    "p1.sitemap": "sitemap-discoverable-and-fresh--4-pts--p1sitemap",
    "p1.llms-txt": "llmstxt-present-and-structured--5-pts--p1llms-txt",
    "p1.organization": "organization--website-sitewide--6-pts--p1organization",
    "p1.breadcrumb": "breadcrumblist-on-nested-pages--3-pts--p1breadcrumb",
    "p1.page-type": "page-type-schema-where-applicable--4-pts--p1page-type",
    "p2.answer-passages": "self-contained-answer-passages--9-pts--p2answer-passages",
    "p2.question-intent": "headings-match-how-people-ask--7-pts--p2question-intent",
    "p2.freshness": "freshness-signal-present--6-pts--p2freshness",
    "p2.sourced-stats": "statistics-carry-a-source--7-pts--p2sourced-stats",
    "p2.named-author": "named-verifiable-authorship--6-pts--p2named-author",
    "p3.listings": "third-party-listings--4-pts--p3listings",
    "p3.mentions": "independent-mentions--4-pts--p3mentions",
    "p3.knowledge-graph": "knowledge-graph-entity--4-pts--p3knowledge-graph",
    "p3.sameas": "sameas-complete-and-resolving--3-pts--p3sameas",
    "p3.video": "video-and-multimodal-presence--3-pts--p3video",
    "p4.answer-shape": "content-shaped-for-extraction--4-pts--p4answer-shape",
    "p4.question-coverage": "coverage-of-the-questions-people-ask--4-pts--p4question-coverage",
    "p4.cn-engines": "chinese-engine-readiness--2-pts--p4cn-engines",
    "b.llms-full": "llms-fulltxt--2-pts--bllms-full",
    "b.ai-txt": "aitxt--2-pts--bai-txt",
    "b.geo-link": "geo-link-tags--1-pts--bgeo-link",
    "b.speakable": "speakable-markup--1-pts--bspeakable",
}

def doc_url(cid):
    """Where a check is defined, pinned to this release's tag so the link never drifts from the scorer."""
    return "https://github.com/jianruntech/geo-score/blob/v%s/rubric/%s.md#%s" % (__version__, RUBRIC, DOC_ANCHOR[cid])

def _level(cid, t, mx):
    """How loudly a CI system should show a check: a gate at zero blocks citation outright."""
    if t == 0:
        return "error" if cid.startswith("g.") else "warning"
    return "note"

def _repo_path(path):
    """A path as a code-scanning location: relative to the working directory (the checkout root in CI),
    with forward slashes. GitHub rejects a location whose URI scheme differs from the checkout's file://."""
    return os.path.relpath(os.path.abspath(path)).replace(os.sep, "/")


def check_lines(json_text):
    """{check id: 1-based line} in a report written by json.dumps(as_json(...), indent=2)."""
    out = {}
    for i, ln in enumerate(json_text.splitlines(), 1):
        m = re.match(r'\s*"id": "([a-z0-9.\-]+)"', ln)
        if m and m.group(1) not in out:
            out[m.group(1)] = i
    return out


def as_sarif(res, artifact="geo-score.sarif", lines=None):
    """SARIF 2.1.0: one rule per rubric check, one result per check below full marks.

    Every result needs a file in the repository and a line (GitHub code scanning rejects a location whose
    URI is the scored website). Each result points at `artifact`, normally the --json-out report, at the
    line where that check sits (`lines`), or at line 1. The site itself is in the message and in
    logicalLocations, which viewers show next to the file."""
    rows, total, den, b, norm, bd, capped = score(res)
    target = res["root"]
    lines = lines or {}
    rules = [{"id": cid, "name": re.sub(r"[^A-Za-z0-9]+", " ", name).title().replace(" ", ""),
              "shortDescription": {"text": name},
              "helpUri": doc_url(cid),
              "properties": {"pillar": pil, "points": pts, "tags": ["geo", "ai-visibility", pil.lower().replace(" ", "-")]}}
             for cid, pil, name, pts, _ in SPEC]
    results = []
    for cid, pil, name, t, mx, e in rows:
        if t is None or t >= mx:
            continue
        tr = tier_reason(cid, t, mx)
        results.append({
            "ruleId": cid, "level": _level(cid, t, mx),
            "message": {"text": "%s on %s: %d/%d. %s%s" % (name, target, t, mx, e, (" " + tr) if tr else "")},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": artifact},
                                                "region": {"startLine": lines.get(cid, 1)}},
                           "logicalLocations": [{"fullyQualifiedName": target, "kind": "resource"}]}],
            "partialFingerprints": {"geoScoreCheck/v1": "%s|%s" % (cid, target)},
            "properties": {"points": t, "max": mx, "pillar": pil}})
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "geo-score", "version": __version__, "semanticVersion": __version__,
                                          "informationUri": "https://github.com/jianruntech/geo-score", "rules": rules}},
                      "automationDetails": {"id": "geo-score/%s/" % urllib.parse.urlsplit(target).netloc},
                      "results": results,
                      "properties": {"rubric": RUBRIC, "readiness": total, "observable_max": den,
                                     "normalised": norm, "band": bd, "gate_capped": capped}}]}

def as_junit(res):
    """JUnit XML: one test per rubric check. A check at zero fails; partial credit passes with its points
    in the name; a check the CLI cannot observe is skipped, never failed."""
    from xml.sax.saxutils import escape, quoteattr
    rows, total, den, b, norm, bd, capped = score(res)
    fails = sum(1 for r in rows if r[3] == 0)
    skips = sum(1 for r in rows if r[3] is None)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<testsuites name="geo-score" tests="%d" failures="%d" skipped="%d">' % (len(rows), fails, skips),
           '  <testsuite name=%s tests="%d" failures="%d" skipped="%d" timestamp="%s">'
           % (quoteattr("AIV readiness %s" % res["root"]), len(rows), fails, skips, time.strftime("%Y-%m-%dT%H:%M:%S")),
           '    <properties>']
    for k, v in (("normalised", norm), ("band", bd), ("rubric", RUBRIC), ("tool", __version__), ("gate_capped", capped)):
        out.append('      <property name=%s value=%s/>' % (quoteattr(k), quoteattr(str(v))))
    out.append('    </properties>')
    for cid, pil, name, t, mx, e in rows:
        e = _UNSAFE.sub("", e or "")      # XML 1.0 cannot carry controls or U+FFFE/FFFF, whatever produced the report
        label = "%s %s (%s)" % (cid, name, "—" if t is None else "%d/%d" % (t, mx))
        out.append('    <testcase classname=%s name=%s>' % (quoteattr("geo-score." + pil.replace(" ", "")), quoteattr(label)))
        if t is None:
            out.append('      <skipped message=%s/>' % quoteattr("not observable by the CLI: " + e[:300]))
        elif t == 0:
            out.append('      <failure message=%s type=%s>%s</failure>'
                       % (quoteattr("%s scored 0/%d" % (name, mx)), quoteattr("gate" if cid.startswith("g.") else "check"),
                          escape(e + " " + tier_reason(cid, t, mx))))
        out.append('    </testcase>')
    out += ['  </testsuite>', '</testsuites>']
    return "\n".join(out) + "\n"

# ── CI assertions ─────────────────────────────────────────────────────────
# --assert CHECK OP VALUE: CHECK is a check id or an fnmatch glob over the rubric's ids, OP is >=, > or =,
# VALUE a whole number or "max". CI policy, not measurement: the result never enters the report.
ASSERT_RE = re.compile(r"^\s*([A-Za-z0-9_.*?\[\]!-]+)\s*(>=|>|=)\s*(\d+|max)\s*$")

def parse_assert(expr):
    """(expression, the ids it names, op, value). A malformed expression, or a glob that names no check,
    raises ValueError: a typo must not pass CI by asserting nothing."""
    m = ASSERT_RE.match(expr)
    if not m:
        raise ValueError("--assert %r is not CHECK OP VALUE, e.g. 'g.*>0', 'g.robots=max' or 'p1.llms-txt>=4'"
                         % expr[:80])
    pat, op, val = m.groups()
    ids = [i for i in [c[0] for c in SPEC] + [b[0] for b in BONUS] if fnmatch.fnmatchcase(i, pat)]
    if not ids:
        raise ValueError("--assert %r: %s names no check (ids look like g.robots or p1.llms-txt)" % (expr[:80], pat))
    return expr.strip(), ids, op, (val if val == "max" else int(val))

def check_assertions(rep, asserts):
    """Parsed assertions against a report from as_json(): [(expression, id, points, max, passed)]. A check
    the run could not observe gives points None and passed None: skipped, never failed."""
    by = {c["id"]: c for c in rep["checks"]}
    out = []
    for expr, ids, op, val in asserts:
        for cid in ids:
            c = by.get(cid) or {}
            if c.get("state") != "scored":
                out.append((expr, cid, None, c.get("max"), None))
                continue
            got, mx = c["points"], c["max"]
            want = mx if val == "max" else val
            out.append((expr, cid, got, mx, got >= want if op == ">=" else got > want if op == ">" else got == want))
    return out

# ── comparing two reports ─────────────────────────────────────────────────
DIFF_FORMAT = "geo-score/diff.v1"
# a check's state between two reports (schema/diff.v1.json). A check that stopped being observed is never a drop to
# zero: it left the denominator, and the report that could not observe it has no points for it
DIFF_STATES = ("up", "down", "same", "became unobservable", "became observable", "unobservable")
SPREAD = 5      # benchmark/REPRODUCIBILITY.md: read one site's score as ±5 between runs that sampled different pages

def _clean(s, n=500):
    """A string from a report file, safe to print: a report is data, and a crafted one must not steer a terminal."""
    return " ".join(_UNSAFE.sub("", str(s)).split())[:n]

def _whole(v):
    return isinstance(v, int) and not isinstance(v, bool)

def load_report(path, what="report"):
    """A level-1 JSON report (schema/report.v2.json) read from path, checked for every field a comparison reads.
    Anything else is a ScoreError: exit 2."""
    def refuse(why):
        return ScoreError("%s %s is not a geo-score report (schema/report.v2.json): %s; pass a report written by "
                          "--json or --json-out" % (what, path, why), kind="usage")
    try:
        with io.open(path, encoding="utf-8-sig") as f:
            d = json.load(f)
    except OSError as e:
        raise ScoreError("cannot read %s %s: %s" % (what, path, e.strerror or e), kind="usage") from None
    except ValueError:
        raise refuse("it is not JSON") from None
    if isinstance(d, list):
        raise refuse("it holds %d reports (written with --compare); pass one" % len(d))
    if not isinstance(d, dict):
        raise refuse("it is not a JSON object")
    rv = d.get("rubric_version")
    if not isinstance(rv, str) or not re.match(r"^v1\.[1-9]\d*$", rv):
        raise refuse("its rubric_version is %s, where report.v2 needs v1.1 or later"
                     % (_clean(json.dumps(rv), 40) if rv is not None else "missing"))
    for k, t in (("target", str), ("band", str), ("gate_capped", bool), ("sampled_urls", list), ("checks", list)):
        if not isinstance(d.get(k), t):
            raise refuse("it has no %s" % k)
    for k in ("readiness", "observable_max", "normalised"):
        if not _whole(d.get(k)) or d[k] < 0:
            raise refuse("it has no whole-number %s" % k)
    if d["normalised"] > 100:
        raise refuse("its normalised score is above 100")
    if not all(isinstance(u, str) for u in d["sampled_urls"]):
        raise refuse("its sampled_urls holds something other than URLs")
    for x in d["checks"]:
        if not isinstance(x, dict) or not isinstance(x.get("id"), str) or not isinstance(x.get("state"), str):
            raise refuse("a check has no id or state")
        if x["state"] == "scored" and not (_whole(x.get("points")) and _whole(x.get("max"))
                                           and 0 <= x["points"] <= x["max"] and x["max"] >= 1):
            raise refuse("the scored check %s has no points from 0 to its max" % _clean(x["id"], 40))
    return d

def same_rubric(before, after, before_name, after_name):
    """Scores from different rubric versions are not comparable: exit 2 rather than compare them."""
    if before["rubric_version"] != after["rubric_version"]:
        raise ScoreError("%s was scored against rubric %s and %s against rubric %s; scores from different rubric "
                         "versions are not comparable" % (before_name, _clean(before["rubric_version"], 20), after_name,
                                                          _clean(after["rubric_version"], 20)), kind="rubric_mismatch")

def tool_note(before_tool, after_tool):
    """The warning when two reports come from different releases, or None."""
    if before_tool == after_tool:
        return None
    return ("The reports were written by different releases (%s, then %s). A release can move a score on its own, "
            "and the changelog names the checks it changed, so part of this difference may be the tool."
            % (before_tool or "tool not stated", after_tool or "tool not stated"))

def target_note(before_target, after_target):
    """The warning when two reports scored different targets, or None: a comparison of two sites is no change."""
    if before_target == after_target:
        return None
    return "The reports scored different targets: %s, then %s." % (before_target, after_target)

def diff_warnings(d):
    """What diff and --baseline print on stderr before the comparison: a change of release, and of target."""
    return [w for w in (tool_note(d["before"]["tool"], d["after"]["tool"]),
                        target_note(d["before"]["target"], d["after"]["target"])) if w]

def diff_reports(before, after, before_name=None, after_name=None):
    """Two reports of one rubric version, check by check (schema/diff.v1.json). Every SPEC and BONUS id gets a row,
    then any other id a report carries. --fail-on-drop reads `regressed`: a check that lost points, a gate that
    reached zero, or a band that fell. A check that became unobservable is none of these."""
    by = ({x["id"]: x for x in before["checks"]}, {x["id"]: x for x in after["checks"]})
    ids = [spec[0] for spec in SPEC] + [b[0] for b in BONUS]
    maxes = dict([(spec[0], spec[3]) for spec in SPEC] + [(b[0], b[2]) for b in BONUS])
    for cid in list(by[0]) + list(by[1]):
        if cid not in ids:
            ids.append(cid)

    def points(side, cid):
        x = by[side].get(cid) or {}
        return x["points"] if x.get("state") == "scored" else None
    checks = []
    for cid in ids:
        pb, pa = points(0, cid), points(1, cid)
        mx = (by[1].get(cid) or {}).get("max") or (by[0].get(cid) or {}).get("max") or maxes.get(cid)
        if pb is None and pa is None:
            state = "unobservable"
        elif pa is None:
            state = "became unobservable"
        elif pb is None:
            state = "became observable"
        else:
            state = "up" if pa > pb else "down" if pa < pb else "same"
        checks.append(dict(id=_clean(cid, 60), before=pb, after=pa, max=mx if _whole(mx) else None, state=state))
    zero = [[x["id"] for x in checks if x["id"].startswith("g.") and x[k] == 0] for k in ("before", "after")]
    lost = [x["id"] for x in checks if x["state"] == "down"]
    reached = [g for g in zero[1] if g not in zero[0]]
    nb, na = before["normalised"], after["normalised"]
    rank = {n: i for i, (_t, n) in enumerate(BANDS)}          # 0 is the top band
    band_fell = rank[band(max(0, min(100, na)))] > rank[band(max(0, min(100, nb)))]
    keys = [{u.rstrip("/") for u in r["sampled_urls"]} for r in (before, after)]
    added = [_clean(u) for u in after["sampled_urls"] if u.rstrip("/") not in keys[0]]
    removed = [_clean(u) for u in before["sampled_urls"] if u.rstrip("/") not in keys[1]]
    same_pages = not added and not removed

    def side(r, name, gates):
        opt = lambda k, n: _clean(r[k], n) if isinstance(r.get(k), str) else None
        return dict(file=_clean(name) if name else None, target=_clean(r["target"]), tool=opt("tool", 120),
                    audited_at=opt("audited_at", 40), sample_source=opt("sample_source", 80),
                    pages=len(r["sampled_urls"]), readiness=r["readiness"], observable_max=r["observable_max"],
                    normalised=r["normalised"], band=_clean(r["band"], 40), gate_capped=r["gate_capped"],
                    gates_at_zero=gates)
    b, a = side(before, before_name, zero[0]), side(after, after_name, zero[1])
    notes = [n for n in [tool_note(b["tool"], a["tool"]), target_note(b["target"], a["target"])] if n]
    if not same_pages:
        notes.append("Different pages were sampled, so movement on a check mixes change on the site with sampling. "
                     "Read each total as ±%d, the run-to-run spread measured in benchmark/REPRODUCIBILITY.md. "
                     "g.reachable is the least stable check: some sites answer crawlers differently from one minute "
                     "to the next. Re-score the same pages (--urls-from, or --baseline) to see the site alone." % SPREAD)
    else:
        notes.append("Both reports scored the same %d page%s, so a difference comes from the site, not from sampling."
                     % (a["pages"], "" if a["pages"] == 1 else "s"))
        if next(x for x in checks if x["id"] == "g.reachable")["state"] not in ("same", "unobservable"):
            notes.append("g.reachable reads how the site answered crawlers at that moment; some sites answer "
                         "differently from one minute to the next.")
    return {"format": DIFF_FORMAT, "tool": "geo-score-cli/%s" % __version__,
            "rubric_version": _clean(after["rubric_version"], 20), "before": b, "after": a,
            "normalised_delta": na - nb, "within_spread": not same_pages and abs(na - nb) <= SPREAD,
            "band_fell": band_fell, "same_pages": same_pages, "pages_added": added, "pages_removed": removed,
            "gates_reached_zero": reached, "gates_left_zero": [g for g in zero[0] if g not in zero[1]],
            "lost_points": lost, "regressed": bool(lost or reached or band_fell), "checks": checks, "notes": notes}

def dropped_checks(d):
    """The checks behind a regression, in rubric order: each that lost points, and each gate that reached zero."""
    hit = set(d["lost_points"]) | set(d["gates_reached_zero"])
    return [x["id"] for x in d["checks"] if x["id"] in hit]

def drop_lines(d):
    """One line per reason --fail-on-drop fails, for stderr."""
    out = []
    for x in d["checks"]:
        if x["id"] in d["lost_points"]:
            lost = x["before"] - x["after"]
            out.append("%s lost %d point%s (%d/%s → %d/%s)%s" % (
                x["id"], lost, "" if lost == 1 else "s", x["before"], x["max"], x["after"], x["max"],
                "; a gate at 0 caps the score at %d" % GATE_CAP if x["id"] in d["gates_reached_zero"] else ""))
        elif x["id"] in d["gates_reached_zero"]:
            out.append("%s is at 0 and was not observed before; a gate at 0 caps the score at %d" % (x["id"], GATE_CAP))
    if d["band_fell"]:
        out.append("the band fell from %s to %s (%d → %d)" % (d["before"]["band"], d["after"]["band"],
                                                              d["before"]["normalised"], d["after"]["normalised"]))
    return out

def render_report_diff(d, fmt="text"):
    """The comparison as text or Markdown; the JSON form is d itself."""
    names = dict([(spec[0], spec[2]) for spec in SPEC] + [(b[0], b[1]) for b in BONUS])
    b, a = d["before"], d["after"]
    md = fmt == "md"
    title = "Changes %s → %s" % (b["file"] or "before", a["file"] or "this run")
    L = ["# " + title if md else title, ""]
    for label, s in (("before", b), ("after", a)):
        what = "%s · %s · %s · %d page%s (%s)" % (s["target"], s["audited_at"] or "date not stated",
                                                  s["tool"] or "tool not stated", s["pages"],
                                                  "" if s["pages"] == 1 else "s", s["sample_source"] or "source not stated")
        L.append("- %s: %s" % (label, what) if md else "  %-10s %s" % (label, what))
    L.append("")
    delta = d["normalised_delta"]
    moved = ("%+d" % delta if delta else "no change") + (", within the measured spread" if d["within_spread"] and delta
                                                          else "")
    gates = ["%s reached 0" % g for g in d["gates_reached_zero"]] + ["%s left 0" % g for g in d["gates_left_zero"]]
    for k, v in (("score", "%d → %d / 100 (%s) · %s" % (b["normalised"], a["normalised"], moved, b["band"]
                                                         if b["band"] == a["band"] else "%s → %s" % (b["band"], a["band"]))),
                 ("observable", "%d → %d points in the denominator" % (b["observable_max"], a["observable_max"])),
                 ("gate cap", "%s → %s%s" % ("yes" if b["gate_capped"] else "no", "yes" if a["gate_capped"] else "no",
                                             ": " + ", ".join(gates) if gates else ""))):
        L.append("- %s: %s" % (k, v) if md else "  %-10s %s" % (k, v))
    L.append("")
    rows = []
    for x in d["checks"]:
        rows.append((x["id"], names.get(x["id"], ""), "—" if x["before"] is None else str(x["before"]),
                     "—" if x["after"] is None else str(x["after"]), "—" if x["max"] is None else str(x["max"]),
                     x["state"] + (" %+d" % (x["after"] - x["before"]) if x["state"] in ("up", "down") else "")))
    head = ("check", "name", "before", "after", "max", "change")
    if md:
        L += ["| %s |" % " | ".join(head), "|---|---|--:|--:|--:|---|"]
        L += ["| `%s` | %s | %s | %s | %s | %s |" % r for r in rows]
    else:
        L += ["  %-20s %-32s %6s %6s %4s  %s" % ((r[0], r[1][:32]) + r[2:]) for r in [head] + rows]
    for label, urls in (("Pages added", d["pages_added"]), ("Pages removed", d["pages_removed"])):
        if urls:
            L += ["", "## %s (%d)" % (label, len(urls)) if md else "  %s (%d)" % (label, len(urls))]
            L += [("- " if md else "    ") + u for u in urls]
    L.append("")
    for n in d["notes"]:
        L += ["Note: " + n] if md else textwrap.wrap("Note: " + n, 100, initial_indent="  ", subsequent_indent="        ")
    return "\n".join(L) + "\n"

def diff_main(argv, prog="geo-score diff"):
    """`geo_score.py diff BEFORE AFTER`: two level-1 reports compared check by check. Exits 0, or 4 when
    --fail-on-drop finds a drop; a file that is not a report, or two rubric versions, exit 2."""
    # under --format json an exit 2 answers in JSON on stdout too (schema/error.v1.json), usage errors included
    fmt = next((x.split("=", 1)[1] for x in argv if x.startswith("--format=")), None) or \
        (argv[argv.index("--format") + 1] if "--format" in argv[:-1] else "text")
    _CLI.update(json=fmt == "json")
    ap = _Parser(prog=prog, description="Compare two level-1 JSON reports (schema/report.v2.json) check by check: "
                                        "points before and after, the score and band, the gates and the pages sampled.")
    ap.add_argument("before", metavar="BEFORE", help="the earlier report, written by --json or --json-out")
    ap.add_argument("after", metavar="AFTER", help="the later report")
    ap.add_argument("--format", choices=["text", "md", "json"], default="text",
                    help="text (default), md, or json (schema/diff.v1.json)")
    ap.add_argument("--fail-on-drop", action="store_true",
                    help="exit 4 when any check lost points, a gate reached 0 or the band fell. A check that became "
                         "unobservable is not a drop")
    a = ap.parse_args(argv)
    before, after = load_report(a.before, "BEFORE"), load_report(a.after, "AFTER")
    same_rubric(before, after, a.before, a.after)
    d = diff_reports(before, after, a.before, a.after)
    for warn in diff_warnings(d):
        print("%swarning: %s%s" % (c.amber, warn, c.r), file=sys.stderr)
    sys.stdout.write(json.dumps(d, ensure_ascii=False, indent=2) + "\n" if a.format == "json"
                     else render_report_diff(d, a.format))
    if a.fail_on_drop and d["regressed"]:
        for ln in drop_lines(d):
            print("%sgeo-score diff --fail-on-drop: %s%s" % (c.red, ln, c.r), file=sys.stderr)
        return 4
    return 0

def _write(path, text):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError as e:
        raise RuntimeError("cannot write %s: %s" % (path, e.strerror or e)) from None

# the package on PyPI carries geo_score.py and geo_watch.py together, with the geo-score and geo-score-mcp commands;
# the release attaches the same wheel, for a machine that cannot reach PyPI
RELEASE_WHEEL = ("https://github.com/jianruntech/geo-score/releases/download/v%s/geo_score-%s-py3-none-any.whl"
                 % (__version__, __version__))

def _watch_module(*, what="--ask"):
    """Levels 2 and 3 live in geo_watch.py beside this file. Piped through `curl | python3 -` there is no beside.
    `what` is what the user typed that needs it: watch, mcp or --ask."""
    import importlib.util
    args = {"mcp": "mcp", "watch": "watch …"}.get(what, "SITE --ask QUESTION")
    then = "geo-score-mcp" if what == "mcp" else "geo-score " + args
    need = ("%s needs geo_watch.py %s next to geo_score.py. The geo-score package on PyPI carries both: "
            "`uvx geo-score@%s %s`, or `pipx install geo-score==%s` and then `%s`. Without PyPI, the release wheel: "
            "`pipx install %s`. Or clone https://github.com/jianruntech/geo-score, or download "
            "cli/geo_score.py and cli/geo_watch.py from the same release"
            % (what, __version__, __version__, args, __version__, then, RELEASE_WHEEL))
    f = globals().get("__file__")
    # piped through `python3 -`, __file__ is "<stdin>": never go looking in the current directory
    here = os.path.dirname(os.path.abspath(f)) if f and os.path.isfile(f) else ""
    p = os.path.join(here, "geo_watch.py") if here else ""
    if not p or not os.path.isfile(p):
        raise RuntimeError(need)
    spec = importlib.util.spec_from_file_location("geo_watch", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if getattr(mod, "__version__", None) != __version__ or not callable(getattr(mod, "citation_check", None)):
        raise RuntimeError(need + " (found geo_watch.py %s)" % getattr(mod, "__version__", "of another version"))
    mod.GEO_SCORE = sys.modules[__name__]
    return mod

def citation_report(run, cit, watch):
    """Level 2 section under the readiness report. An outcome: printed apart, never summed into the score."""
    print("  %s%sAI CITATION CHECK%s  %s(API channel · not scored)%s" % (c.b, c.brass, c.r, c.grey, c.r))
    print(c.grey + "─" * 74 + c.r)
    lines = watch.citation_lines(run, cit)
    for ln in lines[:-1]:
        print("  " + ln)
    print("  %s%s%s" % (c.grey, lines[-1], c.r))
    print()

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
    trail = None
    for x in cols[1:]:
        if trail is None or x["norm"] > trail["norm"]: trail = x
    if trail:
        behind = sorted([(trail["rows"][k][3] - cols[0]["rows"][k][3], cols[0]["rows"][k][2])
                         for k in cols[0]["rows"]
                         if cols[0]["rows"][k][3] is not None and trail["rows"].get(k, (None,)*6)[3] is not None
                         and trail["rows"][k][3] > cols[0]["rows"][k][3]], reverse=True)[:3]
        if behind:
            print("  %sWhere %s is ahead of you%s" % (c.b, trail["host"], c.r))
            for d, nm in behind:
                print("   %s+%-2d%s  %s" % (c.brass, d, c.r, nm))
            print()
    print("  %s%s scored with rubric %s · %s%s"
          % (c.grey, "Both" if len(cols) == 2 else "All", RUBRIC, RUBRIC_URL, c.r))
    print()

def target_url(raw):
    """The URL to score, from what the user typed; ValueError says why it is not one. localhost, IP literals and
    intranet names without a dot are scored like any other host."""
    raw = raw.strip()
    if not raw or any(ch.isspace() for ch in raw):
        raise ValueError("%r is not a URL: it contains whitespace" % raw[:80] if raw else "the URL is empty")
    url = raw if "://" in raw else "https://" + raw
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError as e:
        raise ValueError("%s is not a URL (%s)" % (raw[:80], e)) from None
    if u.scheme.lower() not in ("http", "https"):
        raise ValueError("%s: only http:// and https:// sites can be scored" % raw[:80])
    if not u.hostname:
        raise ValueError("%s has no host name" % raw[:80])
    try:
        port = u.port
    except ValueError:              # not a number, or above 65535
        port = 0
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("%s: the port must be a number from 1 to 65535" % raw[:80])
    return url

class _Parser(argparse.ArgumentParser):
    """argparse, but a usage error under --json also prints the JSON error on stdout, as every other exit 2 does."""
    def error(self, message):
        if "--json" in sys.argv[1:] or _CLI["json"]:
            print(json.dumps(error_json("usage", message, None), ensure_ascii=False))
        argparse.ArgumentParser.error(self, message)

def error_json(kind, message, target):
    """The --json answer when nothing could be scored (schema/error.v1.json)."""
    return {"error": {"kind": kind, "message": message, "target": target}, "tool": "geo-score-cli/%s" % __version__}

HELP_USAGE = ("%(prog)s [options] URL\n"
              "       %(prog)s diff BEFORE.json AFTER.json [options]\n"
              "       %(prog)s watch {init,check,run,ask,report,diff,runs} [options]\n"
              "       %(prog)s mcp [options]")

# --help stands alone: what to type, the other commands, what each exit code means (as cli/README.md says) and
# where the rubric and the troubleshooting guide are, pinned to this release. Lines stay within 80 columns.
HELP_EXAMPLES = [("--brief", "pillar totals and biggest gaps"), ("--explain", "the evidence behind every check"),
                 ("--compare rival.com", "two sites side by side"), ("--urls-from r.json", "score r.json's pages again"),
                 ("--json-out r.json --sarif r.sarif", "a JSON report and SARIF, one run")]

def help_epilog(me):
    """The end of --help, naming the command the user typed."""
    w = len(me) + 32
    out = ["Examples:"]
    for flags, what in HELP_EXAMPLES:
        cmd = "%s example.com %s" % (me, flags)
        out.append("  %-*s  %s" % (w, cmd, what) if len(cmd) <= w else "  %s\n  %*s  %s" % (cmd, w, "", what))
    return "\n".join(out + [
        "",
        "Commands:",
        "  diff BEFORE AFTER  compare two JSON reports check by check",
        "  watch …            level 3, your API keys: citations week over week",
        "  mcp                serve all three levels over MCP (stdio)",
        "  URL --ask Q        level 2, your API keys: a live citation check",
        "",
        "Exit codes:",
        "  0  scored",
        "  1  below --fail-under, or a failed --fail-on-gate or --assert",
        "  2  could not fetch or score the site, a usage error, or an internal error",
        "  4  --fail-on-drop found a drop (with --baseline, or on diff); 1 wins over it",
        "  watch exits 0 done, 1 configuration error, 2 usage error or no geo_watch.py,",
        "  3 nothing measured (no key worked), 4 watch diff --fail-on-drop found a drop",
        "",
        "The rubric, and what each tier needs:",
        "  " + RUBRIC_URL,
        "When a reading looks wrong:",
        "  " + TROUBLESHOOTING_URL])

def main():
    global TIMEOUT, PREFLIGHT
    # the command the user typed, in usage lines, help and messages: geo_score.py from a checkout or a pipe,
    # geo-score after pip
    me = "geo-score" if os.path.basename(sys.argv[0]).startswith("geo-score") else "geo_score.py"
    if len(sys.argv) > 1 and sys.argv[1] == "diff":
        # level 1 only: comparing two reports needs nothing from geo_watch.py
        sys.exit(diff_main(sys.argv[2:], prog=me + " diff"))
    if len(sys.argv) > 1 and sys.argv[1] in ("watch", "mcp"):
        w = _watch_module(what=sys.argv[1])
        if sys.argv[1] == "watch":
            sys.exit(w.main(sys.argv[2:], prog=me + " watch"))
        sys.exit(w.main(["mcp"] + sys.argv[2:], prog=me))
    ap = _Parser(prog=me, usage=HELP_USAGE, epilog=help_epilog(me), formatter_class=argparse.RawDescriptionHelpFormatter,
                 description="Score a site 0-100 on whether AI answer engines can find, parse, trust and\ncite it.")
    ap.add_argument("url", metavar="URL",
                    help="domain, URL, or URL with a path (example.com, example.com/docs); https is assumed")
    ap.add_argument("--json", action="store_true", help="machine-readable output (schema/report.v2.json)")
    ap.add_argument("--json-out", metavar="FILE", help="also write the JSON report to FILE (one run, several outputs)")
    ap.add_argument("--sarif", metavar="FILE", help="also write SARIF 2.1.0 (code scanning, SARIF viewers) to FILE")
    ap.add_argument("--junit", metavar="FILE", help="also write JUnit XML (CI test reports) to FILE")
    ap.add_argument("--explain", "-e", action="store_true", help="show the evidence behind every check")
    ap.add_argument("--brief", action="store_true", help="pillar totals and the three biggest gaps only")
    ap.add_argument("--share", action="store_true",
                    help="print a one-line summary sized for a post, and the badge markdown")
    ap.add_argument("--badge", metavar="FILE", nargs="?", const="aiv-badge.svg",
                    help="also write an embeddable SVG badge (default aiv-badge.svg)")
    ap.add_argument("--badge-json", metavar="FILE",
                    help="also write the badge as shields.io endpoint JSON to FILE: host it anywhere and "
                         "https://img.shields.io/endpoint?url=<its URL> draws the badge")
    ap.add_argument("--sample", type=int, default=8, metavar="N", help="pages to sample, 1 or more (default 8)")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, metavar="SECONDS",
                    help="seconds to wait for each request before it counts as unanswered (default %d)" % DEFAULT_TIMEOUT)
    pin = ap.add_mutually_exclusive_group()
    pin.add_argument("--urls", metavar="FILE",
                     help="score exactly these pages (one URL per line, up to 8) instead of drawing a sample")
    pin.add_argument("--urls-from", metavar="REPORT",
                     help="score the pages an earlier JSON report sampled, so the re-score reads the same pages")
    pin.add_argument("--baseline", metavar="REPORT",
                     help="score the pages an earlier JSON report sampled (as --urls-from does), then print what "
                          "changed since that report, check by check. Under --json stdout is the report alone: "
                          "write it with --json-out and run diff on the two files for the comparison")
    ap.add_argument("--compare", metavar="URL", action="append",
                    help="also score this site and show the two side by side. Repeatable.")
    ap.add_argument("--fail-under", type=int, metavar="N", help="exit 1 if the score is below N (for CI)")
    ap.add_argument("--fail-on-drop", action="store_true",
                    help="with --baseline: exit 4 when any check lost points, a gate reached 0 or the band fell since "
                         "the baseline. A check that became unobservable is not a drop")
    ap.add_argument("--fail-on-gate", action="store_true",
                    help="exit 1 if any gate check (g.*) scores 0. A gate at zero caps the score at 40: a site that would "
                         "otherwise score 40 or more reads exactly 40 and passes --fail-under 40, and this fails any "
                         "capped site. The same as --assert 'g.*>0'")

    def assertion(expr):
        try:
            return parse_assert(expr)
        except ValueError as e:
            raise argparse.ArgumentTypeError(str(e)) from None
    ap.add_argument("--assert", dest="asserts", metavar="EXPR", action="append", type=assertion,
                    help="exit 1 unless CHECK OP VALUE holds, e.g. 'g.robots=max' or 'p1.*>=2': CHECK is a check id or a "
                         "glob over them, OP is >=, > or =, VALUE a number or max. Repeatable. A check the run could not "
                         "observe is skipped, never failed")
    ap.add_argument("--ask", metavar="QUESTION", action="append",
                    help="level 2: also ask ChatGPT, Perplexity, Gemini and Claude this question through their APIs "
                         "(your keys) and report who they cite. Repeatable, up to 5. Never part of the score.")
    ap.add_argument("--brand", metavar="NAME", help="with --ask: the brand name to look for (default: from the domain)")
    ap.add_argument("--domain", metavar="DOMAIN", action="append",
                    help="with --ask: another domain that counts as yours (the scored site always does). Repeatable.")
    ap.add_argument("--quiet", "-q", action="store_true", help="no progress lines on stderr")
    ap.add_argument("--version", action="version", version="geo-score %s (rubric %s)" % (__version__, RUBRIC))
    a = ap.parse_args()
    if (a.brand or a.domain) and not a.ask:
        ap.error("--brand and --domain only apply with --ask")
    if a.fail_on_drop and not a.baseline:
        ap.error("--fail-on-drop needs --baseline REPORT (or compare two saved reports with `diff BEFORE AFTER "
                 "--fail-on-drop`)")
    if a.ask:
        qs = [q.strip() for q in a.ask if q.strip()]
        if not 1 <= len(qs) <= 5 or len(qs) != len(a.ask) or any(len(q) > 500 for q in qs):
            ap.error("--ask takes 1 to 5 non-empty questions of up to 500 characters")
    if not 0 < a.timeout <= MAX_TIMEOUT:            # NaN fails both comparisons
        ap.error("--timeout takes a number of seconds above 0 and up to %d" % MAX_TIMEOUT)
    if a.sample < 1:
        ap.error("--sample takes a whole number of pages, 1 or more")
    try:
        targets = [target_url(u) for u in [a.url] + (a.compare or [])]
    except ValueError as e:
        ap.error(str(e))
    url = targets[0]
    _CLI.update(target=url, json=a.json)
    TIMEOUT, PREFLIGHT = a.timeout, True
    if not a.json and not a.quiet:
        print("%s  scoring %s …%s" % (c.dim, url, c.r), file=sys.stderr)
    if a.ask and len(targets) > 1:
        raise RuntimeError("--ask works with one site at a time; drop --compare")
    if (a.json_out or a.sarif or a.junit) and len(targets) > 1:
        raise RuntimeError("--json-out, --sarif and --junit work with one site at a time; drop --compare")
    pinned = baseline = drift = None
    if a.urls or a.urls_from or a.baseline:
        if len(targets) > 1:
            raise RuntimeError("--urls, --urls-from and --baseline work with one site at a time; drop --compare")
        if a.baseline:
            # read and checked before anything is fetched: a baseline that cannot be compared fails fast
            baseline = load_report(a.baseline, "--baseline")
            if baseline["rubric_version"] != RUBRIC:
                raise ScoreError("--baseline %s was scored against rubric %s and this tool scores rubric %s; scores "
                                 "from different rubric versions are not comparable"
                                 % (a.baseline, _clean(baseline["rubric_version"], 20), RUBRIC), kind="rubric_mismatch")
        got = read_url_list(a.urls) if a.urls else baseline["sampled_urls"] if baseline else read_report_urls(a.urls_from)
        # a report written with --sample above 8 pins as many pages as it sampled
        pinned = pin_urls(url, got, limit=None if a.urls else len(got))
    watch = _watch_module() if a.ask else None
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
        res = run(url, a.sample, verbose=not a.quiet and not a.json, urls=pinned)
        crun = None
        if watch:
            if not a.json and not a.quiet:
                print("%s  asking the AI engines %d question(s) …%s" % (c.dim, len(a.ask), c.r), file=sys.stderr)
            try:
                crun, res["citation"] = watch.citation_check(res["root"], a.ask, a.brand, a.domain, res.get("landed"))
            except watch.ConfigError as e:
                raise RuntimeError(str(e)) from None
        if a.json:
            print(json.dumps(as_json(res), ensure_ascii=False, indent=2))
        elif a.brief:
            brief(res)
        else:
            report(res, a)
        if watch and not a.json:
            citation_report(crun, res["citation"], watch)
        if baseline is not None:
            drift = diff_reports(baseline, as_json(res), a.baseline, None)
            for warn in diff_warnings(drift):
                print("%swarning: %s%s" % (c.amber, warn, c.r), file=sys.stderr)
            if not a.json:
                sys.stdout.write(render_report_diff(drift) + "\n")
        report_text = json.dumps(as_json(res), ensure_ascii=False, indent=2) + "\n"
        if a.json_out:
            _write(a.json_out, report_text)
        if a.sarif:
            # locate results in the JSON report when there is one, else in the SARIF file itself
            where = a.json_out or a.sarif
            _write(a.sarif, json.dumps(as_sarif(res, _repo_path(where), check_lines(report_text) if a.json_out else None),
                                       ensure_ascii=False, indent=2) + "\n")
        if a.junit:
            _write(a.junit, as_junit(res))
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
        pth = write_badge(res, a.badge)[0]
        if not a.json:
            print("  %sbadge%s %s  —  %s" % (c.brass, c.r, pth, badge_face(res)[0]))
            print("  %sMarkdown:%s ![AIV readiness](%s)" % (c.grey, c.r, os.path.basename(pth)))
            print()
    if a.badge_json:
        pth = write_badge_json(res, a.badge_json)
        if not a.json:
            print("  %sbadge JSON%s %s  —  %s" % (c.brass, c.r, pth, badge_face(res)[0]))
            print("  %sHost it at a public URL, then:%s ![AIV readiness](https://img.shields.io/endpoint?url=<URL-encoded "
                  "URL>)" % (c.grey, c.r))
            print()
    failed = False
    if a.fail_under is not None:
        _, _, _, _, norm, _, _ = score(res)
        if norm < a.fail_under:
            print("%sgeo-score %d is below --fail-under %d%s" % (c.red, norm, a.fail_under, c.r), file=sys.stderr)
            failed = True
    checks = [("--fail-on-gate", parse_assert("g.*>0"))] if a.fail_on_gate else []
    checks += [("--assert %s" % x[0], x) for x in a.asserts or []]
    if checks:
        rep = as_json(res)
        ev = {x["id"]: x.get("evidence", "") for x in rep["checks"]}
        for label, x in checks:
            for _expr, cid, got, mx, passed in check_assertions(rep, [x]):
                if passed is None:
                    print("%sgeo-score %s: %s not measured, skipped%s" % (c.grey, label, cid, c.r), file=sys.stderr)
                elif passed and not a.quiet:
                    print("%sgeo-score %s: %s %d/%d passes%s" % (c.grey, label, cid, got, mx, c.r), file=sys.stderr)
                elif not passed:
                    # one line per failure, whitespace collapsed: CI logs read commands at the start of a line
                    print("%sgeo-score %s: %s is %d/%d, failed — %s%s" % (c.red, label, cid, got, mx,
                          " ".join(clip(ev.get(cid, ""), 240).split()), c.r), file=sys.stderr)
                    failed = True
    dropped = a.fail_on_drop and drift is not None and drift["regressed"]
    for ln in drop_lines(drift) if dropped else []:
        print("%sgeo-score --fail-on-drop: %s%s" % (c.red, ln, c.r), file=sys.stderr)
    # exit 4 is opt-in, and a threshold or an assertion that failed keeps its exit 1
    if failed:
        sys.exit(1)
    if dropped:
        sys.exit(4)

ISSUES_URL = "https://github.com/jianruntech/geo-score/issues"
_CLI = {"target": None, "json": False}      # what main() is scoring, and whether it answers in JSON

def _fail(kind, message, target=None):
    """Exit 2: the message on stderr, and under --json the JSON error on stdout, so a pipeline never reads nothing."""
    message = " ".join(_UNSAFE.sub("", message).split())
    print("%s%s%s" % (c.red, message, c.r), file=sys.stderr)
    if _CLI["json"]:
        print(json.dumps(error_json(kind, message, target or _CLI["target"]), ensure_ascii=False))
    sys.exit(2)

def cli():
    """Console entry point (`geo-score` after `pipx install`); the same exits as running the file."""
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except RuntimeError as e:
        _fail(getattr(e, "kind", "error"), str(e), getattr(e, "target", None))
    except Exception as e:
        # a bug, or input no one foresaw: one line and exit 2, never a traceback that exits 1, which CI reads
        # as "below --fail-under". GEO_SCORE_DEBUG=1 shows the traceback.
        if os.environ.get("GEO_SCORE_DEBUG") == "1":
            raise
        _fail("internal", "geo-score internal error (%s)%s; please report it at %s" % (
            type(e).__name__, " while scoring %s" % _CLI["target"] if _CLI["target"] else "", ISSUES_URL))

def mcp_main():
    """Console entry point `geo-score-mcp`: the MCP server over stdio, for MCP client configs."""
    sys.argv = [sys.argv[0], "mcp"] + sys.argv[1:]
    cli()

if __name__ == "__main__":
    cli()
