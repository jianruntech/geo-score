# Open questions against rubric v1.0

> **All eight are resolved in [v1.1](v1.1.md).** The resolutions are recorded inline
> below, and the reasoning behind the calibration is in
> [calibration-v1.1.md](calibration-v1.1.md). This page is kept as the record of how
> v1.0 was wrong and what was decided — not as a live issue list. New ambiguities go
> to GitHub issues under the `rubric` label.

Found by running the rubric against five real sites. Each of these is a place where two
careful implementations would produce **different scores from the same evidence** — which
is the one thing a rubric claiming comparability cannot afford.

They were published rather than quietly patched, because the fix for several of them was
a judgement call we would rather make in the open.

## Resolutions at a glance

| # | Question | What v1.1 decided |
|:-:|---|---|
| 1 | Band labels described the score, not the site's health | All five bands renamed to stage language (Not started / Early / Growing / Solid / Leading). "Critical" is deleted and CI now rejects verdict-style band names. Separately, readiness and citation performance were split into two numbers — a 36 reads as damning mainly because a fixable score and a naturally low one were being averaged together. |
| 2 | Does a "sectioned link group" in `llms.txt` have to contain links | **Yes.** The top tier reads "2 or more topic sections that contain links". A prose section with no links does not count. |
| 3 | May `llms-full.txt` live somewhere other than the root | **Yes**, provided it is discoverable from `llms.txt` or `robots.txt`. The check also moved out of the denominator and became a bonus. |
| 4 | Does "named authorship" require an on-site bio page | **No.** The top tier is "the name links to a verifiable identity page" — an on-site author page and the person's own homepage are equivalent. This is the ambiguity two of our own v1.0 audits resolved in opposite directions. |
| 5 | Does a visible date count as freshness without `dateModified` | **Yes.** A schema date and a reader-visible date are equivalent for the middle tier; the top tier requires both, and that they agree. |
| 6 | "40–90 words" has no authoritative equivalent in Chinese | Fixed at **50–200 Chinese characters** (English widened to 25–120 words), written into scoring rule 7 so it is no longer each auditor's call. |
| 7 | With zero `sameAs` declared, is the check failed or not applicable | **Scored zero, stays in the denominator.** Not declaring is not doing, not "does not apply". |
| 8 | Does a sitemap path declared in `robots.txt` take precedence | **Yes**, over the conventional path. Written into `p1.sitemap`. |

Two of these changed more than a verdict. #1 changed what the number means. #6 made Chinese
and English sites comparable on the content pillar for the first time.

*同一张表的中文版见 [open-questions.zh-CN.md](open-questions.zh-CN.md)。*

---

---

## 1 · The band labels do not describe what they are measuring

anthropic.com scores 36% and lands in **Critical** — while returning 200 to all ten
retrieval crawlers, byte-identical to a browser, with 60 KB of server-rendered prose.
Nothing about that site is critical. It simply has not adopted `llms.txt`, `ai.txt` or
structured data.

Meanwhile `ai.txt`, `speakable` and GEO `<link>` tags together carry 7 points and are
barely adopted anywhere on the web. A rubric may legitimately be ahead of adoption, but
then its labels should say *"has not adopted current conventions"*, not *"critical"*.

**Options:** rename the bands to describe adoption rather than health · re-weight
emerging conventions down · split the score into an "adopted" and an "emerging" component.
**Not yet decided.**

## 2 · What counts as a "sectioned link group" in `llms.txt`

svelte.dev's `llms.txt` has three `##` sections, but one holds prose bullets with no
links. Scored literally that is 2 of 3 required groups, and because the check is
all-or-nothing it drops 3 points and moves the band.

**The check needs to say** whether a section must contain links to count, and whether the
threshold is on sections or on link groups.

## 3 · Where `llms-full.txt` is allowed to live

nextjs.org returns 404 at `/llms-full.txt` but serves a 3.97 MB corpus at
`/docs/llms-full.txt`. The auditor awarded the points and flagged it as the single most
arguable call in that report.

