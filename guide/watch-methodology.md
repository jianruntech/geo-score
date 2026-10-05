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

The report also lists every question on its own, in the table "Who is named for each question"
(`summary.by_question`): how many answers it got, how many of them cite or name the brand and
each tracked competitor, how many name none of them, and how many came from a web search. These
are counts, with no interval and no test; three of four answers is not a rate to compare across
weeks. "Most cited" (`leader`) names a tracked brand only when the question has at least 4 answers
and that brand is cited by more of them than any other. Whether an answer searched is read from
what the run saved: yes when the provider reported a search, exposed a search query or the answer
cites a URL; no when an OpenAI, Gemini or Anthropic answer shows none of these; unknown for
Perplexity and OpenRouter, whose APIs search on every call or do not say, and whose adapters record
one search per answer either way. An answer given without a search cannot cite anything.
"No tracked brand named" counts answers that name none of the brands in the config, which says
nothing about brands the config does not list.

"What the engines searched for" lists the searches the answers expose, the 15 most frequent first
(`summary.searches.top`); OpenAI, Gemini and Anthropic return them, Perplexity and OpenRouter do not.
A line under the table counts, over every exposed search, how many contain a year and how many contain
a ranking or comparison word (`summary.searches.modifiers`: `total`, `with_year`,
`with_ranking_word`). A year is a four-digit number from 1900 to 2099 with no letter, digit or
underscore beside it; a Chinese, Japanese or Korean character beside it is a break, so `2026年` counts.
The words are best, top, vs, versus, review, reviews, compare, comparison, alternative and
alternatives as whole words in any letter case (so "topic" is not "top"), and `最好` `最佳` `推荐`
`排行` `排名` `哪家` `哪个好` `对比` `评测` anywhere. A search counts once for each, however many it
holds, and a search that repeats the question's own words counts as well: the line describes what
was searched, not what the engine added to the question. When an answer's usage reports a search but
no query came back, the section says how many answers, per engine
(`summary.searches.answers_searched_without_queries`, and `searched_without_queries` on each row of
`summary.engines`). Some OpenAI-compatible endpoints a `base_url` points at return the search calls
without their queries; those answers are in neither the table nor the counts, which is not the same
as searching with no year in the query. Only OpenAI, Gemini and Anthropic answers are read this way,
since the Perplexity and OpenRouter adapters record one search per answer whatever happened.

Each answer also records where it names each brand in the config. `mention_order` ranks the brands the
answer names by where each is first named, the earliest match of its name, aliases or domains with the
matcher of `mentioned`: 1 is named first. A brand the answer does not name has no order, and neither
have two brands first named at the same place, as when one name contains the other. `mention_share` is
the share of the answer's sentences that name the brand, every sentence counted the same. A sentence
ends at a line break, at `。！？`, or at `.` `!` `?` followed by whitespace, so a domain or a decimal does
not end one; a piece with no letter or digit, such as a table rule, is not a sentence. Both are read
from the answer as saved, which keeps its first 20,000 characters. The report gives, per engine ("By
engine") and for each brand ("Share of voice"), "named first (tracked)": the answers that name that
brand first among the brands in the config, out of the answers that name at least one of them; and
"sentence share": the mean `mention_share` over the answers that name it. Both describe the answers and
carry no interval or test. They see only the brands in the config, so first among the brands you track
may not be first in the answer. The order is the order of first mention, not a position in a list, and a
longer answer spreads one name over more sentences, so sentence shares from engines that write at
different lengths are not on one scale.

Each question can carry a type, the `intent_tier` column of `queries.csv`, and the report gives each
type its own rate and interval ("By question type"). A rate describes the questions behind it: a set
of one type describes that one kind of question, and a type with few questions gets a wide clustered
interval. The column is free text, and `watch check` counts the questions of each type, with a note
when all share one type or none has one. These labels are suggested, so that sets read alike:

| `intent_tier` | The question | Example |
|---|---|---|
| `list` | asks for the options in a category | best invoicing app for freelancers |
| `vs` | compares named products | acme vs rival |
| `alternative` | asks what to use instead of a named product | alternatives to rival |
| `pricing` | asks about cost, plans or a free tier | how much does an invoicing app cost |
| `problem` | describes a situation and names no category or brand | clients keep paying me late and I lose track of who owes what |
| `persona` | says who it is for | invoicing app for a two-person design studio |
| `verdict` | asks whether something is worth it or can be trusted | is acme worth it |
| `channel` | is about buying or selling through another route: franchise, wholesale, distributor, procurement | invoicing software with a reseller programme |

A `verdict` question about the brand names it, so it counts on the branded line (section 3), not in
the headline.

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
asks (and, in the all-engines row, over the engines). A question is paired only with itself: when
its text changed between the runs under the same `query_id` (compared case-folded, with whitespace
collapsed), it is left out of every row and named in the diff's notes. The row reports:

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
  A second screen applies before Holm's correction (Tarone's screen for discrete tests): with m rows
  in the family, a row with m × 2 / 2^n ≥ 0.05 is `too few questions to tell` and leaves the family,
  and the screen repeats on the rows left. For six questions on two engines plus the all-engines row,
  3 × 2 / 2^6 = 0.094. When every row has the same n, such a row could not pass even if every question
  moved the same way; when the rows differ, a screened row might have passed as the last in Holm's
  order, so the screen is conservative: it can call a real change too few to tell, never the reverse.
