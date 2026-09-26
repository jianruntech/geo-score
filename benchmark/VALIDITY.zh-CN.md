# CLI 与人工审计的一致程度

由 `benchmark/validity.py` 于 2026-09-27 用 geo-score-cli/1.2.0（量表 v1.1）生成。请勿手改，重跑脚本即可。
English: [VALIDITY.md](VALIDITY.md)

## 测了什么

[examples/audits/v1.1](../examples/audits/v1.1/) 里公开的 5 份人工审计，逐一用 CLI 在相同页面上重评（`--urls` 固定为审计的 `sampled_urls`），两边都打了分的检查项逐档比较，共 85 对。

## 结果

- **73% 的检查项两边档位完全一致。** 按规则读取的检查项一致率 90%（40 对）；CLI 用启发式近似的检查项一致率 58%（45 对）。3 个需要判断的检查项 CLI 从不打分。
- **CLI 的归一化分平均低 4.8 分**，范围从低 10 分到高 6 分。

## 引用之前先读这几条

- 样本只有 5 个站，每个站由一位审计者人工打分一次；这是第一次测量，不是效度研究。
- 人工审计有日期，CLI 是之后在线重评的，所以每一处差异里都混有网站自身的变化。
- CLI 只在被审计的域名内抽样，人工抽到的其他域名页面没有参与比较。
- 四个需要判断的检查项 CLI 从不打分，不在比较之内。

## 按站点

| 站点 | 人工审计日期 | 人工分 | CLI 分 | 差值 | 档位一致 | 页面数 |
|---|---|--:|--:|--:|--:|--:|
| anthropic.com | 2026-09-08 | 70 | 64 | -6 | 14/17 | 8 |
| mingdao.com | 2026-09-08 | 69 | 64 | -5 | 11/17 | 8 |
| nextjs.org | 2026-09-08 | 87 | 77 | -10 | 10/17 | 8 |
| stripe.com | 2026-09-08 | 77 | 83 | +6 | 12/17 | 6 |
| svelte.dev | 2026-09-08 | 78 | 69 | -9 | 15/17 | 8 |

## 按检查项

| 检查项 | 名称 | 对数 | 档位一致 | CLI − 人工 平均 | 分歧（人工→CLI） |
|---|---|--:|--:|--:|---|
| `g.robots` | Crawlers allowed in robots.txt | 5 | 80% | -0.4 | mingdao.com 5→3 |
| `g.reachable` | Reachable to retrieval agents | 5 | 40% | -0.4 | anthropic.com 5→3, nextjs.org 5→3, stripe.com 3→5 |
| `g.ssr` | Main content server-rendered | 5 | 60% | -0.8 | nextjs.org 5→3, stripe.com 5→3 |
| `p1.sitemap` | Sitemap discoverable and fresh | 5 | 100% | +0.0 | 无 |
| `p1.llms-txt` | llms.txt present and structured | 5 | 100% | +0.0 | 无 |
| `p1.organization` | Organization + WebSite schema | 5 | 80% | +0.4 | nextjs.org 3→5 |
| `p1.breadcrumb` | BreadcrumbList on nested pages | 5 | 100% | +0.0 | 无 |
| `p1.page-type` | Page-type schema (Product, FAQ…) | 5 | 80% | +0.4 | stripe.com 2→4 |
| `p2.answer-passages` | Self-contained answer passages | 5 | 60% | -1.0 | mingdao.com 7→4, nextjs.org 9→7 |
| `p2.question-intent` | Headings match how people ask | 5 | 80% | -0.8 | mingdao.com 7→3 |
| `p2.freshness` | Freshness signal present | 5 | 60% | -1.2 | anthropic.com 3→0, mingdao.com 3→0 |
| `p2.sourced-stats` | Statistics carry a source | 5 | 20% | +2.8 | anthropic.com 5→7, mingdao.com 3→7, nextjs.org 3→7, stripe.com 3→7 |
| `p2.named-author` | Named, verifiable authorship | 5 | 40% | -0.6 | mingdao.com 0→3, nextjs.org 6→3, svelte.dev 6→3 |
| `p3.listings` | Third-party listings | — | — | — | CLI 不打分，未比较 |
| `p3.mentions` | Independent mentions | — | — | — | CLI 不打分，未比较 |
| `p3.knowledge-graph` | Knowledge-graph entity | 4 | 100% | +0.0 | 无 |
| `p3.sameas` | sameAs links resolve | 5 | 80% | +0.2 | stripe.com 2→3 |
| `p3.video` | Video and multimodal presence | 5 | 60% | -0.8 | nextjs.org 2→0, svelte.dev 2→0 |
| `p4.answer-shape` | Content shaped for extraction | 5 | 100% | +0.0 | 无 |
| `p4.question-coverage` | Covers the questions people ask | — | — | — | CLI 不打分，未比较 |
| `p4.cn-engines` | Chinese engine readiness | 1 | 100% | +0.0 | 无 |

平均值为负，表示 CLI 在这一项上打得比审计者低。不报告 kappa：每项不足 10 对时它没有意义。
