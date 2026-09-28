#!/usr/bin/env bash
# The gate every change passes before it merges.
#
#   bash scripts/check.sh           # offline: structure, generated MCP docs, lint, unit + end-to-end tests,
#                                   # the Action, the packaging manifests and the .mcpb, and every other
#                                   # scripts/test_*.py and benchmark/test_*.py
#   bash scripts/check.sh --live    # also score example.com, check the JSON and --fail-under, run the
#                                   # MCP server through the official Inspector CLI, and check the labels
#   bash scripts/check.sh --all     # run the tests on every Python from 3.8 to 3.14 (and 3.15 when installed)
#   bash scripts/check.sh --strict  # fail, instead of skipping, when uv cannot find a Python the run needs
#
# The flags combine: release.py --execute runs --live --strict.
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
# The CLI promises Python 3.8+ (requires-python). By default the tests run on the oldest and the newest stable
# Python, plus 3.12 (the Docker image's) when uv finds it; pyproject.toml has a classifier for every minor in
# between, and scripts/test_packaging.py checks that against these two lines.
PY_OLDEST=3.8
PY_NEWEST=3.14
LIVE=0 ALL=0 STRICT=0
for arg in "$@"; do
  case "$arg" in
    --live) LIVE=1 ;;
    --all) ALL=1 ;;
    --strict) STRICT=1 ;;
    *) echo "usage: bash scripts/check.sh [--live] [--all] [--strict]" >&2; exit 2 ;;
  esac
done

step() { printf '\n== %s\n' "$*"; }

# Which Pythons the tests run on, decided first so that --strict stops before anything else runs.
# NEED must be found (under --strict); WANT is tried and skipped with a note when it is missing.
if [ "$ALL" = 1 ]; then
  NEED="" m=${PY_OLDEST#3.}
  while [ "$m" -le "${PY_NEWEST#3.}" ]; do NEED="${NEED:+$NEED }3.$m"; m=$((m + 1)); done
  WANT="$NEED 3.$m"
else
  NEED="$PY_OLDEST $PY_NEWEST" WANT="$PY_OLDEST 3.12 $PY_NEWEST"
fi
needed() { case " $NEED " in *" $1 "*) return 0 ;; esac; return 1; }
PYS=()
if command -v uv >/dev/null 2>&1; then
  step "interpreters: $WANT (uv python find)"
  missing=""
  for v in $WANT; do
    p="$(uv python find --no-project "$v" 2>/dev/null || true)"
    if [ -n "$p" ]; then PYS+=("$p"); echo "python $v: $p"
    elif [ "$STRICT" = 1 ] && needed "$v"; then missing="$missing $v"
    else echo "python $v not found by uv: skipped (uv python install $v)"; fi
  done
  if [ -n "$missing" ]; then
    for v in $missing; do echo "python $v not found by uv, and --strict needs it: uv python install $v"; done
    exit 1
  fi
elif [ "$STRICT" = 1 ]; then
  echo "--strict needs uv to find each Python (https://docs.astral.sh/uv/)"; exit 1
fi
# without uv, test whatever python3 is
[ ${#PYS[@]} -gt 0 ] || PYS=("python3")

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

for py in "${PYS[@]}"; do
  step "tests on $("$py" -c 'import sys; print("python %d.%d" % sys.version_info[:2])')"
  "$py" cli/test_geo_score.py
  "$py" cli/test_geo_watch.py
  "$py" cli/test_geo_score_e2e.py
  "$py" scripts/check_mcp.py "$py"
done

# the end-to-end suite validates every report against schema/report.v2.json when jsonschema is importable;
# SCHEMA_PY is the Python that has it (the --live report check below uses it too)
JS="jsonschema==$JSONSCHEMA_VERSION" SCHEMA_PY=""
if command -v uv >/dev/null 2>&1 && uv run --no-project --with "$JS" python -c "import jsonschema" >/dev/null 2>&1; then
  SCHEMA_PY="uv run --no-project --with $JS python" SCHEMA_WITH="jsonschema $JSONSCHEMA_VERSION via uv"
elif have="$(python3 -c 'import importlib.metadata as m; print(m.version("jsonschema"))' 2>/dev/null)"; then
  SCHEMA_PY="python3" SCHEMA_WITH="jsonschema $have"
  [ "$have" = "$JSONSCHEMA_VERSION" ] || SCHEMA_WITH="$SCHEMA_WITH, not the pinned $JSONSCHEMA_VERSION"
fi
if [ -n "$SCHEMA_PY" ]; then
  step "reports against the published schema ($SCHEMA_WITH)"; $SCHEMA_PY cli/test_geo_score_e2e.py
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
  ${SCHEMA_PY:-python3} - "$out" <<'PY'
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
