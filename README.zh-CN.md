<p align="right"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>

# geo-score

**一套开源、带版本号的 GEO（生成式引擎优化）评分口径 —— 给任何网站打 0–100 分，
衡量 AI 回答引擎能不能找到、读懂、信任并引用它。**

它发布的这套口径叫 **AIV 分**（AI Visibility，AI 可见度）。5 个支柱、28 项检查、满分 100，
一份任何人都能照着实现的规范。

[![License: MIT](https://img.shields.io/badge/License-MIT-1E5C46.svg)](LICENSE)
[![Rubric v1.0](https://img.shields.io/badge/rubric-v1.0-A9854C.svg)](rubric/v1.0.md)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-skill-blue.svg)](SKILL.md)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **这里的 GEO 指生成式引擎优化（Generative Engine Optimization）**，
> 是让 ChatGPT、Perplexity、Google AI Overviews、Gemini、Copilot 引用你，
> 与地理信息、地图、定位无关。

[评分口径](rubric/v1.0.md) · [快速开始](#快速开始) · [查什么](#查什么) ·
[示例输出](#示例输出) · [边界](#边界--这个仓库不做什么) · [研究依据](#权重的研究依据)

---

传统 SEO 问的是「我排第几」。回答引擎不排名——它检索段落、判断这个来源值不值得引用、
然后附上引文。这是另一个问题，失效方式也不一样：一个站可以在 Google 排第 3 却从不被引用，
而一个没什么外链的页面天天被引，因为它的段落干净。

**geo-score 做的是这件事的测量那一半。** 它是一份公开、带版本号的评分口径——
5 个支柱 28 项检查合计 100 分——外加一个能跑这套口径的 Claude Code 技能。

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

**不用 Claude Code 也能用。**[评分口径](rubric/v1.0.md)就是一份普通规范，
可以手工打分，也可以在你自己的工具里实现。

## 查什么

完整规范与通过条件见 **[rubric/v1.0.md](rubric/v1.0.md)**。

| 支柱 | 分值 | 检查项 | 举例 |
|---|:-:|:-:|---|
| 基础设施 | 20 | 7 | `robots.txt` 放行 AI 爬虫、`llms.txt` 存在且格式正确、内容在服务端渲染的 HTML 里 |
| 结构化数据 | 20 | 6 | `Organization`、带可解析作者的 `Article`、`FAQPage`、`speakable` |
| **内容可引用性** | **25** | 5 | 40–90 词的自足答案段、数字带出处、真实署名、更新时间 |
| 品牌权威 | 20 | 5 | 知识图谱记录、第三方收录、`sameAs` 双向可达 |
| 平台可见度 | 15 | 5 | Search Console 与 Bing 已验证、固定问题集在 ≥3 个引擎上实测过 |

内容可引用性权重最高是有意的：回答引擎检索的是**段落**，不是域名。
段落的结构比域名的权威更常起决定作用——这一点和传统 SEO 的直觉相反。

### 分数段

| 0–40 | 41–60 | 61–75 | 76–90 | 91–100 |
|:-:|:-:|:-:|:-:|:-:|
| 危急 | 偏低 | 良好 | 强 | 领先 |

## 示例输出

见 [examples/sample-report.md](examples/sample-report.md)。
每份真实报告必须带两样：**评分口径版本**和**审计日期**。

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
  支柱 5 通过要求真实跑一遍问题集来部分覆盖，但那个测试是人工的、样本小。
- **支柱 4 和 5 需要人的判断。**「这个作者是不是真实可查的人」「引擎有没有真的引用你」
  没法完全自动化。这 35 分应当视为辅助判定，不是自动判定。
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
- **[llms.txt 提案，Answer.AI](https://llmstxt.org/)** —— 支柱 1 检查的就是它。

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
