# anthropic.com — AIV audit (rubric v1.1)

> **Readiness 69 / 98 · normalised 70% · Solid** · audited 2026-09-08

Scored against [rubric v1.1](../../../rubric/v1.1.md) using only publicly observable data.
Machine-readable: [`anthropic.com.json`](anthropic.com.json), conforming to
[`schema/report.v2.json`](../../../schema/report.v2.json).

## Sampled URLs (8)

- https://www.anthropic.com/
- https://www.anthropic.com/claude/opus
- https://www.anthropic.com/claude/mythos
- https://www.anthropic.com/engineering/building-effective-agents
- https://www.anthropic.com/engineering/how-we-contain-claude
- https://www.anthropic.com/news/improving-alignment-security-efforts
- https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals
- https://www.anthropic.com/news/enterprise-frontier-safeguards

## Reachable — 15 / 15

**✓ `g.robots` 5/5** — Retrieval crawlers allowed in robots.txt

*Why this tier:* 取 5 档而非 3 档，因为文件里存在一条真实的 Allow 指令、且全文无任何 Disallow——3 档的判据文字是「未显式禁止，也未显式放行」，与实际文件不符。争议点见 notes 第 1 条：该 Allow 挂在通配 User-Agent 下，未逐个点名 GPTBot／ClaudeBot 等检索 UA。

GET https://www.anthropic.com/robots.txt → 200, 71 字节, 逐字节内容（od -c 核验）为："User-Agent: *\nAllow: /\n\nSitemap: https://www.anthropic.com/sitemap.xml\n"。全文无 Disallow 行，无针对具名 UA 的 group。

**✓ `g.reachable` 5/5** — Reachable to retrieval user-agents

*Why this tier:* 取满档：10 个检索 UA × 8 个抽样页 = 80 次请求全部 200，且去标签正文的 MD5 与浏览器 UA 逐页完全一致，不落 3 档的「部分被拦或内容不一致」。

UA 串实测（GPTBot／OAI-SearchBot／ChatGPT-User／ClaudeBot／Claude-SearchBot／PerplexityBot／Perplexity-User／Google-Extended／Applebot／Bingbot），curl -L。80/80 = HTTP 200。正文文本 MD5 逐页与 Chrome/131 基线相同，例：/news/enterprise-frontier-safeguards 浏览器与 10 个 UA 的正文文本均为 16498 字节 / md5 fd8b3e1178425b413152eb3baa2cdc75。原始 HTML 在该页存在 263 字节差（278451 vs 278188，Bingbot／Applebot／Google-Extended 一侧），diff 后确认差异仅为 Next.js 的 <!--$-->/<!--/$--> Suspense 占位注释，去标签文本零差异。首页三次重复抓取 MD5 恒为 24f96aa40b0f5d802155079224f2151f，证明响应确定、可复核。/engineering/how-we-contain-claude 的 Google-Extended 首次返回 curl code=000（传输层瞬断），重试三次均 200 / 228182 字节 / 正文 md5 7be0311cd55434f1c1abd08bdb687607，与基线一致。

**✓ `g.ssr` 5/5** — Main content server-rendered

*Why this tier:* 取满档：8/8 页在不执行 JS 的原始 HTML 响应里就含完整正文，不落 3 档的「部分页可见」。

curl 原始 HTML 去 script/style 后提取正文字数：首页 695 词、/claude/opus 2149 词、/claude/mythos 995 词、/engineering/building-effective-agents 2987 词、/engineering/how-we-contain-claude 4579 词、/news/improving-alignment-security-efforts 4071 词、/news/investigating-incidents-cybersecurity-evals 3590 词、/news/enterprise-frontier-safeguards 2487 词。命中原句（均出自未执行 JS 的响应体）：首页「AI will have a vast impact on the world. Anthropic is a public benefit corporation dedicated to securing its benefits and mitigating its risks.」；/engineering/building-effective-agents「The basic building block of agentic systems is an LLM enhanced with augmentations such as retrieval, tools, and memory.」；/news/investigating-incidents-cybersecurity-evals「After reviewing 141,006 evaluation runs where Claude could have obtained internet access…」。8/8 通过。

## Understandable — 6 / 22

