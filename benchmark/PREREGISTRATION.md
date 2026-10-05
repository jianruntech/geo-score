# A preregistered validation plan: readiness and being cited

中文版：[PREREGISTRATION.zh-CN.md](PREREGISTRATION.zh-CN.md)

> Written down before any data for it are collected. It tests the instrument: whether the AIV
> readiness score goes with being cited. It does not test whether GEO works, and it changes no
> weight, tier or score in [rubric v1.1](../rubric/v1.1.md).

| | |
|---|---|
| Registered | by the first tagged release of geo-score on GitHub that contains this file; that release's publication date is the registration date. A git commit's date is written by its author and is not evidence of when it was written |
| Status | drafted 2026-10-05; no category, question, site or answer has been collected for it |
| Changes | only as dated amendments at the end of this file, each registered the same way, by the first tagged release that contains it; an amendment this plan requires before wave 0 is released before wave 0 starts |
| Rubric | v1.1, as the geo-score CLI version frozen with the sample reads it |

[VALIDITY.md](VALIDITY.md) compares the CLI with a hand audit of the same rubric, and
[REPRODUCIBILITY.md](REPRODUCIBILITY.md) measures how far one site's score moves between runs. Neither
says whether a higher score goes with being cited. This plan asks that, and fixes how before looking.

## 1. The question

**Primary.** Among sites that compete for the same buyer questions, are the sites with higher readiness
cited in a larger share of AI answers to those questions?

**Secondary.** Does the association hold without the sites a gate caps, and after allowing for how well
known a site is? Where a site is cited, does higher readiness go with a larger share of the answer resting
on its pages (absorption)? Does it hold for being named in the answer text?

