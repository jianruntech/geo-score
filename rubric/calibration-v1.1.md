# How v1.1 was calibrated

*简体中文：[calibration-v1.1.zh-CN.md](calibration-v1.1.zh-CN.md)*

Running v1.0 against five real public sites produced this:

| Site | AIV | Normalised | v1.0 band |
|---|:-:|:-:|---|
| stripe.com | 45/88 | 51% | Below average |
| nextjs.org | 40/82 | 49% | Below average |
| svelte.dev | 34/85 | 40% | **Critical** |
| anthropic.com | 32/88 | 36% | **Critical** |
| mingdao.com | 29/85 | 34% | **Critical** |

A site returning 200 to all ten retrieval crawlers, byte-identical to a browser, with
60 KB of server-rendered prose, was labelled *Critical*. That is not a fact about the
site. It is a fact about the rubric. v1.1 is the correction.

## Four structural problems the audits exposed

Laying out all 29 checks across all five sites:

**13 points sat in no-man's-land.** `ai.txt`, GEO `<link>` tags, `speakable`,
`HowTo`/`BreadcrumbList` and `Product`/`Offer` scored **zero on all five sites**. Web
Almanac 2025 explains why: `llms.txt` appears on 2.13% of desktop sites, and among
JSON-LD types `BreadcrumbList` is 5.66%, `Product` 0.77%, `FAQPage` about 0.34%. Those
points were not measuring a difference. They were penalising everyone equally.

**16 points had no discrimination.** Crawler access, live reachability, server-rendered
content, third-party listings and independent mentions were **full marks on all five**.
They matter, but as binary checks they carried no information.

**12 points were invisible from outside.** Of Platform Visibility's 15, the Search
Console check, the Bing check, the multi-engine test and the non-English-engine check
came back `unobservable` on every site. For diagnosing a site you do not own — the entire
use case — that pillar did nothing. Worse, different checks dropped out on different
sites, producing three different maximums (82, 85, 88), so the scores were not comparable
to each other.

**Binary judgement collapsed the range.** With 29 near-equal checks (mean 3.4 points) and
no partial credit, five sites landed inside a 17-point band, 34–51.

## Is that range actually abnormal?

