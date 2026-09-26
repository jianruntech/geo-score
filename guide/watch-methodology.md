# How `watch` counts: intervals, the paired diff and the branded split

Chinese version: [watch-methodology.zh-CN.md](watch-methodology.zh-CN.md)

This page describes the arithmetic behind `geo_score.py watch report` and `watch diff`: what a
citation rate is, which interval is quoted with it, and when a difference between two runs is
called a change. It is about measurement only. The tool counts citations in answers from the
providers' APIs; API answers are not the consumer apps, a question not measured is never a zero,
and citations are not traffic.

## 1. The unit: an answer, clustered by question

A run asks every question in `queries.csv` to every engine, `runs` times each. Each answer is
scored `cited` (it cites a URL the brand owns) and `mentioned` (its text names the brand). A
citation rate is cited answers over answered answers.

Answers are not independent draws. The question decides most of the outcome: whether a page
exists that answers it, which sources the engine's search returns for it, how the engine words
its reply. Asking the same question again mostly draws again from the same pool, and so does
asking it on another engine. Three asks of ten questions are closer to ten observations than to
thirty. Statistics that treat every answer as independent report intervals that are too narrow
and call changes that are not there.

Two consequences run through the rest of this page: intervals resample questions, not answers,
and a diff compares each question with itself.

## 2. Intervals

### Wilson (every answer independent)

For k cited answers out of n, with z = 1.96:

- p = k / n
- centre = (p + z² / 2n) / (1 + z² / n)
- half-width = z · √(p(1 − p) / n + z² / 4n²) / (1 + z² / n)

This is `cited_ci`, unchanged from 1.2.0. It is the right interval when every question was
answered once, and it is the one reports quote in that case.

### Cluster bootstrap (answers grouped by question)

When some question in a block has more than one answer (repeated asks, or several engines in
the overall row), reports quote `cited_ci_clustered`:

1. Group the answers by `query_id`: question q has k_q cited answers out of n_q.
2. Draw Q questions with replacement from the Q questions in the block, and compute
   Σ k_q / Σ n_q over the draw. Repeat 2,000 times.
3. Take the 2.5th and 97.5th percentiles of the 2,000 rates (the 51st lowest and the 51st
   highest).
4. Widen the result to cover the Wilson interval if it is narrower.

Step 4 matters with few questions. Three questions each cited in half their answers resample to
exactly 50% every time, a zero-width interval that no one should quote. Answers that share a
question never carry more information than independent answers, so Wilson is the floor.

The resampling is seeded, so a run always reports the same interval: the seed is the first 16
hex digits of SHA-256 of the run id (any `-2` suffix dropped) and the block's label, read as an
integer and passed to Python's `random.Random`. Each block (`overall`, `headline`, each engine,
each competitor, each question type) also carries `n_questions`. The clustered interval is quoted
exactly when `answered` is greater than `n_questions`.

## 3. Questions that name the brand

A question such as "acme vs rival" or "is acme worth it" puts the brand's name in the engine's
search. The brand's own pages then rank for it and the answer almost always cites them. Such a
question measures whether the engine can find a brand it was told about, not whether a buyer who
has not heard of the brand is sent there. Mixed into the headline, these questions inflate the
rate, and because they are cited every week they also make real movement look smaller.

At run time every question is flagged with the matcher used on answers: the brand's name,
aliases and domains; whole words for Latin script (Lumo does not match Lumos); anywhere for
Chinese, Japanese and Korean names; and a CJK character next to a Latin name counts as a word
break. The run file stores `brand_in_query` and `competitor_in_query` on each question.

An optional `branded` column in `queries.csv` overrides the matcher: `yes` counts the question
as naming the brand even if the text does not match (a nickname, a logo description), `no` keeps
a false match (a brand name that is also a common word) in the headline, and `auto` (the
default, also an empty cell) follows the matcher.

The report then shows:

- the headline: cited and mentioned rates over answers to questions that do not name the brand,
  with the number of answers and questions behind it;
- a separate line for the questions that name the brand, with their own n and interval.

The per-engine, share-of-voice and question-type tables still count every question and say so
under the first table. `watch check` prints how many questions name the brand and warns when it
is more than 30%, because the headline then rests on few questions. The CSV report has a
`branded` column (Y or N) so a spreadsheet can make the same split.

Runs saved by 1.2.0 have no flags. When such a run is reported, the flags are computed from the
saved question text and the run's own brand, aliases and domains, and the report says so in a
note. The run file itself is never rewritten.

## 4. The diff: a paired test per row

