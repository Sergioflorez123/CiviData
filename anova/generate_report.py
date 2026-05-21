"""
Genera presentación HTML a partir del último reporte JSON de ANOVA.
Cada hipótesis tiene su sección con: H₀/H₁, estadísticas, decisión, gráficos y post-hoc.
"""

import json
import glob
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("anova/output")

HYPOTHESES = {
    "departamento": {
        "title": "¿El valor de contratos difiere entre departamentos?",
        "h0": "El valor promedio de contratos es igual en todos los departamentos de Colombia.",
        "h1": "Al menos un departamento tiene un valor promedio de contratos diferente.",
        "interp_sig": "Los departamentos difieren significativamente en el valor promedio de contratación. Esto sugiere desigualdad territorial en la inversión pública o diferencias en la capacidad de gasto.",
        "interp_nosig": "No hay evidencia de diferencias significativas entre departamentos.",
    },
    "modalidad": {
        "title": "¿El valor de contratos difiere según la modalidad de selección?",
        "h0": "El valor promedio es igual para todas las modalidades (Contratación Directa, Licitación Pública, Mínima Cuantía, etc.).",
        "h1": "Al menos una modalidad tiene un valor promedio diferente.",
        "interp_sig": "La modalidad de selección está fuertemente asociada al monto: las licitaciones públicas manejan valores mucho mayores que la mínima cuantía, lo cual es coherente con el diseño normativo.",
        "interp_nosig": "Las modalidades no muestran diferencias significativas en valor.",
    },
    "tipo_contrato": {
        "title": "¿El valor de contratos difiere según el tipo de contrato?",
        "h0": "El valor promedio es igual para todos los tipos de contrato (Obra, Consultoría, Suministro, etc.).",
        "h1": "Al menos un tipo de contrato tiene un valor promedio diferente.",
        "interp_sig": "Los tipos de contrato tienen perfiles de valor muy distintos: obras e interventorías son significativamente más costosas que suministros o prestación de servicios.",
        "interp_nosig": "Los tipos de contrato no difieren significativamente en valor.",
    },
    "origen": {
        "title": "¿El valor de contratos difiere entre fuentes SECOP (I vs II vs Integrado)?",
        "h0": "El valor promedio es igual entre SECOP I, SECOP II y SECOP Integrado.",
        "h1": "Al menos una fuente tiene un valor promedio diferente.",
        "interp_sig": "Las fuentes capturan procesos con características distintas: SECOP II tiende a contratos de mayor valor que SECOP I, reflejando la migración gradual del sistema.",
        "interp_nosig": "Las tres fuentes reportan valores similares.",
    },
    "sector": {
        "title": "¿El valor de contratos difiere según el sector de gasto? (SECOP II)",
        "h0": "El valor promedio es igual en todos los sectores (Educación, Salud, Transporte, Minas, etc.).",
        "h1": "Al menos un sector tiene un valor promedio diferente.",
        "interp_sig": "Los sectores de gasto público tienen perfiles de contratación distintos: Transporte y Minas manejan contratos de mayor valor que Educación o Deportes.",
        "interp_nosig": "No hay diferencias significativas entre sectores.",
    },
    "modalidad + departamento": {
        "title": "¿La modalidad afecta el valor de forma diferente según el departamento?",
        "h0": "No hay interacción entre modalidad y departamento: el efecto de la modalidad sobre el valor es el mismo en todos los departamentos.",
        "h1": "Existe interacción: el efecto de la modalidad sobre el valor varía según el departamento.",
        "interp_sig": "La modalidad tiene efectos diferentes según el departamento. Algunos departamentos usan modalidades de alto valor más que otros, revelando patrones regionales de contratación.",
        "interp_nosig": "La modalidad actúa igual en todos los departamentos.",
    },
    "modalidad_de_contratacion + tipo_de_contrato": {
        "title": "¿La combinación modalidad × tipo de contrato afecta el valor? (SECOP II)",
        "h0": "No hay interacción entre modalidad y tipo de contrato sobre el valor.",
        "h1": "La combinación de modalidad y tipo de contrato afecta el valor más allá de cada factor individual.",
        "interp_sig": "Ciertas modalidades se asocian preferentemente a tipos de contrato de mayor valor. Por ejemplo, Licitación Pública + Obra genera contratos mucho más costosos que Mínima Cuantía + Suministro.",
        "interp_nosig": "Modalidad y tipo de contrato actúan independientemente.",
    },
}