**The check needs to state** whether a non-root path counts, and if so how a scorer is
supposed to find it — a link from `llms.txt`? A `<link>` tag? Convention only?

## 4 · "Named expert authorship … with a bio"

nextjs.org's articles are bylined to real, identifiable engineers whose names link to
their own profiles. There is no bio page on the site. Read literally: 0 of 5. Read by
intent — is the author a real identifiable person — 5 of 5. **A five-point swing on one
preposition.**

**The check needs to define** what satisfies "identifiable": a bio page, a resolvable
profile link, an `author` entity with `sameAs`, or a human name that is not "admin".

## 5 · Freshness when the date is visible but not machine-readable

Several sites show publication and update dates in the page, but declare no
`dateModified` anywhere — no JSON-LD, no `article:modified_time`, no `og:updated_time`.

Since the whole rubric is about machine readability, scoring 0 is defensible. But the
check is named *Freshness signals*, and a visible date is a signal.
**Decide and say so**, rather than leaving it to the scorer.

## 6 · The passage length rule has no CJK equivalent

"40–90 words" does not transfer to Chinese. The auditor of mingdao.com adopted
60–160 Chinese characters (at 1.5–1.8 characters per word) and said so in the evidence — a reasonable
choice, and one that directly decided two checks.

**The rubric must state a CJK-equivalent range**, or state the rule in a script-neutral
unit. Until then, Chinese sites are not comparable to English ones on Pillar 3.

## 7 · `sameAs` integrity when there is no `sameAs`

mingdao.com declares zero `sameAs` links, so the "do they resolve" check has an empty
denominator. The auditor scored it `failed` (0 of 3, still in the denominator), reasoning
that `not_applicable` is defined for missing *page types*, not missing markup.

**Both readings are defensible** and they differ by 3 points. The rules need to say which.

## 8 · Sitemap discovery beyond `/sitemap.xml`

stripe.com returns 404 at `/sitemap.xml`, and its `robots.txt` points at a sitemap index
under a different path. Checking only the conventional location would have scored 0 for a
site that has a complete, correctly-declared sitemap.

**The check should say** that a `Sitemap:` directive in `robots.txt` is authoritative,
and that the conventional path is a fallback, not the definition.

---

## How these get resolved

Each becomes an issue tagged `rubric`. Anything that changes a weight or a pass condition
ships as **v1.1**, in a new file — [`v1.0.md`](v1.0.md) is never edited in place, so the
five audits above stay meaningful and reproducible against the version they were run on.

If you have a view, especially on **1** and **6**, that is the most useful thing you can
contribute right now.

---

## 9 · A site on a subpath is penalised for an origin it does not own

*Found 2026-09-09, after v1.1 shipped. **Resolved 2026-09-09.***

`p1.llms-txt`, `p1.sitemap` and the `b.*` bonus checks all look at the **origin root** —
`https://host/llms.txt`, `https://host/sitemap.xml`. That is correct by each convention's
own spec. But a project page on GitHub Pages, a docs subtree at `example.com/docs`, or a
country folder at `brand.com/de/` cannot write to the origin root. Someone else owns it.

This repository's own leaderboard is the example: it lives at
`jianruntech.github.io/geo-score/` and publishes `llms.txt` at
`/geo-score/llms.txt`, declared from the page with
`<link rel="alternate" type="text/plain">`. The rubric scores it zero, because
`github.io/llms.txt` belongs to GitHub.

The check is not wrong about what retrieval engines do — most look at the origin. But
scoring a site zero for a file it is not permitted to create measures ownership, not
readiness, and the resulting number is not comparable between a root-domain site and a
subpath site.

**Resolved: fall back to the given path.** When the sampled base has a non-empty path
and the origin file is absent, the check looks for the same file under that path.
The origin still wins when both exist, and the evidence line says which one was read,
so a reader can tell a root-domain result from a subpath one. This applies to
`p1.llms-txt`, `p1.sitemap`, `b.llms-full` and `b.ai-txt`.

Scoring this pass changed our own leaderboard page from 69 to 82.

