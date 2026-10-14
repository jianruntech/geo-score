# Round 0, wave 0: results

中文版：[RESULTS-wave0.zh-CN.md](RESULTS-wave0.zh-CN.md)

> Wave 0 of round 0 of the [preregistered validation plan](../../PREREGISTRATION.md): English questions for a buyer in
> the US. It tests the instrument, whether the AIV readiness score goes with being cited, not whether changing a site
> changes its citations. Every number here is in [results-wave0.json](results-wave0.json), the full output of the
> analysis code fixed before the first answer was collected. The plan is not edited after collection started; what this
> wave did differently from it is listed, with the reason, under [Deviations](#deviations-from-the-plan).

| | |
|---|---|
| Answers | 2026-10-12 to 2026-10-14, three consecutive days in the frozen order |
| Readiness | two runs of the frozen CLI (geo-score 1.8.1, rubric v1.1), 2026-10-12 and 2026-10-13 |
| Sample | 16 categories, 83 sites (81 hosts; two hosts sit in two categories each) |
| Answers analysed | 1,280, all from one engine: an OpenAI model, `gpt-5.6-luna`, through an OpenAI-compatible third-party endpoint. The second engine, Gemini 2.5 Flash, contributed none (see [Deviations](#deviations-from-the-plan)) |
| Analysis code | [benchmark/prereg/analysis.py](../analysis.py), unchanged since `30a25c0` |
| Data and output | committed in `595ff4d` (run files, readiness reports, collection log) and `1ebb79f` (results-wave0.json) |

## The result in one sentence

**No association was detected; the design could detect a T at least as large as the recorded power figure (T = 0.29).**

In the 14 categories where it could be computed, the mean Kendall τ_b between a site's readiness and the share of
answers that cited it was T = 0.074 (95% interval −0.19 to 0.34, permutation p = 0.513). None of the secondary
analyses was significant after Holm's correction. Allowing for popularity (S2) did not shrink T; it was 0.178, Holm
p = 0.354. This rests on one engine, below the two the plan sets as the minimum for the primary test. It describes how
the score went with citation in this sample on these days; it says nothing about what changing a site would do.

## Primary (P1) and secondary (S1 to S4) analyses

| Analysis | What is correlated with X | T | 95% interval | p | Holm p | Categories with a τ | Left out |
|---|---|--:|---|--:|--:|--:|---|
| **P1** | R, citation rate | **0.074** | −0.19 to 0.34 | **0.513** | — | 14 of 16 (minimum 12: met) | project-management-software, note-taking-apps: every sampled site had R = 0 |
| S1 | R, without the 14 sites with a gate at zero in either run | 0.148 | −0.13 to 0.42 | 0.276 | 0.551 | 13 | the two above, and online-marketplaces (its two sites left both had R = 0) |
| S2 | R, with X replaced by its residual on log10 Tranco rank | 0.178 | 0.01 to 0.35 | 0.118 | 0.354 | 14 | the two above |
| S3 | A, answer share | not estimable | — | — | — | 7 categories had 3 sites with an A; the plan needs 8 | left the Holm family, as the plan says |
| S4 | N, named in the answer (12 ordinary-word sites have no N) | 0.141 | −0.17 to 0.46 | 0.323 | 0.551 | 14 | the two above |

- **p** is two-sided: X permuted among the sites of each category 10,000 times (seed 20261012), the observed
  permutation counted. **Interval:** 95% percentile bootstrap over categories, 10,000 draws. **Holm** is applied over
  S1, S2 and S4, at α = 0.05.
- **S3** is not a result. For the record, the script still computes the figure over the 11 categories with any τ:
  T = 0.205, interval −0.27 to 0.64, p = 0.387. It is not tested and not read.
- **S2's interval sits just above zero while its p is 0.118 (0.354 after Holm).** The plan's test is the permutation
  p. The bootstrap keeps each category's τ as observed and asks how much their mean moves when categories are
  resampled; the permutation asks how often shuffling readiness within categories gives a T this large, which with 4
  to 6 sites per category and many ties in R happens often. S2 is not significant.

**A number a reader can use (D, reported, not tested).** In the 12 categories that drew both a high-stratum and a
low-stratum site, high-stratum sites were cited in 2.8 percentage points fewer answers than low-stratum sites on
average: D = −0.028, 95% interval −0.15 to 0.09.

### By category

τ is Kendall's τ_b between X and the outcome over the category's sites; D is R in the high stratum minus R in the low
stratum. "—" means the category has no τ (every site had the same outcome) or lacks a stratum.

| Category | Sites | Low / mid / high | τ, P1 | τ, S1 | τ, S2 | τ, S4 | D |
|---|--:|:-:|--:|--:|--:|--:|--:|
| `large-language-models` | 6 | 2 / 2 / 2 | 0.00 | +0.50 | +0.09 | +0.08 | +0.06 |
| `vector-databases` | 5 | 2 / 1 / 2 | −0.12 | +0.24 | +0.12 | +0.24 | +0.03 |
| `cloud-infrastructure` | 6 | 2 / 2 / 2 | +0.07 | −0.20 | +0.07 | −0.20 | −0.18 |
| `javascript-web-frameworks` | 6 | 2 / 2 / 2 | +0.69 | +0.67 | +0.45 | +0.69 | +0.16 |
| `ecommerce-platforms` | 6 | 2 / 2 / 2 | −0.35 | −0.63 | −0.12 | −0.35 | −0.02 |
| `crm-software` | 4 | 0 / 2 / 2 | +0.91 | +0.91 | +0.18 | +1.00 | — |
| `online-payment-providers` | 4 | 0 / 2 / 2 | +0.71 | +0.71 | +0.71 | +1.00 | — |
| `buy-now-pay-later` | 4 | 0 / 2 / 2 | 0.00 | 0.00 | +0.33 | −0.33 | — |
| `online-course-platforms` | 6 | 2 / 2 / 2 | +0.50 | +0.50 | +0.21 | +0.67 | +0.33 |
| `language-learning` | 6 | 2 / 2 / 2 | +0.60 | +0.53 | +0.45 | +0.91 | +0.13 |
| `management-consulting` | 6 | 2 / 2 / 2 | −0.26 | −0.26 | −0.26 | +0.07 | −0.05 |
| `project-management-software` | 5 | 2 / 1 / 2 | — | — | — | — | 0.00 |
| `note-taking-apps` | 4 | 2 / 1 / 1 | — | — | — | — | 0.00 |
| `3d-printers` | 5 | 2 / 2 / 1 | −0.74 | −0.33 | 0.00 | −0.74 | −0.51 |
| `accounting-software` | 6 | 2 / 2 / 2 | −0.75 | −0.71 | −0.45 | −0.74 | −0.28 |
| `online-marketplaces` | 4 | 2 / 2 / 0 | −0.24 | — | +0.71 | −0.33 | — |

Each site's X, R, A, N, stratum, Tranco rank, readiness runs and per-pillar points are in `categories` in
[results-wave0.json](results-wave0.json).

## Described, not tested

**T per engine.** One engine ran, so T for the OpenAI-model engine is P1's: 0.074 over 14 categories (interval −0.19
to 0.34). Gemini has no T.

**R, A and N by stratum**, the mean over sites (pooled across categories, so each mixes categories with different
base rates; D above is the within-category comparison):

| Stratum | Sites | R | A (sites with an A) | N (sites with an N) |
|---|--:|--:|--:|--:|
| Low (below 51) | 26 | 0.125 | 0.061 (11) | 0.163 (23) |
| Mid (51 to 65) | 29 | 0.088 | 0.052 (10) | 0.137 (26) |
| High (66 and above) | 28 | 0.160 | 0.064 (13) | 0.206 (22) |

**Each pillar's points against R**, Kendall's τ_b averaged over categories, with no interval and no test: Reachable
−0.23 (13 categories), Understandable +0.12 (14), Content Citability +0.01 (14), Brand Credibility +0.21 (13), Answer
Fit −0.10 (13). Five unadjusted means over 13 or 14 small categories; read none of them as a finding.

**R over answers that cite anything.** 1,266 of the 1,280 answers cited at least one URL. The 14 that cited nothing
are 13 in javascript-web-frameworks and 1 in language-learning, so R over citing answers equals R everywhere else.
Per site: `described.R_given_any_citation`.

**How often the sampled sites were cited.** 40 of the 83 sites were cited at least once in their category's 80
answers; 43 never were, and in two categories no sampled site was.

**The two readiness runs.** All 81 hosts were scored in both runs. The difference between a site's two scores: mean
0.22 points, median 0, largest 5, none above 5.

**Not computed.** The listed and used source counts and repeat consistency per engine (section 11), and how many
answers searched per engine (section 6): see deviation 4.

## How to read "no association was detected"

"Not detected" is not "none". The registered power figure, 0.289, is the smallest mean T the frozen design detects
80% of the time at α = 0.05, in a simulation of these 83 sites. An association that strong would most likely have
shown; one weaker could exist and go undetected. The observed T is 0.074, but the 95% interval reaches 0.34, so an
association of about 0.29 is unlikely here without being ruled out. The most this wave supports: if readiness and
citation by this engine go together across sites like these, the association is probably weaker than T = 0.29.

The registered figure assumed two engines, 16 answers per question; wave 0 had 8. The same simulation (same seed, 200
simulations and 999 permutations per effect size) with 8 answers per question gives **0.300**, so the reading barely
changes. That rerun was made for this page after the data were in and is not part of the plan:

```bash
python3 -c "import sys; sys.path.insert(0, 'benchmark/prereg'); import analysis as A; \
print(A.power(A.design_of('benchmark/prereg/round0'), [0, .05, .1, .15, .2, .25, .3, .4, .5, .7, 1.0], answers_per_q=8)['smallest_T_with_80pct_power'])"
```

## Deviations from the plan

1. **One engine, not two (sections 3 and 7; amendment of 2026-10-12, items 1, 4 and 5).** The amendment counted on
   Gemini's free tier answering about 500 grounded questions a day. For `gemini-2.5-flash` it allowed 20: every one of
   Gemini's 32 runs (each category's run and its rerun) stopped on HTTP 429 "You exceeded your current quota", the
   error naming a free-tier limit of 20 requests, after 70 answers over the three days in all. Under amendment item 5
   the answers of a stopped engine are not used, and a category whose rerun stops too has no answers from that engine.
   So Gemini is missing from all 16 categories, and every analysis rests on the OpenAI-model engine alone: 1,280 of the
   2,560 answers planned. The plan's minimum for the primary test is two engines, so that minimum was not met. The
   reason is the free tier's quota; the engine was not chosen by its results, and the stopped-engine rule was fixed
   before collection and is applied unchanged.
   Gemini's 70 answers are no longer in the published run files: the Gemini API terms for Grounding with Google
   Search do not allow storing, republishing or analysing grounded results, so
   [redact_gemini.py](redact_gemini.py) removed the answer text, links, search queries and everything computed from
   them on 2026-10-14, keeping each request's question, status, usage and timing. The analysis output is unchanged by
   this, since none of those answers was used.
2. **`failed_engines` is empty in results-wave0.json** although Gemini contributed nothing. The script counts an
   engine as failed only when it answered at least 5 questions without citing anything (amendment item 5); Gemini was
   stopped, not citationless, so it has no used run in any category (`run_files.<category>.used` lists only `openai`).
   The script is not changed after the data; this page states the gap instead.
3. **The power figure assumed two engines.** The wording uses the registered 0.29, as the plan requires; the figure
   for one engine is reported above as a description (0.300).
4. **Three described quantities are not reported.** The listed and used source counts and repeat consistency per engine
   (section 11) and how many answers searched (section 6) are not computed by analysis.py as committed before
   collection, and no code was added after the data to compute them for this page. The run files hold what they need
   (`citations`, `sources_listed`, `search_queries`, the ledger's `search_calls`).
5. **Where the link to this page lives (section 12).** The plan asks for the results page to be linked from the plan
   and from VALIDITY.md, and also says nothing is edited back into the plan after collection starts. The plan is left as
   registered; the link is in [VALIDITY.md](../../VALIDITY.md), the [round 0 README](README.md) and the repository
   README.

Reported, as amendment item 5 asks, and not deviations:

- In crm-software the OpenAI-model engine stopped after 59 answers (three read timeouts in a row) and was run once more
  at once; the rerun answered all 80 and the stopped run's answers are not used. Every other category's first run
  answered all 80.
- The release that registered the sample and the power figure, v1.8.2, was published at 2026-10-12 15:35 UTC; the
  first readiness run started at 15:38 and the first answer run at 15:39.
- Each category ran on its scheduled day. The two readiness runs fell on different UTC days, within 7 days of each
  other, and no site failed either.

## Limitations

- **One engine.** One OpenAI model through a third-party endpoint: the model behind it cannot be verified beyond the
  id it reports, and its answers may differ from the official API's. Nothing here covers Gemini, Perplexity, Anthropic,
  the consumer apps, Google AI Overviews or Chinese engines.
- **One point in time.** Three days in October 2026. Engines and their indexes change; wave 1 repeats the runs.
- **One location.** Every answer and readiness run came from one machine in the US, with `country` set to `US`.
- **One kind of sample.** English questions for a buyer in the US, in 16 software and consumer categories taken from
  English Wikipedia lists. Sites were drawn across the score bands on purpose, so the sample is not the field as it
  is. With 4 to 6 sites per category and half the sites never cited, each category's τ rests on few sites and many
  ties.
- **The CLI's reading of the rubric.** X leaves out the three judgement checks, as the CLI does.
- **An association, not an effect.** Nothing here changed a page (plan section 2).

## Data and code

| What | Where |
|---|---|
| Plan and amendments | [PREREGISTRATION.md](../../PREREGISTRATION.md) ([中文](../../PREREGISTRATION.zh-CN.md)), registered by v1.8.1 and v1.8.2 |
| Frozen sample and configs | [sample.json](sample.json), [sample/](sample/) |
| Run files (33, every run of both engines, stopped ones included) | [runs/wave0/](runs/wave0/) |
| Readiness reports and logs | [readiness/wave0/](readiness/wave0/) |
| Collection log | [collection/wave0/log.tsv](collection/wave0/log.tsv) |
| Analysis code and its synthetic test | [analysis.py](../analysis.py), [test_analysis.py](../test_analysis.py) at `30a25c0` |
| Full output | [results-wave0.json](results-wave0.json) |

To reproduce (standard library only; the output was made with Python 3.12, and a rerun gives the same file except
`computed_at`):

```bash
python3 benchmark/prereg/analysis.py analyze --round benchmark/prereg/round0 --wave 0 --power-t 0.289 \
  --out benchmark/prereg/round0/results-wave0.json
```

The run files keep the answer text as collected. A replication should use the official OpenAI API.

## Next

- **Wave 1** repeats the same questions, configs and sites 12 weeks after wave 0 began, from 2027-01-04, and re-scores
  every site (plan section 9). It needs both engines on a paid quota so that neither stops. Because wave 0 has only the
  OpenAI-model engine, how wave 1's analyses and L1 treat an engine that only wave 1 has is to be fixed by a dated
  amendment, registered before wave 1 starts.
- **L1** is tested only if at least 10 sites' X moves by more than 5 points between the waves; otherwise it is
  described. In wave 0 no site's two runs differed by more than 5.
- The results page for wave 1 follows within 60 days of it, published whichever way it goes.
