#!/usr/bin/env python3
"""Offline tests for `geo-score crawlers LOG…`: the AI crawlers in a site's own access logs.

    python3 cli/test_crawler_logs.py

The fixtures in cli/fixtures/logs/ are made up: documentation addresses (RFC 5737, RFC 3849) and example.com. They
hold every format the command reads (nginx and Apache combined, Vercel and Cloudflare JSON lines, other JSON lines),
a forged GPTBot user-agent, bad lines, and range files in two shapes. The large-file and odd-input cases are built in
a temporary directory. When jsonschema is importable, every JSON answer is validated against schema/crawlers.v1.json
or schema/error.v1.json (check.sh runs this file again with the pinned jsonschema).
"""
import calendar, gzip, importlib.util, io, json, os, random, re, shutil, subprocess, sys, tempfile, time, tracemalloc, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(HERE, "fixtures", "logs")
CLI = os.path.join(HERE, "geo_score.py")
spec = importlib.util.spec_from_file_location("geo_score_logs_under_test", CLI)
gs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gs)
try:
    import jsonschema
except ImportError:
    jsonschema = None


def fx(name):
    return os.path.join(LOGS, name)


ALL = [fx("combined.log"), fx("vercel.jsonl"), fx("cloudflare.jsonl"), fx("json-lines.jsonl")]
EPOCH = calendar.timegm((2026, 11, 19, 5, 0, 0))          # 2026-11-19T05:00:00Z, in seconds


def schema(name):
    with io.open(os.path.join(ROOT, "schema", name), encoding="utf-8") as f:
        return json.load(f)


def by_name(rep):
    return dict((c["name"], c) for c in rep["crawlers"])


def run(*args, stdin=None):
    return subprocess.run([sys.executable, CLI, "crawlers"] + list(args), capture_output=True, text=True,
                          input=stdin, timeout=120)


