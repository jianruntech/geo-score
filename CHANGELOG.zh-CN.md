# 更新日志

英文版：[CHANGELOG.md](CHANGELOG.md)。**量表**的版本号与仓库版本号分开，见 `rubric/`。

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


---

更早的条目见[英文版](CHANGELOG.md)。
