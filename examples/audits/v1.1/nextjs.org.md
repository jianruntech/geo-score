# nextjs.org — AIV audit (rubric v1.1)

> **Readiness 85 / 98 · normalised 87% · Leading** · audited 2026-09-08

Scored against [rubric v1.1](../../../rubric/v1.1.md) using only publicly observable data.
Machine-readable: [`nextjs.org.json`](nextjs.org.json), conforming to
[`schema/report.v2.json`](../../../schema/report.v2.json).

## Sampled URLs (8)

- https://nextjs.org/
- https://nextjs.org/learn
- https://nextjs.org/showcase
- https://nextjs.org/docs/app/getting-started/installation
- https://nextjs.org/docs/app/api-reference/directives/use-cache
- https://nextjs.org/blog/how-we-closed-1500-github-issues
- https://nextjs.org/blog/turbopack-chunking
- https://nextjs.org/blog/august-2026-security-release

## Reachable — 13 / 15

**◐ `g.robots` 3/5** — Retrieval crawlers allowed in robots.txt

*Why this tier:* 只有「未显式禁止也未显式放行」这一档：robots.txt 全文 40 字节，通篇没有任何 User-agent 组，因此既拿不到第 5 档要求的「对主流检索 UA 明确放行」，也不落入第 0 档的 Disallow。第 5 档要的是显式 Allow，缺省允许不等于显式放行。

GET https://nextjs.org/robots.txt → HTTP 200，size_download=40 字节。hexdump 全文逐字节为 `Sitemap: https://nextjs.org/sitemap.xml\n`（0x53 69 74 65 6d 61 70 ... 0x0a），无 User-agent、无 Allow、无 Disallow。换 GPTBot UA 与 bingbot UA 重取，同为 HTTP 200 / 40 字节 / 同一行内容，排除按 UA 分发不同 robots 的可能。

**✓ `g.reachable` 5/5** — Reachable to retrieval user-agents

*Why this tier:* 落第 5 档而非第 3 档，是按量表规则 6「判定看实质不看格式」判的：8×10=80 个检索 UA 单元全部 200，无一被拦；正文与浏览器视图一致，字节差异来自站点主动对 AI 代理做 text/markdown 内容协商（是升级不是降级），不是第 3 档所指的拦截或劣化。逐字节比对已排除「同尺寸不同 MD5」是内容差异。

8 个 URL × 10 个检索 UA（GPTBot / OAI-SearchBot / ChatGPT-User / ClaudeBot / Claude-SearchBot / PerplexityBot / Perplexity-User / Google-Extended / Applebot / Bingbot）= 80 个请求，全部 HTTP 200（首轮 showcase|Perplexity-User 一次 curl(35) SSL_ERROR_SYSCALL，重取即 200 / 200404 字节 / MD5 9c658cbc2cac9925119e387bdc696aa5，判为传输层偶发）。分发模式：首页对 8 个 UA 返回 text/markdown 3939 字节 MD5 d78fc2ce20be349709252ad2ba50077d，浏览器 Chrome UA 返回 text/html 345712 字节 MD5 05e7417b894cc604bc36ff7ed2af5a63，Applebot/Bingbot 返回 text/html 446849 字节；docs-usecache 对 8 个 UA 返回 markdown 31968 字节 MD5 8b14025fccf9ce437277bc5fc48c88e8，Applebot/Bingbot 返回 html 1433287 字节。markdown 版含同一正文原句（首页："The React framework for the web. Next.js is used to build full-stack web applications..."）。/learn 无 markdown 变体，browser 与 GPTBot 同为 411339 字节但 MD5 不同（a6f09776… vs f949ed08…），逐字符 diff 定位到第 294558 字节的 React 随机 key（"bXG2ljt8iONffroXdJGBsv" vs "BDMbW-EB8YkUUtHXt0R2zv"），非内容差异。

**✓ `g.ssr` 5/5** — Main content server-rendered

*Why this tier:* 第 5 档「抽样页正文均在 HTML 响应中」——8/8 通过，无一页需要执行 JS 才出正文，因此不落第 3 档「部分页可见」。

对 8 个页面的浏览器 UA HTML 响应剥离 <script>/<style>/<svg> 后抽正文（未执行任何 JS）：home 7682 字符/1133 词、learn 4636/707、showcase 3731/539、docs-install 16757/2373、docs-usecache 29807/4558、blog-issues 10212/1669、blog-turbo 13248/2284、blog-sec 3318/470。命中原句可复核：blog-issues 的 "Friday, September 4th 2026 How we closed 1,500 GitHub issues in one month Posted by M…"、docs-usecache 的 "The use cache directive allows you to mark a route, React component, or a function as cacheable."。反向佐证：拿 HTML 的爬虫收到的比浏览器更多——docs-usecache 给 Bingbot 1433287 字节 vs 给 Chrome 974728 字节。