`watch diff A B` compares the questions both runs asked, on the engines both runs have. Rows are
one per engine plus "all engines".

### Pairing

Answers are paired by question, engine and ask number, over the asks both runs made: if run A
asked each question once and run B three times, only B's first ask is used. For question q, the
net change d_q is the number of cited answers in B minus the number in A, summed over its paired
asks (and, in the all-engines row, over the engines). The row reports:

- `before_paired`, `after_paired`: cited share of the paired answers in each run, n = `n_asks`;
- `delta_pp`: 100 × Σ d_q / `n_asks`, in percentage points;
- `n_pairs` (question × engine pairs) and `n_questions`.

The 1.2.0 fields `before`, `after`, `delta` and `p_value` are still present with their old
meaning (every answer, unpaired two-proportion z-test), but no verdict uses them.

### The test: exact sign-flip, which is McNemar with one answer per question

If nothing changed between the runs, the two runs are exchangeable, so each question's net change
is as likely to point up as down, whatever its size. Among the m questions with d_q ≠ 0, the
exact two-sided p-value is the share of the 2^m sign patterns whose total is at least as far
from zero as the observed one:

- p = #{ signs s : |Σ s_q · |d_q|| ≥ |Σ d_q| } / 2^m

The distribution is computed exactly by convolution, not by sampling. When every question has
one answer per run (one engine, `runs` = 1) each d_q is −1, 0 or +1 and this is the exact
McNemar test on the g questions gained and l questions lost:

- p = min(1, 2 · Σ_{i=0..min(g, l)} C(g + l, i) / 2^(g + l))

which the code computes with `math.comb` in that case. The result is `p_paired`.

Counting cited answers rather than "cited in at least one ask" keeps the information from
repeated asks. In 400 simulated diffs of 30 questions on 2 engines asked 3 times (one test on
all engines, no correction), a drop of 10 points per answer was detected 53% of the time by
counting answers and 18% of the time by "any ask"; with no drop, both called a change in fewer
than 5% of the diffs.

### Holm across the rows

Each diff makes several comparisons: one per engine and one for all engines. Testing each at
0.05 would raise false alarms with every engine added. The p-values of the testable rows are
adjusted by Holm's step-down method: sort the m p-values from smallest to largest,
p(1) ≤ … ≤ p(m), and set

- adjusted p(i) = max over j ≤ i of min(1, (m − j + 1) · p(j))

Example with three rows, p = 0.012 (engine A), 0.20 (engine B), 0.020 (all engines): sorted,
0.012 × 3 = 0.036, then 0.020 × 2 = 0.040, then 0.20 × 1 = 0.20. Engine A and all engines are
changes at 0.05, engine B is within noise. The result is `p_adjusted`.

When only one engine has answers in both runs, the all-engines row is the same test as that
engine's row and takes its result instead of being counted twice.

### Verdicts

- `not measured`: one of the runs has no answer for this row.
- `too few questions to tell`: fewer than 6 questions were answered in both runs. With 5, even
  all five flipping the same way gives p = 2 / 2^5 = 0.0625, so no outcome could be called a
  change; saying "within noise" would suggest a test was run that could have said otherwise.
- `change`: `p_adjusted` < 0.05.
- `within noise`: otherwise.

`watch diff --fail-on-drop` exits with code 4 when any row's verdict is `change` with a negative
`delta_pp`, so a CI job can stop on a drop and on nothing else.

### The interval for the change

`delta_ci` is a 95% paired bootstrap: draw questions with replacement (each with its d_q and its
paired asks), compute Σ d_q / Σ asks, 2,000 times, and take the 2.5th and 97.5th percentiles. It
is seeded from the two run ids and the row label, as above. It is then widened to cover
Newcombe's hybrid score interval for paired proportions (1998), computed on the table of paired
asks (a both cited, b lost, c gained, d neither, n = a + b + c + d):

- p1 = (a + b) / n before, p2 = (a + c) / n after, with Wilson intervals (l1, u1) and (l2, u2)
- φ = (ad − bc) / √((a + b)(c + d)(a + c)(b + d)), where a positive ad − bc is first reduced by
  n / 2 (not below 0), and φ = 0 when a margin is empty
- lower = (p2 − p1) − √((p2 − l2)² − 2φ(p2 − l2)(u1 − p1) + (u1 − p1)²)
- upper = (p2 − p1) + √((p1 − l1)² − 2φ(p1 − l1)(u2 − p2) + (u2 − p2)²)

The floor keeps a week in which nothing flipped from reporting a change of "0 to 0 points". The
interval is left out (null) below 6 questions.

## 5. A worked example

