# The state of AI visibility

Every site below scored with the same open rubric, the same public tool and the same
eight-page sample. No private data, no vendor dashboards — [re-run it yourself](run.py).

**38 sites · median 61.5 · mean 60.9 · upper quartile 70.8 · range 19–86** · rubric v1.1 · measured 2026-09-08

## What the spread shows

**Half the field sits between 55.0 and 70.8.** The rubric is not grading on a curve — these
are the scores that fall out of it, and they are consistent with the public benchmarks
it was [calibrated against](../rubric/calibration-v1.1.md).

**Sites built for the Chinese market score 21 points lower** — median 43.5 against 64.5
for everyone else. The gap is not content quality. It is `llms.txt`, `Organization`
schema, visible dates and bylines — conventions that spread through the English web
first and have not yet crossed over.

**The same few things are missing almost everywhere.** Counting only each site's three
largest gaps:

| Missing | Sites | What it costs |
|---|:-:|:-:|
| `p2.freshness` | 24 of 38 | 6 pts |
| `p2.answer-passages` | 20 of 38 | 9 pts |
| `p1.organization` | 16 of 38 | 6 pts |
| `p2.named-author` | 15 of 38 | 6 pts |
| `p1.page-type` | 10 of 38 | 4 pts |
| `p1.llms-txt` | 7 of 38 | 5 pts |

None of the top three is expensive. A date in a page template, an opening paragraph
that stands on its own, and one JSON-LD block are between them worth more than any
single pillar on this list.

## By sector

| Sector | Sites | Median |
|---|:-:|:-:|
| Cloud & DevOps | 5 | **76** |
| Developer tools | 8 | **72.5** |
| Ecommerce | 3 | **69** |
| Marketing / CRM | 4 | **63.5** |
| SaaS / Productivity | 6 | **60.0** |
| Payments / Fintech | 3 | **57** |
| China / enterprise | 2 | **55.0** |
| China / no-code | 3 | **44** |
| China / cloud | 1 | **43** |
| AI | 3 | **40** |

## Every site

| # | Site | Score | Band | Sector | Biggest gaps |
|:-:|---|:-:|---|---|---|
| 1 | twilio.com | **86** | Leading | Cloud & DevOps | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 2 | supabase.com | **83** | Leading | Developer tools | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 3 | fly.io | **81** | Solid | Developer tools | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 4 | nextjs.org | **80** | Solid | Developer tools | `p3.video` · `p2.named-author` · `p1.breadcrumb` |
| 5 | cloudflare.com | **80** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.video` |
| 6 | railway.com | **78** | Solid | Developer tools | `p2.named-author` · `p2.freshness` · `p4.answer-shape` |
| 7 | sentry.io | **76** | Solid | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p1.page-type` |
| 8 | asana.com | **72** | Solid | SaaS / Productivity | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 9 | stripe.com | **71** | Solid | Payments / Fintech | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 10 | hubspot.com | **71** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 11 | squarespace.com | **70** | Solid | Ecommerce | `p2.answer-passages` · `p3.knowledge-graph` · `p3.video` |
| 12 | linear.app | **69** | Solid | SaaS / Productivity | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 13 | semrush.com | **69** | Solid | Marketing / CRM | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 14 | shopify.com | **69** | Solid | Ecommerce | `p2.answer-passages` · `p3.knowledge-graph` · `p1.page-type` |
| 15 | vuejs.org | **67** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.video` |
| 16 | kingdee.com | **67** | Solid | China / enterprise | `p2.named-author` · `p3.knowledge-graph` · `p2.question-intent` |
| 17 | svelte.dev | **66** | Solid | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 18 | bigcommerce.com | **63** | Growing | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p3.knowledge-graph` |
| 19 | datadoghq.com | **63** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p1.page-type` |
| 20 | notion.com | **60** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 21 | slack.com | **60** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 22 | mailchimp.com | **58** | Growing | Marketing / CRM | `p2.freshness` · `p1.organization` · `p2.sourced-stats` |
| 23 | ahrefs.com | **58** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 24 | wise.com | **57** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 25 | astro.build | **57** | Growing | Developer tools | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 26 | mingdao.com | **57** | Growing | China / no-code | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 27 | plaid.com | **55** | Growing | Payments / Fintech | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 28 | anthropic.com | **55** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 29 | digitalocean.com | **55** | Growing | Cloud & DevOps | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 30 | remix.run | **53** | Growing | Developer tools | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 31 | jiandaoyun.com | **44** | Early | China / no-code | `p2.named-author` · `p2.answer-passages` · `p1.llms-txt` |
| 32 | yonyou.com | **43** | Early | China / enterprise | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 33 | aliyun.com | **43** | Early | China / cloud | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 34 | huggingface.co | **40** | Early | AI | `p2.named-author` · `p1.organization` · `p2.answer-passages` |
| 35 | cohere.com | **40** | Early | AI | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 36 | figma.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 37 | airtable.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 38 | feishu.cn | **19** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |

### Not scored

- **openai.com** — could not fetch https://www.openai.com — all requests returned 308
- **perplexity.ai** — could not fetch https://www.perplexity.ai — all requests returned 403

A 403 to every client, a browser user-agent included, is bot protection working at the
TLS layer rather than on the user-agent string. It means a static fetch cannot observe
the site — not that the site blocks AI crawlers, which is a separate question this tool
cannot answer from outside.

## What this is not

These are **readiness** scores from a static fetch: whether an answer engine *can*
find, parse and cite the site. They do not measure whether one *does* — that depends
on competition and query intent, and no site-side audit can observe it.

Four checks worth 12 points need off-site search or human judgement and are left out
of the denominator, so these run a little lower than a full audit. The
[five reference audits](../examples/audits/v1.1/) score all 21 checks by hand.

Sites change. Every number here carries the date it was measured, and re-running
gives slightly different results — which is the point of publishing the tool alongside
the table.

