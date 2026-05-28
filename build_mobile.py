#!/usr/bin/env python3
"""
Build a WeChat-compatible mobile quiz app for the antiviral drug question bank.

Usage:
    python3 build_mobile.py --expire 2026-09-01 --max-days 90
    python3 build_mobile.py --expire 2026-09-01 --max-days 90 --mode simple

Modes:
    full   — compressed (smaller, needs iOS 16.4+ / Chrome 80+)
    simple — uncompressed (compatible with ALL browsers incl. WeChat, ~6KB larger)

Distribution:
    Upload the generated HTML to any web host. Share the URL in WeChat.
    Students tap the link → opens in WeChat browser → ready to quiz.
    Can also "Add to Home Screen" in Safari/Chrome for app-like experience.
"""

import argparse
import base64
import datetime
import hashlib
import json
import os
import sys
import zlib

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CSV_PATH = os.path.join(os.path.dirname(__file__), "antiviral.csv")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(__file__), "static", "antiviral_app.html")
DEFAULT_EXPIRE = (datetime.date.today() + datetime.timedelta(days=180)).isoformat()

# ---------------------------------------------------------------------------
# Question bank loader
# ---------------------------------------------------------------------------
def load_questions(path: str) -> list[dict]:
    import csv, io
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        questions = []
        for row in reader:
            questions.append({
                "id": int(row["id"]),
                "q": row["question"].strip(),
                "o": [
                    row["option_a"].strip(),
                    row["option_b"].strip(),
                    row["option_c"].strip(),
                    row["option_d"].strip(),
                    row["option_e"].strip(),
                ],
                "a": row["correct"].strip().upper(),
                "e": row["explanation"].strip(),
                "c": row.get("category", "").strip(),
            })
    return questions

# ---------------------------------------------------------------------------
# Key derivation (must match JS exactly)
# ---------------------------------------------------------------------------
def derive_key(key: str) -> list[int]:
    kh = ""
    for ch in key:
        kh += chr(((ord(ch) * 7 + 13) % 93) + 33)
    return [ord(c) for c in kh]

# ---------------------------------------------------------------------------
# Obfuscation
# ---------------------------------------------------------------------------
def obfuscate_full(data: str, key: str) -> str:
    """Compress + XOR + base64. Smaller but needs DecompressionStream."""
    kb = derive_key(key)
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    compressed = co.compress(data.encode("utf-8")) + co.flush()
    xored = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(compressed))
    return base64.b64encode(xored).decode("ascii")

def obfuscate_simple(data: str, key: str) -> str:
    """XOR + base64 only. No compression. Compatible with ALL browsers."""
    kb = derive_key(key)
    raw = data.encode("utf-8")
    xored = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(raw))
    return base64.b64encode(xored).decode("ascii")

# ---------------------------------------------------------------------------
# JS decode functions
# ---------------------------------------------------------------------------
JS_DECODE_FULL = r"""async function _decode(){
  try{
    var key=__KEY,kh="",kb=[];
    for(var i=0;i<key.length;i++)kh+=String.fromCharCode(((key.charCodeAt(i)*7+13)%93)+33);
    for(var i=0;i<kh.length;i++)kb.push(kh.charCodeAt(i));
    var raw=atob(__ENC),bytes=[];
    for(var i=0;i<raw.length;i++)bytes.push(raw.charCodeAt(i));
    for(var j=0;j<bytes.length;j++)bytes[j]^=kb[j%kb.length];
    var u8=new Uint8Array(bytes);
    var ds=new DecompressionStream("deflate");
    var writer=ds.writable.getWriter();
    writer.write(u8);writer.close();
    var buf=await new Response(ds.readable).arrayBuffer();
    return new TextDecoder("utf-8").decode(buf);
  }catch(e){console.error(e);return"[]";}
}"""

JS_DECODE_SIMPLE = r"""function _decode(){
  try{
    var key=__KEY,kh="",kb=[];
    for(var i=0;i<key.length;i++)kh+=String.fromCharCode(((key.charCodeAt(i)*7+13)%93)+33);
    for(var i=0;i<kh.length;i++)kb.push(kh.charCodeAt(i));
    var raw=atob(__ENC),bytes=new Uint8Array(raw.length);
    for(var i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
    for(var j=0;j<bytes.length;j++)bytes[j]^=kb[j%kb.length];
    return new TextDecoder("utf-8").decode(bytes);
  }catch(e){console.error(e);return"[]";}
}"""

