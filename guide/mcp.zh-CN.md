# geo-score MCP 服务

怎样把 geo-score 接进各个 Agent 客户端，以及这个服务做什么、不做什么。English: [mcp.md](mcp.md)

`geo-score-mcp`（在克隆的仓库里是 `python3 cli/geo_score.py mcp`）是一个走 stdio 的本地 MCP 服务，
和命令行是同一份代码：只用标准库，Python 3.8 及以上。它提供：

- **工具**，对应三级用法：`score_site`（第一级，免费）、`ask`（第二级），以及 `run`、`list_runs`、`report`、
  `diff`（第三级）。从 1.4.0 起还有 `status`；
- **一个资源** `geo-score://rubric/v1.1`：打分器实际执行的每一项检查、分值与档位、分数段和封顶规则；
- **提示词**（从 1.4.0 起）：`audit_site`、`check_citations`、`weekly_watch`、`compare_runs`、`explain_check`。

[安装](#安装) · [各客户端配置](#各客户端配置) · [其他安装方式](#其他安装方式) · [工具](#工具) ·
[选择暴露哪些工具](#选择暴露哪些工具) · [提示词](#提示词) · [配置与 Key](#配置与-key) ·
[超时与取消](#超时与取消) · [协议版本](#协议版本) · [安全](#安全) · [排查](#排查)

## 安装

<!-- BEGIN MCP:install -->
<!-- 由 scripts/mcp_docs.py 按版本 1.3.0 生成；要改请改脚本，不要改这一段。 -->

[![Add geo-score to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=geo-score&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL2ppYW5ydW50ZWNoL2dlby1zY29yZUB2MS4zLjAiLCJnZW8tc2NvcmUtbWNwIl19)
[![Install geo-score in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522geo-score%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522--from%2522%252C%2522git%252Bhttps%253A%252F%252Fgithub.com%252Fjianruntech%252Fgeo-score%2540v1.3.0%2522%252C%2522geo-score-mcp%2522%255D%257D)
[![Install geo-score in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522geo-score%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522--from%2522%252C%2522git%252Bhttps%253A%252F%252Fgithub.com%252Fjianruntech%252Fgeo-score%2540v1.3.0%2522%252C%2522geo-score-mcp%2522%255D%257D)
[![Add geo-score to LM Studio](https://img.shields.io/badge/LM_Studio-Install_Server-4338CA?style=flat-square)](https://lmstudio.ai/install-mcp?name=geo-score&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL2ppYW5ydW50ZWNoL2dlby1zY29yZUB2MS4zLjAiLCJnZW8tc2NvcmUtbWNwIl19)

按钮和下面几行用 `uvx` 安装 geo-score **1.3.0**，需要先装 [uv](https://docs.astral.sh/uv/)。不带任何 Key：第一级可用；在你把服务商 Key 交给服务之前，`ask` 和 `run` 花不了任何钱。

**Claude Code**

```bash
claude mcp add --scope user geo-score -- uvx --from git+https://github.com/jianruntech/geo-score@v1.3.0 geo-score-mcp
```

**标准配置**（第一级，免费，不要 Key），适用于任何读取 `mcpServers` 配置文件的客户端：

```
{
  "mcpServers": {
    "geo-score": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jianruntech/geo-score@v1.3.0", "geo-score-mcp"]
    }
  }
}
```

Claude Desktop 不读你 shell 里的 `PATH`：`command` 请填 `which uvx` 输出的完整路径。
<!-- END MCP:install -->

下面每个客户端跑的都是同一条命令。要用第三级工具，就在参数里加上 `-c /绝对路径/geo-score-watch.json`
（[原因](#配置与-key)）；只有要用 `ask` 和 `run` 时才需要给它 Key。

## 各客户端配置

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add --scope user geo-score -- uvx --from git+https://github.com/jianruntech/geo-score@v1.3.0 geo-score-mcp
```

带上 watch 配置，并把工具超时设为十分钟，免得较长的 `run` 被中途切断：

```bash
claude mcp add-json --scope user geo-score '{"type":"stdio","command":"uvx","args":["--from","git+https://github.com/jianruntech/geo-score@v1.3.0","geo-score-mcp","-c","/absolute/path/geo-score-watch.json"],"timeout":600000}'
```

在启动 `claude` 的那个 shell 里 export 的 Key，通常能传到服务里。`--env NAME=value` 也可以，但会把 Key 明文写进
`~/.claude.json`。`claude mcp list` 显示服务有没有连上，会话里输入 `/mcp` 可以看到它的工具。

</details>

<details>
<summary><b>Claude Desktop</b></summary>

设置 → Developer → Edit Config 会打开 `claude_desktop_config.json`
（macOS 是 `~/Library/Application Support/Claude/claude_desktop_config.json`，
Windows 是 `%APPDATA%\Claude\claude_desktop_config.json`）。

Claude Desktop 启动服务时既没有你 shell 里的 `PATH`，也没有你在 shell 里 export 的变量。所以 `command`
要写 `which uvx` 输出的绝对路径，Key 写在 `env` 里：

```
{
  "mcpServers": {
    "geo-score": {
      "command": "/Users/you/.local/bin/uvx",
      "args": ["--from", "git+https://github.com/jianruntech/geo-score@v1.3.0", "geo-score-mcp",
               "-c", "/Users/you/acme/geo-score-watch.json"],
      "env": {"OPENAI_API_KEY": "sk-...", "PERPLEXITY_API_KEY": "pplx-..."}
    }
  }
}
```

只用第一级就不要写 `env`。写进 `env` 的 Key 以明文存在这个文件里；[MCPB 扩展](#claude-desktop-扩展mcpb)
改用表单填 Key。Windows 上 `command` 写 `uvx.exe` 的完整路径。改完文件要重启 Claude Desktop。

</details>

<details>
<summary><b>Codex</b></summary>

写在 `~/.codex/config.toml`，或项目里的 `.codex/config.toml`：

```toml
[mcp_servers.geo-score]
command = "uvx"
args = ["--from", "git+https://github.com/jianruntech/geo-score@v1.3.0", "geo-score-mcp",
        "-c", "/absolute/path/geo-score-watch.json"]
# 从 Codex 所在的环境透传过去
env_vars = ["OPENAI_API_KEY", "PERPLEXITY_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"]
startup_timeout_sec = 60   # 第一次启动要下载并构建这个版本
tool_timeout_sec = 600     # Codex 默认 60 秒；一次 run 可能更久
```

`codex mcp add geo-score -- uvx --from git+https://github.com/jianruntech/geo-score@v1.3.0 geo-score-mcp`
会写好前三行，其余手动补上。

</details>

<details>
<summary><b>Cursor</b></summary>

点上面的按钮，或者手动写进 `~/.cursor/mcp.json`（所有项目）或 `.cursor/mcp.json`（单个项目）：

```
{
  "mcpServers": {
    "geo-score": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jianruntech/geo-score@v1.3.0", "geo-score-mcp",
               "-c", "${workspaceFolder}/geo-score-watch.json"],
      "env": {"OPENAI_API_KEY": "${env:OPENAI_API_KEY}", "PERPLEXITY_API_KEY": "${env:PERPLEXITY_API_KEY}"}
    }
  }
}
```

`${env:NAME}` 从 Cursor 自己的环境里取变量，Key 不落进文件。`${workspaceFolder}` 是当前打开的项目。

</details>

<details>
<summary><b>VS Code</b></summary>

点上面的按钮，或者写进工作区的 `.vscode/mcp.json`（命令 **MCP: Open User Configuration** 打开的是对所有工作区
生效的那份）。VS Code 的顶层键是 `servers`，不是 `mcpServers`；`inputs` 会问你一次 Key 并替你保存：

```
{
  "inputs": [
    {"type": "promptString", "id": "openai-key", "description": "OpenAI API key (optional, for ask and run)", "password": true}
  ],
  "servers": {
    "geo-score": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jianruntech/geo-score@v1.3.0", "geo-score-mcp",
               "-c", "${workspaceFolder}/geo-score-watch.json"],
      "env": {"OPENAI_API_KEY": "${input:openai-key}"}
    }
  }
}
```

用几家服务商就加几个 input。留空的那家引擎记为未测。

</details>

<details>
<summary><b>Gemini CLI</b></summary>

写在 `~/.gemini/settings.json`，或项目里的 `.gemini/settings.json`。Gemini CLI 交给 MCP 服务的环境里，
名字含 `KEY`、`TOKEN`、`SECRET` 之类的变量都会被去掉，所以每个 Key 都得在 `env` 里列出来，`$NAME` 从你的环境里取值：

```
{
  "mcpServers": {
    "geo-score": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jianruntech/geo-score@v1.3.0", "geo-score-mcp",
               "-c", "/absolute/path/geo-score-watch.json"],
      "env": {"OPENAI_API_KEY": "$OPENAI_API_KEY", "GEMINI_API_KEY": "$GEMINI_API_KEY"}
    }
  }
}
```

只列你确实 export 了的 Key。Gemini CLI 默认等一次工具调用十分钟，用 `"timeout"`（毫秒）可以改。

</details>

<details>
<summary><b>Devin Desktop（原 Windsurf）</b></summary>

macOS 和 Linux 是 `~/.config/devin/mcp_config.json`，Windows 是 `%APPDATA%\devin\mcp_config.json`。
改名之前的 Windsurf 用的是 `~/.codeium/windsurf/mcp_config.json`。格式同样是 `mcpServers`：

```
{
  "mcpServers": {
    "geo-score": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jianruntech/geo-score@v1.3.0", "geo-score-mcp",
               "-c", "/absolute/path/geo-score-watch.json"],
      "env": {"OPENAI_API_KEY": "sk-..."}
    }
  }
}
```

写进 `env` 的 Key 以明文存在这个文件里；只用第一级就不要写 `env`。

</details>

<details>
<summary><b>Zed</b></summary>

写在 Zed 的 `settings.json`：

```
{
  "context_servers": {
    "geo-score": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jianruntech/geo-score@v1.3.0", "geo-score-mcp",
               "-c", "/absolute/path/geo-score-watch.json"],
      "env": {}
    }
  }
}
```

Zed 支持 MCP 的工具和提示词，不支持资源，所以看不到量表资源。从 1.4.0 起，`explain_check` 提示词会把量表带进对话。

</details>

<details>
<summary><b>从克隆的仓库运行</b></summary>

不用 uv，只要 Python 3.8 及以上。`cli/geo_watch.py` 必须和 `cli/geo_score.py` 放在一起。

```bash
git clone https://github.com/jianruntech/geo-score    # 想固定版本就 checkout 一个发布 tag
claude mcp add --scope user geo-score -- python3 /absolute/path/geo-score/cli/geo_score.py mcp -c /absolute/path/geo-score-watch.json
```

在 JSON 配置里写 `"command": "python3"`（Claude Desktop 要写绝对路径）和
`"args": ["/absolute/path/geo-score/cli/geo_score.py", "mcp", "-c", "/absolute/path/geo-score-watch.json"]`。

</details>

LM Studio 用上面的按钮安装，它读的也是和 Cursor 一样的 `mcpServers` 格式。

## 其他安装方式

下面几种都是 1.4.0 新增的，更早的版本没有它们需要的文件。

### Claude Code 插件

```bash
claude plugin marketplace add jianruntech/geo-score
claude plugin install geo-score@jianruntech
```

在会话里用 `/plugin marketplace add jianruntech/geo-score` 和 `/plugin install geo-score@jianruntech` 效果一样。
插件用 `python3` 运行仓库里的 `cli/geo_score.py mcp`，所以 `PATH` 上要有 Python 3.8 及以上，但不需要 uv。
插件不设置任何 Key：要用 `ask` 和 `run`，在启动 `claude` 的 shell 里 export。插件市场跟随仓库，而不是某个发布 tag；
要固定版本，用[安装](#安装)里那行 `uvx`。

### Gemini CLI 扩展

```bash
gemini extensions install https://github.com/jianruntech/geo-score --ref v1.4.0   # 或更新的发布 tag
```

扩展用 `python3` 运行仓库里的 `cli/geo_score.py mcp`。它的设置项里是可选的服务商 Key，Gemini CLI 把它们存在系统钥匙串里，
用 `gemini extensions config geo-score` 修改。

### Claude Desktop 扩展（MCPB）

从 1.4.0 起，每个发布都附带 `geo-score-<版本>.mcpb`，并列在[发布页](https://github.com/jianruntech/geo-score/releases)的
`SHA256SUMS` 里。先校验下载的文件，再用 Claude Desktop 打开它：

```bash
grep ' geo-score-.*\.mcpb$' SHA256SUMS | shasum -a 256 -c
```

Claude Desktop 会弹出一个表单：每个 API Key 和 watch 配置文件都是可选的。Key 字段标记为敏感（sensitive），
Claude Desktop 会遮住输入并当作机密保存。扩展用本机的 `python3`（Windows 上是 `python`）运行它自带的两个脚本，
所以机器上要装有 Python 3.8 及以上。

### Docker

需要自己在本地构建：目前没有发布镜像。从 1.4.0 起仓库里有 `Dockerfile`：

```bash
git clone https://github.com/jianruntech/geo-score && cd geo-score
docker build -t geo-score-mcp .
```

镜像以非特权用户运行，配置从 `/work/geo-score-watch.json` 读。把你的项目挂到 `/work`，并用你自己的用户身份运行，
`run` 才能把文件存进去：

```bash
docker run -i --rm --user "$(id -u)" -v "$PWD:/work" -e OPENAI_API_KEY geo-score-mcp
```

`-e NAME` 不带值，表示从运行 `docker` 的环境里透传这个变量。客户端的 JSON 配置里没有东西会展开 `$PWD` 或
`$(id -u)`，所以要写成具体值：

```
{
  "mcpServers": {
    "geo-score": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--user", "501", "-v", "/absolute/path/acme:/work",
               "-e", "OPENAI_API_KEY", "geo-score-mcp"]
    }
  }
}
```

这里的 `501` 换成你自己 `id -u` 的输出。

## 工具

<!-- BEGIN MCP:tools -->
<!-- 由 scripts/mcp_docs.py 根据 MCPServer.tools() 生成；要改请改服务或脚本，不要改这张表。 -->

| 工具 | 级别 | 费用 | 写入 | 提示 | 参数 |
|---|:-:|---|---|---|---|
| `ask` | 2 | 付费（你的 Key） | 否 | 非破坏性、访问外部 | **`question`**、`engines`、`brand`、`domains` |
| `run` | 3 | 付费（你的 Key）；`dry_run` 免费 | 运行文件，存到配置文件旁的 `.geo-score/watch/runs/` | 非破坏性、访问外部 | `dry_run`、`engines`、`limit`、`max_calls`、`budget_usd` |
| `list_runs` | 3 | 免费 | 否 | 只读 | — |
| `report` | 3 | 免费 | 否 | 只读 | `run`、`format` |
| `diff` | 3 | 免费 | 否 | 只读 | `from`、`to`、`format` |
| `score_site` | 1 | 免费 | 否 | 只读、访问外部 | **`url`**、`urls`、`sample` |

资源：`geo-score://rubric/v1.1`。

加粗的参数必填。「提示」是工具的 MCP 标注（annotations）：客户端可以据此决定哪些调用要你确认；它们只是提示，不是保证。**只有 `ask` 和 `run` 会花钱**，而且只用你交给服务的服务商 Key。
<!-- END MCP:tools -->

- **`score_site`** 读取公开页面：最多抽 8 页，或者只读你传进来的 `urls`（传上一次报告的 `sampled_urls`，
  前后才可比）。文字回答是摘要，完整报告（[schema/report.v2.json](../schema/report.v2.json)）在 `structuredContent` 里。
- **`ask`** 把一个问题拿去问每个有 Key 的引擎，各问一次，不保存。它不需要配置文件：没有配置时用四个默认引擎
  （`chatgpt-api`、`perplexity-api`、`gemini-api`、`claude-api`）；有配置时用你的品牌、竞品和引擎。
- **`run`** 把 `queries.csv` 里的每个问题拿去问每个引擎，并保存这次运行。带 `dry_run: true` 时只返回计划
  （问题数、引擎、计划调用次数、上限），不花钱。`max_calls` 和 `budget_usd` 只能把配置里的上限调低，不能调高；
  `limit` 和 `engines` 用来少问一些。
- **`list_runs`**、**`report`** 和 **`diff`** 读取已保存的运行。只有精确配对检验说有变化，`diff` 才判定为变化；
  方法见 [watch-methodology.zh-CN.md](watch-methodology.zh-CN.md)。
- **`status`**（从 1.4.0 起）说明服务此刻能做什么：版本、开启了哪些工具集、配置文件路径和是否找到（以及错误）、
  每个引擎是否有 Key、是否配了价格、问题数和上限。它从不返回 Key 本身。适合作为第一个调用。

客户端要求时，`ask` 和 `run` 会发送进度通知。

## 选择暴露哪些工具

从 1.4.0 起，可以只开放一部分功能来启动服务。每个参数都有对应的环境变量，方便不好改启动参数的客户端；两者都设时以参数为准。

| 参数 | 环境变量 | 作用 |
|---|---|---|
| `--toolsets NAMES` | `GEO_SCORE_MCP_TOOLSETS` | 打开这些分组：`score`、`ask`、`watch`、`status` 或 `all` |
| `--tools NAMES` | `GEO_SCORE_MCP_TOOLS` | 打开这些工具 |
| `--exclude-tools NAMES` | `GEO_SCORE_MCP_EXCLUDE_TOOLS` | 关掉这些工具，优先于其他所有参数 |
| `--read-only` | `GEO_SCORE_MCP_READ_ONLY=1` | 关掉 `ask` 和 `run` |

名字用逗号分隔。`--toolsets` 和 `--tools` 是叠加的，两个都不给时所有工具都开。分组：`score` 是 `score_site`，
`ask` 是 `ask`，`watch` 是 `run`、`list_runs`、`report`、`diff`，`status` 是 `status`，除非被排除，否则一直开着。
量表资源只在 `score_site` 开着时提供。`GEO_SCORE_MCP_READ_ONLY` 接受 `1`、`true`、`yes`、`on`（以及 `0`、`false`、
`no`、`off`）。名字写错时，服务在启动时以退出码 2 退出，并列出它认识的名字。

**花不了钱的安装。** `--read-only` 保留第一级、读取已保存运行的工具和 `status`；`--toolsets score` 保留
`score_site` 和 `status`。无论环境里有什么 Key，这两种都调不了付费 API：

```bash
claude mcp add --scope user geo-score -- uvx --from git+https://github.com/jianruntech/geo-score@v1.3.0 geo-score-mcp --read-only
```

在 JSON 配置里，把 `"--read-only"` 加到 `args` 末尾，或者在 `env` 里设 `"GEO_SCORE_MCP_READ_ONLY": "1"`。

## 提示词

从 1.4.0 起服务提供提示词：由你主动发起的工作流，比如 Claude Code 里的斜杠命令
（`/mcp__geo-score__audit_site https://acme.com`）。

| 提示词 | 参数 | 做什么 |
|---|---|---|
| `audit_site` | `url`（必填） | 调用 `score_site`，报告分数段和最能提分的检查项，把引用的网站原文当作数据；并说明就绪度不等于被引用 |
| `check_citations` | `question`（必填）、`brand` | 先说明费用，再调用 `ask` |
| `weekly_watch` | 无 | 先 `status`，再带 `dry_run` 跑 `run`；展示计划并等你确认；然后 `run`，最后 `diff` |
| `compare_runs` | `from`、`to` | 比较两次已保存的运行；不带参数时比较最近两次 |
| `explain_check` | `check_id`（必填） | 解释量表里的一项检查，附带量表资源 |

支持补全的客户端可以补全 `explain_check` 的检查项 id，以及在能读到配置时补全 `compare_runs` 的运行 id。
这些提示词只做测量和解释，不给修改建议：这个仓库只负责测量，整改不在范围内。

## 配置与 Key

**第三级工具读哪份配置。** `run`、`list_runs`、`report`、`diff` 需要 `geo-score-watch.json`。服务按顺序找：

1. 启动参数里的 `-c PATH`；
2. 环境变量 `GEO_SCORE_WATCH_CONFIG`；
3. 工作目录下的 `geo-score-watch.json`。

工作目录就是客户端启动服务时所在的目录。终端客户端（Claude Code、Codex、Gemini CLI）通常在你启动它们的目录里
启动服务；桌面应用和编辑器会在别处启动，常常是你的主目录或 `/`，而不是你的项目。拿不准就用绝对路径的 `-c`。
配置里写的问题列表按配置文件所在目录解析，运行结果也存在它旁边的 `.geo-score/watch/runs/` 下。这两个文件用
`geo-score watch init` 创建（在克隆的仓库里是 `python3 cli/geo_score.py watch init`）；全部配置项见
[命令行说明](../cli/README.md#watch)。

**Key。** 服务只从自己的环境变量里读 Key：`OPENAI_API_KEY`、`PERPLEXITY_API_KEY`、`GEMINI_API_KEY`
（或 `GOOGLE_API_KEY`）、`ANTHROPIC_API_KEY`、`OPENROUTER_API_KEY`，或者某个引擎用 `key_env` 指定的变量。
OpenRouter 引擎只能在配置文件里定义。没有 Key 的引擎记为未测，从不记为 0。把 Key 交给服务的几种方式，按暴露程度从低到高：

- 客户端的机密存储：VS Code 带 `"password": true` 的 `inputs`，或 MCPB 的表单（从 1.4.0 起）；
- 客户端从自己的环境里传变量：Cursor 的 `${env:NAME}`、Codex 的 `env_vars`、Gemini CLI 的 `$NAME`，
  以及通常会把自己的环境传下去的 Claude Code；
- 直接写进客户端配置文件的 `env`：所有客户端都支持，但 Key 会以明文留在那个文件里。

服务从不把 Key 写到任何地方。从 1.4.0 起，`status` 会显示每个引擎的 `key_present`，但不显示 Key 本身。

## 超时与取消

`score_site` 大约 20 秒。`run` 对每个问题、每个引擎各调用一次，可能要好几分钟，超过许多客户端默认愿意等的时间：

| 客户端 | 设置 |
|---|---|
| Claude Code | 服务条目上的 `"timeout"`（毫秒），或环境变量 `MCP_TOOL_TIMEOUT`。从 v2.1.212 起，运行超过两分钟的调用会转为后台任务 |
| Codex | `tool_timeout_sec`，默认 60 秒 |
| Gemini CLI | `"timeout"`（毫秒），默认十分钟 |
| 其他 | 见各客户端文档 |

超时很短时，先用 `dry_run` 看计划，再用 `limit` 和 `engines` 少问一些。

从 1.4.0 起，取消调用会生效：服务在下一次调用服务商之前停下 `run` 或 `ask`，不再为这个请求发送任何消息，
被取消的运行不保存。它会在 stderr 打印已经发出的调用次数和费用，因为这些调用已经计费。`run` 进行中，服务照样响应
`ping` 和其他请求。

## 协议版本

从 1.4.0 起，同一个进程同时支持 MCP 的两个时代：

- **旧式（legacy）**，走 `initialize` 握手：2025-11-25、2025-06-18、2025-03-26、2024-11-05。客户端要哪个版本就回哪个；
  不认识的版本回 2025-11-25。JSON-RPC 批量请求只在 2025-03-26 下接受，只有那个版本有批量。
- **新式（modern）**，2026-07-28：`server/discover` 加每个请求自带的 `_meta`，没有握手，也没有会话状态。

1.3.0 只支持 2025-06-18 及更早的版本，客户端要求更新的版本时回 2025-06-18。

## 安全

- **只有 `ask` 和 `run` 会花钱**，而且只用你的 Key 调用配置里的服务商（或默认引擎）。请保留客户端对这两个工具的确认。
  工具标注只是提示，各客户端用法不一。要一个花不了钱的服务，用 `--read-only` 或 `--toolsets score`（从 1.4.0 起）。
- **Agent 只能压低花费。** `max_calls` 和 `budget_usd` 只能把配置里的上限调低，不能调高；读任何文件之前都会先校验运行 id。
- **`score_site` 只连接公网地址。** 被评的 URL、每一跳重定向、网站指向的每个 URL，都必须解析到全局可路由地址。
  直连时连接的就是检查过的那个地址；经过 HTTP 代理时由代理解析域名，最后一步归代理负责。内网站点请用命令行打分。
- **被审网站的原文是数据。** 证据把它放在 `«site text: …»` 里，服务的说明也告诉 Agent 只报告这些文字，不照着做。
- **Key** 只从服务的环境变量读，从不写进配置、运行文件或报告，服务商错误信息里的 Key 会被打码。
  写在客户端配置 `env` 里的 Key 以明文存在那里。
- **文件。** 只有 `run` 会写文件，写在配置文件旁的 `.geo-score/watch/runs/` 下。
- **User-Agent。** `score_site` 用浏览器 User-Agent 和几个具名的 AI 爬虫 User-Agent 抓取，看这些爬虫实际拿到什么。
  调用服务商时发送 `geo-score-watch/<版本>`。
- **没有遥测。** 不向我们或任何人发送数据。

完整的威胁模型见 [SECURITY.md](../SECURITY.md)。

## 排查

**直接查看服务。** [MCP Inspector](https://github.com/modelcontextprotocol/inspector)（需要 Node）不经过客户端就能和它对话。
在克隆的仓库里，`--` 之前的都是启动服务的命令：

```bash
npx --yes @modelcontextprotocol/inspector@2.8.0 --cli python3 cli/geo_score.py mcp -- --method tools/list
npx --yes @modelcontextprotocol/inspector@2.8.0 --cli python3 cli/geo_score.py mcp -- --method resources/read --uri geo-score://rubric/v1.1
npx --yes @modelcontextprotocol/inspector@2.8.0 --cli python3 cli/geo_score.py mcp -- --method tools/call --tool-name score_site --tool-arg url=example.com
npx --yes @modelcontextprotocol/inspector@2.8.0 --cli python3 cli/geo_score.py mcp -c /absolute/path/geo-score-watch.json -- --method tools/call --tool-name run --tool-arg dry_run=true
npx --yes @modelcontextprotocol/inspector@2.8.0 --cli python3 cli/geo_score.py mcp -- --method prompts/list    # 从 1.4.0 起
```

没有 Node 时，手动发送握手：

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 cli/geo_score.py mcp
```

**服务起不来。** 桌面应用常常找不到 `uvx`：在 `command` 里写它的绝对路径（`which uvx`）。第一次启动要下载并构建这个版本，
可能超过客户端的启动超时；再启动一次，或者调大超时（Codex：`startup_timeout_sec`）。

**`cannot read … geo-score-watch.json`。** 服务不是在你的项目里运行的。传 `-c /绝对路径/geo-score-watch.json`，
或者设 `GEO_SCORE_WATCH_CONFIG`。从 1.4.0 起，`status` 会显示服务尝试读取的路径。

**`no engine can run — the MCP server's environment has no API keys`。** Key 没传到服务里。桌面应用看不到 shell 里 export
的变量，Gemini CLI 会去掉没在 `env` 里列出的 Key。见[配置与 Key](#配置与-key)。

**`run` 被中途切断。** 客户端不等了：调大它的工具超时，或者用 `limit` 和 `engines` 少问一些。见[超时与取消](#超时与取消)。

**`url must be an http(s) URL on a public host`。** `score_site` 有意拒绝 localhost、私有和保留地址。这类站点请用命令行打分。

**少了某个工具。** 被 `--read-only`、`--toolsets`、`--tools` 或 `--exclude-tools`（从 1.4.0 起）去掉了。
服务在 `geo_watch.py` 旁边找不到同一版本的 `geo_score.py` 时，`score_site` 也会消失。Zed 只显示工具和提示词，不显示资源。

**日志。** 服务把诊断信息写到 stderr，从不写到 stdout。Claude Desktop 在 macOS 上把它存在
`~/Library/Logs/Claude/mcp-server-geo-score.log`；多数其他客户端会在 MCP 日志或输出面板里显示。

分数本身的问题见[常见问题排查](troubleshooting.zh-CN.md)。