def find_latest_json():
    files = sorted(OUTPUT_DIR.glob("anova_report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No se encontró reporte JSON en anova/output/")
    return files[0]


def p_display(p):
    if not isinstance(p, (int, float)):
        return "N/A"
    if p == 0.0:
        return "&lt; 2.2e-16"
    if p < 1e-10:
        return f"{p:.2e}"
    if p < 0.0001:
        return f"{p:.2e}"
    return f"{p:.6f}"


def format_cop(val):
    if not isinstance(val, (int, float)):
        return "N/A"
    if val >= 1e9:
        return f"${val/1e9:,.2f} mil M"
    elif val >= 1e6:
        return f"${val/1e6:,.1f} M"
    elif val >= 1e3:
        return f"${val/1e3:,.0f} K"
    return f"${val:,.0f}"


def generate_html():
    json_path = find_latest_json()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("anova_results", [])
    tukey_results = data.get("tukey_results", [])
    charts_map = data.get("charts", {})
    timestamp = data.get("timestamp", datetime.now().isoformat())

    tukey_by_col = {t.get("group_col"): t for t in tukey_results if "group_col" in t}

    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Análisis ANOVA — Contratación Pública Colombiana</title>
<style>
:root {{ --bg:#0f1117; --card:#1a1d27; --border:#2a2d3a; --text:#e4e4e7; --muted:#a1a1aa; --accent:#6366f1; --green:#22c55e; --red:#ef4444; --yellow:#eab308; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
.container {{ max-width:1100px; margin:0 auto; padding:2rem 1.5rem; }}
header {{ text-align:center; padding:3rem 0 2rem; border-bottom:1px solid var(--border); margin-bottom:2rem; }}
header h1 {{ font-size:2rem; font-weight:700; margin-bottom:0.5rem; }}
header h1 span {{ color:var(--accent); }}
header p {{ color:var(--muted); font-size:1.05rem; }}
.meta {{ margin-top:1rem; font-size:0.85rem; color:var(--muted); }}
.section-num {{ display:inline-block; background:var(--accent); color:#fff; width:32px; height:32px; border-radius:50%; text-align:center; line-height:32px; font-weight:700; font-size:0.9rem; margin-right:0.5rem; }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:1.5rem; margin-bottom:2rem; }}
.card-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem; }}
.card-header h3 {{ font-size:1.15rem; font-weight:600; }}
.badge {{ padding:0.25rem 0.75rem; border-radius:9999px; font-size:0.8rem; font-weight:600; }}
.badge-reject {{ background:rgba(239,68,68,0.15); color:var(--red); border:1px solid rgba(239,68,68,0.3); }}
.badge-fail {{ background:rgba(34,197,94,0.15); color:var(--green); border:1px solid rgba(34,197,94,0.3); }}
.hypotheses {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin:1rem 0; }}
.hypothesis {{ padding:1rem; border-radius:8px; border-left:3px solid; }}
.h0 {{ background:rgba(239,68,68,0.05); border-color:var(--red); }}
.h1 {{ background:rgba(99,102,241,0.05); border-color:var(--accent); }}
.hypothesis strong {{ font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; }}
.h0 strong {{ color:var(--red); }}
.h1 strong {{ color:var(--accent); }}
.hypothesis p {{ margin-top:0.35rem; font-size:0.9rem; color:var(--muted); }}
.stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:0.75rem; margin:1rem 0; }}
.stat {{ background:rgba(99,102,241,0.05); border:1px solid var(--border); border-radius:8px; padding:0.75rem 1rem; text-align:center; }}
.stat-label {{ font-size:0.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.05em; }}
.stat-value {{ font-size:1.2rem; font-weight:700; margin-top:0.25rem; }}
.stat-value.pval {{ color:var(--yellow); }}
.decision {{ padding:1rem; border-radius:8px; margin:1rem 0; font-size:0.95rem; }}
.decision-reject {{ background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2); }}
.decision-fail {{ background:rgba(34,197,94,0.08); border:1px solid rgba(34,197,94,0.2); }}
.decision strong {{ display:block; margin-bottom:0.25rem; }}
.dataset-info {{ font-size:0.8rem; color:var(--muted); background:rgba(0,0,0,0.2); padding:0.5rem 0.75rem; border-radius:6px; margin:0.5rem 0 1rem; }}
.charts-row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(480px,1fr)); gap:1rem; margin:1rem 0; }}
.charts-row img {{ width:100%; border-radius:8px; border:1px solid var(--border); cursor:zoom-in; transition:opacity 0.2s; }}
.charts-row img:hover {{ opacity:0.85; }}
.lightbox {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.92); z-index:9999; justify-content:center; align-items:center; cursor:zoom-out; }}
.lightbox.active {{ display:flex; }}
.lightbox img {{ max-width:95%; max-height:95%; border-radius:8px; box-shadow:0 0 40px rgba(0,0,0,0.5); }}
.lightbox-close {{ position:absolute; top:1rem; right:1.5rem; color:#fff; font-size:2rem; cursor:pointer; opacity:0.7; }}
.lightbox-close:hover {{ opacity:1; }}
.means-table {{ width:100%; border-collapse:collapse; margin-top:0.75rem; font-size:0.85rem; }}
.means-table th {{ text-align:left; padding:0.4rem 0.6rem; border-bottom:2px solid var(--border); color:var(--muted); font-size:0.75rem; text-transform:uppercase; }}
.means-table td {{ padding:0.4rem 0.6rem; border-bottom:1px solid var(--border); }}
.means-table .bar-cell {{ width:25%; }}
.bar {{ height:6px; background:var(--accent); border-radius:3px; }}
.tukey-section {{ margin-top:1rem; padding-top:0.75rem; border-top:1px solid var(--border); }}
.tukey-section h4 {{ font-size:0.9rem; margin-bottom:0.5rem; color:var(--muted); }}
.tukey-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:0.4rem; max-height:250px; overflow-y:auto; }}
.tukey-item {{ display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0.6rem; border-radius:6px; font-size:0.8rem; background:rgba(0,0,0,0.2); }}
.tukey-item.sig {{ border-left:3px solid var(--red); }}
.tukey-item.nosig {{ border-left:3px solid var(--green); }}
details summary {{ cursor:pointer; color:var(--muted); font-size:0.85rem; padding:0.5rem 0; }}
footer {{ text-align:center; padding:2rem 0; margin-top:2rem; border-top:1px solid var(--border); color:var(--muted); font-size:0.8rem; }}
</style>
</head>
<body>
<div class="container">
<header>
<h1>Análisis <span>ANOVA</span> — Contratación Pública Colombiana</h1>
<p>¿Existen diferencias estadísticamente significativas en el valor de contratos entre grupos?</p>
<div class="meta">Generado: {datetime.fromisoformat(timestamp).strftime("%d/%m/%Y %H:%M")} · Datos: {json_path.name}</div>
</header>
""")

    # ── Summary table ──
    parts.append("""<h2 style="margin-bottom:1rem">Resumen de Hipótesis</h2>