class Reference(unittest.TestCase):
    """The crawlers the command counts are reference/ai-crawlers.md's, kinds and operators included."""

    def table(self, heading):
        with io.open(os.path.join(ROOT, "reference", "ai-crawlers.md"), encoding="utf-8") as f:
            part = f.read().split(heading, 1)[1].split("\n## ", 1)[0]
        return [[c.strip() for c in row.split("|")[1:4]] for row in re.findall(r"^\| `[^\n]+", part, re.M)]

    def test_the_lists_are_the_reference_tables(self):
        retrieval = self.table("## Retrieval crawlers")
        training = self.table("## Training crawlers")
        self.assertEqual([(n.strip("`"), o) for n, o, _ in retrieval],
                         [(n, gs.RETRIEVAL_OPERATORS[n]) for n, _ in gs.RETRIEVAL_UAS])
        self.assertEqual([(n.strip("`"), o) for n, o, _ in training], gs.TRAINING_UAS)
        self.assertEqual(sorted(gs.LIVE_FETCHERS), sorted(n.strip("`") for n, _, role in retrieval if "user" in role.lower()))
        self.assertEqual([c["name"] for c in gs.LOG_CRAWLERS],
                         [n for n, _ in gs.RETRIEVAL_UAS] + [n for n, _ in gs.TRAINING_UAS]
                         + [n for n, _, _ in gs.LOG_ONLY_UAS])
        self.assertEqual(schema("crawlers.v1.json")["properties"]["crawlers"]["items"]["properties"]["name"]["enum"],
                         [c["name"] for c in gs.LOG_CRAWLERS])
        self.assertEqual(schema("crawlers.v1.json")["properties"]["live_fetches"]["properties"]["recent"]["items"]
                         ["properties"]["crawler"]["enum"], list(gs.LOG_LIVE))

    def test_the_log_only_table_widens_the_count_and_never_the_score(self):
        log_only = self.table("## Counted in access logs only")
        self.assertEqual([(n.strip("`"), o, r) for n, o, r in log_only], gs.LOG_ONLY_UAS)
        self.assertTrue(len(gs.LOG_ONLY_UAS) >= 10)
        names = set(n.lower() for n, _, _ in gs.LOG_ONLY_UAS)
        # none is scored, probed or named in g.robots' evidence: the retrieval table and the not-scored tokens are
        # what they were, and no log-only name is in either
        self.assertEqual(len(gs.RETRIEVAL_UAS), 10)
        self.assertEqual(names & set(n.lower() for n, _ in gs.RETRIEVAL_UAS), set())
        self.assertEqual(names & set(n.lower() for n in gs.NOT_SCORED_TOKENS), set())
        self.assertEqual(set(r for _, _, r in gs.LOG_ONLY_UAS), {"search", "user", "training"})
        scored = [c["name"] for c in gs.LOG_CRAWLERS if c["scored"]]
        self.assertEqual(scored, [n for n, _ in gs.RETRIEVAL_UAS])
        for n, _, r in gs.LOG_ONLY_UAS:
            c = next(x for x in gs.LOG_CRAWLERS if x["name"] == n)
            self.assertEqual((c["kind"], c["live"]), ("training" if r == "training" else "retrieval", r == "user"), n)
        self.assertTrue(set(gs.LIVE_FETCHERS) < set(gs.LOG_LIVE))
        # the reference says how the tables relate, and points every log-only row at its operator's page
        with io.open(os.path.join(ROOT, "reference", "ai-crawlers.md"), encoding="utf-8") as f:
            ref = f.read()
        self.assertIn("**How the tables relate.**", ref)
        for row in re.findall(r"^\| `[^`]+` \| [^|]+ \| (?:search|user|training) \|[^\n]+", ref, re.M):
            self.assertRegex(row, r"\(\[[A-Z0-9]+\]\) \|$", row)
        # g.robots never names one in its evidence: a robots.txt that blocks only log-only crawlers scores as before
        txt = "User-agent: Kimi-SearchBot\nDisallow: /\n\nUser-agent: ExaSearchBot\nDisallow: /\n"
        self.assertEqual(gs.robots_tier(txt, len(txt))[0], 3)
        self.assertNotIn("Kimi", gs.robots_tier(txt, len(txt))[1])

    def test_a_log_only_crawler_is_counted_and_marked(self):
        lines = ["198.51.100.%d - - [20/Nov/2026:09:0%d:00 +0000] \"GET /guide HTTP/1.1\" 200 10 \"-\" \"%s\"" % (i, i, ua)
                 for i, ua in enumerate([
                     "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; Kimi-SearchBot/1.0; +https://www.kimi.com/policies/kimi-crawlers",
                     "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; Kimi-User/1.0; +https://www.kimi.com/policies/kimi-crawlers",
                     "meta-webindexer/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)",
                     "Mozilla/5.0 (compatible; ExaSearchBot-Images/1.0; +https://images.crawler.exa.ai)",
                     "DuckAssistBot/1.2; (+http://duckduckgo.com/duckassistbot.html)",
                     "Mozilla/5.0 (compatible) AI2Bot (+https://www.allenai.org/crawler)"], 1)]
        lines.append('192.0.2.9 - - [20/Nov/2026:09:30:00 +0000] "GET /guide HTTP/1.1" 200 10 "https://www.kimi.com/chat/x" '
                     '"Mozilla/5.0 (X11; Linux x86_64) Firefox/133.0"')
        d = tempfile.mkdtemp(prefix="geo-score-logonly-")
        try:
            p = os.path.join(d, "a.log")
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            r = gs.read_crawler_logs([p])
        finally:
            shutil.rmtree(d, ignore_errors=True)
        c = by_name(r)
        self.assertEqual(dict((n, c[n]["requests"]) for n in c if c[n]["requests"]),
                         {"Kimi-SearchBot": 1, "Kimi-User": 1, "Meta-WebIndexer": 1, "ExaSearchBot-Images": 1,
                          "DuckAssistBot": 1, "AI2Bot": 1})
        self.assertFalse(any(c[n]["scored"] for n in c if c[n]["requests"]))
        self.assertEqual(c["ExaSearchBot"]["requests"], 0)          # the whole token: -Images is another crawler
        f = r["funnel"]
        self.assertIn("Kimi-SearchBot", f["indexed"]["crawlers"])
        self.assertEqual((f["indexed"]["requests"], f["read"]["requests"]), (3, 2))
        kimi = next(x for x in f["by_assistant"] if x["assistant"] == "Kimi")
        self.assertEqual((kimi["indexed"], kimi["read"], kimi["clicked"]), (1, 1, 1))
        self.assertEqual(f["read_to_click"]["pairs"], 1)
        text = gs.render_crawlers(r, "text")
        self.assertIn("Kimi-SearchBot (log only)", text)
        self.assertIn("AI2Bot (log only)", text)
        self.assertNotIn("GPTBot (log only)", text)
        if jsonschema is not None:
            jsonschema.validate(json.loads(json.dumps(r)), schema("crawlers.v1.json"))

    def test_a_user_agent_names_a_crawler_by_its_whole_token(self):
        cases = [("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", "Googlebot"),
                 ("Googlebot-Image/1.0", None), ("Mozilla/5.0 (compatible; bingbot/2.0)", "Bingbot"),
                 ("meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)",
                  "Meta-ExternalAgent"),
                 ("Mozilla/5.0 (compatible; NotGPTBot/1.0)", None), ("GPTBotX/1.0", None), ("cohere-ai", "cohere-ai"),
                 ("x; ChatGPT-User/1.0; GPTBot/1.1", "ChatGPT-User"), ("Claude-SearchBot/1.0", "Claude-SearchBot"),
                 ("Applebot-Extended", None), ("", None), (None, None)]
        for ua, want in cases:
            self.assertEqual(gs.log_crawler(ua), want, ua)


