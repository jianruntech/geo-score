#!/usr/bin/env python3
"""Offline stdio conformance smoke test for `geo_score.py mcp`: no network, no keys.

    python3 scripts/check_mcp.py [python-interpreter]      # offline, raw JSON-RPC (check.sh)
    python3 scripts/check_mcp.py --inspector                # also through the official Inspector CLI (check.sh --live)

It spawns the server the way a client does and checks, over raw JSON-RPC:
  - the legacy handshake for every legacy protocol version, and an unknown version falling back to the newest legacy one
  - the modern (2026-07-28) path: server/discover, per-request _meta, -32022 for an unsupported version
  - the exact tool and prompt sets, the rubric resource, protocol vs tool errors
  - that every line on stdout is a JSON-RPC 2.0 message, and that the server exits promptly on EOF
The official conformance suite only drives Streamable HTTP, so this is the stdio gate (scripts/check.sh runs it).
--inspector repeats the key checks through @modelcontextprotocol/inspector (pinned below) and calls score_site on
example.com, so it needs npx, Node 22.19+ and the network; without them it says "skipped" and passes.
"""
import json, os, queue, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARGS = [a for a in sys.argv[1:] if a != "--inspector"]
PY = ARGS[0] if ARGS else sys.executable
INSPECTOR = "@modelcontextprotocol/inspector@2.8.0"
LEGACY = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
MODERN = "2026-07-28"
TOOLS = {"score_site", "ask", "run", "list_runs", "report", "diff", "status"}
PROMPTS = {"audit_site", "check_citations", "weekly_watch", "compare_runs", "explain_check"}
RUBRIC = "geo-score://rubric/v1.1"
TIMEOUT = 30


