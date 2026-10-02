# Weight sensitivity · AIV rubric v1.1

简体中文：[SENSITIVITY.zh-CN.md](SENSITIVITY.zh-CN.md)

How much does the leaderboard depend on the rubric's weights? This re-scores the 324 sites of the 2026-10-02 run (geo-score-cli/1.5.0) offline, from [results.json](results.json) and the [per-site reports](raw/), with [sensitivity.py](sensitivity.py). **Nothing here changes v1.1**: the weights stay as published, and any change ships as a new rubric version. This is input for v1.2.

First the script recomputes every published score from the per-check points with the rubric's arithmetic: each observable check adds its tier's points, over the points of the observable checks, plus the bonus (at most +6), capped at 100 and at 40 when a gate scores zero. 324 of 324 match, so every difference below comes from the weights alone. Every weighting keeps that arithmetic and the gate cap.

## Other weightings

Each row re-scores all 324 sites and compares them with the published scores: Spearman's rank correlation, how many sites change band, the median number of places a site moves, and how many of the top 20 stay in the top 20.

| Weighting | Spearman ρ | Band changes | Median rank move | Top-20 overlap |
|---|:-:|:-:|:-:|:-:|
| Equal: every scored check weighs 100/21 | 0.992 | 35 (11%) | 5.5 | 17 |
| Evidence basis, illustrative: research and vendor-doc checks keep their points, field-observation and convention checks get half | 0.997 | 26 (8%) | 3.5 | 20 |
| 300 random draws, every weight × U(0.5, 1.5): median (5th–95th percentile) | 0.995 (0.992–0.997) | 32 (20–52) | 4.5 (3.5–6.8) | 18 (17–20) |

Across the random draws, 222 sites change band in at least one draw and 3 in half of them or more.

## Leaving one check out

Each row treats one check as unobservable on every site, which is what the rubric does when a check cannot be observed. A gate left out still caps. Sorted by band changes.

| Check | Points | Observed on | Spearman ρ | Band changes | Median rank move | Top-20 overlap |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `g.reachable` | 5 | 320 | 0.998 | 44 | 2.5 | 20 |
| `p2.answer-passages` | 9 | 324 | 0.988 | 43 | 9 | 18 |
| `p2.sourced-stats` | 7 | 322 | 0.996 | 38 | 4.5 | 19 |
| `p1.llms-txt` | 5 | 315 | 0.993 | 36 | 4.5 | 19 |
| `g.ssr` | 5 | 324 | 0.997 | 35 | 4 | 18 |
| `p2.question-intent` | 7 | 321 | 0.995 | 35 | 4.5 | 20 |
| `p3.knowledge-graph` | 4 | 248 | 0.998 | 31 | 2.5 | 19 |
| `p1.organization` | 6 | 317 | 0.994 | 30 | 5 | 19 |
| `p1.page-type` | 4 | 324 | 0.997 | 28 | 3.5 | 17 |
| `p2.named-author` | 6 | 321 | 0.995 | 27 | 3.5 | 18 |
| `g.robots` | 5 | 321 | 0.997 | 25 | 5 | 18 |
| `p1.sitemap` | 4 | 324 | 0.997 | 25 | 5.5 | 20 |
| `p2.freshness` | 6 | 324 | 0.996 | 25 | 4.5 | 19 |
| `p4.answer-shape` | 4 | 324 | 0.998 | 25 | 3 | 20 |
| `p3.sameas` | 3 | 316 | 0.998 | 23 | 3.5 | 18 |
| `p1.breadcrumb` | 3 | 262 | 0.998 | 17 | 1.5 | 18 |
| `p3.video` | 3 | 324 | 0.999 | 17 | 2.5 | 18 |
| `p4.cn-engines` | 2 | 57 | 1.000 | 5 | 0.5 | 20 |

The CLI observed `p3.listings`, `p3.mentions`, `p4.question-coverage` on no site, so leaving them out changes nothing here.

## How each check spreads the field

Over the sites where each check was observed: the share at zero, the share at full points, the largest share any one tier holds, and the item-rest correlation, the check's tier share against the uncapped percentage of the other observed checks (no figure below 10 sites). The [calibration record](../rubric/calibration-v1.1.md#four-structural-problems-the-audits-exposed) found checks that scored the same on all five calibration sites and so carried no information; here a check is flagged ⚑ when one tier holds 90% or more of the sites.

