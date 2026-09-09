# The state of AI visibility

Every site below scored with the same open rubric, the same public tool and the same
eight-page sample. No private data, no vendor dashboards — [re-run it yourself](run.py).

**164 sites · median 59.0 · mean 57.3 · upper quartile 73.0 · range 7–95** · rubric v1.1 · measured 2026-09-09

## A quarter of the field cannot be cited at all

**41 of 164 sites have a gate check at zero** — a crawler cannot get the content, so
nothing else on the page matters. These are two very different problems, and reporting
them as one number is what makes such a number useless:

| Why | Sites | Which |
|---|:-:|---|
| **Deliberate** — `robots.txt` disallows retrieval crawlers | 14 | amazon.com, figma.com, healthline.com, june.so, khanacademy.org, loom.com, mercadolibre.com, payoneer.com, qcloud.com, stackoverflow.blog, techcrunch.com, theverge.com, together.ai, webmd.com |
| **Deliberate or accidental** — the server returns 403 to crawlers | 6 | airbnb.com, css-tricks.com, ebay.com, lenovo.com, stratechery.com, xiaomi.com |
| **Accidental** — body copy only exists after JS runs | 21 | 01.ai, airtable.com, aliexpress.com, baichuan-ai.com, bigmodel.cn, booking.com, cohere.com, feishu.cn, freecodecamp.org, huggingface.co, lianlianpay.com, payoneer.cn, sellersprite.com, shein.com, solidjs.com, stepfun.com, temu.com, turso.tech, walmart.com, weaviate.io, yuque.com |

The first group made a choice. Several news and health publishers block AI crawlers by
name, and this rubric reports that as it is — a site that does not want to be quoted is
not misconfigured. The last group almost certainly did not choose it: their content is
there, a browser can see it, and a retrieval crawler gets an empty shell.

## What the spread shows

**Half the field sits between 40.0 and 73.0.** The rubric is not grading on a curve — these
are the scores that fall out of it, and they are consistent with the public benchmarks
it was [calibrated against](../rubric/calibration-v1.1.md).

**Sites built for the Chinese market score 20 points lower** — median 43.0 against 62.5
for everyone else. The gap is not content quality. It is `llms.txt`, `Organization`
schema, visible dates and bylines — conventions that spread through the English web
first and have not yet crossed over.

**The same few things are missing almost everywhere.** Counting only each site's three
largest gaps:

| Missing | Sites | What it costs |
|---|:-:|:-:|
| `p2.answer-passages` | 82 of 164 | 9 pts |
| `p2.named-author` | 81 of 164 | 6 pts |
| `p2.freshness` | 76 of 164 | 6 pts |
| `p1.organization` | 54 of 164 | 6 pts |
| `p2.question-intent` | 46 of 164 | 7 pts |
| `p1.llms-txt` | 33 of 164 | 5 pts |

None of the top three is expensive. A date in a page template, an opening paragraph
that stands on its own, and one JSON-LD block are between them worth more than any
single pillar on this list.

## By sector

| Sector | Sites | Median |
|---|:-:|:-:|
| Cloud & DevOps | 15 | **81** |
| Developer tools | 25 | **70** |
| Payments / Fintech | 7 | **70** |
| SaaS / Productivity | 17 | **67** |
| Ecommerce | 11 | **66** |
| Marketing / CRM | 12 | **65.5** |
| AI | 18 | **61.0** |
| China / enterprise | 6 | **55.0** |
| China / AI | 9 | **43** |
| China / no-code | 5 | **43** |
| Media / Publishing | 9 | **40** |
| Healthcare | 2 | **39.5** |
| China / consumer | 13 | **37** |
| China / cloud | 3 | **34** |
| Cross-border services | 7 | **30** |
| Education | 3 | **28** |
| Travel | 2 | **23.5** |

## Every site

