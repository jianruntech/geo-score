# svelte.dev — AIV 34 / 85 (v1.0)

**40% · Critical** · audited 2026-09-08 · audience `en`

> svelte.dev 把力气全押在 llms.txt 这条线上——四层共 2.1MB 机读文档、24 字节全放行的 robots.txt、10 个检索爬虫拿到字节完全一致的 SSR 页面——却全站零 JSON-LD、sitemap.xml 返回 404。AIV 34 / 85 (v1.0)，归一化 40%，Critical，恰好压在 band 分界线上。

Machine-readable: [`svelte.dev.json`](svelte.dev.json)

## Sampled URLs (21)

- `https://svelte.dev/`
- `https://svelte.dev/docs/svelte/overview`
- `https://svelte.dev/docs/kit/introduction`
- `https://svelte.dev/docs/cli/overview`
- `https://svelte.dev/blog/whats-new-in-svelte-september-2026`
- `https://svelte.dev/blog/sveltekit-3-release-candidate`
- `https://svelte.dev/blog/whats-new-in-svelte-august-2026`
- `https://svelte.dev/blog/whats-new-in-svelte-july-2026`
- `https://svelte.dev/robots.txt`
- `https://svelte.dev/llms.txt`
- `https://svelte.dev/llms-full.txt`
- `https://svelte.dev/llms-medium.txt`
- …and 9 more, see the JSON

## Infrastructure — 10 / 20

**✓ `p1.robots-allows-retrieval` 3/3**

/robots.txt returns 200, content-type text/plain, and is exactly 24 bytes: "User-agent: *\nDisallow:\n" (verified by xxd). An empty Disallow value disallows nothing, so all 10 retrieval user-agents in reference/ai-crawlers.md are permitted. No per-agent blocks, no opt-out tokens, no Sitemap: directive. floor(3 x 10/10) = 3.

**✓ `p1.retrieval-reachable` 3/3**

Requested https://svelte.dev/ once per retrieval UA (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User, Googlebot, Bingbot, Applebot, Amazonbot). All 10 returned HTTP 200, 89,798 bytes, and all 10 responses share one MD5 (0ca70a3db0ae2c4a7295abcb9c9bf4dc) - byte-identical to a browser UA. Each carries the real page: <h1 class="visually-hidden">Svelte</h1> plus 2,076 chars of body text. No 403, no challenge, no interstitial, no UA-conditional variance. floor(3 x 10/10) = 3.

**✗ `p1.llms-txt` 0/3**

/llms.txt returns 200, text/plain, 1,676 bytes, last-modified Mon 07 Sep 2026. It has an H1 ("# Svelte Documentation for LLMs") and a one-line summary blockquote ("> Svelte is a UI framework that uses a compiler..."). It has three ## sections, but only two of them are link groups: "## Documentation Sets" (3 link bullets) and "## Individual Package Documentation" (4 link bullets); "## Notes" holds 4 prose bullets and 0 links. The spec asks for >=3 sectioned link groups, so this is 2 of 3 - all-or-nothing, 0 points. All 7 linked targets resolve (llms-medium 837KB, llms-small 52.7KB, llms-full 1.19MB, docs/svelte 480KB, docs/kit 589KB, docs/cli 44KB, docs/ai 74KB). This is the single call in the report that moves the band - see notes.

**✓ `p1.llms-full-txt` 2/2**

/llms-full.txt returns 200, 1,186,907 bytes - 708x the 1,676-byte llms.txt. Two intermediate tiers also resolve: /llms-medium.txt (837,205 B) and /llms-small.txt (52,700 B), plus per-package files under /docs/{svelte,kit,cli,ai}/llms.txt.

**✗ `p1.ai-txt` 0/2**

/ai.txt returns HTTP 404 (with -L). /.well-known/ai.txt also returns 404. Both 404s ship a 39.5KB SPA shell whose <title> is "404" and whose body reads "Not found!" - judged on status code only, not body size.

**✗ `p1.sitemap` 0/3**

