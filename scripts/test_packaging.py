#!/usr/bin/env python3
"""Check the packaging manifests against the code they package.

    python3 scripts/test_packaging.py

mcpb/manifest.json (Claude Desktop), server.json (the MCP Registry), .claude-plugin/ (Claude Code),
gemini-extension.json (Gemini CLI) and the Dockerfile each restate something the code already says: the
version, the tool names, the key variables, the entry point. Nothing else would notice when one of them
falls behind, so this compares each with the code, then builds the .mcpb the way release.py does, starts the
bundled server and asks it for its tools.
"""
import importlib.util, io, json, os, re, subprocess, sys, tempfile, zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import release  # noqa: E402  (MANIFESTS, version_fields, pack: the same code a release runs)
import mcp_docs  # noqa: E402  (the install block's wheel URL)

# tracked files that may name a release although --bump does not rewrite them: the changelogs (history), raw
# benchmark reports, build output, the pages build_page.py regenerates from the PINNED benchmark/_page_tpl.py,
# and validate.py, whose rule 27 holds the pattern's text
PIN_EXEMPT = re.compile(r"^(?:CHANGELOG[^/]*|benchmark/raw/.*|dist/.*|docs/[^/]*\.html|\.github/validate\.py)$")
# a wheel download: (the release tag, the version in the wheel's file name)
WHEEL_URL = re.compile(r"releases/download/v(\d+\.\d+\.\d+)/geo_score-(\d+\.\d+\.\d+)-py3-none-any\.whl")
SERVER_SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
NAME_RE = re.compile(r"^[a-zA-Z0-9.-]+/[a-zA-Z0-9._-]+$")     # server.json schema 2025-12-11, `name`
WATCH_ENV = "GEO_SCORE_WATCH_CONFIG"
JSON_FILES = release.MANIFESTS + [".claude-plugin/marketplace.json"]

fails = []


