#!/usr/bin/env python3
"""Tests for geo_watch.py, the watch half of geo-score (levels 2 and 3). No network: every provider is faked
at the transport layer.

    python3 cli/test_geo_watch.py
"""
import contextlib, datetime, http.server, io, json, os, re, shutil, subprocess, sys, tempfile, threading
import unittest, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geo_watch as gw

KEYS = {"OPENAI_API_KEY": "sk-test-openai-0123456789", "PERPLEXITY_API_KEY": "pplx-test-0123456789",
        "GEMINI_API_KEY": "gm-test-0123456789", "ANTHROPIC_API_KEY": "sk-ant-test-0123456789",
        "OPENROUTER_API_KEY": "sk-or-test-0123456789"}
ALL_KEY_ENVS = list(KEYS) + ["GOOGLE_API_KEY"]
FIXED_NOW = datetime.datetime(2026, 9, 26, 8, 30, 0, tzinfo=datetime.timezone.utc)


# ── provider response builders ────────────────────────────────────────────
def openai_resp(text, cites=(), queries=(), tin=1000, tout=200):
    out = [{"type": "web_search_call", "id": "ws_%d" % i, "status": "completed",
            "action": {"type": "search", "query": q}} for i, q in enumerate(queries)]
    out.append({"type": "message", "role": "assistant", "content": [{
        "type": "output_text", "text": text,
        "annotations": [{"type": "url_citation", "start_index": 0, "end_index": 1, "url": u, "title": t}
                        for u, t in cites]}]})
    return {"id": "resp_1", "output": out, "usage": {"input_tokens": tin, "output_tokens": tout}}


def pplx_resp(text, results=(), cost=0.006):
    usage = {"prompt_tokens": 20, "completion_tokens": 300}
    if cost is not None:
        usage["cost"] = {"input_tokens_cost": 0.0, "output_tokens_cost": 0.001, "request_cost": 0.005,
                         "total_cost": cost}
    return {"choices": [{"message": {"role": "assistant", "content": text}}],
            "search_results": [{"url": u, "title": t} for u, t in results], "usage": usage}


def gemini_resp(text, chunks=(), queries=()):
    return {"candidates": [{"content": {"parts": [{"text": "thinking…", "thought": True}, {"text": text}]},
                            "groundingMetadata": {"webSearchQueries": list(queries),
                                                  "groundingChunks": [{"web": {"uri": u, "title": t}} for u, t in chunks]}}],
            "usageMetadata": {"promptTokenCount": 50, "candidatesTokenCount": 200, "thoughtsTokenCount": 100}}


def openrouter_resp(text, cites=(), cost=0.0021):
    return {"choices": [{"message": {"role": "assistant", "content": text, "annotations": [
        {"type": "url_citation", "url_citation": {"url": u, "title": t, "content": "", "start_index": 0,
                                                  "end_index": 1}} for u, t in cites]}}],
            "usage": {"prompt_tokens": 900, "completion_tokens": 150, "cost": cost}}


class FakeAPI(object):
    """Routes by host. A handler gets (url, headers, body) and returns a dict, or (status, dict_or_bytes[, headers])."""

    def __init__(self, routes):
        self.routes, self.calls, self.lock = routes, [], threading.Lock()

    def __call__(self, url, headers, body):
        with self.lock:
            self.calls.append((url, headers, body))
        for host, fn in self.routes.items():
            if host in url:
                r = fn(url, headers, body)
                status, payload, hdrs = 200, r, {}
                if isinstance(r, tuple):
                    status, payload = r[0], r[1]
                    hdrs = r[2] if len(r) > 2 else {}
                raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
                return status, hdrs, raw
        raise gw.TransportError("no route for " + url)


def brand():
    return gw.Entity({"name": "Lumo", "domains": ["lumo.example"], "aliases": ["鹿末"],
                      "url_prefixes": ["https://www.amazon.com/stores/Lumo/"]}, you=True)


def rivals():
    return [gw.Entity({"name": "Pixa", "domains": ["pixa.example"]}), gw.Entity({"name": "Reelcraft", "domains": ["reelcraft.example"]})]


def queries(n=3, prefix="q"):
    return [{"query_id": "%s%02d" % (prefix, i + 1), "query": "question %d" % (i + 1), "intent_tier": "list",
             "target_url": ""} for i in range(n)]


def engines(*ids):
    table = {"chatgpt-api": "openai", "perplexity-api": "perplexity", "gemini-api": "gemini",
             "claude-api": "anthropic", "or-api": "openrouter"}
    return [{"id": i, "provider": table[i], "model": gw.PROVIDERS[table[i]]["model"]} for i in ids]


class Base(unittest.TestCase):
    def setUp(self):
        self._saved = (gw.TRANSPORT, gw.RESOLVER, gw.SLEEP, gw.NOW)
        self._env = dict((k, os.environ.get(k)) for k in ALL_KEY_ENVS + ["GEO_SCORE_WATCH_CONFIG", "GEO_SCORE_PY"])
        for k in ALL_KEY_ENVS:
            os.environ.pop(k, None)
        os.environ.update(KEYS)
        self.sleeps = []
        gw.SLEEP = self.sleeps.append
        gw.NOW = lambda: FIXED_NOW
        gw.RESOLVER = lambda u: None
        self.tmp = tempfile.mkdtemp(prefix="geo-score-watch-test-")

    def tearDown(self):
        gw.TRANSPORT, gw.RESOLVER, gw.SLEEP, gw.NOW = self._saved
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fake(self, routes):
        api = FakeAPI(routes)
        gw.TRANSPORT = api
        return api

    def standard_routes(self):
        return {
            "api.openai.com": lambda u, h, b: openai_resp(
                "Lumo gives 15 free credits; Pixa is another option.",
                [("https://www.lumo.example/free?utm_source=openai", "Lumo free plan"),
                 ("https://pixa.example/pricing?utm_source=openai", "Pixa pricing")],
                ["best free ai video generator"]),
            "api.perplexity.ai": lambda u, h, b: pplx_resp(
                "Pixa [1] and Reelcraft [2] lead; reddit threads disagree [3].",
                [("https://pixa.example/", "Pixa"), ("https://reelcraft.example/", "Reelcraft"),
                 ("https://www.reddit.com/r/aivideo/x", "thread")]),
        }


