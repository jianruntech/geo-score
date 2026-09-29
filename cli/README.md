# geo-score CLI

Score a site against the [AIV rubric v1.1](../rubric/v1.1.md), and, with your own API keys,
check and track whether AI engines cite it. Python 3.8+, standard library only, nothing to
install. Level 1 is `geo_score.py` alone; levels 2 and 3 need `geo_watch.py` from the same
release beside it.

```bash
curl -sL https://raw.githubusercontent.com/jianruntech/geo-score/v1.4.0/cli/geo_score.py \
  | python3 - yoursite.com
```

## Options

| Flag | What it does |
|---|---|
| `--brief` | Pillar totals and the three biggest gaps only — what fits in a screenshot |
| `--explain`, `-e` | Print the evidence behind every check, not just the score |
| `--json` | Machine-readable output conforming to [`schema/report.v2.json`](../schema/report.v2.json) |
| `--json-out FILE` | Also write that JSON to FILE, from the same run as the report on screen |
| `--sarif FILE` | Also write [SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html): one rule per check, one result per check below full marks (a gate at zero is `error`, another check at zero `warning`, partial credit `note`). Each result points at the line of its check in the `--json-out` report (or at the SARIF file when there is none), with the site named in the message, which is what GitHub code scanning requires |
| `--junit FILE` | Also write JUnit XML: one test per check. A check at zero fails, a check the CLI cannot observe is skipped, partial credit passes |
| `--sample N` | How many pages to sample (default 8, which is what the rubric specifies) |
| `--timeout SECONDS` | How long each request may wait for the server before it counts as unanswered (default 15, at most 300). A site that cannot be reached fails fast and says why: a name that does not resolve, a refused connection or a failed TLS handshake is not retried |
| `--urls FILE` | Score exactly these pages instead of drawing a sample: one URL per line (or a path such as `/pricing`), `#` comments allowed, up to 8, all on the site being scored. The report says `sample_source: pinned` |
| `--urls-from REPORT` | Score the pages an earlier JSON report sampled (its `sampled_urls`). Re-score with the same pages to see whether the site changed, without sampling noise |
| `--compare URL` | Score another site too and print them side by side. Repeatable. Not with `--json-out`, `--sarif` or `--junit`, which take one site |
| `--badge [FILE]` | Also write an embeddable SVG badge (default `aiv-badge.svg`) |
| `--share` | Print a one-line summary sized for a post, plus the badge markdown |
| `--fail-under N` | Exit 1 when the score is below N — for CI |
| `--fail-on-gate` | Exit 1 when any gate check (`g.*`) scores 0, and name the gate and its evidence on stderr. A gate at zero caps the score at exactly 40, so `--fail-under 40` never fails a capped site; add `--fail-on-gate`. The same as `--assert 'g.*>0'`. An unobservable gate never fails |
| `--assert EXPR` | Exit 1 unless `CHECK OP VALUE` holds: a check id or an fnmatch glob over the ids, then `>=`, `>` or `=`, then a whole number or `max`, e.g. `g.robots=max` or `p1.llms-txt>=4`. Repeatable. A check the run could not observe prints `not measured, skipped` and never fails. A malformed expression, or a glob that names no check, is a usage error (exit 2). Results go to stderr, never into the report |
| `--quiet`, `-q` | Suppress progress lines on stderr |
| `--ask QUESTION` | Level 2: also ask the AI engines this question through their APIs (your keys) and report who they cite, beside the score. Repeatable, up to 5 |
| `--brand NAME` | With `--ask`: the brand name to look for in answers. Default: the site's domain name, e.g. `stripe` for `docs.stripe.com` |
| `--domain DOMAIN` | With `--ask`: another domain that counts as yours. Repeatable. The scored site, its registrable domain and a redirect's landing domain always count |

`NO_COLOR=1` turns off colour, as does piping to a file. `HTTPS_PROXY` and `NO_PROXY` are honoured.
When a reading looks wrong, see [troubleshooting](../guide/troubleshooting.md).

