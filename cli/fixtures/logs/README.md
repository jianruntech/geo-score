# Access-log fixtures

Made-up logs for `cli/test_crawler_logs.py`, which tests `geo-score crawlers LOG…`. Every address is a documentation
address (RFC 5737: 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24; RFC 3849: 2001:db8::/32) and every host is
example.com, so no line describes a real visitor.

| File | What it holds |
|---|---|
| `combined.log` | nginx and Apache combined lines: retrieval, live-fetch and training crawlers, a forged GPTBot from outside its range, a vhost_combined line, an escaped quote, a path with a backtick, a common-format line with no user-agent, and three lines in no format |
| `vercel.jsonl` | Vercel log drain lines, one with a firewall `wafAction` of `deny`, and a build line with no request |
| `cloudflare.jsonl` | Cloudflare Logpush HTTP request lines with timestamps in nanoseconds and RFC 3339, and `SecurityAction` values |
| `json-lines.jsonl` | An nginx JSON `log_format` line and a Caddy-shaped line |
| `ranges-gptbot.json`, `ranges-oai-searchbot.txt` | Range files in the vendor JSON shape and as plain text. **Not the vendors' ranges** |
| `sitemap.xml`, `urls.txt` | Page lists for `--sitemap` and `--urls` |
| `funnel.log`, `conversions.txt` | The funnel: index and live fetches, visits from ChatGPT (Referer and `utm_source`), Perplexity and Kimi, a `utm_medium` that makes a ChatGPT Referer another referral, a subdomain that is not an assistant's host, a stylesheet loaded after a click, and conversions inside and outside 24 hours; `--conversions` with a prefix |
| `import-records.jsonl` | JSON log records with the usual field names (`time` or `timestamp`, `ip` or `remote_addr`, `path` or `url`, `method`, `status`, `bytes`, `userAgent` or `user_agent`, `location`), a date with no time among them |