| Source | Figure |
|---|---|
| [GeoReady](https://geoready.dev/state-of-geo/) (Auriti's hosted build) | Mean **56.4** across 282 domains; **54.3** mean, median 56 across an earlier 750+ sample |
| [GW Content](https://www.gwcontent.com/pages/aeo-readiness-score) | States plainly that most business websites score **30–55** |
| [Foglift](https://foglift.io/blog/ai-visibility-benchmarks-2026) Q1 2026 | Sector medians: SaaS/B2B **62**, education 58, healthcare 55, agencies 51, ecommerce 48; upper quartile 73–84 |
| [Seomator](https://seomator.com/geo-audit-tool) | **54.6%** of sites it scored between Jan and Jul 2026 fell below its 56-point readiness line |

Two conclusions hold at once, and both have to be accepted.

First, **34–51 is roughly where the market is.** GW Content's "30–55" overlaps almost
exactly. Low scores are not, in themselves, an error.

Second, **our ceiling was set too low.** The web-wide mean is 54–56 and our best site was
51. But the thing that was most wrong was not the numbers — it was calling the market
norm *Critical*.

## What v1.1 changed

**1 · Judge substance, not format.** Three re-readings, all of them format worship:

- *Headings match question intent.* v1.0 required a question mark, which gave stripe.com
  0 of 5. But "Accept a payment" and "How Connect works" are exactly how someone phrases
  a question to an assistant. v1.1 counts questions, tasks and explanations, and excludes
  only keyword strings. mingdao.com's auditor had written into the evidence that its
  headings "are clean Chinese section names, not keyword strings" — and scored it 0
  anyway. That is the gap that needed closing.
- *Answer passages.* v1.0 required the **first** paragraph at **40–90 words**. svelte.dev's
  core sentence is 39 words. One word. v1.1 widened to 25–120 words (50–200 characters for
  Chinese) and dropped the first-paragraph requirement.
- *Freshness.* v1.0 accepted only `dateModified`. stripe.com's four sampled articles carry
  `datePublished` dates within 20 days and scored 0. v1.1 accepts a schema date or a date a
  reader can see — either one.

**2 · Tiers replace pass/fail.** All 21 scored checks now have 2–4 tiers, and each tier
names a count out of the 8 sampled pages.

**3 · Unobservable checks left the base.** The four Platform Visibility checks are out of
the 100. They are reported as an unscored block, marked measurable once access is granted,
rather than silently scored zero.

**4 · Two scores, not one.** *Readiness* is what the owner can change and what a service
can commit to. *Citation performance* is an outcome — LumenGEO's data has SaaS brands
averaging 15–30 and local businesses 0–10 — and is reported separately. Anthropic's 36
was jarring precisely because a fixable score and a naturally low one were being averaged
into a single number.

**5 · Emerging conventions moved to bonus.** Those four checks were 9 points inside the
denominator in v1.0 (`ai.txt` 2 + GEO link tags 2 + `speakable` 3 + `llms-full.txt` 2).
They are now bonus, capped at +6, outside the denominator. Auriti gives its whole
emerging-conventions family 6 of 100 and keeps WebMCP readiness out of the score entirely.

**6 · Gates score and cap.** `g.robots`, `g.reachable` and `g.ssr` are scored normally,
and a **zero** on any of them caps the normalised percentage at 40.

> We diverged from comparable tools here, and it cost us a bug — see below. aeo-lite's
> hard-fail design removes table-stakes checks from scoring entirely, which is right for
> a CI, fail-the-build context. For a diagnostic a non-technical reader will act on, we
> kept them scored: removing a check everyone passes lowers everyone's percentage
> arithmetically (numerator and denominator both drop by a full-marks item), and in
> testing it compressed the range from 17 points to 12.

**7 · Five bands, stage names.** Thresholds come from GW Content's published AEO ladder,
which its own stated distribution backs. "Critical" is deleted. The pattern across the
category is consistent: tools built for CI use *Critical*, because their reader wants a
red light. Diagnostics written for people use stage language, because their reader wants
to know what to do next. This is the latter.

## Backtest

We projected first — recomputing the five sites' v1.0 evidence under v1.1's weights — and
then re-audited them properly. **The projection was wrong.**

| Site | v1.0 | Projected | **v1.1, measured** | Band |
|---|:-:|:-:|:-:|---|
| nextjs.org | 49% | 62% | **85 / 98 = 87%** | Leading |
| svelte.dev | 40% | 53% | **76 / 98 = 78%** | Solid |
| stripe.com | 51% | 61% | **77 / 100 = 77%** | Solid |
| anthropic.com | 36% | 48% | **69 / 98 = 70%** | Solid |
| mingdao.com | 34% | 50% | **69 / 100 = 69%** | Solid |

The projection predicted 48–62%; measurement gave 69–87%. The gap is in the projection's
method: it scaled v1.0's fractional scores onto the new point values, which assumes a site
keeps the same *proportion* of credit. The tier conditions grant far more than that scaling
implied. The starkest case is stripe.com's `p2.question-intent`: 0 of 5 under v1.0 because
its headings are not questions, 7 of 7 under v1.1 with 6 of 8 pages qualifying. Changing a
criterion from form to substance is not a discount you can apply.

**The spread is 18 points against v1.0's 17.** The projection had shown it narrowing to 14,
and on that basis we were prepared to state that tiers had not improved discrimination.
Measurement overturned that — but the way it overturned it also shows that five sites in
the same tier cannot test discrimination at all. 18 versus 17 means nothing.

**The mean is 76%, far above GeoReady's web-wide 54–56.** This one is not a calibration
problem, it is the wrong comparison. GeoReady's figure comes from 282–750 random domains;
these five are among the best-built sites in their categories. The right reference is
Foglift's SaaS/B2B **upper quartile, 73–84** — and 69–87 sits on it. A typical business
site still scores 30–55 under this rubric, which is what GW Content reports.

### A design error the re-audit caught

In the first draft of v1.1, stripe.com scored 77/100 and nextjs.org 85/98 — and both
displayed as **40%, Early**, because the gate rule capped any site whose gate checks fell
short of full marks. stripe.com's `g.robots` scored 3 of 5 only because its `robots.txt`
names no AI retrieval user-agent — while blocking none of them, and serving all ten a 200.
nextjs.org's `robots.txt` is 40 bytes with no user-agent groups at all, which permits
everything, and it scored 3 of 5 too.

**That is v1.0's mistake relocated**: treating *not ideal* as *not working*.

The rule now caps only when a gate scores **zero**, which is the only state that means a
crawler genuinely cannot reach the content. A middle tier means reachable but not ideal —
a deduction, not a cap.

This was found by auditing real sites, not by reasoning about the rubric. That is the
argument for publishing the audits: a rubric that finds no problems in itself has usually
not been pointed at anything real.

## Still unresolved

**The sample cannot test discrimination.** These five are the best-built English technical
sites in their categories, and an 18-point spread against v1.0's 17 is not a meaningful
difference. Testing whether tiers help needs visibly weak sites, and the same site audited
before and after remediation.

**Band thresholds are borrowed, not derived.** Google's meta-rule for Core Web Vitals
thresholds is that any threshold must be one at least 10% of real sites already meet. We
use GW Content's ladder and have five sites of our own. Widening the reference pool to
30–50 sites, filed by sector, would both calibrate the thresholds and let a report say
"you are here relative to your sector" instead of quoting a bare number. That is the main
v1.2 task.

**`p4.question-coverage` still depends on which ten questions the auditor picks.** Pick
different questions, get a different score, and the rubric does not say how to pick them.
It is the largest remaining source of irreproducibility.
