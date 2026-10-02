<p align="right"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>

# geo-score 命令行

按 [AIV 量表 v1.1](../rubric/v1.1.zh-CN.md) 给网站打分；配上你自己的 API Key，还能实测并追踪 AI 引擎有没有引用它。
需要 Python 3.8+，只用标准库，什么都不用装。第一级只要 `geo_score.py` 一个文件；第二、三级还要把同一版本的
`geo_watch.py` 放在它旁边。

```bash
curl -sL https://raw.githubusercontent.com/jianruntech/geo-score/v1.6.0/cli/geo_score.py \
  | python3 - yoursite.com
```

三级都在 PyPI 上的同一个包里：`uvx geo-score@1.6.0 yoursite.com` 不安装直接运行，`pipx install geo-score==1.6.0`
装好 `geo-score` 和 `geo-score-mcp` 两个命令。访问不了 PyPI 时，发布的 wheel 包用法一样：
`pipx install https://github.com/jianruntech/geo-score/releases/download/v1.6.0/geo_score-1.6.0-py3-none-any.whl`。

## <a id="options"></a>参数

| 参数 | 作用 |
|---|---|
| `--brief` | 只看各支柱合计和最大的三个缺口，一张截图装得下 |
| `--explain`, `-e` | 列出每个检查项背后的证据，而不只是分数 |
| `--json` | 机器可读的输出，符合 [`schema/report.v2.json`](../schema/report.v2.json) |
| `--json-out FILE` | 同时把这份 JSON 写进 FILE，和屏幕上的报告出自同一次运行 |
| `--sarif FILE` | 同时写一份 [SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)：每个检查项一条规则，每个没拿满分的检查项一条结果（门槛项得 0 分为 `error`，其他检查项得 0 分为 `warning`，拿到部分分为 `note`）。每条结果指向 `--json-out` 报告里该检查项所在的那一行（没有这份报告时指向 SARIF 文件本身），并在消息里写明被评的网站，这是 GitHub 代码扫描的要求 |
| `--junit FILE` | 同时写一份 JUnit XML：每个检查项一个测试。得 0 分的失败，CLI 观测不到的跳过，拿到部分分的通过 |
| `--sample N` | 抽多少个页面，至少 1 个（默认 8，即量表规定的数目） |
| `--timeout SECONDS` | 每个请求最多等服务器多久，超过就算没有回应（默认 15，最多 300）。连不上的网站会马上失败并说明原因：域名解析不了、连接被拒绝、TLS 握手失败，这几种都不重试 |
| `--urls FILE` | 不抽样，只评这些页面：每行一个 URL（或 `/pricing` 这样的路径），可以用 `#` 写注释，最多 8 个，都必须在被评的网站上。报告里会写 `sample_source: pinned` |
| `--urls-from REPORT` | 评一份旧 JSON 报告抽过的那些页面（即它的 `sampled_urls`）。在同一批页面上重评，就能看出网站有没有变，不受抽样波动干扰 |
| `--baseline REPORT` | 和 `--urls-from` 一样评旧 JSON 报告抽过的页面，然后逐项列出和那份报告相比变了什么（见[对比两份报告](#对比两份报告)）。不能和 `--urls` 或 `--urls-from` 同用。加 `--json` 时 stdout 只有报告本身，不输出对比：用 `--json-out` 写出报告，再对两个文件跑 `diff` |
| `--fail-on-drop` | 配合 `--baseline`：和基线相比，只要有检查项丢分、门槛项降到 0 或分数段下降，就以退出码 4 退出，每条原因在 stderr 上占一行。变得观测不到的检查项不算下降 |
| `--compare URL` | 同时评另一个网站，两边并排输出。可重复。不能和 `--json-out`、`--sarif`、`--junit` 同用，这几个只接受一个网站 |
| `--badge [FILE]` | 同时写一枚可嵌入的 SVG 徽章（默认 `aiv-badge.svg`） |
| `--badge-json FILE` | 同时把这枚徽章写成 [shields.io endpoint](https://shields.io/badges/endpoint-badge) JSON：`schemaVersion`、`label`、`message`、`color` 和 `cacheSeconds`，文字和颜色与 SVG 相同 |
| `--share` | 输出一行适合发帖的总结，外加徽章的 markdown |
| `--fail-under N` | 分数低于 N 时以退出码 1 退出，给 CI 用 |
| `--fail-on-gate` | 任何门槛项（`g.*`）得 0 分时以退出码 1 退出，并在 stderr 上写明是哪个门槛项、证据是什么。门槛项得 0 分会让分数封顶在 40：本来能得 40 分及以上的站显示为 40 整，能通过 `--fail-under 40`，而 `--fail-on-gate` 会让任何被封顶的站失败。等同于 `--assert 'g.*>0'`。观测不到的门槛项永远不会失败 |
| `--assert EXPR` | 除非 `CHECK OP VALUE` 成立，否则以退出码 1 退出：CHECK 是一个检查项 id，或一个匹配 id 的 fnmatch 通配式；OP 是 `>=`、`>` 或 `=`；VALUE 是整数或 `max`，例如 `g.robots=max`、`p1.llms-txt>=4`。可重复。本次运行观测不到的检查项输出 `not measured, skipped`，永远不会失败。表达式写错，或者通配式一个检查项也没匹配到，都算参数错误（退出码 2）。结果写到 stderr，从不写进报告 |
| `--quiet`, `-q` | 不在 stderr 上输出进度 |
| `--version` | 输出工具的版本，以及它依据的量表版本 |
| `--ask QUESTION` | 第二级：同时通过各家 API（用你的 Key）拿这个问题去问 AI 引擎，在分数旁边报告它们引用了谁。可重复，最多 5 个 |
| `--brand NAME` | 配合 `--ask`：在回答里找哪个品牌名。默认取网站的域名，例如 `docs.stripe.com` 取 `stripe` |
| `--domain DOMAIN` | 配合 `--ask`：另一个也算你的域名。可重复。被评的网站、它的注册域名，以及跳转后落地的域名，始终算你的 |

子命令：`diff BEFORE AFTER` 对比两份保存下来的报告（见[对比两份报告](#对比两份报告)）；`watch …` 和 `mcp` 属于第二、三级
（见[第二、三级](#watch)）。`geo_score.py --help` 会列出全部子命令，并附上示例和退出码。

`NO_COLOR=1` 会关掉颜色，输出重定向到文件时也一样。CLI 遵循 `HTTPS_PROXY` 和 `NO_PROXY`。
读数看着不对时，见[排查指南](../guide/troubleshooting.zh-CN.md)。

**退出码。** 第一级：

- `0`：打分完成。
- `1`：低于 `--fail-under`、在 `--fail-on-gate` 下有门槛项得 0 分，或者有一条 `--assert` 不成立。
- `2`：网站抓取不到或只返回人机验证页；固定的 URL 列表被拒绝；参数错误（包括写错的 `--assert`）；`--baseline` 或 `diff`
  拿到的文件不是报告，或是按另一个量表版本评的；内部错误。内部错误只报一行，并写明去哪里反馈
  （设 `GEO_SCORE_DEBUG=1` 可以看到 traceback）。
- `4`：`--fail-on-drop`（配合 `--baseline`，或用在 `diff` 上）发现了下降，并且没有别的原因已经以 1 退出。

网站抓取不到时，报错会写明失败的类型，例如 `dns`、`timeout` 或 `http_403`，并链接到
[排查指南里对应的小节](../guide/troubleshooting.zh-CN.md#could-not-fetch-退出码-2)。只返回人机验证页的网站报
`bot challenge served to a browser user-agent (…)`，类型为 `bot_challenge`。加 `--json`（或 `diff --format json`）时，
退出码 2 会在 stdout 上输出一个 JSON 错误，而不是报告（[`schema/error.v1.json`](../schema/error.v1.json)），`error.kind`
里是同一个类型；两份报告的量表版本不同时，类型为 `rubric_mismatch`。[每个检查项能信几分](#每个检查项能信几分)一节列出的
启发式检查项，对它们下的断言和总分一样带着逐次运行的波动：断言这类检查项时，请用 `--urls-from` 固定页面。

第二、三级（`watch …`）：`0` 完成，`1` 配置错误，`2` 参数错误或找不到 `geo_watch.py`，`3` 什么都没测到（没有一个 Key
能用），`4` `watch diff --fail-on-drop` 发现了超出噪声的下降。

## 和竞品对比

```bash
python3 geo_score.py yoursite.com --compare competitor.com
```

两个网站按同样的方式打分，逐项并排输出：两边不一样的行用 `›` 标出，最后列出对方领先的地方。真正有用的是这张清单，
它是两个真实网站之间的差距，而不是一张抽象的检查表。

## 对比两份报告

```bash
python3 geo_score.py yoursite.com --json-out before.json
# … 网站改动之后 …
python3 geo_score.py yoursite.com --baseline before.json          # 重评同一批页面并对比
python3 geo_score.py diff before.json after.json [--format text|md|json] [--fail-on-drop]
```

`diff` 对比两份保存下来的报告；`--baseline` 在基线报告的那批页面上重新打分，并在报告后面输出同样的对比。两者都会给出：

- 每个检查项前后的得分、满分和状态：`up`、`down`、`same`、`became unobservable`、`became observable`，两份报告都没观测到时
  是 `unobservable`。变得观测不到的检查项是移出了分母，从不显示为掉到 0；
- 前后的总分和分数段，以及门槛封顶是出现了还是解除了，并点名每个降到 0 或回到 0 以上的门槛项；
- 抽样中新增和移除的页面。页面不同时，对比会说明：某个检查项的变动里混着网站的变化和抽样的差异；总分变动在 5 分以内的，
  落在实测的波动范围里（[REPRODUCIBILITY.md](../benchmark/REPRODUCIBILITY.md)）；`g.reachable` 是最不稳定的检查项。
  页面相同时，差异就来自网站本身。

`--format json` 遵循 [`schema/diff.v1.json`](../schema/diff.v1.json)。量表版本不同的两份报告不可比，`diff` 以退出码 2 退出。
不同发布版本写出的报告照样对比，但会给出警告，因为发布版本本身就可能让分数变动（更新日志会点名是哪些检查项）；
两份报告评的不是同一个目标时，同样对比并给出警告，这时的差异并不是变化。`--fail-on-drop` 在有检查项丢分、门槛项降到 0
或分数段下降时以退出码 4 退出，和 `watch diff --fail-on-drop` 对引用的处理一样；不加它，无论什么变了，`diff` 都以 0 退出。
`diff` 只需要 `geo_score.py`。

## 给自己的 README 加一枚徽章

```bash
python3 geo_score.py yoursite.com --badge docs/aiv-badge.svg
```

生成一个 shields 样式的 SVG，可以提交到 README 旁边，像其他徽章一样引用：

```
![AIV readiness](docs/aiv-badge.svg)
```

徽章上有分数、分数段和一个无障碍标签，和你已有的构建徽章放在一起也很协调。颜色跟着分数段走，退步一眼就看得出来；
因门槛项得 0 分而被封顶的分数会标上 `(gate capped)`。

提交进仓库的 SVG 显示的是生成它的那次运行的分数。想让徽章保持最新又不提交图片，就把同一枚徽章写成 shields.io endpoint JSON：

```bash
python3 geo_score.py yoursite.com --badge-json aiv-badge.json
```

```json
{"schemaVersion": 1, "label": "AIV readiness", "message": "71/100 Solid", "color": "#2f8f52", "cacheSeconds": 86400}
```

把这个文件发布到任何能用 URL 访问的地方（仓库里的 raw 文件、gist、release 附件或你自己的网站），再把这个 URL
做 URL 编码后交给 shields.io：

```
![AIV readiness](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FOWNER%2FREPO%2Fmain%2Faiv-badge.json)
```

shields.io 会按 `cacheSeconds`（一天）缓存这份 JSON。徽章只和最近一次写出这个文件的运行一样新，所以要定期重跑，
或者每次部署后重跑。在 [GitHub Action](../action.yml) 里，`badge` 输入会在生成报告的同一次运行里写出其中一种文件
（路径以 `.json` 结尾的写 endpoint JSON，其他路径写 SVG），输出 `badge-path` 给出它的位置。提交或发布这个文件，
是你自己工作流里的一步。

## 测什么，不测什么

CLI 给**静态抓取能如实观测到的 17 个检查项**打分。它先用浏览器 user-agent 把抽样页面各抓一次，再挑其中三个页面，
用十个检索 user-agent 逐一重抓，看有没有哪个拿到的内容不一样。它解析 JSON-LD、`robots.txt`、`llms.txt` 和 sitemap，
并查询公开的 Wikidata 和 Wikipedia 接口，看你的品牌有没有知识图谱实体。

有四个检查项**移出分母**，而不是靠猜：

| 检查项 | CLI 为什么看不到 |
|---|---|
| `p3.listings` | 要知道你所在的行业，再去搜该行业的目录 |
| `p3.mentions` | 要在站外搜索独立报道 |
| `p4.question-coverage` | 要有你的市场里人们真正会问的那十个问题 |
| `p4.cn-engines` | 除非抽到的页面是中文，或者主机名以 `.cn` 结尾，否则移出分母 |

[Claude Code 技能](../SKILL.md)会给全部 21 项打分。

### 每个检查项能信几分

用 1.5.0 在相同页面上重评五份公开的人工审计（[VALIDITY.zh-CN.md](../benchmark/VALIDITY.zh-CN.md)），84 对检查项里
CLI 有 80% 与审计者的档位一致。只看两边都打了分的检查项，CLI 平均低 2.4 分（逐站从低 12 分到高 10 分，平均绝对差 8.8 分）。
按完整的归一化分算，平均低 5.2 分，因为人工审计还给 `p3.listings`、`p3.mentions` 和 `p4.question-coverage` 打了分，
CLI 不打这三项。

| CLI 怎么读 | 检查项 | 与人工审计档位一致 |
|---|---|--:|
| **按规则**：解析文件、状态码或标记，按量表写明的计数给分 | `g.robots`、`p1.*`、`p3.knowledge-graph`、`p3.sameas`、`p4.cn-engines` | 39 对中的 92% |
| **按启发式**：近似量表用文字描述的判断 | `g.reachable`、`g.ssr`、`p2.*`、`p3.video`、`p4.answer-shape` | 45 对中的 69% |
| **完全不读**：需要站外搜索或人的判断 | `p3.listings`、`p3.mentions`、`p4.question-coverage` | 移出分母 |

一致度最低的是 `p2.named-author`（5 个站里只有 1 个一致：CLI 有 2 个判得比审计者高、2 个判得低），其次是 `p1.page-type`、
`p2.answer-passages`、`p2.freshness` 和 `p3.video`（各是 5 个站里 3 个一致）。用 1.3.0 时最低的是 `p2.sourced-stats`
（5 个站里有 4 个 CLI 判得比审计者高）；从 1.5.0 起，数字的出处必须就在它旁边，`p2.sourced-stats` 现在在 5 个站中的 4 个上与审计者一致，
第五个站判得偏低。据此采取行动之前，这几项都先用 `--explain` 看一遍。

## 启发式判断，照直说明

有些检查项是量表用文字描述的判断，CLI 只能近似：

- **页面语言** —— 每个抽样页面的语言取自它的 `<html lang>` 或 `Content-Language` 响应头，除非正文与之矛盾；
  没有声明或声明与正文矛盾时，按文字判断（有假名是日文，有谚文是韩文，只有汉字是中文），拉丁字母的文字再看几个常用词。
  声明为中文、日文或韩文的页面，只要带有 30 个及以上这类字符，就保留声明的语言。代码示例（`<pre>`、`<code>`）不读。
  报告里的 `audience_language` 是最常见的页面语言。
- **答案段落** —— 取正文的前六段，找一段 25–120 词（中文、日文、韩文页面为 50–200 字）、以句末标点结尾的。
  它是否真的能独立成立，要由人来判断。
- **提问意图** —— 用模式匹配标题里的问句、任务动词、说明类和对比类句式，英文和中文都读，导航标签和品牌字样除外。
  其他语言的页面不读；一个可读的页面都不剩时，这一项记为未测。
- **带出处的数据** —— 一个数字只有在它所在的正文块（段落、列表项、表格单元格、定义、图注或引文）或紧接着的下一块里，
  有站外链接、`<cite>`、出处措辞，或者一个链接到来源的脚注时，才算有出处。指向本站、本站 `sameAs` 主页的链接，
  以及社交主页和分享按钮，都不算来源；页面的页眉、导航、页脚和侧栏不读。年份、版本号、日期、编号（备案号、账号、
  电话号码）和价格不算数字。出处措辞只读英文和中文。
- **具名作者** —— 先读 JSON-LD 里的 `author` 字段，读不到再看 `rel="author"` 和署名句式（署名句式只在英文和中文页面上读），
  团队名和品牌名不算。
- **页型 schema** —— 除了量表点名的类型（Product + Offer、HowTo、FAQPage），CLI 也把 SoftwareApplication、Course、Recipe、
  Event、JobPosting、Dataset，以及 Article 及其子类型算作页型标记。

CLI 和一个细心的人判断不一致时，以人为准，量表是裁判。用 `--explain` 看 CLI 究竟观测到了什么；如果某条启发式在你的网站上
判错了，请[开一个 issue](https://github.com/jianruntech/geo-score/issues)，这些规则正是靠这样的反馈变好的。

## <a id="watch"></a>第二、三级：实测与追踪

第二、三级在 `geo_watch.py` 里，它必须和 `geo_score.py` 放在同一个目录。它们用你自己的 Key（从环境变量读取，从不写到磁盘），
通过各家 AI 引擎开了联网搜索的 API 去问你的问题，报告回答引用了谁。它们测到的任何结果都不会加进就绪度分数。

### 第二级：`--ask`

```bash
python3 geo_score.py acme.com --ask "best invoicing app for freelancers" --ask "acme vs rival"
python3 geo_score.py acme.com --ask "…" --brand "Acme Inc" --json   # 结果在报告的 citation 对象里
```

最多 5 个问题，每个配了 Key 的引擎各问一次。品牌名默认取注册域名的第一段；名字不一样时用 `--brand` 指定。
一个 Key 都没有时，引用部分写明未测（not measured），就绪度报告不受影响。

### 第三级：`watch`

| 命令 | |
|---|---|
| `watch init [--dir D] [--brand NAME] [--domain D]… [--competitor NAME=DOMAIN]… [--country CC] [--force]` | 写出 `geo-score-watch.json`（模型写死在里面）和 `queries.csv`，后者给 `list`、`pricing`、`alternative`、`problem`、`verdict` 每种类型各放一个占位问题 |
| `watch check` | 校验配置和问题，按 `intent_tier` 统计每种类型有几个问题，对用不了的 `target_url` 给出警告，显示哪些引擎配了 Key、有没有价格 |
| `watch run [--dry-run] [--engines a,b] [--limit N] [--runs N] [--max-calls N] [--budget-usd X] [--allow-unpriced] [--format text\|md] [-q]` | 把所有问题问一遍，运行结果存到 `.geo-score/watch/runs/` 下。`--dry-run` 只打印计划和它的分辨力（至少要有几个问题朝同一方向变动，`watch diff` 才能判定变化；问题集比这还少时打印 `this plan cannot detect a change`），并以 0 退出，有没有 Key 都一样 |
| `watch report [RUN] --format text\|md\|csv\|json [-o FILE]` | 查看一次保存下来的运行（默认最近一次）。`csv` 每条回答一行：`week, query_id, query, intent_tier, engine, cited, quoted_url, rank, other_domains_cited, note, branded, target_cited` |
| `watch report --since DAYS\|--runs A..B [--format text\|md\|json] [-o FILE]` | 合并多次保存下来的运行：最近 DAYS 天内开始的，或从运行 A 到运行 B（两头都算）。每一次都必须与最新一次一致（问题、每题问的次数、引擎、模型、`country` 和品牌域名都相同），否则以 1 退出，并列出每一次不一致的运行。给出合并了哪些运行、覆盖几天、多少条回答、标题引用率，以及每个引擎一行 |
| `watch diff [A] [B] [--format text\|md\|json] [--fail-on-drop]` | 在两次运行都回答了的问题上逐个引擎比较前后（默认最近两次）：变化了多少个百分点并附 95% 区间、跨引擎做 Holm 校正的精确配对检验，以及结论（`change`、`within noise`、`too few questions to tell` 或 `not measured`）。还会列出丢掉的和新增的引用。同一 id 下文字改过的问题不参与比较，并在说明里点名。`--fail-on-drop` 在有结论是变差的 `change` 时以退出码 4 退出 |
| `watch runs` | 保存过的运行、各自的标题引用率，以及 `questions_hash` 的前 8 位：两次运行问的是同一组问题时，这一列相同 |
| `watch ask "question" [--engines a,b] [--brand NAME] [--domain D] [--format text\|md\|json]` | 不打分的第二级：一个问题马上问遍所有引擎（或 `--engines` 指定的那些），不保存 |
| `mcp` | 通过 MCP（stdio）提供打分和追踪；见 [guide/mcp.zh-CN.md](../guide/mcp.zh-CN.md) |

除了 `watch init`（它用 `--dir` 指定写到哪个目录），每个 `watch` 命令都用 `-c PATH` 指定配置文件
（默认 `./geo-score-watch.json`，或 `$GEO_SCORE_WATCH_CONFIG`）。

`geo-score-watch.json`（下面的价格只是示例，请从你的服务商那里抄当前的价格）：

```json
{
  "brand": {"name": "Acme", "domains": ["acme.com"], "aliases": ["Acme Inc"],
            "url_prefixes": ["amazon.com/stores/Acme"]},
  "competitors": [{"name": "Rival", "domains": ["rival.com"]}],
  "queries": "queries.csv",
  "engines": [{"id": "chatgpt-api", "provider": "openai", "model": "gpt-6-luna"},
              {"id": "perplexity-api", "provider": "perplexity"},
              {"id": "deepseek-via-openrouter", "provider": "openrouter", "model": "deepseek/deepseek-chat"}],
  "country": "US",
  "runs": 1,
  "max_calls": 120,
  "budget_usd": 2.0,
  "prices": {"chatgpt-api": {"input_per_mtok": 0.1, "output_per_mtok": 0.5, "per_search": 0.01}}
}
```

| 键 | |
|---|---|
| `brand.domains` / `url_prefixes` | 哪些算你的。子域名也算；前缀用来覆盖你在别人网站上的店铺页或主页 |
| `brand.aliases` | 回答里可能用到的其他名字。中文、日文、韩文名按包含匹配，其他名字按整词匹配 |
| `country` | 两个字母的国家代码，传给支持指定地区的引擎：OpenAI、Claude、Perplexity 会用它；Gemini 和 OpenRouter 忽略它 |
| `runs` | 每个问题在每个引擎上问几次。设成 `3` 比率更稳，费用也是三倍 |
| `max_calls` | 单次运行提问次数的硬上限 |
| `budget_usd` | 花费上限，每次调用前核对一次；最多超出每个引擎一次调用的费用。设了预算时，没有价格的引擎不跑，除非加 `--allow-unpriced` |
| `prices` | 按引擎配置，单位美元：`input_per_mtok`、`output_per_mtok`，可选 `per_search`、`per_call`。Perplexity 和 OpenRouter 会自报费用 |
| `engines[].api` | 仅限 Gemini：`interactions`（默认）或 `generate_content` |
| `engines[].key_env` / `base_url` | 从另一个环境变量读 Key；指向一个兼容的端点（`https://` 或 `http://localhost`） |
| `engines[].tool`, `max_searches`, `max_tokens`, `max_results` | 服务商调优：联网搜索工具的版本（OpenAI、Anthropic），每条回答的搜索次数和输出 token 数（Anthropic），每次搜索返回的结果数（OpenRouter） |

OpenRouter 引擎测的是这个模型经 OpenRouter 的 `web` 插件作答，不是厂商自家的 App 或搜索：对没有原生搜索的模型（如
`deepseek/deepseek-chat`），插件用 Exa 搜索（依据 OpenRouter 文档，2026-10-02 核对）。引擎 id 命名的是一条模型路由，不是一个产品。

这个文件有哪些键，由 [schema/watch-config.v1.json](../schema/watch-config.v1.json)（JSON Schema draft 2020-12）规定。
`watch init` 把 `"$schema"` 写成第一个键并指向它，支持 JSON Schema 的编辑器就会在你输入时校验并补全。

没有代码读取的键会给出警告，从不悄悄丢掉：否则把 `budget_usd` 误写成 `budget` 这样的笔误，会一声不响地拿掉花费上限。
`watch check` 在每一层（顶层、`brand`、`competitors[i]`、`engines[i]`、`prices.<id>`）点名每个未知的键，有相近的已知键时
一并给出，例如 `unknown key 'budget' (did you mean 'budget_usd'?); it is ignored`；`prices` 里对不上任何引擎的条目也会标出来。
`watch run` 和其他读取配置的命令会在 stderr 上输出同样的警告，MCP 的 `status` 工具也会列出。名字像凭据的键（`api_key`、
`OPENAI_KEY`、`api_token`、`client_secret`、`credentials` …）会提示改用环境变量，它的值从不打印。这些警告不改变退出码。

`queries.csv` 有四列：`query_id,query,intent_tier,target_url`。问题要写成买家在 ChatGPT 里会打出来的样子，而且每周保持
同一组问题不变。可选的第五列 `branded`（`auto`、`yes` 或 `no`；留空即 `auto`）用来覆盖对「问题里有没有提到品牌」的自动判断。
品牌名同时是一个常用词时用 `no`；匹配器认不出的昵称用 `yes`。

`target_url` 可以不填，填了就是这个问题追踪的你的那一个页面。写完整的 `http(s)` 网址，或者以 `/` 开头的路径；路径会接在
`brand.domains` 的第一个域名后面（`/pricing` 变成 `https://acme.com/pricing`）。
其他写法 `watch check`、`watch run` 以及 MCP 的 `run` 和 `status` 工具都会给出警告，运行时忽略；页面不在品牌拥有的域名或 URL 前缀上时，
也会警告，但照样匹配。之后这个问题的每条回答都记下 `target_cited`（有一条引用就是这个页面）
和 `other_own_cited`（没有引用这个页面，但引用了你的另一个网址），报告多一张表「Pages you track」：每个页面对应哪些问题、拿到几条回答、
其中几条引用了这个页面、几条转而引用了你的另一个网址，以及这些回答引用最多的是你的哪个网址（按引用时的原样列出）。CSV 的最后一列
`target_cited`，在追踪页面的问题的回答上是 `Y` 或 `N`，其他情况留空。匹配的是规范化之后的同一个页面：`www`、大小写、末尾的斜杠、
查询串、片段（`#` 之后）和百分号编码都不计，所以 `https://www.acme.com/Pricing/?utm_source=x#plans` 就是 `https://acme.com/pricing`。
除此之外都不算：`/en/pricing` 不是 `/pricing`；页面以规范网址（canonical）被引用、而那个网址不同时，也算另一个页面。
没能解析的跳转链接两边都不算。1.6.0 之前保存的运行，这张表由保存的引用当场算出。

`intent_tier` 可以随便填。报告给每个值单独算一个引用率（「By question type」表），`watch check` 打印每种类型有几个问题；
所有问题都是同一种类型、或者都没有类型时，会给一条提示，但不算失败。只有一种类型的问题集，测的就只是这一类问题。
下面这些标签是建议用法，方便不同的问题集读起来一致：

| `intent_tier` | 这类问题 | 例子 |
|---|---|---|
| `list` | 问某个品类里有哪些选择 | 适合自由职业者的开票软件推荐 |
| `vs` | 比较几个点名的产品 | acme 和 rival 哪个好 |
| `alternative` | 问某个点名产品用什么替代 | rival 的替代品 |
| `pricing` | 问价格、套餐或免费额度 | 开票软件一般多少钱 |
| `problem` | 描述一个处境，不提品类也不提品牌 | 客户老是拖款，我记不清谁还欠多少 |
| `persona` | 说明给谁用 | 两个人的设计工作室用什么开票软件 |
| `verdict` | 问值不值、靠不靠谱 | acme 值得买吗 |
| `channel` | 经别的渠道买或卖：加盟、批发、经销、采购 | 有代理或经销计划的开票软件 |

关于你自己品牌的 `verdict` 问题会提到品牌，所以计入含品牌问题那一行，不进标题数字。

**怎么读这些数字。** 标题引用率只统计没有提到品牌的问题。「acme vs rival」几乎一定会引用 Acme，所以这类问题单列一行；
它们超过问题集的 30% 时，`watch check` 会发出警告。一个问题有不止一条回答时（`runs` > 1，或者总体那一行合并了几个引擎），
95% 区间用对问题做的自助法（bootstrap）重抽样，因为同一个问题的几条回答会一起变动；否则用 Wilson 区间。只有 `diff` 说
`change` 时才算有变化。公式和算例见 [guide/watch-methodology.zh-CN.md](../guide/watch-methodology.zh-CN.md)。

**合并多次运行。** 一次运行是一天的回答。`watch report --since 30`（或 `--runs A..B`）把一段时间里的运行当成一组回答来统计，
这样每个问题的比率建立在更多回答上，某一天的异常影响也更小。只有与窗口里最新一次运行问的是同一组问题（`questions_hash` 相同）、
每题问的次数相同（`runs` 相同）、用的是同样的引擎和模型、`country` 相同、品牌域名和 URL 前缀也相同的运行才会被合并；否则拒绝合并，并逐一列出不一致的运行和原因。
它的 95% 区间把同一个问题的全部回答（不论来自哪次运行、哪个引擎）当作一簇：运行越多，区间最多也只能窄到问题数允许的程度。
合并出来的比率描述的是一段时间，不是对变化的检验，也没有合并后的比较。JSON 遵循 [schema/watch.v1.json](../schema/watch.v1.json)
里的 `$defs/pooled`；MCP 的 `report` 工具接受 `since` 参数。运行之前，`watch run --dry-run` 会打印这套计划的分辨力：E 个引擎时，
`watch diff` 检验 E + 1 行（只有一个引擎时是一行）；至少要有 k 个问题朝同一方向变动，才可能判定变化，k 是满足 行数 × 2 / 2^n < 0.05
的最小 n：一个引擎 6 个问题，两个引擎 7 个，三到五个引擎 8 个。多加问题有用；多加引擎会抬高 k；每题多问几次（`runs`）不会降低 k。
见 [guide/watch-methodology.zh-CN.md · 一次提问、一天、一个月](../guide/watch-methodology.zh-CN.md#8-一次提问一天一个月)。

**每个问题提到了谁。** `watch report` 逐个列出问题：拿到几条回答，其中几条引用、几条提到了你，几条引用、几条提到了每个竞品，
几条一个追踪的品牌都没提到，几条联网搜索过（是、否或未知）；问题至少有 4 条回答、且某个追踪的品牌被引用的次数多于其他所有品牌时，
还列出这个品牌。这些都是计数，不是比率。回答有没有联网搜索，从保存的回答里读：服务商报告了搜索、给出了搜索词，或回答引用了网址，
就算「是」；OpenAI、Gemini 或 Anthropic 的回答这几样都没有，就算「否」；Perplexity 和 OpenRouter 的回答一律记为「未知」，因为它们的 API 每次调用都会搜索，或者不说明。JSON 报告和 MCP 的
`report` 工具以 `summary.by_question` 给出同一张表；1.6.0 之前保存的运行，由保存的回答当场算出。

**谁最先被提到。** 每条回答都为你的品牌和每个竞品记下 `mention_order` 和 `mention_share`。`mention_order`：回答在配置里所有品牌中
最先提到的那个记 1，其次记 2，依此类推；位置取品牌名、别名或域名最早的一处匹配，匹配规则与 `mentioned` 相同。回答没提到这个品牌时
记为 null；两个品牌第一次被提到的位置相同（一个名字包含另一个）时，两者也都是 null。`mention_share` 是回答里提到这个品牌的句子
占全部句子的比例，每句同等计数：句子在换行处、在 `。！？` 处，或在后面跟着空白的 `.` `!` `?` 处结束；没有任何字母、汉字或数字的片段
（比如表格的分隔行）不算一句。配置里有竞品时，「By engine」表多一列 *named first (tracked)*：在你追踪的品牌里最先提到你的回答数，分母是至少提到配置里
一个品牌的回答数。「Share of voice」表给每个品牌加上 *named first (tracked)* 和 *sentence share*：在提到这个品牌的回答里，`mention_share`
的平均值。配置里没列的品牌这两项都看不见，所以在你追踪的品牌里排第一，不一定是在回答里排第一；这里的顺序是第一次提到的先后，
不是在列表里的位置。两者都从保存下来的回答里读，回答只保存前 20,000 个字符（被截断的回答 `answer_truncated` 为 true）。JSON 报告
在 `summary.engines` 和 `summary.share_of_voice` 的每一行里以 `named_first`、`any_named` 和 `mention_share` 给出；1.6.0 之前保存的运行，
由保存的回答当场算出。

**通过 MCP 使用。** `uvx geo-score@1.6.0 mcp`（用 pipx 安装后是 `geo-score-mcp`，在克隆的仓库里是 `geo_score.py mcp`）通过 stdio 把三级都提供给 Agent，配置和上限都一样。
它从自己的环境变量读 Key，而桌面应用和你的 shell 并不共享环境变量；图形界面客户端也不会在你的项目目录里启动它，
所以请传 `-c /absolute/path/geo-score-watch.json`。各客户端的配置、工具表、Key、超时和排查见
[guide/mcp.zh-CN.md](../guide/mcp.zh-CN.md)。

运行文件遵循 [schema/watch.v1.json](../schema/watch.v1.json)。测试：`python3 cli/test_geo_watch.py`（离线运行，所有服务商都是模拟的）。

## 在 GitHub Action 里用

```yaml
- uses: jianruntech/geo-score@v1
  with:
    url: https://example.com
    fail-under: 40
    fail-on-gate: true          # 门槛项得 0 分时分数封顶 40；被封顶、恰好 40 分的站能通过 fail-under 40
    json-out: geo-score.json
    sarif: geo-score.sarif      # 可选
    junit: geo-score.xml        # 可选
    badge: aiv-badge.json       # 可选：shields.io endpoint JSON（写 .svg 则生成 SVG）
```

Action 只给网站打一次分。这一次运行把证据打印到日志，把评分表写进任务摘要（job summary），给得 0 分的检查项加注释
（门槛项为 error，其他检查项为 warning；`annotations: false` 可以关掉），并写出你要求的那些文件。`fail-on-gate: true`
在门槛项得 0 分时让任务失败；`assert` 接受和 `--assert` 相同的表达式，每行一条，每条不成立的都会成为一条 error 注释。
`badge: aiv-badge.json`（或 `.svg`）写出徽章。`baseline: before.json` 评一份旧报告（来自 `json-out`）抽过的页面并对比，
和 `--baseline` 一样：对比写进日志，任务摘要里多一节 *Changes since baseline*，输出 `delta`（分数减去基线的分数）和
`dropped-checks`（丢了分的检查项，以及降到 0 的门槛项，用逗号分隔）让后面的步骤可以只在退步时失败。输出有 `score`、`band`、
`gate-capped`、`report`、`report-path`；有 `badge` 时还有 `badge-path`；有 `baseline` 时还有 `delta` 和 `dropped-checks`。
输入以环境变量的形式交给脚本，从不直接拼进脚本，所以 URL 执行不了 shell 代码。

要在仓库的 Security 标签页里看结果，就上传 SARIF 文件（[示例](../examples/ci/github-actions.yml)）。代码扫描要求每条结果
都落在检出的代码里的某个文件上，所以每条结果都指向 JSON 报告里对应检查项的那一行（设了 `sarif` 时，Action 会把这份报告
写进工作区），并在消息里写明被评的网站。
