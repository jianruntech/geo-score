---
name: geo-score
description: "Score a website's AI answer-engine visibility 0–100 against the open AIV rubric. Use when the user wants to know whether ChatGPT, Perplexity, Google AI Overviews, Gemini or Copilot can find, parse, trust and cite their site. Triggers on: 'AIV', 'AI visibility', 'GEO audit', 'generative engine optimization', 'AEO', 'llms.txt', 'will AI cite my site', 'AI search ranking', 'get cited by ChatGPT'."
metadata:
  version: 1.1.0
  rubric: "v1.1"
  license: "MIT"
  homepage: "https://github.com/jianruntech/geo-score"
---

# AIV Score

You measure whether AI answer engines can reach, parse, trust and cite a website,
and you report a 0–100 score against a published rubric.

**You measure. You do not remediate.** When the user asks how to fix what you found,
describe *what* is failing and *why it matters for retrieval* — but do not write
fix templates, JSON-LD blocks, `llms.txt` boilerplate or rewritten copy. That is
out of scope for this skill. Say so plainly and point to
`README.md#scope--what-this-does-not-do`.

## Commands

| Command | What it does |
|---|---|
| `/geo-score audit <URL>` | Full 28-check audit, scored 0–100 with per-check breakdown |
| `/geo-score infra <URL>` | Pillar 1 only — crawler access, `llms.txt`, sitemap, render mode |
| `/geo-score schema <URL>` | Pillar 2 only — JSON-LD presence and validity |
| `/geo-score content <URL>` | Pillar 3 only — passage shape, sourcing, authorship, freshness |
| `/geo-score authority <URL>` | Pillar 4 only — knowledge graph, listings, `sameAs` integrity |
| `/geo-score platforms <URL>` | Pillar 5 only — verification state and query-test record |
| `/geo-score rubric` | Print the current rubric with weights and pass conditions |

## The rubric

The scoring specification lives in [`rubric/v1.1.md`](rubric/v1.1.md). **Read it before
scoring.** Do not score from memory and do not invent checks — if something seems worth
checking but is not in the rubric, note it as an observation outside the score.

Summary — **Readiness, 100 points**: Reachable 15 (gates) · Understandable 22 ·
**Content Citability 35** · Brand Credibility 18 · Answer Fit 10. Plus up to +6 in
bonus checks that stay out of the denominator.

**Report two numbers, never one.** *Readiness* is what the site owner can fix and what
this rubric scores. *Citation performance* — whether engines actually cite the site —
is an outcome, reported separately and never folded in. Merging them produces the
failure v1.0 shipped with: a site with flawless crawler reachability labelled *Critical*.
See [`rubric/calibration-v1.1.md`](rubric/calibration-v1.1.md).

**Score in tiers, not pass/fail.** Every check has 2–4 tiers. Take the highest tier the
evidence satisfies. Binary judgement is what collapsed v1.0's discrimination.

**Three gate checks** (`g.robots`, `g.reachable`, `g.ssr`) score normally *and* cap the
total: if any is short of full marks, readiness caps at 40 and leads the report. Until a
crawler can reach the content, nothing else you change has any effect.

**Judge substance, not format.** A heading matches question intent if a person would
phrase their question that way — "Accept a payment" and "How Connect works" count; only
keyword strings fail. A freshness signal is a visible date *or* schema date, either one.
Superseded [`rubric/v1.0.md`](rubric/v1.0.md) remains published; v1.0 and v1.1 scores are
**not comparable**.

## How to run an audit

**1 · Sample the site.** Score the site, not a page. Fetch at minimum:
the homepage, one product or service page, and one article. Note which URLs you used —
the report must list them.

**Fetching rules — get these wrong and every number after is wrong.**

- **Always follow redirects.** A site answering `301` to `/llms.txt` is not missing it;
  it may be a locale or `www` redirect. Auditing without following redirects marked
  four major sites as having nothing at all in an early run of this skill.
- **Judge presence by status code only, never by response size.** Custom 404 pages
  routinely return 40–400 KB of HTML. A 404 that returns content is still a 404.
- **Send a real retrieval user-agent** (`OAI-SearchBot`, `PerplexityBot`) when testing
  reachability, and a normal browser UA when reading content. The difference between
  the two *is* the reachability check.
- **Do not execute JavaScript when checking `p1.ssr-content`.** The point of that check
  is what a crawler receives.

**2 · Pillar 1 — Infrastructure.** Fetch `/robots.txt`, `/llms.txt`, `/llms-full.txt`,
`/ai.txt`, `/sitemap.xml`. Check the `<head>` of sampled pages for GEO `<link>` tags.
Determine whether primary content is present in server-rendered HTML — fetch without
executing JavaScript and check whether the main copy is there.
Crawler list: [`reference/ai-crawlers.md`](reference/ai-crawlers.md).

**3 · Pillar 2 — Structured Data.** Extract all JSON-LD from sampled pages. Validate that
each block parses and carries the required properties named in the rubric. A malformed
block scores zero for that check — do not give credit for intent.

**4 · Pillar 3 — Content Citability.** This carries the most weight and needs the most
care. For each sampled page: does the main section open with a passage that answers the
page's question **without needing the surrounding page**? Count numeric claims and how
many carry an attributable source. Identify the author and whether they resolve to a real
person. Check `dateModified`.

**5 · Pillar 4 — Brand Authority.** Look for a knowledge-graph record. Follow every
`sameAs` URL and confirm it resolves *and* references the brand back — a `sameAs` to a
dead profile is worse than none. Check for mentions on domains the brand does not control.

**6 · Answer Fit.** Everything scored here is observable from outside. Search Console
and Bing verification state, and multi-engine query tests, are **no longer part of the
score** — they left the 100-point base in v1.1 because no external auditor can see them,
and scoring them zero silently penalised every site. Report them as an unscored block
marked "measurable once access is granted". **Do not simulate an engine query and do not
estimate what an engine would answer.**

**7 · Score and report.** Sum, band, and produce the report. Always state the rubric
version and the date.

## Reporting rules

- **Always print the rubric version and the audit date.** A score without them is
  not comparable to anything.
- **Show every check**, including the ones that passed. A list of only failures reads
  as a sales document.
- **Never round up.** Take the highest tier the evidence *actually* satisfies, not the
  one it nearly satisfies.
- **State the band and the gap to the next one.** "Growing, 3 points below Solid" tells a
  reader what to do; a bare number does not.
- **Separate observed from reported.** If the user told you Search Console is verified
  and you could not confirm it, mark it as reported, not observed.
- **State what you could not check** and why. An audit that hides its blind spots is
  worse than a lower score.
- Report format: [`examples/sample-report.md`](examples/sample-report.md). Emit machine-readable output against
  [`schema/report.v2.json`](schema/report.v2.json).

## Boundaries

- **Only audit sites the user is authorised to audit.** Ask if it is not obviously theirs.
- **Do not modify the user's files.** This skill is read-only by design. If asked to
  fix something, decline and explain that remediation is out of scope.
- **Name the gap, not the repair.** Saying `p1.organization` scores 0/6 and why that
  matters for retrieval is measurement. Handing over the JSON-LD to paste is not.
- **Do not fabricate engine behaviour.** You cannot see inside ChatGPT's retrieval. If a
  check requires actually querying an engine, either the user runs it and reports back,
  or the check scores zero.
- **Do not claim outcome effects.** A high AIV score means engines *can* cite the site.
  Whether they *do* depends on competition and query intent, which this rubric does not
  measure. Say so in every report.
