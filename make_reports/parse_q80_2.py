import re, statistics
LOG = "20260912_Ornith-1.5-9B-Q4_K_M.log"
ts_re = re.compile(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)')
def parse_ts(m): return int(m[1])*60 + int(m[2]) + int(m[3])/1000 + int(m[4])/1e6
def pe(line):
    m = re.search(r'prompt eval time =\s*(\d+\.?\d*) ms / \s*(\d+) tokens \( *(\d+\.?\d*) ms per token, \s*(\d+\.?\d*) tokens per second\)', line)
    return dict(ms=float(m[1]), tok=int(m[2]), ms_per_tok=float(m[3]), tok_per_s=float(m[4])) if m else None
def gs(line):
    m = re.search(r'n_gen =\s*(\d+), tg =\s*([\d.]+) t/s, tg_3s =\s*([\d.]+) t/s', line)
    return dict(n_gen=int(m[1]), tg=float(m[2])) if m else None
def pp(line):
    m = re.search(r'prompt processing, n_tokens = \s*(\d+), progress = \s*([\d.]+), t = \s*(\d+\.?\d*) s / (\d+\.?\d*) tokens per second', line)
    return dict(tok=int(m[1]), prog=float(m[2]), t=float(m[3]), tok_per_s=float(m[4])) if m else None
def rel(line):
    m = re.search(r'stop processing: n_tokens = \s*(\d+)', line)
    return int(m[1]) if m else 0
tasks = {}; order = []; cur = None
with open(LOG) as f:
    for line in f:
        m = ts_re.match(line)
        if not m: continue
        t = parse_ts(m)
        if 'slot launch_slot_' in line:
            cur = int(re.search(r'task (\d+)', line).group(1)); order.append(cur)
            tasks[cur] = dict(launch=t, pp=[], gs=[], pe=None, rel=None, ntok=0)
        elif 'prompt processing' in line:
            x = pp(line)
            if x: tasks[cur]['pp'].append(x)
        elif 'prompt eval time =' in line:
            x = pe(line)
            if x: tasks[cur]['pe'] = x
        elif 'n_gen =' in line:
            x = gs(line)
            if x: tasks[cur]['gs'].append(x)
        elif 'stop processing:' in line:
            tasks[cur]['ntok'] = rel(line); tasks[cur]['rel'] = t
def mst(v): return round(1.0/v*1000, 2) if v else 0.0
print(f"{'task':>7} {'launch':>8} {'dur':>7} {'p0_tok':>8} {'p1_tok':>8} {'p0_tps':>8} {'p1_tps':>8} {'decay':>8} {'p0_mst':>7} {'p1_mst':>7} {'ev_mst':>7} {'ev_tps':>7} {'gmax':>6} {'g0':>6} {'g1':>6} {'ntok':>7} {'ftps':>7}")
for c in order:
    d = tasks[c]; pp = d['pp']
    d['gmax'] = max([x['n_gen'] for x in d['gs']]) if d['gs'] else 0
    d['g0'] = d['gs'][0]['tg'] if d['gs'] else 0
    d['g1'] = d['gs'][-1]['tg'] if d['gs'] else 0
    d['dur'] = d['rel'] - d['launch'] if d['rel'] else 0
    pp0 = d['pp'][0] if d['pp'] else None; pp1 = d['pp'][-1] if d['pp'] else None
    pe = d['pe'] or {}
    decay = (pp0['tok_per_s']/(pp1['tok_per_s'] or 0.001) - 1) if pp0 else 0
    print(f"{c:>7} {d['launch']:>8.1f} {d['dur']:>7.1f} {pp0['tok'] if pp0 else 0:>8} {pp1['tok'] if pp1 else 0:>8} {pp0['tok_per_s'] if pp0 else 0:>8.1f} {pp1['tok_per_s'] if pp1 else 0:>8.1f} {decay:>8.0f} {mst(pp0['tok_per_s']) if pp0 else 0:>7.2f} {mst(pp1['tok_per_s']) if pp1 else 0:>7.2f} {pe['ms_per_tok'] if pe else 0:>7.2f} {pe['tok_per_s'] if pe else 0:>7.1f} {d['gmax']:>6} {d['g0']:>6.2f} {d['g1']:>6.2f} {d['ntok']:>7} {pe['tok_per_s'] if pe else 0:>7.1f}")
print(f"\nTotal tasks: {len(order)}, Total duration: {tasks[order[-1]]['rel']:.1f} min")
