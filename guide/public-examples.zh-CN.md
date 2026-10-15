# 两个公开样例：robots.txt 和 Organization JSON-LD

geo-score 只测量、不修复，修复是另一个不开源的项目（[边界](../README.zh-CN.md#边界--这个仓库不做什么)）。
这两个样例是例外，因为它们是公开常识：爬虫名字来自各家厂商自己的文档，汇总在
[reference/ai-crawlers.md](../reference/ai-crawlers.md)；标记用的是 schema.org 的词汇。
这个仓库里没有别的可以照贴的模板，以后也不会有。

两个样例都由 `scripts/test_public_examples.py` 用 CLI 自己的代码读一遍；哪个样例达不到本页写的档位，仓库自检就会失败。
English: [public-examples.md](public-examples.md)

## 1 · 让检索爬虫进来的 robots.txt

它点名 `g.robots` 读的全部 10 个检索爬虫，并明确写 `Allow`，这是这一项的最高档：「主流检索 user-agent 被明确放行」。

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

用之前注意：

- **把你原有的 `Disallow` 在点名的那一组里再写一遍。** 按 RFC 9309，有自己一组的爬虫只听这一组、不看 `*`。
  `/admin/` 代表你现在的文件里不让抓的路径；只留在 `*` 下的规则，对上面点名的 10 个爬虫就不再生效。
- **训练爬虫是另一个决定。** `GPTBot`、`ClaudeBot`、`CCBot`，以及 `Google-Extended` 这类退出令牌都不在这一组里，
  量表也不给它们计分。拒绝训练、同时放行检索爬虫，是正当的做法；每个名字管什么，见
  [reference/ai-crawlers.md](../reference/ai-crawlers.md)。
- **robots.txt 是请求，不是门禁。** 防火墙、CDN 的机器人规则或验证页仍然可能拒绝这些爬虫，那是 `g.reachable` 测的事。
- 把 `Sitemap:` 那一行改成你自己站点地图的地址。

## 2 · 首页的 Organization 和 WebSite JSON-LD

带 `name`、`url`、`logo` 的 `Organization`，加上旁边的 `WebSite`，是 `p1.organization` 的中间档；logo 能返回 200、
并声明了 `sameAs`，是最高档。把这段对象放进首页 `<head>` 里的 `<script type="application/ld+json">` 元素。

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

用之前注意：

- **每个值都要和页面上显示的一致**，也要和别的网站对你的描述一致：同一个名字、同一个地址。自相矛盾的实体更难被认出来。
- **`logo` 必须返回 200** 和一张图片；最高档会去抓它。
- **`sameAs` 只列真实存在、属于你的主页**：你在其他网站上的页面，有的话再加公开知识库里的条目。`p3.sameas` 会逐个请求，
  打不开的或不是你的主页会在那一项扣分。
- **`alternateName`** 放曾用名或常用简称；没有就删掉这一行。
