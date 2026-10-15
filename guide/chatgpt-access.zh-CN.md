# ChatGPT 能不能读到你的网站？分两半检查

前一半手工做，用浏览器和终端，不需要我们的任何东西；后一半用 geo-score 把同样的检查再跑一遍，外加几项。
读得到是被引用的前提，不是被引用的保证。
English: [chatgpt-access.md](chatgpt-access.md)

## 哪几个爬虫说了算

ChatGPT 通过两个爬虫访问网站（[reference/ai-crawlers.md](../reference/ai-crawlers.md)）：

| User-agent | 做什么 |
|---|---|
| `OAI-SearchBot` | 建 ChatGPT 搜索背后的索引。OpenAI 说，页面要对它开放，才能在那里被摘要、引用和链接（[Publishers and developers FAQ](https://help.openai.com/en/articles/12627856-publishers-and-developers-faq)） |
| `ChatGPT-User` | 用户的提问需要时，实时抓取一个页面 |

`GPTBot` 是 OpenAI 的训练爬虫。OpenAI 写明各项设置互相独立，所以一个站可以拒绝 `GPTBot`，仍然出现在 ChatGPT 搜索里。
本页说的是上面两个。

## 前一半 · 手工

**1. 读 robots.txt。** 在浏览器里打开 `https://你的域名/robots.txt`。找点名 `OAI-SearchBot` 或 `ChatGPT-User` 的那一组
（`User-agent:` 行）。有的话，只有那一组对它生效；没有的话，`User-agent: *` 那一组生效。生效的那一组里如果有 `Disallow: /`，
这个爬虫就被挡在整个站外。针对某个路径的 `Disallow` 只关掉那个路径，所以要看你在意的那些路径。

**2. 分别以两个爬虫和浏览器的身份请求一个页面。** 下面的 user-agent 字符串是厂商公布的，也是 geo-score 发的。

```bash
URL=https://www.example.com/
SEARCH='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36; compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot'
USER='Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot'
BROWSER='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'
for ua in "$SEARCH" "$USER" "$BROWSER"; do
  curl -s -L -o /dev/null -w '%{http_code} %{size_download} bytes\n' -A "$ua" "$URL"
done
```

三行都是 `200`、大小相近，就是想要的结果。爬虫拿到 `403`、`429`，或者比浏览器小得多的回答，说明它们和你的页面之间有东西在区别对待。

这些请求来自你自己的地址，不是厂商公布的地址。按 IP 段核验爬虫的防火墙，可能拒绝你的请求、却放行真正的爬虫，反过来也可能；
被拒绝应读作「这台服务器拒绝未经核验的爬虫 user-agent」，不是铁证。

**3. 看正文在不在 HTML 里。** 检索爬虫一般读服务器发来的 HTML，不执行其中的 JavaScript。在浏览器里挑一句页面上看得到的话，
到爬虫拿到的内容里找：

```bash
curl -s -L -A "$SEARCH" "$URL" | grep -c '页面上看得到的一句话'
```

结果是 `0`，说明这句话要等 JavaScript 跑完才出现，爬虫拿到的是一个空壳。

**4. 看网站前面那一层。** 在 CDN 或主机的机器人和防火墙设置里，确认没有规则拦截或质询 `OAI-SearchBot`、`ChatGPT-User`，
再到日志里看它们的请求和拿到的状态码。按组拦「AI 机器人」的开关，通常也会拦到它们。

**5. 看结果。** 服务器日志能看出 `OAI-SearchBot` 有没有来抓页面。分析工具里能看到从 ChatGPT 搜索来的访问：
OpenAI 说它发出的链接带 `utm_source=chatgpt.com`。直接问 ChatGPT 你的某个页面，看到的是某一天的一个回答；
每次回答都不一样，一个回答只是个例。

## 后一半 · 用 geo-score

按[几种跑法](../README.zh-CN.md#几种跑法)安装，然后：

```bash
geo-score www.example.com --explain
```

三个门槛项一次替全部 10 个检索爬虫（包括上面两个）回答第 1 到第 3 步：

| 检查项 | 读什么 |
|---|---|
| `g.robots` | robots.txt，按 RFC 9309 为每个爬虫选出生效的那一组 |
| `g.reachable` | 以每个爬虫和浏览器的身份请求抽样页，逐一比较 |
| `g.ssr` | 主要内容在不在服务器渲染的 HTML 里 |

报告的**分数之外**一栏还会把每个抽样页按路径和 robots.txt 对一遍（[cli/README.zh-CN.md](../cli/README.zh-CN.md#分数之外)）。
`--explain` 打印每个读数背后的证据，[排查指南](troubleshooting.zh-CN.md)解释每一种读数。在 CI 里，`--fail-on-gate`
让任一门槛项为 0 时构建失败。

ChatGPT 之后会不会引用你，是另一个问题。第二级用你自己的 Key 通过 API 去问：

```bash
OPENAI_API_KEY=… geo-score www.example.com --ask "你的买家会问的一个问题"
```

那是 API 渠道，不是 ChatGPT 应用；一个回答仍然只是个例。第三级（`watch`）每周问一组固定的问题，报告带置信区间的比例；
见 [watch 方法说明](watch-methodology.zh-CN.md)。