**Two things surfaced while implementing it that the question above had missed:**

`p1.breadcrumb` was affected too. It counted path segments from the origin, so on a
project page every URL looked nested and the site was marked down for missing
breadcrumbs it does not need. Nesting is now counted relative to the given path, and
a site with no genuinely nested pages leaves the denominator instead of scoring zero.

`p1.page-type` did not accept `Dataset`. A page whose subject *is* a published dataset
states its type as precisely as a Product page does; leaving it out silently marked
down open-data portals, research and government publishers as a class. The benchmark
was **not** re-run for this — a spot check of eight sites that list `p1.page-type`
among their top gaps found none declaring `Dataset`, so the published medians hold,
but the next full run may raise a few data-publishing sites.

**`robots.txt` deliberately keeps the origin-only rule.** It genuinely is origin-scoped,
and a site under a path has no robots.txt of its own to offer. A subpath site therefore
still inherits its host's crawler policy — our own page scores 3/5 on `g.robots` because
that file is GitHub's. That asymmetry is real, and it is the honest answer rather than a
fixable bug.

The five published audits are unaffected — all five targets are root domains.

---

## 10 · A robots.txt that cannot be read: allowed, or fully disallowed? (open, for v1.2)

RFC 9309 reads an unreadable robots.txt in two ways. A 4xx answer means there is no file,
and a crawler may fetch anything (section 2.3.1.3). A server error, or a network that gets
no answer, means the file is unreachable, and a crawler must assume a full disallow until it
can read the file again (section 2.3.1.4).

geo-score 1.5.0 does not apply 2.3.1.4. A robots.txt that answers 429 or 5xx on every try
keeps the middle tier of `g.robots`, and the evidence names the status and the number of
tries. A robots.txt that never answers (timeouts, dropped connections) is `unobservable` and
leaves the denominator, because a network that cannot reach a file is no evidence of what the
file says.

**The question for v1.2:** should a robots.txt that answers 5xx on every try read as a full
disallow, which is tier 0 and the gate cap, the way a crawler that follows the RFC treats it?
Against: one audit sees one moment, while a crawler keeps retrying for much longer before it
acts on an outage. Nothing changes in v1.1.

---

## 11 · A sample with few figures: 3 of 7, or not applicable? (open, for v1.2)

`p2.sourced-stats` reads the sampled pages that carry three or more figures. From geo-score 1.5.0 a
figure counts as attributed only when its own block of the content, or the next block, holds a link
to a source off the site, a `<cite>`, a source phrase, or a footnote reference whose note on the page
links to a source. The page chrome (header, nav, footer, aside) is not read. A year, a version number,
an identifier (a run of seven or more digits, or a filing or account number such as `京ICP证030173号`)
and a price (a sum of money written as one, such as `$29/mo` or `68元/月`, or standing alone as a pricing
card or a price-table cell such as `£12 a month`) are not figures. A page attributes most of its
figures when more than half of them are attributed. The top tier needs three quarters of those pages
to attribute most of their figures with a link, the tier below needs half of them to attribute most of
their figures in any of these ways, and the lowest tier above zero needs one attributed figure.

When no sampled page carries three figures, the check keeps the 3 points it has always given: there is
nothing to attribute, so nothing is missing, but nothing is shown either.

**The question for v1.2:** should a sample with no page carrying three figures leave the denominator
(`not_applicable`), as `p1.breadcrumb` does when no nested page is sampled? For: 3 of 7 for a sample
without figures is a reading of nothing. Against: a site that states no figures makes no claim a reader
has to check, and the rubric does not score the absence of a claim as a gap. Nothing changes in v1.1.

---

## Candidate diagnostics: reported, never scored (proposed 2026-10-15)

Five observations we are considering for the report's [Outside the score](../cli/README.md#outside-the-score)
block, where the page-by-page robots.txt reading, the links in the server HTML and hreflang already sit. They are
recorded here before any code exists, so the design can be argued in the open.

Every one of them follows the rules that block already keeps:

