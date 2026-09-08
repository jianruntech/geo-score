# mingdao.com — AIV audit (rubric v1.1)

> **Readiness 69 / 100 · normalised 69% · Solid** · audited 2026-09-08

Scored against [rubric v1.1](../../../rubric/v1.1.md) using only publicly observable data.
Machine-readable: [`mingdao.com.json`](mingdao.com.json), conforming to
[`schema/report.v2.json`](../../../schema/report.v2.json).

## Sampled URLs (8)

- https://www.mingdao.com/
- https://www.mingdao.com/hap/feature
- https://www.mingdao.com/hap/price
- https://www.mingdao.com/landing/data-model/restaurant-and-chain-dining.html
- https://www.mingdao.com/compare/matrix/hap-vs-jiandaoyun
- https://www.mingdao.com/solution/038
- https://www.mingdao.com/case/061
- https://www.mingdao.com/case/605

## Reachable — 15 / 15

**✓ `g.robots` 5/5** — Retrieval crawlers allowed in robots.txt

*Why this tier:* 不是 3 档，因为 robots.txt 为检索 UA 单开了一组并写了 Allow: /，属于「明确放行」而非「未显式禁止也未显式放行」。

https://www.mingdao.com/robots.txt 200，1958 字节。第二组 User-agent 连续声明 15 个检索 UA（GPTBot / ChatGPT-User / OAI-SearchBot / ClaudeBot / Claude-User / Claude-SearchBot / PerplexityBot / Perplexity-User / Google-Extended / Applebot-Extended / Bytespider / Amazonbot / CCBot / meta-externalagent / cohere-ai）后跟 `Allow: /`。该组 Disallow 仅 /act /aja /adm /app，8 个抽样 URL 无一落入。原句：`Content-Signal: search=yes, ai-input=yes, ai-train=no`——ai-train=no 是训练退出，不影响检索索引。另注：Crawl-delay: 10 同时适用于这 15 个 UA。

**✓ `g.reachable` 5/5** — Reachable to retrieval user-agents

*Why this tier:* 不是 3 档，因为 10 个 UA 无一被拦，且正文与浏览器逐字节一致——唯一差异是浏览器两次自身请求之间也会变的渲染 id。

首页对 10 个真实 UA 串（GPTBot/1.1、OAI-SearchBot/1.0、ChatGPT-User/1.0、ClaudeBot/1.0、Claude-SearchBot/1.0、PerplexityBot/1.0、Perplexity-User/1.0、Googlebot/2.1(代 Google-Extended)、Applebot/0.1、bingbot/2.0）全部 status=200、size_download=341603，与 Chrome/131 基线完全相同。逐字节比对：每个 UA 与基线仅差 20–21 字节，全部落在 offset 69413–69433 的 Next.js 每次渲染 id（基线 `\"$9\",\"JiT2PWtoJrM0X1LD0KY7H\"` vs GPTBot `...ht95VxSorwf41nmjQxz0B...`）；浏览器连续两次抓取该 id 同样变化（base1 vs base2 差 20 字节，同一 offset）。屏蔽该 id 后归一化 MD5 全部 = 871d893daf32dea6cbd3e2bc45d71943（11 个响应，含 2 次浏览器基线）。深层页复测：10 个 UA 在 /case/061 均 200/290270B、在 data-model 页均 200/345588B，与浏览器字节数完全一致。

**✓ `g.ssr` 5/5** — Main content server-rendered

*Why this tier:* 不是 3 档，因为 8/8 页都在不执行 JS 的 HTML 里带正文，没有「部分页可见」的情况。

curl 抓取后剥离 script/style/noscript 再抽文本（不执行 JS），8 页字符数/汉字数依次为 3687/2660、2724/1745、2665/1475、14291/7339、1871/1058、1736/1193、3442/2616、3624/2796。命中原句（p4，纯 HTML 响应内）：「餐厅和连锁餐饮行业是满足人们日常餐饮需求的重要组成部分。随着消费者对餐饮体验、食品安全和便捷性的要求不断提高，行业竞争日益激烈。」p6：「该方案针对智能家居行业的痛点，通过明道云的低代码平台实现了客户、项目、库存、财务等模块的系统化管理。」p5 的 204 项对比表格单元格文字同样在 HTML 中。

