#!/usr/bin/env bash
# Round 0, the sampling run (benchmark/PREREGISTRATION.md section 5.2): score every remaining candidate once with the
# frozen CLI, one site at a time, 30 seconds apart, on a fresh Ubuntu VM.
#
#   bash score_candidates.sh TAG [WORKDIR]
#
# TAG is the release that contains round 0's frozen questions (candidates.json); its CLI is the frozen CLI. The
# repository is cloned at TAG into WORKDIR (default ~/prereg-round0). Each remaining candidate's site is scored once
# at https://SITE, and once more at https://www.SITE only when the first try fails with anything but a bot challenge
# (as benchmark/run.py does). Reports go to benchmark/prereg/round0/sampling/ in the clone:
#   reports/SITE.json   the CLI's report (--json-out), when it scored the site
#   errors/SITE.json    the CLI's error (--json on exit 2), when it could not
#   log.tsv             one line per attempt: site, url, exit code, error kind, start and end (UTC)
#   cli.txt             the CLI version, the tag and the commit
# The script is resumable: a site with a line in log.tsv that ended in a report or a final error is not scored again.
# Long: about 270 sites at 30 to 90 seconds each. Run it under nohup or tmux; nothing here needs an API key.
set -euo pipefail

TAG="${1:?usage: bash score_candidates.sh TAG [WORKDIR]}"
WORK="${2:-$HOME/prereg-round0}"
REPO="${GEO_SCORE_REPO:-https://github.com/jianruntech/geo-score}"
PAUSE="${PAUSE:-30}"

command -v git >/dev/null || { echo "install git first (sudo apt-get install -y git)"; exit 1; }
command -v python3 >/dev/null || { echo "install python3 first"; exit 1; }
mkdir -p "$WORK"
SRC="$WORK/geo-score-$TAG"
if [ ! -d "$SRC/.git" ]; then
  git -c advice.detachedHead=false clone --quiet --branch "$TAG" --depth 1 "$REPO" "$SRC"
fi
cd "$SRC"
ROUND=benchmark/prereg/round0
OUT="$ROUND/sampling"
mkdir -p "$OUT/reports" "$OUT/errors" "$OUT/stderr"

{
  python3 cli/geo_score.py --version
  echo "tag $TAG"
  echo "commit $(git rev-parse HEAD)"
  echo "python $(python3 -c 'import sys; print(sys.version.split()[0])')"
  echo "host $(uname -srm)"
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/cli.txt.new"
if [ -f "$OUT/cli.txt" ] && ! cmp -s <(head -3 "$OUT/cli.txt") <(head -3 "$OUT/cli.txt.new"); then
  echo "error: $OUT/cli.txt records another CLI or commit; a sampling run uses one CLI" >&2
  rm -f "$OUT/cli.txt.new"; exit 1
fi
[ -f "$OUT/cli.txt" ] || mv "$OUT/cli.txt.new" "$OUT/cli.txt"
rm -f "$OUT/cli.txt.new"

# every remaining candidate's site, once (a site in two categories is scored once)
python3 - "$ROUND/candidates.json" > "$OUT/sites.txt" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("\n".join(sorted({v["site"] for c in d["categories"] for v in c["candidates"] if v["status"] == "remaining"})))
PY

LOG="$OUT/log.tsv"
[ -f "$LOG" ] || printf 'site\turl\texit\tkind\tstarted\tfinished\n' > "$LOG"
total=$(grep -c . "$OUT/sites.txt")
n=0
while IFS= read -r site; do
  n=$((n + 1))
  if [ -f "$OUT/reports/$site.json" ] || [ -f "$OUT/errors/$site.json" ]; then
    continue
  fi
  urls=("https://$site")
  case "$site" in www.*) ;; *) urls+=("https://www.$site") ;; esac
  for url in "${urls[@]}"; do
    started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    tmp="$OUT/errors/.$site.json.tmp"
    set +e
    python3 cli/geo_score.py "$url" --quiet --json --json-out "$OUT/reports/.$site.json.tmp" > "$tmp" 2> "$OUT/stderr/$site.txt"
    rc=$?
    set -e
    finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    kind=""
    if [ "$rc" = 0 ] && [ -s "$OUT/reports/.$site.json.tmp" ]; then
      mv "$OUT/reports/.$site.json.tmp" "$OUT/reports/$site.json"
      rm -f "$tmp"
    else
      rm -f "$OUT/reports/.$site.json.tmp"
      kind=$(python3 -c 'import json,sys
try: print((json.load(open(sys.argv[1])).get("error") or {}).get("kind") or "unknown")
except Exception: print("unknown")' "$tmp")
    fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$site" "$url" "$rc" "$kind" "$started" "$finished" >> "$LOG"
    echo "[$n/$total] $site $url exit $rc ${kind:+($kind)}"
    if [ -f "$OUT/reports/$site.json" ]; then
      break
    fi
    if [ "$kind" = "bot_challenge" ] || [ "$url" = "${urls[${#urls[@]}-1]}" ]; then
      mv "$tmp" "$OUT/errors/$site.json"     # the last attempt's error is the site's
      break
    fi
    sleep 5
  done
  rm -f "$OUT/errors/.$site.json.tmp"
  sleep "$PAUSE"
done < "$OUT/sites.txt"

echo "finished $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT/cli.txt"
scored=$(find "$OUT/reports" -name '*.json' ! -name '.*' | wc -l)
failed=$(find "$OUT/errors" -name '*.json' ! -name '.*' | wc -l)
echo "done: $scored scored, $failed could not be scored, of $total sites"
echo "next, in $SRC:  OPENAI_COMPAT_MODEL=... python3 $ROUND/vm/draw.py"
