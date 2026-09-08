# The state of AI visibility

Every site below scored with the same open rubric, the same public tool and the same
eight-page sample. No private data, no vendor dashboards — [re-run it yourself](run.py).

**105 sites · median 59 · mean 58.1 · upper quartile 72.0 · range 16–92** · rubric v1.1 · measured 2026-09-09

## What the spread shows

**Half the field sits between 40.0 and 72.0.** The rubric is not grading on a curve — these
are the scores that fall out of it, and they are consistent with the public benchmarks
it was [calibrated against](../rubric/calibration-v1.1.md).

**Sites built for the Chinese market score 22 points lower** — median 44 against 66.0
for everyone else. The gap is not content quality. It is `llms.txt`, `Organization`
schema, visible dates and bylines — conventions that spread through the English web
first and have not yet crossed over.

**The same few things are missing almost everywhere.** Counting only each site's three
largest gaps:

| Missing | Sites | What it costs |
|---|:-:|:-:|
| `p2.freshness` | 58 of 105 | 6 pts |
| `p2.named-author` | 55 of 105 | 6 pts |
| `p2.answer-passages` | 52 of 105 | 9 pts |
| `p1.organization` | 34 of 105 | 6 pts |
| `p2.question-intent` | 26 of 105 | 7 pts |
| `p1.llms-txt` | 20 of 105 | 5 pts |

None of the top three is expensive. A date in a page template, an opening paragraph
that stands on its own, and one JSON-LD block are between them worth more than any
single pillar on this list.

## By sector

| Sector | Sites | Median |
|---|:-:|:-:|
| Cloud & DevOps | 10 | **80.5** |
| Marketing / CRM | 8 | **70.0** |
| Ecommerce | 6 | **69.5** |
| Developer tools | 16 | **69.0** |
| Payments / Fintech | 7 | **65** |
| SaaS / Productivity | 12 | **64.5** |
| AI | 10 | **58.5** |
| China / enterprise | 6 | **53.5** |
| China / AI | 4 | **48.0** |
| China / no-code | 5 | **44** |
| Healthcare | 2 | **40.0** |
| Media / Publishing | 6 | **40.0** |
| China / consumer | 5 | **38** |
| Travel | 2 | **36.5** |
| Education | 3 | **28** |
| China / cloud | 3 | **22** |

## Every site

