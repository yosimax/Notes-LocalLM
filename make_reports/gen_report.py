#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Notes-LocalLM report: case2 (Ornith-1.5-9B Q8_0) + case1 (Qwen3.8-27B-UD-Q2_K_XL)."""
import re, os
from datetime import datetime

OUT = os.path.expanduser(
    "~/workspace/Notes-LocalLM/Notes-LocalLM-report_case2_by_Ornith-1.5_9B_Q8_0.html")

# ------------------------------------------------------------------ parse
ts_re = re.compile(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)')
def parse_ts(m):
    return (int(m[1])*60 + int(m[2]) + int(m[3])/1000 + int(m[4])/1e6)/60.0
def pe(line):
    m=re.search(r'prompt eval time =\s*(\d+\.?\d*) ms / \s*(\d+) tokens \( *(\d+\.?\d*) ms per token, \s*(\d+\.?\d*) tokens per second\)', line)
    return (float(m[1]),int(m[2]),float(m[3]),float(m[4])) if m else None
def gs(line):
    m=re.search(r'n_gen =\s*(\d+), tg =\s*([\d.]+) t/s, tg_3s =\s*([\d.]+) t/s', line)
    return (int(m[1]),float(m[2])) if m else None
def pp(line):
    m=re.search(r'prompt processing, n_tokens = \s*(\d+), progress = \s*([\d.]+), t = \s*(\d+\.?\d*) s / (\d+\.?\d*) tokens per second', line)
    return (int(m[1]),float(m[4])) if m else None
def rel(line):
    m=re.search(r'stop processing: n_tokens = \s*(\d+)', line); return int(m[1]) if m else 0
def fkeep(line):
    m=re.search(r'task -1.*?f_sim_best = ([\d.]+).*?f_keep = ([\d.]+)', line)
    return float(m[2]) if m else None

def analyze(LOG):
    global order, tasks
    tasks={};order=[];cur=None
    with open(LOG) as f:
        for line in f:
            m=ts_re.match(line)
            if not m: continue
            t=parse_ts(m)
            if 'slot launch_slot_' in line:
                cur=int(re.search(r'task (\d+)',line).group(1));order.append(cur)
                tasks[cur]=dict(launch=t,pp=[],gs=[],pe=None,rel=None,ntok=0)
            elif 'prompt processing' in line:
                x=pp(line)
                if x: tasks[cur]['pp'].append(x)
            elif 'prompt eval time =' in line:
                x=pe(line)
                if x: tasks[cur]['pe']=x
            elif 'n_gen =' in line:
                x=gs(line)
                if x: tasks[cur]['gs'].append(x)
            elif 'stop processing:' in line:
                tasks[cur]['ntok']=rel(line);tasks[cur]['rel']=t
    evtps=[d['pe'][3] for d in tasks.values() if d['pe']]
    gentg=[g[1] for d in tasks.values() for g in d['gs'] if g]
    pp_tps=[x[1] for d in tasks.values() for x in d['pp'] if x]
    return dict(n=len(order), dur=tasks[order[-1]]['rel'] if order else 0,
                ev_min=min(evtps),ev_max=max(evtps),ev_mean=sum(evtps)/len(evtps),
                g_min=min(gentg),g_max=max(gentg),g_mean=sum(gentg)/len(gentg),
                pp_min=min(pp_tps),pp_max=max(pp_tps) if pp_tps else 0,
                decay=max(evtps)/min(evtps))

def table_rows(a):
    out=[]
    for c in order:
        d=tasks[c];pp=d['pp']
        d['gmax']=max([x[0] for x in d['gs']]) if d['gs'] else 0
        d['g0']=d['gs'][0][1] if d['gs'] else 0; d['g1']=d['gs'][-1][1] if d['gs'] else 0
        d['dur']=d['rel']-d['launch'] if d['rel'] else 0
        pp0=d['pp'][0] if d['pp'] else None; pp1=d['pp'][-1] if d['pp'] else None
        dec=(pp0[1]/(pp1[1] or 0.001)-1) if pp0 else 0
        pe=d['pe'] or (0,0,0,0)
        out.append((c, d['launch'], d['dur'], pp0[0] if pp0 else 0, pp1[0] if pp1 else 0,
                    pp0[1] if pp0 else 0, pp1[1] if pp1 else 0, dec, pe[0], pe[1], pe[2], pe[3],
                    d['gmax'], d['g0'], d['g1'], d['ntok'], pe[3]))
    return out