- **No tier, point or band reads it.** Rubric v1.1 does not change, and no score moves. Making any of them a check
  would be a rubric change, argued like the open questions above and released as a new rubric version.
- **It ships in a normal release, with offline tests:** a fixture site for each reading below, and a test that the
  score is identical with and without the observation, as the hreflang and robots.txt observations have.
- **A request it needs is added on purpose.** Candidates 12 (its first two readings), 15 and 16 read pages the run
  already fetched. Candidates 12 (its third reading), 13 and 14 need a few requests of their own, which raises the
  request budget that `test_no_request_is_sent_twice` holds the good fixture to ([AGENTS.md](../AGENTS.md)).
- **A threshold is ours, and adjustable.** Where a candidate warns above a number that no vendor publishes, the
  report says so, and the number is a flag a user can change.

| # | Candidate | New requests | Basis |
|:-:|---|:-:|---|
| 12 | canonical: missing, all pointing at the homepage, or not stripping a tracking parameter | 0, then 1 | Vendor documentation |
| 13 | Soft 404: a random path answers 200 | 2 | Vendor documentation |
| 14 | The homepage redirects by language | 2 | Vendor documentation |
| 15 | The same plan shows different prices on two pages | 0 | Field observation |
| 16 | Homepage HTML weight (lower priority) | 0, more for resources | Vendor documentation and field observation |

### 12 · canonical

**What it would report.** Three readings of the canonical URL, from the `<link rel="canonical">` element in the
server HTML and from a `Link` header:

1. Sampled pages that declare no canonical at all.
2. A sample in which every page declares the homepage as its canonical, though the pages are different URLs with
   different content.
3. The homepage, requested again with `?utm_source=chatgpt.com` appended, declaring a canonical that still carries
   the parameter, rather than the clean URL. A redirect to the clean URL is a pass.

