# The state of AI visibility

Every site below scored with the same open rubric, the same public tool and the same
eight-page sample. No private data, no vendor dashboards — [re-run it yourself](run.py).

**314 sites · median 56.0 · mean 54.9 · upper quartile 71.8 · range 12–98** · rubric v1.1 · measured 2026-09-09

## A quarter of the field cannot be cited at all

**80 of 314 sites have a gate check at zero** — a crawler cannot get the content, so
nothing else on the page matters. These are two very different problems, and reporting
them as one number is what makes such a number useless:

| Why | Sites | Which |
|---|:-:|---|
| **Deliberate** — `robots.txt` disallows retrieval crawlers | 19 | amazon.com, expeditors.com, figma.com, healthline.com, jdcloud.com, june.so, khanacademy.org, lexisnexis.com, lonelyplanet.com, loom.com, mercadolibre.com, payoneer.com, qcloud.com, stackoverflow.blog, techcrunch.com, theregister.com, theverge.com, together.ai, webmd.com |
| **Deliberate or accidental** — the server returns 403 to crawlers | 16 | abb.com, airbnb.com, css-tricks.com, drugs.com, ebay.com, hilton.com, honeywell.com, keepa.com, lenovo.com, maersk.com, marriott.com, nostarch.com, pwc.com, slack.com, stratechery.com, trendyol.com |
| **Accidental** — body copy only exists after JS runs | 45 | 01.ai, 4px.com, agoda.com, airtable.com, aliexpress.com, aliyun.com, baichuan-ai.com, bigmodel.cn, booking.com, clevelandclinic.org, cohere.com, continue.dev, datahawk.co, dingtalk.com, drizzle.team, duolingo.com, fanruan.com, feishu.cn, freecodecamp.org, huoban.com, jushuitan.com, lianlianpay.com, megvii.com, narwal.com, obsidian.md, oceanwing.com, payoneer.cn, perpetua.io, rakuten.com, roborock.com, sellersprite.com, sf-express.com, shein.com, shopee.com, skyscanner.net, solidjs.com, stepfun.com, temu.com, turso.tech, walmart.com, weaviate.io, windsurf.com, wps.cn, xiaomi.com, yuque.com |

The first group made a choice. Several news and health publishers block AI crawlers by
name, and this rubric reports that as it is — a site that does not want to be quoted is
not misconfigured. The last group almost certainly did not choose it: their content is
there, a browser can see it, and a retrieval crawler gets an empty shell.

## What the spread shows

**Half the field sits between 40.0 and 71.8.** The rubric is not grading on a curve — these
are the scores that fall out of it, and they are consistent with the public benchmarks
it was [calibrated against](../rubric/calibration-v1.1.md).

**Sites built for the Chinese market score 19 points lower** — median 40.0 against 59.0
for everyone else. The gap is not content quality. It is `llms.txt`, `Organization`
schema, visible dates and bylines — conventions that spread through the English web
first and have not yet crossed over.

**The same few things are missing almost everywhere.** Counting only each site's three
largest gaps:

| Missing | Sites | What it costs |
|---|:-:|:-:|
| `p2.answer-passages` | 155 of 314 | 9 pts |
| `p2.named-author` | 153 of 314 | 6 pts |
| `p2.freshness` | 147 of 314 | 6 pts |
| `p1.organization` | 106 of 314 | 6 pts |
| `p2.question-intent` | 93 of 314 | 7 pts |
| `p1.llms-txt` | 84 of 314 | 5 pts |

None of the top three is expensive. A date in a page template, an opening paragraph
that stands on its own, and one JSON-LD block are between them worth more than any
single pillar on this list.

## By sector

| Sector | Sites | Median |
|---|:-:|:-:|
| Marketing / CRM | 17 | **73** |
| Cloud & DevOps | 24 | **72.5** |
| Professional services | 9 | **70** |
| AI | 29 | **66** |
| Payments / Fintech | 12 | **63.0** |
| Developer tools | 38 | **62.0** |
| SaaS / Productivity | 22 | **59.5** |
| Education | 12 | **55.0** |
| Healthcare | 12 | **51.0** |
| Ecommerce | 14 | **49.5** |
| China / enterprise | 10 | **46.0** |
| China / AI | 13 | **45** |
| Logistics / Freight | 10 | **42.0** |
| Media / Publishing | 10 | **40.0** |
| Travel | 10 | **40.0** |
| Manufacturing / Industrial | 11 | **39** |
| China / consumer | 21 | **38** |
| China / cloud | 9 | **37** |
| Cross-border services | 20 | **37.0** |
| China / no-code | 11 | **36** |

## Every site

