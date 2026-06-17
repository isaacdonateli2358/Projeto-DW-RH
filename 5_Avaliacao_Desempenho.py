import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    aplicar_estilo, render_sidebar_filtros, executar_query, montar_where,
    kpi_card, kpi_sublinha, layout_grafico, page_header, CORES_GRAFICO,
)

st.set_page_config(page_title="Avaliacao de Desempenho - RH Analytics", page_icon="", layout="wide")
aplicar_estilo()

LAYOUT_BR = dict(separators=",.")


def fmt_br(valor, decimais=0):
    if valor is None:
        valor = 0
    s = f"{valor:,.{decimais}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


with st.sidebar:
    filtros = render_sidebar_filtros("avaliacao")

page_header("Avaliacao de Desempenho", "Resultados das avaliacoes de colaboradores - DW RH")

# ── Protecao de performance ─────────────────────────────────────────────
# Garante que toda consulta tenha um filtro de ano antes de agregar, evitando
# escanear a tabela fato inteira. Usa o ano selecionado ou o mais recente.
if filtros.get("anos"):
    ano_ref = max(int(a) for a in filtros["anos"])
else:
    ano_res = executar_query("SELECT MAX(ano) AS ano FROM vw_avaliacao_desempenho WHERE ano IS NOT NULL")
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
        AVG(nota_final)        AS nota_media,
        COUNT(*)                AS total_avaliacoes,
        SUM(CASE WHEN elegivel_promocao = 'Sim' THEN 1 ELSE 0 END) AS elegiveis_promocao,
        SUM(CASE WHEN risco_desligamento = 'Alto' THEN 1 ELSE 0 END) AS risco_alto
    FROM vw_avaliacao_desempenho
    {where}
