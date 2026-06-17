import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    aplicar_estilo, render_sidebar_filtros, executar_query, montar_where,
    kpi_card, kpi_sublinha, layout_grafico, page_header, CORES_GRAFICO,
)

# Formato numerico brasileiro (ponto = milhar, virgula = decimal) nos graficos
LAYOUT_BR = dict(separators=",.")


def fmt_br(valor, decimais=0):
    """Formata numero no padrao brasileiro: ponto para milhar, virgula para decimal."""
    if valor is None:
        valor = 0
    s = f"{valor:,.{decimais}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

st.set_page_config(page_title="Headcount - RH Analytics", page_icon="", layout="wide")
aplicar_estilo()

with st.sidebar:
    filtros = render_sidebar_filtros("headcount")

page_header("Headcount", "Visao geral do quadro de colaboradores - DW RH")

# ── Protecao de performance ─────────────────────────────────────────────
# Garante que toda consulta tenha um filtro de ano antes de agregar, evitando
# escanear a tabela fato inteira. Usa o ano selecionado ou o mais recente.
if filtros.get("anos"):
    ano_ref = max(int(a) for a in filtros["anos"])
else:
    ano_res = executar_query("SELECT MAX(ano) AS ano FROM vw_headcount_evolucao WHERE ano IS NOT NULL")
    ano_ref = (ano_res or [{}])[0].get("ano")
    if ano_ref:
        st.info(f"Exibindo dados de {ano_ref} (ano mais recente). Selecione um ano no filtro para ver outro periodo.")

filtros = dict(filtros)
filtros["anos"] = [str(ano_ref)] if ano_ref else []

where = montar_where(filtros)

if not ano_ref:
    st.warning("Nao foi possivel determinar um ano de referencia. Verifique a conexao com o banco.")
    st.stop()


# ── KPIs ──────────────────────────────────────────────────────────────────
# Admissoes, demissoes e salario medio sao somados/calculados no periodo filtrado
totais_query = f"""
    SELECT
        SUM(admissoes)        AS admissoes,
        SUM(demissoes)        AS demissoes,
        AVG(salario_medio)    AS salario_medio
    FROM vw_headcount_evolucao
    {where}
"""
totais = executar_query(totais_query)
t = totais[0] if totais else {}

admissoes = t.get("admissoes") or 0
demissoes = t.get("demissoes") or 0
salario_medio = t.get("salario_medio") or 0
saldo = admissoes - demissoes

# Headcount Ativo/Orcado sao "retratos" (snapshot): pega o ano_mes mais recente dentro do filtro
ultimo_mes_query = f"""
    SELECT MAX(ano_mes) AS ultimo_mes
    FROM vw_headcount_evolucao
    {where}
"""
ultimo_mes_res = executar_query(ultimo_mes_query)
ultimo_mes = ultimo_mes_res[0]["ultimo_mes"] if ultimo_mes_res and ultimo_mes_res[0]["ultimo_mes"] else None

headcount = 0
headcount_orcado = 0
ano_referencia = None
if ultimo_mes:
    ano_referencia = int(ultimo_mes.split("-")[0])
    clausula_extra = f"ano_mes = '{ultimo_mes}'"
    if where:
        where_snapshot = f"{where} AND {clausula_extra}"
    else:
        where_snapshot = f"WHERE {clausula_extra}"

    snapshot_query = f"""
        SELECT
            SUM(headcount_ativo)  AS headcount,
            SUM(headcount_orcado) AS headcount_orcado
        FROM vw_headcount_evolucao
        {where_snapshot}
    """
    snap = executar_query(snapshot_query)
    if snap:
        headcount = snap[0].get("headcount") or 0
        headcount_orcado = snap[0].get("headcount_orcado") or 0

# ── Headcount Ano Anterior (snapshot do mesmo mes do ano anterior) ─────────
headcount_ano_anterior = 0
if ultimo_mes:
    ano_referencia_local, mes_referencia = ultimo_mes.split("-")
    ano_anterior = int(ano_referencia_local) - 1
    ano_mes_anterior = f"{ano_anterior}-{mes_referencia}"

    filtros_ano_ant = dict(filtros)
    filtros_ano_ant["anos"] = []
    filtros_ano_ant["meses"] = []
    where_base_ant = montar_where(filtros_ano_ant)

    clausula_extra_ant = f"ano_mes = '{ano_mes_anterior}'"
    if where_base_ant:
        where_ano_ant = f"{where_base_ant} AND {clausula_extra_ant}"
    else:
        where_ano_ant = f"WHERE {clausula_extra_ant}"

    ano_ant_query = f"""
        SELECT SUM(headcount_ativo) AS headcount
        FROM vw_headcount_evolucao
        {where_ano_ant}
    """
    res_ano_ant = executar_query(ano_ant_query)
    if res_ano_ant:
        headcount_ano_anterior = res_ano_ant[0].get("headcount") or 0

