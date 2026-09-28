# Weight sensitivity · AIV rubric v1.1

简体中文：[SENSITIVITY.zh-CN.md](SENSITIVITY.zh-CN.md)

How much does the leaderboard depend on the rubric's weights? This re-scores the 317 sites of the 2026-09-27 run (geo-score-cli/1.3.0) offline, from [results.json](results.json) and the [per-site reports](raw/), with [sensitivity.py](sensitivity.py). **Nothing here changes v1.1**: the weights stay as published, and any change ships as a new rubric version. This is input for v1.2.

First the script recomputes every published score from the per-check points with the rubric's arithmetic: each observable check adds its tier's points, over the points of the observable checks, plus the bonus (at most +6), capped at 100 and at 40 when a gate scores zero. 317 of 317 match, so every difference below comes from the weights alone. Every weighting keeps that arithmetic and the gate cap.

## Other weightings

Each row re-scores all 317 sites and compares them with the published scores: Spearman's rank correlation, how many sites change band, the median number of places a site moves, and how many of the top 20 stay in the top 20.

| Weighting | Spearman ρ | Band changes | Median rank move | Top-20 overlap |
|---|:-:|:-:|:-:|:-:|
| Equal: every scored check weighs 100/21 | 0.991 | 39 (12%) | 6 | 16 |
| Evidence basis, illustrative: research and vendor-doc checks keep their points, field-observation and convention checks get half | 0.996 | 22 (7%) | 4.5 | 19 |
| 300 random draws, every weight × U(0.5, 1.5): median (5th–95th percentile) | 0.995 (0.991–0.997) | 26 (18–45) | 4.5 (3–7) | 17 (15–19) |

Across the random draws, 198 sites change band in at least one draw and 1 in half of them or more.

## Leaving one check out

Each row treats one check as unobservable on every site, which is what the rubric does when a check cannot be observed. A gate left out still caps. Sorted by band changes.

| Check | Points | Observed on | Spearman ρ | Band changes | Median rank move | Top-20 overlap |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `p2.sourced-stats` | 7 | 317 | 0.994 | 48 | 5.5 | 18 |
| `p2.answer-passages` | 9 | 317 | 0.988 | 39 | 8 | 17 |
| `p1.llms-txt` | 5 | 317 | 0.993 | 34 | 6.5 | 19 |
| `p1.organization` | 6 | 317 | 0.993 | 32 | 6.5 | 17 |
| `g.reachable` | 5 | 317 | 0.997 | 31 | 4 | 17 |
| `p1.page-type` | 4 | 317 | 0.996 | 29 | 4.5 | 18 |
| `p2.question-intent` | 7 | 317 | 0.992 | 29 | 5 | 18 |
| `g.ssr` | 5 | 317 | 0.997 | 25 | 4.5 | 17 |
| `p2.named-author` | 6 | 317 | 0.995 | 25 | 5.5 | 18 |
| `p1.breadcrumb` | 3 | 251 | 0.998 | 23 | 3.5 | 17 |
| `p3.sameas` | 3 | 316 | 0.997 | 23 | 4 | 17 |
| `g.robots` | 5 | 317 | 0.997 | 22 | 5 | 17 |
| `p1.sitemap` | 4 | 317 | 0.996 | 22 | 5 | 17 |
| `p2.freshness` | 6 | 317 | 0.995 | 22 | 3 | 15 |
| `p4.answer-shape` | 4 | 317 | 0.997 | 18 | 4 | 17 |
| `p3.knowledge-graph` | 4 | 208 | 0.997 | 17 | 3 | 17 |
| `p3.video` | 3 | 317 | 0.998 | 14 | 2.5 | 19 |
| `p4.cn-engines` | 2 | 53 | 0.999 | 1 | 0.5 | 20 |

The CLI observed `p3.listings`, `p3.mentions`, `p4.question-coverage` on no site, so leaving them out changes nothing here.

## How each check spreads the field

Over the sites where each check was observed: the share at zero, the share at full points, the largest share any one tier holds, and the item-rest correlation, the check's tier share against the uncapped percentage of the other observed checks (no figure below 10 sites). The [calibration record](../rubric/calibration-v1.1.md#four-structural-problems-the-audits-exposed) found checks that scored the same on all five calibration sites and so carried no information; here a check is flagged ⚑ when one tier holds 90% or more of the sites.