| # | Site | Score | Band | Sector | Biggest gaps |
|:-:|---|:-:|---|---|---|
| 1 | pulumi.com | **92** | Leading | Cloud & DevOps | `p2.freshness` · `g.ssr` · `g.robots` |
| 2 | zapier.com | **92** | Leading | SaaS / Productivity | `p2.freshness` · `p2.named-author` · `p3.sameas` |
| 3 | netlify.com | **87** | Leading | Cloud & DevOps | `p2.named-author` · `p3.knowledge-graph` · `p2.answer-passages` |
| 4 | prisma.io | **87** | Leading | Developer tools | `p2.question-intent` · `p3.video` · `p2.freshness` |
| 5 | clickup.com | **87** | Leading | SaaS / Productivity | `p3.video` · `p2.freshness` · `p2.answer-passages` |
| 6 | twilio.com | **86** | Leading | Cloud & DevOps | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 7 | bun.sh | **86** | Leading | Developer tools | `p2.freshness` · `p2.question-intent` · `p2.answer-passages` |
| 8 | vercel.com | **84** | Leading | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 9 | elevenlabs.io | **81** | Solid | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 10 | render.com | **81** | Solid | Cloud & DevOps | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 11 | intercom.com | **81** | Solid | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 12 | cloudflare.com | **80** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.video` |
| 13 | fly.io | **80** | Solid | Developer tools | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 14 | supabase.com | **80** | Solid | Developer tools | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 15 | nuxt.com | **79** | Solid | Developer tools | `p2.freshness` · `p3.video` · `p2.named-author` |
| 16 | woocommerce.com | **78** | Solid | Ecommerce | `p3.video` · `p2.named-author` · `p2.freshness` |
| 17 | calendly.com | **78** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 18 | mistral.ai | **77** | Solid | AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 19 | checkout.com | **77** | Solid | Payments / Fintech | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 20 | anker.com | **76** | Solid | China / consumer | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 21 | sentry.io | **76** | Solid | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p1.page-type` |
| 22 | nextjs.org | **76** | Solid | Developer tools | `p3.knowledge-graph` · `p3.video` · `p2.named-author` |
| 23 | klaviyo.com | **76** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 24 | monday.com | **74** | Solid | SaaS / Productivity | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 25 | railway.com | **73** | Solid | Developer tools | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 26 | squarespace.com | **73** | Solid | Ecommerce | `p2.answer-passages` · `p3.video` · `p2.named-author` |
| 27 | arstechnica.com | **72** | Solid | Media / Publishing | `p1.llms-txt` · `p2.question-intent` · `p3.sameas` |
| 28 | grafana.com | **71** | Solid | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p1.page-type` |
| 29 | hubspot.com | **71** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 30 | moz.com | **71** | Solid | Marketing / CRM | `p1.llms-txt` · `p1.page-type` · `p2.named-author` |
| 31 | stripe.com | **71** | Solid | Payments / Fintech | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 32 | asana.com | **71** | Solid | SaaS / Productivity | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 33 | deno.com | **70** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 34 | webflow.com | **70** | Solid | Ecommerce | `p2.freshness` · `p3.knowledge-graph` · `p2.named-author` |
| 35 | adyen.com | **70** | Solid | Payments / Fintech | `p2.freshness` · `p1.page-type` · `p3.video` |
| 36 | pinecone.io | **69** | Solid | AI | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 37 | tencent.com | **69** | Solid | China / enterprise | `p1.llms-txt` · `p2.question-intent` · `p1.page-type` |
| 38 | shopify.com | **69** | Solid | Ecommerce | `p2.answer-passages` · `p3.knowledge-graph` · `p1.page-type` |
| 39 | coursera.org | **69** | Solid | Education | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 40 | semrush.com | **69** | Solid | Marketing / CRM | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 41 | linear.app | **69** | Solid | SaaS / Productivity | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 42 | vuejs.org | **68** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.video` |
| 43 | kingdee.com | **67** | Solid | China / enterprise | `p2.named-author` · `p3.knowledge-graph` · `p2.question-intent` |
| 44 | bigcommerce.com | **67** | Solid | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 45 | svelte.dev | **65** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 46 | airwallex.com | **65** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 47 | datadoghq.com | **63** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p1.page-type` |
| 48 | langchain.com | **62** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 49 | braze.com | **62** | Growing | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p3.video` |
| 50 | alibabagroup.com | **61** | Growing | China / enterprise | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 51 | miro.com | **60** | Growing | SaaS / Productivity | `p2.named-author` · `p1.llms-txt` · `p3.sameas` |
| 52 | anthropic.com | **59** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 53 | smashingmagazine.com | **59** | Growing | Media / Publishing | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 54 | notion.com | **59** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 55 | replicate.com | **58** | Growing | AI | `p1.organization` · `p3.knowledge-graph` · `p1.sitemap` |
| 56 | vitejs.dev | **58** | Growing | Developer tools | `p1.organization` · `p2.question-intent` · `p1.page-type` |
| 57 | mingdao.com | **57** | Growing | China / no-code | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 58 | astro.build | **57** | Growing | Developer tools | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 59 | qwik.dev | **57** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 60 | wix.com | **57** | Growing | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 61 | moonshot.cn | **56** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 62 | mailchimp.com | **56** | Growing | Marketing / CRM | `p2.freshness` · `p1.organization` · `p2.sourced-stats` |
| 63 | digitalocean.com | **55** | Growing | Cloud & DevOps | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 64 | plaid.com | **55** | Growing | Payments / Fintech | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 65 | wise.com | **55** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 66 | deepseek.com | **53** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 67 | remix.run | **53** | Growing | Developer tools | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 68 | ahrefs.com | **53** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 69 | temu.com | **50** | Early | China / consumer | `p2.answer-passages` · `p2.freshness` · `p2.sourced-stats` |
| 70 | tailwindcss.com | **50** | Early | Developer tools | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 71 | huawei.com | **46** | Early | China / enterprise | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 72 | bytedance.com | **45** | Early | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 73 | teambition.com | **45** | Early | China / no-code | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 74 | jiandaoyun.com | **44** | Early | China / no-code | `p2.named-author` · `p2.answer-passages` · `p1.llms-txt` |
| 75 | zhipuai.cn | **43** | Early | China / AI | `p2.answer-passages` · `p2.question-intent` · `p1.organization` |
| 76 | cohere.com | **40** | Early | AI | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 77 | huggingface.co | **40** | Early | AI | `p2.named-author` · `p1.organization` · `p2.answer-passages` |
| 78 | together.ai | **40** | Early | AI | `p2.answer-passages` · `g.robots` · `p3.video` |
| 79 | weaviate.io | **40** | Early | AI | `g.ssr` · `p2.named-author` · `p2.freshness` |
| 80 | 01.ai | **40** | Early | China / AI | `p2.freshness` · `p1.organization` · `g.ssr` |
| 81 | healthline.com | **40** | Early | Healthcare | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 82 | webmd.com | **40** | Early | Healthcare | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 83 | css-tricks.com | **40** | Early | Media / Publishing | `g.reachable` · `p1.sitemap` · `p2.named-author` |
| 84 | stackoverflow.blog | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 85 | techcrunch.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p2.named-author` |
| 86 | theverge.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p2.question-intent` |
| 87 | payoneer.com | **40** | Early | Payments / Fintech | `g.robots` · `g.reachable` · `p1.page-type` |
| 88 | airtable.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 89 | figma.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 90 | loom.com | **40** | Early | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 91 | slack.com | **40** | Early | SaaS / Productivity | `p2.freshness` · `p1.organization` · `g.reachable` |
| 92 | booking.com | **39** | Early | Travel | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 93 | dji.com | **38** | Early | China / consumer | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 94 | yonyou.com | **38** | Early | China / enterprise | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 95 | volcengine.com | **34** | Early | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 96 | airbnb.com | **34** | Early | Travel | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 97 | xiaomi.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 98 | solidjs.com | **29** | Not started | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 99 | khanacademy.org | **28** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 100 | shein.com | **26** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 101 | freecodecamp.org | **23** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 102 | qcloud.com | **22** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 103 | feishu.cn | **20** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 104 | yuque.com | **18** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 105 | aliyun.com | **16** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |

### Not scored

- **openai.com** — could not fetch https://www.openai.com — all requests returned 308
- **perplexity.ai** — could not fetch https://www.perplexity.ai — all requests returned 403
- **runwayml.com** — could not fetch https://www.runwayml.com — all requests returned 308
- **insta360.com** — could not fetch https://www.insta360.com — all requests returned 403
- **hashicorp.com** — could not fetch https://www.hashicorp.com — all requests returned 429
- **etsy.com** — could not fetch https://www.etsy.com — all requests returned 403
- **udemy.com** — could not fetch https://www.udemy.com — all requests returned 403
- **mayoclinic.org** — could not fetch https://www.mayoclinic.org — all requests returned 403
- **expedia.com** — could not fetch https://www.expedia.com — all requests returned 429

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