# ── % YoY do Headcount Ativo ───────────────────────────────────────────────
pct_yoy_headcount = None
if headcount_ano_anterior:
    pct_yoy_headcount = (headcount / headcount_ano_anterior - 1) * 100

# ── % de Atingimento do Headcount Orcado (Realizado / Orcado - 1) ──────────
pct_atingimento = None
if headcount_orcado:
    pct_atingimento = (headcount / headcount_orcado - 1) * 100


col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    kpi_card(
        "Headcount Ativo", fmt_br(headcount), icon="HC",
        sublinha=kpi_sublinha("YoY", "", pct_yoy_headcount)
    )
with col2:
    kpi_card(
        "Headcount Orcado", fmt_br(headcount_orcado), icon="ORC",
        sublinha=kpi_sublinha("Atingimento", "", pct_atingimento)
    )
with col3:
    kpi_card("Admissoes", fmt_br(admissoes), icon="ADM",
             sublinha=kpi_sublinha())
with col4:
    kpi_card("Demissoes", fmt_br(demissoes), icon="DEM",
             sublinha=kpi_sublinha())
with col5:
    delta_tipo = "up" if saldo >= 0 else "down"
    sinal = "+" if saldo >= 0 else ""
    saldo_str = f"{sinal}{fmt_br(saldo)}"
    kpi_card("Saldo Admissoes/Demissoes", saldo_str, delta_tipo=delta_tipo, icon="SLD",
             sublinha=kpi_sublinha())
with col6:
    kpi_card("Salario Medio", f"R$ {fmt_br(salario_medio, 2)}", icon="R$",
             sublinha=kpi_sublinha())


st.markdown("<br>", unsafe_allow_html=True)


