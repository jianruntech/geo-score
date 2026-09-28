#!/usr/bin/env python3
"""Tests for geo_watch.py, the watch half of geo-score (levels 2 and 3). No network: every provider is faked
at the transport layer.

    python3 cli/test_geo_watch.py
"""
import contextlib, datetime, http.server, io, json, os, queue, re, shutil, socket, subprocess, sys, tempfile
import threading, time, unittest, urllib.request
from unittest import mock

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

    def test_half_a_surrogate_pair_from_a_provider_is_saved_and_read_back(self):
        cfg = self.config()
        run = synth("20260926T083000Z", {("q01", "chatgpt-api"): [True]})
        run["samples"][0]["answer"] = "half an emoji " + json.loads('"\\ud83d"') + " then 鹿末"
        path = gw.save_run(cfg, run)
        self.assertEqual(gw.load_run(cfg, "latest"), json.loads(json.dumps(run)))
        with io.open(path, "rb") as f:
            self.assertIn(b"\\ud83d", f.read())               # an escape: the file stays valid UTF-8 JSON
        out = os.path.join(self.tmp, "report.json")
        code, _, err = CLI.main(self, "report", "-c", cfg.path, "--format", "json", "-o", out)
        self.assertEqual(code, 0, err)
        with io.open(out, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["samples"][0]["answer"], run["samples"][0]["answer"])

    def test_a_failed_write_leaves_no_file_and_the_latest_run_intact(self):
        cfg = self.config()
        gw.save_run(cfg, {"run_id": "20260926T083000Z", "format": gw.RUN_FORMAT})

        def disk_full(fd):
            raise OSError(28, "No space left on device")
        with mock.patch.object(os, "fsync", disk_full):
            with self.assertRaises(OSError):
                gw.save_run(cfg, {"run_id": "20260927T083000Z", "format": gw.RUN_FORMAT})
        self.assertEqual(os.listdir(cfg.runs_dir()), ["20260926T083000Z.json"])      # no temporary file either
        self.assertEqual(gw.load_run(cfg, "latest")["run_id"], "20260926T083000Z")

    def test_one_id_twice_and_a_file_system_without_hard_links(self):
        cfg = self.config()
        a, b, c = ({"run_id": "20260926T083000Z", "format": gw.RUN_FORMAT} for _ in range(3))
        gw.save_run(cfg, a)
        gw.save_run(cfg, b)
        self.assertEqual((a["run_id"], b["run_id"]), ("20260926T083000Z", "20260926T083000Z-2"))
        self.assertEqual(gw.load_run(cfg, "20260926T083000Z-2")["run_id"], "20260926T083000Z-2")   # the file's own id

        def no_links(src, dst):
            raise PermissionError(1, "Operation not permitted")
        with mock.patch.object(os, "link", no_links):
            gw.save_run(cfg, c)
        self.assertEqual(c["run_id"], "20260926T083000Z-3")
        self.assertEqual(gw.load_run(cfg, "latest"), c)
        self.assertEqual(sorted(os.listdir(cfg.runs_dir())), ["20260926T083000Z-2.json", "20260926T083000Z-3.json",
                                                               "20260926T083000Z.json"])

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


# ── the config file: unknown keys and schema/watch-config.v1.json ────────
def config_schema():
    with io.open(os.path.join(HERE, "..", "schema", "watch-config.v1.json"), encoding="utf-8") as f:
        return json.load(f)


try:
    import jsonschema
except ImportError:          # the stdlib validator above still runs; the full check needs `pip install jsonschema`
    jsonschema = None

FULL_CONFIG = {
    "$schema": gw.CONFIG_SCHEMA_URL,
    "brand": {"name": "Lumo", "domains": ["lumo.example"], "url_prefixes": ["https://www.amazon.com/stores/Lumo/"],
              "aliases": ["鹿末"]},
    "competitors": [{"name": "Pixa", "domains": "pixa.example", "aliases": []}],
    "queries": "queries.csv",
    "engines": [{"id": "chatgpt-api", "provider": "openai", "model": "gpt-6-luna", "tool": "web_search",
                 "key_env": "WORK_OPENAI_KEY", "base_url": "https://proxy.example/v1/responses"},
                {"id": "gemini-api", "provider": "gemini", "api": "generate_content"},
                {"id": "claude-api", "provider": "anthropic", "max_tokens": 1024, "max_searches": 3},
                {"id": "or-api", "provider": "openrouter", "model": "deepseek/deepseek-chat", "max_results": 3},
                {"id": "local-api", "provider": "perplexity", "base_url": "http://localhost:8080/chat"}],
    "country": "US",
    "runs": 2,
    "max_calls": 50,
    "budget_usd": 1.5,
    "prices": {"chatgpt-api": {"input_per_mtok": 0.1, "output_per_mtok": 0.5, "per_search": 0.01, "per_call": 0},
               "claude-api": {"input_per_mtok": 3, "output_per_mtok": 15}},
}


class ConfigKeys(Base):
    """A mistyped key used to vanish without a word: "budget" for "budget_usd" silently meant no budget."""

    def write(self, cfg, questions="query_id,query\nq01,best free ai video generator\n"):
        p = os.path.join(self.tmp, gw.CONFIG_NAME)
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)
        with io.open(os.path.join(self.tmp, "queries.csv"), "w", encoding="utf-8") as f:
            f.write(questions)
        return p

    def main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gw.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def init(self):
        self.assertEqual(self.main("init", "--dir", self.tmp, "--brand", "Lumo", "--domain", "lumo.example",
                                   "--competitor", "Pixa=pixa.example", "--country", "us")[0], 0)
        with io.open(os.path.join(self.tmp, gw.CONFIG_NAME), encoding="utf-8") as f:
            return json.load(f)

    def test_a_mistyped_cap_is_named_with_a_suggestion_everywhere_the_config_is_read(self):
        cfg = self.init()
        cfg["budget"] = cfg.pop("budget_usd")
        cfg["max_call"] = cfg.pop("max_calls")
        p = self.write(cfg)
        budget = "unknown key 'budget' (did you mean 'budget_usd'?); it is ignored"
        max_call = "unknown key 'max_call' (did you mean 'max_calls'?); it is ignored"
        code, out, _ = self.main("check", "-c", p)
        self.assertEqual(code, 0, out)                          # a warning, never a failure
        self.assertIn("! " + budget, out)
        self.assertIn("! " + max_call, out)
        code, out, err = self.main("run", "-c", p, "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("warning: " + budget, err)
        self.assertIn("warning: " + max_call, err)
        srv = gw.MCPServer(p, out=io.StringIO())
        st = srv.call({"name": "status", "arguments": {}})
        self.assertIn(budget, st["structuredContent"]["config"]["warnings"])
        self.assertIn("warning: " + max_call, st["content"][0]["text"])
        dry = srv.call({"name": "run", "arguments": {"dry_run": True}})
        self.assertFalse(dry["isError"], dry)
        self.assertIn(budget, dry["content"][0]["text"])

    def test_every_level_is_checked(self):
        cfg = gw.Config(self.write({
            "brand": {"name": "Lumo", "domain": ["lumo.example"]},
            "competitors": [{"name": "Pixa", "domains": ["pixa.example"], "alias": ["PX"]}],
            "engines": [{"id": "claude-api", "provider": "anthropic", "max_token": 900}],
            "prices": {"claude-api": {"input_per_mtok": 3, "output_per_mtok": 15, "per_searches": 0.01},
                       "claude": {"input_per_mtok": 3, "output_per_mtok": 15}},
            "zzz": 1}))
        self.assertEqual(cfg.errors, [])
        w = "\n".join(cfg.warnings)
        for needle in ("'brand.domain' (did you mean 'brand.domains'?)",
                       "'competitors[0].alias' (did you mean 'competitors[0].aliases'?)",
                       "'engines[0].max_token' (did you mean 'engines[0].max_tokens'?)",
                       "'prices.claude-api.per_searches' (did you mean 'prices.claude-api.per_search'?)",
                       "prices.claude names no engine (did you mean 'claude-api'?); it is ignored",
                       "unknown key 'zzz'; it is ignored"):
            self.assertIn(needle, w)

    def test_a_fresh_config_names_its_schema_first_and_warns_about_nothing(self):
        self.assertEqual(list(self.init())[0], "$schema")
        cfg = gw.Config(os.path.join(self.tmp, gw.CONFIG_NAME))
        self.assertEqual(cfg.raw["$schema"], gw.CONFIG_SCHEMA_URL)
        self.assertFalse([w for w in cfg.warnings if "unknown key" in w or "names no engine" in w], cfg.warnings)
        full = gw.Config(self.write(FULL_CONFIG))
        self.assertEqual((full.errors, full.warnings), ([], []))

    def test_the_schema_lists_exactly_the_keys_config_reads(self):
        sc = config_schema()
        d = sc["$defs"]
        self.assertEqual(sc["$id"], gw.CONFIG_SCHEMA_URL)
        self.assertEqual(list(sc["properties"]), list(gw.CONFIG_KEYS))
        self.assertEqual(list(d["entity"]["properties"]), list(gw.ENTITY_KEYS))
        self.assertEqual(list(d["engine"]["properties"]), list(gw.ENGINE_KEYS))
        self.assertEqual(list(d["price"]["properties"]), list(gw.PRICE_KEYS))
        for node in (sc, d["entity"], d["engine"], d["price"]):
            self.assertIs(node["additionalProperties"], False)
        eng = d["engine"]["properties"]
        self.assertEqual(eng["provider"]["enum"], sorted(gw.PROVIDERS))
        self.assertEqual(eng["id"]["pattern"], gw.ENGINE_ID_RE.pattern)
        self.assertEqual(sc["properties"]["prices"]["propertyNames"]["pattern"], gw.ENGINE_ID_RE.pattern)
        self.assertEqual(eng["model"]["pattern"], gw.MODEL_RE.pattern)
        self.assertEqual(eng["key_env"]["pattern"], gw.ENV_RE.pattern)
        self.assertEqual(eng["base_url"]["pattern"], gw.BASE_URL_RE.pattern)
        self.assertEqual(sc["properties"]["country"]["pattern"], gw.COUNTRY_RE.pattern)
        self.assertEqual(sc["properties"]["runs"]["maximum"], gw.MAX_RUNS)
        self.assertEqual(sc["properties"]["max_calls"]["default"], gw.DEFAULT_MAX_CALLS)

    def test_configs_validate_against_the_schema(self):
        sc = config_schema()
        good = [self.init(), FULL_CONFIG, {"brand": {"name": "Lumo", "domains": ["lumo.example"]}},
                {"brand": {"name": "Lumo", "domains": ["lumo.example"]}, "engines": engines("chatgpt-api", "perplexity-api"),
                 "max_calls": 10},
                {"brand": {"name": "Lumo"}, "competitors": None, "engines": None, "prices": None, "country": None}]
        typo = dict(good[0], budget=1.0)
        if jsonschema is not None:
            v = jsonschema.validators.validator_for(sc)
            v.check_schema(sc)
            check = v(sc)
        for c in good:
            self.assertEqual(validate(c, sc), [], c)
            self.assertEqual(gw.Config(self.write(c)).errors, [], c)
            if jsonschema is not None:
                self.assertEqual([e.message for e in check.iter_errors(c)], [], c)
        self.assertEqual(validate(typo, sc), ["$: unexpected key budget"])
        if jsonschema is None:
            return
        self.assertTrue(list(check.iter_errors(typo)))
        # what Config refuses, the schema refuses too
        for bad in ({"engines": [{"provider": "openai", "api": "generate_content"}]}, {"engines": []},
                    {"engines": [{"provider": "nope"}]}, {"engines": [{"provider": "openai", "id": "Chat GPT"}]},
                    {"engines": [{"provider": "openai", "base_url": "http://evil.example/v1"}]},
                    {"engines": [{"provider": "openai", "key_env": "lower-case"}]},
                    {"country": "usa"}, {"runs": 0}, {"runs": gw.MAX_RUNS + 1}, {"max_calls": 0},
                    {"budget_usd": -1}, {"queries": ""}, {"prices": {"chatgpt-api": {"input_per_mtok": "cheap"}}}):
            c = dict({"brand": {"name": "Lumo", "domains": ["lumo.example"]}}, **bad)
            self.assertTrue(gw.Config(self.write(c)).errors, bad)
            self.assertTrue(list(check.iter_errors(c)), bad)
        self.assertTrue(list(check.iter_errors({"competitors": []})))       # brand.name is required


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
        self.assertIn("too few questions to tell", out)          # two questions cannot show a change
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
def schema_errors(o, sch, path="$"):
    """The part of JSON Schema the MCP output schemas use: type, enum, required, properties, items and anyOf.
    The fallback when jsonschema is not installed, so the suite stays stdlib-only."""
    types = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float),
             "boolean": bool, "null": type(None)}
    if "anyOf" in sch:
        if not any(not schema_errors(o, branch, path) for branch in sch["anyOf"]):
            return ["%s: %r matches no branch of anyOf" % (path, o)]
    t = sch.get("type")
    if t:
        allowed = tuple(types[x] for x in (t if isinstance(t, list) else [t]))
        if not isinstance(o, allowed) or (isinstance(o, bool) and "boolean" not in (t if isinstance(t, list) else [t])):
            return ["%s: expected %s, got %r" % (path, t, o)]
    if "enum" in sch and o not in sch["enum"]:
        return ["%s: %r not in %r" % (path, o, sch["enum"])]
    errs = []
    if isinstance(o, dict):
        errs += ["%s: missing %s" % (path, k) for k in sch.get("required", []) if k not in o]
        for k, sub in sch.get("properties", {}).items():
            if k in o:
                errs += schema_errors(o[k], sub, path + "." + k)
    if isinstance(o, list) and "items" in sch:
        for i, x in enumerate(o):
            errs += schema_errors(x, sch["items"], "%s[%d]" % (path, i))
    return errs