## Understandable — 18 / 22

**✓ `p1.sitemap` 4/4** — Sitemap discoverable and fresh

*Why this tier:* 不是 2 档，因为 lastmod 覆盖率是 100% 而非「多数」，且 robots.txt 声明的两个 sitemap 都可达。

robots.txt 声明两条：Sitemap: https://www.mingdao.com/sitemap.xml 与 https://www.mingdao.com/landing/data-model/sitemap.xml。主 sitemap 200、47938 字节、application/xml，<url> 296 个、<lastmod> 296 个（296/296 = 100%）。副 sitemap 200、32077 字节、153/153 带 lastmod。最新 lastmod 2026-08-20T00:00:00.000Z（/、/solution、/case），次新 2026-08-18T17:56:38.000Z（/solution/038）。

**✓ `p1.llms-txt` 5/5** — llms.txt present and structured

*Why this tier:* 不是 4 档，因为含链接的主题分节有 9 个，远超「2 个以上」的门槛。

https://www.mingdao.com/llms.txt 200、5695 字节、text/plain; charset=UTF-8。站点定义段为 3 行 `>` 引用，原句：「明道云是一个面向企业的零代码 / 低代码应用平台，产品名为 HAP（Hyper Automation Platform，超级自动化平台）。」`##` 分节 10 个：产品(12 链接)、方案与案例(2)、行业数据模型(5)、Markdown 版页面(6)、开发者(5)、伙伴与服务(5)、教育与认证(4)、公司(5)、条款(2)、内容使用偏好(0)。抽出 49 个 URL 逐条 curl -L：48 个 200，1 个非 200 系我的正则把 `https://api.mingdao.com/mcp`（streamable-http）。` 的中文尾巴一并截入所致，非真实死链。

**◐ `p1.organization` 5/6** — Organization + WebSite sitewide

*Why this tier:* 不是 6 档，因为 6 档要求 logo 可解析「且」含 sameAs，两个条件都不满足：logo GET 返回 403，sameAs 在 8 页中一个都没有。

8/8 页各有 1 个 application/ld+json 块。7 页含 Organization + WebSite；首页 Organization 节点带 name「明道云」、alternateName[上海万企明道软件有限公司, Mingdao HAP]、url https://www.mingdao.com、logo https://fp1.mingdaoyun.cn/open/img/logo.png、description、contactPoint(+86-400-665-6655)。logo 实测：curl -L 返回 403，304 字节，content_type=text/html（file 判定为 HTML 文本，不是 PNG）。grep 'sameAs' p1..p8.html：0 命中。例外：p4（data-model 页）的 Organization 节点只有 name+url，且整页无 WebSite 节点，schema 类型为 Organization/WebPage/TechArticle/BreadcrumbList/ItemList——「两者齐全含 logo」实际成立于 7/8 页。

**◐ `p1.breadcrumb` 2/3** — BreadcrumbList on nested pages

*Why this tier:* 不是 3 档，因为 7 个层级页里只有 1 个带 BreadcrumbList，hap/、compare/、solution/、case/ 四个页族整族没有，够不上「层级页普遍有」。