- `change`: `p_adjusted` < 0.05.
- `within noise`: otherwise.

`watch diff --fail-on-drop` exits with code 4 when any row's verdict is `change` with a negative
`delta_pp`, so a CI job can stop on a drop and on nothing else.

### Answers with no citation at all

Each adapter reads one answer format per provider (for OpenAI, `url_citation` annotations), so a
provider that renames or moves its citations reads as an engine that stopped citing anything. Two
warnings look for that shape, not for the brand: the report warns under "By engine" when an engine
answered 5 or more questions and none of its answers carried a citation of any domain
(`with_citations` is 0 in `summary.engines`), and `watch diff` gives an engine's row a `warning`, and
puts the same words in the notes and on stderr, when the share of its answers carrying any citation
fell from at least 50% to below 5% with the same model and at least 5 questions answered in the later
run. Both count questions, not answers: the answers to one question move together, so one question
asked five times is not five pieces of evidence. Neither changes a verdict
or an exit code: in the saved answers a format change and an engine that stopped citing look the
same, so the warning asks for one answer to be checked with `watch ask`.

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

## 7. What a run cannot see

A run measures what the providers' search-enabled APIs return, and nothing beyond it:

- **Other surfaces.** Google AI Overviews and AI Mode, the AI summaries inside apps such as TikTok, Reddit or
  Xiaohongshu, and the consumer chat apps run their own models, prompts and retrieval; no API returns them.
- **The person asking.** An assistant's memory, account settings and history shape its answers, and an API
  call has none of them. The `country` hint is the only location an API takes, and only some engines apply it.
- **Agents choosing tools.** Which library or API a coding agent picks is decided inside the agent, not in a
  search answer.
- **The retrieval behind a citation.** The citations an API returns are the end of its retrieval: what it
  searched and read but did not cite is mostly not returned, and the shape of what is returned changes between
  API versions, so a sudden move can be the format rather than the engine. The report and the diff warn when an
  engine's answers stop carrying citations altogether ([Answers with no citation at all](#answers-with-no-citation-at-all)).
- **Merit.** A citation is presence, not a verdict on quality: it says an engine named and linked a page, not
  that what it said is true or that the page deserved it. Engines also cite misleading and self-promotional
  pages, so a high rate is not evidence that a source is good, and a low one is not evidence that it is bad.

## 8. One ask, one day, one month

