import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    aplicar_estilo, render_sidebar_filtros, executar_query, montar_where,
    kpi_card, kpi_sublinha, layout_grafico, page_header, CORES_GRAFICO,
)

st.set_page_config(page_title="Metas - RH Analytics", page_icon="", layout="wide")
aplicar_estilo()

LAYOUT_BR = dict(separators=",.")


def fmt_br(valor, decimais=0):
    if valor is None:
        valor = 0
    s = f"{valor:,.{decimais}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


with st.sidebar:
    filtros = render_sidebar_filtros("metas")

page_header("Metas", "Metas vs realizado por indicador - DW RH")

# vw_metas_vs_realizado nao tem departamento/funcao
filtros_metas = dict(filtros)
filtros_metas["departamentos"] = []
filtros_metas["funcoes"] = []
# ── Protecao de performance ─────────────────────────────────────────────
# Garante que toda consulta tenha um filtro de ano antes de agregar, evitando
# escanear a tabela fato inteira. Usa o ano selecionado ou o mais recente.
if filtros_metas.get("anos"):
    ano_ref = max(int(a) for a in filtros_metas["anos"])
else:
    ano_res = executar_query("SELECT MAX(ano) AS ano FROM vw_metas_vs_realizado WHERE ano IS NOT NULL")
    ano_ref = (ano_res or [{}])[0].get("ano")
    if ano_ref:
        st.info(f"Exibindo dados de {ano_ref} (ano mais recente). Selecione um ano no filtro para ver outro periodo.")

filtros_metas = dict(filtros_metas)
filtros_metas["anos"] = [str(ano_ref)] if ano_ref else []

where = montar_where(filtros_metas)

