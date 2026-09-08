# The state of AI visibility

Every site below scored with the same open rubric, the same public tool and the same
eight-page sample. No private data, no vendor dashboards — [re-run it yourself](run.py).

**105 sites · median 59 · mean 58.6 · upper quartile 73.0 · range 19–94** · rubric v1.1 · measured 2026-09-09

## A quarter of the field cannot be cited at all

**25 of 105 sites have a gate check at zero** — a crawler cannot get the content, so
nothing else on the page matters. These are two very different problems, and reporting
them as one number is what makes such a number useless:

| Why | Sites | Which |
|---|:-:|---|
| **Deliberate** — `robots.txt` disallows retrieval crawlers | 11 | figma.com, healthline.com, khanacademy.org, loom.com, payoneer.com, qcloud.com, stackoverflow.blog, techcrunch.com, theverge.com, together.ai, webmd.com |
| **Deliberate or accidental** — the server returns 403 to crawlers | 3 | airbnb.com, css-tricks.com, xiaomi.com |
| **Accidental** — body copy only exists after JS runs | 11 | 01.ai, airtable.com, cohere.com, feishu.cn, freecodecamp.org, huggingface.co, shein.com, solidjs.com, temu.com, weaviate.io, yuque.com |

The first group made a choice. Several news and health publishers block AI crawlers by
name, and this rubric reports that as it is — a site that does not want to be quoted is
not misconfigured. The last group almost certainly did not choose it: their content is
there, a browser can see it, and a retrieval crawler gets an empty shell.

## What the spread shows

**Half the field sits between 40.0 and 73.0.** The rubric is not grading on a curve — these
are the scores that fall out of it, and they are consistent with the public benchmarks
it was [calibrated against](../rubric/calibration-v1.1.md).

**Sites built for the Chinese market score 22 points lower** — median 44 against 65.5
for everyone else. The gap is not content quality. It is `llms.txt`, `Organization`
schema, visible dates and bylines — conventions that spread through the English web
first and have not yet crossed over.

**The same few things are missing almost everywhere.** Counting only each site's three
largest gaps:

| Missing | Sites | What it costs |
|---|:-:|:-:|
| `p2.freshness` | 57 of 105 | 6 pts |
| `p2.named-author` | 53 of 105 | 6 pts |
| `p2.answer-passages` | 52 of 105 | 9 pts |
| `p1.organization` | 36 of 105 | 6 pts |
| `p2.question-intent` | 28 of 105 | 7 pts |
| `p1.llms-txt` | 20 of 105 | 5 pts |

None of the top three is expensive. A date in a page template, an opening paragraph
that stands on its own, and one JSON-LD block are between them worth more than any
single pillar on this list.

## By sector

| Sector | Sites | Median |
|---|:-:|:-:|
| Cloud & DevOps | 10 | **79.0** |
| Ecommerce | 6 | **72.5** |
| Marketing / CRM | 8 | **70.0** |
| Developer tools | 16 | **69.0** |
| Payments / Fintech | 7 | **65** |
| SaaS / Productivity | 12 | **64.0** |
| AI | 10 | **60.5** |
| China / enterprise | 6 | **57.0** |
| China / AI | 4 | **47.0** |
| China / no-code | 5 | **44** |
| Media / Publishing | 6 | **40.0** |
| Healthcare | 2 | **38.5** |
| China / consumer | 5 | **38** |
| Travel | 2 | **36.5** |
| China / cloud | 3 | **30** |
| Education | 3 | **28** |

## Every site

