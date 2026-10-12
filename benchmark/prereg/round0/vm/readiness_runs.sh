#!/usr/bin/env bash
# Round 0, readiness (benchmark/PREREGISTRATION.md section 6): score every sampled site once more with the frozen CLI.
# Each wave has two such runs per site, on different days and within 7 days of each other, inside the wave's window.
#
#   bash readiness_runs.sh DATA_TAG RUN [WAVE] [WORKDIR]
#
# DATA_TAG  the release that contains the frozen sample (benchmark/prereg/round0/sample.json)
# RUN       1 or 2. Run 2 refuses to start on the UTC day run 1 started, and warns when run 1 started more than 6 days
#           before (the two runs of a site must fall within 7 days)
# WAVE      0 (default) or 1
#
# The CLI is the frozen one: cloned at the tag sample.json records, and checked against the version it records. Each
# site is scored at the URL its sampling run scored, one site at a time, 30 seconds apart; the report, or the CLI's
# error when it could not score the site, goes to benchmark/prereg/round0/readiness/wave<WAVE>/run<RUN>/<site>.json in
# the data clone. Resumable: a site that already has a file in this run is not scored again. No API key is needed.
set -euo pipefail

DATA_TAG="${1:?usage: bash readiness_runs.sh DATA_TAG RUN [WAVE] [WORKDIR]}"
RUN="${2:?usage: bash readiness_runs.sh DATA_TAG RUN [WAVE] [WORKDIR]}"
WAVE="${3:-0}"
WORK="${4:-$HOME/prereg-round0}"
REPO="${GEO_SCORE_REPO:-https://github.com/jianruntech/geo-score}"
PAUSE="${PAUSE:-30}"
case "$RUN" in 1|2) ;; *) echo "error: RUN is 1 or 2" >&2; exit 1 ;; esac

mkdir -p "$WORK"
DATA="$WORK/geo-score-$DATA_TAG"
[ -d "$DATA/.git" ] || git -c advice.detachedHead=false clone --quiet --branch "$DATA_TAG" --depth 1 "$REPO" "$DATA"
ROUND="$DATA/benchmark/prereg/round0"
[ -f "$ROUND/sample.json" ] || { echo "error: $DATA_TAG has no frozen sample (sample.json)" >&2; exit 1; }
read -r CLI_TAG CLI_VERSION < <(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["cli_tag"], d["cli_version"])' "$ROUND/sample.json")
CLI="$WORK/geo-score-$CLI_TAG"
[ -d "$CLI/.git" ] || git -c advice.detachedHead=false clone --quiet --branch "$CLI_TAG" --depth 1 "$REPO" "$CLI"
got=$(python3 "$CLI/cli/geo_score.py" --version | awk '{print $2}')
[ "$got" = "$CLI_VERSION" ] || { echo "error: the CLI at $CLI_TAG is $got, the frozen one is $CLI_VERSION" >&2; exit 1; }

OUT="$ROUND/readiness/wave$WAVE/run$RUN"
mkdir -p "$OUT"
FIRST="$ROUND/readiness/wave$WAVE/run1/started.txt"
today=$(date -u +%Y-%m-%d)
if [ "$RUN" = 2 ]; then
  [ -f "$FIRST" ] || { echo "error: run 1 of wave $WAVE has not started" >&2; exit 1; }
  first_day=$(cut -c1-10 "$FIRST")
  if [ "$first_day" = "$today" ]; then
    echo "error: run 1 started today ($today, UTC); the two runs must fall on different days" >&2; exit 1
  fi
  gap=$(( ( $(date -u -d "$today" +%s) - $(date -u -d "$first_day" +%s) ) / 86400 ))
  [ "$gap" -le 6 ] || echo "warning: run 1 started $gap days ago; the two runs of a site must fall within 7 days" >&2
fi
[ -f "$OUT/started.txt" ] || date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/started.txt"
python3 "$CLI/cli/geo_score.py" --version > "$OUT/cli.txt"

# every sampled site once, at the URL its sampling run scored
ROWS=()
while IFS= read -r line; do [ -n "$line" ] && ROWS+=("$line"); done < <(python3 - "$ROUND/sample.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
seen = {}
for c in d["categories"]:
    for s in c["sites"]:
        seen.setdefault(s["site"], s.get("sampling_url") or "https://" + s["site"])
for site, url in sorted(seen.items()):
    print(site, url)
PY
)
LOG="$OUT/log.tsv"
[ -f "$LOG" ] || printf 'site\turl\texit\tstarted\tfinished\n' > "$LOG"
n=0
for row in "${ROWS[@]}"; do
  site="${row%% *}"; url="${row#* }"; n=$((n + 1))
  [ -f "$OUT/$site.json" ] && continue
  started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  set +e
  python3 "$CLI/cli/geo_score.py" "$url" --quiet --json --json-out "$OUT/.$site.report" > "$OUT/.$site.stdout" 2> /dev/null
  rc=$?
  set -e
  if [ "$rc" = 0 ] && [ -s "$OUT/.$site.report" ]; then mv "$OUT/.$site.report" "$OUT/$site.json"
  else mv "$OUT/.$site.stdout" "$OUT/$site.json"; fi           # the CLI's error JSON: no X from this run
  rm -f "$OUT/.$site.report" "$OUT/.$site.stdout"
  printf '%s\t%s\t%s\t%s\t%s\n' "$site" "$url" "$rc" "$started" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
  echo "[$n/${#ROWS[@]}] $site exit $rc"
  sleep "$PAUSE"
done
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/finished.txt"
echo "run $RUN of wave $WAVE done: $OUT"
echo "copy back: tar czf round0-readiness-wave$WAVE-run$RUN.tgz -C $DATA benchmark/prereg/round0/readiness"
