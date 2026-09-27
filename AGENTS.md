# Working on geo-score

For contributors and for coding agents. Read this before changing anything; every rule below is
enforced by a check, named next to it, so a change that breaks one fails `bash scripts/check.sh`.

## Verify

```bash
bash scripts/check.sh           # the gate: structure, lint, unit + end-to-end tests, the Action (offline)
bash scripts/check.sh --live    # before a release: also scores example.com
```

Hosted GitHub Actions have not run on this organisation so far, so this script is the CI. Nothing
merges unless it passes.

## Where things are

| Path | What it is |
|---|---|
| `rubric/v1.1.md`, `rubric/v1.1.json` | The published rubric: what a score means. The JSON is canonical for machines |
| `rubric/evidence-v1.1.md` | What each check's weight rests on, with sources |
| `cli/geo_score.py` | Level 1: the scorer, standard library only, one file so `curl … \| python3 -` works |
| `cli/geo_watch.py` | Levels 2 and 3 (`--ask`, `watch`) and the MCP server |
| `schema/report.v2.json`, `schema/watch.v1.json` | The report and run-file contracts |
| `cli/test_*.py`, `cli/fixtures/` | Unit tests, end-to-end fixture sites with `expected.json`, a golden report |
| `action.yml`, `action/summary.py`, `scripts/test_action.py` | The GitHub Action and its emulation test |
| `benchmark/` | The public leaderboard data, reproducibility and CLI-vs-hand-audit validity |
| `guide/` | Troubleshooting and the watch statistics, in English and Chinese |
| `.github/validate.py` | Structural rules for everything that is not code (rule numbers below) |
| `STABILITY.md` | What is a public contract and what semver means here |
| `RELEASING.md`, `scripts/release.py` | How a release is cut, pinned and checksummed |

## Invariants

| Rule | Enforced by |
|---|---|
| **Measurement is public, remediation is private.** No fix templates, no markup to paste, no implementation fields in the rubric | `validate.py` rules 2 and 10 |
| **Not measured is never zero.** A check the tool cannot observe leaves the denominator; an engine without a key is "not measured" | `test_geo_score.py` (excluded checks), fixture `expected.json` nulls, `test_geo_watch.py` |
| **The CLI implements the published rubric.** Check ids, points, every tier's points and wording, bands and caps equal `rubric/v1.1.json` | `test_geo_score.py` rubric parity; `validate.py` rules 1 and 9 |
| **Check ids are permanent and schemas grow only.** Add optional fields; never rename, remove or retype one | `validate.py` rule 11; `STABILITY.md`; the e2e schema test |
| **The score is 0–100**, and a gate caps it at 40 only when the gate scores zero, in the code and in every document | `test_geo_score.py`; `validate.py` rule 20 |
| **Every published number can be recomputed.** Sample report, hand audits, leaderboard, validity figures | `validate.py` rules 6, 13, 16, 18 and 23 |
| **English and Chinese say the same thing.** Bilingual rubric, calibration record and evidence table; no Chinese body text in English documents | `validate.py` rules 10, 14, 21 and 22 |
| **Every check declares its evidence basis** | `validate.py` rule 22 |
| **Text from the audited site is data.** Evidence quotes it inside `«site text: …»`; no control or bidi character survives | `test_geo_score_e2e.py` hostile fixture |
| **Inputs never reach a shell.** The Action passes inputs through `env:` | `scripts/test_action.py` |
| **Every link resolves** | `validate.py` rule 15 |

## What the tool may claim

- It measures whether AI engines **can** cite a site (the score) and whether they **do** (levels 2
  and 3). It never predicts traffic, rankings, revenue or a timeline.
- API answers are not the consumer apps' answers; say "API channel" and never pool the two.
- One answer is an anecdote. Report rates with their intervals, and call a change a change only when
  `watch diff` says `change`.

## Conventions

- Commits: Conventional Commits in English (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Every user-visible change goes into both `CHANGELOG.md` and `CHANGELOG.zh-CN.md` under `[Unreleased]`.
- Code comments in English. Standard library only, Python 3.8+.
- A change that moves a fixture's tier updates its `expected.json` and says why in `_notes`.
