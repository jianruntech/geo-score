# svelte.dev — AIV audit (rubric v1.1)

> **Readiness 76 / 98 · normalised 78% · Solid** · audited 2026-09-08

Scored against [rubric v1.1](../../../rubric/v1.1.md) using only publicly observable data.
Machine-readable: [`svelte.dev.json`](svelte.dev.json), conforming to
[`schema/report.v2.json`](../../../schema/report.v2.json).

> **The gate rule changed after this audit ran.** These five audits were scored while a
> gate check short of full marks capped the whole score at 40. Several of the caveats below
> are the auditor saying, in real time, that the cap was producing the wrong answer — and
> they were right. The rule now caps only when a gate scores **zero**. The scores shown here
> are recomputed under the corrected rule; the caveats are left exactly as written, because
> they are the record of how the error was found.
> [What changed and why](../../../rubric/calibration-v1.1.md#a-design-error-the-re-audit-caught)

## Sampled URLs (8)

- https://svelte.dev/
- https://svelte.dev/tutorial/svelte/welcome-to-svelte
- https://svelte.dev/playground/hello-world?show=input
- https://svelte.dev/docs/svelte/what-are-runes
- https://svelte.dev/docs/kit/introduction
- https://svelte.dev/blog/whats-new-in-svelte-september-2026
- https://svelte.dev/blog/sveltekit-3-release-candidate
- https://svelte.dev/blog/whats-new-in-svelte-august-2026

## Reachable — 15 / 15

**✓ `g.robots` 5/5** — Retrieval crawlers allowed in robots.txt

*Why this tier:* Not tier 0: the Disallow line in robots.txt has an empty value, which under the robots specification means everything is allowed, not that anything is forbidden. Scored 5 rather than 3 on rubric rule 6, “Substance over format” — the file is an explicit, universal, machine-readable permission directive, not the tier-3 case of “no explicit Disallow, but no explicit Allow either”; and all 10 retrieval user-agents were measured receiving the same body as a browser, byte for byte. If tier 5 strictly requires naming each user-agent before it counts as explicitly allowed, this check is a 3 and the whole site is gate-capped to 40. This is the most contested call in the audit; see notes.

GET https://svelte.dev/robots.txt → 200, 24 bytes, two lines in full: “User-agent: *” and “Disallow:” (empty Disallow value). The file carries no Sitemap directive, no named user-agent section, and no Allow line.

**✓ `g.reachable` 5/5** — Reachable to retrieval user-agents

*Why this tier:* Tier 5 requires “all 10 retrieval user-agents return 200 with matching content” — 10/10 returned 200, with MD5 and byte count identical to the browser user-agent. None was blocked and none returned differing content, so it does not fall to tier 3.

3 targets × 10 retrieval user-agents (GPTBot / OAI-SearchBot / ChatGPT-User / ClaudeBot / Claude-SearchBot / PerplexityBot / Perplexity-User / Google-Extended / Applebot / Bingbot), all 200 under curl -L: homepage 89798 B md5=0ca70a3db0ae2c4a7295abcb9c9bf4dc (identical across 30/30); /docs/svelte/what-are-runes 80914 B md5=29169206ed1b3c4517575bea26274879; /blog/sveltekit-3-release-candidate 67350 B md5=9a612d8b953b29b718cc5ca91b09d408. The browser user-agent (Chrome 131) fetched the same 3 pages and returned exactly the same md5 values and byte counts. Two consecutive browser-user-agent fetches of the homepage returned the same md5, which shows the responses are deterministic and the md5 comparison is valid.

**✓ `g.ssr` 5/5** — Main content server-rendered

*Why this tier:* Tier 5 requires the main content to be “present in the HTML response on every sampled page”. On 7 of 8 pages the full prose body is in the HTML with no JavaScript executed; the eighth, /playground, is a REPL application with no prose body of its own — its rendered <main> holds only 1613 characters of example-index navigation, though the example source string name = $state('world') does appear inside the HTML response body (in the SvelteKit payload script). Passed on the literal tier-5 wording “in the HTML response”; read instead as “visible in the rendered DOM”, playground fails, this check drops to tier 3, and the gate cap of 40 triggers. See notes.

curl -L, no JavaScript executed; body word counts after stripping tags, page by page: homepage 307, tutorial 658, playground 225, what-are-runes 378, kit/introduction 540, September blog post 1166, SvelteKit 3 RC 1200, August blog post 1540. Sentences found in the HTML response: homepage “Svelte is a UI framework that uses a compiler to let you write breathtakingly concise components…”; kit/introduction “SvelteKit is a framework for rapidly developing robust, performant web applications using Svelte.”; on playground the rendered <main> text of 1613 characters is entirely the example directory, and grep 'name = $state(' matches once, inside the <script> payload.

## Understandable — 5 / 22

**✗ `p1.sitemap` 0/4** — Sitemap discoverable and fresh

*Why this tier:* Tier 0, “cannot be discovered, or does not return 200”: robots.txt carries no Sitemap directive, and the conventional path plus 4 common variants all return 404, so there is no 200 response that could earn tier 2.

https://svelte.dev/sitemap.xml → 404 (39549 B, SPA 404 page, <title>404</title>); /sitemap-index.xml → 404 39549 B; /sitemap_index.xml → 404 39549 B; /sitemap.txt → 404 39549 B; /sitemap/sitemap.xml → 404 39584 B. curl -L https://svelte.dev/robots.txt | grep -i sitemap → no output.

**✓ `p1.llms-txt` 5/5** — llms.txt present and structured

*Why this tier:* Tier 5 requires a site definition passage plus “2+ topic sections that contain links”: the site definition passage is the blockquote at the top, and there are 3 topic sections (Documentation Sets / Individual Package Documentation / Notes), the first two carrying 3–4 linked entries each — above the threshold of 2, so it does not stop at tier 4.

GET https://svelte.dev/llms.txt → 200, 1676 B. Definition passage, verbatim: “> Svelte is a UI framework that uses a compiler to let you write breathtakingly concise components that do minimal work in the browser, using languages you already know — HTML, CSS and JavaScript.” Sections: “## Documentation Sets” (3 links: llms-medium.txt / llms-small.txt / llms-full.txt), “## Individual Package Documentation” (4 links: /docs/svelte/llms.txt, /docs/kit/llms.txt, /docs/cli/llms.txt, /docs/ai/llms.txt), and “## Notes”.

**✗ `p1.organization` 0/6** — Organization + WebSite sitewide

*Why this tier:* Tier 0, “neither present”: across 8/8 sampled pages there is no JSON-LD, no schema.org reference and no microdata. Neither Organization nor WebSite exists, so even tier 3, “one of the two present”, does not hold.

Counted page by page over the HTML of the 8 sampled pages: grep -c 'application/ld+json' = 0 (8/8); grep -c 'schema.org' = 0 (8/8); grep -c 'itemtype' = 0 (8/8); grep -c 'itemprop' = 0 (8/8). Listing every <meta>/<link> in the head of s7 gives only charset, viewport, theme-color, manifest, favicon, twitter:site=@sveltejs, twitter:creator=@sveltejs and font/module preloads — no structured data of any kind.

**✗ `p1.breadcrumb` 0/3** — BreadcrumbList on nested pages

*Why this tier:* Tier 0, “absent”: the site has a clear hierarchy (/docs/svelte/*, /docs/kit/*, /blog/*, and pages render a Docs › Svelte Runes › What are runes? style path), so this check stays in the denominator; but there is not one instance of BreadcrumbList structured data, so it does not even reach tier 2, “present on some nested pages”.

grep -c 'application/ld+json' = 0 on 8/8 pages, so BreadcrumbList counts 0 instances. Evidence that the hierarchy exists: the rendered text of /docs/svelte/what-are-runes contains the breadcrumb sequence “Svelte Runes / What are runes?”, and /docs/kit/introduction contains “SvelteKit Getting started / Introduction”.

**✗ `p1.page-type` 0/4** — Page-type schema where applicable

*Why this tier:* Does not leave the denominator: the site has clear FAQ page types (two Frequently asked questions pages) and a HowTo-shaped tutorial, both applicable page types the rubric names; but tier 0, “absent” — there is not one page-type schema anywhere.

https://svelte.dev/docs/svelte/faq → 200, 107657 B, H1 “Frequently asked questions”, 14 H2 questions (e.g. “Does Svelte scale?”, “How do I test Svelte apps?”); https://svelte.dev/docs/kit/faq → 200, 442668 B, H1 “Frequently asked questions”, 9 H2 questions. On both pages grep -c 'application/ld+json' = 0 and grep -c 'schema.org' = 0 — no FAQPage, no HowTo.

## Content Citability — 32 / 35

**✓ `p2.answer-passages` 9/9** — Self-contained answer passages

*Why this tier:* Tier 9, “on most pages”: 7 of 8 pages carry a self-contained answer passage of 25–120 words near the top of the body (this site is in English, so the rubric's English measure applies). The only reason it is not 8/8 is that the playground page has no prose paragraph at all (<p> count 0 on that page), but 7/8 already meets “most”, so it does not fall to tier 7.

Word count and source sentence of the first paragraph of ≥15 words near the top of the body (English 25–120 word measure): homepage 40 words “Svelte is a UI framework that uses a compiler to let you write breathtakingly concise components that do minimal work in the browser, using languages you already know — HTML, CSS and JavaScript. It's a love letter to web development.”; tutorial 29 words; what-are-runes 36 words “Runes are symbols that you use in .svelte and .svelte.js / .svelte.ts files to control the Svelte compiler…”; kit/introduction 33 words “SvelteKit is a framework for rapidly developing robust, performant web applications using Svelte…”; September blog post 27 words; SvelteKit 3 RC 48 words “SvelteKit 3 is now in the Release Candidate phase…”; August blog post 63 words. The playground page has a <p> count of 0 and fails. Passes 7/8.

**✓ `p2.question-intent` 7/7** — Headings match how people ask

*Why this tier:* Tier 7, “most do”: on 6 of 8 pages the H1/H2 headings are questions, task phrasings or explanatory phrasings. No lower tier, because rubric v1.1 explicitly counts explanatory phrasings (the How X works form) and excludes only bare keyword strings and brand labels — and the two pages that fail here are exactly those two cases: the homepage is a brand name plus a tagline, and the playground page has an H1–H3 count of 0.

Headings and subheadings page by page (extracted from the HTML with JavaScript stripped): homepage h1 “Svelte” / h1 “web development for the rest of us” / h2 “used by companies you've heard of” → brand label plus tagline, does not count; playground has 0 h1–h3 in total, does not count; tutorial h2 “What is Svelte?”, “How to use this tutorial” → counts; what-are-runes h1 “What are runes?” → counts; kit/introduction h2 “What is SvelteKit?”, “What is Svelte?”, “SvelteKit vs Svelte” → counts; September blog post h1 “What's new in Svelte: September 2026” plus h2 “What's new in SvelteKit 3's RC” → counts; SvelteKit 3 RC h2 “What's changed?” plus h3 “Error handling is way better”, “Configuration now lives in vite.config.ts” → counts; August blog post is the same shape → counts. Passes 6/8.

**◐ `p2.freshness` 3/6** — Freshness signal present

*Why this tier:* Tier 3, “some pages carry a visible date or datePublished”: only 3 of 8 pages carry a date, short of the “most pages do” that tier 6 requires. Tier 6 also requires dateModified to agree with the visible date, and with zero structured data across the site that half of the condition cannot be met either.

grep '<time' results: September blog post <time datetime="2026-09-01">Sep 1 2026</time>; SvelteKit 3 RC <time datetime="2026-08-13">Aug 13 2026</time>; August blog post <time datetime="2026-08-01">Aug 1 2026</time>. On the other 5 pages (homepage, tutorial, playground, what-are-runes, kit/introduction) grep '<time' matches nothing, grep -c 'datePublished' = 0 and grep -ci 'last updated' = 0. JSON-LD = 0 on 8/8 pages, so there is no dateModified anywhere. (The response header last-modified: Thu, 03 Sep 2026 00:32:18 GMT is present, but the rubric asks for a date visible on the page or in structured data; a response header does not count.) Passes 3/8.

**✓ `p2.sourced-stats` 7/7** — Statistics carry a source

*Why this tier:* Tier 7, “most are attributed and the source is clickable and checkable”: of the 4 sampled pages that carry substantive figures or claims, 3 (the three blog posts) attach a clickable PR or CHANGELOG link to every claim, and the homepage's third-party ranking claim links to an anchor in the annual Stack Overflow survey. It does not stop at tier 5 because the links not only exist — I fetched each one and confirmed 200.

Homepage claim, verbatim: “But don't take our word for it. Developers consistently rank Svelte as the framework they're most excited about using.”, immediately adjacent to the anchor href="https://survey.stackoverflow.co/2024/technology#2-web-frameworks-and-technologies", which measured 200 / 3189185 B with 'svelte' appearing 780 times on the page. The September blog post body carries 63 outbound anchors, of the form <a href="https://github.com/sveltejs/svelte/pull/18728">, <a href="https://github.com/sveltejs/kit/pull/16684">, <a href="https://github.com/sveltejs/svelte/blob/main/packages/svelte/CHANGELOG.md">. Counter-examples (unattributed): below the homepage's “used by companies you've heard of” is a bare logo wall with no source; the FAQ answer to “Does Svelte scale?” is “There will be a blog post about this eventually, but in the meantime, check out this issue.” — a deferral, not an attribution. Pages carrying claims pass 3/4.

**✓ `p2.named-author` 6/6** — Named, verifiable authorship

*Why this tier:* Tier 6, “the name links to a verifiable identity page”: of the 3 sampled pages that carry a byline, 2 are bylined to a named individual whose name hyperlinks to their own homepage, and that homepage measured 200 with the person's own name as its title. This is the most contested tier in the whole audit — judged literally page by page across the 8 sampled pages, 5 pages with no byline plus 1 bylined to an organisation put 6/8 at tier 0 and this check should score 0. I scored 6 on the reading that the check measures whether bylined content is traceable to a person; the reasoning and the counter-argument are both written up in notes.

In the rendered HTML of the September and August blog posts: <p class="byline"><a href="https://dreamindani.com">Dani Sandoval</a> <time datetime="2026-09-01">Sep 1 2026</time></p>; https://dreamindani.com measured 200 / 12685 B / <title>About Me | Dani Sandoval</title>. The SvelteKit 3 RC page byline is <a href="https://svelte.dev/">The Svelte team</a>, an organisation name (tier 0). The homepage, tutorial, playground and both docs pages have no byline element. Scanning the blog index page (143695 B) for the byline preceding each of ~110 <time> elements: the large majority are named individuals (Dani Sandoval, Rich Harris, Ben McCann, Geoff Rich, Simon Holthausen, Elliott Johnson, Puru Vijay, Orta Therox), a minority are The Svelte team. Sampled pages carrying a byline pass 2/3.

## Brand Credibility — 14 / 18

**✓ `p3.listings` 4/4** — Third-party listings

*Why this tier:* Tier 4, “5 or more”: curl verified 6 third-party listing sources returning 200, above the threshold of 5, so it does not stop at tier 3.

Listing pages measured at 200: https://github.com/sveltejs/svelte (333831 B, <title>GitHub - sveltejs/svelte: web development for the rest of us</title>); https://libraries.io/npm/svelte (35089 B, <title>svelte 5.57.0 on npm - Libraries.io…</title>); https://snyk.io/advisor/npm-package/svelte (476925 B, <title>svelte | Snyk</title>); https://data.jsdelivr.com/v1/packages/npm/svelte (325693 B, JSON containing "latest": "5.57.0"); https://en.wikipedia.org/wiki/Svelte (249640 B); https://www.wikidata.org/w/api.php, which returned Q16863097. Two further sources could not be resolved to a status code because of anti-bot measures on their side: https://www.npmjs.com/package/svelte → 403 and https://stackoverflow.com/questions/tagged/svelte → 403; neither is counted.

**✓ `p3.mentions` 4/4** — Independent mentions

*Why this tier:* Tier 4, “sustained mentions across channels”: three mutually independent channels verified, each updated year on year (two annual developer surveys, an encyclopedia entry, and a documentary produced by a third party) — more than the one-off evidence tier 3 asks for, “independent coverage or reviews exist”.

https://survey.stackoverflow.co/2024/technology → 200 / 3189185 B, 'svelte' matched 780 times on the page; https://2024.stateofjs.com/en-US/libraries/front-end-frameworks/ → 200 / 328616 B, 'svelte' matched 3 times; https://en.wikipedia.org/wiki/Svelte → 200 / 249640 B, <title>Svelte - Wikipedia</title>, 'svelte' matched 518 times; homepage anchor <a href="https://www.offerzen.com/community/svelte-origins-documentary">Watch the full Svelte Origins documentary</a> (produced by the third party OfferZen).

**✓ `p3.knowledge-graph` 4/4** — Knowledge-graph entity

*Why this tier:* This check has only tiers 0 and 4. Both the Wikipedia entry and the Wikidata entity were measured to exist and to be this subject, so it lands directly on 4.

https://en.wikipedia.org/wiki/Svelte → 200 / 249640 B / <title>Svelte - Wikipedia</title>. The Wikidata API (action=wbgetentities&sites=enwiki&titles=Svelte) returned {"entities":{"Q16863097":{"id":"Q16863097","labels":{"en":{"value":"Svelte"}},"descriptions":{"en":{"value":"JavaScript framework"}}}},"success":1}. (Note: Q56092956, which I first guessed from memory, fetched an unrelated entry, Trade Wars: Canada's Reaction to the Smoot-Hawley Tariff; it was discarded and the entity confirmed instead by looking it up from enwiki.)

**✗ `p3.sameas` 0/3** — sameAs complete and resolving

*Why this tier:* Tier 0, “not declared”: sameAs rides on JSON-LD, and there is no JSON-LD anywhere on the site, so there is nothing to declare it in. The rubric states that not declared scores 0 and does not leave the denominator, so this check stays in the denominator.

On 8/8 sampled pages grep -c 'application/ld+json' = 0 and grep -c 'schema.org' = 0; sameAs appears 0 times. The site's own accounts do exist (<meta name="twitter:site" content="@sveltejs"> and <meta name="twitter:creator" content="@sveltejs"> in the head, GitHub and Discord links in the body), but none of them is bound to an entity as sameAs.

**◐ `p3.video` 2/3** — Video and multimodal presence

*Why this tier:* Tier 2, “a channel exists but content is sparse”: an official or sister-organisation video channel does exist and the homepage links to the documentary, but tier 3 requires VideoObject on site, and with zero structured data across the site that half of the condition is impossible to satisfy. The check is therefore held at tier 2 for reasons unrelated to how much video is produced.

https://www.youtube.com/@SvelteSociety → 200 / 2304716 B; homepage anchor <a href="https://www.offerzen.com/community/svelte-origins-documentary">Watch the full Svelte Origins documentary</a>; the blog index carries “Advent of Svelte is back — We've pivoted to video” (2025-12-01) and “Svelte Summit videos”. On 8/8 sampled pages grep -c 'VideoObject' = 0 (total JSON-LD count is 0).

## Answer Fit — 8 / 8

**✓ `p4.answer-shape` 4/4** — Content shaped for extraction

*Why this tier:* Scored 4 rather than 2 because tier 2's criterion, “subheadings present but paragraphs run long”, is contradicted by the measurements: across the 8 pages <p> averages 12–41 words with a maximum of 125. Tier 4 literally requires subheadings, lists and tables, and the site has no tables at all (0 even on the API reference page) — so this tier is scored generously, and it is the third contested point in this audit; see notes.

Counted page by page inside the rendered <main>: homepage h=4 lists=0 li=0 tables=0 paras=6 avg=23w max=40w; tutorial h=2 lists=36 li=133 tables=0 paras=10 avg=28w max=62w; playground h=0 lists=22 li=88 tables=0 paras=0; what-are-runes h=11 lists=12 li=99 tables=0 paras=9 avg=12w max=36w; kit/introduction h=13 lists=9 li=84 tables=0 paras=9 avg=39w max=125w; September blog post h=8 lists=9 li=40 tables=0 paras=16 avg=13w max=43w; SvelteKit 3 RC h=12 lists=0 li=0 tables=0 paras=27 avg=41w max=114w; August blog post h=8 lists=10 li=61 tables=0 paras=17 avg=17w max=63w. The API reference page https://svelte.dev/docs/svelte/svelte was also fetched → 200 / 790769 B, grep -c '<table' = 0, confirming that the absence of tables is a sitewide style and not a sampling artefact.

**✓ `p4.question-coverage` 4/4** — Coverage of the questions people ask

*Why this tier:* Tier 4, “9–10 covered”: 9 of the 10 questions I drew up are answered directly by a dedicated page (all curl-verified at 200 with the heading matched). Landing on 4 rather than 3 depends entirely on how the question list is composed — add two more comparison or adoption questions (Svelte vs React, is anyone still using Svelte, performance comparison) and coverage drops to 7/10, which is tier 3. See notes.

Covered (all measured at 200): 1 What is Svelte? → /docs/kit/introduction 72647 B, H2 “What is Svelte?”; 2 What is the difference between Svelte and SvelteKit? → same page, H2 “SvelteKit vs Svelte”; 3 What are runes? → /docs/svelte/what-are-runes 80914 B, H1 of the same name; 4 How do I create a project? → /docs/svelte/getting-started 78446 B plus /docs/kit/creating-a-project 70407 B; 5 How does SvelteKit load data? → /docs/kit/load 1750752 B; 6 How do I deploy? → /docs/kit/adapters 84190 B; 7 How do I handle authentication? → /docs/kit/auth 69827 B; 8 How do I test? → /docs/svelte/testing 647540 B plus the FAQ H2 “How do I test Svelte apps?”; 9 How do I upgrade from Svelte 4 to 5? → /docs/svelte/v5-migration-guide 1018575 B. Not covered: 10 How does Svelte compare with React/Vue, and is it usable in production — there is no comparison page anywhere on the site, and /docs/kit/introduction offers only the aside “If you're coming from React, SvelteKit is similar to Next.”; the FAQ's “Does Svelte scale?” is answered verbatim with “There will be a blog post about this eventually, but in the meantime, check out this issue.”, which defers rather than answers. On llms-small.txt (52700 B), grep 'vs (react|vue)|compared to react|coming from react' also returns no substantive match. Coverage 9/10.

**⊘ `p4.cn-engines`** — not applicable, leaves the denominator

The rubric reads: "applies when the site addresses the Chinese market; leaves the denominator entirely when it does not." svelte.dev is an English open-source project site with no Chinese version, no mainland-China operating entity and no ICP filing obligation. The check does not apply and leaves the denominator.

## Bonus — +2 (outside the denominator)

**✓ `b.llms-full` 2/2** — llms-full.txt

*Why this tier:* Both halves of the bonus criterion — a single aggregated full-text file, discoverable from llms.txt or robots.txt — hold, so full marks. Bonus checks stay out of the denominator.

https://svelte.dev/llms-full.txt → 200, 1186907 B. Discovery path: inside llms.txt, “- [Complete documentation](https://svelte.dev/llms-full.txt): The complete Svelte and SvelteKit documentation including all examples and additional content”. Also present: llms-medium.txt, llms-small.txt (measured 200 / 52700 B) and 4 per-package llms.txt files.

**✗ `b.ai-txt` 0/2** — ai.txt

*Why this tier:* The criterion, “Declares an AI usage policy”, does not hold: the conventional path returns 404, so there is no file to score. Bonus checks stay out of the denominator; a 0 here is not a deduction.

https://svelte.dev/ai.txt → 404, returning the 39549 B SPA 404 page (<title>404</title>) — the same size and the same page as the 404 for /sitemap.xml.

**✗ `b.geo-link` 0/1** — GEO link tags

*Why this tier:* The criterion, “Declares retrieval-facing link relations in the head”, does not hold: apart from font and module preloads and icon/manifest, the head carries no link rel at all. The docs pages do show a visible “llms.txt” text link at the foot of the body, but that is an ordinary anchor inside the body, not a link relation declared in the head.

Extracting every <link rel> in the head of three pages — homepage, what-are-runes, SvelteKit 3 RC — and excluding modulepreload/preload/stylesheet/icon/manifest leaves nothing (0 entries). At the foot of the docs page body, “Edit this page on GitHub llms.txt” is an <a> anchor.

**✗ `b.speakable` 0/1** — speakable markup

*Why this tier:* The criterion, “Marks the region a voice assistant should read aloud”, does not hold: speakable rides on schema.org markup, and there is zero structured data across the site.

On 8/8 sampled pages grep -c 'speakable' = 0; on the same 8/8 pages grep -c 'application/ld+json' = 0.

## Citation performance — not scored

Not measured. The rubric defines citation performance as an outcome metric, to be measured by putting real industry questions to mainstream AI search and observing whether the site is cited, and it states explicitly that this is never folded into readiness. This audit had only curl and no usable AI search interface, and asking the same question twice is itself not reproducible, so no score is given, no estimate is made, and nothing is written as “it would probably be cited”. Producing that number would take a separate round: fix 10–15 real Svelte questions (for example, what is the difference between Svelte and React, how do I deploy SvelteKit to Vercel), run each 3 times in ChatGPT Search / Perplexity / Google AI Overviews / Claude, and tabulate separately the share of runs in which svelte.dev appears in the citation list.

## Auditor's caveats

- Whether g.robots scores 5 or 3 is the most consequential call in this audit: it decides between 78 and a gate cap at 40. The robots.txt at svelte.dev is two lines, “User-agent: *” and “Disallow:” (24 bytes). My reason for 5: an empty-value Disallow is the standard way the robots specification expresses that everything is allowed — an explicit, universal permission, not the tier-3 case of “no explicit Disallow, but no explicit Allow either”; and all 10 retrieval user-agents were measured receiving the same body as a browser, byte for byte, so the point of a gate check (nothing else matters until a crawler can get the content) is satisfied as a matter of fact. The opposing position stands up just as well: tier 5 literally reads “mainstream retrieval user-agents explicitly allowed”, and svelte.dev names no user-agent and carries no Allow line. On that reading this check scores 3, the site caps at 40, and the band drops to Early. The rubric has no written ruling at this tier on whether a wildcard empty Disallow counts as explicitly allowed. v1.2 should add one, or the same site will differ by 38 points between two auditors.
- Tier 5 on g.ssr is just as tight, and it too would trigger the cap. On 7 of the 8 sampled pages the prose body is fully visible in the HTML with no JavaScript executed; the eighth is /playground — a REPL application whose rendered <main> holds only 1613 characters of example-directory navigation. The example source name = $state('world') does appear in the HTML response body, but inside SvelteKit's payload <script>, not in the rendered DOM text. I passed it on the literal tier-5 wording, “present in the HTML response on every sampled page”, and on the further ground that playground has no prose body to render in the first place. Read as “visible once rendered”, this check drops to tier 3 and the site caps at 40. This also exposes a blank in the rubric: it says nothing about the standard to apply when an interactive application page (a REPL, a console, an editor) enters the SSR sample. My sample treats /tutorial and /playground as the “2 main product or service pages”, which is honest for svelte.dev — they are the site's two largest non-documentation surfaces — but another auditor who took /docs/svelte/overview and /docs/kit as the product pages would keep playground out of the sample, and the g.ssr dispute would disappear with it. The sampling choice is itself moving a gate check, which is not healthy.
- Scoring p2.named-author a 6 is the call I am least comfortable with. Read literally page by page as the rubric asks, 5 of the 8 sampled pages carry no byline at all and 1 is bylined to an organisation, “The Svelte team” — 6/8 at tier 0 (“no byline, or the byline is the organisation”), which makes this check a 0. My grounds for 6: the other 2 pages are bylined to a named individual, Dani Sandoval, whose name hyperlinks to dreamindani.com (measured 200, title About Me | Dani Sandoval), and a scan of ~110 historical posts on the blog index shows the large majority bylined to named individuals; documentation pages carrying no byline is normal for collective open-source maintenance, not concealment. But that amounts to quietly swapping the unit of judgement from “sampled pages” to “bylined content”, and the rubric does not authorise the swap — the other tiers here (a few / half / most) are all counted by page, and this one alone is not, which is an inconsistency in the rubric's own wording. Judged literally at 0, the total falls from 78 to 72 and the band is still Solid: the conclusion does not change, but this check's diagnostic value does.
- The 4 on p4.answer-shape is a forced call: tier 4 literally requires subheadings, lists and tables, and svelte.dev uses no tables anywhere — tables=0 on all 8 sampled pages, and 0 on the API reference page /docs/svelte/svelte (790769 B) as well. I did not score tier 2 because tier 2's criterion is “paragraphs run long”, while the measurements give paragraph averages of 12–41 words across the 8 pages with a maximum of 125; writing 2 would put a claim in the report that contradicts the evidence. The rubric offers no landing point between these two tiers, so the choice was which of the two lies less. What is actually true: the hierarchy is very dense (up to 13 headings on a single page), lists are abundant (133 li on the tutorial page) and paragraphs are short — tables are the one thing missing. This site's content shape is in fact well suited to being lifted out in whole blocks; it just does not take the table route.
- The 4 on p4.question-coverage leans heavily on the 10-question list I drew up myself, and is the least reproducible score here. My list is documentation-oriented (how do I create a project, how do I load data, how do I deploy, how do I test, how do I upgrade), and 9 of the 10 hit a dedicated page. But a large share of what real users ask an assistant about Svelte is comparison and adoption questions — is Svelte or React better, is anyone still using Svelte, how much faster is it really, what is the hiring market like — and svelte.dev answers none of them directly (the one related FAQ entry, “Does Svelte scale?”, reads “There will be a blog post about this eventually”). Add two questions of that kind to the list and coverage drops immediately to 7/10, tier 3. This score is essentially a function of the auditor's choice of questions. The rubric should give rules for constructing the industry question list (for instance, requiring N comparison questions), or the check is not comparable across auditors.
- There was one accident during evidence collection, recorded here so a reviewer knows how it was found and ruled out: the scratchpad directory for this run was shared with another agent running in parallel, which wrote anthropic.com pages under exactly the same filenames (pages/p1.html and so on) and overwrote my first round of fetches, at which point I was briefly reading the absurd observation that the svelte.dev homepage returns the Anthropic homepage. What flagged it was the byte count curl -w reported (89798) not matching the file's actual size (176945). I re-fetched into a separate directory, svelte_aiv_17343, and cross-checked with md5 against the first round's user-agent test files (homepage 0ca70a3d…, docs page 29169206…, blog page 9a612d8b… — all three md5 values identical between the two rounds), which confirms the user-agent reachability conclusion was not contaminated. Every piece of evidence in checks is taken from the re-fetched files.
- Two third-party sources could not be resolved to a status code because of anti-bot measures on their side, and by the rules I did not count them toward p3.listings: https://www.npmjs.com/package/svelte returned 403 (5723 B) and https://stackoverflow.com/questions/tagged/svelte returned 403 (5337 B). A Svelte entry almost certainly exists at both, but “almost certainly” is not evidence, so undercounting is the safer error. Counting them would not change the tier in any case (the check is already at the tier-4 ceiling of 5 or more). Separately, the Wikidata id I first guessed from memory, Q56092956, was wrong — it fetched an unrelated entry about the Smoot-Hawley tariff — and was replaced by looking the entity up from enwiki, which gave the correct Q16863097. Writing an entity id from memory is something no audit should do.
- The shape of the score is worth a reviewer's attention: nearly all of the 24 points lost (out of 98) sit in one category, machine-readable metadata — Organization+WebSite 6, page-type 4, sitemap 4, breadcrumb 3, sameAs 3, the VideoObject half of video 1, and the structured-date half of freshness 3. There is no JSON-LD and no schema.org reference anywhere on svelte.dev. This is a site with near-full marks on content and reachability and a complete blank on structured data, and the number 78, being the average of those two extremes, may hide that. The official gloss on the band name Solid is “Foundations are in place. What is left is content depth and brand assets” — the exact opposite of this site's situation, where the gap sits in the metadata layer of the foundations and content depth and brand assets are the strengths. That disconnect between the band gloss and the actual diagnosis is another of my reservations about this result.