if not ano_ref:
    st.warning("Nao foi possivel determinar um ano de referencia. Verifique a conexao com o banco.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────────
kpi_query = f"""
    SELECT
        AVG(metas_atingidas)        AS metas_atingidas_media,
        AVG(realizado_turnover)     AS turnover_realizado,
        AVG(meta_turnover)          AS turnover_meta,
        SUM(realizado_admissoes)    AS admissoes_realizado,
        SUM(meta_admissoes)         AS admissoes_meta
    FROM vw_metas_vs_realizado
    {where}
"""
k = (executar_query(kpi_query) or [{}])[0]

metas_atingidas_media = k.get("metas_atingidas_media") or 0
turnover_realizado     = k.get("turnover_realizado") or 0
turnover_meta           = k.get("turnover_meta") or 0
admissoes_realizado     = k.get("admissoes_realizado") or 0
admissoes_meta           = k.get("admissoes_meta") or 0

pct_admissoes = (admissoes_realizado / admissoes_meta * 100 - 100) if admissoes_meta else None

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Media de Metas Atingidas", fmt_br(metas_atingidas_media, 1), sublinha=kpi_sublinha(), icon="META")
with col2:
    kpi_card("Turnover Realizado", f"{turnover_realizado:.2f}%",
             sublinha=kpi_sublinha("Meta", value=f"{turnover_meta:.2f}%"), icon="TO")
with col3:
    kpi_card("Admissoes Realizadas", fmt_br(admissoes_realizado),
             sublinha=kpi_sublinha("vs Meta", pct=pct_admissoes), icon="ADM")
with col4:
    classif_query = f"""
        SELECT classificacao_geral, COUNT(*) AS qtde
        FROM vw_metas_vs_realizado {where}
        GROUP BY classificacao_geral ORDER BY qtde DESC LIMIT 1
    """
    top_class = (executar_query(classif_query) or [{}])
    classif_top = top_class[0].get("classificacao_geral") if top_class else "N/D"
    kpi_card("Classificacao Mais Frequente", classif_top or "N/D", sublinha=kpi_sublinha(), icon="CLS")

st.markdown("<br>", unsafe_allow_html=True)

# ── Linha 1: Status por indicador ──────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Status das Metas por Indicador</div>', unsafe_allow_html=True)

status_cols = ["status_admissoes", "status_demissoes", "status_turnover", "status_horas_extras", "status_treinamento"]
nomes_indicadores = ["Admissoes", "Demissoes", "Turnover", "Horas Extras", "Treinamento"]

dados_status = []
for col, nome in zip(status_cols, nomes_indicadores):
    q = f"""
        SELECT {col} AS status, COUNT(*) AS qtde
        FROM vw_metas_vs_realizado {where}
        GROUP BY {col}
    """
    res = executar_query(q)
    for r in res:
        dados_status.append({"indicador": nome, "status": r["status"], "qtde": r["qtde"]})

df_status = pd.DataFrame(dados_status)

if not df_status.empty:
    cores_status = {"Atingida": "#48bb78", "Nao Atingida": "#f56565", "Parcial": "#f6ad55"}
    fig = go.Figure()
    for status_val in df_status["status"].unique():
        sub = df_status[df_status["status"] == status_val]
        fig.add_trace(go.Bar(
            x=sub["indicador"], y=sub["qtde"], name=str(status_val),
            marker_color=cores_status.get(status_val, "#4d7cfe"),
        ))
    fig.update_layout(**layout_grafico(showlegend=True, height=360, barmode="stack"), **LAYOUT_BR)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Sem dados.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Linha 2: Turnover realizado vs meta + Classificacao geral ──────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">Turnover Realizado vs Meta por Mes ({ano_ref})</div>', unsafe_allow_html=True)

    filtros_evol = dict(filtros_metas); filtros_evol["meses"] = []
    w_evol = montar_where(filtros_evol)

    df_evol = pd.DataFrame(executar_query(f"""
        SELECT mes, nome_mes, AVG(realizado_turnover) AS realizado, AVG(meta_turnover) AS meta
        FROM vw_metas_vs_realizado {w_evol}
        GROUP BY mes, nome_mes ORDER BY mes
    """))

    if not df_evol.empty:
        df_evol["realizado_fmt"] = df_evol["realizado"].apply(lambda v: f"{v:.2f}%")
        df_evol["meta_fmt"] = df_evol["meta"].apply(lambda v: f"{v:.2f}%")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_evol["nome_mes"], y=df_evol["realizado"], mode="lines+markers+text",
            name="Realizado", line=dict(color="#1a2b5c", width=2), marker=dict(color="#1a2b5c", size=6),
            text=df_evol["realizado_fmt"], textposition="top center", textfont=dict(color="#ffffff", size=10),
        ))
        fig.add_trace(go.Scatter(
            x=df_evol["nome_mes"], y=df_evol["meta"], mode="lines+markers+text",
            name="Meta", line=dict(color="#4d7cfe", width=2, dash="dash"), marker=dict(color="#4d7cfe", size=6),
            text=df_evol["meta_fmt"], textposition="bottom center", textfont=dict(color="#ffffff", size=10),
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=340), **LAYOUT_BR)
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Classificacao Geral</div>', unsafe_allow_html=True)

    df_class = pd.DataFrame(executar_query(f"""
        SELECT classificacao_geral, COUNT(*) AS qtde
        FROM vw_metas_vs_realizado {where}
        GROUP BY classificacao_geral ORDER BY qtde DESC
    """))

    if not df_class.empty:
        fig = go.Figure(go.Pie(
            labels=df_class["classificacao_geral"], values=df_class["qtde"], hole=0.55,
            marker=dict(colors=CORES_GRAFICO, line=dict(color="#0b1437", width=2)),
            textfont=dict(color="#ffffff", size=10), textposition="inside",
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=340), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Linha 3: Metas atingidas por loja ───────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Metas Atingidas por Loja (Top 15)</div>', unsafe_allow_html=True)

df_loja = pd.DataFrame(executar_query(f"""
    SELECT nome_loja, AVG(metas_atingidas) AS metas
    FROM vw_metas_vs_realizado {where}
    GROUP BY nome_loja ORDER BY metas DESC LIMIT 15
"""))

if not df_loja.empty:
    df_loja = df_loja.sort_values("metas")
    df_loja["metas_fmt"] = df_loja["metas"].apply(lambda v: fmt_br(v, 1))
    fig = px.bar(df_loja, x="metas", y="nome_loja", orientation="h",
                 color_discrete_sequence=[CORES_GRAFICO[0]], text="metas_fmt")
    fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
    fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Sem dados.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Tabela detalhada ──────────────────────────────────────────────────────
with st.expander("Ver dados detalhados"):
    df_det = pd.DataFrame(executar_query(f"""
        SELECT ano_mes, nome_loja, meta_turnover, realizado_turnover, status_turnover,
               meta_admissoes, realizado_admissoes, status_admissoes,
               metas_atingidas, classificacao_geral
        FROM vw_metas_vs_realizado {where}
        ORDER BY ano_mes DESC LIMIT 500
    """))
    if not df_det.empty:
        st.dataframe(df_det, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados.")
