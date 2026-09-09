# The state of AI visibility

Every site below scored with the same open rubric, the same public tool and the same
eight-page sample. No private data, no vendor dashboards — [re-run it yourself](run.py).

**230 sites · median 57.5 · mean 56.3 · upper quartile 72.0 · range 12–95** · rubric v1.1 · measured 2026-09-09

## A quarter of the field cannot be cited at all

**56 of 230 sites have a gate check at zero** — a crawler cannot get the content, so
nothing else on the page matters. These are two very different problems, and reporting
them as one number is what makes such a number useless:

| Why | Sites | Which |
|---|:-:|---|
| **Deliberate** — `robots.txt` disallows retrieval crawlers | 15 | figma.com, healthline.com, june.so, khanacademy.org, loom.com, mercadolibre.com, payoneer.com, qcloud.com, stackoverflow.blog, techcrunch.com, theregister.com, theverge.com, together.ai, webmd.com, xtransfer.com |
| **Deliberate or accidental** — the server returns 403 to crawlers | 9 | airbnb.com, css-tricks.com, ebay.com, keepa.com, lenovo.com, nostarch.com, slack.com, stratechery.com, xiaomi.com |
| **Accidental** — body copy only exists after JS runs | 32 | 01.ai, airtable.com, aliexpress.com, amazon.com, baichuan-ai.com, bigmodel.cn, cohere.com, continue.dev, datahawk.co, drizzle.team, feishu.cn, freecodecamp.org, huggingface.co, jushuitan.com, lianlianpay.com, narwal.com, obsidian.md, oceanwing.com, payoneer.cn, rakuten.com, roborock.com, sellersprite.com, shein.com, shopee.com, solidjs.com, stepfun.com, temu.com, turso.tech, walmart.com, weaviate.io, windsurf.com, yuque.com |

The first group made a choice. Several news and health publishers block AI crawlers by
name, and this rubric reports that as it is — a site that does not want to be quoted is
not misconfigured. The last group almost certainly did not choose it: their content is
there, a browser can see it, and a retrieval crawler gets an empty shell.

## What the spread shows

**Half the field sits between 40.0 and 72.0.** The rubric is not grading on a curve — these
are the scores that fall out of it, and they are consistent with the public benchmarks
it was [calibrated against](../rubric/calibration-v1.1.md).

**Sites built for the Chinese market score 16 points lower** — median 43.5 against 59.0
for everyone else. The gap is not content quality. It is `llms.txt`, `Organization`
schema, visible dates and bylines — conventions that spread through the English web
first and have not yet crossed over.

**The same few things are missing almost everywhere.** Counting only each site's three
largest gaps:

| Missing | Sites | What it costs |
|---|:-:|:-:|
| `p2.answer-passages` | 118 of 230 | 9 pts |
| `p2.freshness` | 108 of 230 | 6 pts |
| `p2.named-author` | 101 of 230 | 6 pts |
| `p1.organization` | 84 of 230 | 6 pts |
| `p2.question-intent` | 63 of 230 | 7 pts |
| `p1.llms-txt` | 53 of 230 | 5 pts |

None of the top three is expensive. A date in a page template, an opening paragraph
that stands on its own, and one JSON-LD block are between them worth more than any
single pillar on this list.

## By sector

| Sector | Sites | Median |
|---|:-:|:-:|
| Cloud & DevOps | 24 | **71.0** |
| Payments / Fintech | 7 | **70** |
| Marketing / CRM | 17 | **69** |
| AI | 28 | **63.5** |
| Developer tools | 37 | **59** |
| Ecommerce | 13 | **59** |
| SaaS / Productivity | 22 | **59.0** |
| China / enterprise | 6 | **53.5** |
| Education | 6 | **44.5** |
| China / no-code | 5 | **44** |
| China / AI | 9 | **43** |
| China / consumer | 20 | **40.0** |
| Healthcare | 2 | **40.0** |
| Media / Publishing | 11 | **40** |
| Cross-border services | 17 | **38** |
| Travel | 2 | **34.5** |
| China / cloud | 3 | **33** |
| China/ consumer | 1 | **26** |