**Basis.** Google lists a `rel="canonical"` annotation as a strong signal for which of several duplicate URLs
becomes canonical ([consolidating duplicate URLs](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)).
OpenAI's publisher FAQ says ChatGPT search adds `utm_source=chatgpt.com` to the links it sends
([Publishers and developers FAQ](https://help.openai.com/en/articles/12627856-publishers-and-developers-faq)), so a
page cited there is also reached under a second URL. A canonical that points every page at the homepage tells a
crawler that the inner pages are copies of it.

**False-positive risk: moderate.** A canonical inserted by JavaScript is not in the server HTML: the report would say
"not in the server HTML", never "missing". A site that is genuinely one page, pages of a series that point to a view
of the whole series, and a canonical to another host during a migration or for syndicated copies are deliberate.
A cache keyed on the query string can answer the parameter request differently from the clean one for reasons
unrelated to the page.

**How to test it.** Fixture sites: canonicals per page (clean); every page pointing at `/`; a page that echoes the
query string into its canonical; a parameter URL that redirects to the clean one; a canonical sent only in the
`Link` header. By hand: request the homepage with `?utm_source=chatgpt.com` and read the `rel="canonical"` line
of the HTML it returns.

### 13 · Soft 404

**What it would report.** Two random paths that nothing links to, requested once each: whether they answer 404 or
410, redirect to the homepage, or answer 200 with an HTML page. Both answering 200 is the reading.

**Basis.** Google defines a soft 404 as a URL that returns a page telling the user the page does not exist, with a
200 status, and says such pages are excluded from Search
([soft 404 errors](https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors#soft-404-errors)).
A site that answers every path with 200 also makes a mistyped link in a sitemap or an answer look like a real page.
The CLI already meets this at one path: `p1.llms-txt` reads a 200 HTML answer at `/llms.txt` as a catch-all route,
not a file.

**False-positive risk: moderate.** A bot challenge served on an unknown path is not a page, and the existing
challenge detection would have to run first. A single-page app that renders its "not found" view in the browser
answers 200 by design: that is the reading, but the report should say it is an app shell. A rate limit can answer
a probe with an error page. Two paths, and a reading only when both agree, keep one odd answer from deciding it.

**How to test it.** Fixture sites: a real 404; a catch-all that answers 200; a redirect of unknown paths to the
homepage; a challenge page on unknown paths. By hand: request a path such as `/this-page-should-not-exist-7f3a` and
read the status code alone.

### 14 · The homepage redirects by language

**What it would report.** The homepage requested with two other `Accept-Language` values besides the one every run
already sends (`en,zh;q=0.8`): whether the final URLs differ. A redirect that is the same for every language (the
root always going to `/en/`) is not this reading.

**Basis.** Google says Googlebot's requests usually come from US addresses and do not set `Accept-Language`, so it
may not find every language version, and advises against redirecting visitors automatically by their perceived
language ([multi-regional and multilingual sites](https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites),
[locale-adaptive pages](https://developers.google.com/search/docs/specialty/international/locale-adaptive-pages)).
A retrieval crawler that lands on one language version may never see the others. The CLI already records where a
request landed when a site hands back a different origin, which is the same effect seen from one header.

**False-positive risk: moderate, and a blind spot.** A redirect by IP address cannot be seen from one vantage: the
report can say what the auditor's address got, never what a crawler elsewhere gets. Content negotiated at the same
URL, without a redirect, is a different reading (`Vary: Accept-Language`), and a consent or region wall can redirect
for reasons that have nothing to do with language.

**How to test it.** Fixture sites: a redirect chosen by `Accept-Language`; a redirect to `/en/` for every request;
one URL whose content varies by the header with no redirect. By hand: request the homepage twice, with
`Accept-Language: de` and with `Accept-Language: en`, and compare the `Location` headers.

### 15 · The same plan shows different prices on two pages

**What it would report.** A plan or product name that appears with different amounts, in the same currency and the
same billing period, on two sampled pages (the pricing page and a documentation or FAQ page, say), quoting both
amounts and both pages.

**Basis: field observation.** An answer engine summarises the page it retrieved. When two pages of one site disagree,
two answers to the same question disagree, and the engine has no way to tell which is current. No vendor documents
this as a factor in citation. The CLI already recognises a price as a price (`p2.sourced-stats` excludes prices from
the figures it counts, [question 11](#11--a-sample-with-few-figures-3-of-7-or-not-applicable-open-for-v12)).

**False-positive risk: high,** which is why it would quote the two passages and never conclude. Monthly and yearly
billing, regional prices and currencies, a struck-through old price beside a new one, tax included or not, per seat
or flat, volume tiers, a dated price in a changelog or a blog post, and a price in a worked example all look like a
disagreement and are not. An eight-page sample also rarely holds two pages that price the same plan, so a clean
reading says little.

**How to test it.** Fixture sites: consistent prices; one real disagreement; a monthly and yearly pair; a
struck-through old price. By hand: list each plan's price on every page that states one.

### 16 · Homepage HTML weight (lower priority)

**What it would report.** The size of the homepage's HTML as served and after decompression, and, at a later stage,
the sizes of the stylesheets and scripts its `<head>` references, with a warning above a threshold.

**Basis.** Google documents that, when crawling for Google Search, Googlebot reads the first 2 MB of a supported
file type and fetches each referenced resource separately, under the same limit
([Googlebot](https://developers.google.com/search/docs/crawling-indexing/googlebot), read 2026-10-15). Content past the
limit is not read. Practitioners also report sites dropping out of a search index after their pages grew to many
megabytes; that is anecdote, no vendor publishes a number for it, and any warning below the documented limit would be
a practitioners' rule of thumb: adjustable, and not a vendor figure.

**False-positive risk: low for the measurement, high for the warning.** The size depends on the user agent and on
compression; inline SVG, fonts and data URIs inflate HTML for legitimate reasons; a large serialised state object
is a real cost, but not an error. Measuring resources needs one request each, so it would be capped.

**How to test it.** Fixture sites: a small page; a page with a large inline data block above the threshold; the
same page served gzip-encoded, where the decoded size is the one that counts. By hand: download the homepage with
decompression on and count its bytes.
