# nextjs.org — AIV 40 / 82 (v1.0)

**49% · Below average** · audited 2026-09-08 · audience `en`

> nextjs.org 给 AI 爬虫单独发 markdown、备了 3.97MB 语料，却把 JSON-LD 只留在 HTML 分支——10 个检索爬虫里有 6 个一条 schema 都看不到：AIV 40/82 (v1.0)，基础设施 16/20，可引用性 4/25。

Machine-readable: [`nextjs.org.json`](nextjs.org.json)

## Sampled URLs (8)

- `https://nextjs.org/`
- `https://nextjs.org/docs/app/api-reference/adapters/supported-providers`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/allowedDevOrigins`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`
- `https://nextjs.org/blog/how-we-closed-1500-github-issues`
- `https://nextjs.org/blog/turbopack-chunking`
- `https://nextjs.org/blog/nextjs-security-release-august-2026-update`
- `https://nextjs.org/blog/august-2026-security-release`

## Infrastructure — 16 / 20

**✓ `p1.robots-allows-retrieval` 3/3**

robots.txt returns 200 and is 40 bytes long. Its entire content is one line: `Sitemap: https://nextjs.org/sitemap.xml` (verified byte-exact with xxd). There is no User-agent stanza and no Disallow directive anywhere in the file, so none of the 10 retrieval crawlers in reference/ai-crawlers.md is disallowed. floor(3 x 10/10) = 3.

**✓ `p1.retrieval-reachable` 3/3**

Requested https://nextjs.org/ once per retrieval user-agent. All 10 returned 200 with the real page (the string 'The React Framework' present in every response, no challenge page, no interstitial). Note on the response shape: nextjs.org content-negotiates on user-agent. OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User and Amazonbot each received text/markdown, 3,939 bytes (the /llms.md orientation document); Googlebot received text/html, 345,712 bytes; bingbot and Applebot received text/html, 446,849 bytes. All 10 are reachable, so floor(3 x 10/10) = 3.

**✓ `p1.llms-txt` 3/3**

/llms.txt returns 200, text/plain, 12,724 bytes, 125 lines. Valid Markdown. One H1 ('# Next.js'), one summary blockquote ('> The React Framework for the Web'), 5 H2 sections of which 3 carry link groups: Documentation (6 links), Learn Next.js (4 links), Blog (35 links); 45 link-list items total. Meets the >=3 sectioned link groups bar exactly, with no margin.

**✓ `p1.llms-full-txt` 2/2**

The conventional root path https://nextjs.org/llms-full.txt returns 404 (x-matched-path: /404), as do /llms_full.txt and /llmsfull.txt. The full corpus resolves instead at https://nextjs.org/docs/llms-full.txt: 200, text/plain, content-length 3,970,025 bytes, i.e. 312x the size of /llms.txt. It is discoverable rather than hidden: /llms.txt links to it twice, and /.well-known/ai-catalog.json declares it as entry urn:ai:nextjs.org:docs:full. Scored because the rubric's pass condition for this check states only 'Resolves and is substantially longer than llms.txt' and pins no path, unlike the preceding check which explicitly requires /llms.txt. A reader who requires the root path would score this 0 and the site total 38/82.

**✗ `p1.ai-txt` 0/2**

https://nextjs.org/ai.txt returns 404 (content-type text/html, x-matched-path: /404, content-disposition filename="404"). https://nextjs.org/.well-known/ai.txt also returns 404. Judged on status code only; both 404 responses carry a 12,207-byte HTML body, which is the site's rendered 404 page, not a policy file.

**✓ `p1.sitemap` 3/3**

https://nextjs.org/sitemap.xml returns 200, application/xml, 103,007 bytes. Single flat urlset (no sitemapindex) with 734 <loc> entries, every one of which carries a <lastmod>. It is referenced from robots.txt - that reference is robots.txt's only line. The site is single-locale (JSON-LD WebSite declares inLanguage 'en'; no locale path prefix appears in any of the 734 URLs; no hreflang alternates in any sampled <head>), so 'all indexable locales' is one locale and it is covered. Spot-checked 9 paths: /docs/app/getting-started/installation, /docs/app/getting-started, /showcase, /blog, /learn, /docs/messages/no-unwanted-polyfillio all return 200 and are all present; /templates, /enterprise and /docs/16/app/getting-started are absent but also return 404 on this domain (they are off-domain links to vercel.com), so their absence is correct.