Exit codes. Level 1: `0` scored, `1` below `--fail-under`, a gate at zero under `--fail-on-gate`, or a
failed `--assert`, `2` the site could not be fetched or served only bot-challenge pages, a pinned URL
list was refused, a usage error (a malformed `--assert` included), or an internal error, reported in one
line with where to file it (`GEO_SCORE_DEBUG=1` shows the traceback). When the site could not be
fetched, the message names the kind of failure, such as `dns`, `timeout` or `http_403`, and links to
[its section in troubleshooting](../guide/troubleshooting.md#could-not-fetch--and-exit-code-2). A site
that served only bot-challenge pages says `bot challenge served to a browser user-agent (…)`, kind
`bot_challenge`. With `--json`, an exit 2 prints a JSON error on stdout instead of a report
([`schema/error.v1.json`](../schema/error.v1.json)), with the same kind in `error.kind`. Assertions on
the heuristic checks listed under *How far to trust each check* carry the same run-to-run noise as the
score: pin the pages with `--urls-from` when you assert on them. Levels 2 and 3 (`watch …`): `0` done,
`1` configuration error, `2` usage error or `geo_watch.py` missing, `3` nothing could be measured (no
key worked), `4` `watch diff --fail-on-drop` found a drop beyond noise.

## Comparing against a competitor

```bash
python3 geo_score.py yoursite.com --compare competitor.com
```

Both sites are scored the same way and printed check by check, with a `›` marking every
row where they differ and a closing list of where the other site is ahead. That list is
the useful part: it is the difference between two real sites, not a checklist in the
abstract.

## A badge for your own README

```bash
python3 geo_score.py yoursite.com --badge docs/aiv-badge.svg
```

Writes a shields-shaped SVG you can commit next to your README and reference like any
other badge:

```
![AIV readiness](docs/aiv-badge.svg)
```

It carries the score, the band and an accessible label, and it sits happily beside the
build badges you already have. Colour follows the band, so a regression is visible at a
glance. Re-run it in CI to keep it current — the
[GitHub Action](../action.yml) does this for you if you point `json-out` at a path and
regenerate from there.

## What it measures, and what it does not

The CLI scores the **17 checks a static fetch can honestly observe**. It fetches your
sample pages once with a browser user-agent, then re-fetches three of them with each of
the ten retrieval user-agents to see whether any of them is served something different.
It parses JSON-LD, `robots.txt`, `llms.txt` and your sitemap, and it queries the public
Wikidata and Wikipedia APIs to check whether your brand has a knowledge-graph entity.

Four checks are **left out of the denominator** rather than guessed:

| Check | Why the CLI cannot see it |
|---|---|
| `p3.listings` | Needs to know your industry and search its directories |
| `p3.mentions` | Needs off-site search for independent coverage |
| `p4.question-coverage` | Needs the ten questions people actually ask in your market |
| `p4.cn-engines` | Skipped unless the site addresses the Chinese market |

The [Claude Code skill](../SKILL.md) scores all 21.

### How far to trust each check

Measured by re-scoring the five published hand audits on the same pages
([VALIDITY.md](../benchmark/VALIDITY.md)): the CLI matched the auditor's tier on 79% of 86 check
pairs and read 3.6 points lower on average.

| How the CLI reads it | Checks | Same tier as the hand audit |
|---|---|--:|
| **By rule**: parses a file, a status code or markup and applies the rubric's count | `g.robots`, `p1.*`, `p3.knowledge-graph`, `p3.sameas`, `p4.cn-engines` | 95% of 41 pairs |
| **By heuristic**: approximates a judgement the rubric describes in prose | `g.reachable`, `g.ssr`, `p2.*`, `p3.video`, `p4.answer-shape` | 64% of 45 pairs |
| **Not at all**: needs off-site search or human judgement | `p3.listings`, `p3.mentions`, `p4.question-coverage` | left out of the denominator |

The weakest agreement is `p2.sourced-stats` (the CLI scored higher than the auditor on 4 of 5
sites), then `p2.named-author` (2 of 5 agree). Read those two with `--explain` before acting on
them.

## Heuristics, stated plainly

Some checks are judgements the rubric describes in prose, and the CLI approximates them:

- **Answer passages** — takes the first six paragraphs of the main content and looks for
  one of 25–120 words (50–200 characters on a Chinese-language site) that ends in
  sentence punctuation. A human reader judges whether it truly stands alone.
- **Question intent** — pattern-matches headings for questions, task verbs and
  explanatory forms, excluding navigation labels and brand strings.
- **Sourced statistics** — counts figures per page against citation elements, source
  phrases and outbound references near them.
- **Named authorship** — reads the `author` field from JSON-LD, then falls back to
  `rel="author"` and byline patterns, and rejects team and brand names.
- **Page-type schema** — besides the types the rubric names (Product + Offer, HowTo, FAQPage),
  the CLI also counts SoftwareApplication, Course, Recipe, Event, JobPosting, Dataset, and
  Article with its subtypes as page-type markup.

Where the CLI and a careful human disagree, the human is right and the rubric is the
arbiter. Run `--explain` to see exactly what the CLI observed, and
[open an issue](https://github.com/jianruntech/geo-score/issues) if a heuristic is wrong
on your site — those reports are how these get better.

## Watch

Levels 2 and 3 live in `geo_watch.py`, which must sit next to `geo_score.py`. They ask the AI
engines your questions through their search-enabled APIs with your own keys (read from the
environment, never written to disk) and report who the answers cite. Nothing they measure is
summed into the readiness score.

### Level 2: `--ask`

```bash
python3 geo_score.py acme.com --ask "best invoicing app for freelancers" --ask "acme vs rival"
python3 geo_score.py acme.com --ask "…" --brand "Acme Inc" --json   # result in the report's citation object
```

Up to 5 questions, one ask per engine that has a key. The brand defaults to the first label of the
domain; pass `--brand` when the name differs. Without any key the citation block says "not
measured" and the readiness report is unchanged.

### Level 3: `watch`

| Command | |
|---|---|
| `watch init [--dir D] [--brand NAME] [--domain D]… [--competitor NAME=DOMAIN]… [--country CC] [--force]` | Write `geo-score-watch.json` (models pinned) and `queries.csv` |
| `watch check` | Validate the config and the questions, and show which engines have keys and prices |
| `watch run [--dry-run] [--engines a,b] [--limit N] [--runs N] [--max-calls N] [--budget-usd X] [--allow-unpriced] [--format text\|md] [-q]` | Ask everything and save the run under `.geo-score/watch/runs/`. `--dry-run` prints the plan and exits 0, with or without keys |
| `watch report [RUN] --format text\|md\|csv\|json [-o FILE]` | A saved run. `csv` has one row per answer: `week, query_id, query, intent_tier, engine, cited, quoted_url, rank, other_domains_cited, note, branded` |
| `watch diff [A] [B] [--format text\|md\|json] [--fail-on-drop]` | Before and after, per engine, on the questions both runs answered: the change in points with a 95% interval, an exact paired test Holm-corrected across engines, and a verdict (`change`, `within noise`, `too few questions to tell` or `not measured`). Also lists citations lost and gained. `--fail-on-drop` exits 4 when a verdict is a change for the worse |
| `watch runs` | Saved runs and their headline rate |
| `watch ask "question" [--brand NAME] [--domain D]` | Level 2 without the score: one question to every engine, now, not saved |
| `mcp` | Score and watch over MCP (stdio); see [guide/mcp.md](../guide/mcp.md) |

Every `watch` command takes `-c PATH` for the config (default `./geo-score-watch.json`, or
`$GEO_SCORE_WATCH_CONFIG`).

`geo-score-watch.json` (the prices below are an example; copy current ones from your provider):

```json
{
  "brand": {"name": "Acme", "domains": ["acme.com"], "aliases": ["Acme Inc"],
            "url_prefixes": ["amazon.com/stores/Acme"]},
  "competitors": [{"name": "Rival", "domains": ["rival.com"]}],
  "queries": "queries.csv",
  "engines": [{"id": "chatgpt-api", "provider": "openai", "model": "gpt-6-luna"},
              {"id": "perplexity-api", "provider": "perplexity"},
              {"id": "deepseek-api", "provider": "openrouter", "model": "deepseek/deepseek-chat"}],
  "country": "US",
  "runs": 1,
  "max_calls": 120,
  "budget_usd": 2.0,
  "prices": {"chatgpt-api": {"input_per_mtok": 0.1, "output_per_mtok": 0.5, "per_search": 0.01}}
}
```

| Key | |
|---|---|
| `brand.domains` / `url_prefixes` | What counts as yours. Subdomains count; a prefix covers a store or profile on someone else's site |
| `brand.aliases` | Other names the answer may use. Chinese, Japanese and Korean names match anywhere; all others match whole words |
| `country` | Two-letter code passed to the engines that accept a location (OpenAI, Claude, Perplexity) |
| `runs` | Asks per question per engine. `3` gives steadier rates at three times the cost |
| `max_calls` | Exact cap on questions asked in one run |
| `budget_usd` | Spend cap, checked before every call; it can be exceeded by at most one call per engine. With a budget, unpriced engines are left out unless `--allow-unpriced` |
| `prices` | Per engine, USD: `input_per_mtok`, `output_per_mtok`, optional `per_search`, `per_call`. Perplexity and OpenRouter report their own cost |
| `engines[].api` | Gemini only: `interactions` (default) or `generate_content` |
| `engines[].key_env` / `base_url` | Read the key from another variable; point at a compatible endpoint (`https://` or `http://localhost`) |
| `engines[].tool`, `max_searches`, `max_tokens`, `max_results` | Provider tuning: the web-search tool version (OpenAI, Anthropic), searches and output tokens per answer (Anthropic), results per search (OpenRouter) |

`queries.csv` has four columns, `query_id,query,intent_tier,target_url`. Write the questions the
way a buyer would type them into ChatGPT, and keep the set fixed from week to week. An optional
fifth column, `branded` (`auto`, `yes` or `no`; empty means `auto`), overrides the automatic check
for questions that name the brand. Use `no` when the brand name is also a common word, and `yes` for
a nickname the matcher cannot see.

**Reading the numbers.** The headline rate counts only questions that do not name the brand.
"acme vs rival" all but guarantees an Acme citation, so those questions get their own line, and
`watch check` warns when they are more than 30% of the set. When a question has more than one
answer (`runs` > 1, or several engines in the overall line), the 95% interval is a bootstrap over
questions, because answers to one question move together; otherwise it is Wilson. Call something a
change only when `diff` says `change`. Formulas and a worked example:
[guide/watch-methodology.md](../guide/watch-methodology.md).

**Over MCP.** `geo-score-mcp` (`geo_score.py mcp` from a clone) serves all three levels to an agent
over stdio, with the same config and caps. It reads keys from its own environment, which a desktop
app does not share with your shell, and a GUI client does not start it in your project, so pass
`-c /absolute/path/geo-score-watch.json`. The config for each client, the tool table, keys,
timeouts and troubleshooting: [guide/mcp.md](../guide/mcp.md).

Run files follow [schema/watch.v1.json](../schema/watch.v1.json). Tests:
`python3 cli/test_geo_watch.py` (offline; every provider is faked).

## As a GitHub Action

```yaml
- uses: jianruntech/geo-score@v1
  with:
    url: https://example.com
    fail-under: 40
    fail-on-gate: true          # a gate at zero caps the score at exactly 40, which fail-under 40 cannot catch
    json-out: geo-score.json
    sarif: geo-score.sarif      # optional
    junit: geo-score.xml        # optional
```

The action scores the site once. That one run prints the evidence to the log, writes the scored
table to the job summary, annotates checks at zero (gates as errors, other checks as warnings;
`annotations: false` turns this off) and writes whichever files you asked for. `fail-on-gate: true`
fails the job when a gate scores zero, and `assert` takes the same expressions as `--assert`, one per
line; each failed one is an error annotation. Outputs: `score`,
`band`, `gate-capped`, `report` and `report-path`. Inputs reach the script as environment
variables, never pasted into it, so a URL cannot run shell code.

To see the results in the repository's Security tab, upload the SARIF file
([example](../examples/ci/github-actions.yml)). Code scanning needs every result in a file of the
checkout, so each one points at its check's line in the JSON report (the action writes it into the
workspace when `sarif` is set), and names the scored site in its message.
