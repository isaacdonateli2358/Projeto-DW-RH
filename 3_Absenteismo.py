import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    aplicar_estilo, render_sidebar_filtros, executar_query, montar_where,
    kpi_card, kpi_sublinha, layout_grafico, page_header, CORES_GRAFICO,
)

st.set_page_config(page_title="Absenteismo - RH Analytics", page_icon="", layout="wide")
aplicar_estilo()

LAYOUT_BR = dict(separators=",.")


def fmt_br(valor, decimais=0):
    if valor is None:
        valor = 0
    s = f"{valor:,.{decimais}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


with st.sidebar:
    filtros = render_sidebar_filtros("absenteismo")

page_header("Absenteismo", "Analise de ausencias e afastamentos - DW RH")

# ── Protecao de performance ─────────────────────────────────────────────
# Garante que toda consulta tenha um filtro de ano antes de agregar, evitando
# escanear a tabela fato inteira. Usa o ano selecionado ou o mais recente.
if filtros.get("anos"):
    ano_ref = max(int(a) for a in filtros["anos"])
else:
    ano_res = executar_query("SELECT MAX(ano) AS ano FROM vw_absenteismo_mensal WHERE ano IS NOT NULL")
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
        SUM(total_dias_afastamento) AS total_dias,
        SUM(horas_perdidas)         AS total_horas,
        COUNT(DISTINCT matricula_colaborador) AS colaboradores_afastados,
        COUNT(*)                    AS total_ocorrencias
    FROM vw_absenteismo_mensal
    {where}