**✗ `p1.geo-link-tags` 0/2**

Grepped the <head> of all 8 sampled pages for rel values containing 'llms' or 'ai-policy': zero matches. Also checked the HTTP Link response header on the homepage and on a docs page - it carries only rel=preload entries for fonts and images. The site does publish a machine-readable pointer, but by a different mechanism the rubric does not name: <link rel="alternate" type="text/markdown" href="..."> on the homepage and both docs pages (blog pages instead use rel=alternate type=application/rss+xml), plus /.well-known/ai-catalog.json. None of these is rel="llms", rel="llms-full" or rel="ai-policy", so the check as written does not pass.

**✓ `p1.ssr-content` 2/2**

Fetched all 8 sampled URLs with curl (no JavaScript executed) using a Chrome 131 user-agent: all returned 200 text/html carrying the primary content. Homepage: 345,712 bytes of HTML yielding 7,722 characters of visible text after stripping script/style/tags, including the H1 'The React Framework for the Web', the feature sections and the customer testimonials. Docs and blog pages likewise: 8,568 / 7,973 / 10,284 / 10,269 / 13,419 / 2,417 / 3,357 visible characters respectively. This corrects the briefing figure of '~3.9KB SSR body': 3,939 bytes is the size of the markdown document nextjs.org serves to recognised AI user-agents, not the server-rendered HTML.

## Structured Data — 4 / 14

**✗ `p2.organization-website` 0/4**

