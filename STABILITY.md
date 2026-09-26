# Stability and versioning

geo-score has two version numbers, and they move for different reasons.

- **The rubric** (`rubric/v1.1.md`, `rubric/v1.1.json`) decides what a score means. A score is only
  comparable with scores from the same rubric version, so every report states it.
- **The tool** (`cli/`, currently 1.2.x) follows [Semantic Versioning](https://semver.org/). Its
  version is in every JSON report (`tool`) and in `--version`.

## Public contracts

These are what you can build on. A breaking change to any of them needs a new major version of the
tool, or a new rubric version, and a changelog entry that says what to change.

| Contract | Where it is defined | Breaking change means |
|---|---|---|
| Check ids, points and tiers | `rubric/v<N>.json` | A new rubric version, never an edit in place |
| Score arithmetic (denominator, gate cap, bonus cap, bands) | `rubric/v<N>.md`, `cli/geo_score.py` `score()` | A new rubric version |
| Report JSON | `schema/report.v2.json` | Removing or renaming a field, changing a type, or making an optional field required |
| Watch run files | `schema/watch.v1.json` (`format: geo-score/watch.v1`) | A new `format` value; old files stay readable or the changelog says they are not |
| CLI flags and subcommands | `geo_score.py --help`, `geo_score.py watch --help` (also `geo-score` and `geo-score-mcp` after a pip install) | Removing or renaming one, or changing its default |
| Exit codes | [cli/README.md](cli/README.md#options) | Any change |
| GitHub Action inputs and outputs | `action.yml` | Removing or renaming one |
| SARIF and JUnit output | `--sarif` (SARIF 2.1.0, one rule per check id), `--junit` (one test per check id) | Changing rule or test ids, or which states fail |
| MCP tool names and arguments | `geo_score.py mcp` (`tools/list`) | Removing or renaming one, or making an argument required |

Not contracts: the Python functions inside `geo_score.py` and `geo_watch.py` (`run`, `score`,
`as_json` and the rest are importable, but they can change in any release; build on the CLI, the
JSON and the MCP tools instead), the text layout of the terminal report, colours, the order of evidence strings,
the benchmark numbers (they are a dated measurement, see `benchmark/`), and the default model
of each engine in level 2 and 3 (pin models in your `geo-score-watch.json`).

## What a minor or patch release may do

- **Patch (1.2.x):** fix a bug, harden input handling, improve an error message. A patch can move
  a site's score only when the earlier result was wrong, and the changelog then names the check
  and the direction (see 1.1.2).
- **Minor (1.x):** add a flag, a subcommand, an output format, an optional JSON field, an engine,
  or an MCP tool.
- **Rubric minor (v1.x):** re-weight checks or change tiers. Published with a calibration record
  and never applied to old reports.

## The `v1` tag

`uses: jianruntech/geo-score@v1` follows the latest 1.x release. Pin an exact tag (`@v1.2.0`)
when you need a score to stay put between runs.

## Deprecation

Anything we intend to remove is marked deprecated in the changelog and in `--help` for at least
one minor release first, and keeps working during that time.

## Telemetry

None. The CLI, the Action and the MCP server send nothing to Jianrun or anyone else. Level 1
fetches the site you name, the profile links that site lists in its `sameAs` markup (to check they
resolve), and Wikidata and Wikipedia search (for the knowledge-graph check). Levels 2 and 3 call
only the AI providers whose keys you set.
