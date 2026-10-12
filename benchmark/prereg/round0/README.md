# Round 0: categories and sampling frames

Round 0 of the [preregistered validation plan](../../PREREGISTRATION.md): English questions for a buyer in the
US. This file records what was fixed at each step, in the order the plan sets (section 4): first the categories,
each with its public list at a recorded revision and its candidate sites; then the questions; then the sampling
run. Nothing here has been scored.

## Step 1: categories and sampling frames

[categories.json](categories.json) holds 20 categories. [build_frames.py](build_frames.py) derives it, and
`build_frames.py --cache DIR --check` rebuilds it and compares.

For each category:

- **A one-sentence definition**, written for a buyer in the US.
- **Its public list:** an English Wikipedia list or comparison article, read at the revision id recorded (`frame.revid`;
  `frame.url` opens that revision). The rule that says which rows name the vendors (a table column, or each bullet's
  first link) is recorded with it (`frame.rule`), and so is every row it reads (`frame.rows`).
- **Each listed vendor's own website:** the official website (P856) of the Wikidata item the row links to, with that
  item's revision (`wd_lastrevid`). When the item has several, the English or multilingual one comes first, then an
  unqualified one, then Wikidata's preferred rank, then a generic top-level domain before a country code. A row is
  out, with the reason recorded, when its link has no article or no Wikidata item, when Wikidata records the vendor as
  dissolved (P576) or the product as discontinued (P2669), when no website is recorded, or when the website is a page
  on another site (a code host, `sites.google.com`, a project page). Two values were replaced by hand, each with its
  reason in the row (`website_override`): Rosetta Stone (Wikidata lists only its French site) and OC&C Strategy
  Consultants (only its French office's site).
- **One candidate per owner:** a candidate is the part of a host its owner holds, as `watch` reads it
  (`site_domain` in [cli/geo_watch.py](../../../cli/geo_watch.py): `amazon.com` for `aws.amazon.com`), with
  `napoli.it` added as a public suffix it does not know. Rows that resolve to the same owner are one candidate,
  scored at the first row's website host (`site`), and every domain listed for it counts as its own (`domains`).
- **The benchmark/sites.json sites that sell in it** (`sites_json_in`), matched by hand from the site lists of
  [sites.json](../../sites.json) (its `url` and `sector` only): a site enters when it sells the category's product to
  buyers in the US. A site that is a listed vendor's own site under another domain is merged with that vendor and
  scored at the sites.json site (runway.com for Runway's runwayml.com, bigcommerce.com for Commerce.com, remix.run for
  React Router, cursor.com for Anysphere, ebay.com for ebayinc.com, deepmind.google for Google's video models). Sites
  considered and left out are listed with the reason (`sites_json_out`), most often a China-market site or a
  different kind of product.
- **The size rule** (plan section 5.1): fewer than 6 candidates drops the category before sampling; above 15, 15 are
  drawn with `random.Random(seed).sample` over the candidate ids in sorted order, the seed being the first 16 hex digits
  of SHA-256 of `geo-score prereg round0 frame|<category id>` (`draw`). No category fell below 6.

| Category | Definition | Public list | Candidates | In the frame |
|---|---|---|:-:|:-:|
| `large-language-models` | Large language models that people and businesses in the US use through an app or an API, and the companies that develop them. | [List of large language models](https://en.wikipedia.org/w/index.php?oldid=1378988796) rev. 1378988796 (2026-10-07) | 49 | 15 |
| `ai-video-generators` | AI models and apps that generate video from text or images, offered to creators and businesses in the US. | [Text-to-video model](https://en.wikipedia.org/w/index.php?oldid=1378271382) rev. 1378271382 (2026-10-03) | 12 | 12 |
| `vector-databases` | Databases that store and search vector embeddings, offered to developers and businesses in the US. | [Vector database](https://en.wikipedia.org/w/index.php?oldid=1374243120) rev. 1374243120 (2026-09-10) | 25 | 15 |
| `cloud-infrastructure` | Public cloud infrastructure (virtual machines, storage and networking) that businesses in the US rent. | [Cloud-computing comparison](https://en.wikipedia.org/w/index.php?oldid=1365802661) rev. 1365802661 (2026-07-24) | 13 | 13 |
| `javascript-web-frameworks` | JavaScript and TypeScript frameworks for building websites and web applications, which developers in the US choose for a project. | [Comparison of JavaScript-based web frameworks](https://en.wikipedia.org/w/index.php?oldid=1374992173) rev. 1374992173 (2026-09-15) | 31 | 15 |
| `ecommerce-platforms` | Software and hosted platforms that merchants in the US use to run an online store. | [Comparison of shopping cart software](https://en.wikipedia.org/w/index.php?oldid=1378625961) rev. 1378625961 (2026-10-05) | 22 | 15 |
| `crm-software` | Customer relationship management software that companies in the US use to manage contacts, deals and customer communication. | [Comparison of CRM systems](https://en.wikipedia.org/w/index.php?oldid=1365891310) rev. 1365891310 (2026-07-25) | 27 | 15 |
| `web-analytics` | Software that measures visits to a website, used by site owners and marketers in the US. | [List of web analytics software](https://en.wikipedia.org/w/index.php?oldid=1361857790) rev. 1361857790 (2026-06-30) | 27 | 15 |
| `online-payment-providers` | Services that let businesses in the US accept payments online. | [List of online payment service providers](https://en.wikipedia.org/w/index.php?oldid=1367307700) rev. 1367307700 (2026-08-02) | 27 | 15 |
| `buy-now-pay-later` | Services that let shoppers in the US split a purchase into installments at checkout. | [Buy now, pay later](https://en.wikipedia.org/w/index.php?oldid=1376383699) rev. 1376383699 (2026-09-23) | 6 | 6 |
| `online-course-platforms` | Websites that offer online courses to learners in the US. | [List of MOOC providers](https://en.wikipedia.org/w/index.php?oldid=1363722387) rev. 1363722387 (2026-07-12) | 27 | 15 |
| `language-learning` | Apps, courses and self-study programs that learners in the US use to learn a foreign language. | [List of language self-study programs](https://en.wikipedia.org/w/index.php?oldid=1377422426) rev. 1377422426 (2026-09-29) | 36 | 15 |
| `container-shipping-lines` | Ocean carriers that move shipping containers for importers and exporters in the US. | [List of largest container shipping companies](https://en.wikipedia.org/w/index.php?oldid=1354275764) rev. 1354275764 (2026-05-15) | 17 | 15 |
| `management-consulting` | Firms that companies in the US hire for management consulting. | [List of management consulting firms](https://en.wikipedia.org/w/index.php?oldid=1379170443) rev. 1379170443 (2026-10-08) | 60 | 15 |
| `project-management-software` | Software that teams in the US use to plan, assign and track project work. | [Comparison of project management software](https://en.wikipedia.org/w/index.php?oldid=1364585119) rev. 1364585119 (2026-07-17) | 92 | 15 |
| `note-taking-apps` | Apps that people in the US use to write, organize and search their notes. | [Comparison of note-taking software](https://en.wikipedia.org/w/index.php?oldid=1367074056) rev. 1367074056 (2026-07-31) | 26 | 15 |
| `3d-printers` | 3D printers sold to hobbyists and businesses in the US. | [List of 3D printer manufacturers](https://en.wikipedia.org/w/index.php?oldid=1367768236) rev. 1367768236 (2026-08-05) | 33 | 15 |
| `us-airlines` | Airlines that fly passengers within and from the US. | [List of largest airlines in North America](https://en.wikipedia.org/w/index.php?oldid=1367374301) rev. 1367374301 (2026-08-02) | 10 | 10 |
| `accounting-software` | Accounting software that small and midsize businesses in the US use for bookkeeping, invoicing and financial reports. | [Comparison of accounting software](https://en.wikipedia.org/w/index.php?oldid=1374376033) rev. 1374376033 (2026-09-11) | 41 | 15 |
| `online-marketplaces` | Online marketplaces where shoppers in the US buy consumer goods from many sellers. | [List of online marketplaces](https://en.wikipedia.org/w/index.php?oldid=1373521726) rev. 1373521726 (2026-09-06) | 15 | 15 |

Three lists carry a column that says where a vendor operates or what it sells, and the rule reads it: online payment
providers keep the rows whose Location names the United States or North America or says global or worldwide; US
airlines keep the rows whose Country is the United States; online marketplaces keep the rows whose Industry names
products, fashion or clothing. No other row was screened for the US: a listed vendor that does not sell to buyers in
the US stays a candidate.

**Sectors.** A category's `sectors` are those of its benchmark/sites.json sites, so the 20 categories reach 14 of the
benchmark's 20 sectors (accounting software has no benchmark site). None was found for six: Healthcare (no English
Wikipedia list or comparison of telehealth or health services; "Online doctor" and "Telehealth" list no providers),
Media / Publishing (no list of publications a buyer would ask to have recommended), Manufacturing / Industrial
("Industrial robot" lists no makers; "List of television manufacturers" is mostly defunct brands and conglomerates that
make no televisions), Cross-border services (its sites sell to Chinese exporters, not to buyers in the US), and China
/ cloud and China / no-code, whose sites are China-market sites (the plan reserves a Chinese round). Two more
categories were dropped before any question was written: hotel groups (the table mixes groups that operate only in
China with no column to tell them apart) and online travel agencies (no list).

**What was read.** Only `url` and `sector` of benchmark/sites.json. `benchmark/results.json`, `benchmark/results.csv`
and `benchmark/raw/` were not opened. [benchmark/README.md](../../README.md) was read for its sector list and the
thin-sample rule; it is generated from results.json, and a text search of it for "thin" printed about 60 rows of its
leaderboard table, with those sites' v1.1 scores, before the categories were chosen. No score was used for anything
here. As the plan says (section 4), some candidates' v1.1 scores were public before the questions were written.

## Step 2: names, questions and watch configs (frozen)

[candidates.json](candidates.json) records, in the order the plan sets (section 5.2), each frame candidate's `watch`
entry, then the questions, then the candidates the questions name; [build_configs.py](build_configs.py) writes it and
the configs, and `--check` rebuilds and compares. The questions and configs are frozen from this commit: no question
is added, dropped or reworded, and no candidate is added.

**Names, written first.** Each candidate's entry has the name answers usually give it, its `domains` from step 1, no
URL prefix, and other names as `aliases` only where they are not ordinary English words. A candidate that is a large
company's site carries the company's name, with the listed product as an alias (Microsoft, alias Azure Cosmos DB).

**Ordinary English words (section 5.6).** A one-word name or alias is ordinary when its lowercase form, or its singular,
is a lowercase headword of Webster's Second International (`web2` as BSD and macOS ship it, SHA-256 `be41ad97…2bbab9`)
or a day or month name, and is among the 30,000 most frequent words of the Google Web Trillion Word Corpus counts
Peter Norvig published (`count_1w.txt`, SHA-256 `51df159f…059e690`). No alias passes that test. Eight names were
judged by hand, each with its reason in `ordinary_words.phrases`: phrases (Day One, As Seen On TV), places and
adjectives answers about US flights use (Alaska, Hawaiian, American), a word newer than web2 (Shortcut), a word
answers about language models use in its own sense (Perplexity) and an interjection (HMM). A flagged candidate has
no N, and S4 runs without it; its R and A, read from cited URLs, are unaffected.

**Questions.** Ten English questions per category for a buyer in the US, naming no product, vendor or site, with the
unbranded `intent_tier` labels, all four in every category: four `list`, two `problem`, two `persona` and two
`pricing` questions (JavaScript web frameworks: five `list` and one `pricing`). They are in `watch/<category>/queries.csv`.

**Candidates the questions name.** None: by watch's own matcher (`Entity.named_in`, which sets `brand_in_query` and
`competitor_in_query`: name, aliases and domains, whole words), no frozen question names any candidate, so every
frame candidate remains and every question will carry both flags false.

| Category | Candidates remaining | `brand` (first by name) | Ordinary-word names (no N) |
|---|:-:|---|---|
| `large-language-models` | 15 | 01.AI | Meta, Perplexity |
| `ai-video-generators` | 12 | Alibaba | Runway |
| `vector-databases` | 15 | Aerospike | Oracle |
| `cloud-infrastructure` | 13 | Alibaba Cloud | Oracle |
| `javascript-web-frameworks` | 15 | Angular | Angular, Prototype |
| `ecommerce-platforms` | 15 | BigCommerce | — |
| `crm-software` | 15 | ADempiere | Adobe |
| `web-analytics` | 15 | Adobe | Adobe, Bing, Plausible, Yahoo |
| `online-payment-providers` | 15 | Adyen | Apple, Square, Stripe |
| `buy-now-pay-later` | 6 | Affirm | Affirm, Apple, Zip |
| `online-course-platforms` | 15 | Alison | Alison |
| `language-learning` | 15 | Babbel | Drops, Tandem |
| `container-shipping-lines` | 15 | CMA CGM | Evergreen, HMM |
| `management-consulting` | 15 | AlixPartners | — |
| `project-management-software` | 15 | 24SevenOffice | Shortcut |
| `note-taking-apps` | 15 | Apple Notes | Day One, KeyNote |
| `3d-printers` | 15 | 3D makeR Technologies | — |
| `us-airlines` | 10 | Alaska | American, Alaska, Delta, Frontier, Hawaiian, Southwest, United |
| `accounting-software` | 15 | 24SevenOffice | Tally |
| `online-marketplaces` | 15 | AliExpress | As Seen On TV, Wish |

**Configs.** `watch/<category>/geo-score-watch.json`: the remaining candidates, the first by name as `brand` and the
rest as `competitors`; `runs: 8`, `country: US`, `max_calls: 160` (10 questions × 2 engines × 8), no budget. Two
engines, both searching the web on every call (see the plan's [amendments](../../PREREGISTRATION.md#amendments)):

| Engine id | Provider | Model | How it is reached |
|---|---|---|---|
| `openai` | openai (Responses API, `web_search` tool) | `gpt-5.6-luna` | an OpenAI-compatible endpoint whose address is given at run time: `collect.sh` puts `OPENAI_COMPAT_BASE_URL` in place of the placeholder `https://openai-compatible.invalid/v1/responses`; key in `OPENAI_COMPAT_API_KEY`; the model id is `OPENAI_COMPAT_MODEL`, recorded in the frozen sample; `timeout: 300` |
| `gemini` | gemini (`"api": "generate_content"`, Google Search tool) | `gemini-2.5-flash` | key in `GEMINI_API_KEY` |

geo-score 1.8.0's own defaults are `gpt-6-luna` and `gemini-3.8-flash`; round 0 pins the models above. Every config
passes `geo_score.py watch check` with no error or warning and validates against
[schema/watch-config.v1.json](../../../schema/watch-config.v1.json).

`benchmark/results.json`, `benchmark/results.csv` and `benchmark/raw/` had not been opened when these questions were
committed (see step 1 for what was read).

## Step 3: the analysis code and its synthetic test

[analysis.py](../analysis.py) is section 11 of the plan as code, committed before any answer is collected;
[test_analysis.py](../test_analysis.py) runs it on synthetic rounds and joins the gate (`bash scripts/check.sh` runs
every `benchmark/prereg/test_*.py`). Standard library only, as AGENTS.md requires.

- **Inputs:** `sample.json` (step 4's draw), `runs/wave<N>/<category>/*.json` (the `watch` run files) and
  `readiness/wave<N>/run{1,2}/<site>.json` (the CLI's reports).
- **Measures:** X is the mean of the wave's scored runs; R and N are read from `cited` and `mentioned` (the brand's,
  and `competitors.<name>` for the others), every engine and ask pooled; A is the mean, over the answers that cite the
  site and carry `spans`, of the share by characters a span with a URL the site owns supports, computed for every site
  with `watch`'s own `answer_support` and ownership test, and absent below 5 such answers.
- **Tests:** P1 (mean Kendall tau-b, within-category permutation of X, 10,000 permutations, observed one counted;
  95% percentile bootstrap over categories, 10,000 draws), D, S1 to S4 with Holm's correction (S3 leaves the family
  when fewer than 8 categories have 3 sites with an A), the described quantities, L1 for wave 1, and the wording table.
  The default seed is 20261012; every seed is written into the output.
- **Power:** `analysis.py power --round benchmark/prereg/round0` simulates the frozen design (its sampled sites'
  sampling-run scores) and reports the smallest mean T detected with 80% power at alpha 0.05. Its figure is added to
  the plan by amendment after the draw and before the first answer (section 11).

The synthetic test plants an association (each site's citation probability rises with its readiness rank in its
category) in 14 categories of 5 sites and checks that P1, S1, S2 and S4 call it (T 0.99, p 0.0005 with 2,000
permutations), and runs the same design with the probability unrelated to readiness and checks that nothing is
called (T −0.06, p 0.63). It also checks tau-b with ties, Holm against `watch`'s, the permutation p, the rubric's
strata, that an engine whose answers carry no citation leaves the wave, that a stopped engine is read from its
rerun, that an ordinary-word site has no N, that X survives one failed run, that S1 drops a gate-capped site, that A
for a competitor is `watch`'s rule and is never 0 when unmeasured, that S3 leaves the family without spans, and that
the power simulation rises with the effect.

## Step 4: the VM scripts

In [vm/](vm/), for a fresh Ubuntu VM in a US region (`sudo apt-get install -y git python3`); none of them has been
run. Nothing in round 0 is scored or asked from any other machine.

| Script | What it does | Writes (in the clone it makes) |
|---|---|---|
| [score_candidates.sh](vm/score_candidates.sh) `TAG` | The sampling run (plan section 5.2): clones the repository at `TAG`, whose CLI is the frozen one, and scores every remaining candidate's site once, one at a time, 30 s apart, `--json-out` per site; a site that fails is tried once on its www host, as benchmark/run.py does. Resumable | `sampling/reports/`, `sampling/errors/`, `sampling/log.tsv`, `sampling/cli.txt` |
| [draw.py](vm/draw.py) | Sections 5.2 to 5.4 and 6: drops candidates the CLI could not score or scored on fewer than 4 pages, bands the rest (below 51, 51 to 65, 66 and above), draws up to 2 per stratum per category with recorded seeds, drops categories left with fewer than 4 sites or one stratum, stops below 12 categories (exit 3), cuts to 18 by a recorded draw above 18, records the current Tranco list id and each site's rank, and writes the frozen sample and its configs (the OpenAI-compatible model set from `OPENAI_COMPAT_MODEL`) | `sample.json`, `sample/<category>/` |
| [collect.sh](vm/collect.sh) `DATA_TAG DAY` | Section 7: one day's 6 categories (of the schedule in sample.json), with the frozen CLI and configs, the endpoint put in place of the placeholder from `OPENAI_COMPAT_BASE_URL`; a preflight question on day 1; an engine that stopped is run once more; Gemini's answers per day are capped at 500. `DRY_RUN=1` prints the plans and calls nothing | `runs/wave<N>/<category>/`, `collection/wave<N>/log.tsv` |
| [watch_run.py](vm/watch_run.py) | Used by collect.sh: the frozen CLI's `watch`, with HTTP 429 and 5xx answers retried after 15, 30, 60, 120 and 120 s (a daily-quota 429 is not) | — |
| [readiness_runs.sh](vm/readiness_runs.sh) `DATA_TAG RUN` | Section 6: every sampled site scored once more with the frozen CLI at the URL its sampling run scored; run 2 refuses the UTC day run 1 started and warns past 6 days | `readiness/wave<N>/run<RUN>/` |

Tested here without touching a candidate site or an API: the retry wrapper against a fake transport; draw.py on
synthetic sampling reports and a fake Tranco file (20 categories cut to 18, configs passing `watch check`); and
collect.sh against a local repository with test tags, both `DRY_RUN=1` and a full day against a local
OpenAI-compatible fake (preflight, 6 runs, harvest, a stopped engine run once more, the analysis reading the files).

### On the VM, in order

1. **Sampling run**, after the release `T1` that contains steps 1 to 4 (its CLI becomes the frozen one; about 270
   sites, 5 to 7 hours):
   ```bash
   T1=vX.Y.Z
   curl -fsSLO "https://raw.githubusercontent.com/jianruntech/geo-score/$T1/benchmark/prereg/round0/vm/score_candidates.sh"
   nohup bash score_candidates.sh "$T1" > sampling.out 2>&1 &
   ```
2. **The draw**, when it has finished (needs the model id the endpoint serves):
   ```bash
   cd ~/prereg-round0/geo-score-$T1
   OPENAI_COMPAT_MODEL=gpt-5.6-luna python3 benchmark/prereg/round0/vm/draw.py
   tar czf ~/round0-sample.tgz benchmark/prereg/round0/sampling benchmark/prereg/round0/sample.json benchmark/prereg/round0/sample
   ```
3. **Off the VM:** commit the tarball's contents; run `python3 benchmark/prereg/analysis.py power --round
   benchmark/prereg/round0` and add its figure to the plan by amendment (section 11), with the analysis code's
   commit; release `T2`. Wave 0 starts only after `T2` is published.
4. **Wave 0**, three consecutive days, from the same VM (keys in the environment; nothing prints them):
   ```bash
   export OPENAI_COMPAT_BASE_URL=... OPENAI_COMPAT_API_KEY=... OPENAI_COMPAT_MODEL=gpt-5.6-luna GEMINI_API_KEY=...
   T2=vX.Y.Z
   for f in collect.sh readiness_runs.sh; do curl -fsSLO "https://raw.githubusercontent.com/jianruntech/geo-score/$T2/benchmark/prereg/round0/vm/$f"; done
   DRY_RUN=1 bash collect.sh "$T2" 1                  # the plans, no call
   nohup bash readiness_runs.sh "$T2" 1 > r1.out 2>&1 &  # day 1; start it first, it makes the clones
   nohup bash collect.sh "$T2" 1 > day1.out 2>&1 &       # day 1, about 6 hours
   nohup bash collect.sh "$T2" 2 > day2.out 2>&1 &       # day 2
   nohup bash readiness_runs.sh "$T2" 2 > r2.out 2>&1 &  # day 2 to 6, a different UTC day from run 1
   nohup bash collect.sh "$T2" 3 > day3.out 2>&1 &       # day 3
   ```
5. **Off the VM:** copy back `runs/`, `collection/` and `readiness/`, commit them, and run
   `python3 benchmark/prereg/analysis.py analyze --round benchmark/prereg/round0 --wave 0 --power-t <figure> --out
   benchmark/prereg/round0/results-wave0.json`.

## Step 5: the amendment

What round 0 does differently from the plan's text is in the plan's dated amendment of 2026-10-12
([PREREGISTRATION.md](../../PREREGISTRATION.md#amendments), [中文](../../PREREGISTRATION.zh-CN.md#修订)): two engines,
the OpenAI answers through an OpenAI-compatible third-party endpoint, Gemini without a location, at most 18
categories, and per-engine retries and reruns; with how round 0 reads sections 5 and 6, what was read before the
questions, and the analysis code's commits. The power figure follows in a further amendment once the sample is drawn.