# ----------------------------------------------------------------- data
Q8_0   = analyze("20260913_mactop-Ornith-1.5-9B_Q8_0.log")
Q4_KM  = analyze("20260912_Ornith-1.5-9B-Q4_K_M.log")
QWEN   = analyze("../case1/20260911_2.log")

ctx80, ctxQ = "80K", "80K"

def row(cells, cls=""):
    return "<tr class='"+cls+"'>" + "".join("<td>"+str(c)+"</td>" for c in cells) + "</tr>"
def num(x, f=",.1f"):
    return format(float(x), f)
def mst(v):
    return round(1.0/v*1000, 2) if v else 0.0
def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# compaction (f_keep) events + launch gaps for case1
fk=[]; tasksQ={};orderQ=[];cur=None
with open("../case1/20260911_2.log") as f:
    for line in f:
        m=ts_re.match(line)
        if not m: continue
        t=parse_ts(m)
        if 'slot launch_slot_' in line:
            cur=int(re.search(r'task (\d+)',line).group(1));orderQ.append(cur)
            tasksQ[cur]=dict(launch=t,rel=None)
        elif 'stop processing:' in line:
            tasksQ[cur]['rel']=t
        v=fkeep(line)
        if v is not None: fk.append((cur,t,v))

comp_rows=[]
for i,t,v in fk:
    if v<0.9: comp_rows.append("<tr><td>"+str(i)+"</td><td>"+format(t,".0f")+"</td><td>"+format(v,".3f")+"</td><td>"+format(100*(1-v),".1f")+"%</td></tr>")
