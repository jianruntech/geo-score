# The state of AI visibility

Every site below scored with the same open rubric, the same public tool and the same
eight-page sample. No private data, no vendor dashboards — [re-run it yourself](run.py).

**229 sites · median 57 · mean 56.6 · upper quartile 72.0 · range 7–98** · rubric v1.1 · measured 2026-09-09

## A quarter of the field cannot be cited at all

**54 of 229 sites have a gate check at zero** — a crawler cannot get the content, so
nothing else on the page matters. These are two very different problems, and reporting
them as one number is what makes such a number useless:

| Why | Sites | Which |
|---|:-:|---|
| **Deliberate** — `robots.txt` disallows retrieval crawlers | 14 | amazon.com, figma.com, healthline.com, june.so, khanacademy.org, loom.com, mercadolibre.com, payoneer.com, qcloud.com, stackoverflow.blog, techcrunch.com, theregister.com, theverge.com, webmd.com |
| **Deliberate or accidental** — the server returns 403 to crawlers | 9 | airbnb.com, css-tricks.com, ebay.com, ecoflow.com, keepa.com, lenovo.com, nostarch.com, stratechery.com, xiaomi.com |
| **Accidental** — body copy only exists after JS runs | 31 | 01.ai, airtable.com, aliexpress.com, baichuan-ai.com, bigmodel.cn, booking.com, cohere.com, continue.dev, datahawk.co, drizzle.team, feishu.cn, freecodecamp.org, huggingface.co, jushuitan.com, lianlianpay.com, narwal.com, obsidian.md, oceanwing.com, payoneer.cn, rakuten.com, sellersprite.com, shein.com, shopee.com, solidjs.com, stepfun.com, temu.com, turso.tech, walmart.com, weaviate.io, windsurf.com, yuque.com |

The first group made a choice. Several news and health publishers block AI crawlers by
name, and this rubric reports that as it is — a site that does not want to be quoted is
not misconfigured. The last group almost certainly did not choose it: their content is
there, a browser can see it, and a retrieval crawler gets an empty shell.

## What the spread shows

**Half the field sits between 40.0 and 72.0.** The rubric is not grading on a curve — these
are the scores that fall out of it, and they are consistent with the public benchmarks
it was [calibrated against](../rubric/calibration-v1.1.md).

**Sites built for the Chinese market score 16 points lower** — median 44 against 60.0
for everyone else. The gap is not content quality. It is `llms.txt`, `Organization`
schema, visible dates and bylines — conventions that spread through the English web
first and have not yet crossed over.

**The same few things are missing almost everywhere.** Counting only each site's three
largest gaps:

| Missing | Sites | What it costs |
|---|:-:|:-:|
| `p2.answer-passages` | 117 of 229 | 9 pts |
| `p2.freshness` | 108 of 229 | 6 pts |
| `p2.named-author` | 105 of 229 | 6 pts |
| `p1.organization` | 81 of 229 | 6 pts |
| `p2.question-intent` | 61 of 229 | 7 pts |
| `p1.llms-txt` | 54 of 229 | 5 pts |

None of the top three is expensive. A date in a page template, an opening paragraph
that stands on its own, and one JSON-LD block are between them worth more than any
single pillar on this list.

## By sector

| Sector | Sites | Median |
|---|:-:|:-:|
| Cloud & DevOps | 24 | **71.0** |
| Marketing / CRM | 17 | **67** |
| AI | 28 | **66.5** |
| Payments / Fintech | 7 | **65** |
| Developer tools | 37 | **61** |
| SaaS / Productivity | 22 | **59.5** |
| Ecommerce | 13 | **59** |
| China / enterprise | 6 | **54.0** |
| China / AI | 9 | **48** |
| China / no-code | 5 | **44** |
| Education | 6 | **42.0** |
| Cross-border services | 17 | **40** |
| Healthcare | 2 | **40.0** |
| Media / Publishing | 11 | **40** |
| China / consumer | 20 | **38.5** |
| China / cloud | 3 | **33** |
| Travel | 2 | **26.0** |

## Every site