**✓ `p1.sitemap` 4/4** — Sitemap discoverable and fresh

*Why this tier:* 取满档：robots.txt 显式声明路径、返回 200，且 lastmod 覆盖率 100%（不是「多数」而是全部），故不止步于 2 档。

robots.txt 第 4 行声明 Sitemap: https://www.anthropic.com/sitemap.xml。GET 该地址 → 200, 68561 字节, Content-Type application/xml。<loc> 计数 524，<lastmod> 计数 524（覆盖率 524/524 = 100%）。lastmod 大体逐页独立：最集中的一个时间戳 2026-09-08T13:36:02.671Z 仅 26/524 页共用。抽样 8 页在 sitemap 中的 lastmod 分别为 2026-09-08 / 2026-06-09 / 2026-06-09 / 2026-08-10 / 2026-06-06 / 2026-09-07 / 2026-09-04 / 2026-09-02。

**✗ `p1.llms-txt` 0/5** — llms.txt present and structured

*Why this tier:* 取 0 档：连 2 档的「存在且 200」都不满足——所有常见路径均 404，robots.txt 也未声明替代路径。

GET（curl -L，浏览器 UA）：/llms.txt → 404（59739 字节 text/html 404 页）、/.well-known/llms.txt → 404（59767 字节）。robots.txt 全文 71 字节，除 Sitemap 外无任何其他声明行，不存在非约定路径的可发现入口。

**✗ `p1.organization` 0/6** — Organization + WebSite sitewide

*Why this tier:* 取 0 档而非 3 档：3 档要求 Organization 与 WebSite「有其一」，而被审计主机上两者皆无——首页及 8 页抽样中 schema.org 字符串出现 0 次。见 notes 第 2 条：同集团的 claude.com 上确有完整 Organization 图谱，但那不在本次审计域名内。

对 8 个抽样页做 <script type="application/ld+json"> 抽取：首页 0 块、/engineering/building-effective-agents 0 块、/engineering/how-we-contain-claude 0 块、3 个 news 页各 0 块；/claude/opus 与 /claude/mythos 各 1 块且仅为 FAQPage。对首页与 4 个正文页做原始 HTML grep："schema.org" 命中 0 次、"ld+json" 命中 0 次、itemtype= 命中 0 次。全站唯一的 Organization 图谱出现在 https://www.anthropic.com/product/claude-code，但该 URL 301 跳到 https://claude.com/product/claude-code，@id 为 https://www.anthropic.com/#organization、logo 为 https://claude.com/icon.png——即该结构化数据由 claude.com 提供，anthropic.com 自身不返回。

**✗ `p1.breadcrumb` 0/3** — BreadcrumbList on nested pages

