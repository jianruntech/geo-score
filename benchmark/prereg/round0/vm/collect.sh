#!/usr/bin/env bash
# Round 0, collection (benchmark/PREREGISTRATION.md section 7 and the amendment of 2026-10-12): run the frozen watch
# configs of one day's categories, 10 questions x 2 engines x 8 asks each.
#
#   bash collect.sh DATA_TAG DAY [WAVE] [WORKDIR]
#
# DATA_TAG  the release that contains the frozen sample (benchmark/prereg/round0/sample.json and sample/)
# DAY       1, 2 or 3: the categories sample.json schedules for that day (6 a day, so Gemini's free tier, about 500
#           grounded answers a day, holds the day's 480); run the three days on consecutive days, all within 3 days
# WAVE      0 (default) or 1
#
# The environment must hold, and nothing here prints them:
#   OPENAI_COMPAT_BASE_URL   the OpenAI-compatible endpoint: its Responses URL, or its /v1 root (/responses is added)
#   OPENAI_COMPAT_API_KEY    its key
#   OPENAI_COMPAT_MODEL      its model id; must equal the one frozen in sample.json
#   GEMINI_API_KEY           Gemini's key
#
# The CLI is the frozen one, cloned at the tag sample.json records (cli_tag), and every watch command goes through
# watch_run.py, which retries HTTP 429 and 5xx answers with backoff. Each category runs in a working copy of its frozen
# config outside the repository, with the endpoint put in place of the placeholder; the run file is copied to
# benchmark/prereg/round0/runs/wave<WAVE>/<category>/ in the data clone, with the endpoint's host replaced by
# "<openai-compatible endpoint>" wherever an error message carried it. When an engine stopped in a category's run
# (`engine_failed`), that engine alone is run once more the same day; the analysis reads each engine from its newest
# run that did not stop. Every run is logged in collection/wave<WAVE>/log.tsv. Run from a VM in the US: Gemini
# takes no location parameter, so its answers follow where the request comes from.
#
# DRY_RUN=1 prints each category's plan (`watch run --dry-run`) and calls nothing: a check of the keys' presence, the
# clones, the frozen model and the configs before the first day.
set -euo pipefail
DRY_RUN="${DRY_RUN:-0}"

DATA_TAG="${1:?usage: bash collect.sh DATA_TAG DAY [WAVE] [WORKDIR]}"
DAY="${2:?usage: bash collect.sh DATA_TAG DAY [WAVE] [WORKDIR]}"
WAVE="${3:-0}"
WORK="${4:-$HOME/prereg-round0}"
REPO="${GEO_SCORE_REPO:-https://github.com/jianruntech/geo-score}"
GEMINI_DAILY_CAP="${GEMINI_DAILY_CAP:-500}"

for v in OPENAI_COMPAT_BASE_URL OPENAI_COMPAT_API_KEY OPENAI_COMPAT_MODEL GEMINI_API_KEY; do
  if [ -z "${!v:-}" ]; then echo "error: set $v in the environment (its value is never printed)" >&2; exit 1; fi
done
case "$DAY" in 1|2|3) ;; *) echo "error: DAY is 1, 2 or 3" >&2; exit 1 ;; esac

mkdir -p "$WORK"
DATA="$WORK/geo-score-$DATA_TAG"
[ -d "$DATA/.git" ] || git -c advice.detachedHead=false clone --quiet --branch "$DATA_TAG" --depth 1 "$REPO" "$DATA"
ROUND="$DATA/benchmark/prereg/round0"
[ -f "$ROUND/sample.json" ] || { echo "error: $DATA_TAG has no frozen sample (sample.json)" >&2; exit 1; }

read -r CLI_TAG CLI_VERSION FROZEN_MODEL < <(python3 - "$ROUND/sample.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
m = [e["model"] for e in d["engines"] if e["provider"] == "openai"][0]
print(d["cli_tag"], d["cli_version"], m)
PY
)
if [ "$OPENAI_COMPAT_MODEL" != "$FROZEN_MODEL" ]; then
  echo "error: OPENAI_COMPAT_MODEL differs from the model frozen in sample.json; a change needs an amendment" >&2
  exit 1
