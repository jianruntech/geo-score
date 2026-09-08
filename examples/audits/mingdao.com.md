# mingdao.com — AIV 29 / 85 (v1.0)

**34% · Critical** · audited 2026-09-08 · audience `zh-Hans`

> 明道云 www.mingdao.com：手写了 5.7KB 的 llms.txt、Content-Signal、.well-known/mcp.json 和 6 页 Markdown 镜像，10/10 检索型爬虫可达；但 8 个抽样页上 sameAs、dateModified、speakable、FAQPage、Offer 全是 0 次命中 —— AIV 29 / 85 (v1.0)，归一化 34%，Critical。

Machine-readable: [`mingdao.com.json`](mingdao.com.json)

## Sampled URLs (8)

- `https://www.mingdao.com/`
- `https://www.mingdao.com/hap/feature`
- `https://www.mingdao.com/hap/price`
- `https://www.mingdao.com/hap/pd`
- `https://www.mingdao.com/solution/038`
- `https://www.mingdao.com/case/061`
- `https://www.mingdao.com/solution/230`
- `https://www.mingdao.com/case/605`

## Infrastructure — 14 / 20

**✓ `p1.robots-allows-retrieval` 3/3**

robots.txt 返回 200、text/plain、1958 字节。10 个检索型 UA 全部未被禁止：OAI-SearchBot、ChatGPT-User、Claude-SearchBot、Claude-User、PerplexityBot、Perplexity-User、Amazonbot 命中文件里显式的「AI 爬虫」组（该组写 Allow: /，只 Disallow /act /aja /adm /app）；Googlebot、Bingbot、Applebot 没有专属组，落到 User-agent: * ，同样只禁这 4 个前缀。floor(3 × 10/10) = 3。附带观察：文件用 Content-Signal: search=yes, ai-input=yes, ai-train=no 表达训练用途偏好，而不是靠拦爬虫，按 ai-crawlers.md 这不扣分。另一处实际冲突：Disallow: /act 与 Disallow: /app 这两个前缀挡住了 sitemap 和 llms.txt 都收录的 /activitycenter 与 /appintegration。

**✓ `p1.retrieval-reachable` 3/3**

用 10 个检索型 UA 各请求一次首页（curl -L 跟随重定向）：全部 HTTP 200，响应体均为 341,603 字节的真实页面，都含 <title>明道云HAP｜零代码企业应用平台与超自动化引擎</title> 与 <h1 class="action act homeHeroTitle">搭建可投入生产的企业应用</h1>；没有 403、没有挑战页、没有 JS 中间页。响应头 server: openresty、x-powered-by: Next.js，未见 Cloudflare 一类 bot 管理层。floor(3 × 10/10) = 3。

**✓ `p1.llms-txt` 3/3**

/llms.txt 返回 200、text/plain; charset=UTF-8、5,695 字节、97 行、0 次重定向。H1 为「# 明道云（Mingdao）」；紧跟 3 行「>」摘要引用块；共 10 个 ## 分节，其中 9 节带链接（产品 12 条、方案与案例 2、行业数据模型 5、Markdown 版页面 6、开发者 5、伙伴与服务 5、教育与认证 4、公司 5、条款 2），全文 46 条 Markdown 链接。可解析、合法 Markdown、有 H1、有摘要引用块、≥3 个分节链接组，五项条件全部满足。内容不是自动生成的目录堆砌：行业数据模型一节还写明了 152 个行业页的统一结构与 #activity-1 到 #activity-12 锚点约定。

**✗ `p1.llms-full-txt` 0/2**

/llms-full.txt 返回 404，0 次重定向，content-type text/html，响应体 1,861 字节——与 /this-path-does-not-exist-12345 返回的通用 404 页字节数完全一致。仅按状态码判定：不存在。

**✗ `p1.ai-txt` 0/2**