def ok(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def rd(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def load_watch():
    spec = importlib.util.spec_from_file_location("geo_watch_under_test", os.path.join(ROOT, "cli", "geo_watch.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tracked():
    """The repository's tracked files, or None outside a git checkout."""
    try:
        r = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return None
    return [p for p in r.stdout.decode("utf-8").split("\0") if p] if r.returncode == 0 else None


def check_pins(version):
    """Every tracked file that pins a release is one release.py rewrites, and every wheel URL names this release."""
    print("\n  release pins: every tracked file that names a release is in release.py's PINNED")
    files = tracked()
    if files is None:
        print("  skip  not a git checkout, so there is no list of tracked files")
        return
    listed, bad, wheels = set(release.PINNED), 0, 0
    for p in files:
        full = os.path.join(ROOT, p)
        if PIN_EXEMPT.match(p) or not os.path.isfile(full):
            continue
        text = io.open(full, encoding="utf-8", errors="replace").read()
        for m in WHEEL_URL.finditer(text):
            wheels += 1
            if not m.group(1) == m.group(2) == version:
                ok(False, "%s downloads %s; tag and wheel must both be %s" % (p, m.group(0), version))
        if p in listed:
            continue
        hits = sorted({m.group(0) for rx, _ in release.PINS for m in rx.finditer(text)})
        if hits:
            bad += 1
            ok(False, "%s names %s but is not in PINNED, so --bump would leave it behind" % (p, ", ".join(hits)))
    if not bad:
        ok(True, "%d tracked files: each one that names a release is in PINNED or exempt" % len(files))
    ok(wheels > 0, "%d wheel URLs, each releases/download/v%s/%s" % (wheels, version, release.wheel_name(version)))

    print("\n  the wheel: what the install lines download, and what --bump and preflight do to it")
    url = "%s/releases/download/v%s/%s" % (release.REPO, version, release.wheel_name(version))
    ok(mcp_docs.cfg_for(version)["args"][1] == url, "mcp_docs.py installs %s" % url)
    # built from parts, so this file does not itself name a release
    old = "uvx --from %s/releases/download/v%s/%s geo-score" % (release.REPO, "1.2.3", release.wheel_name("1.2.3"))
    ok(release.repin(old, "9.9.9") == old.replace("1.2.3", "9.9.9"), "--bump rewrites the tag and the wheel's version")
    ok(release.stale_pins(old.replace("v1.2.3", "v9.9.9"), "9.9.9") == ["geo_score-1.2.3"],
       "preflight names a wheel whose version is not the tag's")
    with tempfile.TemporaryDirectory() as tmp:
        io.open(os.path.join(tmp, release.wheel_name(version)), "wb").close()
        ok(release.wheel_problem(version, tmp) is None, "--execute goes on when the build made %s" % release.wheel_name(version))
        os.rename(os.path.join(tmp, release.wheel_name(version)), os.path.join(tmp, "geo_score-%s-cp312-cp312-any.whl" % version))
        ok(release.wheel_problem(version, tmp) is not None, "--execute stops when the build names the wheel differently")


def check_pythons():
    """pyproject.toml's requires-python and classifiers say what check.sh tests: PY_OLDEST to PY_NEWEST."""
    print("\n  Python versions: pyproject.toml against check.sh's PY_OLDEST and PY_NEWEST")
    gate, pp = rd("scripts/check.sh"), rd("pyproject.toml")
    lo, hi = (re.search(r"^%s=3\.(\d+)$" % k, gate, re.M) for k in ("PY_OLDEST", "PY_NEWEST"))
    ok(lo is not None and hi is not None, "check.sh sets PY_OLDEST and PY_NEWEST")
    if lo is None or hi is None:
        return
    lo, hi = int(lo.group(1)), int(hi.group(1))
    ok(re.search(r'^requires-python = ">=3\.%d"$' % lo, pp, re.M) is not None, "requires-python is >=3.%d" % lo)
    got = sorted(int(x) for x in re.findall(r'"Programming Language :: Python :: 3\.(\d+)"', pp))
    ok(got == list(range(lo, hi + 1)),
       "a classifier for each of 3.%d to 3.%d (%s)" % (lo, hi, ", ".join("3.%d" % x for x in got)))
    ok('"Programming Language :: Python :: 3 :: Only"' in pp, "the '3 :: Only' classifier")


def check_gate_pins():
    """The workflow runs the gate with the tool versions check.sh pins, on actions pinned by commit."""
    print("\n  the gate's pins: tools in check.sh and the workflows, actions by commit")
    gate = rd("scripts/check.sh")
    for var, pkg in (("RUFF_VERSION", "ruff"), ("JSONSCHEMA_VERSION", "jsonschema")):
        m = re.search(r"^%s=(\S+)$" % var, gate, re.M)
        ok(m is not None, "check.sh sets %s" % var)
        if m:
            wf = rd(".github/workflows/validate.yml")
            ok("%s==%s" % (pkg, m.group(1)) in wf, "validate.yml installs %s==%s, as check.sh pins" % (pkg, m.group(1)))
    wdir = os.path.join(ROOT, ".github", "workflows")
    for f in sorted(os.listdir(wdir)):
        if not f.endswith((".yml", ".yaml")):
            continue
        text = rd(os.path.join(".github", "workflows", f))
        uses = re.findall(r"^\s*(?:-\s+)?uses:\s*(\S+)(.*)$", text, re.M)
        loose = [u for u, rest in uses if not (re.search(r"@[0-9a-f]{40}$", u) and re.match(r"\s+#\s*v\d", rest))]
        ok(not loose, "%s: every action is pinned by commit with a '# vX.Y.Z' comment%s"
           % (f, " (not: %s)" % ", ".join(loose) if loose else ""))
        ok(re.search(r"^permissions:", text, re.M) is not None, "%s: sets top-level permissions" % f)
        checkouts = len(re.findall(r"uses:\s*actions/checkout@", text))
        ok(len(re.findall(r"persist-credentials:\s*false", text)) >= checkouts,
           "%s: no checkout keeps the token (persist-credentials: false)" % f)


def mcp_session(cmd, cwd, env):
    """initialize then tools/list over stdio; returns (serverInfo, tool names)."""
    lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}}},
             {"jsonrpc": "2.0", "method": "notifications/initialized"},
             {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
    r = subprocess.run(cmd, cwd=cwd, env=env, input="".join(json.dumps(m) + "\n" for m in lines),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
    by_id = {m.get("id"): m for m in (json.loads(x) for x in r.stdout.splitlines() if x.strip())}
    info = by_id.get(1, {}).get("result", {}).get("serverInfo", {})
    return info, [t["name"] for t in by_id.get(2, {}).get("result", {}).get("tools", [])]


def main():
    version = re.search(r'^__version__ = "([^"]+)"', rd("cli/geo_score.py"), re.M).group(1)
    watch = load_watch()
    ok(watch.__version__ == version, "cli/geo_score.py and cli/geo_watch.py are both %s" % version)
    check_pins(version)

    print("\n  every manifest parses, in the layout release.py writes, at the CLI's version")
    m = {}
    for p in JSON_FILES:
        try:
            text = rd(p)
            m[p] = json.loads(text)
        except (IOError, OSError, ValueError) as e:
            ok(False, "%s parses (%s)" % (p, e))
            continue
        # bump() rewrites these with json.dumps(indent=2): any other layout would turn a version bump into a reformat
        ok(text == json.dumps(m[p], indent=2, ensure_ascii=False) + "\n", "%s is in release.py's JSON layout" % p)
    if len(m) != len(JSON_FILES):
        return
    for p in release.MANIFESTS:
        for field, now, want in release.version_fields(m[p], version):
            ok(now == want, "%s %s is %s" % (p, field, want))
    for e in m[".claude-plugin/marketplace.json"]["plugins"]:
        ok(e.get("version") in (None, version), "marketplace.json names no other version for %s" % e.get("name"))

    print("\n  server.json (MCP Registry, schema 2025-12-11)")
    s = m["server.json"]
    ok(s.get("$schema") == SERVER_SCHEMA, "$schema is the 2025-12-11 server schema")
    ok(s.get("name") == "io.github.jianruntech/geo-score" and bool(NAME_RE.match(s.get("name", ""))),
       "name is io.github.jianruntech/geo-score and matches the schema's pattern")
    ok(0 < len(s.get("description", "")) <= 100, "description is 1-100 characters (%d)" % len(s.get("description", "")))
    ok(len(s.get("title", "")) <= 100, "title is at most 100 characters")
    pk = [x for x in s.get("packages", []) if x.get("registryType") == "mcpb"]
    ok(len(pk) == 1, "one mcpb package")
    ok(bool(pk) and pk[0].get("fileSha256") == "${MCPB_SHA256}",
       "the template's fileSha256 is the ${MCPB_SHA256} placeholder (release.py fills it in dist/server.json)")
    ok(bool(pk) and pk[0].get("transport") == {"type": "stdio"}, "the mcpb package speaks stdio")

    print("\n  tools: the MCPB manifest lists exactly what tools/list serves")
    served = [t["name"] for t in watch.MCPServer("/nonexistent/geo-score-watch.json").handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]]
    listed = [t["name"] for t in m["mcpb/manifest.json"].get("tools", [])]
    ok(sorted(listed) == sorted(served), "mcpb/manifest.json tools %s == tools/list %s" % (sorted(listed), sorted(served)))

    print("\n  key variables: every manifest asks for the provider keys in PROVIDERS, and only those")
    # the first variable of each provider; an alias such as GOOGLE_API_KEY still works from the environment,
    # but a form that asked for it too would ask for the same key twice
    keys = {p["env"][0] for p in watch.PROVIDERS.values()}
    every = {e for p in watch.PROVIDERS.values() for e in p["env"]}
    man = m["mcpb/manifest.json"]
    env, uc = man["server"]["mcp_config"].get("env", {}), man.get("user_config", {})
    ok(set(env) == keys | {WATCH_ENV}, "mcpb env maps %s plus %s" % (sorted(keys), WATCH_ENV))
    for var, val in sorted(env.items()):
        opt = re.match(r"^\$\{user_config\.([a-z_]+)\}$", val)
        o = uc.get(opt.group(1)) if opt else None
        ok(o is not None, "mcpb %s comes from a declared user_config option" % var)
        if o is None:
            continue
        # an optional field left empty must reach the server as "" (no key), never as the literal ${user_config...}
        ok(o.get("required") is False and o.get("default") == "", "mcpb %s is optional with default \"\"" % var)
        ok(bool(o.get("sensitive")) == (var in keys), "mcpb %s is %s" % (var, "sensitive" if var in keys else "not sensitive"))
    reg = {e["name"]: e for e in pk[0].get("environmentVariables", [])} if pk else {}
    ok(set(reg) == keys | {WATCH_ENV}, "server.json environmentVariables are the keys plus %s" % WATCH_ENV)
    ok(all(reg[n].get("isSecret") is (n in keys) and reg[n].get("isRequired") is False for n in reg),
       "server.json: keys are secret, nothing is required")
    gem = m["gemini-extension.json"].get("settings", [])
    ok({x.get("envVar") for x in gem} == keys and all(x.get("sensitive") is True for x in gem),
       "gemini-extension.json has one sensitive setting per key")
    plug = m[".claude-plugin/plugin.json"]
    penv = {v for srv in plug.get("mcpServers", {}).values() for v in srv.get("env", {})}
    # Claude Code substitutes "" for an optional userConfig value left empty, which would blank an exported key
    ok(not (penv & every) and not plug.get("userConfig"),
       "plugin.json leaves the keys to the environment Claude Code runs in (no env or userConfig mapping)")

    print("\n  entry points name files that exist")
    srv = man["server"]
    ok(srv["entry_point"] in [a for a, _ in release.MCPB_FILES], "mcpb entry_point %s is in the bundle" % srv["entry_point"])
    ok(srv["mcp_config"]["args"][0] == "${__dirname}/" + srv["entry_point"], "mcpb runs its entry_point")
    for p, prefix, sep in ((".claude-plugin/plugin.json", "${CLAUDE_PLUGIN_ROOT}/", "/"),
                           ("gemini-extension.json", "${extensionPath}${/}", "${/}")):
        for cfg in m[p].get("mcpServers", {}).values():
            a0 = cfg.get("args", [""])[0]
            rel = a0[len(prefix):].replace(sep, "/") if a0.startswith(prefix) else None
            ok(rel == "cli/geo_score.py" and cfg.get("args", [])[1:] == ["mcp"], "%s runs cli/geo_score.py mcp" % p)
            ok("cwd" not in cfg, "%s sets no cwd, so ./geo-score-watch.json is the user's project" % p)
    mk = m[".claude-plugin/marketplace.json"]
    ok([(e.get("name"), e.get("source")) for e in mk.get("plugins", [])] == [(plug["name"], "./")],
       "marketplace.json offers this repository's plugin")
    dock = rd("Dockerfile")
    ok(re.search(r'io\.modelcontextprotocol\.server\.name="%s"' % re.escape(s["name"]), dock) is not None,
       "the Dockerfile's server-name label is server.json's name")
    ok(re.search(r"^COPY cli/geo_score\.py cli/geo_watch\.py /app/$", dock, re.M) is not None,
       "the image copies the two CLI files")
    ok([x for x in rd(".dockerignore").splitlines() if x and not x.startswith("#")]
       == ["*", "!cli/geo_score.py", "!cli/geo_watch.py"], ".dockerignore lets in the two CLI files only")
    ok(re.search(r"^FROM python:[\w.-]+@sha256:[0-9a-f]{64}$", dock, re.M) is not None,
       "the Dockerfile's base image is pinned by digest")
    check_gate_pins()
    check_pythons()

    print("\n  the .mcpb release.py builds")
    with tempfile.TemporaryDirectory() as tmp:
        mcpb, sj = release.pack(version, os.path.join(tmp, "a"))
        again, _ = release.pack(version, os.path.join(tmp, "b"))
        digest = release.sha256(mcpb)
        ok(digest == release.sha256(again), "two builds give one SHA-256 (%s…)" % digest[:12])
        with zipfile.ZipFile(mcpb) as z:
            ok(z.namelist() == ["manifest.json"] + [a for a, _ in release.MCPB_FILES],
               "the bundle holds manifest.json, %s" % ", ".join(a for a, _ in release.MCPB_FILES))
            inner = json.loads(z.read("manifest.json").decode("utf-8"))
            z.extractall(os.path.join(tmp, "x"))
        ok(inner == dict(man, version=version), "the bundled manifest is mcpb/manifest.json at %s" % version)
        built = json.loads(io.open(sj, encoding="utf-8").read())
        bp = [x for x in built.get("packages", []) if x.get("registryType") == "mcpb"]
        ok(bool(bp) and bp[0].get("fileSha256") == digest and bp[0].get("identifier") == release.mcpb_url(version),
           "dist/server.json names the bundle's URL and SHA-256")
        ok("${" not in io.open(sj, encoding="utf-8").read(), "dist/server.json has no placeholder left")
        env = {k: v for k, v in os.environ.items() if k not in every and not k.startswith("GEO_SCORE")}
        info, names = mcp_session([sys.executable, os.path.join(tmp, "x", "server", "geo_score.py"), "mcp"], tmp, env)
        ok(info.get("name") == "geo-score" and info.get("version") == version,
           "the bundled server starts and says geo-score %s" % version)
        ok(sorted(names) == sorted(listed), "the bundled server serves the manifest's tools")

    if fails:
        print("\nFAIL: %d packaging check(s)" % len(fails))
        sys.exit(1)
    print("\nOK: the manifests match the code, and the .mcpb builds, starts and serves its tools")


if __name__ == "__main__":
    main()
