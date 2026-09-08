# Sample report

The output shape `/geo-score audit` produces. This example is a composite built from
real audit patterns — the site is not a real client, and the numbers are illustrative
of the *format*, not benchmarks to compare yourself against.

Two things every real report must carry, both shown here: **the rubric version** and
**the audit date**.

```
AIV 33 / 88  (v1.0)  ·  normalised 38%  ·  2026-09-08
Band: Critical

Sampled (8 URLs)
  /  /products/kettle  /products/grinder  /products/scale
  /blog/pour-over-ratio  /blog/grind-size  /blog/water-temp  /blog/storage

  Infrastructure                 9 / 20
    ✓  robots.txt allows 9 of 10 retrieval user-agents            2/3
    ✓  9 of 10 return 200 with the real page (Applebot 403)       2/3
    ✗  llms.txt                                not found          0/3
    ✗  llms-full.txt                           not found          0/2
    ✗  ai.txt                                  not found          0/2
    ✓  sitemap.xml resolves, referenced from robots.txt           3/3
    ✗  no GEO <link> tags in <head>                               0/2
    ✓  primary content present without executing JS               2/2

  Structured Data                7 / 17   (nominal 20, −3 excluded)
    ✓  Organization + WebSite sitewide                            4/4
    ✗  Article on 4 of 4 articles, but author is "admin"          0/4
    ✗  FAQPage absent on 3 pages structured as Q&A                0/3
    ✗  speakable not declared                                     0/3
    ✓  Product/Offer on 3 of 3 product pages                      3/3
    ⊘  HowTo / BreadcrumbList   not applicable — no procedural pages   —

  Content Citability             6 / 25
    ✗  0 of 8 pages open with a self-contained passage            0/5
    ✗  11 numeric claims, 2 carry a source                        0/5
    ✗  author is a brand name on 4 of 4 articles                  0/5
    ✓  headings phrased as natural questions on 5 of 8            3/5
    ✓  dateModified on 5 of 8, median age 61 days                 3/5

  Brand Authority                9 / 20
    ✗  no Wikidata item                                           0/5
    ✓  listed on 2 independent directories                        5/5
    ✗  no video channel linked via sameAs                         0/4
    ✓  brand discussed on 3 domains you don't control             3/3
    ✗  2 of 5 sameAs URLs resolve, 3 return 404                   1/3

  Platform Visibility            2 / 6   (nominal 15, −9 excluded)
    ⊘  Search Console verification   unobservable — external audit   —
    ⊘  Bing Webmaster submission     unobservable — external audit   —
    ✗  cited in 0 of 3 engines on a 12-query buyer-intent set     0/3
    ✓  answer-shape fit acceptable on 6 of 8 pages                2/3
    ⊘  non-English engines           not applicable — EN audience   —

Excluded from denominator  −12
  3   HowTo / BreadcrumbList
  3   Search Console verification
  3   Bing Webmaster submission
  3   non-English engines

Largest single gap: Content Citability, 6 of 25.
```

## Reading it

- **Every check is shown, including passes.** A report that lists only failures reads
  as a sales document rather than an audit.
- **`✓` means observed, not reported.** Where the site owner told us something we could
  not verify from outside — Search Console verification, for instance — a real report
  marks it `(reported)`.
- **The band matters more than the number.** Moving 41 → 47 inside "Below average" is
  noise; crossing into "Good" reflects a structural change.
- **The largest single gap is called out** because remediation sequencing is usually
  obvious once you see where the weight is lost.

## What this report deliberately does not include

No fix instructions. See [Scope](../README.md#scope--what-this-does-not-do).
