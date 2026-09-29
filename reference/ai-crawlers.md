# AI crawler user-agents

The list the `g.robots` check checks `robots.txt` against. Consolidated from vendor documentation;
this is a reference, not original research. Vendors change these —
[open an issue](https://github.com/jianruntech/geo-score/issues) if one is stale.

**Last verified:** 2026-09-28

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

**The probes are unverified.** `g.reachable` sends each vendor's documented user-agent
string from the auditor's own address, not from the vendor's published IP ranges. For
two of the ten, `Claude-SearchBot` and `Claude-User`, Anthropic documents only the product
token: their strings are built from it, in the form of `ClaudeBot`'s. A firewall that
verifies crawlers by IP range or reverse DNS may refuse these probes and still serve the
real crawler. A refusal therefore reads as "this server refused unverified crawler
user-agents", not as proof that the vendor's crawler is blocked.

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

## How this list is scored

This file is a reference, not a scoring rule. Two rubric checks use it, and both are
defined in [`rubric/v1.1.md`](../rubric/v1.1.md) — read the tiers there, not here:

- **`g.robots`** — whether `robots.txt` allows the retrieval crawlers above. Three tiers.
  Each crawler is read against the group that names it, and against the `*` group only when
  no group names it (RFC 9309, section 2.2.1).
- **`g.reachable`** — whether all 10 actually return 200 with the same main content a
  browser gets. Three tiers, counted out of 10.

One thing worth stating because it is counter-intuitive: **blocking every training
crawler and setting both opt-out tokens costs nothing.** Only the retrieval crawlers
affect either check. Allowing retrieval while refusing training is a coherent posture,
not a compromise, and the rubric scores it as full marks.