<table style="width:100%;border-collapse:collapse;margin-bottom:2rem;font-size:0.9rem;">
<tr><th style="background:var(--accent);color:#fff;padding:0.6rem 0.8rem;text-align:left">#</th>
<th style="background:var(--accent);color:#fff;padding:0.6rem 0.8rem;text-align:left">Hipótesis</th>
<th style="background:var(--accent);color:#fff;padding:0.6rem 0.8rem;text-align:left">Dataset</th>
<th style="background:var(--accent);color:#fff;padding:0.6rem 0.8rem;text-align:left">F</th>
<th style="background:var(--accent);color:#fff;padding:0.6rem 0.8rem;text-align:left">p-value</th>
<th style="background:var(--accent);color:#fff;padding:0.6rem 0.8rem;text-align:left">Decisión</th></tr>
""")
    for i, r in enumerate(results, 1):
        if "error" in r and len(r) == 1:
            continue
        var = r.get("group_col", r.get("factors", ""))
        hypo = HYPOTHESES.get(var, {})
        title = hypo.get("title", var)
        ds = r.get("dataset", "")
        f_val = r.get("f_statistic", "N/A")
        p_val = p_display(r.get("p_value"))
        sig = r.get("significant")
        decision = "Rechazar H₀" if sig else "No rechazar H₀"
        parts.append(f'<tr><td style="padding:0.5rem 0.8rem;border-bottom:1px solid var(--border)">{i}</td><td style="padding:0.5rem 0.8rem;border-bottom:1px solid var(--border)">{title}</td><td style="padding:0.5rem 0.8rem;border-bottom:1px solid var(--border);font-size:0.8rem;color:var(--muted)">{ds[:50]}...</td><td style="padding:0.5rem 0.8rem;border-bottom:1px solid var(--border)">{f_val}</td><td style="padding:0.5rem 0.8rem;border-bottom:1px solid var(--border);font-weight:700;color:var(--yellow)">{p_val}</td><td style="padding:0.5rem 0.8rem;border-bottom:1px solid var(--border)"><strong>{decision}</strong></td></tr>')
    parts.append("</table>")

    # ── Detailed cards per hypothesis ──
    for r in results:
        if "error" in r and len(r) == 1:
            continue

        key = r.get("group_col", r.get("factors", ""))
        hypo = HYPOTHESES.get(key, {})
        title = hypo.get("title", f"ANOVA: {key}")
        h0 = hypo.get("h0", "")
        h1 = hypo.get("h1", "")
        interp_sig = hypo.get("interp_sig", "")
        interp_nosig = hypo.get("interp_nosig", "")
        sig = r.get("significant")
        f_val = r.get("f_statistic", "N/A")
        p_val_raw = r.get("p_value")
        p_val = p_display(p_val_raw)
        p_display_val = r.get("p_value_display", p_val)
        ds = r.get("dataset", "")
        n_groups = r.get("n_groups", "")
        n_total = r.get("n_total", r.get("n_obs", ""))
        r_sq = r.get("r_squared")
        means = r.get("group_means_cop", {})
        is_twoway = r.get("test") == "Two-way ANOVA"

        n_groups_display = n_groups if n_groups else "— (interacción)"

        decision_cls = "decision-reject" if sig else "decision-fail"
        decision_badge = "badge-reject" if sig else "badge-fail"
        decision_text = "Se rechaza H₀" if sig else "No se rechaza H₀"
        interp = interp_sig if sig else interp_nosig
        p_cmp = "&lt;" if isinstance(p_val_raw, (int, float)) and p_val_raw < 0.05 else "&ge;"

        sorted_means = sorted(means.items(), key=lambda x: x[1], reverse=True) if means else []
        max_val = sorted_means[0][1] if sorted_means else 1
        means_rows = ""
        for name, val in sorted_means:
            pct = (val / max_val * 100) if max_val else 0
            means_rows += f'<tr><td>{name}</td><td>{format_cop(val)}</td><td class="bar-cell"><div class="bar" style="width:{pct:.1f}%"></div></td></tr>'

        tukey = tukey_by_col.get(key)
        tukey_html = ""
        if tukey and not is_twoway:
            comps = tukey.get("comparisons", [])[:20]
            comp_items = ""
            for c in comps:
                cls = "sig" if c["significant"] else "nosig"
                comp_items += f'<div class="tukey-item {cls}"><span>{c["group_1"]} vs {c["group_2"]}</span><span style="font-weight:600">p={c["p_adj"]:.6f} {"✗ sig" if c["significant"] else "○"}</span></div>'
            tukey_html = f"""<div class="tukey-section">
