#!/usr/bin/env bash
# The gate every change passes before it merges.
#
#   bash scripts/check.sh           # offline: structure, generated MCP docs, lint, unit + end-to-end tests,
#                                   # the Action, the packaging manifests and the .mcpb, and every other
#                                   # scripts/test_*.py and benchmark/test_*.py
#   bash scripts/check.sh --live    # also score example.com, check the JSON and --fail-under, run the
#                                   # MCP server through the official Inspector CLI, and check the labels
#
# Hosted Actions have never run on this organisation, so this script is the CI: maintainers run it
# before every merge (the pre-push hook in .githooks does it for you), and .github/workflows/validate.yml
# runs the same script, so the two cannot drift if Actions is ever enabled.
set -euo pipefail
cd "$(dirname "$0")/.."
# The tools the gate pins, so an unchanged tree passes or fails the same way on every machine (a new ruff can
# add rules). jsonschema 4.23.0 is the newest release that still installs on Python 3.8, as validate.yml needs;
# the workflow pip-installs these same versions.
RUFF_VERSION=0.15.15
JSONSCHEMA_VERSION=4.23.0
LIVE=0
[ "${1:-}" = "--live" ] && LIVE=1

step() { printf '\n== %s\n' "$*"; }

step "structure: rubric, docs, schemas, generated pages (validate.py)"
python3 .github/validate.py

step "generated MCP docs: tool table and install links in README*/guide/mcp* (mcp_docs.py --check)"
python3 scripts/mcp_docs.py --check

step "lint: ruff $RUFF_VERSION (E9, F, B)"
LINT="cli benchmark .github action scripts"
path_ruff="$(command -v ruff >/dev/null 2>&1 && ruff --version 2>/dev/null || true)"
if [ "$path_ruff" = "ruff $RUFF_VERSION" ]; then
  echo "using $path_ruff from PATH"; ruff check $LINT
elif command -v uvx >/dev/null 2>&1; then
  echo "using uvx ruff@$RUFF_VERSION${path_ruff:+ (PATH has $path_ruff)}"; uvx "ruff@$RUFF_VERSION" check $LINT
elif [ -n "$path_ruff" ]; then
  echo "warning: $path_ruff is not the pinned $RUFF_VERSION and there is no uvx to fetch it; its rules may differ"
  ruff check $LINT
else echo "ruff not installed: skipped (pip install ruff==$RUFF_VERSION)"; fi

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
  "$py" scripts/check_mcp.py "$py"
done

# the end-to-end suite validates every report against schema/report.v2.json when jsonschema is importable
JS="jsonschema==$JSONSCHEMA_VERSION"
if command -v uv >/dev/null 2>&1 && uv run --no-project --with "$JS" python -c "import jsonschema" >/dev/null 2>&1; then
  step "reports against the published schema (jsonschema $JSONSCHEMA_VERSION via uv)"
  uv run --no-project --with "$JS" python cli/test_geo_score_e2e.py
elif have="$(python3 -c 'import importlib.metadata as m; print(m.version("jsonschema"))' 2>/dev/null)"; then
  step "reports against the published schema (jsonschema $have$([ "$have" = "$JSONSCHEMA_VERSION" ] || echo ", not the pinned $JSONSCHEMA_VERSION"))"
  python3 cli/test_geo_score_e2e.py
else
  echo "jsonschema unavailable: the full schema check was skipped (pip install $JS)"
fi

step "the GitHub Action, run as a runner would (scripts/test_action.py)"
python3 scripts/test_action.py

step "packaging: the manifests against the code; the .mcpb builds, starts and serves its tools (test_packaging.py)"
python3 scripts/test_packaging.py

# every other scripts/test_*.py and benchmark/test_*.py: a new suite joins the gate by its name alone
for t in scripts/test_*.py benchmark/test_*.py; do
  case "$t" in scripts/test_action.py|scripts/test_packaging.py) continue ;; esac
  [ -f "$t" ] || continue       # a pattern that matched nothing stays as written
  step "extra tests: $t"
  python3 "$t"
done

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
  step "live: the MCP server through the official Inspector CLI (check_mcp.py --inspector)"
  python3 scripts/check_mcp.py --inspector
  if [ -f scripts/sync_labels.py ]; then
    step "live: the repository's issue labels (sync_labels.py --check)"
    if command -v gh >/dev/null 2>&1; then python3 scripts/sync_labels.py --check
    else echo "gh not installed: skipped (https://cli.github.com)"; fi
  fi
fi

printf '\nall checks passed\n'