## Understandable — 16 / 22

**✓ `p1.sitemap` 4/4** — Sitemap discoverable and fresh

*Why this tier:* 第 4 档「且多数 URL 带 lastmod」——lastmod 覆盖率 100%，不是「多数」而是全部，无更高档可取。

robots.txt 声明 Sitemap: https://nextjs.org/sitemap.xml；GET 该 URL → HTTP 200，size_download=103007 字节，Content-Type application/xml。<loc> 计数 734，<lastmod> 计数 734（734/734 = 100%）。非 sitemapindex（grep sitemapindex = 0）。最新 lastmod 为 2026-09-04T18:13:26.655Z（/blog/how-we-closed-1500-github-issues），与今日 2026-09-08 相差 4 天。

**✓ `p1.llms-txt` 5/5** — llms.txt present and structured

*Why this tier:* 第 5 档需要「含站点定义段」+「2 个以上含链接的主题分节」，两条都远超线：定义段是标准 llms.txt 的 H1+blockquote 形态，含链接主题分节有 5 个（要求 ≥2）。

GET https://nextjs.org/llms.txt → HTTP 200，12724 字节。第 1 行 `# Next.js`，第 3 行 `> The React Framework for the Web` 构成站点定义段；正文第 5 段进一步定义 "Next.js is a React framework for building full-stack web applications."。标题结构（grep '^#'）：## When to use nextjs.org / ### How to read it efficiently / ## Documentation / ### Versioned Documentation / ## Support Policy / ### Version Support / ### Currently Supported Versions / ## Learn Next.js / ## Blog (Showing Last 2 Years)。全文含链接 52 处（grep -c ']\(http'）。

**◐ `p1.organization` 3/6** — Organization + WebSite sitewide

*Why this tier:* 只能落第 3 档「有其一」，虽然两者其实都有：第 5 档要求「两者齐全，含 name／url／logo」，而全站抽样 JSON-LD 里 logo 属性出现 0 次，logo 缺失就上不去第 5 档；第 6 档要的 sameAs 反而已具备但被第 5 档卡住。这是阶梯把 logo 设成 sameAs 的前置条件造成的结果，不是站点两个实体真的只有一个。

