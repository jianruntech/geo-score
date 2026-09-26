# 证据依据 · AIV 量表 v1.1

*English: [evidence-v1.1.md](evidence-v1.1.md)*

> **仅为元数据。** 本页不改动 [v1.1](v1.1.zh-CN.md) 的任何权重、档位或分数，只记录每项检查的权重
> 建立在什么依据上，让读者自己判断这个权重站不站得住。同样的数据以 `evidence` 对象的形式写在
> [v1.1.json](v1.1.json) 的每一项检查里。

下表逐项说明：这一项的权重是依据公开研究、引擎或爬虫运营方自己的文档、我们审计真实站点时的观察，
还是一项没人证明过有用的约定。证据单薄或方向相反时，备注里会直说。

## 四种依据的含义

| 依据 | 含义 |
|---|---|
| `research` | 有公开研究测量过这项效果，或这项检查所依赖的机制。预印本与行业研究会在备注里注明——这里引用的研究大多未经同行评审。 |
| `vendor-doc` | 引擎或爬虫的运营方在自己的文档里写明了这一机制。多数情况下这个运营方是 Google，而 Google 的文档针对的是 Google 搜索，不代表所有答案引擎。 |
| `field-observation` | 没有外部来源支撑这个权重，它建立在量表作者审计真实站点时的观察——[标定记录](calibration-v1.1.zh-CN.md)与[基准榜单](../benchmark/README.md)——以及作者的判断之上。 |
| `convention` | 这项检查衡量的是对某个公开提案或事实约定的采纳，而没有任何主流答案引擎确认会在生成答案时使用它。给的分奖励的是采纳，不是已被证明的效果。 |

依据只说明支撑来自哪里，不说明有多强——强弱写在备注里。每个来源都在「核实日期」一列的日期实际打开过，
并核对了它被引用来支撑的那一点。厂商文档与某项检查的方向相反时，也列为来源。

**计数。** 21 项计分检查中，`vendor-doc` 11 项（45 分），`research` 7 项（39 分），
`field-observation` 2 项（11 分），`convention` 1 项（5 分）。4 项加分项中，`convention` 3 项，
`vendor-doc` 1 项。

## 计分检查 · 满分 100