class Server(object):
    def __init__(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        for k in ("OPENAI_API_KEY", "PERPLEXITY_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
            env.pop(k, None)          # offline and free: no provider can be reached even by mistake
        env["GEO_SCORE_WATCH_CONFIG"] = os.path.join(ROOT, "nonexistent-geo-score-watch.json")
        self.p = subprocess.Popen([PY, os.path.join(ROOT, "cli", "geo_score.py"), "mcp"], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT, env=env)
        self.q, self.lines, self.next_id = queue.Queue(), [], 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in self.p.stdout:
            self.lines.append(raw)
            self.q.put(raw)
        self.q.put(None)

    def send(self, obj):
        self.p.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
        self.p.stdin.flush()

    def request(self, method, params=None):
        self.next_id += 1
        mid = self.next_id
        msg = {"jsonrpc": "2.0", "id": mid, "method": method}
        if params is not None:
            msg["params"] = params
        self.send(msg)
        end = time.time() + TIMEOUT
        while time.time() < end:
            try:
                raw = self.q.get(timeout=max(0.1, end - time.time()))
            except queue.Empty:
                break
            if raw is None:
                break
            m = json.loads(raw)
            if m.get("id") == mid and "method" not in m:
                return m
        raise AssertionError("no response to %s (id %d) within %ds" % (method, mid, TIMEOUT))

    def close(self):
        self.p.stdin.close()
        try:
            code = self.p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.p.kill()
            raise AssertionError("server did not exit within 5 s of EOF") from None
        err = self.p.stderr.read().decode("utf-8", "replace")
        assert code == 0, "server exited %s on EOF: %s" % (code, err[-300:])
        for raw in self.lines:        # stdout carries JSON-RPC and nothing else
            m = json.loads(raw)
            assert isinstance(m, dict) and m.get("jsonrpc") == "2.0", "not a JSON-RPC message on stdout: %r" % raw[:120]


def ok(cond, what):
    if not cond:
        raise AssertionError(what)
    print("  ok  " + what)


def modern_params(extra=None, version=MODERN):
    p = {"_meta": {"io.modelcontextprotocol/protocolVersion": version, "io.modelcontextprotocol/clientCapabilities": {}}}
    p.update(extra or {})
    return p


def legacy(version, expect):
    s = Server()
    r = s.request("initialize", {"protocolVersion": version, "capabilities": {},
                                 "clientInfo": {"name": "check_mcp", "version": "0"}})
    ok(r.get("result", {}).get("protocolVersion") == expect, "initialize %s -> %s" % (version, expect))
    s.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    if version != expect:
        return s.close()
    res = s.request("tools/list")["result"]
    ok({t["name"] for t in res["tools"]} == TOOLS, "[%s] tools/list is exactly %s" % (version, sorted(TOOLS)))
    ok("resultType" not in res and "ttlMs" not in res, "[%s] legacy results carry no modern fields" % version)
    ok(all(t.get("title") and set(t.get("annotations", {})) >= {"readOnlyHint", "destructiveHint", "idempotentHint",
                                                                "openWorldHint"} for t in res["tools"]),
       "[%s] every tool has a title and all four hints" % version)
    ok(s.request("tools/call", {"name": "no_such_tool", "arguments": {}}).get("error", {}).get("code") == -32602,
       "[%s] unknown tool is a protocol error (-32602)" % version)
    bad = s.request("tools/call", {"name": "score_site", "arguments": {}})
    ok(bad.get("result", {}).get("isError") is True, "[%s] a missing argument is a tool error (isError)" % version)
    rr = s.request("resources/read", {"uri": RUBRIC})["result"]
    ok(json.loads(rr["contents"][0]["text"]).get("checks"), "[%s] %s reads as JSON with checks" % (version, RUBRIC))
    ok(s.request("resources/read", {"uri": "geo-score://nope"}).get("error", {}).get("code") == -32002,
       "[%s] unknown resource is -32002 on the legacy path" % version)
    pl = s.request("prompts/list")["result"]
    ok({p["name"] for p in pl["prompts"]} == PROMPTS, "[%s] prompts/list is exactly %s" % (version, sorted(PROMPTS)))
    ok("result" in s.request("ping"), "[%s] ping" % version)
    s.close()


def modern():
    s = Server()
    d = s.request("server/discover", modern_params())["result"]
    ok(d.get("resultType") == "complete" and MODERN in d.get("supportedVersions", []) and "2025-11-25" in d["supportedVersions"],
       "server/discover lists %s and 2025-11-25" % MODERN)
    ok(isinstance(d.get("ttlMs"), int) and d.get("cacheScope") in ("public", "private"), "server/discover carries ttlMs and cacheScope")
    tl = s.request("tools/list", modern_params())["result"]
    ok(tl.get("resultType") == "complete" and {t["name"] for t in tl["tools"]} == TOOLS, "modern tools/list, no initialize")
    e = s.request("tools/list", modern_params(version="2099-01-01")).get("error", {})
    ok(e.get("code") == -32022 and MODERN in (e.get("data") or {}).get("supported", []), "unsupported version is -32022 with data.supported")
    ok(s.request("resources/read", modern_params({"uri": "geo-score://nope"})).get("error", {}).get("code") == -32602,
       "unknown resource is -32602 on the modern path")
    bad = s.request("tools/call", modern_params({"name": "score_site", "arguments": {}}))
    ok(bad.get("result", {}).get("isError") is True, "modern tools/call: a missing argument is a tool error")
    s.close()


def inspector():
    import shutil
    npx = shutil.which("npx")
    node = shutil.which("node")
    if not npx or not node:
        print("inspector: npx or node not found: skipped")
        return
    ver = subprocess.run([node, "-p", "process.versions.node"], stdout=subprocess.PIPE).stdout.decode().strip()
    if tuple(int(x) for x in ver.split(".")[:2]) < (22, 19):
        print("inspector: Node %s is older than 22.19: skipped" % ver)
        return
    server = [PY, os.path.join(ROOT, "cli", "geo_score.py"), "mcp"]
    # the SDK's stdio transport hands the server only a safe list of variables (PATH, HOME, ...): pass the
    # proxy settings on, or score_site cannot reach anything on a network that needs a proxy
    env = []
    for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"):
        if os.environ.get(k):
            env += ["-e", "%s=%s" % (k, os.environ[k])]

    def cli(*args):
        r = subprocess.run([npx, "--yes", INSPECTOR, "--cli"] + server + ["--"] + env + list(args) + ["--format", "json"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT, timeout=180)
        assert r.returncode == 0, "inspector %s exited %d: %s" % (" ".join(args), r.returncode,
                                                                  r.stderr.decode("utf-8", "replace")[-300:])
        return json.loads(r.stdout.decode("utf-8"))

    print("MCP through %s" % INSPECTOR)
    d = cli("--method", "tools/list", "--strict")
    ok(not d.get("schemaFindings") and {t["name"] for t in d["result"]["tools"]} == TOOLS, "tools/list --strict: no schema findings")
    for era, want in (("legacy", LEGACY[0]), ("modern", MODERN)):
        d = cli("--protocol-era", era, "--method", "initialize")
        ok(d["result"].get("protocolVersion") == want, "--protocol-era %s negotiates %s" % (era, want))
    d = cli("--method", "resources/read", "--uri", RUBRIC)
    ok(json.loads(d["result"]["contents"][0]["text"]).get("checks"), "resources/read %s" % RUBRIC)
    d = cli("--method", "prompts/list")
    ok({p["name"] for p in d["result"]["prompts"]} == PROMPTS, "prompts/list")
    d = cli("--method", "tools/call", "--tool-name", "score_site", "--tool-arg", "url=https://example.com")
    sc = d["result"].get("structuredContent") or {}
    ok(isinstance(sc.get("normalised"), int) and 0 <= sc["normalised"] <= 100, "tools/call score_site example.com: normalised %s"
       % sc.get("normalised"))


def main():
    if "--inspector" in sys.argv[1:]:
        inspector()
        print("mcp inspector checks: all passed")
        return 0
    print("MCP stdio conformance (%s)" % PY)
    for v in LEGACY:
        legacy(v, v)
    legacy("1999-01-01", LEGACY[0])
    modern()
    print("mcp conformance: all passed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print("FAIL: %s" % e, file=sys.stderr)
        sys.exit(1)
