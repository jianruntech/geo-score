# How each engine selects sources

What each answer engine's vendor documents about where its sources come from. This file describes
**what the engines do** — it is not a list of tactics. Remediation is out of scope for
this repository (see [Scope](../README.md#scope--what-this-does-not-do)).

Every claim about an engine cites the vendor's own documentation, re-read on the date given under
[Sources](#sources). Where a vendor documents nothing, this file says *no data* rather than
guessing. This repository holds no measurements of which sources the engines cite — the
[benchmark](../benchmark/README.md) scores sites, not answers — so nothing here is offered as our
observation. Engines change without notice.

## Common to all of them

Answer engines that search do not return a ranked list. They retrieve pages, generate an
answer, and link the pages that support it; Google describes this as retrieval-augmented
generation, or grounding, from its Search index ([GA]). Three consequences the rubric is built
on. The first is a hypothesis; the second and third rest on the sources named:

1. **The unit of selection may be a passage rather than a page or a domain.** *Hypothesis, not
   measured here.* The rubric's `p2.answer-passages` check rests on it, and its
   [evidence entry](../rubric/evidence-v1.1.md) calls the support thin: two preprints, and
   Google's statement that content need not be chunked for its AI features.
2. **A page need not rank for the user's own words to be retrieved.** Google says AI Overviews
   and AI Mode may issue several related searches for one question (query fan-out) ([GA]). How
   closely classic rank and citation go together: no data here.
3. **Content a crawler does not receive cannot be retrieved.** A retrieval crawler that honours
   robots.txt and is disallowed there, or one a firewall refuses, gets nothing. Not every fetcher
   honours it: OpenAI and Perplexity say their user-triggered fetchers (`ChatGPT-User`,
   `Perplexity-User`) may not follow robots.txt ([O1], [X1]), while Anthropic says its bots honour
   it ([A1]). Google documents that Googlebot renders JavaScript before it indexes a page ([GJ]);
   for the other crawlers the rubric relies on a traffic study by Vercel and MERJ (a third-party
   report, not verified here; see `g.ssr` in the [evidence](../rubric/evidence-v1.1.md)).

## Google AI Overviews and AI Mode

- Built on Google Search's core ranking and quality systems: pages are retrieved from the Search
  index to ground the answer, and one question may fan out into several searches ([GA]).
- To be eligible for these features, a page must be indexed and eligible to be shown in Search with
  a snippet, and the site must be included under Search generative AI features in Search Console
  ([GA]); include is the default ([GC]). Google's AI features page, which says there are no
  additional technical requirements ([G5]), was last updated on 2025-12-10, before the control
  reached all sites on 2026-08-31 ([GC]).
- **What controls appearing here**, as Google documents it:
  - **Googlebot's robots.txt rules** decide what is crawled for Search, AI features included ([G5]).
  - **`nosnippet`, `data-nosnippet`, `max-snippet`, `noindex`** limit what Search shows from a
    page, AI features included ([G5]).
  - **Search Console, Settings > Search generative AI.** Set to exclude, a site's links and content
    leave AI Overviews, AI Mode and Discover's generative AI features and are no longer used as input
    to generate their answers. The default is include, and Google says the setting is not a ranking
    or inclusion signal for the rest of Search ([GC]).
- **`Google-Extended` does not control grounding here.** Google says it does not affect inclusion or
  ranking in Google Search ([GX]); Search Console's help names it only as the control for training
  the models behind these features ([GC]). The grounding it does govern is Gemini's (below).
- Structured data: Google says it is not required for its generative AI features and that no special
  schema.org markup is needed ([GA]). Whether `Organization` or `Article` markup changes which pages
  are selected: no data.

## ChatGPT

- Two agents with separate settings ([O1]). `OAI-SearchBot` surfaces sites in ChatGPT search; a site
  that opts it out is not shown in ChatGPT search answers, though it can still appear as a
  navigational link. `ChatGPT-User` visits a page when a user's question needs it, is not used to
  decide what appears in search, and robots.txt rules may not apply to it.
- How ChatGPT orders or selects sources: OpenAI's crawler page does not say. No data. The rubric
  scores freshness (`p2.freshness`) on a preprint and on Google's and Bing's documentation, not on
  observations of ChatGPT ([evidence](../rubric/evidence-v1.1.md)).

## Perplexity

- `PerplexityBot` surfaces and links websites in Perplexity's search results and is not used to
  crawl content for AI foundation models; `Perplexity-User` may visit a page when a user asks a
  question and link it in the answer, and generally ignores robots.txt rules ([X1]).
- How Perplexity selects or ranks sources: not in its crawler documentation. No data.

## Gemini

- `Google-Extended` governs whether content Google crawls may be used for grounding in Gemini Apps
  and in Grounding with Google Search on Vertex AI, which Google describes as providing content from
  the Google Search index to the model at prompt time, as well as for training future Gemini models
  ([GX]). A site that disallows it is left out of that grounding.
- How Gemini selects among grounding sources, and what role Google's Knowledge Graph plays: not in
  the pages checked. No data.

## Microsoft Copilot

- Bing's webmaster guidelines cover Bing search, Copilot and grounding API results, and say Bing and
  Copilot search experiences rely on the same crawling, indexing and ranking foundation as
  traditional search, and that GEO does not guarantee grounding or citations ([B1]).
- v1.1 does **not** score Bing verification: it is visible only to the site owner, so it left the
  100-point base along with the other unobservable checks. Report it as "measurable once access is
  granted" rather than scoring a zero you cannot see.

## Claude

- `Claude-SearchBot` indexes content to improve search results, and disabling it may reduce a
  site's visibility in them; `Claude-User` retrieves pages when a user asks. Anthropic says its bots
  honour robots.txt ([A1]).
- Whether `llms.txt` affects which sources Claude cites: Anthropic's crawler article does not mention
  it. No data. The rubric scores `llms.txt` as a convention, not as a demonstrated effect
  ([evidence](../rubric/evidence-v1.1.md)).

## Non-English engines

If the audience is not English-speaking, the engines above may be largely irrelevant.
Regional engines have their own indexes and their own crawler behaviour. v1.1 scores this
in one place only — `p4.cn-engines`, which applies when a site addresses the Chinese
market and leaves the denominator when it does not. Other regional markets are not
scored, because we have not done the observation work to define tiers we could defend.

**We do not currently document regional engines in detail.** This is a known gap and a
good contribution — see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Sources

Each page was re-read on 2026-10-04. The date in parentheses is the page's own, where it gives one.

- **[G5]** Google, [AI features and your website](https://developers.google.com/search/docs/appearance/ai-features) (last updated 2025-12-10).
- **[GA]** Google, [Optimizing your website for generative AI features on Google Search](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) (last updated 2026-07-10).
- **[GC]** Google Search Console Help, [Search generative AI control](https://support.google.com/webmasters/answer/16908024) (no update date; it says the control reached all websites worldwide on 2026-08-31).
- **[GX]** Google, [Google's common crawlers](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers), Google-Extended section (last updated 2026-07-14).
- **[O1]** OpenAI, [Overview of OpenAI Crawlers](https://developers.openai.com/api/docs/bots) (undated).
- **[X1]** Perplexity, [Perplexity Crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers) (undated).
- **[B1]** Microsoft, [Bing Webmaster Guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a) (undated; the page loads its text from `https://www.bing.com/webmasters/api/help/htmlcontent?ArticleId=30fba23a`, which is what was read).
- **[GJ]** Google, [Understand the JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics) (last updated 2026-03-04).
- **[A1]** Anthropic, [Does Anthropic crawl data from the web, and how can site owners block the crawler?](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) (2026-04-07).

[G5]: https://developers.google.com/search/docs/appearance/ai-features
[GA]: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
[GC]: https://support.google.com/webmasters/answer/16908024
[GX]: https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
[O1]: https://developers.openai.com/api/docs/bots
[X1]: https://docs.perplexity.ai/docs/resources/perplexity-crawlers
[B1]: https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a
[GJ]: https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
[A1]: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
