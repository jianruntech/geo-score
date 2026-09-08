# anthropic.com — AIV 32 / 88 (v1.0)

**36% · Critical** · audited 2026-09-08 · audience `en`

> 全站可达性接近满分——10 个检索爬虫全部拿到 200 和完整 SSR 正文——但 8 个抽样页面里只有 1 段 JSON-LD（三个模型页重复的 FAQPage），Organization/sameAs 一处都没有；llms.txt 存在于 docs.claude.com 和 claude.com（均 200），唯独 anthropic.com 是 404。

Machine-readable: [`anthropic.com.json`](anthropic.com.json)

## Sampled URLs (8)

- `https://www.anthropic.com/`
- `https://www.anthropic.com/claude/fable`
- `https://www.anthropic.com/claude/sonnet`
- `https://www.anthropic.com/claude/opus`
- `https://www.anthropic.com/research/formalizing-fermats-last-theorem`
- `https://www.anthropic.com/news/improving-alignment-security-efforts`
- `https://www.anthropic.com/research/india-brief-economic-index`
- `https://www.anthropic.com/research/reviewing-the-evidence-on-worker-retraining-programs`

## Infrastructure — 11 / 20

**✓ `p1.robots-allows-retrieval` 3/3**

robots.txt returns 200, 71 bytes, and its entire body is: "User-Agent: *" / "Allow: /" / "Sitemap: https://www.anthropic.com/sitemap.xml". No Disallow line, no per-agent block, no opt-out token. All 10 retrieval user-agents in reference/ai-crawlers.md are therefore allowed: floor(3 x 10/10) = 3.

**✓ `p1.retrieval-reachable` 3/3**

Requested the homepage once per retrieval user-agent (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User, Googlebot, Bingbot, Applebot, Amazonbot). All 10 returned HTTP 200 with a byte-identical 176,945-byte body carrying <title>Home \ Anthropic</title>, the H1 "AI research and products that put safety at the frontier" and the footer nav - not a challenge page or interstitial. floor(3 x 10/10) = 3.

**✗ `p1.llms-txt` 0/3**