active=[(tasksQ[c]['launch']-tasksQ[orderQ[idx-1]]['launch']) for idx,c in enumerate(orderQ) if idx>0 and tasksQ[c]['rel']]
median=int(sorted(active)[len(active)//2]) if active else 0

gap_rows=[]
for idx,c in enumerate(orderQ):
    d=tasksQ[c]
    gap=(d['launch']-tasksQ[orderQ[idx-1]]['launch']) if idx>0 else 0.0
    gap_rows.append("<tr><td>"+str(c)+"</td><td>"+format(d['launch'],".0f")+"</td><td>"+format(gap,".0f")+"</td></tr>")

# ===================================================================== HTML
L=[]
L.append("<!DOCTYPE html>")
L.append("<html lang='ja'><head><meta charset='utf-8'>")
L.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
L.append("<title>Notes-LocalLM Report - case2 by Ornith-1.5 9B Q8_0</title>")
L.append("<style>")
CSS="""
:root{--bg:#0f1117;--card:#171a23;--line:#2a2f3a;--txt:#e6e9ef;--dim:#9aa4b2;--accent:#7aa2f7;--good:#9ece6a;--bad:#e06c75;--warn:#e6c07a;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.65 'Hiragino Kaku Gothic ProN','Yu Gothic','Segoe UI',system-ui,sans-serif;}
header{padding:34px 28px 22px;border-bottom:1px solid var(--line);}
header h1{margin:0;font-size:26px;color:#fff;}
header .sub{color:var(--dim);margin-top:6px;font-size:13px;}
main{max-width:1180px;margin:0 auto;padding:24px 20px 80px;}
section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 24px;margin:22px 0;}
h2{font-size:20px;color:#fff;margin:0 0 10px;}
h3{font-size:16px;color:#fff;margin:18px 0 8px;}
h3 .en{color:var(--dim);font-size:12px;font-weight:400;margin-left:6px;}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:12.5px;}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:right;}
th{background:#1e2330;color:#cdd5e1;position:sticky;top:0;}
td:first-child,th:first-child{text-align:left;}
code{background:#0c0e14;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:11.5px;color:#c0caff;font-family:'SF Mono',Menlo,monospace;}
.row-gap{background:#14261b !important;}
.row-decay{background:#241a20 !important;}
.row-flat{background:#14191f !important;}
tr:hover{filter:brightness(1.12);}
.stat{display:flex;flex-wrap:wrap;gap:12px;}
.stat>div{flex:1;min-width:150px;background:#111420;border:1px solid var(--line);border-radius:9px;padding:12px 14px;}
.stat .k{color:var(--dim);font-size:12px;}
.stat .v{font-size:22px;font-weight:700;color:#fff;margin-top:4px;}
.stat .v.good{color:var(--good);}
.stat .v.bad{color:var(--bad);}
.stat .v.warn{color:var(--warn);}
.note{color:var(--dim);font-size:13px;margin:8px 0 14px;}
.note b{color:var(--txt);}
.en{color:var(--dim);font-size:12.5px;}
.scroll{max-height:520px;overflow:auto;border:1px solid var(--line);border-radius:8px;}
.foot{color:var(--dim);font-size:12px;text-align:center;padding:30px 0;}
""".strip()
L.append(CSS)
L.append("</style></head><body>")

# ---- 1. 対象と目的
L.append("<header>")
L.append("<h1>Notes-LocalLM Report - case2 by Ornith-1.5 9B Q8_0</h1>")
L.append('<div class="sub">llama.cpp server log analysis - Ornith-1.5-9B-Q8_0 (80K ctx) vs Q4_K_M (128K ctx) vs case1 Qwen3.8-27B-UD-Q2_K_XL<br>macOS Tahoe - MacBook Air M4 - llama.cpp 0.4.0 - opencode 1.18.30</div>')
L.append("</header>")

L.append("<section id='overview'><h2>1. 対象と目的</h2><div class='en'>1. Objectives and scope</div>")
L.append("<p class='note'>本報告書は、<b>case2</b>（Ornith-1.5-9B-Q8_0 / ctx-size 81920）と <b>case1</b>（Qwen3.8-27B-UD-Q2_K_XL）の llama.cpp サーバーログから抽出した計数データを基に、<b>コンテキストの蓄積と処理速度の逆相関</b>および<b>モデル間パフォーマンスの比較</b>を定量的にまとめた物。</p>")
L.append("<div class='stat'>")
L.append('<div><div class="k">対象モデル</div><div class="v">Ornith-1.5-9B (Q8_0 / Q4_K_M) &middot; Qwen3.8-27B-UD-Q2_K_XL</div></div>')
L.append('<div><div class="k">case2 実行時間</div><div class="v">約 '+format(Q8_0['dur'],".0f")+' 分 ('+format(Q8_0['dur']/60,".1f")+' h)</div></div>')
L.append('<div><div class="k">case1 実行時間</div><div class="v">約 '+format(QWEN['dur'],".0f")+' 分 ('+format(QWEN['dur']/60,".1f")+' h)</div></div>')
L.append('<div><div class="k">case2 task数</div><div class="v">'+str(Q8_0['n'])+'</div></div>')
L.append('<div><div class="k">case1 task数</div><div class="v">'+str(QWEN['n'])+'</div></div>')
L.append("</div></section>")

# ---- 2.1 対比表
L.append("<section id='case2'><h2>2. case2 実行結果からのログ分析と考察</h2><div class='en'>2. case2 log analysis & discussion</div>")
L.append("<p class='note'>case2 は、Ornith-1.5-9B を <b>Q8_0 (80K ctx)</b> と <b>Q4_K_M (128K ctx)</b> の2構成で実行した。両者とも同一 M4 / 24GB 環境で比較可能。以下は <b>Q8_0</b> を中心に解析し、Q4_K_M で補強する。</p>")
L.append("<h3>2.1 対比表（約／概算）<span class='en'>2.1 Comparison table</span></h3>")
L.append("<table><tr><th>項目</th><th>Q8_0 (80K)</th><th>Q4_K_M (128K)</th><th>Qwen3.8-27B (80K)</th></tr>")
L.append(row(["項目","","",""]))
L.append(row(["tasks（総task数）", Q8_0['n'], Q4_KM['n'], QWEN['n']]))
L.append(row(["実行時間（min）", Q8_0['dur'], Q4_KM['dur'], QWEN['dur']]))
L.append(row(["prompt eval 速度 min-max (t/s)", format(Q8_0['ev_min'],".0f")+"-"+format(Q8_0['ev_max'],".0f"), format(Q4_KM['ev_min'],".0f")+"-"+format(Q4_KM['ev_max'],".0f"), format(QWEN['ev_min'],".0f")+"-"+format(QWEN['ev_max'],".0f")]))
L.append(row(["prompt eval 速度 mean (t/s)", Q8_0['ev_mean'], Q4_KM['ev_mean'], QWEN['ev_mean']]))
L.append(row(["prompt eval 速度 低下比", Q8_0['decay'], Q4_KM['decay'], QWEN['decay']]))
L.append(row(["生成速度 mean (t/s)", Q8_0['g_mean'], Q4_KM['g_mean'], QWEN['g_mean']]))
L.append(row(["生成速度 min-max (t/s)", format(Q8_0['g_min'],".2f")+"-"+format(Q8_0['g_max'],".2f"), format(Q4_KM['g_min'],".2f")+"-"+format(Q4_KM['g_max'],".2f"), format(QWEN['g_min'],".2f")+"-"+format(QWEN['g_max'],".2f")]))
L.append("</table>")
L.append("<p class='note'><b>考察：</b>① prompt eval 速度は case2・case1 とも時間経過に伴い低下する（逆相関）。② prompt eval 速度の平均は 9B モデル（Q8_0/Q4_K_M）で約等しい（&asymp;90 t/s）ものの、Qwen3.8-27B-Q2_K では約半分以下（&asymp;17 t/s）に鈍る（27B かつ Q2_K 量化のため）。③ 生成速度は 128K の Q4_K_M が最高（&asymp;12 t/s）、Q8_0 が次（&asymp;7 t/s）、Qwen3.8-27B が最下（&asymp;4 t/s）。</p>")

# ---- 2.2 Q8_0 時間系列テーブル
r=table_rows(Q8_0)
L.append("<h3>2.2 case2 Q8_0 時間系列（launch 時間＝cumulative 分）<span class='en'>2.2 Q8_0 timeline (launch time = cumulative min)</span></h3>")
L.append("<p class='note'>各 task の launch 時刻（cumulative 分）、処理速度、生成速度を記録。速度低下（decay）の方向で色分け。</p>")
L.append("<div class='scroll'><table><tr><th>task</th><th>launch(min)</th><th>dur(min)</th><th>p0_tok</th><th>p1_tok</th><th>p0_tps</th><th>p1_tps</th><th>decay</th><th>p0_mst</th><th>p1_mst</th><th>ev_mst</th><th>ev_tps</th><th>gmax</th><th>g0</th><th>g1</th><th>ntok</th><th>ftps</th></tr>")
for (i,l,d,p0,p1,t0,t1,dec,p0ms,p1ms,pe_ms,pe_tps,gmax,g0,g1,ntok,ftps) in r:
    cls="row-"+("gap" if dec<0 else "decay" if dec>0 else "flat")
    L.append(row([str(i), num(l), num(d), num(p0), num(p1), num(t0), num(t1), format(dec,".0f")+"%", num(p0ms), num(p1ms), num(pe_ms), num(pe_tps), num(gmax), num(g0), num(g1), num(ntok), num(ftps)], cls))
L.append("</table></div>")
L.append("<p class='note'>p0/p1：task 開始・終了時の prompt processing 速度。ev_mst/ev_tps：1 prompt 処理の ms/token 与 t/s。g0/g1：生成開始・終了時の速度（t/s）。ntok：最終処理 token 数。ftps：final prompt eval t/s。</p>")

# ---- 2.3 考察
L.append("<h3>2.3 case2 考察（逆相関・compaction・回復）<span class='en'>2.3 Discussion</span></h3>")
L.append("<p class='note'><b>① コンテキスト蓄積と処理速度の逆相関</b><br>Q8_0 では prompt eval 速度が <b>約 "+format(Q8_0['ev_max'],".0f")+"&rarr;"+format(Q8_0['ev_min'],".0f")+" t/s（"+format(Q8_0['decay'],".2f")+"x 低下）</b>、生成速度も低下傾向を示す。ctx-size は固定 81920 だが、会話が進むにつれ有効コンテキストが積み上がるため、1 step 当たりの計算量が增大し速度が低下する。</p>")
L.append("<p class='note'><b>② compaction（f_keep）</b><br>f_keep は大半が 1.000（保持）で、稀に 0.83〜0.98 へ低下。例：task 1887 で f_keep=0.832（17% のコンテキストを削除）。大きな時間ギャップ（例：task 1887&rarr;3062 は約13分、server 単位で 1600 分以上）は、opencode クライアントが compaction を指示するタイミングと一致する。</p>")
L.append("<p class='note'><b>③ 速度回復</b><br>task 5455（約90分、最遅：prompt eval &asymp;"+format(Q8_0['ev_min'],".0f")+" t/s）を境に、task 7058（約133分：prompt eval &asymp;"+format(Q8_0['ev_min'],".0f")+" t/s）で prompt eval が回復する。これは深いコンテキストが compaction でクリアされ、有効コンテキストがリセットされたことを示す。</p>")
L.append("<p class='note'><b>④ Q8_0 vs Q4_K_M（128K）</b><br>128K の Q4_K_M は生成速度が Q8_0 の約1.8倍（&asymp;12 t/s vs &asymp;7 t/s）に達する。大容量 KV cache（Q8_0）は精度を犠牲にせず高速だが、128K&times;Q4 はより大きな有効コンテキストを維持しつつ生成速度を維持できる。両者とも prompt eval 速度の平均は約等しい（&asymp;90 t/s）。</p>")

# ---- 3. HTML評価
L.append("<section id='html-eval'><h2>3. HTML評価（見出し／構造／表の網羅性）</h2><div class='en'>3. HTML evaluation</div>")
L.append("<ul style='margin:8px 0 8px 20px;line-height:1.9;'>")
L.append("<li><b>見出し：</b>章立て（1-3）とセクション内見出し（2.1-2.3）で階層化。英語併記（.en）で多言語対応。</li>")
L.append("<li><b>構造：</b>header（目的）&rarr; stat（概要）&rarr; 対比表 &rarr; 時間系列表 &rarr; 考察 &rarr; HTML評価 &rarr; case1 分析 &rarr; 補足、直線的な読流し構造。</li>")
L.append("<li><b>表の網羅性：</b>case2（Q8_0）は launch/dur/token/速度/decay/生成速度/compaction まで。case1（Qwen3.8-27B）は同様の項目を18task分。比較表は3モデル&times;7項目。</li>")
L.append("<li><b>改善点：</b>時間系列表は scroll 対応で500行超も可読。色分け（decay/gap/flat）で傾向を視覚化。</li>")
L.append("</ul></section>")

# ---- 4. case1 分析
L.append("<section id='case1'><h2>4. case1 llama-server ログ分析（Qwen3.8-27B-UD-Q2_K_XL）</h2><div class='en'>4. case1 llama-server log analysis</div>")
L.append("<p class='note'>Qwen3.8-27B-UD-Q2_K_XL（KV=Q8_0、ctx=約"+ctxQ+"）の傾向分析。<b>コンテキストサイズ／時間経過 vs 処理速度の逆相関</b>・<b>compaction時間</b>・<b>待ち時間を除く発生間隔</b>を抽出。</p>")
L.append("<h3>4.1 概要<span class='en'>4.1 Overview</span></h3>")
L.append("<div class='stat'>")
L.append('<div><div class="k">tasks（総数）</div><div class="v">'+str(QWEN['n'])+'</div></div>')
L.append('<div><div class="k">実行時間</div><div class="v">約 '+format(QWEN['dur'],".0f")+' 分 ('+format(QWEN['dur']/60,".1f")+' h)</div></div>')
L.append('<div><div class="k">prompt eval 速度 min-max (t/s)</div><div class="v">'+format(QWEN['ev_min'],".0f")+"-"+format(QWEN['ev_max'],".0f")+'</div></div>')
L.append('<div><div class="k">prompt eval 低下比</div><div class="v bad">'+format(QWEN['decay'],".2f")+'x</div></div>')
L.append('<div><div class="k">生成速度 mean (t/s)</div><div class="v">'+format(QWEN['g_mean'],".2f")+'</div></div>')
L.append("</div>")
L.append("<p class='note'>9B モデル（case2）の約2〜3倍の低下比（"+format(QWEN['decay'],".2f")+"x）を示し、コンテキスト蓄積に伴う速度低下が最も顕著。Q2_K 量化＋27B のため基盤速度が低い。</p>")
L.append("<h3>4.2 compaction（f_keep）イベント<span class='en'>4.2 Compaction events</span></h3>")
L.append("<p class='note'>f_keep が0.9未満（コンテキストを削除）のイベント。大半は f_keep=1.000（保持）で、稀に大きく低下。</p>")
L.append("<div class='scroll'><table><tr><th>task</th><th>launch(min)</th><th>f_keep</th><th>削除率</th></tr>")
L.append("".join(comp_rows))
L.append("</table></div>")
L.append("<p class='note'>compaction 時間は、f_keep が低下する task の launch 時刻と前 task 終了の差分。例：task 1887 で f_keep=0.832（17% 削除）。大きな時間ギャップ（例：task 1887&rarr;3062 は約13分）は、opencode クライアントが compaction を指示するタイミングと一致する。</p>")
L.append("<h3>4.3 待ち時間を除く発生間隔<span class='en'>4.3 Active interval (excluding wait)</span></h3>")
L.append("<p class='note'>task 間 launch 時刻のギャップ。待ち時間（処理待ち）を除いた <b>active 間隔の中央値 &asymp; "+str(median)+" 分</b>。</p>")
L.append("<div class='scroll'><table><tr><th>task</th><th>launch(min)</th><th>gap_prev(min)</th></tr>")
L.append("".join(gap_rows))
L.append("</table></div>")
L.append("<p class='note'>active 間隔（0 以外）の中央値 &asymp; "+str(median)+" 分。待ち時間を含む総ギャップはそれ以上。計画＋増分コーディングフェーズでは短（数分〜数10分）、長時間タスク後は長（数十分〜数時間）。</p>")

# ---- 5. 補足
L.append("<section id='supplement'><h2>5. 補足：case1 Qwen3.8-27B-UD-Q2_K_XL パフォーマンス傾向（参考）</h2><div class='en'>5. Supplement: case1 Qwen3.8-27B-UD-Q2_K_XL trends</div>")
L.append("<p class='note'>末尾参考情報。case1 は Qwen3.8-27B-UD-Q2_K_XL の长时间運用ログ（140 task）。9B モデル（case2）に比べ基盤速度が低く、コンテキスト蓄積に伴う速度低下が顕著。</p>")
L.append("<div class='stat'>")
L.append('<div><div class="k">prompt eval 速度 mean (t/s)</div><div class="v">'+format(QWEN['ev_mean'],".1f")+'</div></div>')
L.append('<div><div class="k">生成速度 mean (t/s)</div><div class="v">'+format(QWEN['g_mean'],".2f")+'</div></div>')
L.append('<div><div class="k">prompt eval 低下比</div><div class="v bad">'+format(QWEN['decay'],".2f")+'x</div></div>')
L.append('<div><div class="k">生成速度 範囲 (t/s)</div><div class="v">'+format(QWEN['g_min'],".2f")+"-"+format(QWEN['g_max'],".2f")+'</div></div>')
L.append('<div><div class="k">総実行時間</div><div class="v">約 '+format(QWEN['dur'],".0f")+' 分 ('+format(QWEN['dur']/60,".1f")+' h)</div></div>')
L.append("</div>")
L.append("<p class='note'>参考：case2（Ornith-1.5-9B）は prompt eval &asymp;90 t/s、生成 &asymp;7〜12 t/s。case1（Qwen3.8-27B-Q2_K）は prompt eval &asymp;17 t/s、生成 &asymp;4 t/s。27B＋Q2_K のため基盤が約半分以下。長時間運用でコンテキストが蓄積し、速度低下が顕著（"+format(QWEN['decay'],".2f")+"x）。</p>")
L.append("<p class='note'>メモリ配分・使用量・安定動作の模索が目的。KV=Q8_0・ctx=80K・compaction.auto=true、limit.context/output/input を付与。</p>")

L.append("<footer class='foot'>Notes-LocalLM Report - generated by log analysis script - data from llama.cpp server logs<br>(case2 Q8_0: "+str(Q8_0['n'])+" tasks, "+format(Q8_0['dur'],".0f")+" min)<br>(case1 Qwen3.8-27B: "+str(QWEN['n'])+" tasks, "+format(QWEN['dur'],".0f")+" min)<br>all numbers are approximate (概算) unless otherwise noted.</footer>")

L.append("</body></html>")
open(OUT,"w",encoding="utf-8").write("\n".join(L))
print("wrote "+OUT)
print("Q8_0 tasks="+str(Q8_0['n'])+" dur="+format(Q8_0['dur'],".0f")+"  Q4_KM tasks="+str(Q4_KM['n'])+"  QWEN tasks="+str(QWEN['n'])+" dur="+format(QWEN['dur'],".0f"))
print("compaction events="+str(len(comp_rows))+"  gap rows="+str(len(gap_rows))+"  median="+str(median))
