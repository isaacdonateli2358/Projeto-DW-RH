import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    aplicar_estilo, render_sidebar_filtros, executar_query, montar_where,
    kpi_card, kpi_sublinha, layout_grafico, page_header, CORES_GRAFICO,
)

st.set_page_config(page_title="Folha de Pagamento - RH Analytics", page_icon="", layout="wide")
aplicar_estilo()

LAYOUT_BR = dict(separators=",.")


def fmt_br(valor, decimais=0):
    if valor is None:
        valor = 0
    s = f"{valor:,.{decimais}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


with st.sidebar:
    filtros = render_sidebar_filtros("folha")

page_header("Folha de Pagamento", "Custos e composicao da folha - DW RH")

# ── Protecao de performance ─────────────────────────────────────────────
# vw_folha_por_loja tem origem em fato_folha_pagamento (5+ milhoes de linhas).
# Sem um filtro de ano, a consulta varre a tabela inteira e fica muito lenta.
# Por isso, esta pagina SEMPRE usa um ano de referencia: o selecionado no
# filtro, ou o mais recente disponivel, garantindo que toda consulta seja
# filtrada por ano antes de qualquer agregacao.
if filtros.get("anos"):
    ano_ref = max(int(a) for a in filtros["anos"])
else:
    ano_res = executar_query("SELECT MAX(ano) AS ano FROM vw_folha_por_loja WHERE ano IS NOT NULL")
    ano_ref = (ano_res or [{}])[0].get("ano")
    if ano_ref:
        st.info(f"Exibindo dados de {ano_ref} (ano mais recente). Selecione um ano no filtro para ver outro periodo.")

filtros_pagina = dict(filtros)
filtros_pagina["anos"] = [str(ano_ref)] if ano_ref else []
where = montar_where(filtros_pagina)

if not ano_ref:
    st.warning("Nao foi possivel determinar um ano de referencia. Verifique a conexao com o banco.")
    st.stop()

# ── KPIs + composicao em UMA UNICA query (evita repetir o scan da tabela) ──
kpi_query = f"""
    SELECT
        SUM(custo_total_empresa) AS custo_total,
        SUM(salario_base)        AS salario_base_total,
        SUM(horas_extras_valor)  AS horas_extras_total,
        SUM(bonus)                AS bonus_total,
        SUM(comissoes)            AS comissoes_total,
        SUM(vale_alimentacao)     AS va_total,
        SUM(vale_transporte)      AS vt_total,
        AVG(salario_liquido)      AS salario_liquido_medio
    FROM vw_folha_por_loja
    {where}
"""
k = (executar_query(kpi_query) or [{}])[0]

custo_total           = k.get("custo_total") or 0
salario_base_total     = k.get("salario_base_total") or 0
horas_extras_total     = k.get("horas_extras_total") or 0
bonus_total            = k.get("bonus_total") or 0
salario_liquido_medio  = k.get("salario_liquido_medio") or 0

# ── YoY do custo total: ano de referencia vs ano anterior (1 query extra) ──
filtros_ant = dict(filtros)
filtros_ant["anos"] = [str(ano_ref - 1)]
where_ant = montar_where(filtros_ant)
res_ant = (executar_query(f"SELECT SUM(custo_total_empresa) AS custo FROM vw_folha_por_loja {where_ant}") or [{}])[0]
custo_ant = res_ant.get("custo") or 0

pct_yoy_custo = None
if custo_ant:
    pct_yoy_custo = (custo_total / custo_ant - 1) * 100

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Custo Total Empresa", f"R$ {fmt_br(custo_total, 2)}",
             sublinha=kpi_sublinha("YoY", pct=pct_yoy_custo), icon="R$")
with col2:
    kpi_card("Salario Base Total", f"R$ {fmt_br(salario_base_total, 2)}", sublinha=kpi_sublinha(), icon="SAL")
with col3:
    kpi_card("Horas Extras (R$)", f"R$ {fmt_br(horas_extras_total, 2)}", sublinha=kpi_sublinha(), icon="HE")
with col4:
    kpi_card("Bonus Total", f"R$ {fmt_br(bonus_total, 2)}", sublinha=kpi_sublinha(), icon="BON")
with col5:
    kpi_card("Salario Liquido Medio", f"R$ {fmt_br(salario_liquido_medio, 2)}", sublinha=kpi_sublinha(), icon="LIQ")

st.markdown("<br>", unsafe_allow_html=True)