One ask of one question on one engine is an anecdote. The same question gets a different answer from one ask
to the next: the model samples its wording, and its search can return other sources on the next call. One run
of the whole set is a measurement of one day. Asks made minutes apart share that day's index, rankings and
model version, so they are not independent of each other, and they say little about the next week.

**Pooling.** `watch report --since DAYS` (or `--runs A..B`) counts several saved runs as one set of answers.
It pools only runs that asked the same questions (the same `questions_hash`) as many times each (the same
`runs`), on the same engines with the same providers and models, from the same `country`, with the same brand
domains and URL prefixes as the newest run in the window. Otherwise it refuses and names each run that differs
and why: a rate pooled over two question sets or two models describes neither, and every answer weighs the same
in a pool, so a run that asked each question five times would count five times as much as a run that asked once. The output gives the runs, the calendar days from the first to the last,
the answers, the headline rate and a row per engine. The interval is the cluster bootstrap of section 2 with
one cluster per question: every answer to a question, from every run and every engine, is resampled together.

What pooling buys is more answers per question, so each question's rate is pinned down more closely, and,
because every run pooled asked each question as often, one unusual day weighs less. What it does not buy is more questions. The interval resamples questions, so it
narrows only as far as their number allows: ten questions asked every week for a month are still ten
questions. A pooled rate describes a period. It is not a test for a change, and no pooled diff exists; to ask
whether something changed, compare two runs with `watch diff`.

However many runs are pooled, the API channel cannot reproduce what a person sees in an app: the account
(signed in or not, memory, history, settings), the network address a request comes from and the location a
provider infers from it, and the app's own model, prompts and personalisation. Pooling API runs gives a steadier
API rate, not an estimate of the apps (section 7).

**What a plan can tell.** `watch run --dry-run` prints the plan's resolution before anything is spent: the
fewest questions that must move the same way between two runs before `watch diff` can call a change. With E
engines, diff tests m = E + 1 rows, each engine and all engines; with one engine, m = 1, because the
all-engines row is that engine's test. An exact paired test on n questions reaches at best p = 2 / 2^n, every
question moving the same way, and Holm's first step holds the smallest p to 0.05 / m. So k is the smallest n
with m × 2 / 2^n < 0.05, the screen of section 4:

| engines E | rows m | k |
|---|---|---|
| 1 | 1 | 6 |
| 2 | 3 | 7 |
| 3 | 4 | 8 |
| 5 | 6 | 8 |

A set with fewer than k questions gets "this plan cannot detect a change": every diff of two such runs reads
`too few questions to tell`. Adding questions helps; adding engines raises k; asking each question more times
(`runs`) does not lower it, because the test counts questions, not answers. k is a floor, not a promise: at
least k questions must move in the direction of the change, a question that moves the other way never helps,
and a real change of a few points moves only a few questions. The figure assumes every engine answers every
question; a run with failures pairs fewer.

## 9. How much of the answer your pages support, and sources listed against used