"""
k = (executar_query(kpi_query) or [{}])[0]

nota_media         = k.get("nota_media") or 0
total_avaliacoes    = k.get("total_avaliacoes") or 0
elegiveis_promocao  = k.get("elegiveis_promocao") or 0
risco_alto          = k.get("risco_alto") or 0

pct_elegiveis = (elegiveis_promocao / total_avaliacoes * 100) if total_avaliacoes else 0
pct_risco = (risco_alto / total_avaliacoes * 100) if total_avaliacoes else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Nota Media Geral", f"{nota_media:.2f}", sublinha=kpi_sublinha(), icon="NOTA")
with col2:
    kpi_card("Total de Avaliacoes", fmt_br(total_avaliacoes), sublinha=kpi_sublinha(), icon="AVAL")
with col3:
    kpi_card("Elegiveis a Promocao", fmt_br(elegiveis_promocao),
             sublinha=kpi_sublinha("% do total", f"{pct_elegiveis:.1f}%"), icon="PROM")
with col4:
    kpi_card("Risco de Desligamento Alto", fmt_br(risco_alto),
             sublinha=kpi_sublinha("% do total", f"{pct_risco:.1f}%"), icon="RISCO")
with col5:
    rec_query = f"""
        SELECT SUM(CASE WHEN recomendacao_ajuste_salarial = 'Sim' THEN 1 ELSE 0 END) AS qtd
        FROM vw_avaliacao_desempenho {where}
    """
    rec = (executar_query(rec_query) or [{}])[0].get("qtd") or 0
    kpi_card("Recomendados Ajuste Salarial", fmt_br(rec), sublinha=kpi_sublinha(), icon="AJST")

st.markdown("<br>", unsafe_allow_html=True)

# ── Linha 1: Distribuicao de classificacao + Competencias medias ───────────
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Distribuicao por Classificacao</div>', unsafe_allow_html=True)

    df_class = pd.DataFrame(executar_query(f"""
        SELECT classificacao_desempenho, COUNT(*) AS qtde
        FROM vw_avaliacao_desempenho {where}
        GROUP BY classificacao_desempenho ORDER BY qtde DESC
    """))

    if not df_class.empty:
        fig = go.Figure(go.Pie(
            labels=df_class["classificacao_desempenho"], values=df_class["qtde"],
            hole=0.55,
            marker=dict(colors=CORES_GRAFICO, line=dict(color="#0b1437", width=2)),
            textfont=dict(color="#ffffff", size=11), textposition="inside",
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=340), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Media por Competencia</div>', unsafe_allow_html=True)

    comp_query = f"""
        SELECT
            AVG(comunicacao)         AS Comunicacao,
            AVG(trabalho_em_equipe)  AS Trabalho_em_Equipe,
            AVG(proatividade)        AS Proatividade,
            AVG(lideranca)           AS Lideranca,
            AVG(conhecimento_tecnico) AS Conhecimento_Tecnico,
            AVG(organizacao)         AS Organizacao
        FROM vw_avaliacao_desempenho {where}
    """
    comp = (executar_query(comp_query) or [{}])[0]
    labels = [k.replace("_", " ") for k in comp.keys()]
    valores = [comp[k] or 0 for k in comp.keys()]

    if any(valores):
        fig = go.Figure(go.Scatterpolar(
            r=valores, theta=labels, fill="toself",
            line=dict(color="#4d7cfe"),
            fillcolor="rgba(77,124,254,0.25)",
        ))
        layout_radar = layout_grafico(height=340)
        layout_radar["polar"] = dict(
            radialaxis=dict(visible=True, gridcolor="#1b2a5e", tickfont=dict(color="#a0aec0")),
            angularaxis=dict(gridcolor="#1b2a5e", tickfont=dict(color="#ffffff", size=10)),
            bgcolor="rgba(0,0,0,0)",
        )
        fig.update_layout(**layout_radar, **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Linha 2: Nota media por loja + por departamento ─────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Nota Media por Loja (Top 15)</div>', unsafe_allow_html=True)

    df_loja = pd.DataFrame(executar_query(f"""
        SELECT nome_loja, AVG(nota_final) AS nota
        FROM vw_avaliacao_desempenho {where}
        GROUP BY nome_loja ORDER BY nota DESC LIMIT 15
    """))

    if not df_loja.empty:
        df_loja = df_loja.sort_values("nota")
        df_loja["nota_fmt"] = df_loja["nota"].apply(lambda v: f"{v:.2f}")
        fig = px.bar(df_loja, x="nota", y="nome_loja", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[0]], text="nota_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Risco de Desligamento (Distribuicao)</div>', unsafe_allow_html=True)

    df_risco = pd.DataFrame(executar_query(f"""
        SELECT risco_desligamento, COUNT(*) AS qtde
        FROM vw_avaliacao_desempenho {where}
        GROUP BY risco_desligamento ORDER BY qtde DESC
    """))

    if not df_risco.empty:
        df_risco = df_risco.sort_values("qtde")
        df_risco["qtde_fmt"] = df_risco["qtde"].apply(lambda v: fmt_br(v))
        cores_risco = {"Alto": "#f56565", "Medio": "#f6ad55", "Baixo": "#48bb78"}
        cores = [cores_risco.get(r, "#4d7cfe") for r in df_risco["risco_desligamento"]]
        fig = px.bar(df_risco, x="qtde", y="risco_desligamento", orientation="h",
                     color_discrete_sequence=cores, text="qtde_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tabela detalhada ──────────────────────────────────────────────────────
with st.expander("Ver dados detalhados"):
    df_det = pd.DataFrame(executar_query(f"""
        SELECT ano_avaliacao, nome_loja, departamento, nome_colaborador, funcao,
               nota_final, classificacao_desempenho, elegivel_promocao,
               risco_desligamento, competencia_mais_forte, competencia_mais_fraca
        FROM vw_avaliacao_desempenho {where}
        ORDER BY ano_avaliacao DESC, nota_final DESC LIMIT 500
    """))
    if not df_det.empty:
        st.dataframe(df_det, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados.")