| Check | Points | Observed on | At zero | At full | Largest tier | Item-rest r | Sites per tier (points: sites) |
|---|:-:|:-:|:-:|:-:|:-:|:-:|---|
| `g.robots` | 5 | 321 | 6.2% | 43.9% | 49.8% | 0.14 | 0: 20 · 3: 160 · 5: 141 |
| `g.reachable` | 5 | 320 | 5% | 80.6% | 80.6% | 0.13 | 0: 16 · 3: 46 · 5: 258 |
| `g.ssr` | 5 | 324 | 14.2% | 61.1% | 61.1% | 0.47 | 0: 46 · 3: 80 · 5: 198 |
| `p1.sitemap` | 4 | 324 | 21.9% | 51.9% | 51.9% | 0.39 | 0: 71 · 2: 85 · 4: 168 |
| `p1.llms-txt` | 5 | 315 | 56.5% | 34.9% | 56.5% | 0.51 | 0: 178 · 2: 1 · 4: 26 · 5: 110 |
| `p1.organization` | 6 | 317 | 47.3% | 23.7% | 47.3% | 0.61 | 0: 150 · 3: 66 · 5: 26 · 6: 75 |
| `p1.breadcrumb` | 3 | 262 | 66.8% | 22.1% | 66.8% | 0.48 | 0: 175 · 2: 29 · 3: 58 |
| `p1.page-type` | 4 | 324 | 57.1% | 22.8% | 57.1% | 0.63 | 0: 185 · 2: 65 · 4: 74 |
| `p2.answer-passages` | 9 | 324 | 25.9% | 32.1% | 32.1% | 0.57 | 0: 84 · 4: 69 · 7: 67 · 9: 104 |
| `p2.question-intent` | 7 | 321 | 19.3% | 43.3% | 43.3% | 0.67 | 0: 62 · 3: 53 · 5: 67 · 7: 139 |
| `p2.freshness` | 6 | 324 | 33.3% | 13.3% | 53.4% | 0.58 | 0: 108 · 3: 173 · 6: 43 |
| `p2.sourced-stats` | 7 | 322 | 24.8% | 0.6% | 69.9% | 0.15 | 0: 80 · 3: 225 · 5: 15 · 7: 2 |
| `p2.named-author` | 6 | 321 | 42.4% | 9.7% | 48% | 0.55 | 0: 136 · 3: 154 · 6: 31 |
| `p3.knowledge-graph` ⚑ | 4 | 248 | 7.3% | 92.7% | 92.7% | 0.06 | 0: 18 · 4: 230 |
| `p3.sameas` | 3 | 316 | 62% | 35.8% | 62% | 0.55 | 0: 196 · 2: 7 · 3: 113 |
| `p3.video` | 3 | 324 | 42.3% | 3.7% | 54% | 0.50 | 0: 137 · 2: 175 · 3: 12 |
| `p4.answer-shape` | 4 | 324 | 14.5% | 60.5% | 60.5% | 0.61 | 0: 47 · 2: 81 · 4: 196 |
| `p4.cn-engines` | 2 | 57 | 3.5% | 61.4% | 61.4% | 0.28 | 0: 2 · 1: 20 · 2: 35 |
| `b.llms-full` | 2 | 324 | 84.9% | 15.1% | 84.9% | — | 0: 275 · 2: 49 |
| `b.ai-txt` ⚑ | 2 | 324 | 99.1% | 0.9% | 99.1% | — | 0: 321 · 2: 3 |
| `b.geo-link` ⚑ | 1 | 324 | 94.8% | 5.2% | 94.8% | — | 0: 307 · 1: 17 |
| `b.speakable` ⚑ | 1 | 324 | 98.1% | 1.9% | 98.1% | — | 0: 318 · 1: 6 |

## Input for v1.2

- **Rank order is robust to the weights.** Spearman's ρ is at least 0.988 under every weighting above, and at least 0.992 in 95% of the random draws.
- **Bands are where the weights matter.** Equal weights change the band of 35 sites (11%), the evidence-basis weighting 26, and the random draws a median of 32 (20–52); 222 sites change band in at least one draw.
- **Most bands move when one of these is left out:** `g.reachable` (44), `p2.answer-passages` (43), `p2.sourced-stats` (38).
- **One tier holds 90% or more of the sites** for `p3.knowledge-graph`, `b.ai-txt`, `b.geo-link`, `b.speakable`: on this field they carry little information.
- **Item-rest correlation below 0.2** for `g.robots`, `g.reachable`, `p2.sourced-stats`, `p3.knowledge-graph`: they rank sites differently from the rest of the rubric.
- No weight in v1.1 changes. A change to a weight or a tier ships as a new rubric version.
