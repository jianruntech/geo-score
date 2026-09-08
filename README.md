<p align="right"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>

<p align="center"><img src="assets/cover.svg" alt="geo-score — an open rubric for AI answer-engine visibility" width="100%"></p>
# geo-score

**An open, versioned rubric for Generative Engine Optimization — score any site 0–100
on whether AI answer engines can find, parse, trust and cite it.**

The rubric it publishes is the **AIV score** (AI Visibility). 25 tiered checks,
100 points, one specification anyone can implement.

[![License: MIT](https://img.shields.io/badge/License-MIT-1E5C46.svg)](LICENSE)
[![Rubric v1.1](https://img.shields.io/badge/rubric-v1.1-A9854C.svg)](rubric/v1.1.md)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-skill-blue.svg)](SKILL.md)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **GEO here means Generative Engine Optimization** — getting cited by ChatGPT,
> Perplexity, Google AI Overviews, Gemini and Copilot. It has nothing to do with
> geography, maps or geolocation.

[Rubric](rubric/v1.1.md) · [Quickstart](#quickstart) · [What it checks](#what-it-checks) ·
[Sample output](#sample-output) · [Scope](#scope--what-this-does-not-do) · [Research](#research-behind-the-weights)

---

Classic SEO asks *where do I rank*. Answer engines don't rank — they retrieve passages,
decide whether a source is worth quoting, and cite it. That is a different question,
and it has different failure modes: a site can sit at position 3 on Google and never be
quoted, while a page nobody links to gets cited daily because its passages are clean.

**AIV Score is the measurement half of that problem.** It is a published, versioned
rubric — 25 tiered checks adding to 100 — plus a Claude Code skill that runs it.

It deliberately stops at measurement. See [Scope](#scope--what-this-does-not-do).

## Who this is for

- **Site owners** who want a number they can track month over month, and a list of what specifically is failing
- **Agencies and consultants** who need a defensible, auditable score to show a client instead of "trust me, it's better now"
- **Anyone building GEO tooling** who wants a shared rubric so scores mean the same thing across tools

## Why publish a rubric instead of just a tool

Most GEO tools give you a number and keep the method. That number is unfalsifiable —
you cannot check it, cannot reproduce it, and cannot compare it to anything.

A published rubric is checkable. You can disagree with a weight and say why. You can
implement it yourself and see whether your result matches ours. You can hand a client
a score and a spec, and they can audit both.

That is the whole bet here: **a measure that everyone can run is worth more than a
measure only we can run** — even though we sell the remediation on the other side of it.

## Quickstart

```bash
# Install as a Claude Code skill
git clone https://github.com/jianruntech/geo-score.git ~/.claude/skills/geo-score
```

Restart Claude Code, then:

```
/geo-score audit https://example.com
```

**Verify it installed:** type `/geo-score` with no arguments. You should see the
command list. If nothing appears, check that the clone landed in `~/.claude/skills/`
and that the folder contains `SKILL.md`.

You do not need Claude Code to use this. The [rubric](rubric/v1.1.md) is a plain
specification — score a site by hand, or implement it in your own tool.

## What it checks

Full specification with tier conditions: **[rubric/v1.1.md](rubric/v1.1.md)** ·
[简体中文](rubric/v1.1.zh-CN.md)

| Pillar | Pts | Checks | Examples |
|---|:-:|:-:|---|
| Reachable — *gates* | 15 | 3 | Retrieval crawlers allowed in `robots.txt`, all 10 actually served 200, content in server-rendered HTML |
| Understandable | 22 | 5 | `Organization` + `WebSite`, `llms.txt` with sectioned link groups, `BreadcrumbList`, page-type schema |
| **Content Citability** | **35** | 5 | Self-contained answer passages, headings that match how people ask, sourced statistics, real bylines, freshness |
| Brand Credibility | 18 | 5 | Knowledge-graph entity, third-party listings, `sameAs` that resolves, video presence |
| Answer Fit | 10 | 3 | Extractable content shape, coverage of the questions buyers actually ask |
| *Bonus* | *+6* | *4* | `ai.txt`, `speakable`, GEO `<link>` tags, `llms-full.txt` — outside the denominator |

Content Citability carries the most weight on purpose: answer engines retrieve
**passages**, not domains. Structure of the passage beats authority of the domain more
often than classic SEO intuition expects.

**Every check is tiered**, 2–4 tiers each — you take the highest tier the evidence
satisfies. Binary pass/fail is what made v1.0 unable to tell two sites apart.

**Three checks are gates.** Miss full marks on `g.robots`, `g.reachable` or `g.ssr` and
readiness caps at 40, because until a crawler can reach the content, nothing else you
change has any effect.

### Score bands

| 0–30 | 31–50 | 51–65 | 66–82 | 83–100 |
|:-:|:-:|:-:|:-:|:-:|
| Not started | Early | Growing | Solid | Leading |

Band names describe a **stage, not a verdict**. This is a diagnostic meant to decide what
to do next. External benchmarks put most business sites in the 30–55 range — a score in
the forties is ordinary, not alarming.

## Sample output

<details>
<summary><strong>AIV report for a small Shopify storefront (click to expand)</strong></summary>

```
AIV Readiness 45 / 98  (rubric v1.1)  ·  normalised 46%  ·  2026-09-08
Band: Early  —  5 points below Growing

Sampled (8 URLs)
  /  /products/kettle  /products/grinder  /products/scale
  /blog/pour-over-ratio  /blog/grind-size  /blog/water-temp  /blog/storage

  Reachable                    15 / 15   ← gate checks
    ✓  robots.txt names all 10 retrieval UAs under Allow        5/5
       full tier
    ✓  all 10 retrieval UAs return 200, byte-identical to a b…  5/5
       full tier
    ✓  primary content present without executing JS             5/5
       full tier

  Understandable               15 / 22
    ✓  sitemap.xml resolves, declared in robots.txt, lastmod …  4/4
    ✗  llms.txt not found                                       0/5
       tier 1 of 4
    ◐  Organization + WebSite sitewide, logo resolves — no sa…  5/6
       tier 3 of 4
    ◐  BreadcrumbList on 3 of 7 nested pages                    2/3
       tier 2 of 3
    ✓  Product + Offer on 3 of 3 product pages, price and ava…  4/4

  Content Citability            9 / 35
    ✗  0 of 8 pages open with a self-contained passage          0/9
       tier 1 of 4
    ◐  2 of 8 headings phrased as a task or question            3/7
       tier 2 of 4
    ◐  visible dates on 4 blog posts, none on 4 product pages   3/6
       tier 2 of 3
    ◐  11 numeric claims, 2 carry a source                      3/7
       tier 2 of 4
    ✗  author is the brand name on 4 of 4 articles              0/6
       tier 1 of 3

  Brand Credibility             2 / 18
    ◐  listed in 2 directories                                  2/4
       tier 2 of 4
    ✗  no independent coverage found                            0/4
       tier 1 of 4
    ✗  no Wikidata or Wikipedia entity                          0/4
    ✗  sameAs not declared                                      0/3
       tier 1 of 3 — absent scores 0, it is not excluded
    ✗  no official video channel                                0/3
       tier 1 of 3

  Answer Fit                    4 / 8
    ◐  headings present, paragraphs run long                    2/4
       tier 2 of 3
    ◐  3 of 10 common buyer questions answered on site          2/4
       tier 2 of 4

  ⊘ p4.cn-engines  not applicable — no Chinese-market presence  (−2 from the denominator)

  Bonus checks: none found (+0, outside the denominator; caps at +6)

Citation performance — not scored
  Whether engines actually cite this site is an outcome, not a property of the site.
  It is reported separately once query tests are run. A readiness score says engines
  *can* cite you; it does not say they *do*.
```

</details>

Full walkthrough of how to read it: [`examples/sample-report.md`](examples/sample-report.md).

## Five real audits, and what they changed

We ran v1.0 against five public sites. **None cleared 51%** — not Stripe, not Anthropic,
not the framework docs sites whose audience is developers.

Then we looked at *why*, and concluded the rubric was wrong before the sites were.
A site returning 200 to all ten retrieval crawlers, byte-identical to a browser, with
60 KB of server-rendered prose, was being labelled **Critical**. Three external
benchmarks agree the ceiling was set too low: GeoReady reports a mean of 54–56 across
282–750 domains; GW Content states most business sites land between 30 and 55.

[**v1.1**](rubric/v1.1.md) is the recalibration — tiered scoring instead of pass/fail,
readiness split from citation performance, unobservable checks out of the base, and band
names that describe a stage rather than a verdict.
[How it was calibrated](rubric/calibration-v1.1.md) ·
[the 8 ambiguities it settled](rubric/open-questions.md)

| Site | v1.0 | v1.1 (projected) | Band |
|---|:-:|:-:|---|
| [nextjs.org](examples/audits/nextjs.org.md) | 49% | **62%** | Growing |
| [stripe.com](examples/audits/stripe.com.md) | 51% | **61%** | Growing |
| [svelte.dev](examples/audits/svelte.dev.md) | 40% | **53%** | Growing |
| [mingdao.com](examples/audits/mingdao.com.md) | 34% | **50%** | Early |
| [anthropic.com](examples/audits/anthropic.com.md) | 36% | **48%** | Early |

The published audits are the original v1.0 runs, unaltered — every check carries evidence
(status codes, byte counts, MD5s across user-agents, the actual sentence that did or did
not qualify) and every audit ends with the auditor's own caveats. The v1.1 column is a
**projection** recomputed from that evidence, not a fresh audit. [Read them](examples/README.md).

## Scope — what this does *not* do

This is the part most tools leave out, so it's stated plainly.

**AIV Score measures. It does not fix.**

| Not included | Why |
|---|---|
| Fix templates — `robots.txt`, JSON-LD blocks, `llms.txt` boilerplate | Remediation is where the actual work and judgement live. It is a separate, non-open project |
| Content rewriting — how to shape a passage so it gets quoted | Same |
| Per-engine tactics — what to do differently for Perplexity vs Gemini | Same |
| A remediation roadmap | Same |

**Other honest limits:**

- **It measures input-side readiness, not outcomes.** A high AIV score means engines
  *can* cite you. Whether they *do* depends on competition, query intent and factors
  no external audit can observe. Pillar 5 partially covers this by requiring an actual
  query test, but that test is manual and small.
- **Pillar 4 and 5 need human judgement.** "Is this author a real identifiable person"
  and "did the engines surface you" are not fully automatable. Treat those 35 points
  as assisted, not automatic.
- **Heavily client-rendered sites score low, sometimes unfairly.** If your content only
  appears after hydration, most checks will read the pre-hydration HTML — which is also
  roughly what a crawler sees, so the low score is usually right, but verify by hand.
- **Engine behaviour moves.** The rubric is versioned for exactly this reason. A score
  from an older rubric version is not comparable to a current one.

## Research behind the weights

The weights are opinionated but not invented. The two findings that most shaped them:

- **[Aggarwal et al., *GEO: Generative Engine Optimization*, KDD 2024](https://arxiv.org/abs/2311.09735)** —
  citing sources, adding statistics and quoting experts raise visibility by
  **up to 40%** (measured as Position-Adjusted Word Count, not citation count).
  Notably, the paper found an *authoritative tone* produced **no significant improvement** —
  which is why this rubric scores structure and attribution, not voice.
- **[llms.txt proposal, Answer.AI](https://llmstxt.org/)** — the convention this rubric
  checks for in Pillar 1.

Where a check rests on our own field observation rather than published research, the
rubric says so. If you have evidence that a weight is wrong,
[open a rubric proposal](.github/ISSUE_TEMPLATE/rubric_proposal.yml) — that is the
main thing we want contributions on.

## Related tools

Deliberately naming what this is *not*, so you can pick correctly:

| Project | What it does | Relationship |
|---|---|---|
| [llms-txt](https://github.com/AnswerDotAI/llms-txt) | The `llms.txt` specification itself | AIV checks for compliance with it |
| [yao-geo-skills](https://github.com/yaojingang/yao-geo-skills) | 21 categorized GEO skills, execution-oriented | Complementary — they do production, this does measurement |
| [GEOFlow](https://github.com/yaojingang/GEOFlow) | Full GEO operations system for company sites | Much larger scope; AGPL |

If you need remediation and not just a score, those projects overlap with the part
this repo deliberately excludes.

## Who maintains this

Built and maintained by **[Jianrun Tech](https://www.jianruntech.com)** (见润科技), Shenzhen —
we run GEO and AI-adoption programs for cross-border commerce companies. The rubric came
out of client work and out of optimizing our own products; publishing it is how we'd like
AI visibility to be measured consistently, including by people who never become our clients.

Commercial use of this repository is unrestricted under MIT — including inside paid
consulting work. You do not need our permission, and there is no separate commercial licence.

## Contributing

The most valuable contribution is evidence about the weights.
See [CONTRIBUTING.md](CONTRIBUTING.md).

## Citation

If you reference the rubric in research or a report, see [CITATION.cff](CITATION.cff).

## License

[MIT](LICENSE)
