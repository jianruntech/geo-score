# anthropic.com — AIV audit (rubric v1.1)

> **Readiness 69 / 98 · normalised 70% · Solid** · audited 2026-09-08

Scored against [rubric v1.1](../../../rubric/v1.1.md) using only publicly observable data.
Machine-readable: [`anthropic.com.json`](anthropic.com.json), conforming to
[`schema/report.v2.json`](../../../schema/report.v2.json).

> **The gate rule changed after this audit ran.** These five audits were scored while a
> gate check short of full marks capped the whole score at 40. Several of the caveats below
> are the auditor saying, in real time, that the cap was producing the wrong answer — and
> they were right. The rule now caps only when a gate scores **zero**. The scores shown here
> are recomputed under the corrected rule; the caveats are left exactly as written, because
> they are the record of how the error was found.
> [What changed and why](../../../rubric/calibration-v1.1.md#a-design-error-the-re-audit-caught)

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

*Why this tier:* Tier 5 rather than tier 3, because the file contains a real Allow directive and no Disallow anywhere — tier 3's criterion reads "no explicit Disallow, but no explicit Allow either", which does not match the actual file. The contested point is in note 1: the Allow sits under a wildcard User-Agent and does not name individual retrieval user-agents such as GPTBot or ClaudeBot.

GET https://www.anthropic.com/robots.txt → 200, 71 bytes; the byte-for-byte content (verified with od -c) is: "User-Agent: *\nAllow: /\n\nSitemap: https://www.anthropic.com/sitemap.xml\n". There is no Disallow line anywhere in the file, and no group for any named user-agent.

**✓ `g.reachable` 5/5** — Reachable to retrieval user-agents

*Why this tier:* Full tier: 10 retrieval user-agents × 8 sampled pages = 80 requests, all 200, and the MD5 of the tag-stripped body text matches the browser user-agent exactly on every page, so it does not fall to tier 3's "some are blocked, or the body differs from what a browser receives".

Tested with live user-agent strings (GPTBot / OAI-SearchBot / ChatGPT-User / ClaudeBot / Claude-SearchBot / PerplexityBot / Perplexity-User / Google-Extended / Applebot / Bingbot), curl -L. 80/80 = HTTP 200. The body-text MD5 matches the Chrome/131 baseline page by page; for example, on /news/enterprise-frontier-safeguards the body text is 16498 bytes / md5 fd8b3e1178425b413152eb3baa2cdc75 for the browser and for all 10 user-agents alike. The raw HTML on that page differs by 263 bytes (278451 vs 278188, on the Bingbot / Applebot / Google-Extended side); diffing confirms the difference is only Next.js <!--$-->/<!--/$--> Suspense placeholder comments, with zero difference in the tag-stripped text. Three repeat fetches of the home page returned MD5 24f96aa40b0f5d802155079224f2151f every time, showing the response is deterministic and re-checkable. On /engineering/how-we-contain-claude, Google-Extended returned curl code=000 on the first attempt (a momentary transport-layer break); three retries all returned 200 / 228182 bytes / body md5 7be0311cd55434f1c1abd08bdb687607, consistent with the baseline.

**✓ `g.ssr` 5/5** — Main content server-rendered

*Why this tier:* Full tier: 8 of 8 pages carry the complete body text in the raw HTML response without JS execution, so it does not fall to tier 3's "present on some sampled pages".

Body word counts extracted from the raw curl HTML after stripping script/style: home page 695 words, /claude/opus 2149 words, /claude/mythos 995 words, /engineering/building-effective-agents 2987 words, /engineering/how-we-contain-claude 4579 words, /news/improving-alignment-security-efforts 4071 words, /news/investigating-incidents-cybersecurity-evals 3590 words, /news/enterprise-frontier-safeguards 2487 words. Sentences matched (all from response bodies with no JS executed): home page "AI will have a vast impact on the world. Anthropic is a public benefit corporation dedicated to securing its benefits and mitigating its risks."; /engineering/building-effective-agents "The basic building block of agentic systems is an LLM enhanced with augmentations such as retrieval, tools, and memory."; /news/investigating-incidents-cybersecurity-evals "After reviewing 141,006 evaluation runs where Claude could have obtained internet access…". 8/8 pass.

## Understandable — 6 / 22

**✓ `p1.sitemap` 4/4** — Sitemap discoverable and fresh

*Why this tier:* Full tier: robots.txt declares the path explicitly, the file returns 200, and lastmod coverage is 100% (not "most" but all), so it does not stop at tier 2.

Line 4 of robots.txt declares Sitemap: https://www.anthropic.com/sitemap.xml. GET on that address → 200, 68561 bytes, Content-Type application/xml. <loc> count 524, <lastmod> count 524 (coverage 524/524 = 100%). The lastmod values are largely independent per page: the most-shared single timestamp, 2026-09-08T13:36:02.671Z, is used by only 26 of 524 pages. The sitemap lastmod values for the 8 sampled pages are 2026-09-08 / 2026-06-09 / 2026-06-09 / 2026-08-10 / 2026-06-06 / 2026-09-07 / 2026-09-04 / 2026-09-02.

**✗ `p1.llms-txt` 0/5** — llms.txt present and structured

*Why this tier:* Tier 0: even tier 2's "present and returns 200" is not met — every common path returns 404, and robots.txt declares no alternative path.

GET (curl -L, browser user-agent): /llms.txt → 404 (a 59739-byte text/html 404 page); /.well-known/llms.txt → 404 (59767 bytes). The whole of robots.txt is 71 bytes and carries no declaration line other than Sitemap, so there is no discoverable entry point at a non-conventional path.

**✗ `p1.organization` 0/6** — Organization + WebSite sitewide

*Why this tier:* Tier 0 rather than tier 3: tier 3 requires "one of the two present" for Organization and WebSite, and the audited host has neither — the string schema.org appears 0 times on the home page and across the 8-page sample. See note 2: the sibling host claude.com does carry a complete Organization graph, but that is outside the domain under audit.

Extracting <script type="application/ld+json"> from the 8 sampled pages: home page 0 blocks, /engineering/building-effective-agents 0 blocks, /engineering/how-we-contain-claude 0 blocks, the 3 news pages 0 blocks each; /claude/opus and /claude/mythos have 1 block each, and it is only a FAQPage. grep over the raw HTML of the home page and 4 body pages: "schema.org" 0 hits, "ld+json" 0 hits, itemtype= 0 hits. The only Organization graph anywhere on the site appears at https://www.anthropic.com/product/claude-code, but that URL 301s to https://claude.com/product/claude-code, with @id https://www.anthropic.com/#organization and logo https://claude.com/icon.png — that is, the structured data is served by claude.com; anthropic.com does not return it itself.

**✗ `p1.breadcrumb` 0/3** — BreadcrumbList on nested pages

*Why this tier:* Tier 0: the site does have a hierarchy (/news/*, /engineering/*, /claude/*, /company/leadership), so the check does not leave the denominator; but BreadcrumbList appears 0 times in the JSON-LD of the 8 sampled pages, so even tier 2's "present on some nested pages" does not hold.

JSON-LD extraction across the 8 pages: only /claude/opus and /claude/mythos contain 1 FAQPage each, and no BreadcrumbList; the other 6 pages have 0 ld+json blocks. Evidence that the hierarchy exists: the sitemap holds 260 entries under the /news prefix, 155 under /research, 25 under /engineering and 22 under /legal, and second-level paths such as /company/leadership exist.

**◐ `p1.page-type` 2/4** — Page-type schema where applicable

*Why this tier:* Tier 2, "present on some page types", rather than tier 4: FAQPage is complete with genuine field values on 2 of 2 model product pages, but the documentation-style pages (/engineering/* are HowTo in shape) and the news pages carry no schema for their page type, which falls short of "present across applicable page types".

The FAQPage on /claude/opus contains 2 genuine question-answer pairs, verbatim: {"@type":"Question","name":"When should I use Claude Opus 5?"} / {"name":"How much does it cost to use Claude Opus 5?"}, matching the page's visible H3s exactly. The FAQPage on /claude/mythos likewise carries 2: "Why did you create a new version of Mythos for general availability?" / "How can I apply for access to Mythos 5.1?". Against that: /engineering/building-effective-agents has a step-by-step guide structure of 9 H2s and 10 H3s ("Workflow: Prompt chaining", "Workflow: Routing", …) yet 0 ld+json blocks and no HowTo; the 3 news pages have 0 ld+json blocks and no Article. Pages carrying page-type schema: 2/8.

## Content Citability — 27 / 35

**✓ `p2.answer-passages` 9/9** — Self-contained answer passages

*Why this tier:* Tier 9, "on most pages": 7 of 8 pages carry a 25–120 word self-contained answer passage in the upper part of the body that can be lifted out whole (past the 4/8 half mark, hence "most"). It does not stop at tier 7 because a hit rate of 7/8 is clearly above half.

Counting body <p> elements against a 25–120 word window: home page 0 genuine self-contained passages (the 3 candidates turn out on inspection to be navigation and card text concatenated, e.g. "Read moreRead more Latest releasesIntroducing Opus 5…") → not counted; /claude/opus 12 passages hit, representative sentence (46 words) "Pricing for Opus 5 starts at $5 per million input tokens and $25 per million output tokens, with up to 90% cost savings with prompt caching and 50% savings with batch processing."; /claude/mythos 8 passages hit, representative sentence (83 words) "Claude Mythos 5.1 is available to vetted cyberdefenders and life scientists through our trusted access programs…"; /engineering/building-effective-agents hits (61 words) "'Agent' can be defined in several ways. Some customers define agents as fully autonomous systems…"; /engineering/how-we-contain-claude hits (99 words) "The first is to supervise the agent's behavior via a human-in-the-loop… Our telemetry showed users approved roughly 93% of permission prompts."; /news/improving-alignment-security-efforts hits in its first paragraph (90 words) "On July 30, we reported three incidents in which Claude models gained unauthorized access to real computer systems…"; /news/investigating-incidents-cybersecurity-evals hits (53 words) "After reviewing 141,006 evaluation runs where Claude could have obtained internet access, we identified three incidents…"; /news/enterprise-frontier-safeguards hits in its first paragraph (71 words) "Today we're announcing Enterprise Frontier Safeguards (EFS), a solution that combines the privacy of zero data retention (ZDR) with state-of-the-art safeguards for detecting misuse.". 7/8 pass. English is judged on the 25–120 word window (rubric convention).

**✓ `p2.question-intent` 7/7** — Headings match how people ask

*Why this tier:* Tier 7, "most do": on 5 of 8 pages the title is itself a natural-language task or explanatory sentence, and 2 further brand-label model pages carry literal question subheads, giving 7 of 8 pages a natural question can match; no page title is a bare keyword string, so it does not fall to tier 0. The boundary dispute is in note 3 — on the strictest reading (looking only at <title>/H1 and excluding first-person news headlines) only 3/8 hit, which would drop this to tier 3.

Verbatim H1s of the 8 pages: (1) "AI research and products that put safety at the frontier" (brand slogan, not counted); (2) "Claude Opus 4.8" (brand label, title not counted, but the in-page H3s are literal questions — "When should I use Claude Opus 5?" and "How much does it cost to use Claude Opus 5?" — so counted); (3) "Claude Claude Mythos 5" (same as above; H3s are "Why did you create a new version of Mythos for general availability?" and "How can I apply for access to Mythos 5.1?", counted); (4) "Building effective agents" (task sentence, counted; H2s include "What are agents?" and "When (and when not) to use agents"); (5) "How we contain Claude across products" (a How-X-works explanatory sentence, counted); (6) "Improving our alignment and security efforts" (task sentence, counted); (7) "Investigating three real-world incidents in our cybersecurity evaluations" (explanatory sentence, counted; H2s include "What happened" and "How we're responding"); (8) "Developing Enterprise Frontier Safeguards with our customers" (explanatory sentence, counted; H2s include "How EFS works"). 7/8 hit; bare keyword-string titles 0/8.

**◐ `p2.freshness` 3/6** — Freshness signal present

*Why this tier:* Tier 3 rather than tier 6: tier 6 is a conjunction — "most pages do, and dateModified agrees with the visible date". The first half holds (visible dates on the page); the second does not — dateModified and article:modified_time appear 0 times in the structured data and meta of all 8 pages, and the only modification signal (sitemap lastmod) contradicts the visible page date on several pages, so there is nothing for it to "agree" with. See note 4.

Page-level visible dates (immediately after the H1) on 5/8: "Published Dec 19, 2024" (building-effective-agents), "Published May 25, 2026" (how-we-contain-claude), "Aug 31, 2026" (improving-alignment-security-efforts), "Jul 30, 2026" plus "Updated Aug 3:" in the body (investigating-incidents), "Sep 1, 2026" (enterprise-frontier-safeguards). The other 3 pages (home page, /claude/opus, /claude/mythos) carry only card-level dates ("July 24, 2026", "May 28, 2026", "Sep 1, 2026") and no page-level date. Machine-readable dates: datePublished and dateModified each appear 0 times in the ld+json of the 8 pages; meta tags in <head> matching the keywords date/time/publish/modif/author are an empty set on all 8 pages (only twitter:creator=@AnthropicAI is present). Conflict evidence: /engineering/building-effective-agents shows "Published Dec 19, 2024" and its body states "Much of the tooling landscape described in this post has changed since December 2024", while the sitemap lastmod is 2026-08-10T22:57:30.000Z and the page gives no update date at all; /news/improving-alignment-security-efforts shows "Aug 31, 2026" against sitemap lastmod 2026-09-07T09:43:45.000Z.

**◐ `p2.sourced-stats` 5/7** — Statistics carry a source

*Why this tier:* Tier 5, "most are attributed", rather than tier 7: of the 6 pages carrying figures or claims, 4 have a source attribution (a footnote or inline attribution), which is past half; but tier 7 requires the source to be "clickable and checkable", and the majority of the attributions are self-referential and unlinked (benchmark footnotes, internal telemetry), with only 2 pages whose key sources are clickable external links.

6 pages carry figures (the home page has none). Attributed 4/6: (1) /claude/mythos benchmark footnote, verbatim "Terminal-Bench-Science 0.1: The standard error is ±3.5–4.5 pts per model. The public leaderboard (3 trials/task, Claude Code harness) reports Claude Opus 5 at 30.0% and Claude Fable 5 at 21.4%; our setup reproduces them at 29.0% and 24.7%, respectively, both within noise." (methodology given, no hyperlink); (2) /engineering/how-we-contain-claude "Our telemetry showed users approved roughly 93% of permission prompts." and the footnote "roughly 0.4% of benign commands blocked… ~17% of overeager actions get through" (self-referential, no link), though the page does carry 10 off-domain external links, including https://www.nccoe.nist.gov/projects/software-and-ai-agent-identity-and-authorization, https://www.iso.org/standard/42001 and https://media.defense.gov/2026/Apr/30/...; (3) /news/improving-alignment-security-efforts has 2 clickable external links — https://www.aisi.gov.uk/blog/incident-report-unsanctioned-agent-behaviour-during-cyber-testing and https://openai.com/index/hugging-face-model-evaluation-security-incident/ — plus 6 footnotes; (4) /news/investigating-incidents-cybersecurity-evals pairs "141,006 evaluation runs" with 3 clickable external links (the openai.com disclosure, irregular.com, cybench.github.io). Unattributed 2/6: the benchmark figures on /claude/opus are presented as charts with no footnote (grep "standard error|leaderboard|±" returns 0 hits in the body text; the customer testimonials do carry named attribution, e.g. "Scott Wu, CEO"); /news/enterprise-frontier-safeguards gives no source for "more than 100 customers", and the page's off-domain external link count = 0.

**◐ `p2.named-author` 3/6** — Named, verifiable authorship

*Why this tier:* Tier 3, "bylined to a real person": real people are named, so it does not fall to tier 0; but tier 6 requires the name to link to a verifiable identity page, and on all 8 pages the byline is plain text with no <a> link and no author schema. The contested point is that byline coverage is only 2/8 — the tier 3 criterion sets no page-count threshold, so it is taken at its word as 3.

Sentences matched: /engineering/building-effective-agents line 150, "Written by Erik S. and Barry Zhang."; /engineering/how-we-contain-claude line 191, "Written by Max McGuinness, Mikaela Grace, Jiri De Jonghe, Jake Eaton, and Abel Ribbink." (followed by a 19-person acknowledgements list). Neither carries a hyperlink, a mailto, or sameAs. On the 3 news pages (improving-alignment-security-efforts, investigating-incidents-cybersecurity-evals, enterprise-frontier-safeguards), grep for "^(by |author)" and "Written by" returns 0 hits — only the institutional "we". <meta name="author"> appears 0 times across the 8 pages; the only author-type meta is <meta name="twitter:creator" content="@AnthropicAI"/> (an institutional account). Pages with a byline: 2/8.

## Brand Credibility — 14 / 18

**✓ `p3.listings` 4/4** — Third-party listings

*Why this tier:* Full tier, "5 or more": 7 third-party platforms return 200 and are confirmed to belong to this brand, above the tier 4 threshold, without needing to rely on Crunchbase or G2, which are blocked by anti-scraping.

Live curl -L (browser user-agent): https://www.linkedin.com/company/anthropicresearch → 200 / 335783 bytes; https://github.com/anthropics → 200 / 299808; https://apps.apple.com/us/app/claude-by-anthropic/id6473753684 → 200 / 744365, <title> "‎Claude by Anthropic App - App Store"; https://play.google.com/store/apps/details?id=com.anthropic.claude → 200 / 1201066; https://aws.amazon.com/marketplace/seller-profile?id=seller-3ss46uphdvkfe → 200 / 192878; https://www.youtube.com/@anthropic-ai → 200 / 1165045; https://x.com/AnthropicAI → 200 / 269299. 7 platforms. Not counted (403 anti-scraping, listing status cannot be confirmed, so scored neither for nor against): https://www.crunchbase.com/organization/anthropic → 403 / 5487 bytes; https://www.g2.com/products/anthropic-claude/reviews → 403 / 1704 bytes.

**✓ `p3.mentions` 4/4** — Independent mentions

*Why this tier:* Full tier, "sustained mentions across channels", rather than tier 3, "independent coverage or reviews exist": the independent sources are not a scattered few but 65 distinct domains across mainstream financial, technology and wire-service channels, continuing up to the month of the audit.

The references section of the English Wikipedia article on Anthropic is used as a re-checkable sample (GET → 200 / 660932 bytes): 242 external links in the References section, 65 distinct non-Wikipedia domains after de-duplication. Leading counts: cnbc.com 14, reuters.com 12, techcrunch.com 10, venturebeat.com 8, theverge.com 7, arstechnica.com 7, nytimes.com 5, nbcnews.com 4, time.com 4, bbc.com 4, wsj.com 3, bloomberg.com 3, ft.com 3, axios.com 3, theguardian.com 3, washingtonpost.com 2, wired.com 2, technologyreview.com 2 (anthropic.com self-citations number only 12, a low share). Spot check of an independent channel in the current period: the official Salesforce press release https://www.salesforce.com/news/press-releases/2026/08/26/salesforce-and-anthropic-announce-claudeforce/ (2026-08-26, published by a third party).

**✓ `p3.knowledge-graph` 4/4** — Knowledge-graph entity

*Why this tier:* This check is binary, 0 or 4; the entity entries do exist, so 4 outright.

The Wikidata API (action=wbsearchentities&search=Anthropic) returns Q116758847 | Anthropic | "American artificial intelligence corporation", plus Q118876059 | Claude | "large language model family developed by Anthropic". The English Wikipedia REST summary returns title "Anthropic" with the opening sentence "Anthropic, PBC is an American artificial intelligence (AI) public benefit corporation headquartered in San Francisco, California. Its flagship product is Claude, a series of proprietary large language models (LLMs)." GET on the article page → 200 / 660932 bytes.

**✗ `p3.sameas` 0/3** — sameAs complete and resolving

*Why this tier:* Tier 0: the criterion is "not declared" scores 0. The audited domain www.anthropic.com emits no Organization or sameAs across the 8-page sample, which counts as not declared; per the rubric's explicit wording this check does not leave the denominator.

ld+json extraction on the 8 sampled pages: the home page and 5 body pages have 0 blocks each; the 2 model pages have 1 block each and it is only a FAQPage; the string "sameAs" gets 0 hits across all 8 pages. For contrast: the sibling host claude.com does carry a sameAs array on /product/claude-code (including https://en.wikipedia.org/wiki/Anthropic, https://www.linkedin.com/company/anthropicresearch, https://x.com/AnthropicAI, https://github.com/anthropics, https://www.youtube.com/@anthropic-ai), but that response comes from claude.com after the 301, not from the host under audit.

**◐ `p3.video` 2/3** — Video and multimodal presence

*Why this tier:* Tier 2 rather than tier 3: tier 3 is a conjunction, "sustained output, with VideoObject on site". The first half plainly holds (steady updates over the past six months); the second does not hold at all (VideoObject gets 0 hits across the 8 pages). Tier 2's wording, "content is sparse", does not match what was measured — the tier descriptions and the evidence are misaligned here; see note 5.

Official channel RSS: https://www.youtube.com/feeds/videos.xml?channel_id=UCrDwWp7EBBv4NwvScIpBDOA → 200 / 23919 bytes, channel title "Anthropic", 15 entries. Publishing density over the past 6 months: 2026-09-01 "Meet Claude Fable 5.1", 2026-09-01 "Introducing Claude Fable 5.1", 2026-08-28 "Model Hardware Standard: AI operating physical equipment", 2026-08-27 (2 entries), 2026-08-10, 2026-07-06, 2026-06-09, 2026-05-07, 2026-04-07. On-site markup: grep -il "VideoObject" and "speakable" across the 8 sampled pages returns 0 files.

## Answer Fit — 7 / 8

**✓ `p4.answer-shape` 4/4** — Content shaped for extraction

*Why this tier:* Tier 4: the subheading hierarchy is complete site-wide, paragraph length sits in the quotable range (per-page medians of 24–67 words, only 3 paragraphs over 150 words), and lists are present on 6/8 pages; tier 2's criterion, "paragraphs run long", directly contradicts the measurements and so does not apply. The gap is that tables are almost absent (1 <table> across 8 pages), the weak leg of tier 4's conjunction; see note 5.

Counts inside <main> (nav/footer/script removed) — home page h2=4 h3=9 ul=6 li=27 table=0, paragraph median 29 words; /claude/opus h2=7 h3=5 li=5 table=0, median 29; /claude/mythos h2=6 h3=2 li=5 table=0, median 24; /engineering/building-effective-agents h2=9 h3=10 ul=15 ol=1 li=42 table=0, median 40.5, longest 127; /engineering/how-we-contain-claude h2=6 h3=4 ol=1 table=1, median 60.5, longest 132; /news/improving-alignment-security-efforts h2=5 h3=12 ul=2 ol=2 li=16 table=0, median 64, 2 paragraphs over 150 words; /news/investigating-incidents h2=5 h3=6 li=6 table=0, median 67, longest 129; /news/enterprise-frontier-safeguards h2=5 h3=6 li=0 table=0, median 48. Across the 8 pages, table=1 in total.

**◐ `p4.question-coverage` 3/4** — Coverage of the questions people ask

*Why this tier:* Tier 3, "6–8 covered", rather than tier 4: of 10 high-frequency questions, 8 have a direct answer within the www.anthropic.com domain, while the other 2 (getting started with the API, the pricing page) are answered only after a 301 to claude.com and have no content on this domain, so it does not reach 9–10.

Question-by-question testing (curl -L, checking the landing domain): (1) which models and capabilities are there → /claude/opus 200 r=0 ✓; (2) how much does it cost → /pricing 200 r=1, lands on https://claude.com/pricing ✗ (within this domain there is only one sentence in a model page's body, "Pricing for Opus 5 starts at $5 per million input tokens and $25 per million output tokens", counted as half coverage, not full); (3) will you train on my data / how long is it retained → /legal/privacy 200 r=0 ✓, and /news/enterprise-frontier-safeguards body text "Anthropic has never trained on enterprise data without explicit permission" ✓; (4) how does it perform on benchmarks → the Benchmarks sections of /claude/opus and /claude/mythos ✓; (5) what is the safety framework → /responsible-scaling-policy 200 r=0 ✓; (6) who runs the company → /company 200 r=0 and /company/leadership (in the sitemap) ✓; (7) how do I build an agent with Claude → /engineering/building-effective-agents 200 r=0 ✓; (8) which countries are supported → /supported-countries 200 r=0 ✓; (9) compliance / trust center → the footer link points to https://trust.anthropic.com/ (a subdomain, not www; /trust-center and /security both 404 on this domain) ✓ counted; (10) how do I get an API key and get started → /api 200 r=1, lands on https://claude.com/platform/api, and the footer's Developer docs points to https://platform.claude.com/docs ✗. Coverage within this domain: 8/10.

**⊘ `p4.cn-engines`** — not applicable, leaves the denominator

Leaves the denominator entirely. The rubric states that this check applies when a site addresses the Chinese market and leaves the denominator when it does not; testing found no trace of Chinese-market presence.

## Bonus — +0 (outside the denominator)

**✗ `b.llms-full` 0/2** — llms-full.txt

*Why this tier:* Bonus not earned: the file does not exist and there is no discoverable entry point.

GET /llms-full.txt → 404 (a 59749-byte HTML error page). The whole of robots.txt is 71 bytes and declares nothing beyond Sitemap; /llms.txt itself 404s, so there is no way to discover an aggregated file at a non-root path from it.

**✗ `b.ai-txt` 0/2** — ai.txt

*Why this tier:* Bonus not earned: both common paths return 404.

GET /ai.txt → 404 (59735 bytes); GET /.well-known/ai.txt → 404 (59763 bytes).

**✗ `b.geo-link` 0/1** — GEO link tags

*Why this tier:* Bonus not earned: <head> carries no link rel aimed at AI retrieval.

De-duplicated set of link rel values in <head> across the 8 pages: home page [apple-touch-icon, canonical, preconnect, shortcut icon, stylesheet]; the other 7 pages [apple-touch-icon, canonical, icon, mask-icon, preload, shortcut icon, stylesheet]. No AI-retrieval rel such as llms, ai-policy, or alternate type=text/markdown.

**✗ `b.speakable` 0/1** — speakable markup

*Why this tier:* Bonus not earned: no speakable markup, and 6/8 pages have no JSON-LD container at all.

grep -il "speakable" across the 8 sampled pages → 0 files hit; 6 of those pages have 0 ld+json blocks and the other 2 contain only a FAQPage.

## Citation performance — not scored

AI citation performance was not measured this round and is not scored. The rubric lists it as an outcome metric with no maximum, reported separately: it is produced by site readiness plus time, and asking the same question of the same engine several times gives different answers, so it is not reproducible — folding a non-reproducible observation into a 100-point scale damages both the client and the credibility of the method. This audit's toolchain performs only re-checkable HTTP-layer and HTML-layer evidence gathering (status codes, byte counts, MD5, matched source sentences); it ran no live citation tests with real industry questions against ChatGPT, Perplexity, Google AI Overviews or others. This report therefore offers no conclusion on how often Anthropic is cited in AI search, and readers should not infer citation performance from the score of 70. If that metric is needed, it should be a separate round of testing: 10 fixed real industry questions, a fixed engine and time window, 3 repetitions per question, recording the cited URLs and citation positions, reported as a standalone appendix.

## Auditor's caveats

- [The most contested call in this audit; it alone decides whether the total is capped at 40] I gave g.robots the full 5. The whole of Anthropic's robots.txt is 71 bytes: `User-Agent: *` + `Allow: /` + one Sitemap line, with no named retrieval user-agents such as GPTBot, ClaudeBot or PerplexityBot. The rubric's tier 5 reads "mainstream retrieval user-agents explicitly allowed", which can literally be read as requiring names. My reason for 5: tier 3's criterion reads "no explicit Disallow, but no explicit Allow either", and this file does contain an Allow directive with no Disallow anywhere, so under RFC 9309 all ten retrieval user-agents fall into the `*` group and receive an explicit allow — tier 3's description does not match the facts, so tier 3 cannot be used. The objection is reasonable: if an auditor insists that only naming counts as explicit, g.robots is 3 points, the gate check is not at full marks, normalised is capped straight from 70 to 40, and the band drops from Solid to Early. This is the single largest point swing in the report, and reviewers should look here first. My view is that the rubric itself should settle in v1.2 whether a wildcard Allow: / is equivalent to a named allow, rather than leaving it to the auditor.
- [Domain boundary — affects p1.organization and p3.sameas, 9 points between them] Anthropic's product surface has moved to claude.com: /product/claude-code 301 → claude.com/product/claude-code, /pricing 301 → claude.com/pricing, /api 301 → claude.com/platform/api, /learn 301 → academy.claude.com, /engineering/claude-code-best-practices 301 → code.claude.com/docs. The complete Organization + Brand + SoftwareApplication + BreadcrumbList + sameAs graph exists only in the post-301 claude.com response, yet its @id reads https://www.anthropic.com/#organization. Taking "the object of the audit is www.anthropic.com", I scored p1.organization=0 and p3.sameas=0. An equally defensible reading is that crawling rules require following redirects, and what you get after following them is exactly this schema, so it should count — on that reading p1.organization could reach 6 and p3.sameas 3, and the total would reach 78 (still Solid, but close to the 83 line for Leading). I chose the strict reading because the boundary of what the site owner can fix has to be clear: the anthropic.com home page emits no structured data of its own, and that is a real gap fixable on this domain. But I accept that, in the actual experience of AI retrieval, users and crawlers do end up with that Organization graph. In client delivery this item should be written explicitly as a cross-domain asset ownership problem, not simply as "you have no schema".
- [The 7 points on p2.question-intent are the second most lenient call in this audit] I judged 7/8 on the test "can the page title or its subheads be matched by a natural question", which puts it at tier 7. Looking only at <title>/H1, and treating first-person news headlines ("Improving our alignment and security efforts", "Developing Enterprise Frontier Safeguards with our customers") as institutional-announcement voice rather than something a user would ask, leaves only 3/8 hits (building-effective-agents, how-we-contain-claude, investigating-incidents), which is tier 3 and drops this check from 7 to 3. The H1s of the two model pages are bare brand labels ("Claude Opus 4.8", "Claude Claude Mythos 5" — the latter also carries a visible "Claude Claude" duplicate-rendering bug), and I brought them back in on the strength of the literal-question H3s inside those pages; that step extends "heading" to "subheading", beyond the literal criterion. A reviewer who does not accept the extension should score this check 3 or 5.
- [The 3 points on p2.freshness are, by contrast, the strictest call in this audit, and they expose a problem in the rubric's tiers themselves] All 8 sampled pages carry a visible date (5 have a page-level date immediately after the H1, 3 have card-level dates), which on "most pages do" should be enough for tier 6; but tier 6 is a conjunction — it also requires "dateModified agrees with the visible date", and dateModified and article:modified_time get 0 hits in the JSON-LD and meta of all 8 pages. The only modification signal is sitemap lastmod, and it contradicts the page date on several pages (the building-effective-agents page says "Published Dec 19, 2024" and its body admits the content is out of date, while sitemap lastmod is 2026-08-10; the improving-alignment page says Aug 31 against lastmod Sep 07). With the conjunction unmet the only fallback is tier 3, "some pages carry a visible date" — but tier 3's word "some" plainly understates 8/8 visible-date coverage. In other words, whether this check gets 3 or 6, the wording does not fit the facts. I applied the rule "take the highest tier the evidence actually satisfies" and chose 3, but this is the cell I am least satisfied with in this report; I recommend that v1.2 split tier 6 into two levels, "most pages carry a visible date" and "and a consistent dateModified exists".
- [Two further places where the tiers and the evidence are misaligned, in opposite directions — I went strict on one and lenient on the other, and set both out here] (a) p3.video I gave 2: Anthropic's YouTube channel has updated steadily over the past six months (at least 10 entries from 2026-04 to 2026-09), which is nothing like tier 2's "content is sparse", but tier 3 requires "VideoObject on site" and the 8 pages return 0 hits, so it can only fall back to 2 — here I took the strict reading, and the actual content output is understated. (b) p4.answer-shape I gave the full 4: the subheading hierarchy is complete, paragraph medians of 24–67 words sit squarely in the quotable range, and 6/8 pages carry lists — but tier 4 also requires tables, and the 8 pages have 1 <table> in total; the model pages' benchmark figures are presented as charts/SVG, which is in fact worse than a table for AI extraction. A strict reading of the conjunction should have cost points and I did not deduct them, on the grounds that tier 2's "paragraphs run long" directly contradicts the measurements and dropping to 2 would distort more. If this cell is taken strictly as a conjunction, the check falls from 4 to 2, the total from 70 to 68, and the band is unchanged. Two lesser doubts recorded alongside: on p2.named-author I gave 3, but real-name bylines appear on only 2/8 pages and the three news pages have none at all — the tier 3 criterion sets no page-count threshold so I scored it at its word, though effective coverage is low; on p3.listings I counted 7 platforms, but Crunchbase and G2 both returned 403 (anti-scraping) and I scored those as "cannot be confirmed", neither for nor against — if they are in fact listed, that only makes tier 4 firmer and does not change the score.

