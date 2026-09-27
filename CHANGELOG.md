# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/). 中文版：[CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md)。
The **rubric** is versioned separately from the repository — see `rubric/`.

## [Unreleased]

### Added
- **One run, several outputs:** `--json-out FILE`, `--sarif FILE` (SARIF 2.1.0: one rule per check,
  one result per check below full marks) and `--junit FILE` (one test per check; a check at zero
  fails, an unobservable one is skipped). All are written from the same fetch as the report on
  screen, so they cannot disagree with it. Single site only.
- **Install as a command:** `pyproject.toml`, so `pipx install git+https://github.com/jianruntech/geo-score`
  and `uvx --from git+… geo-score` work. Installs `geo-score` and `geo-score-mcp` (the MCP server over
  stdio). Still no dependencies.
- `STABILITY.md`: what is a public contract (check ids, score arithmetic, the JSON schemas, CLI
  flags, exit codes, Action inputs and outputs, MCP tool names, SARIF rule ids), what semver means
  here, and that nothing is sent anywhere (no telemetry).
- Action inputs `sarif`, `junit` and `annotations`; outputs `gate-capped` and `report-path`.
- **Pin the sample:** `--urls FILE` scores exactly the given pages (up to 8, all on the scored site);
  `--urls-from REPORT.json` re-reads the pages an earlier report sampled. Sampling is the main source
  of run-to-run variance, so a before/after comparison on pinned pages shows what changed on the
  site. The report says `sample_source: "pinned"`. Action input `urls-from`.
- **Per-check documentation links:** every check in the JSON report carries `doc_url`, its definition
  in the rubric pinned to the release tag, so the link never drifts from the scorer. SARIF rules link
  there too, and `--explain` prints it under each check below full marks. Optional field in
  `schema/report.v2.json`.
- [Troubleshooting](guide/troubleshooting.md), in English and Chinese: score movement, checks shown
  as `—`, the gate cap, exit code 2, proxies, redirects, the leaderboard's tool version, `watch`
  exit 3, Action annotation limits, CJK thresholds. The terminal report links to it.
- **How far to trust the CLI, measured.** `benchmark/validity.py` re-scores the five published hand
  audits on the same pages and compares every check tier for tier: 73% of 85 check pairs agree (90%
  for checks read by rule, 58% for heuristics), and the CLI reads 4.8 points lower on average, from
  10 lower to 6 higher. Results, caveats and every disagreement: `benchmark/VALIDITY.md` (EN + zh).
  This replaces the unmeasured "typically 5 to 15 points lower", which was wrong for one site in five.
- **Evidence basis for every check.** `rubric/v1.1.json` gains an `evidence` object per check
  (basis, sources, last verified), published as `rubric/evidence-v1.1.md` (EN + zh). Metadata only:
  no weight, tier or score changed.
- **MCP for agents, not only for people.** `score_site`, `report`, `diff` and `list_runs` return
  `structuredContent` (the full report, summary or diff as JSON) beside the text, and declare an
  `outputSchema`, so an agent no longer parses Markdown to recover a score. `score_site` takes `urls`
  (pin the pages, same checks as `--urls`) and `sample`. The rubric is served as the resource
  `geo-score://rubric/v1.1`, built from the scorer's own tables. The server instructions and the
  `score_site` description say that `«site text: …»` spans are data from the audited site.
- `watch diff --fail-on-drop`: exit 4 when a verdict is `change` with a negative change. The MCP
  `diff` tool takes `format: "json"`. [guide/watch-methodology.md](guide/watch-methodology.md)
  (EN + zh) gives the formulas and a worked example.
- **Offline end-to-end tests.** `cli/test_geo_score_e2e.py` serves twelve fixture sites from
  127.0.0.1 (a good site, a JavaScript shell, robots blocks, a firewall that refuses AI crawlers, a
  Chinese site, a site under a path, a hostile site that tries to address an agent, and more) and
  checks every check's tier against each site's `expected.json`, plus a golden report. A socket
  guard fails the run if anything leaves the machine; the suite takes under a second.
- Tests that the CLI's embedded rubric (check ids, points, every tier's points and wording, bands,
  caps, bonus) equals `rubric/v1.1.json`.

