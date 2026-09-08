# AI crawler user-agents

The list Pillar 1 checks `robots.txt` against. Consolidated from vendor documentation;
this is a reference, not original research. Vendors change these —
[open an issue](https://github.com/jianruntech/geo-score/issues) if one is stale.

**Last verified:** 2026-09-08

## The distinction that matters most

Three different kinds of token appear in `robots.txt`, and conflating them is the most
common mistake in AI-visibility advice:

| Kind | What it is | Blocking it costs you |
|---|---|---|
| **Retrieval crawler** | A real crawler that fetches pages to answer user questions | **Citations.** This is what you must allow |
| **Training crawler** | Fetches pages for model training corpora | Nothing, in citation terms |
| **Opt-out token** | *Not a crawler.* Sends no requests. A control signal that says "don't use my content for AI training/grounding" | Nothing, in citation terms |

An opt-out token looks like a user-agent and sits in `robots.txt`, which is why it gets
mistaken for a crawler. `Disallow: Google-Extended` does not stop Googlebot from crawling
you and does not remove you from AI Overviews; `Disallow: Applebot-Extended` does not
remove you from Siri or Spotlight results.

**This rubric scores retrieval-crawler access only.** Blocking training crawlers and
opt-out tokens is a legitimate posture — content stays out of model weights while
remaining quotable — and is not penalised.

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

**9 of these 10 are the denominator for the Pillar 1 proportional check.**
`Perplexity-User` and `ChatGPT-User` are user-initiated and are counted with their
indexing counterparts, so the denominator is **10**. If a site's audience makes one
of these irrelevant, mark that check partially unobservable rather than failing it.

## Training crawlers — blocking these costs no citations

| User-agent | Operator |
|---|---|
| `GPTBot` | OpenAI |
| `ClaudeBot` | Anthropic |
| `CCBot` | Common Crawl |
| `cohere-ai` | Cohere |
| `Bytespider` | ByteDance |
| `Meta-ExternalAgent` | Meta |

## Opt-out tokens — not crawlers, send no requests

| Token | Operator | What it actually controls |
|---|---|---|
| `Google-Extended` | Google | Whether your content grounds Gemini and is used for training. **Does not affect Googlebot crawling or AI Overviews inclusion** |
| `Applebot-Extended` | Apple | Whether your content trains Apple's models. **Does not affect Applebot crawling or Siri/Spotlight results** |
| `anthropic-ai` | Anthropic | Legacy token, superseded by the named agents above |

## Scoring note

Pillar 1's first check awards 4 points by the proportion of **retrieval** crawlers
allowed, out of the 10 listed above. Partial credit is `floor(4 × allowed / 10)`.

A blanket `User-agent: * / Disallow: /` scores 0.
Allowing all retrieval crawlers while blocking every training crawler and setting both
opt-out tokens scores the full 4 — that combination is a deliberate, coherent posture,
not a failure.
