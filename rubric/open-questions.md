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
