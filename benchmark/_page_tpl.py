TPL = '''<!doctype html>
<html lang="%(htmllang)s"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(t_title)s</title>
<meta name="description" content="%(t_desc)s">
<meta property="og:title" content="%(t_ogtitle)s">
<meta property="og:description" content="%(t_ogdesc)s">
<meta property="og:type" content="website">
<link rel="alternate" hreflang="en" href="https://jianruntech.github.io/geo-score/">
<link rel="alternate" hreflang="zh" href="https://jianruntech.github.io/geo-score/zh.html">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>%(css)s</style></head><body>
<nav class="langs"><a href="./" class="%(on_en)s">EN</a><a href="./zh.html" class="%(on_zh)s">中文</a></nav>
<div class="wrap">

<header>
<p class="eyebrow">JIANRUNTECH / GEO-SCORE</p>
<h1>%(t_h1)s</h1>
<p class="sub">%(t_sub)s</p>
<div class="stats">
<div class="stat"><b>%(n)d</b><span>%(l_sites)s</span></div>
<div class="stat"><b>%(med)s</b><span>%(l_median)s</span></div>
<div class="stat"><b>%(p75)s</b><span>%(l_uq)s</span></div>
<div class="stat"><b>%(mn)d&ndash;%(mx)d</b><span>%(l_range)s</span></div>
<div class="stat"><b>%(cap)d</b><span>%(l_cap)s</span></div>
</div>
</header>

<h2>%(t_h2gate)s</h2>
<p>%(t_pgate)s</p>

<div class="two">
<div><h3>%(l_delib)s &mdash; %(nblk)d</h3><p>%(t_delib)s<br><br><code class="list">%(blk)s</code></p></div>
<div><h3>%(l_accid)s &mdash; %(njs)d</h3><p>%(t_accid)s<br><br><code class="list">%(js)s</code></p></div>
</div>

<div class="finding">%(t_china)s</div>

<h2>%(t_h2dist)s</h2>
<p>%(t_pdist)s</p>
<div class="hist">%(hist)s</div>
<div class="histx">%(histx)s</div>

<h2>%(t_h2check)s</h2>
<p>%(t_pcheck)s</p>
<pre>curl -sL https://raw.githubusercontent.com/jianruntech/geo-score/main/cli/geo_score.py \\
  | python3 - <b>yoursite.com</b></pre>
<p style="color:var(--dim);font-size:13.5px">%(t_flags)s</p>

<h2>%(t_h2all)s</h2>
<p>%(t_pall)s</p>
<div class="toolbar">
<input id="q" type="search" placeholder="%(l_search)s" autocomplete="off">
<select id="sec"><option value="">%(l_allsec)s</option>%(secopts)s</select>
<select id="fil"><option value="">%(l_allsites)s</option><option value="cap">%(l_fcap)s</option><option value="top">%(l_ftop)s</option><option value="low">%(l_flow)s</option></select>
</div>
<div class="tw"><table id="t"><thead><tr>
<th data-k="s">%(l_site)s</th><th data-k="n" class="num">%(l_score)s</th><th></th>
<th data-k="b">%(l_band)s</th><th data-k="k">%(l_sector)s</th><th>%(l_gaps)s</th>
</tr></thead><tbody id="tb"></tbody></table></div>
<p id="count" style="color:var(--dim);font-size:12.5px"></p>

<h2>%(t_h2sec)s</h2>
<div class="tw"><table><thead><tr><th>%(l_sector)s</th><th class="num">%(l_sites)s</th><th class="num">%(l_median)s</th><th></th></tr></thead><tbody>%(sectbl)s</tbody></table></div>

<footer>%(t_footer)s</footer>
</div>
<script>
const D=%(data)s;
const BAND=%(bandmap)s;
const bandCol=%(bandcol)s;
let sortK="n",sortD=-1;
const tb=document.getElementById("tb"),q=document.getElementById("q"),sec=document.getElementById("sec"),fil=document.getElementById("fil"),cnt=document.getElementById("count");
const CNT=%(l_count)s;
function rows(){
  const t=q.value.trim().toLowerCase(),sv=sec.value,fv=fil.value;
  let r=D.filter(d=>(!t||d.s.toLowerCase().includes(t)||d.k.toLowerCase().includes(t))&&(!sv||d.k===sv)
    &&(!fv||(fv==="cap"?d.c:fv==="top"?d.n>=66:d.n!==null&&d.n<50)));
  r.sort((a,b)=>{const x=a[sortK],y=b[sortK];
    if(x===null)return 1; if(y===null)return -1;
    return (typeof x==="number"?x-y:String(x).localeCompare(String(y)))*sortD;});
  return r;
}
function draw(){
  const r=rows();
  tb.innerHTML=r.map(d=>{
    const w=d.n===null?0:d.n, cls=w>=66?"hi":w<40?"lo":"";
    return `<tr><td>${d.s}${d.c?' <span class="pill">%(l_pill)s</span>':''}</td>`+
      `<td class="num" style="color:${bandCol[d.b]}">${d.n===null?"\\u2014":d.n}</td>`+
      `<td class="bar"><i class="${cls}" style="width:${w}%%"></i></td>`+
      `<td class="band" style="color:${bandCol[d.b]}">${BAND[d.b]||d.b}</td>`+
      `<td class="sect">${d.k}</td>`+
      `<td class="gaps">${d.n===null?(d.w||"").slice(0,60):d.g.join(" \\u00b7 ")}</td></tr>`;
  }).join("");
  cnt.textContent=CNT.replace("{a}",r.length).replace("{b}",D.length);
}
document.querySelectorAll("th[data-k]").forEach(th=>th.onclick=()=>{
  const k=th.dataset.k; sortD=(k===sortK)?-sortD:(k==="n"?-1:1); sortK=k; draw();});
[q,sec,fil].forEach(el=>el.oninput=draw);
draw();
</script></body></html>
'''