/ai.txt 返回 404，0 次重定向，1,861 字节，与通用 404 页一致。仅按状态码判定：不存在。附注：站点把内容使用偏好放在了 robots.txt 的 Content-Signal 指令和 llms.txt 末节「内容使用偏好」里，是一种替代表达，但本项的 pass 条件只问 /ai.txt 是否解析。

**✓ `p1.sitemap` 3/3**

/sitemap.xml 返回 200、application/xml、47,938 字节、296 个 <url>，每条都带 <lastmod>。robots.txt 用两条 Sitemap: 指令引用它以及 /landing/data-model/sitemap.xml（后者 200、text/xml、153 个 <loc>），并注明主 sitemap 未收录那批行业数据模型页。语言覆盖：<html lang="zh-Hans">，导航列出 6 种界面语言，但 /en、/en/、/ja、/zh-TW 全部返回 404；8 个抽样页 grep hreflang 与 rel="alternate" 命中 0 次；带 Accept-Language: en-US 或 lang/i18n cookie 请求首页，<title> 仍是中文——即只存在 zh-Hans 一套可索引 URL，sitemap 已覆盖。

**✗ `p1.geo-link-tags` 0/2**

首页 <head> 共 16 条 <link>：8 条 stylesheet、5 条 preload、1 条 preconnect、1 条 canonical、1 条 icon。8 个抽样页 grep 「llms」「ai-policy」「rel=\"llms\"」命中均为 0。llms.txt 本身存在且质量很高，但 HTML 里没有任何指向它的发现入口，只能靠爬虫猜根路径。

**✓ `p1.ssr-content` 2/2**

不执行 JavaScript、直接 curl 取回的 HTML 就含各页正文。例证：/case/605 原始 HTML 里包含完整的 204 汉字案例概览段，以及「客户挑战 / 解决方案 / 核心效益」全部条目正文；/hap/price 原始 HTML 含四档年费（¥0 / ¥14900 / ¥29900 / ¥59900）与全部约 80 行配额；/solution/230 含 83 汉字的方案简介与全部角色、流程、数据对象条目。8 页均无 <meta name="robots">，无 noindex。

## Structured Data — 4 / 17

**✓ `p2.organization-website` 4/4**

8 个抽样页每页各有 1 段 application/ld+json，内容逐字相同的 @graph：Organization（@id https://www.mingdao.com/#organization，name「明道云」，alternateName ["上海万企明道软件有限公司","Mingdao HAP"]，含 url / logo / description / contactPoint，电话 +86-400-665-6655，areaServed CN）+ WebSite（@id .../#website，publisher 用 @id 反指 organization）。8 段 JSON 全部解析通过。抽样外再验 /edu/certificate，同一段。

**✗ `p2.article-author` 0/4**

抽样里的 4 个文章型页面（/solution/038、/case/061、/solution/230、/case/605）都是长篇编辑内容——案例页有客户名称、所属行业、企业规模、启用日期和数千字叙述——但 8 页 grep「Article」「BlogPosting」「datePublished」「dateModified」命中全为 0，全站结构化数据只有 Organization + WebSite。页面上的署名是机构或团队：/case/061「内容贡献者：第11服务团」、/case/605「内容贡献者：上海龙林信息科技有限公司」、/solution/230「由 山东中政数海大数据有限公司 提供」，/solution/038 的「由…提供」栏渲染为空。没有 author 属性，也没有可解析的身份。0/4 → floor(4 × 0/4) = 0。补充：站点确有博客，但在 blog.mingdao.com 这个独立主机上，不属于本次审计目标 www.mingdao.com，也不在其 sitemap 内。

**⊘ `p2.faqpage` — not_applicable**

8 个抽样页的渲染文本里，以「？」结尾的行数为 0；标题全是陈述式小节名（方案简介 / 角色 / 流程 / 数据对象 / 效果 / 客户挑战 / 解决方案 / 核心效益 / 案例概览）。抽样外再查 /hap/price 与 /edu/certificate，问句行同样为 0。唯一的问句是案例页底部 CTA「想了解明道云HAP如何助力您的企业？」，属营销按钮而非问答内容。本项分母为空，按规则 5 从分母剔除 3 分。

