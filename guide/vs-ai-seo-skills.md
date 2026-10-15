# How geo-score differs from a general AI SEO skill

An AI SEO skill is a set of instructions for a coding agent: it asks the model to read a site, judge it against a
checklist and suggest changes, often writing them. geo-score is a published scoring rule with code that implements
it. They answer different questions, and they work well together. This page names no other project; it compares the
two kinds of tool.
中文版：[vs-ai-seo-skills.zh-CN.md](vs-ai-seo-skills.zh-CN.md)

| | A general AI SEO skill | geo-score |
|---|---|---|
| What it is | Instructions a model follows | A versioned rubric ([v1.1](../rubric/v1.1.md)) and a program that implements it, standard library only |
| Who decides the reading | The model, on the pages it happened to read | The rubric: 21 checks, each tier a count out of 8 sampled pages |
| Same site, run again | Depends on the model, the prompt and the day | The same pages give the same score; how far a fresh sample moves it is measured in [REPRODUCIBILITY.md](../benchmark/REPRODUCIBILITY.md) |
| What it sees | What the agent's own fetcher gets | robots.txt read as RFC 9309 says, the pages requested as ten retrieval crawlers and as a browser, the server HTML before JavaScript |
| Evidence | Prose | One evidence line per check (`--explain`), a JSON report against a [published schema](../schema/report.v2.json) |
| What it cannot see | Usually unstated | Left out of the denominator and named, never scored zero |
| Whether AI cites you | Usually not measured, or one answer | Levels 2 and 3, through the engines' APIs with your keys, as rates with intervals, never added to the score |
| Fixes | Often writes them | Does not, apart from [two public examples](public-examples.md) |
| Cost | Model usage | Level 1 is free; levels 2 and 3 cost your own API calls |

## What a skill does better

Writing. Rewriting a passage so it stands on its own, drafting an FAQ, suggesting headings people actually ask,
reviewing tone: these are judgement and craft, and a model with good instructions is a fair tool for them. Three
of the rubric's own checks (`p3.listings`, `p3.mentions`, `p4.question-coverage`) need off-site search or judgement,
which is why geo-score also ships as an agent skill ([SKILL.md](../SKILL.md)) that does those with the agent and says
so.

## What a checklist in a prompt cannot promise

- **Comparability.** A reading that depends on the model cannot be compared with last month's, or with a competitor's.
  A versioned rubric can: every report names its version, and scores from different versions are not compared.
- **The crawler's view.** A model that fetches a page sees what its own fetcher gets. A firewall that refuses one
  retrieval crawler and serves the others, or a page whose text appears only after JavaScript runs, looks fine from
  there.
- **A number you can recompute.** Every check, tier and weight is published, so anyone can recompute a geo-score
  result from the same pages, by hand ([rubric/README.md](../rubric/README.md#how-to-score-without-the-skill)) or
  with another implementation.

## Using both

Score before a change, make the change with whatever tool or person suits it, and score again on the same pages:
`--baseline before.json` re-reads the pages of the first run and prints what moved, check by check
([cli/README.md](../cli/README.md#comparing-two-reports)). The measurement stays the same while the way you change
the site does not have to.
