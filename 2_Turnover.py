import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    aplicar_estilo, render_sidebar_filtros, executar_query, montar_where,
    kpi_card, kpi_sublinha, layout_grafico, page_header, CORES_GRAFICO,
)

st.set_page_config(page_title="Turnover - RH Analytics", page_icon="", layout="wide")
aplicar_estilo()

LAYOUT_BR = dict(separators=",.")


def fmt_br(valor, decimais=0):
    """Formata numero no padrao brasileiro: ponto para milhar, virgula para decimal."""
    if valor is None:
        valor = 0
    s = f"{valor:,.{decimais}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


with st.sidebar:
    filtros = render_sidebar_filtros("turnover")

page_header("Turnover", "Analise de rotatividade de colaboradores - DW RH")

# vw_turnover_mensal nao tem departamento/funcao -> remove esses filtros do WHERE desta pagina
alias_map = {}
filtros_turnover = dict(filtros)
filtros_turnover["departamentos"] = []
filtros_turnover["funcoes"] = []
# ── Protecao de performance ─────────────────────────────────────────────
# Garante que toda consulta tenha um filtro de ano antes de agregar, evitando
# escanear a tabela fato inteira. Usa o ano selecionado ou o mais recente.
if filtros_turnover.get("anos"):
    ano_ref = max(int(a) for a in filtros_turnover["anos"])
else:
    ano_res = executar_query("SELECT MAX(ano) AS ano FROM vw_turnover_mensal WHERE ano IS NOT NULL")
    ano_ref = (ano_res or [{}])[0].get("ano")
    if ano_ref:
        st.info(f"Exibindo dados de {ano_ref} (ano mais recente). Selecione um ano no filtro para ver outro periodo.")

filtros_turnover = dict(filtros_turnover)
filtros_turnover["anos"] = [str(ano_ref)] if ano_ref else []

where = montar_where(filtros_turnover)

if not ano_ref:
    st.warning("Nao foi possivel determinar um ano de referencia. Verifique a conexao com o banco.")
    st.stop()


# ── KPIs ─────────────────────────────────────────────────────────────────
# Turnover realizado e meta sao taxas (percentuais) -> usar media no periodo filtrado
# Headcount, admissoes e demissoes sao somados no periodo filtrado
totais_query = f"""
    SELECT
        AVG(turnover_realizado) AS turnover_realizado,
        AVG(turnover_meta)      AS turnover_meta,
        SUM(admissoes)          AS admissoes,
        SUM(demissoes)          AS demissoes
    FROM vw_turnover_mensal
    {where}
"""
totais = executar_query(totais_query)
t = totais[0] if totais else {}

turnover_realizado = t.get("turnover_realizado") or 0
turnover_meta = t.get("turnover_meta") or 0
admissoes = t.get("admissoes") or 0
demissoes = t.get("demissoes") or 0

# ── Turnover YoY: compara o ano de referencia (fixado acima) vs ano anterior ──
# filtros_turnover["anos"] ja esta fixo em [ano_ref], entao turnover_realizado
# (calculado mais acima) ja E o turnover do periodo atual.
turnover_periodo_atual = turnover_realizado
turnover_ano_anterior = None

filtros_ant = dict(filtros_turnover)
filtros_ant["anos"] = [str(ano_ref - 1)]
where_ant = montar_where(filtros_ant)
res_ant = executar_query(f"SELECT AVG(turnover_realizado) AS turnover FROM vw_turnover_mensal {where_ant}")
if res_ant and res_ant[0]["turnover"] is not None:
    turnover_ano_anterior = res_ant[0]["turnover"]

# YoY do turnover: queda no turnover (negativo) e bom -> seta para baixo = "up" (verde)
pct_yoy_turnover = None
if turnover_ano_anterior and turnover_periodo_atual is not None:
    pct_yoy_turnover = (turnover_periodo_atual / turnover_ano_anterior - 1) * 100

# Variacao vs meta: turnover realizado abaixo da meta = bom
variacao_vs_meta = None
if turnover_meta:
    variacao_vs_meta = (turnover_realizado / turnover_meta - 1) * 100

