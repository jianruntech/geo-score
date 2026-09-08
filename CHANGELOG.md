# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/).
The **rubric** is versioned separately from the repository — see `rubric/`.

## v1.1 — 重新标定

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

## [Unreleased]

## [1.0.0] — 2026-09-08

First tagged release. The repository was pushed a few hours earlier without a tag;
the rubric was corrected before this tag, so v1.0 as released here is the only v1.0.
Corrections made in that window are listed under *Fixed before first tag*.

### Added
- Rubric v1.0: **29 checks** across 5 pillars, 100 nominal points, with pass conditions,
  an explicit Credit type per check, three-state scoring, and score bands
- `SKILL.md` — Claude Code skill that runs the rubric
- `reference/ai-crawlers.md` — the AI user-agent list Pillar 1 checks against
- `reference/platform-source-selection.md` — how each engine selects sources
- `examples/sample-report.md`

### Fixed before first tag
- **Crawler classification was wrong.** `Google-Extended` and `Applebot-Extended` were
  listed as retrieval crawlers. They are opt-out tokens — they send no requests, and
  blocking them costs no citations. The real retrieval crawler `Applebot` was missing
  entirely. Net effect was inverted: blocking a harmless token lost points, blocking a
  real crawler did not.
- **Anthropic's retrieval agents were missing.** `Claude-SearchBot` and `Claude-User`
  were absent; only the training crawler `ClaudeBot` was listed. A site blocking both
  retrieval agents could still score full marks.
- **Added a reachability check.** `robots.txt` states an intention; the edge decides.
  A WAF returning 403 to `OAI-SearchBot` while `robots.txt` says `Allow` was previously
  a perfect score.
- **Pillar 5 scored procedure, not outcome.** "A query test was performed" is now
  "cited in N of 3 engines" — being cited nowhere scores zero.
- **No rule for inapplicable or unobservable checks.** A brand site with no articles lost
  points for having no `Article` schema. Scores now report `score / observable max` and
  band on the normalised percentage.
- **Partial-credit rule contradicted the sample report.** Every check now carries an
  explicit `prop.` or `all/none` Credit value, with `floor()` rounding stated.
- **The sample report did not add up** — a pillar subtotal was 2 points above its line
  items. CI now validates the arithmetic of every report block in the repo.

### Scope note
Remediation (fix templates, content rewriting, per-engine tactics) is deliberately
out of scope. See [Scope](README.md#scope--what-this-does-not-do).