| # | Site | Score | Band | Sector | Biggest gaps |
|:-:|---|:-:|---|---|---|
| 1 | minimaxi.com | **95** | Leading | China / AI | `p2.question-intent` · `p4.cn-engines` · `p3.video` |
| 2 | pulumi.com | **95** | Leading | Cloud & DevOps | `g.robots` · `g.reachable` · `p3.video` |
| 3 | resend.com | **94** | Leading | Developer tools | `p2.freshness` · `p2.answer-passages` · `p3.video` |
| 4 | zapier.com | **92** | Leading | SaaS / Productivity | `p2.freshness` · `p2.named-author` · `p3.sameas` |
| 5 | netlify.com | **91** | Leading | Cloud & DevOps | `p2.named-author` · `p2.answer-passages` · `p3.video` |
| 6 | bun.sh | **88** | Leading | Developer tools | `p2.freshness` · `p2.question-intent` · `p2.answer-passages` |
| 7 | clerk.com | **88** | Leading | Developer tools | `p2.sourced-stats` · `p2.answer-passages` · `p1.sitemap` |
| 8 | prisma.io | **87** | Leading | Developer tools | `p2.question-intent` · `p3.video` · `p2.freshness` |
| 9 | trigger.dev | **87** | Leading | Developer tools | `p3.video` · `p3.sameas` · `p2.named-author` |
| 10 | clickup.com | **87** | Leading | SaaS / Productivity | `p3.video` · `p2.freshness` · `p2.answer-passages` |
| 11 | twilio.com | **85** | Leading | Cloud & DevOps | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 12 | elevenlabs.io | **84** | Leading | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 13 | axiom.co | **84** | Leading | Cloud & DevOps | `p2.freshness` · `p3.video` · `p2.named-author` |
| 14 | nuxt.com | **84** | Leading | Developer tools | `p2.freshness` · `p3.video` · `p2.question-intent` |
| 15 | upstash.com | **83** | Leading | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p3.video` |
| 16 | vercel.com | **83** | Leading | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 17 | fly.io | **83** | Leading | Developer tools | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 18 | supabase.com | **82** | Solid | Developer tools | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 19 | cloudflare.com | **81** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.video` |
| 20 | sentry.io | **81** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 21 | planetscale.com | **81** | Solid | Developer tools | `p3.knowledge-graph` · `p2.named-author` · `p2.answer-passages` |
| 22 | mistral.ai | **80** | Solid | AI | `p2.answer-passages` · `p2.named-author` · `p1.breadcrumb` |
| 23 | baseus.com | **80** | Solid | China / consumer | `p3.knowledge-graph` · `p3.sameas` · `p2.named-author` |
| 24 | render.com | **80** | Solid | Cloud & DevOps | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 25 | helium10.com | **79** | Solid | Cross-border services | `p2.answer-passages` · `p1.llms-txt` · `p2.named-author` |
| 26 | intercom.com | **79** | Solid | Marketing / CRM | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 27 | calendly.com | **79** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 28 | junglescout.com | **78** | Solid | Cross-border services | `p1.llms-txt` · `p1.page-type` · `p3.sameas` |
| 29 | woocommerce.com | **78** | Solid | Ecommerce | `p3.video` · `p2.named-author` · `p2.freshness` |
| 30 | fireworks.ai | **77** | Solid | AI | `p1.llms-txt` · `p2.named-author` · `p2.freshness` |
| 31 | tcl.com | **77** | Solid | China / consumer | `p1.llms-txt` · `p3.sameas` · `p2.named-author` |
| 32 | railway.com | **77** | Solid | Developer tools | `p2.named-author` · `p2.freshness` · `p4.answer-shape` |
| 33 | typeform.com | **77** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 34 | nextjs.org | **76** | Solid | Developer tools | `p3.knowledge-graph` · `p3.video` · `p2.named-author` |
| 35 | moz.com | **76** | Solid | Marketing / CRM | `p1.llms-txt` · `p1.page-type` · `p1.organization` |
| 36 | airwallex.com | **76** | Solid | Payments / Fintech | `p2.freshness` · `p2.named-author` · `p1.organization` |
| 37 | inngest.com | **74** | Solid | Developer tools | `p2.freshness` · `p3.knowledge-graph` · `p2.question-intent` |
| 38 | squarespace.com | **74** | Solid | Ecommerce | `p2.answer-passages` · `p3.video` · `p2.named-author` |
| 39 | webflow.com | **74** | Solid | Ecommerce | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 40 | klaviyo.com | **74** | Solid | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p4.answer-shape` |
| 41 | crewai.com | **73** | Solid | AI | `p2.question-intent` · `p1.page-type` · `p2.named-author` |
| 42 | ecoflow.com | **73** | Solid | China / consumer | `p2.answer-passages` · `p1.page-type` · `p2.named-author` |
| 43 | shopify.com | **73** | Solid | Ecommerce | `p2.answer-passages` · `p1.page-type` · `p2.named-author` |
| 44 | monday.com | **73** | Solid | SaaS / Productivity | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 45 | arstechnica.com | **72** | Solid | Media / Publishing | `p1.llms-txt` · `p2.question-intent` · `p3.sameas` |
| 46 | checkout.com | **72** | Solid | Payments / Fintech | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 47 | asana.com | **72** | Solid | SaaS / Productivity | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 48 | kingdee.com | **71** | Solid | China / enterprise | `p2.named-author` · `p2.question-intent` · `p1.page-type` |
| 49 | grafana.com | **71** | Solid | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p1.page-type` |
| 50 | wired.com | **71** | Solid | Media / Publishing | `p1.llms-txt` · `p3.sameas` · `p2.named-author` |
| 51 | stripe.com | **71** | Solid | Payments / Fintech | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 52 | productboard.com | **71** | Solid | SaaS / Productivity | `p2.answer-passages` · `p1.page-type` · `p2.named-author` |
| 53 | langfuse.com | **70** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 54 | modal.com | **70** | Solid | AI | `p3.knowledge-graph` · `p1.sitemap` · `p1.page-type` |
| 55 | tencent.com | **70** | Solid | China / enterprise | `p1.llms-txt` · `p2.question-intent` · `p1.page-type` |
| 56 | deno.com | **70** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 57 | vuejs.org | **70** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.video` |
| 58 | hubspot.com | **70** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 59 | adyen.com | **70** | Solid | Payments / Fintech | `p2.freshness` · `p1.page-type` · `p3.video` |
| 60 | pinecone.io | **69** | Solid | AI | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 61 | anker.com | **69** | Solid | China / consumer | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 62 | shoplazza.com | **69** | Solid | Ecommerce | `p1.organization` · `p3.knowledge-graph` · `p3.sameas` |
| 63 | coursera.org | **69** | Solid | Education | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 64 | semrush.com | **69** | Solid | Marketing / CRM | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 65 | linear.app | **69** | Solid | SaaS / Productivity | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 66 | replicate.com | **67** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.video` |
| 67 | attio.com | **67** | Solid | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p2.named-author` |
| 68 | cal.com | **67** | Solid | SaaS / Productivity | `p2.answer-passages` · `p3.knowledge-graph` · `p3.sameas` |
| 69 | bigcommerce.com | **66** | Solid | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 70 | braze.com | **64** | Growing | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p3.video` |
| 71 | datadoghq.com | **63** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p1.page-type` |
| 72 | langchain.com | **62** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 73 | svelte.dev | **62** | Growing | Developer tools | `p1.organization` · `p3.knowledge-graph` · `p1.sitemap` |
| 74 | alibabagroup.com | **61** | Growing | China / enterprise | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 75 | browserbase.com | **60** | Growing | AI | `p2.named-author` · `p2.answer-passages` · `p3.knowledge-graph` |
| 76 | mingdao.com | **60** | Growing | China / no-code | `p2.freshness` · `p2.answer-passages` · `p2.question-intent` |
| 77 | astro.build | **60** | Growing | Developer tools | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 78 | vitest.dev | **60** | Growing | Developer tools | `p1.organization` · `p3.knowledge-graph` · `p1.sitemap` |
| 79 | miro.com | **60** | Growing | SaaS / Productivity | `p2.named-author` · `p1.llms-txt` · `p3.sameas` |
| 80 | anthropic.com | **59** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 81 | koyeb.com | **59** | Growing | Cloud & DevOps | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 82 | posthog.com | **59** | Growing | Marketing / CRM | `p2.freshness` · `p2.answer-passages` · `p2.sourced-stats` |
| 83 | notion.com | **59** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 84 | hono.dev | **58** | Growing | Developer tools | `p1.organization` · `p2.sourced-stats` · `p1.sitemap` |
| 85 | vitejs.dev | **58** | Growing | Developer tools | `p1.organization` · `p2.question-intent` · `p1.page-type` |
| 86 | porter.run | **57** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p1.page-type` |
| 87 | customer.io | **57** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p3.knowledge-graph` |
| 88 | smashingmagazine.com | **57** | Growing | Media / Publishing | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 89 | wise.com | **57** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 90 | moonshot.cn | **56** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 91 | siliconflow.cn | **56** | Growing | China / AI | `p2.named-author` · `p1.organization` · `p2.sourced-stats` |
| 92 | mailchimp.com | **56** | Growing | Marketing / CRM | `p2.freshness` · `p1.organization` · `p2.sourced-stats` |
| 93 | slack.com | **56** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p3.knowledge-graph` |
| 94 | qwik.dev | **55** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 95 | wix.com | **55** | Growing | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p3.knowledge-graph` |
| 96 | tability.io | **55** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 97 | deepseek.com | **54** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 98 | betterstack.com | **53** | Growing | Cloud & DevOps | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 99 | ahrefs.com | **53** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 100 | digitalocean.com | **52** | Growing | Cloud & DevOps | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 101 | plaid.com | **52** | Growing | Payments / Fintech | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 102 | baseten.co | **51** | Growing | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 103 | groq.com | **51** | Growing | AI | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 104 | remix.run | **51** | Growing | Developer tools | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 105 | tailwindcss.com | **50** | Early | Developer tools | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 106 | simonwillison.net | **50** | Early | Media / Publishing | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 107 | llamaindex.ai | **49** | Early | AI | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 108 | huawei.com | **49** | Early | China / enterprise | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 109 | biomejs.dev | **49** | Early | Developer tools | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 110 | aliyun.com | **48** | Early | China / cloud | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 111 | teambition.com | **47** | Early | China / no-code | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 112 | lazada.com | **44** | Early | China / consumer | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 113 | bytedance.com | **44** | Early | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 114 | coda.io | **44** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 115 | zhipuai.cn | **43** | Early | China / AI | `p2.answer-passages` · `p2.question-intent` · `p1.organization` |
| 116 | yonyou.com | **43** | Early | China / enterprise | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 117 | jiandaoyun.com | **43** | Early | China / no-code | `p2.question-intent` · `p2.named-author` · `p2.answer-passages` |
| 118 | cohere.com | **40** | Early | AI | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 119 | huggingface.co | **40** | Early | AI | `p2.named-author` · `p1.organization` · `p2.answer-passages` |
| 120 | together.ai | **40** | Early | AI | `p2.answer-passages` · `g.robots` · `p3.video` |
| 121 | weaviate.io | **40** | Early | AI | `g.ssr` · `p3.knowledge-graph` · `p2.named-author` |
| 122 | 01.ai | **40** | Early | China / AI | `p2.freshness` · `p1.organization` · `g.ssr` |
| 123 | dji.com | **40** | Early | China / consumer | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 124 | sellersprite.com | **40** | Early | Cross-border services | `p2.answer-passages` · `g.ssr` · `p2.question-intent` |
| 125 | turso.tech | **40** | Early | Developer tools | `p2.named-author` · `p2.answer-passages` · `g.ssr` |
| 126 | ebay.com | **40** | Early | Ecommerce | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 127 | walmart.com | **40** | Early | Ecommerce | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 128 | healthline.com | **40** | Early | Healthcare | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 129 | june.so | **40** | Early | Marketing / CRM | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 130 | css-tricks.com | **40** | Early | Media / Publishing | `g.reachable` · `p1.sitemap` · `p2.named-author` |
| 131 | stackoverflow.blog | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 132 | stratechery.com | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.reachable` |
| 133 | techcrunch.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p2.question-intent` |
| 134 | theverge.com | **40** | Early | Media / Publishing | `p2.answer-passages` · `p1.llms-txt` · `g.robots` |
| 135 | payoneer.com | **40** | Early | Payments / Fintech | `g.robots` · `g.reachable` · `p1.page-type` |
| 136 | airtable.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 137 | figma.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 138 | loom.com | **40** | Early | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 139 | webmd.com | **39** | Early | Healthcare | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 140 | temu.com | **37** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 141 | volcengine.com | **34** | Early | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 142 | hisense.com | **34** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 143 | lenovo.com | **34** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 144 | miniso.com | **34** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 145 | aliexpress.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 146 | payoneer.cn | **30** | Not started | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 147 | yuncang.com | **30** | Not started | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 148 | solidjs.com | **29** | Not started | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 149 | airbnb.com | **29** | Not started | Travel | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 150 | khanacademy.org | **28** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 151 | xiaomi.com | **27** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 152 | bigmodel.cn | **26** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 153 | pingpongx.com | **24** | Not started | Cross-border services | `p2.answer-passages` · `p2.sourced-stats` · `p2.question-intent` |
| 154 | qcloud.com | **23** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 155 | freecodecamp.org | **23** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 156 | shein.com | **21** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 157 | feishu.cn | **20** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 158 | yuque.com | **19** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 159 | booking.com | **18** | Not started | Travel | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 160 | baichuan-ai.com | **16** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 161 | stepfun.com | **14** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 162 | lianlianpay.com | **14** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 163 | amazon.com | **8** | Not started | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 164 | mercadolibre.com | **7** | Not started | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |

### Not scored

- **openai.com** — could not fetch https://www.openai.com — all requests returned 308
- **perplexity.ai** — could not fetch https://www.perplexity.ai — all requests returned 403
- **runwayml.com** — could not fetch https://www.runwayml.com — all requests returned 308
- **cider.com** — could not fetch https://www.cider.com — <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostn
- **clubfactory.com** — unknown url type: '/sitemap.xml'
- **insta360.com** — could not fetch https://www.insta360.com — all requests returned 403
- **oceanwing.com** — could not fetch https://www.oceanwing.com — all requests returned 403
- **ugreen.com** — could not fetch https://www.ugreen.com — all requests returned 429
- **hashicorp.com** — could not fetch https://www.hashicorp.com — all requests returned 429
- **aftership.com** — could not fetch https://www.aftership.com — all requests returned 403
- **neon.tech** — could not fetch https://www.neon.tech — all requests returned 308
- **allegro.pl** — could not fetch https://www.allegro.pl — all requests returned 403
- **etsy.com** — could not fetch https://www.etsy.com — all requests returned 403
- **ozon.ru** — could not fetch https://www.ozon.ru — all requests returned 307
- **shopline.com** — could not fetch https://www.shopline.com — all requests returned 403
- **udemy.com** — could not fetch https://www.udemy.com — all requests returned 403
- **mayoclinic.org** — could not fetch https://www.mayoclinic.org — all requests returned 403
- **theinformation.com** — could not fetch https://www.theinformation.com — all requests returned 403
- **height.app** — could not fetch https://www.height.app — <urlopen error _ssl.c:1112: The handshake operation timed out>
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