**✗ `p2.speakable` 0/3**

8 页 grep「speakable」命中 0 次。分母并不为空：抽样中确有具备清晰答案段的页面——/solution/038（109 汉字方案简介）、/solution/230（83 汉字方案简介）、/case/061 与 /case/605 的开篇概览段——共 4 页有可指认的答案段，却没有一页声明 speakable。floor(3 × 0/4) = 0。

**✗ `p2.product-offer` 0/3**

/hap/price 是明确的定价页：HTML 中含四档年费（免费版 ¥0、标准版 ¥14900、专业版 ¥29900、旗舰版 ¥59900）、折合月费、以及约 80 行功能配额对比与增值服务报价（如「300元/人/年」「20元/1G/年」）。但该页 JSON-LD 仍只有 Organization + WebSite；8 页 grep「Offer」命中 0 次，「Product」的唯一命中是 CSS 类名 isProduct，不是 schema.org 类型。商业页型确实存在而标记缺失，因此判 failed 而不是 not_applicable。

**✗ `p2.howto-breadcrumb` 0/3**

8 页 grep「BreadcrumbList」「HowTo」「itemprop」命中均为 0，页面上也没有可见的面包屑串（/solution/230 顶部的「伙伴解决方案」是分类标签，不是层级路径）。抽样里层级是明确的：/hap/feature、/hap/price、/hap/pd 同属 /hap/；/case/061 与 /case/605 属 /case/（共 114 个案例页）；/solution/038 与 /solution/230 属 /solution/（共 143 个）。/hap/pd 还有「快速安装」四种方式的过程型内容。页型存在、标记缺失。

## Content Citability — 1 / 25

**✓ `p3.answer-passages` 1/5**

中文换算口径（本报告自定，供复核）：rubric 的 40–90 词按中文平均 1.5–1.8 字/词折算为 60–160 汉字；逐页量取正文主区第一段。达标 2/8：/solution/230 的「方案简介」83 汉字（「智慧消防远程值守平台基于明道云低代码平台，连接消控主机和物联网设备……」），/solution/038 的「方案简介」109 汉字，两段都自带主语、点明平台与行业，脱离上下文也能独立引用。不达标 6/8：首页正文主区是口号栅格，H1「搭建可投入生产的企业应用」仅 11 字，全页最长的连续散文是轮播里的客户证言（86 汉字）而非开篇；/hap/feature 没有 H1，文档序上第一条 ≥40 汉字的散文出现在页面深处（44 汉字的智能体说明）；/hap/price 全页没有任何一行达到 40 汉字，纯表格；/hap/pd 开篇只有 24 字副标题「社区免费版，前端开源，支持OTA升级，Docker高效部署」；/case/061（282 汉字）与 /case/605（204 汉字）的开篇概览自洽且点名主体，但显著超出 40–90 词区间，按字面口径判不达标——这两页失分在长度，不在内容。floor(5 × 2/8) = 1。

**✗ `p3.sourced-statistics` 0/5**

计数口径（供复核）：8 个抽样页正文中的量化断言，复合断言（如「由3天缩短至2小时」）计 1 条；排除定价表的价格与配额单元格（属目录事实）、以及每页重复的页脚 CTA。共 37 条，例如「内置2800+常用第三方API」「支持与27+种主流数据库双向同步」「私有部署版已经过上千家企业核心业务使用验证」「在10万员工级别客户中验证了集群的稳定性」「自主搭建场景应用300+、场景应用数1800+、覆盖用户3.2万、日均访问2.1万、非科技人员占比超70%」「单项目节省费用超12万、预计年节省工时超6036小时」「历史数据迁移准确率达100%」「代理费计算准确率由约85%提升至100%」「节省约40%预算、结项回访内部评分4.8/5」。没有一条给出可链接的来源：案例页数字全部由站方直接陈述，被点名的只有客户与伙伴主体（华夏银行、河南九域博慧方舟、上海龙林信息），无引用链接、无来源文档。最接近达标的是首页证言「抄表员人均工作量由0.8万户/人提升至1.4万户/人」——署名到人与单位（戴建峰，宁波西店供电所 所长），有名但不可链接。两种口径同为 0：floor(5 × 1/37) = 0，floor(5 × 0/37) = 0。另注：「付费企业超 4000 家」只出现在 meta description 与 og:description，正文无此句，故未计入分母。