def schema_nodes(sch):
    """Every subschema, for rules that hold everywhere (no type lists)."""
    yield sch
    for k, v in sch.items():
        if k in ("properties",) and isinstance(v, dict):
            for sub in v.values():
                for x in schema_nodes(sub):
                    yield x
        elif k in ("items",) and isinstance(v, dict):
            for x in schema_nodes(v):
                yield x
        elif k in ("anyOf",):
            for sub in v:
                for x in schema_nodes(sub):
                    yield x


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
        self.assertEqual(names, ["score_site", "ask", "run", "list_runs", "report", "diff", "status"])   # free first
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
        for bad in ("nope", "__init__", None):
            r = srv.handle({"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": bad}})
            self.assertEqual(r["error"]["code"], -32602, bad)        # a protocol error, not a tool result

    def check_schema(self, obj, schema, where):
        """jsonschema when it is installed; otherwise the required keys and types, so the suite stays stdlib-only."""
        try:
            import jsonschema
        except ImportError:
            jsonschema = None
        if jsonschema is not None:
            jsonschema.validate(obj, schema)
            return
        self.assertEqual(schema_errors(obj, schema), [], where)

    def test_structured_content_matches_the_declared_output_schema(self):
        srv = self.server()
        self.fake(self.standard_routes())
        self.assertFalse(self.call(srv, "run", {})["isError"])
        gw.NOW = lambda: FIXED_NOW + datetime.timedelta(days=7)
        self.assertFalse(self.call(srv, "run", {})["isError"])
        schemas = {t["name"]: t.get("outputSchema") for t in srv.tools()}
        for name, args in (("list_runs", {}), ("report", {}), ("report", {"format": "json"}), ("diff", {})):
            r = self.call(srv, name, args)
            self.assertFalse(r["isError"], r)
            self.assertIn("structuredContent", r, name)
            self.assertIsInstance(r["structuredContent"], dict, name)
            self.check_schema(r["structuredContent"], schemas[name], name)
            self.assertTrue(r["content"][0]["text"], name)       # people still get the text
        self.assertEqual(len(self.call(srv, "list_runs")["structuredContent"]["runs"]), 2)
        # ask and run: the answers and the plan as data, a dry run included
        del os.environ["PERPLEXITY_API_KEY"]
        for name, args in (("ask", {"question": "best free ai video generator"}), ("run", {"dry_run": True}),
                           ("run", {"limit": 1})):
            r = self.call(srv, name, args)
            self.assertFalse(r["isError"], r)
            self.check_schema(r["structuredContent"], schemas[name], name)
            self.assertTrue(r["content"][0]["text"], name)
        a = self.call(srv, "ask", {"question": "q"})["structuredContent"]
        chat, pplx = a["engines"]
        self.assertEqual((chat["engine"], chat["status"], chat["cited"], chat["rank"]), ("chatgpt-api", "ok", True, 1))
        self.assertIn("https://pixa.example/pricing", chat["cited_urls"])
        self.assertEqual(chat["searches"], ["best free ai video generator"])
        self.assertEqual((pplx["status"], pplx["cited"]), ("no_key", None))       # not measured, never a zero
        dry = self.call(srv, "run", {"dry_run": True, "max_calls": 999})["structuredContent"]
        self.assertEqual((dry["dry_run"], dry["run_id"], dry["summary"]), (True, None, None))
        self.assertEqual(dry["plan"]["engines_active"], ["chatgpt-api"])
        self.assertEqual((dry["plan"]["planned_calls"], dry["plan"]["max_calls"]), (2, 10))
        self.assertEqual(dry["plan"]["not_measured"], [{"engine": "perplexity-api", "reason": "no_key"}])
        gw.NOW = lambda: FIXED_NOW + datetime.timedelta(days=14)
        real = self.call(srv, "run", {"limit": 1})["structuredContent"]
        self.assertEqual((real["dry_run"], real["run_id"]), (False, "20261010T083000Z"))
        self.assertEqual(real["summary"]["overall"]["answered"], 1)

    def test_rubric_resource_and_site_text_notice(self):
        srv = self.server()
        init = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
        self.assertIn("resources", init["result"]["capabilities"])
        self.assertIn("«site text: …»", init["result"]["instructions"])
        score = next(t for t in srv.tools() if t["name"] == "score_site")
        self.assertIn("«site text: …»", score["description"])
        res = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "resources/list"})["result"]["resources"]
        self.assertEqual([r["uri"] for r in res], ["geo-score://rubric/v1.1"])
        body = srv.handle({"jsonrpc": "2.0", "id": 3, "method": "resources/read",
                           "params": {"uri": "geo-score://rubric/v1.1"}})["result"]["contents"][0]
        served = json.loads(body["text"])
        with io.open(os.path.join(HERE, "..", "rubric", "v1.1.json"), encoding="utf-8") as f:
            published = json.load(f)
        self.assertEqual([(c["id"], c["points"]) for c in served["checks"]],
                         [(c["id"], c["points"]) for c in published["checks"]])
        self.assertEqual((served["gate_cap"], served["bonus_cap"]), (published["gate_cap"], published["bonus_cap"]))
        err = srv.handle({"jsonrpc": "2.0", "id": 4, "method": "resources/read", "params": {"uri": "file:///etc/passwd"}})
        self.assertEqual(err["error"]["code"], -32002)
        # pinned to the release it came from, as every check's doc_url is
        self.assertEqual(served["source"], "https://github.com/jianruntech/geo-score/blob/v%s/rubric/v1.1.json"
                         % gw.__version__)

    def test_score_site_arguments_are_checked(self):
        srv = self.server()
        self.assertIn("urls", next(t for t in srv.tools() if t["name"] == "score_site")["inputSchema"]["properties"])
        for args in ({"url": "stripe.com", "sample": 0}, {"url": "stripe.com", "sample": 9},
                     {"url": "stripe.com", "sample": True}, {"url": "stripe.com", "urls": "https://stripe.com/a"},
                     {"url": "stripe.com", "urls": ["https://evil.example/a"]}):
            self.assertTrue(self.call(srv, "score_site", args)["isError"], args)

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
            f.write("print('stdout noise at import')\nADDRESS_GUARD = False\n"
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
        # a scorer that predates the address guard is not offered: it would let an agent reach private hosts
        with io.open(fake, "w", encoding="utf-8") as f:
            f.write("def run(url, sample=8):\n    return {}\ndef as_json(res):\n    return {}\n")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertNotIn("score_site", [t["name"] for t in self.server().tools()])

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
        # tools/call answers from a worker thread, so it may come after later lines; it still comes before exit
        by_id = dict((l.get("id"), l) for l in lines)
        self.assertEqual(len(lines), 4)
        self.assertEqual([l.get("id") for l in lines if l.get("id") != 3], [1, 2, None])
        self.assertEqual(by_id[1]["result"]["serverInfo"]["name"], "geo-score")
        self.assertIn("score_site", [t["name"] for t in by_id[2]["result"]["tools"]])
        self.assertTrue(by_id[3]["result"]["isError"])                              # no keys in this environment
        self.assertEqual(by_id[None]["error"]["code"], -32700)
        self.assertEqual(p.returncode, 0)


MCP_FIXTURES = os.path.join(HERE, "fixtures", "mcp")


class MCPSurface(Base):
    """What a client sees before it calls anything: the tool list is a contract (STABILITY.md) and a snapshot."""
    def server(self):
        return gw.MCPServer(os.path.join(self.tmp, "none.json"), out=io.StringIO())

    def listing(self, srv):
        return srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]

    def test_tools_list_matches_the_snapshot(self):
        # UPDATE_SNAPSHOTS=1 python3 cli/test_geo_watch.py rewrites it; say why in the commit
        got = json.dumps(self.listing(self.server()), ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        path = os.path.join(MCP_FIXTURES, "tools.snapshot.json")
        if os.environ.get("UPDATE_SNAPSHOTS") == "1":
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(got)
        with io.open(path, encoding="utf-8") as f:
            self.assertEqual(got, f.read(), "tools/list changed: check it, then UPDATE_SNAPSHOTS=1")

    def test_no_released_tool_or_argument_disappears_and_none_becomes_required(self):
        with io.open(os.path.join(MCP_FIXTURES, "contract-1.3.0.json"), encoding="utf-8") as f:
            base = json.load(f)["tools"]
        now = dict((t["name"], t["inputSchema"]) for t in self.listing(self.server())["tools"])
        for name, was in sorted(base.items()):
            self.assertIn(name, now, "tool %s was removed or renamed" % name)
            args = now[name].get("properties", {})
            for a in was["arguments"]:
                self.assertIn(a, args, "%s.%s was removed or renamed" % (name, a))
            self.assertEqual(sorted(set(now[name].get("required", [])) - set(was["required"])), [],
                             "%s gained a required argument" % name)

    def test_every_tool_has_a_title_and_all_four_hints(self):
        tools = self.listing(self.server())["tools"]
        for t in tools:
            self.assertTrue(t.get("title"), t["name"])
            ann = t["annotations"]
            self.assertEqual(ann["title"], t["title"], t["name"])
            for h in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"):
                self.assertIsInstance(ann.get(h), bool, "%s.%s" % (t["name"], h))
            self.assertFalse(ann["destructiveHint"], t["name"])
        hints = dict((t["name"], tuple(t["annotations"][h] for h in ("readOnlyHint", "idempotentHint", "openWorldHint")))
                     for t in tools)
        self.assertEqual(hints["score_site"], (True, False, True))      # the live site can change between calls
        for name in ("ask", "run"):
            self.assertEqual(hints[name], (False, False, True), name)     # paid: never marked read-only
        for name in ("list_runs", "report", "diff", "status"):
            self.assertEqual(hints[name], (True, True, False), name)

    def test_schemas_are_portable_and_closed(self):
        for t in self.listing(self.server())["tools"]:
            self.assertEqual(t["inputSchema"]["type"], "object", t["name"])
            self.assertIs(t["inputSchema"].get("additionalProperties"), False, t["name"])
            if "outputSchema" in t:
                self.assertEqual(t["outputSchema"]["type"], "object", t["name"])      # legacy clients need an object root
            for sch in (t["inputSchema"], t.get("outputSchema") or {}):
                for node in schema_nodes(sch):
                    self.assertNotIsInstance(node.get("type"), list, "%s: a type list; use anyOf" % t["name"])
        # the schema is closed, the server stays lenient: an extra key is ignored, not an error
        srv = gw.MCPServer(os.path.join(self.tmp, "none.json"), out=io.StringIO())
        r = srv.call({"name": "ask", "arguments": {"question": "", "unexpected": 1}})
        self.assertIn("question must be", r["content"][0]["text"])

    def test_descriptions_open_with_the_cost(self):
        d = dict((t["name"], t["description"]) for t in self.listing(self.server())["tools"])
        self.assertTrue(d["score_site"].startswith("Free, no API key."))
        self.assertTrue(d["ask"].startswith("Paid: one API call per configured engine, billed to your keys."))
        self.assertTrue(d["run"].startswith("Paid: up to max_calls calls; call with dry_run:true first."))
        for name in ("list_runs", "report", "diff", "status"):
            self.assertTrue(d[name].startswith("Free, local:"), name)

    def test_the_first_512_characters_of_the_instructions_stand_alone(self):
        init = self.server().handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                     "params": {"protocolVersion": "2025-06-18"}})["result"]
        text = init["instructions"]
        head = text[:512]
        self.assertIn("«site text", head)                    # Codex keeps only this much
        self.assertIn("dry_run", head)
        end = text.index("not a trend.") + len("not a trend.")
        self.assertLessEqual(end, 512)                       # the self-contained part ends before the cut
        info = init["serverInfo"]
        self.assertEqual((info["name"], info["version"]), ("geo-score", gw.__version__))
        self.assertEqual(info["websiteUrl"], "https://github.com/jianruntech/geo-score")
        self.assertLessEqual(len(info["description"]), 100)
        self.assertNotIn("icons", info)