/sitemap.xml returns HTTP 404 (39,549-byte body, <title>404</title>, body text "Not found!"). /sitemap_index.xml also 404. robots.txt is 24 bytes and contains no Sitemap: line. No sitemap was found at any conventional location, so nothing to test for locale coverage.

**✗ `p1.geo-link-tags` 0/2**

Grepped <head> on all 8 sampled pages for rel="llms", rel="llms-full", rel="ai-policy": zero matches. The head carries manifest, icon, opensearch, twitter:*, og:image, description and title only - there is also no rel="canonical" anywhere. The llms.txt family exists but is discoverable only by convention, never announced from the HTML. (Docs pages do carry a visible "llms.txt" text link in the page footer, which is not a <link> tag.)

**✓ `p1.ssr-content` 2/2**

curl without executing JS returns the primary content on every sampled page. Visible body text after stripping <script>/<style>: homepage 2,076 chars; /docs/kit/introduction 3,653; the four blog posts 7,076 / 7,375 / 9,678 / 7,818; /docs/svelte/faq 8,709 chars of main content including all 14 question headings and their answers. Headings, prose, code samples and outbound links are all present in the server HTML.

## Structured Data — 0 / 17

**✗ `p2.organization-website` 0/4**

Zero application/ld+json blocks on all 8 sampled pages. Also zero on 5 further page types checked to rule out a template-specific gap: /docs, /blog, /tutorial/svelte/welcome-to-svelte, /packages, /docs/svelte/faq. The string "schema.org" appears 0 times and "itemtype" 0 times sitewide - no JSON-LD, no microdata, no RDFa. No Organization, no WebSite.

**✗ `p2.article-author` 0/4**

0 of the 4 sampled articles carry Article or BlogPosting JSON-LD (0 ld+json blocks on each). Authorship exists in the HTML only - a <p class="byline"> holding an <a> and a <time datetime>. No machine-readable author property. floor(4 x 0/4) = 0.

**✗ `p2.faqpage` 0/3**

The site has an explicit Q&A page: /faq 307-redirects to /docs/svelte/faq, h1 "Frequently asked questions", 14 <h2> headings each phrased as a question ("I'm new to Svelte. Where should I start?", "Does Svelte scale?", "Is there a router?", "How do I test Svelte apps?", ...) with an answer under each, 8,709 chars of SSR text. It carries 0 application/ld+json blocks, so no FAQPage. /docs/kit/introduction is also partly Q&A-shaped ("What is SvelteKit?", "What is Svelte?") with no FAQPage either. 0 of the pages structured as questions declare it.

**✗ `p2.speakable` 0/3**

5 of the 8 sampled pages do open with a clear self-contained answer passage (see p3.answer-passages), so the check applies. speakable appears 0 times across the sample - a consequence of there being no JSON-LD at all. floor(3 x 0/5) = 0.

**⊘ `p2.product-offer` — not_applicable**

/pricing, /shop, /store, /sponsors and /support all return 404. Svelte is free and open source (MIT), distributed through the npm registry rather than sold from svelte.dev; the only money-facing outbound link found is https://opencollective.com/svelte (donations). There is no page for Product/Offer to sit on, so its 3 points leave the denominator.

**✗ `p2.howto-breadcrumb` 0/3**

The check applies twice over: docs pages sit three levels deep in a real hierarchy (/docs/svelte/overview, /docs/kit/introduction, /docs/cli/overview) with visible section navigation, and /tutorial/svelte/welcome-to-svelte is an explicitly procedural, step-by-step page. Neither BreadcrumbList nor HowTo is declared - 0 ld+json blocks on all of them. The hierarchy is expressed in URL shape and sidebar links only.

## Content Citability — 14 / 25

**✓ `p3.answer-passages` 3/5**

