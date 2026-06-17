"""
Modulo compartilhado: conexao com banco, estilo visual e filtros.
Usado pelo chatbot (app.py) e por todas as paginas do dashboard.
"""
import streamlit as st
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


# ── Estilo visual global (azul marinho, fontes brancas) ─────────────────────
def aplicar_estilo():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif !important; }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #0b1437 !important;
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] {
        background: #111c44 !important;
        border-right: 1px solid #1b2a5e !important;
    }
    [data-testid="stSidebar"] * { color: #ffffff !important; }

    [data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 2rem !important; }

    /* Header */
    .rh-header {
        padding: 0 0 1.5rem 0;
        border-bottom: 1px solid #1b2a5e;
        margin-bottom: 2rem;
    }
    .rh-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    .rh-subtitle {
        font-size: 0.8rem;
        color: #a0aec0 !important;
        margin-top: 3px;
    }

    /* Cards de KPI */
    .kpi-card {
        background: #111c44;
        border: 1px solid #1b2a5e;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        height: 100%;
    }
    .kpi-label {
        font-size: 0.7rem;
        color: #a0aec0 !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff !important;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .kpi-delta-up {
        font-size: 0.75rem;
        color: #68d391 !important;
        font-weight: 600;
        margin-top: 4px;
    }
    .kpi-delta-down {
        font-size: 0.75rem;
        color: #fc8181 !important;
        font-weight: 600;
        margin-top: 4px;
    }
    .kpi-delta-neutral {
        font-size: 0.75rem;
        color: #a0aec0 !important;
        font-weight: 600;
        margin-top: 4px;
    }
    .kpi-icon {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, #4d7cfe, #6b8fff);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
        margin-bottom: 10px;
    }

    /* Cards de secao (graficos) */
    .section-card {
        background: #111c44;
        border: 1px solid #1b2a5e;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1.2rem;
    }
    .section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #ffffff !important;
        margin-bottom: 0.8rem;
    }

    /* Status banco */
    .status-ok {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(72,187,120,0.1);
        border: 1px solid rgba(72,187,120,0.3);
        color: #68d391 !important;
        font-size: 0.75rem; font-weight: 600;
        padding: 5px 14px; border-radius: 20px;
    }
    .status-err {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(128,90,213,0.1);
        border: 1px solid rgba(128,90,213,0.3);
        color: #b794f4 !important;
        font-size: 0.75rem; font-weight: 600;
        padding: 5px 14px; border-radius: 20px;
    }

    /* Sidebar logo */
    .sidebar-logo {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff !important;
        padding: 1.2rem 0 0.5rem 0;
        letter-spacing: -0.2px;
    }
    .sidebar-logo span { color: #4d7cfe !important; }
    .sidebar-sub {
        font-size: 0.72rem;
        color: #a0aec0 !important;
        margin-bottom: 1rem;
    }
    .sec-title {
        font-size: 0.65rem;
        color: #a0aec0 !important;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin: 1.2rem 0 0.6rem 0;
    }

    /* Labels dos filtros */
    [data-testid="stMultiSelect"] > label,
    [data-testid="stSelectbox"] > label {
        color: #a0aec0 !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background-color: #0d1a3a !important;
        border: 1px solid #1b2a5e !important;
        border-radius: 8px !important;
        min-height: 36px !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div:hover,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {
        border-color: #4d7cfe !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] span,
    [data-testid="stSelectbox"] [data-baseweb="select"] span,
    [data-testid="stMultiSelect"] input,
    [data-testid="stSelectbox"] input {
        color: #ffffff !important;
        font-size: 0.8rem !important;
    }
    [data-baseweb="tag"] {
        background: linear-gradient(135deg, #1b3a7a, #1e4db7) !important;
        border-radius: 4px !important;
        border: none !important;
        padding: 1px 6px !important;
    }
    [data-baseweb="tag"] span { color: #ffffff !important; font-size: 0.75rem !important; }
    [data-baseweb="tag"] svg { fill: #7eb3ff !important; }
    [data-baseweb="popover"] > div,
    [data-baseweb="menu"] {
        background-color: #0d1a3a !important;
        border: 1px solid #1b2a5e !important;
        border-radius: 8px !important;
    }
    [data-baseweb="option"] {
        color: #c8d8f0 !important;
        background-color: transparent !important;
        font-size: 0.8rem !important;
        padding: 6px 12px !important;
    }
    [data-baseweb="option"]:hover,
    [data-baseweb="option"][aria-selected="true"] {
        background-color: #1b2a5e !important;
        color: #ffffff !important;
    }
    [data-testid="stMultiSelect"] svg,
    [data-testid="stSelectbox"] svg {
        fill: #4d7cfe !important;
    }

    /* Botoes sidebar */
    .stButton > button {
        background: #0b1437 !important;
        color: #ffffff !important;
        border: 1px solid #1b2a5e !important;
        border-radius: 8px !important;
        font-size: 0.8rem !important;
        font-weight: 400 !important;
        text-align: left !important;
        padding: 0.5rem 0.9rem !important;
        transition: all 0.15s !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background: #1b2a5e !important;
        border-color: #4d7cfe !important;
        color: #ffffff !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 10px !important;
        border: 1px solid #1b2a5e !important;
    }
    [data-testid="stDataFrame"] * { color: #ffffff !important; }

    /* Tabs */
    [data-testid="stTabs"] button[role="tab"] {
        color: #a0aec0 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #ffffff !important;
        border-bottom-color: #4d7cfe !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0b1437; }
    ::-webkit-scrollbar-thumb { background: #1b2a5e; border-radius: 2px; }

    hr { border-color: #1b2a5e !important; }
    </style>
    """, unsafe_allow_html=True)


# ── Conexao com o banco ───────────────────────────────────────────────────
@st.cache_resource
def conectar_banco():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "dw_rh"),
        )
    except Exception:
        return None


def executar_query(sql: str, params: tuple = None):
    """Executa uma query e retorna lista de dicts."""
    conn = conectar_banco()
    if not conn:
        return []
    try:
        conn.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        # Conexao cacheada morreu definitivamente: limpa o cache e recria
        conectar_banco.clear()
        conn = conectar_banco()
        if not conn:
            return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        res = cursor.fetchall()
        cursor.close()
        return res
    except Exception as e:
        st.error(f"Erro na consulta: {e}")
        return []


# ── Filtros globais (compartilhados entre paginas via session_state) ────────
@st.cache_data(ttl=600)
def obter_opcoes_filtros():
    conn = conectar_banco()
    if not conn:
        return {}
    try:
        conn.ping(reconnect=True)
        cursor = conn.cursor()
        opcoes = {}
        queries = {
            "anos":        "SELECT DISTINCT ano FROM vw_headcount_evolucao ORDER BY ano DESC",
            "meses":       "SELECT DISTINCT mes, nome_mes FROM vw_headcount_evolucao ORDER BY mes",
            "regioes":     "SELECT DISTINCT regiao FROM vw_headcount_evolucao WHERE regiao IS NOT NULL ORDER BY regiao",
            "estados":     "SELECT DISTINCT estado FROM vw_headcount_evolucao WHERE estado IS NOT NULL ORDER BY estado",
            "lojas":       "SELECT DISTINCT nome_loja FROM vw_headcount_evolucao WHERE nome_loja IS NOT NULL ORDER BY nome_loja",
            "departamentos":"SELECT DISTINCT departamento FROM vw_headcount_evolucao WHERE departamento IS NOT NULL ORDER BY departamento",
            "funcoes":     "SELECT DISTINCT funcao FROM vw_headcount_evolucao WHERE funcao IS NOT NULL ORDER BY funcao",
        }
        for key, q in queries.items():
            cursor.execute(q)
            rows = cursor.fetchall()
            if key == "meses":
                opcoes[key] = {str(r[0]): r[1] for r in rows}
            else:
                opcoes[key] = [str(r[0]) for r in rows]
        cursor.close()
        return opcoes
    except Exception:
        return {}


def render_sidebar_filtros(pagina_atual: str = ""):
    """Renderiza o cabecalho + filtros padrao na sidebar. Retorna dict de filtros."""
    st.markdown("""
    <div class='sidebar-logo'>RH <span>Analytics</span></div>
    <div class='sidebar-sub'>Painel de indicadores de RH</div>
    <hr style='margin:0 0 1rem 0;'>
    """, unsafe_allow_html=True)

    conn = conectar_banco()
    if conn:
        st.markdown("<div class='status-ok'>* Banco conectado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-err'>* Banco desconectado</div>", unsafe_allow_html=True)

    st.markdown("<div class='sec-title' style='margin-top:1.5rem;'>Segmentacao de dados</div>", unsafe_allow_html=True)

    opcoes = obter_opcoes_filtros()

    sel_anos = st.multiselect(
        "Ano", options=opcoes.get("anos", []),
        default=[], placeholder="Todos os anos",
        key=f"fil_ano_{pagina_atual}"
    )
    meses_map = opcoes.get("meses", {})
    sel_meses_nomes = st.multiselect(
        "Mes", options=list(meses_map.values()),
        default=[], placeholder="Todos os meses",
        key=f"fil_mes_{pagina_atual}"
    )
    sel_meses = [k for k, v in meses_map.items() if v in sel_meses_nomes]

    sel_regioes = st.multiselect(
        "Regiao", options=opcoes.get("regioes", []),
        default=[], placeholder="Todas as regioes",
        key=f"fil_regiao_{pagina_atual}"
    )
    sel_estados = st.multiselect(
        "Estado", options=opcoes.get("estados", []),
        default=[], placeholder="Todos os estados",
        key=f"fil_estado_{pagina_atual}"
    )
    sel_lojas = st.multiselect(
        "Loja", options=opcoes.get("lojas", []),
        default=[], placeholder="Todas as lojas",
        key=f"fil_loja_{pagina_atual}"
    )
    sel_deps = st.multiselect(
        "Departamento", options=opcoes.get("departamentos", []),
        default=[], placeholder="Todos os departamentos",
        key=f"fil_dep_{pagina_atual}"
    )
    sel_funcs = st.multiselect(
        "Funcao", options=opcoes.get("funcoes", []),
        default=[], placeholder="Todas as funcoes",
        key=f"fil_func_{pagina_atual}"
    )

    filtros = {
        "anos": sel_anos,
        "meses": sel_meses,
        "regioes": sel_regioes,
        "estados": sel_estados,
        "lojas": sel_lojas,
        "departamentos": sel_deps,
        "funcoes": sel_funcs,
    }

    filtros_ativos = sum(1 for v in filtros.values() if v)
    if filtros_ativos > 0:
        st.markdown(f"<div style='font-size:0.72rem;color:#4d7cfe;margin-top:0.3rem;'>{filtros_ativos} filtro(s) ativo(s)</div>", unsafe_allow_html=True)

    return filtros


def montar_where(filtros: dict, alias_map: dict = None) -> str:
    """
    Gera clausula WHERE a partir dos filtros.
    alias_map permite mapear nomes de coluna diferentes por tabela/view,
    ex: {"lojas": "nome_loja", "anos": "ano"}
    """
    alias_map = alias_map or {}
    col_ano   = alias_map.get("anos", "ano")
    col_mes   = alias_map.get("meses", "mes")
    col_regiao = alias_map.get("regioes", "regiao")
    col_estado = alias_map.get("estados", "estado")
    col_loja  = alias_map.get("lojas", "nome_loja")
    col_dep   = alias_map.get("departamentos", "departamento")
    col_func  = alias_map.get("funcoes", "funcao")

    clausulas = []
    if filtros.get("anos"):
        clausulas.append(f"{col_ano} IN ({', '.join(filtros['anos'])})")
    if filtros.get("meses"):
        clausulas.append(f"{col_mes} IN ({', '.join(filtros['meses'])})")
    if filtros.get("regioes"):
        vals = "', '".join(filtros["regioes"])
        clausulas.append(f"{col_regiao} IN ('{vals}')")
    if filtros.get("estados"):
        vals = "', '".join(filtros["estados"])
        clausulas.append(f"{col_estado} IN ('{vals}')")
    if filtros.get("lojas"):
        vals = "', '".join(filtros["lojas"])
        clausulas.append(f"{col_loja} IN ('{vals}')")
    if filtros.get("departamentos"):
        vals = "', '".join(filtros["departamentos"])
        clausulas.append(f"{col_dep} IN ('{vals}')")
    if filtros.get("funcoes"):
        vals = "', '".join(filtros["funcoes"])
        clausulas.append(f"{col_func} IN ('{vals}')")

    if not clausulas:
        return ""
    return "WHERE " + " AND ".join(clausulas)


# ── Layout padrao de KPI ──────────────────────────────────────────────────
def kpi_card(label: str, value: str, delta: str = None, delta_tipo: str = "neutral", icon: str = "",
              sublinha: str = None):
    """
    Renderiza um card de KPI.
    delta_tipo: 'up', 'down' ou 'neutral'.
    sublinha: HTML extra exibido abaixo do delta (ex: comparativo ano anterior).
    """
    delta_html = ""
    if delta:
        classe = {"up": "kpi-delta-up", "down": "kpi-delta-down"}.get(delta_tipo, "kpi-delta-neutral")
        seta = {"up": "^", "down": "v"}.get(delta_tipo, "*")
        delta_html = f'<div class="{classe}">{seta} {delta}</div>'

    icon_html = f'<div class="kpi-icon">{icon}</div>' if icon else ""

    # Monta o HTML do card inteiro como uma unica string, sem placeholders aninhados problematicos
    partes = [
        '<div class="kpi-card">',
        icon_html,
        f'<div class="kpi-label">{label}</div>',
        f'<div class="kpi-value">{value}</div>',
        delta_html,
    ]
    if sublinha:
        partes.append(sublinha)
    partes.append('</div>')

    html_final = "".join(partes)
    st.markdown(html_final, unsafe_allow_html=True)


def kpi_sublinha(label: str = "", value: str = "", pct: float = None, inverter_cores: bool = False):
    """
    Gera o HTML de uma sub-informacao dentro do card de KPI.
    - Se 'pct' for informado: mostra 'Label: +3,2% ^' (ou v se negativo).
    - Se 'value' for informado (sem pct): mostra 'Label: value'.
    - Se ambos vazios: renderiza uma linha em branco (apenas para manter altura uniforme).
    - inverter_cores: se True, valores negativos sao "bons" (verde) e positivos "maus" (vermelho).
      Usado para metricas onde queda e desejavel (ex: turnover).
    """
    if pct is not None:
        if inverter_cores:
            bom = pct < 0
        else:
            bom = pct >= 0
        classe = "kpi-delta-up" if bom else "kpi-delta-down"
        seta = "^" if pct >= 0 else "v"
        sinal = "+" if pct >= 0 else ""
        prefixo = (label + ": ") if label else ""
        conteudo = (
            '<span style="font-size:0.7rem; color:#a0aec0;">' + prefixo + '</span>'
            '<span class="' + classe + '" style="font-size:0.8rem; font-weight:700;">'
            + seta + ' ' + sinal + f'{pct:.2f}' + '%</span>'
        )
    elif value:
        prefixo = (label + ": ") if label else ""
        conteudo = (
            '<span style="font-size:0.7rem; color:#a0aec0;">' + prefixo + '</span>'
            '<span style="font-size:0.8rem; color:#ffffff; font-weight:600;">' + value + '</span>'
        )
    else:
        conteudo = '&nbsp;'

    return ('<div style="border-top:1px solid #1b2a5e; margin-top:10px; padding-top:8px; min-height:22px;">'
            + conteudo + '</div>')


# ── Layout de cores para graficos ───────────────────────────────────────────
CORES_GRAFICO = ["#4d7cfe", "#6b8fff", "#38b2ac", "#805ad5", "#ed64a6", "#48bb78", "#f6ad55", "#f56565"]


def layout_grafico(titulo: str = "", **kwargs):
    """Retorna dict de layout padrao para graficos plotly."""
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(11,20,55,0.5)",
        font=dict(color="#ffffff", family="Inter", size=11),
        title=dict(text=titulo, font=dict(color="#ffffff", size=14, family="Inter"), x=0),
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis=dict(gridcolor="#1b2a5e", linecolor="#1b2a5e", tickfont=dict(color="#a0aec0"), title_font=dict(color="#a0aec0")),
        yaxis=dict(gridcolor="#1b2a5e", linecolor="#1b2a5e", tickfont=dict(color="#a0aec0"), title_font=dict(color="#a0aec0")),
        showlegend=False,
        legend=dict(font=dict(color="#ffffff"), bgcolor="rgba(0,0,0,0)"),
    )
    base.update(kwargs)
    return base


def page_header(titulo: str, subtitulo: str):
    st.markdown(f"""
    <div class='rh-header'>
        <div class='rh-title'>{titulo}</div>
        <div class='rh-subtitle'>{subtitulo}</div>
    </div>
    """, unsafe_allow_html=True)