saldo = admissoes - demissoes


col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    sub = kpi_sublinha("YoY", pct=pct_yoy_turnover, inverter_cores=True)
    kpi_card("Turnover Realizado", f"{turnover_realizado:.2f}%", icon="TO", sublinha=sub)

with col2:
    sub = kpi_sublinha("vs Realizado", pct=variacao_vs_meta, inverter_cores=True)
    kpi_card("Turnover Meta", f"{turnover_meta:.2f}%", icon="META", sublinha=sub)

with col3:
    kpi_card("Admissoes", fmt_br(admissoes), icon="ADM", sublinha=kpi_sublinha())
with col4:
    kpi_card("Demissoes", fmt_br(demissoes), icon="DEM", sublinha=kpi_sublinha())
with col5:
    delta_tipo = "up" if saldo >= 0 else "down"
    sinal = "+" if saldo >= 0 else ""
    kpi_card("Saldo Admissoes/Demissoes", f"{sinal}{fmt_br(saldo)}", delta_tipo=delta_tipo, icon="SLD",
             sublinha=kpi_sublinha())
with col6:
    headcount_query = f"""
        SELECT AVG(headcount_ativo) AS headcount
        FROM vw_turnover_mensal
        {where}
    """
    hc_res = executar_query(headcount_query)
    headcount_medio = hc_res[0]["headcount"] if hc_res and hc_res[0]["headcount"] else 0
    kpi_card("Headcount Medio", fmt_br(headcount_medio), icon="HC", sublinha=kpi_sublinha())


st.markdown("<br>", unsafe_allow_html=True)