# ── parsing each provider ─────────────────────────────────────────────────
class ProviderParsing(Base):
    def test_openai_citations_rank_and_searches(self):
        self.fake(self.standard_routes())
        res = gw.call_openai(engines("chatgpt-api")[0], KEYS["OPENAI_API_KEY"], "q", "US")
        s = gw.evaluate(res, brand(), rivals())
        self.assertTrue(s["cited"])
        self.assertEqual(s["rank"], 1)
        self.assertEqual(s["quoted_url"], "https://www.lumo.example/free")   # utm_source=openai dropped
        self.assertTrue(s["mentioned"])
        self.assertEqual(s["competitors"]["Pixa"], {"cited": True, "rank": 2, "mentioned": True})
        self.assertEqual(s["competitors"]["Reelcraft"], {"cited": False, "rank": None, "mentioned": False})
        self.assertEqual(s["search_queries"], ["best free ai video generator"])
        self.assertEqual(res["usage"], {"input_tokens": 1000, "output_tokens": 200, "search_calls": 1, "api_calls": 1})

    def test_openai_request_shape(self):
        api = self.fake(self.standard_routes())
        gw.call_openai(engines("chatgpt-api")[0], KEYS["OPENAI_API_KEY"], "which one?", "DE")
        url, headers, body = api.calls[0]
        self.assertEqual(url, "https://api.openai.com/v1/responses")
        self.assertEqual(headers["Authorization"], "Bearer " + KEYS["OPENAI_API_KEY"])
        self.assertEqual(body["tools"], [{"type": "web_search",
                                          "user_location": {"type": "approximate", "country": "DE"}}])
        self.assertEqual(body["input"], "which one?")

    def test_perplexity_keeps_only_numbered_sources(self):
        self.fake({"api.perplexity.ai": lambda u, h, b: pplx_resp(
            "Try Lumo [2] or Pixa [3].", [("https://reddit.com/r/x", "r"), ("https://lumo.example/", "Lumo"),
                                          ("https://pixa.example/", "Pixa")])})
        res = gw.call_perplexity(engines("perplexity-api")[0], KEYS["PERPLEXITY_API_KEY"], "q", None)
        self.assertEqual([c[0] for c in res["citations"]], ["https://lumo.example/", "https://pixa.example/"])
        self.assertEqual(res["reported_cost"], 0.006)
        s = gw.evaluate(res, brand(), rivals())
        self.assertEqual((s["cited"], s["rank"]), (True, 1))

    def test_perplexity_without_markers_keeps_all_and_falls_back_to_citations(self):
        self.fake({"api.perplexity.ai": lambda u, h, b: {
            "choices": [{"message": {"content": [{"type": "text", "text": "no markers here"}]}}],
            "citations": ["https://a.com/1", "https://lumo.example/x"], "usage": {}}})
        res = gw.call_perplexity(engines("perplexity-api")[0], "k" * 10, "q", None)
        self.assertEqual(len(res["citations"]), 2)
        self.assertEqual(res["answer"], "no markers here")
        self.assertIsNone(res["reported_cost"])
        self.assertEqual(gw.evaluate(res, brand(), [])["rank"], 2)

    def test_perplexity_markers_out_of_range_keep_everything(self):
        self.fake({"api.perplexity.ai": lambda u, h, b: pplx_resp("see [9]", [("https://lumo.example/", "L")])})
        res = gw.call_perplexity(engines("perplexity-api")[0], "k" * 10, "q", None)
        self.assertEqual(len(res["citations"]), 1)

    def test_gemini_resolves_only_where_it_matters(self):
        resolved = []

        def resolver(u):
            resolved.append(u)
            return {"https://vertexaisearch.cloud.google.com/grounding-api-redirect/AAA": "https://lumo.example/pricing",
                    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/CCC": "https://medium.com/x"}.get(u)
        gw.RESOLVER = resolver
        api = self.fake({"generativelanguage.googleapis.com": lambda u, h, b: gemini_resp(
            "Lumo is free to start.",
            [("https://vertexaisearch.cloud.google.com/grounding-api-redirect/AAA", "lumo.example"),
             ("https://vertexaisearch.cloud.google.com/grounding-api-redirect/BBB", "reddit.com"),
             ("https://vertexaisearch.cloud.google.com/grounding-api-redirect/CCC", "An article with no domain")],
            ["free ai video generator", "lumo pricing"])})
        eng = dict(engines("gemini-api")[0], api="generate_content", model="gemini-2.5-flash")
        res = gw.call_gemini(eng, KEYS["GEMINI_API_KEY"], "q", None)
        s = gw.evaluate(res, brand(), rivals())
        self.assertEqual(resolved, ["https://vertexaisearch.cloud.google.com/grounding-api-redirect/AAA",
                                    "https://vertexaisearch.cloud.google.com/grounding-api-redirect/CCC"])
        self.assertEqual([c["domain"] for c in s["citations"]], ["lumo.example", "reddit.com", "medium.com"])
        self.assertEqual((s["cited"], s["rank"], s["quoted_url"]), (True, 1, "https://lumo.example/pricing"))
        self.assertEqual(s["answer"], "Lumo is free to start.")                  # the thought part is not the answer
        self.assertEqual(res["usage"]["output_tokens"], 300)                     # thinking tokens are billed
        self.assertEqual(res["usage"]["search_calls"], 2)
        self.assertEqual(api.calls[0][0], "https://generativelanguage.googleapis.com/v1beta/models/"
                                          "gemini-2.5-flash:generateContent")
        self.assertEqual(api.calls[0][1], {"x-goog-api-key": KEYS["GEMINI_API_KEY"]})

    def test_gemini_unresolved_brand_redirect_still_counts_by_title(self):
        gw.RESOLVER = lambda u: None
        self.fake({"generativelanguage.googleapis.com": lambda u, h, b: gemini_resp(
            "x", [("https://vertexaisearch.cloud.google.com/grounding-api-redirect/AAA", "www.lumo.example")])})
        eng = dict(engines("gemini-api")[0], api="generate_content")
        s = gw.evaluate(gw.call_gemini(eng, "k" * 10, "q", None), brand(), [])
        self.assertTrue(s["cited"])

    def test_gemini_interactions_api(self):
        api = self.fake({"generativelanguage.googleapis.com": lambda u, h, b: {
            "id": "int_1", "status": "completed",
            "steps": [{"type": "thought", "summary": [{"type": "text", "text": "I should search."}]},
                      {"type": "google_search_call", "arguments": {"queries": ["lumo pricing", "free ai video"]}},
                      {"type": "google_search_result", "call_id": "s1", "result": [{"search_suggestions": "<div>"}]},
                      {"type": "model_output", "content": [{"type": "text", "text": "Pixa and Lumo both have free plans.",
                       "annotations": [{"type": "url_citation", "url": "https://pixa.example/pricing", "title": "pixa.example",
                                        "start_index": 0, "end_index": 4},
                                       {"type": "url_citation", "url": "https://lumo.example/pricing",
                                        "title": "lumo.example", "start_index": 9, "end_index": 13}]}]}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 40}}})
        res = gw.call_gemini(engines("gemini-api")[0], KEYS["GEMINI_API_KEY"], "q", "US")
        url, headers, body = api.calls[0]
        self.assertEqual(url, "https://generativelanguage.googleapis.com/v1beta/interactions")
        self.assertEqual(body, {"model": "gemini-3.8-flash", "input": "q", "tools": [{"type": "google_search"}],
                                "store": False})
        self.assertEqual(res["answer"], "Pixa and Lumo both have free plans.")      # the thought is not the answer
        self.assertEqual(res["search_queries"], ["lumo pricing", "free ai video"])
        self.assertEqual(res["usage"], {"input_tokens": 10, "output_tokens": 30, "search_calls": 2, "api_calls": 1})
        s = gw.evaluate(res, brand(), rivals())
        self.assertEqual((s["cited"], s["rank"], s["competitors"]["Pixa"]["rank"]), (True, 2, 1))

    def test_anthropic_continues_a_paused_turn(self):
        replies = [
            {"content": [{"type": "server_tool_use", "id": "s1", "name": "web_search", "input": {"query": "lumo ai"}},
                         {"type": "web_search_tool_result", "tool_use_id": "s1",
                          "content": [{"type": "web_search_result", "url": "https://lumo.example/", "title": "Lumo"}]},
                         {"type": "text", "text": "Lumo "}],
             "stop_reason": "pause_turn",
             "usage": {"input_tokens": 100, "output_tokens": 10, "server_tool_use": {"web_search_requests": 1}}},
            {"content": [{"type": "text", "text": "is the cheapest.", "citations": [
                {"type": "web_search_result_location", "url": "https://lumo.example/pricing", "title": "Pricing",
                 "cited_text": "..."}]}],
             "stop_reason": "end_turn",
             "usage": {"input_tokens": 200, "output_tokens": 50, "server_tool_use": {"web_search_requests": 1}}},
        ]
        api = self.fake({"api.anthropic.com": lambda u, h, b: replies[len(api.calls) - 1]})
        res = gw.call_anthropic(engines("claude-api")[0], KEYS["ANTHROPIC_API_KEY"], "q", "US")
        self.assertEqual(res["answer"], "Lumo is the cheapest.")
        self.assertEqual(res["usage"], {"input_tokens": 300, "output_tokens": 60, "search_calls": 2, "api_calls": 2})
        self.assertEqual(res["search_queries"], ["lumo ai"])
        second = api.calls[1][2]["messages"]
        self.assertEqual(second[1]["role"], "assistant")
        self.assertEqual(api.calls[0][1]["anthropic-version"], "2023-06-01")
        self.assertEqual(api.calls[0][2]["tools"][0]["user_location"], {"type": "approximate", "country": "US"})
        self.assertTrue(gw.evaluate(res, brand(), [])["cited"])

    def test_openrouter_annotations_and_cost(self):
        api = self.fake({"openrouter.ai": lambda u, h, b: openrouter_resp(
            "Reelcraft wins.", [("https://reelcraft.example/pricing", "Reelcraft")])})
        eng = {"id": "or-api", "provider": "openrouter", "model": "deepseek/deepseek-chat"}
        res = gw.call_openrouter(eng, KEYS["OPENROUTER_API_KEY"], "q", "US")
        self.assertEqual(res["reported_cost"], 0.0021)
        self.assertEqual(api.calls[0][2]["plugins"][0]["id"], "web")
        s = gw.evaluate(res, brand(), rivals())
        self.assertEqual((s["cited"], s["competitors"]["Reelcraft"]["rank"]), (False, 1))


# ── matching ──────────────────────────────────────────────────────────────
class Matching(Base):
    def test_mentions_respect_word_boundaries_and_cjk(self):
        b = brand()
        self.assertFalse(b.named_in("Lumos is a spell"))
        self.assertTrue(b.named_in("Try Lumo's editor"))
        self.assertTrue(b.named_in("鹿末视频的免费额度"))
        self.assertTrue(b.named_in("see lumo.example for details"))
        self.assertFalse(b.named_in("illumination"))

    def test_url_prefix_owns_a_marketplace_store_only(self):
        b = brand()
        self.assertTrue(b.owns("https://amazon.com/stores/lumo/page/123", "amazon.com"))
        self.assertTrue(b.owns("https://www.amazon.com/stores/Lumo", "amazon.com"))
        self.assertFalse(b.owns("https://amazon.com/stores/lumosity", "amazon.com"))
        self.assertFalse(b.owns("https://amazon.com/dp/B000", "amazon.com"))
        self.assertTrue(b.owns("https://app.lumo.example/x", "app.lumo.example"))
        self.assertFalse(b.owns("https://notlumo.example/", "notlumo.example"))

    def test_rank_counts_distinct_domains_before_the_brand(self):
        res = gw._result("x", [("https://a.com/1", ""), ("https://a.com/2", ""), ("https://b.com/", ""),
                               ("https://lumo.example/", ""), ("https://a.com/1", "")], [], 0, 0, 0)
        s = gw.evaluate(res, brand(), [])
        self.assertEqual(s["rank"], 3)
        self.assertEqual(len(s["citations"]), 4)                                 # the repeated URL is dropped

    def test_clean_url_and_host(self):
        self.assertEqual(gw.clean_url("javascript:alert(1)"), "")
        self.assertEqual(gw.clean_url("ftp://a.com/x"), "")
        self.assertEqual(gw.clean_url("https://a.com/p?utm_source=openai&id=3#frag"), "https://a.com/p?id=3")
        self.assertEqual(gw.clean_url("https://a.com"), "https://a.com/")
        self.assertEqual(gw.host_of("WWW.Lumo.Example."), "lumo.example")
        self.assertEqual(gw.host_of("lumo.example/x"), "lumo.example")
        self.assertEqual(gw.host_of("http://[bad"), "")

    def test_statistics(self):
        self.assertEqual(gw.wilson(2, 4), [0.15, 0.85])
        self.assertIsNone(gw.wilson(0, 0))
        self.assertEqual(gw.wilson(0, 10)[0], 0.0)
        self.assertLess(gw.two_prop_p(2, 40, 20, 40), 0.001)
        self.assertGreater(gw.two_prop_p(10, 40, 12, 40), 0.5)
        self.assertEqual(gw.two_prop_p(0, 10, 0, 10), 1.0)
        self.assertIsNone(gw.two_prop_p(1, 0, 1, 1))


# ── running: caps, budget, errors ─────────────────────────────────────────
class Running(Base):
    def run_std(self, **kw):
        self.fake(self.standard_routes())
        args = dict(runs=1, country=None, prices={}, max_calls=100)
        args.update(kw)
        return gw.execute(brand(), rivals(), kw.pop("engs", engines("chatgpt-api", "perplexity-api", "gemini-api",
                                                                      "claude-api")),
                          queries(3), **{k: v for k, v in args.items() if k != "engs"})

    def test_engines_without_keys_are_not_measured_not_zero(self):
        del os.environ["GEMINI_API_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]
        run = self.run_std()
        st = dict((e["id"], e["status"]) for e in run["engines"])
        self.assertEqual(st, {"chatgpt-api": "measured", "perplexity-api": "measured",
                              "gemini-api": "no_key", "claude-api": "no_key"})
        self.assertEqual(len(run["samples"]), 6)
        o = run["summary"]["overall"]
        self.assertEqual((o["answered"], o["cited"]), (6, 3))
        gem = next(e for e in run["summary"]["engines"] if e["id"] == "gemini-api")
        self.assertEqual((gem["answered"], gem["cited_rate"]), (0, None))
        self.assertIn("GEMINI_API_KEY or GOOGLE_API_KEY", next(e for e in run["engines"] if e["id"] == "gemini-api")["error"])

    def test_max_calls_is_exact(self):
        del os.environ["GEMINI_API_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]
        run = self.run_std(max_calls=4)
        st = [s["status"] for s in run["samples"]]
        self.assertEqual(st.count("ok"), 4)
        self.assertEqual([s["skip_reason"] for s in run["samples"] if s["status"] == "skipped"], ["max_calls"] * 2)
        self.assertEqual(run["ledger"]["questions_asked"], 4)

    def test_budget_skips_unpriced_engines_and_stops_at_the_cap(self):
        run = self.run_std(budget=0.01, engs=engines("chatgpt-api", "perplexity-api"))
        st = dict((e["id"], e["status"]) for e in run["engines"])
        self.assertEqual(st["chatgpt-api"], "no_price")
        pp = [s for s in run["samples"] if s["engine"] == "perplexity-api"]
        self.assertEqual([s["status"] for s in pp], ["ok", "skipped", "skipped"])
        self.assertEqual(pp[1]["skip_reason"], "budget")
        self.assertEqual(run["ledger"]["cost_usd"], 0.006)
        self.assertLessEqual(run["ledger"]["cost_usd"], 0.01)

    def test_budget_with_configured_prices(self):
        prices = {"chatgpt-api": {"input_per_mtok": 1.0, "output_per_mtok": 10.0, "per_search": 0.01}}
        run = self.run_std(budget=0.05, prices=prices, engs=engines("chatgpt-api"))
        # 1000 in + 200 out + 1 search = 0.001 + 0.002 + 0.01 = 0.013 per answer -> three fit under 0.05
        self.assertEqual([s["status"] for s in run["samples"]], ["ok", "ok", "ok"])
        self.assertEqual(run["samples"][0]["cost_usd"], 0.013)
        self.assertEqual(run["ledger"]["cost_usd"], 0.039)
        self.assertTrue(run["ledger"]["cost_complete"])

    def test_budget_stops_an_engine_whose_cost_stops_being_reported(self):
        self.fake({"api.perplexity.ai": lambda u, h, b: pplx_resp("x", [("https://a.com/", "")], cost=None)})
        run = gw.execute(brand(), [], engines("perplexity-api"), queries(3), budget=1.0)
        self.assertEqual([s.get("skip_reason") for s in run["samples"]], [None, "unpriced", "unpriced"])
        self.assertEqual(run["engines"][0]["stopped"], "unpriced")

    def test_allow_unpriced_runs_with_unknown_cost(self):
        run = self.run_std(budget=0.01, allow_unpriced=True, engs=engines("chatgpt-api"))
        self.assertEqual([s["status"] for s in run["samples"]], ["ok"] * 3)
        self.assertEqual(run["ledger"]["unpriced_answers"], 3)
        self.assertFalse(run["ledger"]["cost_complete"])

    def test_retries_429_then_succeeds(self):
        seq = [(429, {"error": {"message": "slow down"}}, {"Retry-After": "3"}),
               (503, b"", {}), openai_resp("ok", [("https://lumo.example/", "")])]
        api = self.fake({"api.openai.com": lambda u, h, b: seq[len(api.calls) - 1]})
        run = gw.execute(brand(), [], engines("chatgpt-api"), queries(1))
        self.assertEqual(run["samples"][0]["status"], "ok")
        self.assertEqual(self.sleeps, [3.0, 4.0])
        self.assertEqual(run["ledger"]["http_attempts"], 3)

    def test_gives_up_after_three_5xx(self):
        self.fake({"api.openai.com": lambda u, h, b: (503, {"error": {"message": "overloaded"}})})
        run = gw.execute(brand(), [], engines("chatgpt-api"), queries(1))
        self.assertEqual(run["samples"][0]["status"], "error")
        self.assertIn("HTTP 503: overloaded", run["samples"][0]["error"])

    def test_a_bad_key_stops_the_engine_and_is_redacted(self):
        key = KEYS["OPENAI_API_KEY"]
        self.fake({"api.openai.com": lambda u, h, b: (401, {"error": {"message": "Incorrect API key: %s" % key}})})
        run = gw.execute(brand(), [], engines("chatgpt-api"), queries(3))
        st = [(s["status"], s.get("skip_reason")) for s in run["samples"]]
        self.assertEqual(st, [("error", None), ("skipped", "engine_failed"), ("skipped", "engine_failed")])
        self.assertNotIn(key, json.dumps(run))
        self.assertIn("[redacted]", run["samples"][0]["error"])
        self.assertEqual(run["engines"][0]["stopped"], "engine_failed")
        self.assertIn("stopped:", gw.render(run))

    def test_three_failures_in_a_row_stop_an_engine(self):
        self.fake({"api.openai.com": lambda u, h, b: (200, b"[not an object]")})
        run = gw.execute(brand(), [], engines("chatgpt-api"), queries(5))
        self.assertEqual([s["status"] for s in run["samples"]], ["error"] * 3 + ["skipped"] * 2)

    def test_an_answer_that_breaks_the_parser_is_an_error_not_a_crash(self):
        self.fake(self.standard_routes())
        real = gw.evaluate
        gw.evaluate = lambda *a, **k: (_ for _ in ()).throw(ValueError("odd shape"))
        try:
            run = gw.execute(brand(), [], engines("chatgpt-api"), queries(2))
        finally:
            gw.evaluate = real
        self.assertEqual([s["status"] for s in run["samples"]], ["error", "error"])
        self.assertIn("odd shape", run["samples"][0]["error"])
        self.assertEqual(run["ledger"]["api_requests"], 2)                         # still paid for

    def test_network_errors_are_recorded(self):
        def boom(u, h, b):
            raise gw.TransportError("timed out")
        gw.TRANSPORT = boom
        run = gw.execute(brand(), [], engines("chatgpt-api"), queries(1))
        self.assertEqual(run["samples"][0]["error"], "network: timed out")
        self.assertEqual(run["summary"]["overall"]["answered"], 0)

    def test_a_preset_stop_skips_everything(self):
        self.fake(self.standard_routes())
        ev = threading.Event()
        ev.set()
        run = gw.execute(brand(), [], engines("chatgpt-api"), queries(2), stop=ev)
        self.assertTrue(run["interrupted"])
        self.assertEqual([s["skip_reason"] for s in run["samples"]], ["interrupted"] * 2)

    def test_runs_repeat_each_question(self):
        self.fake(self.standard_routes())
        run = gw.execute(brand(), [], engines("chatgpt-api"), queries(2), runs=3)
        self.assertEqual(sorted((s["query_id"], s["run"]) for s in run["samples"]),
                         [("q01", 1), ("q01", 2), ("q01", 3), ("q02", 1), ("q02", 2), ("q02", 3)])

    def test_progress_sees_every_sample(self):
        self.fake(self.standard_routes())
        seen = []
        gw.execute(brand(), [], engines("chatgpt-api", "perplexity-api"), queries(3),
                   progress=lambda n, t, s: seen.append((n, t)))
        self.assertEqual(sorted(seen), [(i, 6) for i in range(1, 7)])


# ── summary, diff, output ─────────────────────────────────────────────────
def canned(per_query):
    """per_query: {query_id: (text, [urls])} for a single openai engine."""
    def handler(u, h, b):
        text, urls = per_query[b["input"]]
        return openai_resp(text, [(x, "") for x in urls])
    return handler


class Reading(Base):
    def make(self, per_query):
        self.fake({"api.openai.com": canned(per_query)})
        qs = [{"query_id": "q%d" % i, "query": q, "intent_tier": "list" if i < 3 else "pricing", "target_url": ""}
              for i, q in enumerate(sorted(per_query), 1)]
        return gw.execute(brand(), rivals(), engines("chatgpt-api"), qs)

    def test_summary(self):
        run = self.make({"a": ("Lumo", ["https://lumo.example/a", "https://reddit.com/x"]),
                         "b": ("Lumo and Pixa", ["https://pixa.example/", "https://lumo.example/b"]),
                         "c": ("Pixa", ["https://pixa.example/", "https://reddit.com/y"]),
                         "d": ("nothing", ["https://g2.com/x"])})
        sm = run["summary"]
        self.assertEqual((sm["overall"]["cited"], sm["overall"]["answered"]), (2, 4))
        self.assertEqual(sm["overall"]["cited_ci"], [0.15, 0.85])
        self.assertEqual(sm["engines"][0]["avg_rank"], 1.5)
        self.assertEqual(sm["gaps"], [{"query_id": "q3", "query": "c", "competitors": ["Pixa"], "answered": 1}])
        top = dict((s["domain"], (s["answers"], s["owner"])) for s in sm["top_sources"])
        self.assertEqual(top, {"reddit.com": (2, None), "pixa.example": (2, "Pixa"), "g2.com": (1, None)})
        share = dict((s["name"], s["cited"]) for s in sm["share_of_voice"])
        self.assertEqual(share, {"Lumo": 2, "Pixa": 2, "Reelcraft": 0})
        self.assertEqual([(t["tier"], t["answered"]) for t in sm["by_tier"]], [("list", 2), ("pricing", 2)])
        self.assertEqual(sm["questions"], {"asked": 4, "cited_somewhere": 2})
        text = gw.render(run)
        self.assertIn("Cited in 50% of answers (2 of 4, 95% CI 15–85%)", text)
        self.assertIn("Pixa", gw.render(run, "md"))

    def test_diff(self):
        def mk(cited_ids, n=40):
            per = {}
            for i in range(n):
                q = "q%03d" % i
                per[q] = ("x", ["https://lumo.example/%s" % q] if i in cited_ids else ["https://a.com/"])
            self.fake({"api.openai.com": canned(per)})
            qs = [{"query_id": q, "query": q, "intent_tier": "", "target_url": ""} for q in sorted(per)]
            return gw.execute(brand(), [], engines("chatgpt-api"), qs, max_calls=n)
        a, b = mk({0, 1}), mk(set(range(1, 21)))
        a["run_id"], b["run_id"] = "20260919T083000Z", "20260926T083000Z"
        d = gw.diff_runs(a, b)
        self.assertEqual(d["overall"]["verdict"], "change")
        self.assertEqual(d["overall"]["delta"], 0.45)
        self.assertEqual([x["query_id"] for x in d["lost"]], ["q000"])
        self.assertEqual(d["lost"][0]["was"], "https://lumo.example/q000")
        self.assertEqual(len(d["gained"]), 19)
        c = mk(set(range(0, 3)))
        c["run_id"] = "20261003T083000Z"
        self.assertEqual(gw.diff_runs(a, c)["overall"]["verdict"], "within noise")
        c["engines"][0]["model"] = "gpt-5"
        self.assertIn("model changed", gw.diff_runs(a, c)["engines"][0]["note"])
        self.assertIn("within noise", gw.render_diff(gw.diff_runs(a, c)))

    def test_csv(self):
        self.fake(self.standard_routes())
        qs = [{"query_id": "q01", "query": "=HYPERLINK(\"http://x\")", "intent_tier": "list", "target_url": ""},
              {"query_id": "q02", "query": "normal", "intent_tier": "", "target_url": ""}]
        run = gw.execute(brand(), rivals(), engines("chatgpt-api", "perplexity-api"), qs, max_calls=3)
        rows = list(__import__("csv").reader(io.StringIO(gw.render_csv(run))))
        self.assertEqual(rows[0], gw.CSV_COLS)
        week = "%d-W%02d" % FIXED_NOW.isocalendar()[:2]
        self.assertTrue(all(r[0] == week for r in rows[1:]))
        self.assertTrue(rows[1][2].startswith("'="))
        cited = [r for r in rows[1:] if r[4] == "chatgpt-api" and r[5] == "Y"]
        self.assertEqual(cited[0][6:9], ["https://www.lumo.example/free", "1", "pixa.example"])
        skipped = [r for r in rows[1:] if r[5] == ""]
        self.assertEqual(len(skipped), 1)
        self.assertTrue(skipped[0][9].startswith("skipped: max_calls"))


# ── the run file ──────────────────────────────────────────────────────────
def validate(inst, schema, root=None, path="$"):
    """Enough JSON Schema for our own file: type, const, enum, required, properties, additionalProperties,
    items, pattern, minimum and local $ref."""
    root = root or schema
    errs = []
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return validate(inst, node, root, path)
    t = schema.get("type")
    if t:
        types = t if isinstance(t, list) else [t]
        ok = any({"object": isinstance(inst, dict), "array": isinstance(inst, list), "string": isinstance(inst, str),
                  "boolean": isinstance(inst, bool), "null": inst is None,
                  "integer": isinstance(inst, int) and not isinstance(inst, bool),
                  "number": isinstance(inst, (int, float)) and not isinstance(inst, bool)}[x] for x in types)
        if not ok:
            return ["%s: expected %s, got %r" % (path, t, inst)]
    if "const" in schema and inst != schema["const"]:
        errs.append("%s: expected %r" % (path, schema["const"]))
    if "enum" in schema and inst not in schema["enum"]:
        errs.append("%s: %r not in %r" % (path, inst, schema["enum"]))
    if "pattern" in schema and isinstance(inst, str) and not re.search(schema["pattern"], inst):
        errs.append("%s: %r does not match %s" % (path, inst, schema["pattern"]))
    if "minimum" in schema and isinstance(inst, (int, float)) and inst < schema["minimum"]:
        errs.append("%s: below minimum" % path)
    if isinstance(inst, dict):
        for k in schema.get("required", []):
            if k not in inst:
                errs.append("%s: missing %s" % (path, k))
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for k, v in inst.items():
            if k in props:
                errs += validate(v, props[k], root, path + "." + k)
            elif extra is False:
                errs.append("%s: unexpected key %s" % (path, k))
            elif isinstance(extra, dict):
                errs += validate(v, extra, root, path + "." + k)
    if isinstance(inst, list) and "items" in schema:
        for i, v in enumerate(inst):
            errs += validate(v, schema["items"], root, "%s[%d]" % (path, i))
    return errs


class RunFile(Base):
    def test_every_kind_of_sample_matches_the_schema(self):
        with io.open(os.path.join(HERE, "..", "schema", "watch.v1.json"), encoding="utf-8") as f:
            schema = json.load(f)
        del os.environ["GEMINI_API_KEY"]
        routes = self.standard_routes()
        routes["api.anthropic.com"] = lambda u, h, b: (401, {"error": {"message": "bad key"}})
        self.fake(routes)
        run = gw.execute(brand(), rivals(), engines("chatgpt-api", "perplexity-api", "gemini-api", "claude-api"),
                         queries(3), max_calls=100, budget=None)
        kinds = set((s["status"], s.get("skip_reason")) for s in run["samples"])
        self.assertIn(("ok", None), kinds)
        self.assertIn(("error", None), kinds)
        self.assertTrue(any(k[0] == "skipped" for k in kinds))
        self.assertEqual(validate(json.loads(json.dumps(run)), schema), [])
        cfg = self.config()
        path = gw.save_run(cfg, run)
        with io.open(path, encoding="utf-8") as f:
            text = f.read()
        for k in KEYS.values():
            self.assertNotIn(k, text)

    def config(self, extra=None, queries_csv="query_id,query,intent_tier,target_url\nq01,which is best,list,\n"):
        c = {"brand": {"name": "Lumo", "domains": ["lumo.example"]}, "competitors": [{"name": "Pixa", "domains": ["pixa.example"]}]}
        c.update(extra or {})
        with io.open(os.path.join(self.tmp, "geo-score-watch.json"), "w", encoding="utf-8") as f:
            json.dump(c, f)
        with io.open(os.path.join(self.tmp, "queries.csv"), "w", encoding="utf-8") as f:
            f.write(queries_csv)
        return gw.Config(os.path.join(self.tmp, "geo-score-watch.json"))

    def test_ids_never_collide_and_sort_numerically(self):
        cfg = self.config()
        ids = []
        for _ in range(11):
            run = {"run_id": "20260926T083000Z", "format": gw.RUN_FORMAT}
            gw.save_run(cfg, run)
            ids.append(run["run_id"])
        self.assertEqual(ids[:3], ["20260926T083000Z", "20260926T083000Z-2", "20260926T083000Z-3"])
        self.assertEqual(gw.list_run_ids(cfg)[-1], "20260926T083000Z-11")
        self.assertEqual(gw.load_run(cfg)["run_id"], "20260926T083000Z-11")
        self.assertEqual(gw.load_run(cfg, "previous")["run_id"], "20260926T083000Z-10")
        for bad in ("../../etc/passwd", "20260926T083000Z/../x", "latest.json"):
            with self.assertRaises(gw.ConfigError):
                gw.load_run(cfg, bad)

    def test_config_validation(self):
        cfg = self.config({"engines": [{"provider": "nope"}, {"id": "Chat GPT", "provider": "openai"},
                                       {"id": "x", "provider": "openai", "model": "a b"},
                                       {"id": "y", "provider": "openai", "base_url": "http://evil.example/v1"},
                                       {"id": "z", "provider": "openai", "base_url": "http://localhost:8080/v1"},
                                       {"id": "z", "provider": "perplexity", "key_env": "lower-case"},
                                       {"id": "w", "provider": "openai", "api": "generate_content"},
                                       {"id": "v", "provider": "gemini", "api": "generate_content"}],
                           "country": "usa", "runs": 0, "prices": {"x": {"input_per_mtok": "cheap"}},
                           "competitors": [{"name": "Lumo", "domains": ["x.com"]}, {"name": "AI", "domains": ["ai.com"]}]})
        text = "\n".join(cfg.errors)
        for needle in ("engines[0].provider", "engines[1].id", "engines[2].model", "engines[3].base_url",
                       "engines[5].id", "engines[5].key_env", "engines[6].api", "country", "runs", "prices.x", "competitor name 'Lumo'"):
            self.assertIn(needle, text)
        self.assertNotIn("engines[4]", text)
        self.assertNotIn("engines[7]", text)
        self.assertTrue(any("'AI' is shorter" in w for w in cfg.warnings))

    def test_query_files(self):
        cfg = self.config(queries_csv="﻿query_id,query,intent_tier,target_url\nq01,哪个AI视频工具免费,list,\n,,,\n")
        self.assertEqual(cfg.load_queries()[0]["query"], "哪个AI视频工具免费")
        with io.open(os.path.join(self.tmp, "queries.csv"), "wb") as f:
            f.write("query_id,query\nq01,哪个AI视频工具免费\n".encode("gb18030"))
        self.assertEqual(cfg.load_queries()[0]["query"], "哪个AI视频工具免费")
        for body, needle in (("query_id,query\nq01,<a question>\n", "placeholder"),
                             ("query_id,query\nq01,a\nq01,b\n", "used twice"),
                             ("query_id,query\nq 1,a\n", "letters, digits"),
                             ("id,question\nq01,a\n", "needs the columns"),
                             ("query_id,query\n", "no questions"),
                             ("query_id,query\nq01,%s\n" % ("x" * 501), "longer than")):
            with io.open(os.path.join(self.tmp, "queries.csv"), "w", encoding="utf-8") as f:
                f.write(body)
            with self.assertRaises(gw.ConfigError) as cm:
                cfg.load_queries()
            self.assertIn(needle, str(cm.exception))


# ── transport, for real, against a local server ───────────────────────────
class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n)
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:%d/ok" % self.server.server_address[1])
            self.end_headers()
            return
        code = 200 if self.path == "/ok" else 500
        out = json.dumps({"echo": json.loads(body.decode()), "auth": self.headers.get("Authorization")}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


class Transport(unittest.TestCase):
    def setUp(self):
        self.srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = "http://127.0.0.1:%d" % self.srv.server_address[1]
        self._opener = gw._OPENER
        gw._OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), gw._NoRedirect)

    def tearDown(self):
        gw._OPENER = self._opener
        self.srv.shutdown()
        self.srv.server_close()

    def test_post_ok_error_and_redirect_not_followed(self):
        st, h, raw = gw.http_post(self.base + "/ok", {"Authorization": "Bearer secret"}, {"a": 1})
        self.assertEqual((st, json.loads(raw)["echo"]), (200, {"a": 1}))
        st, h, raw = gw.http_post(self.base + "/fail", {}, {"a": 1})
        self.assertEqual(st, 500)
        st, h, raw = gw.http_post(self.base + "/redirect", {"Authorization": "Bearer secret"}, {"a": 1})
        self.assertEqual(st, 302)                               # surfaced, not followed: the key stays put

    def test_unreachable_is_a_transport_error(self):
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()                                               # nothing listens there now
        with self.assertRaises(gw.TransportError):
            gw.http_post("http://127.0.0.1:%d/ok" % port, {}, {}, timeout=3)


# ── CLI end to end ────────────────────────────────────────────────────────
class CLI(Base):
    def main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gw.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_init_run_report_diff(self):
        del os.environ["GEMINI_API_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]
        self.fake(self.standard_routes())
        cfgp = os.path.join(self.tmp, "geo-score-watch.json")
        code, out, _ = self.main("init", "--dir", self.tmp, "--brand", "Lumo", "--domain", "lumo.example",
                                 "--competitor", "Pixa=pixa.example", "--country", "us")
        self.assertEqual(code, 0)
        self.assertEqual(self.main("init", "--dir", self.tmp)[0], 1)               # no silent overwrite
        code, _, err = self.main("run", "-c", cfgp)
        self.assertEqual(code, 1)
        self.assertIn("placeholder", err)
        with io.open(os.path.join(self.tmp, "queries.csv"), "w", encoding="utf-8") as f:
            f.write("query_id,query,intent_tier,target_url\nq01,best free ai video generator,list,\n"
                    "q02,lumo vs pixa,vs,\n")
        code, out, _ = self.main("check", "-c", cfgp)
        self.assertEqual(code, 0)
        self.assertIn("2 questions", out)
        code, out, _ = self.main("run", "-c", cfgp, "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("2 questions × 2 engines × 1 = 4", out)
        self.assertIn("gemini-api: not measured — set GEMINI_API_KEY or GOOGLE_API_KEY", out)
        self.assertEqual(self.main("run", "-c", cfgp, "--max-calls", "3")[0], 1)
        for bad in (["--limit", "-1"], ["--budget-usd", "-1"], ["--max-calls", "0"]):
            self.assertEqual(self.main("run", "-c", cfgp, *bad)[0], 1)
        code, out, err = self.main("run", "-c", cfgp)
        self.assertEqual(code, 0, err)
        self.assertIn("Cited in 50% of answers", out)
        self.assertIn("[4/4]", err)
        gw.NOW = lambda: FIXED_NOW + datetime.timedelta(days=7)
        self.assertEqual(self.main("run", "-c", cfgp, "-q")[0], 0)
        code, out, _ = self.main("runs", "-c", cfgp)
        self.assertEqual(len([l for l in out.splitlines() if re.match(r"\s+2026", l)]), 2)
        for fmt in ("md", "csv", "json", "text"):
            code, out, _ = self.main("report", "-c", cfgp, "--format", fmt)
            self.assertEqual(code, 0)
        mdp = os.path.join(self.tmp, "r.md")
        self.assertEqual(self.main("report", "-c", cfgp, "--format", "md", "-o", mdp)[0], 0)
        self.assertTrue(os.path.getsize(mdp) > 200)
        code, out, _ = self.main("diff", "-c", cfgp)
        self.assertEqual(code, 0)
        self.assertIn("within noise", out)
        code, out, _ = self.main("ask", "-c", cfgp, "which AI video tool is free?", "--engines", "chatgpt-api")
        self.assertEqual(code, 0)
        self.assertIn("cited #1 (https://www.lumo.example/free)", out)
        self.assertEqual(self.main("report", "-c", cfgp, "../x")[0], 1)

    def test_ask_without_config_or_keys(self):
        for k in ALL_KEY_ENVS:
            os.environ.pop(k, None)
        code, _, err = self.main("ask", "-c", os.path.join(self.tmp, "none.json"), "q?")
        self.assertEqual(code, 3)
        self.assertIn("export at least one API key", err)
        os.environ["PERPLEXITY_API_KEY"] = KEYS["PERPLEXITY_API_KEY"]
        self.fake(self.standard_routes())
        code, out, _ = self.main("ask", "-c", os.path.join(self.tmp, "none.json"), "q?", "--brand", "Pixa",
                                 "--domain", "pixa.example")
        self.assertEqual(code, 0)
        self.assertIn("perplexity-api (sonar) — cited #1 (https://pixa.example/)", out)
        self.assertIn("chatgpt-api — not measured", out)


# ── MCP ───────────────────────────────────────────────────────────────────
class MCP(Base):
    def server(self, with_config=True):
        cfgp = os.path.join(self.tmp, "geo-score-watch.json")
        if with_config:
            with io.open(cfgp, "w", encoding="utf-8") as f:
                json.dump({"brand": {"name": "Lumo", "domains": ["lumo.example"]},
                           "engines": engines("chatgpt-api", "perplexity-api"), "max_calls": 10}, f)
            with io.open(os.path.join(self.tmp, "queries.csv"), "w", encoding="utf-8") as f:
                f.write("query_id,query\nq01,best free ai video generator\nq02,lumo pricing\n")
        self.out = io.StringIO()
        return gw.MCPServer(cfgp, out=self.out)

    def call(self, srv, name, args=None, meta=None):
        p = {"name": name, "arguments": args or {}}
        if meta:
            p["_meta"] = meta
        r = srv.handle({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": p})
        self.assertEqual(r["id"], 7)
        return r["result"]

    def test_handshake_and_listing(self):
        srv = self.server()
        r = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t"}}})
        self.assertEqual(r["result"]["protocolVersion"], "2025-03-26")
        self.assertEqual(r["result"]["serverInfo"]["name"], "geo-score")
        r = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}})
        self.assertEqual(r["result"]["protocolVersion"], gw.MCP_VERSIONS[0])
        self.assertIsNone(srv.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(srv.handle({"jsonrpc": "2.0", "id": 3, "method": "ping"})["result"], {})
        names = [t["name"] for t in srv.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/list"})["result"]["tools"]]
        self.assertEqual(names[:5], ["ask", "run", "list_runs", "report", "diff"])
        self.assertEqual(srv.handle({"jsonrpc": "2.0", "id": 5, "method": "nope"})["error"]["code"], -32601)
        self.assertEqual(srv.handle({"id": 6, "method": "ping"})["error"]["code"], -32600)
        self.assertIsNone(srv.handle({"jsonrpc": "2.0", "id": 9, "result": {}}))

    def test_tools(self):
        srv = self.server()
        self.fake(self.standard_routes())
        r = self.call(srv, "ask", {"question": "best free ai video generator"}, meta={"progressToken": "p1"})
        self.assertFalse(r["isError"], r)
        self.assertIn("cited #1 (https://www.lumo.example/free)", r["content"][0]["text"])
        notes = [json.loads(l) for l in self.out.getvalue().splitlines()]
        self.assertEqual(sorted(n["params"]["progress"] for n in notes), [1, 2])
        self.assertTrue(self.call(srv, "ask", {"question": ""})["isError"])
        self.assertTrue(self.call(srv, "ask", {"question": "q", "engines": "chatgpt-api"})["isError"])
        self.assertTrue(self.call(srv, "report")["isError"])                       # no runs yet
        r = self.call(srv, "run", {"dry_run": True, "max_calls": 999})
        self.assertIn("= 4 (cap 10)", r["content"][0]["text"])                    # can tighten, never loosen
        self.assertTrue(self.call(srv, "run", {"max_calls": 3})["isError"])
        r = self.call(srv, "run", {})
        self.assertFalse(r["isError"], r)
        self.assertIn("saved `.geo-score/watch/runs/", r["content"][0]["text"])
        gw.NOW = lambda: FIXED_NOW + datetime.timedelta(days=7)
        self.assertFalse(self.call(srv, "run", {"limit": 1})["isError"])
        self.assertIn("20260926T083000Z", self.call(srv, "list_runs")["content"][0]["text"])
        self.assertIn("By engine", self.call(srv, "report")["content"][0]["text"])
        summary = json.loads(self.call(srv, "report", {"format": "json"})["content"][0]["text"])
        self.assertEqual(summary["overall"]["answered"], 2)
        self.assertIn("Changes", self.call(srv, "diff")["content"][0]["text"])
        self.assertTrue(self.call(srv, "report", {"run": "../../x"})["isError"])
        self.assertTrue(self.call(srv, "nope")["isError"])
        self.assertTrue(self.call(srv, "__init__")["isError"])

    def test_ask_without_a_config(self):
        srv = self.server(with_config=False)
        self.fake(self.standard_routes())
        r = self.call(srv, "ask", {"question": "q", "brand": "Pixa", "domains": ["pixa.example"],
                                   "engines": ["perplexity-api"]})
        self.assertFalse(r["isError"], r)
        self.assertIn("cited #1 (https://pixa.example/)", r["content"][0]["text"])

    def test_score_site_is_listed_only_when_geo_score_is_found(self):
        real = gw.load_geo_score
        gw.load_geo_score = lambda: None
        try:
            self.assertNotIn("score_site", [t["name"] for t in self.server().tools()])
        finally:
            gw.load_geo_score = real
        os.environ["GEO_SCORE_PY"] = os.path.join(self.tmp, "missing.py")
        self.assertIn("score_site", [t["name"] for t in self.server().tools()])   # the geo_score.py beside it
        fake = os.path.join(self.tmp, "geo_score.py")
        with io.open(fake, "w", encoding="utf-8") as f:
            f.write("print('stdout noise at import')\n"
                    "def run(url, sample=8):\n    print('noise'); return {'u': url}\n"
                    "def as_json(res):\n    return {'target': res['u'], 'normalised': 71, 'band': 'Solid', "
                    "'gate_capped': False, 'tool': 'geo-score-cli/1.1.2', 'rubric_version': 'v1.1', "
                    "'checks': [{'id': 'p1.bc', 'state': 'scored', 'points': 0, 'max': 3, 'evidence': 'none'}]}\n")
        os.environ["GEO_SCORE_PY"] = fake
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            srv = self.server()
            r = self.call(srv, "score_site", {"url": "stripe.com"})
        self.assertFalse(r["isError"], r)
        self.assertIn("71 / 100 · Solid", r["content"][0]["text"])
        self.assertIn("https://stripe.com", r["content"][0]["text"])
        self.assertEqual(self.out.getvalue(), "")                                 # noise went to stderr
        self.assertTrue(self.call(srv, "score_site", {"url": "file:///etc/passwd"})["isError"])

    def test_stdio_stays_pure_json(self):
        env = dict(os.environ)
        for k in ALL_KEY_ENVS:
            env.pop(k, None)
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "ask", "arguments": {"question": "q"}}}]
        stdin = "\n".join(json.dumps(m) for m in msgs) + "\nnot json\n"
        p = subprocess.run([sys.executable, os.path.join(HERE, "geo_score.py"), "mcp", "-c",
                            os.path.join(self.tmp, "none.json")], input=stdin.encode(), capture_output=True,
                           env=env, timeout=60)
        lines = [json.loads(l) for l in p.stdout.decode().splitlines()]
        self.assertEqual([l.get("id") for l in lines], [1, 2, 3, None])
        self.assertEqual(lines[0]["result"]["serverInfo"]["name"], "geo-score")
        self.assertIn("score_site", [t["name"] for t in lines[1]["result"]["tools"]])
        self.assertTrue(lines[2]["result"]["isError"])                              # no keys in this environment
        self.assertEqual(lines[3]["error"]["code"], -32700)


# ── level 2 and the geo_score.py entry point ─────────────────────────────
class Level2(Base):
    def schema_citation(self):
        with io.open(os.path.join(HERE, "..", "schema", "report.v2.json"), encoding="utf-8") as f:
            sc = json.load(f)
        return sc["properties"]["citation"], sc

    def test_without_keys_nothing_is_measured(self):
        for k in ALL_KEY_ENVS:
            os.environ.pop(k, None)
        run, cit = gw.citation_check("https://www.lumo.example/", ["best free ai video generator"])
        self.assertIsNone(run)
        self.assertFalse(cit["measured"])
        self.assertEqual(cit["engines"], [])
        self.assertIn("no API key", cit["note"])
        node, root = self.schema_citation()
        self.assertEqual(validate(cit, node, root), [])

    def test_with_keys_the_result_fits_the_reserved_citation_field(self):
        del os.environ["GEMINI_API_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]
        self.fake(self.standard_routes())
        run, cit = gw.citation_check("https://www.lumo.example/", ["q one", "q two"])
        self.assertTrue(cit["measured"])
        self.assertEqual(cit["channel"], "api")
        self.assertEqual(cit["engines"], ["chatgpt-api", "perplexity-api"])
        self.assertEqual((cit["answered"], cit["cited_count"]), (4, 2))       # openai cites lumo; perplexity does not
        self.assertEqual([e["engine"] for e in cit["per_engine"]], ["chatgpt-api", "perplexity-api"])
        self.assertIn("never summed into readiness", cit["note"])
        node, root = self.schema_citation()
        self.assertEqual(validate(json.loads(json.dumps(cit)), node, root), [])
        text = "\n".join(gw.citation_lines(run, cit))
        self.assertIn("q1 cited #1", text)
        self.assertIn("gemini-api", text)                                     # named as not measured, not zero

    def test_brand_defaults_to_the_domain_and_questions_are_capped(self):
        self.fake(self.standard_routes())
        del os.environ["PERPLEXITY_API_KEY"]
        run, cit = gw.citation_check("https://www.lumo.example/", ["q"])
        self.assertEqual(run["brand"]["name"], "lumo")
        self.assertEqual(run["brand"]["domains"], ["lumo.example"])
        for bad in ([], ["x" * 501], ["a", "b", "c", "d", "e", "f"]):
            with self.assertRaises(gw.ConfigError):
                gw.citation_check("https://a.example/", bad)


class EntryPoint(unittest.TestCase):
    def cli(self, *args, stdin=None):
        env = dict(os.environ)
        for k in ALL_KEY_ENVS:
            env.pop(k, None)
        return subprocess.run([sys.executable, os.path.join(HERE, "geo_score.py")] + list(args),
                              input=stdin, capture_output=True, env=env, timeout=60)

    def test_watch_is_a_subcommand_of_geo_score(self):
        p = self.cli("watch", "--help")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(b"geo_score.py watch", p.stdout)
        self.assertEqual(self.cli("watch", "--version").stdout.strip(), b"geo-score watch " + gw.__version__.encode())

    def test_versions_match(self):
        p = self.cli("--version")
        self.assertIn(gw.__version__.encode(), p.stdout)

    def test_ask_needs_one_site(self):
        p = self.cli("a.example", "--compare", "b.example", "--ask", "q")
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"one site at a time", p.stderr)

    def test_piped_without_the_watch_file_says_what_to_download(self):
        with io.open(os.path.join(HERE, "geo_score.py"), "rb") as f:
            src = f.read()
        env = dict(os.environ)
        p = subprocess.run([sys.executable, "-", "watch", "--help"], input=src, capture_output=True,
                           cwd=tempfile.gettempdir(), env=env, timeout=60)
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"geo_watch.py", p.stderr)


