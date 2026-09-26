# Running geo-score in CI

## GitHub Actions

Copy [`github-actions.yml`](github-actions.yml) into `.github/workflows/` and change the
`url`. It scores on every push to `main` and once a week, writes a scored table to the
job summary, annotates the checks at zero, uploads the JSON report as an artifact, and sends
the SARIF file to code scanning, so each check at zero shows up as an alert in the Security tab
and closes by itself once the check passes. Drop the `sarif` input and the `upload-sarif` step if
you do not use code scanning; for a test-report tool, use the `junit` input instead.

`fail-under` is optional. Leave it out while you are establishing a baseline; add it
once you know your number, so a regression fails the build instead of going unnoticed.

## Weekly citation tracking (level 3)

[`watch-weekly.yml`](watch-weekly.yml) runs `geo_score.py watch` every Monday with API keys from
repository secrets, writes the Markdown report and the comparison with last week to the job
summary, and commits each run file back, so the history lives in git. Set up the config and the
question list first with `python3 geo_score.py watch init --dir geo-score --brand … --domain …`
(see [cli/README.md](../../cli/README.md#watch)), and set at least one API key secret; with no key
the job exits 3 and records nothing. **Run files contain your questions and the full AI answers:
use a private repository, or replace the commit step with `actions/upload-artifact`.**

## Anything else

Level 1 is a single file with no dependencies and a machine-readable mode, so any CI
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
