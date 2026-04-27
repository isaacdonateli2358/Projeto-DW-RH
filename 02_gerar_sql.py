"""
============================================================
SCRIPT 2 — GERAÇÃO DOS ARQUIVOS SQL (TODAS AS BASES)
============================================================
Lê colaboradores.csv e gera 8 arquivos SQL:

  colaboradores.sql
  folha_pagamento.sql
  treinamentos.sql
  avaliacao_desempenho.sql
  absenteismo.sql
  recrutamento_selecao.sql
  metas.sql
  headcount_orcado.sql
  tabela_salarial.sql

Execução recomendada:
    python 02_gerar_sql.py

Os arquivos são gravados diretamente em disco (streaming)
para suportar o volume de ~5,8 milhões de linhas da folha.

Dependências: pandas, numpy, openpyxl
============================================================
"""

import os
import subprocess
import pandas as pd
import numpy as np
import random
from datetime import date, timedelta

random.seed(123)
np.random.seed(123)

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
INPUT_COLAB       = "colaboradores.csv"
PATH_SAL_CLT      = "tabela_salarial_funcao.xlsx"
PATH_SAL_APRENDIZ = "tabela_salarial_funcao_aprendizes.xlsx"
PATH_SAL_ESTAGIO  = "tabela_salarial_funcao_estagiario.xlsx"
OUTPUT_DIR        = "sql_output"
TODAY             = date(2026, 4, 18)
BATCH_SIZE        = 500   # linhas por INSERT

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── HELPER: escape de valores SQL ───────────────────────────────────────────
def ev(val) -> str:
    """Converte um valor Python para literal SQL seguro."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "NULL"
    if isinstance(val, (int, np.integer)):
        return str(int(val))
    if isinstance(val, (float, np.floating)):
        return f"{val:.2f}"
    s = str(val).replace("'", "''")
    return f"'{s}'"


def write_batch(f, table: str, batch: list):
    """Escreve um batch de tuplas como INSERT INTO ... VALUES ..."""
    if not batch:
        return
    f.write(f"INSERT INTO {table} VALUES\n")
    f.write(",\n".join("(" + ", ".join(ev(x) for x in row) + ")" for row in batch))
    f.write(";\n\n")


# ─── CARREGA BASE DE COLABORADORES ────────────────────────────────────────────
print("Carregando colaboradores.csv...")
df = pd.read_csv(INPUT_COLAB)
df["data_admissao"] = pd.to_datetime(df["data_admissao"])
df["data_demissao"] = pd.to_datetime(df["data_demissao"])
df["data_nascimento"] = pd.to_datetime(df["data_nascimento"])
print(f"  {len(df)} colaboradores carregados.")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. COLABORADORES
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[1/9] colaboradores.sql ...")
CREATE_COLABORADORES = """CREATE TABLE IF NOT EXISTS colaboradores (
    matricula_colaborador VARCHAR(8) PRIMARY KEY,
    nome_colaborador      VARCHAR(100),
    sexo                  VARCHAR(10),
    data_nascimento       DATE,
    idade_na_contratacao  INT,
    idade                 INT,
    cidade_moradia        VARCHAR(50),
    estado_moradia        VARCHAR(2),
    pais                  VARCHAR(20),
    naturalidade          VARCHAR(100),
    data_admissao         DATE,
    data_demissao         DATE,
    situacao              VARCHAR(20),
    motivo_desligamento   VARCHAR(60),
    tipo_desligamento     VARCHAR(40),
    tipo_contratacao      VARCHAR(10),
    escolaridade          VARCHAR(40),
    departamento          VARCHAR(20),
    centro_custo          VARCHAR(40),
    funcao                VARCHAR(60),
    salario_contratacao   DECIMAL(10,2),
    vale_alimentacao      DECIMAL(8,2),
    auxilio_combustivel   DECIMAL(8,2),
    auxilio_creche        DECIMAL(8,2),
    loja                  VARCHAR(60),
    cidade_loja           VARCHAR(50),
    estado_loja           VARCHAR(2),
    pais_loja             VARCHAR(20)
);"""

cols = df.columns.tolist()
path = os.path.join(OUTPUT_DIR, "colaboradores.sql")
with open(path, "w", encoding="utf-8") as f:
    f.write(CREATE_COLABORADORES + "\n\n")
    batch = []
    for row in df.values.tolist():
        d = dict(zip(cols, row))
        batch.append((
            d["matricula_colaborador"], d["nome_colaborador"], d["sexo"],
            str(d["data_nascimento"])[:10] if str(d["data_nascimento"]) != "NaT" else None,
            int(d["idade_na_contratacao"]) if pd.notna(d["idade_na_contratacao"]) else None,
            int(d["idade"]) if pd.notna(d["idade"]) else None,
            d["cidade_moradia"], d["estado_moradia"], d["pais"], d["naturalidade"],
            str(d["data_admissao"])[:10] if str(d["data_admissao"]) != "NaT" else None,
            str(d["data_demissao"])[:10] if pd.notna(d["data_demissao"]) else None,
            d["situacao"],
            d["motivo_desligamento"] if pd.notna(d["motivo_desligamento"]) else None,
            d["tipo_desligamento"] if pd.notna(d["tipo_desligamento"]) else None,
            d["tipo_contratacao"], d["escolaridade"], d["departamento"],
            d["centro_custo"], d["funcao"],
            float(d["salario_contratacao"]), float(d["vale_alimentacao"]),
            float(d["auxilio_combustivel"]), float(d["auxilio_creche"]),
            d["loja"], d["cidade_loja"], d["estado_loja"], d["pais_loja"],
        ))
        if len(batch) >= BATCH_SIZE:
            write_batch(f, "colaboradores", batch)
            batch = []
    write_batch(f, "colaboradores", batch)
print(f"  OK — {os.path.getsize(path)/1024/1024:.1f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. FOLHA DE PAGAMENTO
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[2/9] folha_pagamento.sql  (pode demorar alguns minutos)...")

CREATE_FOLHA = """CREATE TABLE IF NOT EXISTS folha_pagamento (
    id                    BIGINT AUTO_INCREMENT PRIMARY KEY,
    matricula_colaborador VARCHAR(8),
    nome_colaborador      VARCHAR(100),
    mes_ano               VARCHAR(7),
    salario_base          DECIMAL(10,2),
    horas_extras_qtd      DECIMAL(6,2),
    horas_extras_valor    DECIMAL(10,2),
    adicional_noturno     DECIMAL(10,2),
    bonus                 DECIMAL(10,2),
    comissoes             DECIMAL(10,2),
    vale_alimentacao      DECIMAL(8,2),
    vale_transporte       DECIMAL(8,2),
    auxilio_combustivel   DECIMAL(8,2),
    auxilio_creche        DECIMAL(8,2),
    inss                  DECIMAL(10,2),
    irrf                  DECIMAL(10,2),
    total_proventos       DECIMAL(10,2),
    total_descontos       DECIMAL(10,2),
    salario_liquido       DECIMAL(10,2),
    fgts                  DECIMAL(10,2),
    custo_total_empresa   DECIMAL(10,2),
    centro_custo          VARCHAR(40),
    departamento          VARCHAR(20),
    funcao                VARCHAR(60),
    tipo_contratacao      VARCHAR(10)
);"""


def calc_inss(sal: float) -> float:
    """INSS progressivo simplificado (tabela 2025)."""
    if sal <= 1412.00:    return round(sal * 0.075, 2)
    if sal <= 2666.68:    return round(sal * 0.090, 2)
    if sal <= 4000.03:    return round(sal * 0.120, 2)
    if sal <= 7786.02:    return round(sal * 0.140, 2)
    return round(7786.02  * 0.140, 2)


def calc_irrf(base: float) -> float:
    """IRRF sobre base (salário − INSS)."""
    if base <= 2259.20:   return 0.0
    if base <= 2826.65:   return round(base * 0.075 - 169.44, 2)
    if base <= 3751.05:   return round(base * 0.150 - 381.44, 2)
    if base <= 4664.68:   return round(base * 0.225 - 662.77, 2)
    return round(base * 0.275 - 896.00, 2)


path = os.path.join(OUTPUT_DIR, "folha_pagamento.sql")
row_count = 0
with open(path, "w", encoding="utf-8") as f:
    f.write(CREATE_FOLHA + "\n\n")
    batch = []

    for idx, r in df.iterrows():
        if idx % 10_000 == 0:
            print(f"    Colaborador {idx}/{len(df)} — linhas até agora: {row_count:,}")

        adm     = r["data_admissao"]
        dem     = r["data_demissao"]
        dept    = r["departamento"]
        funcao  = r["funcao"]
        tc      = r["tipo_contratacao"]

        start_mes = date(max(2005, adm.year), adm.month, 1)
        end_mes   = date(dem.year, dem.month, 1) if pd.notna(dem) else date(2026, 12, 1)

        sal_atual   = float(r["salario_contratacao"])
        last_year   = start_mes.year
        va          = float(r["vale_alimentacao"])
        vt_bruto    = round(sal_atual * 0.04, 2)
        auxc        = float(r["auxilio_combustivel"])
        creche      = float(r["auxilio_creche"])
        is_gestao   = any(x in funcao for x in ["Coordenador","Gerente","Diretor"])
        is_comercial_vendas = dept == "Comercial" and "Vendas" in str(r["centro_custo"])

        current = start_mes
        while current <= end_mes and current <= date(2026, 12, 1):
            # Reajuste salarial anual
            if current.year > last_year:
                sal_atual = round(sal_atual * (1 + random.uniform(0.025, 0.07)), 2)
                last_year = current.year

            mes_ano = f"{current.year}-{current.month:02d}"

            # Horas extras
            he_qtd = 0.0
            if dept in ["Operações","Comercial"] and random.random() < 0.35:
                he_qtd = round(random.uniform(4, 18), 1)
            elif random.random() < 0.12:
                he_qtd = round(random.uniform(2, 8), 1)
            he_val = round(he_qtd * (sal_atual / 220) * 1.5, 2) if he_qtd > 0 else 0.0

            # Adicional noturno (apenas Operações)
            ad_not = round(sal_atual * random.uniform(0, 0.025), 2) if dept == "Operações" else 0.0

            # Bônus trimestral (gestão)
            bonus = round(sal_atual * random.uniform(0.05, 0.25), 2) \
                    if is_gestao and current.month in [3,6,9,12] else 0.0

            # Comissões (Comercial Vendas)
            comissoes = round(sal_atual * random.uniform(0.02, 0.12), 2) \
                        if is_comercial_vendas and random.random() < 0.65 else 0.0

            inss        = calc_inss(sal_atual)
            irrf        = max(0.0, calc_irrf(sal_atual - inss))
            vt_desc     = min(vt_bruto * 0.06, vt_bruto)

            total_prov  = round(sal_atual + he_val + ad_not + bonus + comissoes + va + auxc + creche, 2)
            total_desc  = round(inss + irrf + vt_desc, 2)
            sal_liq     = round(total_prov - total_desc, 2)
            fgts        = round(sal_atual * 0.08, 2)
            custo_total = round(total_prov + fgts + sal_atual * 0.20, 2)

            batch.append((
                None,
                r["matricula_colaborador"], r["nome_colaborador"], mes_ano,
                sal_atual, he_qtd, he_val, ad_not, bonus, comissoes,
                va, vt_bruto, auxc, creche, inss, irrf,
                total_prov, total_desc, sal_liq, fgts, custo_total,
                r["centro_custo"], dept, funcao, tc,
            ))
            row_count += 1

            if len(batch) >= BATCH_SIZE:
                write_batch(f, "folha_pagamento", batch)
                batch = []

            current = date(current.year + 1, 1, 1) if current.month == 12 \
                      else date(current.year, current.month + 1, 1)

    write_batch(f, "folha_pagamento", batch)

print(f"  OK — {row_count:,} linhas — {os.path.getsize(path)/1024/1024:.0f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TREINAMENTOS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[3/9] treinamentos.sql ...")

CREATE_TREI = """CREATE TABLE IF NOT EXISTS treinamentos (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    matricula_colaborador VARCHAR(8),
    nome_colaborador      VARCHAR(100),
    funcao                VARCHAR(60),
    centro_custo          VARCHAR(40),
    departamento          VARCHAR(20),
    curso                 VARCHAR(100),
    data_inicio           DATE,
    data_fim              DATE,
    horas_treinamento     INT,
    status                VARCHAR(20)
);"""

CURSOS = {
    "Administrativo": ["Excel Avançado","Power BI","Gestão do Tempo","Comunicação Corporativa",
                       "Compliance e Ética","Liderança Situacional","Negociação Avançada",
                       "Gestão de Projetos","Legislação Trabalhista","Excel para RH"],
    "Operações":      ["Segurança do Trabalho NR-35","Primeiros Socorros","Operação de Empilhadeira",
                       "Gestão de Estoques","Logística Integrada","ISO 9001","5S Avançado",
                       "Lean Manufacturing","PPRA/PCMSO","NR-10"],
    "Tecnologia":     ["Python para Dados","SQL Avançado","Power BI Developer","Azure Fundamentals",
                       "Scrum Certification","Docker & Kubernetes","Git e GitHub","Clean Code",
                       "Segurança da Informação","Machine Learning Básico"],
    "Comercial":      ["Técnicas de Vendas","Atendimento ao Cliente","Prevenção de Perdas",
                       "Operação de Caixa","Vitrinismo e Merchandising","Gestão de Metas",
                       "Fidelização de Clientes","Postura Profissional","Controle de Estoque",
                       "Liderança em Varejo"],
}
CURSOS_GERAIS = ["Diversidade e Inclusão","Ética e Conduta","LGPD",
                 "Integração de Novos Colaboradores","Saúde Mental no Trabalho",
                 "Feedback Eficaz","Gestão de Conflitos"]

path = os.path.join(OUTPUT_DIR, "treinamentos.sql")
row_count = 0
with open(path, "w", encoding="utf-8") as f:
    f.write(CREATE_TREI + "\n\n")
    batch = []
    for _, r in df.iterrows():
        adm    = r["data_admissao"]
        dem    = r["data_demissao"]
        end_dt = (dem if pd.notna(dem) else pd.Timestamp("2026-12-01"))
        max_s  = min(end_dt, pd.Timestamp("2026-12-01"))
        if adm >= max_s:
            continue

        dept       = r["departamento"]
        pool       = CURSOS.get(dept, CURSOS_GERAIS) + CURSOS_GERAIS
        usados     = set()
        n_cur      = random.randint(1, 6)

        for _ in range(n_cur):
            disp = [c for c in pool if c not in usados]
            if not disp: break
            curso = random.choice(disp)
            usados.add(curso)

            offset   = random.randint(0, (max_s - adm).days)
            t_start  = (adm + timedelta(days=offset)).date()
            horas    = random.choice([4, 8, 16, 24, 32, 40])
            t_end    = t_start + timedelta(days=max(1, horas // 8))
            status   = "Concluído" if t_end <= TODAY else "Em Andamento"

            batch.append((
                None,
                r["matricula_colaborador"], r["nome_colaborador"],
                r["funcao"], r["centro_custo"], dept,
                curso, str(t_start), str(t_end), horas, status,
            ))
            row_count += 1
            if len(batch) >= BATCH_SIZE:
                write_batch(f, "treinamentos", batch)
                batch = []

    write_batch(f, "treinamentos", batch)
print(f"  OK — {row_count:,} linhas — {os.path.getsize(path)/1024/1024:.1f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. AVALIAÇÃO DE DESEMPENHO
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[4/9] avaliacao_desempenho.sql ...")

CREATE_AVAL = """CREATE TABLE IF NOT EXISTS avaliacao_desempenho (
    id                           INT AUTO_INCREMENT PRIMARY KEY,
    matricula_colaborador        VARCHAR(8),
    nome_colaborador             VARCHAR(100),
    ano                          INT,
    ciclo_avaliacao              VARCHAR(10),
    data_da_avaliacao            DATE,
    centro_custo                 VARCHAR(40),
    departamento                 VARCHAR(20),
    funcao                       VARCHAR(60),
    gestor_avaliador             VARCHAR(100),
    tipo_avaliacao               VARCHAR(20),
    comunicacao                  DECIMAL(4,1),
    trabalho_em_equipe           DECIMAL(4,1),
    proatividade                 DECIMAL(4,1),
    lideranca                    DECIMAL(4,1),
    conhecimento_tecnico         DECIMAL(4,1),
    organizacao                  DECIMAL(4,1),
    nota_final                   DECIMAL(4,1),
    classificacao_desempenho     VARCHAR(15),
    elegivel_promocao            VARCHAR(3),
    recomendacao_ajuste_salarial VARCHAR(3),
    percentual_ajuste            DECIMAL(5,2),
    risco_desligamento           VARCHAR(6),
    pontos_fortes                VARCHAR(200),
    pontos_desenvolvimento       VARCHAR(200)
);"""

PONTOS_F = ["Proatividade e iniciativa","Comunicacao clara","Trabalho em equipe",
            "Conhecimento tecnico solido","Comprometimento com resultados",
            "Organizacao e disciplina","Lideranca natural","Foco no cliente",
            "Adaptabilidade","Pontualidade e responsabilidade"]
PONTOS_D = ["Desenvolver lideranca","Melhorar gestao do tempo","Aprimorar comunicacao",
            "Conhecimento em TI","Delegacao de tarefas","Melhorar planejamento",
            "Visao estrategica","Investir em certificacoes","Melhorar apresentacoes",
            "Inteligencia emocional"]

# Lookup de gestores por departamento
gestores_por_dept = {}
df_gest = df[df["funcao"].str.contains("Gerente|Coordenador|Diretor", na=False) &
             (df["situacao"] == "Ativo")]
for dept in df["departamento"].unique():
    nomes = df_gest[df_gest["departamento"] == dept]["nome_colaborador"].tolist()
    gestores_por_dept[dept] = nomes if nomes else ["Gestão de RH"]

TIPOS_AVAL   = ["Gestor","Autoavaliacao","Pares","360"]
TIPOS_WEIGHT = [0.50, 0.25, 0.15, 0.10]

path = os.path.join(OUTPUT_DIR, "avaliacao_desempenho.sql")
row_count = 0
with open(path, "w", encoding="utf-8") as f:
    f.write(CREATE_AVAL + "\n\n")
    batch = []

    for _, r in df.iterrows():
        adm      = r["data_admissao"]
        dem      = r["data_demissao"]
        end_year = min(2026, int(str(dem if pd.notna(dem) else "2026-12-31")[:4]))
        is_gest  = any(x in str(r["funcao"]) for x in ["Coordenador","Gerente","Diretor"])
        gestor   = random.choice(gestores_por_dept.get(r["departamento"], ["Gestão de RH"]))

        for ano in range(max(2005, adm.year), end_year + 1):
            if random.random() > 0.68:
                continue
            ciclos = [f"{ano}.1", f"{ano}.2"] if random.random() < 0.40 else [str(ano)]

            for ciclo in ciclos:
                if ".1" in ciclo:
                    d_aval = date(ano, random.randint(5, 7),  random.randint(1, 28))
                elif ".2" in ciclo:
                    d_aval = date(ano, random.randint(10, 12), random.randint(1, 28))
                else:
                    d_aval = date(ano, random.randint(11, 12), random.randint(1, 28))

                if d_aval > TODAY or d_aval < adm.date():
                    continue

                tipo   = random.choices(TIPOS_AVAL, weights=TIPOS_WEIGHT)[0]
                base   = max(3.0, min(10.0, round(random.gauss(7.5, 1.5), 1)))
                def sc(): return max(1.0, min(10.0, round(base + random.gauss(0, 0.8), 1)))

                com = sc(); eq = sc(); prot = sc(); lid = sc() if is_gest else None
                tec = sc(); org = sc()
                scores = [com, eq, prot, tec, org] + ([lid] if lid else [])
                nf     = round(sum(scores) / len(scores), 1)

                cl    = "Excelente" if nf >= 9 else ("Alto" if nf >= 7.5 else ("Medio" if nf >= 6 else "Baixo"))
                eleg  = "Sim" if nf >= 8.5 and random.random() < 0.6 else "Nao"
                rec   = "Sim" if nf >= 8.0 and random.random() < 0.5 else "Nao"
                perc  = round(random.uniform(3, 15), 2) if rec == "Sim" else 0.0
                risco = "Alto" if nf < 5 else ("Medio" if nf < 7 else "Baixo")

                batch.append((
                    None,
                    r["matricula_colaborador"], r["nome_colaborador"],
                    ano, ciclo, str(d_aval),
                    r["centro_custo"], r["departamento"], r["funcao"],
                    gestor, tipo,
                    com, eq, prot, lid, tec, org, nf, cl,
                    eleg, rec, perc, risco,
                    random.choice(PONTOS_F) + "; " + random.choice(PONTOS_F),
                    random.choice(PONTOS_D) + "; " + random.choice(PONTOS_D),
                ))
                row_count += 1
                if len(batch) >= BATCH_SIZE:
                    write_batch(f, "avaliacao_desempenho", batch)
                    batch = []

    write_batch(f, "avaliacao_desempenho", batch)
print(f"  OK — {row_count:,} linhas — {os.path.getsize(path)/1024/1024:.1f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ABSENTEÍSMO
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[5/9] absenteismo.sql ...")

CREATE_ABS = """CREATE TABLE IF NOT EXISTS absenteismo (
    id                       INT AUTO_INCREMENT PRIMARY KEY,
    matricula_colaborador    VARCHAR(8),
    nome_colaborador         VARCHAR(100),
    funcao                   VARCHAR(60),
    data_inicio_afastamento  DATE,
    data_final_afastamento   DATE,
    total_dias_afastamento   INT,
    tipo_falta               VARCHAR(40),
    horas_perdidas           DECIMAL(6,2),
    justificada              VARCHAR(3),
    cid                      VARCHAR(10),
    departamento             VARCHAR(20),
    centro_custo             VARCHAR(40),
    mes_ano                  VARCHAR(7),
    tipo_ocorrencia          VARCHAR(20)
);"""

TIPOS_FALTA = [
    ("Atestado medico",       "Sim", "Falta",           [1,1,1,2,3,5,7,15,30]),
    ("Falta injustificada",   "Nao", "Falta",           [1,1,1]),
    ("Atraso",                "Nao", "Atraso",          [1]),
    ("Licenca maternidade",   "Sim", "Falta",           [120,180]),
    ("Licenca paternidade",   "Sim", "Falta",           [5,20]),
    ("Acidente de trabalho",  "Sim", "Falta",           [3,7,15,30,60]),
    ("Saida antecipada",      "Nao", "Saida antecipada",[1]),
    ("Luto",                  "Sim", "Falta",           [3,5]),
    ("Consulta medica",       "Sim", "Atraso",          [1]),
]
TIPO_W = [0.40, 0.15, 0.15, 0.04, 0.03, 0.03, 0.10, 0.02, 0.08]
CIDS   = ["Z00","J06","K59","M54","F43","J45","R51","K21","M79","J18","F32","Z34"]

path = os.path.join(OUTPUT_DIR, "absenteismo.sql")
row_count = 0
with open(path, "w", encoding="utf-8") as f:
    f.write(CREATE_ABS + "\n\n")
    batch = []

    for _, r in df.iterrows():
        adm     = r["data_admissao"]
        dem     = r["data_demissao"]
        end_dt  = (dem if pd.notna(dem) else pd.Timestamp("2026-04-17")).date()
        start_dt = adm.date()
        if start_dt >= end_dt:
            continue

        tenure_y  = max(1, (end_dt - start_dt).days // 365)
        n_abs     = random.randint(0, min(8, tenure_y * 2))

        for _ in range(n_abs):
            days_range = (end_dt - start_dt).days
            if days_range <= 0: break
            abs_start = start_dt + timedelta(days=random.randint(0, days_range))
            if abs_start.weekday() >= 5: continue  # pula fim de semana

            t_idx  = random.choices(range(len(TIPOS_FALTA)), weights=TIPO_W)[0]
            tipo_n, just, tipo_oc, dias_opts = TIPOS_FALTA[t_idx]

            if tipo_n == "Licenca maternidade" and r["sexo"] != "Feminino": continue
            if tipo_n == "Licenca paternidade" and r["sexo"] != "Masculino": continue

            n_dias   = random.choice(dias_opts)
            abs_end  = min(abs_start + timedelta(days=n_dias - 1), end_dt)
            horas    = n_dias * 8.0 if tipo_oc == "Falta" else round(random.uniform(0.5, 4), 1)
            cid      = random.choice(CIDS) if just == "Sim" and "medico" in tipo_n.lower() else None
            mes_ano  = f"{abs_start.year}-{abs_start.month:02d}"

            batch.append((
                None,
                r["matricula_colaborador"], r["nome_colaborador"], r["funcao"],
                str(abs_start), str(abs_end), n_dias, tipo_n, horas,
                just, cid, r["departamento"], r["centro_custo"], mes_ano, tipo_oc,
            ))
            row_count += 1
            if len(batch) >= BATCH_SIZE:
                write_batch(f, "absenteismo", batch)
                batch = []

    write_batch(f, "absenteismo", batch)
print(f"  OK — {row_count:,} linhas — {os.path.getsize(path)/1024/1024:.1f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. RECRUTAMENTO E SELEÇÃO
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[6/9] recrutamento_selecao.sql ...")

CREATE_REC = """CREATE TABLE IF NOT EXISTS recrutamento_selecao (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    id_vaga               VARCHAR(12),
    funcao                VARCHAR(60),
    centro_custo          VARCHAR(40),
    departamento          VARCHAR(20),
    gestor_solicitante    VARCHAR(100),
    id_candidato          VARCHAR(12),
    nome_candidato        VARCHAR(100),
    sexo                  VARCHAR(10),
    idade                 INT,
    cidade                VARCHAR(50),
    estado                VARCHAR(2),
    fonte_candidato       VARCHAR(20),
    data_candidatura      DATE,
    etapa_processo        VARCHAR(20),
    status_candidato      VARCHAR(15),
    data_triagem          DATE,
    data_entrevista_rh    DATE,
    data_entrevista_gestor DATE,
    data_proposta         DATE,
    data_contratacao      DATE,
    tempo_contratacao_dias INT,
    tempo_por_etapa       INT,
    aprovado              VARCHAR(3),
    salario_oferecido     DECIMAL(10,2),
    nivel_vaga            VARCHAR(15),
    tipo_contratacao      VARCHAR(10)
);"""

FONTES   = ["LinkedIn","Indicacao","Site","Consultoria","Indeed","Vagas.com","Catho"]
FONTE_W  = [0.30, 0.20, 0.15, 0.10, 0.10, 0.10, 0.05]

# Lookup de gerentes por dept/cc para gestor_solicitante
df_ger = df[df["funcao"].str.contains("Gerente", na=False)].copy()
df_dir = df[df["funcao"].str.contains("Diretor", na=False)].copy()

def get_gestor_solicitante(dept: str, cc: str, adm_date) -> str:
    cands = df_ger[(df_ger["departamento"] == dept) &
                   (df_ger["centro_custo"]  == cc) &
                   (df_ger["data_admissao"] <= adm_date)]
    if cands.empty:
        cands = df_ger[(df_ger["departamento"] == dept) &
                       (df_ger["data_admissao"] <= adm_date)]
    if cands.empty:
        mapa = {"Administrativo":"Diretor Administrativo","Operações":"Diretor de Operações",
                "Tecnologia":"Diretor de Tecnologia","Comercial":"Diretor Comercial"}
        cands = df_dir[(df_dir["funcao"] == mapa.get(dept,"")) &
                       (df_dir["data_admissao"] <= adm_date)]
    if cands.empty:
        return "Recrutamento e Seleção"
    return cands.iloc[random.randint(0, len(cands) - 1)]["nome_colaborador"]


def nivel_vaga(funcao: str) -> str:
    f = funcao.lower()
    if any(x in f for x in ["diretor","gerente","coordenador"]): return "Gestao"
    if any(x in f for x in ["analista","engenheiro","arquiteto","cientista",
                              "controller","business","scrum","product","pmo",
                              "tech","advogado","medico","enfermeiro"]): return "Analista"
    return "Operacional"


path = os.path.join(OUTPUT_DIR, "recrutamento_selecao.sql")
row_count = 0
with open(path, "w", encoding="utf-8") as f:
    f.write(CREATE_REC + "\n\n")
    batch = []

    for idx, r in df.iterrows():
        adm      = r["data_admissao"]
        adm_date = adm.date()
        days_bef = random.randint(10, 60)
        cand_d   = adm_date - timedelta(days=days_bef)
        if cand_d.weekday() >= 5:
            cand_d -= timedelta(days=cand_d.weekday() - 4)

        triagem   = cand_d + timedelta(days=random.randint(2, 7))
        ent_rh    = triagem + timedelta(days=random.randint(3, 10))
        ent_gest  = ent_rh  + timedelta(days=random.randint(3, 10))
        proposta  = ent_gest + timedelta(days=random.randint(2, 7))
        tempo_tot = (adm_date - cand_d).days

        batch.append((
            None,
            f"VAG{idx+1:07d}", r["funcao"], r["centro_custo"], r["departamento"],
            get_gestor_solicitante(r["departamento"], r["centro_custo"], adm),
            f"CAND{idx+1:07d}", r["nome_colaborador"], r["sexo"],
            int(r["idade_na_contratacao"]), r["cidade_loja"], r["estado_loja"],
            random.choices(FONTES, weights=FONTE_W)[0],
            str(cand_d), "Contratado", "Aprovado",
            str(triagem), str(ent_rh), str(ent_gest), str(proposta), str(adm_date),
            tempo_tot, tempo_tot // 5,
            "Sim", float(r["salario_contratacao"]),
            nivel_vaga(r["funcao"]), r["tipo_contratacao"],
        ))
        row_count += 1
        if len(batch) >= BATCH_SIZE:
            write_batch(f, "recrutamento_selecao", batch)
            batch = []

    write_batch(f, "recrutamento_selecao", batch)
print(f"  OK — {row_count:,} linhas — {os.path.getsize(path)/1024/1024:.1f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. METAS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[7/9] metas.sql ...")

CREATE_METAS = """CREATE TABLE IF NOT EXISTS metas (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    ano                   INT,
    mes                   INT,
    centro_custo          VARCHAR(40),
    departamento          VARCHAR(20),
    nome_loja             VARCHAR(60),
    turnover_percentual   DECIMAL(5,2),
    admissoes_quantidade  INT,
    demissoes_quantidade  INT,
    horas_extras          DECIMAL(8,2),
    absenteismo_percentual DECIMAL(5,2),
    treinamento_horas     DECIMAL(8,2)
);"""

combos = df[["departamento","centro_custo","loja"]].drop_duplicates()
rows_m = []

for _, row in combos.iterrows():
    dept = row["departamento"]
    for ano in range(2005, 2027):
        for mes in range(1, 13):
            alta = mes in [1, 4, 7, 12]
            mult = 1.25 if alta else 1.0
            if dept == "Comercial":
                adm  = int(random.randint(3, 8)  * mult)
                dem  = random.randint(2, 6)
                he   = round(random.uniform(80, 200) * mult, 2)
                abs_ = round(random.uniform(1.5, 4.0), 2)
                trn  = round(random.uniform(20, 60) * mult, 2)
            elif dept == "Operações":
                adm  = int(random.randint(2, 6)  * mult)
                dem  = random.randint(1, 4)
                he   = round(random.uniform(100, 300) * mult, 2)
                abs_ = round(random.uniform(2.0, 5.0), 2)
                trn  = round(random.uniform(30, 80), 2)
            elif dept == "Tecnologia":
                adm  = random.randint(1, 3);  dem = random.randint(0, 2)
                he   = round(random.uniform(20, 80), 2)
                abs_ = round(random.uniform(0.8, 2.5), 2)
                trn  = round(random.uniform(40, 120), 2)
            else:  # Administrativo
                adm  = random.randint(1, 4);  dem = random.randint(0, 3)
                he   = round(random.uniform(15, 60), 2)
                abs_ = round(random.uniform(1.0, 3.0), 2)
                trn  = round(random.uniform(25, 70), 2)

            turnover = round((dem / max(1, adm + dem)) * 100, 2)
            rows_m.append((None, ano, mes, row["centro_custo"], dept, row["loja"],
                           turnover, adm, dem, he, abs_, trn))

path = os.path.join(OUTPUT_DIR, "metas.sql")
with open(path, "w", encoding="utf-8") as f:
    f.write(CREATE_METAS + "\n\n")
    for i in range(0, len(rows_m), BATCH_SIZE):
        write_batch(f, "metas", rows_m[i:i+BATCH_SIZE])
print(f"  OK — {len(rows_m):,} linhas — {os.path.getsize(path)/1024/1024:.1f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. HEADCOUNT ORÇADO
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[8/9] headcount_orcado.sql ...")

CREATE_HC = """CREATE TABLE IF NOT EXISTS headcount_orcado (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    ano                   INT,
    mes                   INT,
    nome_loja             VARCHAR(60),
    departamento          VARCHAR(20),
    centro_custo          VARCHAR(40),
    funcao                VARCHAR(60),
    total_headcount_orcado INT
);"""

combos_hc = df[["loja","departamento","centro_custo","funcao"]].drop_duplicates()
rows_hc   = []

for _, row in combos_hc.iterrows():
    f_l = str(row["funcao"]).lower()
    if any(x in f_l for x in ["diretor","gerente"]): base = 1
    elif "coordenador" in f_l:                        base = random.randint(1, 3)
    elif any(x in f_l for x in ["analista","engenheiro","advogado"]): base = random.randint(2, 8)
    else:                                              base = random.randint(5, 25)

    for ano in range(2005, 2027):
        for mes in range(1, 13):
            alta = mes in [1, 4, 7, 12]
            if alta and row["departamento"] == "Comercial":
                hc = max(1, int(base * random.uniform(1.15, 1.35)))
            elif alta and row["departamento"] == "Operações":
                hc = max(1, int(base * random.uniform(1.05, 1.20)))
            else:
                hc = max(1, int(base * random.uniform(0.90, 1.10)))
            rows_hc.append((None, ano, mes, row["loja"], row["departamento"],
                            row["centro_custo"], row["funcao"], hc))

path = os.path.join(OUTPUT_DIR, "headcount_orcado.sql")
with open(path, "w", encoding="utf-8") as f:
    f.write(CREATE_HC + "\n\n")
    for i in range(0, len(rows_hc), BATCH_SIZE):
        write_batch(f, "headcount_orcado", rows_hc[i:i+BATCH_SIZE])
print(f"  OK — {len(rows_hc):,} linhas — {os.path.getsize(path)/1024/1024:.1f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# 9. TABELA SALARIAL
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[9/9] tabela_salarial.sql ...")

CREATE_SAL = """CREATE TABLE IF NOT EXISTS tabela_salarial (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    tipo_contratacao VARCHAR(10),
    funcao           VARCHAR(60),
    cidade           VARCHAR(50),
    salario          DECIMAL(10,2)
);"""

rows_sal = []
for fname, tipo in [
    (PATH_SAL_CLT,      "CLT"),
    (PATH_SAL_APRENDIZ, "Aprendiz"),
    (PATH_SAL_ESTAGIO,  "Estágio"),
]:
    df_s = pd.read_excel(fname)
    cidades = [c for c in df_s.columns if c != "Função"]
    for _, row in df_s.iterrows():
        for cidade in cidades:
            sal = row[cidade]
            if pd.notna(sal) and sal > 0:
                rows_sal.append((None, tipo, row["Função"], cidade, float(sal)))

path = os.path.join(OUTPUT_DIR, "tabela_salarial.sql")
with open(path, "w", encoding="utf-8") as f:
    f.write(CREATE_SAL + "\n\n")
    for i in range(0, len(rows_sal), BATCH_SIZE):
        write_batch(f, "tabela_salarial", rows_sal[i:i+BATCH_SIZE])
print(f"  OK — {len(rows_sal):,} linhas — {os.path.getsize(path)/1024/1024:.2f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPRIME E EMPACOTA EM ZIP
# ═══════════════════════════════════════════════════════════════════════════════
print("\nComprimindo arquivos SQL...")
import zipfile, gzip, shutil

zip_path = "RH_DataBase_SQL.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for sql_file in sorted(os.listdir(OUTPUT_DIR)):
        if sql_file.endswith(".sql"):
            full = os.path.join(OUTPUT_DIR, sql_file)
            gz   = full + ".gz"
            with open(full, "rb") as f_in, gzip.open(gz, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            zf.write(gz, sql_file.replace(".sql", ".sql.gz"))
            print(f"  {sql_file}.gz")

print(f"\n✅ Concluído! ZIP: {zip_path}  ({os.path.getsize(zip_path)/1024/1024:.0f} MB)")