| 检查项 | 名称 | 分值 | 依据 | 来源 | 核实日期 | 备注 |
|---|---|:-:|---|---|---|---|
| `g.robots` | robots 放行检索爬虫 | 5 | `vendor-doc` | [OpenAI 爬虫文档](https://developers.openai.com/api/docs/bots) · [Anthropic 爬虫文档](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler) · [Perplexity 爬虫文档](https://docs.perplexity.ai/docs/resources/perplexity-crawlers) · [Google 常见爬虫](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers) · [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html) | 2026-09-27 | OpenAI、Anthropic、Perplexity 都在官方文档中写明：屏蔽其搜索爬虫，站点就不会出现在（或更少出现在）它们的答案里——这支撑 0 分档与门槛；但 RFC 9309 规定没有匹配规则即不受限制，所以从「无规则」（3 分）到「明确 Allow」（5 分）这一步是本量表的约定，不是厂商要求。 |
| `g.reachable` | 检索 UA 实测可达 | 5 | `vendor-doc` | [Cloudflare 2025-07](https://blog.cloudflare.com/content-independence-day-no-ai-crawl-without-compensation/) · [Cloudflare AI bots 文档](https://developers.cloudflare.com/bots/additional-configurations/block-ai-bots/) · [Perplexity 爬虫文档](https://docs.perplexity.ai/docs/resources/perplexity-crawlers) · [基准榜单](../benchmark/README.md) | 2026-09-27 | Cloudflare 文档写明它在网络边缘拦截 AI 爬虫，2025 年 7 月起对新域名默认拦截 AI 爬虫（2026-09-15 起改用新的默认规则）；Perplexity 也要求站点在防火墙层与 robots.txt 同时放行；2026-09-09 基准中 314 站有 16 站对检索爬虫返回 403。固定的 10 个 UA 清单是本量表自定的。 |
| `g.ssr` | 正文服务端可见 | 5 | `research` | [Vercel + MERJ 2024](https://vercel.com/blog/the-rise-of-the-ai-crawler) · [Google JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics) · [基准榜单](../benchmark/README.md) | 2026-09-27 | Vercel 与 MERJ 的流量分析（2024 年 12 月；行业研究，未经同行评审）未发现 OpenAI、Anthropic、Perplexity 的爬虫执行 JavaScript；但 Google 文档写明 Googlebot 会渲染 JS，同一研究也发现 AppleBot 会渲染——所以理由写的是「多数」而不是「全部」。基准中 314 站有 45 站的正文只在 JS 执行后出现。 |
| `p1.sitemap` | sitemap 可发现且新鲜 | 4 | `vendor-doc` | [Google sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap) · [Bing 2025-07](https://blogs.bing.com/webmaster/2025/7/Keeping-Content-Discoverable-with-Sitemaps-in-AI-Powered-Search/) · [sitemaps.org](https://www.sitemaps.org/protocol.html) | 2026-09-27 | Google 在 lastmod 持续准确时会使用它；Bing 称 lastmod 是 AI 搜索中决定重抓的关键信号；sitemaps 协议定义了 robots.txt 中的 Sitemap 指令。OpenAI、Anthropic、Perplexity 的文档没有提到 sitemap。 |
| `p1.llms-txt` | llms.txt | 5 | `convention` | [llmstxt.org](https://llmstxt.org/) · [Web Almanac 2025 SEO 章](https://almanac.httparchive.org/en/2025/seo) · [Google 生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) · [标定记录](calibration-v1.1.zh-CN.md#逐项表现暴露的四个结构问题) | 2026-09-27 | 这是一份提案（Jeremy Howard，2024；2026 年 8 月修订为 v2），据 Web Almanac 2025，桌面站点采纳率 2.13%（标定记录已引用）；截至 2026-09-27，没有任何主流答案引擎公开确认会用 llms.txt 选择或引用来源，Google 明确表示 Google 搜索忽略它——这 5 分奖励的是对一项约定的采纳，而不是已被证明的效果。 |
| `p1.organization` | Organization + WebSite | 6 | `vendor-doc` | [Google Organization 文档](https://developers.google.com/search/docs/appearance/structured-data/organization) · [Google 网站名称文档](https://developers.google.com/search/docs/appearance/site-names) · [schema.org/Organization](https://schema.org/Organization) · [Google 生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) | 2026-09-27 | Google 文档写明 Organization 标记帮助它区分同名机构、确定 logo 与知识面板信息，WebSite 标记是网站名称的主要依据；但它的生成式 AI 指南说 AI 功能不需要任何特殊 schema，其他答案引擎也没有文档说明会用这两种类型。 |
| `p1.breadcrumb` | BreadcrumbList | 3 | `vendor-doc` | [Google 面包屑文档](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb) · [schema.org/BreadcrumbList](https://schema.org/BreadcrumbList) · [Web Almanac 2024 结构化数据章](https://almanac.httparchive.org/en/2024/structured-data) | 2026-09-27 | Google 文档写明面包屑标记表示页面在站点层级中的位置，并用于在搜索结果中给页面归类；没有答案引擎文档说明会用它。Web Almanac 2024 结构化数据章统计其出现在 5.66% 的页面上。 |
| `p1.page-type` | 页型专用 schema | 4 | `vendor-doc` | [Google Product 文档](https://developers.google.com/search/docs/appearance/structured-data/product) · [Google 2023-08](https://developers.google.com/search/blog/2023/08/howto-faq-changes) · [Google Search 文档更新记录](https://developers.google.com/search/updates) · [Google Dataset 文档](https://developers.google.com/search/docs/appearance/structured-data/dataset) | 2026-09-27 | Google 仍为 Product 标记提供商品结果文档，但 HowTo 富结果已于 2023 年停止展示，FAQ 富结果于 2026 年 5 月停止展示，Dataset 标记只用于 Dataset Search——量表点名的几种类型里，只有 Product 在 Google 搜索中仍有对应功能，也没有答案引擎文档说明会用其中任何一种。 |
| `p2.answer-passages` | 自足答案段 | 9 | `research` | [Wu 等 2025](https://arxiv.org/abs/2510.11438) · [Zhang 等 2026](https://arxiv.org/abs/2604.25707) · [Google 生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) · [标定记录](calibration-v1.1.zh-CN.md#v11-做了什么) | 2026-09-27 | 两篇预印本方向一致：从模拟引擎提取的偏好规则里有「信息以自足单元呈现」（Wu 等 2025），一项观察性研究发现含定义句的被引页面平均影响力高 57%（Zhang 等 2026）；但两者都未经同行评审，Google 说其 AI 功能不需要把内容切块，25–120 词的区间来自标定时的实测——对分值最高的一项而言，支撑偏弱。 |
| `p2.question-intent` | 标题匹配提问意图 | 7 | `field-observation` | [标定记录](calibration-v1.1.zh-CN.md#v11-做了什么) · [Google 生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) · [Zhang 等 2026](https://arxiv.org/abs/2604.25707) | 2026-09-27 | 我们没有找到把标题措辞与被引用联系起来的一手来源：Google 说其 AI 功能按语义与同义词匹配，不需要为它改写内容；一篇观察性预印本发现问答格式的页面影响力反而低 5.7%。「看实质不看格式」的判据来自标定实测，7 分的权重是作者的判断。 |
| `p2.freshness` | 时间信号 | 6 | `research` | [Fang 等 2025](https://arxiv.org/abs/2509.11353) · [Google 发布日期文档](https://developers.google.com/search/docs/appearance/publication-dates) · [Bing 2025-07](https://blogs.bing.com/webmaster/2025/7/Keeping-Content-Discoverable-with-Sitemaps-in-AI-Powered-Search/) | 2026-09-27 | 七个用作重排序器的 LLM 都会把注入了较新日期的段落排得更靠前（Fang 等 2025，预印本）；Bing 说时效信号影响 AI 答案反映更新的速度；Google 文档写明它同时读取可见日期与结构化日期，并要求二者一致。「任一种日期即可拿中间档」是本量表的规则。 |
| `p2.sourced-stats` | 数据带出处 | 7 | `research` | [Aggarwal 等，KDD 2024](https://arxiv.org/abs/2311.09735) · [Wu 等 2025](https://arxiv.org/abs/2510.11438) · [Zhang 等 2026](https://arxiv.org/abs/2604.25707) | 2026-09-27 | 全量表最强的外部证据：在对照实验中，加入统计数据、引语或来源引用使可见度（按位置加权的字数指标）提升 30–40%（Aggarwal 等，KDD 2024；模拟引擎加 Perplexity 子集），之后两篇预印本结论一致。「来源可点击可核实」这一要求是本量表自己加的。 |
| `p2.named-author` | 具名作者可核实 | 6 | `vendor-doc` | [Google 有用内容指南](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) · [Google Article 文档](https://developers.google.com/search/docs/appearance/structured-data/article) | 2026-09-27 | Google 的有用内容指南会问页面是否有署名、署名是否能链到作者的更多信息；其 Article 标记把社交主页、about 页或 bio 页都列为合格的作者 URL，与最高档一致。这是面向 Google 搜索整体的指南，没有答案引擎文档说明会看作者署名。 |
| `p3.listings` | 第三方平台收录 | 4 | `research` | [Chen 等 2025](https://arxiv.org/abs/2509.08919) · [Kumar 2026](https://arxiv.org/abs/2606.20065) · [标定记录](calibration-v1.1.zh-CN.md#逐项表现暴露的四个结构问题) | 2026-09-27 | AI 搜索引擎来自「赢得媒体」（含评测与比价网站）的引用占比远高于 Google（Chen 等 2025，预印本）；但一篇厂商自做的预印本测得 G2 与 Capterra 只占引用的 1.1%，我们也没找到单独考察目录或应用商店收录的研究，且标定时五个站全部满分——证据薄且不一致。 |
| `p3.mentions` | 独立第三方提及 | 4 | `research` | [Chen 等 2025](https://arxiv.org/abs/2509.08919) · [Google 生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) · [标定记录](calibration-v1.1.zh-CN.md#逐项表现暴露的四个结构问题) | 2026-09-27 | AI 搜索引擎对第三方「赢得媒体」的偏好远强于 Google，品牌自有内容占比低得多（Chen 等 2025，预印本）；Google 说其 AI 功能会呈现全网对产品的评价，同时提醒刷出来的提及没有用。各档的边界由审计者判断。 |
| `p3.knowledge-graph` | 知识图谱实体 | 4 | `vendor-doc` | [Google 知识面板说明](https://support.google.com/knowledgepanel/answer/9787176?hl=en) · [Zhang 等 2026](https://arxiv.org/abs/2604.25707) | 2026-09-27 | Google 文档说明其知识图谱来自公开来源与授权数据，但没有点名维基数据或维基百科；一篇观察性预印本发现百科类页面是被引来源中影响力最高的类型。我们没有找到「有条目就会被更多引用」的证据，理由中「最强的单一信号」一说并未得到证实。 |
| `p3.sameas` | sameAs 完整可解析 | 3 | `vendor-doc` | [Google Organization 文档](https://developers.google.com/search/docs/appearance/structured-data/organization) · [schema.org/sameAs](https://schema.org/sameAs) | 2026-09-27 | Google 文档把 sameAs 定义为指向其他网站上关于该机构的页面，schema.org 将其定义为能明确指明实体身份的参考页面。「每个链接都可解析且确属本品牌」是本量表自己的检验，没有答案引擎文档说明会用 sameAs。 |
| `p3.video` | 视频与多模态 | 3 | `vendor-doc` | [Google 生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) · [Google 视频文档](https://developers.google.com/search/docs/appearance/structured-data/video) · [Kumar 2026](https://arxiv.org/abs/2606.20065) | 2026-09-27 | Google 说其生成式 AI 功能会在网页链接之外引入相关视频，并提供 VideoObject 标记文档；一篇厂商自做的预印本发现 YouTube 是被引最多的非企业来源，占引用 4.2%。「持续输出」一档由审计者判断。 |
| `p4.answer-shape` | 答案形态适配 | 4 | `research` | [Zhang 等 2026](https://arxiv.org/abs/2604.25707) · [Wu 等 2025](https://arxiv.org/abs/2510.11438) · [Google 生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) | 2026-09-27 | 一篇观察性预印本中，影响力最高的四分位被引页面，标题数是最低四分位的 12.5 倍、列表密度是 8.9 倍，但它们也长 11 倍，存在混杂（Zhang 等 2026）；模拟引擎的偏好规则里有「清晰的标题与列表」（Wu 等 2025）。Google 建议分节与标题是为了读者而非 AI，段落长度阈值是本量表自定的。 |
| `p4.question-coverage` | 高频问题覆盖 | 4 | `field-observation` | [标定记录](calibration-v1.1.zh-CN.md#仍未解决) · [Google 生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) | 2026-09-27 | 前提是：站点不会因为一个它从未回答的问题被引用。Google 文档描述了查询扇出（query fan-out），但也提醒为了影响 AI 回答而为每种问法批量造页违反其规模化内容政策；标定记录把「选哪十个问题」列为本量表最大的不可复现来源。 |
| `p4.cn-engines` | 中文引擎适配 | 2 | `vendor-doc` | [Baiduspider FAQ](https://help.baidu.com/question?prod_id=99&class=0&id=3001) · [《互联网信息服务管理办法》](https://www.gov.cn/gongbao/content/2011/content_1860864.htm) | 2026-09-27 | 百度文档写明 Baiduspider 遵守 robots.txt、被屏蔽的页面不会出现在其结果中；《互联网信息服务管理办法》第四条规定非经营性互联网信息服务须备案。没有中文答案引擎文档说明会把备案或主体信息当作信号，所以第二分是本量表的约定。 |

## 加分项 · 不进分母，封顶 +6

| 检查项 | 名称 | 分值 | 依据 | 来源 | 核实日期 | 备注 |
|---|---|:-:|---|---|---|---|
| `b.llms-full` | llms-full.txt | 2 | `convention` | [Mintlify](https://www.mintlify.com/blog/what-is-llms-txt) · [llmstxt.org](https://llmstxt.org/) · [Google 生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) | 2026-09-27 | 单文件全文变体，Mintlify 称是它与 Anthropic 合作开发的；现行 llms.txt 提案正文没有定义它，没有答案引擎文档说明会读取它，Google 说 Google 搜索忽略这类 AI 文本文件。 |
| `b.ai-txt` | ai.txt | 2 | `convention` | [Spawning 2023](https://spawning.substack.com/p/aitxt-a-new-way-for-websites-to-set) · [IETF 草案 2026](https://www.ietf.org/archive/id/draft-car-ai-txt-wellknown-00.html) · [标定记录](calibration-v1.1.zh-CN.md#逐项表现暴露的四个结构问题) | 2026-09-27 | 同名的是两份互不相关的提案：Spawning 2023 年的根目录文件，与 2026 年一份放在 well-known 路径下的 IETF 个人草案；两者声明的都是使用与训练许可，没有答案引擎文档说明会读取；标定时五个站全部为 0。 |
| `b.geo-link` | GEO link 标签 | 1 | `convention` | [llmstxt.org](https://llmstxt.org/) · [标定记录](calibration-v1.1.zh-CN.md#逐项表现暴露的四个结构问题) | 2026-09-27 | llms.txt 提案（v2，2026 年 8 月）建议用标准 link 关系指向页面的 markdown 版本及覆盖它的 llms.txt；没有答案引擎文档说明会读取，标定时五个站都没有。 |
| `b.speakable` | speakable | 1 | `vendor-doc` | [Google speakable 文档](https://developers.google.com/search/docs/appearance/structured-data/speakable) · [schema.org/speakable](https://schema.org/speakable) · [标定记录](calibration-v1.1.zh-CN.md#逐项表现暴露的四个结构问题) | 2026-09-27 | Google 文档把 speakable 列为测试版功能，供 Google 助理在智能音箱上朗读时事新闻；没有生成式答案引擎文档说明会用它，标定时五个站都没有。 |

## 证据最薄的几项

按各自所占分值衡量：

- **`p2.answer-passages`（9 分）**——分值最高的一项只有两篇预印本支撑，其中一篇用的是模拟引擎；
  Google 还说其 AI 功能不需要把内容切块。
- **`p2.question-intent`（7 分）**——没有外部来源；Google 的指南与一篇观察性预印本的方向相反。
- **`p1.llms-txt`（5 分）**——一项桌面站点采纳率 2.13% 的约定，没有主流答案引擎确认使用，
  Google 明言 Google 搜索忽略它。
- **`p1.page-type`（4 分）**——量表点名的几种类型里，只有 Product 在 Google 搜索中仍有对应功能。
- **`p3.knowledge-graph`（4 分）**——全有或全无，理由中「最强的单一信号」一说没有任何来源证实。
- **`p4.question-coverage`（4 分）**——取决于审计者挑选的十个问题。

这些是将来调整权重的候选项。任何权重改动都以新版本量表发布，绝不原地修改 v1.1——见
[量表 README](README.md)。

## 关于来源的说明

- **采纳率数字。** llms.txt 的 2.13%（桌面站点）出自 Web Almanac **2025** 的 SEO 章。标定记录里与它
  并列引用的结构化数据数字（BreadcrumbList 5.66%、Product 0.77%、FAQPage 约 0.34%）出自 Web Almanac
  **2024** 的结构化数据章；2025 版没有结构化数据章。
- **预印本。** Wu 等 2025（arXiv 2510.11438）用小型商用模型搭建模拟引擎，不是线上产品。Zhang 等 2026
  （arXiv 2604.25707）是观察性研究，并声明不做因果推断。Kumar 2026（arXiv 2606.20065）是一家 GEO
  厂商做的测量研究。Chen 等 2025（arXiv 2509.08919）与 Fang 等 2025（arXiv 2509.11353）是预印本。
  这里引用的研究中，只有 Aggarwal 等（arXiv 2311.09735）有同行评审的发表场合：KDD 2024。
- **重新核实。** 这一领域的厂商文档变化很快：Google 在 2026 年撤掉了 FAQ 富结果并发布了生成式 AI
  指南，Cloudflare 的爬虫默认规则在 2026-09-15 更换。来源的时效以「核实日期」为准。
