# Security Policy

This repository contains a scoring rubric, a Markdown skill definition and a CLI. The CLI
ships no hosted service and processes no user data of its own. Levels 2 and 3 (`--ask`,
`watch`) use API keys that can spend money, so they are careful with them:

- Keys are read from environment variables only. They are never written to the config, to
  run files or to reports, and a key that appears in a provider's error message is replaced
  with `[redacted]` before it is stored or printed.
- Requests to providers never follow redirects; a redirecting endpoint is reported as an
  error rather than handed the key. A custom `base_url` must be `https://` (or `http://localhost`).
- The MCP server lets an agent lower `max_calls` and `budget_usd`, never raise them, and run ids
  are validated before any file is read.
- CSV output escapes cells a spreadsheet would treat as formulas.
- Run files hold your questions and the full text of the AI answers, and `queries.csv` holds the
  question list. If either is confidential, keep `.geo-score/` and `queries.csv` out of public
  repositories (the included `.gitignore` covers `.geo-score/`), and note that the weekly
  workflow in `examples/ci/` commits run files on purpose: use it in a private repository.

The realistic risks are:

- **The skill instructs an agent to fetch URLs you supply.** Only audit sites you are
  authorised to audit. Auditing at volume can look like scraping to the target.
- **Audit output can contain data from the target site.** Treat a generated report as
  you would treat any document about a client.

## Reporting

If you find something that could harm a user of this repository, email
**hello@jianruntech.com** rather than opening a public issue. We'll acknowledge within
five working days.
