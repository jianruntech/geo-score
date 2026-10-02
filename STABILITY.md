# Stability and versioning

geo-score has two version numbers, and they move for different reasons.

- **The rubric** (`rubric/v1.1.md`, `rubric/v1.1.json`) decides what a score means. A score is only
  comparable with scores from the same rubric version, so every report states it.
- **The tool** (`cli/`) follows [Semantic Versioning](https://semver.org/). Its
  version is in every JSON report (`tool`) and in `--version`.

## Public contracts

These are what you can build on. A breaking change to any of them needs a new major version of the
tool, or a new rubric version, and a changelog entry that says what to change.

| Contract | Where it is defined | Breaking change means |
|---|---|---|
| Check ids, points and tiers | `rubric/v<N>.json` | A new rubric version, never an edit in place |
| Score arithmetic (denominator, gate cap, bonus cap, bands) | `rubric/v<N>.md`, `cli/geo_score.py` `score()` | A new rubric version |
| Report JSON | `schema/report.v2.json` | Removing or renaming a field, changing a type, or making an optional field required |
| Report comparison JSON | `schema/diff.v1.json` (`format: geo-score/diff.v1`), printed by `geo-score diff … --format json` (1.5.0) | Removing or renaming a field, changing a type, removing a check state, or a new `format` value |
| Error JSON | `schema/error.v1.json`, printed on stdout instead of a report when the CLI exits 2 under `--json` (or `diff --format json`) (1.5.0) | Removing or renaming a field or a kind, or changing a type. A minor release may add kinds; read an unknown one as `error` |
| Bot-challenge error | A site that served only bot-challenge pages exits 2 with a message that starts `bot challenge served to a browser user-agent` (kind `bot_challenge` under `--json`). `benchmark/run.py` files a CLI error that starts with it under a not-scored reason of its own (1.5.0) | Changing that prefix. The rest of the message is not a contract, like every other error message |
| shields.io endpoint badge | `--badge-json`, and the Action's `badge` input with a `.json` path: the keys `schemaVersion`, `label`, `message`, `color` and `cacheSeconds` of shields.io's endpoint schema (1.5.0) | Removing a key or changing `label`. The message wording and the colours follow the SVG badge and are not a contract |
| Watch run files | `schema/watch.v1.json` (`format: geo-score/watch.v1`) | A new `format` value; old files stay readable or the changelog says they are not |
| Watch config | `schema/watch-config.v1.json` (the keys of `geo-score-watch.json`) | Removing or renaming a key, narrowing what a key accepts, or making an optional key required. A key the tool does not read stays a warning, never an error |
| CLI flags and subcommands | `geo_score.py --help`, `geo_score.py diff --help` (the `diff` subcommand, 1.5.0), `geo_score.py watch --help` (also `geo-score` and `geo-score-mcp` after a pip install) | Removing or renaming one, or changing its default |
| Exit codes | [cli/README.md](cli/README.md#options) | Any change |
| GitHub Action inputs and outputs | `action.yml` (1.5.0 adds the inputs `fail-on-gate`, `assert`, `badge` and `baseline`, and the outputs `badge-path`, `delta` and `dropped-checks`) | Removing or renaming one |
| Release wheel | `geo_score-X.Y.Z-py3-none-any.whl`, attached to every release from 1.4.0 at `releases/download/vX.Y.Z/`. The documented install lines for a machine without PyPI download it by that name, and `release.py --execute` refuses a build that names it differently | Renaming it, or a release without it |
| PyPI package | `geo-score` on PyPI from 1.5.0: each release's wheel and sdist, byte for byte the files attached to the GitHub release (1.5.0's were checked against its `SHA256SUMS` once uploaded; from 1.6.0 `release.py --execute` uploads them and checks each SHA-256 against `SHA256SUMS`). The documented install lines run `uvx geo-score@X.Y.Z` and `pipx install geo-score==X.Y.Z`, and the MCP Registry listing in `server.json` names it | Renaming the package, or a release missing from it |
| SARIF and JUnit output | `--sarif` (SARIF 2.1.0, one rule per check id), `--junit` (one test per check id) | Changing rule or test ids, or which states fail |
| MCP tool names and arguments | `geo_score.py mcp` (`tools/list`); the 1.3.0 baseline is `cli/fixtures/mcp/contract-1.3.0.json`, checked by `test_geo_watch.py` | Removing or renaming one, or making an argument required |
| MCP prompt names and arguments | `prompts/list`: `audit_site`, `check_citations`, `weekly_watch`, `compare_runs`, `explain_check` | Removing or renaming one, or making an argument required |
| MCP protocol versions | `server/discover` and `initialize`: 2026-07-28, 2025-11-25, 2025-06-18, 2025-03-26, 2024-11-05 | Dropping one |
| MCP server flags and environment | `--toolsets`, `--tools`, `--exclude-tools`, `--read-only`; `GEO_SCORE_MCP_TOOLSETS`, `GEO_SCORE_MCP_TOOLS`, `GEO_SCORE_MCP_EXCLUDE_TOOLS`, `GEO_SCORE_MCP_READ_ONLY` | Removing or renaming one, or changing its default (all tools, read-write) |

`--fail-on-gate` and `--assert` are CI policy, not measurement: their results are printed to stderr and never
written into the report JSON. `elapsed_s` in the report (since 1.5.0) describes the run, not the site: it
depends on the machine and network that ran the score, it may be absent, and `diff` never compares it. The
flags, subcommands and exit codes `--help` lists are contracts; its wording, examples and layout are not.

Not contracts: the Python functions inside `geo_score.py` and `geo_watch.py` (`run`, `score`,
`as_json` and the rest are importable, but they can change in any release; build on the CLI, the
JSON and the MCP tools instead), the text layout of the terminal report and of the comparison that `diff` and `--baseline` print (their
JSON is the contract), the wording of error messages other than the bot-challenge prefix (match on the
JSON `kind`), colours, the order of evidence strings, the order of MCP tools and the
wording of their descriptions,
the benchmark numbers (they are a dated measurement, see `benchmark/` and [Benchmark data](#benchmark-data)),
the default model of each engine in level 2 and 3 (pin models in your `geo-score-watch.json`), and the
copyable CI examples in `examples/ci/` (they pin a release and third-party actions by commit SHA, and
change in any release).

## What a minor or patch release may do

- **Patch (the third number):** fix a bug, harden input handling, improve an error message. A patch can move
  a site's score only when the earlier result was wrong, and the changelog then names the check
  and the direction (see 1.1.2, and the fixes in 1.5.0).
- **Minor (1.x):** add a flag, a subcommand, an output format, an optional JSON field, an engine,
  an MCP tool, prompt or protocol version; add an exit code that only an opt-in flag can produce (`watch diff --fail-on-drop`
  exits 4; since 1.5.0 `diff --fail-on-drop` and `--baseline … --fail-on-drop` do too, and a failed
  threshold or assertion keeps its exit 1), leaving the codes of existing invocations unchanged. A minor release may also correct a
  statistical method when the old one overstated certainty (1.3.0 made `watch diff` paired and
  corrected for multiple comparisons); the changelog then says which verdicts can change.
- **Rubric minor (v1.x):** re-weight checks or change tiers. Published with a calibration record
  and never applied to old reports.

### What 1.5.0 changes under these rules

- `--fail-on-gate` and `--assert` are opt-in flags that exit 1 as `--fail-under` does, or 2 on a
  malformed expression; `--timeout`, `--badge-json`, `--baseline`, `--fail-on-drop` and `diff` are new too.
  Existing invocations keep their exit codes, apart from the three corrections below.
- Exit 2 also covers a site that served only bot-challenge pages. 1.4.0 scored such a site (`g.ssr` 0,
  capped at 40) and exited 0 or 1, which was wrong, so the change falls under the patch rule: the check
  is `g.ssr`, the direction 0 to not scored. A site that answered 403 with a Cloudflare challenge now
  gets kind `bot_challenge`.
- An unexpected error exits 2 in one line (`GEO_SCORE_DEBUG=1` shows the traceback). In 1.4.0 the
  traceback ended the process with exit 1, which CI read as a failed threshold.
- `--sample N` with N below 1 is refused as a usage error (exit 2; kind `usage` under `--json`). In
  1.4.0, 0 ended in a traceback and a negative N scored fewer pages and exited as any run does.
  `run(url, sample)` raises ValueError when it gets no pinned `urls` and `sample` is not a whole number
  of 1 or more; its signature is unchanged.
- `g.robots` can be `unobservable` when robots.txt could not be read after 3 tries, where 1.4.0 read
  "No robots.txt". report.v2 already allows that state for every check.
- `audience_language` stays a BCP 47 string and now takes values other than `en` and `zh-CN` (`ja`, `de`,
  `fr`, `ko`, `und`, …), and `notes` may carry the new sample lines. report.v2 keeps its shape and gains
  only the optional `elapsed_s`.
- `p2.sourced-stats` reads a source only beside its figure, and identifiers and prices are no longer
  figures. This and every other reading that moves is named in the changelog with its direction.

## The `v1` tag

`uses: jianruntech/geo-score@v1` follows the latest 1.x release. Pin an exact tag (`jianruntech/geo-score@v1.6.0`)
when you need a score to stay put between runs.

## Supported Python

`requires-python` is `>=3.8`. `release.py --execute` tests a release on Python 3.8 and on the newest
stable Python (3.14, `PY_NEWEST` in `scripts/check.sh`): it runs `check.sh --live --strict`, which stops
when either is missing. Before a minor or major release the owner also runs the CLI suites and
the MCP conformance check on Windows with both ([RELEASING.md](RELEASING.md), step 6).

## Benchmark data

The benchmark is a dated measurement, not an API, but other tools read its files, so they change in
known ways.

- **The leaderboard's address** is https://www.jianruntech.com/leaderboard, and the Chinese page is
  https://www.jianruntech.com/leaderboard/zh, with no trailing slash and no `.html`. `GEO_SITE_BASE`
  moves the base; the Chinese page is always `<base>/zh`. The GitHub Pages copy is not a supported
  location.
- **`benchmark/results.csv` and `checks.csv`.** results.csv holds the fixed fields (`site` to `error`),
  then one column per check id in rubric order: a new rubric version can add or remove check columns,
  and the fixed fields are not renamed within a minor release. checks.csv has the columns `site`,
  `check_id`, `state`, `points` and `max`.
- **Optional fields.** A run made with the current `run.py` records `measured_from` (the vantage its
  operator declared, or null), `python` (the interpreter's version) and `pinned_from` (the directory of
  the pinned pages, relative to the run's own, or null) at the top of results.json, and `sample_n` and
  `sample_source` on each row; data measured earlier lacks them. `stats.json` has
  `china_gap_detail` (null when raw/ is incomplete), and `validity.json` has `common_checks` and
  `validation_set`, beside every earlier key.
- **`reproducibility.json` is `format: 2`:** `study` (null until a study is recorded) and `legacy` (the
  2026-09-09 runs with their original keys, plus `analysis`). A study stores one record per site per
  run, with `normalised`, `band`, `gate_capped`, `gate_reason` and the tiers in `checks` order.
- **Generated analyses.** `percentiles.json` and `sensitivity.json` can change shape between releases.
- **Maintainer tooling.** The flags of `benchmark/run.py` (`--out`, `--urls-from-dir`, `--vantage`,
  `--readme-only`) and `benchmark/retest.py` (`--labels`, `--check`) are not part of the CLI's contract.
- **Qualifiers follow the data.** The notes on the robots.txt and JavaScript groups appear only while
  results.json was measured with a tool older than 1.5.0, and disappear without an edit when the
  leaderboard is re-run with 1.5.0 or later.

## Deprecation

Anything we intend to remove is marked deprecated in the changelog and in `--help` for at least
one minor release first, and keeps working during that time.

## Telemetry

None. The CLI, the Action and the MCP server send nothing to Jianrun or anyone else. Level 1
fetches the site you name (following its redirects), the URLs that site's markup and robots.txt point
to (its `sameAs` profiles, its logo and its declared sitemap, to check they resolve), and Wikidata and
Wikipedia search (for the knowledge-graph check, in English and in the sampled pages' most common
other language when Wikipedia has a large edition in it). Levels 2 and 3 call
only the AI providers whose keys you set.