class Feed(object):
    """stdin for a server under test: lines go in when the test says, and close() is the end of file."""
    def __init__(self):
        self.q = queue.Queue()

    def send(self, obj):
        self.q.put(json.dumps(obj) + "\n")

    def close(self):
        self.q.put(None)

    def __iter__(self):
        while True:
            line = self.q.get()
            if line is None:
                return
            yield line


class Lines(object):
    """stdout for a server under test: every line must be JSON, and a test can wait for the one it expects."""
    def __init__(self):
        self.cond, self.buf = threading.Condition(), ""

    def write(self, s):
        with self.cond:
            self.buf += s
            self.cond.notify_all()

    def flush(self):
        pass

    def lines(self):
        with self.cond:
            return [json.loads(l) for l in self.buf.splitlines()]

    def wait_until(self, done, timeout=10):
        deadline = time.time() + timeout
        with self.cond:
            while True:
                got = [json.loads(l) for l in self.buf.splitlines()]
                if done(got):
                    return got
                if time.time() >= deadline:
                    raise AssertionError("timed out waiting; stdout so far: %r" % got)
                self.cond.wait(0.1)

    def wait_for(self, pred, timeout=10):
        return self.wait_until(lambda got: any(pred(l) for l in got), timeout)


class MCPConcurrency(Base):
    """tools/call runs on worker threads: the loop keeps answering, and notifications/cancelled stops the spend."""
    server = MCP.server

    def start(self, gate):
        routes = self.standard_routes()
        slow = routes["api.openai.com"]
        routes["api.openai.com"] = lambda u, h, b: (gate.wait(10), slow(u, h, b))[1]
        api = self.fake(routes)
        srv = self.server()
        srv.out = out = Lines()
        feed, ret = Feed(), []
        t = threading.Thread(target=lambda: ret.append(srv.serve(feed)), daemon=True)
        t.start()
        return srv, feed, out, t, ret, api

    def settle(self, srv):
        deadline = time.time() + 10
        while srv.inflight and time.time() < deadline:
            time.sleep(0.02)
        self.assertEqual(srv.inflight, {})

    def runs_saved(self):
        d = os.path.join(self.tmp, ".geo-score", "watch", "runs")
        return os.listdir(d) if os.path.isdir(d) else []

    def test_ping_is_answered_during_a_run_and_a_cancelled_run_falls_silent(self):
        gate, err = threading.Event(), io.StringIO()
        with contextlib.redirect_stderr(err):
            srv, feed, out, t, ret, _ = self.start(gate)
            feed.send({"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                       "params": {"name": "run", "arguments": {}, "_meta": {"progressToken": "p7"}}})
            out.wait_for(lambda l: l.get("method") == "notifications/progress")   # perplexity answered at once
            feed.send({"jsonrpc": "2.0", "id": 8, "method": "ping"})
            out.wait_for(lambda l: l.get("id") == 8)                             # while chatgpt is still asking
            self.assertFalse(any(l.get("id") == 7 for l in out.lines()))
            feed.send({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 7, "reason": "user"}})
            feed.send({"jsonrpc": "2.0", "id": 9, "method": "ping"})
            n = len(out.wait_for(lambda l: l.get("id") == 9))                      # the cancel has been read
            gate.set()
            self.settle(srv)
            feed.close()
            t.join(5)
        self.assertEqual(ret, [0])
        after = out.lines()[n:]
        self.assertEqual(after, [])                                  # no progress and no answer after the cancel
        self.assertFalse(any(l.get("id") == 7 for l in out.lines()))
        self.assertEqual(self.runs_saved(), [])                      # a cancelled run is not saved
        self.assertIn("geo-score mcp: run stopped before it finished", err.getvalue())
        self.assertIn("not saved", err.getvalue())

    def test_cancelling_an_unknown_or_finished_request_is_ignored(self):
        srv = self.server()
        self.assertIsNone(srv.handle({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 99}}))
        self.assertIsNone(srv.handle({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {}}))
        self.assertEqual(srv.inflight, {})

    def test_end_of_file_stops_the_calls_in_flight_and_returns_promptly(self):
        gate = threading.Event()
        with contextlib.redirect_stderr(io.StringIO()):
            srv, feed, out, t, ret, api = self.start(gate)
            feed.send({"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                       "params": {"name": "run", "arguments": {}, "_meta": {"progressToken": 1}}})
            out.wait_for(lambda l: l.get("method") == "notifications/progress")
            t0 = time.time()
            feed.close()
            t.join(5)
            self.assertLess(time.time() - t0, gw.EOF_GRACE + 1)
            self.assertEqual(ret, [0])
            asked = len(api.calls)
            gate.set()                                               # the one call already on the wire comes back
            self.settle(srv)
        self.assertEqual(len(api.calls), asked)                      # and nothing new was asked after the end of file
        self.assertEqual(self.runs_saved(), [])

    def test_at_most_four_calls_run_at_once_and_the_loop_stays_responsive(self):
        gate = threading.Event()
        srv, feed, out, t, ret, api = self.start(gate)
        for i in range(5):
            feed.send({"jsonrpc": "2.0", "id": "a%d" % i, "method": "tools/call",
                       "params": {"name": "ask", "arguments": {"question": "q%d" % i, "engines": ["chatgpt-api"]}}})
        deadline = time.time() + 10
        while len(api.calls) < gw.MCP_WORKERS and time.time() < deadline:
            time.sleep(0.02)
        feed.send({"jsonrpc": "2.0", "id": "p", "method": "ping"})
        out.wait_for(lambda l: l.get("id") == "p")
        time.sleep(0.3)
        self.assertEqual(len(api.calls), gw.MCP_WORKERS)             # the fifth waits for a free worker
        gate.set()
        answers = lambda got: [l for l in got if str(l.get("id")).startswith("a")]
        got = answers(out.wait_until(lambda got: len(answers(got)) == 5))
        self.assertEqual(sorted(l["id"] for l in got), ["a%d" % i for i in range(5)])
        self.assertTrue(all(not l["result"]["isError"] for l in got), got)
        feed.close()
        t.join(5)
        self.assertEqual(ret, [0])


class MCPToolsets(Base):
    """--toolsets, --tools, --exclude-tools and --read-only, their environment twins, and the status tool."""
    server = MCP.server

    def test_the_filter(self):
        f = gw.tool_filter
        self.assertEqual(f(), set(gw.MCP_TOOLS))
        self.assertEqual(f("all"), set(gw.MCP_TOOLS))
        self.assertEqual(f("score"), {"score_site", "status"})
        self.assertEqual(f("score,ask"), {"score_site", "ask", "status"})
        self.assertEqual(f(["watch"], ["ask"]), {"run", "list_runs", "report", "diff", "ask", "status"})
        self.assertEqual(f(None, "score_site"), {"score_site", "status"})            # --tools alone: only those
        self.assertEqual(f(read_only=True), set(gw.MCP_TOOLS) - {"ask", "run"})
        self.assertEqual(f("ask,watch", read_only=True), {"list_runs", "report", "diff", "status"})
        self.assertEqual(f(None, "ask,run", "run"), {"ask", "status"})              # exclusion always wins
        self.assertEqual(f(exclude="status"), set(gw.MCP_TOOLS) - {"status"})
        for bad, word in (({"toolsets": "nope"}, "toolset"), ({"tools": "score"}, "tool"),
                          ({"exclude": "scor_site"}, "tool")):
            with self.assertRaises(ValueError) as cm:
                f(**bad)
            self.assertIn("unknown %s" % word, str(cm.exception))
            self.assertIn("known: ", str(cm.exception))

    def test_capabilities_resources_and_calls_follow_the_filter(self):
        cfgp = os.path.join(self.tmp, "none.json")
        srv = gw.MCPServer(cfgp, out=io.StringIO(), enabled=gw.tool_filter("ask"))
        self.assertEqual([t["name"] for t in srv.tools()], ["ask", "status"])
        init = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}})
        self.assertNotIn("resources", init["result"]["capabilities"])                 # the rubric is in the score set
        self.assertEqual(srv.handle({"jsonrpc": "2.0", "id": 2, "method": "resources/list"})["result"]["resources"], [])
        r = srv.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "score_site",
                                                                                      "arguments": {"url": "a.example"}}})
        self.assertEqual(r["error"]["code"], -32602)                                  # not offered, so unknown
        ro = gw.MCPServer(cfgp, out=io.StringIO(), enabled=gw.tool_filter(read_only=True))
        self.assertEqual([t["name"] for t in ro.tools()], ["score_site", "list_runs", "report", "diff", "status"])
        self.assertTrue(all(t["annotations"]["readOnlyHint"] for t in ro.tools()))

    def test_status_says_what_can_run_and_never_shows_a_key(self):
        os.environ["OPENAI_API_KEY"] = "sk-test-SECRET"
        os.environ["PERPLEXITY_API_KEY"] = "pplx-test-SECRET with a space"            # malformed: named, never echoed
        for with_config in (False, True):
            srv = self.server(with_config)
            r = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "status"}})
            wire = json.dumps(r)
            self.assertNotIn("SECRET", wire)
            res = r["result"]
            self.assertFalse(res["isError"], res)
            st = res["structuredContent"]
            self.assertEqual(schema_errors(st, gw.OUT_STATUS), [])
            self.assertEqual(st["version"], gw.__version__)
            self.assertEqual(st["tools"], list(gw.MCP_TOOLS))
            self.assertEqual(st["toolsets"], ["ask", "score", "status", "watch"])
            self.assertEqual(st["config"]["found"], with_config)
            keys = dict((e["id"], e["key_present"]) for e in st["engines"])
            self.assertTrue(keys["chatgpt-api"])
            self.assertFalse(keys["perplexity-api"])
            self.assertTrue(st["ready"]["ask"])
            self.assertTrue(st["ready"]["score_site"])
        self.assertEqual((st["questions"], st["runs"], st["caps"]), (2, 0, {"max_calls": 10, "budget_usd": None}))
        self.assertEqual((st["ready"]["run"], st["ready"]["report"], st["ready"]["diff"]), (True, False, False))
        self.assertIn("OPENAI_API_KEY", [e["key_env"] for e in st["engines"]])
        broken = self.server(with_config=False)
        with io.open(broken.config_path, "w", encoding="utf-8") as f:
            f.write("{not json")
        st = broken.call({"name": "status"})["structuredContent"]
        self.assertTrue(st["config"]["found"])
        self.assertIn("not valid JSON", st["config"]["errors"][0])
        self.assertEqual((st["ready"]["ask"], st["ready"]["run"], st["ready"]["list_runs"]), (False, False, False))

    def mcp(self, *args, env=None, entry=None, lines=()):
        e = dict(os.environ)
        for k in ALL_KEY_ENVS + ["GEO_SCORE_MCP_TOOLSETS", "GEO_SCORE_MCP_TOOLS", "GEO_SCORE_MCP_EXCLUDE_TOOLS",
                                 "GEO_SCORE_MCP_READ_ONLY"]:
            e.pop(k, None)
        e.update(env or {})
        cmd = [sys.executable, os.path.join(HERE, "geo_score.py"), "mcp"] if entry is None else entry
        return subprocess.run(cmd + ["-c", os.path.join(self.tmp, "none.json")] + list(args), capture_output=True,
                              env=e, timeout=60, input="".join(json.dumps(m) + "\n" for m in lines).encode())

    def listed(self, p):
        self.assertEqual(p.returncode, 0, p.stderr)
        return [t["name"] for t in json.loads(p.stdout.decode().splitlines()[0])["result"]["tools"]]

    def test_flags_and_environment_on_both_entry_points(self):
        ls = [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}]
        free = ["score_site", "list_runs", "report", "diff", "status"]
        self.assertEqual(self.listed(self.mcp("--read-only", lines=ls)), free)
        self.assertEqual(self.listed(self.mcp(lines=ls, env={"GEO_SCORE_MCP_READ_ONLY": "1"})), free)
        self.assertEqual(self.listed(self.mcp("--toolsets", "score", lines=ls)), ["score_site", "status"])
        self.assertEqual(self.listed(self.mcp(lines=ls, env={"GEO_SCORE_MCP_TOOLSETS": "watch",
                                                             "GEO_SCORE_MCP_EXCLUDE_TOOLS": "diff,status"})),
                         ["run", "list_runs", "report"])
        self.assertEqual(self.listed(self.mcp("--tools", "ask", "--tools", "diff", lines=ls,
                                              env={"GEO_SCORE_MCP_TOOLS": "run"})),        # a flag beats its twin
                         ["ask", "diff", "status"])
        # the console script geo-score-mcp goes through geo_score.mcp_main with the same flags
        entry = [sys.executable, "-c", "import sys; sys.path.insert(0, %r); import geo_score; "
                                       "sys.argv[0] = 'geo-score-mcp'; geo_score.mcp_main()" % HERE]
        self.assertEqual(self.listed(self.mcp("--read-only", "--exclude-tools", "status", entry=entry, lines=ls)),
                         ["score_site", "list_runs", "report", "diff"])
        for args, env, word in ((["--toolsets", "nope"], {}, "unknown toolset 'nope' (known: all, ask, score, status, watch)"),
                                (["--tools", "score"], {}, "unknown tool 'score' (known: score_site, ask, run,"),
                                ([], {"GEO_SCORE_MCP_EXCLUDE_TOOLS": "asks"}, "unknown tool 'asks'"),
                                ([], {"GEO_SCORE_MCP_READ_ONLY": "maybe"}, "GEO_SCORE_MCP_READ_ONLY must be 1 or 0")):
            for e in (None, entry):
                p = self.mcp(*args, env=env, entry=e)
                self.assertEqual(p.returncode, 2, (args, env, p.stderr))
                self.assertIn(word, p.stderr.decode())
                self.assertEqual(p.stdout, b"")