# ── review findings (2026-09-27): each one pinned by a test ──────────────
class ReviewFindings(Base):
    def test_a_malformed_key_is_never_used_or_echoed(self):
        os.environ["OPENAI_API_KEY"] = "sk-proj-FIRSTHALF999\nSECONDHALF888"
        self.assertEqual(gw.key_for(engines("chatgpt-api")[0]), "")
        issue = gw.key_issue(engines("chatgpt-api")[0])
        self.assertIn("OPENAI_API_KEY", issue)
        self.assertNotIn("FIRSTHALF", issue)
        self.fake(self.standard_routes())
        run = gw.execute(brand(), [], engines("chatgpt-api"), queries(1))
        self.assertEqual(run["engines"][0]["status"], "no_key")
        self.assertNotIn("FIRSTHALF", json.dumps(run))

    def test_redact_catches_escaped_and_split_keys(self):
        key = "sk-proj-FIRSTHALF999\nSECONDHALF888"
        for text in ("b'Bearer %s'" % repr(key)[1:-1], "part sk-proj-FIRSTHALF999 and SECONDHALF888", key):
            out = gw.redact(text, key)
            self.assertNotIn("FIRSTHALF999", out)
            self.assertNotIn("SECONDHALF888", out)

    def test_invalid_header_errors_do_not_carry_the_message(self):
        class Boom(Exception):
            pass
        real = gw._OPENER
        class O:
            def open(self, *a, **k):
                raise ValueError("Invalid header value b'Bearer sk-SECRET-123456'")
        gw._OPENER = O()
        try:
            with self.assertRaises(gw.TransportError) as cm:
                gw.http_post("https://api.example/", {"Authorization": "Bearer x"}, {})
        finally:
            gw._OPENER = real
        self.assertNotIn("SECRET", str(cm.exception))

    def test_unexpected_errors_are_redacted_in_the_engine_row(self):
        key = KEYS["OPENAI_API_KEY"]
        def boom(u, h, b):
            raise RuntimeError("proxy said: auth header Bearer " + key)
        gw.TRANSPORT = boom
        run = gw.execute(brand(), [], engines("chatgpt-api"), queries(4))
        self.assertNotIn(key, json.dumps(run))
        self.assertEqual(run["engines"][0]["stopped"], "engine_failed")

    def test_level2_never_reports_unmeasured_zeros(self):
        del os.environ["GEMINI_API_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]
        self.fake({"api.openai.com": lambda u, h, b: (401, {"error": {"message": "bad key"}}),
                   "api.perplexity.ai": lambda u, h, b: (401, {"error": {"message": "bad key"}})})
        run, cit = gw.citation_check("https://lumo.example/", ["q"])
        self.assertEqual(set(cit), {"channel", "queries", "measured", "engines", "note"})
        self.assertFalse(cit["measured"])
        self.assertIn("chatgpt-api", cit["note"])
        routes = self.standard_routes()
        routes["api.perplexity.ai"] = lambda u, h, b: (503, {"error": {"message": "down"}})
        self.fake(routes)
        run, cit = gw.citation_check("https://lumo.example/", ["q"])
        self.assertEqual(cit["engines"], ["chatgpt-api"])
        self.assertEqual([e["engine"] for e in cit["per_engine"]], ["chatgpt-api"])
        self.assertIsNone(cit["cost_usd"])
        self.assertIn("No answer from: perplexity-api", cit["note"])
        text = "\n".join(gw.citation_lines(run, cit))
        self.assertIn("failed (HTTP 503", text)

    def test_brand_and_domains_come_from_the_site_not_the_subdomain(self):
        eq = self.assertEqual
        eq(gw.site_domain("docs.stripe.com"), "stripe.com")
        eq(gw.site_domain("shop.acme.co.uk"), "acme.co.uk")
        eq(gw.site_domain("acme.github.io"), "acme.github.io")
        eq(gw.site_domain("a.b.myshopify.com"), "b.myshopify.com")
        self.fake(self.standard_routes())
        del os.environ["PERPLEXITY_API_KEY"]
        run, cit = gw.citation_check("https://docs.lumo.example/", ["q"], landed_url="https://www.lumo-new.example/")
        eq(run["brand"]["name"], "lumo")
        eq(run["brand"]["domains"], ["lumo.example", "lumo-new.example"])
        self.assertTrue(cit["measured"])
        self.assertEqual(cit["cited_count"], 1)          # the apex citation counts for a docs subdomain
        run, cit = gw.citation_check("https://m.io/", ["q"])
        eq(run["brand"]["name"], "")
        self.assertIn("too short", cit["note"])

    def test_idn_hosts_match_their_punycode(self):
        self.assertEqual(gw.host_of("https://例子.cn/x"), gw.host_of("https://xn--fsqu00a.cn/x"))

    def test_names_accented_latin_whole_word_cjk_anywhere(self):
        e = gw.Entity({"name": "Nestlé", "aliases": ["鹿末"]})
        self.assertTrue(e.named_in("Try Nestlé cereal"))
        self.assertFalse(e.named_in("Nestléxyz is different"))
        self.assertTrue(e.named_in("关于鹿末视频"))

    def test_terminal_escapes_are_stripped(self):
        self.assertEqual(gw._cut("safe\x1b[31mRED\x1b[0m text\u202e", 80), "safe[31mRED[0m text")

    def test_mcp_ask_is_not_read_only_and_score_site_refuses_private_hosts(self):
        srv = gw.MCPServer(os.path.join(self.tmp, "none.json"), out=io.StringIO())
        ask = next(t for t in srv.tools() if t["name"] == "ask")
        self.assertFalse(ask["annotations"]["readOnlyHint"])
        for bad in ("http://localhost/", "http://127.0.0.1:8080/", "10.0.0.5", "http://169.254.169.254/latest"):
            r = srv.call({"name": "score_site", "arguments": {"url": bad}})
            self.assertTrue(r["isError"], bad)

    def test_init_pins_the_models(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(gw.main(["init", "--dir", self.tmp, "--brand", "Lumo", "--domain", "lumo.example"]), 0)
        with io.open(os.path.join(self.tmp, gw.CONFIG_NAME), encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertTrue(all(e.get("model") for e in cfg["engines"]))

    def test_run_without_keys_exits_3_and_dry_run_still_shows_the_plan(self):
        for k in ALL_KEY_ENVS:
            os.environ.pop(k, None)
        cfgp = os.path.join(self.tmp, gw.CONFIG_NAME)
        with io.open(cfgp, "w", encoding="utf-8") as f:
            json.dump({"brand": {"name": "Lumo", "domains": ["lumo.example"]}}, f)
        with io.open(os.path.join(self.tmp, "queries.csv"), "w", encoding="utf-8") as f:
            f.write("query_id,query\nq01,a real question\n")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(gw.main(["run", "-c", cfgp, "--dry-run"]), 0)
            self.assertEqual(gw.main(["run", "-c", cfgp]), 3)
            self.assertEqual(gw.main(["ask", "-c", cfgp, "q?"]), 3)
        self.assertIn("nothing would be measured", out.getvalue())


class MergeSeam(Base):
    """geo_score.py --ask: the readiness half must come out identical with and without it."""
    def score_main(self, argv):
        import geo_score as gs
        full = {c[0]: c[3] for c in gs.SPEC}
        res = dict(root="https://www.lumo.example/", landed="https://www.lumo.example/", urls=["https://www.lumo.example/"],
                   lang="en", tier=full, ev={k: "" for k in full}, bonus={}, robots_bytes=0)
        real_run, real_mod, real_argv = gs.run, gs._watch_module, sys.argv
        gs.run = lambda url, sample=8, verbose=False: json.loads(json.dumps(res))
        gw.GEO_SCORE = gs
        gs._watch_module = lambda: gw
        sys.argv = ["geo_score.py"] + argv
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                gs.main()
        finally:
            gs.run, gs._watch_module, sys.argv = real_run, real_mod, real_argv
            gw.GEO_SCORE = None
        return out.getvalue()

    def test_ask_adds_a_citation_block_and_changes_nothing_else(self):
        del os.environ["GEMINI_API_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]
        self.fake(self.standard_routes())
        plain = json.loads(self.score_main(["lumo.example", "--json"]))
        asked = json.loads(self.score_main(["lumo.example", "--json", "--ask", "best free ai video generator"]))
        cit = asked.pop("citation")
        self.assertEqual(plain, asked)
        self.assertTrue(cit["measured"])
        with io.open(os.path.join(HERE, "..", "schema", "report.v2.json"), encoding="utf-8") as f:
            sc = json.load(f)
        self.assertEqual(validate(json.loads(json.dumps(dict(asked, citation=cit))), sc), [])
        text = self.score_main(["lumo.example", "--brief", "--ask", "best free ai video generator"])
        self.assertIn("AI CITATION CHECK", text)
        self.assertIn("q1 cited #1", text)


# ── statistics: clustered intervals, paired diff, Holm ───────────────────
FIXTURES = os.path.join(HERE, "fixtures", "watch")


def watch_schema():
    with io.open(os.path.join(HERE, "..", "schema", "watch.v1.json"), encoding="utf-8") as f:
        return json.load(f)


def synth(run_id, cited, runs=1, qs=None, who=None):
    """A saved run built straight from {(query_id, engine): [cited on each ask]}: no transport, no threads."""
    who = who or brand()
    qids = sorted(set(q for q, _ in cited))
    qs = qs or [{"query_id": q, "query": "question " + q, "intent_tier": "", "target_url": ""} for q in qids]
    samples = []
    for (q, e), asks in sorted(cited.items()):
        for i, c in enumerate(asks, 1):
            url = "https://lumo.example/" + q
            samples.append({"query_id": q, "engine": e, "run": i, "status": "ok", "cited": bool(c),
                            "rank": 1 if c else None, "quoted_url": url if c else None, "mentioned": bool(c),
                            "competitors": {}, "citations": [{"url": url, "domain": "lumo.example", "title": ""}] if c else [],
                            "search_queries": [], "answer": "", "answer_truncated": False,
                            "usage": {"input_tokens": 0, "output_tokens": 0, "search_calls": 0, "api_calls": 1},
                            "cost_usd": None, "seconds": 0.0})
    at = datetime.datetime.strptime(run_id[:16], "%Y%m%dT%H%M%SZ").strftime("%Y-%m-%dT%H:%M:%SZ")
    run = {"format": gw.RUN_FORMAT, "tool": "geo-score-watch/" + gw.__version__, "channel": "api", "run_id": run_id,
           "started_at": at, "finished_at": at, "interrupted": False, "brand": who.as_json(), "competitors": [],
           "country": None, "runs": runs,
           "engines": [dict(e, status="measured") for e in engines(*sorted(set(e for _, e in cited)))],
           "queries": qs, "caps": {"max_calls": 1000, "budget_usd": None},
           "ledger": {"questions_asked": len(samples), "api_requests": len(samples), "http_attempts": len(samples),
                      "errors": 0, "input_tokens": 0, "output_tokens": 0, "search_calls": 0, "cost_usd": 0.0,
                      "unpriced_answers": len(samples), "cost_complete": False},
           "samples": samples, "notes": gw.NOTES}
    run["summary"] = gw.summarize(run)
    return run


def draw(rng, probs, runs=1):
    """One run's answers: each (question, engine) cited on each ask with its own probability."""
    return dict((u, [rng.random() < p for _ in range(runs)]) for u, p in sorted(probs.items()))


class Statistics(Base):
    def test_clustered_interval_is_wider_than_wilson_when_answers_cluster(self):
        # 20 questions asked 10 times each: half are always cited, half never. 200 answers, but only 20 questions.
        cited = dict((("q%02d" % i, "chatgpt-api"), [i < 10] * 10) for i in range(20))
        run = synth("20260926T083000Z", cited, runs=10)
        o = run["summary"]["overall"]
        self.assertEqual((o["answered"], o["n_questions"], o["cited_rate"]), (200, 20, 0.5))
        w, c = o["cited_ci"], o["cited_ci_clustered"]
        self.assertGreater(c[1] - c[0], 2 * (w[1] - w[0]))
        self.assertLess(c[0], w[0])
        self.assertEqual(gw.head_ci(o), c)
        self.assertIn("95%% CI %s" % gw.ci_s(c), gw.render(run))
        self.assertEqual(validate(json.loads(json.dumps(run)), watch_schema()), [])
        # deterministic, and a -2 suffix from save_run does not move it
        self.assertEqual(synth("20260926T083000Z-2", cited, runs=10)["summary"]["overall"]["cited_ci_clustered"], c)
        # asked once each, the Wilson interval is the one quoted, as in 1.2.0
        once = synth("20260926T083000Z", dict((u, a[:1]) for u, a in cited.items()))
        self.assertEqual(gw.head_ci(once["summary"]["overall"]), once["summary"]["overall"]["cited_ci"])

    def test_clustered_interval_is_never_narrower_than_wilson(self):
        # three questions each cited in half their answers: every bootstrap resample says exactly 50%
        self.assertEqual(gw.cluster_ci([(2, 4)] * 3, 1), gw.wilson(6, 12))
        self.assertEqual(gw.cluster_ci([(1, 2)], 1), gw.wilson(1, 2))
        self.assertIsNone(gw.cluster_ci([], 1))

    def test_exact_tests_and_holm(self):
        self.assertEqual(gw.mcnemar_p(0, 5), 0.0625)          # why fewer than 6 questions is "too few to tell"
        self.assertEqual(gw.mcnemar_p(6, 0), 2 / 64.0)
        self.assertEqual(gw.mcnemar_p(3, 3), 1.0)
        self.assertEqual(gw.mcnemar_p(0, 0), 1.0)
        self.assertAlmostEqual(gw.mcnemar_p(1, 19), 42 / 2.0 ** 20)
        for up, down in ((0, 5), (2, 9), (7, 7), (1, 30), (12, 3)):
            self.assertAlmostEqual(gw.signflip_p([1] * up + [-1] * down + [0] * 4), gw.mcnemar_p(up, down))
        self.assertEqual(gw.signflip_p([3, 3, 3]), 0.25)
        self.assertEqual([round(p, 4) for p in gw.holm([0.01, 0.04, 0.03])], [0.03, 0.06, 0.06])
        lo, hi = gw.newcombe_paired(20, 0, 0, 20)             # nothing flipped: still an interval, not a point
        self.assertTrue(lo < -0.02 and hi > 0.02)

    def test_a_null_diff_rarely_calls_a_change(self):
        # Two runs drawn from the same generator: any "change" is a false alarm. Holm keeps them near 5% or below.
        gw.BOOTSTRAP_REPS, saved = 200, gw.BOOTSTRAP_REPS    # intervals do not enter the verdict; keep it quick
        try:
            alarms = 0
            for seed in range(200):
                rng = __import__("random").Random(seed)
                probs = {}
                for i in range(30):
                    base = rng.choice([0.02, 0.1, 0.3, 0.5, 0.7, 0.9, 0.98])
                    probs[("q%02d" % i, "chatgpt-api")] = base
                    probs[("q%02d" % i, "perplexity-api")] = min(0.99, max(0.01, base + rng.choice([-0.1, 0.1])))
                d = gw.diff_runs(synth("20260919T083000Z", draw(rng, probs, 2), runs=2),
                                 synth("20260926T083000Z", draw(rng, probs, 2), runs=2))
                alarms += any(r["verdict"] == "change" for r in [d["overall"]] + d["engines"])
        finally:
            gw.BOOTSTRAP_REPS = saved
        self.assertLessEqual(alarms, 16, "%d of 200 null diffs called a change" % alarms)

    def test_too_few_questions_to_tell(self):
        def flip(n):
            a = synth("20260919T083000Z", dict((("q%d" % i, "chatgpt-api"), [True]) for i in range(n)))
            b = synth("20260926T083000Z", dict((("q%d" % i, "chatgpt-api"), [False]) for i in range(n)))
            return gw.diff_runs(a, b)
        d = flip(5)                                           # all five lost: p = 0.0625, it could be chance
        self.assertEqual(d["overall"]["verdict"], "too few questions to tell")
        self.assertEqual((d["overall"]["p_paired"], d["overall"]["p_adjusted"], d["overall"]["delta_ci"]),
                         (0.0625, None, None))
        self.assertIn("still be within noise", gw.render_diff(d))
        d = flip(6)                                           # one engine: overall and engine are one test
        self.assertEqual(d["overall"]["p_adjusted"], 0.0312)
        self.assertEqual(d["engines"][0]["p_adjusted"], 0.0312)
        self.assertEqual((d["overall"]["verdict"], d["overall"]["delta_pp"]), ("change", -100.0))
        self.assertEqual(gw.drops(d), ["all engines", "chatgpt-api"])

    def test_diff_pairs_the_asks_both_runs_made(self):
        a = synth("20260919T083000Z", dict((("q%d" % i, "chatgpt-api"), [False]) for i in range(8)))
        b = synth("20260926T083000Z", dict((("q%d" % i, "chatgpt-api"), [False, False, True]) for i in range(8)),
                  runs=3)
        d = gw.diff_runs(a, b)
        self.assertEqual(d["overall"]["delta_pp"], 0.0)       # the third ask has nothing to pair with
        self.assertEqual(d["overall"]["verdict"], "within noise")
        self.assertTrue(any("asked each question 1 and 3 times" in n for n in d["notes"]))

    def test_a_planted_drop_is_found_and_fails_the_build(self):
        rng = __import__("random").Random(7)
        units = [("q%02d" % i, e) for i in range(30) for e in ("chatgpt-api", "perplexity-api")]
        a = synth("20260919T083000Z", draw(rng, dict((u, 0.8) for u in units)))
        b = synth("20260926T083000Z", draw(rng, dict((u, 0.2) for u in units)))
        d = gw.diff_runs(a, b)
        for r in [d["overall"]] + d["engines"]:
            self.assertEqual(r["verdict"], "change", r)
            self.assertLess(r["delta_pp"], 0)
            self.assertLess(r["delta_ci"][1], 0)
            self.assertLessEqual(r["p_paired"], r["p_adjusted"])
        self.assertEqual(d["overall"]["n_pairs"], 60)
        self.assertEqual(d["overall"]["n_questions"], 30)
        sc = watch_schema()
        self.assertEqual(validate(json.loads(json.dumps(d)), sc["$defs"]["diff"], sc), [])

        cfgp = os.path.join(self.tmp, gw.CONFIG_NAME)
        with io.open(cfgp, "w", encoding="utf-8") as f:
            json.dump({"brand": {"name": "Lumo", "domains": ["lumo.example"]}}, f)
        cfg = gw.Config(cfgp)
        for r in (a, b):
            gw.save_run(cfg, r)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(gw.main(["diff", "-c", cfgp]), 0)
            self.assertEqual(gw.main(["diff", "-c", cfgp, "--fail-on-drop"]), 4)
            self.assertEqual(gw.main(["diff", "-c", cfgp, "--fail-on-drop", "--format", "json"]), 4)
            self.assertEqual(gw.main(["diff", "-c", cfgp, b["run_id"], a["run_id"], "--fail-on-drop"]), 0)  # a gain
        self.assertIn("dropped beyond noise: all engines, chatgpt-api, perplexity-api", err.getvalue())
        srv = gw.MCPServer(cfgp, out=io.StringIO())
        r = srv.call({"name": "diff", "arguments": {"format": "json"}})
        self.assertFalse(r["isError"], r)
        mj = json.loads(r["content"][0]["text"])
        self.assertEqual(mj["overall"]["verdict"], "change")
        for k in ("p_value", "p_paired", "p_adjusted", "n_pairs", "delta_pp", "delta_ci"):
            self.assertIn(k, mj["overall"])
        self.assertIn("p (Holm)", srv.call({"name": "diff", "arguments": {}})["content"][0]["text"])


# ── run files saved by 1.2.0 ─────────────────────────────────────────────
class OldRuns(Base):
    def setUp(self):
        Base.setUp(self)
        self.cfgp = os.path.join(self.tmp, gw.CONFIG_NAME)
        with io.open(self.cfgp, "w", encoding="utf-8") as f:
            json.dump({"brand": {"name": "Lumo", "domains": ["lumo.example"], "aliases": ["鹿末"]},
                       "competitors": [{"name": "Pixa", "domains": ["pixa.example"]}]}, f)
        self.cfg = gw.Config(self.cfgp)
        os.makedirs(self.cfg.runs_dir())
        self.ids = []
        for name in sorted(os.listdir(FIXTURES)):
            shutil.copy(os.path.join(FIXTURES, name), self.cfg.runs_dir())
            self.ids.append(name[:-5])

    def main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = gw.main(list(argv))
        return code, out.getvalue()

    def test_a_1_2_0_run_file_loads_summarizes_and_diffs(self):
        self.assertEqual(self.ids, ["20260919T083000Z", "20260926T083000Z"])
        sc = watch_schema()
        for rid in self.ids:
            run = gw.load_run(self.cfg, rid)
            self.assertEqual(run["tool"], "geo-score-watch/1.2.0")
            self.assertNotIn("n_questions", run["summary"]["overall"])
            self.assertEqual(validate(run, sc), [])
        run = gw.load_run(self.cfg, self.ids[0])
        sm = gw.summary_of(run)
        self.assertEqual((sm["overall"]["answered"], sm["overall"]["n_questions"]), (24, 6))
        self.assertEqual(sm["overall"]["cited_ci"], run["summary"]["overall"]["cited_ci"])   # Wilson unchanged
        self.assertTrue(sm["overall"]["cited_ci_clustered"])
        self.assertEqual(validate(json.loads(json.dumps(dict(run, summary=sm))), sc), [])
        self.assertIn("95%% CI %s" % gw.ci_s(sm["overall"]["cited_ci_clustered"]), gw.render(run))
        d = gw.diff_runs(*[gw.load_run(self.cfg, rid) for rid in self.ids])
        self.assertEqual(validate(json.loads(json.dumps(d)), sc["$defs"]["diff"], sc), [])
        self.assertEqual(d["overall"]["n_questions"], 6)
        self.assertNotEqual(d["overall"]["verdict"], "change")
        for fmt in ("text", "md", "csv", "json"):
            self.assertEqual(self.main("report", "-c", self.cfgp, "--format", fmt)[0], 0)
        code, out = self.main("report", "-c", self.cfgp, "--format", "json")
        self.assertIn("cited_ci_clustered", json.loads(out)["summary"]["overall"])
        code, out = self.main("diff", "-c", self.cfgp, "--fail-on-drop")
        self.assertEqual(code, 0)
        self.assertIn("within noise", out)
        self.assertEqual(self.main("runs", "-c", self.cfgp)[0], 0)
        with io.open(os.path.join(FIXTURES, self.ids[0] + ".json"), encoding="utf-8") as f:
            self.assertNotIn("n_questions", f.read())                    # reports never rewrite a run file


class PipedDecoy(unittest.TestCase):
    def test_a_geo_watch_py_in_the_current_directory_is_never_loaded(self):
        d = tempfile.mkdtemp(prefix="geo-score-decoy-")
        try:
            with io.open(os.path.join(d, "geo_watch.py"), "w", encoding="utf-8") as f:
                f.write("print('DECOY EXECUTED')\n__version__ = '0.0.0'\ndef main(a=None, prog=None):\n    return 0\n")
            with io.open(os.path.join(HERE, "geo_score.py"), "rb") as f:
                src = f.read()
            p = subprocess.run([sys.executable, "-", "watch", "runs"], input=src, capture_output=True, cwd=d, timeout=60)
            self.assertEqual(p.returncode, 2)
            self.assertNotIn(b"DECOY", p.stdout + p.stderr)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