| # | Site | Score | Band | Sector | Biggest gaps |
|:-:|---|:-:|---|---|---|
| 1 | pulumi.com | **98** | Leading | Cloud & DevOps | `g.robots` · `p3.video` · `p3.sameas` |
| 2 | minimaxi.com | **95** | Leading | China / AI | `p2.question-intent` · `p4.cn-engines` · `p3.video` |
| 3 | lumalabs.ai | **93** | Leading | AI | `p2.question-intent` · `g.reachable` · `p3.sameas` |
| 4 | resend.com | **93** | Leading | Developer tools | `p3.knowledge-graph` · `p2.answer-passages` · `p3.video` |
| 5 | ironcladapp.com | **91** | Leading | Professional services | `p2.named-author` · `p2.answer-passages` · `p1.sitemap` |
| 6 | bun.sh | **88** | Leading | Developer tools | `p2.freshness` · `p2.question-intent` · `p2.answer-passages` |
| 7 | clerk.com | **88** | Leading | Developer tools | `p2.sourced-stats` · `p2.answer-passages` · `p1.sitemap` |
| 8 | kayak.com | **88** | Leading | Travel | `p2.named-author` · `p2.freshness` · `p1.sitemap` |
| 9 | clickup.com | **87** | Leading | SaaS / Productivity | `p3.video` · `p2.freshness` · `p2.answer-passages` |
| 10 | zapier.com | **87** | Leading | SaaS / Productivity | `p2.freshness` · `p2.named-author` · `p2.question-intent` |
| 11 | runway.com | **86** | Leading | AI | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 12 | veeva.com | **86** | Leading | Healthcare | `p3.sameas` · `p2.named-author` · `p1.page-type` |
| 13 | openrouter.ai | **85** | Leading | AI | `p2.answer-passages` · `p2.named-author` · `p2.sourced-stats` |
| 14 | elevenlabs.io | **84** | Leading | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 15 | axiom.co | **84** | Leading | Cloud & DevOps | `p2.freshness` · `p3.video` · `p2.named-author` |
| 16 | motherduck.com | **84** | Leading | Cloud & DevOps | `p2.named-author` · `p2.freshness` · `p4.answer-shape` |
| 17 | vercel.com | **84** | Leading | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 18 | fly.io | **84** | Leading | Developer tools | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 19 | nuxt.com | **84** | Leading | Developer tools | `p2.freshness` · `p3.video` · `p2.question-intent` |
| 20 | netlify.com | **83** | Leading | Cloud & DevOps | `p2.named-author` · `p2.answer-passages` · `p2.freshness` |
| 21 | upstash.com | **83** | Leading | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p3.video` |
| 22 | worldfirst.com | **83** | Leading | Cross-border services | `p1.page-type` · `p3.sameas` · `p2.named-author` |
| 23 | trigger.dev | **83** | Leading | Developer tools | `p3.knowledge-graph` · `p3.video` · `p3.sameas` |
| 24 | intercom.com | **83** | Leading | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 25 | kpmg.com | **83** | Leading | Professional services | `p3.sameas` · `p2.named-author` · `p2.freshness` |
| 26 | render.com | **81** | Solid | Cloud & DevOps | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 27 | planetscale.com | **81** | Solid | Developer tools | `p3.knowledge-graph` · `p2.named-author` · `p2.answer-passages` |
| 28 | teladochealth.com | **81** | Solid | Healthcare | `p2.freshness` · `p1.llms-txt` · `p2.named-author` |
| 29 | kuka.com | **81** | Solid | Manufacturing / Industrial | `p1.llms-txt` · `p2.named-author` · `p2.question-intent` |
| 30 | pinecone.io | **80** | Solid | AI | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 31 | baseus.com | **80** | Solid | China / consumer | `p3.knowledge-graph` · `p3.sameas` · `p2.named-author` |
| 32 | sentry.io | **80** | Solid | Cloud & DevOps | `p2.freshness` · `p2.named-author` · `p1.organization` |
| 33 | nextjs.org | **80** | Solid | Developer tools | `p3.video` · `p2.named-author` · `p1.breadcrumb` |
| 34 | cursor.com | **79** | Solid | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 35 | cloudflare.com | **79** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.video` |
| 36 | neon.com | **79** | Solid | Developer tools | `p2.freshness` · `p2.named-author` · `p1.organization` |
| 37 | woocommerce.com | **79** | Solid | Ecommerce | `p3.video` · `p2.named-author` · `p2.freshness` |
| 38 | beehiiv.com | **79** | Solid | Marketing / CRM | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 39 | buttondown.com | **79** | Solid | Marketing / CRM | `p2.sourced-stats` · `p3.video` · `p2.freshness` |
| 40 | ideogram.ai | **78** | Solid | AI | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 41 | junglescout.com | **78** | Solid | Cross-border services | `p1.llms-txt` · `p1.page-type` · `p3.sameas` |
| 42 | edx.org | **78** | Solid | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 43 | productboard.com | **78** | Solid | SaaS / Productivity | `p2.answer-passages` · `p2.named-author` · `p1.organization` |
| 44 | mistral.ai | **77** | Solid | AI | `p2.answer-passages` · `p3.knowledge-graph` · `p2.named-author` |
| 45 | tcl.com | **77** | Solid | China / consumer | `p1.llms-txt` · `p3.sameas` · `p2.named-author` |
| 46 | grafana.com | **77** | Solid | Cloud & DevOps | `p3.knowledge-graph` · `p3.sameas` · `p2.named-author` |
| 47 | supabase.com | **77** | Solid | Developer tools | `p2.answer-passages` · `p3.knowledge-graph` · `p2.named-author` |
| 48 | tanstack.com | **77** | Solid | Developer tools | `p2.answer-passages` · `p3.knowledge-graph` · `p2.freshness` |
| 49 | ghost.org | **77** | Solid | Marketing / CRM | `p1.llms-txt` · `p3.sameas` · `p2.freshness` |
| 50 | moz.com | **77** | Solid | Marketing / CRM | `p1.llms-txt` · `p1.page-type` · `p1.organization` |
| 51 | calendly.com | **77** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 52 | deepmind.google | **76** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 53 | suno.com | **76** | Solid | AI | `p3.knowledge-graph` · `p2.named-author` · `p1.breadcrumb` |
| 54 | anker.com | **76** | Solid | China / consumer | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 55 | helium10.com | **76** | Solid | Cross-border services | `p2.answer-passages` · `p1.llms-txt` · `p3.knowledge-graph` |
| 56 | klaviyo.com | **76** | Solid | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p4.answer-shape` |
| 57 | docusign.com | **76** | Solid | Professional services | `p2.answer-passages` · `p1.llms-txt` · `p2.named-author` |
| 58 | typeform.com | **76** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 59 | modal.com | **74** | Solid | AI | `p1.sitemap` · `p1.page-type` · `p3.sameas` |
| 60 | unisound.com | **74** | Solid | China / AI | `p2.question-intent` · `p3.video` · `p3.sameas` |
| 61 | twilio.com | **74** | Solid | Cloud & DevOps | `p2.named-author` · `p2.freshness` · `p1.page-type` |
| 62 | inngest.com | **74** | Solid | Developer tools | `p2.freshness` · `p3.knowledge-graph` · `p2.question-intent` |
| 63 | squarespace.com | **74** | Solid | Ecommerce | `p2.answer-passages` · `p3.video` · `p2.named-author` |
| 64 | webflow.com | **74** | Solid | Ecommerce | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 65 | brilliant.org | **74** | Solid | Education | `p1.organization` · `p3.video` · `p3.sameas` |
| 66 | flexport.com | **74** | Solid | Logistics / Freight | `p2.freshness` · `p1.llms-txt` · `p3.video` |
| 67 | braze.com | **74** | Solid | Marketing / CRM | `p3.video` · `p3.sameas` · `p2.named-author` |
| 68 | plausible.io | **74** | Solid | Marketing / CRM | `p1.llms-txt` · `p3.video` · `p3.sameas` |
| 69 | checkout.com | **74** | Solid | Payments / Fintech | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 70 | monday.com | **74** | Solid | SaaS / Productivity | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 71 | crewai.com | **73** | Solid | AI | `p2.question-intent` · `p1.page-type` · `p2.named-author` |
| 72 | duckdb.org | **73** | Solid | Cloud & DevOps | `p2.question-intent` · `p3.sameas` · `p2.named-author` |
| 73 | railway.com | **73** | Solid | Developer tools | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 74 | fathom.ai | **73** | Solid | Marketing / CRM | `p2.freshness` · `p1.organization` · `p3.video` |
| 75 | brex.com | **73** | Solid | Payments / Fintech | `p3.sameas` · `p2.named-author` · `p2.freshness` |
| 76 | clickhouse.com | **72** | Solid | Cloud & DevOps | `p3.knowledge-graph` · `p3.video` · `p3.sameas` |
| 77 | prefect.io | **72** | Solid | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 78 | arstechnica.com | **72** | Solid | Media / Publishing | `p1.llms-txt` · `p2.question-intent` · `p3.sameas` |
| 79 | ey.com | **72** | Solid | Professional services | `p1.llms-txt` · `p3.sameas` · `p2.named-author` |
| 80 | tencent.com | **71** | Solid | China / enterprise | `p1.llms-txt` · `p2.question-intent` · `p1.page-type` |
| 81 | dagster.io | **71** | Solid | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p1.page-type` |
| 82 | temporal.io | **71** | Solid | Cloud & DevOps | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 83 | airwallex.com | **71** | Solid | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.page-type` |
| 84 | fireworks.ai | **70** | Solid | AI | `p1.llms-txt` · `p3.knowledge-graph` · `p2.named-author` |
| 85 | prisma.io | **70** | Solid | Developer tools | `p2.freshness` · `p2.question-intent` · `p1.page-type` |
| 86 | nhs.uk | **70** | Solid | Healthcare | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 87 | hubspot.com | **70** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 88 | accenture.com | **70** | Solid | Professional services | `p1.llms-txt` · `p2.named-author` · `p2.freshness` |
| 89 | cal.com | **70** | Solid | SaaS / Productivity | `p2.answer-passages` · `p3.sameas` · `p2.named-author` |
| 90 | shopify.com | **69** | Solid | Ecommerce | `p2.answer-passages` · `p3.knowledge-graph` · `p1.page-type` |
| 91 | shoplazza.com | **69** | Solid | Ecommerce | `p1.organization` · `p3.knowledge-graph` · `p3.sameas` |
| 92 | coursera.org | **69** | Solid | Education | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 93 | semrush.com | **69** | Solid | Marketing / CRM | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 94 | wired.com | **69** | Solid | Media / Publishing | `p1.llms-txt` · `p3.sameas` · `p2.named-author` |
| 95 | ramp.com | **69** | Solid | Payments / Fintech | `p1.llms-txt` · `p3.video` · `p3.sameas` |
| 96 | stripe.com | **69** | Solid | Payments / Fintech | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 97 | asana.com | **69** | Solid | SaaS / Productivity | `p2.freshness` · `p2.question-intent` · `p2.named-author` |
| 98 | linear.app | **69** | Solid | SaaS / Productivity | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 99 | vuejs.org | **68** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.video` |
| 100 | pika.art | **67** | Solid | AI | `p2.freshness` · `p2.named-author` · `p1.organization` |
| 101 | kingdee.com | **67** | Solid | China / enterprise | `p2.named-author` · `p3.knowledge-graph` · `p2.question-intent` |
| 102 | xtransfer.com | **67** | Solid | Cross-border services | `p2.freshness` · `p2.answer-passages` · `p2.sourced-stats` |
| 103 | deno.com | **67** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 104 | attio.com | **67** | Solid | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p2.named-author` |
| 105 | baseten.co | **66** | Solid | AI | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 106 | langfuse.com | **66** | Solid | AI | `p1.organization` · `p3.knowledge-graph` · `p1.page-type` |
| 107 | replicate.com | **66** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.video` |
| 108 | materialize.com | **65** | Growing | Cloud & DevOps | `p2.freshness` · `p2.answer-passages` · `p1.page-type` |
| 109 | svelte.dev | **65** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 110 | siemens.com | **65** | Growing | Manufacturing / Industrial | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 111 | oclean.com | **64** | Growing | China / consumer | `p1.organization` · `p2.sourced-stats` · `p3.sameas` |
| 112 | porter.run | **64** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p3.video` |
| 113 | panda-css.com | **63** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 114 | vitest.dev | **63** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 115 | adyen.com | **63** | Growing | Payments / Fintech | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 116 | klarna.com | **63** | Growing | Payments / Fintech | `p2.freshness` · `p1.organization` · `p3.video` |
| 117 | langchain.com | **62** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 118 | m19.com | **62** | Growing | Cross-border services | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 119 | bigcommerce.com | **62** | Growing | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 120 | dsv.com | **62** | Growing | Logistics / Freight | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 121 | deloitte.com | **62** | Growing | Professional services | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 122 | alibabagroup.com | **61** | Growing | China / enterprise | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 123 | elysiajs.com | **61** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 124 | aider.chat | **60** | Growing | AI | `p1.organization` · `p1.llms-txt` · `p3.sameas` |
| 125 | browserbase.com | **60** | Growing | AI | `p2.named-author` · `p2.answer-passages` · `p3.knowledge-graph` |
| 126 | mingdao.com | **60** | Growing | China / no-code | `p2.freshness` · `p2.answer-passages` · `p2.question-intent` |
| 127 | tigerbeetle.com | **60** | Growing | Cloud & DevOps | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 128 | tigerdata.com | **60** | Growing | Cloud & DevOps | `p2.answer-passages` · `p3.knowledge-graph` · `p3.sameas` |
| 129 | marqeta.com | **60** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 130 | notion.com | **60** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 131 | raycast.com | **60** | Growing | SaaS / Productivity | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 132 | klook.com | **60** | Growing | Travel | `p2.freshness` · `p1.organization` · `p2.sourced-stats` |
| 133 | anthropic.com | **59** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 134 | govee.com | **59** | Growing | China / consumer | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 135 | astro.build | **59** | Growing | Developer tools | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 136 | vite.dev | **59** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p3.knowledge-graph` |
| 137 | wix.com | **59** | Growing | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 138 | kuehne-nagel.com | **59** | Growing | Logistics / Freight | `p2.freshness` · `p1.llms-txt` · `p3.knowledge-graph` |
| 139 | superhuman.com | **59** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 140 | trip.com | **59** | Growing | Travel | `p2.freshness` · `p2.answer-passages` · `p2.question-intent` |
| 141 | creality.com | **58** | Growing | China / consumer | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 142 | datadoghq.com | **58** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 143 | zod.dev | **58** | Growing | Developer tools | `p1.organization` · `p2.answer-passages` · `p2.question-intent` |
| 144 | skillshare.com | **58** | Growing | Education | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 145 | ro.co | **58** | Growing | Healthcare | `p2.answer-passages` · `p1.llms-txt` · `p3.video` |
| 146 | zocdoc.com | **58** | Growing | Healthcare | `p2.freshness` · `p1.llms-txt` · `p2.sourced-stats` |
| 147 | mailchimp.com | **58** | Growing | Marketing / CRM | `p2.freshness` · `p1.organization` · `p2.sourced-stats` |
| 148 | thomsonreuters.com | **58** | Growing | Professional services | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 149 | codecademy.com | **57** | Growing | Education | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 150 | pluralsight.com | **57** | Growing | Education | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 151 | customer.io | **57** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p3.knowledge-graph` |
| 152 | smashingmagazine.com | **57** | Growing | Media / Publishing | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 153 | wise.com | **57** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 154 | readwise.io | **57** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 155 | moonshot.cn | **56** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 156 | ucloud.cn | **56** | Growing | China / cloud | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 157 | betterstack.com | **56** | Growing | Cloud & DevOps | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 158 | koyeb.com | **56** | Growing | Cloud & DevOps | `p1.organization` · `p1.llms-txt` · `p3.knowledge-graph` |
| 159 | hono.dev | **56** | Growing | Developer tools | `p1.organization` · `p2.sourced-stats` · `p1.sitemap` |
| 160 | nitro.build | **56** | Growing | Developer tools | `p1.organization` · `p2.question-intent` · `p1.sitemap` |
| 161 | orm.drizzle.team | **56** | Growing | Developer tools | `p2.question-intent` · `p1.organization` · `p2.sourced-stats` |
| 162 | valibot.dev | **56** | Growing | Developer tools | `p2.named-author` · `p1.organization` · `p3.knowledge-graph` |
| 163 | miro.com | **56** | Growing | SaaS / Productivity | `p2.sourced-stats` · `p2.named-author` · `p2.freshness` |
| 164 | digitalocean.com | **55** | Growing | Cloud & DevOps | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 165 | effect.website | **55** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 166 | qwik.dev | **55** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 167 | posthog.com | **55** | Growing | Marketing / CRM | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 168 | plaid.com | **55** | Growing | Payments / Fintech | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 169 | tability.io | **55** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 170 | ecoflow.com | **54** | Growing | China / consumer | `p2.answer-passages` · `p1.llms-txt` · `p1.sitemap` |
| 171 | deepseek.com | **53** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 172 | siliconflow.cn | **53** | Growing | China / AI | `p2.named-author` · `p1.organization` · `p3.knowledge-graph` |
| 173 | remix.run | **53** | Growing | Developer tools | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 174 | pragprog.com | **53** | Growing | Education | `p1.organization` · `p1.llms-txt` · `p3.knowledge-graph` |
| 175 | rockwellautomation.com | **53** | Growing | Manufacturing / Industrial | `p2.answer-passages` · `p2.freshness` · `p2.sourced-stats` |
| 176 | ahrefs.com | **53** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 177 | mercury.com | **53** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 178 | vevor.com | **52** | Growing | China / consumer | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 179 | hioscar.com | **52** | Growing | Healthcare | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 180 | arc.net | **52** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 181 | groq.com | **51** | Growing | AI | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 182 | llamaindex.ai | **51** | Growing | AI | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 183 | unocss.dev | **51** | Growing | Developer tools | `p1.organization` · `p3.knowledge-graph` · `p2.question-intent` |
| 184 | fanuc.co.jp | **51** | Growing | Manufacturing / Industrial | `p2.answer-passages` · `p2.named-author` · `p1.organization` |
| 185 | qiniu.com | **50** | Early | China / cloud | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 186 | dianxiaomi.com | **50** | Early | Cross-border services | `p2.question-intent` · `p2.named-author` · `p2.answer-passages` |
| 187 | tailwindcss.com | **50** | Early | Developer tools | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 188 | who.int | **50** | Early | Healthcare | `p2.freshness` · `p1.llms-txt` · `p3.knowledge-graph` |
| 189 | simonwillison.net | **50** | Early | Media / Publishing | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 190 | biomejs.dev | **49** | Early | Developer tools | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 191 | roadmap.sh | **49** | Early | Education | `p2.sourced-stats` · `p2.freshness` · `p1.organization` |
| 192 | coda.io | **49** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 193 | sensetime.com | **48** | Early | China / AI | `p2.named-author` · `p1.llms-txt` · `p3.knowledge-graph` |
| 194 | huaweicloud.com | **48** | Early | China / cloud | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 195 | jiandaoyun.com | **48** | Early | China / no-code | `p2.named-author` · `p1.llms-txt` · `p3.knowledge-graph` |
| 196 | doximity.com | **48** | Early | Healthcare | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 197 | bytedance.com | **47** | Early | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 198 | huawei.com | **47** | Early | China / enterprise | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 199 | vika.cn | **46** | Early | China / no-code | `p2.sourced-stats` · `p2.named-author` · `p1.llms-txt` |
| 200 | zhipuai.cn | **45** | Early | China / AI | `p2.answer-passages` · `p2.question-intent` · `p1.organization` |
| 201 | seeyon.com | **45** | Early | China / enterprise | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 202 | teambition.com | **45** | Early | China / no-code | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 203 | huggingface.co | **44** | Early | AI | `p2.named-author` · `p1.organization` · `p2.answer-passages` |
| 204 | lazada.com | **44** | Early | China / consumer | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 205 | yonyou.com | **43** | Early | China / enterprise | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 206 | jtexpress.com | **43** | Early | Logistics / Freight | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 207 | yunexpress.com | **43** | Early | Logistics / Freight | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 208 | pingpongx.com | **42** | Early | Cross-border services | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 209 | fedex.com | **41** | Early | Logistics / Freight | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 210 | cohere.com | **40** | Early | AI | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 211 | continue.dev | **40** | Early | AI | `p2.freshness` · `p1.llms-txt` · `g.ssr` |
| 212 | together.ai | **40** | Early | AI | `p2.answer-passages` · `g.robots` · `p3.video` |
| 213 | weaviate.io | **40** | Early | AI | `g.ssr` · `p2.named-author` · `p2.freshness` |
| 214 | windsurf.com | **40** | Early | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 215 | 01.ai | **40** | Early | China / AI | `p2.freshness` · `p1.organization` · `g.ssr` |
| 216 | iflytek.com | **40** | Early | China / AI | `p2.question-intent` · `p2.freshness` · `p2.answer-passages` |
| 217 | temu.com | **40** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 218 | clickpaas.com | **40** | Early | China / no-code | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 219 | datahawk.co | **40** | Early | Cross-border services | `p2.answer-passages` · `p1.llms-txt` · `g.ssr` |
| 220 | sellersprite.com | **40** | Early | Cross-border services | `p2.answer-passages` · `g.ssr` · `p3.knowledge-graph` |
| 221 | turso.tech | **40** | Early | Developer tools | `p2.named-author` · `p2.answer-passages` · `g.ssr` |
| 222 | ebay.com | **40** | Early | Ecommerce | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 223 | rakuten.com | **40** | Early | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 224 | walmart.com | **40** | Early | Ecommerce | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 225 | nostarch.com | **40** | Early | Education | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 226 | clevelandclinic.org | **40** | Early | Healthcare | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 227 | drugs.com | **40** | Early | Healthcare | `p1.llms-txt` · `g.reachable` · `p2.question-intent` |
| 228 | healthline.com | **40** | Early | Healthcare | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 229 | webmd.com | **40** | Early | Healthcare | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 230 | expeditors.com | **40** | Early | Logistics / Freight | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 231 | maersk.com | **40** | Early | Logistics / Freight | `p2.freshness` · `g.reachable` · `p3.knowledge-graph` |
| 232 | honeywell.com | **40** | Early | Manufacturing / Industrial | `p2.answer-passages` · `p1.llms-txt` · `g.reachable` |
| 233 | css-tricks.com | **40** | Early | Media / Publishing | `g.reachable` · `p1.sitemap` · `p2.named-author` |
| 234 | stackoverflow.blog | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 235 | stratechery.com | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.reachable` |
| 236 | techcrunch.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p2.question-intent` |
| 237 | theregister.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p3.video` |
| 238 | theverge.com | **40** | Early | Media / Publishing | `p2.answer-passages` · `p1.llms-txt` · `g.robots` |
| 239 | payoneer.com | **40** | Early | Payments / Fintech | `g.robots` · `g.reachable` · `p1.page-type` |
| 240 | lexisnexis.com | **40** | Early | Professional services | `p2.freshness` · `p1.llms-txt` · `g.robots` |
| 241 | pwc.com | **40** | Early | Professional services | `p2.answer-passages` · `p1.llms-txt` · `g.ssr` |
| 242 | airtable.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 243 | figma.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 244 | loom.com | **40** | Early | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 245 | obsidian.md | **40** | Early | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 246 | slack.com | **40** | Early | SaaS / Productivity | `p2.freshness` · `p1.organization` · `g.reachable` |
| 247 | hilton.com | **40** | Early | Travel | `p2.freshness` · `p1.llms-txt` · `g.reachable` |
| 248 | lonelyplanet.com | **40** | Early | Travel | `p1.llms-txt` · `g.robots` · `p2.sourced-stats` |
| 249 | marriott.com | **40** | Early | Travel | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 250 | jdcloud.com | **39** | Early | China / cloud | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 251 | tapd.cn | **39** | Early | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 252 | shopee.com | **39** | Early | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 253 | weichai.com | **39** | Early | Manufacturing / Industrial | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 254 | dji.com | **38** | Early | China / consumer | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 255 | wiseasy.com | **38** | Early | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 256 | haier.com | **38** | Early | Manufacturing / Industrial | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 257 | upyun.com | **37** | Early | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 258 | radix-ui.com | **37** | Early | Developer tools | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 259 | xiaomi.com | **36** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 260 | huoban.com | **36** | Early | China / no-code | `p2.named-author` · `p1.organization` · `p2.answer-passages` |
| 261 | mabangerp.com | **36** | Early | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 262 | tongtool.com | **36** | Early | Cross-border services | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 263 | trendyol.com | **36** | Early | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 264 | abb.com | **36** | Early | Manufacturing / Industrial | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 265 | perpetua.io | **35** | Early | Cross-border services | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 266 | oceanpayment.com | **34** | Early | Cross-border services | `p2.sourced-stats` · `p2.named-author` · `p2.freshness` |
| 267 | airbnb.com | **34** | Early | Travel | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 268 | solidjs.com | **33** | Early | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 269 | midea.com | **33** | Early | Manufacturing / Industrial | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 270 | june.so | **33** | Early | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 271 | shadcn.com | **31** | Early | Developer tools | `p2.question-intent` · `p2.freshness` · `p1.organization` |
| 272 | ctyun.cn | **30** | Not started | China / cloud | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 273 | volcengine.com | **30** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 274 | hisense.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 275 | miniso.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 276 | narwal.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 277 | dingtalk.com | **30** | Not started | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 278 | payoneer.cn | **30** | Not started | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 279 | yuncang.com | **30** | Not started | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 280 | drizzle.team | **30** | Not started | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 281 | duolingo.com | **30** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 282 | skyscanner.net | **30** | Not started | Travel | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 283 | lenovo.com | **29** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 284 | roborock.com | **29** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 285 | yunzhijia.com | **29** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 286 | khanacademy.org | **29** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 287 | gree.com | **29** | Not started | Manufacturing / Industrial | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 288 | dreame.tech | **28** | Not started | China / consumer | `p2.answer-passages` · `p2.sourced-stats` · `p2.question-intent` |
| 289 | ueeshop.com | **28** | Not started | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 290 | megvii.com | **27** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 291 | aliexpress.com | **27** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 292 | agoda.com | **27** | Not started | Travel | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 293 | bigmodel.cn | **26** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 294 | xcmg.com | **26** | Not started | Manufacturing / Industrial | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 295 | aliwork.com | **25** | Not started | China / no-code | `p2.answer-passages` · `p2.sourced-stats` · `p2.question-intent` |
| 296 | jushuitan.com | **25** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 297 | oceanwing.com | **24** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 298 | freecodecamp.org | **23** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 299 | qcloud.com | **22** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 300 | shein.com | **21** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 301 | feishu.cn | **20** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 302 | fanruan.com | **18** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 303 | yuque.com | **18** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 304 | booking.com | **18** | Not started | Travel | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 305 | baichuan-ai.com | **16** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 306 | aliyun.com | **16** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 307 | wps.cn | **16** | Not started | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 308 | sf-express.com | **14** | Not started | Logistics / Freight | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 309 | stepfun.com | **13** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 310 | lianlianpay.com | **13** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 311 | 4px.com | **13** | Not started | Logistics / Freight | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 312 | keepa.com | **12** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 313 | amazon.com | **12** | Not started | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 314 | mercadolibre.com | **12** | Not started | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |

