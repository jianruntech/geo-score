# Glossary

The terms you meet in geo-score's README, its reports and its guides, in alphabetical order. Each
entry says what the term means, where it shows up and which page goes deeper. This page defines words
and commands; it does not say how to change a site.
Chinese version: [glossary.zh-CN.md](glossary.zh-CN.md)

[A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [G](#g) · [H](#h) · [J](#j) · [L](#l) · [M](#m) ·
[N](#n) · [O](#o) · [P](#p) · [R](#r) · [S](#s) · [T](#t) · [W](#w)

## A

### AEO

Answer engine optimization: work aimed at getting a site quoted in the answers of answer engines, a
term for much the same field as GEO. The rubric's band cut-offs are taken from an AEO ladder published
by GW Content.

**Where:** the Bands section of the rubric. **More:** [rubric v1.1, Bands](../rubric/v1.1.md#bands)

### AIV, AIV readiness

AIV stands for AI visibility: whether AI answer engines can find, parse, trust and cite a site. AIV
readiness is the 0–100 score the rubric gives for it, and it measures whether engines *can* cite the
site, not whether they *do*.

**Where:** the first line of the terminal report (`AIV READINESS`), the badge's label, the rubric's
title.
**More:** [rubric v1.1, Two scores. Never one](../rubric/v1.1.md#two-scores-never-one)

### Answer engine

An AI system that answers a question in prose and cites the sources it drew on, instead of returning
a ranked list of links: ChatGPT search, Perplexity, Google AI Overviews, Gemini or Copilot. It
retrieves passages, decides whether a source is worth quoting, and cites it.

**Where:** `--help` ("whether AI answer engines can find, parse, trust and cite it"), the README and
the rubric. **More:** [README, Why this is a different question from SEO](../README.md#why-this-is-a-different-question-from-seo)

## B

### Band

The name of a range of the 0–100 score: Not started (0–30), Early (31–50), Growing (51–65), Solid
(66–82) and Leading (83–100). A band names a stage, not a verdict, and it is read from the score after
any gate cap.

**Where:** next to the score in the terminal report, with `N points to <band>` under it; the JSON field
`band`; the badge, whose colour follows the band; `diff` and `--fail-on-drop` ("the band fell").
**More:** [rubric v1.1, Bands](../rubric/v1.1.md#bands)

### Baseline

The earlier JSON report a new score is compared with. `--baseline REPORT` scores the site again on the
pages that report sampled and prints what changed since it, check by check.

**Where:** `--baseline REPORT`, and with it `--fail-on-drop`, which exits 4 when a check lost points, a
gate reached 0 or the band fell; the GitHub Action's `baseline` input and its `delta` and
`dropped-checks` outputs. **More:** [CLI reference, Comparing two reports](../cli/README.md#comparing-two-reports)

### Biggest gaps

The three checks with the most points to gain at their next tier, with any gate at zero first. Each
line gives the points the next tier adds and the points to full marks, and the full report adds the
next tier's condition as the rubric states it (`needs: …`).

**Where:** the terminal report and `--brief`; the MCP tool `score_site` lists its gaps in the same
order. **More:** [rubric v1.1, Report shape](../rubric/v1.1.md#report-shape)

### Bonus

Four `b.` checks (`b.llms-full`, `b.ai-txt`, `b.geo-link`, `b.speakable`) with no tiers: each is met or
not. Their points add to readiness up to +6 but stay outside the denominator, and the 0–100 score
never goes above 100.

**Where:** `+N bonus (outside the denominator)` in the report; the JSON field `bonus_awarded` and the
`b.` entries in `checks`. **More:** [rubric v1.1, Scoring rules](../rubric/v1.1.md#scoring-rules) (rule 5)

### Bot challenge

A page that bot protection (AWS WAF, Akamai, Cloudflare and the like) serves instead of the site's
page, which only a browser that runs its script can pass. It is never scored as the site's content: a
challenged page leaves the sample, and a site that serves nothing but challenges is not scored.

**Where:** the note `Scored on N of M sampled pages; …`; exit code 2 with a message that starts
`bot challenge served to a browser user-agent`, kind `bot_challenge` under `--json`.
**More:** [troubleshooting, bot_challenge](troubleshooting.md#bot_challenge-a-challenge-page-came-back-instead-of-the-site)

### Branded question

A tracked question that names your brand, such as "acme vs rival", which engines answer by citing you
almost every time. `watch` flags these questions, keeps them out of the headline cited rate and
reports them on a line of their own.

**Where:** the optional `branded` column of `queries.csv` (`auto`, `yes` or `no`); `brand_in_query` in
run files; the warning `watch check` prints when they are more than 30% of the set.
**More:** [watch methodology, Questions that name the brand](watch-methodology.md#3-questions-that-name-the-brand)

## C

### Check, check id

A check is one criterion of the rubric: what is measured, its tiers, and why it matters for
retrieval. Its id is a stable name made of a prefix and a slug, such as `p2.freshness`: `g.` for the
gates, `p1.` to `p4.` for the Understandable, Content Citability, Brand Credibility and Answer Fit
pillars, and `b.` for the bonus checks.

**Where:** `--explain`; the JSON field `checks[].id`; `--assert`; SARIF rule ids and JUnit test names;
the MCP prompt `explain_check`. Check ids are a public contract ([STABILITY.md](../STABILITY.md#public-contracts)).
**More:** [rubric v1.1](../rubric/v1.1.md)

### Citation

An answer cites you when it links to a URL you own: one of your domains (subdomains included), or a
URL prefix you declared, such as your store on someone else's site. Whether engines cite you is an
outcome that levels 2 and 3 report beside the readiness score, never added to it.

**Where:** the citation block under the report with `--ask`; the JSON `citation` object; the `cited`
column of `watch report`. **More:** [README, Levels 2 and 3](../README.md#levels-2-and-3--does-ai-actually-cite-you),
[rubric v1.1, Two scores. Never one](../rubric/v1.1.md#two-scores-never-one)

### Cited rate

The share of the answers that came back which cite you, with a 95% interval: Wilson when each question
was answered once, a bootstrap over questions when a question has several answers. The headline rate
counts only the questions that do not name the brand.

**Where:** `Cited in N% of answers …` in `watch report`; the headline rate in `watch runs`;
`summary.headline` in run files. **More:** [watch methodology, The unit](watch-methodology.md#1-the-unit-an-answer-clustered-by-question)

## D

### Denominator

The sum of the maximum points of the checks a run observed; the 0–100 score divides the points
scored by it. A check that was not observed leaves the denominator instead of scoring 0, and bonus
checks are never in it.

**Where:** the report's footer (`N checks left the denominator`) and legend
(`⊘ not measured (left the denominator)`). **More:** [rubric v1.1, Scoring rules](../rubric/v1.1.md#scoring-rules) (rule 3)

### Diff

A comparison of two saved results. `geo_score.py diff BEFORE AFTER` compares two level 1 JSON reports
check by check (`up`, `down`, `same`, `became unobservable`, `became observable`, or `unobservable`
when neither report observed the check), and `watch diff [A] [B]` compares two watch runs, by default
the latest two, with a paired test and a verdict: `change`, `within noise`, `too few questions to tell`
or `not measured`.

**Where:** `diff --format text|md|json` (the JSON follows `schema/diff.v1.json`); `watch diff`; the MCP
tool `diff`, for watch runs. With `--fail-on-drop`, either exits 4 on a drop.
**More:** [CLI reference, Comparing two reports](../cli/README.md#comparing-two-reports),
[watch methodology, The diff](watch-methodology.md#4-the-diff-a-paired-test-per-row)

## E

### Engine

An answer engine as levels 2 and 3 reach it: a provider's API with web search switched on, named by an
engine id (`chatgpt-api`, `perplexity-api`, `gemini-api`, `claude-api`, or an id you give an
OpenRouter model). API answers are not the answers of the consumer apps, so API runs are compared
only with API runs.

**Where:** `engines` in `geo-score-watch.json`; `watch run --engines`; the By engine table of a watch
report; the `engines` argument of the MCP tools `ask` and `run`.
**More:** [README, Levels 2 and 3](../README.md#levels-2-and-3--does-ai-actually-cite-you)

### Evidence

The observation behind a check's reading that someone else can reproduce: a status code, a byte count,
the sentence that did or did not qualify. A judgement without evidence does not stand.

**Where:** `--explain`; the JSON fields `checks[].evidence` and `tier_reason`, or `reason` for a check
that was not observed; SARIF and JUnit messages. **More:** [rubric v1.1, Scoring rules](../rubric/v1.1.md#scoring-rules) (rule 8)

## G

### Gate

One of the three checks of the Reachable pillar: `g.robots` (retrieval crawlers allowed in
robots.txt), `g.reachable` (reachable to retrieval user-agents) and `g.ssr` (main content
server-rendered). A gate scores like any other check, and at zero it also limits the score: see
*Gate cap*.

**Where:** `GATE AT ZERO — …` at the top of the report; `--fail-on-gate`, the same as
`--assert 'g.*>0'`; SARIF level `error`. **More:** [rubric v1.1, Reachable](../rubric/v1.1.md#reachable--15-points)

### Gate cap

When any gate scores zero, the 0–100 score is capped at 40; a gate at a middle tier is an ordinary
deduction, and a gate that was not observed never caps. The cap is an upper limit, `min(score, 40)`,
applied after the bonus: a site that would otherwise score 40 or more reads 40, and a site that would
score less keeps its own, lower score.

**Where:** the JSON field `gate_capped`; `(gate capped)` on the badge;
`the score cannot exceed 40 while a gate is at zero` in the report. A capped site can read 40 and
pass `--fail-under 40`; `--fail-on-gate` fails every capped site.
**More:** [troubleshooting, a gate scored zero](troubleshooting.md#the-score-is-capped-at-40-a-gate-scored-zero)

### GEO

Generative Engine Optimization: getting a site cited in the answers that AI engines such as ChatGPT,
Perplexity, Google AI Overviews, Gemini and Copilot generate. It has nothing to do with geography or
maps.

**Where:** the tool's name and the README. **More:** [README, Why this is a different question from SEO](../README.md#why-this-is-a-different-question-from-seo),
and the paper [GEO: Generative Engine Optimization (KDD 2024)](https://arxiv.org/abs/2311.09735)

## H

### Hand audit

A reading of all 21 checks by a person following the rubric, with the evidence behind each tier; a
check that does not apply to the site is marked `not_applicable`. The published hand audits are what
the CLI's agreement figures are measured against.

**Where:** `examples/audits/v1.1/`; the README's comparison of the CLI with the hand audits.
**More:** [VALIDITY.md](../benchmark/VALIDITY.md)

### Heuristic

A check the CLI reads by approximating a judgement the rubric describes in prose, as opposed to one it
reads by rule from a file, a status code or markup. The heuristic checks are `g.reachable`, `g.ssr`,
the `p2.` checks, `p3.video` and `p4.answer-shape`, and they match a hand audit less often than the
checks read by rule.

**Where:** the trust table in the CLI reference; the README's CLI-versus-hand-audit figures.
**More:** [CLI reference, How far to trust each check](../cli/README.md#how-far-to-trust-each-check)

## J

### JUnit

The XML test-report format that CI systems display. `--junit FILE` writes one test per check: a check
at zero fails, a check that was not observed is skipped, and partial credit passes.

**Where:** `--junit FILE`. **More:** [CLI reference, Options](../cli/README.md#options)

## L

### Leaderboard

geo-score's public benchmark: well-known sites, grouped by sector, each scored with the same rubric and
the same public tool, with every site's full report published beside the table. It is a dated
measurement, not a contract, and its data records the tool version and the day it was measured.

**Where:** [jianruntech.com/leaderboard](https://www.jianruntech.com/leaderboard); `benchmark/README.md`;
`results.json`, `results.csv`, `checks.csv` and `raw/` in `benchmark/`.
**More:** [benchmark/README.md](../benchmark/README.md), [STABILITY.md, Benchmark data](../STABILITY.md#benchmark-data)

### Levels 1, 2 and 3

geo-score's three uses: level 1 scores readiness against the rubric, free and with no key; level 2
puts a question to the engines once, through their APIs with your keys; level 3 tracks a fixed set of
questions week over week. Levels 2 and 3 measure citations and are never added to the score.

**Where:** `geo_score.py URL` (level 1); `--ask QUESTION` and `watch ask` (level 2); `watch run`,
`watch report` and `watch diff` (level 3); the level column of the MCP tool table. Levels 2 and 3
need `cli/geo_watch.py` beside `cli/geo_score.py`. **More:** [README, Three levels, one tool](../README.md#three-levels-one-tool)

## M

### MCP prompt

A ready-made workflow the MCP server offers for you to start, for example as a slash command:
`audit_site`, `check_citations`, `weekly_watch`, `compare_runs` and `explain_check`. A prompt is
offered only when the tools it calls are on.

**Where:** `prompts/list`; in Claude Code, `/mcp__geo-score__audit_site`. **More:** [MCP guide, Prompts](mcp.md#prompts)

### MCP resource

Data the MCP server lets a client read. With the `score_site` tool on, `geo-score://rubric/v1.1` holds
every check with its points and tiers, the bands and the caps, as the scorer applies them. With the
`report` tool on, the template `geo-score://runs/{run_id}` reads the summary of a saved run.

**Where:** `resources/list`; the prompt `explain_check` attaches the rubric resource.
**More:** [MCP guide](mcp.md)

### MCP server

`geo-score-mcp`, or `geo_score.py mcp` from a clone: a local server over stdio that gives an agent all
three levels through the Model Context Protocol. It is the same code as the CLI, and `--read-only`
makes a server that cannot spend.

**Where:** `geo-score-mcp` with `--toolsets`, `--tools`, `--exclude-tools`, `--read-only` and
`-c CONFIG`. **More:** [MCP guide](mcp.md)

### MCP tool

A function the MCP server lets an agent call: `score_site` (level 1, free), `ask` (level 2), `run`,
`list_runs`, `report` and `diff` (level 3), and `status`. Only `ask` and `run` can spend money, and
only with the provider keys you give the server.

**Where:** `tools/list`; the tool table in the README and the MCP guide. **More:** [MCP guide, Tools](mcp.md#tools)

### Mentioned

An answer mentions you when its text names your brand, one of its aliases or your domain, whether or
not it links to you. Chinese, Japanese and Korean names match anywhere; other names match whole words
only.

**Where:** the `mentioned` column of a watch report; `mentioned_count` in the JSON `citation` object.
**More:** [README, Levels 2 and 3](../README.md#levels-2-and-3--does-ai-actually-cite-you)

## N

### Normalised score

The 0–100 score itself: readiness (the points scored, bonus included) divided by the observable max,
times 100, rounded and never above 100. When a gate is at zero, it is also capped at 40.

**Where:** `N / 100` at the top of the report; the JSON fields `normalised`, `readiness` and
`observable_max`. Bands, `--fail-under` and the badge all read it.
**More:** [rubric v1.1, Scoring rules](../rubric/v1.1.md#scoring-rules), [schema/report.v2.json](../schema/report.v2.json)

### Not observed, unobservable

A check the run could not observe: it shows `—` (⊘), has the state `unobservable` with a `reason`, and
leaves the denominator instead of scoring 0. The CLI never observes `p3.listings`, `p3.mentions` and
`p4.question-coverage`, which need off-site search or judgement; other checks go unobserved in a given
run, for example when Wikidata does not answer, no sampled page is nested, or fewer than half of the
ten retrieval crawlers get any answer to their probes.

**Where:** the footer lines `Needs off-site search or judgement:` and `Not observable this run:`.
`--assert` skips such a check, JUnit marks it skipped, and `diff` shows `became unobservable`, never a
drop. The rubric's third state, `not_applicable`, leaves the denominator too; the CLI writes only
`scored` and `unobservable`. **More:** [troubleshooting, A check shows —](troubleshooting.md#a-check-shows--instead-of-a-score)

## O

### Observable max

The denominator as a report prints it: Y in `Scored X / Y observable`. It is 100 only when all 21
scored checks were observed, which never happens in a CLI run, since three of them need off-site
search or judgement.

**Where:** the report's footer; the JSON field `observable_max`. **More:** [rubric v1.1, Scoring rules](../rubric/v1.1.md#scoring-rules) (rule 3)

### Opt-out token

A name in robots.txt that looks like a user-agent but belongs to no crawler and sends no requests, such
as `Google-Extended` or `Applebot-Extended`: a signal about whether content may be used for AI training
or grounding. The rubric does not score opt-out tokens.

**Where:** the rubric's `g.robots` check, which reads only the retrieval crawlers; the AI crawler
reference. **More:** [AI crawler user-agents](../reference/ai-crawlers.md#the-distinction-that-matters-most)

## P

### Pillar

One of the five groups the rubric's checks fall into: Reachable (15 points, the three gates),
Understandable (22), Content Citability (35), Brand Credibility (18) and Answer Fit (10). The terminal
report lists the checks by pillar, each with its total.

**Where:** the terminal report and `--brief`; the `pillar` property of each SARIF rule.
**More:** [README, What it checks](../README.md#what-it-checks)

### Pinned sample

A sample you fix instead of letting the run draw one. `--urls FILE` scores exactly the pages listed (up
to 8, all on the site being scored), and `--urls-from REPORT` or `--baseline REPORT` scores the pages
an earlier JSON report sampled, so a comparison shows the site and not the sampling.

**Where:** `--urls`, `--urls-from` and `--baseline`; the `urls` argument of the MCP tool `score_site`;
the report then says `sample_source: pinned`.
**More:** [troubleshooting, The score moved a few points](troubleshooting.md#the-score-moved-a-few-points-between-two-runs)

### Points

A check's weight is its maximum points: the 21 scored checks' maxima add up to 100, and the four
bonus checks' to 6. A run gives a check the points of the tier it reached.

**Where:** `3/5` beside each check; the JSON fields `checks[].points` and `max`; the value in
`--assert`, a number or `max`. **More:** [rubric v1.1](../rubric/v1.1.md)

### Probe

A live request that `g.reachable` sends with a retrieval crawler's user-agent string: each of the ten,
on up to three sampled pages, and a timeout, a dropped connection, a 429 or a 5xx is tried once more. A
crawler refused with an HTTP error on any of those pages (a 403, or a 429 or 5xx that outlasts the
retry) counts as blocked; a crawler that gets no answer at all on any page is not counted, and when
fewer than half of the ten get any answer the check is not observed. Only refusals bring the gate to
zero: it reads 0 when more than half of the ten are refused. Probes are unverified: they come from the
auditor's own address (the machine running geo-score), not from the vendor's published IP ranges, so a
firewall that verifies crawlers by IP range or reverse DNS may refuse a probe and still serve the real
crawler.

**Where:** the `g.reachable` evidence, which names the crawlers refused (`Not reached — …`) and those
with no answer on any page (`No answer on any page, so not counted: …`), then adds
`(Unverified probes: vendor user-agent strings sent from this machine's address.)`; when too few
answered, its reason starts `Only N of 10 retrieval user-agents got an answer`.
**More:** [AI crawler user-agents](../reference/ai-crawlers.md), [rubric v1.1, `g.reachable`](../rubric/v1.1.md#reachable-to-retrieval-user-agents--5-pts--greachable)

## R

### Retrieval crawler

A crawler that fetches pages to answer people's questions, for an AI search index or live on a person's
behalf. `g.robots` and `g.reachable` score access for ten of them only: OAI-SearchBot, ChatGPT-User,
Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User, Googlebot, Bingbot, Applebot and
Amazonbot.

**Where:** the `g.robots` and `g.reachable` evidence. **More:** [AI crawler user-agents](../reference/ai-crawlers.md#the-distinction-that-matters-most)

### Rubric

The published specification behind every score: each check with its tiers and points, the bands, the
gate cap and the bonus cap. It says what is measured and why, never how to fix a site;
`rubric/v1.1.md` is written for people and `rubric/v1.1.json` for programs.

**Where:** the link at the foot of the terminal report; the links `--explain` prints under checks
below full marks; the MCP resource `geo-score://rubric/v1.1`. **More:** [rubric v1.1](../rubric/v1.1.md)

### Rubric version

The version of the rubric a score was measured against, currently v1.1; scores are comparable only
within one rubric version. It moves separately from the tool's version (1.5.0 here), which follows
Semantic Versioning.

**Where:** the JSON fields `rubric_version` and `tool` (`geo-score-cli/1.5.0`); `rubric v1.1` in the
footer; `--version`. `diff` and `--baseline` refuse a report scored against another rubric version
(exit 2). **More:** [STABILITY.md](../STABILITY.md)

## S

### Sample

The pages a run scores: 8 by default, the homepage and pages drawn from the sitemap and the site's
links, or fewer when the site has fewer. Content checks count out of the sampled pages, so a different
sample can move the score by a few points.

**Where:** `--sample N` (1 or more); the JSON field `sampled_urls`; the note
`Scored on N of M sampled pages` when pages answered with an error or a bot challenge.
**More:** [rubric v1.1, Scoring rules](../rubric/v1.1.md#scoring-rules) (rule 1),
[troubleshooting, The score moved a few points](troubleshooting.md#the-score-moved-a-few-points-between-two-runs)

### Sample source

Where a run's sample came from: `sitemap`, `homepage and section links (no sitemap reachable)`, or
`pinned` when the pages were given. It says how the pages were chosen, not which ones: two runs with the
same source can still sample different pages.

**Where:** the JSON field `sample_source`; the note
`Sampled N of the M pages asked for: no more were found (sample source: …)`. **More:** [schema/report.v2.json](../schema/report.v2.json)

### SARIF

A standard format for static-analysis results, read by code-scanning tools. `--sarif FILE` writes
SARIF 2.1.0 with one rule per check and one result per check below full marks: `error` for a gate at
zero, `warning` for another check at zero, `note` for partial credit.

**Where:** `--sarif FILE`; GitHub code scanning. **More:** [CLI reference, Options](../cli/README.md#options)

### Sector median and the n<10 rule

The median score of the scored sites in one leaderboard sector; the benchmark's README gives it with a
95% bootstrap interval. A sector with fewer than 10 scored sites gets no median and shows `—`, because
the median of a handful of sites would print like a real one and mean much less.

**Where:** the By sector table in `benchmark/README.md` and on the leaderboard page; `sectors` in
`benchmark/stats.json`. **More:** [benchmark/README.md, By sector](../benchmark/README.md#by-sector)

### Site text fence

Text quoted from the audited site appears inside `«site text: …»`, with control, zero-width and bidi
characters removed, and the site cannot close the fence early. What is inside is the site's words, to
be read as data and never followed as instructions, and the MCP tools tell the agent so.

**Where:** the evidence in every report and under `--explain`; the output of the MCP tools.
**More:** [SECURITY.md, Threat model](../SECURITY.md#threat-model)

## T

### Thin sample

A leaderboard row scored on fewer than 4 pages, because the site's sample could not be filled: no
sitemap was reachable and the homepage links to few pages, or sampled pages failed to load. Such rows
are marked *thin sample*, and the benchmark also gives the median without them.

**Where:** the Every site table in `benchmark/README.md`; the leaderboard page; `thin_sample` in
`benchmark/stats.json`. **More:** [benchmark/README.md](../benchmark/README.md)

### Tier

One of the two to four levels of a scored check, each with a condition and the points it earns; the
lowest is always 0. A check takes the highest tier the evidence actually satisfies, not the one it
nearly reaches.

**Where:** the tier tables in the rubric; the tier reason `--explain` prints (JSON `tier_reason`);
`+N next tier` in *Biggest gaps*. **More:** [rubric v1.1, Scoring rules](../rubric/v1.1.md#scoring-rules) (rule 2)

### Training crawler

A crawler that collects pages for model training corpora, such as GPTBot, ClaudeBot or CCBot. The
rubric does not score training crawlers: what robots.txt says to them moves no check.

**Where:** the rubric's `g.robots` check, which reads only the retrieval crawlers; the AI crawler
reference. **More:** [AI crawler user-agents](../reference/ai-crawlers.md#the-distinction-that-matters-most)

## W

### Watch run

One `watch run`: every question in `queries.csv` put to every engine that has a key, `runs` times
each, and saved as a run file under `.geo-score/watch/runs/` with a ledger of requests, tokens,
searches and cost. `watch run --dry-run` prints the plan and the caps without calling anything.

**Where:** `watch run`, `watch runs` and `watch report [RUN]`; the MCP tools `run`, `list_runs` and
`report`; `max_calls` and `budget_usd` in the config limit a run. Run files follow
`schema/watch.v1.json`. **More:** [README, Levels 2 and 3](../README.md#levels-2-and-3--does-ai-actually-cite-you),
[CLI reference, Watch](../cli/README.md#watch)
