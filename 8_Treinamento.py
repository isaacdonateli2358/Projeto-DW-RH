import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    aplicar_estilo, render_sidebar_filtros, executar_query, montar_where,
    kpi_card, kpi_sublinha, layout_grafico, page_header, CORES_GRAFICO,
)

st.set_page_config(page_title="Treinamento - RH Analytics", page_icon="", layout="wide")
aplicar_estilo()

LAYOUT_BR = dict(separators=",.")


def fmt_br(valor, decimais=0):
    if valor is None:
        valor = 0
    s = f"{valor:,.{decimais}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


with st.sidebar:
    filtros = render_sidebar_filtros("treinamento")

page_header("Treinamento", "Capacitacao e desenvolvimento de colaboradores - DW RH")

# ── Protecao de performance ─────────────────────────────────────────────
# Garante que toda consulta tenha um filtro de ano antes de agregar, evitando
# escanear a tabela fato inteira. Usa o ano selecionado ou o mais recente.
if filtros.get("anos"):
    ano_ref = max(int(a) for a in filtros["anos"])
else:
    ano_res = executar_query("SELECT MAX(ano) AS ano FROM vw_treinamento_por_colaborador WHERE ano IS NOT NULL")
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
        SUM(horas_treinamento)                AS total_horas,
        COUNT(DISTINCT matricula_colaborador) AS colaboradores_treinados,
        COUNT(*)                              AS total_treinamentos,
        SUM(CASE WHEN status = 'Concluido' THEN 1 ELSE 0 END) AS concluidos
    FROM vw_treinamento_por_colaborador
    {where}
"""
k = (executar_query(kpi_query) or [{}])[0]

total_horas              = k.get("total_horas") or 0
colaboradores_treinados   = k.get("colaboradores_treinados") or 0
total_treinamentos        = k.get("total_treinamentos") or 0
concluidos                 = k.get("concluidos") or 0

taxa_conclusao = (concluidos / total_treinamentos * 100) if total_treinamentos else 0
media_horas = (total_horas / colaboradores_treinados) if colaboradores_treinados else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Total de Horas", fmt_br(total_horas), sublinha=kpi_sublinha(), icon="HR")
with col2:
    kpi_card("Colaboradores Treinados", fmt_br(colaboradores_treinados), sublinha=kpi_sublinha(), icon="COL")
with col3:
    kpi_card("Total de Treinamentos", fmt_br(total_treinamentos),
             sublinha=kpi_sublinha("Taxa Conclusao", f"{taxa_conclusao:.1f}%"), icon="TRN")
with col4:
    kpi_card("Media de Horas/Colaborador", fmt_br(media_horas, 1), sublinha=kpi_sublinha(), icon="MED")
with col5:
    kpi_card("Treinamentos Concluidos", fmt_br(concluidos), sublinha=kpi_sublinha(), icon="CONC")

st.markdown("<br>", unsafe_allow_html=True)

# ── Linha 1: Evolucao mensal + Status ────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">Horas de Treinamento por Mes ({ano_ref})</div>', unsafe_allow_html=True)

    filtros_evol = dict(filtros); filtros_evol["meses"] = []
    w_evol = montar_where(filtros_evol)

    df_evol = pd.DataFrame(executar_query(f"""
        SELECT mes, nome_mes, SUM(horas_treinamento) AS horas
        FROM vw_treinamento_por_colaborador {w_evol}
        GROUP BY mes, nome_mes ORDER BY mes
    """))

    if not df_evol.empty:
        df_evol["horas_fmt"] = df_evol["horas"].apply(lambda v: fmt_br(v))
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_evol["nome_mes"], y=df_evol["horas"], mode="lines+markers+text",
            name="Horas", line=dict(color="#4d7cfe", width=2), marker=dict(color="#6b8fff", size=6),
            text=df_evol["horas_fmt"], textposition="top center", textfont=dict(color="#ffffff", size=10),
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
    st.markdown('<div class="section-title">Status dos Treinamentos</div>', unsafe_allow_html=True)

    df_status = pd.DataFrame(executar_query(f"""
        SELECT status, COUNT(*) AS qtde
        FROM vw_treinamento_por_colaborador {where}
        GROUP BY status ORDER BY qtde DESC
    """))

    if not df_status.empty:
        cores_status = {"Concluido": "#48bb78", "Em Andamento": "#f6ad55", "Cancelado": "#f56565"}
        cores = [cores_status.get(s, "#4d7cfe") for s in df_status["status"]]
        fig = go.Figure(go.Pie(
            labels=df_status["status"], values=df_status["qtde"], hole=0.55,
            marker=dict(colors=cores, line=dict(color="#0b1437", width=2)),
            textfont=dict(color="#ffffff", size=11), textposition="inside",
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=320), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Linha 2: Horas por curso + por loja ─────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Horas por Curso (Top 10)</div>', unsafe_allow_html=True)

    df_curso = pd.DataFrame(executar_query(f"""
        SELECT curso, SUM(horas_treinamento) AS horas
        FROM vw_treinamento_por_colaborador {where}
        GROUP BY curso ORDER BY horas DESC LIMIT 10
    """))

    if not df_curso.empty:
        df_curso = df_curso.sort_values("horas")
        df_curso["horas_fmt"] = df_curso["horas"].apply(lambda v: fmt_br(v))
        fig = px.bar(df_curso, x="horas", y="curso", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[0]], text="horas_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=380), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Horas de Treinamento por Loja (Top 15)</div>', unsafe_allow_html=True)

    df_loja = pd.DataFrame(executar_query(f"""
        SELECT nome_loja, SUM(horas_treinamento) AS horas
        FROM vw_treinamento_por_colaborador {where}
        GROUP BY nome_loja ORDER BY horas DESC LIMIT 15
    """))

    if not df_loja.empty:
        df_loja = df_loja.sort_values("horas")
        df_loja["horas_fmt"] = df_loja["horas"].apply(lambda v: fmt_br(v))
        fig = px.bar(df_loja, x="horas", y="nome_loja", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[2]], text="horas_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=380), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tabela detalhada ──────────────────────────────────────────────────────
with st.expander("Ver dados detalhados"):
    df_det = pd.DataFrame(executar_query(f"""
        SELECT ano_mes, nome_loja, departamento, nome_colaborador, funcao,
               curso, horas_treinamento, status, classificacao_carga, dias_duracao
        FROM vw_treinamento_por_colaborador {where}
        ORDER BY ano_mes DESC LIMIT 500
    """))
    if not df_det.empty:
        st.dataframe(df_det, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados.")