| Check | Points | Observed on | At zero | At full | Largest tier | Item-rest r | Sites per tier (points: sites) |
|---|:-:|:-:|:-:|:-:|:-:|:-:|---|
| `g.robots` | 5 | 317 | 7.3% | 40.7% | 52.1% | 0.15 | 0: 23 · 3: 165 · 5: 129 |
| `g.reachable` | 5 | 317 | 5% | 63.4% | 63.4% | -0.02 | 0: 16 · 3: 100 · 5: 201 |
| `g.ssr` | 5 | 317 | 16.7% | 57.1% | 57.1% | 0.51 | 0: 53 · 3: 83 · 5: 181 |
| `p1.sitemap` | 4 | 317 | 23.7% | 50.8% | 50.8% | 0.42 | 0: 75 · 2: 81 · 4: 161 |
| `p1.llms-txt` | 5 | 317 | 56.8% | 34.4% | 56.8% | 0.49 | 0: 180 · 2: 1 · 4: 27 · 5: 109 |
| `p1.organization` | 6 | 317 | 47.9% | 22.4% | 47.9% | 0.59 | 0: 152 · 3: 67 · 5: 27 · 6: 71 |
| `p1.breadcrumb` | 3 | 251 | 67.3% | 20.7% | 67.3% | 0.46 | 0: 169 · 2: 30 · 3: 52 |
| `p1.page-type` | 4 | 317 | 59.6% | 20.8% | 59.6% | 0.59 | 0: 189 · 2: 62 · 4: 66 |
| `p2.answer-passages` | 9 | 317 | 28.7% | 27.4% | 28.7% | 0.55 | 0: 91 · 4: 77 · 7: 62 · 9: 87 |
| `p2.question-intent` | 7 | 317 | 21.5% | 42.9% | 42.9% | 0.68 | 0: 68 · 3: 60 · 5: 53 · 7: 136 |
| `p2.freshness` | 6 | 317 | 34.4% | 12.3% | 53.3% | 0.59 | 0: 109 · 3: 169 · 6: 39 |
| `p2.sourced-stats` | 7 | 317 | 3.2% | 68.5% | 68.5% | 0.41 | 0: 10 · 3: 58 · 5: 32 · 7: 217 |
| `p2.named-author` | 6 | 317 | 43.5% | 7.6% | 48.9% | 0.55 | 0: 138 · 3: 155 · 6: 24 |
| `p3.knowledge-graph` ⚑ | 4 | 208 | 9.1% | 90.9% | 90.9% | 0.09 | 0: 19 · 4: 189 |
| `p3.sameas` | 3 | 316 | 63.6% | 33.2% | 63.6% | 0.54 | 0: 201 · 2: 10 · 3: 105 |
| `p3.video` | 3 | 317 | 42.9% | 3.5% | 53.6% | 0.48 | 0: 136 · 2: 170 · 3: 11 |
| `p4.answer-shape` | 4 | 317 | 15.5% | 57.4% | 57.4% | 0.64 | 0: 49 · 2: 86 · 4: 182 |
| `p4.cn-engines` | 2 | 53 | 1.9% | 66% | 66% | 0.23 | 0: 1 · 1: 17 · 2: 35 |
| `b.llms-full` | 2 | 317 | 85.5% | 14.5% | 85.5% | — | 0: 271 · 2: 46 |
| `b.ai-txt` ⚑ | 2 | 317 | 99.1% | 0.9% | 99.1% | — | 0: 314 · 2: 3 |
| `b.geo-link` ⚑ | 1 | 317 | 94.6% | 5.4% | 94.6% | — | 0: 300 · 1: 17 |
| `b.speakable` ⚑ | 1 | 317 | 98.4% | 1.6% | 98.4% | — | 0: 312 · 1: 5 |

## Input for v1.2

- **Rank order is robust to the weights.** Spearman's ρ is at least 0.988 under every weighting above, and at least 0.991 in 95% of the random draws.
- **Bands are where the weights matter.** Equal weights change the band of 39 sites (12%), the evidence-basis weighting 22, and the random draws a median of 26 (18–45); 198 sites change band in at least one draw.
- **Most bands move when one of these is left out:** `p2.sourced-stats` (48), `p2.answer-passages` (39), `p1.llms-txt` (34).
- **One tier holds 90% or more of the sites** for `p3.knowledge-graph`, `b.ai-txt`, `b.geo-link`, `b.speakable`: on this field they carry little information.
- **Item-rest correlation below 0.2** for `g.robots`, `g.reachable`, `p3.knowledge-graph`: they rank sites differently from the rest of the rubric.
- No weight in v1.1 changes. A change to a weight or a tier ships as a new rubric version.
