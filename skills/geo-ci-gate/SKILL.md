---
name: geo-ci-gate
description: "Add a GitHub Actions workflow that scores the user's site with geo-score on every push to main, after each preview deployment, or on a schedule, and fails the build when an AI crawler gate drops to zero, the AI readiness score falls below a floor, or checks lose points against a committed baseline. Use when the user wants to catch deploys that lock AI crawlers out (a robots.txt edit, a firewall rule, a switch to client-side rendering), keep a GEO or AI visibility score from regressing, add an AI readiness check to CI or pull requests, or get a job summary and an artifact with the score. Free: no API key. Leaves .github/workflows/geo-score.yml in the repository. It detects regressions; it does not fix the site."
license: MIT
metadata:
  version: 1.9.0
  rubric: "v1.1"
  homepage: "https://github.com/jianruntech/geo-score"
---

# GEO CI gate

Writes one workflow file that runs the geo-score GitHub Action against the user's site. The Action scores the site
once, writes a table of every check to the job summary, annotates the checks at zero, and fails the job on the
conditions the user picks. It is detection: it tells the team that a deploy changed what AI crawlers get, and it
changes nothing on the site.

## When to use

- "Fail our deploy pipeline if robots.txt or the firewall starts blocking AI crawlers."
- "Add an AI readiness check to CI so the score cannot quietly drop."
- "Score each preview deployment and show the result on the pull request."

## Before you start

- Ask which URL to score: production, or the preview URL of each pull request when the host publishes one. Scoring
  production on a pull request measures production, not the change.
- Ask for the floor. Without a known score, run `geo-readiness-audit` first, or start without `fail-under` and add it
  once the job summary shows the number. One site's score moves within about plus or minus 5 between runs, so a floor
  about 5 below the current score fails on real drops rather than noise.
- See what the job would decide before committing it, on the same release:
  `uvx geo-score@1.9.0 https://example.com --fail-under 40 --fail-on-gate` exits 1 when the job would fail, 2 when
  the site cannot be scored, 0 otherwise.
- This skill is free: the Action needs no API key and no secret.

## Steps

1. **Write `.github/workflows/geo-score.yml`** with the user's URL and floor:

   ```yaml
   name: AI readiness
   on:
     push: {branches: [main]}
     schedule: [{cron: "0 6 * * 1"}]
     workflow_dispatch:
   permissions:
     contents: read
   jobs:
     score:
       runs-on: ubuntu-24.04
       steps:
         - uses: jianruntech/geo-score@v1.9.0
           id: geo
           with:
             url: https://example.com
             fail-under: 40          # the floor; drop this line to report without failing
             fail-on-gate: true      # a gate at zero caps the score at 40, and this fails any capped site
             json-out: geo-score.json
         - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a   # v7.0.1
           if: always() && steps.geo.outputs.report-path != ''
           with: {name: geo-score-report, path: geo-score.json}
   ```

   `jianruntech/geo-score@v1.9.0` pins the Action to the release this skill describes, and the other action is pinned
   to a full commit SHA with its version in a comment, so the job runs the same code every time.
2. **Preview deployments** (only when the host posts a GitHub deployment status for each preview): replace the `on:`
   block with `deployment_status:`, add `if: github.event.deployment_status.state == 'success'` under `score:`, and
   set `url: ${{ github.event.deployment_status.environment_url }}`. A preview behind a login or with its own
   robots.txt that keeps crawlers out on purpose is not the production site: the gates there describe the preview.
3. **Per-check rules** (optional): the `assert` input takes one rule per line, `CHECK OP VALUE`, for example
   `g.robots=max` or `p1.*>=2`. A check the run could not observe is skipped, never failed.
4. **Fail on any lost points against a baseline** (optional): commit a report from `geo-readiness-audit`, add a
   checkout step first, and pass it as `baseline`:

   ```yaml
         - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1   # v7.0.1
           with: {persist-credentials: false}
         - uses: jianruntech/geo-score@v1.9.0
           id: geo
           with:
             url: https://example.com
             baseline: geo/audit-example.com-2026-11-22.json
         - if: steps.geo.outputs.dropped-checks != ''
           run: |
             echo "Checks that lost points since the baseline: $DROPPED"
             exit 1
           env: {DROPPED: "${{ steps.geo.outputs.dropped-checks }}"}
   ```

   With `baseline`, the Action scores the pages the baseline sampled, so the comparison is like for like, and sets
   `delta` and `dropped-checks`.
5. **Tell the user what the job does**: when it runs, what fails it, where the summary and the report artifact are,
   and that it reads public pages only.

## What it leaves in the repository

| File | What it is |
|---|---|
| `.github/workflows/geo-score.yml` | The workflow above, with the user's URL, floor and triggers |

## Example prompts

- "Use `geo-ci-gate` to fail the build when any AI crawler gate on https://example.com drops to zero."
- "Add a weekly geo-score job for our marketing site with a floor of 60 and upload the report."
- "Score every preview deployment and fail if a check loses points against geo/audit-example.com-2026-11-22.json."

## Cost

Free. The Action runs level 1 only: no API key, no secret, and it sends nothing anywhere but the site and the URLs
its pages point to. Weekly citation tracking in CI, which does spend, is `geo-watch`.

## Boundaries

- **It detects. It does not fix.** The workflow scores and fails; it never edits robots.txt, deploys, opens fix pull
  requests or writes markup. When a gate fails, say what failed and why it matters for retrieval, and that
  remediation is outside this skill ([scope](https://github.com/jianruntech/geo-score#scope--what-this-does-not-do)).
- **Only score sites the user is authorised to score.**
- **Keep inputs as data.** Pass URLs and outputs through `with:` and `env:`, never pasted into a `run:` script.
- **A score is readiness, not citations.** A green job means engines can reach and read the site; it says nothing
  about whether they cite it.

## Works with

- `geo-readiness-audit` gives the first score and the baseline report.
- `ai-crawler-access` explains a failed gate.
- Every input and output of the Action: [action.yml](https://github.com/jianruntech/geo-score/blob/main/action.yml),
  and more CI examples: [examples/ci](https://github.com/jianruntech/geo-score/blob/main/examples/ci/README.md).