5 of 8. Meeting: / (63-word opening block; the 39-word core sentence "Svelte is a UI framework that uses a compiler to let you write breathtakingly concise components..." is fully self-contained); /blog/...september-2026 (53 words before the first h2); /blog/sveltekit-3-release-candidate (46-word opener, "SvelteKit 3 is now in the Release Candidate phase..."); /blog/...august-2026 (63 words); /blog/...july-2026 (45 words). Not meeting: /docs/svelte/overview (25-word opener, and the sentence is cut mid-clause by a code sample - it literally ends "...written in HTML, CSS and JavaScript..." and resumes "...into lean, tightly optimized JavaScript" after the block); /docs/kit/introduction (main section opens with an h2 "Before we begin" holding two 15-word and 13-word housekeeping callouts; the 34-word definition sits one section lower under "What is SvelteKit?"); /docs/cli/overview (16-word opener). floor(5 x 5/8) = 3.

**✓ `p3.sourced-statistics` 5/5**

8 of 8 pages carry no unsourced quantitative claim about the world. The homepage's one such claim - "Developers consistently rank Svelte as the framework they're most excited about using" - is followed immediately by two anchors to named primary sources, https://survey.stackoverflow.co/2024/technology#2-web-frameworks-and-technologies (alt "Stack Overflow 2024 Developer Survey") and https://2025.stateofjs.com/en-US/libraries/front-end-frameworks/ (alt "State of JavaScript 2025"). The three docs pages make no numeric claims. The blog posts' claims are release facts, each carrying a version tag, a docs link and a GitHub PR number - 33, 37 and 30 github.com links on the September, August and July posts respectively. floor(5 x 8/8) = 5. Caveat: the two survey citations are anchors wrapping screenshot images, not inline text links, so the attribution is weaker to a text extractor than it looks to a reader.

**✓ `p3.named-author` 3/5**

Denominator is the 4 sampled articles (the homepage and 3 reference-docs pages carry no byline, which is normal for reference documentation). 3 of 4 are bylined "Dani Sandoval" linking to https://dreamindani.com - returns 200, <title>About Me | Dani Sandoval</title>, identifying a named person, "Principal Product Designer at ClickHouse", with a bio. The 4th, /blog/sveltekit-3-release-candidate, is bylined "The Svelte team" linked to https://svelte.dev/ - a brand, not a person. No on-site author pages exist (/blog/authors and /authors/dani-sandoval both 404), so the identity is entirely off-domain. floor(5 x 3/4) = 3.

**✓ `p3.natural-questions` 3/5**

5 of 8. Meeting: /docs/kit/introduction (h2s "Before we begin", "What is SvelteKit?", "What is Svelte?", "SvelteKit vs Svelte"); /blog/sveltekit-3-release-candidate ("What's changed?", plus descriptive h3s like "Configuration now lives in vite.config.ts", "The $lib alias is now #lib"); and the three "What's new in Svelte: <month>" posts, whose h1 and h2s are phrased the way a person asks ("What's new in SvelteKit", "What's new in the Svelte CLI and Language Tools"). Not meeting: / (h2s "used by companies you've heard of", "join our friendly community" - brand copy); /docs/svelte/overview and /docs/cli/overview, whose headings are single-word nav labels ("Overview", "Usage", "Runes", "Styling", "Acknowledgements"). floor(5 x 5/8) = 3. Worth noting the site's strongest question phrasing sits on /docs/svelte/faq, outside the sample.

**✗ `p3.freshness` 0/5**

dateModified is present on 0 of 8 sampled pages - there is no JSON-LD, no article:modified_time, no og:updated_time. What exists is a publication date only: the 4 blog posts each carry one <time datetime="2026-09-01" / "2026-08-13" / "2026-08-01" / "2026-07-01">, all within 180 days of the audit; the 4 non-article pages carry no date element at all. The HTTP last-modified header is not usable as a substitute - it tracks CDN cache fill (age: 460,982 on the homepage, x-vercel-cache: HIT) and returns the same 2026-09-03T00:32:18Z on three unrelated pages. floor(5 x 0/8) = 0 on the literal signal; a reviewer reading <time datetime> as the freshness signal would get 4 of 8 and floor(5 x 4/8) = 2. Scored strictly - see notes.

## Brand Authority — 8 / 20

**✗ `p4.knowledge-graph` 0/5**

