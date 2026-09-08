# stripe.com — AIV 45 / 88 (v1.0)

**51% · Below average** · audited 2026-09-08 · audience `mul`

> Stripe 有一份 65KB、30 个分节的 llms.txt 和满分级的品牌权威（Wikidata + Wikipedia + 双 YouTube 频道），但结构化数据只拿到 20 分里的 4 分——首页之外没有任何页面带 Organization/WebSite，全站零 dateModified、零 speakable、零 BreadcrumbList，/pricing 连 Product/Offer 都没有。AIV 45 / 88 (v1.0)，归一化 51%，Below average。

Machine-readable: [`stripe.com.json`](stripe.com.json)

## Sampled URLs (78)

- `https://stripe.com/`
- `https://stripe.com/payments`
- `https://stripe.com/connect`
- `https://stripe.com/payments/payment-links`
- `https://stripe.com/blog/five-monetization-trends-from-global-pricing-leaders`
- `https://stripe.com/blog/why-global-workers-are-driving-demand-for-stablecoin-payouts`
- `https://stripe.com/blog/reduce-fx-costs-with-stripe`
- `https://stripe.com/blog/mapping-the-ai-economy`
- `https://stripe.com/robots.txt`
- `https://stripe.com/llms.txt`
- `https://stripe.com/llms-full.txt`
- `https://stripe.com/ai.txt`
- …and 66 more, see the JSON

## Infrastructure — 14 / 20

**✓ `p1.robots-allows-retrieval` 3/3**

