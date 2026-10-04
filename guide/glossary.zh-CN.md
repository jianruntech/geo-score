# 术语表

读 geo-score 的 README、报告和各篇指南时会碰到的术语。条目按英文术语的字母顺序排列，与英文版一一对应；
报告和命令行输出本身是英文的，所以每条都先写英文原词。每条说明它是什么意思、在哪里出现，以及去哪一页看更详细的说明。
本页只解释术语和命令，不讲怎么改网站。English: [glossary.md](glossary.md)

[A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [G](#g) · [H](#h) · [J](#j) · [L](#l) · [M](#m) ·
[N](#n) · [O](#o) · [P](#p) · [R](#r) · [S](#s) · [T](#t) · [W](#w)

## A

### AEO（答案引擎优化）

answer engine optimization 的缩写，指让网站内容被答案引擎写进回答、并注明出处的那部分工作，和 GEO 说的基本是同一件事。
量表的分数段分界线取自 GW Content 公开的 AEO 阶梯。

**出现在：** 量表的「档位」一节。**详见：** [量表 v1.1 · 档位](../rubric/v1.1.zh-CN.md#档位)

### AIV、AIV readiness（AIV 就绪度）

AIV 是 AI visibility（AI 可见度）的缩写，指 AI 答案引擎能否找到、读懂、信任并引用一个网站。AIV 就绪度是量表据此给出的
0–100 分，衡量的是引擎「能不能」引用这个站，而不是「有没有」引用。

**出现在：** 终端报告的第一行（`AIV READINESS`）、徽章左半边的文字、量表的标题。
**详见：** [量表 v1.1 · 两个分数，不要混在一起](../rubric/v1.1.zh-CN.md#两个分数不要混在一起)

### Answer engine（答案引擎）

直接用一段文字回答问题、并注明所依据来源的 AI 系统（中文文档里也叫「回答引擎」），比如 ChatGPT 搜索、Perplexity、
Google AI Overviews、Gemini、Copilot；它给的不是一串排好序的链接。它先检索段落，判断哪个来源值得引用，再引用它。

**出现在：** `--help` 的第一句（whether AI answer engines can find, parse, trust and cite it）、README、量表。
**详见：** [README · 这和 SEO 问的不是同一个问题](../README.zh-CN.md#这和-seo-问的不是同一个问题)

## B

### Band（分数段）

0–100 分划成的五段：未起步（0–30）、起步期（31–50）、成长期（51–65）、基础扎实（66–82）、领先（83–100），量表里称为「档位」。
分数段描述的是所处阶段，不是判决；它按门槛封顶之后的分数来定。

**出现在：** 终端报告里分数的旁边，下一行是离下一段还差几分（`N points to <band>`）；JSON 的 `band` 字段（CLI 输出英文段名）；
徽章，颜色随分数段变化；`diff` 和 `--fail-on-drop`（分数段下降）。**详见：** [量表 v1.1 · 档位](../rubric/v1.1.zh-CN.md#档位)

### Baseline（基线）

拿来和新分数对比的那份旧 JSON 报告。`--baseline REPORT` 在这份报告抽过的页面上重新打分，并逐项列出和它相比哪里变了。

**出现在：** `--baseline REPORT`；配合 `--fail-on-drop`，有检查项丢分、门槛项降到 0 或分数段下降时以退出码 4 退出；
GitHub Action 的 `baseline` 输入，以及 `delta`、`dropped-checks` 两个输出。
**详见：** [CLI 说明 · 对比两份报告](../cli/README.zh-CN.md#对比两份报告)

### Biggest gaps（最大缺口）

升到下一档能多拿分最多的三个检查项，得 0 分的门槛项永远排在最前。每行写明下一档加几分、离满分还差几分；
完整报告还会引用量表对下一档的要求（`needs: …`）。

**出现在：** 终端报告和 `--brief`；MCP 工具 `score_site` 也按同样的顺序列出缺口。
**详见：** [量表 v1.1 · 报告形态](../rubric/v1.1.zh-CN.md#报告形态)

### Bonus（加分项）

四项 `b.` 开头的检查（`b.llms-full`、`b.ai-txt`、`b.geo-link`、`b.speakable`），不分档，只有做到和没做到。得分加进就绪度，
最多加 6 分，但不进分母，0–100 分也不会因此超过 100。

**出现在：** 报告里的 `+N bonus (outside the denominator)`；JSON 的 `bonus_awarded` 字段，以及 `checks` 里的 `b.` 条目。
**详见：** [量表 v1.1 · 打分规则](../rubric/v1.1.zh-CN.md#打分规则)第 5 条

### Bot challenge（人机验证页）

防爬服务（AWS WAF、Akamai、Cloudflare 等）拿来顶替网站页面的验证页，只有真正执行它脚本的浏览器才能通过。
它从不被当作网站内容打分：被验证页顶替的页面移出抽样，整站只返回验证页时不打分。

**出现在：** 注释 `Scored on N of M sampled pages; …`；整站都是验证页时以退出码 2 退出，报错以
`bot challenge served to a browser user-agent` 开头，`--json` 下类型为 `bot_challenge`。
**详见：** [排查指南 · bot_challenge](troubleshooting.zh-CN.md#bot_challenge返回的是人机验证页不是网站内容)

### Branded question（提到品牌的问题）

追踪的问题里直接点了你品牌名的那些，比如「acme vs rival」，引擎几乎每次都会引用你。`watch` 会把这类问题标出来，
不计入标题引用率，单独列一行。

**出现在：** `queries.csv` 可选的 `branded` 列（`auto`、`yes` 或 `no`）；运行文件里的 `brand_in_query`；这类问题超过三成时
`watch check` 给出的警告。**详见：** [watch 方法说明 · 提到品牌的问题](watch-methodology.zh-CN.md#3-提到品牌的问题)

### By question（逐个问题）

追踪报告里按问题看的视图。对每个追踪的问题，它统计拿到几条回答，其中几条引用或提到了你、几条引用或提到了每个追踪的竞品、
几条一个追踪的品牌都没提到、几条[联网搜索过](#searched联网搜索过)，以及被引用次数最多的追踪品牌；后者只在问题至少有 4 条回答、
且这个品牌多于其他所有品牌时才给出。每个值都是计数，不是比率。

**出现在：** `watch report` 里的 `Who is named for each question` 表；运行文件、JSON 报告和 MCP `report` 工具里的 `summary.by_question`。
**详见：** [watch 方法说明 · 单位](watch-methodology.zh-CN.md#1-单位一条回答按问题成簇)

## C

### Check、check id（检查项与检查项 id）

检查项是量表里的一条判据：测什么、分几档、为什么对被检索重要。id 是它固定不变的名字，由前缀加短名组成，例如
`p2.freshness`：`g.` 是门槛项，`p1.` 到 `p4.` 依次对应可被理解、内容可被引用、品牌可信、问答适配四个支柱，`b.` 是加分项。

**出现在：** `--explain`；JSON 的 `checks[].id`；`--assert`；SARIF 的规则 id 和 JUnit 的测试名；MCP 提示词 `explain_check`。
检查项 id 属于公开契约（[STABILITY.md](../STABILITY.md#public-contracts)，英文）。**详见：** [量表 v1.1](../rubric/v1.1.zh-CN.md)

### Citation（引用）

回答链接到了你拥有的网址，就算引用了你：你的某个域名（含子域名），或者你声明过的网址前缀，比如你在别家平台上的店铺页。
引擎到底有没有引用你是一项结果，由第二、三级在就绪度旁边单独报告，从不加进分数。

**出现在：** 加 `--ask` 时报告下方的引用结果；JSON 的 `citation` 对象；`watch report` 的 `cited` 列。
**详见：** [README · 第二、三级](../README.zh-CN.md#第二三级--ai-到底有没有引用你)、
[量表 v1.1 · 两个分数，不要混在一起](../rubric/v1.1.zh-CN.md#两个分数不要混在一起)

### Cited rate（引用率）

在拿到的回答里，引用了你的回答占多少，附 95% 区间：每个问题只答一次时用 Wilson 区间，
一个问题有多条回答时按问题做自助法重抽样。标题引用率只算没有提到品牌的问题。

**出现在：** `watch report` 里的 `Cited in N% of answers …`；`watch runs` 列出的标题引用率；运行文件的 `summary.headline`。
**详见：** [watch 方法说明 · 单位](watch-methodology.zh-CN.md#1-单位一条回答按问题成簇)

## D

### Denominator（分母）

本次运行观测到的检查项的满分之和，0–100 分就是拿得分除以它算出来的。没观测到的检查项移出分母，而不是记 0 分；加分项从不进分母。

**出现在：** 报告页脚的 `N checks left the denominator` 和图例里的 `⊘ not measured (left the denominator)`。
**详见：** [量表 v1.1 · 打分规则](../rubric/v1.1.zh-CN.md#打分规则)第 3 条

### Diff（对比）

把两次保存下来的结果放在一起比。`geo_score.py diff BEFORE AFTER` 逐项对比两份第一级 JSON 报告（状态有 `up`、`down`、
`same`、`became unobservable`、`became observable`，两份报告都没观测到的检查项则是 `unobservable`）；
`watch diff [A] [B]` 对比两次追踪运行，默认取最近两次，做配对检验并给出结论：`change`、`within noise`、
`too few questions to tell` 或 `not measured`。

**出现在：** `diff --format text|md|json`（JSON 遵循 `schema/diff.v1.json`）；`watch diff`；MCP 工具 `diff`（对比追踪运行）。
两者加上 `--fail-on-drop`，发现下降时都以退出码 4 退出。
**详见：** [CLI 说明 · 对比两份报告](../cli/README.zh-CN.md#对比两份报告)、
[watch 方法说明 · 比较两次运行](watch-methodology.zh-CN.md#4-比较两次运行逐行的配对检验)

## E

### Engine（引擎）

第二、三级接入的答案引擎，也就是各家开了联网搜索的 API，用引擎 id 称呼：`chatgpt-api`、`perplexity-api`、`gemini-api`、
`claude-api`，或者你给某个 OpenRouter 模型起的 id。API 的回答不等于消费端 App 的回答，所以 API 渠道的结果只和 API 渠道比。

**出现在：** `geo-score-watch.json` 的 `engines`；`watch run --engines`；追踪报告的 By engine 表；MCP 工具 `ask` 和 `run` 的
`engines` 参数。**详见：** [README · 第二、三级](../README.zh-CN.md#第二三级--ai-到底有没有引用你)

### Evidence（证据）

检查项读数背后、别人也能复核的观察：状态码、字节数、符合或不符合要求的那一句话。没有证据的判定不成立。

**出现在：** `--explain`；JSON 的 `checks[].evidence` 和 `tier_reason`，没观测到的检查项则是 `reason`；SARIF 和 JUnit 里的消息。
**详见：** [量表 v1.1 · 打分规则](../rubric/v1.1.zh-CN.md#打分规则)第 8 条

## G

### Gate（门槛项）

「可被抓取」支柱下的三个检查项：`g.robots`（robots.txt 放行检索爬虫）、`g.reachable`（检索 UA 实测可达）和 `g.ssr`
（正文服务端可见）。门槛项和其他检查项一样计分，得 0 分时还会压低总分的上限，见下一条「门槛封顶」。

**出现在：** 报告开头的 `GATE AT ZERO — …`；`--fail-on-gate`，等同于 `--assert 'g.*>0'`；SARIF 的 `error` 级别。
**详见：** [量表 v1.1 · 可被抓取](../rubric/v1.1.zh-CN.md#可被抓取--15-分)

### Gate cap（门槛封顶）

任一门槛项得 0 分时，0–100 分封顶 40；门槛项落在中间档只是普通扣分，观测不到的门槛项也不会触发封顶。封顶是一个上限，即
`min(分数, 40)`，在算进加分项之后才套用：本来能得 40 分及以上的站显示为 40，本来就不到 40 的站保留自己更低的分数。

**出现在：** JSON 的 `gate_capped` 字段；徽章上的 `(gate capped)`；报告里的
`the score cannot exceed 40 while a gate is at zero`。被封顶的站可能恰好是 40 分，因而能通过 `--fail-under 40`；
`--fail-on-gate` 则让所有被封顶的站失败。**详见：** [排查指南 · 门槛项得 0 分](troubleshooting.zh-CN.md#分数被封顶在-40有门槛项得-0-分)

### GEO（生成式引擎优化）

Generative Engine Optimization 的缩写：让 ChatGPT、Perplexity、Google AI Overviews、Gemini、
Copilot 这类生成答案的 AI 引擎在回答里引用你的网站。和地理、地图无关。

**出现在：** 工具名和 README。**详见：** [README · 这和 SEO 问的不是同一个问题](../README.zh-CN.md#这和-seo-问的不是同一个问题)，
以及论文 [GEO: Generative Engine Optimization（KDD 2024）](https://arxiv.org/abs/2311.09735)

## H

### Hand audit（人工审计）

由人按量表逐一判读全部 21 个检查项，每一档都附上证据；不适用于该站的检查项标为 `not_applicable`。
CLI 和人工结果的一致度，就是拿已发布的人工审计来测的。

**出现在：** `examples/audits/v1.1/`；README 里 CLI 和人工审计的对比数字。**详见：** [VALIDITY.zh-CN.md](../benchmark/VALIDITY.zh-CN.md)

### Heuristic（启发式判断）

量表用文字描述的判断，CLI 用近似的办法去读，这类检查项就是启发式的；与之相对，有些检查项按规则直接读文件、状态码或标记。
启发式检查项是 `g.reachable`、`g.ssr`、`p2.` 各项、`p3.video` 和 `p4.answer-shape`，它们和人工审计一致的比例低于按规则读的检查项。

**出现在：** CLI 说明里的可信度表；README 里 CLI 与人工审计的对比数字。
**详见：** [CLI 说明 · 每个检查项能信几分](../cli/README.zh-CN.md#每个检查项能信几分)

## J

### JUnit

CI 系统用来展示测试结果的 XML 格式。`--junit FILE` 为每个检查项写一个测试：得 0 分的失败，没观测到的跳过，拿到部分分的通过。

**出现在：** `--junit FILE`。**详见：** [CLI 说明 · 参数](../cli/README.zh-CN.md#options)

## L

### Leaderboard（榜单）

geo-score 的公开基准：一批知名网站按行业分组，全部用同一套量表、同一个公开工具打分，每个站的完整报告和表格一起公开。
它是某一天的测量结果，不是契约，数据里记着所用的工具版本和测量日期。

**出现在：** [jianruntech.com/leaderboard/zh](https://www.jianruntech.com/leaderboard/zh)；`benchmark/README.md`；
`benchmark/` 下的 `results.json`、`results.csv`、`checks.csv` 和 `raw/`。
**详见：** [benchmark/README.md](../benchmark/README.md)（英文）、[STABILITY.md · Benchmark data](../STABILITY.md#benchmark-data)（英文）

### Levels 1, 2 and 3（第一、二、三级）

geo-score 的三种用法：第一级按量表给就绪度打分，免费、不要 Key；第二级用你的 API Key 把一个问题拿去问各个引擎一次；
第三级每周追踪一组固定的问题。第二、三级测的是引用，从不加进分数。

**出现在：** `geo_score.py URL`（第一级）；`--ask QUESTION` 和 `watch ask`（第二级）；`watch run`、`watch report`、
`watch diff`（第三级）；MCP 工具表里的「级别」一列。第二、三级需要 `cli/geo_watch.py` 和 `cli/geo_score.py` 放在一起。
**详见：** [README · 一个工具，三级用法](../README.zh-CN.md#一个工具三级用法)

## M

### MCP prompt（MCP 提示词）

MCP 服务预先写好、由你自己发起的工作流，比如在 Claude Code 里当斜杠命令用：`audit_site`、`check_citations`、`weekly_watch`、
`compare_runs`、`explain_check`。只有它要调用的工具都开着时，服务才提供这个提示词。

**出现在：** `prompts/list`；Claude Code 里的 `/mcp__geo-score__audit_site`。**详见：** [MCP 指南 · 提示词](mcp.zh-CN.md#提示词)

### MCP resource（MCP 资源）

MCP 服务开放给客户端读取的数据。开着 `score_site` 工具时，`geo-score://rubric/v1.1` 里是打分器实际执行的每个检查项
及其分值和档、分数段和封顶规则；开着 `report` 工具时，还有资源模板 `geo-score://runs/{run_id}`，用来读某次保存的运行的摘要。

**出现在：** `resources/list`；提示词 `explain_check` 会附上量表资源。**详见：** [MCP 指南](mcp.zh-CN.md)

### MCP server（MCP 服务）

`geo-score-mcp`（在克隆的仓库里是 `geo_score.py mcp`）：一个走 stdio 的本地服务，让 Agent 通过 Model Context Protocol 用上全部三级。
它和命令行是同一份代码，加 `--read-only` 就成了一个花不了钱的服务。

**出现在：** `geo-score-mcp` 及其参数 `--toolsets`、`--tools`、`--exclude-tools`、`--read-only`、`-c CONFIG`。
**详见：** [MCP 指南](mcp.zh-CN.md)

### MCP tool（MCP 工具）

MCP 服务让 Agent 调用的功能：`score_site`（第一级，免费）、`ask`（第二级）、`run`、`list_runs`、`report`、`diff`（第三级），
以及 `status`。只有 `ask` 和 `run` 会花钱，而且只能用你交给服务的 Key。

**出现在：** `tools/list`；README 和 MCP 指南里的工具表。**详见：** [MCP 指南 · 工具](mcp.zh-CN.md#工具)

### Mentioned（被提及）

回答正文里出现了你的品牌名、某个别名或你的域名，不管有没有链接到你。中文、日文、韩文名按包含匹配，其他名字只按整词匹配。

**出现在：** 追踪报告的 `mentioned` 列；JSON `citation` 对象里的 `mentioned_count`。
**详见：** [README · 第二、三级](../README.zh-CN.md#第二三级--ai-到底有没有引用你)

## N

### Named first（最先被提到）

追踪报告里，最先提到某个品牌（在配置里所有品牌中）的回答数，分母是至少提到配置里一个品牌的回答数。先后看每条回答的
`mention_order`：取每个品牌的名字、别名或域名最早的一处匹配，匹配规则与[被提及](#mentioned被提及)相同。两个品牌第一次被提到的位置
相同时都没有名次；配置里没列的品牌看不见，所以在你追踪的品牌里排第一，不一定是在回答里排第一。它读的是保存下来的回答，即前 20,000 个字符。

**出现在：** `watch report` 里 `By engine` 和 `Share of voice` 两张表的 `named first (tracked)` 列；运行文件里每条回答及其竞品的 `mention_order`；
`summary.engines` 和 `summary.share_of_voice` 每一行的 `named_first` 与 `any_named`。
**详见：** [watch 方法说明 · 单位](watch-methodology.zh-CN.md#1-单位一条回答按问题成簇)

### Normalised score（归一化分）

也就是 0–100 分本身：就绪度（得分加上加分项）除以可观测满分，乘以 100 后四舍五入，最高 100。有门槛项得 0 分时，再封顶 40。

**出现在：** 报告开头的 `N / 100`；JSON 的 `normalised`、`readiness`、`observable_max` 字段。分数段、`--fail-under` 和徽章读的都是它。
**详见：** [量表 v1.1 · 打分规则](../rubric/v1.1.zh-CN.md#打分规则)、[schema/report.v2.json](../schema/report.v2.json)

### Not observed、unobservable（未测、不可观测）

本次运行观测不到的检查项：显示为 `—`（⊘），状态是 `unobservable` 并附 `reason`，它移出分母，而不是记 0 分。
`p3.listings`、`p3.mentions`、`p4.question-coverage` 需要站外搜索或人工判断，CLI 从不给它们打分；其他检查项可能某一次观测不到，
比如 Wikidata 没有回应、抽到的页面都不是嵌套页，或者十个检索爬虫里得到任何应答的不到一半。

**出现在：** 报告页脚的 `Needs off-site search or judgement:` 和 `Not observable this run:` 两行。`--assert` 会跳过这类检查项，
JUnit 记为跳过，`diff` 显示为 `became unobservable`，从不算下降。量表的第三种状态 `not_applicable`（不适用）同样移出分母；
CLI 只输出 `scored` 和 `unobservable`。**详见：** [排查指南 · 检查项显示 —](troubleshooting.zh-CN.md#某个检查项显示--而不是分数)

## O

### Observable max（可观测满分）

报告里写出来的分母，即 `Scored X / Y observable` 中的 Y。只有 21 个计分检查项全部观测到时它才是 100，CLI 的一次运行永远到不了，
因为其中三项需要站外搜索或人工判断。

**出现在：** 报告页脚；JSON 的 `observable_max` 字段。**详见：** [量表 v1.1 · 打分规则](../rubric/v1.1.zh-CN.md#打分规则)第 3 条

### Opt-out token（选择退出令牌）

写在 robots.txt 里、看上去像 user-agent 的名字，但不对应任何爬虫，也不发请求，比如 `Google-Extended`、`Applebot-Extended`；
它表达的是内容能不能用于 AI 训练或作为生成答案的依据。量表不给它计分。

**出现在：** 量表的 `g.robots` 检查项（它只看检索爬虫）；AI 爬虫一览。
**详见：** [AI 爬虫 user-agent 一览](../reference/ai-crawlers.md#the-distinction-that-matters-most)（英文）

### Outside the score（分数之外）

报告观测到、但不计分的内容：不影响任何一档、任何分数和档位。目前有两项。**Pages robots.txt blocks** 拿首页、抽样页面和
sitemap 的前 200 个 URL，对照每个检索爬虫遵守的规则，按 RFC 9309 的读法判断（匹配上的规则里最长的那条说了算）；
**Rules read differently** 列出 Python `urllib.robotparser` 和许多老检查工具的「第一条匹配」读法（按文件顺序，第一条前缀匹配的规则说了算）
得出相反结论的页面。**Links in the server HTML** 统计不运行 JavaScript 的爬虫能跟的链接，首页链接到本站页面少于 3 个时给出提示，
并列出没有任何一个抓到的页面链接到的 sitemap URL；只搜索了抓到的页面。

**出现在：** 终端报告页脚之后的 `Outside the score (observed, never scored)`、MCP `score_site` 摘要和 Action 的 job summary；
JSON 的 `access` 字段。**详见：** [CLI 参考 · 分数之外](../cli/README.zh-CN.md#分数之外)

## P

### Pillar（支柱）

量表把检查项分成的五组：可被抓取（15 分，即三个门槛项）、可被理解（22 分）、内容可被引用（35 分）、品牌可信（18 分）、
问答适配（10 分）。终端报告按支柱分组列出检查项，并给出每组的合计。

**出现在：** 终端报告和 `--brief`，用的是英文支柱名 Reachable、Understandable、Content Citability、Brand Credibility、
Answer Fit；SARIF 每条规则的 `pillar` 属性。**详见：** [README · 查什么](../README.zh-CN.md#查什么)

### Pinned sample（固定抽样）

不让运行自己抽样，而是指定页面。`--urls FILE` 只评列出的页面（最多 8 个，都得在被评的网站上）；`--urls-from REPORT` 或
`--baseline REPORT` 评一份旧 JSON 报告抽过的页面，这样对比出来的是网站的变化，而不是抽样的差异。

**出现在：** `--urls`、`--urls-from` 和 `--baseline`；MCP 工具 `score_site` 的 `urls` 参数；报告里随之写明 `sample_source: pinned`。
**详见：** [排查指南 · 两次运行分数差了几分](troubleshooting.zh-CN.md#两次运行分数差了几分)

### Points（分值）

检查项的权重就是它的满分：21 个计分检查项的满分合计 100，四个加分项合计 6。一次运行给某个检查项的分，就是它达到的那一档的分值。

**出现在：** 每个检查项旁边的 `3/5`；JSON 的 `checks[].points` 和 `max`；`--assert` 里的取值，一个数或 `max`。
**详见：** [量表 v1.1](../rubric/v1.1.zh-CN.md)

### Pooled report（合并报告）

把多次保存下来的 watch 运行当成一组回答来统计：最近 N 天的运行，或一段运行 ID 范围内的运行。只有问的是同一组问题、每题问的次数相同、用的是同样的引擎和模型、
`country` 相同、品牌域名也相同的运行才会被合并；否则命令拒绝合并，并列出不一致的运行。它的区间把同一个问题的全部回答（不论来自哪次运行）
当作一簇，所以合并最多只能把区间收窄到问题数允许的程度。它描述的是一段时间，不是对变化的检验。

**出现在：** `watch report --since DAYS` 或 `--runs A..B`；MCP 的 `report` 工具带 `since`；`schema/watch.v1.json` 里的 `$defs/pooled`。
**详见：** [watch 方法说明 · 一次提问、一天、一个月](watch-methodology.zh-CN.md#8-一次提问一天一个月)

### Probe（探测）

`g.reachable` 用检索爬虫的 user-agent 字符串发出的实时请求：十个 UA 各发一遍，最多测三个抽样页面；
遇到超时、断连、429 或 5xx 会再试一次。某个爬虫在其中任一页面上被 HTTP 错误拒绝（403，或重试后仍是 429、5xx），
就算被拦；在所有页面上都完全没有应答的爬虫不计入；十个里得到任何应答的不到一半时，这一项记为未测。
只有被拒绝才会让这个门槛项得 0 分：十个里有超过一半被拒绝时，它才记 0 分。
探测没有经过身份验证：它从审计方自己的地址（也就是运行 geo-score 的那台机器）发出，而不是从厂商公布的 IP 段发出，
所以按 IP 段或反向 DNS 核验爬虫的防火墙可能拒绝探测，却照常放行真正的爬虫。

**出现在：** `g.reachable` 的证据：被拒绝的爬虫列在 `Not reached — …` 里，所有页面都没有应答的列在
`No answer on any page, so not counted: …` 里，后面再加一句
`(Unverified probes: vendor user-agent strings sent from this machine's address.)`；应答的太少时，`reason` 以
`Only N of 10 retrieval user-agents got an answer` 开头。
**详见：** [AI 爬虫 user-agent 一览](../reference/ai-crawlers.md)（英文）、[量表 v1.1 · 检索 UA 实测可达](../rubric/v1.1.zh-CN.md#检索-ua-实测可达--5--greachable)

## R

### Resolution（分辨力）

一套 watch 计划在运行之前就能知道的事：两次运行之间至少要有 k 个问题朝同一方向变动，`watch diff` 才可能判定变化。
E 个引擎时 diff 检验 E + 1 行（只有一个引擎时是一行），k 是满足 行数 × 2 / 2^n < 0.05 的最小 n：一个引擎 6，两个引擎 7，三到五个引擎 8。
多加问题有用；多加引擎会抬高 k；每题多问几次不会降低 k。

**出现在：** `watch run --dry-run` 和 MCP `run` 工具带 `dry_run` 时打印的 `resolution:` 一行；问题集少于 k 个问题时，还会加上
`this plan cannot detect a change`。
**详见：** [watch 方法说明 · 一次提问、一天、一个月](watch-methodology.zh-CN.md#8-一次提问一天一个月)

### Retrieval crawler（检索爬虫）

为回答用户的问题而抓取页面的爬虫：有的给 AI 搜索建索引，有的在用户提问时当场替人去取。
`g.robots` 和 `g.reachable` 只看其中十个：OAI-SearchBot、ChatGPT-User、Claude-SearchBot、Claude-User、PerplexityBot、Perplexity-User、Googlebot、Bingbot、
Applebot、Amazonbot。

**出现在：** `g.robots` 和 `g.reachable` 的证据。**详见：** [AI 爬虫 user-agent 一览](../reference/ai-crawlers.md#the-distinction-that-matters-most)（英文）

### Rubric（量表）

每个分数背后公开发布的规范：每个检查项的档和分值、分数段、门槛封顶和加分上限。它只说测什么、为什么测，从不说怎么修；
`rubric/v1.1.md` 给人读（中文版是 `rubric/v1.1.zh-CN.md`），`rubric/v1.1.json` 给程序读。

**出现在：** 终端报告页脚的链接；`--explain` 在没拿满分的检查项下给出的链接；MCP 资源 `geo-score://rubric/v1.1`。
**详见：** [量表 v1.1](../rubric/v1.1.zh-CN.md)

### Rubric version（量表版本）

打分所依据的量表版本，目前是 v1.1；只有同一量表版本的分数才能相互比较。它和工具版本（这里是 1.5.0，遵循语义化版本）各自变动，互不牵连。

**出现在：** JSON 的 `rubric_version` 和 `tool`（`geo-score-cli/1.5.0`）字段；页脚的 `rubric v1.1`；`--version`。
`diff` 和 `--baseline` 遇到按另一量表版本评出的报告会拒绝，以退出码 2 退出。**详见：** [STABILITY.md](../STABILITY.md)（英文）

## S

### Sample（抽样）

一次运行实际评分的页面：默认 8 个，包括首页，其余从 sitemap 和网站的链接里抽；网站页面不够时就少于 8 个。
内容类检查项都按抽样页面计数，所以换一批页面，分数就可能差几分。

**出现在：** `--sample N`（至少 1）；JSON 的 `sampled_urls` 字段；有页面出错或是人机验证页时，注释里的
`Scored on N of M sampled pages`。**详见：** [量表 v1.1 · 打分规则](../rubric/v1.1.zh-CN.md#打分规则)第 1 条、
[排查指南 · 两次运行分数差了几分](troubleshooting.zh-CN.md#两次运行分数差了几分)

### Sample source（抽样来源）

这次抽样从哪里来：`sitemap`；`homepage and section links (no sitemap reachable)`，即拿不到 sitemap，改从首页和栏目页的链接里抽；
或者 `pinned`，即页面是指定的。它说的是页面怎么选出来的，不是选了哪些：来源相同的两次运行，抽到的页面照样可能不同。

**出现在：** JSON 的 `sample_source` 字段；注释 `Sampled N of the M pages asked for: no more were found (sample source: …)`。
**详见：** [schema/report.v2.json](../schema/report.v2.json)

### SARIF

代码扫描工具读取静态分析结果用的标准格式。`--sarif FILE` 写出 SARIF 2.1.0：每个检查项一条规则，每个没拿满分的检查项一条结果，
门槛项得 0 分为 `error`，其他检查项得 0 分为 `warning`，拿到部分分为 `note`。

**出现在：** `--sarif FILE`；GitHub 代码扫描。**详见：** [CLI 说明 · 参数](../cli/README.zh-CN.md#options)

### Searched（联网搜索过）

引擎给出某条回答前有没有联网搜索，从运行保存的内容里读：服务商报告了搜索、给出了搜索词，或回答引用了网址，就算「是」；
OpenAI、Gemini 或 Anthropic 的回答这几样都没有，就算「否」；Perplexity 和 OpenRouter 记为「未知」，因为它们的 API
每次调用都会搜索，或者不说明。没有联网搜索就给出的回答，不可能引用任何东西。

**出现在：** `watch report` 逐题表里的 `searched yes/no/unknown` 列；运行文件里的 `summary.by_question[].searched`。
**详见：** [By question（逐个问题）](#by-question逐个问题)

### Sector median and the n<10 rule（行业中位数与 n<10 规则）

榜单上某个行业里已打分站点的分数中位数，基准的 README 同时给出 95% 自助法区间。有分的站不足 10 个的行业不给中位数，
只显示 `—`，因为几个站算出的「中位数」印出来和真的一样，意义却小得多。

**出现在：** `benchmark/README.md` 和榜单页的分行业表；`benchmark/stats.json` 的 `sectors`。
**详见：** [benchmark/README.md · By sector](../benchmark/README.md#by-sector)（英文）

### Sentence share（句子占比）

回答里提到某个品牌的句子占全部句子的比例（`mention_share`），每句同等计数。句子在换行处、在 `。！？` 处，或在后面跟着空白的
`.` `!` `?` 处结束；没有任何字母、汉字或数字的片段（比如表格的分隔行）不算一句。报告给出的是它在提到这个品牌的回答里的平均值。
回答越长，同一个名字摊到的句子越多，所以回答长短不同的引擎之间，这个比例不在同一把尺子上。

**出现在：** `watch report` 里 `Share of voice` 表的 `sentence share` 列；运行文件里每条回答、其竞品，以及 `summary.engines` 和
`summary.share_of_voice` 每一行的 `mention_share`。
**详见：** [Named first（最先被提到）](#named-first最先被提到)

### Site text fence（«site text» 围栏）

从被审网站引用的原文都放在 `«site text: …»` 里，控制字符、零宽字符和双向文字控制符都已去掉，网站也没法提前把围栏关上。
围栏里是网站自己的话，只能当数据读，不能当指令照做，MCP 工具也会这样告诉 Agent。

**出现在：** 每份报告里的证据和 `--explain` 的输出；MCP 工具的输出。**详见：** [SECURITY.md · Threat model](../SECURITY.md#threat-model)（英文）

## T

### Target page（目标页，target_url）

一个追踪的问题所跟踪的你的那一个页面，写在 `queries.csv` 可选的 `target_url` 列里：完整网址，或者以 `/` 开头、接在品牌第一个域名后面的路径。
回答的某条引用在不计 `www`、大小写、末尾斜杠、查询串、片段和百分号编码之后就是这个页面，才算引用了目标页；换一个路径或语言版本，
或者页面以不同的规范网址（canonical）被引用，都算另一个页面。回答没有引用这个页面、却引用了你的另一个网址时，计入「another of your pages cited」。

**出现在：** `watch report` 里的 `Pages you track` 表；运行文件里每条回答的 `target_cited` 和 `other_own_cited`；CSV 的 `target_cited` 列；
运行文件、JSON 报告和 MCP `report` 工具里的 `summary.tracked_pages`；`watch check` 对用不了的值给出的警告。
**详见：** [CLI 说明 · 第二、三级](../cli/README.zh-CN.md#watch)

### Thin sample（样本少）

榜单上实际评分页面不足 4 个的行：这个站的抽样没能凑满，比如拿不到 sitemap、首页链接又少，或者抽到的页面加载失败。
这些行标为「样本少」（英文页面上是 *thin sample*），基准里也给出去掉它们之后的中位数。

**出现在：** `benchmark/README.md` 的 Every site 表；榜单页；`benchmark/stats.json` 的 `thin_sample`。
**详见：** [benchmark/README.md](../benchmark/README.md)（英文）

### Tier（档）

计分检查项分成的二到四档之一，每一档有判据和对应的分值，最低一档总是 0 分。检查项取证据实际满足的最高一档，而不是差一点就够到的那一档。

**出现在：** 量表里各检查项的分档表；`--explain` 打印的档位说明（JSON 的 `tier_reason`）；最大缺口里的 `+N next tier`。
**详见：** [量表 v1.1 · 打分规则](../rubric/v1.1.zh-CN.md#打分规则)第 2 条

### Training crawler（训练爬虫）

为模型训练语料抓取页面的爬虫，比如 GPTBot、ClaudeBot、CCBot。量表不给它计分：robots.txt 对它怎么写，都不影响任何检查项。

**出现在：** 量表的 `g.robots` 检查项（它只看检索爬虫）；AI 爬虫一览。
**详见：** [AI 爬虫 user-agent 一览](../reference/ai-crawlers.md#the-distinction-that-matters-most)（英文）

## W

### Watch run（追踪运行）

执行一次 `watch run`：把 `queries.csv` 里的每个问题拿去问每个配了 Key 的引擎，各问 `runs` 次，结果存成
`.geo-score/watch/runs/` 下的一个运行文件，附一本账，记下请求数、token、搜索次数和花费。`watch run --dry-run` 只打印计划和上限，
不调用任何接口。

**出现在：** `watch run`、`watch runs` 和 `watch report [RUN]`；MCP 工具 `run`、`list_runs`、`report`；配置里的 `max_calls` 和
`budget_usd` 限制一次运行。运行文件遵循 `schema/watch.v1.json`。
**详见：** [README · 第二、三级](../README.zh-CN.md#第二三级--ai-到底有没有引用你)、[CLI 说明 · 第二、三级](../cli/README.zh-CN.md#watch)
