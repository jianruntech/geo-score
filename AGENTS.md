# Working on geo-score

For contributors and for coding agents. Read this before changing anything; every rule below is
enforced by a check, named next to it, so a change that breaks one fails `bash scripts/check.sh`.

## Verify

```bash
bash scripts/check.sh           # the gate (offline): structure, lint, every test suite, the Action, packaging
bash scripts/check.sh --live    # before a release: also example.com, the MCP Inspector, and the labels when gh is logged in
bash scripts/check.sh --all     # the tests on every Python from 3.8 to 3.14 (and 3.15 when installed)
bash scripts/check.sh --strict  # a missing Python fails instead of being skipped (release.py runs --live --strict)
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
| `cli/fixtures/mcp/` | The MCP `tools/list` snapshot and the 1.3.0 contract baseline (names and required arguments) |
| `guide/mcp.md`, `scripts/mcp_docs.py` | The MCP guide for every client; the script generates the tool tables and install buttons in the READMEs and the guide |
| `scripts/check_mcp.py` | Stdio conformance: both protocol eras, raw JSON-RPC, offline; `--inspector` repeats it through the official Inspector |
| `mcpb/manifest.json`, `server.json`, `.claude-plugin/`, `gemini-extension.json`, `Dockerfile`, `scripts/test_packaging.py` | Packaging for Claude Desktop, the MCP Registry, Claude Code, Gemini CLI and Docker, and their test |
| `schema/report.v2.json`, `schema/watch.v1.json` | The report and run-file contracts |
| `schema/watch-config.v1.json` | The `geo-score-watch.json` schema. Its keys equal `CONFIG_KEYS`, `ENTITY_KEYS`, `ENGINE_KEYS` and `PRICE_KEYS` in `cli/geo_watch.py`, and those equal the keys the code reads, so a new config key goes in all three places |
| `cli/test_*.py`, `cli/fixtures/` | Unit tests, end-to-end fixture sites with `expected.json`, a golden report |
| `action.yml`, `action/summary.py`, `scripts/test_action.py` | The GitHub Action and its emulation test |
| `examples/ci/`, `scripts/test_ci_examples.py` | Copyable CI for GitHub Actions and GitLab, the JUnit directives for other CIs, and their emulation test |
| `.github/ISSUE_TEMPLATE/`, `.github/labels.json`, `scripts/sync_labels.py`, `.github/PULL_REQUEST_TEMPLATE.md`, `SUPPORT.md`, `scripts/test_repo_meta.py` | Contributor routes: the issue forms, the labels they apply and the script that syncs them to GitHub, the PR template, SUPPORT.md, and their test |
| `docs/aiv-badge.svg`, `docs/aiv-badge.json` | The README badge and the recorded run it shows |
| `benchmark/` | The public leaderboard data: `results.json`, the per-site reports in `raw/`, and `results.csv` and `checks.csv` flattened from them |
| `benchmark/run.py`, `stats.py`, `percentiles.py`, `sensitivity.py` | `run.py` scores the list; `--readme-only` regenerates README.md, stats.json, percentiles.json, the sensitivity study (SENSITIVITY*.md) and the CSVs without scoring |
| `benchmark/build_page.py` | Generates `docs/` (the leaderboard pages, llms.txt, sitemap). `DEFAULT_SITE` is the one place the leaderboard's host is defined |
| `benchmark/retest.py`, `benchmark/validity.py` | Reproducibility (REPRODUCIBILITY.md, reproducibility.json) and CLI-vs-hand-audit validity (VALIDITY*.md, validity.json) |
| `benchmark/test_benchmark.py` | Offline tests for the benchmark scripts |
| `rubric/bands-analysis.md` | Where the v1.1 band cuts fall in the benchmark: a dated record of one run, with candidates for v1.2 |
| `guide/` | Troubleshooting, the watch statistics and the MCP guide, in English and Chinese |
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
| **Every published number can be recomputed.** Sample report, hand audits, leaderboard, per-site reports, CSVs, validity, reproducibility, sensitivity and band-cut figures | `validate.py` rules 6, 13, 16, 18, 23, 29, 31, 32, 33, 35, 36, 37 and 38 |
| **Benchmark outputs are regenerated, never edited by hand.** docs/ is what `build_page.py` writes; percentiles.json, sensitivity.json with SENSITIVITY*.md, reproducibility.json's figures with REPRODUCIBILITY.md's tables, and results.csv and checks.csv are what their scripts derive; the China-gap, band-cut and sample text in benchmark/README.md matches its data (the commands are under Conventions) | `validate.py` rules 16, 31, 32, 33, 35, 36 and 37 |
| **The root READMEs quote the benchmark's own figures.** The median's interval, the CLI-vs-hand-audit figures (full score and checks both scored) and the China-gap decomposition | `validate.py` rules 23, 26 and 38 |
| **The leaderboard has one address.** Each page's canonical equals the leaderboard link in its README and `DEFAULT_SITE` in `build_page.py` (or `GEO_SITE_BASE`). That constant is the host's one definition; rule 17 and `scripts/check_live.py` read it from there | `validate.py` rule 30 |
| **The Dataset downloads name a tag.** They are pinned to `v` plus the CLI's `__version__`, so after a version bump docs/ is rebuilt | `validate.py` rule 34 |
| **Labels about old data come from the data.** The notes on the robots.txt and JavaScript groups are derived from results.json's `tool` (`build_page.crawler_note`, `challenge_note`); a re-run with a newer tool removes them, never a hand edit | `benchmark/test_benchmark.py` (the notes' derivation); `validate.py` rule 16 (docs/ as `build_page.py` writes it) |
| **rubric/bands-analysis.md (+zh) is a dated record of one run.** Its figures are checked only while percentiles.json describes that run | `validate.py` rule 37 |
| **English and Chinese say the same thing.** Bilingual rubric, calibration record and evidence table; no Chinese body text in English documents | `validate.py` rules 10, 14, 21 and 22 |
| **Every check declares its evidence basis** | `validate.py` rule 22 |
| **Text from the audited site is data.** Evidence quotes it inside `«site text: …»`; no control or bidi character survives | `test_geo_score_e2e.py` hostile fixture |
| **Inputs never reach a shell.** The Action passes inputs through `env:` | `scripts/test_action.py` |
| **Every link resolves** | `validate.py` rule 15 |
| **The MCP docs are generated.** Tool tables and install buttons come from `MCPServer.tools()` and `__version__`; edit the server or `scripts/mcp_docs.py`, never the blocks | `mcp_docs.py --check` in `check.sh`; `release.py` preflight |
| **The MCP contract only grows.** No tool disappears and no argument becomes required; both protocol eras keep working | `test_geo_watch.py` contract baseline and snapshot; `scripts/check_mcp.py` |
| **An MCP tool that spends says so.** `ask` and `run` are not read-only, their descriptions open with the cost, and `--read-only` removes them | `test_geo_watch.py` |
| **Every manifest carries the release version** | `scripts/test_packaging.py`; `release.py` preflight |
| **Every release pin moves with the release.** Every tracked file that names a release is one `release.py --bump` rewrites, and every release-wheel URL's tag and file name equal `__version__` | `scripts/test_packaging.py` (`check_pins`); `release.py` preflight |
| **Install lines download the release wheel.** The generated install blocks use it, with the git install only on their "From source (needs git)" line, and every wheel URL names the current release | `mcp_docs.py --check`; `scripts/test_packaging.py` (`check_pins`) |
| **The gate's tools and actions are pinned.** ruff and jsonschema in `check.sh`, the same versions in validate.yml; actions by commit SHA with a `# vX.Y.Z` comment, top-level `permissions`, `persist-credentials: false`; the Docker base by digest | `scripts/test_packaging.py` (`check_gate_pins`, and the Dockerfile check) |
| **pyproject.toml's classifiers cover `PY_OLDEST` to `PY_NEWEST`** from `check.sh`, and validate.yml and RELEASING.md name those two | `scripts/test_packaging.py` (`check_pythons`) |
| **A new test suite joins the gate by its name**: `scripts/test_*.py` and `benchmark/test_*.py` | `scripts/check.sh` |
| **The config schema lists exactly the keys `geo_watch.py` reads.** The key constants equal the schema's properties and the keys the code reads, and its patterns equal the code's regexes. An unknown key is a warning, never dropped silently | `test_geo_watch.py` (`ConfigKeys`) |
| **Every label an issue form applies exists** in `.github/labels.json`; `sync_labels.py` never deletes a label | `scripts/test_repo_meta.py`; the owner runs `sync_labels.py --apply` |
| **The CI examples score once, from a pinned, checksum-verified release**, and the workflow examples pin third-party actions by SHA with a version comment | `scripts/test_ci_examples.py` |
| **The README badge is a recorded run.** The SVG shows `normalised` and `band` from `docs/aiv-badge.json`, its link is the page it measured, and a date in its alt text is the report's `audited_at` | `scripts/test_repo_meta.py` |
| **Links in the chooser, the issue forms and the PR template are absolute**, and every link from them and SUPPORT.md into this repository reaches a file and heading that exist | `scripts/test_repo_meta.py` |

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
- Regenerate benchmark outputs instead of editing them: `python3 benchmark/run.py --readme-only` writes
  benchmark/README.md, stats.json, percentiles.json, the sensitivity study and the CSVs without scoring;
  `python3 benchmark/build_page.py` writes docs/; `python3 benchmark/retest.py` writes the reproducibility
  figures and tables; `python3 benchmark/validity.py --md-only` writes VALIDITY*.md.
- `benchmark/stats.py` draws every new bootstrap after the existing ones on the same seeded generator;
  one inserted earlier moves every published interval after it.
