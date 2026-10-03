# 更新日志

英文版：[CHANGELOG.md](CHANGELOG.md)。**量表**的版本号与仓库版本号分开，见 `rubric/`。

## [Unreleased]

### 新增
- **`engines[].timeout`。** 等一个引擎回答的秒数，10 到 600（默认 120），用于响应慢的接口、或要长时间搜索和推理的模型。超时的请求仍不重试。
- **「What the engines searched for」统计年份和排名类的词，并写明搜了却没返回搜索词的回答。** 表下多一行：在回答给出的全部搜索词里，
  几条含年份（1900 到 2099 之间单独出现的四位数），几条含排名或比较类的词：`best`、`top`、`vs`、`versus`、`review`、`reviews`、
  `compare`、`comparison`、`alternative`、`alternatives` 按整词匹配、不分大小写，`最好`、`最佳`、`推荐`、`排行`、`排名`、`哪家`、
  `哪个好`、`对比`、`评测` 出现在任何位置都算。一条搜索词每一项只算一次，照搬问题原话的也照样计入：这一行描述的是实际搜了什么，
  不是引擎加了什么。OpenAI、Gemini 或 Anthropic 的回答报告了搜索、却没有给出搜索词时（`base_url` 指向的 OpenAI 兼容接口返回
  不带 `action` 的 `web_search_call` 就是这样），这一节不再消失，而是写明有几条回答搜了却没有返回搜索词，并按引擎列出；
  `watch ask` 也在回答下面写明。Perplexity 和 OpenRouter 的回答从不计入，因为它们的适配器不管实际情况都为每条回答记一次搜索。
  summary 新增 `summary.searches.answers_searched_without_queries`、`summary.searches.modifiers`（`total`、`with_year`、
  `with_ranking_word`）和 `summary.engines` 每一行的 `searched_without_queries`，schema/watch.v1.json 现在描述了 `summary.searches`。
  本版之前保存的运行在出报告时由保存的回答当场算出，运行文件本身不会被改写。

### 变更
- **没有一条回答有价格时，账本写明费用未知。** 以前写成 `$0 + 4 answers with no price (add prices to geo-score-watch.json)`，
  看起来像没花钱；现在写成 `cost unknown: 4 answers with no price (add prices to geo-score-watch.json)`。部分回答有价格时仍写
  `$0.07 + 12 answers with no price`。MCP `run` 工具在运行被取消时的提示用同样的说法。JSON 账本不变。
- **账本写明失败了多少。** 有调用失败时，`watch report` 多出一行，写明失败几次、一共发出多少次 HTTP 请求，因为服务商可能对超时的请求照样计费。
  不在当前目录下的路径改为显示绝对路径，不再是一串 `../`。

### 修复
- **OpenAI 引擎把问题作为单条消息的列表发送。** Responses API 字符串和列表都接受；有些用 `base_url` 指向的
  OpenAI 兼容接口只接受列表，之前每次调用都被拒。官方 OpenAI 两种写法的回答相同。

## [1.6.0] — 2026-10-03

### 新增
- **`watch report` 列出每个问题提到了谁。** 新表「Who is named for each question」逐个列出问题：拿到几条回答，其中几条引用、几条提到了你，
  几条引用、几条提到了每个竞品，几条一个追踪的品牌都没提到，几条联网搜索过（是、否或未知），以及被引用次数最多的追踪品牌；后者只在问题
  至少有 4 条回答、且这个品牌多于其他所有品牌时才给出。每个值都是计数。回答有没有联网搜索，由每次运行本来就保存的内容推出（报告的搜索次数、
  给出的搜索词或引用）；Perplexity 和 OpenRouter 的回答一律记为「未知」，因为它们的适配器不管实际情况都为每条回答记一次搜索。表下三行说明
  这些计数说明不了什么：没有联网搜索的回答不可能引用任何东西；「no tracked brand named」只覆盖配置里的品牌；以及为什么有些回答是「未知」。
  summary 新增 `summary.by_question`（schema/watch.v1.json 的 `$defs/by_question`），JSON 报告和 MCP `report` 工具都带上它；它是该工具
  输出 schema 里的可选字段，MCP 契约只增不减。本版之前保存的运行在出报告时由保存的回答当场算出，运行文件本身不会被改写。
- **建议的问题类型，`watch check` 会统计。** `intent_tier` 仍然可以随便填；cli/README 和 guide/watch-methodology 现在建议 8 个标签，
  各附一句说明和一个例子：`list`、`vs`、`alternative`、`pricing`、`problem`（描述一个处境，不提品类也不提品牌）、`persona`（给谁用）、
  `verdict`（值不值、靠不靠谱）和 `channel`（加盟、批发、经销、采购）。`watch check` 打印每种类型有几个问题；所有问题同属一种类型、
  或者都没有类型时给一条提示，但不算失败。`watch init` 多写两个占位问题：一行 `problem`，一行 `verdict`。
- **`target_url` 开始生效：`watch report` 统计问题追踪的页面被引用了几次。** 这一列以前写进了文档、也存进了运行文件，但没有任何代码读它。
  现在读取问题时就解析它：完整的 `http(s)` 网址按原样使用（去掉片段和 `utm_*` 参数），以 `/` 开头的路径接在品牌的第一个域名后面。
  其他写法 `watch check`、`watch run` 以及 MCP 的 `run`（包括试运行）和 `status` 工具都会警告，运行时忽略；页面不在品牌的域名或
  URL 前缀上时也会警告，但照样匹配。每条回答记下 `target_cited`（有一条引用就是这个页面）和 `other_own_cited`（没有引用这个页面，但引用了品牌的另一个网址）；问题不追踪页面时两者都是 null。
  匹配的是不计 `www`、大小写、末尾斜杠、查询串、片段和百分号编码之后的同一个页面；`/en/x` 不是 `/x`，没能解析的跳转链接两边都不算。
  新表「Pages you track」逐个页面列出对应的问题、回答数、其中几条引用了这个页面、几条转而引用了你的另一个网址，以及这些回答引用最多的
  你的网址（按引用时的原样）。CSV 导出最后多一列 `target_cited`（`Y`、`N` 或留空）。Schema 新增 `$defs/sample` 里的 `target_cited`
  和 `other_own_cited`、`summary.tracked_pages` 及 `$defs/tracked_page`，并给保存的 `target_url` 加了说明。MCP `report` 工具的输出
  schema 新增可选的 `tracked_pages`，MCP 契约只增不减。本版之前保存的运行在出报告时由保存的引用当场算出这张表。
- **`watch report` 列出谁最先被提到。** 每条回答为品牌和每个竞品记下 `mention_order`（在配置里所有品牌中最先被提到的记 1，位置取名字、
  别名或域名最早的一处匹配，匹配规则与 `mentioned` 相同；没提到、或两个品牌第一次被提到的位置相同时为 null）和 `mention_share`
  （提到它的句子占全部句子的比例，每句同等计数；句子在换行处、`。！？` 处，或后面跟着空白的 `.` `!` `?` 处结束）。配置里有竞品时，
  「By engine」表多一列「named first (tracked)」：在配置里的品牌中最先提到你的回答数，分母是至少提到配置里一个品牌的回答数。
  「Share of voice」表多出「named first (tracked)」
  和「sentence share」（在提到这个品牌的回答里 `mention_share` 的平均值），表下三行说明怎么读。配置里没列的品牌看不见，所以在你追踪的
  品牌里排第一，不一定是在回答里排第一。两者都从保存下来的回答里读，回答只保存前 20,000 个字符。Schema：`$defs/sample` 及其竞品里
  新增 `mention_order` 和 `mention_share`，`summary.engines` 与 `summary.share_of_voice` 每一行新增 `named_first`、`any_named` 和
  `mention_share`。MCP 工具的 schema 不变。本版之前保存的运行在出报告时由保存的回答当场算出。
- **`watch run --dry-run` 说明这套计划能测出什么，`watch report` 可以合并多次运行。** 试运行会打印计划的分辨力：E 个引擎时，
  `watch diff` 检验 E + 1 行（只有一个引擎时是一行）；两次运行之间至少要有 k 个问题朝同一方向变动，才可能判定变化。k 是满足
  行数 × 2 / 2^n < 0.05 的最小 n，也就是 diff 本来就用的筛选：一个引擎 6 个问题，两个引擎 7 个，三到五个引擎 8 个。问题更少时打印
  「this plan cannot detect a change」：多加问题有用，多加引擎会抬高 k，每题多问几次不会降低 k。MCP `run` 工具试运行时打印同样的几行。
  `watch report --since DAYS`（或 `--runs A..B`）把一段时间里保存的运行当成一组回答来统计，前提是每一次都与最新一次问的是同一组问题
  （`questions_hash` 相同）、每题问的次数相同（`runs` 相同，每次运行分量一样）、用的是同样的引擎和模型、
  `country` 相同、品牌域名和 URL 前缀也相同；否则以 1 退出，并逐一列出不一致的运行和原因。
  输出给出合并了哪些运行、覆盖的日历天数、回答数、标题引用率和每个引擎一行，95% 区间对问题重抽样（每个问题带着它在每次运行里的全部回答），
  并保留单次报告的说明（API 渠道、提到品牌的问题、什么算未测量，以及它预测不了流量、排名或收入）。
  没有合并后的比较。Schema：schema/watch.v1.json 新增 `$defs/pooled`。MCP：`report` 工具新增可选参数 `since`，
  输出 schema 新增可选的 `runs` 和 `days`，MCP 契约只增不减。guide/watch-methodology 新增第 8 节「一次提问、一天、一个月」。

### 变更
- **从 PyPI 安装。** geo-score 从 1.5.0 起就在 PyPI 上，文件就是 GitHub 发布附带的那个 wheel 和 sdist；现在各处的安装命令
  都先给它：`uvx geo-score@X.Y.Z example.com`、`pipx install geo-score==X.Y.Z`，MCP 客户端用 `uvx geo-score@X.Y.Z mcp`
  （安装按钮、Claude Code 那一行、标准配置、guide/mcp.zh-CN.md 里的每个客户端，以及 Claude Desktop 安装包里 watch init
  的提示）。发布的 wheel 链接留作访问不了 PyPI 时的那一行，git tag 留作从源码安装的那一行，`curl` 那一行仍是什么都不装就能跑
  第一级的用法。server.json 在 `.mcpb` 旁边加上 pypi 包，MCP Registry 从本版起因此也会提供它；README.md（也就是这个包在 PyPI
  上的说明）带上 Registry 认领用的 `mcp-name` 一行（1.5.0 在 PyPI 上的说明没有这一行，所以 1.5.0 的登记只列 `.mcpb`）。
  `release.py --bump` 会改写所有 `geo-score@X.Y.Z` 和 `geo-score==X.Y.Z`；`--execute` 最后一步就是上传 PyPI（`--no-pypi`
  跳过这一步，`--publish-pypi` 只做这一步）：用 `TWINE_VERSION` 固定版本的 twine 只上传 `SHA256SUMS` 里列出的 wheel 和
  sdist，再核对 PyPI 上每个文件的 SHA-256（RELEASING.md 第 8 步）。它对 GitHub 和 PyPI 的请求会试三次；中途停下、而重跑能
  接着做完时，会给出重跑的命令。缺少 `geo_watch.py` 时（用管道跑的那一行命令），`watch`、`mcp` 和 `--ask` 打印的提示也先给
  这个包，再给 wheel 包。

### 修复
- **`watch diff` 只拿一个问题和它自己比较。** 以前只按 `query_id` 配对，同一 id 下改写过的问题会和旧措辞配对，改写本身可能被读成
  「变化」（`--fail-on-drop` 也会因此以退出码 4 退出）。现在会比较问题文字（忽略大小写、合并空白）：文字改过的问题不进入任何一行，
  并在说明里点名（最多列 10 个 id，其余写成 `and N more`）。至少 6 个问题的门槛，以及对任何检验都判不出来的行的筛查，都只按剩下的问题计算，
  所以在含改写问题的运行上，结论可能变化，也可能变成 `too few questions to tell`。两次运行的提问地区（`country`）不同、或某个引擎 id
  换了服务商时，说明里也会写明。运行文件新增可选的顶层字段 `questions_hash`（对按 id 排序的「id + 规范化文字」对做 SHA-256，定义见
  schema/watch.v1.json），`watch runs` 显示它的前 8 位；更早的运行由保存的问题当场算出。