**✗ `p3.named-author` 0/5**

分母取抽样中的 4 个文章型页面（产品页与定价页本就不需要署名）。观察到的署名：/case/061「内容贡献者：第11服务团」、/case/605「内容贡献者：上海龙林信息科技有限公司」、/solution/230「由 山东中政数海大数据有限公司 提供」、/solution/038 的「由…提供」栏渲染为空字符串。全部是机构名或内部团队编号，不是可识别的自然人；没有任何作者简介、作者页链接或 author 标记。0/4 → floor(5 × 0/4) = 0。

**✗ `p3.natural-questions` 0/5**

8 页的 H1–H3 标题共出现 20 次、去重后 15 个：搭建可投入生产的企业应用 / 梦想中的数字化工具 / 我们的用户 ❤️ 明道云 / 客户评价 / 永不停歇的企业应用动力站 / 自主拥有的零代码企业应用平台 / 智能家居行业的流程自动化与API集成 / 方案简介 / 角色 / 流程 / 智慧消防远程值守平台 / 华夏银行「春芽」引领低代码浪潮：从全民开发到高价值落地，提质降本增效 / 全民开发驱动高价值落地 / 招投标管理从旧系统走向全流程协同 / 基于明道云HAP重构招投标全流程管理。没有一个是问句形式。渲染文本里唯一以「？」结尾的行是案例页底部 CTA「想了解明道云HAP如何助力您的企业？」，不是内容标题。0/8 → floor(5 × 0/8) = 0。需要说明的是：这些标题是干净的中文小节名，并不是关键词堆砌串——本项失分反映的是标题没有对齐用户向助手提问时的措辞，而不是标题写得差。

**✗ `p3.freshness` 0/5**

