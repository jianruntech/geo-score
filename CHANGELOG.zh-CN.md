# 更新日志

英文版：[CHANGELOG.md](CHANGELOG.md)。**量表**的版本号与仓库版本号分开，见 `rubric/`。

## [Unreleased]

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
  86 对检查项里 78% 一致（按规则读取的项 95%，启发式的项 62%），CLI 平均低 4.2 分，范围从低 13 分到高 6 分。
  结果、注意事项和每一处分歧见 `benchmark/VALIDITY.zh-CN.md`。这取代了没有数据支撑的「通常低 5 到 15 分」，
  那句话对 5 个站里的 1 个是错的。
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

### 修复
- **离线测试站点发现的计分修正。** 每一处都只在旧读数违背量表时改变分数：
  - `g.robots`：多行 `User-agent` 共享其后的规则（RFC 9309 2.1）。此前规则只挂在最后一行上，一个在同一组里屏蔽
    GPTBot、ClaudeBot、PerplexityBot 的文件会被读成什么都没屏蔽。以这种方式屏蔽的站会下降，降到 0 分并触发门槛封顶。
  - `p1.llms-txt`、`b.llms-full`、`b.ai-txt`：对所有路径都返回 HTML 外壳的单页应用，不再算作提供了这些文件。下降。
  - `p1.organization`：Organization 和 WebSite 都有但缺 name、url、logo 时按量表给 3 分，不再给 5 分（下降）；
    相对路径的 logo 按它所在的页面解析（现在能加载到的上升）。
  - `p1.page-type`：最高档要求真实的字段值；只有 `{"@type": "Product"}` 的空壳给 2 分。下降。
  - `p2.freshness`：紧贴中文的日期、英文月份写法的日期都能读到（上升）；最高档要求 `dateModified` 不早于页面显示的日期（早于的下降）。
  - `p2.sourced-stats`：「resources」不再算作「source」（下降）；紧贴中文的数字算作数字（可升可降）。
  - `p2.named-author`：「Editor」、机构自己的名字、页脚的「Powered by Hugo」都不算个人署名。下降。
  - 抽样：对位于某个路径下的站点，不再抽到同级的兄弟目录（`/docs` 之于 `/docs-legacy`）；站点根目录没有 sitemap 时使用路径下的 sitemap。
- **SARIF 可以上传到 GitHub 代码扫描了。** 此前结果定位在被评网站的 URL 上，代码扫描会拒收；现在每条结果指向 JSON 报告里该检查项所在的行
  （设置 `sarif` 时 Action 会把报告写进工作区），网站名写在 message 里。
- `watch diff` 在问题数相对比较行数太少时不再写 `within noise`：经 Holm 校正后最好的 p 也不低于 0.05 的行，判为
  `too few questions to tell`。调用不存在的 MCP 工具返回 JSON-RPC 错误（-32602），符合协议规定。
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

[Unreleased]: https://github.com/jianruntech/geo-score/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/jianruntech/geo-score/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/jianruntech/geo-score/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/jianruntech/geo-score/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/jianruntech/geo-score/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jianruntech/geo-score/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jianruntech/geo-score/releases/tag/v1.0.0
