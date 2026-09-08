# Running geo-score in CI

## GitHub Actions

Copy [`github-actions.yml`](github-actions.yml) into `.github/workflows/` and change the
`url`. It scores on every push to `main` and once a week, writes a scored table to the
job summary, and uploads the JSON report as an artifact.

`fail-under` is optional. Leave it out while you are establishing a baseline; add it
once you know your number, so a regression fails the build instead of going unnoticed.

## Anything else

The CLI is a single file with no dependencies and a machine-readable mode, so any CI
works:

```bash
curl -sLO https://raw.githubusercontent.com/jianruntech/geo-score/main/cli/geo_score.py
python3 geo_score.py "$SITE_URL" --json --quiet > geo-score.json
python3 geo_score.py "$SITE_URL" --fail-under 40 --quiet
```

Exit code is 1 when the score is below `--fail-under`, 0 otherwise.

## Tracking the score over time

The report includes `rubric_version`, so scores stay comparable as long as that value
does not change. When it does, re-baseline — scores from different rubric versions are
not comparable, and averaging them produces a number that means nothing.

```bash
python3 geo_score.py "$SITE_URL" --json --quiet \
  | python3 -c 'import json,sys,datetime as d; r=json.load(sys.stdin); \
print(d.date.today(), r["rubric_version"], r["normalised"], r["band"], sep="\t")' \
  >> history.tsv
```