# ── Linha 1: Evolucao do custo total (Jan-Dez do ano_ref) + Composicao ─────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">Custo Total da Folha por Mes ({ano_ref})</div>', unsafe_allow_html=True)

    df_evol = pd.DataFrame(executar_query(f"""
        SELECT mes, nome_mes, SUM(custo_total_empresa) AS custo
        FROM vw_folha_por_loja {where}
        GROUP BY mes, nome_mes ORDER BY mes
    """))

    if not df_evol.empty:
        df_evol["custo_fmt"] = df_evol["custo"].apply(lambda v: "R$ " + fmt_br(v, 0))
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_evol["nome_mes"], y=df_evol["custo"],
            mode="lines+markers+text", name="Custo Total",
            line=dict(color="#4d7cfe", width=2),
            marker=dict(color="#6b8fff", size=6),
            text=df_evol["custo_fmt"], textposition="top center",
            textfont=dict(color="#ffffff", size=9),
            fill="tozeroy", fillcolor="rgba(77,124,254,0.08)",
        ))
        fig.update_layout(**layout_grafico(showlegend=False, height=320), **LAYOUT_BR)
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Composicao da Folha</div>', unsafe_allow_html=True)

    labels = ["Salario Base", "Horas Extras", "Bonus", "Comissoes", "Vale Alimentacao", "Vale Transporte"]
    valores = [
        k.get("salario_base_total") or 0,
        k.get("horas_extras_total") or 0,
        k.get("bonus_total") or 0,
        k.get("comissoes_total") or 0,
        k.get("va_total") or 0,
        k.get("vt_total") or 0,
    ]

    if any(valores):
        fig = go.Figure(go.Pie(
            labels=labels, values=valores, hole=0.55,
            marker=dict(colors=CORES_GRAFICO, line=dict(color="#0b1437", width=2)),
            textfont=dict(color="#ffffff", size=10), textposition="inside",
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=320), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Linha 2: Custo por loja + por departamento ──────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Custo Total por Loja (Top 15)</div>', unsafe_allow_html=True)

    df_loja = pd.DataFrame(executar_query(f"""
        SELECT nome_loja, SUM(custo_total_empresa) AS custo
        FROM vw_folha_por_loja {where}
        GROUP BY nome_loja ORDER BY custo DESC LIMIT 15
    """))

    if not df_loja.empty:
        df_loja = df_loja.sort_values("custo")
        df_loja["custo_fmt"] = df_loja["custo"].apply(lambda v: "R$ " + fmt_br(v, 0))
        fig = px.bar(df_loja, x="custo", y="nome_loja", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[0]], text="custo_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Salario Medio por Cargo (Top 10)</div>', unsafe_allow_html=True)

    df_cargo = pd.DataFrame(executar_query(f"""
        SELECT funcao, AVG(salario_base) AS salario
        FROM vw_folha_por_loja {where}
        GROUP BY funcao ORDER BY salario DESC LIMIT 10
    """))

    if not df_cargo.empty:
        df_cargo = df_cargo.sort_values("salario")
        df_cargo["salario_fmt"] = df_cargo["salario"].apply(lambda v: "R$ " + fmt_br(v, 0))
        fig = px.bar(df_cargo, x="salario", y="funcao", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[2]], text="salario_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Linha 3: Encargos (INSS, IRRF, FGTS) por mes ────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown(f'<div class="section-title">Encargos por Mes - INSS, IRRF, FGTS ({ano_ref})</div>', unsafe_allow_html=True)

df_enc = pd.DataFrame(executar_query(f"""
    SELECT mes, nome_mes, SUM(inss) AS inss, SUM(irrf) AS irrf, SUM(fgts) AS fgts
    FROM vw_folha_por_loja {where}
    GROUP BY mes, nome_mes ORDER BY mes
"""))

if not df_enc.empty:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_enc["nome_mes"], y=df_enc["inss"], name="INSS", marker_color="#4d7cfe"))
    fig.add_trace(go.Bar(x=df_enc["nome_mes"], y=df_enc["irrf"], name="IRRF", marker_color="#805ad5"))
    fig.add_trace(go.Bar(x=df_enc["nome_mes"], y=df_enc["fgts"], name="FGTS", marker_color="#38b2ac"))
    fig.update_layout(**layout_grafico(showlegend=True, height=380, barmode="stack"), **LAYOUT_BR)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Sem dados.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Tabela detalhada ──────────────────────────────────────────────────────
with st.expander("Ver dados detalhados (amostra limitada a 500 registros)"):
    df_det = pd.DataFrame(executar_query(f"""
        SELECT ano_mes, nome_loja, departamento, funcao,
               salario_base, horas_extras_valor, bonus, comissoes,
               total_proventos, total_descontos, salario_liquido, custo_total_empresa
        FROM vw_folha_por_loja {where}
        ORDER BY ano_mes DESC LIMIT 500
    """))
    if not df_det.empty:
        st.dataframe(df_det, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados.")
