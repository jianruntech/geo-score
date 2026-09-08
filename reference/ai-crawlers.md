# AI crawler user-agents

The list Pillar 1 checks `robots.txt` against. These are publicly documented user-agents;
this file is a consolidated reference, not original research. Vendors change these —
[open an issue](https://github.com/jianruntech/geo-score/issues) if one is stale.

## Retrieval crawlers — allowing these is how you get cited

| User-agent | Operator | Purpose |
|---|---|---|
| `OAI-SearchBot` | OpenAI | Powers ChatGPT search results |
| `ChatGPT-User` | OpenAI | Fetches a page when a user's prompt requires it |
| `PerplexityBot` | Perplexity | Indexing for Perplexity answers |
| `Perplexity-User` | Perplexity | User-initiated fetch |
| `Google-Extended` | Google | Controls Gemini / AI Overviews grounding |
| `Googlebot` | Google | Also feeds AI Overviews |
| `Bingbot` | Microsoft | Feeds Copilot |
| `Applebot-Extended` | Apple | Apple Intelligence |
| `Amazonbot` | Amazon | Alexa and Rufus |

## Training crawlers — blocking these does not cost you citations

| User-agent | Operator |
|---|---|
| `GPTBot` | OpenAI |
| `ClaudeBot`, `anthropic-ai` | Anthropic |
| `CCBot` | Common Crawl |
| `cohere-ai` | Cohere |
| `Bytespider` | ByteDance |

**The distinction matters for scoring.** Blocking training crawlers while allowing
retrieval crawlers is a legitimate, deliberate posture — it keeps your content out of
model weights while remaining quotable. The rubric scores **retrieval** crawler access
and does not penalise blocking training crawlers.

## Scoring note

Pillar 1's first check awards 4 points by the proportion of *retrieval* crawlers allowed.
A blanket `User-agent: * / Disallow: /` scores zero. A site that allows all retrieval
crawlers and blocks all training crawlers scores full marks.
