# The AIV rubric

This folder holds the versioned scoring specification. **The rubric is the product** —
the Claude Code skill is one implementation of it, not the definition.

| Version | Status | Checks | Released |
|---|---|:-:|---|
| [v1.1](v1.1.md) · [简体中文](v1.1.zh-CN.md) | **current** | 25 tiered | 2026-09-08 |
| [v1.0](v1.0.md) | superseded | 29 binary | 2026-09-08 |

**v1.0 was never released to users.** It was written, then run against five real public
sites before announcing it — and it labelled a site returning 200 to all ten retrieval
crawlers, byte-identical to a browser, with 60 KB of server-rendered prose, as *Critical*.
That is a failed calibration check, so v1.1 shipped instead.

Both stay published. The [five v1.0 audits](../examples/audits/) are the evidence that
found the problem, [eight ambiguities](open-questions.md) were settled by the correction,
and [the calibration record](calibration-v1.1.md) shows the reasoning against three
external benchmarks. A rubric that quietly rewrites its own history is not one you can
compare against.

## Why version a rubric

A visibility score is only useful if you can compare it — to last month, to a competitor,
to what a different tool measured. That requires everyone to agree on what was measured.

So two rules, and they are not negotiable:

1. **Every score reports its rubric version.** `AIV 62 (v1.1)` is a claim. `AIV 62` is not.
2. **Scores from different rubric versions are not comparable.** Don't average them,
   don't chart them on the same axis. Re-score with the current version instead.

## What bumps the version

| Change | Version |
|---|---|
| Typo, clearer wording, better example | none — normal PR |
| Reordering checks without changing weights | none |
| Adding or removing a check | **minor** (v1.0 → v1.1) |
| Changing a weight | **minor** |
| Changing whether a check passes | **minor** |
| Restructuring the pillars | **major** (v1.x → v2.0) |

A released rubric file is **never edited in place**. New version, new file, and the old
one is marked superseded so anyone holding an old score can still see what it meant.

## How to score without the skill

The rubric is a plain specification. To score a site by hand:

1. Pick your sample — at minimum the homepage, one product/service page, one article.
   Write the URLs down; the score is only meaningful with them.
2. Walk each pillar in [v1.1.md](v1.1.md) and give each check the **highest tier its
   evidence actually satisfies** — not the one it nearly reaches.
3. Sum, find the band, and record **the rubric version and the date**.
4. Note what you could not verify. An audit that hides its blind spots is worth less
   than a lower score that states them.

Implementing it in your own tool is explicitly welcome — that is the point of publishing it.
If your implementation disagrees with ours on a real site, that's a
[bug report](../.github/ISSUE_TEMPLATE/bug_report.yml) we want.

## Design decisions, and the arguments against them

Stated openly, because these are the things a careful reader will push back on.

**Content Citability is 25 points, the most of any pillar.**
Answer engines retrieve passages, so passage shape has more leverage than domain
authority — which inverts classic SEO intuition.
*Argument against:* it is also the most subjective pillar to score, so it adds the most
variance between two people scoring the same site. We accepted the variance because
under-weighting it produced scores that didn't match observed citation behaviour.

**Brand Authority is 20 points even though it is slow to move.**
An engine deciding whether to quote you leans on corroboration it did not get from you.
*Argument against:* it punishes new sites for being new, and the work here has the
longest lag. True — a new site should expect to lose most of these 20 points for months.
That is information, not a defect.

**Platform Visibility requires a manual query test.**
Everything else can be checked from outside; this one cannot be faked by inspecting HTML.
*Argument against:* it makes the score partly non-reproducible. Accepted, and flagged in
[Scope](../README.md#scope--what-this-does-not-do) — these 15 points are assisted, not automatic.

**Nothing here scores writing quality or tone.**
The Princeton GEO study found an authoritative tone produced *no significant improvement*.
So the rubric scores structure, sourcing and attribution, and stays out of style.

## Machine-readable

| File | What it is |
|---|---|
| [`v1.1.json`](v1.1.json) | The 25 checks with **stable ids** (`p2.answer-passages`), tier conditions, points, bands and gate rules |
| [`v1.0.json`](v1.0.json) | Superseded — the 29 binary checks, kept so old audits stay resolvable |
| [`../schema/report.v2.json`](../schema/report.v2.json) | JSON Schema for audit output under v1.1 — emit this and your results are comparable with anyone else's |
| [`../schema/report.v1.json`](../schema/report.v1.json) | Superseded — the v1.0 output shape, kept so v1.0 reports still validate |

Check ids are **permanent**. A future rubric version may retire an id, but never reuses
one for a different check — that is what makes it possible to diff v1.0 against v1.1 and
map an old score onto a new one.

CI enforces that the `.json` and the `.md` agree: same number of checks, same point
values, unique well-formed ids, valid credit types.