# ---------------------------------------------------------------------------
# Shared HTML template (with placeholders)
# ---------------------------------------------------------------------------
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<!-- iOS PWA -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="抗病毒药题库">
<!-- WeChat -->
<meta name="wechat-enable-text-zoom" content="false">
<meta itemprop="name" content="抗病毒药题库">
<meta itemprop="description" content="药理学第四十四章 · 抗病毒药训练题库">
<!-- Android PWA -->
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#2563eb">
<title>抗病毒药题库</title>
<link rel="manifest" href="data:application/json;base64,MANIFEST_B64">
<link rel="apple-touch-icon" href="data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgcng9IjIwIiBmaWxsPSIjMjU2M2ViIi8+PHRleHQgeD0iNTAiIHk9IjY4IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjUyIj7wn5KKPC90ZXh0Pjwvc3ZnPg==">
<style>
:root{
  --p:#2563eb;--pl:#dbeafe;--s:#16a34a;--sl:#dcfce7;--d:#dc2626;--dl:#fee2e2;
  --bg:#f1f5f9;--card:#fff;--b:#e2e8f0;--t:#1e293b;--tm:#64748b;--r:12px;
  --safe-b:env(safe-area-inset-bottom,0px);
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Microsoft YaHei",sans-serif;
  background:var(--bg);color:var(--t);line-height:1.6;min-height:100vh;
  padding-bottom:calc(80px + var(--safe-b));user-select:none;-webkit-user-select:none;
}
.container{max-width:600px;margin:0 auto;padding:10px}

.splash{
  position:fixed;inset:0;background:var(--bg);z-index:999;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
}
.splash-icon{font-size:2.8rem;margin-bottom:10px}
.splash-title{font-size:1.15rem;font-weight:700;margin-bottom:6px}
.splash-sub{font-size:.78rem;color:var(--tm)}
.splash-loader{width:40px;height:3px;background:var(--b);border-radius:2px;margin-top:14px;overflow:hidden}
.splash-loader-fill{width:40%;height:100%;background:var(--p);border-radius:2px;animation:ld 1.2s ease-in-out infinite}
@keyframes ld{0%{transform:translateX(-100%)}100%{transform:translateX(350%)}}

.expired{
  position:fixed;inset:0;background:var(--bg);z-index:998;
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:24px;
}
.expired-icon{font-size:3.2rem;margin-bottom:14px}
.expired-title{font-size:1.15rem;font-weight:700;color:var(--d);margin-bottom:6px}
.expired-text{font-size:.88rem;color:var(--tm);max-width:300px;line-height:1.6}

.topbar{
  background:var(--card);padding:12px 14px;border-bottom:1px solid var(--b);
  position:sticky;top:0;z-index:100;display:flex;justify-content:space-between;
  align-items:center;gap:8px;
}
.topbar h1{font-size:.95rem;font-weight:700}
.top-stats{display:flex;gap:10px;font-size:.72rem;color:var(--tm)}
.top-stats strong{color:var(--t);font-size:.82rem}