GET /llms.txt returns HTTP 404 (verified with -L on both https://anthropic.com/llms.txt and https://www.anthropic.com/llms.txt, and under Chrome, Googlebot and OAI-SearchBot user-agents - 404 every time). The response body is 59,696 bytes of the site's HTML 404 page, so body size is not evidence of presence; only the status code is. Note: docs.claude.com/llms.txt and claude.com/llms.txt both return 200 (73,533 and 4,146 bytes), so the file exists on sibling Anthropic hosts but not on the audited one.

**✗ `p1.llms-full-txt` 0/2**

GET /llms-full.txt returns HTTP 404 with a 59,749-byte HTML 404 page. No alternate path found (/.well-known/llms-full.txt not present either).

**✗ `p1.ai-txt` 0/2**

GET /ai.txt returns HTTP 404 (59,735-byte HTML 404 page). /.well-known/ai.txt also returns HTTP 404 (59,806 bytes). robots.txt contains no AI-policy directive or pointer.

**✓ `p1.sitemap` 3/3**

sitemap.xml returns 200, 68,561 bytes, application/xml, a flat <urlset> of 524 <url> entries, every one carrying a <lastmod>. It is referenced from robots.txt line 4. The site is single-locale: <html lang="en">, zero hreflang/rel=alternate tags on any sampled page, and probes of /ja /ko /fr /de /es /zh-CN /pt-BR all return 404 - so there are no other indexable locales to cover. (Observed gap, not scored here: /pricing and /contact-sales 301 off-domain to claude.com, so they are not this host's pages.)

**✗ `p1.geo-link-tags` 0/2**

Enumerated every <link> element in <head> on all 8 sampled pages. Present: preconnect, stylesheet, preload, canonical, shortcut icon, apple-touch-icon, mask-icon. Absent on all 8: rel="llms", rel="llms-full", rel="ai-policy" (0 occurrences of any of the three strings in any sampled HTML).

**✓ `p1.ssr-content` 2/2**

Plain curl with no JavaScript execution returns the full primary content on all 8 pages. Extracted visible text after stripping <script>/<style>: homepage 4,859 chars, /claude/opus 13,444, FLT article 16,655, alignment-and-security article 26,592 (4,071 words) - full body prose, all H2/H3 headings and footnote text are in the delivered HTML. The homepage is Webflow-rendered, the other 7 are Next.js RSC; both stacks ship complete markup.

## Structured Data — 3 / 20

**✗ `p2.organization-website` 0/4**

The homepage carries zero <script type="application/ld+json"> blocks. Across all 8 sampled pages the strings "Organization" and "WebSite" appear 0 times as a JSON-LD @type. The only JSON-LD anywhere in the sample is one FAQPage block each on the three /claude/* pages. There is consequently no machine-readable brand entity, no logo, no url and no sameAs anywhere on the site.

**✗ `p2.article-author` 0/4**

0 of the 4 sampled article pages (/research/formalizing-fermats-last-theorem, /news/improving-alignment-security-efforts, /research/india-brief-economic-index, /research/reviewing-the-evidence-on-worker-retraining-programs) emit Article or BlogPosting JSON-LD - 0 occurrences of either @type. og:type is "website" rather than "article" on all four, and there is no article:published_time or article:author meta. floor(4 x 0/4) = 0.

**✓ `p2.faqpage` 3/3**

3 pages in the sample are structured as questions - /claude/fable, /claude/sonnet and /claude/opus each end in a "Frequently asked questions" H2 with question-phrased H3s - and all 3 emit valid FAQPage JSON-LD whose mainEntity Question/acceptedAnswer pairs match the rendered H3s (Fable 5 questions, Sonnet 2, Opus 2). No other sampled page is Q&A-structured. floor(3 x 3/3) = 3.

**✗ `p2.speakable` 0/3**

The string "speakable" appears 0 times in all 8 sampled HTML files (case-insensitive). At least 2 sampled pages have a clean answer passage that would qualify - the 49-word italic dek on the FLT article and the 90-word opening paragraph of the alignment-and-security post - so the check applies. floor(3 x 0/2) = 0.

**✗ `p2.product-offer` 0/3**

The three /claude/* pages are product pages in substance: H1 is the product name ("Claude Opus 4.8"), with "Availability and pricing" sections quoting concrete prices ("Claude Fable 5.1 is priced at $10 per million input tokens and $50 per million output tokens"; "Pricing for Opus 5 starts at $5 per million input tokens") and "Get API access" CTAs. Neither "Product" nor "Offer" appears as a JSON-LD @type on any of them. Note: the transactional pricing page itself lives off-domain - /pricing 301s to claude.com/pricing - so only these on-domain product pages were scorable.

**✗ `p2.howto-breadcrumb` 0/3**

Every sampled page sits in a two-level hierarchy and renders its parent as a visible eyebrow label above the H1 ("Science" on the FLT article, "Economics" on both economics briefs, "Announcements" on the news post, "Claude" on /claude/fable), so the hierarchy condition applies. "BreadcrumbList" appears 0 times across all 8 pages; "HowTo" also 0.

## Content Citability — 8 / 25

**✓ `p3.answer-passages` 1/5**

Measured the first substantive block after each H1. Inside the 40-90 word window and self-contained: FLT article 49 words (italic dek: "We are sharing the first complete computer-checked proof of Fermat's Last Theorem...") and the alignment-and-security post exactly 90 words ("On July 30, we reported three incidents..."). Outside it: homepage 24 words, /claude/fable 12, /claude/sonnet 18, /claude/opus 15 (all one-line product deks), worker-retraining 21, and the India brief 104 words - a strong executive-summary paragraph that misses only on length. 2 of 8 -> floor(5 x 2/8) = 1.

**✓ `p3.sourced-statistics` 4/5**

Denominator is the 7 sampled pages that actually make numeric claims (the homepage makes none and is excluded from this check only). 6 attribute them: FLT article has a numbered Footnotes section linking en.wikipedia.org/wiki/Kepler_conjecture, github.com/flyspeck/flyspeck and ias.edu, plus github.com/anthropics/fermats-last-theorem behind the "13 million lines of Lean / 29,500 theorems" claims; the alignment post links aisi.gov.uk's own incident report for the UK AISI incident; the India brief has a Methodology section naming O*NET/SOC, the >=200-observation cutoff and a link to the fourth Anthropic Economic Index report behind figures like "45.2% of O*NET-mapped tasks" and "5.8% of total Claude.ai use"; the worker-retraining page attributes "56 randomized US studies" to a linked PDF (www-cdn.anthropic.com/.../WorkerRetraining.pdf) with a BibTeX block naming Roodman and Massenkoff; /claude/sonnet and /claude/opus carry benchmark footnotes naming harnesses and third parties ("Terminal-Bench 2.0: we used the Terminus-2 harness...", "MCP-Atlas: revised grading methodology from Scale AI") plus a system-card link. /claude/fable's Benchmarks section names its benchmarks but carries no link or footnote of its own. 6 of 7 -> floor(5 x 6/7) = 4.

**✓ `p3.named-author` 2/5**

Denominator is the 4 sampled article pages. No page in the sample has a byline element, an author link, or an author bio anywhere - the site publishes editorially in the corporate first person. Two do name individuals in machine-readable form inside their Citation blocks: the India brief's BibTeX reads author = {Ruth Appel}, and the worker-retraining page reads author = {Roodman, David and Massenkoff, Maxim} and repeats it in prose ("coauthored by independent researcher David Roodman and Anthropic's Maxim Massenkoff"). The FLT article names "Tianyi Peng, an Anthropic researcher" in the body but as a subject, not an author; the alignment post names no individual. Scored 2 of 4 on the reading that a named, identifiable individual satisfies the check; a strict reading that also requires an on-page bio scores 0 of 4, i.e. 0/5. floor(5 x 2/4) = 2.

**✓ `p3.natural-questions` 1/5**

Extracted every H1/H2/H3 from all 8 pages. 3 carry interrogative, assistant-style headings: /claude/fable ("When should I use Claude Fable 5.1?", "Why did you create new safeguards for Claude Fable 5.1?", "How does the fallback work?"), /claude/sonnet ("When should I use Claude Sonnet 5?", plus prompt-shaped H3s like "What should I look for when reviewing a Pull Request for a Python web app?") and /claude/opus. The other 5 use declarative section headings - none of them keyword strings, and the India brief's are answer-shaped ("India is among the leading countries in global AI adoption"), but none are phrased as a question. 3 of 8 -> floor(5 x 3/8) = 1. A looser reading that credits answer-shaped declaratives would give 4 of 8 -> 2.

**✗ `p3.freshness` 0/5**

No dateModified in any machine-readable form on any of the 8 pages: 0 schema.org dateModified, 0 <time> elements, 0 article:modified_time meta. The Next.js RSC payload does contain Sanity _updatedAt fields, but the values are identical across all 7 Next.js pages (2023-11-20T23:54:09Z, 2026-04-09T19:48:51Z, 2026-09-04T17:17:43Z), i.e. site-chrome documents rather than per-article timestamps. What exists instead: a rendered publication date on 7 of 8 pages (Sep 4 2026, Aug 31 2026, Aug 12 2026, Feb 16 2026 on the articles) as plain text, and <lastmod> on 524 of 524 sitemap URLs - but 18 of those, the homepage included, read 2026-09-08T08:31:41.600Z, equal to my fetch time, so lastmod is partly generated rather than a true modification date. 0 of 8.

## Brand Authority — 8 / 20

**✗ `p4.knowledge-graph` 0/5**

The authority record exists and is strong: Wikidata Q116758847 "Anthropic" returns 200, describes it as "American artificial intelligence corporation", carries P856 official website = https://www.anthropic.com/ (so the destination references the brand back), P571 inception 2021-01-26, and 57 sitelinks including en.wikipedia.org/wiki/Anthropic (200). The check fails on its second half only: the site references it via sameAs 0 times, because it emits no Organization JSON-LD at all. All-or-nothing, so 0/5 - the gap is the declaration, not the record.

**✓ `p4.third-party-listings` 5/5**

Independently maintained authority records confirmed by direct fetch: wikidata.org/wiki/Q116758847 returns 200 with <title>Anthropic - Wikidata</title> and 57 language sitelinks; en.wikipedia.org/wiki/Anthropic returns 200. Both are outside Anthropic's control and both point back at www.anthropic.com. (crunchbase.com/organization/anthropic and g2.com/products/claude/reviews returned 403 to my client - their own bot protection, not evidence of absence - so they are not counted either way.)

**✗ `p4.video-presence` 0/4**

The channel exists and publishes: youtube.com/@anthropic-ai returns 200 (1.16 MB) and its /videos tab returns 200 with 30 distinct videoId values in the delivered HTML. It is linked from the footer of every sampled page as a plain <a href="https://www.youtube.com/@anthropic-ai">. But the check requires the link to be in sameAs, and there are 0 sameAs properties on the site. All-or-nothing, so 0/4 despite the channel being real.

**✓ `p4.independent-mentions` 3/3**

Verified by fetch on domains Anthropic does not control: news.ycombinator.com/from?site=anthropic.com returns 200 and lists multiple discussion threads on the audited pages themselves ("Formalizing Fermat's Last Theorem", "Improving our alignment and security efforts", "Claude Fable 5.1"); aisi.gov.uk publishes its own incident report that the sampled news post links to; en.wikipedia.org/wiki/Anthropic returns 200.

**✗ `p4.sameas-resolve` 0/3**

There are no sameAs URLs to resolve: 0 occurrences of sameAs across all 8 sampled pages, a direct consequence of there being no Organization/WebSite JSON-LD. The brand profiles do exist as plain footer anchors and 2 of 3 resolve cleanly on direct fetch - x.com/AnthropicAI 200, youtube.com/@anthropic-ai 200, linkedin.com/company/anthropicresearch 429 (LinkedIn rate-limiting my client, not a broken link) - but none of them is declared as sameAs, so the proportional numerator and denominator are both empty and the check earns nothing.

## Platform Visibility — 2 / 3

**⊘ `p5.search-console` — unobservable**

Verification state lives inside the Search Console property and cannot be read from outside. The one public artifact: <meta name="google-site-verification" content="BqiAW_sWOg-KrPk-Accxm6ge9dtnFEyV6DB6vzVZSGs"> is present on all 8 sampled pages, which is consistent with a verified property but proves only that the token was published - not that verification succeeded or is still current. Reported as unobservable rather than scored either way.

**⊘ `p5.bing-webmaster` — unobservable**

Submission and index status are inside Bing Webmaster Tools and are not externally readable. What I could check is only weak negative evidence and does not decide it: no msvalidate.01 meta on any of the 8 pages, and /BingSiteAuth.xml returns 404. Bing verification can also be done by DNS record, so neither absence implies non-verification. Bingbot itself reaches the homepage with 200 (see p1.retrieval-reachable).

**⊘ `p5.multi-engine-cited` — unobservable**

This check requires a human to run a fixed set of >=10 buyer-intent queries against >=3 answer engines and record whether anthropic.com is cited. That cannot be done with curl or fetch, and I will not simulate or infer an engine's citation behaviour. Requires a manual query-set run before this check can be scored; its 3 points are removed from the denominator until then.

**✓ `p5.answer-shape-fit` 2/3**

6 of 8 sampled pages are shaped the way answer engines chunk and quote: the three /claude/* pages pair a scannable H2 spine (Availability and pricing / Use cases / Benchmarks / FAQ) with an explicit FAQ block, and the FLT article (2,561 words), the alignment post (4,071 words) and the India brief (1,808 words, opening with an "Executive summary" H2) are sectioned long-form with short paragraphs and footnotes. 2 do not: the homepage delivers only 695 words of extracted text, most of it navigation and release-card labels, and the worker-retraining page is a 739-word stub whose substance is a downloadable PDF. floor(3 x 6/8) = 2.

**⊘ `p5.non-english-engines` — not_applicable**

The audited host serves one language only: <html lang="en"> on every sampled page, zero hreflang or rel=alternate tags, no locale segments in the 524-URL sitemap, and probes of /ja /ko /fr /de /es /zh-CN /pt-BR all return 404. Per rule 6 the audience is English-speaking, so this check does not apply and is never awarded by default.

## Excluded from the denominator

| Check | Pts | Why |
|---|:-:|---|
| `p5.search-console` | 3 | Property verification state is only visible inside Search Console. A google-site-verification meta token is published on all 8 pages but does not prove the verification succeeded. |
| `p5.bing-webmaster` | 3 | Submission and index status are only visible inside Bing Webmaster Tools. No msvalidate.01 meta and /BingSiteAuth.xml 404, but DNS verification would leave no public trace. |
| `p5.multi-engine-cited` | 3 | Needs a human to run a fixed >=10 query buyer-intent set against >=3 engines and record citations. Not simulated. |
| `p5.non-english-engines` | 3 | Single-locale English site: lang=en, no hreflang, no locale paths (7 locale probes all 404). Rule 6. |

## Auditor's caveats

*Where this audit made a judgement call, or could not verify something.*

- 只用 curl 抓取，没有执行 JavaScript。如果站点通过 GTM 或客户端脚本注入 Organization/Article JSON-LD，我看不到——Pillar 2 的 0 分是「服务端未声明」的结论，不是「浏览器渲染后也没有」。这是本次审计最大的单一盲点，复查者可以用无头浏览器再跑一遍 p2 的六项。
- Pillar 3 有三项依赖读法，我在 evidence 里同时写了两种读法的分数：named-author（2/5 宽松 vs 0/5 严格要求 bio）、natural-questions（1/5 只算疑问句 vs 2/5 兼算答案式陈述句）、answer-passages 把印度经济简报的 executive summary 判为不通过——它 104 词，只超出 40–90 窗口上限 14 词，这是全篇最严苛的一次判定。三项合计的读法差异最多 3 分（32→35，归一化 36%→40%，仍在 Critical 带内）。
- p2.product-offer 判 failed 而非 not_applicable 是我的判断。/claude/* 页面确实标了每百万 token 的具体价格、有「Get API access」CTA，实质是产品页；但真正的交易页 /pricing 是 301 到 claude.com 的站外页。若审计者认为本域不存在商业页，这 3 分应移出分母，分数会变成 32/85 = 38%。
- crunchbase.com/organization/anthropic 和 g2.com/products/claude/reviews 对我的客户端返回 403（是它们自己的 bot 防护，不代表条目不存在），linkedin.com/company/anthropicresearch 返回 429（限流）。所以 p4.third-party-listings 的 5 分完全建立在 Wikidata + Wikipedia 两条可直接验证的记录上；把 Wikidata 算作「independent directory site」本身也是一个可以被质疑的归类。
- Search Console / Bing / 多引擎被引三项标 unobservable，这意味着 15 分的 Platform Visibility 里只有 3 分进了分母。observable_max=88 与任何自审报告（站主能看到 GSC 和 Bing）都不可直接比较——这正是 rubric 规则 5 要求打印分母的原因。
- sitemap 里 18 条 <lastmod> 等于我的抓取时刻（2026-09-08T08:31:41.600Z），是请求时生成的。这直接影响「最近修改」的抽样排序：我改用真实 lastmod 值排序，但另一个审计者若照字面取最新的 3 条，会抽到 /features/* 和 /claude-fable-and-mythos-5-1，样本不同、Pillar 2/3 的比例分也会不同。
- 样本只有 8 个 URL，站上有 524 个。/engineering/* 这类模板我没抽到，不能排除它们带有 Article schema 或 byline——虽然 /research 与 /news 共用同一套 Next.js 模板，横向一致的可能性很高。
- reference/ai-crawlers.md 与 rubric 正文对 p1.robots-allows-retrieval 的分值不一致（4 分 vs 3 分）。我按 v1.0.md 和 v1.0.json 的 3 分计；若按 reference 的 4 分，nominal max 就不是 100，这是 geo-score 仓库自身需要修的一处不一致。

## Notes

Sampling (rule 3). Homepage plus the 3 most recently modified product/service pages and the 4 most recently modified articles, taken from the 524-URL sitemap.xml. One caveat a re-runner needs: 18 sitemap entries, the homepage among them, carry <lastmod> 2026-09-08T08:31:41.600Z - exactly my fetch time - so those timestamps are generated at request time, not real modification dates. I therefore ordered by genuine lastmod values, which puts /claude/fable (2026-09-01), /claude/sonnet and /claude/opus (both 2026-06-09) at the top of the product/service set, and /research/formalizing-fermats-last-theorem (2026-09-07), /news/improving-alignment-security-efforts (2026-09-07), /research/india-brief-economic-index (2026-09-04) and /research/reviewing-the-evidence-on-worker-retraining-programs (2026-09-04) at the top of the article set. https://anthropic.com 301s to https://www.anthropic.com/; every fetch followed redirects, and presence was decided on status code alone - the site's 404 page returns ~59 KB of HTML, so body size would have been misleading.

The shape of this score. The two halves of the rubric split cleanly here. Everything about reaching and reading the site is close to ideal: an unrestricted robots.txt, all 10 retrieval crawlers served an identical 200 with the real page, a complete sitemap, and full prose delivered without JavaScript on both the Webflow homepage and the Next.js content stack - a 4,000-word article arrives whole in the first response. Everything about *declaring* what the pages are is nearly absent: 1 JSON-LD block across 8 pages, and it is the same FAQPage pattern repeated on three model pages. That single missing Organization block cascades: it is why knowledge-graph (0/5), video presence (0/4) and sameAs resolution (0/3) all score zero even though the Wikidata item, the 30-video YouTube channel and the social profiles all demonstrably exist and resolve. 12 of the 20 Brand Authority points are lost to a declaration gap rather than a corroboration gap - the corroboration is there.

Where this is a trade-off rather than a defect. Anthropic publishes its GEO files on the domains where its documentation lives, not on its brand site: docs.claude.com/llms.txt and claude.com/llms.txt both return 200 (73,533 and 4,146 bytes) while www.anthropic.com/llms.txt is a 404. Likewise the transactional pricing page 301s to claude.com. Read as a multi-domain architecture that is a coherent choice; read as an audit of this hostname it costs 7 points across llms.txt, llms-full.txt and ai.txt. Similarly, the absence of bylines is an editorial posture - the site publishes in the corporate first person, and its research pages carry BibTeX citation blocks instead - not an "admin" byline of the kind the rubric was written to catch.

Judgement calls a reviewer should check first. Three checks in Pillar 3 turn on a reading, and I have printed both readings in each evidence string: named-author scores 2/5 crediting individuals named in BibTeX blocks and 0/5 if an on-page bio is required; natural-questions scores 1/5 counting only interrogative headings and 2/5 if answer-shaped declaratives count; answer-passages excludes the India brief's executive summary at 104 words, 14 over the band's ceiling, which is the single harshest call in this report. Two more worth flagging: sourced-statistics uses a 7-page denominator because the homepage makes no numeric claims at all, and product-offer is scored as failed rather than not_applicable because the /claude/* pages quote per-token prices and are product pages in substance even though checkout lives on another domain.

Largest single gap: Structured Data, 3 of 20. Nothing else in the report is more than one JSON-LD block away from moving.

One inconsistency in the rubric materials themselves, noted for the maintainers: reference/ai-crawlers.md says the first Pillar 1 check awards 4 points, while rubric/v1.0.md and v1.0.json both say 3. I scored 3, per the rubric files.