| # | Site | Score | Band | Sector | Biggest gaps |
|:-:|---|:-:|---|---|---|
| 1 | pulumi.com | **98** | Leading | Cloud & DevOps | `g.robots` · `p3.video` · `p3.sameas` |
| 2 | minimaxi.com | **95** | Leading | China / AI | `p2.question-intent` · `p4.cn-engines` · `p3.video` |
| 3 | resend.com | **94** | Leading | Developer tools | `p2.freshness` · `p2.answer-passages` · `p3.video` |
| 4 | lumalabs.ai | **93** | Leading | AI | `p2.question-intent` · `g.reachable` · `p3.sameas` |
| 5 | zapier.com | **92** | Leading | SaaS / Productivity | `p2.freshness` · `p2.named-author` · `p3.sameas` |
| 6 | bun.sh | **88** | Leading | Developer tools | `p2.freshness` · `p2.question-intent` · `p2.answer-passages` |
| 7 | prisma.io | **87** | Leading | Developer tools | `p2.question-intent` · `p3.video` · `p2.freshness` |
| 8 | trigger.dev | **87** | Leading | Developer tools | `p3.video` · `p3.sameas` · `p2.named-author` |
| 9 | clickup.com | **87** | Leading | SaaS / Productivity | `p3.video` · `p2.freshness` · `p2.answer-passages` |
| 10 | netlify.com | **85** | Leading | Cloud & DevOps | `p2.named-author` · `p2.answer-passages` · `p2.freshness` |
| 11 | twilio.com | **85** | Leading | Cloud & DevOps | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 12 | clerk.com | **85** | Leading | Developer tools | `p2.sourced-stats` · `p2.answer-passages` · `p1.sitemap` |
| 13 | planetscale.com | **85** | Leading | Developer tools | `p2.named-author` · `p2.answer-passages` · `p1.page-type` |
| 14 | vercel.com | **84** | Leading | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 15 | fly.io | **84** | Leading | Developer tools | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 16 | nuxt.com | **84** | Leading | Developer tools | `p2.freshness` · `p3.video` · `p2.question-intent` |
| 17 | axiom.co | **83** | Leading | Cloud & DevOps | `p2.freshness` · `p3.video` · `p2.named-author` |
| 18 | upstash.com | **83** | Leading | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p3.video` |
| 19 | ideogram.ai | **82** | Solid | AI | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 20 | mistral.ai | **81** | Solid | AI | `p2.answer-passages` · `p2.named-author` · `p1.breadcrumb` |
| 21 | cloudflare.com | **81** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.video` |
| 22 | render.com | **81** | Solid | Cloud & DevOps | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 23 | supabase.com | **81** | Solid | Developer tools | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 24 | intercom.com | **81** | Solid | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 25 | sentry.io | **80** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 26 | nextjs.org | **80** | Solid | Developer tools | `p3.video` · `p2.named-author` · `p1.breadcrumb` |
| 27 | cursor.com | **79** | Solid | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 28 | elevenlabs.io | **79** | Solid | AI | `p2.answer-passages` · `p3.knowledge-graph` · `p2.named-author` |
| 29 | suno.com | **79** | Solid | AI | `p2.named-author` · `p1.breadcrumb` · `p4.answer-shape` |
| 30 | helium10.com | **79** | Solid | Cross-border services | `p2.answer-passages` · `p1.llms-txt` · `p2.named-author` |
| 31 | woocommerce.com | **79** | Solid | Ecommerce | `p3.video` · `p2.named-author` · `p2.freshness` |
| 32 | buttondown.com | **79** | Solid | Marketing / CRM | `p2.sourced-stats` · `p3.video` · `p2.freshness` |
| 33 | typeform.com | **79** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 34 | baseus.com | **78** | Solid | China / consumer | `p3.knowledge-graph` · `p3.sameas` · `p2.named-author` |
| 35 | clickhouse.com | **78** | Solid | Cloud & DevOps | `p3.video` · `p3.sameas` · `p2.named-author` |
| 36 | calendly.com | **78** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 37 | junglescout.com | **77** | Solid | Cross-border services | `p1.llms-txt` · `p1.page-type` · `p3.sameas` |
| 38 | tanstack.com | **77** | Solid | Developer tools | `p2.answer-passages` · `p3.knowledge-graph` · `p2.freshness` |
| 39 | moz.com | **77** | Solid | Marketing / CRM | `p1.llms-txt` · `p1.page-type` · `p1.organization` |
| 40 | checkout.com | **77** | Solid | Payments / Fintech | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 41 | deepmind.google | **76** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 42 | tcl.com | **76** | Solid | China / consumer | `p1.llms-txt` · `p3.sameas` · `p2.named-author` |
| 43 | klaviyo.com | **76** | Solid | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p4.answer-shape` |
| 44 | fireworks.ai | **74** | Solid | AI | `p1.llms-txt` · `p2.named-author` · `p2.freshness` |
| 45 | modal.com | **74** | Solid | AI | `p1.sitemap` · `p1.page-type` · `p3.sameas` |
| 46 | together.ai | **74** | Solid | AI | `p2.answer-passages` · `p3.video` · `p2.named-author` |
| 47 | anker.com | **74** | Solid | China / consumer | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 48 | inngest.com | **74** | Solid | Developer tools | `p2.freshness` · `p3.knowledge-graph` · `p2.question-intent` |
| 49 | squarespace.com | **74** | Solid | Ecommerce | `p2.answer-passages` · `p3.video` · `p2.named-author` |
| 50 | webflow.com | **74** | Solid | Ecommerce | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 51 | beehiiv.com | **74** | Solid | Marketing / CRM | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 52 | plausible.io | **74** | Solid | Marketing / CRM | `p1.llms-txt` · `p3.video` · `p3.sameas` |
| 53 | crewai.com | **73** | Solid | AI | `p2.question-intent` · `p1.page-type` · `p2.named-author` |
| 54 | railway.com | **73** | Solid | Developer tools | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 55 | ghost.org | **73** | Solid | Marketing / CRM | `p1.llms-txt` · `p3.sameas` · `p2.freshness` |
| 56 | monday.com | **73** | Solid | SaaS / Productivity | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 57 | grafana.com | **72** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.sameas` |
| 58 | shopify.com | **72** | Solid | Ecommerce | `p2.answer-passages` · `p1.page-type` · `p2.named-author` |
| 59 | productboard.com | **72** | Solid | SaaS / Productivity | `p2.answer-passages` · `p1.page-type` · `p2.named-author` |
| 60 | kingdee.com | **71** | Solid | China / enterprise | `p2.named-author` · `p2.question-intent` · `p1.page-type` |
| 61 | tencent.com | **71** | Solid | China / enterprise | `p1.llms-txt` · `p2.question-intent` · `p1.page-type` |
| 62 | dagster.io | **71** | Solid | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p1.page-type` |
| 63 | prefect.io | **71** | Solid | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 64 | arstechnica.com | **71** | Solid | Media / Publishing | `p1.llms-txt` · `p2.question-intent` · `p3.sameas` |
| 65 | stripe.com | **71** | Solid | Payments / Fintech | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 66 | asana.com | **71** | Solid | SaaS / Productivity | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 67 | cal.com | **71** | Solid | SaaS / Productivity | `p2.answer-passages` · `p3.sameas` · `p2.named-author` |
| 68 | langfuse.com | **70** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 69 | temporal.io | **70** | Solid | Cloud & DevOps | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 70 | deno.com | **70** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 71 | hubspot.com | **70** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 72 | wired.com | **70** | Solid | Media / Publishing | `p2.answer-passages` · `p1.llms-txt` · `p3.sameas` |
| 73 | adyen.com | **70** | Solid | Payments / Fintech | `p2.freshness` · `p1.page-type` · `p3.video` |
| 74 | pinecone.io | **69** | Solid | AI | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 75 | shoplazza.com | **69** | Solid | Ecommerce | `p1.organization` · `p3.knowledge-graph` · `p3.sameas` |
| 76 | coursera.org | **69** | Solid | Education | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 77 | linear.app | **69** | Solid | SaaS / Productivity | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 78 | vuejs.org | **68** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.video` |
| 79 | openrouter.ai | **67** | Solid | AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 80 | bigcommerce.com | **67** | Solid | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 81 | attio.com | **67** | Solid | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p2.named-author` |
| 82 | semrush.com | **67** | Solid | Marketing / CRM | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 83 | replicate.com | **66** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.video` |
| 84 | duckdb.org | **66** | Solid | Cloud & DevOps | `p2.answer-passages` · `p3.video` · `p3.sameas` |
| 85 | motherduck.com | **66** | Solid | Cloud & DevOps | `p2.question-intent` · `p2.freshness` · `p3.knowledge-graph` |
| 86 | xtransfer.com | **66** | Solid | Cross-border services | `p2.freshness` · `p2.answer-passages` · `p2.sourced-stats` |
| 87 | svelte.dev | **66** | Solid | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 88 | airwallex.com | **65** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 89 | oclean.com | **64** | Growing | China / consumer | `p1.organization` · `p2.sourced-stats` · `p3.sameas` |
| 90 | porter.run | **64** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p3.video` |
| 91 | braze.com | **64** | Growing | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p3.video` |
| 92 | pika.art | **63** | Growing | AI | `p2.freshness` · `p3.knowledge-graph` · `p2.named-author` |
| 93 | panda-css.com | **63** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 94 | vitest.dev | **63** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 95 | alibabagroup.com | **61** | Growing | China / enterprise | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 96 | datadoghq.com | **61** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p1.page-type` |
| 97 | elysiajs.com | **61** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 98 | aider.chat | **60** | Growing | AI | `p1.organization` · `p1.llms-txt` · `p3.sameas` |
| 99 | browserbase.com | **60** | Growing | AI | `p2.named-author` · `p2.answer-passages` · `p3.knowledge-graph` |
| 100 | timescale.com | **60** | Growing | Cloud & DevOps | `p2.answer-passages` · `p3.knowledge-graph` · `p3.sameas` |
| 101 | m19.com | **60** | Growing | Cross-border services | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 102 | valibot.dev | **60** | Growing | Developer tools | `p2.named-author` · `p1.organization` · `p2.question-intent` |
| 103 | miro.com | **60** | Growing | SaaS / Productivity | `p2.named-author` · `p1.llms-txt` · `p3.sameas` |
| 104 | slack.com | **60** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 105 | langchain.com | **59** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 106 | govee.com | **59** | Growing | China / consumer | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 107 | astro.build | **59** | Growing | Developer tools | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 108 | wix.com | **59** | Growing | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 109 | hackaday.com | **59** | Growing | Media / Publishing | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 110 | notion.com | **59** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 111 | creality.com | **58** | Growing | China / consumer | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 112 | materialize.com | **58** | Growing | Cloud & DevOps | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 113 | zod.dev | **58** | Growing | Developer tools | `p1.organization` · `p2.answer-passages` · `p2.question-intent` |
| 114 | ahrefs.com | **58** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 115 | anthropic.com | **57** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 116 | mingdao.com | **57** | Growing | China / no-code | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 117 | posthog.com | **57** | Growing | Marketing / CRM | `p2.freshness` · `p2.answer-passages` · `p2.sourced-stats` |
| 118 | smashingmagazine.com | **57** | Growing | Media / Publishing | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 119 | raycast.com | **57** | Growing | SaaS / Productivity | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 120 | readwise.io | **57** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 121 | superhuman.com | **57** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 122 | tability.io | **57** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 123 | betterstack.com | **56** | Growing | Cloud & DevOps | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 124 | koyeb.com | **56** | Growing | Cloud & DevOps | `p1.organization` · `p1.llms-txt` · `p3.knowledge-graph` |
| 125 | tigerbeetle.com | **56** | Growing | Cloud & DevOps | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 126 | nitro.build | **56** | Growing | Developer tools | `p1.organization` · `p2.question-intent` · `p1.sitemap` |
| 127 | vitejs.dev | **56** | Growing | Developer tools | `p1.organization` · `p2.question-intent` · `p1.page-type` |
| 128 | pragprog.com | **56** | Growing | Education | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 129 | customer.io | **56** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p3.knowledge-graph` |
| 130 | mailchimp.com | **56** | Growing | Marketing / CRM | `p2.freshness` · `p1.organization` · `p2.sourced-stats` |
| 131 | fathom.video | **55** | Growing | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 132 | wise.com | **55** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 133 | deepseek.com | **54** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 134 | moonshot.cn | **54** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 135 | siliconflow.cn | **53** | Growing | China / AI | `p2.named-author` · `p1.organization` · `p3.knowledge-graph` |
| 136 | hono.dev | **53** | Growing | Developer tools | `p1.organization` · `p3.knowledge-graph` · `p2.sourced-stats` |
| 137 | digitalocean.com | **52** | Growing | Cloud & DevOps | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 138 | dianxiaomi.com | **52** | Growing | Cross-border services | `p2.question-intent` · `p2.named-author` · `p2.answer-passages` |
| 139 | effect.website | **52** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 140 | qwik.dev | **52** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 141 | tailwindcss.com | **52** | Growing | Developer tools | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 142 | arc.net | **52** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 143 | baseten.co | **51** | Growing | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 144 | remix.run | **51** | Growing | Developer tools | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 145 | unocss.dev | **51** | Growing | Developer tools | `p1.organization` · `p3.knowledge-graph` · `p2.question-intent` |
| 146 | vevor.com | **50** | Early | China / consumer | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 147 | simonwillison.net | **50** | Early | Media / Publishing | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 148 | plaid.com | **50** | Early | Payments / Fintech | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 149 | groq.com | **49** | Early | AI | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 150 | orm.drizzle.team | **49** | Early | Developer tools | `p2.question-intent` · `p1.organization` · `p3.knowledge-graph` |
| 151 | zhipuai.cn | **48** | Early | China / AI | `p2.answer-passages` · `p2.question-intent` · `p1.organization` |
| 152 | radix-ui.com | **48** | Early | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 153 | bytedance.com | **47** | Early | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 154 | llamaindex.ai | **46** | Early | AI | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 155 | aliyun.com | **46** | Early | China / cloud | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 156 | huawei.com | **46** | Early | China / enterprise | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 157 | biomejs.dev | **46** | Early | Developer tools | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 158 | coda.io | **46** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 159 | teambition.com | **45** | Early | China / no-code | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 160 | lazada.com | **44** | Early | China / consumer | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 161 | jiandaoyun.com | **44** | Early | China / no-code | `p2.named-author` · `p2.answer-passages` · `p1.llms-txt` |
| 162 | roadmap.sh | **44** | Early | Education | `p2.sourced-stats` · `p2.freshness` · `p1.organization` |
| 163 | perpetua.io | **42** | Early | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 164 | cohere.com | **40** | Early | AI | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 165 | continue.dev | **40** | Early | AI | `p2.freshness` · `p1.llms-txt` · `g.ssr` |
| 166 | huggingface.co | **40** | Early | AI | `p2.named-author` · `p1.organization` · `p2.answer-passages` |
| 167 | weaviate.io | **40** | Early | AI | `g.ssr` · `p2.named-author` · `p2.freshness` |
| 168 | 01.ai | **40** | Early | China / AI | `p2.freshness` · `p1.organization` · `g.ssr` |
| 169 | ecoflow.com | **40** | Early | China / consumer | `p2.answer-passages` · `p1.llms-txt` · `g.reachable` |
| 170 | datahawk.co | **40** | Early | Cross-border services | `p2.answer-passages` · `p1.llms-txt` · `g.ssr` |
| 171 | sellersprite.com | **40** | Early | Cross-border services | `p2.answer-passages` · `g.ssr` · `p3.knowledge-graph` |
| 172 | wiseasy.com | **40** | Early | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 173 | turso.tech | **40** | Early | Developer tools | `p2.named-author` · `p2.answer-passages` · `g.ssr` |
| 174 | ebay.com | **40** | Early | Ecommerce | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 175 | rakuten.com | **40** | Early | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 176 | walmart.com | **40** | Early | Ecommerce | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 177 | nostarch.com | **40** | Early | Education | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 178 | healthline.com | **40** | Early | Healthcare | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 179 | webmd.com | **40** | Early | Healthcare | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 180 | june.so | **40** | Early | Marketing / CRM | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 181 | css-tricks.com | **40** | Early | Media / Publishing | `g.reachable` · `p1.sitemap` · `p2.named-author` |
| 182 | stackoverflow.blog | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 183 | stratechery.com | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.reachable` |
| 184 | techcrunch.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p3.knowledge-graph` |
| 185 | theregister.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p3.video` |
| 186 | theverge.com | **40** | Early | Media / Publishing | `p2.answer-passages` · `p1.llms-txt` · `g.robots` |
| 187 | payoneer.com | **40** | Early | Payments / Fintech | `g.robots` · `g.reachable` · `p1.page-type` |
| 188 | airtable.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 189 | figma.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 190 | loom.com | **40** | Early | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 191 | windsurf.com | **39** | Early | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 192 | temu.com | **39** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 193 | shopee.com | **39** | Early | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 194 | dji.com | **38** | Early | China / consumer | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 195 | yonyou.com | **38** | Early | China / enterprise | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 196 | mabangerp.com | **38** | Early | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 197 | tongtool.com | **36** | Early | Cross-border services | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 198 | obsidian.md | **36** | Early | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 199 | hisense.com | **34** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 200 | airbnb.com | **34** | Early | Travel | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 201 | volcengine.com | **33** | Early | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 202 | shadcn.com | **33** | Early | Developer tools | `p2.question-intent` · `p2.freshness` · `p1.organization` |
| 203 | aliexpress.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 204 | lenovo.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 205 | miniso.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 206 | payoneer.cn | **30** | Not started | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 207 | yuncang.com | **30** | Not started | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 208 | dreame.tech | **29** | Not started | China / consumer | `p2.answer-passages` · `p2.sourced-stats` · `p2.question-intent` |
| 209 | solidjs.com | **28** | Not started | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 210 | narwal.com | **27** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 211 | xiaomi.com | **27** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 212 | jushuitan.com | **27** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 213 | bigmodel.cn | **26** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 214 | khanacademy.org | **26** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 215 | drizzle.team | **25** | Not started | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 216 | oceanwing.com | **24** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 217 | pingpongx.com | **24** | Not started | Cross-border services | `p2.answer-passages` · `p2.sourced-stats` · `p2.question-intent` |
| 218 | freecodecamp.org | **23** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 219 | qcloud.com | **22** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 220 | shein.com | **22** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 221 | feishu.cn | **20** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 222 | yuque.com | **19** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 223 | booking.com | **18** | Not started | Travel | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 224 | baichuan-ai.com | **16** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 225 | stepfun.com | **14** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 226 | lianlianpay.com | **14** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 227 | amazon.com | **12** | Not started | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 228 | mercadolibre.com | **12** | Not started | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 229 | keepa.com | **7** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |

### Not scored

- **codeium.com** — could not fetch https://www.codeium.com — all requests returned 308
- **midjourney.com** — could not fetch https://www.midjourney.com — <urlopen error [SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol ver
- **openai.com** — could not fetch https://www.openai.com — all requests returned 308
- **perplexity.ai** — could not fetch https://www.perplexity.ai — all requests returned 403
- **runwayml.com** — could not fetch https://www.runwayml.com — all requests returned 308
- **aosom.com** — could not fetch https://www.aosom.com — all requests returned 403
- **bambulab.com** — could not fetch https://www.bambulab.com — all requests returned 403
- **cider.com** — could not fetch https://www.cider.com — <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostn
- **clubfactory.com** — unknown url type: '/sitemap.xml'
- **cubiitek.com** — could not fetch https://www.cubiitek.com — <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>
- **elegoo.com** — could not fetch https://www.elegoo.com — all requests returned 429
- **hiwonder.com** — could not fetch https://www.hiwonder.com — all requests returned 429
- **insta360.com** — could not fetch https://www.insta360.com — all requests returned 403
- **laifen.com** — could not fetch https://www.laifen.com — <urlopen error _ssl.c:1112: The handshake operation timed out>
- **sonoff.tech** — could not fetch https://www.sonoff.tech — all requests returned 429
- **ugreen.com** — could not fetch https://www.ugreen.com — all requests returned 429
- **roborock.com** — could not fetch https://www.roborock.com — all requests returned 429
- **hashicorp.com** — could not fetch https://www.hashicorp.com — all requests returned 429
- **aftership.com** — could not fetch https://www.aftership.com — all requests returned 403
- **neon.tech** — could not fetch https://www.neon.tech — all requests returned 308
- **allegro.pl** — could not fetch https://www.allegro.pl — all requests returned 403
- **coupang.com** — could not fetch https://www.coupang.com — all requests returned 403
- **etsy.com** — could not fetch https://www.etsy.com — all requests returned 403
- **jumia.com** — could not fetch https://www.jumia.com — all requests returned 403
- **noon.com** — could not fetch https://www.noon.com — The read operation timed out
- **ozon.ru** — could not fetch https://www.ozon.ru — all requests returned 307
- **shopline.com** — could not fetch https://www.shopline.com — all requests returned 403
- **trendyol.com** — could not fetch https://www.trendyol.com — all requests returned 403
- **wildberries.ru** — could not fetch https://www.wildberries.ru — The read operation timed out
- **exercism.org** — could not fetch https://www.exercism.org — all requests returned 403
- **udemy.com** — could not fetch https://www.udemy.com — all requests returned 403
- **mayoclinic.org** — could not fetch https://www.mayoclinic.org — all requests returned 403
- **lwn.net** — could not fetch https://www.lwn.net — all requests returned 429
- **phoronix.com** — could not fetch https://www.phoronix.com — all requests returned 403
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