robots.txt returns 200, 643 bytes, 3 user-agent groups (ia_archiver, *, rogerbot). None of the 10 retrieval crawlers is named, so all 10 fall under 'User-agent: *', which carries 'Allow: /docs' plus 8 narrow Disallow paths (/bitcoin/refund, /sources/*, /unsupported-browser, /handoff*) and no 'Disallow: /'. 10 of 10 retrieval user-agents allowed on the homepage and on every sampled URL. floor(3 x 10/10) = 3. No training-crawler or opt-out-token directives appear at all (no GPTBot, ClaudeBot, CCBot, Google-Extended, Applebot-Extended lines), and no Content-Signal directive — unlike docs.stripe.com, whose robots.txt carries 'Content-Signal: ai-train=yes, search=yes, ai-input=yes'.

**✓ `p1.retrieval-reachable` 3/3**

Requested https://stripe.com/ once per retrieval user-agent. All 10 returned HTTP 200 with the real page: OAI-SearchBot, ChatGPT-User, Googlebot, Bingbot, Applebot, PerplexityBot each returned 651,619-652,730 bytes and 12,800 chars of script-stripped body text; Claude-SearchBot, Claude-User, Perplexity-User, Amazonbot returned 660,522-661,633 bytes and 13,255 chars (the larger variant serves an extra 'Guide me' recommender module — an A/B treatment, not a challenge). Every response carried the real hero <h1 data-testid="homepage-hero-title"> and the Organization/WebSite JSON-LD block. No 403, no challenge page, no interstitial. floor(3 x 10/10) = 3.

**✓ `p1.llms-txt` 3/3**

https://stripe.com/llms.txt returns 200, 65,026 bytes, 379 lines of valid Markdown. One H1 ('# Stripe'), one summary blockquote ('> Stripe is a technology company that provides financial infrastructure for businesses...'), 30 '##' sectioned link groups (Payments, Connect, Payment Links, Checkout, Elements, Billing, Invoicing, Tax, Atlas, Terminal, Radar, Issuing, Revenue Recognition, Identity, Financial Connections, Treasury, Capital, Data Pipeline, Sigma, Climate, Link, Global Payouts, Crypto, Solutions, Ecosystem, Documentation, Resources, Other, External domains, Optional) and 285 '- [title](url): description' link lines. Requirement is >=3 sectioned groups; this has 30.

**✗ `p1.llms-full-txt` 0/2**

https://stripe.com/llms-full.txt returns HTTP 404 (following redirects). The response body is 367,569 bytes because Stripe serves a full rendered HTML 404 page rather than an empty body — status code, not body size, is the test. https://docs.stripe.com/llms-full.txt also returns 404. (docs.stripe.com does serve /llms.txt at 200 and a .md twin for every docs page, e.g. docs.stripe.com/payments.md 200 text/markdown, but that is a different host and outside this target.)

**✗ `p1.ai-txt` 0/2**

https://stripe.com/ai.txt returns HTTP 404 (367,569-byte HTML 404 page). Also checked https://stripe.com/.well-known/ai.txt -> 404 and https://stripe.com/ai-policy -> 404. No AI usage-policy file at any of those locations.

**✓ `p1.sitemap` 3/3**

robots.txt line 1 declares 'Sitemap: https://stripe.com/sitemap/sitemap.xml'. That URL returns 200, application/xml, 805 bytes: a <sitemapindex> naming 9 partitions. All 9 partitions return 200 (1.1 MB - 6.9 MB each) for 6,727 <url> entries in total. Locale coverage: 5,294 of 6,727 entries (79%) carry xhtml:link alternates; the homepage entry alone declares 76 hreflang alternates (de-AT ... zh-US), matching the 89 alternate <link> tags in the homepage <head>. Localized pages are exposed as hreflang alternates on the canonical <loc> rather than as separate <loc> entries, which is a valid pattern. Two caveats worth recording: the literal path https://stripe.com/sitemap.xml returns 404 (the file lives one level down, at the robots.txt-declared path), and not a single <lastmod> element appears anywhere in the 9 partitions.

**✗ `p1.geo-link-tags` 0/2**

The homepage <head> is 23,569 bytes and contains 0 occurrences of rel="llms", rel="llms-full" or rel="ai-policy". It does carry canonical, 89 rel=alternate hreflang tags, 4 icon tags, preload/preconnect and stylesheet links. Same result on all 8 sampled pages. The llms.txt file exists and is substantial but nothing in the HTML points a crawler at it.

**✓ `p1.ssr-content` 2/2**

Checked specifically because the site is a Next.js app. Fetching https://stripe.com/ with curl and no JavaScript execution returns 651,619 bytes; after stripping <script>, <style>, <svg>, <noscript> and comments the body still holds 12,800 characters / 1,875 words of visible text and 57 headings. The primary content is genuinely server-rendered: '<h1 class="hds-heading hero-section__title..." data-testid="homepage-hero-title">Financial infrastructure to grow your revenue...' appears at byte offset 42,102 in the raw HTML, outside any <script> or <template> (the document contains 0 <template> tags). Section headings ('Flexible solutions for every business model.', 'The backbone of global commerce', 'Powering businesses of all sizes.') and the stat block ('$1.9T in payments volume processed in 2025', '99.999% historical uptime') are all present without JS. The four sampled product/article pages likewise return 10,729-29,538 chars of no-JS text. A reported ~57-character SSR body did not reproduce; 57 is the heading count, not the character count.

## Structured Data — 4 / 20

**✗ `p2.organization-website` 0/4**

The homepage carries one 6,818-byte JSON-LD @graph with a complete WebSite node and an Organization node (@id https://stripe.com/#organization, legalName 'Stripe, LLC', two Person founders, logo, contactPoint, 12 sameAs URLs, 22 Place locations). But it is homepage-only. /payments, /connect and /payments/payment-links contain 0 JSON-LD blocks of any kind. /pricing and /billing carry a FAQPage block and nothing else. The 4 sampled blog posts carry an Article/BlogPosting block and nothing else. /resources pages carry an Article block whose publisher is a bare {'@id':'https://stripe.com/#organization'} pointer to a node that is not present on that page. The check requires valid Organization + WebSite JSON-LD on every indexable page; observed on 1 of the 10 non-article pages read.

**✓ `p2.article-author` 4/4**

All 4 sampled articles carry @type ['Article','BlogPosting'] with a Person author that has a resolvable identity: 'Scott Woody' (linkedin.com/in/scott-woody-21677121), 'Siddharth Kulkarni' + 'Mitchell Martins-Collum' (two authors, both with LinkedIn URLs), 'Bart Heideman' (ie.linkedin.com/in/bartheideman), 'Abhi Tiwari' (linkedin.com/in/abhinav-tiwari-4687117). floor(4 x 4/4) = 4. Recorded but not scored here, because it falls outside the rule-3 sample: the far larger /resources learning-centre library (3,358 of 6,727 sitemap URLs) also emits Article JSON-LD, but with "author": null on every page checked (7 of 7).

**✗ `p2.faqpage` 0/3**

Surveyed 15 pages for Q&A structure; 13 are genuinely structured as questions. FAQPage is declared on 3 of them: /pricing (5 Question nodes), /billing (3), /radar. It is absent from the other 10: /legal/dpa/faqs (10 question <h2>s, no schema), /resources/more/what-is-a-payment-vault (6), /resources/more/how-do-vat-taxes-work (7), /resources/more/what-is-dynamic-payment-routing (7), /resources/more/what-is-link (7), /resources/more/what-is-a-discount-code (6), /resources/more/what-is-par-value (5), /resources/more/what-is-a-data-pipeline (6), /resources/more/what-is-elt (6), /resources/more/what-is-data-ingestion (6). floor(3 x 3/13) = 0. Two pages counted as not Q&A-structured (/india-data-storage-faq, /startups/partner-benefits-faq) and three that only link out to FAQs (/identity, /climate, /capital) were excluded from the denominator. The gap is concentrated in the 3,358-URL /resources library, which is the site's largest question-shaped surface and carries no FAQPage anywhere sampled.

**✗ `p2.speakable` 0/3**

0 occurrences of the string 'speakable' across all 8 sampled pages and the 12 additional pages read (homepage, 3 product pages, 4 articles, /pricing, /billing, /radar, /tax, /terminal, /issuing, /atlas, /identity, /climate, /treasury, /capital, 2 /resources pages, 1 /guides page). The 4 blog posts and the /connect hero do have clear answer passages that would qualify for a speakable declaration; none is declared.

**✗ `p2.product-offer` 0/3**

Applies: Stripe is a commercial site with a dedicated /pricing page and per-product pricing pages. /pricing returns 200 (977,065 bytes) and contains exactly one JSON-LD block, a FAQPage — 0 occurrences of '"Product"' or '"Offer"'. The published rate card ('Starts at 2.9% + 30c per successful charge', /billing/pricing, /connect/pricing, /invoicing/pricing, /tax/pricing) is rendered as HTML only. /payments, /connect and /payments/payment-links carry no JSON-LD at all. No Product or Offer node found on any page read.

**✗ `p2.howto-breadcrumb` 0/3**

Applies on both halves of the check. Procedures exist: the sitemap contains /resources/more/how-to-start-a-plumbing-business, /how-to-start-a-trucking-company, /how-to-start-an-llc-in-texas and hundreds of similar step-by-step pages. Hierarchy exists: URLs nest three and four levels deep (/payments/payment-links, /guides/atlas/creating-your-founding-documents, /legal/dpa/faqs). Yet 0 occurrences of 'HowTo' and 0 of 'BreadcrumbList' across all 20 pages read. /resources/more/how-to-start-a-plumbing-business carries only a generic Article block; /guides/atlas/creating-your-founding-documents carries no JSON-LD at all.

## Content Citability — 7 / 25

**✓ `p3.answer-passages` 1/5**

Criterion applied: the first body paragraph of the page's main section must be 40-90 words and answer the page's own question standalone. 3 of 8 pass. PASS — /connect (45 words: 'The world's most successful platforms and marketplaces, including Shopify and DoorDash, use Stripe Connect to embed payments into their products. Connect offers seamless onboarding, embedded components, global payouts...'); /blog/why-global-workers... (53 words, opens with the survey finding itself); /blog/mapping-the-ai-economy (84 words, states the data position and the headline figure). FAIL — homepage (longest opening paragraph 23 words); /payments (22 words); /payments/payment-links (28 words); /blog/five-monetization-trends (58 words but scene-setting, names none of the five trends); /blog/reduce-fx-costs (39 words, under the floor, and describes the problem rather than the capability). floor(5 x 3/8) = 1.

**✓ `p3.sourced-statistics` 1/5**

Scored per page over the 8-URL sample; 3 pass. PASS — /blog/why-global-workers... (all 8 numeric claims trace to one named, linked source, 'A Stripe survey of more than 2,300 independent workers in 20 countries', linked to the published report, plus outbound links to Deel, Ramp and Coindesk); /blog/mapping-the-ai-economy (13 claims; methodology stated in prose and the external and prior-analysis claims are linked — Pew Research, Salesforce newsroom, /customers/runway, /customers/gamma, two prior Stripe analyses); /payments/payment-links (makes no numeric claims at all, so carries no unsourced ones — a vacuous pass, flagged for transparency). FAIL — homepage (the 'backbone of global commerce' block asserts '135+ currencies', '$1.9T in payments volume processed in 2025', '99.999% historical uptime', '200M+ active subscriptions' with no citation; '50% of Fortune 100' and '88% of the Forbes AI 50' likewise unlinked); /payments ('Businesses see a 3.8% revenue increase and 32% lower fraud on average', '2x average payment growth rate' — unattributed, though the Slack/Twilio/GitHub customer figures do link to case studies); /connect (stat block '17,000+', '13+', '11M+', '$1B+' with zero attribution); /blog/five-monetization-trends (the load-bearing '120% average growth, on pace for 175% in 2026' is unlinked); /blog/reduce-fx-costs (4 first-party figures — 40% annual cross-border growth, 35% adoption growth, 50% repeat conversion — none linked to a methodology). floor(5 x 3/8) = 1; dropping the vacuous pass gives 2 of 8, which floors to 1 as well.

**✓ `p3.named-author` 5/5**

Denominator is the 4 authored pages in the sample; the homepage and 3 product pages carry no byline by design, matching the rubric's own worked example which scores this check over articles rather than the full 8. All 4 name a real person with a role title rendered on the page and an external identity link: 'Scott Woody' (CEO, Metronome); 'Siddharth Kulkarni, Quant Research Lead, Link' and 'Mitchell Martins-Collum, UX Research Lead, Money Management'; 'Bart Heideman'; 'Abhi Tiwari'. Each name resolves to a LinkedIn profile in both the byline and the JSON-LD author node. No 'admin', no brand-name bylines. floor(5 x 4/4) = 5. Counterweight recorded in notes: the /resources library ships "author": null.

**✗ `p3.natural-questions` 0/5**

0 of the 8 sampled pages carry a substantive heading phrased as a question. The only interrogative headings anywhere in the sample are navigation and footer chrome: 'Ready to get started?' (/, /payments), 'Don't code?' (/), 'Ready to start?' (/connect), 'Have any feedback or questions?' and 'Like this post?' (all 4 articles), 'Not sure where to start?' (nav). Content headings are declarative marketing or thesis statements: 'Convert more customers', 'Expand to new markets faster', 'The focus on ARR is holding software companies back from more flexible monetization'. They are natural-language prose, not keyword strings — the failure is the absence of interrogative framing, not stuffing. floor(5 x 0/8) = 0. Important sampling artefact, recorded in notes: outside the rule-3 sample, the 3,358-URL /resources library is almost entirely question-headed (5-7 question <h2>s per page, e.g. 'What is a payment vault?', 'How do VAT taxes work in the supply chain?').

**✗ `p3.freshness` 0/5**

0 occurrences of 'dateModified' across all 8 sampled pages and all 12 additional pages read; 0 occurrences of article:modified_time or og:updated_time; and 0 <lastmod> elements in any of the 9 sitemap partitions. There is therefore no machine-readable freshness signal anywhere on the site. datePublished does exist and is recent — 2026-08-20, 2026-08-19, 2026-08-17 and 2026-08-11 on the 4 sampled articles, all within 20-28 days of the audit date, and 2026-08-24 on the most recent /resources pages checked — but the check is specifically dateModified, and product and pricing pages carry no date of any kind. floor(5 x 0/8) = 0.

## Brand Authority — 19 / 20

**✓ `p4.knowledge-graph` 5/5**

The homepage Organization node's sameAs array includes https://www.wikidata.org/wiki/Q7624104. Fetched Special:EntityData/Q7624104.json: HTTP 200, English label 'Stripe', description 'Irish-American payment technology company', 56 property claims, 28 sitelinks, and P856 (official website) = 'https://stripe.com/' — so the reference resolves in both directions. The same sameAs array also carries https://en.wikipedia.org/wiki/Stripe,_Inc. (200, 472,653 bytes, 1,067 occurrences of 'Stripe').

**✓ `p4.third-party-listings` 5/5**

Verified two independent directories at 200 without needing credentials: https://www.ycombinator.com/companies/stripe (200, title 'Stripe: Economic infrastructure for the internet. | Y Combinator', 85 brand mentions) and https://wordpress.org/plugins/woocommerce-gateway-stripe/ (200, a public plugin directory listing with user ratings, 220 brand mentions). Wikipedia and Wikidata add authority records. Note on method: the dedicated review sites all sit behind bot walls to a plain fetch — G2 403, Capterra 403 (Cloudflare 'Attention Required'), TrustRadius 403, Trustpilot 403, Gartner Peer Insights 403 — so their listings were neither confirmed nor denied; the check passes on the two that were directly observable.

**✓ `p4.video-presence` 4/4**

Two YouTube channels appear in the homepage sameAs array and both resolve with published content: https://www.youtube.com/@stripe (200, title 'Stripe - YouTube', 30 distinct videoIds on the /videos tab) and https://www.youtube.com/@StripeDev (200, title 'Stripe Developers - YouTube', 30 distinct videoIds). Linked from the site, live, and populated.

**✓ `p4.independent-mentions` 3/3**

Observed on domains Stripe does not control: en.wikipedia.org/wiki/Stripe,_Inc. (200, a full editorially-maintained encyclopedia article, 1,067 brand mentions); wikidata.org/wiki/Q7624104 (200, 56 claims, 28 language sitelinks); ycombinator.com/companies/stripe (200, third-party company profile); wordpress.org/plugins/woocommerce-gateway-stripe/ (200, third-party plugin directory with public user reviews). The 403 responses from G2, Capterra, TrustRadius, Trustpilot and Gartner indicate listings exist behind bot protection but were not read.

**✓ `p4.sameas-resolve` 2/3**

12 sameAs URLs in the homepage Organization node, each fetched with redirects followed and a browser user-agent. 9 return 200 and reference the brand back: twitter.com/stripe -> x.com/stripe (200, <title>Stripe (@stripe) / X</title>, og:description 'Stripe builds programmable financial services'); youtube.com/@stripe (200); youtube.com/@StripeDev (200); linkedin.com/company/stripe/ (200, 263 brand mentions — returned 429 on a first, plainer request, so this needed a retry with full browser headers); facebook.com/StripeHQ (200, 104 mentions — a first request without browser headers redirected to /login and returned 400); en.wikipedia.org/wiki/Stripe,_Inc. (200); github.com/stripe (200); instagram.com/stripehq/ (200); wikidata.org/wiki/Q7624104 (200). 1 is dead: finance.yahoo.com/quote/STRI.PVT/ returns HTTP 404, 502 bytes — Yahoo Finance no longer hosts that private-company quote page. 2 could not be read from here: crunchbase.com/organization/stripe (403) and bloomberg.com/profile/company/0170016D:US (403), both bot walls rather than evidence of a missing page. floor(3 x 9/12) = 2. Scoring the two bot-walled URLs as live instead gives 11/12, which also floors to 2, so the result is stable either way.

## Platform Visibility — 1 / 3

**⊘ `p5.search-console` — unobservable**

Checked what is externally visible: no google-site-verification <meta> tag in the homepage <head> (23,569 bytes examined) and no /google*.html verification file referenced anywhere. Absence of a meta tag proves nothing, since DNS TXT and Google Analytics verification leave no on-page trace. Points removed from the denominator rather than scored 0.

**⊘ `p5.bing-webmaster` — unobservable**

No msvalidate.01 <meta> tag in the homepage <head>, and no BingSiteAuth.xml referenced. As with Search Console, verification can be completed by DNS or file upload without leaving an observable on-page signal, so absence is not evidence. Points removed from the denominator rather than scored 0.

**⊘ `p5.multi-engine-cited` — unobservable**

No query set was executed against ChatGPT, Perplexity, Claude, Copilot, Gemini or AI Overviews, and no engine exposes a citation history for a third-party domain. Simulating or predicting the result would be a guess, so the 3 points are removed from the denominator. Re-running this check requires the fixed query set to be run manually and published alongside the score.

**✓ `p5.answer-shape-fit` 1/3**

Criterion applied: a page fits when its body is extractable prose — one content-level H1, sequential H2 sections, and paragraphs long enough to lift as an answer. 4 of 8 fit. FIT — all 4 blog posts: each has a single article H1, 3-6 sequential H2 sections and 1,483-2,586 words of continuous prose with paragraphs in the 40-90 word band. NOT FIT — homepage and the 3 product pages: /payments has 68 <h1> elements and 8 <h2>, /connect 67 <h1> and 5 <h2>, /payments/payment-links 40 <h1> and 5 <h2>, with H2 used as small eyebrow labels above the H1s, so the document outline is inverted; their copy is 2,012-4,099 words of short fragments and text baked into interactive UI mock-ups (card numbers, receipts, dashboards) rather than paragraphs, and the longest opening passage across the three is 45 words. The homepage carries 1,875 words but its longest paragraph is 23 words. floor(3 x 4/8) = 1.

**⊘ `p5.non-english-engines` — unobservable**

Audience is multilingual by direct observation: the homepage <head> declares 89 rel=alternate hreflang tags and the sitemap declares 76 distinct locales across 11 languages, including zh-CN, zh-HK, zh-SG, zh-MY, zh-US, ja-JP, th-TH, plus de, fr, es, it, pt, nl and sv variants. Localized paths (/cn, /jp, /th, /br, /mx, /de, /fr, /es, /se, /nl, /it) are live and enumerated in the sitemap. So the check applies. What cannot be observed is the outcome: like p5.multi-engine-cited, it requires manually running a query set against regional engines. Points removed from the denominator rather than scored 0.

## Excluded from the denominator

| Check | Pts | Why |
|---|:-:|---|
| `p5.search-console` | 3 | External audit; verification state lives inside the owner's Google account and can be completed via DNS without an on-page trace. |
| `p5.bing-webmaster` | 3 | External audit; submission and index state live inside the owner's Bing Webmaster account. |
| `p5.multi-engine-cited` | 3 | Needs a human to run a fixed >=10-query buyer-intent set against >=3 engines and record citations. Not run; the outcome is not inferable over HTTP. |
| `p5.non-english-engines` | 3 | Audience is multilingual (76 sitemap locales, 89 hreflang tags), so the check applies, but no regional-engine query set was run and the owner's testing practice is not externally visible. |

## Auditor's caveats

*Where this audit made a judgement call, or could not verify something.*

- 任务给的两条『已知』事实经我重抓后不成立，我按自己的观测改了判定：(1) sitemap.xml 确实 404，但 robots.txt 第一行声明的是 https://stripe.com/sitemap/sitemap.xml，返回 200，索引 9 个分片共 6727 条 URL、76 个 locale，所以 p1.sitemap 我给了满分 3/3；(2) 首页 SSR 正文不是 57 字符——不执行 JS 抓取后正文有 12,800 字符/1,875 词，hero <h1> 在原始 HTML 第 42,102 字节处、页面 0 个 <template>，57 是标题数不是字符数，所以 p1.ssr-content 给 2/2。这两条我用 10 个不同的检索型 UA 各复核过一遍。如果复查者拿到的是不同结果，请以状态码和无 JS 抓取的正文字符数为准。
- 抽样规则 3 我做了两处替换，这是本报告最可能被挑战的地方。整个 sitemap 的 9 个分片里一个 <lastmod> 都没有，源站也不返回 Last-Modified 头，所以『最近修改的 3 个产品页』根本观察不到。我用的替代规则是『llms.txt 前三个 ## 分节里各取第一个产品链接』，得到 /payments、/connect、/payments/payment-links——理由是确定性且读自 Stripe 自己发布的文件，但这是我定的规则，不是 rubric 定的。换一条规则（比如取 /pricing）会得到不同的抽样。
- 『文章』我取自 /blog（有署名、有日期的编辑内容），没取 /resources。这个选择影响很大：/resources 有 3,358 条 URL（占 sitemap 一半），几乎每页都是问句标题（5–7 个问句 h2），但 JSON-LD 里 author 全是 null。如果复查者把 /resources 当作『文章』来抽样，p3.natural-questions 会从 0 分变高，而 p2.article-author（我给 4/4）和 p3.named-author（我给 5/5）会崩掉。两边大致抵消但单项差好几分，所以这份报告的分项不一定能被逐行复现。
- p2.faqpage 的分母是我自己划的。我调查了 15 个页面，判定其中 13 个是问答结构，3 个带 FAQPage，得 floor(3×3/13)=0。分母大小完全取决于我调查了多少页——多查几个带 FAQPage 的产品页，或少查几个 /resources 页，结果就会不同。这是无界分母比例题的固有问题，我把调查过的每一个 URL 都列进了 sampled_urls 以便复核。
- p3.sourced-statistics 我按『页』算（8 页中 3 页通过），但 rubric 自带的示例报告是按『条数字声明』算的（『11 numeric claims, 2 carry a source』）。我在 1MB 的营销页上做不出可复现的逐条计数，所以退到页级并写明了。粗略的条级重算大约会给 2 分而不是 1 分。另外 /payments/payment-links 是『没有任何数字声明所以没有未标注来源的声明』的空真通过，我在 evidence 里标了；去掉它变成 2/8，floor 后仍是 1 分，所以这一项结论稳。
- p3.answer-passages 和 p5.answer-shape-fit 都需要我自己定一个可判定的标准（前者：主区首段 40–90 词且能独立回答页面标题的问题；后者：单一内容 H1 + 顺序 H2 + 可摘取的段落）。标准写进了 evidence，但换个判官会有不同的边界判断，尤其是 /blog/five-monetization-trends（58 词但只铺垫不作答，我判 fail）和 /blog/mapping-the-ai-economy（84 词但以设问收尾，我判 pass）。
- p3.natural-questions 我判 0 分用的是『是否有实质性的疑问句标题』这个口径（和 rubric 示例报告『headings phrased as natural questions on 5 of 8』的措辞一致）。但 pass 条件原文是『不是关键词串』，而 Stripe 的标题全是自然语言完整句、完全不是关键词堆砌。按后一种读法这项不该是 0。我在 evidence 里写清了这个区别。
- review 类站点（G2、Capterra、TrustRadius、Trustpilot、Gartner）以及 Crunchbase、Bloomberg 全部对 curl 返回 403 Cloudflare 墙，我既无法确认也无法否认那里的 listing。p4.third-party-listings 我是靠 Y Combinator 目录和 WordPress.org 插件目录这两个能直接读到 200 的独立目录判过的；p4.sameas-resolve 里我把这两个 403 记为『读不到』而不是失败——即便把它们算作有效（11/12），floor 后仍是 2 分，所以这一项结论不受影响。
- p5.non-english-engines 我标 unobservable 而不是 not_applicable：Stripe 受众明确不是纯英语（89 个 hreflang、76 个 locale、11 种语言，/cn /jp /th 都是活的），所以规则 6 的豁免不成立；但『是否测过对应区域引擎』是站主的流程事实，外部看不到，我也没跑百度/Yandex/Naver 的问题集。有人可能认为这该判 failed，那会让分母变成 91、分数 45/91（49%），band 仍是 Below average。
- audience_language 我填了 'mul'（BCP-47 的多语言码）。如果发布方希望填单一主语言，应该是 'en-US'（x-default 和 canonical 都指向它），但那会让人误以为非英语引擎那项应判 not_applicable。
- 这是 2026-09-08 单一时点、单一出口 IP、纯 curl（不执行 JS）的读数。Cloudflare 之类的边缘策略可能对不同地区、不同时间的同一 UA 返回不同结果，Pillar 1 的可达性尤其可能随时间变化。

## Notes

AIV 45 / 88 (v1.0) - normalised 51% - Below average, audited 2026-09-08.

SHAPE OF THE RESULT. Two pillars sit at opposite ends. Brand Authority scores 19 of 20: the homepage ships a 6,818-byte Organization/WebSite @graph with 12 sameAs targets, a live Wikidata item (Q7624104, 56 claims, 28 sitelinks, P856 pointing back to stripe.com), a Wikipedia article, two populated YouTube channels and third-party directory listings. Structured Data scores 4 of 20, and Content Citability 7 of 25. The gap is not neglect - it is a house style. Stripe's marketing pages are visually engineered: copy is short, confident fragments arranged around interactive product mock-ups, with 40-68 <h1> elements per page and <h2> reserved for small eyebrow labels above them. That reads beautifully to a person and poorly to a passage retriever, which wants one H1, ordered H2s and 40-90 word self-contained paragraphs. This is a trade-off, not a defect, and it is worth naming as one.

WHAT THE PRE-AUDIT BRIEF GOT WRONG. Two of the three 'known' facts handed to this audit did not survive a re-fetch. (1) 'sitemap.xml 404' - true of the literal path, but robots.txt line 1 declares https://stripe.com/sitemap/sitemap.xml, which returns 200 and indexes 9 partitions holding 6,727 URLs and 76 locales. The check passes 3/3. (2) 'homepage SSR body ~57 characters, probably fully client-rendered' - did not reproduce. A no-JS fetch returns 12,800 characters and 1,875 words of visible body text, with the hero <h1> at byte offset 42,102 in the raw HTML and 0 <template> tags. 57 is the heading count. The check passes 2/2. Both were re-verified with 10 different retrieval user-agents. Only the third, the 65 KB llms.txt, held up as stated.

SAMPLING (rule 3). The first 8 URLs in sampled_urls are the rule-3 sample; the remaining 69 are every additional URL the audit read, listed so the score can be reproduced. Two substitutions had to be made and should be checked by anyone re-scoring. First, the sitemap contains no <lastmod> element anywhere and Stripe's origin returns no Last-Modified header, so 'the 3 most recently modified product/service pages' is not observable. The substitute rule used, chosen because it is deterministic and reads from a published Stripe file: the first product link in each of the first three '##' sections of llms.txt, giving /payments, /connect and /payments/payment-links. Second, 'the 4 most recently modified articles' was read from the /blog index, which does render dates: 2026-08-20, 08-19, 08-17 and 08-11 are the four most recent.

THE SAMPLING ARTEFACT THAT MATTERS MOST. Rule 3's sample lands entirely on the marketing site and misses /resources, which is 3,358 of the 6,727 sitemap URLs - half the site. That library is the mirror image of the pages sampled: almost every page is a question ('What is a payment vault?', 'How do VAT taxes work in the supply chain?') with 5-7 question <h2>s. Had the sample drawn from it, p3.natural-questions would have scored well instead of 0. Conversely those pages ship "author": null (7 of 7 checked), so p2.article-author and p3.named-author, which scored 4/4 and 5/5 on the bylined blog, would have collapsed. The two effects roughly cancel in total but they move individual lines by several points each, so a re-score that samples /resources as its 'articles' is a legitimately different reading of rule 3 and will not match this one line for line.

CHEAPEST STRUCTURAL GAPS, stated as observations rather than advice: llms.txt exists and is thorough but no <link rel="llms"> points at it; no dateModified exists anywhere on the site, in HTML or in the sitemap; the /pricing page carries a FAQPage but no Product or Offer; and 3,358 question-shaped pages carry no FAQPage. One sameAs link is genuinely dead - finance.yahoo.com/quote/STRI.PVT/ returns 404.

METHOD NOTES. Every existence test was decided on the HTTP status code alone: stripe.com serves a full 367,569-byte rendered HTML page on 404, so llms-full.txt, ai.txt and sitemap.xml all return large bodies while being absent. All fetches followed redirects. Bot walls were distinguished from dead links by retrying with full browser headers - LinkedIn (429) and Facebook (400) both became 200 on retry and were counted as live; Crunchbase, Bloomberg, G2, Capterra, TrustRadius, Trustpilot and Gartner stayed at 403 and were reported as unread rather than as failures. Nothing in Pillar 5 was simulated. docs.stripe.com is a separate host and was excluded from scoring, but for context it does what stripe.com does not: its own /llms.txt at 200, a .md twin for every documentation page, and a 'Content-Signal: ai-train=yes, search=yes, ai-input=yes' directive in robots.txt that stripe.com's own robots.txt lacks.
