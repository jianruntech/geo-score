# How each engine selects sources

Observable characteristics of each answer engine's source selection. This file describes
**what the engines do** — it is not a list of tactics. Remediation is out of scope for
this repository (see [Scope](../README.md#scope--what-this-does-not-do)).

Everything here is inferred from public documentation and from observing live results.
Engines change without notice. Where a claim is our observation rather than vendor
documentation, it says so.

## Common to all of them

Answer engines do not return a ranked list. They **retrieve passages**, assemble an
answer, and attach citations to the passages they used. Three consequences that classic
SEO intuition gets wrong:

1. **The unit of selection is a passage, not a page or a domain.** A page can be cited
   for one paragraph and ignored for the rest.
2. **Rank position is weakly correlated with citation.** Sources outside the classic
   top 10 are routinely cited when their passages are cleaner.
3. **Parseability gates everything.** If the content is not in the HTML the crawler
   receives, no amount of authority compensates.

## Google AI Overviews

- Grounded in Google's existing index; `Google-Extended` controls whether your content
  may be used for grounding, separately from classic indexing.
- Structured data and clear entity relationships are visible inputs — pages with valid
  `Organization` / `Article` schema appear disproportionately in our observations.
- Topical depth across a cluster of related pages correlates with appearing at all.

## ChatGPT

- Two distinct agents: `OAI-SearchBot` for the search index, `ChatGPT-User` for
  on-demand fetches. Allowing one and not the other produces confusing results.
- *Our observation:* recently-updated pages are cited disproportionately relative to
  their link profile. We treat freshness as a real signal, which is why the rubric
  scores `dateModified`.

## Perplexity

- Heavily citation-forward — it shows sources by default, so being quotable is the
  whole game.
- *Our observation:* pages structured as explicit Q&A, and publicly reachable PDFs,
  are surfaced more often than their domain authority alone would predict.

## Gemini

- Draws on Google's Knowledge Graph. Entity records that resolve — a Wikidata item,
  consistent `sameAs` links — make the brand addressable as an entity rather than as
  a string.

## Microsoft Copilot

- Rides the Bing index. If Bing has not indexed the site, Copilot cannot cite it,
  regardless of Google standing. This is the single most common blind spot we see.
  v1.1 does **not** score Bing verification: it is visible only to the site owner, so it
  left the 100-point base along with the other unobservable checks. Report it as
  "measurable once access is granted" rather than scoring a zero you cannot see.

## Claude

- Uses web search results plus its training corpus. `llms.txt` quality matters more
  here than elsewhere in our observations, because the file is a concise, structured
  statement of what a site is.

## Non-English engines

If the audience is not English-speaking, the engines above may be largely irrelevant.
Regional engines have their own indexes and their own crawler behaviour. v1.1 scores this
in one place only — `p4.cn-engines`, which applies when a site addresses the Chinese
market and leaves the denominator when it does not. Other regional markets are not
scored, because we have not done the observation work to define tiers we could defend.

**We do not currently document regional engines in detail.** This is a known gap and a
good contribution — see [CONTRIBUTING.md](../CONTRIBUTING.md).
