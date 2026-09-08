# Examples

| File | What it shows |
|---|---|
| [sample-report.md](sample-report.md) | The output shape, on a composite site. Read this first |
| [audits/](audits/) | **Five real audits of public sites**, with evidence for every check |

## The five audits

Run 2026-09-08 against rubric v1.0, using only publicly observable data.
Each has a human-readable `.md` and a machine-readable `.json` conforming to
[`schema/report.v1.json`](../schema/report.v1.json).

| Site | AIV | Normalised | Band | The short version |
|---|:-:|:-:|---|---|
| [stripe.com](audits/stripe.com.md) | 45 / 88 | 51% | Below average | A 65 KB `llms.txt` and near-perfect brand authority, undercut by a homepage that ships almost no server-rendered text |
| [nextjs.org](audits/nextjs.org.md) | 40 / 82 | 49% | Below average | Serves markdown to AI crawlers and keeps a 3.97 MB corpus — and declares almost no structured data |
| [svelte.dev](audits/svelte.dev.md) | 34 / 85 | 40% | Critical | Everything bet on the `llms.txt` line: four tiers, 2.1 MB. No sitemap, no JSON-LD at all |
| [anthropic.com](audits/anthropic.com.md) | 32 / 88 | 36% | Critical | Perfect crawler reachability and 60 KB of server-rendered text, but 1 answer passage across 8 pages |
| [mingdao.com](audits/mingdao.com.md) | 29 / 85 | 34% | Critical | A hand-written `llms.txt` and a Content-Signal policy — rare in Chinese SaaS — on top of thin machine-readable structure |

## What five real audits actually told us

**Nobody cleared 51%.** Not Stripe, not Anthropic, not the framework docs sites whose
audience is literally developers. If you were expecting a leaderboard, this is not one.

Two honest readings of that, and we hold both:

**Reading one — the bar really is low.** Most of what this rubric checks is cheap and
uncontroversial: declare an author, put a sitemap where you said it is, open a page with
a sentence that answers its own question. Sites that do sophisticated engineering
elsewhere are simply not doing these, because until recently there was no reason to.

**Reading two — parts of this rubric are ahead of adoption.** `ai.txt`, `speakable`, and
GEO `<link>` tags are barely adopted anywhere. A site can lose 7 points for skipping
conventions most of the web has never heard of. And a band label of *Critical* on a site
with flawless crawler reachability and 60 KB of server-rendered prose reads wrong — the
band describes the score, not the site's health.

We have not resolved this. It is the first item in
[rubric/open-questions.md](../rubric/open-questions.md), and it is exactly the kind of
thing we would rather argue about in public than quietly tune away.

## Reading an audit

- **Every check carries evidence**, including the ones that passed. Byte counts, status
  codes, MD5s across user-agents, the actual sentence that did or did not qualify as an
  answer passage.
- **`⊘` is not a failure.** It is either *unobservable* (Search Console state, when
  auditing someone else's site) or *not applicable* (Product schema on a site with
  nothing for sale). Those points leave the denominator, which is why the maximums differ.
- **Every audit ends with the auditor's caveats** — the judgement calls, and what could
  not be verified. Several of those became open questions against the rubric.

## Contributing an audit

We want more, especially:

- a site scoring **above 60**, which we did not find
- a non-English site outside Chinese
- a **before / after** pair on the same site, both dates, both rubric versions

Use only publicly observable data. Never guess a check — mark it `unobservable` and say
why. Include the caveats; an audit that hides its judgement calls is worth less than one
that shows them.
