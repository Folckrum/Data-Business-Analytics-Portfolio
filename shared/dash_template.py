import json

DARK, SURFACE, BORDER, TEXT, MUTED = "#0d1117", "#161b22", "#30363d", "#e6edf3", "#8b949e"

BASE = dict(
    paper_bgcolor=DARK, plot_bgcolor=SURFACE,
    font=dict(color=TEXT, family="Segoe UI, system-ui, sans-serif"),
    xaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickfont=dict(color=MUTED)),
    margin=dict(l=60, r=30, t=50, b=50), height=380,
    legend=dict(bgcolor=SURFACE, bordercolor=BORDER),
)

CSS = """
:root{--bg:#0d1117;--s:#161b22;--b:#30363d;--t:#e6edf3;--m:#8b949e;--a:#388bfd}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--t);font-family:'Segoe UI',system-ui,sans-serif}
.top{background:var(--s);border-bottom:1px solid var(--b);padding:16px 32px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:9}
.top h1{font-size:18px}.top span.tag{background:rgba(56,139,253,.15);border:1px solid rgba(56,139,253,.4);color:var(--a);padding:4px 12px;border-radius:20px;font-size:12px}
.wrap{max-width:1400px;margin:0 auto;padding:28px 32px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:12px}
.kpi{background:var(--s);border:1px solid var(--b);border-radius:10px;padding:18px 20px}
.kpi small{color:var(--m);font-size:11px;text-transform:uppercase;letter-spacing:.8px}
.kpi b{display:block;font-size:22px;margin:8px 0 4px}.kpi i{font-style:normal;font-size:12px;color:var(--m)}
h2{font-size:15px;margin:28px 0 14px;padding-bottom:10px;border-bottom:1px solid var(--b)}
.grid{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:20px;margin-bottom:20px}
.card{background:var(--s);border:1px solid var(--b);border-radius:12px;padding:4px;min-width:0}
footer{text-align:center;color:var(--m);font-size:12px;padding:28px;border-top:1px solid var(--b);margin-top:32px}
@media(max-width:900px){.kpis{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}}
"""


def page(path, title, tag, kpis, sections, figs):
    """kpis: [(label, value, sub, color)]; sections: [(heading, [chart ids])]; figs: {id: plotly fig}"""
    k = "".join(f'<div class="kpi"><small>{a}</small><b style="color:{d}">{b}</b><i>{c}</i></div>' for a, b, c, d in kpis)
    body = ""
    for head, ids in sections:
        cards = "".join(f'<div class="card" id="{i}"></div>' for i in ids)
        body += f'<h2>{head}</h2><div class="grid" style="--n:{len(ids)}">{cards}</div>'
    data = json.dumps({i: f.to_json() for i, f in figs.items()})
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist@2.27.0/plotly.min.js"></script>
<style>{CSS}</style></head><body>
<div class="top"><h1>{title}</h1><span class="tag">{tag}</span></div>
<div class="wrap"><div class="kpis">{k}</div>{body}</div>
<footer>{title} · Folckrum</footer>
<script>const D={data};
for(const [id,s] of Object.entries(D)){{const f=JSON.parse(s);Plotly.newPlot(id,f.data,f.layout,{{responsive:true,displayModeBar:false}})}}
</script></body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"saved {path} ({len(html)/1024:.0f} KB)")