class Formats(unittest.TestCase):
    def test_each_format_alone(self):
        for name, fmt, read, not_read in [("combined.log", "combined", 19, 3), ("vercel.jsonl", "vercel", 4, 1),
                                          ("cloudflare.jsonl", "cloudflare", 4, 0), ("json-lines.jsonl", "json", 2, 0)]:
            f = gs.read_crawler_logs([fx(name)])["files"][0]
            self.assertEqual((f["formats"], f["read"], f["not_read"]), ({fmt: read}, read, not_read), name)

    def test_times_in_every_shape_read_as_utc(self):
        for v, want in [("19/Nov/2026:14:30:00 +0100", "2026-11-19T13:30:00Z"), ("2026-11-20T06:00:00Z", "2026-11-20T06:00:00Z"),
                        ("2026-11-21T11:00:00+00:00", "2026-11-21T11:00:00Z"), ("2026-11-21 11:00:00.250", "2026-11-21T11:00:00Z"),
                        (EPOCH, "2026-11-19T05:00:00Z"), (EPOCH * 1000, "2026-11-19T05:00:00Z"),
                        (EPOCH * 10 ** 9, "2026-11-19T05:00:00Z"), (str(EPOCH), "2026-11-19T05:00:00Z")]:
            self.assertEqual(gs._iso(gs._log_time(v)), want, v)
        for v in ["yesterday", "", None, True, 10 ** 30, "99/Zzz/2026:00:00:00 +0000", "9999-99-99T99:99:99Z", -1, {}]:
            self.assertIsNone(gs._log_time(v), v)

    def test_paths_are_compared_without_query_and_trailing_slash(self):
        for v, want in [("/pricing?utm_source=x", "/pricing"), ("/docs/start/", "/docs/start"), ("/", "/"),
                        ("https://example.com/a/b/?x#y", "/a/b"), ("*", None), ("", None), ("/a b`c|d", "/a%20b%60c%7Cd")]:
            self.assertEqual(gs._log_path(v), want, v)


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.r = gs.read_crawler_logs(
            ALL, ranges=dict([gs.load_ip_ranges("GPTBot=" + fx("ranges-gptbot.json")),
                              gs.load_ip_ranges("oai-searchbot=" + fx("ranges-oai-searchbot.txt"))]),
            pages=gs.load_page_list(fx("sitemap.xml"), "sitemap"), page_source="sitemap.xml")
        self.c = by_name(self.r)

    def test_the_counts(self):
        self.assertEqual(self.r["lines"], {"total": 34, "read": 29, "not_read": 4, "ai_requests": 23})
        self.assertEqual(self.r["window"], {"from": "2026-11-18T08:00:00Z", "to": "2026-11-21T16:45:10Z"})
        self.assertEqual(dict((n, c["requests"]) for n, c in self.c.items() if c["requests"]),
                         {"OAI-SearchBot": 3, "ChatGPT-User": 2, "Claude-SearchBot": 1, "Claude-User": 1, "PerplexityBot": 2,
                          "Perplexity-User": 1, "Googlebot": 1, "Bingbot": 1, "Applebot": 1, "Amazonbot": 1, "GPTBot": 4,
                          "ClaudeBot": 1, "CCBot": 1, "cohere-ai": 1, "Bytespider": 1, "Meta-ExternalAgent": 1})
        self.assertEqual(len(self.r["crawlers"]), len(gs.LOG_CRAWLERS))   # every crawler of the reference, requests or not
        oai = self.c["OAI-SearchBot"]
        self.assertEqual((oai["pages"], oai["first"], oai["last"]), (2, "2026-11-18T09:15:02Z", "2026-11-19T10:00:00Z"))
        self.assertEqual(oai["top_pages"][0], {"path": "/pricing", "requests": 2, "ok": 2, "first": "2026-11-18T09:15:02Z",
                                               "last": "2026-11-19T09:15:02Z"})
        self.assertEqual([(c["kind"], c["live"]) for c in self.r["crawlers"] if c["name"] in ("GPTBot", "ChatGPT-User", "Googlebot")],
                         [("retrieval", True), ("retrieval", False), ("training", False)])

    def test_a_forged_user_agent_is_told_apart_only_by_its_address(self):
        g = self.c["GPTBot"]["verification"]
        self.assertEqual((g["checked"], g["verified"], g["not_in_ranges"], g["unverified"]), (True, 2, 2, 0))
        self.assertEqual(self.c["OAI-SearchBot"]["verification"]["verified"], 3)
        self.assertEqual(self.c["ClaudeBot"]["verification"], {"checked": False, "verified": 0, "not_in_ranges": 0,
                                                               "unverified": 1})
        self.assertEqual(self.r["verification"]["mode"], "ip_ranges")
        plain = gs.read_crawler_logs([fx("combined.log")])
        self.assertEqual(plain["verification"], {"mode": "user_agent_only", "ranges": []})
        self.assertEqual(by_name(plain)["GPTBot"]["verification"]["unverified"], 4)
        self.assertIn("unverified", plain["notes"][0])
        self.assertIn("Unverified: a user-agent can be forged", gs.render_crawlers(plain))

    def test_status_codes_and_refusals(self):
        self.assertEqual(self.c["PerplexityBot"]["status"]["5xx"], 1)
        self.assertEqual(self.c["PerplexityBot"]["status"]["blocked"], 0)            # a 503 is an error, not a refusal
        for n in ("ClaudeBot", "Bytespider", "Meta-ExternalAgent", "Applebot"):
            self.assertEqual((self.c[n]["status"]["4xx"], self.c[n]["status"]["blocked"]), (1, 1), n)
        self.assertEqual(sum(self.c[n]["status"]["firewall"] for n in self.c), 3)    # deny, block, managedChallenge
        self.assertEqual(self.c["GPTBot"]["status"]["codes"], {"200": 3, "404": 1})
        self.assertEqual(self.c["Bingbot"]["status"]["3xx"], 1)

    def test_live_fetches_have_their_own_timeline(self):
        lf = self.r["live_fetches"]
        self.assertEqual(lf["total"], 4)
        self.assertEqual(lf["by_day"], [{"day": "2026-11-19", "ChatGPT-User": 1, "Claude-User": 1},
                                        {"day": "2026-11-20", "Perplexity-User": 1}, {"day": "2026-11-21", "ChatGPT-User": 1}])
        self.assertEqual([(e["time"], e["crawler"], e["path"]) for e in lf["recent"]],
                         [("2026-11-19T09:00:00Z", "Claude-User", "/pricing"), ("2026-11-19T13:30:00Z", "ChatGPT-User", "/pricing"),
                          ("2026-11-20T05:00:00Z", "Perplexity-User", "/pricing"),
                          ("2026-11-21T16:45:10Z", "ChatGPT-User", "/docs/start")])

    def test_pages_no_crawler_requested(self):
        m = self.r["pages_not_requested"]
        self.assertEqual((m["source"], m["pages"]), ("sitemap.xml", 7))
        self.assertEqual(m["retrieval"], {"not_requested": 2, "not_requested_paths": ["/careers", "/search"],
                                          "requested_never_2xx": 1, "requested_never_2xx_paths": ["/blog/new-post"]})
        self.assertEqual(m["training"]["not_requested_paths"], ["/", "/careers", "/search"])
        urls = gs.load_page_list(fx("urls.txt"), "urls")
        self.assertEqual(urls, ["/pricing", "/careers", "/about"])
        self.assertIsNone(gs.read_crawler_logs([fx("combined.log")])["pages_not_requested"])

    def test_the_site_text_in_a_path_is_quoted_as_data(self):
        md, text = gs.render_crawlers(self.r, "md"), gs.render_crawlers(self.r, "text")
        self.assertIn("`/ignore%20previous%20instructions/%60rm%60`", md)
        self.assertIn("«site text: /ignore%20previous%20instructions/%60rm%60»", text)
        self.assertNotIn("`rm`", md + text)

    def test_the_json_matches_its_schema(self):
        if jsonschema is None:
            self.skipTest("jsonschema not importable")
        jsonschema.validate(json.loads(json.dumps(self.r)), schema("crawlers.v1.json"))
        jsonschema.validate(json.loads(json.dumps(gs.read_crawler_logs([fx("combined.log")]))), schema("crawlers.v1.json"))