8 页 grep「dateModified」「datePublished」「<time」命中均为 0，页面上没有任何机器可读的更新时间。新鲜度信号在别处确实存在：sitemap.xml 里 8 个抽样 URL 都有 <lastmod>，且都很新（2026-08-04 至 2026-08-20，相对审计日 2026-09-08 为 19 至 35 天，全部在 180 天内）；/md/*.md 镜像头部也写了「更新于 2026-08-04」。也就是说信息是有的，只是没有落到页面自身的 dateModified 上。本项按字面口径判定：0/8 → floor(5 × 0/8) = 0。

## Brand Authority — 8 / 20

**✗ `p4.knowledge-graph` 0/5**

Wikidata wbsearchentities 以「明道云」查询（language=zh）返回空结果集 {"search":[]}；以「Mingdao」查询（language=en）返回 8 条，全部是宋代年号（Q11088210 Mingdao，仁宗 1032–1033）与历史人物，没有该软件公司的条目。同时 8 个抽样页 grep「sameAs」命中 0 次，Organization 节点的键只有 @id / @type / alternateName / contactPoint / description / logo / name / url，不引用任何权威记录。两个条件（存在权威记录、经 sameAs 引用）都不满足。核查限制：baike.baidu.com/item/明道云 从本审计位置返回 403，无法确认是否存在百度百科词条——但即便存在，站点也没有 sameAs 指向它。

**✓ `p4.third-party-listings` 5/5**

https://www.websoft9.com/apps/mingdao 返回 200、397,518 字节，是 Websoft9（独立第三方自托管应用目录，与站方无控制关系）为「明道云私有部署版」建的目录页：含产品描述正文（「明道云私有部署版镜像，通过容器化技术，将高性能、高弹性和高用户体验的 APaaS 公共云服务封装……」）、截图资源 mingdao-main-lib-websoft9.png 与 mingdao-tables-websoft9.jpg、标签「明道,明道云,APaaS,低代码」，以及指向 mingdao.com 的链接。pass 条件只要求 ≥1 个独立评测或目录站，已满足。核查限制：G2、Capterra、alternativeto、SourceForge、百度百科从本审计位置均返回 403，ProductHunt 403、知乎 403、LinkedIn 429，因此本项只统计到能实际打开的那一个；真实的第三方收录面很可能比这更宽。

**✗ `p4.video-presence` 0/4**

频道存在且有内容，这一半是达标的：首页页脚以 <a href="https://space.bilibili.com/314748279" title="B站"> 直接链出，B 站开放接口 x/web-interface/card?mid=314748279 返回 name「明道云」、fans 13,642、签名「明道云是上海万企明道软件有限公司设计和开发的超级应用平台。」，归属可确认。页脚另有微信公众号、视频号、抖音、小红书（号 3152645850）入口，但都是二维码图片而非可抓取链接。本项失分只因 pass 条件明确要求「linked via sameAs」：全站 sameAs 命中 0 次，Organization 节点上没有这条机器可读的身份边，引擎无法把频道与品牌实体关联起来。另：youtube.com/@mingdao 返回 200、标题「mingdao - YouTube」，但该频道页未见指向 mingdao.com 的信息，无法确认归属，故不作为证据采信。

**✓ `p4.independent-mentions` 3/3**

GitHub 搜索接口 q=明道云 返回 total_count 56，其中多个仓库的归属账号与站方无关：andyleimc-source/hap-auto-maker（17 星，「基于 AI（DeepSeek/Gemini）的明道云HAP应用全生命周期自动化工具」）、Lany-w/mingdaoyun-php-sdk（8 星）、devzwy/mdhelper（3 星）、Websoft9Archive/ansible-mingdao（3 星）、gerardhb/go-mdy、ceasarboy/HAP-APS、MoringstarsH/mingdaoYuque、JianxunOPS/pd-openweb。加上上面 websoft9.com 的目录页，品牌确实在站方不控制的域上被讨论。

**✗ `p4.sameas-resolve` 0/3**

8 个抽样页 grep「sameAs」命中 0 次；Organization 节点未声明任何 sameAs URL，可解析集合为空，没有 URL 可以去请求。口径说明（本报告唯一一处需要判断的地方）：规则 5 把 not_applicable 定义为「本站不存在该页型」，而 sameAs 是站点选择不输出的标记属性、不是页型，因此这里按 failed 计 0 分并留在分母内，而不是剔除。若复核者持另一种口径（空分母 → 剔除），总分会变成 29 / 82、归一化 35%，仍落在 Critical 区间，结论不变。

## Platform Visibility — 2 / 3

**⊘ `p5.search-console` — unobservable**

首页 <head> 未见 google-site-verification meta（同时也未见 msvalidate.01、baidu-site-verification、sogou_site_verification、360-site-verification、shenma-site-verification 等任何验证 meta）。但属性验证同样可以通过 DNS TXT 记录或上传验证文件完成，从站外无法区分「未验证」与「用了别的验证方式」。按规则 5 标 unobservable、从分母剔除 3 分，而不是判 failed。

**⊘ `p5.bing-webmaster` — unobservable**

首页 <head> 未见 msvalidate.01 验证 meta。Bing 的提交与索引状态只存在于站长后台，需要凭据才能读取；从站外拿不到。robots.txt 未拦截 Bingbot（无专属组，落到 User-agent: * ，只禁 /act /aja /adm /app 四个前缀），且用 Bingbot UA 请求首页返回 200 真实页面——但可达不等于已提交并被收录。按规则 5 标 unobservable、剔除 3 分。

**⊘ `p5.multi-engine-cited` — unobservable**

本项要求用 ≥10 条购买意图问题跑 ≥3 个引擎，并观察站点是否被实际引用。这个测试无法通过 curl / fetch 从站外复现——引擎的答案是会话级的、随时间与账号变化，任何「模拟」结果都不构成证据。按规则 5 标 unobservable、剔除 3 分。要补齐这一项，需要人工在 ChatGPT、Perplexity、Claude 里跑一组固定的零代码 / 低代码选型问题（中文受众还应加上豆包、Kimi、文心一言、夸克等），逐条记录是否出现 mingdao.com 的引用。

**✓ `p5.answer-shape-fit` 2/3**

按爬虫默认拿到的 HTML 表示（Accept: text/html）逐页判定。合身 6/8：/hap/feature 与 /hap/pd 是「短标题 + 30–60 字说明」的能力块；/solution/038 与 /solution/230 是「方案简介 + 角色 / 流程 / 数据对象 / 效果」的短条目结构；/case/061 与 /case/605 是「客户挑战 / 解决方案 / 核心效益」下每条 40–80 字的带标签条目——这些形状很容易被摘成一段答案。不合身 2/8：首页正文线性化后是口号碎片（「AI 搭建，对话生成」「数据贯通，集成一体」这类），缺少可直接引用的连续散文；/hap/price 的对比表在纯文本线性化后是列优先的——先出现一整串功能名（工作表总数 / 单个工作表最大行数 / 工作流执行次数……），再出现一整串取值（100个 / 1万行 / 1000次/月……），功能与数值的对应关系在文本层丢失，引擎难以正确回答「专业版工作表总数是多少」。floor(3 × 6/8) = 2。缓解项（已核实，但不改判分）：/、/hap/feature、/hap/price、/hap/pd、/agent、/about 提供 Markdown 镜像，且对原 URL 带 Accept: text/markdown 请求会真的返回 text/markdown——实测 /hap/price 返回 200、text/markdown、3,579 字节，里面是规整的四档价格 Markdown 表格，完全解决了上面的列优先问题。但这是需要主动内容协商的旁路表示，默认抓取拿不到，且只覆盖 6 个页面（对 /case/605 发同样的请求仍返回 text/html）。

**⊘ `p5.non-english-engines` — unobservable**

受众判定（可观察，明确）：<html lang="zh-Hans">，og:locale zh_CN，全站正文中文，JSON-LD contactPoint 的 areaServed 为 CN，客服电话 +86-400-665-6655。因此按规则 6 本项适用。站外能观察到的中文引擎准备度是混合的——正面：sitemap.xml（296 条）与 llms.txt（5,695 字节）均为中文内容且可正常抓取；robots.txt 没有为 Baiduspider、Sogou web spider、YisouSpider 开专属组，它们落到 User-agent: * 一样被放行；Content-Signal 明确 search=yes；JSON-LD 的 Organization 用中文名并带 alternateName「上海万企明道软件有限公司」，对中文实体消歧是有用的。缺口：首页 <head> 未见 baidu-site-verification、sogou_site_verification、360-site-verification、shenma-site-verification 中的任何一个，也未见百度统计（hm.baidu.com）等常见中文站长工具痕迹；robots.txt 里显式列名的 AI 爬虫组全是英文引擎的 UA，没有一个中文引擎 UA。但这些只是「准备度」的旁证，不等于 pass 条件所要求的「已测试」。按规则 5 标 unobservable、剔除 3 分，不判 failed。

## Excluded from the denominator

| Check | Pts | Why |
|---|:-:|---|
| `p2.faqpage` | 3 | 8 个抽样页（外加 /hap/price、/edu/certificate 两页扩查）中没有任何一页按问答组织，问句行数为 0；问答页型在被观察范围内不存在。 |
| `p5.search-console` | 3 | 第三方外部审计，无 Search Console 凭据；DNS/文件验证方式从站外不可区分。 |
| `p5.bing-webmaster` | 3 | 第三方外部审计，无 Bing Webmaster 凭据；提交与收录状态只在后台可见。 |
| `p5.multi-engine-cited` | 3 | 需要人工在 ≥3 个引擎里跑 ≥10 条购买意图问题，站外无法执行，且不做模拟或推测。 |
| `p5.non-english-engines` | 3 | 受众为中文、本项适用，但「是否测试过中文引擎」属站方内部流程，站外观察不到；可观察到的只是准备度信号，已写入该项 evidence。 |

## Auditor's caveats

*Where this audit made a judgement call, or could not verify something.*

- p4.sameas-resolve 是本报告唯一一处需要口径判断的地方：站点声明了 0 个 sameAs，本项分母为空。我按 failed 计 0 分并留在分母内（理由：规则 5 的 not_applicable 定义限于「页型不存在」，sameAs 是标记属性不是页型）。若复核者认为空分母应剔除，结果会变成 29 / 82、归一化 35%，仍是 Critical。
- 「40–90 词」在中文没有权威换算。我自定为 60–160 汉字（按 1.5–1.8 字/词）并写进了 evidence。这个换算直接决定了 /case/061（282 汉字）与 /case/605（204 汉字）的判定——若复核者采用更宽的上限，p3.answer-passages 会从 4/8 达标变成 1 分升到 2 分（floor(5×4/8)=2）。这是全报告对换算口径最敏感的一项。
- p4.third-party-listings 只核实到 1 个可打开的独立目录（websoft9.com/apps/mingdao）。G2、Capterra、alternativeto、SourceForge、百度百科从本审计位置返回 403，ProductHunt 403、知乎 403、LinkedIn 429。所以这一项是「至少一个」的下界证据，真实第三方收录面很可能更宽；同理，百度百科是否存在明道云词条我无法核实（但不影响 p4.knowledge-graph 的判定，因为站点没有任何 sameAs）。
- Wikidata 我只用 wbsearchentities 搜了「明道云」（zh）与「Mingdao」（en）两个词，没有穷举「上海万企明道软件」「Mingdao HAP」等别名。若存在冷门条目我会漏掉——但同样不改判定结果。
- p5.answer-shape-fit 的 6/8 是形状判断而非可自动复现的测量。我给出了每页的判定理由（首页口号碎片化、/hap/price 表格列优先线性化），但不同复核者可能判 5/8 或 7/8，对应 2 分或 3 分。
- p3.sourced-statistics 的「37 条」是按我在 evidence 里写明的口径逐条清点的（复合断言计 1 条、排除定价表配额与页脚 CTA）。换口径分母会变，但分子在两种算法下都是 0 或 1，得分恒为 0。
- 全部观察基于 curl 取回的原始 HTML，没有用真实浏览器渲染。若有内容只在 JS 执行后注入我会漏看（不过本站正文实测已在 SSR HTML 中，SSR 这项是实证通过的）。
- 抽样中的「4 篇文章」是用 /case 与 /solution 页顶替的——该主机的 sitemap 里没有博客板块。站点真正的博客在 blog.mingdao.com 这个独立主机上，不在本次审计目标内。若把该子域纳入目标，p2.article-author、p3.named-author、p3.freshness 三项的读数可能完全不同。
- Search Console、Bing Webmaster、多引擎被引用、中文引擎测试四项共 12 分被剔除，是外部审计的固有上限。站方自审的 observable_max 会更高，两个分数按规则 5 不可直接比较。
- 这是 2026-09-08 的一次点时读数。robots.txt 的 Content-Signal、Markdown 内容协商这类配置随时可能变动，隔一段时间需要重抓。

## Notes

【为什么选这个站】需要一个面向中文受众的真实商业站，来给「非英文引擎」这一项一个真实实例。明道云（上海万企明道软件有限公司）是中文零代码 / 低代码 SaaS，官网全中文、有产品页、定价页、114 个客户案例与 143 个伙伴解决方案，页型齐全，29 项检查里只有 1 项因页型缺席被剔除。选它还有一个具体理由：在候选的十几个中文站里，它是极少数真的做了 /llms.txt 的（同批抓取中，爱范儿、有赞、简道云等站 /llms.txt 返回 404；少数派与智谱返回 200 但是 SPA 通配壳，四个不同路径返回同一份 HTML）。一个基础设施做得比同行更靠前的站，更能把 rubric 里「基础设施」与「内容可引用性」的分离量出来。它不是见润的站，也不是政府站。

【抽样怎么取的，规则 3】审计目标是 www.mingdao.com 这个主机。sitemap.xml 的 296 条 URL 里没有博客 / 新闻这类文章板块（站点的博客在 blog.mingdao.com 这个独立主机上，不在本次目标内，也不在本 sitemap 中）。按规则 3「Where a site has fewer of a type, take what exists and say so」，本次这样取：产品 / 服务页取 3 个——/hap/feature、/hap/price、/hap/pd，它们是 lastmod 最新的一批非索引类产品页（同为 2026-08-15，用 sitemap 的 priority 0.9/0.9/0.8 作为并列时的次序）；文章位 4 个用站内最接近长文的页型（案例与解决方案）顶替，取 /case 与 /solution 里 lastmod 最新的 4 条——/solution/038（2026-08-18）、/case/061（2026-08-14）、/solution/230（2026-08-04）、/case/605（2026-08-04）。/solution 与 /case 的索引页 lastmod 更新（2026-08-20），但它们是聚合入口不是内容页，未纳入。加上首页共 8 条，全部列在 sampled_urls 里。

【这次读数说明什么】AIV 29 / 85，归一化 34%，落在 Critical。这个数字和站点给人的第一印象不一致，值得说清楚：基础设施拿了 14/20——手写的 llms.txt（含 10 个分节、46 条链接、以及一段解释 152 个行业页统一结构的说明）、robots.txt 里的 Content-Signal 声明、.well-known 下的 mcp.json 与 agent-skills 清单、6 个页面的 Markdown 镜像加上 Accept: text/markdown 内容协商、10/10 检索型爬虫可达且拿到完整服务端渲染正文——这些都实测通过，比同批抓取的多数中文站都靠前。失分几乎全部集中在页面层：全站结构化数据只有 Organization + WebSite 两个节点，8 页 grep 下来 sameAs、dateModified、datePublished、speakable、BreadcrumbList、FAQPage、Offer 全部为 0 次命中。于是内容可引用性 1/25、品牌权威 8/20。换句话说，这个站是「让 AI 能进来」做得很好、「让 AI 能把某一段摘出去并归因到实体」几乎没做。最大的单项缺口是内容可引用性 1/25。

【哪些不是缺陷，是取舍】ai.txt 缺席，但站点把同一件事写进了 robots.txt 的 Content-Signal 和 llms.txt 末节；llms-full.txt 缺席，但有 6 个页面的 Markdown 镜像与内容协商这条替代路径；标题不是问句形式，但也不是关键词堆砌串，而是干净的中文小节名。rubric 按字面口径给分，这几处的低分反映的是实现路线不同，不是内容质量差。同样，问答页型不存在只是页型选择，已从分母剔除而非计 0。

【一处观察到的实际冲突】robots.txt 的 Disallow: /act 与 Disallow: /app 是前缀匹配，实际挡住了 sitemap.xml 与 llms.txt 都在推荐的 /activitycenter 和 /appintegration 两个页面。这不影响本次任何一项打分（本项只看检索型 UA 是否被禁），但对站方是可操作的信息。

【复核入口】本报告所有结论都可以用 curl -L 复现：状态码判定一律只看 HTTP code（站点的通用 404 页固定为 1,861 字节，与 llms-full.txt、ai.txt 的响应体一致，可用来交叉验证）；抓取时间 2026-09-08 UTC 08:30–08:50；抓取 UA 包括普通 Chrome UA 与 10 个检索型爬虫 UA，首页在全部 11 种 UA 下返回一致。