Not sitewide. Homepage: one ld+json block with an @graph carrying SoftwareApplication (@id #software, softwareVersion 16.3.4), WebSite (@id #website) and Organization (@id #publisher, name 'Vercel'). But /docs/app/api-reference/config/next-config-js/allowedDevOrigins and .../serverActions carry only a TechArticle whose author is an inline Organization - no WebSite node. All 4 blog posts carry only a TechArticle with Person authors - no Organization node and no WebSite node. And /docs/app/api-reference/adapters/supported-providers contains zero ld+json blocks at all, despite being the single most recently modified URL in the sitemap. All-or-nothing, so 0.

**✓ `p2.article-author` 4/4**

Denominator: the 4 blog articles in the sample. All 4 carry JSON-LD @type TechArticle (an Article subtype) with a named Person author: Marcos Hernanz; Sam Poder; and Josh Story + Karim Rahal + Sebastian Silbermann on both security posts. Identity resolves - the rendered byline links each name to a public profile (e.g. 'Posted by Marcos Hernanz @marcoshernanz' -> https://twitter.com/marcoshernanz; 'Sam Poder @sam_poder' -> https://twitter.com/sam_poder). floor(4 x 4/4) = 4. Weakness recorded but not penalised here: the resolution lives in the HTML byline, not in the structured data - each Person object carries only name and image, no url, sameAs or @id - and the markdown variant that AI crawlers receive lists authors as bare names in frontmatter with no handle or URL. The 2 sampled docs pages are excluded from the denominator as collectively-maintained reference material rather than articles; had they been included they would fail (their TechArticle author is the Organization 'Vercel'), giving floor(4 x 4/6) = 2.

**⊘ `p2.faqpage` — not_applicable**

No page in the fixed 8-URL sample is structured as questions - headings are API identifiers ('allowedDevOrigins', 'serverActions', 'bodySizeLimit'), release headlines ('August 2026 Security Release') or narrative section titles ('Clearing the backlog', 'Three chunking strategies'). Widened the look beyond the sample as a sanity check: 0 case-insensitive occurrences of 'faq' in /docs/llms.txt, the 48,355-byte index of all 508 documentation URLs. The denominator for this proportional check is therefore 0 and its 3 points leave the denominator. Not a defect - an API reference site legitimately has no Q&A-structured pages.

**✗ `p2.speakable` 0/3**

3 of the 8 sampled pages do have a clear answer passage (see p3.answer-passages): the homepage, /docs/.../allowedDevOrigins and /blog/august-2026-security-release. The string 'speakable' appears zero times in any of the 8 pages' HTML. floor(3 x 0/3) = 0. This check applies and is unmet, so it stays in the denominator.

**⊘ `p2.product-offer` — not_applicable**

nextjs.org has no pricing or product pages. The site states this itself in /llms.md and /llms.txt: 'This site is documentation, not an API service. There is no REST API, no API keys, and nothing to sign up for. Everything here is public and free to read; the framework itself is open source (MIT) and installed from npm.' The homepage's 'Enterprise' and 'Templates' navigation items are marked as external and point off-domain; /enterprise and /templates both return 404 on nextjs.org. The homepage does carry a SoftwareApplication node, which declares isAccessibleForFree: true. Page type does not exist, so the 3 points leave the denominator.

**✗ `p2.howto-breadcrumb` 0/3**

Both conditions apply and neither is marked up. Hierarchy: the sampled docs URLs sit 5-6 path segments deep and the pages render a visual breadcrumb - /docs/app/api-reference/adapters/supported-providers opens with the visible text 'Adapters Supported Providers' above its H1. Procedure: the docs contain step-numbered instructions, and /docs/app/getting-started/installation is a procedural page. Grepped all 8 sampled pages for 'BreadcrumbList' and 'HowTo': zero occurrences of either. All-or-nothing, so 0.

## Content Citability — 4 / 25

**✓ `p3.answer-passages` 1/5**

Method: for each sampled URL I took the prose from the start of the main content to the first heading, code fence, table or embedded component, and counted words. Judged on the representation retrieval crawlers actually receive (markdown where the site negotiates it, HTML otherwise). PASS 3: homepage 43 words ('The React framework for the web. Next.js is used to build full-stack web applications: you write React components for the UI, and Next.js provides routing, rendering, data fetching, caching, and build tooling around them...'); allowedDevOrigins 75 words; august-2026-security-release 62 words (in range and it states the actionable substance - versions v16.3.3 and v15.5.24 - though it opens with the anaphoric '[Last week] we announced'). FAIL 5: supported-providers 10 words (crawlers receive a 'Page Not Found' stub, see notes); serverActions 31 words and it defers the explanation to another page; how-we-closed-1500-github-issues 180 words of narrative lead-in before any answer; turbopack-chunking 20 words that depend on an interactive component ('Open the network tab of this page and you will see...'); nextjs-security-release-august-2026-update 95 words, just past the 90-word ceiling. floor(5 x 3/8) = 1.

**✗ `p3.sourced-statistics` 0/5**

Counted quantitative claims about the world across the 8 sampled pages, excluding version numbers, port numbers, config literals and code. 12 claims found: homepage testimonials 'average 0.09 or lower for Cumulative Layout Shift' and 'responds to user input within 100ms and all animations run at a consistent 60fps'; serverActions 'an additional 10-20 KB is a reasonable rule of thumb'; how-we-closed-1500-github-issues '36 new reports each week', 'peaked at 3,109 open reports in January 2025', 'By August 10, 2026, it still had 2,244', 'closed 1,462 issues ... below 1,000, even as 218 new reports arrived', the two-year/18-month stale threshold, 'an average of 30 minutes ... 200 eve sessions running at once'; turbopack-chunking 'We estimate 2/3 of sessions are a single page', 'defaults cut requests by more than half ... shipped 10% more code overall', 'about 10 KB of client-side JavaScript on every navigation'. Exactly 1 carries a named, linkable source: the stale-issue thresholds link to github.com/vercel/next.js/pull/73488 and /pull/75630, where the numbers can be checked. The rest are first-party operational metrics with no per-claim citation; the two homepage testimonials name a speaker ('Charlton Roberts, Product Engineering'; the other gives only 'Senior Software Engineer, Frontend') but link to no measurement. floor(5 x 1/12) = 0. Even on the most generous reading, counting both testimonials as sourced, floor(5 x 3/12) = 1.

**✗ `p3.named-author` 0/5**

> **Note added 2026-09-08.** This check was read differently here than in [stripe.com](stripe.com.md), on the same v1.0 criterion ("a real, identifiable person **with a bio**"). That disagreement between two of our own audits is how ambiguity #4 in [open-questions](../../rubric/open-questions.md) was found. v1.1 settles it: an on-site author page and the person's own homepage are equivalent. Neither audit was rewritten.


Denominator: the 4 blog articles. All 4 name real, identifiable people - Marcos Hernanz, Sam Poder, Josh Story, Karim Rahal, Sebastian Silbermann - never 'admin' and never a brand name, and each byline links to the author's public X profile. What is absent is the bio the check also requires: the byline renders as name plus handle and nothing else, there is no author page, and the byline does not link to /team. Checked /team (343,703 bytes) for all five names: only 'Josh Story' appears; the other four are not on it. 0 of 4 meet both conditions, so floor(5 x 0/4) = 0. This is the single most contestable zero in the report: a reader who treats a linked public profile as satisfying 'with a bio' would score this 5/5 and the site total 45/82.

**✓ `p3.natural-questions` 1/5**

Test applied: does the page's heading set contain at least one heading phrased the way a person would put the question to an assistant, rather than as an identifier or a bare label. PASS 3: homepage (H2 'What's in Next.js?', alongside 'Get started in seconds'); /blog/how-we-closed-1500-github-issues ('How we closed 1,500 GitHub issues in one month'); /blog/turbopack-chunking ('How Turbopack chunks your JavaScript'). FAIL 5: supported-providers ('Adapters Support', 'bun', 'vercel'); allowedDevOrigins (H1 is the bare identifier 'allowedDevOrigins', no other H1/H2); serverActions ('serverActions', 'allowedOrigins', 'bodySizeLimit'); and both security posts, whose headings are release headlines plus bare labels ('Impact', 'Our security program') - not keyword strings, but not question-shaped either. floor(5 x 3/8) = 1. The pattern is consistent: the engineering blog is phrased naturally, the API reference is named after its identifiers.

**✓ `p3.freshness` 2/5**

Denominator: the 4 evergreen pages in the sample - the homepage and the 3 docs pages. The 4 blog posts are excluded because they are dated announcements the site itself declares are never revised (/blog/llms.txt: 'blog posts describe a release at a point in time and are never revised'), and none of them carries dateModified - only dateCreated and article:published_time. PASS 2 of 4: allowedDevOrigins and serverActions both declare dateModified 2026-09-07, one day before the audit. FAIL 2 of 4: the homepage carries no date property of any kind, and supported-providers carries no JSON-LD at all. floor(5 x 2/4) = 2. Had all 8 sampled pages been kept in the denominator the result would be floor(5 x 2/8) = 1. Partial mitigation not creditable under this check: sitemap.xml supplies a lastmod for all 734 URLs, including all 8 sampled ones.

## Brand Authority — 15 / 20

**✓ `p4.knowledge-graph` 5/5**

The homepage SoftwareApplication node's sameAs array contains https://www.wikidata.org/wiki/Q56062435 and https://en.wikipedia.org/wiki/Next.js. Both fetched: Wikidata Q56062435 returns 200 with 63 'Next.js' back-references, Wikipedia returns 200 with 247. The Organization node adds a second pair of authority records for the publisher, https://www.wikidata.org/wiki/Q56069184 and https://en.wikipedia.org/wiki/Vercel, both 200 with 41 and 265 'Vercel' back-references respectively.

**✓ `p4.third-party-listings` 5/5**

Two independent listings fetched and confirmed: https://libraries.io/npm/next returns 200 with 26 'Next.js' mentions, and https://snyk.io/advisor/npm-package/next returns 200 with 355. Both are directory/advisor sites operated by parties unrelated to Vercel. The package registry listing the site links from its own sameAs, https://www.npmjs.com/package/next, could not be confirmed - it returns 403 to this client even with full browser headers (npm's anti-automation, not a broken link). One independent listing suffices for the check and two were verified.

**✗ `p4.video-presence` 0/4**

The channel exists but is not linked via sameAs, and the check requires both. https://www.youtube.com/@NextJS returns 200 with channelMetadataRenderer title 'nextjs' and 132 videoId occurrences in the response, so it is a real channel with published content. But no YouTube URL appears in either sameAs array (SoftwareApplication lists en.wikipedia.org, wikidata.org, github.com/vercel/next.js, npmjs.com, x.com/nextjs, bsky.app/profile/nextjs.org; Organization lists en.wikipedia.org/wiki/Vercel, wikidata.org, github.com/vercel, x.com/vercel), and grepping the whole homepage HTML for youtube.com or youtu.be returns zero matches - the site's only social links are X and Bluesky.

**✓ `p4.independent-mentions` 3/3**

The brand is discussed at length on four domains Vercel does not control, all fetched and confirmed 200: en.wikipedia.org/wiki/Next.js (247 mentions), www.wikidata.org/wiki/Q56062435 (63), snyk.io/advisor/npm-package/next (355) and libraries.io/npm/next (26). github.com/vercel/next.js is not counted here as it is a property the brand controls.

**✓ `p4.sameas-resolve` 2/3**

10 sameAs URLs across the homepage's two nodes. 9 return 200 with the correct brand referenced back (each destination tested against its own node's brand - Next.js for the SoftwareApplication's six, Vercel for the Organization's four): en.wikipedia.org/wiki/Next.js 247 hits, wikidata Q56062435 63, github.com/vercel/next.js 278, x.com/nextjs 172, bsky.app/profile/nextjs.org 87, en.wikipedia.org/wiki/Vercel 265, wikidata Q56069184 41, github.com/vercel 199, x.com/vercel 139. 1 fails to return 200: https://www.npmjs.com/package/next gives 403, retried with a full Chrome header set and still 403. floor(3 x 9/10) = 2. Caveat for anyone rechecking: the npm 403 is npm's anti-automation response to this client and the page is very likely reachable from a real browser and from engine crawlers, in which case the score is floor(3 x 10/10) = 3.

