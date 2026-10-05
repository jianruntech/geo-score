# CLI 与人工审计的一致程度

由 `benchmark/validity.py` 于 2026-10-02 用 geo-score-cli/1.5.0（量表 v1.1）生成。请勿手改，重跑脚本即可。
English: [VALIDITY.md](VALIDITY.md)

## 测了什么

[examples/audits/v1.1](../examples/audits/v1.1/) 里公开的 5 份人工审计，逐一用 CLI 在相同页面上重评（`--urls` 固定为审计的 `sampled_urls`），两边都打了分的检查项逐档比较，共 84 对。

这里比较的是 CLI 与人工按同一量表的读数。就绪度分数和被不被引用有没有关系是另一个问题，在收集任何数据之前写定在[预注册的验证方案](PREREGISTRATION.zh-CN.md)里。

## 结果

- **只看两边都打了分的检查项，CLI 平均低 2.4 分。** 逐站看，CLI 在这些检查项上的得分率减去审计者的，范围从低 12 分到高 10 分（平均绝对差 8.8 分）。Bland-Altman（n=5）：偏差 -2.4，95% 一致性界限 -21.7 到 +16.9。
- **按完整的归一化分算，CLI 平均低 5.2 分**，范围从低 16 分到高 7 分。两个数不同，是因为审计者还给 p3.listings、p3.mentions、p4.question-coverage 打了分，而 CLI 把这 3 项退出了分母。
- **80% 的检查项两边档位完全一致。** 按规则读取的检查项一致率 92%（39 对）；CLI 用启发式近似的检查项一致率 69%（45 对）。3 个需要判断的检查项 CLI 从不打分。

## 引用之前先读这几条

- 样本只有 5 个站，每个站由一位审计者人工打分一次；这是第一次测量，不是效度研究。
- 人工审计有日期，CLI 是之后在线重评的，所以每一处差异里都混有网站自身的变化。
- CLI 只在被审计的域名内抽样，人工抽到的其他域名页面没有参与比较。
- 三个需要判断的检查项 CLI 从不打分，不在比较之内；p4.cn-engines 只在 CLI 和审计者都打了分时才比较。
- 这 5 个站正是当初用 v1.0 审计来校准 v1.1 的那几个站（[校准记录](../rubric/calibration-v1.1.zh-CN.md)），所以这是开发数据，不是留出的检验集。
- 5 个站的人工分都在 69 到 87 之间，其中 1 个是中文站，0 个被门槛封顶，所以低分站和被封顶的站都没有代表。
- 审计文件没有记录是谁打的分，也没有记录打分的人是否看过 CLI 的输出。

## 按站点

| 站点 | 人工审计日期 | 人工分 | CLI 分 | 差值 | 档位一致 | 页面数 |
|---|---|--:|--:|--:|--:|--:|
| anthropic.com | 2026-09-08 | 70 | 77 | +7 | 14/17 | 8 |
| mingdao.com | 2026-09-08 | 69 | 58 | -11 | 12/17 | 8 |
| nextjs.org | 2026-09-08 | 87 | 71 | -16 | 12/16 | 8 |
| stripe.com | 2026-09-08 | 77 | 80 | +3 | 14/17 | 6 |
| svelte.dev | 2026-09-08 | 78 | 69 | -9 | 15/17 | 8 |

## 按检查项

| 检查项 | 名称 | 对数 | 档位一致 | CLI − 人工 平均 | 分歧（人工→CLI） |
|---|---|--:|--:|--:|---|
| `g.robots` | Crawlers allowed in robots.txt | 5 | 100% | +0.0 | 无 |
| `g.reachable` | Reachable to retrieval agents | 5 | 80% | +0.4 | stripe.com 3→5 |
| `g.ssr` | Main content server-rendered | 5 | 80% | -0.4 | nextjs.org 5→3 |
| `p1.sitemap` | Sitemap discoverable and fresh | 5 | 100% | +0.0 | 无 |
| `p1.llms-txt` | llms.txt present and structured | 5 | 100% | +0.0 | 无 |
| `p1.organization` | Organization + WebSite schema | 5 | 100% | +0.0 | 无 |
| `p1.breadcrumb` | BreadcrumbList on nested pages | 5 | 100% | +0.0 | 无 |
| `p1.page-type` | Page-type schema (Product, FAQ…) | 5 | 60% | +0.8 | anthropic.com 2→4, stripe.com 2→4 |
| `p2.answer-passages` | Self-contained answer passages | 5 | 60% | -1.0 | mingdao.com 7→4, nextjs.org 9→7 |
| `p2.question-intent` | Headings match how people ask | 5 | 80% | -0.8 | mingdao.com 7→3 |
| `p2.freshness` | Freshness signal present | 5 | 60% | +0.0 | anthropic.com 3→6, mingdao.com 3→0 |
| `p2.sourced-stats` | Statistics carry a source | 5 | 80% | -0.6 | mingdao.com 3→0 |
| `p2.named-author` | Named, verifiable authorship | 5 | 20% | +0.0 | anthropic.com 3→6, mingdao.com 0→3, nextjs.org 6→3, svelte.dev 6→3 |
| `p3.listings` | Third-party listings | — | — | — | CLI 不打分，未比较 |
| `p3.mentions` | Independent mentions | — | — | — | CLI 不打分，未比较 |
| `p3.knowledge-graph` | Knowledge-graph entity | 3 | 100% | +0.0 | 无 |
| `p3.sameas` | sameAs links resolve | 5 | 80% | +0.2 | stripe.com 2→3 |
| `p3.video` | Video and multimodal presence | 5 | 60% | -0.8 | nextjs.org 2→0, svelte.dev 2→0 |
| `p4.answer-shape` | Content shaped for extraction | 5 | 100% | +0.0 | 无 |
| `p4.question-coverage` | Covers the questions people ask | — | — | — | CLI 不打分，未比较 |
| `p4.cn-engines` | Chinese engine readiness | 1 | 100% | +0.0 | 无 |

平均值为负，表示 CLI 在这一项上打得比审计者低。不报告 kappa：每项不足 10 对时它没有意义。