"""
k = (executar_query(kpi_query) or [{}])[0]

total_dias   = k.get("total_dias") or 0
total_horas  = k.get("total_horas") or 0
colab_afast  = k.get("colaboradores_afastados") or 0
total_ocorr  = k.get("total_ocorrencias") or 0

# YoY: filtros["anos"] ja esta fixo em [ano_ref], entao total_dias (calculado acima)
# ja E o total do periodo de referencia. So precisamos buscar o ano anterior.
pct_yoy_dias = None
filtros_ant = dict(filtros)
filtros_ant["anos"] = [str(ano_ref - 1)]
w_ant = montar_where(filtros_ant)
res_ant = (executar_query(f"SELECT SUM(total_dias_afastamento) AS dias FROM vw_absenteismo_mensal {w_ant}") or [{}])[0]
dias_ant = res_ant.get("dias") or 0

if dias_ant:
    pct_yoy_dias = (total_dias / dias_ant - 1) * 100

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Total Dias Afastamento", fmt_br(total_dias),
             sublinha=kpi_sublinha("YoY", pct=pct_yoy_dias, inverter_cores=True), icon="DIA")
with col2:
    kpi_card("Horas Perdidas", fmt_br(total_horas, 1), sublinha=kpi_sublinha(), icon="HR")
with col3:
    kpi_card("Colaboradores Afastados", fmt_br(colab_afast), sublinha=kpi_sublinha(), icon="COL")
with col4:
    kpi_card("Total de Ocorrencias", fmt_br(total_ocorr), sublinha=kpi_sublinha(), icon="OC")
with col5:
    media_dias = total_dias / colab_afast if colab_afast else 0
    kpi_card("Media Dias por Colaborador", fmt_br(media_dias, 1), sublinha=kpi_sublinha(), icon="MED")

st.markdown("<br>", unsafe_allow_html=True)

# ── Linha 1: Evolucao mensal + Tipo de falta ────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">Dias de Afastamento por Mes ({ano_ref})</div>', unsafe_allow_html=True)

    filtros_evol = dict(filtros); filtros_evol["meses"] = []
    w_evol = montar_where(filtros_evol)

    df_evol = pd.DataFrame(executar_query(f"""
        SELECT mes, nome_mes, SUM(total_dias_afastamento) AS dias, SUM(horas_perdidas) AS horas
        FROM vw_absenteismo_mensal {w_evol}
        GROUP BY mes, nome_mes ORDER BY mes
    """))

    if not df_evol.empty:
        df_evol["dias_fmt"] = df_evol["dias"].apply(lambda v: fmt_br(v))
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_evol["nome_mes"], y=df_evol["dias"],
            mode="lines+markers+text", name="Dias Afastamento",
            line=dict(color="#4d7cfe", width=2),
            marker=dict(color="#6b8fff", size=6),
            text=df_evol["dias_fmt"], textposition="top center",
            textfont=dict(color="#ffffff", size=10),
        ))
        fig.update_layout(**layout_grafico(showlegend=False, height=320), **LAYOUT_BR)
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Tipo de Falta</div>', unsafe_allow_html=True)

    df_tipo = pd.DataFrame(executar_query(f"""
        SELECT tipo_falta, SUM(total_dias_afastamento) AS dias
        FROM vw_absenteismo_mensal {where}
        GROUP BY tipo_falta ORDER BY dias DESC
    """))

    if not df_tipo.empty:
        fig = go.Figure(go.Pie(
            labels=df_tipo["tipo_falta"], values=df_tipo["dias"],
            hole=0.55,
            marker=dict(colors=CORES_GRAFICO, line=dict(color="#0b1437", width=2)),
            textfont=dict(color="#ffffff", size=11), textposition="inside",
        ))
        fig.update_layout(**layout_grafico(showlegend=True, height=320), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Linha 2: Absenteismo por loja + por departamento ───────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Dias de Afastamento por Loja (Top 15)</div>', unsafe_allow_html=True)

    df_loja = pd.DataFrame(executar_query(f"""
        SELECT nome_loja, SUM(total_dias_afastamento) AS dias
        FROM vw_absenteismo_mensal {where}
        GROUP BY nome_loja ORDER BY dias DESC LIMIT 15
    """))

    if not df_loja.empty:
        df_loja = df_loja.sort_values("dias")
        df_loja["dias_fmt"] = df_loja["dias"].apply(lambda v: fmt_br(v))
        fig = px.bar(df_loja, x="dias", y="nome_loja", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[0]], text="dias_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Dias de Afastamento por Departamento</div>', unsafe_allow_html=True)

    df_dep = pd.DataFrame(executar_query(f"""
        SELECT departamento, SUM(total_dias_afastamento) AS dias
        FROM vw_absenteismo_mensal {where}
        GROUP BY departamento ORDER BY dias DESC LIMIT 10
    """))

    if not df_dep.empty:
        df_dep = df_dep.sort_values("dias")
        df_dep["dias_fmt"] = df_dep["dias"].apply(lambda v: fmt_br(v))
        fig = px.bar(df_dep, x="dias", y="departamento", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[2]], text="dias_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=400), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Linha 3: Justificada vs Nao justificada + Classificacao duracao ─────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Faltas Justificadas vs Nao Justificadas</div>', unsafe_allow_html=True)

    df_just = pd.DataFrame(executar_query(f"""
        SELECT justificada, SUM(total_dias_afastamento) AS dias
        FROM vw_absenteismo_mensal {where}
        GROUP BY justificada ORDER BY dias DESC
    """))

    if not df_just.empty:
        df_just["dias_fmt"] = df_just["dias"].apply(lambda v: fmt_br(v))
        cores_just = {"Sim": "#48bb78", "Nao": "#f56565"}
        cores = [cores_just.get(j, "#4d7cfe") for j in df_just["justificada"]]
        fig = px.bar(df_just, x="justificada", y="dias", text="dias_fmt",
                     color_discrete_sequence=cores)
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=11))
        fig.update_layout(**layout_grafico(height=320), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Classificacao por Duracao</div>', unsafe_allow_html=True)

    df_dur = pd.DataFrame(executar_query(f"""
        SELECT classificacao_duracao, COUNT(*) AS qtde
        FROM vw_absenteismo_mensal {where}
        GROUP BY classificacao_duracao ORDER BY qtde DESC
    """))

    if not df_dur.empty:
        df_dur["qtde_fmt"] = df_dur["qtde"].apply(lambda v: fmt_br(v))
        df_dur = df_dur.sort_values("qtde")
        fig = px.bar(df_dur, x="qtde", y="classificacao_duracao", orientation="h",
                     color_discrete_sequence=[CORES_GRAFICO[3]], text="qtde_fmt")
        fig.update_traces(marker_line_width=0, textposition="outside", textfont=dict(color="#ffffff", size=10))
        fig.update_layout(**layout_grafico(height=320), **LAYOUT_BR)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tabela detalhada ──────────────────────────────────────────────────────
with st.expander("Ver dados detalhados"):
    df_det = pd.DataFrame(executar_query(f"""
        SELECT ano_mes, nome_loja, departamento, nome_colaborador,
               tipo_falta, tipo_ocorrencia, justificada,
               total_dias_afastamento, horas_perdidas, classificacao_duracao
        FROM vw_absenteismo_mensal {where}
        ORDER BY ano_mes DESC, total_dias_afastamento DESC LIMIT 500
    """))
    if not df_det.empty:
        st.dataframe(df_det, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados.")