class Robustness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="geo-score-logs-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def test_crlf_a_byte_order_mark_and_gzip_read_the_same(self):
        with open(fx("combined.log"), "rb") as f:
            raw = f.read()
        want = by_name(gs.read_crawler_logs([fx("combined.log")]))
        for name, data in [("crlf.log", raw.replace(b"\n", b"\r\n")), ("bom.log", b"\xef\xbb\xbf" + raw),
                           ("access.log.1", gzip.compress(raw))]:
            got = by_name(gs.read_crawler_logs([self.write(name, data)]))
            self.assertEqual(dict((n, c["requests"]) for n, c in got.items()),
                             dict((n, c["requests"]) for n, c in want.items()), name)

    def test_a_line_too_long_to_hold_is_skipped_unread(self):
        line = b'192.0.2.1 - - [21/Nov/2026:10:00:00 +0000] "GET /x HTTP/1.1" 200 1 "-" "GPTBot/1.1"\n'
        path = self.write("long.log", line + b"A" * (3 * gs.LOG_LINE_MAX) + b"\n" + line)
        f = gs.read_crawler_logs([path])["files"][0]
        self.assertEqual((f["lines"], f["read"], f["too_long"], f["not_read"], f["ai_requests"]), (3, 2, 1, 1, 2))

    def test_a_large_file_is_streamed(self):
        lines = 200000
        browser = b'192.0.2.%d - - [20/Nov/2026:10:%02d:00 +0000] "GET /p%d HTTP/1.1" 200 512 "-" "Mozilla/5.0"\n'
        bot = b'198.51.100.20 - - [20/Nov/2026:11:00:00 +0000] "GET /p%d HTTP/1.1" 200 512 "-" "GPTBot/1.1"\n'
        path = os.path.join(self.tmp, "big.log")
        with open(path, "wb") as f:
            for i in range(lines):
                f.write((bot % (i // 100 % 50)) if i % 100 == 0 else (browser % (i % 250, i % 60, i)))
        size = os.path.getsize(path)
        tracemalloc.start()
        start = time.time()
        r = gs.read_crawler_logs([path])
        took = time.time() - start
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        self.assertEqual((r["lines"]["total"], r["lines"]["ai_requests"]), (lines, lines // 100))
        self.assertEqual(by_name(r)["GPTBot"]["pages"], 50)
        self.assertGreater(size, 15 * 1024 * 1024)
        self.assertLess(peak, 8 * 1024 * 1024, "a %d-byte log held %d bytes at its peak" % (size, peak))
        self.assertLess(took, 120)

    def test_random_bytes_never_end_in_a_traceback(self):
        rng = random.Random(20261123)
        pieces = [b'192.0.2.1 - - [', b'21/Nov/2026:10:00:00 +0000', b'] "GET /', b' HTTP/1.1" ', b'200', b' 1 "-" "',
                  b'GPTBot/1.1', b'"', b'{"proxy": {"userAgent": ["ChatGPT-User/1.0"], "path": "/a", "timestamp": ',
                  b'1e400', b'}}', b'\x00', b'\xff\xfe', b'\n', b'\\"', b'{"ClientRequestUserAgent": null}', b'[]',
                  b'{"ts": "9999999999999999999999"}', b'"status": "abc"']
        for k in range(40):
            data = b"".join(rng.choice(pieces) for _ in range(rng.randint(1, 400)))
            path = self.write("random%d.log" % k, data)
            try:
                r = gs.read_crawler_logs([path])
                gs.render_crawlers(r, "md")
                gs.render_crawlers(r, "text")
            except gs.ScoreError as e:
                self.assertEqual(e.kind, "usage")

    def test_range_files_in_three_shapes(self):
        nets = gs.load_ip_ranges("gptbot=" + fx("ranges-gptbot.json"))
        self.assertEqual((nets[0], [str(n) for n in nets[1]]), ("GPTBot", ["198.51.100.16/28", "2001:db8:1::/48"]))
        path = self.write("list.json", b'["203.0.113.0/24", "not a range"]')
        self.assertEqual([str(n) for n in gs.load_ip_ranges("ClaudeBot=" + path)[1]], ["203.0.113.0/24"])
        for spec, why in [("Nobody=" + path, "not a crawler"), ("GPTBot", "NAME=FILE"),
                          ("GPTBot=" + self.write("empty.txt", b"# nothing\n"), "no address range"),
                          ("GPTBot=" + os.path.join(self.tmp, "missing.json"), "cannot read")]:
            with self.assertRaises(gs.ScoreError) as e:
                gs.load_ip_ranges(spec)
            self.assertIn(why, str(e.exception))

    def test_addresses_in_the_shapes_logs_write_them(self):
        for v, want in [("198.51.100.20", "198.51.100.20"), ("198.51.100.20:4431", "198.51.100.20"),
                        ("203.0.113.5, 10.0.0.1", "203.0.113.5"), ("[2001:db8::1]:443", "2001:db8::1"),
                        ("2001:db8::1", "2001:db8::1"), ("-", None), ("", None), (None, None)]:
            got = gs._log_ip(v)
            self.assertEqual(str(got) if got else None, want, v)


class Funnel(unittest.TestCase):
    """Indexed, read, clicked, converted: four layers counted apart, with the step from read to click timed."""

    def setUp(self):
        self.r = gs.read_crawler_logs([fx("funnel.log")], conversions=gs.load_conversions(fx("conversions.txt")))
        self.f = self.r["funnel"]

    def test_each_layer(self):
        f = self.f
        self.assertEqual((f["indexed"]["requests"], f["indexed"]["pages"], f["indexed"]["pages_2xx"]), (2, 2, 2))
        self.assertIn("OAI-SearchBot", f["indexed"]["crawlers"])
        self.assertNotIn("ChatGPT-User", f["indexed"]["crawlers"])
        self.assertEqual((f["read"]["crawlers"], f["read"]["requests"], f["read"]["pages"]),
                         (list(gs.LOG_LIVE), 2, 2))
        # ChatGPT by Referer, ChatGPT by utm_source even with utm_medium=email, Perplexity, Kimi; not google.com, not
        # a ChatGPT Referer under utm_medium=newsletter, not a subdomain, not the stylesheet the page loaded
        self.assertEqual(f["clicked"]["by_assistant"], {"ChatGPT": 2, "Kimi": 1, "Perplexity": 1})
        self.assertEqual((f["clicked"]["visits"], f["clicked"]["pages"]), (4, 3))
        self.assertEqual(f["clicked"]["top_pages"][0], {"path": "/docs", "visits": 2})
        # three requests for a conversion page; one came within 24 hours of an AI visit by the same visitor, one came
        # 50 hours after, one never followed an AI visit
        self.assertEqual(f["converted"], {"paths": 2, "requests": 3, "after_ai_visit": 1, "window_hours": 24,
                                          "by_assistant": {"ChatGPT": 1}})
        self.assertEqual(f["read_to_click"], {"pairs": 1, "median_seconds": 180, "window_days": 7})
        self.assertEqual([(x["assistant"], x["indexed"], x["read"], x["clicked"], x["converted"]) for x in f["by_assistant"]],
                         [("ChatGPT", 2, 1, 2, 1), ("Perplexity", 0, 1, 1, 0), ("Kimi", 0, 0, 1, 0)])
        self.assertEqual(f["referral_rules"], "ai-referral-hosts-2026-11")

    def test_without_conversions_the_last_layer_is_not_measured(self):
        f = gs.read_crawler_logs([fx("funnel.log")])["funnel"]
        self.assertIsNone(f["converted"])
        self.assertIsNone(f["by_assistant"][0]["converted"])
        text = gs.render_crawlers(gs.read_crawler_logs([fx("funnel.log")]), "text")
        self.assertIn("not measured (--conversions FILE)", text)

    def test_the_referral_rules(self):
        cases = [("/a?utm_source=chatgpt.com", None, "ChatGPT"), ("/a?utm_source=ChatGPT", None, "ChatGPT"),
                 ("/a", "https://chat.openai.com/c/1", "ChatGPT"), ("/a", "https://www.perplexity.ai/", "Perplexity"),
                 ("/a", "https://doubao.com/chat", "Doubao"), ("/a?utm_source=yuanbao", None, "Yuanbao"),
                 ("/a", "https://chat.deepseek.com/", "DeepSeek"), ("/a", "https://deepseek.com/", None),
                 ("/a", "https://chatgpt.com:443/", "ChatGPT"), ("/a", "https://evil.example/?chatgpt.com", None),
                 ("/a?utm_medium=email", "https://claude.ai/", None), ("/a?utm_source=newsletter", "https://claude.ai/", "Claude"),
                 ("/a", "chatgpt.com", None), ("/a", None, None), (None, "https://[bad", None)]
        for path, ref, want in cases:
            self.assertEqual(gs.ai_referral(path, ref), want, (path, ref))
        hosts = [h for a in gs.AI_ASSISTANTS for h in a[1]]
        self.assertEqual(len(hosts), len(set(hosts)))
        names = dict((c["name"], c) for c in gs.LOG_CRAWLERS)
        for name, _, _, idx, live in gs.AI_ASSISTANTS:
            self.assertTrue(idx is None or (idx in names and not names[idx]["live"]), name)
            self.assertTrue(live is None or live in gs.LOG_LIVE, name)

    def test_conversion_paths(self):
        conv = gs.load_conversions(fx("conversions.txt"))
        self.assertEqual(conv, [("/thank-you", False), ("/order/done", True)])
        for path, want in (("/thank-you", True), ("/thank-you/x", False), ("/order/done", True),
                           ("/order/done/42", True), ("/order/donex", True), ("/orders", False), (None, False)):
            self.assertEqual(gs._converts(path, conv), want, path)

    def test_the_views_and_the_schema(self):
        text, md = gs.render_crawlers(self.r, "text"), gs.render_crawlers(self.r, "md")
        for v in (text, md):
            self.assertIn("The funnel: indexed, read, clicked, converted", v)
            self.assertIn("median 3 min over 1 click", v)
            self.assertIn("The funnel by assistant", v)
        self.assertIn("«site text: /docs»", text)
        # nothing the visitor sent is copied: no Referer, query string, address or user-agent
        js = json.dumps(self.r)
        for leak in ("chatgpt.com/", "utm_source=", "192.0.2.50", "Safari", "power-stations"):
            self.assertNotIn(leak, js)
        self.assertEqual([c["purpose"] for c in self.r["crawlers"] if c["name"] in ("OAI-SearchBot", "ChatGPT-User", "GPTBot")],
                         ["search", "user", "training"])
        if jsonschema is not None:
            jsonschema.validate(json.loads(js), schema("crawlers.v1.json"))

    def test_json_records_with_the_usual_field_names_read_as_they_are(self):
        r = gs.read_crawler_logs([fx("import-records.jsonl")])
        self.assertEqual((r["files"][0]["formats"], r["lines"]["ai_requests"]), ({"json": 3}, 3))
        c = by_name(r)
        self.assertEqual((c["OAI-SearchBot"]["first"], c["ChatGPT-User"]["first"], c["GPTBot"]["first"]),
                         ("2026-11-20T01:00:00Z", "2026-11-20T10:00:00Z", "2026-11-20T00:00:00Z"))
        self.assertEqual(c["GPTBot"]["status"]["codes"], {"304": 1})
        self.assertEqual(gs._iso(gs._log_time("2026-11-20")), "2026-11-20T00:00:00Z")

    def test_the_command_takes_conversions(self):
        p = run(fx("funnel.log"), "--conversions", fx("conversions.txt"), "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["funnel"]["converted"]["after_ai_visit"], 1)
        empty = os.path.join(tempfile.mkdtemp(prefix="geo-score-conv-"), "none.txt")
        with open(empty, "w") as f:
            f.write("# nothing\n")
        p = run(fx("funnel.log"), "--conversions", empty, "--json")
        self.assertEqual(p.returncode, 2)
        self.assertIn("lists no conversion path", p.stdout + p.stderr)
        shutil.rmtree(os.path.dirname(empty), ignore_errors=True)


class Command(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="geo-score-logs-cli-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_json_md_and_files_from_one_read(self):
        md, js = os.path.join(self.tmp, "geo", "logs.md"), os.path.join(self.tmp, "geo", "logs.json")
        p = run(*(ALL + ["--format", "md", "-o", md, "--json-out", js, "--urls", fx("urls.txt")]))
        self.assertEqual((p.returncode, p.stdout), (0, ""), p.stderr)
        with io.open(md, encoding="utf-8") as f:
            self.assertTrue(f.read().startswith("# AI crawlers in access logs\n"))
        with io.open(js, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual((data["format"], data["lines"]["ai_requests"], data["pages_not_requested"]["source"]),
                         ("geo-score/crawlers.v1", 23, "urls.txt"))
        p = run(fx("combined.log"), "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        if jsonschema is not None:
            jsonschema.validate(json.loads(p.stdout), schema("crawlers.v1.json"))

    def test_standard_input(self):
        with open(fx("cloudflare.jsonl"), encoding="utf-8") as f:
            p = run("-", "--json", stdin=f.read())
        self.assertEqual((p.returncode, json.loads(p.stdout)["files"][0]["formats"]), (0, {"cloudflare": 4}), p.stderr)

    def test_exit_2_answers_in_json(self):
        bad = os.path.join(self.tmp, "bad.log")
        with open(bad, "w") as f:
            f.write("nothing here\n")
        for args, needle in [([os.path.join(self.tmp, "none.log")], "cannot read"), ([bad], "none of the 1 line"),
                             ([fx("combined.log"), "--verify-ips", "Nobody=x"], "not a crawler"),
                             ([fx("combined.log"), "--sitemap", fx("urls.txt")], "lists no page"),
                             ([fx("combined.log"), "--format", "xml"], "invalid choice")]:
            p = run(*(args + ["--json"]))
            self.assertEqual(p.returncode, 2, args)
            err = json.loads(p.stdout.strip().splitlines()[-1])
            self.assertEqual(err["error"]["kind"], "usage", args)
            self.assertIn(needle, err["error"]["message"] + p.stderr, args)
            self.assertNotIn("Traceback", p.stderr)
            if jsonschema is not None:
                jsonschema.validate(err, schema("error.v1.json"))

    def test_nothing_is_fetched(self):
        # offline: the command never opens a connection, whatever the logs and lists name
        import socket
        real = socket.socket.connect

        def refuse(*a, **k):
            raise AssertionError("crawlers opened a connection")
        socket.socket.connect = refuse
        try:
            gs.read_crawler_logs(ALL, pages=gs.load_page_list(fx("sitemap.xml"), "sitemap"), page_source="sitemap.xml")
        finally:
            socket.socket.connect = real


if __name__ == "__main__":
    unittest.main(verbosity=1)