<h4>Post-hoc Tukey HSD — {tukey.get('n_comparisons',0)} comparaciones ({tukey.get('significant_comparisons',0)} significativas)</h4>
<div class="tukey-grid">{comp_items}</div>
</div>"""

        charts = charts_map.get(key, [])
        charts_html = ""
        if charts:
            imgs = "".join(f'<img src="{c}" alt="{c}" class="zoomable">' for c in charts if c)
            charts_html = f'<div class="charts-row">{imgs}</div>'

        extra_stats = ""
        if r_sq is not None:
            extra_stats = f'<div class="stat"><div class="stat-label">R²</div><div class="stat-value">{r_sq}</div></div>'

        parts.append(f"""<div class="card">
<div class="card-header">
<h3><span class="section-num">{results.index(r)+1}</span>{title}</h3>
<span class="badge {decision_badge}">{decision_text}</span>
</div>
<div class="dataset-info">Dataset: {ds}</div>
<div class="hypotheses">
<div class="hypothesis h0"><strong>H₀ (Nula)</strong><p>{h0}</p></div>
<div class="hypothesis h1"><strong>H₁ (Alternativa)</strong><p>{h1}</p></div>
</div>
<div class="stats-grid">
<div class="stat"><div class="stat-label">Estadístico F</div><div class="stat-value">{f_val}</div></div>
<div class="stat"><div class="stat-label">p-value</div><div class="stat-value pval">{p_display_val}</div></div>
<div class="stat"><div class="stat-label">Decisión (α=0.05)</div><div class="stat-value" style="font-size:0.95rem">{decision_text}</div></div>
<div class="stat"><div class="stat-label">N grupos</div><div class="stat-value">{n_groups_display}</div></div>
<div class="stat"><div class="stat-label">N observaciones</div><div class="stat-value">{n_total:,}</div></div>
{extra_stats}
</div>
<div class="decision {decision_cls}">
<strong>Decisión: {decision_text} (p {p_cmp} 0.05)</strong>
{interp}
{f'R² = {r_sq}: el modelo explica {float(r_sq)*100:.1f}% de la varianza.' if r_sq is not None else ''}
</div>
{charts_html}
{tukey_html}
{f'<details><summary>Ver medias por grupo ({n_groups} grupos)</summary><table class="means-table"><tr><th>Grupo</th><th>Valor promedio</th><th></th></tr>{means_rows}</table></details>' if means else ''}
</div>""")

    parts.append("""</div>
<div class="lightbox" id="lightbox"><span class="lightbox-close">&times;</span><img src="" alt="Zoom"></div>
<script>
document.addEventListener('click', function(e) {
    var lb = document.getElementById('lightbox');
    if (e.target.classList.contains('zoomable')) {
        lb.querySelector('img').src = e.target.src;
        lb.classList.add('active');
    } else if (lb.classList.contains('active') && (e.target === lb || e.target.classList.contains('lightbox-close'))) {
        lb.classList.remove('active');
    }
});
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') document.getElementById('lightbox').classList.remove('active');
});
</script>
<footer>
<p>Análisis ANOVA — CiviData · Contratación Pública Colombiana (SECOP)</p>
<p>One-way ANOVA: scipy.stats.f_oneway · Two-way ANOVA: statsmodels OLS · Post-hoc: Tukey HSD</p>
<p>Nivel de significancia α = 0.05 · Variable dependiente: log(1 + valor_contrato)</p>
</footer>
</body>
</html>""")

    html = "".join(parts)
    out_path = OUTPUT_DIR / "anova_presentation.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Presentación generada: {out_path}")


if __name__ == "__main__":
    generate_html()
