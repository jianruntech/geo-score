# Support

geo-score measures; it does not fix. This page says where each kind of report or question goes, so it
reaches the form that asks for what is needed to reproduce it.

## Which form

| You have | Open |
|---|---|
| A score or a check that looks wrong on a site | [Wrong score](https://github.com/jianruntech/geo-score/issues/new?template=bug_report.yml): the check id and the JSON report |
| A leaderboard row that a fresh measurement does not support | [Benchmark correction](https://github.com/jianruntech/geo-score/issues/new?template=benchmark_correction.yml): the row, what is disputed and your report |
| The CLI, the GitHub Action, the MCP server or an install (pip, pipx, uvx, MCPB, plugin, extension, Docker) that does not work | [Tool problem](https://github.com/jianruntech/geo-score/issues/new?template=tool_problem.yml): the version, the command or config, and the output |
| An engine that fails, a citation missed or miscounted, or a watch number that looks wrong | [Citation check problem](https://github.com/jianruntech/geo-score/issues/new?template=engine_bug.yml): the version and the `watch check` output |
| Evidence that a weight or a pass condition is wrong | [Rubric proposal](https://github.com/jianruntech/geo-score/issues/new?template=rubric_proposal.yml): what you observed, on how many sites |
| A site the leaderboard should include | [Add a site](https://github.com/jianruntech/geo-score/issues/new?template=add_site.yml) |
| A security problem | Email, as [SECURITY.md](SECURITY.md#reporting-a-vulnerability) describes; not a public issue |

Many questions are answered already. The [troubleshooting guide](../guide/troubleshooting.md) covers a
score that moved between runs, a check that shows `—`, a score capped at 40, a site that could not be
fetched, proxies, and a score that differs from the leaderboard. The MCP server's
[troubleshooting section](../guide/mcp.md#troubleshooting) covers a server that does not start or cannot
find its config or keys.

## Before you paste

Never paste an API key. geo-score redacts keys from what it stores and prints, but check configs and
logs before you paste them. A `watch` run file holds your questions and the full answers; shorten or
remove anything confidential.

## Out of scope

How to raise a score is out of scope for this repository: fix templates, markup to paste, content
rewrites and remediation playbooks. See [Scope](../README.md#scope--what-this-does-not-do). A report that
a check measures the wrong thing is in scope, and is the most useful report there is.