| # | Site | Score | Band | Sector | Biggest gaps |
|:-:|---|:-:|---|---|---|
| 1 | pulumi.com | **94** | Leading | Cloud & DevOps | `p2.freshness` · `g.robots` · `p3.video` |
| 2 | netlify.com | **92** | Leading | Cloud & DevOps | `p2.named-author` · `p2.answer-passages` · `p3.video` |
| 3 | zapier.com | **92** | Leading | SaaS / Productivity | `p2.freshness` · `p2.named-author` · `p3.sameas` |
| 4 | bun.sh | **88** | Leading | Developer tools | `p2.freshness` · `p2.question-intent` · `p2.answer-passages` |
| 5 | clickup.com | **87** | Leading | SaaS / Productivity | `p3.video` · `p2.freshness` · `p2.answer-passages` |
| 6 | prisma.io | **85** | Leading | Developer tools | `p2.question-intent` · `p3.video` · `p2.freshness` |
| 7 | elevenlabs.io | **84** | Leading | AI | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 8 | vercel.com | **84** | Leading | Cloud & DevOps | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 9 | fly.io | **84** | Leading | Developer tools | `p2.named-author` · `p2.freshness` · `p1.breadcrumb` |
| 10 | nuxt.com | **84** | Leading | Developer tools | `p2.freshness` · `p3.video` · `p2.question-intent` |
| 11 | intercom.com | **84** | Leading | Marketing / CRM | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 12 | supabase.com | **83** | Leading | Developer tools | `p2.answer-passages` · `p2.named-author` · `p2.freshness` |
| 13 | woocommerce.com | **81** | Solid | Ecommerce | `p3.video` · `p2.named-author` · `p2.freshness` |
| 14 | cloudflare.com | **80** | Solid | Cloud & DevOps | `p2.freshness` · `p1.page-type` · `p3.video` |
| 15 | nextjs.org | **80** | Solid | Developer tools | `p3.video` · `p2.named-author` · `p1.breadcrumb` |
| 16 | render.com | **79** | Solid | Cloud & DevOps | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 17 | twilio.com | **79** | Solid | Cloud & DevOps | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 18 | mistral.ai | **77** | Solid | AI | `p2.answer-passages` · `p3.knowledge-graph` · `p2.named-author` |
| 19 | checkout.com | **77** | Solid | Payments / Fintech | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 20 | anker.com | **76** | Solid | China / consumer | `p2.freshness` · `p2.answer-passages` · `p2.named-author` |
| 21 | sentry.io | **76** | Solid | Cloud & DevOps | `p2.freshness` · `p3.knowledge-graph` · `p1.page-type` |
| 22 | moz.com | **76** | Solid | Marketing / CRM | `p1.llms-txt` · `p1.page-type` · `p1.organization` |
| 23 | squarespace.com | **74** | Solid | Ecommerce | `p2.answer-passages` · `p3.video` · `p2.named-author` |
| 24 | calendly.com | **74** | Solid | SaaS / Productivity | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 25 | railway.com | **73** | Solid | Developer tools | `p3.knowledge-graph` · `p2.named-author` · `p2.freshness` |
| 26 | webflow.com | **73** | Solid | Ecommerce | `p2.freshness` · `p2.named-author` · `p1.breadcrumb` |
| 27 | monday.com | **73** | Solid | SaaS / Productivity | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 28 | shopify.com | **72** | Solid | Ecommerce | `p2.answer-passages` · `p1.page-type` · `p2.named-author` |
| 29 | klaviyo.com | **72** | Solid | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p2.named-author` |
| 30 | arstechnica.com | **72** | Solid | Media / Publishing | `p1.llms-txt` · `p2.question-intent` · `p3.sameas` |
| 31 | kingdee.com | **71** | Solid | China / enterprise | `p2.named-author` · `p2.question-intent` · `p1.page-type` |
| 32 | hubspot.com | **71** | Solid | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 33 | vuejs.org | **70** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.video` |
| 34 | adyen.com | **70** | Solid | Payments / Fintech | `p2.freshness` · `p1.page-type` · `p3.video` |
| 35 | stripe.com | **70** | Solid | Payments / Fintech | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 36 | tencent.com | **69** | Solid | China / enterprise | `p1.llms-txt` · `p2.question-intent` · `p1.page-type` |
| 37 | coursera.org | **69** | Solid | Education | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 38 | semrush.com | **69** | Solid | Marketing / CRM | `p2.freshness` · `p1.page-type` · `p2.named-author` |
| 39 | linear.app | **69** | Solid | SaaS / Productivity | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 40 | deno.com | **68** | Solid | Developer tools | `p1.organization` · `p1.page-type` · `p3.sameas` |
| 41 | asana.com | **68** | Solid | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 42 | grafana.com | **67** | Solid | Cloud & DevOps | `p2.named-author` · `p2.freshness` · `p3.knowledge-graph` |
| 43 | replicate.com | **66** | Solid | AI | `p1.organization` · `p1.page-type` · `p3.video` |
| 44 | bigcommerce.com | **66** | Solid | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p1.page-type` |
| 45 | alibabagroup.com | **65** | Growing | China / enterprise | `p1.organization` · `p2.answer-passages` · `p2.question-intent` |
| 46 | airwallex.com | **65** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 47 | pinecone.io | **64** | Growing | AI | `p2.answer-passages` · `p2.freshness` · `p3.knowledge-graph` |
| 48 | svelte.dev | **64** | Growing | Developer tools | `p1.organization` · `p1.sitemap` · `p1.page-type` |
| 49 | braze.com | **64** | Growing | Marketing / CRM | `p2.answer-passages` · `p3.knowledge-graph` · `p3.video` |
| 50 | langchain.com | **62** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 51 | miro.com | **60** | Growing | SaaS / Productivity | `p2.named-author` · `p1.llms-txt` · `p3.sameas` |
| 52 | slack.com | **60** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 53 | anthropic.com | **59** | Growing | AI | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 54 | wix.com | **59** | Growing | Ecommerce | `p2.answer-passages` · `p2.freshness` · `p2.named-author` |
| 55 | smashingmagazine.com | **59** | Growing | Media / Publishing | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 56 | notion.com | **59** | Growing | SaaS / Productivity | `p2.freshness` · `p1.organization` · `p1.page-type` |
| 57 | datadoghq.com | **58** | Growing | Cloud & DevOps | `p1.organization` · `p2.answer-passages` · `p3.knowledge-graph` |
| 58 | ahrefs.com | **58** | Growing | Marketing / CRM | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 59 | mingdao.com | **57** | Growing | China / no-code | `p2.freshness` · `p2.answer-passages` · `p3.knowledge-graph` |
| 60 | astro.build | **57** | Growing | Developer tools | `p1.organization` · `p2.answer-passages` · `p1.llms-txt` |
| 61 | qwik.dev | **57** | Growing | Developer tools | `p2.freshness` · `p1.organization` · `p1.llms-txt` |
| 62 | moonshot.cn | **56** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 63 | mailchimp.com | **56** | Growing | Marketing / CRM | `p2.freshness` · `p1.organization` · `p2.sourced-stats` |
| 64 | plaid.com | **55** | Growing | Payments / Fintech | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 65 | remix.run | **53** | Growing | Developer tools | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 66 | vitejs.dev | **53** | Growing | Developer tools | `p1.organization` · `p3.knowledge-graph` · `p2.question-intent` |
| 67 | digitalocean.com | **52** | Growing | Cloud & DevOps | `p2.answer-passages` · `p1.organization` · `p1.llms-txt` |
| 68 | tailwindcss.com | **52** | Growing | Developer tools | `p2.named-author` · `p1.organization` · `p1.llms-txt` |
| 69 | wise.com | **52** | Growing | Payments / Fintech | `p2.freshness` · `p2.answer-passages` · `p1.llms-txt` |
| 70 | deepseek.com | **51** | Growing | China / AI | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 71 | huawei.com | **49** | Early | China / enterprise | `p2.freshness` · `p1.organization` · `p2.answer-passages` |
| 72 | aliyun.com | **46** | Early | China / cloud | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 73 | teambition.com | **45** | Early | China / no-code | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 74 | bytedance.com | **44** | Early | China / enterprise | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 75 | jiandaoyun.com | **44** | Early | China / no-code | `p2.named-author` · `p2.answer-passages` · `p1.llms-txt` |
| 76 | zhipuai.cn | **43** | Early | China / AI | `p2.answer-passages` · `p2.question-intent` · `p1.organization` |
| 77 | yonyou.com | **43** | Early | China / enterprise | `p2.question-intent` · `p2.named-author` · `p1.organization` |
| 78 | cohere.com | **40** | Early | AI | `p2.answer-passages` · `p2.freshness` · `g.ssr` |
| 79 | huggingface.co | **40** | Early | AI | `p2.named-author` · `p1.organization` · `p2.answer-passages` |
| 80 | together.ai | **40** | Early | AI | `p2.answer-passages` · `g.robots` · `p3.video` |
| 81 | weaviate.io | **40** | Early | AI | `g.ssr` · `p2.named-author` · `p2.freshness` |
| 82 | 01.ai | **40** | Early | China / AI | `p2.freshness` · `p1.organization` · `g.ssr` |
| 83 | healthline.com | **40** | Early | Healthcare | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 84 | css-tricks.com | **40** | Early | Media / Publishing | `g.reachable` · `p1.sitemap` · `p2.named-author` |
| 85 | stackoverflow.blog | **40** | Early | Media / Publishing | `p1.organization` · `p1.llms-txt` · `g.robots` |
| 86 | techcrunch.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `g.reachable` |
| 87 | theverge.com | **40** | Early | Media / Publishing | `p1.llms-txt` · `g.robots` · `p2.question-intent` |
| 88 | payoneer.com | **40** | Early | Payments / Fintech | `g.robots` · `g.reachable` · `p1.page-type` |
| 89 | figma.com | **40** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 90 | loom.com | **40** | Early | SaaS / Productivity | `p2.named-author` · `p2.freshness` · `p2.answer-passages` |
| 91 | temu.com | **39** | Early | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.freshness` |
| 92 | booking.com | **39** | Early | Travel | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 93 | dji.com | **38** | Early | China / consumer | `p2.question-intent` · `p2.named-author` · `p2.freshness` |
| 94 | airtable.com | **38** | Early | SaaS / Productivity | `p2.answer-passages` · `p2.freshness` · `p1.organization` |
| 95 | webmd.com | **37** | Early | Healthcare | `p2.named-author` · `p2.freshness` · `p1.organization` |
| 96 | airbnb.com | **34** | Early | Travel | `p2.answer-passages` · `p2.freshness` · `p1.llms-txt` |
| 97 | volcengine.com | **30** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 98 | solidjs.com | **29** | Not started | Developer tools | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 99 | khanacademy.org | **28** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 100 | shein.com | **26** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 101 | xiaomi.com | **25** | Not started | China / consumer | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 102 | freecodecamp.org | **23** | Not started | Education | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 103 | qcloud.com | **22** | Not started | China / cloud | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 104 | feishu.cn | **19** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |
| 105 | yuque.com | **19** | Not started | China / no-code | `p2.answer-passages` · `p2.question-intent` · `p2.named-author` |

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

