# The state of AI visibility

Every site below scored with the same open rubric, the same public tool and the same
eight-page sample. No private data, no vendor dashboards — [re-run it yourself](run.py).

**Browse it as a page instead:** [English](https://jianruntech.github.io/geo-score/) ·
[简体中文](https://jianruntech.github.io/geo-score/zh.html) — searchable, sortable, and
filterable by sector. This file and those pages are both generated from
[`results.json`](results.json), so they cannot drift.

**106 sites · median 59.5 · mean 57.9 · upper quartile 73.0 · range 14–92** · rubric v1.1 · measured 2026-09-09

## A quarter of the field cannot be cited at all

**27 of 106 sites have a gate check at zero** — a crawler cannot get the content, so
nothing else on the page matters. These are two very different problems, and reporting
them as one number is what makes such a number useless:

| Why | Sites | Which |
|---|:-:|---|
| **Deliberate** — `robots.txt` disallows retrieval crawlers | 11 | figma.com, healthline.com, khanacademy.org, loom.com, payoneer.com, qcloud.com, stackoverflow.blog, techcrunch.com, theverge.com, together.ai, webmd.com |
| **Deliberate or accidental** — the server returns 403 to crawlers | 3 | airbnb.com, css-tricks.com, xiaomi.com |
| **Accidental** — body copy only exists after JS runs | 13 | 01.ai, airtable.com, aliyun.com, booking.com, cohere.com, feishu.cn, freecodecamp.org, huggingface.co, shein.com, solidjs.com, temu.com, weaviate.io, yuque.com |

The first group made a choice. Several news and health publishers block AI crawlers by
name, and this rubric reports that as it is — a site that does not want to be quoted is
not misconfigured. The last group almost certainly did not choose it: their content is
there, a browser can see it, and a retrieval crawler gets an empty shell.

## What the spread shows

**Half the field sits between 40.0 and 73.0.** The rubric is not grading on a curve — these
are the scores that fall out of it, and they are consistent with the public benchmarks
it was [calibrated against](../rubric/calibration-v1.1.md).

**Sites built for the Chinese market score 23 points lower** — median 43.0 against 66.0
for everyone else. The gap is not content quality. It is `llms.txt`, `Organization`
schema, visible dates and bylines — conventions that spread through the English web
first and have not yet crossed over.

**The same few things are missing almost everywhere.** Counting only each site's three
largest gaps:

| Missing | Sites | What it costs |
|---|:-:|:-:|
| `p2.named-author` | 57 of 106 | 6 pts |
| `p2.freshness` | 57 of 106 | 6 pts |
| `p2.answer-passages` | 53 of 106 | 9 pts |
| `p1.organization` | 33 of 106 | 6 pts |
| `p2.question-intent` | 30 of 106 | 7 pts |
| `p1.page-type` | 20 of 106 | 4 pts |

None of the top three is expensive. A date in a page template, an opening paragraph
that stands on its own, and one JSON-LD block are between them worth more than any
single pillar on this list.

## By sector

| Sector | Sites | Median |
|---|:-:|:-:|
| Cloud & DevOps | 10 | **81.0** |
| Ecommerce | 6 | **73.5** |
| Developer tools | 16 | **70.0** |
| Marketing / CRM | 8 | **70.0** |
| Payments / Fintech | 7 | **70** |
| SaaS / Productivity | 12 | **63.5** |
| AI | 10 | **60.5** |
| China / enterprise | 6 | **55.5** |
| China / AI | 4 | **49.5** |
| China / no-code | 5 | **45** |
| Healthcare | 2 | **40.0** |
| Media / Publishing | 6 | **40.0** |
| China / consumer | 6 | **32.0** |
| Education | 3 | **24** |
| China / cloud | 3 | **23** |
| Travel | 2 | **22.0** |

## Every site

| # | Site | Score | Band | Sector | Biggest gaps |
|:-:|---|:-:|---|---|---|
| 1 | netlify.com | **92** | Leading | Cloud & DevOps | `p2.named-author` · `p2.answer-passages` · `p3.video` |
| 2 | pulumi.com | **91** | Leading | Cloud & DevOps | `p2.freshness` · `g.robots` · `g.reachable` |
| 3 | bun.sh | **88** | Leading | Developer tools | `p2.freshness` · `p2.question-intent` · `p2.answer-passages` |
| 4 | prisma.io | **87** | Leading | Developer tools | `p2.question-intent` · `p3.video` · `p2.freshness` |
| 5 | clickup.com | **87** | Leading | SaaS / Productivity | `p3.video` · `p2.freshness` · `p2.answer-passages` |
| 6 | zapier.com | **87** | Leading | SaaS / Productivity | `p2.freshness` · `p3.knowledge-graph` · `p2.named-author` |
| 7 | elevenlabs.io | **84** | Leading | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 8 | intercom.com | **84** | Leading | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 9 | twilio.com | **83** | Leading | Cloud & DevOps | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 10 | vercel.com | **83** | Leading | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 11 | supabase.com | **83** | Leading | Developer tools | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 12 | mistral.ai | **81** | Solid | AI | `p2.answer-passages` · `p2.named-author` · `p1.breadcrumb` |
| 13 | cloudflare.com | **81** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.video` |
| 14 | render.com | **81** | Solid | Cloud & DevOps | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 15 | sentry.io | **81** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 16 | fly.io | **81** | Solid | Developer tools | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 17 | nextjs.org | **80** | Solid | Developer tools | `p3.video` · `p2.named-author` · `p1.breadcrumb` |
| 18 | nuxt.com | **79** | Solid | Developer tools | `p2.freshness` · `p3.video` · `p2.named-author` |
| 19 | woocommerce.com | **79** | Solid | Ecommerce | `p3.video` · `p2.named-author` · `p2.freshness` |
| 20 | calendly.com | **78** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 21 | checkout.com | **77** | Solid | Payments / Fintech | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 22 | klaviyo.com | **76** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 23 | grafana.com | **74** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.sameas` |
| 24 | squarespace.com | **74** | Solid | Ecommerce | `p2.answer-passages` · `p3.video` · `p2.named-author` |
| 25 | webflow.com | **74** | Solid | Ecommerce | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 26 | monday.com | **74** | Solid | SaaS / Productivity | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 27 | anker.com | **73** | Solid | China / consumer | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 28 | railway.com | **73** | Solid | Developer tools | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 29 | shopify.com | **73** | Solid | Ecommerce | `p2.answer-passages` · `p1.page-type` · `p2.named-author` |
| 30 | moz.com | **73** | Solid | Marketing / CRM | `p1.llms-txt` · `p1.page-type` · `p2.named-author` |
| 31 | arstechnica.com | **72** | Solid | Media / Publishing | `p1.llms-txt` · `p2.question-intent` · `p3.sameas` |
| 32 | hubspot.com | **71** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 33 | stripe.com | **71** | Solid | Payments / Fintech | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 34 | deno.com | **70** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 35 | vuejs.org | **70** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.video` |
| 36 | adyen.com | **70** | Solid | Payments / Fintech | `p2.freshness` · `p1.page-type` · `p3.video` |
| 37 | airwallex.com | **70** | Solid | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.page-type` |
| 38 | asana.com | **70** | Solid | SaaS / Productivity | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 39 | tencent.com | **69** | Solid | China / enterprise | `p1.llms-txt` · `p2.question-intent` · `p1.page-type` |
| 40 | semrush.com | **69** | Solid | Marketing / CRM | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 41 | pinecone.io | **67** | Solid | AI | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 42 | kingdee.com | **67** | Solid | China / enterprise | `p2.named-author` · `p3.knowledge-graph` · `p2.question-intent` |
| 43 | linear.app | **67** | Solid | SaaS / Productivity | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 44 | replicate.com | **66** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.video` |
| 45 | svelte.dev | **66** | Solid | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 46 | bigcommerce.com | **66** | Solid | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 47 | coursera.org | **64** | Growing | Education | `p2.answer-passages` · `p2.freshness` · `p3.knowledge-graph` |
| 48 | braze.com | **64** | Growing | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p3.video` |
| 49 | langchain.com | **62** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 50 | alibabagroup.com | **62** | Growing | China / enterprise | `p1.organization` · `p2.answer-passages` · `p2.question-intent` |
| 51 | datadoghq.com | **60** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p1.page-type` |
| 52 | notion.com | **60** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 53 | slack.com | **60** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 54 | anthropic.com | **59** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 55 | smashingmagazine.com | **59** | Growing | Media / Publishing | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 56 | miro.com | **59** | Growing | SaaS / Productivity | `p2.named-author` · `p1.llms-txt` · `p3.sameas` |
| 57 | deepseek.com | **58** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 58 | vitejs.dev | **58** | Growing | Developer tools | `p1.organization` · `p2.question-intent` · `p1.page-type` |
| 59 | ahrefs.com | **58** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 60 | mingdao.com | **57** | Growing | China / no-code | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 61 | wise.com | **57** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 62 | moonshot.cn | **56** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 63 | mailchimp.com | **56** | Growing | Marketing / CRM | `p2.freshness` · `p1.organization` · `p2.sourced-stats` |
| 64 | astro.build | **55** | Growing | Developer tools | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 65 | digitalocean.com | **52** | Growing | Cloud & DevOps | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 66 | tailwindcss.com | **52** | Growing | Developer tools | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 67 | wix.com | **52** | Growing | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p3.knowledge-graph` |
| 68 | remix.run | **51** | Growing | Developer tools | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 69 | qwik.dev | **50** | Early | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 70 | plaid.com | **50** | Early | Payments / Fintech | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 71 | huawei.com | **49** | Early | China / enterprise | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 72 | bytedance.com | **45** | Early | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 73 | jiandaoyun.com | **45** | Early | China / no-code | `p2.question-intent` · `p2.named-author` · `p2.answer-passages` |
| 74 | teambition.com | **45** | Early | China / no-code | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 75 | zhipuai.cn | **43** | Early | China / AI | `p2.answer-passages` · `p2.question-intent` · `p1.organization` |
| 76 | yonyou.com | **43** | Early | China / enterprise | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 77 | cohere.com | **40** | Early | AI | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 78 | huggingface.co | **40** | Early | AI | `p2.named-author` · `p1.organization` · `p2.answer-passages` |
| 79 | together.ai | **40** | Early | AI | `p2.answer-passages` · `g.robots` · `p3.video` |
| 80 | weaviate.io | **40** | Early | AI | `g.ssr` · `p2.named-author` · `p2.freshness` |
| 81 | 01.ai | **40** | Early | China / AI | `p2.freshness` · `p1.organization` · `g.ssr` |
| 82 | healthline.com | **40** | Early | Healthcare | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 83 | webmd.com | **40** | Early | Healthcare | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 84 | css-tricks.com | **40** | Early | Media / Publishing | `g.reachable` · `p1.sitemap` · `p2.named-author` |
| 85 | stackoverflow.blog | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 86 | techcrunch.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p2.named-author` |
| 87 | theverge.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p2.question-intent` |
| 88 | payoneer.com | **40** | Early | Payments / Fintech | `g.robots` · `g.reachable` · `p3.knowledge-graph` |
| 89 | airtable.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 90 | figma.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 91 | loom.com | **40** | Early | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 92 | dji.com | **38** | Early | China / consumer | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 93 | volcengine.com | **33** | Early | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 94 | insta360.com | **33** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 95 | solidjs.com | **33** | Early | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 96 | temu.com | **31** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 97 | xiaomi.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 98 | airbnb.com | **30** | Not started | Travel | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 99 | khanacademy.org | **24** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 100 | qcloud.com | **23** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 101 | shein.com | **23** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 102 | feishu.cn | **20** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 103 | freecodecamp.org | **19** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 104 | yuque.com | **18** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 105 | aliyun.com | **16** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 106 | booking.com | **14** | Not started | Travel | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |

### Not scored

- **openai.com** — could not fetch https://www.openai.com — all requests returned 308
- **perplexity.ai** — could not fetch https://www.perplexity.ai — all requests returned 403
- **runwayml.com** — could not fetch https://www.runwayml.com — all requests returned 308
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