## Platform Visibility — 1 / 3

**⊘ `p5.search-console` — unobservable**

Google Search Console property verification is visible only from inside the property owner's account. Nothing in robots.txt, the sitemap, the HTTP headers or any sampled page's HTML discloses it, and no google-site-verification meta tag or /google*.html token is a reliable signal either way (DNS TXT and Analytics-based verification leave no on-page trace). This is an external audit, so the 3 points leave the denominator rather than scoring 0.

**⊘ `p5.bing-webmaster` — unobservable**

Bing Webmaster Tools submission and index status are visible only from inside the property owner's account. No msvalidate.01 meta tag or BingSiteAuth.xml would prove current submission even if present, and scraping Bing SERPs is not a reliable substitute. External audit, so the 3 points leave the denominator rather than scoring 0.

**⊘ `p5.multi-engine-cited` — unobservable**

This check requires running a fixed set of at least 10 buyer-intent queries against at least 3 answer engines and recording where nextjs.org is actually cited. That is a human-in-the-loop procedure against live engine UIs; it cannot be performed from curl, and nothing observable from the site's own responses substitutes for it. No result is inferred or simulated here. The 3 points leave the denominator; a follow-up audit that runs the query set should re-score this check and report a different observable_max.

**✓ `p5.answer-shape-fit` 1/3**