class MCPRobustness(Base):
    """What the 1.4.0 pre-release review found: nothing a file or a request carries ends the server, a pasted key
    is never shown, a non-UTF-8 stream loses no answer, and one approval cannot start two paid runs."""
    server = MCP.server
    call = MCP.call
    start = MCPConcurrency.start
    settle = MCPConcurrency.settle
    runs_saved = MCPConcurrency.runs_saved
    mcp = MCPToolsets.mcp
    listed = MCPToolsets.listed

    def write_config(self, **extra):
        cfg = {"brand": {"name": "Lumo", "domains": ["lumo.example"]}, "engines": engines("chatgpt-api", "perplexity-api"),
               "max_calls": 10}
        cfg.update(extra)
        with io.open(os.path.join(self.tmp, "geo-score-watch.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f)
        with io.open(os.path.join(self.tmp, "queries.csv"), "w", encoding="utf-8") as f:
            f.write("query_id,query\nq01,best free ai video generator\nq02,lumo pricing\n")
        self.out = io.StringIO()
        return gw.MCPServer(os.path.join(self.tmp, "geo-score-watch.json"), out=self.out)

    def serve_lines(self, srv, msgs):
        srv.out = out = Lines()
        feed, ret = Feed(), []
        t = threading.Thread(target=lambda: ret.append(srv.serve(feed)), daemon=True)
        t.start()
        for m in msgs:
            feed.send(m)
        out.wait_for(lambda l: l.get("id") == "last")
        feed.close()
        t.join(10)
        self.assertEqual(ret, [0])
        return dict((l.get("id"), l) for l in out.lines())

    def test_a_malformed_run_file_or_config_is_an_error_answer_not_the_end(self):
        srv = self.server()
        d = os.path.join(self.tmp, ".geo-score", "watch", "runs")
        os.makedirs(d)
        with io.open(os.path.join(d, "20260926T083000Z.json"), "w", encoding="utf-8") as f:
            json.dump({"format": "geo-score/watch.v1"}, f)
        got = self.serve_lines(srv, [
            {"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "geo-score://runs/20260926T083000Z"}},
            {"jsonrpc": "2.0", "id": "last", "method": "ping"}])
        self.assertEqual(got[1]["error"]["code"], -32603)
        self.assertIn("result", got["last"])
        self.assertEqual(self.call(srv, "list_runs")["structuredContent"]["runs"][0]["readable"], False)
        srv = self.write_config(competitors=5)
        got = self.serve_lines(srv, [
            {"jsonrpc": "2.0", "id": 1, "method": "completion/complete",
             "params": {"ref": {"type": "ref/prompt", "name": "compare_runs"}, "argument": {"name": "from", "value": ""}}},
            {"jsonrpc": "2.0", "id": "last", "method": "ping"}])
        self.assertIn("result", got[1])
        self.assertIn("result", got["last"])

    def test_status_never_shows_a_key_pasted_into_key_env_and_survives_a_broken_one(self):
        for bad in ("sk-proj-SECRETabc123", 5):
            eng = engines("chatgpt-api")
            eng[0]["key_env"] = bad
            srv = self.write_config(engines=eng)
            r = self.call(srv, "status")
            self.assertFalse(r["isError"], r)
            blob = r["content"][0]["text"] + json.dumps(r["structuredContent"])
            self.assertNotIn("SECRET", blob)
            self.assertIn("key_env is invalid", blob)

    def test_status_says_run_is_ready_only_when_it_could_start(self):
        # a budget, and an engine that neither reports its cost nor has prices: nothing can run
        srv = self.write_config(budget_usd=5, engines=engines("chatgpt-api"))
        self.assertFalse(self.call(srv, "status")["structuredContent"]["ready"]["run"])
        srv = self.write_config(max_calls=3)                      # 2 questions x 2 engines = 4 > 3
        self.assertFalse(self.call(srv, "status")["structuredContent"]["ready"]["run"])
        srv = self.write_config()
        self.assertTrue(self.call(srv, "status")["structuredContent"]["ready"]["run"])

    def test_a_stream_that_cannot_carry_the_text_still_gets_every_answer(self):
        srv = self.server()
        buf = io.BytesIO()
        srv.out = io.TextIOWrapper(buf, encoding="ascii", newline="\n")
        srv.send(srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}))
        srv.send({"jsonrpc": "2.0", "id": 2, "result": {"text": "\ud800 lone surrogate"}})
        srv.out.flush()
        lines = [json.loads(x) for x in buf.getvalue().decode("ascii").splitlines()]
        self.assertEqual([l["id"] for l in lines], [1, 2])
        self.assertIn("«site text", json.dumps(lines[0], ensure_ascii=False))

    def test_arguments_that_are_not_an_object_start_nothing(self):
        api = self.fake(self.standard_routes())
        srv = self.server()
        r = srv.handle({"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                        "params": {"name": "run", "arguments": json.dumps({"dry_run": True})}})["result"]
        self.assertTrue(r["isError"])
        self.assertIn("arguments must be an object", r["content"][0]["text"])
        self.assertEqual((len(api.calls), self.runs_saved()), (0, []))

    def test_a_second_run_during_a_run_is_refused(self):
        gate = threading.Event()
        with contextlib.redirect_stderr(io.StringIO()):
            srv, feed, out, t, ret, api = self.start(gate)
            feed.send({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "run", "arguments": {}}})
            deadline = time.time() + 10
            while not api.calls and time.time() < deadline:
                time.sleep(0.02)
            feed.send({"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "run", "arguments": {}}})
            second = [l for l in out.wait_for(lambda l: l.get("id") == 8) if l.get("id") == 8][0]
            self.assertTrue(second["result"]["isError"])
            self.assertIn("already in progress", second["result"]["content"][0]["text"])
            gate.set()
            out.wait_for(lambda l: l.get("id") == 7)
            feed.close()
            t.join(5)
        self.assertEqual(len(self.runs_saved()), 1)
        self.assertEqual(len(api.calls), 4)                       # one run's worth: 2 questions x 2 engines

    def test_end_of_file_lets_a_free_call_answer(self):
        srv = self.server()
        srv.out = out = Lines()
        feed, ret = Feed(), []
        t = threading.Thread(target=lambda: ret.append(srv.serve(feed)), daemon=True)
        t.start()
        feed.send({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "status", "arguments": {}}})
        feed.close()
        t.join(10)
        self.assertEqual(ret, [0])
        got = [l for l in out.lines() if l.get("id") == 5]
        self.assertEqual(len(got), 1)
        self.assertFalse(got[0]["result"]["isError"], got)          # answered for real, not "cancelled"

    def test_exclusions_from_the_environment_and_the_command_line_add_up(self):
        ls = [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}]
        self.assertEqual(self.listed(self.mcp("--exclude-tools", "diff", lines=ls,
                                              env={"GEO_SCORE_MCP_EXCLUDE_TOOLS": "ask,run"})),
                         ["score_site", "list_runs", "report", "status"])


MODERN = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
          "io.modelcontextprotocol/clientInfo": {"name": "t", "version": "0"},
          "io.modelcontextprotocol/clientCapabilities": {}}


class MCPProtocol(Base):
    """Dual era: initialize for legacy clients (2024-11-05 to 2025-11-25), per-request _meta for 2026-07-28."""
    server = MCP.server

    def rpc(self, srv, method, params=None, meta=None, mid=1):
        p = dict(params or {})
        if meta is not None:
            p["_meta"] = meta
        return srv.handle({"jsonrpc": "2.0", "id": mid, "method": method, "params": p})

    def test_initialize_answers_every_legacy_version_and_falls_back_to_the_newest(self):
        srv = self.server()
        for v in gw.LEGACY_VERSIONS:
            r = self.rpc(srv, "initialize", {"protocolVersion": v, "capabilities": {}})["result"]
            self.assertEqual(r["protocolVersion"], v)
            self.assertEqual(srv.session_version, v)
        # initialize is legacy: a modern or unknown version gets the newest legacy one, which the client may refuse
        for v in ("2026-07-28", "1999-01-01", None):
            r = self.rpc(srv, "initialize", {"protocolVersion": v})["result"]
            self.assertEqual(r["protocolVersion"], "2025-11-25", v)
        self.assertEqual(gw.MCP_VERSIONS, gw.LEGACY_VERSIONS)
        self.assertEqual(gw.SUPPORTED_VERSIONS, ("2026-07-28",) + gw.LEGACY_VERSIONS)

    def test_server_discover(self):
        r = self.rpc(self.server(), "server/discover", meta=MODERN)["result"]
        self.assertEqual(r["resultType"], "complete")
        self.assertEqual(r["supportedVersions"], list(gw.SUPPORTED_VERSIONS))
        self.assertIn("tools", r["capabilities"])
        self.assertIn("«site text", r["instructions"])
        info = r["_meta"]["io.modelcontextprotocol/serverInfo"]
        self.assertEqual((info["name"], info["version"]), ("geo-score", gw.__version__))
        self.assertEqual((r["ttlMs"], r["cacheScope"]), (3600000, "public"))

    def test_an_unsupported_version_names_the_supported_ones(self):
        srv = self.server()
        for v in ("1999-01-01", "2025-11-25"):          # a legacy version is served through initialize, not _meta
            e = self.rpc(srv, "tools/list", meta=dict(MODERN, **{"io.modelcontextprotocol/protocolVersion": v}))["error"]
            self.assertEqual(e["code"], -32022)
            self.assertEqual(e["message"], "Unsupported protocol version")
            self.assertEqual(e["data"], {"supported": list(gw.SUPPORTED_VERSIONS), "requested": v})
        e = self.rpc(srv, "server/discover", meta={"io.modelcontextprotocol/protocolVersion": "1999-01-01",
                                                   "io.modelcontextprotocol/clientCapabilities": {}})["error"]
        self.assertEqual(e["code"], -32022)

    def test_required_meta_fields_are_checked(self):
        srv = self.server()
        for meta in ({"io.modelcontextprotocol/protocolVersion": "2026-07-28"},
                     dict(MODERN, **{"io.modelcontextprotocol/clientCapabilities": "all"}),
                     dict(MODERN, **{"io.modelcontextprotocol/protocolVersion": 20260728}),
                     dict(MODERN, **{"io.modelcontextprotocol/logLevel": "loud"})):
            self.assertEqual(self.rpc(srv, "tools/list", meta=meta)["error"]["code"], -32602, meta)
        self.assertEqual(self.rpc(srv, "server/discover")["error"]["code"], -32602)       # no _meta at all
        ok = self.rpc(srv, "tools/list", meta=dict(MODERN, **{"io.modelcontextprotocol/logLevel": "warning"}))
        self.assertIn("result", ok)

    def test_modern_results_carry_result_type_and_cache_hints_and_legacy_ones_do_not(self):
        srv = self.server()
        hints = {"tools/list": (3600000, "public"), "resources/list": (86400000, "public"),
                 "resources/templates/list": (86400000, "public")}
        for method, (ttl, scope) in sorted(hints.items()):
            modern = self.rpc(srv, method, meta=MODERN)["result"]
            self.assertEqual((modern["resultType"], modern["ttlMs"], modern["cacheScope"]), ("complete", ttl, scope))
            self.assertIn("io.modelcontextprotocol/serverInfo", modern["_meta"])
            legacy = self.rpc(srv, method)["result"]
            for k in ("resultType", "ttlMs", "cacheScope", "_meta"):
                self.assertNotIn(k, legacy, method)
            self.assertEqual(dict((k, v) for k, v in modern.items() if k not in ("resultType", "ttlMs", "cacheScope", "_meta")),
                             legacy, method)                     # the same answer, only the envelope differs
        read = self.rpc(srv, "resources/read", {"uri": "geo-score://rubric/v1.1"}, meta=MODERN)["result"]
        self.assertEqual((read["ttlMs"], read["cacheScope"]), (86400000, "public"))
        self.assertNotIn("ttlMs", self.rpc(srv, "resources/read", {"uri": "geo-score://rubric/v1.1"})["result"])
        call = self.rpc(srv, "tools/call", {"name": "ask", "arguments": {"question": ""}}, meta=MODERN)["result"]
        self.assertEqual(call["resultType"], "complete")
        self.assertTrue(call["isError"])
        self.assertNotIn("ttlMs", call)                          # only lists, discovery and reads are cacheable

    def test_resource_not_found_is_32002_for_legacy_and_32602_for_modern(self):
        srv = self.server()
        legacy = self.rpc(srv, "resources/read", {"uri": "file:///etc/passwd"})["error"]
        self.assertEqual((legacy["code"], legacy["data"]["uri"]), (-32002, "file:///etc/passwd"))
        modern = self.rpc(srv, "resources/read", {"uri": "file:///etc/passwd"}, meta=MODERN)["error"]
        self.assertEqual((modern["code"], modern["data"]["uri"]), (-32602, "file:///etc/passwd"))

    def test_legacy_only_methods_are_not_found_on_the_modern_path(self):
        srv = self.server()
        for method in ("initialize", "ping", "logging/setLevel", "resources/subscribe"):
            self.assertEqual(self.rpc(srv, method, meta=MODERN)["error"]["code"], -32601, method)
        self.assertEqual(self.rpc(srv, "ping")["result"], {})    # still there for legacy clients
        self.assertIsNone(srv.session_version)                   # and a modern request never set any state

    def test_a_cursor_is_refused_because_none_is_ever_issued(self):
        srv = self.server()
        for method in ("tools/list", "resources/list", "resources/templates/list"):
            self.assertEqual(self.rpc(srv, method, {"cursor": "garbage"})["error"]["code"], -32602, method)
            self.assertEqual(self.rpc(srv, method, {"cursor": "garbage"}, meta=MODERN)["error"]["code"], -32602, method)

    def serve(self, *msgs):
        srv, out = self.server(), io.StringIO()
        srv.out = out
        srv.serve(io.StringIO("".join(json.dumps(m) + "\n" for m in msgs)))
        return [json.loads(l) for l in out.getvalue().splitlines()]

    def test_batches_only_in_2025_03_26(self):
        batch = [{"jsonrpc": "2.0", "id": 2, "method": "ping"}, {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}]
        refused = {"jsonrpc": "2.0", "id": None,
                   "error": {"code": -32600, "message": "batches are not supported in this protocol version"}}
        self.assertEqual(self.serve(batch), [refused])                                   # no initialize at all
        init = lambda v: {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": v}}
        for v in ("2025-11-25", "2025-06-18", "2024-11-05"):
            self.assertEqual(self.serve(init(v), batch)[1], refused, v)
        out = self.serve(init("2025-03-26"), batch)
        self.assertEqual([r["id"] for r in out[1]], [2, 3])
        self.assertEqual(self.serve(init("2025-03-26"), [])[1]["error"]["code"], -32600)

    def test_stdio_serves_a_modern_client_that_never_initializes(self):
        env = dict(os.environ)
        for k in ALL_KEY_ENVS:
            env.pop(k, None)
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": MODERN}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"_meta": MODERN}},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                 "params": {"name": "ask", "arguments": {"question": "q"}, "_meta": MODERN}}]
        p = subprocess.run([sys.executable, os.path.join(HERE, "geo_score.py"), "mcp", "-c",
                            os.path.join(self.tmp, "none.json")], capture_output=True, env=env, timeout=60,
                           input="".join(json.dumps(m) + "\n" for m in msgs).encode())
        self.assertEqual(p.returncode, 0, p.stderr)
        by_id = dict((l["id"], l) for l in (json.loads(x) for x in p.stdout.decode().splitlines()))
        self.assertEqual(sorted(by_id), [1, 2, 3])
        self.assertEqual(by_id[1]["result"]["supportedVersions"][0], "2026-07-28")
        self.assertIn("score_site", [t["name"] for t in by_id[2]["result"]["tools"]])
        self.assertEqual(by_id[3]["result"]["resultType"], "complete")
        self.assertTrue(by_id[3]["result"]["isError"])                               # no keys in this environment


class MCPPrompts(Base):
    """Prompts (the user's slash commands), completions, and the saved-run resource template."""
    server = MCP.server
    PROMPTS = ["audit_site", "check_citations", "weekly_watch", "compare_runs", "explain_check"]

    def rpc(self, srv, method, params=None, meta=None):
        p = dict(params or {})
        if meta is not None:
            p["_meta"] = meta
        return srv.handle({"jsonrpc": "2.0", "id": 1, "method": method, "params": p})

    def get(self, srv, name, args=None):
        return self.rpc(srv, "prompts/get", {"name": name, "arguments": args or {}})

    def with_two_runs(self):
        srv = self.server()
        self.fake(self.standard_routes())
        self.assertFalse(srv.call({"name": "run", "arguments": {}})["isError"])
        gw.NOW = lambda: FIXED_NOW + datetime.timedelta(days=7)
        self.assertFalse(srv.call({"name": "run", "arguments": {}})["isError"])
        return srv

    def test_listed_with_their_capabilities(self):
        srv = self.server()
        caps = self.rpc(srv, "initialize", {"protocolVersion": "2025-11-25"})["result"]["capabilities"]
        self.assertEqual((caps["prompts"], caps["completions"]), ({"listChanged": False}, {}))
        prompts = self.rpc(srv, "prompts/list")["result"]["prompts"]
        self.assertEqual([p["name"] for p in prompts], self.PROMPTS)
        for p in prompts:
            self.assertTrue(p["title"] and p["description"], p)
            self.assertNotIn("needs", p)
            for a in p["arguments"]:
                self.assertIsInstance(a["required"], bool)
        req = dict((p["name"], [a["name"] for a in p["arguments"] if a["required"]]) for p in prompts)
        self.assertEqual(req, {"audit_site": ["url"], "check_citations": ["question"], "weekly_watch": [],
                               "compare_runs": [], "explain_check": ["check_id"]})
        modern = self.rpc(srv, "prompts/list", meta=MODERN)["result"]
        self.assertEqual((modern["resultType"], modern["ttlMs"], modern["cacheScope"]), ("complete", 3600000, "public"))
        self.assertEqual(self.rpc(srv, "prompts/list", {"cursor": "x"})["error"]["code"], -32602)

    def test_prompts_follow_the_tool_filter(self):
        cfgp = os.path.join(self.tmp, "none.json")
        names = lambda srv: [p["name"] for p in srv.prompts()]
        ro = gw.MCPServer(cfgp, out=io.StringIO(), enabled=gw.tool_filter(read_only=True))
        self.assertEqual(names(ro), ["audit_site", "compare_runs", "explain_check"])     # nothing that spends
        self.assertEqual(self.get(ro, "weekly_watch")["error"]["code"], -32602)
        ask = gw.MCPServer(cfgp, out=io.StringIO(), enabled=gw.tool_filter("ask"))
        self.assertEqual(names(ask), ["check_citations"])
        bare = gw.MCPServer(cfgp, out=io.StringIO(), enabled=gw.tool_filter("status"))
        self.assertEqual(names(bare), [])
        caps = self.rpc(bare, "initialize", {"protocolVersion": "2025-11-25"})["result"]["capabilities"]
        self.assertEqual(sorted(caps), ["tools"])                     # no prompts, completions or resources

    def test_prompts_get(self):
        srv = self.server()
        r = self.get(srv, "audit_site", {"url": "example.com"})["result"]
        text = r["messages"][-1]["content"]["text"]
        self.assertEqual(r["messages"][-1]["role"], "user")
        self.assertIn('call score_site with {"url": "example.com"}', text)
        self.assertIn("«site text", text)
        self.assertIn("not whether they do", text)
        t = self.get(srv, "check_citations", {"question": "best free ai video generator", "brand": "Lumo"})["result"]
        t = t["messages"][0]["content"]["text"]
        self.assertIn("paid", t)
        self.assertIn('call ask with {"question": "best free ai video generator", "brand": "Lumo"}', t)
        self.assertIn("domains", t)
        self.assertNotIn("domains", self.get(srv, "check_citations", {"question": "q"})["result"]["messages"][0]
                         ["content"]["text"])
        w = self.get(srv, "weekly_watch")["result"]["messages"][0]["content"]["text"]
        self.assertLess(w.index("status"), w.index('{"dry_run": true}'))
        self.assertLess(w.index('{"dry_run": true}'), w.index("wait for me to confirm"))
        self.assertLess(w.index("wait for me to confirm"), w.index("Call diff"))
        c = self.get(srv, "compare_runs", {"from": "20260926T083000Z"})["result"]["messages"][0]["content"]["text"]
        self.assertIn('call diff with {"from": "20260926T083000Z"}', c)
        self.assertIn("(the previous and the latest run)", self.get(srv, "compare_runs")["result"]["messages"][0]
                      ["content"]["text"])
        e = self.get(srv, "explain_check", {"check_id": "p1.sitemap"})["result"]["messages"]
        self.assertEqual(e[0]["content"]["type"], "resource")
        self.assertEqual(e[0]["content"]["resource"]["uri"], "geo-score://rubric/v1.1")
        self.assertIn("p1.sitemap", [c["id"] for c in json.loads(e[0]["content"]["resource"]["text"])["checks"]])
        self.assertIn("explain check p1.sitemap", e[1]["content"]["text"])
        modern = self.rpc(srv, "prompts/get", {"name": "weekly_watch"}, meta=MODERN)["result"]
        self.assertEqual(modern["resultType"], "complete")
        self.assertNotIn("ttlMs", modern)

    def test_bad_prompt_requests_are_invalid_params(self):
        srv = self.server()
        for name, args in (("nope", {}), (None, {}), ("audit_site", {}), ("audit_site", {"url": "  "}),
                           ("audit_site", {"url": 5}), ("audit_site", {"url": "x" * 3000}),
                           ("check_citations", {"question": "q" * 501}), ("compare_runs", {"from": "../x"}),
                           ("explain_check", {"check_id": "p9.nope"})):
            self.assertEqual(self.get(srv, name, args)["error"]["code"], -32602, (name, args))
        self.assertEqual(self.rpc(srv, "prompts/get", {"name": "audit_site", "arguments": ["x"]})["error"]["code"], -32602)

    def test_no_prompt_writes_a_fix(self):
        # measurement is public, remediation is private (AGENTS.md): prompts measure and explain, never prescribe
        srv = self.server()
        args = {"audit_site": {"url": "example.com"}, "check_citations": {"question": "q", "brand": "b"},
                "explain_check": {"check_id": "p1.sitemap"}}
        for name in self.PROMPTS:
            r = self.get(srv, name, args.get(name))["result"]
            text = " ".join([r["description"]] + [m["content"]["text"] for m in r["messages"]
                                                  if m["content"]["type"] == "text"]).lower()
            for word in ("fix", "remediat", "improve", "```", "markup", "json-ld"):
                self.assertNotIn(word, text, name)

    def test_completions(self):
        srv = self.with_two_runs()
        comp = lambda ref, name, value, meta=None: self.rpc(
            srv, "completion/complete", {"ref": ref, "argument": {"name": name, "value": value}}, meta)
        prompt = lambda n: {"type": "ref/prompt", "name": n}
        ids = [c["id"] for c in gw.rubric_resource(srv.geo_score)["checks"]]
        c = comp(prompt("explain_check"), "check_id", "")["result"]["completion"]
        self.assertEqual((c["values"], c["total"], c["hasMore"]), (ids[:100], len(ids), len(ids) > 100))
        c = comp(prompt("explain_check"), "check_id", "P1.")["result"]["completion"]
        self.assertTrue(c["values"] and all(v.startswith("p1.") for v in c["values"]), c)
        runs = ["20261003T083000Z", "20260926T083000Z"]                                     # newest first
        self.assertEqual(comp(prompt("compare_runs"), "from", "")["result"]["completion"]["values"],
                         runs + ["latest", "previous"])
        self.assertEqual(comp(prompt("compare_runs"), "to", "202609")["result"]["completion"]["values"], runs[1:])
        self.assertEqual(comp({"type": "ref/resource", "uri": "geo-score://runs/{run_id}"}, "run_id", "")["result"]
                         ["completion"]["values"], runs)
        self.assertEqual(comp(prompt("audit_site"), "url", "exa")["result"]["completion"]["values"], [])
        modern = comp(prompt("explain_check"), "check_id", "g.", MODERN)["result"]
        self.assertEqual(modern["resultType"], "complete")
        for ref, name in ((prompt("nope"), "x"), ({"type": "ref/other"}, "x"), ("explain_check", "check_id")):
            self.assertEqual(comp(ref, name, "")["error"]["code"], -32602, ref)

    def test_saved_runs_as_a_resource_template(self):
        srv = self.with_two_runs()
        tpl = self.rpc(srv, "resources/templates/list")["result"]["resourceTemplates"]
        self.assertEqual([t["uriTemplate"] for t in tpl], ["geo-score://runs/{run_id}"])
        r = self.rpc(srv, "resources/read", {"uri": "geo-score://runs/20260926T083000Z"})["result"]
        self.assertEqual(json.loads(r["contents"][0]["text"])["overall"]["answered"], 4)
        m = self.rpc(srv, "resources/read", {"uri": "geo-score://runs/20260926T083000Z"}, meta=MODERN)["result"]
        self.assertEqual((m["ttlMs"], m["cacheScope"]), (0, "private"))                # the user's own data
        for uri in ("geo-score://runs/20990101T000000Z", "geo-score://runs/../../etc/passwd", "geo-score://runs/latest"):
            self.assertEqual(self.rpc(srv, "resources/read", {"uri": uri})["error"]["code"], -32002, uri)
        score_only = gw.MCPServer(srv.config_path, out=io.StringIO(), enabled=gw.tool_filter("score"))
        self.assertEqual(self.rpc(score_only, "resources/templates/list")["result"]["resourceTemplates"], [])
        self.assertEqual(self.rpc(score_only, "resources/read", {"uri": "geo-score://runs/20260926T083000Z"})
                         ["error"]["code"], -32002)


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
        self.assertIn(b"installed as geo-score-mcp", b" ".join(p.stdout.split()))
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
        for bad in ("http://localhost/", "http://127.0.0.1:8080/", "10.0.0.5", "http://169.254.169.254/latest",
                    "http://100.100.100.200/latest/meta-data/", "100.64.0.1", "http://[::ffff:127.0.0.1]/"):
            r = srv.call({"name": "score_site", "arguments": {"url": bad}})
            self.assertTrue(r["isError"], bad)

    def test_score_site_says_a_name_does_not_resolve_instead_of_calling_it_private(self):
        fake = os.path.join(self.tmp, "geo_score.py")
        with io.open(fake, "w", encoding="utf-8") as f:
            f.write("ADDRESS_GUARD = False\n"
                    "def run(url, sample=8):\n    return {'u': url}\n"
                    "def as_json(res):\n    return {'target': res['u'], 'normalised': 71, 'band': 'Solid', "
                    "'gate_capped': False, 'tool': 'geo-score-cli/1.4.0', 'rubric_version': 'v1.1', 'checks': []}\n")
        os.environ["GEO_SCORE_PY"] = fake
        srv = gw.MCPServer(os.path.join(self.tmp, "none.json"), out=io.StringIO())
        dns = {"nonexistent-host-zz9q.example": socket.gaierror(socket.EAI_NONAME, "nodename nor servname provided"),
               "intranet.example": [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0))],
               "public.example": [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 0))]}

        def getaddrinfo(host, *a, **k):
            if isinstance(dns[host], Exception):
                raise dns[host]
            return dns[host]

        def score(url):
            r = srv.call({"name": "score_site", "arguments": {"url": url}})
            return r["isError"], r["content"][0]["text"]

        with mock.patch.object(socket, "getaddrinfo", getaddrinfo), \
                mock.patch.object(urllib.request, "getproxies", lambda: {}):
            self.assertEqual(score("nonexistent-host-zz9q.example"), (True, "cannot resolve nonexistent-host-zz9q.example: "
                                                                           "check the spelling, or your DNS/proxy settings"))
            bad, text = score("https://intranet.example/docs")
            self.assertTrue(bad)
            self.assertEqual(text, "url must be on a public host: intranet.example resolves to a private, loopback or "
                                   "reserved address")
            self.assertEqual(score("public.example")[0], False)           # resolved, public: scored
        # behind a proxy the name still has to resolve here, because the address check runs here: the error says so
        with mock.patch.object(socket, "getaddrinfo", getaddrinfo), \
                mock.patch.object(urllib.request, "getproxies", lambda: {"https": "http://127.0.0.1:7897"}), \
                mock.patch.object(urllib.request, "proxy_bypass", lambda host: False):
            bad, text = score("nonexistent-host-zz9q.example")
            self.assertTrue(bad)
            self.assertTrue(text.startswith("cannot resolve nonexistent-host-zz9q.example: check the spelling"), text)
            self.assertIn("even through a proxy", text)

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
        gs.run = lambda url, sample=8, verbose=False, urls=None: json.loads(json.dumps(res))
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
           "queries": [gw.flag_query(q, who, []) for q in qs], "caps": {"max_calls": 1000, "budget_usd": None},
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

    def test_holm_makes_small_sets_untestable_and_says_so(self):
        # six questions all lost on two engines: 2/2^6 = 0.031 per row, but three rows make the best adjusted
        # p 0.094. "within noise" would claim the data showed no change; it only cannot show one.
        cited = {}
        for i in range(6):
            for e in ("chatgpt-api", "perplexity-api"):
                cited[("q%d" % i, e)] = [True]
        a = synth("20260919T083000Z", cited)
        b = synth("20260926T083000Z", dict((k, [False]) for k in cited))
        d = gw.diff_runs(a, b)
        self.assertEqual(set(r["verdict"] for r in [d["overall"]] + d["engines"] if r["n_pairs"]),
                         {"too few questions to tell"})
        cited = dict((("q%d" % i, e), [True]) for i in range(10) for e in ("chatgpt-api", "perplexity-api"))
        d = gw.diff_runs(synth("20260919T083000Z", cited), synth("20260926T083000Z", dict((k, [False]) for k in cited)))
        self.assertEqual(d["overall"]["verdict"], "change")        # ten questions: 3 x 2/2^10 is far below 0.05

    def test_too_few_questions_to_tell(self):
        def flip(n):
            a = synth("20260919T083000Z", dict((("q%d" % i, "chatgpt-api"), [True]) for i in range(n)))
            b = synth("20260926T083000Z", dict((("q%d" % i, "chatgpt-api"), [False]) for i in range(n)))
            return gw.diff_runs(a, b)
        d = flip(5)                                           # all five lost: p = 0.0625, it could be chance
        self.assertEqual(d["overall"]["verdict"], "too few questions to tell")
        self.assertEqual((d["overall"]["p_paired"], d["overall"]["p_adjusted"], d["overall"]["delta_ci"]),
                         (0.0625, None, None))
        self.assertIn("Tarone's screen", gw.render_diff(d))
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


