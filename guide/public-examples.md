# Two public examples: robots.txt and Organization JSON-LD

geo-score measures; it does not fix, and remediation is a separate, non-open project
([Scope](../README.md#scope--what-this-does-not-do)). These two examples are the exception, because they are public
common knowledge: the crawler names come from each vendor's own documentation, collected in
[reference/ai-crawlers.md](../reference/ai-crawlers.md), and the markup is schema.org vocabulary. Nothing else in this
repository is a template to paste, and nothing else will be.

Both are read by the CLI's own code in `scripts/test_public_examples.py`, so an example that stopped reaching the tier
this page names would fail the repository's checks.
中文版：[public-examples.zh-CN.md](public-examples.zh-CN.md)

## 1 · A robots.txt that lets retrieval crawlers in

It names each of the ten retrieval crawlers that `g.robots` reads and gives them an explicit `Allow`, which is the
check's top tier, "mainstream retrieval user-agents explicitly allowed".

```text
# Retrieval crawlers: they fetch pages to answer people's questions, and cite them.
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: PerplexityBot
User-agent: Perplexity-User
User-agent: Googlebot
User-agent: Bingbot
User-agent: Applebot
User-agent: Amazonbot
Allow: /
Disallow: /admin/

# Every other crawler
User-agent: *
Allow: /
Disallow: /admin/

Sitemap: https://www.example.com/sitemap.xml
```

Before you use it:

- **Repeat your own `Disallow` lines in the named group.** Under RFC 9309 a crawler that has a group of its own obeys
  only that group and ignores `*`. `/admin/` stands for whatever your current file keeps out; a rule left only under
  `*` no longer applies to the ten crawlers named above.
- **Training crawlers are a separate decision.** `GPTBot`, `ClaudeBot`, `CCBot` and the opt-out tokens such as
  `Google-Extended` are not in this group, and the rubric does not score them. Refusing training while admitting the
  retrieval crawlers is a legitimate posture; what each name controls is in
  [reference/ai-crawlers.md](../reference/ai-crawlers.md).
- **robots.txt is a request, not a gate.** A firewall, a CDN's bot rules or a challenge page can still refuse these
  crawlers; that is what `g.reachable` measures.
- Change the `Sitemap:` line to your own sitemap's address.

## 2 · Organization and WebSite JSON-LD for the homepage

An `Organization` with `name`, `url` and `logo`, and a `WebSite` beside it, is the middle tier of `p1.organization`; a
logo that answers 200 and declared `sameAs` profiles make the top tier. Put the object inside a
`<script type="application/ld+json">` element in the homepage's `<head>`.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://www.example.com/#organization",
      "name": "Example Co",
      "alternateName": "Example",
      "url": "https://www.example.com/",
      "logo": "https://www.example.com/logo.png",
      "sameAs": [
        "https://profiles.example.org/example-co",
        "https://code.example.org/example-co"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://www.example.com/#website",
      "name": "Example Co",
      "url": "https://www.example.com/",
      "publisher": { "@id": "https://www.example.com/#organization" }
    }
  ]
}
```

Before you use it:

- **Every value must match what the page shows** and what other sites say about you: the same name, the same address.
  An entity that disagrees with itself is harder to recognise, not easier.
- **`logo` must answer 200** with an image; the top tier fetches it.
- **`sameAs` lists only profiles that exist and belong to you**: your pages on other sites, and an entry in a public
  knowledge base if you have one. `p3.sameas` requests each one, and a dead or foreign profile costs points there.
- **`alternateName`** is where a former name or a common short name goes. Leave it out if there is none.
