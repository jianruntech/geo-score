# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/).
The **rubric** is versioned separately from the repository — see `rubric/`.

## [Unreleased]

## [1.0.0] — 2026-09-08

First tagged release. The repository was pushed a few hours earlier without a tag;
the rubric was corrected before this tag, so v1.0 as released here is the only v1.0.
Corrections made in that window are listed under *Fixed before first tag*.

### Added
- Rubric v1.0: **29 checks** across 5 pillars, 100 nominal points, with pass conditions,
  an explicit Credit type per check, three-state scoring, and score bands
- `SKILL.md` — Claude Code skill that runs the rubric
- `reference/ai-crawlers.md` — the AI user-agent list Pillar 1 checks against
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
