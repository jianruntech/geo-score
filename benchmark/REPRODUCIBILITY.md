# How reproducible is a single run?

The leaderboard says the benchmark is reproducible and invites you to re-run it. That
invitation is worth nothing without a number attached, so here is the number.

We ran the whole benchmark twice on the same day with the same code, and compared every
site. [`reproducibility.json`](reproducibility.json) has the raw per-site pairs, and
[`retest.py`](retest.py) derives every table on this page from it.

**The band below was measured on 2026-09-09 on 229 sites with a 1.1.x build, before the
1.1.2 variance fixes** (sameAs, knowledge-graph lookups and sampling retries; see the
[changelog](../CHANGELOG.md)). It has not been re-measured with the current tool, and the
list has grown since, so the counts in the table are that measurement's counts, not today's
totals. It still describes the method's main sources of variance, but the size of the band
for the current tool is an open measurement: [A retest with the current tool](#a-retest-with-the-current-tool)
records it once it has been run.

## The measured band

<!-- retest:legacy-band -->

| | |
|---|---|
| Measured | 2026-09-09, a 1.1.x build, before the 1.1.2 variance fixes |
| Sites in both runs | **229** |
| Identical score | **103** (45.0%) |
| Within ±2 | **179** (78.2%) |
| Within ±5 | **219** (95.6%) |
| Moved more than 5 | **10** (4.4%) |
| Band changed | **18** (7.9%) |
| Gate-cap state flipped | **5** |
| ICC(A,1) | **0.974** |
| SEM | **3.09** points |

Medians 57 → 57.5, means 56.6 → 56.3 across the two runs.

<!-- /retest:legacy-band -->

**Read a single site's number as ±5, not as exact.** Read the median, the sector
medians and the distribution as stable.

## A retest with the current tool

<!-- retest:study -->

No retest with the current tool is recorded yet. The runs cost nothing but time and are the maintainer's to make (see [Reproducing this](#reproducing-this)); until then the only measured band is the one above, and it describes a 1.1.x build.

<!-- /retest:study -->

## Why it moves

**Sampling.** Every content check states a count out of 8 sampled pages. Which 8 pages
get sampled comes from the sitemap and the homepage's own links, and that set is not
identical from one run to the next — a page 404s, a sitemap reorders, a link rotates.
Given the *same* eight pages two scorers agree exactly, which is what the rubric's
"count out of 8" rule is for. Across runs the sample itself differs.

A control, same code and same site, three consecutive runs: `stripe.com` scored
**69, 71, 71**. The spread is inherent to the method, not a consequence of any change
to the tool.

**Bot protection.** The gate checks ask what a site does to a retrieval user-agent
right now, and some sites answer differently minute to minute. Five sites flipped
between the two runs:

<!-- retest:legacy-flips -->

| Site | Run 1 | Run 2 |
|---|---|---|
| booking.com | capped — content needs JavaScript | not capped |
| ecoflow.com | capped — serves crawlers an error | not capped |
| slack.com | not capped | capped — serves crawlers an error |
| together.ai | not capped | capped — blocks crawlers |
| xtransfer.com | not capped | capped — blocks crawlers |

<!-- /retest:legacy-flips -->

Three of the large movers land exactly on 40 because that is the gate cap. During the
second run the log also caught live rate limiting — `ugreen.com` and `hiwonder.com`
returned 429 to every request, `insta360.com` returned 403 — which is the same
mechanism seen from the other side.

This is a property of the thing being measured, not a defect in the measurement. A site
whose WAF answers a crawler differently from one minute to the next *is* harder to cite,
and a tool that hid that variance behind a single confident number would be lying about
it. But it does mean a gate result is worth re-checking before anyone acts on it.

## Two things that were not reproducible at all, and are now fixed

The band above was measured after these were found. Both are worth stating plainly,
because both meant the number depended on something other than the site.

**308 redirects were not followed, so the score depended on the Python version.**
`urllib` below Python 3.11 raises on 307/308 instead of following them, and its
`redirect_request` rejects 308 outright — so aliasing the error handler is not enough on
its own. A site whose www-to-apex hop is a 308 read as unreachable on Python 3.8–3.10
and scored normally on 3.11+. The CLI claims 3.8+, so the same site could come back with
a score or with "could not fetch" depending on who ran it. openai.com, runwayml.com and
neon.tech were all absent from the benchmark for this reason. Fixed by overriding
`redirect_request`; there is a test for it, and it asserts the method survives the hop.

**A site can hand back a different origin than the one asked for.** Two kinds:

- *Renames.* `neon.tech` now answers as `neon.com`, `runwayml.com` as `runway.com`,
  `vitejs.dev` as `vite.dev`. Following the hop and keeping the old label would publish
  a score for one site under another site's name. Seven entries were relabelled.
- *Locale swaps.* The tool sends `Accept-Language: en,zh;q=0.8` — English first — and
  some sites use that to serve their international edition instead: `aliyun.com` can
  answer as `alibabacloud.com`, `xiaomi.com` as `mi.com`, `shein.com` as `us.shein.com`.
  This matters for the China-market comparison, because it can mean an English edition
  is standing in for the site the label names. It is also intermittent: the same host
  answered as `www.aliyun.com` on a later request.

Because the second kind cannot be settled by choosing a better header, it is recorded
instead of hidden. Every result carries `resolved_to` when the landing apex differs from
the label, and the human output prints *"redirected to X — that is what was scored"*.
Read a China-sector score with that field in view.

## What this means for how the numbers are used

- **A site's own score**: treat as ±5. Re-run before drawing a conclusion from a small
  gap between two sites.
- **A gate failure**: re-check. It is the least stable part of the score and the most
  consequential, since it caps the result.
- **Medians and distributions**: stable across runs. The "about a quarter cannot be
  cited at all" finding held at 25/25/25/24% across four samples of growing size, and
  the capped count moved only 54 → 56 between these two runs.
- **`--fail-under` in CI**: leave headroom. A threshold set 1 point below today's score
  will fail on noise. Five points of margin is the smallest that makes sense.
- **Before and after a change to your own site**: pin the sample. Save the first run with
  `--json-out before.json`, then re-score with `--urls-from before.json`. The second run
  reads exactly the same pages, so a difference comes from the site, not from the sample.
  (A page that has since gone away drops out, and the report lists what was read.)

## Reproducing this

```
python3 benchmark/run.py --out ~/geo-runs/a --vantage "LABEL"         # run A
python3 benchmark/run.py --out ~/geo-runs/b --vantage "LABEL"         # run B: same day, same place
python3 benchmark/run.py --out ~/geo-runs/c --vantage "LABEL" \
    --urls-from-dir ~/geo-runs/a/raw                                   # run C: A's pages
python3 benchmark/retest.py ~/geo-runs/a ~/geo-runs/b ~/geo-runs/c    # reproducibility.json + the tables above
```

A run with `--out` writes its `results.json` and `raw/` there and leaves the published files
alone.

Each pair isolates something. A against B is the whole run-to-run variance a reader of the
leaderboard sees. A against C reads the same pages, so what is left is the sites and the
network rather than the sample. A fourth run from a second place (a different `--vantage`)
shows what the vantage adds: a network that cannot reach Wikidata, LinkedIn or a WAF-fronted
host scores those checks differently. `--vantage` is a label the operator declares; nothing
looks an address up. Every run also records its tool version and Python version.

`python3 benchmark/retest.py` with no arguments re-derives every figure from the records in
`reproducibility.json`, and `.github/validate.py` fails when this page or that file differs
from what it gives.

`benchmark/results.json` publishes one run. The others are kept only inside
`reproducibility.json`; the public pages, the cards and the README are all synced to the
published run, so every published number comes from one internally consistent run rather
than a blend of two.
