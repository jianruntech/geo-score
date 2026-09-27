#!/usr/bin/env python3
"""Run action.yml's script the way a GitHub runner would, against a local fixture site.

    python3 scripts/test_action.py

Hosted Actions have never run on this organisation, so this is the only execution the action gets
before a release. It reads the `run:` block and the `env:` map out of action.yml (no YAML library),
serves the `good` fixture from cli/fixtures on 127.0.0.1, and checks the outputs, the job summary,
the SARIF and JUnit files, the threshold, input validation, and that a crafted URL cannot run shell.
"""
import io, json, os, re, subprocess, sys, tempfile, xml.dom.minidom

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "cli"))
import test_geo_score_e2e as e2e  # noqa: E402  (the fixture server; importing it clears proxy variables)

fails = []


def ok(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def action_parts():
    text = io.open(os.path.join(ROOT, "action.yml"), encoding="utf-8").read()
    head, body = text.split("      run: |\n", 1)
    env_block = head.rsplit("      env:\n", 1)[1]
    env = dict(re.findall(r"^\s{8}(GEO_[A-Z_]+):\s*\$\{\{\s*([^}]+?)\s*\}\}\s*$", env_block, re.M))
    script = "\n".join(line[8:] for line in body.splitlines())
    return env, script


def run(script, tmp, **env):
    out, summ = os.path.join(tmp, "gh-output"), os.path.join(tmp, "gh-summary")
    for p in (out, summ):
        io.open(p, "w").close()
    e = {k: v for k, v in os.environ.items() if not k.startswith("GEO_")}
    # stay offline and fast: the fixture is served on loopback, and every off-site lookup the scorer makes
    # (Wikidata, sameAs profiles) goes to a proxy port nothing listens on, so it fails at once and reads
    # as not measured instead of waiting for a network timeout
    e.update(GITHUB_OUTPUT=out, GITHUB_STEP_SUMMARY=summ, RUNNER_TEMP=tmp, GEO_ACTION_PATH=ROOT, GEO_SAMPLE="8",
             GEO_ANNOTATIONS="true", HTTPS_PROXY="http://127.0.0.1:9", HTTP_PROXY="http://127.0.0.1:9",
             https_proxy="http://127.0.0.1:9", http_proxy="http://127.0.0.1:9",
             NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    e.update(env)
    p = subprocess.run(["bash", "-c", script], cwd=tmp, env=e, capture_output=True, text=True, timeout=300)
    outputs = dict(re.findall(r"^([a-z-]+)=(.*)$", io.open(out, encoding="utf-8").read(), re.M))
    return p, outputs, io.open(summ, encoding="utf-8").read()


def main():
    env, script = action_parts()
    used = set(re.findall(r"\$\{?(GEO_[A-Z_]+)", script))
    ok(used <= set(env) | {"GEO_ACTION_PATH"}, "every GEO_ variable the script reads is mapped in env: %s"
       % sorted(used - set(env) - {"GEO_ACTION_PATH"}))
    ok(not re.search(r"\$\{\{\s*inputs\.", script), "no ${{ inputs.* }} is pasted into the script")
    srv = e2e.start_server("good")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            print("\n  scoring the good fixture through action.yml")
            p, o, summ = run(script, tmp, GEO_URL=srv.origin, GEO_SARIF="out/r.sarif", GEO_JUNIT="out/r.xml")
            ok(p.returncode == 0, "exit 0 (got %d)%s" % (p.returncode, "" if p.returncode == 0 else ": " + p.stderr[-400:]))
            ok({"score", "band", "gate-capped", "report-path"} <= set(o), "outputs score, band, gate-capped, report-path")
            ok(o.get("score", "").isdigit() and 0 <= int(o["score"]) <= 100, "score is 0-100: %r" % o.get("score"))
            ok(summ.startswith("## AI visibility") and "| Check | Score | Why |" in summ, "the job summary has the table")
            sar = json.load(io.open(os.path.join(tmp, "out", "r.sarif"), encoding="utf-8"))
            ok(sar.get("version") == "2.1.0" and sar["runs"][0]["tool"]["driver"]["name"] == "geo-score", "SARIF 2.1.0 written")
            xml.dom.minidom.parse(os.path.join(tmp, "out", "r.xml"))
            ok(True, "JUnit XML parses")
            rep = json.load(io.open(o["report-path"], encoding="utf-8"))
            ok(str(rep["normalised"]) == o.get("score"), "the summary, the outputs and the JSON describe the same run")

        with tempfile.TemporaryDirectory() as tmp:
            p, o, summ = run(script, tmp, GEO_URL=srv.origin, GEO_FAIL_UNDER="101", GEO_ANNOTATIONS="false")
            ok(p.returncode == 1 and "below the 101 threshold" in p.stdout, "fail-under 101 fails the step with exit 1")
            ok(bool(summ) and "score" in o, "and still writes the summary and outputs first")
            ok("::warning" not in p.stdout, "annotations: false turns annotations off")

        with tempfile.TemporaryDirectory() as tmp:
            canary = os.path.join(tmp, "pwned")
            p, _, _ = run(script, tmp, GEO_URL="$(touch %s)" % canary)
            ok(p.returncode == 2 and not os.path.exists(canary), "a URL carrying $(…) is data, never shell")
            p, _, _ = run(script, tmp, GEO_URL=srv.origin, GEO_FAIL_UNDER="40; touch %s" % canary)
            ok(p.returncode == 2 and not os.path.exists(canary), "a non-numeric fail-under is refused, not executed")
            p, _, _ = run(script, tmp, GEO_URL=srv.origin, GEO_SAMPLE="abc")
            ok(p.returncode == 2 and "whole number" in p.stdout, "a non-numeric sample is refused")
    finally:
        srv.shutdown()
        srv.server_close()
    if fails:
        print("\nFAIL: %d action check(s)" % len(fails))
        sys.exit(1)
    print("\nOK: action.yml runs once, writes every output, and keeps inputs out of the shell")


if __name__ == "__main__":
    main()
