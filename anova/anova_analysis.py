"""
Análisis ANOVA - Contratación Pública Colombiana (SECOP)

Hipótesis seleccionadas (las más informativas):
  One-way: departamento, modalidad, tipo_contrato, origen (Consolidado) + sector (SECOP II)
  Two-way: modalidad×departamento (Consolidado) + modalidad×tipo_contrato (SECOP II)

Output:
  - Gráficos PNG por hipótesis en anova/output/
  - Reporte JSON con datos completos para presentación HTML
"""

import pandas as pd
import numpy as np
import logging
import json
from pathlib import Path
from datetime import datetime
from itertools import combinations

from scipy.stats import f_oneway

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

import warnings

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("anova/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path("datalake")
CONSOLIDATED_PATH = DATA_DIR / "export/consolidated/secop_consolidado_latest.csv"
SECOP_II_PATH = DATA_DIR / "clean/contratacion/secop_ii_20260428_clean.csv"


# ─── Load ────────────────────────────────────────────────────────────────────


def load_consolidated():
    logger.info(f"Cargando consolidado: {CONSOLIDATED_PATH}")
    df = pd.read_csv(CONSOLIDATED_PATH, low_memory=False)
    df.columns = df.columns.str.lower()
    logger.info(f"  {len(df)} filas, {len(df.columns)} columnas")
    return df


def load_secop_ii():
    logger.info(f"Cargando SECOP II: {SECOP_II_PATH}")
    df = pd.read_csv(SECOP_II_PATH, low_memory=False)
    df.columns = df.columns.str.lower()
    logger.info(f"  {len(df)} filas, {len(df.columns)} columnas")
    return df


# ─── Preprocess ──────────────────────────────────────────────────────────────


DEPTO_NORMALIZE = {
    "bogota d.c.": "Bogotá D.C.",
    "bogota": "Bogotá D.C.",
    "distrito capital de bogota": "Bogotá D.C.",
    "distrito capital de bogotá": "Bogotá D.C.",
    "san andres, providencia y santa catalina": "San Andrés, Providencia Y Santa Catalina",
    "san andres providencia y santa catalina": "San Andrés, Providencia Y Santa Catalina",
    "san andrés providencia y santa catalina": "San Andrés, Providencia Y Santa Catalina",
    "san andrés, providencia y santa catalina": "San Andrés, Providencia Y Santa Catalina",
}

DEPTO_EXCLUDE = {"colombia", "no aplica", "no definido", "sin definir", "sin información"}


def normalize_departamentos(df, col="departamento"):
    if col not in df.columns:
        return df
    df = df.copy()
    df[col] = df[col].map(lambda x: DEPTO_NORMALIZE.get(str(x).strip().lower(), x))
    df = df[~df[col].str.strip().str.lower().isin(DEPTO_EXCLUDE)]
    return df


def preprocess_consolidated(df):
    df = df.copy()
    df["valor_contrato"] = pd.to_numeric(df["valor_contrato"], errors="coerce")
    df = df[df["valor_contrato"] > 0]
    df["log_valor"] = np.log1p(df["valor_contrato"])
    for col in ["departamento", "modalidad", "tipo_contrato", "origen"]:
        if col in df.columns:
            df[col] = df[col].fillna("Sin definir").astype(str).str.strip()
            df[col] = df[col].replace({"": "Sin definir", "nan": "Sin definir"})
    df = normalize_departamentos(df, "departamento")
    return df


def preprocess_secop_ii(df):
    df = df.copy()
    valor_col = "valor_del_contrato" if "valor_del_contrato" in df.columns else "valor_contrato"
    df["valor_contrato"] = pd.to_numeric(df[valor_col], errors="coerce")
    df = df[df["valor_contrato"] > 0]
    df["log_valor"] = np.log1p(df["valor_contrato"])
    for col in ["departamento", "sector", "rama", "tipo_de_contrato",
                "modalidad_de_contratacion", "estado_contrato"]:
        if col in df.columns:
            df[col] = df[col].fillna("Sin definir").astype(str).str.strip()
            df[col] = df[col].replace({"": "Sin definir", "nan": "Sin definir"})
    df = normalize_departamentos(df, "departamento")
    return df


# ─── Helpers ─────────────────────────────────────────────────────────────────


def filter_groups(df, group_col, value_col="log_valor", min_groups=3, min_n=10):
    group_sizes = df.groupby(group_col)[value_col].size()
    valid = group_sizes[group_sizes >= min_n].index.tolist()
    if len(valid) < min_groups:
        return None, f"Solo {len(valid)} grupos válidos (mínimo {min_groups})"
    return df[df[group_col].isin(valid)], None


def p_value_str(p):
    if not isinstance(p, (int, float)):
        return "N/A"
    if p == 0.0:
        return "&lt; 2.2e-16"
    if p < 1e-10:
        return f"{p:.2e}"
    if p < 0.0001:
        return f"{p:.2e}"
    return f"{p:.6f}"


# ─── ANOVA Tests ─────────────────────────────────────────────────────────────


def one_way_anova(df, group_col, value_col="log_valor", min_n=10):
    filtered, err = filter_groups(df, group_col, value_col, min_n=min_n)
    if filtered is None:
        return {"group_col": group_col, "error": err}

    groups = [g for _, g in filtered.groupby(group_col)]
    group_values = [g[value_col].values for g in groups]
    f_stat, p_value = f_oneway(*group_values)

    group_sizes = {name: int(len(g)) for name, g in filtered.groupby(group_col)}
    group_means = {
        name: round(float(np.expm1(g[value_col].mean())), 2)
        for name, g in filtered.groupby(group_col)
    }

    return {
        "test": "One-way ANOVA",
        "group_col": group_col,
        "f_statistic": round(float(f_stat), 4),
        "p_value": float(p_value),
        "p_value_display": p_value_str(p_value),
        "significant": bool(p_value < 0.05),
        "n_groups": len(groups),
        "n_total": sum(len(g) for g in groups),
        "group_sizes": group_sizes,
        "group_means_cop": group_means,
    }


def two_way_anova(df, col_a, col_b, value_col="log_valor", min_n=5):
    try:
        import statsmodels.formula.api as smf

        col_a_safe = col_a.replace(" ", "_").replace("-", "_")
        col_b_safe = col_b.replace(" ", "_").replace("-", "_")
        df_work = df[[col_a, col_b, value_col]].copy()
        df_work[col_a_safe] = df_work[col_a].astype(str)
        df_work[col_b_safe] = df_work[col_b].astype(str)

        grouped = df_work.groupby([col_a_safe, col_b_safe])[value_col].filter(
            lambda x: len(x) >= min_n
        )
        if grouped.empty:
            return {"error": "No hay grupos con tamaño suficiente"}
        df_work = df_work.loc[grouped.index]

        formula = f"{value_col} ~ C({col_a_safe}) + C({col_b_safe}) + C({col_a_safe}):C({col_b_safe})"
        model = smf.ols(formula, data=df_work).fit()

        p_val = model.f_pvalue
        n_combinations = df_work.groupby([col_a_safe, col_b_safe]).ngroups
        return {
            "test": "Two-way ANOVA",
            "factors": f"{col_a} + {col_b}",
            "r_squared": round(float(model.rsquared), 4),
            "f_statistic": round(float(model.fvalue), 4),
            "p_value": float(p_val),
            "p_value_display": p_value_str(p_val),
            "significant": bool(p_val < 0.05),
            "n_obs": len(df_work),
            "n_groups": n_combinations,
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Tukey Post-hoc ─────────────────────────────────────────────────────────


def tukey_posthoc(df, group_col, value_col="log_valor", top_n=10):
    try:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd

        filtered, err = filter_groups(df, group_col, value_col, min_n=10)
        if filtered is None:
            return {"error": err}

        group_sizes = filtered.groupby(group_col).size().sort_values(ascending=False)
        top_groups = group_sizes.head(top_n).index.tolist()
        sub = filtered[filtered[group_col].isin(top_groups)].copy()
        sub[group_col] = sub[group_col].astype(str)

        tukey = pairwise_tukeyhsd(
            sub[value_col].values, sub[group_col].values, alpha=0.05
        )
        groups = list(tukey.groupsunique)
        results = []
        for idx, (g1, g2) in enumerate(combinations(groups, 2)):
            if idx < len(tukey.pvalues):
                results.append(
                    {
                        "group_1": str(g1),
                        "group_2": str(g2),
                        "mean_diff": round(float(tukey.meandiffs[idx]), 4),
                        "p_adj": round(float(tukey.pvalues[idx]), 6),
                        "significant": bool(tukey.reject[idx]),
                    }
                )

        return {
            "group_col": group_col,
            "n_comparisons": len(results),
            "significant_comparisons": sum(1 for r in results if r["significant"]),
            "comparisons": results[:50],
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Visualizations ─────────────────────────────────────────────────────────


def plot_boxplot(df, group_col, value_col, title, filename, max_groups=15):
    filtered, _ = filter_groups(df, group_col, value_col, min_n=10)
    if filtered is None:
        return None
    group_sizes = filtered.groupby(group_col).size().sort_values(ascending=False)
    top = group_sizes.head(max_groups).index.tolist()
    sub = filtered[filtered[group_col].isin(top)]

    fig, ax = plt.subplots(figsize=(14, 7))
    sns.boxplot(
        data=sub,
        x=group_col,
        y=value_col,
        ax=ax,
        palette="Set2",
        showfliers=False,
        linewidth=0.8,
    )
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(group_col.replace("_", " ").title(), fontsize=11)
    ax.set_ylabel("Valor del contrato (escala logarítmica)", fontsize=11)
    ax.tick_params(axis="x", rotation=45, labelsize=9)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    return filename


def plot_bar_means(df, group_col, value_col, title, filename, max_groups=15):
    filtered, _ = filter_groups(df, group_col, value_col, min_n=10)
    if filtered is None:
        return None
    group_sizes = filtered.groupby(group_col).size().sort_values(ascending=False)
    top = group_sizes.head(max_groups).index.tolist()
    sub = filtered[filtered[group_col].isin(top)]

    fig, ax = plt.subplots(figsize=(14, 7))
    sns.barplot(data=sub, x=group_col, y=value_col, ax=ax,
                palette="viridis", errorbar="ci", capsize=0.1)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(group_col.replace("_", " ").title(), fontsize=11)
    ax.set_ylabel("Valor del contrato (escala logarítmica)", fontsize=11)
    ax.tick_params(axis="x", rotation=45, labelsize=9)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    return filename


def plot_interaction(df, col_a, col_b, value_col, title, filename, top_a=8, top_b=8):
    """Interaction plot: mean value per combination of two factors."""
    sub_a = (
        df.groupby(col_a)[value_col]
        .size()
        .sort_values(ascending=False)
        .head(top_a)
        .index
    )
    sub_b = (
        df.groupby(col_b)[value_col]
        .size()
        .sort_values(ascending=False)
        .head(top_b)
        .index
    )
    data = df[(df[col_a].isin(sub_a)) & (df[col_b].isin(sub_b))].copy()

    if data.empty:
        return None

    pivot = data.groupby([col_a, col_b])[value_col].mean().unstack()

    fig, ax = plt.subplots(figsize=(14, 7))
    for col_name in pivot.columns:
        ax.plot(
            pivot.index,
            pivot[col_name],
            marker="o",
            linewidth=2,
            label=str(col_name)[:30],
        )
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(col_a.replace("_", " ").title(), fontsize=11)
    ax.set_ylabel("Valor del contrato (escala logarítmica)", fontsize=11)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.legend(fontsize=8, loc="upper right", framealpha=0.9)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    return filename


# ─── Main ────────────────────────────────────────────────────────────────────


def run():
    logger.info("=" * 60)
    logger.info("ANÁLISIS ANOVA - CONTRATACIÓN PÚBLICA (SECOP)")
    logger.info("=" * 60)

    consolidated = preprocess_consolidated(load_consolidated())
    secop_ii = preprocess_secop_ii(load_secop_ii())

    all_results = []
    all_tukey = []

    # ── HYPOTHESES TO TEST (filtered to most informative) ──

    tests_oneway = [
        {
            "col": "departamento",
            "df": consolidated,
            "dataset": "Consolidado (SECOP I + II + Integrado, 133,371 registros)",
        },
        {
            "col": "modalidad",
            "df": consolidated,
            "dataset": "Consolidado (SECOP I + II + Integrado, 133,371 registros)",
        },
        {
            "col": "tipo_contrato",
            "df": consolidated,
            "dataset": "Consolidado (SECOP I + II + Integrado, 133,371 registros)",
        },
        {
            "col": "origen",
            "df": consolidated,
            "dataset": "Consolidado (SECOP I + II + Integrado, 133,371 registros)",
        },
        {
            "col": "sector",
            "df": secop_ii,
            "dataset": "SECOP II (48,310 registros con sector clasificado)",
        },
    ]

    tests_twoway = [
        {
            "col_a": "modalidad",
            "col_b": "departamento",
            "df": consolidated,
            "dataset": "Consolidado (SECOP I + II + Integrado, 133,371 registros)",
        },
        {
            "col_a": "modalidad_de_contratacion",
            "col_b": "tipo_de_contrato",
            "df": secop_ii,
            "dataset": "SECOP II (48,310 registros)",
        },
    ]

    # ── Run One-way ANOVA ──
    logger.info("\n--- One-way ANOVA ---")
    for t in tests_oneway:
        col = t["col"]
        if col not in t["df"].columns:
            continue
        logger.info(f"  ANOVA: {col} [{t['dataset'][:40]}...]")
        res = one_way_anova(t["df"], col)
        res["dataset"] = t["dataset"]
        all_results.append(res)
        sig = res.get("significant", False)
        logger.info(
            f"    F={res.get('f_statistic')}, p={res.get('p_value_display')}, "
            f"significativo={'Sí' if sig else 'No'}"
        )

    # ── Run Two-way ANOVA ──
    logger.info("\n--- Two-way ANOVA ---")
    for t in tests_twoway:
        if t["col_a"] not in t["df"].columns or t["col_b"] not in t["df"].columns:
            continue
        logger.info(f"  Two-way: {t['col_a']} x {t['col_b']}")
        res = two_way_anova(t["df"], t["col_a"], t["col_b"])
        res["dataset"] = t["dataset"]
        all_results.append(res)
        logger.info(
            f"    F={res.get('f_statistic')}, p={res.get('p_value_display')}, "
            f"R²={res.get('r_squared')}"
        )

    # ── Tukey Post-hoc (only for oneway with significant results) ──
    logger.info("\n--- Post-hoc Tukey HSD ---")
    tukey_map = {}
    for r in all_results:
        if r.get("test") != "One-way ANOVA" or not r.get("significant"):
            continue
        col = r.get("group_col")
        df_src = consolidated if col in consolidated.columns else secop_ii
        logger.info(f"  Tukey: {col}")
        tres = tukey_posthoc(df_src, col)
        tukey_map[col] = tres
        all_tukey.append({"group_col": col, **tres})
        n_sig = tres.get("significant_comparisons", 0)
        logger.info(f"    {n_sig} significativas de {tres.get('n_comparisons', 0)}")

    # ── Generate charts PER HYPOTHESIS ──
    logger.info("\n--- Generando gráficos por hipótesis ---")

    chart_map = {}

    for t in tests_oneway:
        col = t["col"]
        df_src = t["df"]
        base = f"{col}_{df_src is consolidated and 'consolidado' or 'secop2'}"

        bp = plot_boxplot(
            df_src,
            col,
            "log_valor",
            f"Distribución por {col.replace('_', ' ').title()}",
            f"boxplot_{base}.png",
        )
        bar = plot_bar_means(
            df_src,
            col,
            "log_valor",
            f"Valor promedio por {col.replace('_', ' ').title()}",
            f"bar_{base}.png",
        )
        charts = [c for c in [bp, bar] if c]
        chart_map[col] = charts
        logger.info(f"  {col}: {charts}")

    for t in tests_twoway:
        ca, cb = t["col_a"], t["col_b"]
        df_src = t["df"]
        base = f"interaction_{ca[:10]}_{cb[:10]}"
        ip = plot_interaction(
            df_src,
            ca,
            cb,
            "log_valor",
            f"Interacción: {ca.replace('_', ' ').title()} × {cb.replace('_', ' ').title()}",
            f"{base}.png",
        )
        key = f"{ca} + {cb}"
        chart_map[key] = [ip] if ip else []
        logger.info(f"  {key}: {[ip]}")

    # ── Save report ──
    logger.info("\n--- Guardando reportes ---")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    report = {
        "timestamp": datetime.now().isoformat(),
        "anova_results": all_results,
        "tukey_results": all_tukey,
        "charts": chart_map,
    }
    with open(OUTPUT_DIR / f"anova_report_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"  JSON: anova_report_{ts}.json")

    csv_rows = []
    for r in all_results:
        if "error" in r and len(r) == 1:
            continue
        csv_rows.append(
            {
                "test": r.get("test", ""),
                "variable": r.get("group_col", r.get("factors", "")),
                "dataset": r.get("dataset", ""),
                "f_statistic": r.get("f_statistic", ""),
                "p_value": r.get("p_value_display", ""),
                "significant": "Sí" if r.get("significant") else "No",
                "n_groups": r.get("n_groups", ""),
                "n_total": r.get("n_total", r.get("n_obs", "")),
            }
        )
    pd.DataFrame(csv_rows).to_csv(OUTPUT_DIR / f"anova_report_{ts}.csv", index=False)
    logger.info(f"  CSV: anova_report_{ts}.csv")

    logger.info("\n" + "=" * 60)
    logger.info("ANÁLISIS COMPLETADO")
    logger.info(f"Resultados en: {OUTPUT_DIR}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
