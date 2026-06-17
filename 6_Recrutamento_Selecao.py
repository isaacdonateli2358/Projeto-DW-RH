import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    aplicar_estilo, render_sidebar_filtros, executar_query, montar_where,
    kpi_card, kpi_sublinha, layout_grafico, page_header, CORES_GRAFICO,
)

st.set_page_config(page_title="Recrutamento e Selecao - RH Analytics", page_icon="", layout="wide")
aplicar_estilo()

LAYOUT_BR = dict(separators=",.")


def fmt_br(valor, decimais=0):
    if valor is None:
        valor = 0
    s = f"{valor:,.{decimais}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


with st.sidebar:
    filtros = render_sidebar_filtros("recrutamento")

page_header("Recrutamento e Selecao", "Funil de contratacao e indicadores de vagas - DW RH")

# ── Protecao de performance ─────────────────────────────────────────────
# Garante que toda consulta tenha um filtro de ano antes de agregar, evitando
# escanear a tabela fato inteira. Usa o ano selecionado ou o mais recente.
if filtros.get("anos"):
    ano_ref = max(int(a) for a in filtros["anos"])
else:
    ano_res = executar_query("SELECT MAX(ano) AS ano FROM vw_recrutamento_funil WHERE ano IS NOT NULL")
    ano_ref = (ano_res or [{}])[0].get("ano")
    if ano_ref:
        st.info(f"Exibindo dados de {ano_ref} (ano mais recente). Selecione um ano no filtro para ver outro periodo.")

filtros = dict(filtros)
filtros["anos"] = [str(ano_ref)] if ano_ref else []

where = montar_where(filtros)

if not ano_ref:
    st.warning("Nao foi possivel determinar um ano de referencia. Verifique a conexao com o banco.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────────
kpi_query = f"""
    SELECT
        COUNT(DISTINCT id_vaga)      AS total_vagas,
        COUNT(DISTINCT id_candidato) AS total_candidatos,
        SUM(CASE WHEN aprovado = 'Sim' THEN 1 ELSE 0 END) AS total_aprovados,
        AVG(tempo_contratacao_dias)  AS tempo_medio,
        AVG(salario_oferecido)        AS salario_medio_oferecido
    FROM vw_recrutamento_funil
    {where}
"""
k = (executar_query(kpi_query) or [{}])[0]

total_vagas      = k.get("total_vagas") or 0
total_candidatos  = k.get("total_candidatos") or 0
total_aprovados   = k.get("total_aprovados") or 0
tempo_medio       = k.get("tempo_medio") or 0
salario_medio     = k.get("salario_medio_oferecido") or 0

taxa_conversao = (total_aprovados / total_candidatos * 100) if total_candidatos else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Total de Vagas", fmt_br(total_vagas), sublinha=kpi_sublinha(), icon="VAGA")
with col2:
    kpi_card("Total de Candidatos", fmt_br(total_candidatos), sublinha=kpi_sublinha(), icon="CAND")
with col3:
    kpi_card("Total de Aprovados", fmt_br(total_aprovados),
             sublinha=kpi_sublinha("Taxa Conversao", f"{taxa_conversao:.1f}%"), icon="APR")
with col4:
    kpi_card("Tempo Medio Contratacao", f"{fmt_br(tempo_medio, 1)} dias", sublinha=kpi_sublinha(), icon="TEMPO")
with col5:
    kpi_card("Salario Medio Oferecido", f"R$ {fmt_br(salario_medio, 2)}", sublinha=kpi_sublinha(), icon="R$")

st.markdown("<br>", unsafe_allow_html=True)

# ── Linha 1: Funil de etapas + Fonte de candidatos ──────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Funil do Processo Seletivo</div>', unsafe_allow_html=True)

    df_funil = pd.DataFrame(executar_query(f"""
        SELECT etapa_processo, COUNT(*) AS qtde
        FROM vw_recrutamento_funil {where}
        GROUP BY etapa_processo ORDER BY qtde DESC
    """))

    if not df_funil.empty:
        df_funil["qtde_fmt"] = df_funil["qtde"].apply(lambda v: fmt_br(v))
        fig = go.Figure(go.Funnel(
            y=df_funil["etapa_processo"], x=df_funil["qtde"],
            textinfo="value+percent initial",
            marker=dict(color=CORES_GRAFICO[:len(df_funil)]),
            textfont=dict(color="#ffffff", size=11),
        ))
        fig.update_layout(**layout_grafico(height=340), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Fonte dos Candidatos</div>', unsafe_allow_html=True)

    df_fonte = pd.DataFrame(executar_query(f"""
        SELECT fonte_candidato, COUNT(*) AS qtde
        FROM vw_recrutamento_funil {where}
        GROUP BY fonte_candidato ORDER BY qtde DESC
    """))

    if not df_fonte.empty:
        fig = go.Figure(go.Pie(
            labels=df_fonte["fonte_candidato"], values=df_fonte["qtde"],
            hole=0.55,
            marker=dict(colors=CORES_GRAFICO, line=dict(color="#0b1437", width=2)),
            textfont=dict(color="#ffffff", size=10), textposition="inside",
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=340), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Linha 2: Vagas por loja + Tempo medio por etapa ─────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Candidatos por Loja (Top 15)</div>', unsafe_allow_html=True)

    df_loja = pd.DataFrame(executar_query(f"""
        SELECT nome_loja, COUNT(DISTINCT id_candidato) AS candidatos
        FROM vw_recrutamento_funil {where}
        GROUP BY nome_loja ORDER BY candidatos DESC LIMIT 15
    """))

    if not df_loja.empty:
        df_loja = df_loja.sort_values("candidatos")
        df_loja["cand_fmt"] = df_loja["candidatos"].apply(lambda v: fmt_br(v))
        fig = px.bar(df_loja, x="candidatos", y="nome_loja", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[0]], text="cand_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Classificacao do Tempo de Contratacao</div>', unsafe_allow_html=True)

    df_tempo = pd.DataFrame(executar_query(f"""
        SELECT classificacao_tempo, COUNT(*) AS qtde
        FROM vw_recrutamento_funil {where}
        GROUP BY classificacao_tempo ORDER BY qtde DESC
    """))

    if not df_tempo.empty:
        df_tempo = df_tempo.sort_values("qtde")
        df_tempo["qtde_fmt"] = df_tempo["qtde"].apply(lambda v: fmt_br(v))
        fig = px.bar(df_tempo, x="qtde", y="classificacao_tempo", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[3]], text="qtde_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tabela detalhada ──────────────────────────────────────────────────────
with st.expander("Ver dados detalhados"):
    df_det = pd.DataFrame(executar_query(f"""
        SELECT ano_mes_contratacao, nome_loja, funcao, nome_colaborador,
               fonte_candidato, etapa_processo, status_candidato, aprovado,
               tempo_contratacao_dias, salario_oferecido
        FROM vw_recrutamento_funil {where}
        ORDER BY ano_mes_contratacao DESC LIMIT 500
    """))
    if not df_det.empty:
        st.dataframe(df_det, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados.")