首页单个 application/ld+json 块内 @graph 三节点：SoftwareApplication(@id .../#software)、WebSite(@id .../#website, url/name/description/inLanguage/about/publisher 齐全)、Organization(@id .../#publisher, name "Vercel", url https://vercel.com, sameAs 4 条)。SoftwareApplication 另带 sameAs 6 条。对 8 个抽样页的 browser+Bingbot HTML 共 16 份响应 grep '"logo"' → 命中 0 次（唯二命中在 YouTube 页面，非本站）。首页 <head> 亦无 rel="logo" 或 ImageObject。

**✗ `p1.breadcrumb` 0/3** — BreadcrumbList on nested pages

*Why this tier:* 第 2 档「部分层级页有」都不成立：抽样含两个五级深度的文档页，BreadcrumbList 命中数为 0。站点有明确层级（/docs/app/api-reference/directives/use-cache），因此不适用「全站无层级则退出分母」的豁免，留在分母记 0。

对 8 个抽样页的 browser UA HTML + Bingbot UA HTML（共 16 份）grep 'BreadcrumbList' → 全部 0 次；另查 /learn/dashboard-app/getting-started 与 /conf/session/the-open-web 亦为 0。站内层级客观存在：docs-install 页面可见面包屑文案 "Using App Router / Getting Started / Installation"，URL 深度 /docs/app/api-reference/directives/use-cache 为 5 级；sitemap 734 条 URL 中 508 条在 /docs 下。

**✓ `p1.page-type` 4/4** — Page-type schema where applicable

*Why this tier:* 第 4 档「适用页型普遍有，且字段真实」：按 sitemap 体量，/docs 508 + /learn 113 + /blog 79 = 700/734（95.4%）的 URL 所属页型都带页型专用 schema 且字段是真值，不是占位。未取更低档是因为覆盖不是「部分页型」而是主体页型全覆盖；扣分理由不存在于本项阶梯（缺口在 /conf 的 25 条，占 3.4%）。

docs-install → TechArticle{headline "Getting Started: Installation", dateModified "2026-07-21", url, image, author Organization Vercel}；docs-usecache → TechArticle{dateModified "2026-08-25"}；blog-issues/blog-turbo/blog-sec → TechArticle{author 为 Person 数组, dateCreated 2026-09-04T04:00Z / 2026-09-03T16:00Z / 2026-08-25T18:00Z}；/learn/dashboard-app/getting-started → LearningResource{headline "App Router: Getting Started", url, image}；首页 → SoftwareApplication{softwareVersion "16.3.4", license, codeRepository}。sitemap 页型分布：/docs 508、/learn 113、/blog 79、/conf 25、其余 9。缺口：/conf/session/the-open-web 与 /conf 的 ld+json 块数为 0（无 Event）；/showcase ld+json 块数为 0。量表点名的 HowTo 全站命中 0 次，本项按「页型专用」实质判定，以 TechArticle/LearningResource 计。

## Content Citability — 28 / 35

**✓ `p2.answer-passages` 9/9** — Self-contained answer passages

*Why this tier:* 第 9 档「多数页有」：6/8 通过（超过半数即第 7 档的线）。未降到第 7 档，是因为 6/8 已构成多数；但其中首页与 docs-install 属边界通过（见 notes 第 4 条），若按最严口径只认 HTML 视图的散文段则为 4/8，那会落到第 7 档。

口径：英文 25–120 词，不限第一段，正文前部任一段。通过 6 页——首页 44 词（agent 视图 markdown）"The React framework for the web. Next.js is used to build full-stack web applications: you write React components for the UI, and Next.js provides routing, rendering, data fetching, caching, and build tooling around them. Maintained by Vercel. Latest stable release: 16.3.4."；docs-install 45 词 "`--yes` skips prompts using saved preferences or defaults. The default setup enables TypeScript, Tailwind CSS, ESLint, App Router, and Turbopack, with import alias `@/*`…"；docs-usecache 74 词 "The `use cache` directive allows you to mark a route, React component, or a function as cacheable…"；blog-issues 33 词 "Millions of developers use Next.js, and the issue tracker is one of the main ways we learn where they run into problems. It receives an average of 36 new reports each week."；blog-turbo 26 词 "“Chunking” is the process of deciding which code goes into which chunk. There are a lot of ways to do chunking, each with their own tradeoffs."；blog-sec 43 词 "Last week we announced an upcoming security release for Next.js. Earlier today, we moved the release forward after identifying an additional critical severity vulnerability…"。不通过 2 页——/learn 首段 24 词（"Go from beginner to expert by learning the foundations of Next.js and building a fully functional demo website that uses all the latest features."，差 1 词）；/showcase 前部仅有 ≤27 词的展示卡拼接文案，无独立成立的说明段。

**✓ `p2.question-intent` 7/7** — Headings match how people ask

*Why this tier:* 第 7 档「多数贴近」：6/8 通过。未停在第 5 档（半数），是因为按 v1.1 规则 6 把任务句与说明句一并计入，且量表本项写的是「标题（headings）」复数，小节标题同样计入。若只认 <title>/H1 则通过 3–5 页，会落第 3 或第 5 档。

通过——/learn H1 "Start building with Next.js"（任务句）+ H2 "How does the course work?" / "What will I learn?"（问句）；blog-issues "How we closed 1,500 GitHub issues in one month"（说明句）；blog-turbo "How Turbopack chunks your JavaScript"（说明句，与量表举例 How Connect works 同型）；docs-install H2 序列 "Quick start / System requirements / Supported browsers / Create with the CLI / Run the development server / Set up TypeScript / Set up linting"（任务句，与量表举例 Accept a payment 同型）；docs-usecache H2 "How use cache works"（说明句）；blog-sec "August 2026 Security Release"（事件名，非关键词串）。不通过——首页 <title> "Next.js by Vercel - The React Framework" / H1 "The React Framework for the Web"（品牌标签+定位语）；/showcase <title> "Showcase | Next.js by Vercel" / H1 "The web framework for when it matters"（营销标语，不对应任何提问）。

**◐ `p2.freshness` 3/6** — Freshness signal present

*Why this tier:* 只取第 3 档「部分页有可见日期或 datePublished」。第 6 档写的是「多数页有，且与 dateModified 一致」，而 8 个抽样页里只有 2 页存在 dateModified（两个文档页），3 篇博客只有 dateCreated、无 dateModified，3 个页面完全无日期——「与 dateModified 一致」这个合取项只在 2/8 上可验证，2/8 不构成「多数」，按规则 2「取证据实际满足的档、不取差一点就到的档」只能停在第 3 档。这一档的判法争议见 notes 第 2 条。

有日期 5/8：docs-install 页面可见 "Last updated July 21, 2026" + schema dateModified "2026-07-21"（完全一致）；docs-usecache 可见 "Last updated August 25, 2026" + dateModified "2026-08-25"（完全一致）；blog-issues 可见 "Friday, September 4th 2026" + dateCreated "2026-09-04T04:00:00.000Z"；blog-turbo 可见 "Thursday, September 3rd 2026" + dateCreated "2026-09-03T16:00:00.000Z"；blog-sec 可见 "Tuesday, August 25th 2026" + dateCreated "2026-08-25T18:00:00.000Z"。无日期 3/8：首页、/learn、/showcase —— 正则扫可见文本与原始 HTML（含 script）中的 ISO 日期、英文月份日期、"Last updated"、dateModified/datePublished/dateCreated 全部 0 命中。站点级另有 sitemap 734/734 条 lastmod，但本项按页判。

**◐ `p2.sourced-stats` 3/7** — Statistics carry a source

*Why this tier:* 只取第 3 档「部分标注」。第 5/7 档都要求「多数标注」，实测抽样页上约 35 处数字与事实主张里只有约 10 处带可点击出处（≈29%），两篇数字密度最高的工程博客的核心数据全是无出处的第一方测量，因此够不上「多数」。凡有出处的地方出处确实可点击可核实，所以一旦判到「多数」就会直接跳到第 7 档——本项没有中间地带，见 notes 第 5 条。

带可点击出处：blog-sec 6 处漏洞主张全部链到一手advisory（https://www.cve.org/CVERecord?id=CVE-2026-75604、https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36、https://github.com/strukturag/libheif/security/advisories/GHSA-g89c-p67h-r497）；/showcase 的 "100% uptime with over 17 million edge requests at launch" 链到 https://vercel.com/blog/architecting-reliability-stripes-black-friday-site；docs-install 的 React canary 说法链到 https://react.dev/blog/2023/05/03/react-canaries、Node 20.9 链到 https://nodejs.org/；blog-issues 的 issue tracker 与 stale workflow 链到 https://github.com/vercel/next.js/issues 与 .../pull/73488。裸数字：blog-issues 的 "average of 36 new reports each week"、"peaked at 3,109 open reports in January 2025"、"By August 10, 2026, it still had 2,244"、"closed 1,462 issues"、"218 new reports"、"Already fixed 543 / 37%"、"average of 30 minutes"、"200 eve sessions" 共 8 处无逐条出处；blog-turbo 三列基准表约 15 个数字（"363.6 KiB (76 requests)" / "561.6 KiB (96 requests)" / "610.0 KiB (15 requests)" 等）无复现方法链接；首页三条推荐语数字 "0.09 or lower for Cumulative Layout Shift"、"within 100ms"、"consistent 60fps" 只署人名或职务，无可核实文档，且其中一条署名仅为 "Senior Software Engineer, Frontend" 未具名。

**✓ `p2.named-author` 6/6** — Named, verifiable authorship

*Why this tier:* 第 6 档「姓名链向可核实的身份页」：凡有署名的页面，署名都是真实自然人且链接可解析，无一例外。未降到第 3 档是因为链接实测全部 200；未降到第 0 档「仅署机构名」是因为博客这一署名相关页型 3/3 都是 Person。争议在于文档页 author 是 Organization，按页数口径会掉档，见 notes 第 3 条。

blog-issues：JSON-LD author [{Person, name "Marcos Hernanz"}]，HTML 署名锚点 <a href="https://twitter.com/marcoshernanz"> → 200，224527 字节，最终 URL https://x.com/marcoshernanz。blog-turbo：Person "Sam Poder" → https://twitter.com/sam_poder → 200，287875 字节 → https://x.com/sam_poder。blog-sec：Person ×3 "Josh Story"/"Karim Rahal"/"Sebastian Silbermann"，前两条链接 https://twitter.com/joshcstory → 200 / 186927 字节、https://twitter.com/karimpwnz → 200 / 242237 字节。站内另有 https://nextjs.org/team → 200，343703 字节。反面：docs-install 与 docs-usecache 的 author 为 {"@type":"Organization","name":"Vercel"}；首页 / /learn / /showcase 无 author 字段。8 页中带自然人署名的为 3 页。

## Brand Credibility — 17 / 18

**✓ `p3.listings` 4/4** — Third-party listings

*Why this tier:* 第 4 档「5 家以上」：实测 7 家返回 200，超过 5 家的线，无更高档。

逐个实测（浏览器 UA，跟随重定向）：https://github.com/vercel/next.js → 200 / 433963 字节；https://registry.npmjs.org/next → 200 / 31210938 字节（且 https://api.npmjs.org/downloads/point/last-week/next 返回 {"downloads":40645752,"start":"2026-08-31","end":"2026-09-06"}）；https://en.wikipedia.org/wiki/Next.js → 200 / 235653 字节；https://www.wikidata.org/wiki/Q56062435 → 200 / 4945362 字节；https://libraries.io/npm/next → 200 / 39393 字节；https://www.producthunt.com/products/next-js → 200 / 624034 字节；https://snyk.io/advisor/npm-package/next → 200 / 803829 字节。另有 https://stackshare.io/next-js → 429（限流）、https://www.g2.com/products/next-js/reviews → 403、https://alternativeto.net/software/next-js/ → 403，均为对方反爬，未计入 7 家。

**✓ `p3.mentions` 4/4** — Independent mentions

*Why this tier:* 第 4 档「多渠道持续提及」：既有维基百科这类独立百科条目（第 3 档「独立报道或评测」的强形态），也有跨域名、跨月份持续产出的第三方评测内容，超出第 3 档的单点报道。

独立百科：https://en.wikipedia.org/wiki/Next.js → 200 / 235653 字节（非站方可控）。第三方评测/报道（2026 年内、7 个互不相同的域名，经 WebSearch 检索到）：medium.com/@emmaschmidt304（2026-06 "Next.js in 2026: The Features That Are Changing How We Build the Web"）、pagepro.co/blog/what-is-nextjs/、medium.com/@mernstackdevbykevin、flex.com.ph/articles/nextjs-2026-...、javascriptdoctor.blog/2026/05/...、nucamp.co/blog/top-10-full-stack-frameworks-in-2026-...、articsledge.com/post/nextjs。其中含批评性内容（"accumulates complexity over time and nudges teams toward Vercel lock-in"），非站方通稿。

**✓ `p3.knowledge-graph` 4/4** — Knowledge-graph entity

*Why this tier:* 本项是 0/4 二元项，条目存在即满分。产品实体与母公司实体在维基数据与维基百科都各有条目，且被站点 JSON-LD 的 sameAs 主动指认。

https://www.wikidata.org/wiki/Q56062435（Next.js）→ 200 / 4945362 字节；https://en.wikipedia.org/wiki/Next.js → 200 / 235653 字节；母公司 https://www.wikidata.org/wiki/Q56069184（Vercel）→ 200 / 130213 字节；https://en.wikipedia.org/wiki/Vercel → 200 / 212486 字节。四条均由首页 JSON-LD 的 sameAs 数组显式声明，构成站点自述与知识库的双向绑定。

**✓ `p3.sameas` 3/3** — sameAs complete and resolving

*Why this tier:* 第 3 档「全部可解析且确为本品牌」。未落第 2 档「部分失效」，是因为唯一非 200 的那条不是死链而是 npm 官网对我的客户端做了反爬，用同一资源的 registry 端点验证到内容确实在线且确为本包。

SoftwareApplication.sameAs 6 条 + Organization.sameAs 4 条 = 10 条，逐条实测：en.wikipedia.org/wiki/Next.js 200/235653、wikidata.org/wiki/Q56062435 200/4945362、github.com/vercel/next.js 200/433963、x.com/nextjs 200/352291、bsky.app/profile/nextjs.org 200/21673、en.wikipedia.org/wiki/Vercel 200/212486、wikidata.org/wiki/Q56069184 200/130213、github.com/vercel 200/314513、x.com/vercel 200/292135 —— 9/10 直接 200。第 10 条 https://www.npmjs.com/package/next → 403 / 5717 字节（npm 站点反爬页），改测同一资源的 https://registry.npmjs.org/next → 200 / 31210938 字节，且 api.npmjs.org 周下载量 40645752，确认包在线且归属本品牌。10 条主体均为 Next.js 或其维护方 Vercel。

**◐ `p3.video` 2/3** — Video and multimodal presence

*Why this tier:* 第 3 档要求「持续输出且站内带 VideoObject」，两个条件是合取；持续输出成立（Vercel 频道 474 支视频、11.6 万订阅，承载 Next.js Conf 全部讲次），但站内 VideoObject 命中 0 次，合取不成立，只能停在第 2 档。注意第 2 档措辞是「有账号但内容零星」，与实际情况（内容并不零星）不符——这是阶梯缺一档造成的，见 notes 第 6 条。

官方视频承载渠道：https://www.youtube.com/@VercelHQ → 200 / 1614058 字节，channelMetadataRenderer.title = "Vercel"，subscriberCountText 解析出 "116K subscribers"，"474 videos"。反例：https://www.youtube.com/@NextJS → 200 / 953805 字节，title = "nextjs"，"2 subscribers" / "20 videos"，判定为非官方占位号。站内 VideoObject：对 8 个抽样页的 browser + Bingbot HTML（16 份）以及 https://nextjs.org/conf（200 / 352818 字节）、https://nextjs.org/conf/session/the-open-web（200 / 109492 字节）grep 'VideoObject' → 全部 0 次；且两个 conf 页面的 application/ld+json 块数为 0，讲次页连 Event schema 都没有。

## Answer Fit — 8 / 8

**✓ `p4.answer-shape` 4/4** — Content shaped for extraction

*Why this tier:* 第 4 档「小标题、列表、表格齐备，段落适中」。未落第 2 档「有小标题但段落偏长」——实测中位段长 26–37 词，最长 111 词，全在可摘范围。首页/learn/showcase 确实无列表无表格，但它们的段落中位仅 12–18 词，也不符合第 2 档描述；且这三页占 sitemap 734 条 URL 中的 3 条，内容主体（/docs 508 + /blog 79）结构齐备。

逐页结构统计（browser UA HTML，剥离 script）：docs-install h2=11 h3=3 ul=34 ol=3 li=330 pre=19，散文段中位 26 词；docs-usecache h2=11 h3=25 ul=34 table=3 li=346 pre=25，中位 37 词；blog-issues h2=6 ul=2 ol=2 table=1 li=16，中位 37 词、最长 111 词；blog-turbo h2=3 h3=4 ul=4 table=3 li=14，中位 30 词、最长 106 词；blog-sec h2=2 h3=2 ul=1 li=4，中位 29 词、最长 48 词。营销页：home h2=5 h3=3 ul=0 table=0，中位 18 词；learn h2=2 ul=0，中位 12 词；showcase h2=3 h3=3 ul=1 li=4，中位 12 词。

**✓ `p4.question-coverage` 4/4** — Coverage of the questions people ask

*Why this tier:* 第 4 档「覆盖 9–10 个」：自拟的 10 个前端开发者高频真实问题逐条在站内找到正面回答的专页，10/10，无缺口，因此不落第 3 档（6–8 个）。

以 https://nextjs.org/docs/llms.txt（200 / 48355 字节，每页带一句描述）逐题核对，10 题 10 中：①怎么新建 Next.js 应用 → /docs/app/getting-started/installation（"Learn how to create a new Next.js application with the create-next-app CLI…"）②怎么取数据 → /docs/app/getting-started/fetching-data ③Server 与 Client 组件怎么选 → /docs/app/getting-started/server-and-client-components ④缓存怎么工作 / use cache 是什么 → /docs/app/getting-started/caching + /docs/app/api-reference/directives/use-cache ⑤不用 Vercel 怎么自托管 → /docs/app/guides/self-hosting（"…on a Node.js server, Docker image, or static…"）⑥怎么升级到最新版 → /docs/app/getting-started/upgrading ⑦怎么加鉴权 → /docs/app/guides/authentication ⑧怎么做图片优化 → /docs/app/getting-started/images ⑨Pages Router 怎么迁到 App Router → /docs/app/guides/migrating/app-router-migration ⑩怎么写测试 → /docs/app/guides/testing（"…Cypress, Playwright, Vitest, and Jest"）。另附送覆盖：环境变量、错误处理、国际化、Route Handlers、metadata/OG 均有专页。

**⊘ `p4.cn-engines`** — not applicable (leaves the denominator)

整项退出分母：量表写明「面向中文市场时适用；不面向中文市场则整项退出分母」。本站是纯英文的全球开源框架文档站，无任何中文市场定向证据，因此既不判 0 也不判 1。

## Bonus — +3 (outside the denominator)

**✓ `b.llms-full` 2/2** — llms-full.txt

*Why this tier:* 加分项，判据是「提供全文聚合文件；允许非根路径，但需可从 llms.txt 或 robots.txt 发现」——非根路径 /docs/llms-full.txt 成立，且在 llms.txt 里被明确列出，两条都满足。

GET https://nextjs.org/docs/llms-full.txt → HTTP 200，size_download=3970025 字节，Content-Type text/plain;charset=UTF-8。发现路径：llms.txt 的 ## Documentation 分节内命中原句 "- [Full documentation](https://nextjs.org/docs/llms-full.txt) — complete text, one document"，另在 "### How to read it efficiently" 中再次出现。/.well-known/ai-catalog.json（200 / 1866 字节）亦以 urn:ai:nextjs.org:docs:full 条目指向同一 URL。

**✗ `b.ai-txt` 0/2** — ai.txt

*Why this tier:* 判据是「声明 AI 使用政策」，两个约定路径都是 404，站内也找不到等价的 AI 使用政策声明。/.well-known/ai-catalog.json 虽然存在，但它是资源目录（列出 llms.txt / llms-full.txt / markdown 端点），不含任何使用条款或授权表述，不构成政策声明，故记 0 而非满分。

GET https://nextjs.org/ai.txt → HTTP 404（返回 12207 字节的 HTML 错误页）；GET https://nextjs.org/.well-known/ai.txt → HTTP 404 / 12207 字节。robots.txt 全文 40 字节仅一行 Sitemap，无任何政策性注释。/.well-known/ai-catalog.json 全文 1866 字节，字段仅 specVersion / host / entries，逐条 entry 只有 identifier、displayName、type、url、description，无 usage、license、policy、terms 类字段。

**✓ `b.geo-link` 1/1** — GEO link tags

*Why this tier:* 判据是「在 head 声明面向 AI 检索的 link 关系」：head 里确有一条指向 markdown 全站入口的 alternate 关系，且目标可解析并返回 markdown，不是空声明。

首页 <head> 内命中原句 `<link rel="alternate" type="text/markdown" href="https://nextjs.org/llms.md"/>`（与之并列的还有 `<link rel="canonical" href="https://nextjs.org"/>`）。GET https://nextjs.org/llms.md → HTTP 200，3939 字节，Content-Type text/markdown; charset=utf-8，与检索 UA 在首页拿到的 markdown 体积完全一致（3939 字节）。

**✗ `b.speakable` 0/1** — speakable markup

*Why this tier:* 判据是「为语音助手标注可朗读区域」，全站抽样中 speakable 属性一次都没出现，无任何档可给。

对 8 个抽样页的 browser UA 与 Bingbot UA HTML（16 份）、以及 /conf、/conf/session/the-open-web、/learn/dashboard-app/getting-started、llms.txt、llms.md、ai-catalog.json 全部执行 grep -i 'speakable' → 0 命中。

## Citation performance — not scored

未测。AI 引用表现是结果型指标，按 v1.1 与站点就绪度分开报告、不并入主分，本次任务范围仅为站外可观测的就绪度审计，未在 ChatGPT / Perplexity / Google AI Overviews / Claude 等引擎上跑真实行业问题的实测。三条不测的实质理由：①同一问题多次提问结果不同，单次实测不可复现，写进报告等于给客户一个下周就对不上的数字；②它由就绪度与时间共同决定，站方当下可修的部分已经全部体现在上面 20 个计分项里；③本次没有可复核的实测记录（无对话截图、无时间戳、无提问清单），按规则 8「没有证据的判定不成立」，宁可留空也不给猜测值。若要补测，建议口径：固定 10 个前端开发者真实问题（即 p4.question-coverage 用的那 10 题），在 4 个引擎各问 3 次，记录 nextjs.org 被引次数与被引 URL，单独成表并标注实测时间窗。补充一条对该指标的先验判断（不计分、不写进结论）：本站在被引用的技术前提上做得比常见站点更多——/docs/llms-full.txt 全文聚合 3970025 字节、对 8 个检索 UA 主动做 text/markdown 内容协商、/.well-known/ai-catalog.json 资源目录、head 里的 rel=alternate type=text/markdown——但这些是否转化为更高引用率，只能实测，不能推断。

## Auditor's caveats

- 【最该被质疑的一条：门槛封顶把 87 压成 40】未封顶的归一化是 85/98 = 87%（领先档），封顶后是 40%（起步档），一条 40 字节的 robots.txt 造成 47 分落差。而 nextjs.org 的 robots.txt 不含任何 User-agent 组——按 RFC 9309 这是「全部允许」，实测 80/80 个检索 UA 单元也确实全部 200 拿到了内容。也就是说，触发封顶的这条门槛在现实中根本没有阻挡任何爬虫，封顶所依据的因果（「爬虫拿不到内容之前其余改动无效」）在本站并不成立。我认为这暴露的是量表的问题而不是站点的问题：g.robots 第 5 档要求「显式放行」，但显式 Allow 在 robots 协议里是可选的、且缺省即允许，把它设成封顶条件等于惩罚一个合规的极简 robots.txt。建议 v1.2 讨论：要么 g.robots 的封顶触发改为只在实测不可达（g.reachable 掉档）时联动，要么把「无任何指令组」单列为第 5 档。我按现行 v1.1 字面执行了封顶，但这个数字不该被当成对 nextjs.org 的技术判断。
- 【p2.freshness 判 3 还是 6，我来回改了三次】第 6 档写的是「多数页有，且与 dateModified 一致」。事实是：5/8 页有日期，两个文档页的可见「Last updated」与 schema dateModified 逐日精确一致，三篇博客的可见日期与 dateCreated 逐日精确一致但没有 dateModified，三个营销页完全无日期。如果把第 6 档读成合取（必须存在 dateModified 且一致），只有 2/8 满足，判 3；如果读成「多数页有日期，且凡存在 dateModified 处不矛盾」，则判 6。我按规则 2「取证据实际满足的档、不取差一点就到的档」选了 3，但我不确定这是量表作者的原意——按站点实际（508 个文档页全部带 Last updated + dateModified）读者很可能觉得 3 分不公。若改判 6，readiness 变 88、未封顶归一化变 90%，封顶后仍是 40，不影响档位。
- 【p2.named-author 判 6 分是本报告最激进的一处】本项阶梯不含页数口径（不像 answer-passages 写「多数页」），我据此按「凡有署名处的署名质量」判定：3 篇博客 3/3 是自然人 Person + 可解析身份链接，判第 6 档。但换成页数口径就完全不同——8 页里只有 3 页有自然人署名，2 个文档页的 author 是 {"@type":"Organization","name":"Vercel"}，而 Organization 恰好是第 0 档的原文条件；那样会判 3 甚至 0。这是 6 分项上 6 分的摆动幅度。我倾向 6 分的理由是：框架文档由机构署名是行业常规，E-E-A-T 真正吃紧的博客页型上本站做得完整（含 JSON-LD Person 数组、站内 /team 页、外部 x.com 身份页四条全部 200）。但我承认这是解释，不是测量。
- 【p2.answer-passages 的 9 分建立在两个边界通过之上】首页在 HTML 里的首段只有 22 词（不到 25 词线），是靠 agent 视图的 markdown 里那段 44 词 blockquote 通过的——理由是 10 个检索 UA 里有 8 个实际收到的就是那份 markdown，但「同一 URL 对不同 UA 有两种正文，判定该看哪一份」量表没有规定，这是我自己定的口径。docs-install 是靠一条 45 词的项目符号段通过的，页面自身的导语只有 9 词。更刺眼的是 /learn 的首段 24 词——差一个词落榜，而 v1.1 的改版说明里明确提到 svelte 因为 39 词差一词被判 0 是需要修的问题，现在同样的边界效应在 25 词线上重现了。严口径（只认 HTML 里的散文段）是 4/8，判 7 分。
- 【p2.sourced-stats 这个阶梯没有中间地带】第 5 档是「多数标注」，第 7 档是「多数标注且来源可点击可核实」。本站的情况是：凡标注处 100% 可点击（CVE/GHSA 直链、客户案例直链、react.dev/nodejs.org 直链），但标注覆盖率只有约 29%（我数出约 35 处数字与事实主张、约 10 处带出处）。这意味着判定塌成了二元——只要判到「多数」就直接是 7 分，判不到就是 3 分，5 分那一档在本站结构下实际上不可达。3 分和 7 分之间是 4 分的跳变，而我这 29% 的分母是手工数的，把 blog-turbo 那张三列基准表算成 1 处还是 15 处，结论就可能翻转。这个计数口径应该在 v1.2 里写死。
- 【两处阶梯措辞与事实对不上，我按分数取档但措辞是错的】其一，p1.organization 判 3 分，档位描述是「有其一」，但本站 Organization 与 WebSite 两个节点都在同一个 @graph 里、还带 @id 互相引用、Organization 另有 4 条 sameAs——它缺的只是一个 logo 属性（全站 16 份抽样响应 grep "logo" 命中 0）。因为 logo 被放在第 5 档、sameAs 被放在第 6 档，一个「有 sameAs 无 logo」的站被打回到和「只有一个实体」同分。其二，p3.video 判 2 分，档位描述是「有账号但内容零星」，但实际是 Vercel 频道 474 支视频、11.6 万订阅、承载全部 Next.js Conf 讲次，一点都不零星——它卡在第 3 档只因为站内 VideoObject 为 0（且 25 个 /conf 讲次页连 ld+json 块都没有）。两处都建议把合取条件拆开重排。
- 【g.reachable 判 5 分是一次实质优先于字面的裁量】第 3 档的条件之一是「返回内容与浏览器不一致」，而本站对 8 个检索 UA 返回 text/markdown、对浏览器返回 text/html，字节与 MD5 都不同，字面上完全命中第 3 档。我判 5 分的依据是 v1.1 规则 6「判定看实质不看格式」：这份差异是站点公开声明的、面向 AI 检索的升级（llms.txt 里写明 "Recognised agents get markdown there automatically"），markdown 里是同一份正文加上 title/url/lastUpdated/prerequisites 的结构化前置元数据，不是 cloaking 也不是劣化。另外我已逐字符验证过：同尺寸不同 MD5（如 /learn 的 411339 字节）的差异出在 React 每请求随机 key，不是内容。需要说明的是这一判定不影响本报告结论——g.robots 已经触发封顶，此处判 3 还是 5 都不改变 gate_capped 与最终 40 分，只改变未封顶的 87% 与 85%。但换一个站它就可能是决定性的，所以留档。
- 【抽样代表性偏差，对本站是系统性不利】8 页样本里有 3 页（首页、/learn、/showcase）是营销/索引页，占样本 37.5%，但在 sitemap 734 条 URL 里只占 3 条（0.4%）。这 3 页恰好是无日期、无列表表格、无署名、无自足答案段、无页型 schema 的那批，直接压低了 freshness、answer-passages、question-intent 三项。反过来，占全站 69% 的 /docs（508 条）只进了 2 页样本。量表规则 1 的固定配比（1 首页 + 2 产品页 + 2 文档页 + 3 内容页）对一个 95% 内容是文档的开源站是失真的——它把一个文档站当成商业站来抽。这不是本次审计能修的，但读者复核时应当知道：换一组同样合规的抽样（比如多取两个文档页），几项分数会不同。