A synthetic brand, Acme, tracks 10 questions on one engine with `runs` = 3, so 30 answers a week.
Questions q09 "acme vs rival" and q10 "is acme worth it" name the brand. Cited answers per
question, out of 3:

| question | q01 | q02 | q03 | q04 | q05 | q06 | q07 | q08 | q09 | q10 |
|---|---|---|---|---|---|---|---|---|---|---|
| week 1 (run 20260919T083000Z) | 3 | 3 | 3 | 2 | 0 | 0 | 0 | 0 | 3 | 3 |
| week 2 (run 20260926T083000Z) | 1 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 3 | 3 |
| net change d_q | −2 | −3 | −1 | −2 | 0 | 0 | +1 | 0 | 0 | 0 |

### Week 1 report

Counting all 30 answers as 1.2.0 did: 17 of 30 cited, 57%, Wilson 39.2% to 72.6%.

The headline now leaves out q09 and q10: 11 of 24 answers, 46%, over 8 questions. Wilson on 24
answers would say 27.9% to 64.9%. The answers come three to a question and the questions are
very different (three always cited, four never), so the cluster bootstrap gives 12.5% to 75.0%.
That is the interval the report quotes. The two branded questions are 6 of 6, 100%, Wilson 61.0%
to 100%. The report's first lines:

```
Cited in 46% of answers to questions that do not name Acme (11 of 24, 8 questions, 95% CI 12–75%) · mentioned in 46%
Questions that name Acme (2, kept out of the headline): cited in 100% (6 of 6, 95% CI 61–100%) · mentioned in 100%
```

### The diff from week 1 to week 2

Paired answers: 30 (10 questions × 3 asks). Before 17 of 30 (56.7%), after 10 of 30 (33.3%),
a change of −23.3 points.

Five questions moved: four down (by 2, 3, 1 and 2 answers) and one up (by 1). The sign-flip test
counts the 2^5 = 32 ways to assign signs to 2, 3, 1, 2 and 1; six of them reach a total of 7 or
more in either direction, so p = 6 / 32 = 0.1875. With one engine there is nothing to correct
for, and `p_adjusted` = 0.1875. Verdict: within noise.

The change interval is −46.7 to 0.0 points: the paired bootstrap over the 10 questions, widened
to cover Newcombe's −39.8 to −4.0 points on the 30 paired answers (9 cited both weeks, 8 lost,
1 gained, 12 neither).

The same data under two wrong units:

- Treating the 30 answers as 30 independent pairs, McNemar on 8 lost and 1 gained gives
  p = 2 × (1 + 9) / 2^9 = 0.039, a "change". That counts q02's three lost answers as three pieces
  of evidence when they are one question moving.
- The 1.2.0 unpaired z-test on 17 of 30 against 10 of 30 gives p = 0.069.

Seven fewer cited answers, concentrated in four questions, is what week-to-week variation on 10
questions can produce. `watch diff --fail-on-drop` exits 0 here. The lists of citations lost
and gained still name q02, q04 and q07 so they can be read, but they are not a trend.

## 6. How the method was checked

The test suite (`cli/test_geo_watch.py`, offline) includes:

- a null check: 200 pairs of runs drawn from the same generator (30 questions, 2 engines, 2 asks,
  per-question citation probabilities from 2% to 98%); a `change` verdict on any row appeared in
  4 of the 200 diffs (2%), and the test fails above 16 (8%);
- a planted drop (citation probability 80% in week 1, 20% in week 2): every row is a `change`
  with a negative change and an interval below zero, and `--fail-on-drop` exits 4;
- strongly clustered answers (20 questions asked 10 times, half always cited, half never): the
  clustered interval is more than twice as wide as Wilson.

In a longer simulation, 1,000 null diffs of 30 questions on 2 engines asked 3 times, with
per-question citation probabilities from 30% to 70% and a repeated ask returning the first
answer 80% of the time, 1.2.0's unpaired, uncorrected tests reported a change in 36.2% of the
diffs and the paired, Holm-corrected diff in 2.6%. With independent asks the figures were 8.9%
and 2.3%.

## Where the fields are

- Run files: [schema/watch.v1.json](../schema/watch.v1.json), `summary.headline`,
  `summary.branded`, `summary.brand_flags`, `cited_ci_clustered` and `n_questions` in every rate
  block, and `brand_in_query`, `competitor_in_query` and `branded` on each question.
- Diff output (`watch diff --format json`, or the MCP `diff` tool with `format: json`): the
  `diff` and `diff_row` definitions in the same schema.
- Commands and flags: [cli/README.md](../cli/README.md).