.controls{
  background:var(--card);border-radius:var(--r);padding:8px 12px;margin-bottom:8px;
  display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:.78rem;
}
select,button{
  padding:7px 10px;border:1px solid var(--b);border-radius:8px;font-size:.8rem;
  font-family:inherit;background:var(--card);color:var(--t);cursor:pointer;
  -webkit-appearance:none;
}
.btn-p{background:var(--p);color:#fff;border-color:var(--p);font-weight:600}
.btn-o{border-color:var(--p);color:var(--p)}
.flex1{flex:1}

.card{background:var(--card);border-radius:var(--r);overflow:hidden;margin-bottom:8px}
.card-hd{
  padding:8px 12px;border-bottom:1px solid var(--b);
  display:flex;justify-content:space-between;align-items:center;gap:6px;
}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.7rem;font-weight:600}
.badge-c{background:var(--pl);color:var(--p)}
.badge-n{background:#f1f5f9;color:var(--tm)}

.card-body{padding:16px 12px}
.q-text{font-size:.92rem;font-weight:600;margin-bottom:14px;line-height:1.65}
.options{display:flex;flex-direction:column;gap:6px}
.opt{
  display:flex;align-items:flex-start;gap:8px;padding:11px 12px;
  border:1.5px solid var(--b);border-radius:10px;cursor:pointer;transition:all .1s;
  font-size:.88rem;
}
.opt:active{transform:scale(.98)}
.opt.sel{border-color:var(--p);background:var(--pl)}
.opt.ok{border-color:var(--s);background:var(--sl)}
.opt.no{border-color:var(--d);background:var(--dl)}
.opt.rev{border-color:var(--s);background:var(--sl)}
.opt-dot{
  width:22px;height:22px;border:2px solid #cbd5e1;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:.68rem;flex-shrink:0;color:var(--tm);margin-top:1px;
}
.opt.sel .opt-dot,.opt.ok .opt-dot,.opt.rev .opt-dot{background:var(--p);border-color:var(--p);color:#fff}
.opt.no .opt-dot{background:var(--d);border-color:var(--d);color:#fff}
.opt-txt{flex:1;padding-top:1px}
.locked .opt{pointer-events:none}

.expl{
  margin-top:12px;padding:11px 12px;border-radius:10px;
  background:#fffbeb;border:1px solid #fde68a;font-size:.82rem;line-height:1.55;display:none;
}
.expl.on{display:block}
.expl-title{font-weight:700;margin-bottom:2px;color:#92400e}

.btm-bar{
  position:fixed;bottom:0;left:0;right:0;background:var(--card);
  border-top:1px solid var(--b);padding:8px 12px calc(8px + var(--safe-b));
  display:flex;gap:8px;align-items:center;z-index:100;
}
.btm-bar .counter{font-size:.76rem;color:var(--tm);min-width:55px;text-align:center}
.btm-btn{
  flex:1;text-align:center;padding:10px;border-radius:8px;font-weight:600;font-size:.8rem;
  border:1px solid var(--b);background:var(--card);color:var(--t);cursor:pointer;
}
.btm-btn:disabled{opacity:.35}
.btm-btn.primary{background:var(--p);color:#fff;border-color:var(--p)}
.btm-btn.danger{background:var(--d);color:#fff;border-color:var(--d)}

.dot-nav{
  display:flex;gap:2px;flex-wrap:wrap;padding:6px 12px 12px;
  border-top:1px solid var(--b);max-height:110px;overflow-y:auto;
}
.dot{
  width:23px;height:23px;border-radius:4px;border:1px solid var(--b);
  background:#fff;font-size:.6rem;font-family:inherit;cursor:pointer;
  display:inline-flex;align-items:center;justify-content:center;color:var(--tm);flex-shrink:0;
}
.dot.cur{background:var(--p);color:#fff;border-color:var(--p);font-weight:700}
.dot.good{background:var(--sl);border-color:var(--s);color:var(--s)}
.dot.bad{background:var(--dl);border-color:var(--d);color:var(--d)}

.stats{background:var(--card);border-radius:var(--r);padding:14px;margin-bottom:8px}
.stats h3{font-size:.82rem;margin-bottom:8px}
.stats-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;text-align:center}
.st-item{padding:8px;background:var(--bg);border-radius:8px}
.st-val{font-size:1.15rem;font-weight:700;color:var(--p)}
.st-label{font-size:.66rem;color:var(--tm);margin-top:1px}

.toast{
  position:fixed;top:14px;left:50%;transform:translateX(-50%);
  padding:9px 16px;border-radius:8px;font-size:.8rem;font-weight:600;
  z-index:999;box-shadow:0 4px 12px rgba(0,0,0,.15);animation:ti .25s;
}
.toast-e{background:#fee2e2;color:#991b1b}
.toast-o{background:#dcfce7;color:#166534}
@keyframes ti{from{opacity:0;transform:translateX(-50%) translateY(-6px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}

@media(min-width:600px){
  .container{padding:14px}.card-body{padding:22px 18px}.q-text{font-size:1rem}
}
.dot-nav::-webkit-scrollbar{display:none}
</style>
</head>
<body>

<div class="splash" id="splash">
  <div class="splash-icon">💊</div>
  <div class="splash-title">抗病毒药 · 题库训练</div>
  <div class="splash-sub">药理学第四十四章</div>
  <div class="splash-loader"><div class="splash-loader-fill"></div></div>
</div>

<div id="expiredView" class="expired" style="display:none">
  <div class="expired-icon">⏰</div>
  <div class="expired-title">应用已过期</div>
  <div class="expired-text" id="expiredMsg"></div>
</div>

<div class="container" id="app" style="display:none;padding-bottom:80px">

  <div class="topbar">
    <h1>抗病毒药题库</h1>
    <div class="top-stats">
      <span>已答<strong id="hAns">0</strong>/<span id="hTot">100</span></span>
      <span>正确<strong id="hCor">0</strong></span>
      <span><strong id="hPct">-</strong></span>
    </div>
  </div>

  <div class="controls">
    <select id="catSel" onchange="applyFilter()"><option value="all">全部</option></select>
    <select id="modeSel" onchange="applyFilter()">
      <option value="all">顺序</option><option value="rnd">随机</option>
      <option value="wrong">错题</option><option value="unans">未答</option>
    </select>
    <div class="flex1"></div>
    <button class="btn-o" onclick="resetAll()">重置</button>
  </div>

  <div class="card">
    <div class="card-hd">
      <span class="badge badge-c" id="qCat">-</span>
      <span class="badge badge-n" id="qNum">-</span>
    </div>
    <div class="card-body" id="qBody">
      <div class="q-text" id="qText"></div>
      <div class="options" id="qOpts"></div>
      <div class="expl" id="qExpl">
        <div class="expl-title">解析</div>
        <div id="qExplText"></div>
      </div>
    </div>
    <div class="dot-nav" id="dotNav"></div>
  </div>

  <div class="stats">
    <h3>学习统计</h3>
    <div class="stats-grid">
      <div class="st-item"><div class="st-val" id="stAns">0</div><div class="st-label">已答</div></div>
      <div class="st-item"><div class="st-val" id="stCor">0</div><div class="st-label">正确</div></div>
      <div class="st-item"><div class="st-val" id="stPct">-</div><div class="st-label">正确率</div></div>
    </div>
  </div>
</div>

<div class="btm-bar" id="btmBar" style="display:none">
  <button class="btm-btn" id="btnPrev" onclick="prevQ()" disabled>◀</button>
  <span class="counter" id="navInfo">1/100</span>
  <button class="btm-btn" id="btnNext" onclick="nextQ()">▶</button>
  <button class="btm-btn danger" id="btnReveal" onclick="reveal()">显示答案</button>
</div>

<script>
// ===== EXPIRY CONFIG =====
var __EXP={date:"EXPIRY_DATE",sig:"EXPIRY_SIG",maxDays:MAX_DAYS,build:"BUILD_ID"};

// ===== INTEGRITY & EXPIRY CHECK =====
(function(){
  // Verify integrity
  var raw=__EXP.date+":"+__EXP.maxDays+":"+__EXP.build,h=0;
  for(var i=0;i<raw.length;i++)h=((h*31)+raw.charCodeAt(i))>>>0;
  h=((h>>>16)^(h&0xFFFF)).toString(16);
  if(h.length<4)h="0".repeat(4-h.length)+h;
  if(h!=="EXPIRY_HASH"){
    document.body.innerHTML='<div style="padding:40px;text-align:center;color:#dc2626;font-size:1.1rem">应用校验失败。请从老师处重新获取。</div>';
    throw new Error("integrity");
  }

  var expireDate=new Date(__EXP.date+"T23:59:59");
  var now=new Date();
  var firstUse=localStorage.getItem("_av_fu");
  var lastUse=localStorage.getItem("_av_lu");

  if(!firstUse){
    firstUse=now.toISOString();
    try{localStorage.setItem("_av_fu",firstUse)}catch(e){}
  }else{
    var fu=new Date(firstUse);
    if(now<fu){
      document.getElementById("expiredView").style.display="flex";
      document.getElementById("expiredMsg").textContent="检测到系统时间异常。请将手机设置为自动时间后重试。";
      return;
    }
    if(__EXP.maxDays>0){
      var maxEnd=new Date(fu);
      maxEnd.setDate(maxEnd.getDate()+__EXP.maxDays);
      if(now>maxEnd){
        document.getElementById("expiredView").style.display="flex";
        document.getElementById("expiredMsg").textContent="本应用自首次使用起"+__EXP.maxDays+"天内有效，已到期。请联系老师获取新版本。";
        return;
      }
    }
  }
  try{localStorage.setItem("_av_lu",now.toISOString())}catch(e){}

  if(now>expireDate){
    document.getElementById("expiredView").style.display="flex";
    document.getElementById("expiredMsg").textContent="本应用有效期至 "+expireDate.toLocaleDateString("zh-CN")+"，已到期。";
    return;
  }
  window._avReady=true;
})();

// ===== QUESTION BANK =====
var __ENC="ENCODED_QUESTIONS";
var __KEY="EXPIRY_DATE";

DECODE_FUNCTION

// ===== STATE =====
var QS=[],currentIdx=0,answers={},correctMap={},explanations={},LS="_av_qz_v3";

function _s(){try{localStorage.setItem(LS,JSON.stringify({a:answers,c:correctMap,e:explanations}))}catch(e){}}
function _l(){try{var d=JSON.parse(localStorage.getItem(LS)||"{}");answers=d.a||{};correctMap=d.c||{};explanations=d.e||{};}catch(e){}}

// ===== INIT =====
DECODE_CALL

// ===== RENDER =====
function render(){
  if(!QS.length)return;
  var q=QS[currentIdx],idx=currentIdx;
  document.getElementById("qCat").textContent=q.c||"综合";
  document.getElementById("qNum").textContent=(idx+1)+"/"+QS.length;
  document.getElementById("qText").textContent=q.q;

  var labels=["A","B","C","D","E"],answered=answers[q.id]!==undefined,ua=answers[q.id],ca=correctMap[q.id];
  var html="";
  q.o.forEach(function(opt,i){
    var lbl=labels[i],cls="opt";
    if(answered&&ca){
      if(lbl===ca)cls+=" rev";
      else if(lbl===ua&&ua!==ca&&ua!=="__SKIP__")cls+=" no";
    }
    html+='<div class="'+cls+'"'+(answered?'':' onclick="answer(\''+lbl+'\')"')+'>';
    html+='<span class="opt-dot">'+lbl+'</span>';
    html+='<span class="opt-txt">'+_esc(opt)+'</span>';
    html+='</div>';
  });
  document.getElementById("qOpts").innerHTML=html;

  var body=document.getElementById("qBody");
  if(answered)body.classList.add("locked");else body.classList.remove("locked");

  var explDiv=document.getElementById("qExpl");
  if(answered&&explanations[q.id]){
    explDiv.classList.add("on");
    document.getElementById("qExplText").textContent=explanations[q.id];
  }else{explDiv.classList.remove("on")}

  document.getElementById("btnPrev").disabled=idx===0;
  document.getElementById("btnNext").disabled=idx>=QS.length-1;
  document.getElementById("btnReveal").style.display=answered?"none":"";
  document.getElementById("navInfo").textContent=(idx+1)+"/"+QS.length;

  drawDots();updateStats();
}

function answer(label){
  var q=QS[currentIdx];
  if(!q||answers[q.id]!==undefined)return;
  answers[q.id]=label;correctMap[q.id]=q.a;explanations[q.id]=q.e;
  _s();render();
}

function reveal(){
  var q=QS[currentIdx];if(!q)return;
  correctMap[q.id]=q.a;explanations[q.id]=q.e;
  if(answers[q.id]===undefined)answers[q.id]="__SKIP__";
  _s();render();
}

function prevQ(){if(currentIdx>0){currentIdx--;render()}}
function nextQ(){if(currentIdx<QS.length-1){currentIdx++;render()}}

function drawDots(){
  var html="";
  for(var i=0;i<QS.length;i++){
    var cls="dot";if(i===currentIdx)cls+=" cur";
    var q=QS[i];
    if(answers[q.id]&&answers[q.id]!=="__SKIP__")cls+=answers[q.id]===correctMap[q.id]?" good":" bad";
    html+='<button class="'+cls+'" onclick="jump('+i+')">'+(i+1)+'</button>';
  }
  document.getElementById("dotNav").innerHTML=html;
}

function jump(i){currentIdx=i;render()}

function updateStats(){
  var an=0,cn=0;
  QS.forEach(function(q){
    if(answers[q.id]&&answers[q.id]!=="__SKIP__"){an++;if(answers[q.id]===correctMap[q.id])cn++;}
  });
  var pct=an>0?Math.round(cn/an*100):0;
  document.getElementById("hAns").textContent=an;document.getElementById("hCor").textContent=cn;
  document.getElementById("hPct").textContent=an>0?pct+"%":"-";
  document.getElementById("stAns").textContent=an;document.getElementById("stCor").textContent=cn;
  document.getElementById("stPct").textContent=an>0?pct+"%":"-";
}

function applyFilter(){
  var mode=document.getElementById("modeSel").value,cat=document.getElementById("catSel").value;
  var pool=QS.slice();
  if(cat!=="all")pool=pool.filter(function(q){return q.c===cat});
  if(mode==="wrong"){
    var w=pool.filter(function(q){return answers[q.id]&&answers[q.id]!=="__SKIP__"&&answers[q.id]!==correctMap[q.id]});
    if(w.length===0){_toast("暂无错题！","o");document.getElementById("modeSel").value="all";return}
    currentIdx=QS.indexOf(w[0]);
  }else if(mode==="rnd"){currentIdx=QS.indexOf(pool[Math.floor(Math.random()*pool.length)])}
  else if(mode==="unans"){
    var u=pool.filter(function(q){return!answers[q.id]});
    if(u.length===0){_toast("全部答完！","o");document.getElementById("modeSel").value="all";return}
    currentIdx=QS.indexOf(u[0]);
  }
  render();
}

function resetAll(){
  if(!confirm("确定重置所有答题进度？"))return;
  answers={};correctMap={};explanations={};_s();currentIdx=0;
  document.getElementById("modeSel").value="all";render();
}

function _esc(s){return(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}
function _toast(m,t){
  var el=document.createElement("div");el.className="toast toast-"+(t==="e"?"e":"o");
  el.textContent=m;document.body.appendChild(el);setTimeout(function(){el.remove()},2000);
}

// Keyboard
document.addEventListener("keydown",function(e){
  var q=QS[currentIdx];if(!q)return;
  if(!answers[q.id]){var m={49:"A",50:"B",51:"C",52:"D",53:"E"},k=e.key.toUpperCase(),lbl=m[e.keyCode]||(["A","B","C","D","E"].indexOf(k)>=0?k:null);if(lbl)answer(lbl)}
  if(e.key==="ArrowLeft")prevQ();if(e.key==="ArrowRight")nextQ();
});

// Swipe
var _sx=0;
document.addEventListener("touchstart",function(e){_sx=e.touches[0].clientX},{passive:true});
document.addEventListener("touchend",function(e){
  var dx=e.changedTouches[0].clientX-_sx;
  if(Math.abs(dx)>70){if(dx<0)nextQ();else prevQ()}
});
</script>
</body>
</html>"""

# ===== WeChat-optimized init variants =====
INIT_FULL = """async function init(){
  if(!window._avReady)return;_l();
  try{var raw=await _decode();QS=JSON.parse(raw)}catch(e){document.getElementById("splash").innerHTML='<p style="color:#dc2626">题库加载失败，请重新下载。</p>';return}
  document.getElementById("hTot").textContent=QS.length;
  var cats={};QS.forEach(function(q){cats[q.c]=(cats[q.c]||0)+1});
  var sel=document.getElementById("catSel");sel.innerHTML='<option value="all">全部 ('+QS.length+'题)</option>';
  Object.keys(cats).sort().forEach(function(c){sel.innerHTML+='<option value="'+_esc(c)+'">'+_esc(c)+' ('+cats[c]+')</option>'});
  document.getElementById("splash").style.display="none";
  document.getElementById("app").style.display="block";
  document.getElementById("btmBar").style.display="flex";render();
}"""

INIT_SIMPLE = """function init(){
  if(!window._avReady)return;_l();
  try{var raw=_decode();QS=JSON.parse(raw)}catch(e){document.getElementById("splash").innerHTML='<p style="color:#dc2626">题库加载失败。</p>';return}
  document.getElementById("hTot").textContent=QS.length;
  var cats={};QS.forEach(function(q){cats[q.c]=(cats[q.c]||0)+1});
  var sel=document.getElementById("catSel");sel.innerHTML='<option value="all">全部 ('+QS.length+'题)</option>';
  Object.keys(cats).sort().forEach(function(c){sel.innerHTML+='<option value="'+_esc(c)+'">'+_esc(c)+' ('+cats[c]+')</option>'});
  document.getElementById("splash").style.display="none";
  document.getElementById("app").style.display="block";
  document.getElementById("btmBar").style.display="flex";render();
}
init();"""

# ===== Manifest =====
MANIFEST = {
    "name": "抗病毒药题库",
    "short_name": "抗病毒药",
    "start_url": ".",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#f1f5f9",
    "theme_color": "#2563eb",
}

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(expire_date: str, max_days: int = 0, output: str = DEFAULT_OUTPUT, mode: str = "full"):
    questions = load_questions(CSV_PATH)
    print(f"[build] {len(questions)} questions loaded")

    if max_days <= 0:
        max_days = 0

    build_id = datetime.datetime.now().strftime("%Y%m%d%H%M")

    # Encode questions
    questions_json = json.dumps(questions, ensure_ascii=False, separators=(",", ":"))
    if mode == "simple":
        encoded = obfuscate_simple(questions_json, expire_date)
        decode_fn = JS_DECODE_SIMPLE
        init_code = INIT_SIMPLE
    else:
        encoded = obfuscate_full(questions_json, expire_date)
        decode_fn = JS_DECODE_FULL
        init_code = INIT_FULL

    # Integrity hash
    raw = f"{expire_date}:{max_days}:{build_id}"
    h = 0
    for ch in raw:
        h = ((h * 31) + ord(ch)) & 0xFFFFFFFF
    h = ((h >> 16) ^ (h & 0xFFFF))
    expiry_hash = f"{h:04x}"

    # Manifest
    manifest_b64 = base64.b64encode(json.dumps(MANIFEST).encode()).decode()

    # Assemble
    html = HTML_TEMPLATE
    html = html.replace("MANIFEST_B64", manifest_b64)
    html = html.replace("EXPIRY_DATE", expire_date)
    html = html.replace("EXPIRY_SIG", "na")
    html = html.replace("MAX_DAYS", str(max_days))
    html = html.replace("BUILD_ID", build_id)
    html = html.replace("EXPIRY_HASH", expiry_hash)
    html = html.replace("ENCODED_QUESTIONS", encoded)
    html = html.replace("DECODE_FUNCTION", decode_fn)
    html = html.replace("DECODE_CALL", init_code)

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(output) / 1024
    print(f"[build] Output: {output}  ({size_kb:.0f} KB)")
    print(f"[build] Mode: {mode}")
    print(f"[build] Expiry: {expire_date}" + (f" + {max_days}d from first use" if max_days > 0 else ""))
    print(f"[build] ✓ Ready — upload to any web host and share the URL in WeChat")

    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build WeChat-compatible quiz app")
    parser.add_argument("--expire", default=DEFAULT_EXPIRE, help="Expiry date YYYY-MM-DD")
    parser.add_argument("--max-days", type=int, default=90, help="Max days from first use (default: 90)")
    parser.add_argument("--mode", choices=["full", "simple"], default="simple",
                        help="'simple' = all browsers incl. WeChat; 'full' = compressed, needs modern browser")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output HTML file")
    args = parser.parse_args()

    try:
        datetime.date.fromisoformat(args.expire)
    except ValueError:
        print(f"ERROR: Invalid date '{args.expire}'. Use YYYY-MM-DD.")
        sys.exit(1)

    build(args.expire, args.max_days, args.output, args.mode)
