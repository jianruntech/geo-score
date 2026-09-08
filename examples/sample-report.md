# Sample report

The output shape `/geo-score audit` produces. This example is a composite built from
real audit patterns — the site is not a real client, and the numbers are illustrative
of the *format*, not benchmarks to compare yourself against.

Two things every real report must carry, both shown here: **the rubric version** and
**the audit date**.

```
AIV Score  41 / 100   ·  rubric v1.0  ·  2026-09-08
Band: Below average — reachable, but not structured for retrieval

  Infrastructure        11 / 20
    ✓  robots.txt allows 9 of 12 known AI user-agents          4/4
    ✗  llms.txt                              not found         0/4
    ✗  llms-full.txt                         not found         0/3
    ✗  ai.txt                                not found         0/2
    ✓  sitemap.xml resolves, referenced from robots.txt        3/3
    ✗  no GEO <link> tags in <head>                            0/2
    ✓  primary content present in server-rendered HTML         2/2

  Structured Data        7 / 20
    ✓  Organization + WebSite sitewide                         4/4
    ✗  Article schema present but author is "admin"            0/4
    ✗  FAQPage absent on 6 pages structured as Q&A             0/3
    ✗  speakable not declared                                  0/3
    ✓  Product/Offer on 24 product pages                       3/3
    ✗  no BreadcrumbList                                       0/3

  Content Citability    10 / 25
    ✗  0 of 8 sampled pages open with a self-contained passage 0/5
    ✗  11 numeric claims, 2 carry a source                     1/5
    ✗  author is a brand name, not a person                    0/5
    ✓  headings phrased as natural questions on 5 of 8 pages   4/5
    ✓  dateModified present, median age 61 days                5/5

  Brand Authority        8 / 20
    ✗  no Wikidata item                                        0/5
    ✓  listed on 2 independent directories                     5/5
    ✗  no video channel linked via sameAs                      0/4
    ✓  brand discussed on 3 domains you don't control          3/3
    ✗  2 of 5 sameAs URLs 404                                  0/3

  Platform Visibility    5 / 15
    ✓  Search Console verified                                 3/3
    ✗  not submitted to Bing Webmaster                         0/3
    ✗  no recorded multi-engine query test                     0/3
    ✓  answer-shape fit acceptable on sampled pages            2/3
    ✗  audience is non-English; no regional engine tested      0/3

Largest single gap: Content Citability (10/25).
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