A citation says an engine chose a page. It does not say how much of the answer the page carried, and
research on generative engines measures the two apart: being selected as a source, and being absorbed into
the answer ([arXiv 2604.25707](https://arxiv.org/abs/2604.25707), §5; §9.2 lists an absorption score
among the measures a dashboard should carry, next to the selection rate). The first measure of
generative-engine visibility was of the second kind: the words of the answer's sentences that cite a source,
over all the answer's words, and the same with each sentence weighted down by its position
([arXiv 2311.09735](https://arxiv.org/abs/2311.09735), §2.2.1, Eq. 2 and Eq. 3). That paper measured it in a
simulated engine whose input already held the source, not whether a page gets chosen (§3.1, §9). `watch`
records two such measures where the providers document what they need. Both are reported beside the cited
rate and never merged into it; neither enters the headline, the intervals or `watch diff`.

### Answer share: the text your pages support

Each answer records where its citations sit (`spans`: `start`, `end`, `urls`, `kind`, character offsets
into the answer as saved), read only from fields the provider documents:

| Engine | What the API gives | `kind` | Offsets |
|---|---|---|---|
| OpenAI (Responses) | `url_citation` annotations on `output_text`, `start_index` and `end_index`: "the URL citation in the message" ([reference](https://developers.openai.com/api/reference/resources/responses/methods/create), URLCitation) | `marker` | characters of that text part |
| OpenRouter | `url_citation` annotations on the message, the same two fields ([web search](https://openrouter.ai/docs/guides/features/plugins/web-search)) | `marker` | characters of the message |
| Perplexity | `[n]` marks in the text, each naming "the result whose `id` is n" ([migration guide](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/how-to), Inline citations) | `marker` | found in the text |
| Gemini, Interactions API (default) | `url_citation` annotations on each text block: "a text segment (defined by `start_index` and `end_index`)" ([guide](https://ai.google.dev/gemini-api/docs/google-search)), "measured in bytes" ([reference](https://ai.google.dev/api/interactions-api), UrlCitation) | `segment` | UTF-8 bytes of that block |
| Gemini, `"api": "generate_content"` | `groundingSupports`: a `segment` (`partIndex`, `startIndex`, `endIndex`, "measured in bytes", and its `text`) and the `groundingChunkIndices` that support it ([reference](https://ai.google.dev/api/generate-content), GroundingSupport, Segment) | `segment` | UTF-8 bytes of that part |
| Claude | text blocks that carry `citations`: "each text block can contain a claim ... and a list of citations that support the claim" ([citations](https://platform.claude.com/docs/en/build-with-claude/citations)) | `segment` | the block's own text |

A `segment` is the text the provider says a source supports. A `marker` is where the provider says a
citation sits in the text; the text it supports is read as the sentence it closes: the sentence it sits in
when text comes before it there, otherwise the sentence before. That rule is geo-score's, not the
provider's. Google's guide slices the Interactions text
with its offsets in a Python example, which counts characters, while its reference says bytes; the two agree
on ASCII text, and `watch` follows the reference.

An answer gets no `spans`, and is **not measured**, never 0, when it has no citation; when any citation came
without a usable position (one missing, outside its text, cutting a character in two, or a Gemini segment
whose bytes do not hold the `text` it gives); when it passes a cap (500 citations, 20 URLs on one); and, for
Perplexity, when the search results carry no `id`. Sonar's documented response shows none, and the
documentation ties `[n]` to a result only through it, so positions are kept only when every result has an id
and the ids run 1, 2, 3 in order, the reading `cited` has always used. An OpenAI-compatible `base_url` that
strips annotations looks like an answer with no citation, which is why that is not measured rather than 0.

From the spans, `supported_share` gives three numbers for the brand. The sentences are those of
`mention_share` (section 1), split with every marker blanked out, so a mark never counts as text. For a
sentence s, |s| is its characters (not whitespace, marks left out) and c(s) the part of them a span with a
URL the brand owns supports, by the matching that decides `cited`: all of |s| when such a marker credits s,
otherwise the characters of s inside such segments.

- `chars`: Σ c(s) / Σ |s|.
- `sentences`: the sentences with c(s) > 0, over all sentences.
- `weighted`: Σ c(s) · e^(−pos(s)/|S|) / Σ |s|, where pos(s) is the sentence's index from 0 and |S| the
  number of sentences. This is Eq. 3 of arXiv 2311.09735 (§2.2.1) with three choices of ours: characters
  in place of words, so Chinese and Japanese, written without spaces, count on the same footing; positions
  from 0, so the first sentence counts in full, a start the paper does not state; and a sentence the brand
  and other sources support counts in full for the brand, where the paper shares a sentence's words equally
  among the sources citing it. A marker credits whole sentences, as the paper does; a segment credits only
  its own characters.

Per engine, `summary.engines[].supported_share` gives the answers measured, the median of each number over
them, and how many are above zero (`above_zero`); the report prints them in "Answer share your pages
support", next to the cited rate, with "not measured" and the reason for an engine with no measured answer.
There is no interval and no test. Medians are over the answers with positions only, so they describe answers
that cite, and the two readings (a marked sentence, a supported segment) and engines that write at different
lengths are not on one scale.

This is not `mention_share`. That counts the sentences that name the brand; this counts the text the brand's
pages support, whether or not it names the brand. An answer can name you in every sentence and rest on other
people's pages, or carry a paragraph from your docs without naming you. Like the absorption score of the study
above, it is a proxy built from what the provider attributes, not a check that the text came from the page
(arXiv 2604.25707 calls its own score a constructed proxy, §5.3, §10.1).

### Sources listed and used

Some APIs return the sources beside the answer and mark in the text the ones it uses. In a study of Chinese
answer engines that mark sources inline, 39.3% of the sources listed with an answer did not appear in its text
(10.5 listed and 6.9 in the text per answer; [arXiv 2607.15771](https://arxiv.org/abs/2607.15771), §2.4).
That study sampled the web and app interfaces of other engines (§1.1); it is context, not a benchmark for
these APIs.

Where the API gives both, each answer records `sources_listed` (every source returned) and `sources_used` (the
ones the text marks):

- **Perplexity**: listed are the `search_results` (or the older `citations` list); used are those its `[n]`
  marks name, the n-th listed source for `[n]`. Before, an answer with marks kept only the marked sources and
  dropped the rest; they are now kept in `sources_listed`. `citations`, and so `cited`, the rank and the
  headline, read exactly as before: the marked sources, or every listed source when the text marks none. An
  answer with no marks records neither list (what it used is unknown), nor does one whose results carry ids
  that disagree with their order.
- **Gemini with `"api": "generate_content"`**: listed are the `groundingChunks`; used are those a grounding
  support names. `cited` reads every chunk, as before.
- **OpenAI, Claude, OpenRouter and Gemini's Interactions API** return one list, the citations tied to the
  text, and no list beside it, so listed against used is **not measured**. OpenAI can also return the URLs its search consulted
  ([guide](https://developers.openai.com/api/docs/guides/tools-web-search), Sources) and Claude returns its
  search results; those are what the engine read, a different set from a list shown beside the answer, and
  `watch` neither requests nor records them.

Per engine, `summary.engines[].sources` gives the answers that recorded both lists, the sources listed and used
summed over them, `used_rate` (used over listed) and how many of those answers list, and use, a URL the brand
owns. The report prints them per answer in "Sources listed and used in the answer".

A run records what it measured in `recorded` (`spans`, `sources`). A run saved before these existed has no such
list, and its report says they were not recorded rather than that an engine gave none; its summary is computed
again when it is reported, and the file is not rewritten.

## Where the fields are

- Run files: [schema/watch.v1.json](../schema/watch.v1.json), `summary.headline`,
  `summary.branded`, `summary.brand_flags`, `cited_ci_clustered` and `n_questions` in every rate
  block, `with_citations` and `with_searches` on each row of `summary.engines`,
  `named_first`, `any_named` and `mention_share` on each row of `summary.engines` and
  `summary.share_of_voice`, `mention_order` and `mention_share` on each answer and on each of its
  `competitors`, `summary.by_question`, `brand_in_query`, `competitor_in_query` and `branded` on
  each question, `summary.searches` with its `modifiers` and `answers_searched_without_queries`,
  `questions_hash`, which two runs share when they asked the same questions, and, from section 9,
  `spans`, `supported_share`, `sources_listed` and `sources_used` on each answer, `supported_share`
  and `sources` on each row of `summary.engines`, and `recorded`.
- Diff output (`watch diff --format json`, or the MCP `diff` tool with `format: json`): the
  `diff` and `diff_row` definitions in the same schema.
- Pooled output (`watch report --since DAYS` or `--runs A..B` with `--format json`, or the MCP `report` tool
  with `since`): the `pooled` definition in the same schema.
- Commands and flags: [cli/README.md](../cli/README.md).
