# Open questions against rubric v1.0

Found by running the rubric against five real sites. Each of these is a place where two
careful implementations would produce **different scores from the same evidence** — which
is the one thing a rubric claiming comparability cannot afford.

They are published rather than quietly patched, because the fix for several of them is a
judgement call we would rather make in the open. Each is a candidate for **v1.1**.

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
60–160 汉字 (at 1.5–1.8 characters per word) and said so in the evidence — a reasonable
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