### Not scored

- **midjourney.com** — could not fetch https://www.midjourney.com — <urlopen error [SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol ver
- **openai.com** — could not fetch https://www.openai.com — all requests returned 403
- **perplexity.ai** — could not fetch https://www.perplexity.ai — all requests returned 403
- **baidubce.com** — could not fetch https://www.baidubce.com — <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>
- **aosom.com** — could not fetch https://www.aosom.com — all requests returned 403
- **bambulab.com** — could not fetch https://www.bambulab.com — all requests returned 403
- **cider.com** — could not fetch https://www.cider.com — <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostn
- **clubfactory.com** — unknown url type: '/sitemap.xml'
- **cubiitek.com** — could not fetch https://www.cubiitek.com — <urlopen error _ssl.c:1112: The handshake operation timed out>
- **elegoo.com** — could not fetch https://www.elegoo.com — all requests returned 429
- **hiwonder.com** — could not fetch https://www.hiwonder.com — all requests returned 429
- **insta360.com** — could not fetch https://www.insta360.com — all requests returned 403
- **laifen.com** — could not fetch https://www.laifen.com — <urlopen error _ssl.c:1112: The handshake operation timed out>
- **sonoff.tech** — could not fetch https://www.sonoff.tech — all requests returned 429
- **ugreen.com** — could not fetch https://www.ugreen.com — all requests returned 429
- **treelab.com.cn** — could not fetch https://www.treelab.com.cn — <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>
- **hashicorp.com** — could not fetch https://www.hashicorp.com — all requests returned 429
- **aftership.com** — could not fetch https://www.aftership.com — all requests returned 403
- **allegro.pl** — could not fetch https://www.allegro.pl — all requests returned 403
- **coupang.com** — could not fetch https://www.coupang.com — all requests returned 403
- **etsy.com** — could not fetch https://www.etsy.com — all requests returned 403
- **jumia.com** — could not fetch https://www.jumia.com — all requests returned 403
- **noon.com** — could not fetch https://www.noon.com — The read operation timed out
- **ozon.ru** — could not fetch https://www.ozon.ru — all requests returned 307
- **shopline.com** — could not fetch https://www.shopline.com — all requests returned 403
- **wildberries.ru** — could not fetch https://www.wildberries.ru — all requests returned 498
- **chegg.com** — could not fetch https://www.chegg.com — all requests returned 403
- **datacamp.com** — could not fetch https://www.datacamp.com — all requests returned 403
- **exercism.org** — could not fetch https://www.exercism.org — all requests returned 403
- **udemy.com** — could not fetch https://www.udemy.com — all requests returned 403
- **hims.com** — could not fetch https://www.hims.com — all requests returned 403
- **mayoclinic.org** — could not fetch https://www.mayoclinic.org — all requests returned 403
- **medlineplus.gov** — could not fetch https://www.medlineplus.gov — <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>
- **nih.gov** — could not fetch https://www.nih.gov — <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>
- **cma-cgm.com** — could not fetch https://www.cma-cgm.com — all requests returned 403
- **dhl.com** — could not fetch https://www.dhl.com — The read operation timed out
- **hapag-lloyd.com** — could not fetch https://www.hapag-lloyd.com — all requests returned 403
- **ups.com** — could not fetch https://www.ups.com — The read operation timed out
- **ge.com** — could not fetch https://www.ge.com — <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>
- **sany.com** — could not fetch https://www.sany.com — <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self s
- **se.com** — could not fetch https://www.se.com — all requests returned 403
- **hackaday.com** — could not fetch https://www.hackaday.com — all requests returned 502
- **lwn.net** — could not fetch https://www.lwn.net — all requests returned 429
- **phoronix.com** — could not fetch https://www.phoronix.com — all requests returned 403
- **theinformation.com** — could not fetch https://www.theinformation.com — all requests returned 403
- **revolut.com** — could not fetch https://www.revolut.com — all requests returned 403
- **bcg.com** — could not fetch https://www.bcg.com — all requests returned 403
- **clio.com** — could not fetch https://www.clio.com — all requests returned 403
- **mckinsey.com** — could not fetch https://www.mckinsey.com — The read operation timed out
- **height.app** — could not fetch https://www.height.app — <urlopen error _ssl.c:1112: The handshake operation timed out>
- **delta.com** — could not fetch https://www.delta.com — <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>
- **expedia.com** — could not fetch https://www.expedia.com — all requests returned 429
- **getyourguide.com** — could not fetch https://www.getyourguide.com — all requests returned 403
- **tripadvisor.com** — could not fetch https://www.tripadvisor.com — all requests returned 403
- **united.com** — could not fetch https://www.united.com — The read operation timed out
- **viator.com** — could not fetch https://www.viator.com — all requests returned 403

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