*Why this tier:* 取 0 档：站点确有层级（/news/*、/engineering/*、/claude/*、/company/leadership），故不退出分母；但 8 个抽样页的 JSON-LD 中 BreadcrumbList 出现 0 次，连 2 档的「部分层级页有」都不成立。

8 页 JSON-LD 抽取结果：仅 /claude/opus 与 /claude/mythos 各含 1 个 FAQPage，无任何 BreadcrumbList；其余 6 页 ld+json 块数为 0。层级存在的证据：sitemap 中 /news 前缀 260 条、/research 155 条、/engineering 25 条、/legal 22 条，且存在 /company/leadership 这类二级路径。

**◐ `p1.page-type` 2/4** — Page-type schema where applicable

*Why this tier:* 取 2 档「部分页型有」而非 4 档：FAQPage 在 2/2 个模型产品页上齐全且字段真实，但文档型页（/engineering/* 属 HowTo 形态）与新闻页均无对应页型 schema，达不到「适用页型普遍有」。

/claude/opus 的 FAQPage 含 2 条真实问答，原句：{"@type":"Question","name":"When should I use Claude Opus 5?"} / {"name":"How much does it cost to use Claude Opus 5?"}，且与页面可见 H3 完全一致。/claude/mythos 的 FAQPage 同样 2 条："Why did you create a new version of Mythos for general availability?" / "How can I apply for access to Mythos 5.1?"。反面：/engineering/building-effective-agents 有 9 个 H2、10 个 H3 的分步指南结构（"Workflow: Prompt chaining"、"Workflow: Routing"…）却 0 个 ld+json 块，无 HowTo；3 个 news 页 0 个 ld+json 块，无 Article。命中页型 schema 的页数：2/8。

## Content Citability — 27 / 35

**✓ `p2.answer-passages` 9/9** — Self-contained answer passages

*Why this tier:* 取 9 档「多数页有」：7/8 页在正文前部含 25–120 词、可整段摘出的自足答案段（超过半数 4/8，达到多数）。未止于 7 档是因为命中率 7/8 已明显高于半数。

按 25–120 词窗口统计正文 <p>：首页 0 段真实自足段（3 个命中项经检查全是导航／卡片文本拼接，如 "Read moreRead more Latest releasesIntroducing Opus 5…"）→ 不计；/claude/opus 12 段命中，代表原句（46 词）"Pricing for Opus 5 starts at $5 per million input tokens and $25 per million output tokens, with up to 90% cost savings with prompt caching and 50% savings with batch processing."；/claude/mythos 8 段命中，代表原句（83 词）"Claude Mythos 5.1 is available to vetted cyberdefenders and life scientists through our trusted access programs…"；/engineering/building-effective-agents 命中（61 词）"'Agent' can be defined in several ways. Some customers define agents as fully autonomous systems…"；/engineering/how-we-contain-claude 命中（99 词）"The first is to supervise the agent's behavior via a human-in-the-loop… Our telemetry showed users approved roughly 93% of permission prompts."；/news/improving-alignment-security-efforts 首段即命中（90 词）"On July 30, we reported three incidents in which Claude models gained unauthorized access to real computer systems…"；/news/investigating-incidents-cybersecurity-evals 命中（53 词）"After reviewing 141,006 evaluation runs where Claude could have obtained internet access, we identified three incidents…"；/news/enterprise-frontier-safeguards 首段命中（71 词）"Today we're announcing Enterprise Frontier Safeguards (EFS), a solution that combines the privacy of zero data retention (ZDR) with state-of-the-art safeguards for detecting misuse."。通过 7/8。英文按 25–120 词判定（量表约定）。

**✓ `p2.question-intent` 7/7** — Headings match how people ask

*Why this tier:* 取 7 档「多数贴近」：5/8 页标题本身是自然语言任务句／说明句，另 2 个品牌标签型模型页承载字面问句小标题，合计 7/8 页可被自然提问命中；没有一页标题是纯关键词串，故不落 0 档。边界争议见 notes 第 3 条——按最严口径（只看 <title>／H1、且把第一人称新闻标题排除）只有 3/8，会掉到 3 档。

8 页 H1 原文：① "AI research and products that put safety at the frontier"（品牌口号，不计）② "Claude Opus 4.8"（品牌标签，标题不计，但页内 H3 为字面问句 "When should I use Claude Opus 5?" 与 "How much does it cost to use Claude Opus 5?"，计入）③ "Claude Claude Mythos 5"（同上，H3 为 "Why did you create a new version of Mythos for general availability?" 与 "How can I apply for access to Mythos 5.1?"，计入）④ "Building effective agents"（任务句，计入；H2 含 "What are agents?"、"When (and when not) to use agents"）⑤ "How we contain Claude across products"（How X works 说明句，计入）⑥ "Improving our alignment and security efforts"（任务句，计入）⑦ "Investigating three real-world incidents in our cybersecurity evaluations"（说明句，计入；H2 含 "What happened"、"How we're responding"）⑧ "Developing Enterprise Frontier Safeguards with our customers"（说明句，计入；H2 含 "How EFS works"）。命中 7/8；纯关键词串标题 0/8。

**◐ `p2.freshness` 3/6** — Freshness signal present

*Why this tier:* 取 3 档而非 6 档：6 档是合取条件「多数页有 + 与 dateModified 一致」，前半满足（页面可见日期），后半不成立——全站 8 页的结构化数据与 meta 中 dateModified／article:modified_time 出现 0 次，唯一的修改信号（sitemap lastmod）与页面可见日期在多页上互相矛盾，无法「一致」。见 notes 第 4 条。

页面级可见日期（紧跟 H1）5/8："Published Dec 19, 2024"（building-effective-agents）、"Published May 25, 2026"（how-we-contain-claude）、"Aug 31, 2026"（improving-alignment-security-efforts）、"Jul 30, 2026" 并含正文 "Updated Aug 3:"（investigating-incidents）、"Sep 1, 2026"（enterprise-frontier-safeguards）。另 3 页（首页、/claude/opus、/claude/mythos）只有卡片级日期（"July 24, 2026"、"May 28, 2026"、"Sep 1, 2026"），无页面级日期。机器可读日期：8 页 ld+json 中 datePublished／dateModified 各 0 次；<head> 中含 date/time/publish/modif/author 关键字的 meta 标签 8 页均为空集（仅有 twitter:creator=@AnthropicAI）。冲突证据：/engineering/building-effective-agents 页面显示 "Published Dec 19, 2024" 且正文自述 "Much of the tooling landscape described in this post has changed since December 2024"，而 sitemap lastmod 为 2026-08-10T22:57:30.000Z，页面不给出任何更新日期；/news/improving-alignment-security-efforts 页面 "Aug 31, 2026" vs sitemap lastmod 2026-09-07T09:43:45.000Z。

**◐ `p2.sourced-stats` 5/7** — Statistics carry a source

*Why this tier:* 取 5 档「多数标注」而非 7 档：带数字／结论的 6 个页面中 4 个有出处标注（脚注或行内归因），已过半；但 7 档要求「来源可点击可核实」，而占多数的标注是自引式、无链接的（基准脚注、内部遥测数据），只有 2 页的关键来源是可点击外链。

带数字页 6 个（首页无数字）。已标注 4/6：① /claude/mythos 基准脚注原句 "Terminal-Bench-Science 0.1: The standard error is ±3.5–4.5 pts per model. The public leaderboard (3 trials/task, Claude Code harness) reports Claude Opus 5 at 30.0% and Claude Fable 5 at 21.4%; our setup reproduces them at 29.0% and 24.7%, respectively, both within noise."（有方法学，无超链接）② /engineering/how-we-contain-claude "Our telemetry showed users approved roughly 93% of permission prompts." 及脚注 "roughly 0.4% of benign commands blocked… ~17% of overeager actions get through"（自引，无链接），但页面另有 10 条非本域外链，含 https://www.nccoe.nist.gov/projects/software-and-ai-agent-identity-and-authorization、https://www.iso.org/standard/42001、https://media.defense.gov/2026/Apr/30/... ③ /news/improving-alignment-security-efforts 2 条可点击外链：https://www.aisi.gov.uk/blog/incident-report-unsanctioned-agent-behaviour-during-cyber-testing、https://openai.com/index/hugging-face-model-evaluation-security-incident/，另有 6 条脚注 ④ /news/investigating-incidents-cybersecurity-evals "141,006 evaluation runs" 配 3 条可点击外链（openai.com 披露、irregular.com、cybench.github.io）。未标注 2/6：/claude/opus 的基准数字以图表呈现且无脚注（grep "standard error|leaderboard|±" 在正文文本中 0 命中，客户证言虽有具名归因如 "Scott Wu, CEO"）；/news/enterprise-frontier-safeguards "more than 100 customers" 无出处，全页非本域外链数 = 0。

**◐ `p2.named-author` 3/6** — Named, verifiable authorship

*Why this tier:* 取 3 档「署真实姓名」：确有真人署名，故不落 0 档；但 6 档要求姓名链向可核实的身份页，8 页中署名处均为纯文本、无任何 <a> 链接，也无 author schema。争议在于署名覆盖率只有 2/8——3 档判据未设页数门槛，故按字面取 3。

命中原句：/engineering/building-effective-agents 第 150 行 "Written by Erik S. and Barry Zhang."；/engineering/how-we-contain-claude 第 191 行 "Written by Max McGuinness, Mikaela Grace, Jiri De Jonghe, Jake Eaton, and Abel Ribbink."（后附 19 人致谢名单）。两处均无超链接、无 mailto、无 sameAs。3 个 news 页（improving-alignment-security-efforts、investigating-incidents-cybersecurity-evals、enterprise-frontier-safeguards）grep "^(by |author)" 与 "Written by" 均 0 命中，只有机构口吻的 "we"。8 页 <meta name="author"> 命中 0 次；唯一作者类 meta 为 <meta name="twitter:creator" content="@AnthropicAI"/>（机构账号）。署名页 2/8。

## Brand Credibility — 14 / 18

**✓ `p3.listings` 4/4** — Third-party listings

*Why this tier:* 取满档「5 家以上」：实测 200 且确为本品牌的第三方平台已达 7 家，超过 4 档门槛，不必依赖被反爬拦截的 Crunchbase／G2。

curl -L 实测（浏览器 UA）：https://www.linkedin.com/company/anthropicresearch → 200 / 335783 字节；https://github.com/anthropics → 200 / 299808；https://apps.apple.com/us/app/claude-by-anthropic/id6473753684 → 200 / 744365，<title> 为 "‎Claude by Anthropic App - App Store"；https://play.google.com/store/apps/details?id=com.anthropic.claude → 200 / 1201066；https://aws.amazon.com/marketplace/seller-profile?id=seller-3ss46uphdvkfe → 200 / 192878；https://www.youtube.com/@anthropic-ai → 200 / 1165045；https://x.com/AnthropicAI → 200 / 269299。计 7 家。未计入（返回 403 反爬，无法确证收录状态，不作正反判定）：https://www.crunchbase.com/organization/anthropic → 403 / 5487 字节；https://www.g2.com/products/anthropic-claude/reviews → 403 / 1704 字节。

**✓ `p3.mentions` 4/4** — Independent mentions

*Why this tier:* 取满档「多渠道持续提及」而非 3 档「有独立报道或评测」：独立来源不是零星几家，而是 65 个不同域名、跨主流财经／科技／通讯社多渠道，且时间上延续至审计当月。

以英文维基百科 Anthropic 条目参考文献区为可复核样本（GET → 200 / 660932 字节）：References 段外链 242 条、去重后 65 个非维基域名。计数前列：cnbc.com 14、reuters.com 12、techcrunch.com 10、venturebeat.com 8、theverge.com 7、arstechnica.com 7、nytimes.com 5、nbcnews.com 4、time.com 4、bbc.com 4、wsj.com 3、bloomberg.com 3、ft.com 3、axios.com 3、theguardian.com 3、washingtonpost.com 2、wired.com 2、technologyreview.com 2（anthropic.com 自引仅 12 条，占比低）。当期独立渠道抽查：Salesforce 官方新闻稿 https://www.salesforce.com/news/press-releases/2026/08/26/salesforce-and-anthropic-announce-claudeforce/（2026-08-26，第三方主体发布）。

**✓ `p3.knowledge-graph` 4/4** — Knowledge-graph entity

*Why this tier:* 本项为 0／4 二元档，实体条目确实存在，直接取 4。

Wikidata API（action=wbsearchentities&search=Anthropic）返回 Q116758847 | Anthropic | "American artificial intelligence corporation"，另有 Q118876059 | Claude | "large language model family developed by Anthropic"。英文维基百科 REST summary 返回 title "Anthropic"，首句 "Anthropic, PBC is an American artificial intelligence (AI) public benefit corporation headquartered in San Francisco, California. Its flagship product is Claude, a series of proprietary large language models (LLMs)." 条目页 GET → 200 / 660932 字节。

**✗ `p3.sameas` 0/3** — sameAs complete and resolving

*Why this tier:* 取 0 档：判据「未声明记 0 分」。被审计域名 www.anthropic.com 在 8 页抽样中不输出任何 Organization／sameAs，属未声明；本项按量表明文不退出分母。

8 个抽样页 ld+json 抽取：首页与 5 个正文页各 0 块，2 个模型页各 1 块且仅 FAQPage，全部 8 页中 "sameAs" 字符串命中 0 次。对照：同集团 claude.com 在 /product/claude-code 上确有 sameAs 数组（含 https://en.wikipedia.org/wiki/Anthropic、https://www.linkedin.com/company/anthropicresearch、https://x.com/AnthropicAI、https://github.com/anthropics、https://www.youtube.com/@anthropic-ai），但该响应来自 301 后的 claude.com，不是本次审计主机返回。

**◐ `p3.video` 2/3** — Video and multimodal presence

*Why this tier:* 取 2 档而非 3 档：3 档是合取条件「持续输出 + 站内带 VideoObject」，前半明显满足（近半年稳定更新），后半完全不成立（8 页 VideoObject 命中 0）。2 档判据文字「内容零星」与实测不符，属阶梯描述与证据错位，见 notes 第 5 条。

官方频道 RSS：https://www.youtube.com/feeds/videos.xml?channel_id=UCrDwWp7EBBv4NwvScIpBDOA → 200 / 23919 字节，channel title "Anthropic"，15 条 entry。近 6 个月发布密度：2026-09-01 "Meet Claude Fable 5.1"、2026-09-01 "Introducing Claude Fable 5.1"、2026-08-28 "Model Hardware Standard: AI operating physical equipment"、2026-08-27（2 条）、2026-08-10、2026-07-06、2026-06-09、2026-05-07、2026-04-07。站内标注：对 8 个抽样页 grep -il "VideoObject" 与 "speakable" 均 0 文件命中。

## Answer Fit — 7 / 8

**✓ `p4.answer-shape` 4/4** — Content shaped for extraction

*Why this tier:* 取 4 档：小标题层级全站齐备、段落长度落在可引用区间（各页中位数 24–67 词，仅 3 段超 150 词）、列表在 6/8 页存在；2 档判据「段落偏长」与实测直接矛盾，故不适用。缺口是表格几乎为零（8 页仅 1 个 <table>），属 4 档合取条件里的短板，见 notes 第 5 条。

<main> 内统计（已剔除 nav/footer/script）——首页 h2=4 h3=9 ul=6 li=27 table=0 段落中位数 29 词；/claude/opus h2=7 h3=5 li=5 table=0 中位数 29；/claude/mythos h2=6 h3=2 li=5 table=0 中位数 24；/engineering/building-effective-agents h2=9 h3=10 ul=15 ol=1 li=42 table=0 中位数 40.5 最长 127；/engineering/how-we-contain-claude h2=6 h3=4 ol=1 table=1 中位数 60.5 最长 132；/news/improving-alignment-security-efforts h2=5 h3=12 ul=2 ol=2 li=16 table=0 中位数 64，超 150 词段 2 段；/news/investigating-incidents h2=5 h3=6 li=6 table=0 中位数 67 最长 129；/news/enterprise-frontier-safeguards h2=5 h3=6 li=0 table=0 中位数 48。8 页合计 table=1。

**◐ `p4.question-coverage` 3/4** — Coverage of the questions people ask

*Why this tier:* 取 3 档「覆盖 6–8 个」而非 4 档：10 个高频问题中 8 个能在 www.anthropic.com 域内找到正面回答，另 2 个（API 上手、报价页）只有 301 到 claude.com 后才有答案，本域内无内容，故达不到 9–10 个。

逐题实测（curl -L 看落地域名）：① 有哪些模型／能力 → /claude/opus 200 r=0 ✓ ② 定价多少 → /pricing 200 r=1 落到 https://claude.com/pricing ✗（本域内仅模型页正文有一句 "Pricing for Opus 5 starts at $5 per million input tokens and $25 per million output tokens"，按半覆盖不计满）③ 会不会拿我的数据训练／留存多久 → /legal/privacy 200 r=0 ✓ 且 /news/enterprise-frontier-safeguards 正文 "Anthropic has never trained on enterprise data without explicit permission" ✓ ④ 基准表现如何 → /claude/opus、/claude/mythos 的 Benchmarks 段 ✓ ⑤ 安全框架是什么 → /responsible-scaling-policy 200 r=0 ✓ ⑥ 谁在管这家公司 → /company 200 r=0、/company/leadership（sitemap 收录）✓ ⑦ 怎么用 Claude 搭 agent → /engineering/building-effective-agents 200 r=0 ✓ ⑧ 哪些国家可用 → /supported-countries 200 r=0 ✓ ⑨ 合规／Trust center → 页脚链接指向 https://trust.anthropic.com/（子域，非 www；/trust-center 与 /security 在本域均 404）✓ 计入 ⑩ 怎么拿 API key 上手 → /api 200 r=1 落到 https://claude.com/platform/api，页脚 Developer docs 指向 https://platform.claude.com/docs ✗。本域覆盖 8/10。

**⊘ `p4.cn-engines`** — not applicable (leaves the denominator)

整项退出分母：量表规定「不面向中文市场则整项退出分母」，实测无任何中文市场投放痕迹。

## Bonus — +0 (outside the denominator)

**✗ `b.llms-full` 0/2** — llms-full.txt

*Why this tier:* 加分项未命中：文件不存在，且无可发现入口。

GET /llms-full.txt → 404（59749 字节 HTML 错误页）。robots.txt 全文 71 字节，除 Sitemap 外无声明；/llms.txt 本身 404，不存在从中发现非根路径聚合文件的可能。

**✗ `b.ai-txt` 0/2** — ai.txt

*Why this tier:* 加分项未命中：两个常见路径均 404。

GET /ai.txt → 404（59735 字节）；GET /.well-known/ai.txt → 404（59763 字节）。

**✗ `b.geo-link` 0/1** — GEO link tags

*Why this tier:* 加分项未命中：<head> 中无任何面向 AI 检索的 link rel。

8 页 <head> 的 link rel 去重集合：首页 [apple-touch-icon, canonical, preconnect, shortcut icon, stylesheet]；其余 7 页 [apple-touch-icon, canonical, icon, mask-icon, preload, shortcut icon, stylesheet]。无 llms、ai-policy、alternate type=text/markdown 等 AI 检索相关 rel。

**✗ `b.speakable` 0/1** — speakable markup

*Why this tier:* 加分项未命中：无 speakable 标注，且 6/8 页根本没有 JSON-LD 容器。

对 8 个抽样页 grep -il "speakable" → 0 文件命中；其中 6 页 ld+json 块数为 0，另 2 页仅含 FAQPage。

## Citation performance — not scored

本次不测「AI 引用表现」，也不给分。量表把它列为不设满分、单独报告的结果型指标：它由站点就绪度与时间共同决定，且同一问题在同一引擎多次提问的结果不同，不可复现——把不可复现的观察折进一个 100 分制会同时伤害客户和口径可信度。本次审计的工具链只做 HTTP 层与 HTML 层的可复核取证（状态码、字节数、MD5、命中原句），未对 ChatGPT／Perplexity／Google AI Overviews 等做行业真实问题的引用实测，因此关于「Anthropic 在 AI 搜索里被引用得多不多」这份报告不提供任何结论，读者也不应从 70 分反推引用表现。若需要该项，应另立一轮实测：固定 10 个行业真实问题、固定引擎与时间窗、每题重复 3 次、记录被引 URL 与引用位次，作为独立附录报告。

## Auditor's caveats

- 【最有争议的一条，直接决定总分是否被封顶 40】g.robots 我给了满档 5。Anthropic 的 robots.txt 全文只有 71 字节：`User-Agent: *` + `Allow: /` + 一行 Sitemap，没有逐个点名 GPTBot／ClaudeBot／PerplexityBot 等检索 UA。量表 5 档写的是「对主流检索 UA 明确放行」，字面可以解读成必须具名。我判 5 的理由是：3 档的判据文字是「未显式禁止，也未显式放行」，而这个文件里确实存在一条 Allow 指令、且全文无任何 Disallow，按 RFC 9309 十个检索 UA 全部落入 `*` 组并拿到显式放行——3 档的描述与事实不符，就不能用 3 档。反对意见是合理的：如果审计者坚持「具名才算明确」，g.robots 就是 3 分，门槛项未拿满，normalised 从 70 直接封顶到 40，档位从「基础扎实」掉到「起步期」。这是全篇分差最大的单点，复核者应优先看这里。我认为量表本身应当在 v1.2 里把「通配 Allow: / 是否等同具名放行」写死，不要留给审计者。
- 【域名边界，影响 p1.organization / p3.sameas 两项共 9 分】Anthropic 的产品面已迁到 claude.com：/product/claude-code 301 → claude.com/product/claude-code，/pricing 301 → claude.com/pricing，/api 301 → claude.com/platform/api，/learn 301 → academy.claude.com，/engineering/claude-code-best-practices 301 → code.claude.com/docs。完整的 Organization + Brand + SoftwareApplication + BreadcrumbList + sameAs 图谱只在 301 之后的 claude.com 响应里存在，@id 却写着 https://www.anthropic.com/#organization。我按「审计对象是 www.anthropic.com」判 p1.organization=0、p3.sameas=0。另一种同样站得住的口径是：抓取规则要求跟随重定向，跟随后拿到的就是这些 schema，因此应该记分——那样 p1.organization 可到 6、p3.sameas 可到 3，总分会到 78（仍是「基础扎实」，但接近 83 的「领先」线）。我选择严口径是因为「站方可修」的边界要清楚：anthropic.com 首页自己不输出任何结构化数据，这是本域可修的真实缺口；但我承认，从 AI 检索的实际体验看，用户和爬虫最终确实拿到了那份 Organization 图谱。这条建议在交付给客户时明确写成「跨域资产归属问题」，而不是简单的「你没做 schema」。
- 【p2.question-intent 的 7 分是全篇第二宽松的判定】我按「页面标题或其小标题能否被自然提问命中」判 7/8，取了 7 档。若只看 <title>／H1、且认为第一人称新闻标题（"Improving our alignment and security efforts"、"Developing Enterprise Frontier Safeguards with our customers"）是机构公告口吻而非用户会问的话，命中就只剩 3/8（building-effective-agents、how-we-contain-claude、investigating-incidents），落到 3 档，本项从 7 掉到 3。两个模型页 H1 是纯品牌标签（"Claude Opus 4.8"、"Claude Claude Mythos 5"——后者还有一个可见的 "Claude Claude" 重复渲染 bug），我是靠它们页内的字面问句 H3 把它们捞回来的，这一步把「标题」扩展到了「小标题」，超出了判据字面。复核者若不接受这个扩展，本项应记 3 或 5。
- 【p2.freshness 的 3 分反而是全篇最严的判定，且暴露量表阶梯本身的问题】8 个抽样页全部有可见日期（5 页是紧跟 H1 的页面级日期，3 页是卡片级），按「多数页有」应该够 6 档；但 6 档是合取——还要求「与 dateModified 一致」，而全站 8 页的 JSON-LD 与 meta 里 dateModified／article:modified_time 命中 0 次，唯一的修改信号是 sitemap lastmod，且它与页面日期在多页上互相矛盾（building-effective-agents 页面写 "Published Dec 19, 2024"、正文自承内容已过时，sitemap lastmod 却是 2026-08-10；improving-alignment 页面 Aug 31 vs lastmod Sep 07）。合取不成立就只能退回 3 档「部分页有」，可 3 档的措辞「部分」又明显低估了 8/8 的可见日期覆盖率。也就是说这一项无论给 3 还是给 6，措辞都对不上事实。我按「取证据实际满足的最高档」的规则选了 3，但这是本篇里我最不满意的一格，建议 v1.2 把 6 档拆成「多数页有可见日期」与「且有一致的 dateModified」两级。
- 【还有两处阶梯与证据错位，方向相反，我一严一宽，此处交代清楚】(a) p3.video 我给 2：Anthropic 的 YouTube 频道近半年稳定更新（2026-04 到 2026-09 至少 10 条），完全不是 2 档说的「内容零星」，但 3 档要求「站内带 VideoObject」而 8 页命中 0，只能退到 2——这里我按严口径，实际内容产出被低估了。(b) p4.answer-shape 我给了满档 4：小标题层级完备、段落中位数 24–67 词正落在可引用区间、6/8 页有列表，但 4 档还要求「表格齐备」，而 8 页合计只有 1 个 <table>——模型页的基准数字是用图表／SVG 呈现的，对 AI 抽取其实比表格差。严格按合取应该扣，我没扣，理由是 2 档的「段落偏长」与实测直接矛盾、掉到 2 会更失真。这一格若按合取从严，本项从 4 掉到 2，总分从 70 降到 68，档位不变。另外两处次要存疑一并记下：p2.named-author 我给 3，但真人署名只出现在 2/8 页、三个新闻页完全无署名，3 档判据没写页数门槛所以我按字面给了分，实质覆盖率偏低；p3.listings 我数了 7 家，但 Crunchbase 与 G2 都返回 403（反爬），我按「无法确证」既不记正也不记负——若这两家实际有收录，只是把 4 档坐得更实，不改变分数。