# ── Linha 1: Evolucao mensal Realizado vs Meta + Classificacao ──────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)

    st.markdown(f'<div class="section-title">Turnover Realizado vs Meta por Mes ({ano_ref})</div>', unsafe_allow_html=True)

    filtros_evol = dict(filtros_turnover)
    filtros_evol["meses"] = []
    where_evol = montar_where(filtros_evol)

    evol_query = f"""
        SELECT mes, nome_mes,
               AVG(turnover_realizado) AS realizado,
               AVG(turnover_meta)      AS meta
        FROM vw_turnover_mensal
        {where_evol}
        GROUP BY mes, nome_mes
        ORDER BY mes
    """
    df_evol = pd.DataFrame(executar_query(evol_query))

    if not df_evol.empty:
        df_evol["realizado_fmt"] = df_evol["realizado"].apply(lambda v: f"{v:.2f}%")
        df_evol["meta_fmt"] = df_evol["meta"].apply(lambda v: f"{v:.2f}%")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_evol["nome_mes"], y=df_evol["realizado"],
            mode="lines+markers+text", name="Turnover Realizado",
            line=dict(color="#1a2b5c", width=2),
            marker=dict(color="#1a2b5c", size=6),
            text=df_evol["realizado_fmt"], textposition="top center",
            textfont=dict(color="#ffffff", size=10),
        ))
        fig.add_trace(go.Scatter(
            x=df_evol["nome_mes"], y=df_evol["meta"],
            mode="lines+markers+text", name="Turnover Meta",
            line=dict(color="#4d7cfe", width=2, dash="dash"),
            marker=dict(color="#4d7cfe", size=6),
            text=df_evol["meta_fmt"], textposition="bottom center",
            textfont=dict(color="#ffffff", size=10),
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=340), **LAYOUT_BR)
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados para os filtros selecionados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Classificacao do Turnover</div>', unsafe_allow_html=True)

    class_query = f"""
        SELECT classificacao_turnover, COUNT(*) AS qtde
        FROM vw_turnover_mensal
        {where}
        GROUP BY classificacao_turnover
        ORDER BY qtde DESC
    """
    df_class = pd.DataFrame(executar_query(class_query))

    if not df_class.empty:
        # Cores fixas e bem distintas por classificacao (independente da ordem)
        mapa_cores = {
            "Sem Movimentacao": "#4d7cfe",
            "Saudavel":         "#48bb78",
            "Atencao":          "#f6ad55",
            "Critico":          "#ed64a6",
            "Muito Critico":    "#f56565",
        }
        cores_pizza = [mapa_cores.get(c, "#a0aec0") for c in df_class["classificacao_turnover"]]

        fig = go.Figure(go.Pie(
            labels=df_class["classificacao_turnover"], values=df_class["qtde"],
            hole=0.55,
            marker=dict(colors=cores_pizza, line=dict(color="#0b1437", width=2)),
            textfont=dict(color="#ffffff", size=11),
            textposition="inside",
            insidetextorientation="horizontal",
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=340), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Linha 2: Turnover por loja + Status meta ────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Turnover Medio por Loja (Top 15)</div>', unsafe_allow_html=True)

    loja_query = f"""
        SELECT nome_loja, AVG(turnover_realizado) AS turnover
        FROM vw_turnover_mensal
        {where}
        GROUP BY nome_loja
        ORDER BY turnover DESC
        LIMIT 15
    """
    df_loja = pd.DataFrame(executar_query(loja_query))

    if not df_loja.empty:
        df_loja = df_loja.sort_values("turnover")
        df_loja["turnover_fmt"] = df_loja["turnover"].apply(lambda v: f"{v:.2f}%")
        fig = px.bar(df_loja, x="turnover", y="nome_loja", orientation="h",
                      color_discrete_sequence=[CORES_GRAFICO[0]], text="turnover_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside",
                           textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Status da Meta (Distribuicao)</div>', unsafe_allow_html=True)

    status_query = f"""
        SELECT status_meta, COUNT(*) AS qtde
        FROM vw_turnover_mensal
        {where}
        GROUP BY status_meta
        ORDER BY qtde DESC
    """
    df_status = pd.DataFrame(executar_query(status_query))

    if not df_status.empty:
        df_status = df_status.sort_values("qtde")
        df_status["qtde_fmt"] = df_status["qtde"].apply(lambda v: fmt_br(v))
        fig = px.bar(df_status, x="qtde", y="status_meta", orientation="h",
                      color_discrete_sequence=[CORES_GRAFICO[3]], text="qtde_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside",
                           textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Linha 3: Turnover por regiao ────────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Turnover Medio por Regiao</div>', unsafe_allow_html=True)

regiao_query = f"""
    SELECT regiao, AVG(turnover_realizado) AS realizado, AVG(turnover_meta) AS meta
    FROM vw_turnover_mensal
    {where}
    GROUP BY regiao
    ORDER BY realizado DESC
"""
df_regiao = pd.DataFrame(executar_query(regiao_query))

if not df_regiao.empty:
    df_regiao["realizado_fmt"] = df_regiao["realizado"].apply(lambda v: f"{v:.2f}%")
    df_regiao["meta_fmt"] = df_regiao["meta"].apply(lambda v: f"{v:.2f}%")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_regiao["regiao"], y=df_regiao["realizado"], name="Realizado",
        marker_color="#4d7cfe", text=df_regiao["realizado_fmt"], textposition="outside",
        textfont=dict(color="#ffffff", size=10),
    ))
    fig.add_trace(go.Bar(
        x=df_regiao["regiao"], y=df_regiao["meta"], name="Meta",
        marker_color="#a0aec0", text=df_regiao["meta_fmt"], textposition="outside",
        textfont=dict(color="#ffffff", size=10),
    ))
    fig.update_layout(**layout_grafico(showlegend=True, height=380, barmode="group"), **LAYOUT_BR)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Sem dados.")
st.markdown('</div>', unsafe_allow_html=True)


# ── Tabela detalhada ─────────────────────────────────────────────────────
with st.expander("Ver dados detalhados"):
    detalhe_query = f"""
        SELECT ano_mes, nome_loja, regiao, headcount_ativo, admissoes, demissoes,
               turnover_realizado, turnover_meta, variacao_turnover,
               classificacao_turnover, status_meta
        FROM vw_turnover_mensal
        {where}
        ORDER BY ano_mes DESC, nome_loja
        LIMIT 500
    """
    df_detalhe = pd.DataFrame(executar_query(detalhe_query))
    if not df_detalhe.empty:
        st.dataframe(df_detalhe, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados.")
