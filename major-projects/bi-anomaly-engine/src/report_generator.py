import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from anomaly_detector import Anomaly
from typing import List


def _severity_badge(sev):
    colors = {"critical": "#e74c3c", "warning": "#f39c12", "info": "#3498db"}
    return f'<span class="badge" style="background:{colors.get(sev,"#95a5a6")}">{sev.upper()}</span>'


def _direction_icon(direction):
    return "▼" if direction == "drop" else "▲"


def _direction_color(direction):
    return "#e74c3c" if direction == "drop" else "#27ae60"


def build_kpi_cards(sales, support, marketing):
    latest = sales["date"].max()
    last7 = sales[sales["date"] >= latest - pd.Timedelta(days=6)]
    prev7 = sales[(sales["date"] >= latest - pd.Timedelta(days=13)) &
                  (sales["date"] < latest - pd.Timedelta(days=6))]

    rev_curr = last7["revenue"].sum()
    rev_prev = prev7["revenue"].sum()
    rev_chg = (rev_curr - rev_prev) / rev_prev * 100 if rev_prev else 0

    ord_curr = last7["orders"].sum()
    ord_prev = prev7["orders"].sum()
    ord_chg = (ord_curr - ord_prev) / ord_prev * 100 if ord_prev else 0

    sup_latest = support[support["date"] >= latest - pd.Timedelta(days=6)]
    csat = sup_latest["csat_score"].mean()
    tickets = sup_latest["tickets_opened"].sum()

    mkt_latest = marketing[marketing["date"] >= latest - pd.Timedelta(days=6)]
    roas = mkt_latest["roas"].mean()

    def card(title, value, change=None, unit="", inverse=False):
        if change is not None:
            good = (change > 0) != inverse
            col = "#27ae60" if good else "#e74c3c"
            arr = "▲" if change > 0 else "▼"
            chg_html = f'<div class="kpi-change" style="color:{col}">{arr} {abs(change):.1f}% WoW</div>'
        else:
            chg_html = ""
        return f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{unit}{value}</div>
            {chg_html}
        </div>"""

    return (
        card("Revenue (7d)", f"{rev_curr:,.0f}", rev_chg, "₹") +
        card("Orders (7d)", f"{ord_curr:,}", ord_chg) +
        card("Avg CSAT", f"{csat:.2f}", None, "") +
        card("Support Tickets (7d)", f"{tickets:,}", None, "", inverse=True) +
        card("Avg ROAS", f"{roas:.2f}", None, "")
    )


def build_anomaly_table(anomalies: List[Anomaly], filter_sev=None):
    rows = ""
    for a in anomalies:
        if filter_sev and a.severity != filter_sev:
            continue
        col = _direction_color(a.direction)
        icon = _direction_icon(a.direction)
        rows += f"""
        <tr>
            <td>{a.date}</td>
            <td>{a.metric}</td>
            <td>{a.segment}</td>
            <td>{_severity_badge(a.severity)}</td>
            <td style="color:{col};font-weight:600">{icon} {abs(a.deviation_pct):.1f}%</td>
            <td>{a.method}</td>
            <td class="narrative">{a.narrative}</td>
        </tr>"""

    if not rows:
        rows = '<tr><td colspan="7" style="text-align:center;color:#7f8c8d">No anomalies in this category</td></tr>'
    return rows


def build_charts_data(sales, anomalies):
    sales_daily = sales.groupby("date")[["revenue", "orders"]].sum().reset_index()
    sales_daily["date"] = sales_daily["date"].astype(str)

    critical_dates = list({a.date for a in anomalies if a.severity == "critical"})

    by_cat = sales.groupby("category")["revenue"].sum().reset_index()
    by_reg = sales.groupby("region")["revenue"].sum().reset_index()
    by_month = sales.copy()
    by_month["month"] = pd.to_datetime(by_month["date"]).dt.strftime("%Y-%m")
    by_month = by_month.groupby("month")["revenue"].sum().reset_index()

    sev_counts = {"critical": 0, "warning": 0, "info": 0}
    for a in anomalies:
        sev_counts[a.severity] = sev_counts.get(a.severity, 0) + 1

    return {
        "dates": sales_daily["date"].tolist(),
        "revenue": sales_daily["revenue"].tolist(),
        "orders": sales_daily["orders"].tolist(),
        "critical_dates": critical_dates,
        "categories": by_cat["category"].tolist(),
        "cat_revenue": by_cat["revenue"].tolist(),
        "regions": by_reg["region"].tolist(),
        "reg_revenue": by_reg["revenue"].tolist(),
        "months": by_month["month"].tolist(),
        "monthly_revenue": by_month["revenue"].tolist(),
        "sev_counts": sev_counts,
    }


def generate_report(sales, support, marketing, anomalies: List[Anomaly], output_path="reports/bi_report.html"):
    os.makedirs("reports", exist_ok=True)

    kpi_cards = build_kpi_cards(sales, support, marketing)
    all_rows = build_anomaly_table(anomalies)
    critical_rows = build_anomaly_table(anomalies, "critical")
    warning_rows = build_anomaly_table(anomalies, "warning")
    charts = build_charts_data(sales, anomalies)
    charts_json = json.dumps(charts)

    n_critical = sum(1 for a in anomalies if a.severity == "critical")
    n_warning = sum(1 for a in anomalies if a.severity == "warning")
    n_info = sum(1 for a in anomalies if a.severity == "info")
    generated = datetime.now().strftime("%d %b %Y, %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BI Anomaly Engine — Intelligence Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #232635;
    --border: #2e3250;
    --text: #e8eaf6;
    --muted: #7986cb;
    --critical: #ef5350;
    --warning: #ffa726;
    --info: #42a5f5;
    --success: #66bb6a;
    --accent: #7c4dff;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 14px; }}
  
  .topbar {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .topbar h1 {{ font-size: 18px; font-weight: 700; color: #fff; }}
  .topbar h1 span {{ color: var(--accent); }}
  .topbar-meta {{ color: var(--muted); font-size: 12px; }}
  .status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(239,83,80,0.15);
    border: 1px solid rgba(239,83,80,0.4);
    color: var(--critical);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
  }}
  .status-pill.ok {{ background: rgba(102,187,106,0.15); border-color: rgba(102,187,106,0.4); color: var(--success); }}
  .dot {{ width: 7px; height: 7px; border-radius: 50%; background: currentColor; animation: pulse 1.5s infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity:1 }} 50% {{ opacity:0.3 }} }}

  .container {{ max-width: 1400px; margin: 0 auto; padding: 28px 32px; }}

  .summary-bar {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 28px;
  }}
  .summary-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
  }}
  .summary-icon {{
    width: 48px; height: 48px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
  }}
  .summary-card.critical .summary-icon {{ background: rgba(239,83,80,0.15); }}
  .summary-card.warning .summary-icon {{ background: rgba(255,167,38,0.15); }}
  .summary-card.info .summary-icon {{ background: rgba(66,165,245,0.15); }}
  .summary-num {{ font-size: 32px; font-weight: 700; line-height: 1; }}
  .summary-label {{ color: var(--muted); font-size: 13px; margin-top: 4px; }}
  .summary-card.critical .summary-num {{ color: var(--critical); }}
  .summary-card.warning .summary-num {{ color: var(--warning); }}
  .summary-card.info .summary-num {{ color: var(--info); }}

  .kpi-strip {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
    margin-bottom: 28px;
  }}
  .kpi-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
  }}
  .kpi-title {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }}
  .kpi-value {{ font-size: 22px; font-weight: 700; color: #fff; }}
  .kpi-change {{ font-size: 12px; margin-top: 6px; font-weight: 600; }}

  .charts-grid {{
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    margin-bottom: 28px;
  }}
  .charts-row {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    margin-bottom: 28px;
  }}
  .chart-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
  }}
  .chart-title {{ font-size: 13px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 16px; }}
  .chart-card canvas {{ max-height: 220px; }}

  .section-header {{
    font-size: 16px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
  }}

  .tabs {{ display: flex; gap: 4px; margin-bottom: 16px; }}
  .tab {{
    padding: 8px 18px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--muted);
    transition: all 0.2s;
  }}
  .tab.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
  .tab-pane {{ display: none; }}
  .tab-pane.active {{ display: block; }}

  .table-wrap {{ overflow-x: auto; border-radius: 10px; border: 1px solid var(--border); }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{
    background: var(--surface2);
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
  }}
  td {{ padding: 12px 16px; border-top: 1px solid var(--border); vertical-align: top; font-size: 13px; }}
  tr:hover td {{ background: var(--surface2); }}
  .narrative {{ color: #b0bec5; line-height: 1.5; max-width: 420px; }}
  .badge {{
    display: inline-block;
    padding: 3px 9px;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 700;
    color: #fff;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  .search-bar {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 16px;
    color: var(--text);
    font-size: 13px;
    width: 100%;
    margin-bottom: 14px;
    outline: none;
  }}
  .search-bar:focus {{ border-color: var(--accent); }}

  footer {{
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    padding: 28px;
    border-top: 1px solid var(--border);
    margin-top: 40px;
  }}
</style>
</head>
<body>

<div class="topbar">
  <h1>BI <span>Anomaly</span> Engine</h1>
  <div style="display:flex;align-items:center;gap:16px">
    <span class="topbar-meta">Generated: {generated}</span>
    <span class="status-pill {"ok" if n_critical == 0 else ""}">
      <span class="dot"></span>
      {"ALL CLEAR" if n_critical == 0 else f"{n_critical} CRITICAL ALERTS"}
    </span>
  </div>
</div>

<div class="container">

  <!-- Summary Bar -->
  <div class="summary-bar">
    <div class="summary-card critical">
      <div class="summary-icon">🔴</div>
      <div>
        <div class="summary-num">{n_critical}</div>
        <div class="summary-label">Critical Anomalies</div>
      </div>
    </div>
    <div class="summary-card warning">
      <div class="summary-icon">🟡</div>
      <div>
        <div class="summary-num">{n_warning}</div>
        <div class="summary-label">Warnings</div>
      </div>
    </div>
    <div class="summary-card info">
      <div class="summary-icon">🔵</div>
      <div>
        <div class="summary-num">{n_info}</div>
        <div class="summary-label">Informational</div>
      </div>
    </div>
  </div>

  <!-- KPI Strip -->
  <div class="kpi-strip">
    {kpi_cards}
  </div>

  <!-- Charts Row 1 -->
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">Daily Revenue — Full Year</div>
      <canvas id="revenueChart"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Anomalies by Severity</div>
      <canvas id="sevChart"></canvas>
    </div>
  </div>

  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-title">Revenue by Category</div>
      <canvas id="catChart"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Revenue by Region</div>
      <canvas id="regChart"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-title">Monthly Revenue Trend</div>
      <canvas id="monthChart"></canvas>
    </div>
  </div>

  <!-- Anomaly Tables -->
  <div class="section-header">📋 Anomaly Intelligence Report</div>

  <input class="search-bar" id="searchBox" placeholder="Search by segment, metric, date..." onkeyup="filterTable()">

  <div class="tabs">
    <button class="tab active" onclick="switchTab('all', this)">All ({len(anomalies)})</button>
    <button class="tab" onclick="switchTab('critical', this)">Critical ({n_critical})</button>
    <button class="tab" onclick="switchTab('warning', this)">Warning ({n_warning})</button>
  </div>

  <div id="all" class="tab-pane active">
    <div class="table-wrap">
      <table id="mainTable">
        <thead>
          <tr>
            <th>Date</th><th>Metric</th><th>Segment</th><th>Severity</th>
            <th>Deviation</th><th>Method</th><th>Intelligence Narrative</th>
          </tr>
        </thead>
        <tbody>{all_rows}</tbody>
      </table>
    </div>
  </div>

  <div id="critical" class="tab-pane">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th><th>Metric</th><th>Segment</th><th>Severity</th>
            <th>Deviation</th><th>Method</th><th>Intelligence Narrative</th>
          </tr>
        </thead>
        <tbody>{critical_rows}</tbody>
      </table>
    </div>
  </div>

  <div id="warning" class="tab-pane">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th><th>Metric</th><th>Segment</th><th>Severity</th>
            <th>Deviation</th><th>Method</th><th>Intelligence Narrative</th>
          </tr>
        </thead>
        <tbody>{warning_rows}</tbody>
      </table>
    </div>
  </div>

</div>

<footer>
  BI Anomaly Engine &mdash; Automated Business Intelligence &mdash; Folckrum &mdash; {generated}
</footer>

<script>
const C = {charts_json};

// Revenue chart with anomaly markers
const revCtx = document.getElementById('revenueChart').getContext('2d');
const critSet = new Set(C.critical_dates);
const pointColors = C.dates.map(d => critSet.has(d) ? '#ef5350' : 'transparent');
const pointRadius = C.dates.map(d => critSet.has(d) ? 5 : 0);

new Chart(revCtx, {{
  type: 'line',
  data: {{
    labels: C.dates,
    datasets: [{{
      label: 'Revenue',
      data: C.revenue,
      borderColor: '#7c4dff',
      borderWidth: 1.5,
      fill: true,
      backgroundColor: 'rgba(124,77,255,0.08)',
      tension: 0.3,
      pointRadius: pointRadius,
      pointBackgroundColor: pointColors,
      pointBorderColor: pointColors,
    }}]
  }},
  options: {{
    responsive: true,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          label: ctx => '₹' + ctx.parsed.y.toLocaleString('en-IN', {{maximumFractionDigits:0}})
        }}
      }}
    }},
    scales: {{
      x: {{ ticks: {{ maxTicksLimit: 12, color: '#7986cb' }}, grid: {{ color: '#1e2235' }} }},
      y: {{ ticks: {{ color: '#7986cb', callback: v => '₹' + (v/1000).toFixed(0)+'K' }}, grid: {{ color: '#1e2235' }} }}
    }}
  }}
}});

// Severity donut
new Chart(document.getElementById('sevChart').getContext('2d'), {{
  type: 'doughnut',
  data: {{
    labels: ['Critical', 'Warning', 'Info'],
    datasets: [{{ data: [C.sev_counts.critical, C.sev_counts.warning, C.sev_counts.info],
      backgroundColor: ['#ef5350','#ffa726','#42a5f5'],
      borderColor: '#1a1d27', borderWidth: 3 }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#b0bec5', padding: 16 }} }} }}
  }}
}});

// Category bar
new Chart(document.getElementById('catChart').getContext('2d'), {{
  type: 'bar',
  data: {{
    labels: C.categories,
    datasets: [{{ label: 'Revenue', data: C.cat_revenue,
      backgroundColor: ['#7c4dff','#42a5f5','#66bb6a','#ffa726','#ef5350'] }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#7986cb' }}, grid: {{ display: false }} }},
      y: {{ ticks: {{ color: '#7986cb', callback: v => '₹'+(v/1000000).toFixed(1)+'M' }}, grid: {{ color: '#1e2235' }} }}
    }}
  }}
}});

// Region bar
new Chart(document.getElementById('regChart').getContext('2d'), {{
  type: 'bar',
  data: {{
    labels: C.regions,
    datasets: [{{ label: 'Revenue', data: C.reg_revenue,
      backgroundColor: ['#7c4dff','#42a5f5','#66bb6a','#ffa726'] }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#7986cb' }}, grid: {{ display: false }} }},
      y: {{ ticks: {{ color: '#7986cb', callback: v => '₹'+(v/1000000).toFixed(1)+'M' }}, grid: {{ color: '#1e2235' }} }}
    }}
  }}
}});

// Monthly line
new Chart(document.getElementById('monthChart').getContext('2d'), {{
  type: 'line',
  data: {{
    labels: C.months,
    datasets: [{{ label: 'Monthly Revenue', data: C.monthly_revenue,
      borderColor: '#66bb6a', backgroundColor: 'rgba(102,187,106,0.08)',
      fill: true, tension: 0.3, pointRadius: 4, pointBackgroundColor: '#66bb6a' }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#7986cb' }}, grid: {{ color: '#1e2235' }} }},
      y: {{ ticks: {{ color: '#7986cb', callback: v => '₹'+(v/1000000).toFixed(1)+'M' }}, grid: {{ color: '#1e2235' }} }}
    }}
  }}
}});

function switchTab(id, btn) {{
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  btn.classList.add('active');
}}

function filterTable() {{
  const q = document.getElementById('searchBox').value.toLowerCase();
  document.querySelectorAll('#mainTable tbody tr').forEach(row => {{
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"report saved: {output_path}")
    return output_path