Judged on the document the engines receive, by length and by whether the structure survives extraction. PASS 5: homepage markdown 3,939 bytes with a blockquote summary and sectioned links; allowedDevOrigins 3,234 bytes; serverActions 5,702 bytes, both tight and sectioned per option with comparison tables; and the two security posts at 1,483 and 2,559 bytes, short and cleanly headed with linked CVE/GHSA identifiers. FAIL 3: supported-providers, where the crawler-facing document is a 641-byte 'Page Not Found' stub; how-we-closed-1500-github-issues (9,474 bytes) and turbopack-chunking (14,938 bytes), long-form narrative whose load-bearing content sits in interactive components that emit no text in the markdown - <IssueBacklogChart />, <ChunkInspector />, <ChunkDiagram variant="per-module" />, <VideoPlayer /> and 7 others - and turbopack-chunking additionally leaks raw JSX into the agent-facing text, with 16 occurrences of className and a {/* prettier-ignore */} comment. floor(3 x 5/8) = 1.

**⊘ `p5.non-english-engines` — not_applicable**

The audience is English-speaking. The homepage WebSite node declares inLanguage 'en'; none of the 734 sitemap URLs carries a locale path prefix; no sampled page emits an hreflang alternate; /llms.txt, /docs/llms.txt and /blog/llms.txt are English-only. Per rule 6 the check is not applicable and its 3 points leave the denominator - it is never awarded by default.

## Excluded from the denominator

