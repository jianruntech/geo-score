# AI crawler user-agents

The list the `g.robots` check checks `robots.txt` against. Consolidated from vendor documentation;
this is a reference, not original research. Vendors change these —
[open an issue](https://github.com/jianruntech/geo-score/issues) if one is stale.

**Last verified:** 2026-10-04 for the training crawlers, the opt-out tokens and Google's controls
(each source and its date are under [Sources](#sources)); 2026-09-28 for the retrieval table.

## The distinction that matters most

Three different kinds of token appear in `robots.txt`, and conflating them is the most
common mistake in AI-visibility advice:

| Kind | What it is | What blocking it costs |
|---|---|---|
| **Retrieval crawler** | A real crawler that fetches pages to answer user questions | **Citations.** This is what you must allow |
| **Training crawler** | Fetches pages for model training corpora | For `GPTBot` and `ClaudeBot`, the vendors document a training effect only, and run separate search crawlers ([O1], [A1]). Meta documents `Meta-ExternalAgent` for training and also for indexing content to improve its products ([MT]). For the others, no data |
| **Opt-out token** | *Not a crawler.* Sends no requests. A control that says how content another crawler fetched may be used | **Depends on the token.** `Google-Extended` also governs grounding in Gemini Apps and in Grounding with Google Search on Vertex AI, so blocking it can cost you there ([GX]). `Applebot-Extended` governs training only ([AP]) |

An opt-out token looks like a user-agent and sits in `robots.txt`, which is why it gets
mistaken for a crawler. `Disallow: Google-Extended` does not stop Googlebot from crawling you,
and Google says it does not affect inclusion or ranking in Google Search ([GX]); AI Overviews
and AI Mode have a control of their own (see
[Google's AI features](#googles-ai-features-which-control-does-what)). It does keep your content
out of the grounding Gemini Apps and Vertex AI do with Google Search, and out of training future
Gemini models ([GX]). `Disallow: Applebot-Extended` does not remove you from search results in
Spotlight, Siri or Safari ([AP]).

**This rubric scores retrieval-crawler access only.** Blocking training crawlers and opt-out
tokens is not penalised, and refusing training while letting the retrieval crawlers fetch is a
legitimate posture. Not penalised is not the same as free, and not every name below is
training-only: `Google-Extended` reaches past training into Gemini's grounding ([GX]), Meta
describes `Meta-ExternalAgent` as also indexing content to improve its products ([MT]), and for
the rows marked no data, what blocking costs is unknown. No check here measures any of it.

## Retrieval crawlers — allow these to be cited

| User-agent | Operator | Role |
|---|---|---|
| `OAI-SearchBot` | OpenAI | Builds the index behind ChatGPT search |
| `ChatGPT-User` | OpenAI | Fetches a page live when a user's prompt requires it |
| `Claude-SearchBot` | Anthropic | Indexes for Claude's search results |
| `Claude-User` | Anthropic | Fetches live when a user's prompt requires it |
| `PerplexityBot` | Perplexity | Indexes for Perplexity answers |
| `Perplexity-User` | Perplexity | User-initiated fetch |
| `Googlebot` | Google | Also the source for AI Overviews grounding |
| `Bingbot` | Microsoft | Feeds Copilot |
| `Applebot` | Apple | Feeds Siri and Spotlight, including their AI answers |
| `Amazonbot` | Amazon | Alexa and Rufus |

**All 10 are what `g.reachable` tests.** `Perplexity-User` and `ChatGPT-User` are
user-initiated rather than scheduled, but they fetch pages on a person's behalf and a
block on them is still a block, so they count. If a site's audience makes one of these
genuinely irrelevant, mark the check partially unobservable rather than failing it.

This table is the CLI's list: `RETRIEVAL_UAS` in `cli/geo_score.py` is tested against it, and
no name from the two tables below may appear there.

Amazon's crawler page now also documents `Amzn-SearchBot` (search, including Alexa) and
`Amzn-User` (fetches on a user's behalf), and says `Amazonbot`'s crawl may be used to train
Amazon's models. The table keeps `Amazonbot` as a retrieval crawler until that classification
is reviewed.

Meta's crawler page documents two agents this table does not list ([MT]): `Meta-WebIndexer`,
which crawls to improve Meta AI's search results and which, Meta says, helps Meta AI cite and link
a site's content, and `Meta-ExternalFetcher`, which fetches links at a user's request and may
bypass robots.txt. Neither is checked or probed.

**The probes are unverified.** `g.reachable` sends each vendor's documented user-agent
string from the auditor's own address, not from the vendor's published IP ranges. For
two of the ten, `Claude-SearchBot` and `Claude-User`, Anthropic documents only the product
token: their strings are built from it, in the form of `ClaudeBot`'s. A firewall that
verifies crawlers by IP range or reverse DNS may refuse these probes and still serve the
real crawler. A refusal therefore reads as "this server refused unverified crawler
user-agents", not as proof that the vendor's crawler is blocked.

## Training crawlers — not scored

| User-agent | Operator | What the vendor documents |
|---|---|---|
| `GPTBot` | OpenAI | Crawls content that may be used to train OpenAI's foundation models; disallowing it says the content should not be used for that. Each setting is independent: a site can allow `OAI-SearchBot` to appear in ChatGPT search while disallowing `GPTBot` ([O1]) |
| `ClaudeBot` | Anthropic | Collects content that could contribute to training; restricting it says the site's future materials should be left out of training datasets. Search and user fetches are `Claude-SearchBot` and `Claude-User` ([A1]) |
| `CCBot` | Common Crawl | Builds Common Crawl's open repository of web crawl data, which anyone may use ([CC]). Common Crawl is not an answer engine; what blocking it costs downstream: no data |
| `cohere-ai` | Cohere | Not checked against vendor documentation: no data |
| `Bytespider` | ByteDance | Not checked against vendor documentation: no data |
| `Meta-ExternalAgent` | Meta | Crawls the web "for use cases such as training foundation AI models or improving products by indexing content directly" ([MT]). Not documented as training-only; which products that indexing feeds, and what blocking it costs: no data |

## Opt-out tokens — not scored

`Google-Extended` and `Applebot-Extended` are not crawlers and send no requests of their own:
Google crawls with its existing user agents, and Apple says `Applebot-Extended` does not crawl
([GX], [AP]). `anthropic-ai` is listed here because the CLI's `NOT_SCORED_TOKENS` lists it;
whether it is an opt-out token or sends requests of its own: no data.

| Token | Operator | What it actually controls |
|---|---|---|
| `Google-Extended` | Google | Whether content Google crawls may be used to train future Gemini models (those behind Gemini Apps and the Vertex AI API for Gemini), **and for grounding in Gemini Apps and in Grounding with Google Search on Vertex AI** ([GX]). Search Console's help also names it as the control for training the models that generate AI Overviews and AI Mode answers ([GC]). It has no user-agent of its own: Google crawls with its existing crawlers. **Does not affect inclusion or ranking in Google Search** ([GX]) |
| `Applebot-Extended` | Apple | Whether content Applebot crawls may train Apple's foundation models (Apple Intelligence, Services, Developer Tools). It does not crawl, pages that disallow it can still appear in search results, and its rules are not used in ranking ([AP]). **It does not control Apple's AI answers:** Siri and Search answers that draw on Applebot's crawl are opted out of with `nosnippet` ([AP]) |
| `anthropic-ai` | Anthropic | Not in Anthropic's current crawler article, which names three agents: `ClaudeBot`, `Claude-User`, `Claude-SearchBot` ([A1]). What it controls today: no data |

## Google's AI features: which control does what

Google documents a separate control for each part. `Google-Extended` is not the control for appearing in AI
Overviews or AI Mode.

| What you want | The control Google documents |
|---|---|
| Keep Google from crawling a page, for Search and its AI features alike | robots.txt rules for Googlebot ([G5]) |
| Limit what Search shows from a page, AI features included | `nosnippet`, `data-nosnippet`, `max-snippet` or `noindex` ([G5]) |
| Leave AI Overviews, AI Mode and Discover's generative AI features, and stop your content grounding their answers | Search Console, Settings > Search generative AI, set to exclude. The default is include, and Google says the setting is not a ranking or inclusion signal for the rest of Search ([GC]). Its guide for generative AI features names being included there as a condition of appearing in them ([GA]) |
| Keep content out of Gemini training, and out of grounding in Gemini Apps and Vertex AI | `Google-Extended` ([GX]) |

To be eligible for Google's generative AI features, a page must be indexed and eligible to be
shown in Search with a snippet, and the site must be included under Search generative AI features
in Search Console ([GA]); include is the default ([GC]). Google's AI features page, which says there
are no additional technical requirements ([G5]), was last updated on 2025-12-10, before the control
reached all sites on 2026-08-31 ([GC]).

## How this list is scored

This file is a reference, not a scoring rule. Two rubric checks use it, and both are
defined in [`rubric/v1.1.md`](../rubric/v1.1.md) — read the tiers there, not here:

- **`g.robots`** — whether `robots.txt` allows the retrieval crawlers above. Three tiers.
  Each crawler is read against the group that names it, and against the `*` group only when
  no group names it (RFC 9309, section 2.2.1).
- **`g.reachable`** — whether all 10 actually return 200 with the same main content a
  browser gets. Three tiers, counted out of 10.

One thing worth stating because it is counter-intuitive: **blocking every training crawler and
every opt-out token costs nothing in the score.** Only the retrieval crawlers affect either check,
and the rubric scores a site that allows retrieval while refusing training at full marks. That is
the score, not the whole cost, and no check measures the rest. A `Disallow` for `Google-Extended`
also takes the site out of grounding in Gemini Apps and Vertex AI ([GX]). Meta describes
`Meta-ExternalAgent` as also indexing content to improve its products ([MT]). For `cohere-ai`,
`Bytespider` and `anthropic-ai`, and for what `CCBot`'s data feeds downstream, what blocking costs
is unknown. Refusing training is a coherent posture; refusing Gemini's grounding as well is a
separate choice, best made knowing that.

## Sources

Each page was re-read on 2026-10-04. The date in parentheses is the page's own, where it gives one.

- **[GX]** Google, [Google's common crawlers](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers), Google-Extended section (last updated 2026-07-14).
- **[GC]** Google Search Console Help, [Search generative AI control](https://support.google.com/webmasters/answer/16908024) (no update date; it says the control reached all websites worldwide on 2026-08-31).
- **[G5]** Google, [AI features and your website](https://developers.google.com/search/docs/appearance/ai-features) (last updated 2025-12-10).
- **[GA]** Google, [Optimizing your website for generative AI features on Google Search](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) (last updated 2026-07-10).
- **[AP]** Apple, [About Applebot](https://support.apple.com/en-us/119829) (published 2026-09-04).
- **[O1]** OpenAI, [Overview of OpenAI Crawlers](https://developers.openai.com/api/docs/bots) (undated).
- **[A1]** Anthropic, [Does Anthropic crawl data from the web, and how can site owners block the crawler?](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) (2026-04-07).
- **[CC]** Common Crawl, [CCBot](https://commoncrawl.org/ccbot) (undated).
- **[MT]** Meta, [Meta Web Crawlers](https://developers.facebook.com/documentation/sharing/webmasters/web-crawlers) (undated; the old address, `https://developers.facebook.com/docs/sharing/webmasters/web-crawlers/`, redirects there).

[GX]: https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
[GC]: https://support.google.com/webmasters/answer/16908024
[G5]: https://developers.google.com/search/docs/appearance/ai-features
[GA]: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
[AP]: https://support.apple.com/en-us/119829
[O1]: https://developers.openai.com/api/docs/bots
[A1]: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
[CC]: https://commoncrawl.org/ccbot
[MT]: https://developers.facebook.com/documentation/sharing/webmasters/web-crawlers