Being selected as a source and being absorbed into the answer are kept apart throughout, as the
measurement literature separates them (Zhang et al. 2026, [arXiv 2604.25707](https://arxiv.org/abs/2604.25707),
§5 and §9.2).

## 2. What this plan does not claim

- **It tests the instrument, not GEO.** An association, whatever its sign, says how the readiness score
  relates to citation in this sample. It does not show that raising a site's score raises its citations,
  and nothing in this plan changes a page. A causal test would randomise page changes, for instance the
  five-arm design (original page, headings only, evidence blocks only, intent alignment only, full rewrite)
  proposed in arXiv 2604.25707 appendix B. That is a different study.
- **A positive result can have other causes.** Large, well-known brands tend to have both better-built
  sites and more coverage elsewhere. The popularity-adjusted analysis (S2) narrows this; it does not
  remove it.
- **A null result does not show that readiness is irrelevant.** The sample may be too small or too narrow
  in readiness, and engines may answer from what they already hold.
- **API answers are not the apps.** `watch` measures the providers' search-enabled APIs
  ([watch methodology §7](../guide/watch-methodology.md#7-what-a-run-cannot-see)). The results say nothing
  about consumer apps, Google AI Overviews or Chinese engines.
- **It does not validate single checks or weights.** Per-pillar results are described, not tested.
  Whatever the result, v1.1 does not change; any change ships as a new version under
  [the rubric's rules](../rubric/README.md#what-bumps-the-version).
- **Traffic is not measured.** On the one site where it was measured, most of the raw growth in ChatGPT
  referrals was the platform's own (Watanabe and Nakayashiki 2026,
  [arXiv 2606.04362](https://arxiv.org/abs/2606.04362), §6.1 and §6.2). This plan counts citations in answers,
  never visits.

## 3. Design at a glance

| | Planned | Minimum for the primary test |
|---|---|---|
| Categories | 20 | 12 |
| Sites per category | 4 to 6, from at least two readiness strata | 4, from at least two strata |
| Questions per category | 10, naming no product, vendor or site | 10 |
| Engines | OpenAI, Perplexity, Gemini and Anthropic, each with web search | 2 |
| Asks per question, per engine, per wave | 8 | 8 |
| Waves | wave 0, and wave 1 twelve weeks later | wave 0 |
| Readiness | geo-score CLI, rubric v1.1, two runs per site per wave | the same |

At the planned size a wave is 20 × 10 × 4 × 8 = 6,400 answers.

## 4. Categories and questions

A category is a kind of product or service a buyer would ask an assistant to recommend or explain, with at
least six candidate sites selling it (section 5). Categories are written down with a one-sentence definition,
spread across the benchmark's sectors, and committed before any candidate is scored. Round one asks
English-language questions for a buyer in the US; a Chinese round needs its own categories, engines and
registration.

The order is fixed: first the categories, each with its public list at a recorded revision and the
`benchmark/sites.json` sites that sell in it (section 5), so every candidate is known; then the questions;
then the sampling run. Each category gets 10 questions, written and committed before any candidate site is
scored, so they cannot be tuned to sites whose scores are known. They are written without consulting
`benchmark/results.json`. That cannot be checked from outside, since some candidates' v1.1 scores were
already public there, and the results say so. No question names a product, vendor or site: in the run file
every question must carry `brand_in_query` and `competitor_in_query` false, which the sampling rules of
section 5 guarantee. The questions use the unbranded `intent_tier` labels of the
[watch methodology](../guide/watch-methodology.md) (`list`, `problem`, `persona`, `pricing`), at least three
of the four in each category. No question is added, dropped or reworded after the freeze.

## 5. Sites: how they are chosen and banded

1. **Frame.** A category's candidates are the vendors with their own website listed in a public list or
   comparison article for the category (English Wikipedia, at a recorded revision id), together with the
   sites in `benchmark/sites.json` that sell in it, which are listed with the category before any question is
   written. No candidate is added because an AI answer cited it:
   choosing sites by the outcome would decide the result. A category with fewer than 6 candidates is dropped
   before sampling, and the drop is recorded. Above 15 candidates, 15 are drawn at random with a recorded seed.
2. **Names, then the sampling run.** Every candidate's `watch` config entry (name, aliases, domains, URL
   prefixes) is written first, with aliases only where they are not ordinary English words. A candidate that any
   frozen question of its category names, by the matcher `watch` uses for `brand_in_query` (name, aliases and
   domains as whole words), is out, so no drawn site can flag a question and no question has to change. Then
   every remaining candidate is scored once with the frozen CLI version. A candidate the CLI cannot score, or
   scores on fewer than 4 sampled pages (a thin sample, as the [benchmark](README.md) marks it), is out. Every
   exclusion is recorded with its reason.
3. **Strata, from the rubric's own band cuts.** Low: below 51 (Not started and Early). Mid: 51 to 65
   (Growing). High: 66 and above (Solid and Leading). No new cut is introduced.
4. **Draw.** In each category up to 2 sites per stratum are drawn at random with a recorded seed, 4 to 6 sites
   in all. A category left with fewer than 4 sites, or with sites in only one stratum, is dropped and recorded.
   Selecting on the predictor keeps the test valid, since no site is chosen by its outcome; it does mean that
   the size of the association describes a sample spread across the bands on purpose, not the field as it is.
   If fewer than 12 categories survive the drops, the study stops before any answer is collected, and the
   shortfall is published as an amendment.
5. **Gate-capped sites stay in.** A site with a gate at zero is eligible like any other; analysis S1 leaves
   them out.
6. **Identity.** Each site's domains and URL prefixes go into its category's `watch` config, one site as
   `brand` and the others as `competitors`. `watch` decides `cited` for the brand and for each tracked
   competitor with the same domain and URL-prefix matcher, so the roles do not change the counts. A site whose
   name is also an ordinary English word (Notion or Monday, for example) is marked in the frozen sample: the
   text matcher cannot tell the brand from the word, so its N is not measured and S4 runs without it. Its R
   and A, read from the URLs an answer cites, are unaffected.

The frozen sample (categories, frames with their revision ids, questions, candidates with their sampling-run
scores, seeds, draws, configs and exclusions) is committed under `benchmark/prereg/` before the first answer is
collected, and is registered as this plan is, by the first tagged release that contains it. After it, no site,
question or category is replaced or dropped.

## 6. Measures

**Readiness (X).** The CLI's normalised score, 0 to 100, under rubric v1.1, with the gate cap as the rubric
applies it. Every sampled site is scored twice in each wave, on different days, and X is the mean of the two.
The CLI leaves the three judgement checks (`p3.listings`, `p3.mentions`, `p4.question-coverage`) out of its
denominator ([VALIDITY.md](VALIDITY.md)), so this tests the CLI's reading of the rubric, not a hand audit. The
difference between the two runs is recorded; a single run moves by about ±5 ([REPRODUCIBILITY.md](REPRODUCIBILITY.md)).

**Selection: citation rate (R).** Whether an answer cites a URL the site owns: `cited` on the answer for the
brand and `competitors.<name>.cited` for each tracked competitor, in run files of the format
[schema/watch.v1.json](../schema/watch.v1.json) describes; per question these are the `you` and `competitors`
counts of `summary.by_question`. A site's R is its cited answers over the answered answers to its category's
questions, every engine and ask pooled. All sites of a category are counted on the same answers.

**Absorption: answer share (A).** How much of an answer rests on the site's own pages, read from where the
provider places each citation in the answer. `watch` saves those places on each answer as `spans`, and for the
configured brand the share as `supported_share` ([schema/watch.v1.json](../schema/watch.v1.json); definition
in the [watch methodology](../guide/watch-methodology.md)). A is the share by characters,
`supported_share.chars`: the characters a span with a URL the site owns supports, over all characters, counting
the non-whitespace characters of the answer's sentences and leaving citation markers out (a marker supports the
sentence it closes). For the brand A is read from the run file. For every other site the analysis script
computes it from the same saved answer, `spans`, `citations` and `sources_listed` by the same rule, with the
site's own config entry deciding which URLs it owns, as `watch` decides `cited`; so every site of a category is
measured on the same answers. The by-sentence and position-weighted variants (`supported_share.sentences` and
`supported_share.weighted`) are described, not tested.

An answer has an A only when it carries `spans`, which `watch` saves only when every citation came with a
position the provider documents. On any other answer, and on every answer from an engine whose provider does
not document positions, A is not measured, never zero. A site's A in a wave is the mean of A over the answers
that cite it and have an A, every engine pooled. If no released `watch` version saves `spans` when a wave runs,
that wave's absorption is not measured, and the results say so. If the released definition differs from the
one written here, the analysis script applies the one written here to the saved spans, and the difference is
reported as a deviation.

**Named in the answer (N).** The share of answered answers whose text names the site: `mentioned` for the
brand and `competitors.<name>.mentioned` for the others. Not measured for a site whose name is also an ordinary
word (section 5).

**Recorded alongside, not tested.** Per engine, how many answers searched; the counts of sources listed and
sources used in the answer text, where `watch` reports them; repeat consistency, the pairwise overlap of cited
domains across the 8 asks of a question; and the popularity covariate, each site's rank in a
[Tranco](https://tranco-list.eu/) list whose id is fixed in the frozen sample (a site outside the list gets
rank 1,000,001 and a flag).

## 7. Collection

- **Repeats.** Each question is asked 8 times per engine in every wave (`runs: 8`), in one run on one day. One
  ask is an anecdote ([watch methodology §8](../guide/watch-methodology.md#8-one-ask-one-day-one-month)):
  repeated runs of a prompt within 24 hours, counting runs that cited something, had a mean source overlap
  (Jaccard) of only 0.32 to 0.43 in each of four industries with four engines pooled, and 0.23 to 0.51 engine
  by engine (Schulte et al. 2026, [arXiv 2604.07585](https://arxiv.org/abs/2604.07585), §5, Tables 4 and 6),
  and the same study recommends at least 7 runs per prompt per day to track a brand and at least 8 to track
  sources (§7).
- **Waves.** Wave 0 starts after the frozen sample and the analysis script are committed and registered (see
  the header). Within it, every category's run is made within 3 days and every site's two readiness runs
  within 7. Wave 1 repeats the same runs, questions and configs 12 weeks after wave 0 began.
- **Engines.** OpenAI, Perplexity, Gemini and Anthropic with web search, at the models fixed in the frozen
  configs, with `country` set to `US`. An engine that fails for a whole wave is reported, and that wave's
  analyses use the engines that ran.

## 8. Concurrent controls

- **Same answers.** Every site of a category is checked against the same answers to the same questions,
  collected at the same time. Engine updates, index changes and platform growth reach all of them at once.
  This is the logic of a same-period control on the same domain, applied across sites: what moves every site
  together cannot be read as one site's effect (arXiv 2606.04362 §5).
- **Same window.** Readiness is scored in the same wave window as the answers are collected, so neither is
  compared with a stale reading of the other.
- **Change is read against the category.** In the longitudinal analysis a site's change is set against the
  other sites of its category over the same two waves, never read as a raw before-and-after.

## 9. Competitor and engine change log

Every site in a category is every other site's competitor, and in a simulated study the gain from a rewriting
method shrank as more of the competing documents used it (Puerto et al. 2025,
[arXiv 2506.11097](https://arxiv.org/abs/2506.11097), §6.4, Fig. 5): one site's result depends on what the others
do. So at
wave 1 every sampled site is re-scored, not only the ones whose change is of interest, and the log records, per
site: the score and every check's points in each wave, any move of more than 5 points, and domain changes such
as redirects or rebrands. Per engine it records the model each wave used, the `watch` version and any notes in
the run file. The log is published with the data.

## 10. Exclusions, fixed now

- **Answers.** Only answered answers count. An answer that cites nothing stays in R's denominator, as it does
  in `watch`'s citation rate; R over answers with at least one citation is reported as a description.
- **Absorption.** A is read only from answers that cite the site, so selection and absorption stay apart, as
  arXiv 2604.25707 §11.1 asks for failed fetches (kept for the selection analysis, dropped only from
  absorption). A site with fewer than 5 citing answers that have an A in a wave has no A for that wave.
- **Sites.** Replaced only before the sample is frozen. After that, a site the CLI cannot score in a wave has
  no X for that wave and leaves that wave's analyses, by name.
- **Categories.** A category whose run fails is run once more inside the wave window; if it fails again it is
  reported missing, not replaced.

## 11. Analyses fixed in advance

The analysis code is committed before the first answer is collected, with a test on synthetic data, so the
confirmatory analysis is fixed as code and not only as prose (arXiv 2604.25707 §11.1). Its commit is recorded
in an amendment.

### Primary (P1)

For each category c, τ_c is Kendall's τ_b between X and R over the category's sites. A category in which every
site has the same R (for example, none is cited) has no τ_c and is left out, and the number left out is
reported. The statistic T is the mean of τ_c over categories. If fewer than 12 categories have a τ_c, P1 is
still run and reported, and the results say the minimum was not met.

- **Test.** X is permuted among the sites within each category, 10,000 times with a recorded seed; p is the
  share of permutations, the observed one included, whose |T| is at least the observed |T|. Two-sided,
  α = 0.05.
- **Interval.** A 95% percentile bootstrap that resamples categories, 10,000 draws.
- **A number a reader can use.** D, the mean over categories of R in the high stratum minus R in the low
  stratum (strata as drawn; categories without both are left out), with the same bootstrap interval. Reported,
  not tested.

### Secondary (S1 to S4), Holm-corrected as one family at α = 0.05

- **S1, without the gates.** P1 without the sites that have a gate at zero in either wave-0 run. A gate at
  zero means a retrieval crawler is blocked, cannot reach the site or cannot read its content (vendor
  documentation for robots and reachability, an industry study for rendering; see the
  [evidence table](../rubric/evidence-v1.1.md)); this asks whether the rest of the score adds anything.
- **S2, allowing for popularity.** P1 with X replaced by its residual from a least-squares fit, within each
  category, on the base-10 logarithm of the site's Tranco rank.
- **S3, absorption.** P1 with A in place of R, over sites that have an A, on engines where A is measured. If
  fewer than 8 categories have 3 sites with an A, S3 is reported as not estimable and leaves the family.
- **S4, named in the answer.** P1 with N in place of R.

### Described, not tested

T per engine; R, A and N by stratum; Kendall's τ_b between each pillar's points and R, averaged over
categories; R over answers that cite anything; the listed and used counts; repeat consistency per engine; the
difference between each site's two readiness runs.

### Longitudinal (L1, wave 1)

Tested only if at least 10 sites' X moved by more than 5 points between waves: the mean over categories of
Kendall's τ_b between the change in X and the change in R, with the permutation test of P1, α = 0.05. With
fewer sites moving it is described, not tested.

### Power

Before wave 0 the analysis script simulates the frozen design and reports the smallest T it detects with 80%
power at α = 0.05. That figure is added here by amendment before the first answer is collected, so a null
result can be read against it.

### How each result will be worded

| Result | Wording |
|---|---|
| T above 0, p below 0.05 | In this sample, sites with higher readiness were cited in more answers to their category's questions. |
| p at or above 0.05 | No association was detected; the design could detect a T at least as large as the recorded power figure. |
| T below 0, p below 0.05 | Sites with higher readiness were cited in fewer answers. Reported as such, and opened as a rubric issue for the next version. |

None of these is worded as the effect of changing a site. If S2 shrinks or removes what P1 found, the results
say so in the same paragraph.

## 12. Published whatever the result

- This plan and every amendment, dated. Nothing is edited back into the plan after data collection starts.
- The frozen sample, every `watch` run file and every CLI report for both waves. Where a provider's terms do
  not allow republishing answer text, the text is removed and every count derived from it is kept.
- The analysis script at the commit used, and its full output.
- Every pre-specified analysis (P1, S1 to S4, L1) with its estimate, interval and p, significant or not, and
  every described quantity.
- Every deviation from this plan, with its reason.
- A results page in `benchmark/`, in English and Chinese, linked from this plan and from
  [VALIDITY.md](VALIDITY.md), within 60 days of the last wave. If the study stops early, the reason is added
  here as an amendment and whatever was collected is published.

## Amendments

None yet.

## Sources

| Source | Used for |
|---|---|
| Zhang, He and Yao 2026, [arXiv 2604.25707](https://arxiv.org/abs/2604.25707), preprint | Appendix B: a five-arm randomised design, the causal study this plan is not. §11.1: the confirmatory analysis fixed as code before inference, separate selection and absorption outcomes, exclusion rules set in advance. §5 and §9.2: selection and absorption measured apart. |
| Watanabe and Nakayashiki 2026, [arXiv 2606.04362](https://arxiv.org/abs/2606.04362), preprint | §5: a same-period control that shares the platform's growth. §6.1 and §6.2: on one site, most of the raw ChatGPT referral growth was the platform's. |
| Schulte, Bleeker and Kaufmann 2026, [arXiv 2604.07585](https://arxiv.org/abs/2604.07585), preprint | §7: at least 7 runs per prompt per day to track brands, 8 to track sources. §5: source overlap within 24 hours of 0.32 to 0.43 per industry with engines pooled (Table 4), 0.23 to 0.51 per engine (Table 6). |
| Puerto et al. 2025, [arXiv 2506.11097](https://arxiv.org/abs/2506.11097), NeurIPS 2025 Datasets and Benchmarks | §6.4, Fig. 5: in a simulation, the gain per adopter of a rewriting method shrinks as more competing documents adopt it, the reason competitors' changes are logged. |
