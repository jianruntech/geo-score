# How reproducible is a single run?

The leaderboard says the benchmark is reproducible and invites you to re-run it. That
invitation is worth nothing without a number attached, so here is the number.

We ran the whole 266-site benchmark twice on the same day with the same code, and
compared every site. [`reproducibility.json`](reproducibility.json) has the raw
per-site pairs.

## The measured band

| | |
|---|---|
| Sites in both runs | **229** |
| Identical score | **103** (45.0%) |
| Within ±2 | **179** (78.2%) |
| Within ±5 | **219** (95.6%) |
| Moved more than 5 | **10** (4.4%) |
| Gate-cap state flipped | **5** |

**Read a single site's number as ±5, not as exact.** Read the median, the sector
medians and the distribution as stable: the median moved 57 → 57.5 and the mean
56.6 → 56.3 across the two runs.

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

| Site | Run 1 | Run 2 |
|---|---|---|
| booking.com | capped — content needs JavaScript | not capped |
| ecoflow.com | capped — serves crawlers an error | not capped |
| slack.com | not capped | capped — serves crawlers an error |
| together.ai | not capped | capped — blocks crawlers |
| xtransfer.com | not capped | capped — blocks crawlers |

Three of the large movers land exactly on 40 because that is the gate cap. During the
second run the log also caught live rate limiting — `ugreen.com` and `hiwonder.com`
returned 429 to every request, `insta360.com` returned 403 — which is the same
mechanism seen from the other side.

This is a property of the thing being measured, not a defect in the measurement. A site
whose WAF answers a crawler differently from one minute to the next *is* harder to cite,
and a tool that hid that variance behind a single confident number would be lying about
it. But it does mean a gate result is worth re-checking before anyone acts on it.

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

## Reproducing this

```
python3 benchmark/run.py                      # writes benchmark/results.json
python3 benchmark/run.py                      # again, to a copy
python3 -c "..."                              # compare — see reproducibility.json
```

`benchmark/results.json` publishes run 1. Run 2 is kept only inside
`reproducibility.json`; the public pages, the cards and the README are all synced to
run 1, so every published number comes from one internally consistent run rather than
a blend of two.