- **API 改了回答格式，不再悄无声息地被读成「引擎不再引用」。** 每个适配器只读各家服务商的一种格式，引用字段一改名，回答就一条引用都没有，
  `watch diff --fail-on-drop` 也可能因为一次格式变化以退出码 4 退出。现在某个引擎回答了 5 个或更多问题、
  却没有一条回答带任何域名的引用时，`watch report` 在「By engine」下给出警告；同一模型下，某个引擎带任何引用的回答占比从至少 50%
  降到 5% 以下、且后一次运行至少回答了 5 个问题时，`watch diff` 在这个引擎的行上加 `warning`，并把同样的话写进说明和 stderr。
  两者数的都是问题而不是回答，因为同一个问题的几条回答会一起变动。结论和退出码 4 都不变：警告请你用 `watch ask`
  核对一条回答。summary 的 `summary.engines` 每一行新增 `with_citations` 和 `with_searches`，没有这两项的旧运行在出报告时由保存的回答
  当场算出。Schema 新增这两个计数，以及 `$defs/diff_row` 里可选的 `warning`；MCP `diff` 工具的输出 schema 新增可选的 `warning`，
  MCP 契约只增不减。
- **`p3.video`：抖音、西瓜视频和快手的频道链接算作频道。** 指向抖音账号主页（`douyin.com/user/…`，或分享链接展开后的
  `iesdouyin.com/share/user/…`）、西瓜视频频道（`ixigua.com/home/…`、`m.ixigua.com/user/…`）或快手个人主页
  （`kuaishou.com/profile/…`、`live.kuaishou.com/profile/…`）的链接，现在读作频道链接；抖音开放平台的播放器
  （`open.douyin.com/player/video`）读作嵌入播放器。1.5.0 及以前只认 YouTube、B 站和 Vimeo。短链接（`v.douyin.com`、
  `v.kuaishou.com`）和单条视频的链接一律不算频道。证据行里的「official channel links」改为「channel links」，
  因为指向并非本站所有的账号的链接也会计入。方向：上升，只涉及链接了这些平台的网站。榜单在下一次重跑时体现这一变化。

## [1.5.0] — 2026-09-30

这一版关乎按量表的本意读网站，也关乎让 CI 为对的原因失败。两个爬虫门槛项现在只看 10 个检索爬虫，按 RFC 9309 为每个爬虫选
robots.txt 分组，遇到掉线先重试再下结论；人机验证页不再被当成要跑 JavaScript 的页面来评分；每个页面按它自己的语言读；一个数字
只有来源就在旁边时才算有来源。这些修正会让分数变动，下面每一条都写明检查项和方向。CI 方面有 `--fail-on-gate` 和 `--assert`（门槛
项得 0 分时总分封顶 40，本来能得 40 分及以上的站正好停在 40，`--fail-under 40` 会放它通过），逐项对比两份报告的
`geo-score diff` 和 `--baseline`，以及 shields.io endpoint 徽章。评不了分的网站很快失败，用一行话说明原因，`--json` 下给出 JSON
格式的错误；一次评分运行也不会再卡住不动。CLI 之外：watch 配置有了 schema 和拼错键名的提示，从发布的 wheel 安装、不需要
git，关卡锁定所用工具的版本，CI 示例覆盖 GitHub 之外的平台，有了对榜单某一行提出异议的表单，基准榜单可以重测、也可以拆开来看。榜单本身仍是 2026-09-27 用 1.3.0 跑的那一轮。

**从 1.4.0 升级。** 第一级的分数只在 1.4.0 读错了网站的地方变动，每一处都列在「修复」下，写明检查项和方向：门槛项（`g.robots`、
`g.reachable`，以及有人机验证、有日文或韩文页面、或英文页面带 20 个以上汉字的站的 `g.ssr`）、读页面文字的检查项
（`p2.answer-passages`、`p2.question-intent`、`p2.sourced-stats`、`p2.named-author`、`p4.answer-shape`、`p4.cn-engines` 和
`p3.knowledge-graph`），以及文件、logo 或爬虫请求现在会重试的检查项（`p1.llms-txt`、`b.llms-full`、`b.ai-txt`、`p1.organization`
和 `p4.cn-engines`）。有三种调用的退出码变了：只返回人机验证页的网站不再评分、以退出码 2 结束；意料之外的错误以一行信息、退出码 2
结束，不再打印 traceback 并以 1 退出；`--sample` 小于 1 时以退出码 2 结束，1.4.0 遇到 0 会崩溃，遇到负数会少抽页面。`diff`
现在是子命令，名字就叫 `diff` 的主机要写成 `https://diff`。`audience_language` 现在可能是 `en`、`zh-CN` 以外的语言；报告只多了一
个可选字段 `elapsed_s`。

### 新增
- **术语表与中文版 CLI 说明。** 新增 `guide/glossary.zh-CN.md`（英文版 `guide/glossary.md`），解释 README、报告和各篇指南里
  用到的 49 个术语，每条写明在哪里出现、去哪一页看详细说明；新增 `cli/README.zh-CN.md`，即 CLI 说明的简体中文版，两个版本顶部都有语言切换。
- **`--fail-on-gate` 与 `--assert EXPR`**，CLI 和 Action（输入 `fail-on-gate`、`assert`）都有。门槛项得 0 分时分数封顶 40：
  本来能得 40 分及以上的站正好停在 40，能通过 `--fail-under 40`（`fail-under: 40`）。`--fail-on-gate` 会让任何被封顶的站失败：
  任一 `g.*` 检查项得 0 分时退出码为 1，并写明是哪个门槛项及其证据，等同于 `--assert 'g.*>0'`。`--assert` 把单个检查项、或用
  fnmatch 通配匹配的一组检查项锁定在某个值，例如 `g.robots=max`、`p1.llms-txt>=4`，可重复使用。本次运行观测不到的检查项跳
  过，不算失败。表达式写错、或通配匹配不到任何检查项时退出码为 2。两个参数都需显式开启，不改变任何分数；结果只写到 stderr，不进入报告。
- **`geo-score diff BEFORE AFTER [--format text|md|json] [--fail-on-drop]`**：逐项对比两份一级报告。每个检查项列出前后得分、满分
  和状态：`up`、`down`、`same`、`became unobservable`、`became observable`，两次都没测到的是 `unobservable`。还会列出前后的总分、
  档位和门槛封顶情况，点名降到 0 分或离开 0 分的门槛项，并列出抽样中新增和移除的页面。两次抽样不同时会明确说明，总分按 ±5 读（benchmark/REPRODUCIBILITY.md），
  并指出 `g.reachable` 是最不稳定的检查项。变得无法观测的检查项从不显示为掉到 0 分。`--format json` 遵循新增的
  `schema/diff.v1.json`。两份报告的量表版本不同时退出码为 2；工具版本不同、或评的是两个不同目标时照常对比，但会在 stderr
  给出警告。`diff` 只需要 `geo_score.py`。
- **`--baseline REPORT`**：评分时重新评基线报告抽过的那些页面（和 `--urls-from` 一样），并在报告之后输出同样的对比。不能和
  `--urls`、`--urls-from` 同时使用。加 `--json` 时，stdout 只输出报告本身，不打印对比：用 `--json-out` 写出报告，再对两个文件运行
  `geo-score diff` 才能看到。`--fail-on-drop` 仍会以退出码 4 结束，并在 stderr 写明每一处下降。
- **`--fail-on-drop`**（配合 `--baseline`，或用于 `diff`）：有检查项丢分、门槛项降到 0 分或档位下降时以退出码 4 退出，每个原因在
  stderr 输出一行。和 `watch diff --fail-on-drop` 一样需要主动开启，所以现有的调用方式退出码都不变。`--fail-under`、
  `--fail-on-gate` 或 `--assert` 未通过时，退出码仍然是 1。
- **Action：** 新增 `baseline` 输入和 `delta`、`dropped-checks` 两个输出，job summary 里增加「Changes since baseline」一节，从基
  线文件读来的检查项 id 会转义。基线文件可以和 `json-out` 是同一个文件。