fi
CLI="$WORK/geo-score-$CLI_TAG"
[ -d "$CLI/.git" ] || git -c advice.detachedHead=false clone --quiet --branch "$CLI_TAG" --depth 1 "$REPO" "$CLI"
got=$(python3 "$CLI/cli/geo_score.py" --version | awk '{print $2}')
[ "$got" = "$CLI_VERSION" ] || { echo "error: the CLI at $CLI_TAG is $got, the frozen one is $CLI_VERSION" >&2; exit 1; }

# the endpoint: a Responses URL as given, or a /v1 root with /responses added
ENDPOINT="${OPENAI_COMPAT_BASE_URL%/}"
case "$ENDPOINT" in
  */responses) ;;
  */v1) ENDPOINT="$ENDPOINT/responses" ;;
  *) echo "error: OPENAI_COMPAT_BASE_URL must end in /v1 or /responses" >&2; exit 1 ;;
esac
export ROUND0_ENDPOINT="$ENDPOINT"

CATS=()
while IFS= read -r line; do [ -n "$line" ] && CATS+=("$line"); done < <(python3 - "$ROUND/sample.json" "$DAY" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
days = d["collection_schedule"]["days"]
k = int(sys.argv[2])
print("\n".join(days[k - 1] if k <= len(days) else []))
PY
)
[ "${#CATS[@]}" -gt 0 ] || { echo "nothing scheduled for day $DAY"; exit 0; }

LOGDIR="$ROUND/collection/wave$WAVE"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/log.tsv"
[ -f "$LOG" ] || printf 'category\trun_id\tengine\tmodel\tstatus\tstopped\tanswered\tplanned\terrors\tstarted\tfinished\n' > "$LOG"
RUNNER=("python3" "$ROUND/vm/watch_run.py" "--cli" "$CLI/cli/geo_watch.py" "--")

# one question, outside the frozen set, to each engine: is it answering, citing, and placing its citations?
preflight() {
  local rt="$WORK/runtime/preflight"
  mkdir -p "$rt"
  make_config "${CATS[0]}" "$rt"
  "${RUNNER[@]}" ask "Which public libraries in the US lend e-books?" -c "$rt/geo-score-watch.json" --format json \
    > "$rt/ask.json" 2> "$rt/ask.err" || true
  python3 - "$rt/ask.json" <<'PY'
import json, sys
try:
    run = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    sys.exit("preflight: no answer came back; see the .err file next to it")
for s in run["samples"]:
    print("preflight %-7s %-6s citations %2d  spans %s  search queries %d" % (
        s["engine"], s["status"], len(s.get("citations") or []), "yes" if s.get("spans") else "no",
        len(s.get("search_queries") or [])))
PY
}

# the frozen config of one category, in a working copy, with the endpoint in place of the placeholder
make_config() {
  local cat="$1" dir="$2"
  mkdir -p "$dir"
  cp "$ROUND/sample/$cat/queries.csv" "$dir/queries.csv"
  python3 - "$ROUND/sample/$cat/geo-score-watch.json" "$dir/geo-score-watch.json" <<'PY'
import json, os, sys
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
for e in cfg["engines"]:
    if e["provider"] == "openai":
        e["base_url"] = os.environ["ROUND0_ENDPOINT"]
json.dump(cfg, open(sys.argv[2], "w", encoding="utf-8"), indent=2)
PY
}

# copy a category's new run files into the round, the endpoint's host scrubbed, and log them
harvest() {
  local cat="$1" rt="$2" dest="$ROUND/runs/wave$WAVE/$1"
  mkdir -p "$dest"
  python3 - "$rt/.geo-score/watch/runs" "$dest" "$cat" "$LOG" <<'PY'
import glob, json, os, sys, urllib.parse
src, dest, cat, log = sys.argv[1:5]
host = urllib.parse.urlsplit(os.environ["ROUND0_ENDPOINT"]).netloc
for p in sorted(glob.glob(os.path.join(src, "*.json"))):
    out = os.path.join(dest, os.path.basename(p))
    if os.path.exists(out):
        continue
    text = open(p, encoding="utf-8").read()
    if host and host in text:
        text = text.replace(host, "<openai-compatible endpoint>")
    open(out, "w", encoding="utf-8").write(text)
    run = json.loads(text)
    with open(log, "a", encoding="utf-8") as f:
        for e in run["engines"]:
            rows = [s for s in run["samples"] if s["engine"] == e["id"]]
            f.write("\t".join(str(x) for x in (cat, run["run_id"], e["id"], e["model"], e["status"], e.get("stopped", ""),
                    sum(1 for s in rows if s["status"] == "ok"), len(rows),
                    sum(1 for s in rows if s["status"] == "error"), run["started_at"], run["finished_at"])) + "\n")
        print("%s %s: %s" % (cat, run["run_id"], ", ".join("%s %d/%d%s" % (
            e["id"], sum(1 for s in run["samples"] if s["engine"] == e["id"] and s["status"] == "ok"),
            sum(1 for s in run["samples"] if s["engine"] == e["id"]), " STOPPED" if e.get("stopped") else "")
            for e in run["engines"])))
PY
}