| Check | Pts | Why |
|---|:-:|---|
| `p2.faqpage` | 3 | No Q&A-structured page in the sample, and 0 occurrences of 'faq' in the 508-URL documentation index. Proportional denominator is 0. |
| `p2.product-offer` | 3 | No pricing or product pages on the domain; /enterprise and /templates 404 on nextjs.org. The site states it has nothing to sign up for and the framework is free and MIT-licensed. |
| `p5.search-console` | 3 | Property verification is visible only inside the owner's account. External audit. |
| `p5.bing-webmaster` | 3 | Submission and index status are visible only inside the owner's account. External audit. |
| `p5.multi-engine-cited` | 3 | Requires running a >=10-query buyer-intent set against >=3 live answer engines by hand. Not performed, not simulated. |
| `p5.non-english-engines` | 3 | English-only audience: inLanguage 'en', no locale prefixes across 734 sitemap URLs, no hreflang. Rule 6. |

## Auditor's caveats

*Where this audit made a judgement call, or could not verify something.*

- p1.llms-full-txt 是全篇最可争议的一分。根路径 /llms-full.txt 返回 404，语料实际在 /docs/llms-full.txt（200，3,970,025 字节）。我判 scored，理由是 rubric 该项 pass 条件只写「Resolves and is substantially longer than llms.txt」、没有钉路径，而紧邻的 llms.txt 那项明确写了「Resolves at /llms.txt」。若按 llmstxt.org 惯例要求根路径，此项为 0，总分变 38/82（归一化 46%，仍是 Below average）。
- p3.named-author 判 0 是全篇摆动最大的一项（5 分）。四篇文章的作者都是真实可辨识的工程师，署名还链到本人 X 主页；我判 failed 只卡在 rubric 那句「with a bio」——站上没有作者简介页，署名不指向 /team，且 5 位作者里只有 Josh Story 出现在 /team。若把「链到公开主页」算作 bio，此项 5/5，总分 45/82（55%）。
- p4.sameas-resolve 记 9/10，是因为 https://www.npmjs.com/package/next 对我这个客户端返回 403（换成完整 Chrome 请求头重试仍是 403）。这大概率是 npm 的反自动化策略而非死链，真实浏览器和引擎爬虫多半能打开。若算通过则 floor(3×10/10)=3，总分 41/82。
- p3.freshness 的分母是我做的判断：只算 4 个 evergreen 页（首页+3 个 docs），把 4 篇博客排除在外，依据是站方自己在 /blog/llms.txt 写明博客「are never revised」。若把 8 个页面全放进分母，此项从 2 分降到 1 分。
- p3.sourced-statistics 的 12 条「数值主张」是我人工圈定的，剔除了版本号、端口号、配置字面量和代码。别人重新圈可能得到不同的数字。不过这项对分母不敏感：1/12、2/12、3/12 分别得 0、0、1 分。
- p2.article-author 与 p3.named-author 的分母都取 4 篇博客，把 2 个 docs 页排除在「文章」之外。若把 docs 页也算进去（它们的 TechArticle author 是 Organization「Vercel」，即品牌名），p2.article-author 会从 4 分降到 floor(4×4/6)=2 分。
- p5.answer-shape-fit 的 5/8 是定性判断，没有可量化的通过阈值。我的判据是「篇幅 + 抽取后结构是否还成立」，把两篇正文靠交互组件承载信息、markdown 里只剩 <IssueBacklogChart /> 之类空标签的长文判为不通过。换个判据结果会不同。
- p5 的三项 unobservable（Search Console、Bing Webmaster、多引擎被引用）我完全没有尝试推测。特别是 multi-engine-cited：我没有也无法真的去 ChatGPT / Perplexity / Gemini 里跑问题集，需要人工执行；因此 observable_max 是 82 而不是 85/88，跟真跑过问题集的审计结果不可直接比。
- 爬虫可达性是从单一 IP、单一地理位置、每个 UA 各发一次请求测的。边缘层（Vercel / WAF）的行为可能随地区、请求频率、时间而变，10/10 全通只代表此时此地这一次的观测。
- x.com 的两个 sameAs 回链是在未执行 JS 的原始 HTML 里 grep 到品牌名的（x.com/nextjs 172 处、x.com/vercel 139 处），这些命中来自页面骨架和内嵌 JSON，不等于人眼看到的渲染结果。判定偏宽松。
- rubric 内部有处不一致：reference/ai-crawlers.md 的 Scoring note 说 robots 那项值 4 分、partial credit 是 floor(4 × allowed / 10)，而 rubric/v1.0.json 与 v1.0.md 都写 3 分。我按 v1.0.json/v1.0.md 的 3 分计。同一文件还先说「9 of these 10 are the denominator」又说分母是 10——我按分母 10 计。这两处建议在仓库里修掉，否则不同实现会打出不同的分。
- supported-providers 的 markdown「Page Not Found」桩我只抽样了另外 14 个 sitemap URL 做对照，都正常。14 个不足以证明这是孤例，只能说没发现第二例。