- **能自动保持最新的徽章。** `--badge-json FILE` 把徽章写成 [shields.io endpoint](https://shields.io/badges/endpoint-badge) JSON：
  `{"schemaVersion": 1, "label": "AIV readiness", "message": "71/100 Solid", "color": "#2f8f52", "cacheSeconds": 86400}`。SVG 和
  JSON 的文字、颜色出自同一个函数，两者不会对不上。把文件放到任何能访问的地址，`https://img.shields.io/endpoint?url=<它的地址>`
  就能显示徽章。Action 新增 `badge` 输入：路径以 `.json` 结尾写 endpoint JSON，其他路径写 SVG；新增输出 `badge-path`，给出文件写
  到了哪里。
- **出错时给 JSON，而不是什么都没有。** 加 `--json` 时，每一次退出码 2（包括参数错误）都在 stdout 输出
  `{"error": {"kind", "message", "target"}, "tool": "geo-score-cli/X.Y.Z"}`，以前 stdout 是空的；`diff --format json` 也一样。新
  增的 `schema/error.v1.json` 列出各种类型：没有任何回应时是 `dns`、`refused`、`tls`、`timeout`、`dropped`、`no_response`；站点
  有回应时是 `http_<code>`、`no_content`、`slow`、`bot_challenge`；运行超时是 `deadline`；MCP 服务的地址防护拒绝时是
  `not_public`；此外还有 `usage`、`rubric_mismatch`（传给 `diff` 或 `--baseline` 的两份报告量表版本不同）、`error` 和 `internal`。
  次版本可以新增类型，读到不认识的类型按 `error` 处理。
- **`--timeout SECONDS`**（默认 15，与以前相同；最多 300）：每个请求最多等服务器多少秒，超过就算没有回应。
- **JSON 报告新增 `elapsed_s`**（可选，见 `schema/report.v2.json`）：本次运行在执行它的机器上用了多少秒，页脚也会显示（`· took 23.4 s`）。
  它描述的是这次运行，不是站点，`diff` 不比较它。
- **`geo-score-watch.json` 有了 schema，没有任何代码读取的键都会提示。** `schema/watch-config.v1.json`（JSON Schema draft 2020-12）
  描述这个文件，`watch init` 现在把 `"$schema"` 写成第一个键，编辑器可以据此校验和补全。以前写错的键会被悄悄忽略：把
  `budget_usd` 写成 `budget` 等于没有预算上限，把 `max_calls` 写成 `max_call` 则回到默认的 120 次上限。现在 `watch check`
  会逐层（顶层、`brand`、`competitors[i]`、`engines[i]`、`prices.<id>`）列出每个未知的键，有相近的已知键时一并给出，例如
  `unknown key 'budget' (did you mean 'budget_usd'?); it is ignored`；`prices` 里写了不存在的引擎也会提示。`watch run` 和其他
  读取配置的命令把同样的警告写到 stderr；MCP 的 `status` 工具会列出它们，`run` 工具在计划里和保存运行结果之后都会显示。名字像
  凭据的键（`api_key`、`OPENAI_KEY`、`api_token`、`client_secret`、`credentials` 等）会被提示改用环境变量，值从不打印。只是警告，
  退出码不变。
- **GitHub 之外的 CI。** `examples/ci/gitlab-ci.yml` 是基于 `python:3.12-slim` 的 GitLab 任务：从固定版本的 release 下载
  `geo_score.py`，用 `SHA256SUMS` 校验，只打一次分，把 `geo-score.json` 存为 artifact，并把 `geo-score.xml` 作为 JUnit 报告交给
  GitLab，得 0 分的检查项显示为失败的测试。`examples/ci/README.md` 列出 Bitbucket Pipelines、Azure Pipelines、Jenkins 和
  CircleCI 各自读取 `--junit` 文件所需的那一条配置。
- **什么问题找哪里。** *Benchmark correction*（榜单更正）表单用来对某一行的分数、门槛原因、标签或未打分原因提出异议，附一份新的
  `--json-out` 报告和工具版本；*Tool problem*（工具问题）表单覆盖 CLI、Action、MCP 服务、pip/pipx/uvx、MCPB 安装包、Claude Code
  插件、Gemini CLI 扩展和 Docker。Issue 选择页链接排障指南和 MCP 排障章节，新增的 `SUPPORT.md` 说明什么问题用哪张表单。原来的表单
  会打上仓库里并不存在的 `benchmark`、`engine`、`rubric` 标签，这些 issue 实际上没有标签：现在 `.github/labels.json` 列出全部标签，
  由 `scripts/sync_labels.py` 同步到 GitHub（默认只演练；`--apply` 才创建和更新，`--check` 在缺标签时退出码为 1，且从不删除标签）。
  它只打印代理的主机和端口，不输出 `HTTPS_PROXY` 里的凭据。
- **基准榜单：可以重跑的重测研究。** `benchmark/retest.py` 输入两个或更多运行目录（results.json 加 raw/），记录每次运行的工具版本、
  日期、Python 版本、声明的测量位置以及是否固定页面。每一对运行报告完全一致、±2 以内、±5 以内的比例，ICC(A,1) 与 SEM，档位变化与
  门槛封顶翻转，以及逐项的档位翻转和每次运行各检查项测不到的比例。它逐站逐次保存记录，所以每个数字都能重算；`--check` 核对提交的
  文件（`validate.py` 第 32 条）。`benchmark/run.py` 新增 `--out DIR`（为重测跑一轮，不动公开的文件）、`--urls-from-dir DIR`
  （通过 CLI 的 `--urls-from` 读取器，让每个站重读上一次运行抽到的页面）和 `--vantage LABEL`，后者记为 results.json 的
  `measured_from`，与 `python`、`pinned_from` 并列。标签由运行者声明，不查询任何地址。
- **基准榜单：把中文市场的差距拆开。** `benchmark/stats.json` 新增 `china_gap_detail`，在已有的 bootstrap 之后用同一个种子继续抽样，
  所以已发布的区间一个都不动。内容包括：按受众语言分组的差距，与按行业标签的差距并列，附交叉表（37/27/13/240）；四组相近行业的
  一一对比，不足 10 站不给数；原始分差距按规则读取与启发式检查拆开（启发式占 68%，这是启发式误读最多能解释的比例）；
  `p3.knowledge-graph` 在 50 个中文站里有 33 个测不到，其余 267 个站里是 76 个；这一项补成 0 分时差距为 20 分，补成 4 分时为 19 分。
- **基准榜单：扁平下载文件。** `benchmark/results.csv` 每个上榜站一行（该行各字段、`sample_n`、`sample_source`、未打分原因和报错，
  之后每个检查项一列、写分数，观测不到的留空）；`benchmark/checks.csv` 每个已打分站的每个检查项一行。`run.py`（包括
  `--readme-only`）生成这两个文件，榜单页的 Dataset 标记和 llms.txt 都链接它们，`validate.py` 第 35 条逐格核对 results.json 和
  raw/。raw/ 没有记录每个 user-agent 拿到的状态，所以暂不提供 robots.csv。
- **基准榜单：每一行靠的是什么。** 每行的真实样本数（`sample_n`、`sample_source`）都公开，已提交的数据从 raw/ 读取。实际评分不足
  4 个页面的 69 行，在基准榜单 README 和中英两个页面上都标为「样本少」，页面上可以按它筛选；stats.json 把去掉这些行后的中位数
  （62）放在主数字 56 旁边（`validate.py` 第 33 条）。另有一张从 raw/ 算出的表，说明各项做法有多普遍：317 个站中 137 个提供
  `llms.txt`，98 个的 Organization 与 WebSite 标记齐全，251 个有内页的站中 82 个的内页有 BreadcrumbList，161 个的 sitemap 带
  `lastmod`，67 个至少一半页面有个人署名。旁边附 Web Almanac 2025 的 `llms.txt` 数字，并说明两边统计的站点群体不同。
- **基准榜单：怎么抓取，以及怎么更正一行。** 「怎么抓取」一节写明每站的请求上限，由 CLI 自己的 user-agent 列表和常量算出（发往该站
  最多 67 个请求，发往其他地方最多 20 个，不含跳转和重试），并说明爬虫 user-agent 是从运营者自己的地址发出的，不是厂商的地址。
  「更正」一节链接榜单更正表单：确认是工具错误的，以补丁版本修复；已发布的分数只在重新测量时才会变。`run.py` 把以
  `bot challenge served to a browser user-agent` 开头的 CLI 报错单独归为一种未打分原因，未打分列表按原因分组。用 1.5.0 或更新版本
  测的行会记下 CLI 的错误类型（results.json 里的 `error_kind`），并按它归类：`http_*` 归为拒绝，`timeout`、`slow`、`deadline` 归为
  超时，`dns`、`refused`、`tls`、`dropped`、`no_response` 归为连接失败。用 1.3.0 测的行仍按报错文字归类。网站本身和它的 `www`
  主机都失败时，这一行记下走得更远的那次尝试的报错（以前记的是 `www` 主机的），IP 地址也不再用 `www` 重试。
- **权重敏感性分析**（`benchmark/sensitivity.py`、`SENSITIVITY.md` 及中文版）。先从 raw/ 重算全部 317 个分数（0 处不一致），再在
  等权、按证据依据加权（示意）、逐项拿掉一个检查项、300 次带种子的随机抽样这几种情况下重新打分。名次很稳：各种情况下 Spearman
  ρ 都 ≥ 0.988；档位没那么稳：等权让 39 个站换档，按证据依据加权是 24 个，随机抽样的中位数是 26 个。之后是各检查项的分档分布和
  项目-其余相关，结尾列出给 v1.2 的输入。它用 `math.fsum` 累加，任何 Python 版本写出的文件都相同。v1.1 权重不变。`validate.py`
  第 36 条。
- **档位线落在哪里**（`benchmark/percentiles.py`、`percentiles.json`、基准榜单 README 里的表、`rubric/bands-analysis.md` 及中文版）。
  317 个站中达到起步期、成长期、基础扎实、领先的比例依次是 85%、58%、34%、10%。分析用三条标准检验 v1.1 的档位线（按 Core Web
  Vitals 的定义衡量可达成性：达到领先的是 10%，没有余量；317 个站里 168 个离某条档位线在重测 SEM 的噪声以内；起步期 88 个站里
  48 个是被门槛封顶的），并列出 v1.2 的候选档位线。v1.1 的档位线不变。`validate.py` 第 37 条。
- **关卡覆盖每个 Python 版本。** `scripts/check.sh --all` 在 3.8 到 3.14 的每个 Python 版本上跑三个 CLI 测试套件和 MCP 一致性检查，
  装了 3.15 也会跑；`--strict` 在缺少需要的解释器时直接失败并提示 `uv python install X`，不再跳过。两者都可以和 `--live` 组合，
  参数不认识时退出码为 2。关卡用 `python3` 运行所有 `scripts/test_*.py` 和 `benchmark/test_*.py`，新的测试文件按名字自动加入；
  `--live` 下，装了 `gh` 且已登录时还会运行 `scripts/sync_labels.py --check`。
- **新的测试。** `scripts/test_ci_examples.py` 用 bash 对着本地夹具站点跑可复制的 CI 示例。`scripts/test_repo_meta.py` 检查表单与
  标签是否一致、README 徽章与它记录的那次运行是否一致，以及选择页、表单、`SUPPORT.md` 和 PR 模板里的链接。
  `benchmark/test_benchmark.py` 离线测试 retest.py、限定语、canonical 地址、中国差距的小样本抑制、样本数、抓取请求上限、两个 CSV、
  敏感性与分位数的算术以及效度数字。`scripts/test_packaging.py` 新增检查：每个写了发布版本号的受版本控制文件都在 `release.py --bump` 会改写的
  范围内（更新日志、benchmark/raw/、dist/、docs/*.html 和 .github/validate.py 除外）；每个发布 wheel 链接里的 tag 和文件名都等于
  `__version__`；validate.yml 安装 check.sh 锁定的 ruff 和 jsonschema 版本，并把 action 锁定到 commit；Dockerfile 的基础镜像锁定了
  digest；pyproject 的分类标签覆盖 3.8 到 3.14，validate.yml 和 RELEASING.md 写的也是这两端。
  `cli/test_geo_score.py` 新增七个曾让 1.4.0 解析器崩溃的输入，以及一个带种子的属性测试：把 200 个随机页面和 robots.txt 文件送进
  各个解析器和 `run()`；它还跑了 MCP 地址防护在连接时锁定已检查地址、拒绝重新解析到私有地址的域名、以及经代理访问 HTTPS 时的
  CONNECT 分支，这些代码以前没有任何测试跑到过。`cli/test_geo_score_e2e.py` 注入故障（连接中断、429、固定状态码、一点一点往外吐
  的回应），统计 good 夹具发出的每一个请求，并用 golden 文件核对 `diff` 的输出。

### 变更
- **文档：一次 API 运行看不到什么，以及 OpenRouter 示例。** README 与 watch 方法说明（新增第 7 节）列出这些 API 够不着的界面，
  并说明被引用是在场、不是好坏。OpenRouter 示例引擎改名为 `deepseek-via-openrouter`，文档写明 OpenRouter 引擎测的是模型经
  OpenRouter 的搜索作答，不是厂商自家的搜索；`country` 由 OpenAI、Claude、Perplexity 采用，Gemini 和 OpenRouter 忽略。
- **报告开头点名门槛项。** 默认视图和 `--brief` 都会点名每个得 0 分的门槛项，并附上其证据的第一句：
  `GATE AT ZERO — g.ssr: 0 of 8 sampled pages carry substantive body text …; the score cannot exceed 40 while a gate is at zero`。
  以前只写 `GATE CAPPED — a gate check scored zero`。
- **所有视图用同一个差距排序。** 默认视图、`--brief` 和 `--share` 的排序相同：先是得 0 分的门槛项，再按升到下一档能加的分从高到
  低，最后按量表顺序。每一行印的数字就是旁边那个条件对应的分，例如
  `+4 next tier (+9 to full)  Self-contained answer passages  needs: …`。以前在下一档的条件旁边印的是离满分的差距。`--share` 现
  在点名门槛项：「robots.txt disallows AI retrieval crawlers」「AI retrieval crawlers are refused」或「crawlers get no
  server-rendered body text」。以前不管是哪个门槛项，都说爬虫「cannot reach the content at all」。内容差距现在写作
  `(+N at the next tier)`。MCP 的 `score_site` 摘要也一样：有门槛项得 0 分时用同一句开头，最多六个差距按同样的顺序列出，每项写明升到
  下一档能加几分。以前它列的是得分比例最低的六项，其中还有加分项。
- **报告页脚。** `Needs judgement:` 拆成两行。`Needs off-site search or judgement:` 列出 p3.listings、p3.mentions、
  p4.question-coverage；`Not observable this run:` 列出其余各项，每项附一句简短原因，例如
  `p4.cn-engines (not a Chinese-language site)`。报告和 `--brief` 增加 ✓ ◐ ✗ ⊘ 的图例。量表和排查指南的链接指向本次发版的标签（`blob/v1.5.0/…`），
  和每个检查项的 `doc_url` 一致。终端排版不属于公开契约。
- **抽样之后一波发出。** 抽样页面取回后，凡是网址已经确定的请求都一次并发发出，各项检查从本次运行的缓存里读结果：sitemap、
  `llms.txt`、`llms-full.txt`、`ai.txt` 与 `/.well-known/ai.txt`（给了路径时连同该路径下的同名文件）、Organization 的 logo、最多
  8 个 `sameAs` 主页、中文搜索引擎爬虫，以及 30 个检索爬虫探测。Wikidata 与 Wikipedia 查询在旁边并行，仍然一次查一个品牌候选，所
  以发出的查询和以前一样。发往站点的请求仍共用 8 个连接，发往其他主机的另有自己的连接。在测试夹具上给每个应答加 0.2 秒延迟，一次
  运行里前后相接的请求从 18–29 轮减到 11–12 轮。这一波本身不改变分数，请求的网址也和 1.4.0 相同，只有一处例外：
  `/.well-known/ai.txt` 现在即使 `/ai.txt` 存在也会请求。它为站点文件、logo 和中文爬虫加上的重试会让分数变动，写在「修复」下。
- **`--help` 自成一体。** 它写出你实际运行的命令（`geo_score.py` 或 `geo-score`），在用法行里列出 `diff`、`watch`、`mcp`，并解释
  URL 参数和 `-q`。末尾有五个示例、退出码（含 watch 的），以及本版本评分标准和排障指南的链接。缺少 `geo_watch.py` 时，`mcp`、
  `watch`、`--ask` 会说明是哪一个需要它，并先给出发布版 wheel 的 `uvx` 与 `pipx` 命令，再给出 clone。
- 门槛封顶时，SVG 徽章显示 `40/100 Early (gate capped)`，与 endpoint JSON 一致。
- `diff` 现在是子命令，和 `watch`、`mcp` 一样。要评分一个名字就叫 `diff` 的主机，请写成 `https://diff`。
- **评分器的文档。** guide/troubleshooting.md（中英文）为每种错误类型各设一节，CLI 的报错信息按发布标签链接到对应小节；新增「分
  数为什么变了」一节；「中文站按字数算，英文站按词数算」一节改为「每个页面按它自己的语言读」。rubric/v1.1.md（中英文）在
  `g.robots` 和 `g.reachable` 下写明读的是哪 10 个爬虫、怎么读，在 `g.ssr` 下写明人机验证页不算抽样页面，也永远不会被读成 0 分；
  这些都是澄清，档位和分值不变。reference/ai-crawlers.md（2026-09-28 核对）写明 `RETRIEVAL_UAS` 按它的检索爬虫表测试，探测用的是
  厂商公布的 UA 字符串、从审计方自己的地址发出、未经身份验证，Claude-SearchBot 和 Claude-User 的字符串是按 Anthropic 公布的产品
  标识拼出来的，以及在 Amazon 对 Amazonbot 的新描述复核之前，它仍算检索爬虫。rubric/open-questions.md（中英文）为 v1.2 新开两个
  问题：第 10 条，每次都返回 5xx 的 robots.txt 是否算全站禁止；第 11 条，样本里没有一页带三个数字时，`p2.sourced-stats` 是退出分
  母，还是给 3 分。
- **从发布的 wheel 包安装。** uvx、pipx 和 MCP 的安装命令改为下载
  `https://github.com/jianruntech/geo-score/releases/download/vX.Y.Z/geo_score-X.Y.Z-py3-none-any.whl`，不需要 git，也没有构建步骤。
  涉及：README 的安装说明、Cursor / VS Code / VS Code Insiders / LM Studio 按钮、Claude Code 命令、标准 `mcpServers` 配置、
  guide/mcp.zh-CN.md 里各客户端的配置，以及 MCPB 的 watch init 提示。从 git 安装（`git+https://github.com/jianruntech/geo-score@vX.Y.Z`）
  保留为标注「从源码安装（需要 git）」的一行。`release.py --bump` 除了改 tag，也改 wheel 文件名里的版本号。
- **关卡与发布。** 关卡默认找 Python 3.8、3.12 和 3.14 来测（以前找的是 3.8、3.12、3.13，从来不测 3.14），uv 找不到的版本
  跳过并给出安装提示；`--strict` 要求 3.8 和 3.14 都在。
  关卡锁定 ruff 0.15.15 和 jsonschema 4.23.0（仍能装在 Python 3.8 上的最新 jsonschema）：PATH 上的 ruff 正好是锁定版本时才用它，
  否则用 `uvx ruff@0.15.15`，先找 uv 缓存再联网；python3 自带的 jsonschema 正是锁定版本时直接用它。离线且缓存为空时，退回 PATH
  上的 ruff 和 python3 的 jsonschema，与锁定之前一样。`--all` 下，比最新受支持版本更新的那个 Python 标为可选；没有 uv 时，`--all`
  会说明只在 python3 上跑测试。`release.py --execute` 先确认 `gh` 已登录，否则立即停止；
  随后运行 `check.sh --live --strict`（以前是 `--live`）；构建出的 wheel 文件名如果和安装命令里下载的不一致，也会停止。
- **validate.yml** 设置 `permissions: {contents: read}`，把 actions/checkout v7.0.1 和 actions/setup-python v7.0.0 锁定到 commit SHA，
  设置 `persist-credentials: false`，安装同样锁定版本的 ruff 和 jsonschema，测试 3.8 和 3.14，并运行在 `ubuntu-24.04` 上，这是
  setup-python 仍为 3.8 构建的最新镜像。Dockerfile 的基础镜像 `python:3.12-slim` 按镜像索引 digest 锁定（3.12.14-slim-trixie，
  2026-09-28）。pyproject.toml 增加 Python 3.8 到 3.14 的分类标签，以及 "3 :: Only"。
- **可复制的 CI 示例。** `examples/ci/github-actions.yml` 把 `actions/checkout`、`actions/upload-artifact`、
  `github/codeql-action/upload-sarif` 固定到提交 SHA，并在注释里写明对应版本；设置 `persist-credentials: false`；步骤输出经 `env:`
  传入；并说明怎样让 Action 在两次运行之间保持不变（固定到某个发布 tag，或更严格地固定到它的 commit）。
  `examples/ci/watch-weekly.yml` 同样固定 `actions/checkout` 与 `actions/setup-python`，它要推送运行文件，所以保留凭据。
- **README 徽章是一次记录在案的运行。** 它由榜单页的一次运行生成，记录在 `docs/aiv-badge.json`（2026-09-28，geo-score 1.4.0）：
  93/100 Leading，替代文字写明这个日期和版本。原来的徽章是手工提交的 87。打分代码没有变化。
- **参与贡献。** PR 模板要求贴出 `bash scripts/check.sh` 的最后几行、更新中英两份更新日志、中英文同步、重新生成榜单产物、披露雇主
  的站点，且只用绝对链接。它和 CONTRIBUTING.md 都列出新量表版本需要的全部文件：下一个版本的中英量表和 JSON、中英证据表，以及一份
  用它打分的公开审计。CONTRIBUTING.md 还列出了两个新的测试文件。
- **榜单只有一个地址。** 榜单的 canonical、og:url、og:image、hreflang、llms.txt 与 sitemap 地址改指向在维护的镜像
  https://www.jianruntech.com/leaderboard 与 /leaderboard/zh，不再指向停在 229 站的 GitHub Pages 旧副本；`GEO_SITE_BASE` 仍可覆盖。
  `scripts/check_live.py` 默认检查镜像，并直接从页面读站点数、中位数与日期。`validate.py` 第 30 条。
- **CLI 与人工审计的对照改为同口径比较。** 只看两边都打了分的检查项，CLI 平均低 0.4 分（逐站从低 6 分到高 9 分，平均绝对差 5.2；
  Bland-Altman 偏差 −0.4，95% 一致性界限 −12.8 到 +12.0，n=5），记在 `benchmark/validity.json` 的 `common_checks` 里，旁边另有
  `validation_set`。按完整分数的「低 3.6 分」放第二位：人工审计还给 `p3.listings`、`p3.mentions`、`p4.question-coverage` 打了分，
  CLI 不打这三项。VALIDITY 中英两版新增三条说明：这 5 个站就是 v1.0→v1.1 的校准站，属于开发数据；人工分都在 69–87 之间，只有 1 个
  中文站，没有被封顶的站；审计文件没有记录打分人。两份 README 都先引用同口径的数字，`validate.py` 第 23 条核对它和
  `common_checks` 都等于逐站数据。1.3.0 的条目保持发布时原样。
- **中文市场的差距不再只报一个数**，benchmark/README.md、榜单页和两份 README 都拆开来说：「低 20 分」写明定义（五个中国行业）、按
  语言分组的差距（20 分，95% 置信区间 13–25）、相近行业对比的范围（6 到 30 分）和启发式占比上限（68%）。`validate.py` 第 31 条和
  第 38 条。
- **REPRODUCIBILITY.md 写明 ±5 / 96% 是怎么测的：** 2026-09-09 用 1.1.2 修正波动之前的 1.1.x 版本、在 229 个站上测得。新增
  ICC(A,1) 0.974、SEM 3.09 与 18 个档位变化，表格由 retest.py 生成。`reproducibility.json` 改为 format 2，旧的两次运行保存在
  `legacy` 下。页面页脚和两份 README 都写明日期与版本。
- **证据说明，只补元数据**（不改权重和档位）：`p2.question-intent` 注明 1.4.x 及以前 CLI 的中文标题词表缺少英文词表能匹配的任务型
  与解释型写法；`p3.knowledge-graph` 注明 CLI 只查维基数据与维基百科，不查百度百科。量表 README 和证据表链接了敏感性分析，校准记录
  链接了档位分析。

### 修复
- **样本只取文档。** sitemap 或链接里列出的文件（如 `agents.md` 这类 Markdown、订阅源、JSON、PDF、媒体文件）不再被抽为样本页；
  列表页（分页、分类、标签、作者、系列、归档页）只在内容页都用完后才会抽到。方向：两边都有，都是向网站内容本身的读数靠拢。
  1.3.0 榜单上有 5 个站的样本里混进了文件，39 个站的样本里有两个及以上列表页；baseus.com 当时只按 `agents.md` 一个文件评分。
- **`p1.llms-txt`：没有应答记为不可观测。** 重试后仍没有应答的 `/llms.txt` 现在移出分母，不再记 0 分。方向：由 0 分变为不可观测
  （1.5.0 第一轮重跑中，有 38 个站因为请求始终没有应答而在这一项得了 0 分）。
- **握手进行到一半被断开，算作连接断开。** 握手过程中的 SSL EOF 现在记为 `dropped` 并会重试，不再记为不重试的 `tls`。
  如果运行 CLI 的 Python 其 TLS 库不支持 TLS 1.3，`tls` 报错会写明这一点：macOS 自带的 `/usr/bin/python3` 基于 LibreSSL 2.8，
  而很多网站要求 TLS 1.3。
- **榜单对网络失败再试一次。** `benchmark/run.py` 在整轮结束后，对因网络故障（连接断开、超时、TLS 错误、429 或 5xx）失败的站
  再试一次。1.5.0 的榜单用 Python 3.12 运行：先在系统自带的 Python 上跑的一轮，有 68 个站因 TLS 错误没能评分。
- **`g.robots` 与 `g.reachable` 只对 `reference/ai-crawlers.md` 列出的 10 个检索爬虫计分。** 补上 Claude-User、Googlebot、
  Amazonbot，去掉 GPTBot、ClaudeBot 和一个杜撰的 Google-Extended 探测。每个爬虫都用厂商公布的 UA 字符串。`g.robots` 按 RFC 9309
  第 2.2.1 节为每个爬虫选规则：有点名它的组，就不再看 `*` 组。文件开头的字节顺序标记不再吞掉第一组。分数变动有三个方向：
  - **上升**：只挡训练爬虫或选择退出令牌的站。榜单上（2026-09-28 实测）together.ai、lonelyplanet.com、loom.com、
    stackoverflow.blog、webmd.com、airbnb.com、khanacademy.org 的 `g.robots` 不再是 0。airbnb.com 对所有爬虫 UA 都返回 403，仍因
    `g.reachable` 被封顶。
  - **上升**：`*` 组 Disallow、同时为检索爬虫逐个具名 Allow 的站。
  - **下降**：挡了 Claude-User、Googlebot 或 Amazonbot 的站，以及字节顺序标记藏住了禁止组的站。healthline.com 仍是 0，原因变为挡
    了 Amazonbot。

  证据现在写明被挡的爬虫及挡住它的组；按名字禁止的训练爬虫与选择退出令牌列为「不计分」；`g.reachable` 的证据列出没探测成功的 UA。
- **偶发的网络故障先重试，再影响门槛项。** robots.txt、首页和 sitemap 每次运行只抓一次，并带重试。`g.reachable` 的探测在无响
  应、429 或 5xx 时重试一次，并遵守不超过 5 秒的 Retry-After。在所有页面上都没有应答（每次都超时或连接被断开）的爬虫不计入：
  从一个地址发出时，这多半是网络问题，否则就是防火墙丢弃了从非厂商地址发来的爬虫 UA，真正的爬虫不会遇到。档位按有应答的爬虫来判；
  0 分那一档（「多数检索 UA 被拦」）要求十个里超过一半以 HTTP 明确拒绝；有应答的不到一半时，该项记为不可观测。在部分页面有应答的爬虫算访问成功。
  这条规则来自 1.5.0 第一次重跑榜单：那次把没有应答当成拒绝，让浏览器和多数爬虫都能访问的 31 个站被门槛封顶（pulumi.com 从 99 分降到 40 分）；
  在五个人工审计站上，`g.reachable` 的档位完全一致率由 0.4 升到 0.8。
- **首页抓不到，不等于没有实体标记。** 首页在样本里却抓取失败时，如果其他页面上没有 Organization，`p1.organization`、`p3.sameas`、
  `p3.knowledge-graph` 记为不可观测而不是 0 分，因为它通常就放在首页。方向：首页失败的运行中由 0 分变为不可观测（nextjs.org 的人工对照曾因一次
  抓取失败，把这三项都读成 0 分）。重试 3 次仍读不到的 robots.txt 现在记为「不可观
  测」、退出分母，不再当作「没有 robots.txt」。每次都返回 429 或 5xx 的，仍给第 3 档并在证据中写明。方向两边都有：一次 robots.txt 抓取失败曾藏住
  Disallow 的站下降；爬虫探测偶遇 429 或连接重置而被当成拦截的站上升。1.3.0 榜单上有五行的 `g.robots` 来自失败的抓取
  （「No robots.txt (HTTP 0)」）：clickpaas.com、codecademy.com、continue.dev、helium10.com、xcmg.com。
- **站点文件、Organization 的 logo 和中文爬虫的请求会重试。** 1.4.0 对 `llms.txt`、`llms-full.txt`、`ai.txt`、logo，以及各中
  文爬虫访问首页的请求都只发一次，所以一次超时、连接重置、429 或 5xx 就被读成文件不存在、logo 打不开或爬虫没访问成功。现在这些文件
  和 logo 像 sitemap 一样重试（最多 3 次），中文爬虫像检索爬虫探测一样重试（重试一次）；重试完仍没有应答的，读法和以前一样；明确的
  应答只请求一次，健康的站不会多收请求。方向：上升，涉及以前把偶发故障读成「没有」的 `p1.llms-txt`、`b.llms-full`、
  `b.ai-txt`、`p1.organization` 里 logo 那一部分，以及 `p4.cn-engines`。经代理的七次实测里，有两次因为一次超时丢了
  `p1.llms-txt`。
- **人机验证页不再评分。** 反爬服务（AWS WAF、Akamai、Cloudflare、Fastly、PerimeterX、DataDome 或 Imperva）给 CLI 的浏览器 UA 返
  回人机验证页、而不是页面本身时，这一页和抓取失败的页面一样移出样本。只返回验证页的网站过去会被记为 `g.ssr` 0 分并封顶 40，榜单
  上写成「正文需要 JavaScript」。现在这类网站不评分，以退出码 2 结束，报错为
  `bot challenge served to a browser user-agent (<厂商>): a static fetch cannot measure this site`；加 `--json` 时给出错误类型
  `bot_challenge`。方向：这类网站的 `g.ssr` 从 0 分变为不评分：2026-09-30 实测，ups.com（Akamai，1.3.0 榜单上 16 分、被封顶）得到
  人机验证的报错。只在部分页面返回验证页的网站，用剩下的真实页面评分，`notes` 里写明有几页是验证页：booking.com（AWS WAF，1.3.0
  榜单上 20 分、被封顶）2026-09-30 有一次运行得到人机验证的报错，同一天另外两次运行用剩下的页面评了分。openai.com 在 1.3.0 榜单上
  记为「all requests returned 403」，它返回的是 Cloudflare 的验证页，现在得到的是人机验证的报错。只是加载了某家反爬探针脚本的
  JavaScript 空壳仍记 `g.ssr` 0 分。gzip 压缩的 HTTP 错误页现在会先解压，压缩过的验证页也能认出来。
- **少于抽样页数的报告会写明。** 有页面被移出时，`notes` 增加一条
  `Scored on N of M sampled pages; K returned errors, J were bot challenges`；发现的页面少于要求的数量时，增加一条
  `Sampled N of the 8 pages asked for: no more were found (sample source: …)`。`schema/report.v2.json`（`sampled_urls`）一直这样
  要求。终端报告也打印同样的内容。分数不变。
- **`p2.sourced-stats` 只认数字旁边的来源。** 一个数字只有在它所在的内容块（段落、列表项、表格单元格、定义、图注或引文）或下一个
  块里有指向站外来源的链接、`<cite>`、来源措辞，或一个脚注引用且该脚注链接到来源时，才算有来源。内容指第一个 `<main>` 或
  `<article>`，没有的话就是去掉页眉、导航、页脚和侧栏之后的页面。指向站点自己的域名、它自己的 `sameAs` 主页、社交主页或分享按钮
  的链接都不算来源。1.4.0 只要一个页面的主体 HTML 里任意位置有两个站外链接、`<cite>`、`<blockquote>` 或来源用语，就把它们当作页
  面上所有数字的来源，所以一个社交图标、一个合作方 logo 或一个「Research」菜单项就够了。算作数字的东西也少了：年份、版本号、用点
  分隔的日期、几号、`#` 编号、编号（七位及以上的连续数字，或前面是 ICP备、ICP证、公安备、网安备、号，或后面跟着号的数字：备案号、
  账号、电话号码），以及价格（按价格写法写的金额，如 `$29/mo`、`68元/月`、`$15 per user`、`¥68起`；跟在每月、售价、起价、低至这
  类价格用语后面的金额；单独成为一块的金额，如价格卡片上的 `$29`）。其他金额仍算数字，后面带量级的金额也算（`$4.5 billion`、
  `3000亿元`）。档位仍按页面比例：7 分要求带三个及以上数字的页面中有四分之三为多数数字给出链接来源，5 分要求一半给出任何来源，3
  分要求至少有一个数字有来源；样本里没有这种页面时仍给 3 分。证据里给出各项计数。方向是下降。2026-09-30 用 1.5.0 在 1.3.0 榜单
  报告抽过的页面上重评：sentry.io、seeyon.com 为 3 分（1.3.0 榜单上 7 分），mingdao.com 为 0 分（7 分）；mistral.ai 的页面是法文，
  这一项不评分（1.3.0 榜单上 5 分，见下面的页面语言）。五个人工审计过的站当天在审计页面上重评，CLI 与审计者档位一致的有 4
  个，VALIDITY.md（用 1.3.0 测）里是 1 个，当时另外四个 CLI 都判得更高；mingdao.com 现在 CLI 判 0 分，审计者是 3 分。
- **每个页面按它自己的语言读。** 抽样页面的语言先看 `<html lang>`，没有就看 `Content-Language` 响应头，除非可见文字与之矛盾。两
  者都没有时按文字判断（有假名是日文，有谚文是韩文，只有汉字是中文），拉丁字母的文字再按几个常用词区分英文、德文、法文、西班牙文
  和葡萄牙文。判断时不读代码示例（`<pre>`、`<code>`）；声明为中文、日文或韩文的页面，只要带 30 个及以上这类字符，就保留声明。
  1.4.x 及以前，一个中文页就让整次运行的所有页面都按中文阈值判定，日文站被标成 `zh-CN`，德文、法文标题用英文词表来读。受影响的检
  查项及方向：
  - `p2.answer-passages` 上升。每页按自己的单位数：中文、日文、韩文页面按字（50–200），其他页面按词（25–120）。首页是中文的样本
    里，英文页现在按词数读（airwallex.com 的英文页此前 8 页得 0 页），假名和谚文也算作字。证据写明多少页用了哪种单位。
  - `g.ssr` 在日文、韩文页面上上升：假名和谚文计入 120 的下限（一个日文样例站由 0 分、总分因此封顶 40，变为 5 分）。正文里有超过
    20 个汉字（例如语言菜单）的英文页面也上升。「正文要跑 JavaScript」的判断同向变化。
  - `p2.question-intent`：没有标题词表的语言（CLI 只有英文和中文）的页面不参与计数。一个页面都不剩的站记为未测（「no
    question-intent lexicon for ja」），不再用英文词表去读。中文的任务、说明和对比类标题（创建你的第一个应用、工作流的工作原理、
    价格与版本对比）开始计入，管理团队、处理器这类名词，以及对比度、原理图这类产品参数不算；英文的对比类标题（compare、vs、
    versus、compared）也开始计入。方向上升。
  - `p2.sourced-stats` 和 `p2.named-author` 趋向未测。来源措辞和文字署名「By …」只在英文和中文页面上读；来源链接、`<cite>`、脚注，
    以及结构化数据或 `rel="author"` 里的作者，任何语言都读。两种情况下该项移出分母，而不是记 0 分：带数字的页面没有一页能读来源
    措辞且读数低于 5 分，或者没有一页能读署名。
  - `p4.cn-engines` 在日文、韩文站上移出分母：抽到中文页面或主机名以 `.cn` 结尾时才可测，不再因为页面汉字多就可测。没有中文页面、
    只是地址里含有 `.cn` 的站（如 `www.cnn.com`、`www.cnbc.com`）也移出分母：1.4.0 只看地址里任何位置有没有 `.cn`。榜单上没有这类
    站。
  - `p4.answer-shape` 在部分页面上下降，因为段落长度上限改为按页设定：首页是中文的样本里，英文页重新按 90 词判定，日文段落把假名
    也计入。
  - `p3.knowledge-graph`：Wikidata 和 Wikipedia 用英文和英文以外最常见的页面语言查询（Wikipedia 有该语言的大型版本时）。日文站不
    再用中文查。每个品牌名仍最多查两种语言。
- **`audience_language` 取最常见的页面语言**，写作 BCP 47 主标签（`en`、`ja`、`de`……）。中文仍写 `zh-CN`；`und` 表示没有一个页面
  能判断出语言。中文首页加英文页面的样本现在是 `en`。这个字段本来就是 BCP 47 字符串，schema/report.v2.json 的说明现在写明了它的
  含义。
- **连不上的网站很快失败，并说明原因。** 以前一个拼错的域名或一台停机的主机要等 20 秒到 4 分钟，最后给出一段原始的 urllib 文字。
  现在 CLI 在运行前先解析一次主机名（请求经代理发出时跳过，因为由代理来解析），不存在的域名立即失败，报
  `cannot resolve <host>: check the spelling, or your DNS/proxy settings (HTTPS_PROXY)`。解析不了的域名、被拒绝的连接和失败的
  TLS 握手都不重试。最后的报错是一句话，写明失败的类型、经过的代理（只写主机和端口，从不写凭据）以及排障指南里对应的小节，链接固
  定到发布标签。不是带主机名的 http 或 https 网址的输入（含空白字符、其他协议、端口不在 1–65535 之间）按参数错误处理，退出码 2；
  localhost、IP 地址和不带点的内网主机名照常评分。有回应的网站评分和以前完全一样。
- **慢吞吞的服务器不再能拖住一次运行。** `--timeout` 限制的是每一次读取，而不是总和：一台每隔几秒才发一个字节的服务器，能把一次
  抓取、连同 CI 任务或 MCP 工作线程拖上几个小时。现在一个请求（含跳转）最多用 30 秒或 `--timeout` 的两倍，取较长者，超过就记为
  `slow` 类型，不再重试。一次评分运行最多 300 秒：到时不再发起新请求，进行中的请求以 `deadline` 类型停止，需要它的检查项记为不可
  观测（门槛项也一样），而不是 0 分。原来会把每个没闭合的标签一直重试到页尾的 HTML 扫描（80 KB 的 `<script>x ` 要 1.8 秒，4 MB
  的页面要几个小时）改为一遍扫完，结果不变。在这些限制内有回应的网站，评分和以前一样。
- **格式错误的标记不再让运行崩溃。** `{"@type": {"@id": …}}`、像 `http://[::1` 这样的链接、Sitemap 行或 logo 地址、JSON-LD 名称
  里落单的代理项转义，或嵌套 2000 层的 JSON-LD，以前会让运行打印 traceback 并以退出码 1 结束，CI 会把它读成「低于 `--fail-under`」。
  现在只有字符串才算类型名，格式错误的链接当作没有链接，落单的代理项变成 `?`（emoji 仍完整保留），JSON-LD 改用不递归的方式展开。
  其他意料之外的错误输出 `geo-score internal error (<Type>) while scoring <url>; please report it at …/issues` 并以退出码 2 结束；
  `GEO_SCORE_DEBUG=1` 会显示 traceback。分数不变。
- `--sample` 小于 1 改为参数错误（退出码 2）。此前 0 会崩溃，负数会悄悄少抽页面。Action 的 `sample` 输入只接受 1 及以上的整数。
- cli/README.md 原来写着 GitHub Action「只要把 `json-out` 指向一个路径」就会重新生成徽章，其实 Action 从来没有这个功能。这一节现
  在只介绍确实存在的东西：`--badge`、`--badge-json`、Action 的 `badge` 输入，以及 shields.io 的用法。
- 报告和 `--brief` 里离下一档的距离写作 `1 point to Solid`，不再写成 `1 points to Solid`。
- **保存付费的运行结果，要么完整，要么不留。** 回答里如果有半个代理对（半个 emoji，服务商有时会返回这种字符），保存会在中途失败，
  留下一个截断的运行文件：已经付费的这次运行丢了，而且在手动删掉这个文件之前，`watch report`、`watch diff` 和 MCP 工具读取最新一次
  运行都会报错。现在先把完整内容写进隐藏的临时文件、刷到磁盘，再以一个没有被占用的运行 id 链接到位（id 已被占用时顺延为
  `<id>-2` 等），保存失败既不留下半个文件，也不动之前的运行。UTF-8 装不下的文本存成 `\u` 转义，读回来还是同样的文字。
- **半个代理对不再让 `watch run`、`watch report`、`watch ask`、`watch diff` 崩溃。** 文本输出把它显示为 `\u` 转义，stdout 和 `-o`
  文件都一样；`watch report --format json` 和 `watch ask --format json` 也能输出这类回答。
- **引擎的调优键会被检查。** `max_tokens`、`max_searches`、`max_results` 必须是正整数，`tool` 必须是字符串；`watch check` 以及所有
  读取配置的命令现在都拒绝其他值，包括 1.4.0 接受的 `"2048"` 这样的字符串。以前误填进 `max_tokens` 的值会被送进 `int()`，保存在
  运行文件里的错误信息会带上它；新的报错从不显示这个值。`runs`、`max_calls` 和调优键接受 `2.0`，与 JSON Schema 一致。
- **MCP 的 `score_site` 说清楚为什么拒绝一个主机。** 解析不了的域名返回
  `cannot resolve <host>: check the spelling, or your DNS/proxy settings`，走代理时还会注明 `score_site` 在运行服务的机器上解析每个
  主机名来确认它是公网地址；以前这样的主机会被说成私有地址。解析到私有、回环或保留地址的主机返回
  `url must be on a public host: <host> resolves to a private, loopback or reserved address`。
- MCP 量表资源的 `source` 链接指向发布标签下的量表，不再指向 `main`；`geo_score.py watch --help` 里 `mcp` 一项写明安装后的命令名
  `geo-score-mcp`。
- **安装不再需要 git。** 文档里的 `uvx`、`pipx` 安装方式和一键 MCP 按钮，在装了 uv 但没有 git 的机器上不再失败（"Git operation
  failed"），第一次启动也不再从源码构建。guide/mcp.md 中英两版删掉了没有实测依据的「`score_site` 大约 20 秒」，
  榜单页（「大约二十秒」）、README 封面图和演示图的说明文字也删掉了同样的说法。一次运行要多久取决于网站和网络，报告里的
  `elapsed_s` 记下了实际用时。
- **「Anything else」CI 片段**原来把 CLI 跑两次，保存下来的报告可能与决定退出码的那次运行不同，而且下载后不校验。现在从固定版本的
  release 下载 `geo_score.py` 和 `SHA256SUMS`，用 `--json-out`、`--junit`、`--fail-under` 只跑一次。校验与打分用 `&&` 串联，即使
  shell 没开 `set -e`（如 Azure Pipelines 的 script 步骤）或 `pipefail`，文件对不上也会在打分前停下。GitLab 任务和每周 watch 工作流
  逐个文件对照它在 `SHA256SUMS` 里的那一行校验，校验失败后每周对比步骤不再运行。
- PR 模板里 Scope 的链接是相对路径，在 PR 正文里会变成 404。CONTRIBUTING.md 让量表贡献者新增 `rubric/v1.1.md`，而这个版本已经发布，
  现在改为写下一个版本。
- **榜单的分组只说 1.3.0 的数据撑得住的话。** 只要 results.json 的测量工具早于 1.5.0，「robots.txt 屏蔽」一组就带限定语：1.3.0 的
  读法把 GPTBot、ClaudeBot 和 Google-Extended 也算作检索爬虫，所以这 23 个里包括只屏蔽训练爬虫或只声明退出令牌的站。「正文要跑
  JavaScript」一组也带一句：那时的读法分不出人机验证页和 JavaScript 空壳。两句都出现在 benchmark/README.md、中英两个页面和
  llms.txt 里，用 1.5.0 或更新的版本重跑榜单后自动消失。403 一组改为「服务器拒绝爬虫 user-agent（探测来自审计方自己的地址，未经
  爬虫身份验证）」；页面也不再说中国差距「不是内容质量，是 llms.txt、Organization 结构化数据……」：逐项差得最多的两项是启发式判断。
- 基准榜单 README 不再说「每个站同样抽 8 个页面」，改为每个站最多 8 个页面，并说明 69 个站实际评分的页面不足 4 个（其中 55 个只有
  1 页）。
- **榜单页的 Dataset 标记。** 原来把 `readiness` 写成「0-100 的归一化分数」，实际上它是原始分，`normalised` 才是百分比。
  `variableMeasured` 现在列出 normalised、readiness、observable_max、band 和 gate_capped；下载链接原来指向 blob/main 的页面，现在
  改为 raw.githubusercontent.com 上 `v<版本号>` 的文件，旁边加上两个 CSV。许可证暂时仍是 MIT。`validate.py` 第 34 条。
- 以上基准榜单的条目都没有重新打分：results.json 仍是 2026-09-27 用 1.3.0 跑的那一轮，检查项的 id 和读法也没有因此改变。

## [1.4.0] — 2026-09-28

MCP 服务成为使用 geo-score 的正式方式：README 里有独立章节和一键安装按钮，每个客户端都有配置说明，有一键安装包，
同时支持新旧两代协议，而且每个工具都说清楚花不花钱、可以一键关掉花钱的部分。

### 新增
- **MCP 服务同时支持两代协议。** 2026-07-28（`server/discover`、每个请求自带 `_meta`、缓存提示）与经 `initialize` 协商的
  2025-11-25、2025-06-18、2025-03-26、2024-11-05 并存。旧版里不认识的版本号按 2025-11-25 回答；新版里不支持的版本返回
  `-32022` 并列出支持的版本。批量请求只在 2025-03-26 下接受；服务从不发 cursor，所以传 cursor 视为参数错误。
- **MCP 工具先说花不花钱。** `score_site` 排第一；每个工具都有标题和全部四个标注提示，描述第一句就是费用（"Free, no API key." / "Paid: …"），
  输入 schema 拒收未知参数，可为空的字段改用 `anyOf`，严格的客户端也能接受。`ask` 和 `run` 返回结构化结果，`run` 的 dry run 也以数据形式返回计划。
- **取消即停止花费。** 收到 `notifications/cancelled` 后，`ask` 和 `run` 不再发出下一次调用；被取消的 run 不保存，已发出的调用和费用写到 stderr。
  工具调用在工作线程里执行（最多 4 个），长时间运行时仍会响应 `ping`。读到输入结束时立即停下付费调用，免费调用照常返回结果。
  同一时间只跑一个 `run`：进行中时第二个会被拒绝，并行调用不会让一次授权花两倍的钱。
- **健壮性。** 损坏的运行文件或配置只会得到一条错误回复，不会让服务退出；不是对象的 arguments 直接拒绝，不再当作 `{}`；
  各平台上 stdio 都用 UTF-8，输出流表示不了的字符改为转义，不会丢掉整条回复；`status` 从不显示误填进 `key_env` 的值，
  只有真能开跑时才报告 `run` 就绪；`GEO_SCORE_MCP_EXCLUDE_TOOLS` 与 `--exclude-tools` 取并集。
- **可以选择开放哪些工具。** `--toolsets score,ask,watch`、`--tools`、`--exclude-tools`、`--read-only`，各有 `GEO_SCORE_MCP_*`
  环境变量对应。`--read-only` 启动的服务不可能花钱。新增只读工具 `status`：报告版本、找到的配置、哪些引擎有 Key（从不返回 Key 本身）和上限。
- **提示与补全。** `audit_site`、`check_citations`、`weekly_watch`、`compare_runs`、`explain_check`，检查项 id 和 run id 可以补全，
  另有 `geo-score://runs/{run_id}` 资源。它们都不含改法：测量公开，改法不公开。
- **安装包。** 每次发版附带 Claude Desktop 安装包（`geo-score-X.Y.Z.mcpb`）和 MCP Registry 用的 `server.json`，都在 `SHA256SUMS` 里。
  仓库本身也是 Claude Code 插件市场（`/plugin marketplace add jianruntech/geo-score`）和 Gemini CLI 扩展，并提供运行 stdio 服务的 Dockerfile。
  目前还没有发布到任何 registry、PyPI 或容器仓库。
- **文档。** 两份 README 都新增「MCP 服务」一节：一键安装按钮（Cursor、VS Code、VS Code Insiders、LM Studio）、标准配置、工具表和示例提问；
  `guide/mcp.zh-CN.md` 给出 Claude Code、Claude Desktop、Codex、Cursor、VS Code、Gemini CLI、Devin Desktop、Zed 的确切配置，
  以及超时、安全和排查。`scripts/mcp_docs.py` 从服务本身生成工具表和按钮，内容过期时 `check.sh` 报错。
- **检查。** `scripts/check_mcp.py` 在每个被测的 Python 版本上，用原始 stdio 按两代协议驱动服务；`check.sh --live` 再用官方 MCP Inspector
  （2.8.0，`--strict`）跑一遍并实际调用 `score_site`。`scripts/test_packaging.py` 逐个核对清单和代码。快照和 1.3.0 契约基线防止工具或必填参数被无意改动。
- SECURITY.md 新增 MCP 服务的逐工具表：联网、读写文件和花费。

### 变更
- **榜单用 1.3.0 重跑**（2026-09-27）：370 站中 317 站有分，中位数 56（95% 置信区间 52–58），最低 11、最高 99；
  83 个站（26%）有门槛项得 0 分（47 个要靠 JavaScript、23 个屏蔽 AI 爬虫、13 个报错）。两轮都有分的 312 个站平均变化 −0.4 分，
  72% 的站变化在 5 分以内——这里混着 1.3.0 的计分修正和网站 18 天里的变化，不是复现精度（复现精度见 `benchmark/REPRODUCIBILITY.md`，同一版本跑两遍）。
- 这一轮每个站的完整报告放在 `benchmark/raw/`，`validate.py` 第 29 条核对它和 `results.json` 一致。
- 榜单说明里的结论改为由数据计算，不再手写：标题里的比例、最常见的缺口、以及哪些检查项拉开了中文市场的差距。这个差距是 20 分
  （95% 置信区间 16–28），差得最多的两项是启发式判断，而在人工审计对照里唯一的中文站上，CLI 这两项也比人工判得低；说明里写明了这一点。
- 两份 README 的榜单链接改到 www.jianruntech.com/leaderboard（持续更新）；组织的 Actions 与 Pages 被停用期间，GitHub Pages 上的副本无法重建。

## [1.3.0] — 2026-09-27

这一版关乎测量是否可信：CI 系统能直接读的输出、做前后对比用的固定抽样、不再把噪声判成变化的变化检测、12 个测试站点上的离线端到端测试、
实测的 CLI 与人工审计一致度，以及每个检查项的证据依据。测试站点还找出了 CLI 读错网站、与量表不符的地方（robots.txt 分组规则、单页应用的兜底页面、空的结构化数据、过期的 `dateModified`、署名、
中文里的日期和数字），这些都已修正，并在下面注明分数变化的方向。百分比不再可能超过 100；MCP 服务的每个连接都只到公网地址。

**从 1.2.0 升级。** 第一级的分数只在某项检查读错了网站时变化；每一处修正及其方向都列在「修复」下，公开榜单（用 1.1.0 测量）不重新评分。`watch` 里，标题引用率不再计入提到品牌的问题；
同一问题有多条回答时区间变宽；部分原先判为 `change` 的 `diff` 结论会变成 `within noise` 或 `too few questions to tell`，
1.2.0 的字段含义保持不变。证据里引用的网站原文现在包在 `«site text: …»` 里。CSV 报告多了第 11 列 `branded`。

### 新增
- **一次运行，多种输出**：`--json-out FILE`、`--sarif FILE`（SARIF 2.1.0：每个检查项一条规则，没拿满分的项各一条结果）、
  `--junit FILE`（每个检查项一个测试；0 分为失败，测不到的项跳过）。都和屏幕上的报告来自同一次抓取，不会互相对不上。
  只支持单站。
- **可以装成命令**：新增 `pyproject.toml`，`pipx install git+https://github.com/jianruntech/geo-score` 和
  `uvx --from git+… geo-score` 都能用。装好后有 `geo-score` 和 `geo-score-mcp`（stdio MCP 服务）两个命令。仍然零依赖。
- `STABILITY.md`：写明哪些是公开约定（检查项 id、计分算法、两份 JSON schema、命令行参数、退出码、Action 输入输出、
  MCP 工具名、SARIF 规则 id）、这里的语义化版本指什么，以及不向任何地方发送数据（无遥测）。
- Action 新增输入 `sarif`、`junit`、`annotations`，新增输出 `gate-capped`、`report-path`。
- **固定抽样页面**：`--urls FILE` 只给指定的页面打分（最多 8 个，必须在被评的站内）；`--urls-from REPORT.json`
  读取之前某份报告抽到的页面重新评分。抽样是两次运行分数不同的主要原因，固定页面做前后对比，看到的才是站点本身的变化。
  报告里 `sample_source` 为 `"pinned"`。Action 新增输入 `urls-from`。
- **每个检查项都有文档链接**：JSON 报告里每个检查项带 `doc_url`，指向量表里该项的定义，并锁定到发布版本的 tag，
  链接不会和评分代码脱节。SARIF 规则也指向这里，`--explain` 会在每个未拿满分的检查项下打印它。已作为可选字段写入 `schema/report.v2.json`。
- 新增[排查指南](guide/troubleshooting.zh-CN.md)（中英两份）：分数波动、显示 `—` 的检查项、门槛封顶、退出码 2、代理、跳转、
  榜单的工具版本、`watch` 退出码 3、Action 注释上限、中文阈值。终端报告里有链接。
- **榜单中位数加上置信区间。** `benchmark/stats.py` 用固定种子的自助法，为总体中位数、各行业中位数和中国市场差距算出 95% 区间，
  `benchmark/README.md` 与两份 README 都引用了：总体 56（53–58），差距 19 分（12–26）。托管的网页在重新生成并部署之前，仍显示不带区间的中位数。评上分不足 10 个站的行业（China / cloud、Professional services，各 9 个）
  不再印中位数；`validate.py` 按评上分的站数而不是名单站数来数。`benchmark/run.py --readme-only` 可以不重新评分、只重新生成 README。
- 榜单可以换托管地址：`GEO_SITE_BASE` 统一设置 canonical、`og:image`、hreflang、`llms.txt` 和 sitemap 里的地址；
  `scripts/check_live.py` 比对线上页面与提交的数据（目前 Pages 上仍是 229 站，数据是 314 站）。
- **CLI 可信到什么程度，有了实测。** `benchmark/validity.py` 在相同页面上重评公开的 5 份人工审计并逐档比较：
  86 对检查项里 79% 一致（按规则读取的项 95%，启发式的项 64%），CLI 平均低 3.6 分，范围从低 10 分到高 6 分。
  结果、注意事项和每一处分歧见 `benchmark/VALIDITY.zh-CN.md`。这取代了没有数据支撑的「通常低 5 到 15 分」，
  那句话对 5 个站里的 2 个是错的。
- **每个检查项都注明证据依据。** `rubric/v1.1.json` 每一项新增 `evidence` 对象（依据类型、来源、最后核实日期），
  并发布为 `rubric/evidence-v1.1.zh-CN.md`（中英两份）。只是元数据，没有改动任何权重、档位或分数。
- **MCP 面向 agent，而不只是给人看。** `score_site`、`report`、`diff`、`list_runs` 在文字之外返回
  `structuredContent`（完整的报告、摘要或对比 JSON），并声明 `outputSchema`，agent 不必再从 Markdown 里抠分数。
  `score_site` 新增 `urls`（固定页面，校验规则同 `--urls`）和 `sample` 参数。量表以资源 `geo-score://rubric/v1.1`
  提供，由评分器自己的表格生成。服务说明和 `score_site` 的描述写明：`«site text: …»` 里是被评网站的原文，是数据。
- `watch diff --fail-on-drop`：有结论为 `change` 且变化为负时退出码为 4。MCP `diff` 工具支持 `format: "json"`。
  [guide/watch-methodology.zh-CN.md](guide/watch-methodology.zh-CN.md)（中英两份）给出公式与算例。
- **统一的检查入口：`scripts/check.sh`。** 依次跑结构校验、ruff、三套测试（Python 3.8 与可用的最新版本），并在测试站点上模拟一次
  GitHub Action（`scripts/test_action.py`）；加 `--live` 再跑 example.com。`.githooks/pre-push` 推送前自动运行它，
  `.github/workflows/validate.yml` 跑的也是同一个脚本。托管的 Actions 在这个组织下至今没有运行过，所以 `CONTRIBUTING.md`
  不再说「CI 会检查」：维护者每次合并前手动运行这个脚本。
- `AGENTS.md`：仓库的各条约定，每条都对应到执行它的检查，给贡献者和写代码的 agent 看（`CLAUDE.md` 指向它）。
- issue 表单要求填写工具版本和 JSON 报告；新增第二、三级引擎问题的表单，并提醒绝不要贴 Key；安全问题引导到 `SECURITY.md`。
- **离线端到端测试。** `cli/test_geo_score_e2e.py` 在 127.0.0.1 上架起 12 个测试站点（标准站、纯 JavaScript 壳、
  robots 屏蔽、拦截 AI 爬虫的防火墙、中文站、路径下的站点、试图对 agent 下指令的恶意站点等），逐项核对每个检查项的档位
  与各站的 `expected.json`，并比对一份基准报告。有任何请求离开本机即判失败；整套不到一秒。
- 新增测试：CLI 内置的量表（检查项 id、分值、每一档的分值与文字、档位线、封顶、加分项）必须与 `rubric/v1.1.json` 完全一致。

### 变更
- **`watch diff` 改为配对比较、按问题聚类，并做多重比较校正。** 只比较两次运行都回答了的问题，每一行做精确配对检验
  （每题每次只有一条回答时为 McNemar，否则为按每题净变化的精确符号翻转检验），并对各引擎行与「全部引擎」行做 Holm 校正。
  校正后 p < 0.05 才判为 `change`；共同问题少于 6 个时判为 `too few questions to tell`。1.2.0 对并不独立的回答
  用了非配对的双比例检验，容易把噪声判成变化。新增字段：`p_paired`、`p_adjusted`、`n_pairs`、`n_questions`、`n_asks`、
  `before_paired`、`after_paired`、`delta_pp`、`delta_ci`。`before`、`after`、`delta`、`p_value` 保持 1.2.0 的非配对含义，结论不再使用它们。
- **区间考虑重复提问。** 每个比率块新增 `cited_ci_clustered`（按问题重抽样 2,000 次、固定种子，不窄于 Wilson）和
  `n_questions`；只要有问题得到多条回答，报告就引用它。`cited_ci`（Wilson）不变。
- **标题数字排除提到品牌的问题。** 运行时用回答所用的匹配器给问题打标（`brand_in_query`、`competitor_in_query`），
  标题只统计其余问题，提到品牌的问题单列一行并给出各自的 n。`queries.csv` 可选 `branded` 列（`auto`、`yes`、`no`）
  可覆盖打标；超过 30% 的问题提到品牌时 `watch check` 会警告；CSV 报告末尾新增 `branded` 列。
- **Action 只评一次分。** 以前要抓取并评分两遍（一遍出 JSON，一遍出日志），耗时翻倍，两遍的分数还可能不同。
  现在任务摘要、代码注释和所有文件都来自同一次运行。
- Action 会给 0 分的检查项加注释：门槛项标为 error，其他项标为 warning（GitHub 每种最多显示 10 条，其余见任务摘要）。
- `geo-score watch --help` 显示的命令名跟随你实际输入的命令（pip 安装后是 `geo-score`）。
- `--compare` 对比三个及以上站点时，不再写「Both scored」。
- 网站跳转到另一个域名时，完整报告会写明，JSON 里带 `landed`（可选），即实际评分的地址。

### 修复
- **离线测试站点发现的计分修正。** 每一处都只在旧读数违背量表时改变分数：
  - `g.robots`：多行 `User-agent` 共享其后的规则（RFC 9309 2.1）。此前规则只挂在最后一行上，同一组里列出 GPTBot、ClaudeBot、
    CCBot 并写 `Disallow: /` 的文件，会被读成只屏蔽了 CCBot。分组规则屏蔽了检索爬虫的站下降，降到 0 分并触发门槛封顶；
    分组里的 `Allow` 现在算作明确许可的站上升（3 到 5）。
  - `p1.llms-txt`、`b.llms-full`、`b.ai-txt`、`p1.sitemap`：对所有路径都返回 HTML 外壳的单页应用，不再算作提供了这些文件；
    sitemap 必须是带 `<urlset>` 或 `<sitemapindex>` 的 XML。下降。robots.txt 里写成相对路径的 `Sitemap:` 按域名补全（现在能加载到的上升）。
  - `p1.organization`：Organization 和 WebSite 都有但缺 name、url、logo 时按量表给 3 分，不再给 5 分（下降）；
    相对路径的 logo 按它所在的页面解析（现在能加载到的上升）；Organization 的子类型（EducationalOrganization、
    NewsMediaOrganization、LocalBusiness 等）也读取 logo 和 sameAs，这样标注的站 `p1.organization` 和 `p3.sameas` 上升。
    不是 http(s) 地址的 `sameAs` 值不再去请求。
  - `p1.page-type`：最高档要求真实的字段值；只有 `{"@type": "Product"}` 的空壳给 2 分。下降。
  - `p2.freshness`：紧贴中文的日期、英文月份写法的日期都能读到（上升）；最高档要求在声明了 `dateModified` 的页面里，
    至少四分之三的 `dateModified` 不早于页面自己的日期（datePublished、article 时间或正文中的第一个日期），否则下降。
  - `p2.sourced-stats`：「resources」不再算作「source」（下降）；紧贴中文的数字算作数字（可升可降）。
  - `p2.named-author`：「Editor」、机构自己的名字、页脚的「Powered by Hugo」都不算个人署名。下降。
  - 抽样：对位于某个路径下的站点，不再抽到同级的兄弟目录（`/docs` 之于 `/docs-legacy`）；站点根目录没有 sitemap 时使用路径下的 sitemap。
- **SARIF 可以上传到 GitHub 代码扫描了。** 此前结果定位在被评网站的 URL 上，代码扫描会拒收；现在每条结果指向 JSON 报告里该检查项所在的行
  （设置 `sarif` 时 Action 会把报告写进工作区），网站名写在 message 里。
- `watch diff` 在问题数相对比较行数太少时不再写 `within noise`：Holm 校正之前，m × 2 / 2^n ≥ 0.05 的行（m 行、n 个问题；
  Tarone 筛选）判为 `too few questions to tell` 并退出比较组。这道筛选是保守的。调用不存在的 MCP 工具返回 JSON-RPC 错误（-32602），符合协议规定。
- **分数可能超过 100。** 加分项不进分母，满分或接近满分的站加上加分项会读到 100 以上（good 测试站读到 107），连报告 schema（`normalised` ≤ 100）都不满足。
  现在百分比封顶 100，量表第 5 条也写明了。已发布的分数都不受影响：榜单最高 98，人工审计最高 87。这个问题是离线测试站点发现的。
- `--json-out`、`--sarif`、`--junit` 写不进去时给出明确的报错（退出码 2），不再抛出回溯。
- 拉丁字母品牌名紧贴中日韩文字时（「用Lumo做视频」）现在算作提及，此前从未匹配。因此新运行在这类回答上的 `mentioned`
  比率可能高于之前的运行。
- 1.2.0 保存的运行文件仍可读取；报告会重算摘要，并根据保存的问题文本计算品牌标记，同时加注说明。
- 几处文档仍在描述已废止的门槛规则：`rubric/README.md`、中文校准记录、`SKILL.md` 和示例报告写的是「门槛项未拿满就封顶」。
  v1.1 起的规则是门槛项**得 0 分**才封顶。分数一直是按正确规则算的；`validate.py` 现在会拦下任何没写「得 0 分」条件的封顶表述。
- 校准记录把结构化数据的采纳率（BreadcrumbList 5.66%、Product 0.77%、FAQPage 0.34%）写成出自 2025 年版 Web Almanac，
  实际出自 2024 年版。只有 llms.txt 的 2.13% 出自 2025 年版。
- 中文校准记录漏了英文版里的两条事实（60 KB 服务端渲染正文、Foglift 的上四分位），新增检查比对两份里的数字。

### 安全
- **MCP 服务的每一跳连接都只能到公网地址。** 1.2.0 只检查 agent 传入的那个 URL，之后的请求一概不查：被评网站可以借跳转、
  `sameAs` 链接、logo 或声明的 sitemap，让评分器访问本机或内网地址；而且检查放过了运营商级 NAT 网段（100.64.0.0/10，
  100.100.100.200 这样的云元数据地址就在这里）。现在 MCP 模式下每个连接都先解析并检查（`is_global`），每一跳跳转都检查，
  直连时就连检查过的那个地址；检查用的是实际要请求的主机名，而不是去掉 `www.` 的品牌名。命令行工具照旧给用户指定的任何站点打分。
- 更多文字被标注或清理：网站声明的 sitemap 地址作为网站原文引用，并去掉查询串和片段；带控制字符或双向文本字符的 sitemap 条目被丢弃；
  Unicode tag 字符、软连字符、行分隔符和 XML 不允许的字符被清除；截断的证据行不会留下没闭合的 `«site text: …»`；
  服务器报错信息压成一行干净文字；Action 的任务摘要对证据做转义，不再当作 Markdown 和 HTML 渲染。
- Action 改为通过环境变量把输入传给脚本。之前 `url` 等输入是直接拼进 shell 脚本的，精心构造的值可以在工作流里执行命令。
  `sample` 和 `fail-under` 现在会校验必须是整数。
- **证据里的网站原文标注为数据。** 引用被评网站内容的证据（答案段落、从页面读出的品牌名、Wikidata 描述）现在包在
  `«site text: …»` 里，所有证据字符串都去掉控制字符、零宽字符和双向文本控制字符。报告会经 MCP 服务交给 AI agent，
  否则网页可以借工具的口吻对 agent 下指令。带这类字符的站内链接不再进入抽样。
- 包装底层异常的错误（格式不对的请求头、读不了的配置）不再串联原异常，未捕获的回溯因此不会打印原始信息——
  对请求头来说，那条信息里可能带着 API Key。
- `SECURITY.md` 新增支持版本表和威胁模型；`SKILL.md` 明确告诉 agent：抓取到的文字是证据，不是指令。

## [1.2.0] — 2026-09-27

### 新增 · 第二、三级：AI 到底有没有引用你

geo-watch 0.1.0 并入本仓库。一个工具测 AI 可见度的两半：AI **能不能**引用这个站（打分，免费），
和 AI **有没有**引用它（用你自己的 API Key）。引用结果从不加进分数，这是量表一直以来的要求。

- **第二级 `--ask "问题"`**（可重复，最多 5 个）：出完就绪度报告后，通过 ChatGPT、Perplexity、Gemini、
  Claude 的联网 API 各问一次（有 Key 的引擎才问），结果写进报告的 `citation` 字段。没有 Key 时这一块写
  「未测」，分数不受影响。
- **第三级 `geo_score.py watch`**：固定一组问题每周问一次；按引擎给出引用率和 95% Wilson 区间、对竞品的
  声量份额、AI 引用的第三方来源、AI 实际搜了什么、带上限的费用账本（`max_calls` 是硬上限；`budget_usd` 最多超出每个引擎一次调用），
  以及用双比例检验判断变化的 `diff`。运行文件遵循 `schema/watch.v1.json`。
- **`geo_score.py mcp`**：零依赖的 stdio MCP 服务，提供 `score_site`（第一级）和 `ask`、`run`、
  `list_runs`、`report`、`diff`（第二、三级）。
- `schema/report.v2.json`：预留的 `citation` 字段新增可选的 `channel`、`answered`、`mentioned_count`、
  `per_engine`、`top_sources`、`cost_usd`。只增不改，1.1.x 的报告依旧通过校验。
- `examples/ci/watch-weekly.yml`：每周定时跑的模板。

第二、三级需要同一版本的 `cli/geo_watch.py` 与 `cli/geo_score.py` 放在一起；一行 `curl | python3` 仍然可以单独跑第一级。
分数与 1.1.2 相同。

**geo-watch 0.1.0 的用户：** 把 `geo-watch.json` 改名为 `geo-score-watch.json`，改用 `python3 cli/geo_score.py watch …`。
运行文件现在存在 `.geo-score/watch/runs/`，格式是 `geo-score/watch.v1`，0.1.0 的运行文件不再读取。CSV 导出里
`competitors_cited` 改名为 `other_domains_cited`，一直为空的 `wrong_fact` 列删除。

## [1.1.2] — 2026-09-25

### 变更 · 分数会变

同一台机器连跑两次，一个站得了 88 和 95，另一个站三次得了 71、40、71——都超出了本仓库承诺的 ±5。
原因有三个，原则只有一条：**网络连不上，不等于东西不存在。**

- **p3.sameas** 把所有非 200 都算死链。现在超时、连接重置、451（LinkedIn、X、YouTube、GitHub、维基百科在中国大陆都连不上）
  和反爬墙（Crunchbase、知乎、Facebook、LinkedIn 返回的 401 / 403 / 429 / 999）不计入，只有 404 / 410 算死链；
  一个都测不到时整项移出分母，而不是记 0。同样 12 个资料页，大陆网络能解析 1 个，境外网络能解析 9 个。
- **p3.knowledge-graph** 在 Wikidata / 维基百科**部分**查询超时、其余没找到时记 0。现在只有所有查询都应答了才能判定「没有」，
  部分应答记为不可观测。（全部失败本来就记不可观测。）
- **采样**只抓一次 sitemap。一次请求失败，采样就改用首页链接，换了八个页面，中间那次跌破 g.ssr 门槛被封顶 40。
  现在首页、robots.txt、sitemap、栏目索引与被采样页遇到超时、429、5xx 会重试；报告里新增 `sample_source` 字段。

修改后各跑三次：jianruntech.com 直连 95 / 95 / 95，境外 93 / 93 / 95；stripe.com 直连 75 / 75 / 75，境外并发 70 / 72 / 70。
**已发布的榜单是 2026-09-09 用修改前的逻辑测的，这次没有重跑。** sameAs 或知识图谱查询碰到连不上的站点的，
今天重新打分可能比榜单上高几分。报告里的工具版本现在是 `geo-score-cli/1.1.2`，可以据此区分两者。

### 修复
- **gzip 炸弹。** 原来 4 MB 的读取上限卡的是压缩后的数据，而 `gzip.decompress` 不限制解压后的大小，
  几 MB 构造好的 gzip 能解出几 GB，直接把进程打崩——在 GitHub Action 的运行器上就是内存溢出，而不是一个分数。
  现在解压后最多 16 MB，真实页面远用不到这么多。**不影响任何分数。**

## [1.1.1] — 2026-09-09

量表变成了能直接跑的工具。本节根据该 tag 的提交历史补记；这个版本发布时没有写更新日志。

### 新增
- **CLI**（`cli/geo_score.py`）：只用标准库，一条命令、无需安装；给静态抓取能观测到的 17 项打分，其余移出分母。
  每一项都写明上一档要什么、值几分，报告列出最大的几个缺口。
- **GitHub Action**（`uses: jianruntech/geo-score@v1`），CI 可用 `--fail-under`，以及浮动的 `v1` 标签。
- `--compare URL` 与竞品并排打分；`--badge` 生成可嵌入的 SVG 徽章；`--share` 输出一行摘要。
- **公开基准**：266 个知名站点中 229 个用同一套量表打分，门槛失效分成主动与无意两类；榜单页由数据生成，中英两版，带分享卡。

### 修复
- 位于某个路径下的站点（项目页、文档子目录）在该路径内抽样。
- 解析 `@graph` 里的 `@id` 作者引用；此前有作者的页面会被判成没有作者。
- 非 ASCII 域名在发出第一个请求前就崩溃。
- examples 索引里 22 条坏链接；CI 开始检查站内链接。

## [1.1.0] — 2026-09-08 · 重新标定

v1.0 把 anthropic.com 判为 *Critical*，而该站对十个检索爬虫全部返回 200、
正文服务端渲染完好。问题在量表不在站点。完整依据见
[rubric/calibration-v1.1.md](rubric/calibration-v1.1.md)。

### 变更

- **两个分数拆开**。「站点就绪度」（站方可修，本量表打分的对象）与
  「AI 引用表现」（结果型，天然低）不再合并。
- **二元改阶梯**。21 个计分项全部拆成 2–4 档，取证据满足的最高档。
  这是 v1.0 区分度塌陷的主因。
- **判定看实质不看格式**。标题匹配提问意图不再要求问号，任务句与说明句同等计入；
  时间信号接受页面可见日期或 schema 日期；自足答案段放宽到 25–120 词
  （中文 50–200 字）且不限定首段。
- **站外不可观测项移出主分**。Search Console／Bing 验证状态、多引擎实测四项
  离开 100 分基数，改为「授权后可测」的不计分区块。
- **新兴约定降权**。`ai.txt`、`speakable`、GEO link 标签、`llms-full.txt`
  从 13 分计入分母改为不进分母的加分项，封顶 +6。
- **门槛项**。`g.robots`、`g.reachable`、`g.ssr` 计分，同时任一未拿满则总分封顶 40
  并置顶为 P0。
- **档位改五档，档名用阶段语义**。「危急」删除，CI 拦截判决式档名。
- **公开／实施边界收紧**。修法、工作量、承担角色不再出现在公开量表，CI 强制。
  公开的量表说测什么与为什么，实施层不在本仓库。

### 兼容性

v1.0 与 v1.1 的分数**不可直接比较**。v1.0 的量表与已发布的五份审计保持原样，
不做追溯改写。`examples/audits/` 里仍是 v1.0 审计；按 v1.1 重跑的真实审计尚未进行。

### 被这一版定掉的

[rubric/open-questions.md](rubric/open-questions.md) 里公开的 8 条口径歧义全部有了决定。


## [1.0.0] — 2026-09-08

打了 tag 但没有对外发布；几个小时后未通过自己的校准检查，被 1.1.0 取代。保留发布是为了让这次修正可以追溯。
量表 v1.0：5 个支柱共 **29 项检查**，名义满分 100，每项有达标条件和计分类型，三态计分与分数段；附 `SKILL.md`、
AI 爬虫 UA 列表、各引擎选源方式说明和示例报告。详细条目见[英文版](CHANGELOG.md#100--2026-09-08)。

[Unreleased]: https://github.com/jianruntech/geo-score/compare/v1.6.0...HEAD
[1.6.0]: https://github.com/jianruntech/geo-score/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/jianruntech/geo-score/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/jianruntech/geo-score/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/jianruntech/geo-score/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/jianruntech/geo-score/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/jianruntech/geo-score/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/jianruntech/geo-score/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jianruntech/geo-score/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jianruntech/geo-score/releases/tag/v1.0.0
