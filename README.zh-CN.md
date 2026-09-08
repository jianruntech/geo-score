<p align="right"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>

<p align="center"><img src="assets/cover.svg" alt="geo-score — 开源的 AI 可见度评分口径" width="100%"></p>

# geo-score

**一套开源、带版本号的 GEO（生成式引擎优化）评分口径 —— 给任何网站打 0–100 分，
衡量 AI 回答引擎能不能找到、读懂、信任并引用它。**

它发布的这套口径叫 **AIV 分**（AI Visibility，AI 可见度）。21 项阶梯式检查合计 100 分，
另有 4 项加分检查、不进分母、最多 +6——一份任何人都能照着实现的规范。

[![License: MIT](https://img.shields.io/badge/License-MIT-1E5C46.svg)](LICENSE)
[![Rubric v1.1](https://img.shields.io/badge/rubric-v1.1-A9854C.svg)](rubric/v1.1.zh-CN.md)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-skill-blue.svg)](SKILL.md)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **这里的 GEO 指生成式引擎优化（Generative Engine Optimization）**，
> 是让 ChatGPT、Perplexity、Google AI Overviews、Gemini、Copilot 引用你，
> 与地理信息、地图、定位无关。

[评分口径](rubric/v1.1.zh-CN.md) · [快速开始](#快速开始) · [查什么](#查什么) ·
[示例输出](#示例输出) · [边界](#边界--这个仓库不做什么) · [研究依据](#权重的研究依据)

---

传统 SEO 问的是「我排第几」。回答引擎不排名——它检索段落、判断这个来源值不值得引用、
然后附上引文。这是另一个问题，失效方式也不一样：一个站可以在 Google 排第 3 却从不被引用，
而一个没什么外链的页面天天被引，因为它的段落干净。

**geo-score 做的是这件事的测量那一半。** 它是一份公开、带版本号的评分口径——
21 项阶梯式检查合计 100 分，另有 4 项不进分母的加分检查——外加一个能跑这套口径的 Claude Code 技能。

**它刻意停在测量。** 见[边界](#边界--这个仓库不做什么)。

## 谁会用

- **站长**：想要一个能按月追踪的数字，和一份具体哪里没做到的清单
- **代理商与顾问**：需要一个站得住、可复核的分数拿给客户看，而不是「相信我，变好了」
- **做 GEO 工具的人**：需要一份共享口径，让不同工具算出来的分是一个意思

## 为什么发布口径，而不是只发一个工具

大多数 GEO 工具给你一个分数，把方法留在自己手里。那个分数是**不可证伪**的——
你没法核对、没法复现、也没法拿去跟任何东西比。

公开的口径是可核对的。你可以不同意某个权重并说出理由；可以自己实现一遍，
看结果跟我们的一致不一致；可以把分数和规范一起交给客户，让他两样都能查。

这就是这里的赌注：**一个所有人都能跑的衡量方式，比一个只有我们能跑的更值钱**——
即使我们卖的是它另一半的修复服务。

## 快速开始

```bash
git clone https://github.com/jianruntech/geo-score.git ~/.claude/skills/geo-score
```

重启 Claude Code，然后：

```
/geo-score audit https://example.com
```

**验证装好了**：不带参数输入 `/geo-score`，应该看到命令列表。
没反应就检查 clone 是不是落在 `~/.claude/skills/` 下、目录里有没有 `SKILL.md`。

**不用 Claude Code 也能用。**[评分口径](rubric/v1.1.zh-CN.md)就是一份普通规范，
可以手工打分，也可以在你自己的工具里实现。

## 查什么

完整规范与各档判据见 **[rubric/v1.1.zh-CN.md](rubric/v1.1.zh-CN.md)**。

| 支柱 | 分值 | 检查项 | 举例 |
|---|:-:|:-:|---|
| 可被抓取 —— *门槛* | 15 | 3 | `robots.txt` 放行检索爬虫、10 个检索 UA 实测都返回 200、正文在服务端渲染的 HTML 里 |
| 可被理解 | 22 | 5 | `Organization` + `WebSite`、带分节链接组的 `llms.txt`、`BreadcrumbList`、页型专用 schema |
| **内容可被引用** | **35** | 5 | 自足答案段、标题匹配人们真实的提问措辞、数据带出处、真实署名、时间信号 |
| 品牌可信 | 18 | 5 | 知识图谱实体、第三方收录、`sameAs` 可解析、视频存在 |
| 问答适配 | 10 | 3 | 内容形态便于摘录、覆盖客户真实会问的问题 |
| *加分项* | *+6* | *4* | `ai.txt`、`speakable`、GEO `<link>` 标签、`llms-full.txt` —— 不进分母 |

内容可被引用权重最高是有意的：回答引擎检索的是**段落**，不是域名。
段落的结构比域名的权威更常起决定作用——这一点和传统 SEO 的直觉相反。

**每个计分项都是阶梯给分**，2–4 档，取证据实际满足的最高档，每一档写的是具体页数而不是「多数」。
加分项不分档。阶梯的作用是让站点能体现部分进展、让复审能看出移动。
在我们那五个站的样本上跨度是 18 分、v1.0 是 17 分——五个同梯队的站，
这个差别不足以证明任何一方（[数据](rubric/calibration-v1.1.zh-CN.md)）。

**其中三项是门槛。** `g.robots`、`g.reachable`、`g.ssr` 任一未拿满，
就绪度总分封顶 40——因为在爬虫拿不到内容之前，其余各项的改动都不会产生效果。

### 分数段

| 0–30 | 31–50 | 51–65 | 66–82 | 83–100 |
|:-:|:-:|:-:|:-:|:-:|
| 未起步 | 起步期 | 成长期 | 基础扎实 | 领先 |

档名描述的是**所处阶段，不是判决**。这是一份用来决定下一步做什么的诊断。
外部基准显示多数商业网站落在 30–55 之间——四十几分是常态，不是警报。

## 示例输出

<details>
<summary><strong>一个小型 Shopify 店铺的 AIV 报告（点开）</strong></summary>

```
AIV Readiness 45 / 98  (rubric v1.1)  ·  normalised 46%  ·  2026-09-08
Band: Early  —  5 points below Growing

Largest gaps
  9 pts  0 of 8 pages open with a self-contained pass…  p2.answer-passages
  6 pts  author is the brand name on 4 of 4 articles    p2.named-author
  5 pts  llms.txt not found                             p1.llms-txt

------------------------------------------------------------------------

Sampled (8 URLs)
  /  /products/kettle  /products/grinder  /products/scale
  /blog/pour-over-ratio  /blog/grind-size  /blog/water-temp  /blog/storage

  Reachable                    15 / 15   ← gate checks
    ✓  robots.txt names all 10 retrieval UAs under Allow        5/5
    ✓  all 10 retrieval UAs return 200, byte-identical to a b…  5/5
    ✓  primary content present without executing JS             5/5

  Understandable               15 / 22
    ✓  sitemap.xml resolves, declared in robots.txt, lastmod …  4/4
    ✗  llms.txt not found                                       0/5
       tier 1 of 4 - tier 2 needs the file to exist and return 200
    ◐  Organization + WebSite sitewide, logo resolves — no sa…  5/6
       tier 3 of 4
    ◐  BreadcrumbList on 3 of 7 nested pages                    2/3
       tier 2 of 3 - tier 3 needs it on half the nested pages or more
    ✓  Product + Offer on 3 of 3 product pages, price and ava…  4/4

  Content Citability            9 / 35
    ✗  0 of 8 pages open with a self-contained passage          0/9
       tier 1 of 4 - tier 2 needs 1 of the 8 sampled pages
    ◐  2 of 8 headings phrased as a task or question            3/7
       tier 2 of 4 - tier 3 needs 4 of 8
    ◐  visible dates on 4 blog posts, none on 4 product pages   3/6
       tier 2 of 3 - tier 3 needs 6 of 8 with dateModified matching
    ◐  11 numeric claims, 2 carry a source                      3/7
       tier 2 of 4 - tier 3 needs 4 or more attributed
    ✗  author is the brand name on 4 of 4 articles              0/6
       tier 1 of 3 - tier 2 needs a real person's name, not the brand

  Brand Credibility             2 / 18
    ◐  listed in 2 directories                                  2/4
       tier 2 of 4 - tier 3 needs 3 or 4
    ✗  no independent coverage found                            0/4
       tier 1 of 4 - tier 2 needs occasional mentions
    ✗  no Wikidata or Wikipedia entity                          0/4
    ✗  sameAs not declared                                      0/3
       tier 1 of 3 — absent scores 0, it is not excluded
    ✗  no official video channel                                0/3
       tier 1 of 3 - tier 2 needs a channel with some content

  Answer Fit                    4 / 8
    ◐  headings present, paragraphs run long                    2/4
       tier 2 of 3 - tier 3 needs lists or tables and shorter paragraphs
    ◐  3 of 10 common buyer questions answered on site          2/4
       tier 2 of 4 - tier 3 needs 6 of 10

  ⊘ p4.cn-engines  not applicable — no Chinese-market presence  (−2 from the denominator)

  Bonus checks: none found (+0, outside the denominator; caps at +6)

Citation performance — not scored
  Whether engines actually cite this site is an outcome, not a property of the site.
  It is reported separately once query tests are run. A readiness score says engines
  *can* cite you; it does not say they *do*.
```

</details>

怎么读这份报告：[`examples/sample-report.md`](examples/sample-report.md)。
每份真实报告必须带四样：**口径版本**、**审计日期**、**距下一档还差几分**、
以及**哪些项退出了分母、为什么**。

## 五份真实审计，以及它们改变了什么

我们写完 v1.0，在对外宣布之前先拿五个公开站点实测。它把 anthropic.com 判成了**危急**——
一个对十个检索爬虫全部返回 200、响应与浏览器逐字节一致、正文 60KB 服务端渲染的站。
那是标定没通过，所以直接发了 v1.1，两版都公开。

| 站点 | v1.0 | **v1.1** | 档 |
|---|:-:|:-:|---|
| [nextjs.org](examples/audits/v1.1/nextjs.org.md) | 49% | **85 / 98 = 87%** | Leading |
| [svelte.dev](examples/audits/v1.1/svelte.dev.md) | 40% | **76 / 98 = 78%** | Solid |
| [stripe.com](examples/audits/v1.1/stripe.com.md) | 51% | **77 / 100 = 77%** | Solid |
| [anthropic.com](examples/audits/v1.1/anthropic.com.md) | 36% | **69 / 98 = 70%** | Solid |
| [mingdao.com](examples/audits/v1.1/mingdao.com.md) | 34% | **69 / 100 = 69%** | Solid |

每一项检查都带可复核的证据：状态码、字节数、十个 UA 的响应比对、
到底是哪一句话算或不算自足答案段，以及一句「为什么落在这一档而不是上一档」。
每份审计末尾都有审计者自己的存疑。[v1.0 的那五份](examples/audits/)原样保留——
它们正是发现问题的证据。

**重跑的时候又发现了第二个设计错误。** 在 v1.1 的第一版规则下，
stripe.com 原始分 77/100、nextjs.org 85/98，却双双显示为 **40%、起步期**——
因为当时的门槛规则是「任一门槛项未拿满即封顶」。nextjs.org 的 `robots.txt` 全文 40 字节、
连一个 User-agent 组都没有，等于全放行，却因此只拿 3/5 并把整站封顶。
这是 v1.0 的错误换了个位置重演：把「没做到最好」当成「根本不通」。
现在封顶只在门槛项得 0 分时触发。

推理过程见[标定记录](rubric/calibration-v1.1.zh-CN.md)，
第一轮定掉的八条歧义见[待决问题](rubric/open-questions.md)。

## 边界 · 这个仓库不做什么

这是大多数工具会略过的部分，所以直说。

**geo-score 只测量，不修复。**

| 不包含 | 为什么 |
|---|---|
| 修复模板 —— `robots.txt`、JSON-LD 代码块、`llms.txt` 样板 | 修复才是真正需要工作量和判断的地方，那是另一个不开源的项目 |
| 内容改写 —— 怎么把一段话写成会被引用的样子 | 同上 |
| 分平台打法 —— 对 Perplexity 和对 Gemini 该分别怎么做 | 同上 |
| 改造路线图 | 同上 |

**其他要说清的限制：**

- **它测的是输入侧的就绪度，不是结果。** 分高只说明引擎**能**引用你，
  至于**会不会**引用，取决于竞争和提问意图，这些外部审计观察不到。
  引用表现单独测、单独报，**不进这 100 分**——见
  [两个分数，不要混在一起](rubric/v1.1.zh-CN.md#两个分数不要混在一起)。
- **品牌可信与具名作者这一项需要人的判断。**「这个作者是不是真实可查的人」
  「这条提及是不是独立的」没法完全自动化。这 24 分左右应当视为辅助判定。
- **阶梯降低分歧，但消不掉分歧。** 每一档都写成 8 个抽样页里的具体页数，
  所以两个审计者在算术上不会分歧；但「这一段算不算自足答案」仍然是判断。
  [已定掉的歧义](rubric/open-questions.md)是我们发现的那些，一定还有别的。
- **重客户端渲染的站会打低分，有时不公平。** 如果内容要 hydration 之后才出现，
  大部分检查读到的是 hydration 之前的 HTML——那也大致就是爬虫看到的，
  所以低分通常是对的，但值得人工复核一遍。
- **引擎行为会变。** 口径带版本号正是为此。旧版本口径算出来的分与当前版本不可比。

## 权重的研究依据

权重是有主张的，但不是拍脑袋。影响最大的两项：

- **[Aggarwal et al., *GEO: Generative Engine Optimization*, KDD 2024](https://arxiv.org/abs/2311.09735)**
  —— 引用来源、加入统计数字、引述专家可以把可见度提升**最多 40%**
  （度量口径是 Position-Adjusted Word Count，不是引用次数）。
  值得注意的是，论文发现**「权威语气」没有显著提升**——
  这正是本口径给结构和出处打分、而不给语气打分的原因。
- **[llms.txt 提案，Answer.AI](https://llmstxt.org/)** —— 可被理解支柱里 `p1.llms-txt` 检查的就是它。

凡是依据我们自己的观察而非公开研究的检查项，口径里都会注明。
如果你有证据表明某个权重不对，
[提一个口径提案](.github/ISSUE_TEMPLATE/rubric_proposal.yml)——这是我们最希望收到的贡献。

## 相关项目

刻意说清这个仓库**不是**什么，方便你选对工具：

| 项目 | 做什么 | 关系 |
|---|---|---|
| [llms-txt](https://github.com/AnswerDotAI/llms-txt) | `llms.txt` 规范本体 | geo-score 检查是否符合它 |
| [yao-geo-skills](https://github.com/yaojingang/yao-geo-skills) | 21 个分类 GEO 技能，偏执行 | 互补——它做生产，这里做测量 |
| [GEOFlow](https://github.com/yaojingang/GEOFlow) | 企业官网 GEO 运营系统 | 范围大得多；AGPL 协议 |

如果你要的是修复而不只是一个分数，上面这些项目覆盖了本仓库刻意排除的那部分。

## 谁在维护

由深圳 **[见润科技](https://www.jianruntech.com)** 建立并维护——
我们为跨境出海企业做 GEO 与 AI 落地。这套口径来自客户项目和优化我们自己产品的过程；
把它公开，是希望 AI 可见度能有一个一致的衡量方式，**包括被那些永远不会成为我们客户的人使用**。

本仓库的商业使用不受限制（MIT），包括用在付费咨询项目里。
不需要获得我们许可，也没有另外的商业授权。

## 参与贡献

最有价值的贡献是**关于权重的证据**。见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 引用

在研究或报告中引用本口径，见 [CITATION.cff](CITATION.cff)。

## 开源协议

[MIT](LICENSE)
