# Sample report

The output shape `/geo-score audit` produces. This example is a composite built from
real audit patterns — the site is not a real client, and the numbers illustrate the
*format*, not a benchmark to compare yourself against.

Four things every real report must carry, all shown here: **the rubric version**, **the
audit date**, **the gap to the next band**, and **which checks left the denominator and why**.

```
AIV Readiness 45 / 98  (rubric v1.1)  ·  normalised 46%  ·  2026-09-08
Band: Early  —  5 points below Growing

Sampled (8 URLs)
  /  /products/kettle  /products/grinder  /products/scale
  /blog/pour-over-ratio  /blog/grind-size  /blog/water-temp  /blog/storage

  Reachable                    15 / 15   ← gate checks
    ✓  robots.txt names all 10 retrieval UAs under Allow        5/5
       full tier
    ✓  all 10 retrieval UAs return 200, byte-identical to a b…  5/5
       full tier
    ✓  primary content present without executing JS             5/5
       full tier

  Understandable               15 / 22
    ✓  sitemap.xml resolves, declared in robots.txt, lastmod …  4/4
    ✗  llms.txt not found                                       0/5
       tier 1 of 4
    ◐  Organization + WebSite sitewide, logo resolves — no sa…  5/6
       tier 3 of 4
    ◐  BreadcrumbList on 3 of 7 nested pages                    2/3
       tier 2 of 3
    ✓  Product + Offer on 3 of 3 product pages, price and ava…  4/4

  Content Citability            9 / 35
    ✗  0 of 8 pages open with a self-contained passage          0/9
       tier 1 of 4
    ◐  2 of 8 headings phrased as a task or question            3/7
       tier 2 of 4
    ◐  visible dates on 4 blog posts, none on 4 product pages   3/6
       tier 2 of 3
    ◐  11 numeric claims, 2 carry a source                      3/7
       tier 2 of 4
    ✗  author is the brand name on 4 of 4 articles              0/6
       tier 1 of 3

  Brand Credibility             2 / 18
    ◐  listed in 2 directories                                  2/4
       tier 2 of 4
    ✗  no independent coverage found                            0/4
       tier 1 of 4
    ✗  no Wikidata or Wikipedia entity                          0/4
    ✗  sameAs not declared                                      0/3
       tier 1 of 3 — absent scores 0, it is not excluded
    ✗  no official video channel                                0/3
       tier 1 of 3

  Answer Fit                    4 / 8
    ◐  headings present, paragraphs run long                    2/4
       tier 2 of 3
    ◐  3 of 10 common buyer questions answered on site          2/4
       tier 2 of 4

  ⊘ p4.cn-engines  not applicable — no Chinese-market presence  (−2 from the denominator)

  Bonus checks: none found (+0, outside the denominator; caps at +6)

Citation performance — not scored
  Whether engines actually cite this site is an outcome, not a property of the site.
  It is reported separately once query tests are run. A readiness score says engines
  *can* cite you; it does not say they *do*.
```

## Reading it

**The score is readiness, not results.** It says whether an engine *can* find, parse,
trust and cite the site. Whether one *does* depends on competition and query intent,
which no site-side audit can observe. The two are reported separately and never summed.

**Tiers, not pass/fail.** `2/4` on a 4-point check means the evidence satisfied the
second tier, not that someone awarded half marks. The tier reason says why it did not
reach the next one — that line is the actionable part.

**Excluded checks leave the denominator.** A site with no product pages is not penalised
for missing `Product` schema; the check is removed and the maximum drops. This is why
the header reads `45 / 98` rather than `45 / 100`, and why two sites' raw scores are only
comparable after normalising.

**Gate checks come first.** If `g.robots`, `g.reachable` or `g.ssr` is short of full
marks, readiness caps at 40 and the report leads with it. Until a crawler can reach the
content, nothing else you change has any effect.