# ── Linha 1: Evolucao mensal + Distribuicao por tipo de loja ────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)

    # Determina o ano de referencia: usa o filtro selecionado, ou o ano mais recente disponivel
    if filtros.get("anos"):
        ano_evolucao = max(int(a) for a in filtros["anos"])
    else:
        ano_res = executar_query("SELECT MAX(ano) AS ano FROM vw_headcount_evolucao")
        ano_evolucao = ano_res[0]["ano"] if ano_res and ano_res[0]["ano"] else None

    st.markdown(f'<div class="section-title">Headcount Ativo e Headcount Orcado por Mes ({ano_evolucao})</div>', unsafe_allow_html=True)

    # Reaplica os demais filtros (exceto ano/mes, que sao controlados pelo ano de referencia)
    filtros_evol = dict(filtros)
    filtros_evol["anos"] = [str(ano_evolucao)] if ano_evolucao else []
    filtros_evol["meses"] = []
    where_evol = montar_where(filtros_evol)

    evol_query = f"""
        SELECT mes, nome_mes,
               SUM(headcount_ativo)  AS headcount,
               SUM(headcount_orcado) AS orcado
        FROM vw_headcount_evolucao
        {where_evol}
        GROUP BY mes, nome_mes
        ORDER BY mes
    """
    df_evol = pd.DataFrame(executar_query(evol_query))

    if not df_evol.empty:
        df_evol["headcount_fmt"] = df_evol["headcount"].apply(lambda v: fmt_br(v))
        df_evol["orcado_fmt"] = df_evol["orcado"].apply(lambda v: fmt_br(v))

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_evol["nome_mes"], y=df_evol["headcount"],
            mode="lines+markers+text", name="Headcount Ativo",
            line=dict(color="#1a2b5c", width=2),
            marker=dict(color="#1a2b5c", size=6),
            text=df_evol["headcount_fmt"], textposition="top center",
            textfont=dict(color="#ffffff", size=10),
        ))
        if df_evol["orcado"].notna().any():
            fig.add_trace(go.Scatter(
                x=df_evol["nome_mes"], y=df_evol["orcado"],
                mode="lines+markers+text", name="Headcount Orcado",
                line=dict(color="#4d7cfe", width=2),
                marker=dict(color="#4d7cfe", size=6),
                text=df_evol["orcado_fmt"], textposition="bottom center",
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
    st.markdown('<div class="section-title">Distribuicao por Tipo de Loja</div>', unsafe_allow_html=True)

    tipo_query = f"""
        SELECT tipo_loja, SUM(headcount_ativo) AS headcount
        FROM vw_headcount_evolucao
        {where}
        GROUP BY tipo_loja
        ORDER BY headcount DESC
    """
    df_tipo = pd.DataFrame(executar_query(tipo_query))

    if not df_tipo.empty:
        fig = go.Figure(go.Pie(
            labels=df_tipo["tipo_loja"], values=df_tipo["headcount"],
            hole=0.55,
            marker=dict(colors=CORES_GRAFICO, line=dict(color="#0b1437", width=2)),
            textfont=dict(color="#ffffff"),
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=320), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Linha 2: Top lojas + Headcount por departamento ─────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Top 10 Lojas por Headcount</div>', unsafe_allow_html=True)

    loja_query = f"""
        SELECT nome_loja, SUM(headcount_ativo) AS headcount
        FROM vw_headcount_evolucao
        {where}
        GROUP BY nome_loja
        ORDER BY headcount DESC
        LIMIT 10
    """
    df_loja = pd.DataFrame(executar_query(loja_query))

    if not df_loja.empty:
        df_loja = df_loja.sort_values("headcount")
        df_loja["headcount_fmt"] = df_loja["headcount"].apply(lambda v: fmt_br(v))
        fig = px.bar(df_loja, x="headcount", y="nome_loja", orientation="h",
                      color_discrete_sequence=[CORES_GRAFICO[0]], text="headcount_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside",
                           textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=380), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Headcount por Departamento</div>', unsafe_allow_html=True)

    dep_query = f"""
        SELECT departamento, SUM(headcount_ativo) AS headcount
        FROM vw_headcount_evolucao
        {where}
        GROUP BY departamento
        ORDER BY headcount DESC
        LIMIT 10
    """
    df_dep = pd.DataFrame(executar_query(dep_query))

    if not df_dep.empty:
        df_dep = df_dep.sort_values("headcount")
        df_dep["headcount_fmt"] = df_dep["headcount"].apply(lambda v: fmt_br(v))
        fig = px.bar(df_dep, x="headcount", y="departamento", orientation="h",
                      color_discrete_sequence=[CORES_GRAFICO[2]], text="headcount_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside",
                           textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=380), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Linha 3: Headcount Real vs Orcado por loja ──────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Headcount Real vs Orcado por Loja</div>', unsafe_allow_html=True)

orc_query = f"""
    SELECT nome_loja,
           SUM(headcount_ativo)  AS realizado,
           SUM(headcount_orcado) AS orcado
    FROM vw_headcount_evolucao
    {where}
    GROUP BY nome_loja
    ORDER BY realizado DESC
    LIMIT 15
"""
df_orc = pd.DataFrame(executar_query(orc_query))

if not df_orc.empty:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_orc["nome_loja"], y=df_orc["realizado"], name="Realizado",
        marker_color="#4d7cfe",
    ))
    fig.add_trace(go.Bar(
        x=df_orc["nome_loja"], y=df_orc["orcado"], name="Orcado",
        marker_color="#a0aec0",
    ))
    fig.update_layout(**layout_grafico(showlegend=True, height=380, barmode="group"), **LAYOUT_BR)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Sem dados.")
st.markdown('</div>', unsafe_allow_html=True)


# ── Tabela detalhada ─────────────────────────────────────────────────────
with st.expander("Ver dados detalhados"):
    detalhe_query = f"""
        SELECT ano_mes, nome_loja, departamento, funcao,
               headcount_ativo, admissoes, demissoes,
               headcount_orcado, salario_medio
        FROM vw_headcount_evolucao
        {where}
        ORDER BY ano_mes DESC, nome_loja
        LIMIT 500
    """
    df_detalhe = pd.DataFrame(executar_query(detalhe_query))
    if not df_detalhe.empty:
        st.dataframe(df_detalhe, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados.")