## Notes

AIV 40 / 82 (v1.0), normalised 49%, Below average. Pillar split: Infrastructure 16/20, Structured Data 4/14, Content Citability 4/25, Brand Authority 15/20, Platform Visibility 1/3.

SAMPLING (rule 3). 8 URLs: the homepage, 3 product/service-equivalent pages and 4 articles. nextjs.org has no commercial product pages, so the documentation pages stand in for that slot, taken from sitemap.xml by a stated deterministic rule - lastmod descending, ties broken by URL ascending. That yields supported-providers (2026-09-08T01:21:51Z, the most recently modified URL on the site) and two next-config-js reference pages from a 2026-09-07T17:10:05.997Z bulk-deploy tie affecting many pages. Articles were taken as the 4 most recently modified /blog/ URLs; only the top 2 have distinct lastmod values, because 76 of the 78 blog URLs share a single 2026-08-29T15:09:12.695Z bulk timestamp, so that tie was broken by publication date descending from /blog/llms.txt. Every URL is listed in sampled_urls; the selection is reproducible from sitemap.xml alone.

THE FINDING THAT SHAPES THE SCORE. nextjs.org content-negotiates on user-agent: OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User and Amazonbot all receive text/markdown, while Googlebot, bingbot and Applebot receive HTML. Six of the ten retrieval crawlers therefore never see the JSON-LD at all - it exists only in the HTML branch. This is worth stating plainly rather than scoring: the site's structured-data investment is invisible to most of the engines the rubric is about, and its markdown investment is invisible to the schema checks. Related: the briefing figure of '~3.9KB SSR body' was an artifact of this negotiation. 3,939 bytes is the markdown document; a plain browser request returns 345,712 bytes of HTML carrying 7,722 characters of visible text, so p1.ssr-content passes cleanly.

A REPRODUCIBLE DEFECT. https://nextjs.org/docs/app/api-reference/adapters/supported-providers returns a full 589,491-byte page with a stats table to a browser, but returns HTTP 200 with the body '# Page Not Found / The URL /docs/app/api-reference/adapters/supported-providers does not exist.' to anything asking for markdown - confirmed three ways: the .md variant, Accept: text/markdown on the canonical URL, and an OAI-SearchBot user-agent. It is the most recently modified URL in the sitemap and the only sampled page with no JSON-LD. Sampling 14 other sitemap URLs found no second instance, so this looks isolated to that page rather than systemic; /docs and /blog have working markdown, while /learn and /conf fall back to HTML, which is fine.

READING THE SCORE. The low number is largely a site-type artifact and should not be read as neglect. 18 of the 100 nominal points left the denominator, 6 of them because a free open-source documentation site has no Q&A pages and nothing to sell - not defects. Infrastructure at 16/20 is near the top of what this rubric can award; robots.txt disallows nobody and all 10 retrieval crawlers get a 200 with real content. What the site genuinely gives up sits in Pillar 3, at 4 of 25: numeric claims are first-party operational metrics carrying no citation (1 of 12 sourced), bylines name real engineers but publish no bio, only 3 of 8 pages open with a self-contained 40-90 word passage, and dateModified is absent from the homepage and from every blog post. Those are editorial choices an engineering blog can reasonably make, and they are also exactly what a passage-retrieval engine reads. Two points of the total rest on contestable readings, both flagged in their check evidence: llms-full.txt resolves at /docs/llms-full.txt rather than the root (worth 2 points), and p3.named-author is scored 0 on the literal 'with a bio' clause where a looser reading would give 5.

Rubric v1.0, audited 2026-09-08. Scores are comparable only against another v1.0 audit with observable_max 82.
