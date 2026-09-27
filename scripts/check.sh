#!/usr/bin/env bash
# The gate every change passes before it merges.
#
#   bash scripts/check.sh           # offline: structure, generated MCP docs, lint, unit + end-to-end tests,
#                                   # the Action, the packaging manifests and the .mcpb
#   bash scripts/check.sh --live    # also score example.com and check the JSON and --fail-under
#
# Hosted Actions have never run on this organisation, so this script is the CI: maintainers run it
# before every merge (the pre-push hook in .githooks does it for you), and .github/workflows/validate.yml
# runs the same script, so the two cannot drift if Actions is ever enabled.
set -euo pipefail
cd "$(dirname "$0")/.."
LIVE=0
[ "${1:-}" = "--live" ] && LIVE=1

step() { printf '\n== %s\n' "$*"; }

step "structure: rubric, docs, schemas, generated pages (validate.py)"
python3 .github/validate.py

step "generated MCP docs: tool table and install links in README*/guide/mcp* (mcp_docs.py --check)"
python3 scripts/mcp_docs.py --check

step "lint: ruff (E9, F, B)"
if command -v ruff >/dev/null 2>&1; then ruff check cli benchmark .github action scripts
elif command -v uvx >/dev/null 2>&1; then uvx ruff check cli benchmark .github action scripts
else echo "ruff not installed: skipped (pip install ruff)"; fi

# The CLI promises Python 3.8+. With uv, test the oldest and the newest it can find; without it,
# test whatever python3 is.
PYS=()
if command -v uv >/dev/null 2>&1; then
  for v in 3.8 3.12 3.13; do
    p="$(uv python find --no-project "$v" 2>/dev/null || true)"
    if [ -n "$p" ]; then PYS+=("$p"); else echo "python $v not found by uv: skipped (uv python install $v)"; fi
  done
fi
[ ${#PYS[@]} -gt 0 ] || PYS=("python3")

for py in "${PYS[@]}"; do
  step "tests on $("$py" -c 'import sys; print("python %d.%d" % sys.version_info[:2])')"
  "$py" cli/test_geo_score.py
  "$py" cli/test_geo_watch.py
  "$py" cli/test_geo_score_e2e.py
done

# the end-to-end suite validates every report against schema/report.v2.json when jsonschema is importable
if python3 -c "import jsonschema" >/dev/null 2>&1; then
  step "reports against the published schema (jsonschema)"; python3 cli/test_geo_score_e2e.py
elif command -v uv >/dev/null 2>&1 && uv run --no-project --with jsonschema python -c "import jsonschema" >/dev/null 2>&1; then
  step "reports against the published schema (jsonschema via uv)"; uv run --no-project --with jsonschema python cli/test_geo_score_e2e.py
else
  echo "jsonschema unavailable: the full schema check was skipped (pip install jsonschema)"
fi

step "the GitHub Action, run as a runner would (scripts/test_action.py)"
python3 scripts/test_action.py

step "packaging: the manifests against the code; the .mcpb builds, starts and serves its tools (test_packaging.py)"
python3 scripts/test_packaging.py

if [ "$LIVE" = 1 ]; then
  step "live: example.com, JSON against the schema"
  out="$(mktemp)"
  python3 cli/geo_score.py example.com --json --quiet > "$out"
  python3 - "$out" <<'PY'
import json, sys
rep = json.load(open(sys.argv[1]))
try:
    import jsonschema
    jsonschema.validate(rep, json.load(open("schema/report.v2.json")))
except ImportError:
    print("jsonschema not installed: schema validation skipped (pip install jsonschema)")
ids = {c["id"] for c in rep["checks"]}
spec = {c["id"] for c in json.load(open("rubric/v1.1.json"))["checks"]}
assert ids <= spec, "CLI emitted unknown check ids: %s" % sorted(ids - spec)
assert 0 <= rep["normalised"] <= 100
print("ok: %d/100 %s, %d checks" % (rep["normalised"], rep["band"], len(ids)))
PY
  rm -f "$out"
  step "live: --fail-under gates"
  python3 cli/geo_score.py example.com --fail-under 0 --quiet > /dev/null
  if python3 cli/geo_score.py example.com --fail-under 101 --quiet > /dev/null 2>&1; then
    echo "--fail-under 101 should have failed"; exit 1
  fi
  echo "ok: 0 passes, 101 fails"
fi

printf '\nall checks passed\n'
