# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/). 中文版：[CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md)。
The **rubric** is versioned separately from the repository — see `rubric/`.

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
