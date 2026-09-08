# Security Policy

This repository contains a scoring rubric and a Markdown skill definition. It ships no
executable service, stores no credentials, and processes no user data.

The realistic risks are:

- **The skill instructs an agent to fetch URLs you supply.** Only audit sites you are
  authorised to audit. Auditing at volume can look like scraping to the target.
- **Audit output can contain data from the target site.** Treat a generated report as
  you would treat any document about a client.

## Reporting

If you find something that could harm a user of this repository, email
**hello@jianruntech.com** rather than opening a public issue. We'll acknowledge within
five working days.