# Gemini answers asked today (UTC), from the round's run files: the free tier's daily quota is shared
gemini_today() {
  python3 - "$ROUND/runs" <<'PY'
import datetime, glob, json, os, sys
today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
n = 0
for p in glob.glob(os.path.join(sys.argv[1], "wave*", "*", "*.json")):
    run = json.load(open(p, encoding="utf-8"))
    if run["started_at"].startswith(today):
        n += sum(1 for s in run["samples"] if s["engine"] == "gemini" and s["status"] != "skipped")
print(n)
PY
}

stopped_engines() {
  python3 - "$ROUND/runs/wave$WAVE/$1" <<'PY'
import glob, json, os, sys
files = sorted(glob.glob(os.path.join(sys.argv[1], "*.json")))
best = {}
for p in files:
    run = json.load(open(p, encoding="utf-8"))
    for e in run["engines"]:
        ok = e["status"] == "measured" and not e.get("stopped") and not run.get("interrupted")
        best[e["id"]] = best.get(e["id"], False) or ok
print(" ".join(sorted(k for k, ok in best.items() if not ok)))
PY
}

echo "wave $WAVE, day $DAY: ${CATS[*]}"
echo "CLI $CLI_VERSION ($CLI_TAG); models: OpenAI-compatible $FROZEN_MODEL, gemini-2.5-flash"
if [ "$DRY_RUN" = 1 ]; then
  for cat in "${CATS[@]}"; do
    rt="$WORK/runtime/dry/$cat"
    rm -rf "$rt"
    make_config "$cat" "$rt"
    echo "== $cat"
    "${RUNNER[@]}" run -c "$rt/geo-score-watch.json" --dry-run
  done
  exit 0
fi
[ "$DAY" = 1 ] && preflight
for cat in "${CATS[@]}"; do
  if [ -n "$(ls "$ROUND/runs/wave$WAVE/$cat/"*.json 2>/dev/null)" ]; then
    echo "$cat: already has a run in wave $WAVE; skipped (the analysis reads the files there)"
    continue
  fi
  used=$(gemini_today)
  if [ $((used + 80)) -gt "$GEMINI_DAILY_CAP" ]; then
    echo "$cat: Gemini has asked $used questions today; 80 more would pass $GEMINI_DAILY_CAP. Stopping for today." >&2
    break
  fi
  rt="$WORK/runtime/wave$WAVE/$cat"
  rm -rf "$rt"
  make_config "$cat" "$rt"
  echo "$cat: started $(date -u +%H:%M:%SZ)"
  "${RUNNER[@]}" run -c "$rt/geo-score-watch.json" --quiet > "$rt/run.out" 2> "$rt/run.err" || true
  harvest "$cat" "$rt"
  for eng in $(stopped_engines "$cat"); do
    used=$(gemini_today)
    if [ "$eng" = gemini ] && [ $((used + 80)) -gt "$GEMINI_DAILY_CAP" ]; then
      echo "$cat: $eng stopped; not run again today, the Gemini quota is used up (reported missing if not rerun in the window)" >&2
      continue
    fi
    echo "$cat: $eng stopped; running it once more"
    "${RUNNER[@]}" run -c "$rt/geo-score-watch.json" --engines "$eng" --quiet > "$rt/rerun.out" 2> "$rt/rerun.err" || true
    harvest "$cat" "$rt"
  done
done
echo "day $DAY done $(date -u +%Y-%m-%dT%H:%M:%SZ). Run files: $ROUND/runs/wave$WAVE/; log: $LOG"
echo "copy back: tar czf round0-wave$WAVE-day$DAY.tgz -C $DATA benchmark/prereg/round0/runs benchmark/prereg/round0/collection"