The authority record exists and is in good shape: Wikidata Q16863097 "Svelte" / "JavaScript framework", P856 official website = https://svelte.dev/, P1324 source repo = github.com/sveltejs/svelte, 22 sitelinks; the English Wikipedia article "Svelte" resolves and describes the framework. The site does not reference it back - sameAs appears 0 times across the sample because no JSON-LD exists. All-or-nothing needs both halves, so 0.

**✓ `p4.third-party-listings` 5/5**

Verified independently: registry.npmjs.org/svelte returns 200 with 1,091 published versions, latest 5.57.0, homepage field "https://svelte.dev"; en.wikipedia.org/wiki/Svelte returns 200 as the framework article, not a disambiguation page; wikidata.org Q16863097 returns 200 with 22 sitelinks; github.com/sveltejs/svelte returns 200. (npmjs.com's web page returned 403 to a scripted request - I used the registry API instead, which is the authoritative record.)

**✗ `p4.video-presence` 0/4**

A channel with published content does exist - youtube.com/@SvelteSociety returns 200, <title>Svelte Society - YouTube</title>, and the sampled blog posts link 10+ individual YouTube videos and a "This Week in Svelte" playlist (PLdAi-nB9AYut1ixrraX3E96rNNVj3iq4F). It is not linked via sameAs, because no sameAs exists anywhere on the site; the homepage's only social link is https://bsky.app/profile/svelte.dev. Note youtube.com/@svelte is a different, unrelated channel ("svelto") - I checked so as not to credit the wrong account.

**✓ `p4.independent-mentions` 3/3**

The brand is discussed on domains Svelte does not control: the Stack Overflow Developer Survey 2024 web-frameworks section, State of JavaScript 2025 front-end-frameworks, the English Wikipedia article, sveltesociety.dev (a separate sister organisation), offerzen.com (the Svelte Origins documentary), and multiple reddit.com threads that the site's own community showcase links out to.

**✗ `p4.sameas-resolve` 0/3**

Zero sameAs URLs are emitted anywhere in the sample - a direct consequence of there being no JSON-LD - so there is nothing to resolve. Scored 0 rather than treated as vacuously satisfied by an empty set; the state is "failed" and not "not_applicable" because sameAs is not a page type and nothing about a docs site makes it inapplicable. This is an interpretation call on a rubric gap - see notes.

## Platform Visibility — 2 / 3

**⊘ `p5.search-console` — unobservable**

No external signal exists. The <head> carries no google-site-verification meta tag on any sampled page, but its absence proves nothing - DNS TXT and file-based verification are both invisible from outside, and svelte.dev is plainly present in Google's index. 3 points removed from the denominator rather than scored 0.

**⊘ `p5.bing-webmaster` — unobservable**

No msvalidate.01 meta tag on any sampled page, which again proves nothing either way. Bingbot fetches the homepage successfully (200, real page, verified above), so nothing blocks indexing - but whether the property was submitted and is indexed cannot be read from outside. 3 points removed from the denominator.

**⊘ `p5.multi-engine-cited` — unobservable**

Not attempted and not inferred. Citation outcomes cannot be derived from crawling the site; simulating or estimating them would be a guess. Whatever this site's actual citation rate is, this audit did not measure it. 3 points removed from the denominator.

**✓ `p5.answer-shape-fit` 2/3**

6 of 8, judged on main-content length plus whether sub-headings segment the page into retrievable chunks. Fitting: / (1,992 chars with a quotable 39-word definition lead); /docs/kit/introduction (2,379 chars, 4 h2 sections, 34- and 84-word answers under question headings); and the 4 blog posts (6,987 / 7,286 / 9,589 / 7,729 chars, each with 3-4 h2 and 3-7 h3 sections). Not fitting: /docs/svelte/overview (1,130 chars of main text, no h2 sections in the content body - the only h3s are sidebar nav - and its lead sentence is split by a code block) and /docs/cli/overview (844 chars, two thin sections). floor(3 x 6/8) = 2.

**⊘ `p5.non-english-engines` — not_applicable**

<html lang="en"> on every sampled page, 0 hreflang alternates, no locale path segments or locale subdomains found, and llms.txt and all documentation sets are English-only. 3 points removed from the denominator.

## Excluded from the denominator

| Check | Pts | Why |
|---|:-:|---|
| `p2.product-offer` | 3 | No pricing, product or store page exists (/pricing, /shop, /store all 404). Free MIT-licensed software distributed via npm. |
| `p5.search-console` | 3 | External audit - verification state is private to the property owner. |
| `p5.bing-webmaster` | 3 | External audit - submission state is private to the property owner. |
| `p5.multi-engine-cited` | 3 | Needs a human to run a >=10-query set against >=3 engines and record citations. Not run, not simulated. |
| `p5.non-english-engines` | 3 | Rule 6: English audience (lang=en sitewide, no hreflang, English-only docs). |

## Auditor's caveats

*Where this audit made a judgement call, or could not verify something.*

- p1.llms-txt 是全报告唯一决定 band 的判断。llms.txt 有 3 个 ## 小节但只有 2 个是链接组（## Notes 是 4 条无链接的散文 bullet），规范要求 ≥3 个 sectioned link groups，我按严格读法判 failed。若把 ## Notes 算作第三节，分数变成 37/85 = 44%，band 从 Critical 跳到 Below average。这一条我不确定，两种读法都写进了 evidence 和 notes。
- p3.freshness 同样是字面 vs 精神的取舍。8 个抽样页 dateModified 全缺（无 JSON-LD、无 article:modified_time、无 og:updated_time），但 4 篇文章都有 <time datetime> 且全在 180 天内。我按字面判 0/5；若把 <time datetime> 认作新鲜度信号则是 floor(5×4/8)=2。HTTP last-modified 头不能用——它是 CDN 缓存填充时间（首页 age=460982、x-vercel-cache: HIT），三个不相干页面返回同一个 2026-09-03T00:32:18Z。
- p4.sameas-resolve 在 sameAs 数量为 0 时是 0/0，rubric v1.0 没规定怎么算：字面读「every sameAs URL returns 200」对空集为真会给满分 3，按精神是 0。我判 failed 0/3，但这值得给 rubric 提 issue。另外，缺 JSON-LD 这一个根因同时决定了 p2 的四项和 p4 的三项，rubric 结构上是重复计权的，读者应把它当成一件事而非七件事。
- 抽样不完全符合规则 3：没有 sitemap 就没有 lastmod 可排序，3 个「产品/服务页」是按站内 Docs 菜单顺序取的（Svelte / SvelteKit / CLI），不是按最近修改时间。若换成 /docs/ai/overview 或 /docs/svelte/faq，p3.answer-passages、p3.natural-questions、p5.answer-shape-fit 的比例分都会变——尤其 /docs/svelte/faq 是全站问句化最好的页面，它不在样本里。
- p2.faqpage 和 p2.howto-breadcrumb 引用了 8 个样本之外的页面（/docs/svelte/faq、/tutorial/svelte/welcome-to-svelte），因为这两项的 pass 条件写的是「wherever / where the page is…」而不是「on key pages」，规则 3 的样本分母不适用。这是我的判断，不是规范明文。
- answer passage 的口径是我自己定的：「主内容区第一个连续散文块，跳过代码块，但代码块若打断句子则视为不自足」。按此口径 5/8。换口径结果会变——首页那句核心定义去掉破折号只有 39 词，差 1 词就掉出 40–90 区间，我是按「首个连续散文块 63 词」计入的。
- reference/ai-crawlers.md 的 Scoring note 写「awards 4 points … floor(4 × allowed / 10)」，与 rubric/v1.0.json 里 p1.robots-allows-retrieval 的 3 分不一致。我按 v1.0.json 的 3 分算。这看起来是上游文档笔误，应该开 issue。
- 爬虫可达性是用 UA 伪装测的，源 IP 是普通机房 IP。真实的 OAI-SearchBot / PerplexityBot 从各自公布的 IP 段访问时，边缘（Vercel + WAF）可能有不同策略。10/10 全通只对「UA 层面无差别对待」成立，不等于真实爬虫 IP 也一定拿到 200。
- 全程只用 curl，未执行 JS，理论上可能存在客户端注入的 JSON-LD。我在 7 种页面上都得到 0 个 ld+json 块，且 schema.org / itemtype / sameAs / speakable 字符串在整份 HTML 里都是 0 次，结论应该稳；但严格说这是「服务端 HTML 里没有」，不是「浏览器渲染后也没有」。
- p5.bing-webmaster 的「indexed」那一半理论上可通过 site: 查询部分观察，但 Bing 对脚本请求返回不稳定，我没有拆分该项，整项标了 unobservable。这偏保守——若实现方能可靠查 Bing 索引，这 3 分或许该回到分母里。

## Notes

AIV 34 / 85 (v1.0) - normalised 40% - Critical. Measured 2026-09-08 from outside the site, using curl -L only.

SAMPLING. Rule 3 asks for 8 URLs drawn from sitemap.xml. sitemap.xml returns 404, so there is no lastmod to sort by; the sample was taken from the site's own top navigation and blog index instead. The 8 rule-3 URLs are the first 8 in sampled_urls: the homepage; the three product-doc landing pages in the order the Docs menu lists them (Svelte, SvelteKit, CLI - each reached through a 307 from /docs/svelte, /docs/kit, /docs/cli); and the 4 most recent posts on /blog (Sep 1, Aug 13, Aug 1, Jul 1 2026). The remaining sampled_urls are the well-known files and additional pages individual checks cite, listed so the score can be reproduced. /docs/ai/overview exists as a fourth docs section and was not sampled.

THE CALL THAT MOVES THE BAND. p1.llms-txt is scored 0 because the file has two sectioned link groups where the spec asks for three (the third section, ## Notes, is prose bullets with no links). It is otherwise a textbook llms.txt: correct H1, correct summary blockquote, four tiers of documentation and per-package files, all seven targets live. A reviewer who counts ## Notes as a third section gets AIV 37 / 85, normalised 44%, band Below average. One 3-point all-or-nothing call therefore decides Critical vs Below average here, and the 40% result sits exactly on the 0-40 band boundary. Both readings are shown so the reader can pick.

STRICTNESS RULE USED THROUGHOUT. Where a pass condition names a specific signal, the specific signal was scored, with the adjacent observation recorded in the evidence. That is why p3.freshness is 0 despite every sampled article carrying a <time datetime> inside 180 days: the condition names dateModified, and dateModified does not exist here. The looser reading is stated in that check's evidence (it would be 2 of 5).

ONE ROOT CAUSE, FOUR CHECKS. svelte.dev emits no JSON-LD, no microdata and no RDFa on any page type tested. That single fact zeroes all of Pillar 2's applicable checks and also decides p4.knowledge-graph, p4.video-presence and p4.sameas-resolve - roughly 29 of the 34 points not earned. The Wikidata item, the npm listing, the Wikipedia article and the YouTube channel all exist and resolve; the site simply never claims them in machine-readable form. That is one afternoon of work, not four separate problems, and the score understates how close this site is to a much higher one.

p4.sameas-resolve is an interpretation call worth flagging to the rubric maintainers: with zero sameAs URLs the proportional formula is 0/0. Read literally, "every sameAs URL returns 200" is vacuously true and would award 3; read in spirit it is 0. This report scored 0. The rubric should say which.

WHAT THE SCORE IS NOT SAYING. This is a measurement, not a verdict. Several of the low scores describe a deliberate and coherent posture rather than neglect. A framework documentation site has nothing to put Product/Offer on, and it is excluded rather than failed. More interestingly, svelte.dev has invested heavily on the axis it evidently considers real - a four-tier llms.txt family totalling 2.1MB of machine-readable documentation, per-package files, and a fully open robots.txt that lets all 10 retrieval crawlers through to byte-identical server-rendered content - while investing nothing in the schema.org layer that Pillars 2 and 4 mostly measure. Whether that trade is right depends on which engines matter to them; the rubric only records that they made it.

Largest single gap: Structured Data, 0 of 17.