# ── questions that name the brand ────────────────────────────────────────
class Branded(Base):
    def test_questions_naming_the_brand_are_flagged(self):
        f = lambda text: gw.flag_query({"query_id": "q", "query": text}, brand(), rivals())
        self.assertTrue(f("鹿末视频免费吗")["brand_in_query"])            # CJK alias, no word boundaries
        self.assertTrue(f("哪个比较好：鹿末还是Pixa")["competitor_in_query"])  # a Latin name beside CJK text
        self.assertTrue(f("用Lumo做视频要多少钱")["brand_in_query"])
        self.assertFalse(f("is Lumos a good app")["brand_in_query"])    # whole words for Latin names
        self.assertTrue(f("is lumo.example legit")["brand_in_query"])   # a brand domain counts
        q = f("Lumo vs Pixa")
        self.assertEqual((q["brand_in_query"], q["competitor_in_query"], q["branded"]), (True, True, "auto"))
        q = f("pixa alternatives")
        self.assertEqual((q["brand_in_query"], q["competitor_in_query"]), (False, True))

    def test_the_branded_column_overrides_the_matcher(self):
        cfgp = os.path.join(self.tmp, gw.CONFIG_NAME)
        with io.open(cfgp, "w", encoding="utf-8") as f:
            json.dump({"brand": {"name": "Lumo", "domains": ["lumo.example"]}}, f)
        qp = os.path.join(self.tmp, "queries.csv")
        with io.open(qp, "w", encoding="utf-8") as f:
            f.write("query_id,query,intent_tier,target_url,branded\n"
                    "q1,lumo vs pixa,vs,,\nq2,is lumo worth it,,,No\nq3,the app with the fox logo,,,yes\n"
                    "q4,best ai video tool,,,auto\n")
        cfg = gw.Config(cfgp)
        qs = [gw.flag_query(q, cfg.brand, cfg.competitors) for q in cfg.load_queries()]
        self.assertEqual([q["branded"] for q in qs], ["auto", "no", "yes", "auto"])
        self.assertEqual([gw.is_branded(q) for q in qs], [True, False, True, False])
        with io.open(qp, "w", encoding="utf-8") as f:
            f.write("query_id,query,branded\nq1,lumo vs pixa,maybe\n")
        with self.assertRaises(gw.ConfigError) as cm:
            cfg.load_queries()
        self.assertIn("branded must be auto, yes or no", str(cm.exception))
        with io.open(qp, "w", encoding="utf-8") as f:
            f.write("query_id,query\nq1,lumo vs pixa\n")                # no column: auto
        self.assertEqual(cfg.load_queries()[0]["branded"], "auto")

    def test_the_headline_leaves_out_questions_that_name_the_brand(self):
        def handler(u, h, b):
            q = b["input"]
            cite = "lumo" in q.lower() or "鹿末" in q
            return openai_resp("Lumo is fine." if cite else "Pixa.",
                               [("https://lumo.example/", "")] if cite else [("https://pixa.example/", "")])
        self.fake({"api.openai.com": handler})
        qs = [{"query_id": "q1", "query": "best ai video tool", "intent_tier": "", "target_url": ""},
              {"query_id": "q2", "query": "cheap text to video", "intent_tier": "", "target_url": ""},
              {"query_id": "q3", "query": "lumo vs pixa", "intent_tier": "", "target_url": ""},
              {"query_id": "q4", "query": "鹿末怎么样", "intent_tier": "", "target_url": ""},
              {"query_id": "q5", "query": "is lumo free", "intent_tier": "", "target_url": "", "branded": "no"}]
        run = gw.execute(brand(), rivals(), engines("chatgpt-api"), qs)
        sm = run["summary"]
        self.assertEqual((sm["overall"]["cited"], sm["overall"]["answered"]), (3, 5))
        self.assertEqual((sm["headline"]["cited"], sm["headline"]["answered"], sm["headline"]["n_questions"]), (1, 3, 3))
        self.assertEqual(sm["branded"]["question_ids"], ["q3", "q4"])
        self.assertEqual((sm["branded"]["cited"], sm["branded"]["answered"]), (2, 2))
        self.assertEqual(sm["brand_flags"], "run")
        self.assertEqual([q["brand_in_query"] for q in run["queries"]], [False, False, True, True, True])
        text = gw.render(run)
        self.assertIn("Cited in 33% of answers to questions that do not name Lumo (1 of 3, 3 questions", text)
        self.assertIn("Questions that name Lumo (2, kept out of the headline): cited in 100% (2 of 2", text)
        self.assertIn("the 2 that name Lumo included", text)
        self.assertEqual(validate(json.loads(json.dumps(run)), watch_schema()), [])
        rows = list(__import__("csv").DictReader(io.StringIO(gw.render_csv(run))))
        self.assertEqual([r["branded"] for r in rows], ["N", "N", "Y", "Y", "N"])

    def test_every_question_naming_the_brand_leaves_no_headline(self):
        run = synth("20260926T083000Z", {("q1", "chatgpt-api"): [True]},
                    qs=[{"query_id": "q1", "query": "lumo pricing", "intent_tier": "", "target_url": ""}])
        text = gw.render(run)
        self.assertIn("No headline rate", text)
        self.assertNotIn("Cited in 100%", text)

    def test_check_warns_when_many_questions_name_the_brand(self):
        cfgp = os.path.join(self.tmp, gw.CONFIG_NAME)
        with io.open(cfgp, "w", encoding="utf-8") as f:
            json.dump({"brand": {"name": "Lumo", "domains": ["lumo.example"], "aliases": ["鹿末"]}}, f)

        def check(body):
            with io.open(os.path.join(self.tmp, "queries.csv"), "w", encoding="utf-8") as f:
                f.write("query_id,query\n" + body)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = gw.main(["check", "-c", cfgp])
            return code, out.getvalue()
        code, out = check("q1,lumo vs pixa\nq2,鹿末好用吗\nq3,best ai video tool\n")
        self.assertEqual(code, 0)
        self.assertIn("! 2 of 3 questions (67%) name Lumo (q1, q2)", out)
        code, out = check("q1,lumo vs pixa\nq2,a\nq3,b\nq4,c\nq5,d\n")
        self.assertEqual(code, 0)
        self.assertIn("· 1 of 5 questions (20%) name Lumo (q1)", out)
        self.assertNotIn("! ", out)

    def test_level2_says_when_a_question_names_the_brand(self):
        del os.environ["GEMINI_API_KEY"]
        del os.environ["ANTHROPIC_API_KEY"]
        self.fake(self.standard_routes())
        run, cit = gw.citation_check("https://www.lumo.example/", ["best free ai video generator", "lumo vs pixa"])
        self.assertIn("q2 names the brand", cit["note"])


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
            self.assertNotIn("brand_in_query", run["queries"][0])
            self.assertNotIn("headline", run["summary"])
            self.assertEqual(validate(run, sc), [])
        run = gw.load_run(self.cfg, self.ids[0])
        sm = gw.summary_of(run)
        self.assertEqual(sm["brand_flags"], "computed")
        self.assertEqual(sm["branded"]["question_ids"], ["q04", "q06"])     # "lumo vs pixa" and the 鹿末 question
        self.assertEqual((sm["headline"]["answered"], sm["headline"]["n_questions"]), (16, 4))
        self.assertEqual(sm["overall"]["cited_ci"], run["summary"]["overall"]["cited_ci"])   # Wilson unchanged
        self.assertTrue(sm["overall"]["cited_ci_clustered"])
        self.assertTrue(any("saved before questions were flagged" in n for n in sm["notes"]))
        self.assertEqual(validate(json.loads(json.dumps(dict(run, summary=sm))), sc), [])
        text = gw.render(run)
        self.assertIn("do not name Lumo", text)
        self.assertIn("saved before questions were flagged", text)
        d = gw.diff_runs(*[gw.load_run(self.cfg, rid) for rid in self.ids])
        self.assertEqual(validate(json.loads(json.dumps(d)), sc["$defs"]["diff"], sc), [])
        self.assertEqual(d["overall"]["n_questions"], 6)
        self.assertNotEqual(d["overall"]["verdict"], "change")
        for fmt in ("text", "md", "csv", "json"):
            self.assertEqual(self.main("report", "-c", self.cfgp, "--format", fmt)[0], 0)
        code, out = self.main("report", "-c", self.cfgp, "--format", "json")
        self.assertEqual(json.loads(out)["summary"]["brand_flags"], "computed")
        code, out = self.main("diff", "-c", self.cfgp, "--fail-on-drop")
        self.assertEqual(code, 0)
        # six questions over two engines and the overall row: even a unanimous move could not pass Holm
        self.assertIn("too few questions to tell", out)
        self.assertNotRegex(out, r"(?m)within noise\s*$")          # no row's verdict is "within noise"
        code, out = self.main("runs", "-c", self.cfgp)
        self.assertIn("cited (headline)", out)
        with io.open(os.path.join(FIXTURES, self.ids[0] + ".json"), encoding="utf-8") as f:
            self.assertNotIn("brand_in_query", f.read())                 # reports never rewrite a run file


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
