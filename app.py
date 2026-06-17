import streamlit as st
import mysql.connector
import ollama
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="RH Analytics",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

/* Remove streamlit padrão */
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

/* Mensagens */
.msg-user {
    background: linear-gradient(135deg, #1a3a6e, #1e4080);
    border: 1px solid #2a4a8a;
    padding: 0.9rem 1.2rem;
    border-radius: 14px 14px 4px 14px;
    margin: 0.8rem 0 0.3rem auto;
    max-width: 75%;
    color: #ffffff !important;
    font-size: 0.9rem;
    line-height: 1.6;
}
.msg-bot {
    background: #111c44;
    border: 1px solid #1b2a5e;
    border-left: 3px solid #4d7cfe;
    padding: 0.9rem 1.2rem;
    border-radius: 4px 14px 14px 14px;
    margin: 0.3rem 0 0.8rem 0;
    color: #ffffff !important;
    font-size: 0.88rem;
    line-height: 1.7;
}
.msg-erro {
    background: #1a1130;
    border: 1px solid #3a2060;
    border-left: 3px solid #805ad5;
    padding: 0.9rem 1.2rem;
    border-radius: 4px 14px 14px 14px;
    margin: 0.3rem 0 0.8rem 0;
    color: #ffffff !important;
    font-size: 0.88rem;
    line-height: 1.6;
}
.label-user {
    text-align: right;
    font-size: 0.65rem;
    color: #a0aec0 !important;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.label-bot {
    font-size: 0.65rem;
    color: #4d7cfe !important;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.label-err {
    font-size: 0.65rem;
    color: #805ad5 !important;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 3px;
}

/* Sidebar logo */
.sidebar-logo {
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff !important;
    padding: 1.2rem 0 0.5rem 0;
    letter-spacing: -0.2px;
}
.sidebar-logo span {
    color: #4d7cfe !important;
}
.sidebar-sub {
    font-size: 0.72rem;
    color: #a0aec0 !important;
    margin-bottom: 1rem;
}

/* Status */
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

/* Section title sidebar */
.sec-title {
    font-size: 0.65rem;
    color: #a0aec0 !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 1.2rem 0 0.6rem 0;
}

/* Botões sugestão */
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

/* Botão Enviar */
div[data-testid="column"]:last-child .stButton > button {
    background: linear-gradient(135deg, #4d7cfe, #6b8fff) !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border-radius: 10px !important;
    padding: 0.55rem 1rem !important;
}
div[data-testid="column"]:last-child .stButton > button:hover {
    background: linear-gradient(135deg, #3a6aee, #5a7fee) !important;
}

/* Input */
.stTextInput input {
    background-color: #111c44 !important;
    color: #ffffff !important;
    border: 1px solid #1b2a5e !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
}
.stTextInput input:focus {
    border-color: #4d7cfe !important;
    box-shadow: 0 0 0 2px rgba(77,124,254,0.2) !important;
}
.stTextInput input::placeholder { color: #4a5a8a !important; }

/* Expander */
details {
    background: #111c44 !important;
    border: 1px solid #1b2a5e !important;
    border-radius: 10px !important;
}
details summary {
    color: #a0aec0 !important;
    font-size: 0.8rem !important;
    padding: 0.6rem 1rem !important;
}
details summary:hover { color: #ffffff !important; }

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1px solid #1b2a5e !important;
}
[data-testid="stDataFrame"] * { color: #ffffff !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0b1437; }
::-webkit-scrollbar-thumb { background: #1b2a5e; border-radius: 2px; }

/* Esconde label input */
label[data-testid="stWidgetLabel"] { display: none !important; }

/* Divider */
hr { border-color: #1b2a5e !important; }
</style>
""", unsafe_allow_html=True)


# ── Banco ────────────────────────────────────────────────────────────────────
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


@st.cache_data(ttl=3600)
def obter_schema():
    conn = conectar_banco()
    if not conn:
        return ""
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tabelas = [t[0] for t in cursor.fetchall()]
    schema = []
    for tabela in tabelas:
        cursor.execute(f"DESCRIBE `{tabela}`")
        colunas = [c[0] for c in cursor.fetchall()]
        schema.append(f"  {tabela}({', '.join(colunas)})")
    cursor.close()
    return "\n".join(schema)



@st.cache_data(ttl=600)

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


def montar_clausula_filtros(filtros: dict) -> str:
    """Gera a clausula WHERE com os filtros selecionados."""
    clausulas = []
    if filtros.get("anos"):
        anos = ", ".join(filtros["anos"])
        clausulas.append(f"ano IN ({anos})")
    if filtros.get("meses"):
        meses = ", ".join(filtros["meses"])
        clausulas.append(f"mes IN ({meses})")
    if filtros.get("regioes"):
        regioes = "', '".join(filtros["regioes"])
        clausulas.append(f"regiao IN ('{regioes}')")
    if filtros.get("estados"):
        estados = "', '".join(filtros["estados"])
        clausulas.append(f"estado IN ('{estados}')")
    if filtros.get("lojas"):
        lojas = "', '".join(filtros["lojas"])
        clausulas.append(f"nome_loja IN ('{lojas}')")
    if filtros.get("departamentos"):
        deps = "', '".join(filtros["departamentos"])
        clausulas.append(f"departamento IN ('{deps}')")
    if filtros.get("funcoes"):
        funcs = "', '".join(filtros["funcoes"])
        clausulas.append(f"funcao IN ('{funcs}')")
    return " AND ".join(clausulas) if clausulas else ""

def aplicar_filtros_no_sql(sql: str, filtros: dict) -> str:
    """Injeta os filtros selecionados na clausula WHERE do SQL gerado pelo modelo."""
    clausula = montar_clausula_filtros(filtros)
    if not clausula:
        return sql

    sql_limpo = sql.strip().rstrip(";")
    sql_upper = sql_limpo.upper()

    # Encontra posicoes das clausulas que vem depois do WHERE
    pos_group = sql_upper.find("GROUP BY")
    pos_order = sql_upper.find("ORDER BY")
    pos_limit = sql_upper.find("LIMIT")
    pos_having = sql_upper.find("HAVING")

    # A primeira clausula que aparece define onde "cortar" o SQL
    posicoes = [p for p in [pos_group, pos_having, pos_order, pos_limit] if p != -1]
    pos_corte = min(posicoes) if posicoes else len(sql_limpo)

    parte_principal = sql_limpo[:pos_corte].rstrip()
    parte_resto = sql_limpo[pos_corte:].strip()

    if " WHERE " in parte_principal.upper():
        # Ja existe WHERE: adiciona com AND
        nova_principal = f"{parte_principal} AND ({clausula})"
    else:
        # Nao existe WHERE: adiciona
        nova_principal = f"{parte_principal} WHERE {clausula}"

    novo_sql = f"{nova_principal} {parte_resto}".strip()
    return novo_sql



def carregar_opcoes_filtros():
    conn = conectar_banco()
    if not conn:
        return {}
    try:
        conn.ping(reconnect=True)
        cursor = conn.cursor()
        opcoes = {}
        queries = {
            "ano":        "SELECT DISTINCT ano FROM vw_headcount_evolucao WHERE ano IS NOT NULL ORDER BY ano DESC",
            "mes":        "SELECT DISTINCT mes, nome_mes FROM vw_headcount_evolucao WHERE mes IS NOT NULL ORDER BY mes",
            "regiao":     "SELECT DISTINCT regiao FROM vw_headcount_evolucao WHERE regiao IS NOT NULL ORDER BY regiao",
            "estado":     "SELECT DISTINCT estado FROM vw_headcount_evolucao WHERE estado IS NOT NULL ORDER BY estado",
            "nome_loja":  "SELECT DISTINCT nome_loja FROM vw_headcount_evolucao WHERE nome_loja IS NOT NULL ORDER BY nome_loja",
            "departamento":"SELECT DISTINCT departamento FROM vw_headcount_evolucao WHERE departamento IS NOT NULL ORDER BY departamento",
            "funcao":     "SELECT DISTINCT funcao FROM vw_headcount_evolucao WHERE funcao IS NOT NULL ORDER BY funcao",
        }
        for campo, sql in queries.items():
            cursor.execute(sql)
            rows = cursor.fetchall()
            if campo == "mes":
                opcoes[campo] = {str(r[0]): r[1] for r in rows}
            else:
                opcoes[campo] = [str(r[0]) for r in rows]
        cursor.close()
        return opcoes
    except Exception as e:
        return {}

def montar_clausula_where(filtros: dict) -> str:
    """Monta clausula WHERE com os filtros ativos."""
    clausulas = []
    if filtros.get("ano"):
        anos = ", ".join(filtros["ano"])
        clausulas.append(f"ano IN ({anos})")
    if filtros.get("mes"):
        meses = ", ".join(filtros["mes"])
        clausulas.append(f"mes IN ({meses})")
    if filtros.get("regiao"):
        regioes = "', '".join(filtros["regiao"])
        clausulas.append(f"regiao IN ('{regioes}')")
    if filtros.get("estado"):
        estados = "', '".join(filtros["estado"])
        clausulas.append(f"estado IN ('{estados}')")
    if filtros.get("nome_loja"):
        lojas = "', '".join(filtros["nome_loja"])
        clausulas.append(f"nome_loja IN ('{lojas}')")
    if filtros.get("departamento"):
        deptos = "', '".join(filtros["departamento"])
        clausulas.append(f"departamento IN ('{deptos}')")
    if filtros.get("funcao"):
        funcoes = "', '".join(filtros["funcao"])
        clausulas.append(f"funcao IN ('{funcoes}')")
    return " AND ".join(clausulas) if clausulas else ""

def executar_sql(sql: str):
    conn = conectar_banco()
    if not conn:
        return None, "Nao foi possivel conectar ao banco."
    try:
        conn.ping(reconnect=True)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        res = cursor.fetchall()
        cursor.close()
        return res, None
    except Exception as e:
        return None, str(e)


def gerar_sql(pergunta: str, schema: str, historico: list, filtros_contexto: str = "") -> str:
    system_prompt = f"""Voce e um especialista em SQL para MySQL e analise de dados de RH.
Converta perguntas em linguagem natural para SQL valido MySQL.

REGRAS ABSOLUTAS:
1. Responda APENAS com codigo SQL puro. Sem explicacoes, sem markdown, sem crases.
2. Use SOMENTE as colunas listadas abaixo. NUNCA invente colunas.
3. SEMPRE use GROUP BY ao pedir totais/medias por categoria. SEMPRE use ORDER BY.
4. Prefira views (vw_*) pois ja tem dados consolidados.
5. LIMIT 50 quando nao especificado.
6. Nunca use INSERT, UPDATE, DELETE ou DROP.
7. Se nao conseguir responder, escreva apenas: NAO_SEI

SCHEMA COMPLETO:

vw_headcount_evolucao: ano, semestre, trimestre, mes, nome_mes, ano_mes, ano_trimestre, nome_loja, tipo_loja, cidade, estado, regiao, departamento, centro_custo, funcao, nivel_cargo, familia_cargo, headcount_ativo, admissoes, demissoes, massa_salarial, headcount_orcado, variacao_orcado, turnover_percentual, salario_medio, percentual_atingimento_orcado

vw_turnover_mensal: ano, trimestre, mes, nome_mes, ano_mes, ano_trimestre, nome_loja, tipo_loja, cidade, estado, regiao, headcount_ativo, admissoes, demissoes, turnover_realizado, turnover_meta, variacao_turnover, classificacao_turnover, status_meta

vw_absenteismo_mensal: ano, semestre, trimestre, mes, nome_mes, ano_mes, ano_trimestre, nome_loja, tipo_loja, cidade, estado, regiao, departamento, centro_custo, funcao, nivel_cargo, familia_cargo, matricula_colaborador, nome_colaborador, sexo, faixa_etaria, tipo_contratacao, tipo_falta, tipo_ocorrencia, justificada, cid, total_dias_afastamento, horas_perdidas, classificacao_duracao, status_justificativa

vw_avaliacao_desempenho: ano, semestre, trimestre, mes, nome_mes, ano_mes, ano_trimestre, nome_loja, tipo_loja, cidade, estado, regiao, departamento, centro_custo, funcao, nivel_cargo, familia_cargo, matricula_colaborador, nome_colaborador, sexo, faixa_etaria, escolaridade, tipo_contratacao, situacao, tempo_casa_anos, ano_avaliacao, ciclo_avaliacao, tipo_avaliacao, gestor_avaliador, comunicacao, trabalho_em_equipe, proatividade, lideranca, conhecimento_tecnico, organizacao, nota_final, classificacao_desempenho, elegivel_promocao, recomendacao_ajuste_salarial, percentual_ajuste, risco_desligamento, faixa_nota, competencia_mais_fraca, competencia_mais_forte

vw_folha_por_loja: ano, mes, nome_mes, ano_mes, trimestre, semestre, ano_trimestre, nome_loja, tipo_loja, cidade, estado, regiao, departamento, centro_custo, funcao, nivel_cargo, familia_cargo, sexo, faixa_etaria, escolaridade, tipo_contratacao, salario_base, horas_extras_qtd, horas_extras_valor, adicional_noturno, bonus, comissoes, vale_alimentacao, vale_transporte, auxilio_combustivel, auxilio_creche, total_proventos, inss, irrf, total_descontos, salario_liquido, fgts, custo_total_empresa

vw_metas_vs_realizado: ano, semestre, trimestre, mes, nome_mes, ano_mes, ano_trimestre, nome_loja, tipo_loja, cidade, estado, regiao, meta_turnover, meta_admissoes, meta_demissoes, meta_horas_extras, meta_absenteismo, meta_treinamento_horas, realizado_admissoes, realizado_demissoes, realizado_turnover, realizado_horas_extras, realizado_treinamento_horas, variacao_admissoes, variacao_demissoes, variacao_turnover, variacao_horas_extras, variacao_treinamento, status_admissoes, status_demissoes, status_turnover, status_horas_extras, status_treinamento, metas_atingidas, classificacao_geral

vw_recrutamento_funil: ano, semestre, trimestre, mes, nome_mes, ano_mes, ano_trimestre, nome_loja, tipo_loja, cidade, estado, regiao, departamento, centro_custo, funcao, nivel_cargo, familia_cargo, matricula_colaborador, nome_colaborador, sexo, faixa_etaria, escolaridade, id_vaga, id_candidato, fonte_candidato, nivel_vaga, tipo_contratacao, status_candidato, aprovado, etapa_processo, tempo_contratacao_dias, tempo_por_etapa, salario_oferecido, classificacao_tempo, faixa_salarial_oferecida, ano_contratacao, ano_mes_contratacao

vw_treinamento_por_colaborador: ano, semestre, trimestre, mes, nome_mes, ano_mes, ano_trimestre, nome_loja, tipo_loja, cidade, estado, regiao, departamento, centro_custo, funcao, nivel_cargo, familia_cargo, matricula_colaborador, nome_colaborador, sexo, faixa_etaria, escolaridade, tipo_contratacao, situacao, curso, horas_treinamento, status, classificacao_carga, dias_duracao

colaboradores: matricula_colaborador, nome_colaborador, sexo, data_nascimento, idade_na_contratacao, idade, cidade_moradia, estado_moradia, pais, naturalidade, data_admissao, data_demissao, situacao, motivo_desligamento, tipo_desligamento, tipo_contratacao, escolaridade, departamento, centro_custo, funcao, salario_contratacao, vale_alimentacao, auxilio_combustivel, auxilio_creche, loja, cidade_loja, estado_loja, pais_loja

folha_pagamento: id, matricula_colaborador, nome_colaborador, mes_ano, salario_base, horas_extras_qtd, horas_extras_valor, adicional_noturno, bonus, comissoes, vale_alimentacao, vale_transporte, auxilio_combustivel, auxilio_creche, inss, irrf, total_proventos, total_descontos, salario_liquido, fgts, custo_total_empresa, centro_custo, departamento, funcao, tipo_contratacao

absenteismo: id, matricula_colaborador, nome_colaborador, funcao, data_inicio_afastamento, data_final_afastamento, total_dias_afastamento, tipo_falta, horas_perdidas, justificada, cid, departamento, centro_custo, mes_ano, tipo_ocorrencia

treinamentos: id, matricula_colaborador, nome_colaborador, funcao, centro_custo, departamento, curso, data_inicio, data_fim, horas_treinamento, status

recrutamento_selecao: id, id_vaga, funcao, centro_custo, departamento, gestor_solicitante, id_candidato, nome_candidato, sexo, idade, cidade, estado, fonte_candidato, data_candidatura, etapa_processo, status_candidato, data_triagem, data_entrevista_rh, data_entrevista_gestor, data_proposta, data_contratacao, tempo_contratacao_dias, tempo_por_etapa, aprovado, salario_oferecido, nivel_vaga, tipo_contratacao

metas: id, ano, mes, centro_custo, departamento, nome_loja, turnover_percentual, admissoes_quantidade, demissoes_quantidade, horas_extras, absenteismo_percentual, treinamento_horas

EXEMPLOS CORRETOS:
- Headcount por loja: SELECT nome_loja, SUM(headcount_ativo) as headcount FROM vw_headcount_evolucao GROUP BY nome_loja ORDER BY headcount DESC LIMIT 50
- Turnover 2025: SELECT ano_mes, AVG(turnover_realizado) as turnover FROM vw_turnover_mensal WHERE ano = 2025 GROUP BY ano_mes ORDER BY ano_mes
- Salario por cargo: SELECT funcao, ROUND(AVG(salario_medio),2) as salario FROM vw_headcount_evolucao GROUP BY funcao ORDER BY salario DESC LIMIT 50
- Absenteismo por loja: SELECT nome_loja, SUM(total_dias_afastamento) as dias FROM vw_absenteismo_mensal GROUP BY nome_loja ORDER BY dias DESC

FILTROS ATIVOS DO USUARIO (inclua no WHERE quando relevante):
{filtros_contexto}"""
    msgs = [{"role": "system", "content": system_prompt}]
    for m in historico[-4:]:
        msgs.append(m)
    msgs.append({"role": "user", "content": pergunta})
    r = ollama.chat(model=os.getenv("OLLAMA_MODEL", "phi3"), messages=msgs)
    return r["message"]["content"].strip()


def interpretar_e_grafico(pergunta: str, resultados: list) -> dict:
    if not resultados:
        return {"texto": "A consulta nao retornou resultados.", "grafico": None}

    amostra = resultados[:20]
    system_prompt = """Voce e um analista de RH experiente.
Analise os dados e responda em JSON exato:
{
  "texto": "analise detalhada em portugues com numeros concretos, destaques e insights relevantes para o gestor de RH",
  "grafico": {
    "tipo": "bar" | "bar_h" | "line" | "pie" | "none",
    "x": "coluna_x",
    "y": "coluna_y",
    "titulo": "titulo do grafico"
  }
}
- bar: ate 10 categorias
- bar_h: mais de 10 categorias
- line: serie temporal
- pie: proporcoes ate 6 itens
- none: sem grafico
Responda APENAS com o JSON."""

    r = ollama.chat(
        model=os.getenv("OLLAMA_MODEL", "phi3"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Pergunta: {pergunta}\n\nDados ({len(resultados)} registros):\n{amostra}"},
        ],
    )
    raw = r["message"]["content"].strip()
    # Tenta extrair JSON mesmo que venha com texto ao redor
    import re
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            # Garante que grafico sempre existe
            if "grafico" not in parsed:
                parsed["grafico"] = None
            return parsed
        except Exception:
            pass
    # Fallback: gera grafico automaticamente baseado nos dados
    cols = list(resultados[0].keys()) if resultados else []
    grafico = None
    if len(cols) >= 2:
        # Detecta coluna numerica
        col_num = next((c for c in cols[1:] if isinstance(resultados[0].get(c), (int, float))), None)
        col_cat = cols[0]
        if col_num:
            tipo = "bar_h" if len(resultados) > 10 else "bar"
            grafico = {"tipo": tipo, "x": col_cat, "y": col_num, "titulo": pergunta.capitalize()}
    return {"texto": raw.replace("```json", "").replace("```", "").strip(), "grafico": grafico}


def criar_grafico(df: pd.DataFrame, config: dict):
    tipo = config.get("tipo", "none")
    x = config.get("x")
    y = config.get("y")
    titulo = config.get("titulo", "")

    if not x or x not in df.columns:
        return None
    if tipo != "pie" and (not y or y not in df.columns):
        return None

    cores = ["#4d7cfe", "#6b8fff", "#38b2ac", "#805ad5", "#ed64a6", "#48bb78", "#f6ad55"]

    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(11,20,55,0.5)",
        font=dict(color="#ffffff", family="Inter", size=11),
        title=dict(text=titulo, font=dict(color="#ffffff", size=14, family="Inter", weight=600), x=0),
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(
            gridcolor="#1b2a5e", linecolor="#1b2a5e",
            tickfont=dict(color="#a0aec0"), title_font=dict(color="#a0aec0"),
        ),
        yaxis=dict(
            gridcolor="#1b2a5e", linecolor="#1b2a5e",
            tickfont=dict(color="#a0aec0"), title_font=dict(color="#a0aec0"),
        ),
        showlegend=False,
    )

    try:
        if tipo == "bar":
            fig = px.bar(df, x=x, y=y, color_discrete_sequence=cores, text=y)
            fig.update_traces(marker_line_width=0, textposition="outside",
                textfont=dict(color="#ffffff", size=10),
                texttemplate="%{text:,.0f}")
        elif tipo == "bar_h":
            fig = px.bar(df, x=y, y=x, orientation="h", color_discrete_sequence=cores, text=y)
            fig.update_traces(marker_line_width=0, textposition="outside",
                textfont=dict(color="#ffffff", size=10),
                texttemplate="%{text:,.0f}")
        elif tipo == "line":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df[x], y=df[y],
                mode="lines+markers+text",
                line=dict(color="#4d7cfe", width=2.5, shape="spline"),
                marker=dict(color="#6b8fff", size=7),
                fill="tozeroy",
                fillcolor="rgba(77,124,254,0.1)",
                text=df[y].apply(lambda v: f"{v:,.0f}" if isinstance(v, (int, float)) else str(v)),
                textposition="top center",
                textfont=dict(color="#ffffff", size=10),
            ))
            fig.update_layout(title=titulo)
        elif tipo == "pie":
            fig = go.Figure(go.Pie(
                labels=df[x],
                values=df[y] if y and y in df.columns else [1]*len(df),
                hole=0.5,
                marker=dict(colors=cores, line=dict(color="#0b1437", width=2)),
                textfont=dict(color="#ffffff"),
            ))
            fig.update_layout(
                title=titulo,
                legend=dict(font=dict(color="#ffffff"), bgcolor="rgba(0,0,0,0)"),
                showlegend=True,
            )
        else:
            return None

        fig.update_layout(**layout)
        return fig
    except Exception:
        return None


# ── Estado ───────────────────────────────────────────────────────────────────
if "historico" not in st.session_state:
    st.session_state.historico = []
if "historico_llm" not in st.session_state:
    st.session_state.historico_llm = []
if "filtros" not in st.session_state:
    st.session_state.filtros = {}


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class='sidebar-logo'>RH <span>Analytics</span></div>
    <div class='sidebar-sub'>Assistente inteligente de dados</div>
    <hr style='margin:0 0 1rem 0;'>
    """, unsafe_allow_html=True)

    conn = conectar_banco()
    if conn:
        st.markdown("<div class='status-ok'>● Banco conectado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-err'>● Banco desconectado</div>", unsafe_allow_html=True)

    # ── Segmentação de dados ──────────────────────────────────────────────
    st.markdown("<div class='sec-title' style='margin-top:1.5rem;'>Segmentacao de dados</div>", unsafe_allow_html=True)

    opcoes = obter_opcoes_filtros()

    sel_anos = st.multiselect(
        "Ano", options=opcoes.get("anos", []),
        default=[], placeholder="Todos os anos",
        key="fil_ano"
    )
    meses_map = opcoes.get("meses", {})
    sel_meses_nomes = st.multiselect(
        "Mes", options=list(meses_map.values()),
        default=[], placeholder="Todos os meses",
        key="fil_mes"
    )
    sel_meses = [k for k, v in meses_map.items() if v in sel_meses_nomes]

    sel_regioes = st.multiselect(
        "Regiao", options=opcoes.get("regioes", []),
        default=[], placeholder="Todas as regioes",
        key="fil_regiao"
    )
    sel_estados = st.multiselect(
        "Estado", options=opcoes.get("estados", []),
        default=[], placeholder="Todos os estados",
        key="fil_estado"
    )
    sel_lojas = st.multiselect(
        "Loja", options=opcoes.get("lojas", []),
        default=[], placeholder="Todas as lojas",
        key="fil_loja"
    )
    sel_deps = st.multiselect(
        "Departamento", options=opcoes.get("departamentos", []),
        default=[], placeholder="Todos os departamentos",
        key="fil_dep"
    )
    sel_funcs = st.multiselect(
        "Funcao", options=opcoes.get("funcoes", []),
        default=[], placeholder="Todas as funcoes",
        key="fil_func"
    )

    st.session_state.filtros = {
        "anos": sel_anos,
        "meses": sel_meses,
        "regioes": sel_regioes,
        "estados": sel_estados,
        "lojas": sel_lojas,
        "departamentos": sel_deps,
        "funcoes": sel_funcs,
    }

    filtros_ativos = sum(1 for v in st.session_state.filtros.values() if v)
    if filtros_ativos > 0:
        st.markdown(f"<div style='font-size:0.72rem;color:#4d7cfe;margin-top:0.3rem;'>{filtros_ativos} filtro(s) ativo(s)</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:0.8rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='sec-title'>Perguntas sugeridas</div>", unsafe_allow_html=True)

    exemplos = [
        "Headcount atual por loja",
        "Desligamentos este mes",
        "Media salarial por cargo",
        "Absenteismo por loja",
        "Metas atingidas vs nao atingidas",
        "Vagas em recrutamento aberto",
        "Turnover do ultimo trimestre",
        "Treinamentos por colaborador",
    ]
    for ex in exemplos:
        if st.button(ex, key=ex, use_container_width=True):
            st.session_state["pergunta_input"] = ex

    st.markdown("<hr style='margin:1rem 0;'>", unsafe_allow_html=True)
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.historico = []
        st.session_state.historico_llm = []
        st.rerun()

    st.markdown("<div style='font-size:0.65rem;color:#1b2a5e;margin-top:1rem;text-align:center;'>phi3 · MySQL · Streamlit</div>", unsafe_allow_html=True)


# ── Main ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='rh-header'>
    <div class='rh-title'>Assistente de Analise de RH</div>
    <div class='rh-subtitle'>Faca perguntas sobre seus dados em linguagem natural</div>
</div>
""", unsafe_allow_html=True)

for item in st.session_state.historico:
    if item["role"] == "user":
        st.markdown(f'<div class="label-user">Voce</div><div class="msg-user">{item["content"]}</div>', unsafe_allow_html=True)

    elif item["role"] == "assistant":
        st.markdown(f'<div class="label-bot">Assistente</div><div class="msg-bot">{item["content"]}</div>', unsafe_allow_html=True)

        if item.get("grafico_config") and item.get("df"):
            df = pd.DataFrame(item["df"])
            fig = criar_grafico(df, item["grafico_config"])
            if fig:
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        if item.get("df"):
            df = pd.DataFrame(item["df"])
            gc = item.get("grafico_config")
            if len(df.columns) > 2 or not gc or gc.get("tipo") == "none":
                with st.expander(f"Ver tabela completa  —  {len(df)} registros"):
                    st.dataframe(df, use_container_width=True, hide_index=True)

    elif item["role"] == "error":
        st.markdown(f'<div class="label-err">Aviso</div><div class="msg-erro">{item["content"]}</div>', unsafe_allow_html=True)


# ── Input ─────────────────────────────────────────────────────────────────────
pergunta_default = st.session_state.pop("pergunta_input", "")
col1, col2 = st.columns([5, 1])
with col1:
    pergunta = st.text_input(
        "pergunta", value=pergunta_default,
        placeholder="Ex: Qual o headcount atual por loja?",
        label_visibility="collapsed", key="input_pergunta",
    )
with col2:
    enviar = st.button("Enviar", use_container_width=True)


# ── Processar ─────────────────────────────────────────────────────────────────
if enviar and pergunta.strip():
    st.session_state.historico.append({"role": "user", "content": pergunta})

    with st.spinner("Analisando..."):
        schema = obter_schema()
        sql = gerar_sql(pergunta, schema, st.session_state.historico_llm)

    if sql == "NAO_SEI" or not sql:
        st.session_state.historico.append({
            "role": "error",
            "content": "Nao consegui interpretar essa pergunta. Tente reformular.",
        })
    else:
        sql = aplicar_filtros_no_sql(sql, st.session_state.filtros)
        with st.spinner("Consultando banco de dados..."):
            resultados, erro = executar_sql(sql)

        if erro:
            st.session_state.historico.append({"role": "error", "content": f"Erro: {erro}"})
        else:
            with st.spinner("Preparando visualizacao..."):
                resposta = interpretar_e_grafico(pergunta, resultados or [])

            st.session_state.historico.append({
                "role": "assistant",
                "content": resposta.get("texto", ""),
                "df": resultados,
                "grafico_config": resposta.get("grafico"),
            })
            st.session_state.historico_llm.append({"role": "user", "content": pergunta})
            st.session_state.historico_llm.append({"role": "assistant", "content": resposta.get("texto", "")})

    st.rerun()
