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
works. Download the CLI and the checksums from a pinned release, check the file, then score once:

```bash
rel=https://github.com/jianruntech/geo-score/releases/download/v1.4.0
curl -sSfLO "$rel/geo_score.py"
curl -sSfLO "$rel/SHA256SUMS"
grep ' geo_score\.py$' SHA256SUMS > geo_score.py.sha256 && sha256sum -c geo_score.py.sha256 &&
python3 geo_score.py "$SITE_URL" --quiet --json-out geo-score.json --junit geo-score.xml --fail-under 40
```

The `&&` chain is what keeps an unchecked file from running. Some CI shells, Azure Pipelines' script
step among them, do not stop at a failed command, so a check on a line of its own would print `FAILED`
and score anyway. The line goes to its own file rather than through a pipe because some `sha256sum`
builds (macOS) pass empty input. On a machine without `sha256sum`, `shasum -a 256 -c geo_score.py.sha256`
reads the same file.

One run writes the report, writes the test file and applies the threshold. Two runs fetch the site
twice and can print two different scores, so the report you keep would not be the run that passed or
failed the build. Exit code is 1 when the score is below `--fail-under`, 2 when the site could not be
fetched, and 0 otherwise; a file that does not match `SHA256SUMS` stops the step before scoring.

### GitLab CI

[`gitlab-ci.yml`](gitlab-ci.yml) is the same download, check and single run as a GitLab job on
`python:3.12-slim`. It runs on schedules and on pushes to the default branch, keeps `geo-score.json` as
an artifact, and hands `geo-score.xml` to GitLab as a JUnit report. Each check is a test case, so a
check at zero shows as a failed test in the pipeline's Tests tab, and in the merge request widget when
you also run the job in merge request pipelines (the file has the rule to uncomment).

### Other CIs

`--junit` writes one test case per check, a check at zero as a failure and a check the CLI cannot
observe as skipped. Each of these CIs needs one directive to show it:

| CI | What picks up `geo-score.xml` |
|---|---|
| Bitbucket Pipelines | Write it into a `test-results/` directory (`--junit test-results/geo-score.xml`); Pipelines reads that directory by itself |
| Azure Pipelines | A `PublishTestResults@2` task with `testResultsFormat: JUnit`, `testResultsFiles: geo-score.xml` and `condition: succeededOrFailed()` |
| Jenkins | The `junit` step, `junit 'geo-score.xml'`, in a `post { always { … } }` block |
| CircleCI | A `store_test_results` step whose `path` is the file or the directory that holds it |

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