## Every site

| # | Site | Score | Band | Sector | Biggest gaps |
|:-:|---|:-:|---|---|---|
| 1 | minimaxi.com | **95** | Leading | China / AI | `p2.question-intent` · `p4.cn-engines` · `p3.video` |
| 2 | pulumi.com | **95** | Leading | Cloud & DevOps | `g.robots` · `g.reachable` · `p3.video` |
| 3 | zapier.com | **92** | Leading | SaaS / Productivity | `p2.freshness` · `p2.named-author` · `p3.sameas` |
| 4 | netlify.com | **91** | Leading | Cloud & DevOps | `p2.named-author` · `p2.answer-passages` · `p3.video` |
| 5 | lumalabs.ai | **90** | Leading | AI | `p3.knowledge-graph` · `p2.question-intent` · `g.reachable` |
| 6 | resend.com | **90** | Leading | Developer tools | `p3.knowledge-graph` · `p2.freshness` · `p2.answer-passages` |
| 7 | bun.sh | **88** | Leading | Developer tools | `p2.freshness` · `p2.question-intent` · `p2.answer-passages` |
| 8 | clerk.com | **87** | Leading | Developer tools | `p2.sourced-stats` · `p2.answer-passages` · `p1.sitemap` |
| 9 | prisma.io | **87** | Leading | Developer tools | `p2.question-intent` · `p3.video` · `p2.freshness` |
| 10 | clickup.com | **87** | Leading | SaaS / Productivity | `p3.video` · `p2.freshness` · `p2.answer-passages` |
| 11 | twilio.com | **86** | Leading | Cloud & DevOps | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 12 | planetscale.com | **85** | Leading | Developer tools | `p2.named-author` · `p2.answer-passages` · `p1.page-type` |
| 13 | elevenlabs.io | **84** | Leading | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 14 | ideogram.ai | **84** | Leading | AI | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 15 | vercel.com | **84** | Leading | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 16 | intercom.com | **84** | Leading | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 17 | axiom.co | **83** | Leading | Cloud & DevOps | `p2.freshness` · `p3.video` · `p2.named-author` |
| 18 | upstash.com | **83** | Leading | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p3.video` |
| 19 | fly.io | **83** | Leading | Developer tools | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 20 | nuxt.com | **83** | Leading | Developer tools | `p2.freshness` · `p3.video` · `p2.question-intent` |
| 21 | trigger.dev | **83** | Leading | Developer tools | `p3.knowledge-graph` · `p3.video` · `p3.sameas` |
| 22 | supabase.com | **82** | Solid | Developer tools | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 23 | mistral.ai | **80** | Solid | AI | `p2.answer-passages` · `p2.named-author` · `p1.breadcrumb` |
| 24 | suno.com | **80** | Solid | AI | `p2.named-author` · `p1.breadcrumb` · `p4.answer-shape` |
| 25 | baseus.com | **80** | Solid | China / consumer | `p3.knowledge-graph` · `p3.sameas` · `p2.named-author` |
| 26 | nextjs.org | **80** | Solid | Developer tools | `p3.video` · `p2.named-author` · `p1.breadcrumb` |
| 27 | clickhouse.com | **79** | Solid | Cloud & DevOps | `p3.video` · `p3.sameas` · `p2.named-author` |
| 28 | cloudflare.com | **79** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.video` |
| 29 | render.com | **79** | Solid | Cloud & DevOps | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 30 | woocommerce.com | **79** | Solid | Ecommerce | `p3.video` · `p2.named-author` · `p2.freshness` |
| 31 | buttondown.com | **79** | Solid | Marketing / CRM | `p2.sourced-stats` · `p3.video` · `p2.freshness` |
| 32 | calendly.com | **79** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 33 | typeform.com | **79** | Solid | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 34 | junglescout.com | **78** | Solid | Cross-border services | `p1.llms-txt` · `p1.page-type` · `p3.sameas` |
| 35 | cursor.com | **77** | Solid | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 36 | fireworks.ai | **77** | Solid | AI | `p1.llms-txt` · `p2.named-author` · `p2.freshness` |
| 37 | tcl.com | **77** | Solid | China / consumer | `p1.llms-txt` · `p3.sameas` · `p2.named-author` |
| 38 | tanstack.com | **77** | Solid | Developer tools | `p2.answer-passages` · `p3.knowledge-graph` · `p2.freshness` |
| 39 | moz.com | **77** | Solid | Marketing / CRM | `p1.llms-txt` · `p1.page-type` · `p1.organization` |
| 40 | checkout.com | **77** | Solid | Payments / Fintech | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 41 | anker.com | **76** | Solid | China / consumer | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 42 | sentry.io | **76** | Solid | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p1.page-type` |
| 43 | klaviyo.com | **76** | Solid | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p4.answer-shape` |
| 44 | deepmind.google | **74** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 45 | modal.com | **74** | Solid | AI | `p1.sitemap` · `p1.page-type` · `p3.sameas` |
| 46 | squarespace.com | **74** | Solid | Ecommerce | `p2.answer-passages` · `p3.video` · `p2.named-author` |
| 47 | webflow.com | **74** | Solid | Ecommerce | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 48 | plausible.io | **74** | Solid | Marketing / CRM | `p1.llms-txt` · `p3.video` · `p3.sameas` |
| 49 | monday.com | **74** | Solid | SaaS / Productivity | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 50 | crewai.com | **73** | Solid | AI | `p2.question-intent` · `p1.page-type` · `p2.named-author` |
| 51 | helium10.com | **73** | Solid | Cross-border services | `p2.answer-passages` · `p1.llms-txt` · `p3.knowledge-graph` |
| 52 | railway.com | **73** | Solid | Developer tools | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 53 | shopify.com | **73** | Solid | Ecommerce | `p2.answer-passages` · `p1.page-type` · `p2.named-author` |
| 54 | prefect.io | **72** | Solid | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 55 | inngest.com | **72** | Solid | Developer tools | `p2.freshness` · `p3.knowledge-graph` · `p2.question-intent` |
| 56 | ghost.org | **72** | Solid | Marketing / CRM | `p1.llms-txt` · `p3.knowledge-graph` · `p3.sameas` |
| 57 | arstechnica.com | **72** | Solid | Media / Publishing | `p1.llms-txt` · `p2.question-intent` · `p3.sameas` |
| 58 | asana.com | **72** | Solid | SaaS / Productivity | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 59 | cal.com | **72** | Solid | SaaS / Productivity | `p2.answer-passages` · `p3.sameas` · `p2.named-author` |
| 60 | productboard.com | **72** | Solid | SaaS / Productivity | `p2.answer-passages` · `p1.page-type` · `p2.named-author` |
| 61 | openrouter.ai | **71** | Solid | AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 62 | motherduck.com | **71** | Solid | Cloud & DevOps | `p2.question-intent` · `p2.freshness` · `p2.sourced-stats` |
| 63 | temporal.io | **71** | Solid | Cloud & DevOps | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 64 | hubspot.com | **71** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 65 | stripe.com | **71** | Solid | Payments / Fintech | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 66 | langfuse.com | **70** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 67 | tencent.com | **70** | Solid | China / enterprise | `p1.llms-txt` · `p2.question-intent` · `p1.page-type` |
| 68 | deno.com | **70** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 69 | adyen.com | **70** | Solid | Payments / Fintech | `p2.freshness` · `p1.page-type` · `p3.video` |
| 70 | airwallex.com | **70** | Solid | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.page-type` |
| 71 | dagster.io | **69** | Solid | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p1.page-type` |
| 72 | shoplazza.com | **69** | Solid | Ecommerce | `p1.organization` · `p3.knowledge-graph` · `p3.sameas` |
| 73 | beehiiv.com | **69** | Solid | Marketing / CRM | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 74 | semrush.com | **69** | Solid | Marketing / CRM | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 75 | wired.com | **69** | Solid | Media / Publishing | `p1.llms-txt` · `p3.sameas` · `p2.named-author` |
| 76 | vuejs.org | **68** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.video` |
| 77 | pinecone.io | **67** | Solid | AI | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 78 | kingdee.com | **67** | Solid | China / enterprise | `p2.named-author` · `p3.knowledge-graph` · `p2.question-intent` |
| 79 | bigcommerce.com | **67** | Solid | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 80 | attio.com | **67** | Solid | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p2.named-author` |
| 81 | linear.app | **67** | Solid | SaaS / Productivity | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 82 | duckdb.org | **66** | Solid | Cloud & DevOps | `p2.answer-passages` · `p3.video` · `p3.sameas` |
| 83 | coursera.org | **66** | Solid | Education | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 84 | materialize.com | **65** | Growing | Cloud & DevOps | `p2.freshness` · `p2.answer-passages` · `p1.page-type` |
| 85 | svelte.dev | **65** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 86 | pika.art | **64** | Growing | AI | `p2.freshness` · `p3.knowledge-graph` · `p2.named-author` |
| 87 | braze.com | **64** | Growing | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p3.video` |
| 88 | replicate.com | **63** | Growing | AI | `p1.organization` · `p3.knowledge-graph` · `p1.page-type` |
| 89 | elysiajs.com | **63** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 90 | oclean.com | **62** | Growing | China / consumer | `p1.organization` · `p2.sourced-stats` · `p3.sameas` |
| 91 | alibabagroup.com | **61** | Growing | China / enterprise | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 92 | browserbase.com | **60** | Growing | AI | `p2.named-author` · `p2.answer-passages` · `p3.knowledge-graph` |
| 93 | ecoflow.com | **60** | Growing | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p1.page-type` |
| 94 | vitest.dev | **60** | Growing | Developer tools | `p1.organization` · `p3.knowledge-graph` · `p1.sitemap` |
| 95 | hackaday.com | **60** | Growing | Media / Publishing | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 96 | miro.com | **60** | Growing | SaaS / Productivity | `p2.named-author` · `p1.llms-txt` · `p3.sameas` |
| 97 | anthropic.com | **59** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 98 | langchain.com | **59** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 99 | govee.com | **59** | Growing | China / consumer | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 100 | porter.run | **59** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 101 | m19.com | **59** | Growing | Cross-border services | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 102 | astro.build | **59** | Growing | Developer tools | `p1.organization` · `p1.llms-txt` · `p1.page-type` |
| 103 | valibot.dev | **59** | Growing | Developer tools | `p2.named-author` · `p1.organization` · `p2.question-intent` |
| 104 | wix.com | **59** | Growing | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 105 | posthog.com | **59** | Growing | Marketing / CRM | `p2.freshness` · `p2.answer-passages` · `p2.sourced-stats` |
| 106 | smashingmagazine.com | **59** | Growing | Media / Publishing | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 107 | notion.com | **59** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 108 | superhuman.com | **59** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 109 | aider.chat | **58** | Growing | AI | `p1.organization` · `p1.llms-txt` · `p3.sameas` |
| 110 | deepseek.com | **58** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 111 | creality.com | **58** | Growing | China / consumer | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 112 | datadoghq.com | **58** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 113 | tigerbeetle.com | **58** | Growing | Cloud & DevOps | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 114 | panda-css.com | **58** | Growing | Developer tools | `p1.organization` · `p3.knowledge-graph` · `p1.sitemap` |
| 115 | ahrefs.com | **58** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 116 | mingdao.com | **57** | Growing | China / no-code | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 117 | timescale.com | **57** | Growing | Cloud & DevOps | `p2.answer-passages` · `p1.organization` · `p3.knowledge-graph` |
| 118 | customer.io | **57** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p3.knowledge-graph` |
| 119 | wise.com | **57** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 120 | raycast.com | **57** | Growing | SaaS / Productivity | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 121 | siliconflow.cn | **56** | Growing | China / AI | `p2.named-author` · `p1.organization` · `p2.sourced-stats` |
| 122 | betterstack.com | **56** | Growing | Cloud & DevOps | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 123 | koyeb.com | **56** | Growing | Cloud & DevOps | `p1.organization` · `p1.llms-txt` · `p3.knowledge-graph` |
| 124 | hono.dev | **56** | Growing | Developer tools | `p1.organization` · `p2.sourced-stats` · `p1.sitemap` |
| 125 | orm.drizzle.team | **56** | Growing | Developer tools | `p2.question-intent` · `p1.organization` · `p2.sourced-stats` |
| 126 | vitejs.dev | **56** | Growing | Developer tools | `p1.organization` · `p2.question-intent` · `p1.page-type` |
| 127 | zod.dev | **56** | Growing | Developer tools | `p1.organization` · `p2.answer-passages` · `p2.question-intent` |
| 128 | mailchimp.com | **56** | Growing | Marketing / CRM | `p2.freshness` · `p1.organization` · `p2.sourced-stats` |
| 129 | effect.website | **55** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 130 | qwik.dev | **55** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 131 | fathom.video | **55** | Growing | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 132 | plaid.com | **55** | Growing | Payments / Fintech | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 133 | readwise.io | **55** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 134 | tability.io | **55** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 135 | moonshot.cn | **54** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 136 | nitro.build | **54** | Growing | Developer tools | `p1.organization` · `p2.question-intent` · `p1.sitemap` |
| 137 | remix.run | **53** | Growing | Developer tools | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 138 | pragprog.com | **53** | Growing | Education | `p1.organization` · `p1.llms-txt` · `p3.knowledge-graph` |
| 139 | digitalocean.com | **52** | Growing | Cloud & DevOps | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 140 | dianxiaomi.com | **52** | Growing | Cross-border services | `p2.question-intent` · `p2.named-author` · `p2.answer-passages` |
| 141 | baseten.co | **51** | Growing | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 142 | groq.com | **51** | Growing | AI | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 143 | unocss.dev | **51** | Growing | Developer tools | `p1.organization` · `p3.knowledge-graph` · `p2.question-intent` |
| 144 | grafana.com | **50** | Early | Cloud & DevOps | `p2.sourced-stats` · `p2.freshness` · `p1.organization` |
| 145 | tailwindcss.com | **50** | Early | Developer tools | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 146 | simonwillison.net | **50** | Early | Media / Publishing | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 147 | arc.net | **50** | Early | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 148 | llamaindex.ai | **49** | Early | AI | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 149 | roadmap.sh | **49** | Early | Education | `p2.sourced-stats` · `p2.freshness` · `p1.organization` |
| 150 | vevor.com | **48** | Early | China / consumer | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 151 | radix-ui.com | **48** | Early | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 152 | teambition.com | **47** | Early | China / no-code | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 153 | aliyun.com | **46** | Early | China / cloud | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 154 | huawei.com | **46** | Early | China / enterprise | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 155 | biomejs.dev | **46** | Early | Developer tools | `p1.organization` · `p1.llms-txt` · `p2.question-intent` |
| 156 | bytedance.com | **45** | Early | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 157 | lazada.com | **44** | Early | China / consumer | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 158 | jiandaoyun.com | **44** | Early | China / no-code | `p2.named-author` · `p2.answer-passages` · `p1.llms-txt` |
| 159 | perpetua.io | **44** | Early | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 160 | coda.io | **44** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 161 | zhipuai.cn | **43** | Early | China / AI | `p2.answer-passages` · `p2.question-intent` · `p1.organization` |
| 162 | cohere.com | **40** | Early | AI | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 163 | continue.dev | **40** | Early | AI | `p2.freshness` · `p1.llms-txt` · `g.ssr` |
| 164 | huggingface.co | **40** | Early | AI | `p2.named-author` · `p1.organization` · `p2.answer-passages` |
| 165 | together.ai | **40** | Early | AI | `p2.answer-passages` · `g.robots` · `p3.video` |
| 166 | weaviate.io | **40** | Early | AI | `g.ssr` · `p2.named-author` · `p2.freshness` |
| 167 | windsurf.com | **40** | Early | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 168 | 01.ai | **40** | Early | China / AI | `p2.freshness` · `p1.organization` · `g.ssr` |
| 169 | dji.com | **40** | Early | China / consumer | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 170 | temu.com | **40** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 171 | datahawk.co | **40** | Early | Cross-border services | `p2.answer-passages` · `p1.llms-txt` · `g.ssr` |
| 172 | sellersprite.com | **40** | Early | Cross-border services | `p2.answer-passages` · `g.ssr` · `p2.question-intent` |
| 173 | xtransfer.com | **40** | Early | Cross-border services | `p2.freshness` · `p2.answer-passages` · `g.robots` |
| 174 | turso.tech | **40** | Early | Developer tools | `p2.named-author` · `p2.answer-passages` · `g.ssr` |
| 175 | ebay.com | **40** | Early | Ecommerce | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 176 | rakuten.com | **40** | Early | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 177 | walmart.com | **40** | Early | Ecommerce | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 178 | nostarch.com | **40** | Early | Education | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 179 | healthline.com | **40** | Early | Healthcare | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 180 | webmd.com | **40** | Early | Healthcare | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 181 | june.so | **40** | Early | Marketing / CRM | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 182 | css-tricks.com | **40** | Early | Media / Publishing | `g.reachable` · `p1.sitemap` · `p2.named-author` |
| 183 | stackoverflow.blog | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 184 | stratechery.com | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.reachable` |
| 185 | techcrunch.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p3.knowledge-graph` |
| 186 | theregister.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p3.video` |
| 187 | theverge.com | **40** | Early | Media / Publishing | `p2.answer-passages` · `p1.llms-txt` · `g.robots` |
| 188 | payoneer.com | **40** | Early | Payments / Fintech | `g.robots` · `g.reachable` · `p1.page-type` |
| 189 | airtable.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 190 | figma.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 191 | loom.com | **40** | Early | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 192 | obsidian.md | **40** | Early | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 193 | slack.com | **40** | Early | SaaS / Productivity | `p2.freshness` · `p1.organization` · `g.reachable` |
| 194 | shopee.com | **39** | Early | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 195 | yonyou.com | **38** | Early | China / enterprise | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 196 | tongtool.com | **38** | Early | Cross-border services | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 197 | wiseasy.com | **38** | Early | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 198 | mabangerp.com | **36** | Early | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 199 | booking.com | **35** | Early | Travel | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 200 | hisense.com | **34** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 201 | airbnb.com | **34** | Early | Travel | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 202 | volcengine.com | **33** | Early | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 203 | solidjs.com | **33** | Early | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 204 | shadcn.com | **31** | Early | Developer tools | `p2.question-intent` · `p2.freshness` · `p1.organization` |
| 205 | lenovo.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 206 | narwal.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 207 | xiaomi.com | **30** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 208 | payoneer.cn | **30** | Not started | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 209 | yuncang.com | **30** | Not started | Cross-border services | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 210 | drizzle.team | **30** | Not started | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 211 | dreame.tech | **29** | Not started | China / consumer | `p2.answer-passages` · `p2.sourced-stats` · `p2.question-intent` |
| 212 | miniso.com | **28** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 213 | khanacademy.org | **28** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 214 | aliexpress.com | **27** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 215 | bigmodel.cn | **26** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 216 | shein.com | **26** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 217 | roborock.com | **26** | Not started | China/ consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 218 | jushuitan.com | **25** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 219 | pingpongx.com | **24** | Not started | Cross-border services | `p2.answer-passages` · `p2.sourced-stats` · `p2.question-intent` |
| 220 | oceanwing.com | **23** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 221 | qcloud.com | **22** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 222 | freecodecamp.org | **20** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 223 | feishu.cn | **19** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 224 | yuque.com | **18** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 225 | baichuan-ai.com | **16** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 226 | amazon.com | **16** | Not started | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 227 | stepfun.com | **14** | Not started | China / AI | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 228 | lianlianpay.com | **13** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 229 | keepa.com | **12** | Not started | Cross-border services | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 230 | mercadolibre.com | **12** | Not started | Ecommerce | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |

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
- **wildberries.ru** — could not fetch https://www.wildberries.ru — all requests returned 498
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

