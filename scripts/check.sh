#!/usr/bin/env bash
# The gate every change passes before it merges.
#
#   bash scripts/check.sh           # offline: structure, generated MCP docs, lint, unit + end-to-end tests,
#                                   # the Action, the packaging manifests and the .mcpb, and every other
#                                   # scripts/test_*.py and benchmark/test_*.py
#   bash scripts/check.sh --live    # also score example.com, check the JSON and --fail-under, run the
#                                   # MCP server through the official Inspector CLI, and, when gh is logged
#                                   # in, check that .github/labels.json's labels exist on GitHub
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
# the PATH ruff runs when it is the pinned one; otherwise uvx runs the pinned ruff, from uv's cache when it is
# there (--offline never waits on a network that drops packets) and fetched only when it is not; when it can do
# neither (offline, cold cache) the gate falls back to the PATH ruff, as it did before the pin, while lint
# findings from either ruff still fail it
uvx_ruff=""
if [ "$path_ruff" != "ruff $RUFF_VERSION" ] && command -v uvx >/dev/null 2>&1; then
  if uvx --offline "ruff@$RUFF_VERSION" --version >/dev/null 2>&1; then uvx_ruff="uvx --offline ruff@$RUFF_VERSION"
  elif uvx "ruff@$RUFF_VERSION" --version >/dev/null 2>&1; then uvx_ruff="uvx ruff@$RUFF_VERSION"; fi
fi
if [ "$path_ruff" = "ruff $RUFF_VERSION" ]; then
  echo "using $path_ruff from PATH"; ruff check $LINT
elif [ -n "$uvx_ruff" ]; then
  echo "using $uvx_ruff${path_ruff:+ (PATH has $path_ruff)}"; $uvx_ruff check $LINT
elif [ -n "$path_ruff" ]; then
  echo "warning: $path_ruff is not the pinned $RUFF_VERSION, and uvx is missing or could not fetch it (offline?);" \
    "its rules may differ"
  ruff check $LINT
else echo "ruff $RUFF_VERSION unavailable (no ruff, and no uvx that can fetch it): skipped (pip install ruff==$RUFF_VERSION)"; fi

for py in "${PYS[@]}"; do
  step "tests on $("$py" -c 'import sys; print("python %d.%d" % sys.version_info[:2])')"
  "$py" cli/test_geo_score.py
  "$py" cli/test_geo_watch.py
  "$py" cli/test_geo_score_e2e.py
  "$py" scripts/check_mcp.py "$py"
done

# the end-to-end suite validates every report against schema/report.v2.json when jsonschema is importable;
# SCHEMA_PY is the Python that has it (the --live report check below uses it too). The pinned jsonschema comes
# from python3 when it has that version, else from uv's cache, and only then from the network, so a warm machine
# never waits on one; failing all three, python3's own jsonschema is used, as it was before the pin
JS="jsonschema==$JSONSCHEMA_VERSION" SCHEMA_PY="" SCHEMA_WITH=""
have="$(python3 -c 'import importlib.metadata as m; print(m.version("jsonschema"))' 2>/dev/null || true)"
if [ "$have" = "$JSONSCHEMA_VERSION" ]; then
  SCHEMA_PY="python3" SCHEMA_WITH="jsonschema $have"
elif command -v uv >/dev/null 2>&1 && uv run --offline --no-project --with "$JS" python -c "import jsonschema" >/dev/null 2>&1; then
  SCHEMA_PY="uv run --offline --no-project --with $JS python" SCHEMA_WITH="jsonschema $JSONSCHEMA_VERSION via uv, cached"
elif command -v uv >/dev/null 2>&1 && uv run --no-project --with "$JS" python -c "import jsonschema" >/dev/null 2>&1; then
  SCHEMA_PY="uv run --no-project --with $JS python" SCHEMA_WITH="jsonschema $JSONSCHEMA_VERSION via uv"
elif [ -n "$have" ]; then
  SCHEMA_PY="python3" SCHEMA_WITH="jsonschema $have, not the pinned $JSONSCHEMA_VERSION"
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
  # labels are repository settings, not code: without gh credentials (a fresh machine, the workflow, which
  # has no token) the step is skipped; logged in, a missing label stops the gate until someone creates it
  if [ -f scripts/sync_labels.py ]; then
    step "live: the repository's issue labels (sync_labels.py --check)"
    if ! command -v gh >/dev/null 2>&1; then echo "gh not installed: skipped (https://cli.github.com)"
    elif ! gh auth status >/dev/null 2>&1; then echo "gh not authenticated: skipped (gh auth login)"
    else python3 scripts/sync_labels.py --check || {
      echo "labels: python3 scripts/sync_labels.py --apply creates any that are missing (RELEASING.md, step 5)"; exit 1; }
    fi
  fi
fi

printf '\nall checks passed\n'
