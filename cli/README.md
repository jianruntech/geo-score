<p align="right"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>

# geo-score CLI

Score a site against the [AIV rubric v1.1](../rubric/v1.1.md), and, with your own API keys,
check and track whether AI engines cite it. Python 3.8+, standard library only, nothing to
install. Level 1 is `geo_score.py` alone; levels 2 and 3 need `geo_watch.py` from the same
release beside it.

```bash
curl -sL https://raw.githubusercontent.com/jianruntech/geo-score/v1.6.0/cli/geo_score.py \
  | python3 - yoursite.com
```

All three levels come in one package on PyPI: `uvx geo-score@1.6.0 yoursite.com` runs it without
installing, and `pipx install geo-score==1.6.0` installs the `geo-score` and `geo-score-mcp` commands.
Without access to PyPI, the release wheel does the same:
`pipx install https://github.com/jianruntech/geo-score/releases/download/v1.6.0/geo_score-1.6.0-py3-none-any.whl`.

## Options

| Flag | What it does |
|---|---|
| `--brief` | Pillar totals and the three biggest gaps only — what fits in a screenshot |
| `--explain`, `-e` | Print the evidence behind every check, not just the score |
| `--json` | Machine-readable output conforming to [`schema/report.v2.json`](../schema/report.v2.json) |
| `--json-out FILE` | Also write that JSON to FILE, from the same run as the report on screen |
| `--sarif FILE` | Also write [SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html): one rule per check, one result per check below full marks (a gate at zero is `error`, another check at zero `warning`, partial credit `note`). Each result points at the line of its check in the `--json-out` report (or at the SARIF file when there is none), with the site named in the message, which is what GitHub code scanning requires |
| `--junit FILE` | Also write JUnit XML: one test per check. A check at zero fails, a check the CLI cannot observe is skipped, partial credit passes |
| `--sample N` | How many pages to sample, 1 or more (default 8, which is what the rubric specifies) |
| `--timeout SECONDS` | How long each request may wait for the server before it counts as unanswered (default 15, at most 300). A site that cannot be reached fails fast and says why: a name that does not resolve, a refused connection or a failed TLS handshake is not retried |
| `--urls FILE` | Score exactly these pages instead of drawing a sample: one URL per line (or a path such as `/pricing`), `#` comments allowed, up to 8, all on the site being scored. The report says `sample_source: pinned` |
| `--urls-from REPORT` | Score the pages an earlier JSON report sampled (its `sampled_urls`). Re-score with the same pages to see whether the site changed, without sampling noise |
| `--baseline REPORT` | Score the pages an earlier JSON report sampled, as `--urls-from` does, then print what changed since that report, check by check (see [Comparing two reports](#comparing-two-reports)). Not with `--urls` or `--urls-from`. Under `--json` stdout stays the report alone and the comparison is not printed: write the report with `--json-out` and run `diff` on the two files |
| `--fail-on-drop` | With `--baseline`: exit 4 when any check lost points, a gate reached 0 or the band fell since the baseline, one line per reason on stderr. A check that became unobservable is not a drop |
| `--compare URL` | Score another site too and print them side by side. Repeatable. Not with `--json-out`, `--sarif` or `--junit`, which take one site |
| `--badge [FILE]` | Also write an embeddable SVG badge (default `aiv-badge.svg`) |
| `--badge-json FILE` | Also write the same badge as [shields.io endpoint](https://shields.io/badges/endpoint-badge) JSON: `schemaVersion`, `label`, `message`, `color` and `cacheSeconds`, with the SVG's text and colour |
| `--share` | Print a one-line summary sized for a post, plus the badge markdown |
| `--fail-under N` | Exit 1 when the score is below N — for CI |
| `--fail-on-gate` | Exit 1 when any gate check (`g.*`) scores 0, and name the gate and its evidence on stderr. A gate at zero caps the score at 40: a site that would otherwise score 40 or more reads exactly 40 and passes `--fail-under 40`, and `--fail-on-gate` fails any capped site. The same as `--assert 'g.*>0'`. An unobservable gate never fails |
| `--assert EXPR` | Exit 1 unless `CHECK OP VALUE` holds: a check id or an fnmatch glob over the ids, then `>=`, `>` or `=`, then a whole number or `max`, e.g. `g.robots=max` or `p1.llms-txt>=4`. Repeatable. A check the run could not observe prints `not measured, skipped` and never fails. A malformed expression, or a glob that names no check, is a usage error (exit 2). Results go to stderr, never into the report |
| `--quiet`, `-q` | Suppress progress lines on stderr |
| `--version` | Print the tool's version and the rubric version it scores |
| `--ask QUESTION` | Level 2: also ask the AI engines this question through their APIs (your keys) and report who they cite, beside the score. Repeatable, up to 5 |
| `--brand NAME` | With `--ask`: the brand name to look for in answers. Default: the site's domain name, e.g. `stripe` for `docs.stripe.com` |
| `--domain DOMAIN` | With `--ask`: another domain that counts as yours. Repeatable. The scored site, its registrable domain and a redirect's landing domain always count |

Subcommands: `diff BEFORE AFTER` compares two saved reports ([Comparing two reports](#comparing-two-reports)),
and `watch …` and `mcp` are levels 2 and 3 ([Watch](#watch)). `geo_score.py --help` lists them all, with
examples and the exit codes.

`NO_COLOR=1` turns off colour, as does piping to a file. `HTTPS_PROXY` and `NO_PROXY` are honoured.
When a reading looks wrong, see [troubleshooting](../guide/troubleshooting.md).

Exit codes. Level 1: `0` scored, `1` below `--fail-under`, a gate at zero under `--fail-on-gate`, or a
failed `--assert`, `2` the site could not be fetched or served only bot-challenge pages, a pinned URL
list was refused, a usage error (a malformed `--assert` included), a `--baseline` or `diff` file that is
not a report or was scored against another rubric version, or an internal error, reported in one
line with where to file it (`GEO_SCORE_DEBUG=1` shows the traceback), `4` a drop found by
`--fail-on-drop` (with `--baseline`, or on `diff`), when nothing else exited 1. When the site could not be
fetched, the message names the kind of failure, such as `dns`, `timeout` or `http_403`, and links to
[its section in troubleshooting](../guide/troubleshooting.md#could-not-fetch--and-exit-code-2). A site
that served only bot-challenge pages says `bot challenge served to a browser user-agent (…)`, kind
`bot_challenge`. With `--json` (or `diff --format json`), an exit 2 prints a JSON error on stdout
instead of a report ([`schema/error.v1.json`](../schema/error.v1.json)), with the same kind in
`error.kind`; reports of two rubric versions are kind `rubric_mismatch`. Assertions on
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

## Comparing two reports

```bash
python3 geo_score.py yoursite.com --json-out before.json
# … the site changes …
python3 geo_score.py yoursite.com --baseline before.json          # re-score the same pages and compare
python3 geo_score.py diff before.json after.json [--format text|md|json] [--fail-on-drop]
```

`diff` compares two saved reports; `--baseline` scores the site again on the baseline's pages and
prints the same comparison after the report. Both show:

- every check with its points before and after, its max and a state: `up`, `down`, `same`,
  `became unobservable`, `became observable`, or `unobservable` when neither report observed it. A
  check that became unobservable left the denominator; it is never shown as a drop to 0;
- the score and band before and after, and whether a gate cap started or ended, naming each gate
  that reached or left 0;
- the pages added to or removed from the sample. When the pages differ, the comparison says that
  movement on a check mixes change on the site with sampling, reads a total that moved by 5 or less
  as within the measured spread ([REPRODUCIBILITY.md](../benchmark/REPRODUCIBILITY.md)), and notes
  that `g.reachable` is the least stable check. On the same pages, a difference comes from the site.

`--format json` follows [`schema/diff.v1.json`](../schema/diff.v1.json). Two reports of different
rubric versions are not comparable: `diff` exits 2. Reports written by different releases are
compared with a warning, because a release can move a score on its own (the changelog names the
checks), and so are reports of two different targets, whose difference is not a change. `--fail-on-drop` exits 4 when any check lost points, a gate reached 0 or the band fell, as
`watch diff --fail-on-drop` does for citations; without it, `diff` exits 0 whatever moved. `diff`
needs only `geo_score.py`.

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
glance, and a score capped by a gate at zero says `(gate capped)`.

A committed SVG shows the score of the run that wrote it. To keep a badge current without
committing an image, write the same badge as shields.io endpoint JSON:

```bash
python3 geo_score.py yoursite.com --badge-json aiv-badge.json
```

```json
{"schemaVersion": 1, "label": "AIV readiness", "message": "71/100 Solid", "color": "#2f8f52", "cacheSeconds": 86400}
```

Publish the file wherever a URL can reach it (a raw file in a repository, a gist, a release
asset or your own site) and point shields.io at that URL, URL-encoded:

```
![AIV readiness](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2Fmain%2Faiv-badge.json)
```

shields.io caches the JSON for `cacheSeconds` (a day). The badge is as current as the last
run that wrote the file, so re-run it on a schedule or after a deploy. In the
[GitHub Action](../action.yml), the `badge` input writes either file in the same run as the
report (a path ending in `.json` gets the endpoint JSON, any other path the SVG) and the
`badge-path` output says where. Committing or publishing it is a step of your own workflow.

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
| `p4.cn-engines` | Left out unless a sampled page is in Chinese or the host name ends in `.cn` |

The [Claude Code skill](../SKILL.md) scores all 21.

### How far to trust each check

Re-scoring the five published hand audits on the same pages with 1.5.0
([VALIDITY.md](../benchmark/VALIDITY.md)), the CLI matched the auditor's tier on 80% of 84 check
pairs. On the checks both scored it read 2.4 points lower on average (per site from 12 lower
to 10 higher; mean absolute difference 8.8). Its full normalised score read 5.2 points lower on average,
because the hand audits also score `p3.listings`, `p3.mentions` and `p4.question-coverage`, which the
CLI leaves out.

| How the CLI reads it | Checks | Same tier as the hand audit |
|---|---|--:|
| **By rule**: parses a file, a status code or markup and applies the rubric's count | `g.robots`, `p1.*`, `p3.knowledge-graph`, `p3.sameas`, `p4.cn-engines` | 92% of 39 pairs |
| **By heuristic**: approximates a judgement the rubric describes in prose | `g.reachable`, `g.ssr`, `p2.*`, `p3.video`, `p4.answer-shape` | 69% of 45 pairs |
| **Not at all**: needs off-site search or human judgement | `p3.listings`, `p3.mentions`, `p4.question-coverage` | left out of the denominator |

The weakest agreement is `p2.named-author` (1 of 5 sites agree: the CLI scored two higher than the
auditor and two lower), then `p1.page-type`, `p2.answer-passages`, `p2.freshness` and `p3.video`
(3 of 5 each). With 1.3.0 the weakest was `p2.sourced-stats` (the CLI scored higher than the auditor
on 4 of 5 sites); from 1.5.0 a figure's source must sit beside it, and `p2.sourced-stats` now matches
the auditor on 4 of the 5 sites and reads lower on the fifth. Read these with `--explain` before acting
on them.

## Heuristics, stated plainly

Some checks are judgements the rubric describes in prose, and the CLI approximates them:

- **Page language** — each sampled page's language comes from its `<html lang>` or
  `Content-Language` header unless its text contradicts it, else from its script (kana is
  Japanese, hangul Korean, Han alone Chinese) and a few common words for Latin-script text.
  A page declared Chinese, Japanese or Korean keeps its declaration while it carries 30 or
  more such characters. Code samples (`<pre>`, `<code>`) are not read.
  The report's `audience_language` is the most common page language.
- **Answer passages** — takes the first six paragraphs of the main content and looks for
  one of 25–120 words (50–200 characters on a Chinese, Japanese or Korean page) that ends in
  sentence punctuation. A human reader judges whether it truly stands alone.
- **Question intent** — pattern-matches headings for questions, task verbs,
  explanatory and comparison forms, in English and in Chinese, excluding navigation labels
  and brand strings. Pages in other languages are not read; with none left, the check is
  not measured.
- **Sourced statistics** — a figure counts as sourced only when its own block of the main
  content (a paragraph, list item, table cell, definition, caption or quotation), or the next
  block, holds an off-site link, a `<cite>`, a source phrase or a footnote whose note links to a
  source. Links to the site itself, its `sameAs` profiles and social profiles or share buttons are
  not sources, and a page's header, navigation, footer and asides are not read. Years, version
  numbers, dates, identifiers (filing, account and phone numbers) and prices are not figures.
  Source phrases are read in English and Chinese only.
- **Named authorship** — reads the `author` field from JSON-LD, then falls back to
  `rel="author"` and byline patterns (read in English and Chinese pages only), and rejects
  team and brand names.
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
| `watch init [--dir D] [--brand NAME] [--domain D]… [--competitor NAME=DOMAIN]… [--country CC] [--force]` | Write `geo-score-watch.json` (models pinned) and `queries.csv`, with one placeholder question for each of the types `list`, `pricing`, `alternative`, `problem` and `verdict` |
| `watch check` | Validate the config and the questions, count the questions of each `intent_tier`, warn about a `target_url` it cannot use, and show which engines have keys and prices |
| `watch run [--dry-run] [--engines a,b] [--limit N] [--runs N] [--max-calls N] [--budget-usd X] [--allow-unpriced] [--format text\|md] [-q]` | Ask everything and save the run under `.geo-score/watch/runs/`. `--dry-run` prints the plan and its resolution, the fewest questions that must move the same way for `watch diff` to call a change (and `this plan cannot detect a change` when the set has fewer), and exits 0, with or without keys |
| `watch report [RUN] --format text\|md\|csv\|json [-o FILE]` | A saved run. `csv` has one row per answer: `week, query_id, query, intent_tier, engine, cited, quoted_url, rank, other_domains_cited, note, branded, target_cited` |
| `watch report --since DAYS\|--runs A..B [--format text\|md\|json] [-o FILE]` | Several saved runs pooled: those started in the last DAYS days, or from run A to run B, both included. Each must match the newest (same questions, asks per question, engines, models, country and brand domains); otherwise it exits 1 and names every run that differs. Gives the runs, the days they cover, the answers, the headline rate and a row per engine |
| `watch diff [A] [B] [--format text\|md\|json] [--fail-on-drop]` | Before and after, per engine, on the questions both runs answered: the change in points with a 95% interval, an exact paired test Holm-corrected across engines, and a verdict (`change`, `within noise`, `too few questions to tell` or `not measured`). Also lists citations lost and gained. A question whose text changed under the same id is not compared, and a note names it. `--fail-on-drop` exits 4 when a verdict is a change for the worse |
| `watch runs` | Saved runs, their headline rate and the first 8 characters of their `questions_hash`, which two runs share when they asked the same questions |
| `watch ask "question" [--engines a,b] [--brand NAME] [--domain D] [--format text\|md\|json]` | Level 2 without the score: one question to every engine, now, not saved |
| `mcp` | Score and watch over MCP (stdio); see [guide/mcp.md](../guide/mcp.md) |

Every `watch` command except `watch init` takes `-c PATH` for the config (default `./geo-score-watch.json`,
or `$GEO_SCORE_WATCH_CONFIG`); `watch init` writes into `--dir` (default `.`).

`geo-score-watch.json` (the prices below are an example; copy current ones from your provider):

```json
{
  "brand": {"name": "Acme", "domains": ["acme.com"], "aliases": ["Acme Inc"],
            "url_prefixes": ["amazon.com/stores/Acme"]},
  "competitors": [{"name": "Rival", "domains": ["rival.com"]}],
  "queries": "queries.csv",
  "engines": [{"id": "chatgpt-api", "provider": "openai", "model": "gpt-6-luna"},
              {"id": "perplexity-api", "provider": "perplexity"},
              {"id": "deepseek-via-openrouter", "provider": "openrouter", "model": "deepseek/deepseek-chat"}],
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
| `country` | Two-letter code passed to the engines that accept a location: OpenAI, Claude and Perplexity apply it; Gemini and OpenRouter ignore it |
| `runs` | Asks per question per engine. `3` gives steadier rates at three times the cost |
| `max_calls` | Exact cap on questions asked in one run |
| `budget_usd` | Spend cap, checked before every call; it can be exceeded by at most one call per engine. With a budget, unpriced engines are left out unless `--allow-unpriced` |
| `prices` | Per engine, USD: `input_per_mtok`, `output_per_mtok`, optional `per_search`, `per_call`. Perplexity and OpenRouter report their own cost |
| `engines[].api` | Gemini only: `interactions` (default) or `generate_content` |
| `engines[].key_env` / `base_url` | Read the key from another variable; point at a compatible endpoint (`https://` or `http://localhost`) |
| `engines[].tool`, `max_searches`, `max_tokens`, `max_results` | Provider tuning: the web-search tool version (OpenAI, Anthropic), searches and output tokens per answer (Anthropic), results per search (OpenRouter) |
| `engines[].timeout` | Seconds to wait for this engine's answer, 10 to 600 (default 120). A slow endpoint, or a model that searches and reasons at length, may need more; a request that timed out is not retried and may still be billed |

An OpenRouter engine measures that model answering through OpenRouter's `web` plugin, not the vendor's own app
or search: for a model without native search, such as `deepseek/deepseek-chat`, the plugin searches with Exa
(OpenRouter's documentation, checked 2026-10-02). The engine id names a model route, not a product.

The file's keys are specified in [schema/watch-config.v1.json](../schema/watch-config.v1.json)
(JSON Schema draft 2020-12). `watch init` writes `"$schema"` as the first key, pointing at it, so an
editor that reads JSON Schema checks and completes the file as you type.

A key nothing reads is a warning, never dropped in silence: a typo such as `budget` for `budget_usd`
would otherwise remove a spending cap without a word. `watch check` names every unknown key at every
level (top, `brand`, `competitors[i]`, `engines[i]`, `prices.<id>`), with the nearest known key when
one is close, as in `unknown key 'budget' (did you mean 'budget_usd'?); it is ignored`, and flags a
`prices` entry that names no engine. `watch run` and the other commands that read the config print
the same warnings on stderr, and the MCP `status` tool lists them. A key named like a credential
(`api_key`, `OPENAI_KEY`, `api_token`, `client_secret`, `credentials` …) is pointed at environment
variables instead, and its value is never printed. The warnings change no exit code.

`queries.csv` has four columns, `query_id,query,intent_tier,target_url`. Write the questions the
way a buyer would type them into ChatGPT, and keep the set fixed from week to week. An optional
fifth column, `branded` (`auto`, `yes` or `no`; empty means `auto`), overrides the automatic check
for questions that name the brand. Use `no` when the brand name is also a common word, and `yes` for
a nickname the matcher cannot see.

`target_url` is optional: the one page of yours a question tracks. Write an absolute `http(s)` URL,
or a path that starts with `/`, which is joined to the first of `brand.domains`
(`/pricing` becomes `https://acme.com/pricing`). `watch check`, `watch run` and the MCP `run` and
`status` tools warn about any other value, and the run ignores it; they also warn, and the run still
matches, when the page is not on a domain or URL prefix the brand owns. Each answer to the question then records `target_cited` (one of its citations is
that page) and `other_own_cited` (it cites another URL of yours, not that page), and the report
adds a table, "Pages you track": per page, its questions, their answers, how many cite the page,
how many cite another of your URLs instead, and which of your URLs those answers cite most, shown
exactly as cited. The CSV's last column, `target_cited`, is `Y` or `N` on an answer to a question
that tracks a page and empty otherwise. The match is the exact page after normalisation: `www`,
letter case, a trailing slash, the query string, the fragment and percent-encoding are set aside,
so `https://www.acme.com/Pricing/?utm_source=x#plans` is `https://acme.com/pricing`. Nothing else
is: `/en/pricing` is not `/pricing`, and a page cited by its canonical URL, when that URL differs,
is another page. A citation left as an unresolved redirect counts as neither. For a run saved
before 1.6.0 the table is computed from the saved citations.

`intent_tier` is free text. The report gives each value its own rate ("By question type"), and
`watch check` prints how many questions have each one, with a note, never a failure, when every
question has the same type or none has one. A set of one type measures that one kind of question.
These labels are suggested, so that sets read alike:

| `intent_tier` | The question | Example |
|---|---|---|
| `list` | asks for the options in a category | best invoicing app for freelancers |
| `vs` | compares named products | acme vs rival |
| `alternative` | asks what to use instead of a named product | alternatives to rival |
| `pricing` | asks about cost, plans or a free tier | how much does an invoicing app cost |
| `problem` | describes a situation and names no category or brand | clients keep paying me late and I lose track of who owes what |
| `persona` | says who it is for | invoicing app for a two-person design studio |
| `verdict` | asks whether something is worth it or can be trusted | is acme worth it |
| `channel` | is about buying or selling through another route: franchise, wholesale, distributor, procurement | invoicing software with a reseller programme |

A `verdict` question about your own brand names it, so it counts on the branded line, not in the
headline.

**Reading the numbers.** The headline rate counts only questions that do not name the brand.
"acme vs rival" all but guarantees an Acme citation, so those questions get their own line, and
`watch check` warns when they are more than 30% of the set. When a question has more than one
answer (`runs` > 1, or several engines in the overall line), the 95% interval is a bootstrap over
questions, because answers to one question move together; otherwise it is Wilson. Call something a
change only when `diff` says `change`. Formulas and a worked example:
[guide/watch-methodology.md](../guide/watch-methodology.md).

**Pooling runs.** One run is one day's answers. `watch report --since 30` (or `--runs A..B`) counts the runs
of a period as one set of answers, so each question's rate rests on more answers and one unusual day weighs
less. It pools only runs that asked the same questions (the same `questions_hash`) as many times each (the same
`runs`), on the same engines with the same models, from the same `country`, with the same brand domains and URL
prefixes as the newest run in the window, and refuses otherwise, naming each run that differs and why. Its 95% interval treats every answer to one
question, from every run and engine, as one cluster: more runs narrow it only as far as the number of questions
allows. A pooled rate describes a period; it is not a test for a change, and there is no pooled diff. The JSON
follows `$defs/pooled` in [schema/watch.v1.json](../schema/watch.v1.json); the MCP `report` tool takes `since`.
Before a run, `watch run --dry-run` prints the plan's resolution: with E engines, `watch diff` tests E + 1 rows
(one row with one engine), and a change can be called only when at least k questions move the same way, k being
the smallest n with rows × 2 / 2^n < 0.05: 6 questions with one engine, 7 with two, 8 with three to five. More
questions help; more engines raise k; more asks per question (`runs`) do not lower it.
[guide/watch-methodology.md, One ask, one day, one month](../guide/watch-methodology.md#8-one-ask-one-day-one-month).

**Who is named for each question.** `watch report` lists every question with the number of answers
it got and, out of those, how many cite and name you, how many cite and name each competitor, how
many name no tracked brand, how many searched the web (yes, no or unknown), and the tracked brand
cited most often when the question has at least 4 answers and one brand is ahead of every other.
These are counts, not rates. Whether an answer searched is read from the saved answer: yes when the
provider reported a search, exposed a search query or the answer cites a URL; no when an OpenAI,
Gemini or Anthropic answer shows none of these; unknown for every Perplexity and OpenRouter answer,
because those APIs search on every call or do not say. The JSON
report and the MCP `report` tool carry the same table as `summary.by_question`; for a run saved
before 1.6.0 it is computed from the saved answers.

**Who is named first.** Each answer records, for your brand and each competitor, `mention_order` and
`mention_share`. `mention_order` is 1 for the brand the answer names before every other brand in your
config, 2 for the next, and so on, by the earliest match of its name, aliases or domains with the
matcher of `mentioned`; it is null when the answer does not name the brand, and for two brands first
named at the same place, one name inside the other. `mention_share` is the share of the answer's
sentences that name the brand, every sentence counted the same: a sentence ends at a line break, at
`。！？`, or at `.` `!` `?` before whitespace, and a piece with no letter or digit, such as a table rule,
is not a sentence. With competitors in the config, "By engine" gains a column, *named first
(tracked)*: the answers that name you first among the brands you track, out of the answers that name
at least one of them. "Share of voice" gains *named first (tracked)* for every brand and *sentence
share*, the mean `mention_share` over the answers that name it. Brands your config does not list are
invisible to both, so first among the brands you track may not be first in the answer, and the order
is the order of first mention, not a position in a list. Both are read from the answer as saved, which
keeps its first 20,000 characters (`answer_truncated` marks an answer that was cut). The JSON report
carries them as `named_first`, `any_named` and `mention_share` on each row of `summary.engines` and
`summary.share_of_voice`; for a run saved before 1.6.0 they are computed from the saved answers.

**Over MCP.** `uvx geo-score@1.6.0 mcp` (`geo-score-mcp` after a pipx install, `geo_score.py mcp` from a
clone) serves all three levels to an agent over stdio, with the same config and caps. It reads keys from its own environment, which a desktop
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
    fail-on-gate: true          # a gate at zero caps the score at 40; a capped site at exactly 40 passes fail-under 40
    json-out: geo-score.json
    sarif: geo-score.sarif      # optional
    junit: geo-score.xml        # optional
    badge: aiv-badge.json       # optional: shields.io endpoint JSON (.svg for an SVG)
```

The action scores the site once. That one run prints the evidence to the log, writes the scored
table to the job summary, annotates checks at zero (gates as errors, other checks as warnings;
`annotations: false` turns this off) and writes whichever files you asked for. `fail-on-gate: true`
fails the job when a gate scores zero, and `assert` takes the same expressions as `--assert`, one per
line; each failed one is an error annotation. `badge: aiv-badge.json` (or
`.svg`) writes a badge. `baseline: before.json` scores the pages of an earlier report (from
`json-out`) and compares, as `--baseline` does: the comparison goes to the log, a *Changes since
baseline* section to the job summary, and the outputs `delta` (the score minus the baseline's) and
`dropped-checks` (the checks that lost points or, for a gate, reached 0, comma-separated) let a later
step fail on a regression alone. Outputs: `score`, `band`, `gate-capped`, `report`, `report-path`
and, with `badge`, `badge-path`; with `baseline`, `delta` and `dropped-checks`. Inputs reach the script as environment
variables, never pasted into it, so a URL cannot run shell code.

To see the results in the repository's Security tab, upload the SARIF file
([example](../examples/ci/github-actions.yml)). Code scanning needs every result in a file of the
checkout, so each one points at its check's line in the JSON report (the action writes it into the
workspace when `sarif` is set), and names the scored site in its message.