8 个抽样 URL 中 7 个为层级页（除首页）。grep 'BreadcrumbList'：仅 p4 命中 1 次，itemListElement 3 项——首页(https://www.mingdao.com) → 数据模型(/landing/data-model) → 餐厅和连锁餐饮。加抽 4 页复核：/landing/data-model/comprehensive-hospital.html 200/333006B 同样有 BreadcrumbList；/compare/matrix 200/624158B、/solution 200/647803B、/case 200/264504B 的 ld+json 类型均只有 ['Organization','WebSite']，无 BreadcrumbList。p6 页面顶部有可见的「伙伴解决方案」标签但无对应结构化数据。

**◐ `p1.page-type` 2/4** — Page-type schema where applicable

*Why this tier:* 不是 4 档，因为只有 data-model 一个页族有页型 schema；最该用 Product+Offer 的价格页一项没有，compare/solution/case 三族也只有 Organization+WebSite。也不是 0 档，因为 data-model 的 TechArticle+ItemList 字段是真实的。

适用页型确实存在：/hap/price 列出四个明码标价版本（¥0/年、¥14900/年、¥29900/年、¥59900/年，另有 ￥0/￥1242/￥2492 月折算），Product+Offer 完全适用。grep '\"Product\"'、'\"Offer\"'、'HowTo'、'FAQPage'：8 页全部 0 命中。有的一处：p4 的 TechArticle（headline/description/inLanguage/publisher/articleSection[行业概述,核心运营活动,主要业务流程,主要管理指标,数据模型]/keywords）+ ItemList（numberOfItems 12，12 个 ListItem 各带 name、description、url 锚点 #activity-1..#activity-12，如「菜品研发与管理／根据市场趋势和消费者反馈，开发新菜品，并对现有菜品进行优化和标准化管理。」）——字段真实非占位。

## Content Citability — 20 / 35

**◐ `p2.answer-passages` 7/9** — Self-contained answer passages

*Why this tier:* 恰好 4/8 = 半数，取 7；不是 9 档，因为「多数」需要 5 页以上。也不是 4 档，因为通过页确为 4 页而非少数。

中文站按 v1.1 规则 7 换算：自足答案段判定为 50–200 汉字（英文口径 25–120 词），下同。通过 4 页：p4 正文 1% 深度处连续 3 段，162/139/146 汉字（原句「餐厅和连锁餐饮行业是满足人们日常餐饮需求的重要组成部分。…」）；p6 14% 深度 109 汉字（「该方案针对智能家居行业的痛点，…提升了客户满意度和运营效率。」）；p7 29%–62% 深度 5 段 50–63 汉字（原句 50 汉字：「项目从需求到投产常历经多轮沟通与排期，导致审批、营销、运营等一线场景无法快速上线迭代，影响客户体验与经营时效。」）；p8 27% 深度 114 汉字（「随着招投标项目数量和业务复杂度不断上升，九域博慧方舟原有系统逐渐难以支撑日常运营。…」）另有 83/87/92/94 汉字多段。不通过 4 页：p1 正文前部最长仅 21–28 汉字标语，落在 50–200 区间的 12 段全是 62%–73% 深度的客户证言；p2 仅 1 段 56 汉字真散文且在 77% 深度（「通过多项资质认证，包括ISO27001、ISO9001、等保三级、CMMI3。…」），其余为页脚导航串；p3 在区间内的 2 段全是页脚导航串；p5 在区间内的 4 段是表格单元格里的顿号功能清单（64/81 汉字）与页脚串，非散文。超上限记录：p7 首段 282 汉字、客户挑战 295 汉字、方案 336 汉字；p8 首段 204 汉字。

**✓ `p2.question-intent` 7/7** — Headings match how people ask

*Why this tier:* 7/8 贴近提问意图，属「多数」；不是 5 档，因为按 v1.1「看实质不看格式」，任务句与说明句同样计入，过半以上而非恰好半数。

逐条 <title>：p3「明道云HAP价格与版本对比｜免费版起」对应「明道云多少钱」；p5「明道云HAP VS 简道云｜能力对比矩阵」对应「明道云和简道云有什么区别」；p2「明道云HAP产品特性｜八大核心能力全景」对应「明道云有哪些能力」；p6「智能家居行业的流程自动化与API集成」；p7「华夏银行“春芽”引领低代码浪潮：从全民开发到高价值落地，提质降本增效」为完整说明句；p8「招投标管理从旧系统走向全流程协同」为说明句；p4「餐厅和连锁餐饮行业应用数据模型 | 餐饮管理 | 供应链管理 | 客户关系」——句头贴近提问，句尾三段竖线关键词属关键词串，计为通过但有瑕疵。不通过 1 页：p1「明道云HAP｜零代码企业应用平台与超自动化引擎」，品牌名+品类descriptor，按 v1.1 属品牌标签。

**◐ `p2.freshness` 3/6** — Freshness signal present

*Why this tier:* 只有 2/8 页有读者可见日期，属「部分页有」；不是 6 档，因为多数页零日期信号，且全站 8 页无 dateModified 可与之一致。

结构化数据：grep -E '\"date(Published|Modified)\":' 于 p1..p8 → 0 命中；grep <meta ...(article:published_time|article:modified_time|date) → 0 命中。页面可见日期 2/8：p7「2021年5月 启用日期」、p8「2026年3月 启用日期」（p8 正文另有「2026年3月底系统按计划上线」）。8/8 页脚均为「© 2012- 2026 mingdao.com」，按惯例未计为时效信号。HTTP 头：/、/case/605 无 last-modified（cache-control: private, no-cache, no-store）；仅静态的 /landing/data-model/*.html 带 last-modified: Thu, 27 Aug 2026 05:57:23 GMT——但档位文字限定「页面与结构化数据」，故未计入。sitemap 的 296/296 lastmod 已在 p1.sitemap 计分，未重复计。

**◐ `p2.sourced-stats` 3/7** — Statistics carry a source

*Why this tier:* 3/8 页给出了某种出处，属「部分标注」；不是 5 档，因为绝大多数单个数字仍是裸数字；不是 7 档，因为没有任何一处出处可点击。

有标注的 3 页：p5 表尾原句「本页对比内容由 AI 从各厂商官网、帮助文档及公开资料抓取整理，请注意鉴别。」并对无据项标「暂无数据支撑结论」（该短语在页内多次出现）；p7 顶部「内容贡献者：第11服务团」；p8 顶部「内容贡献者：上海龙林信息科技有限公司」。裸数字举例：p7「业务人员自助搭建场景应用已超过300个，场景应用数达1800+，覆盖用户3.2万、日均访问用户4000+、日均访问2.1万」「低代码模式将15人月工作缩短至1人月」「单项目节省费用超12万，预计年节省工时超6036小时」「非科技人员占比超70%」；p8「代理费计算准确率由约85%提升至100%」「效率提升90%以上」「任务超期率下降60%」「节省约40%预算；结项回访内部评分4.8/5」；p1「在10万员工级别客户中验证了集群的稳定性」。可点击性核查：p1/p5/p7/p8 的站外 href 去重后 15 条，全部是页脚友情链接（infordata.com.cn、intsig.com、authing.cn、esign.cn、fadada.com、datamesh.com.cn 等）与 beian.gov.cn 备案链接，无一是引证链接。

**✗ `p2.named-author` 0/6** — Named, verifiable authorship

*Why this tier:* 正落在 0 档判据「无署名或仅署机构名」；两处署名都是团队/公司而非人名，够不上 3 档的「署真实姓名」。

grep -E '<meta[^>]*author[^>]*>' p1..p8.html → 0 命中。8 页正文中唯一的署名字段是 p7「内容贡献者：第11服务团」与 p8「内容贡献者：上海龙林信息科技有限公司」，均为机构；两者都不带链接。其余 6 页无任何署名区块。

## Brand Credibility — 9 / 18

**◐ `p3.listings` 3/4** — Third-party listings

*Why this tier:* 实测在线的第三方平台是 4 家，落在 3 档(3–4 家)；不是 4 档，因为需 5 家以上，而本可凑数的腾讯云与华为云商品页已下架/404。

在线可核实 4 家：①阿里云云市场 market.aliyun.com/products/56014009/cmjj00063289.html 200/43033B，<title> 含「明道云-零代码企业应用搭建私有部署-云市场-阿里云」；同站 /products/9000000220/cmjj00039214.html 200/43138B。②Apple App Store 中国区，itunes.apple.com/search?term=明道云&country=cn 返回 resultCount=5，其中「明道云」id468630782、「明道云(私有部署)」id825276156，sellerName 均为 Shanghai Wanqi Mingdao Software Co., Ltd.。③PartnerShare www.partnershare.cn/product/ming-dao-yun 200/70522B。④36氪创投平台 pitchhub.36kr.com/project/1713086958266626 200/93409B。已失效/不可核实：腾讯云市场 market.cloud.tencent.com/products/19148 与 /19693 均返回 200 但 <title> 为「很抱歉，您访问的商品不存在 - 腾讯云应用市场」(68785B)；华为云商店 contents/ac657a62-78b1-4e7f-92c0-7f64af9ff73d 与 contents/77b99aff-bd23-4539-aae2-df5ce161921e 均 404(49088B)；G2 /products/mingdao/reviews 403、Capterra /p/218757/Mingdao/ 403、鲸选型 403；Google Play com.mingdao.app 404。

**✓ `p3.mentions` 4/4** — Independent mentions

*Why this tier:* 不是 3 档，因为不止「存在独立报道」：科技媒体、消费科技媒体、云厂商开发者社区、UGC 评测四条渠道各有内容，且时间跨 2021→2026-07，构成「多渠道持续」。

①中关村在线 m.zol.com.cn/article/12165609.html 200/167815B，页内日期 2026-07-16，标题「2026十大零代码平台盘点」，原句「明道云 —— 零代码aPaaS，灵活但需自建」「明道云、轻流等平台走“平台能力”路线，不提供开箱即用的场景方案」。②阿里云开发者社区 developer.aliyun.com/article/982567 200/106115B，<title>「全网最全的低代码/无代码平台盘点:Notion Like 产品、简道云、伙伴云、明道云、轻流…」。③36氪 36kr.com/p/1313301282259716 200/17603B（正文 JS 渲染，标题据检索索引「36氪首发｜「明道云」转型APaaS领域后完成近亿元融资，发力伙伴关系」）。④知乎专栏 zhuanlan.zhihu.com/p/485268765「明道云零代码应用搭建平台如何？明道云无代码开发平台评价如何？」——对机器 UA 返回 403，仅凭检索索引标题。

**✗ `p3.knowledge-graph` 0/4** — Knowledge-graph entity

*Why this tier:* 3 个知识库里 2 个已用 API 确证无条目，第 3 个（百度百科）经两轮站内限定检索只捞到创始人与前身产品条目、未见「明道云」本体条目，故取 0；4 档要求存在对应实体条目，未满足。

Wikidata wbsearchentities：search=明道云 → {"search":[],"success":1}；search=上海万企明道软件 → 空；search=明道云HAP → 空；search=Mingdao → 仅 Q1073110 永嘉玄覺、Q11088210 明道(北宋年号)等 8 个无关历史人物。zh.wikipedia action=query&list=search&srsearch=明道云 → 明道(藝人)、明道大學、边云波、陈道明、鄭凱云，无匹配。百度百科：直连 baike.baidu.com/item/明道云 与 /item/上海万企明道软件有限公司 均 403（<title>百度安全验证，2520/2601 字节），WebFetch 同样 403；两次 allowed_domains=baike.baidu.com 的限定检索返回的是 baike.baidu.com/item/任向晖/5846811（创始人）、baike.baidu.com/item/明道/2475680（「梅花信息推出的企业软件平台」，前身产品）以及竞品 baike.baidu.com/item/简道云/53684529、/item/得帆/49759805，未出现「明道云」条目。

**✗ `p3.sameas` 0/3** — sameAs complete and resolving

*Why this tier:* 正落在 0 档「未声明」；量表明文规定未声明记 0 且不退出分母，故不作 not_applicable 处理。

grep 'sameAs' p1.html..p8.html → 无任何文件命中。首页 Organization 节点字段完整清单为 @type/@id/name/alternateName/url/logo/description/contactPoint，无 sameAs。可绑定的账号在页脚以非结构化形式存在：href="https://space.bilibili.com/314748279"、文本「微信公众号：明道云」「小红书号：3152645850」，以及视频号/抖音的二维码图片（无 href）——都没有进入 schema。

**◐ `p3.video` 2/3** — Video and multimodal presence

*Why this tier:* 3 档要求「持续输出且站内带 VideoObject」两个条件同时成立，站内 VideoObject 为 0，故封在 2 档——尽管内容量实际远超 2 档「零星」的描述。

官方 B 站号 space.bilibili.com/314748279（自 p1/p5/p7/p8 页脚 href 取得，空间页 200）。api.bilibili.com/x/space/navnum?mid=314748279 → {"video":471,"cinema":2,"season_num":16}；api.bilibili.com/x/relation/stat?vmid=314748279 → {"follower":13643}。站内标记：grep 'VideoObject' p1..p8.html → 0 命中。页脚另有抖音、微信视频号、小红书（3152645850）三处二维码图片，均无可跟随链接。

## Answer Fit — 7 / 10

**◐ `p4.answer-shape` 2/4** — Content shaped for extraction

*Why this tier:* 不是 4 档，因为「小标题、列表、表格齐备且段落适中」只在 1/8 页成立；篇幅最长、最可引用的两个案例页恰恰是 h2 以下无层级、段落最长的。也不是 0 档，因为多数页仍有可识别的小标题。

标签普查（h1/h2/h3/h4/p/table/ul/ol）：p1 1/2/2/0/3/0/19/0；p2 0/0/1/0/1/0/17/0；p3 0/0/1/0/2/0/10/0；p4 1/5/51/60/70/60/0/2；p5 1/0/1/0/1/1/2/0；p6 1/0/3/6/7/0/2/0；p7 1/1/0/0/0/0/2/0；p8 1/1/0/0/0/0/2/0。即：p7、p8 的全部正文散文都装在 div 里，<p> 元素数为 0，且首段分别长 282/295/336 汉字与 204 汉字；p2、p3 无 h1 无 h2；p3、p6、p7、p8 无 table。仅 p4 同时具备完整标题层级、70 个 <p>、60 张表与 2 个有序列表。

**◐ `p4.question-coverage` 3/4** — Coverage of the questions people ask

*Why this tier:* 按「有独立页面正面回答」计为 8/10，落在 3 档(6–8)；不是 4 档，因为差的 2 条恰是买家最先问的定义题与安全合规题，站内没有承接页面。

覆盖 8 条（均在 www.mingdao.com 实测 200）：价格版本→/hap/price 302312B；选型对比→/compare/matrix 624158B 及 6 个 hap-vs-* 页；私有部署→/hap/pd 299137B「社区版免费·前端开源」；能搭什么系统→/solution 647803B（sitemap 内 143 条）；集成与 API→/appintegration 280121B + apidoc.mingdao.com 200；行业该建哪些表→/landing/data-model 132644B（副 sitemap 153 条）；真实案例与效果→/case 264504B（sitemap 内 114 条）；培训与认证→/edu/certificate 260379B。未覆盖 2 条：①「什么是零代码、和低代码有什么区别」——/zerocode、/whatiszerocode、/faq 均 404，296 条主 sitemap 中无术语/定义页；②「安全合规与信创」——/security、/trust 均 404，仅以 /hap/feature 内一个小节回答，原句「通过多项资质认证，包括ISO27001、ISO9001、等保三级、CMMI3。采用多项安全防护措施，并经过阿里云、腾讯云和深信服的基线检测与安全厂商的镜像、漏扫、渗透检测。」

**✓ `p4.cn-engines` 2/2** — Chinese engine readiness

*Why this tier:* 不是 1 档，因为除可抓取外，备案号、公安备案号、法人主体名与联系方式四项齐备。

中文引擎实测（首页）：Baiduspider/2.0 200/341603B、Sogou web spider/4.0 200/341603B、360Spider 200/341603B、Bytespider 200/341603B——字节数与浏览器基线 341603 完全一致。robots.txt 的放行组明确列入 Bytespider。备案与主体：8/8 页页脚原句「iTrust 沪公安备 31010402008586号 | 沪ICP备14017582号 | 等保三级认定 | ISO27001 认定 | ISO9001 认定 | © 2012- 2026 mingdao.com」，法人主体「上海万企明道软件有限公司」见首页 Organization.alternateName，联系方式「电话咨询：400-665-6655 邮箱：feedback@mingdao.com」。

## Bonus — +0 (outside the denominator)

**✗ `b.llms-full` 0/2** — llms-full.txt

*Why this tier:* 无全文聚合文件；llms.txt 提供的是逐页 .md，属于另一件事，不满足「全文聚合」判据。

https://www.mingdao.com/llms-full.txt → 404，1861 字节，content_type=text/html。robots.txt 未声明任何等价路径。llms.txt 的「## Markdown 版页面」列的是 6 个逐页文件：/md/index.md 200/4911B、/md/hap-feature.md 200/4845B、/md/hap-price.md 200/3579B，均为 text/markdown; charset=UTF-8——是分页 Markdown，不是聚合全文。

**✗ `b.ai-txt` 0/2** — ai.txt

*Why this tier:* 判据点名 ai.txt 这个端点；AI 使用政策确实声明了，但在 robots.txt 与 llms.txt 里，不在 ai.txt。

https://www.mingdao.com/ai.txt → 404，1861 字节，text/html。政策实际存在于两处：robots.txt 两组各有一行 `Content-Signal: search=yes, ai-input=yes, ai-train=no`；llms.txt 末尾「## 内容使用偏好」段原句「允许搜索引擎索引，允许 AI 在回答用户提问时实时引用本站内容（请注明来源并链接回原页面），不允许将本站内容用于训练或微调生成式模型。」

**✗ `b.geo-link` 0/1** — GEO link tags

*Why this tier:* head 内无任何面向 AI 检索的 link 关系；已有的内容协商能力没有在 head 里声明出来。

首页 <link rel> 全量：stylesheet ×8、preload ×4、preconnect ×1（https://www.mingdao.com）、canonical ×1（https://www.mingdao.com）、icon ×1。无 rel 指向 llms.txt，无 <link rel="alternate" type="text/markdown">。旁证：内容协商本身是通的——curl -H 'Accept: text/markdown' https://www.mingdao.com/ 返回 200、4911 字节、text/markdown; charset=UTF-8——但这一能力只写在 llms.txt 正文里，head 中无声明。

**✗ `b.speakable` 0/1** — speakable markup

*Why this tier:* 未标注任何可朗读区域。

grep 'speakable' p1.html..p8.html → 8 个文件全部 0 命中。

## Citation performance — not scored

未测，不打分。AI 引用表现按 v1.1 是结果型指标，需要用行业真实问题在 ChatGPT / Perplexity / 豆包 / 文心等引擎逐个实测被引用情况；同一问题多次提问结果不同，不可复现，且它由就绪度与时间共同决定。本次审计只做站外可观测、站方可修的就绪度部分，引用表现应作为独立区块单独立项报告，不并入上面这 69 分。

## Auditor's caveats

- p2.answer-passages 的 7 分踩在 7 与 4 的分界线上，且 4 个通过页里有 2 个是边界判定。p7 真正的导语是 282 汉字，超出 50–200 上限，它能通过靠的是 29%–62% 深度处几段 50–63 汉字的散文（最短那段正好 50 字，压线）；p8 导语 204 汉字，只超 4 个字。如果把「正文前部」严格读作正文前 20%，p7 不通过，本项掉到 4 分（少数页有），总分 66、仍在基础扎实档但只剩 0 分余量；如果把 200 字上限读作参考而非硬边界，p7/p8 靠导语即通过，结果不变。也就是说这 7 分向下脆弱、向上稳固。
- p2.freshness 给 3 还是给 0 是本次最有争议的一处。8 个抽样页里唯一的读者可见日期是 p7「2021年5月 启用日期」和 p8「2026年3月 启用日期」——这是客户系统上线时间，不是页面的发布或更新时间。全站 8 页没有 datePublished、dateModified、article:published_time，也没有「更新于」字样。我按 v1.1「时间信号看的是读者与爬虫能否确认时效」判为 3，因为对一篇案例而言上线时间确实能让读者判断新旧；但把它归为内容数据、判 0，同样讲得通，那样总分是 66，正好卡在档位线上。另外两项我刻意没计入：页脚「© 2012- 2026」按惯例不算时效信号；sitemap 的 296/296 lastmod 与 data-model 页的 HTTP Last-Modified 头也没算，因为档位文字限定在「页面与结构化数据」——但后者对爬虫其实是真实可用的时间信号，这是量表本身可以再想的地方。
- p3.video 的 2 分是量表档位不够用，不是判定为难。B 站 471 个视频、13643 关注、16 个合集，跟 2 档描述的「内容零星」完全相反；但 3 档把「持续输出」和「站内带 VideoObject」捆在一起，而 VideoObject 全站 0 命中，只能封在 2。结果是这一分同时低估了渠道、高估了标记。建议 v1.2 把这两个条件拆开，否则任何「内容做得很足但没上 schema」的中文站都会被压在同一格。
- p3.knowledge-graph 判 0 有残余不确定。Wikidata 和中文维基我是用 API 确证为空的（wbsearchentities 对明道云/上海万企明道软件/明道云HAP 三个词都返回 search:[]），但百度百科对我试过的所有 UA 都返 403 百度安全验证，直连和 WebFetch 都进不去，只能靠两轮站内限定检索间接判断——检索捞回来的是创始人任向晖的条目和前身产品「明道（梅花信息推出的企业软件平台）」的条目，以及竞品简道云、得帆的条目，唯独没有明道云本体。对一个中文 SaaS 来说，百度百科正是最可能有条目的地方，而它恰恰是我核不动的那个。若实际存在明道云条目，本项应为 4 分，总分 73，档位不变。
- 抽样运气在 p1.breadcrumb 和 p1.page-type 两项上放大了误差。全站只有 /landing/data-model/ 这一个页族（153 页）带 BreadcrumbList + TechArticle + ItemList，而我这 8 个 URL 恰好抽中其中 1 页。多抽一页，breadcrumb 就可能够到「层级页普遍有」；一页没抽中，这两项都是 0。8 页抽样是量表的规则，但对这种「一个页族做得很好、四个页族什么都没有」的站，它是个高方差的量具。更诚实的说法是：data-model 页族的结构化数据做得相当完整，hap/、compare/、solution/、case/ 四族基本裸奔——这个事实比 2 分或 3 分本身更有用。
- p4.question-coverage 的 3 分卡在一条定义题上。我只按「有独立页面正面回答」计，所以「什么是零代码、和低代码有什么区别」（/zerocode、/whatiszerocode、/faq 全 404，296 条 sitemap 里无术语页）和「安全合规与信创」（/security、/trust 均 404，只在 /hap/feature 里有个小节）都算未覆盖，得 8/10。若把那个安全小节算作覆盖就是 9/10，本项变 4 分。另外我把覆盖范围限定在 www.mingdao.com：blog.mingdao.com 一周更新数次（首屏三条 2026-09-02、2026-09-01、2026-08-27，且都带可见日期），大概率能补上零代码定义那一条——但它是另一个 host，不在 www 的 sitemap 里，更要紧的是也不在 llms.txt 里（llms.txt 列了 apidoc，却没列 blog 和 help）。全站最新鲜、最像内容的那部分，恰好是没被指路的那部分。
- p1.organization 的 5 分建立在 7/8 页之上，有个值得点名的不一致：data-model 页的 Organization 节点只有 name+url，整页没有 WebSite 节点——「两者齐全含 logo」成立于 Next.js 的 www 模板，不成立于静态的 /landing/ 页族。而模板里声明的那个 logo（fp1.mingdaoyun.cn/open/img/logo.png）实测 403、304 字节、返回的是 HTML 不是 PNG。修好这个链接再补上 sameAs（页脚已经有 B 站、公众号、视频号、抖音、小红书五个账号，只是没进 schema），第 6 分是现成的。
- v1.1 的标定文件把 mingdao.com 回测投影为 50%（起步期），我实测 69%。我没有复核 v1.0 当时的逐项证据，但这次看到的东西——一份点名 15 个检索 UA 并带 Content-Signal 的 robots.txt、一份 5695 字节且 48/49 链接可达的 llms.txt、可用的 Accept: text/markdown 内容协商、.well-known/mcp.json 与 agent-skills 索引——不像是那份投影所依据的那个站。这 19 分的差距应当读作「站点变了」，不应读作「量表漂了」，更不能拿我的 69 去反证投影方法的准确性。这也正好印证标定文件自己写的那句：按 v1.1 重跑的真实审计此前尚未进行。