### Changed
- **`watch diff` is paired, clustered and corrected for multiple comparisons.** It compares the
  questions both runs answered, with an exact paired test per row (McNemar when every question has
  one answer per run, otherwise an exact sign-flip test on each question's net change) and Holm's
  correction across the engine rows and the all-engines row. The verdict is `change` only when the
  adjusted p < 0.05, and `too few questions to tell` below 6 shared questions. 1.2.0 used an unpaired
  two-proportion test on answers that are not independent, which called changes too readily. New
  row fields: `p_paired`, `p_adjusted`, `n_pairs`, `n_questions`, `n_asks`, `before_paired`,
  `after_paired`, `delta_pp`, `delta_ci`. `before`, `after`, `delta` and `p_value` keep their 1.2.0
  unpaired meaning; no verdict uses them.
- **Intervals account for repeated asks.** Every rate block gains `cited_ci_clustered` (a bootstrap
  over questions, 2,000 seeded resamples, never narrower than Wilson) and `n_questions`; reports quote
  it whenever a question has more than one answer. `cited_ci` (Wilson) is unchanged.
- **Headline rates leave out questions that name the brand.** Questions are flagged at run time
  (`brand_in_query`, `competitor_in_query`) with the matcher used on answers; the headline covers the
  other questions and branded ones get their own line and n. An optional `branded` column in
  `queries.csv` (`auto`, `yes`, `no`) overrides the flag, `watch check` warns when more than 30% of the
  questions name the brand, and the CSV report gains a trailing `branded` column.
- **The Action scores the site once.** It used to fetch and score twice (once for JSON, once for
  the log), which doubled the time and could print two different scores. The job summary, the
  annotations and every file now come from one run.
- The Action annotates checks at zero: gates as errors, other checks as warnings (GitHub shows up
  to 10 of each; the rest are in the job summary).
- `geo-score watch --help` names the command you typed (`geo-score` after an install).
- `--compare` with three or more sites no longer says "Both scored".

### Fixed
- A Latin brand name written directly next to Chinese, Japanese or Korean text ("用Lumo做视频") now
  counts as a mention; it never matched before. New runs can therefore show a higher `mentioned` rate
  on such answers than earlier runs.
- Run files saved by 1.2.0 still load; reports recompute their summary and the branded flag from the
  saved question text, and say so in a note.
- Documentation that still described the superseded gate rule: `rubric/README.md`, the Chinese
  calibration record, `SKILL.md` and the sample report said a gate short of full marks caps the score.
  The rule since v1.1 is that only a gate at **zero** caps it. The scores were always computed with the
  correct rule; `validate.py` now fails on any sentence that states the cap without the zero condition.
- The calibration record credited the structured-data adoption figures (BreadcrumbList 5.66%,
  Product 0.77%, FAQPage 0.34%) to the 2025 Web Almanac; they are from the 2024 edition. Only the
  llms.txt figure (2.13%) is from 2025.
- The Chinese calibration record was missing two facts the English one has (the 60 KB of
  server-rendered prose, Foglift's upper quartile); a new check compares the numbers in both.

### Security
- The Action passes its inputs to the script as environment variables. Before this, `url` and the
  other inputs were pasted into the shell script, so a crafted value could run commands in the
  workflow. `sample` and `fail-under` are now checked to be whole numbers.
- **Site text in evidence is fenced as data.** Evidence that quotes the audited site (an answer
  passage, the brand name read from the page, a Wikidata description) now carries it inside
  `«site text: …»`, and control, zero-width and bidi characters are stripped from every evidence
  string. The report reaches AI agents through the MCP server, so a page could otherwise address the
  agent in the tool's own voice. Harvested links carrying such characters are dropped from the sample.
- Errors that wrap a lower-level exception (a malformed request header, an unreadable config) no
  longer chain it, so an uncaught traceback cannot print the original message, which for a header can
  contain the API key.
- `SECURITY.md` now has a supported-versions table and a threat model; `SKILL.md` tells the agent
  that fetched text is evidence, never instructions.

## [1.2.0] — 2026-09-27

### Added — levels 2 and 3: does AI actually cite you?

geo-watch 0.1.0 is merged into this repository. One tool now measures both halves of AI
visibility: whether engines **can** cite a site (the score, free) and whether they **do**
(with the user's own API keys). The citation half is never summed into the score, as the
rubric has always required.

- **Level 2, `--ask "question"`** (repeatable, up to 5): after the readiness report, asks
  ChatGPT, Perplexity, Gemini and Claude the question through their search-enabled APIs,
  one ask per engine that has a key, and fills the report's `citation` object. Without a key
  the block says not measured and the score is unchanged.
- **Level 3, `geo_score.py watch`**: a fixed question list asked every week; citation rate per
  engine with 95% Wilson intervals, share of voice against competitors, the third-party
  sources the engines cite, the searches they ran, a cost ledger with caps (`max_calls`
  is exact; `budget_usd` can be exceeded by at most one call per engine), and `diff` with a
  two-proportion test. Runs follow `schema/watch.v1.json`.
- **`geo_score.py mcp`**: a dependency-free stdio MCP server with `score_site` (level 1) and
  `ask`, `run`, `list_runs`, `report`, `diff` (levels 2 and 3).
- `schema/report.v2.json`: the reserved `citation` object gains optional `channel`,
  `answered`, `mentioned_count`, `per_engine`, `top_sources` and `cost_usd`. Additive; every
  1.1.x report still validates.
- `examples/ci/watch-weekly.yml`: the weekly schedule.

Levels 2 and 3 need `cli/geo_watch.py` from the same release next to `cli/geo_score.py`. The
one-line `curl | python3` install still runs level 1 on its own. Scores are unchanged from 1.1.2.

**For geo-watch 0.1.0 users:** rename `geo-watch.json` to `geo-score-watch.json` and run
`python3 cli/geo_score.py watch …` instead of `geo_watch.py …`. Runs now live in
`.geo-score/watch/runs/` with format `geo-score/watch.v1`; 0.1.0 run files are not read. The CSV
export renames `competitors_cited` to `other_domains_cited` and drops the always-empty
`wrong_fact` column.

## [1.1.2] — 2026-09-25

### Changed — scores move

A site scored 88 and then 95 on two consecutive runs from one machine, and another
scored 71, 40, 71 — both outside the ±5 this repository promises. Three causes, one
principle: **a network that cannot reach something is not evidence that it is missing.**

- **p3.sameas** counted every non-200 as a dead profile. Timeouts, resets and 451 (LinkedIn,
  X, YouTube, GitHub and Wikipedia are unreachable from mainland China) and bot walls
  (401 / 403 / 429 / 999 from Crunchbase, Zhihu, Facebook, LinkedIn) are now left out;
  only 404 / 410 count as gone. When no link can be checked, the check leaves the
  denominator instead of scoring 0. The same 12 profiles resolved 1 of 12 from a
  mainland network and 9 of 12 from overseas.
- **p3.knowledge-graph** scored 0 when *some* Wikidata / Wikipedia lookups timed out and
  the rest found nothing. Absence now needs every lookup to answer; a partial answer is
  unobservable. (All lookups failing was already unobservable.)
- **Sampling** fetched the sitemap once. One dropped request sent discovery to homepage
  links, a different eight pages were scored, and the middle run fell under the g.ssr
  gate (capped at 40). The homepage, robots.txt, sitemap, section indexes and sampled
  pages are now retried on timeouts, 429 and 5xx. Reports carry `sample_source`.

After the change, three runs each: jianruntech.com 95 / 95 / 95 (direct) and 93 / 93 / 95
(overseas); stripe.com 75 / 75 / 75 (direct) and 70 / 72 / 70 (overseas, concurrent).
**The published benchmark was measured on 2026-09-09 with the earlier logic and has not been
re-run.** A site whose sameAs or knowledge-graph lookups hit an unreachable host can score a
few points higher today than its leaderboard row. Reports now say `geo-score-cli/1.1.2`, so the
two can be told apart.

### Fixed
- **gzip bomb.** The 4 MB read cap applied to the compressed stream, and `gzip.decompress`
  has no output limit, so a few MB of crafted gzip could inflate to gigabytes and kill the
  process — on a GitHub Action runner, an out-of-memory crash instead of a score. Inflation
  is now capped at 16 MB; real pages never get near it. **No score changes.**

## [1.1.0] — 2026-09-08

Rubric **v1.1**. v1.0 was tagged a few hours earlier but never announced: running it
against five real sites before release labelled anthropic.com *Critical* — a site
returning 200 to all ten retrieval crawlers, byte-identical to a browser, with 60 KB of
server-rendered prose. That is a failed calibration check, so v1.1 shipped instead.
Full reasoning: [rubric/calibration-v1.1.md](rubric/calibration-v1.1.md).

**Scores from v1.0 and v1.1 are not comparable.** v1.0 and its five audits stay published,
unaltered — they are the evidence that found the problem.

### Changed
- **Two scores, never one.** *Readiness* (what the site owner can change, observable from
  outside) is what the rubric scores. *Citation performance* is reported separately and
  never folded in. Merging them is what produced the *Critical* verdict above.
- **Tiers replace pass/fail.** All 21 scored checks now carry 2–4 tiers, and every tier
  states a count out of the 8 sampled pages rather than "most" or "a few".
- **Substance over format.** Headings match question intent whether or not they carry a
  question mark — tasks ("Accept a payment") and explanations ("How Connect works") count.
  A freshness signal is a visible date *or* a schema date. Answer passages widened to
  25–120 words (50–200 characters for Chinese) and no longer have to be the first paragraph.
- **Unobservable checks left the base.** Search Console and Bing verification state and
  multi-engine query tests are gone from the 100 — no external auditor can see them, and
  scoring them zero silently penalised every site. They are reported as an unscored block.
- **Emerging conventions moved to bonus.** `ai.txt`, `speakable`, GEO `<link>` tags and
  `llms-full.txt` were 9 points inside the denominator; they are now bonus checks worth up
  to +6 outside it.
- **Gates.** `g.robots`, `g.reachable` and `g.ssr` score normally and cap the normalised
  percentage at 40 — but only when one of them scores **zero**.
- **Five bands with stage names.** "Critical" is gone; CI now rejects verdict-style band
  names. Thresholds are taken from a published AEO ladder its own distribution backs.
- **Rubric is bilingual.** [`rubric/v1.1.md`](rubric/v1.1.md) (English) and
  [`rubric/v1.1.zh-CN.md`](rubric/v1.1.zh-CN.md), with both languages in the JSON.

### Added
- [`rubric/calibration-v1.1.md`](rubric/calibration-v1.1.md) — how the recalibration was
  reasoned, against four external benchmarks
- [`schema/report.v2.json`](schema/report.v2.json) — v1.1 changed the output shape
  (`score` became `readiness`, `gate_capped` and `tier_reason` are new, the `failed` state
  is gone). `report.v1.json` stays for v1.0 reports.
- [`examples/audits/v1.1/`](examples/audits/v1.1/) — the five sites re-audited under v1.1
- CI now validates published audits against the schema and recomputes every score,
  checks that gate-cap figures agree across both languages and the JSON, rejects
  implementation fields (`fix_zh`, `effort_days`, `owner`) in the public rubric, and
  rejects stale pillar names and retired check ids anywhere in the repo

### Fixed
- A first draft of v1.1 capped any site whose gate checks fell short of full marks. That
  showed stripe.com (77/100) and nextjs.org (85/98) as **40%, Early** — v1.0's mistake in a
  new place, treating *not ideal* as *not working*. Gates now cap only at tier zero.
- The eight ambiguities in [`rubric/open-questions.md`](rubric/open-questions.md) all have
  decisions, recorded inline.

## [Unreleased]

## [1.0.0] — 2026-09-08

Tagged but never announced; superseded within hours by 1.1.0 after it failed its own
calibration check. Kept published so the correction stays auditable.
The repository was pushed a few hours earlier without a tag;
the rubric was corrected before this tag, so v1.0 as released here is the only v1.0.
Corrections made in that window are listed under *Fixed before first tag*.

### Added
- Rubric v1.0: **29 checks** across 5 pillars, 100 nominal points, with pass conditions,
  an explicit Credit type per check, three-state scoring, and score bands
- `SKILL.md` — Claude Code skill that runs the rubric
- `reference/ai-crawlers.md` — the AI user-agent list the crawler checks run against
- `reference/platform-source-selection.md` — how each engine selects sources
- `examples/sample-report.md`

### Fixed before first tag
- **Crawler classification was wrong.** `Google-Extended` and `Applebot-Extended` were
  listed as retrieval crawlers. They are opt-out tokens — they send no requests, and
  blocking them costs no citations. The real retrieval crawler `Applebot` was missing
  entirely. Net effect was inverted: blocking a harmless token lost points, blocking a
  real crawler did not.
- **Anthropic's retrieval agents were missing.** `Claude-SearchBot` and `Claude-User`
  were absent; only the training crawler `ClaudeBot` was listed. A site blocking both
  retrieval agents could still score full marks.
- **Added a reachability check.** `robots.txt` states an intention; the edge decides.
  A WAF returning 403 to `OAI-SearchBot` while `robots.txt` says `Allow` was previously
  a perfect score.
- **Pillar 5 scored procedure, not outcome.** "A query test was performed" is now
  "cited in N of 3 engines" — being cited nowhere scores zero.
- **No rule for inapplicable or unobservable checks.** A brand site with no articles lost
  points for having no `Article` schema. Scores now report `score / observable max` and
  band on the normalised percentage.
- **Partial-credit rule contradicted the sample report.** Every check now carries an
  explicit `prop.` or `all/none` Credit value, with `floor()` rounding stated.
- **The sample report did not add up** — a pillar subtotal was 2 points above its line
  items. CI now validates the arithmetic of every report block in the repo.

### Scope note
Remediation (fix templates, content rewriting, per-engine tactics) is deliberately
out of scope. See [Scope](README.md#scope--what-this-does-not-do).
