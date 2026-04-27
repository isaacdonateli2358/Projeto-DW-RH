"""
============================================================
SCRIPT 1 — GERAÇÃO DA BASE DE COLABORADORES
============================================================
Gera 50.000 registros sintéticos de colaboradores seguindo
todas as regras de negócio definidas no briefing de RH.

Dependências:
    pip install pandas openpyxl numpy

Entrada:
    - tabela_salarial_funcao.xlsx
    - tabela_salarial_funcao_aprendizes.xlsx
    - tabela_salarial_funcao_estagiario.xlsx

Saída:
    - colaboradores.csv
    - lookup.csv  (subset para uso pelos demais scripts)
============================================================
"""

import pandas as pd
import numpy as np
import random
from datetime import date, timedelta

random.seed(42)
np.random.seed(42)

# ─── PATHS ────────────────────────────────────────────────────────────────────
PATH_SAL_CLT      = "tabela_salarial_funcao.xlsx"
PATH_SAL_APRENDIZ = "tabela_salarial_funcao_aprendizes.xlsx"
PATH_SAL_ESTAGIO  = "tabela_salarial_funcao_estagiario.xlsx"
OUTPUT_COLAB      = "colaboradores.csv"
OUTPUT_LOOKUP     = "lookup.csv"

TODAY             = date(2026, 4, 18)
ADMISSAO_START    = date(2005, 1, 1)
ADMISSAO_END      = date(2026, 12, 31)
TARGET_RECORDS    = 50_000

# ─── MAPEAMENTO LOJAS ─────────────────────────────────────────────────────────
LOJAS = {
    "Matriz":                         {"cidade": "São Paulo",         "estado": "SP"},
    "Centro Distribuição – Campinas":  {"cidade": "Campinas",          "estado": "SP"},
    "Centro Distribuição – Maringá":   {"cidade": "Maringá",           "estado": "PR"},
    "Centro Distribuição – Santos":    {"cidade": "Santos",            "estado": "SP"},
    "Loja Anápolis":                   {"cidade": "Anápolis",          "estado": "GO"},
    "Loja Aracaju":                    {"cidade": "Aracaju",           "estado": "SE"},
    "Loja Belém":                      {"cidade": "Belém",             "estado": "PA"},
    "Loja Belo Horizonte":             {"cidade": "Belo Horizonte",    "estado": "MG"},
    "Loja Boa Vista":                  {"cidade": "Boa Vista",         "estado": "RR"},
    "Loja Brasília":                   {"cidade": "Brasília",          "estado": "DF"},
    "Loja Campinas":                   {"cidade": "Campinas",          "estado": "SP"},
    "Loja Campo Grande":               {"cidade": "Campo Grande",      "estado": "MS"},
    "Loja Caruaru":                    {"cidade": "Caruaru",           "estado": "PE"},
    "Loja Caxias do Sul":              {"cidade": "Caxias do Sul",     "estado": "RS"},
    "Loja Cuiabá":                     {"cidade": "Cuiabá",            "estado": "MT"},
    "Loja Curitiba":                   {"cidade": "Curitiba",          "estado": "PR"},
    "Loja Feira de Santana":           {"cidade": "Feira de Santana",  "estado": "BA"},
    "Loja Florianópolis":              {"cidade": "Florianópolis",     "estado": "SC"},
    "Loja Fortaleza":                  {"cidade": "Fortaleza",         "estado": "CE"},
    "Loja Goiânia":                    {"cidade": "Goiânia",           "estado": "GO"},
    "Loja João Pessoa":                {"cidade": "João Pessoa",       "estado": "PB"},
    "Loja Joinville":                  {"cidade": "Joinville",         "estado": "SC"},
    "Loja Juazeiro do Norte":          {"cidade": "Juazeiro do Norte", "estado": "CE"},
    "Loja Londrina":                   {"cidade": "Londrina",          "estado": "PR"},
    "Loja Macapá":                     {"cidade": "Macapá",            "estado": "AP"},
    "Loja Maceió":                     {"cidade": "Maceió",            "estado": "AL"},
    "Loja Manaus":                     {"cidade": "Manaus",            "estado": "AM"},
    "Loja Maringá":                    {"cidade": "Maringá",           "estado": "PR"},
    "Loja Natal":                      {"cidade": "Natal",             "estado": "RN"},
    "Loja Niterói":                    {"cidade": "Niterói",           "estado": "RJ"},
    "Loja Palmas":                     {"cidade": "Palmas",            "estado": "TO"},
    "Loja Porto Alegre":               {"cidade": "Porto Alegre",      "estado": "RS"},
    "Loja Porto Velho":                {"cidade": "Porto Velho",       "estado": "RO"},
    "Loja Recife":                     {"cidade": "Recife",            "estado": "PE"},
    "Loja Ribeirão Preto":             {"cidade": "Ribeirão Preto",    "estado": "SP"},
    "Loja Rio Branco":                 {"cidade": "Rio Branco",        "estado": "AC"},
    "Loja Rio de Janeiro":             {"cidade": "Rio de Janeiro",    "estado": "RJ"},
    "Loja Salvador":                   {"cidade": "Salvador",          "estado": "BA"},
    "Loja Santos":                     {"cidade": "Santos",            "estado": "SP"},
    "Loja São Luís":                   {"cidade": "São Luís",          "estado": "MA"},
    "Loja São Paulo":                  {"cidade": "São Paulo",         "estado": "SP"},
    "Loja Sorocaba":                   {"cidade": "Sorocaba",          "estado": "SP"},
    "Loja Teresina":                   {"cidade": "Teresina",          "estado": "PI"},
    "Loja Uberlândia":                 {"cidade": "Uberlândia",        "estado": "MG"},
}

# Departamento → lojas permitidas
DEPT_LOJAS = {
    "Administrativo": ["Matriz"],
    "Tecnologia":     ["Matriz"],
    "Operações":      ["Centro Distribuição – Campinas",
                       "Centro Distribuição – Maringá",
                       "Centro Distribuição – Santos"],
    "Comercial":      [l for l in LOJAS if l not in
                       ["Matriz","Centro Distribuição – Campinas",
                        "Centro Distribuição – Maringá","Centro Distribuição – Santos"]],
}

# ─── ESTRUTURA COMPLETA: Departamento → Centro de Custo → Funções ─────────────
STRUCTURE = {
    "Administrativo": {
        "Departamento Pessoal": [
            "Auxiliar de Departamento Pessoal","Assistente de Departamento Pessoal",
            "Analista de Departamento Pessoal Jr","Analista de Departamento Pessoal Pl",
            "Analista de Departamento Pessoal Sr","Coordenador de Departamento Pessoal",
            "Gerente de Departamento Pessoal",
        ],
        "DHO": [
            "Auxiliar de RH","Assistente de RH","Analista de DHO Jr","Analista de DHO Pl",
            "Analista de DHO Sr","Analista de Treinamento e Desenvolvimento",
            "Analista de Cultura Organizacional","Business Partner (HRBP)",
            "Coordenador de DHO","Gerente de DHO",
        ],
        "Recrutamento e Seleção": [
            "Auxiliar de Recrutamento e Seleção","Assistente de Recrutamento e Seleção",
            "Analista de Recrutamento e Seleção Jr","Analista de Recrutamento e Seleção Pl",
            "Analista de Recrutamento e Seleção Sr","Analista de Talent Acquisition",
            "Tech Recruiter","Especialista em Recrutamento e Seleção",
            "Coordenador de Recrutamento e Seleção","Gerente de Recrutamento e Seleção",
        ],
        "Planejamento": [
            "Assistente de Planejamento","Analista de Planejamento Jr",
            "Analista de Planejamento Pl","Analista de Planejamento Sr",
            "Analista de Planejamento Estratégico","Coordenador de Planejamento",
            "Gerente de Planejamento",
        ],
        "Controladoria": [
            "Assistente de Controladoria","Analista de Controladoria Jr",
            "Analista de Controladoria Pl","Analista de Controladoria Sr",
            "Controller","Coordenador de Controladoria","Gerente de Controladoria",
        ],
        "Compras": [
            "Auxiliar de Compras","Assistente de Compras","Analista de Compras Jr",
            "Analista de Compras Pl","Analista de Compras Sr","Comprador",
            "Coordenador de Compras","Gerente de Compras",
        ],
        "Frotas": [
            "Auxiliar de Frotas","Assistente de Frotas","Analista de Frotas Jr",
            "Analista de Frotas Pl","Analista de Frotas Sr",
            "Coordenador de Frotas","Gerente de Frotas",
        ],
        "Jurídico": [
            "Assistente Jurídico","Analista Jurídico Jr","Analista Jurídico Pl",
            "Analista Jurídico Sr","Advogado Jr","Advogado Pl","Advogado Sr",
            "Coordenador Jurídico","Gerente Jurídico",
        ],
        "Diretoria": [
            "Diretor Administrativo","Diretor de Operações",
            "Diretor de Tecnologia","Diretor Comercial",
        ],
        "Financeiro": [
            "Auxiliar Financeiro","Assistente Financeiro","Analista Financeiro Jr",
            "Analista Financeiro Pl","Analista Financeiro Sr",
            "Analista de Contas a Pagar","Analista de Contas a Receber",
            "Tesoureiro","Coordenador Financeiro","Gerente Financeiro",
        ],
        "Facilities": [
            "Auxiliar de Limpeza","Oficial de Manutenção Predial","Recepcionista",
            "Auxiliar de Facilities","Assistente de Facilities","Analista de Facilities Jr",
            "Analista de Facilities Pl","Analista de Facilities Sr",
            "Coordenador de Facilities","Gerente de Facilities",
        ],
        "Qualidade": [
            "Auxiliar de Qualidade","Assistente de Qualidade","Analista de Qualidade Jr",
            "Analista de Qualidade Pl","Analista de Qualidade Sr","Auditor de Qualidade",
            "Engenheiro de Qualidade","Coordenador de Qualidade","Gerente de Qualidade",
        ],
        "Projeto Inovação": [
            "Assistente de Projetos","Analista de Projetos Jr","Analista de Projetos Pl",
            "Analista de Projetos Sr","PMO (Project Management Officer)","Scrum Master",
            "Product Owner","Coordenador de Projetos","Gerente de Projetos","Gerente de Inovação",
        ],
        "SESMT": [
            "Técnico de Segurança do Trabalho","Técnico de Segurança do Trabalho Sr",
            "Engenheiro de Segurança do Trabalho","Enfermeiro do Trabalho",
            "Técnico de Enfermagem do Trabalho","Médico do Trabalho",
            "Coordenador de Segurança do Trabalho","Gerente de SESMT",
        ],
    },
    "Operações": {
        "Logística": [
            "Auxiliar de Logística","Assistente de Logística","Analista de Logística Jr",
            "Analista de Logística Pl","Analista de Logística Sr",
            "Coordenador de Logística","Gerente de Logística",
        ],
        "Manutenção": [
            "Auxiliar de Manutenção","Técnico de Manutenção","Técnico de Manutenção Sr",
            "Engenheiro de Manutenção","Coordenador de Manutenção","Gerente de Manutenção",
        ],
        "Prevenção de Perdas": [
            "Coordenador de Prevenção de Perdas","Fiscal de Prevenção de Perdas",
        ],
        "SESMT – CD": [
            "Enfermeiro do Trabalho","Médico do Trabalho","Técnico de Segurança do Trabalho",
        ],
        "RH – CD": [
            "Assistente de Departamento Pessoal","Analista de Recrutamento e Seleção Jr",
        ],
        "Produção": [
            "Auxiliar de Produção","Operador de Produção","Líder de Produção",
            "Supervisor de Produção","Coordenador de Produção","Gerente de Produção",
        ],
        "Depósito": [
            "Auxiliar de Limpeza","Auxiliar de Depósito","Conferente","Estoquista",
            "Líder de Depósito","Supervisor de Depósito","Coordenador de Depósito",
        ],
    },
    "Tecnologia": {
        "Suporte e Service Desk": [
            "Auxiliar de TI","Técnico de Suporte","Analista de Service Desk Jr",
            "Analista de Service Desk Pl","Analista de Service Desk Sr",
            "Coordenador de Suporte","Gerente de Suporte",
        ],
        "Infraestrutura": [
            "Técnico de Infraestrutura","Analista de Infraestrutura Jr",
            "Analista de Infraestrutura Pl","Analista de Infraestrutura Sr",
            "Engenheiro de Infraestrutura","Coordenador de Infraestrutura",
            "Gerente de Infraestrutura",
        ],
        "Desenvolvimento": [
            "Desenvolvedor Jr","Desenvolvedor Pl","Desenvolvedor Sr",
            "Engenheiro de Software","Arquiteto de Software","Tech Lead",
            "Coordenador de Desenvolvimento","Gerente de Desenvolvimento",
        ],
        "Inteligência de Negócios": [
            "Auxiliar de Dados","Assistente de BI","Analista de BI Jr","Analista de BI Pl",
            "Analista de BI Sr","Analista de Dados","Analista de Dados Jr","Cientista de Dados",
            "Engenheiro de Dados","Coordenador de BI","Gerente de BI",
        ],
    },
    "Comercial": {
        "Vendas": [
            "Auxiliar de Vendas","Assistente de Vendas","Vendedor","Vendedor Sr",
            "Executivo de Contas","Supervisor de Vendas","Coordenador de Vendas",
            "Gerente de Vendas",
        ],
        "Limpeza": [
            "Auxiliar de Limpeza","Servente de Limpeza","Líder de Limpeza","Supervisor de Limpeza",
        ],
        "Prevenção de Perdas": [
            "Fiscal de Prevenção de Perdas","Coordenador de Prevenção de Perdas",
        ],
        "SESMT – Lojas": [
            "Médico do Trabalho","Enfermeiro do Trabalho","Técnico de Segurança do Trabalho",
        ],
        "RH – Lojas": [
            "Analista de Recrutamento e Seleção Jr","Assistente de Departamento Pessoal",
        ],
        "Caixas": [
            "Operador de Caixa","Fiscal de Caixa","Supervisor de Caixa","Tesoureiro",
        ],
        "Estoque": [
            "Auxiliar de Estoque","Estoquista","Conferente de Estoque","Analista de Estoque",
            "Supervisor de Estoque","Coordenador de Estoque",
        ],
    },
}

# ─── REGRAS DE TIPO DE CONTRATAÇÃO ────────────────────────────────────────────
APRENDIZ_FUNCOES = {
    "Auxiliar de Departamento Pessoal","Auxiliar de RH","Assistente de Planejamento",
    "Assistente de Controladoria","Auxiliar de Compras","Auxiliar de Frotas",
    "Assistente Jurídico","Auxiliar Financeiro","Auxiliar de Facilities",
    "Auxiliar de Logística","Auxiliar de Produção","Auxiliar de Depósito",
    "Auxiliar de Estoque","Auxiliar de TI","Auxiliar de Dados","Assistente de BI",
    "Auxiliar de Vendas","Auxiliar de Limpeza","Auxiliar de Recrutamento e Seleção",
}

ESTAGIO_FUNCOES = {
    "Auxiliar de Departamento Pessoal","Assistente de Departamento Pessoal",
    "Auxiliar de RH","Assistente de RH","Assistente de Planejamento",
    "Assistente de Controladoria","Auxiliar de Compras","Assistente de Compras",
    "Auxiliar Financeiro","Assistente Financeiro","Assistente Jurídico",
    "Analista de Planejamento Jr","Analista de Controladoria Jr","Analista Financeiro Jr",
    "Analista de Compras Jr","Analista de BI Jr","Analista de Dados Jr","Auxiliar de TI",
    "Técnico de Suporte","Analista de Service Desk Jr","Analista de Infraestrutura Jr",
    "Desenvolvedor Jr","Auxiliar de Logística","Assistente de Logística",
    "Auxiliar de Produção","Auxiliar de Depósito","Auxiliar de Estoque",
    "Auxiliar de Vendas","Assistente de Vendas","Auxiliar de Facilities",
    "Auxiliar de Frotas","Auxiliar de Qualidade","Assistente de Qualidade",
    "Auxiliar de Recrutamento e Seleção",
}

# ─── LISTAS DE NOMES ──────────────────────────────────────────────────────────
NOMES_M = [
    "Carlos","José","João","Pedro","Lucas","Marcos","Fernando","Rafael","Paulo","Luís",
    "André","Bruno","Diego","Felipe","Gustavo","Henrique","Igor","Júlio","Leonardo","Marcelo",
    "Nelson","Otávio","Ricardo","Sérgio","Thiago","Victor","Wagner","Eduardo","Antônio","Rodrigo",
    "Alexandre","Augusto","Caio","Daniel","Edson","Fábio","Gabriel","Hudson","Ivan","Jaime",
    "Kevin","Leandro","Mateus","Nilton","Osmar","Plínio","Renato","Samuel","Tiago","Ulisses",
]
NOMES_F = [
    "Maria","Ana","Fernanda","Juliana","Camila","Patrícia","Cristina","Renata","Luciana","Amanda",
    "Bruna","Carla","Daniela","Eliane","Flávia","Gabriela","Helena","Isabel","Joana","Karen",
    "Larissa","Mônica","Natália","Olivia","Paula","Quésia","Roberta","Sandra","Tatiana","Ursula",
    "Vanessa","Wanda","Aline","Beatriz","Cláudia","Débora","Erika","Fabiana","Giovana","Helo",
    "Ingrid","Jéssica","Kelly","Luana","Mariana","Nicole","Priscila","Raquel","Simone","Tânia",
]
SOBRENOMES = [
    "Silva","Santos","Oliveira","Souza","Rodrigues","Ferreira","Alves","Pereira","Lima","Gomes",
    "Costa","Ribeiro","Martins","Carvalho","Almeida","Lopes","Sousa","Fernandes","Vieira","Barbosa",
    "Rocha","Dias","Nascimento","Andrade","Moreira","Nunes","Marques","Machado","Mendes","Freitas",
    "Cardoso","Ramos","Morais","Araújo","Correia","Castro","Pinto","Teixeira","Neves","Borges",
    "Campos","Cavalcanti","Monteiro","Azevedo","Pires","Fonseca","Cunha","Moraes","Batista","Reis",
]
CIDADES_NATURAIS = [
    ("São Paulo","SP"),("Rio de Janeiro","RJ"),("Belo Horizonte","MG"),("Salvador","BA"),
    ("Fortaleza","CE"),("Curitiba","PR"),("Manaus","AM"),("Recife","PE"),("Porto Alegre","RS"),
    ("Belém","PA"),("Goiânia","GO"),("Florianópolis","SC"),("São Luís","MA"),("Maceió","AL"),
    ("Natal","RN"),("Teresina","PI"),("Campo Grande","MS"),("João Pessoa","PB"),("Aracaju","SE"),
    ("Cuiabá","MT"),("Macapá","AP"),("Porto Velho","RO"),("Rio Branco","AC"),("Boa Vista","RR"),
    ("Palmas","TO"),("Brasília","DF"),("Uberlândia","MG"),("Campinas","SP"),("Sorocaba","SP"),
    ("Ribeirão Preto","SP"),("Santos","SP"),("Joinville","SC"),("Londrina","PR"),("Maringá","PR"),
    ("Caxias do Sul","RS"),("Niterói","RJ"),("Feira de Santana","BA"),("Caruaru","PE"),
    ("Anápolis","GO"),("Juazeiro do Norte","CE"),
]

# ─── FUNÇÕES AUXILIARES ────────────────────────────────────────────────────────

def gerar_nome(sexo: str) -> str:
    pool = NOMES_M if sexo == "Masculino" else NOMES_F
    nome = random.choice(pool)
    meio = random.choice(SOBRENOMES + ["da","de","dos","das"])
    sobrenome = random.choice(SOBRENOMES)
    if random.random() < 0.3:
        return f"{nome} {meio} {sobrenome} {random.choice(SOBRENOMES)}"
    return f"{nome} {meio} {sobrenome}"


def random_workday(start: date, end: date) -> date:
    """Retorna um dia útil (Seg–Sex) aleatório entre start e end."""
    delta = (end - start).days
    for _ in range(2000):
        d = start + timedelta(days=random.randint(0, max(0, delta)))
        if d.weekday() < 5:
            return d
    return start


def get_escolaridade(funcao: str, tipo_contratacao: str, idade: int) -> str:
    f = funcao.lower()
    if tipo_contratacao == "Aprendiz":
        return "Ensino Médio Incompleto" if idade < 18 else "Ensino Médio Completo"
    if tipo_contratacao == "Estágio":
        return random.choice(["Superior Incompleto", "Pós-Graduação Incompleto"])
    # CLT
    if any(x in f for x in ["diretor","gerente","coordenador"]):
        return random.choice(["Superior Completo","Pós-Graduação Completo","Pós-Graduação Incompleto"])
    if any(x in f for x in ["analista","engenheiro","arquiteto","cientista","auditor",
                              "controller","business partner","scrum master","product owner",
                              "pmo","tech lead","tech recruiter","especialista",
                              "médico","enfermeiro","advogado","comprador","tesoureiro"]):
        return random.choice(["Superior Completo","Pós-Graduação Incompleto",
                               "Pós-Graduação Completo","Mestrado","Doutorado"])
    return random.choice(["Ensino Médio Completo","Superior Incompleto","Superior Completo"])


def weight_funcao(funcao: str) -> float:
    """Peso de seleção de função — mais operacional que gestão."""
    f = funcao.lower()
    if any(x in f for x in ["diretor","gerente","coordenador"]):
        return 0.08
    if any(x in f for x in ["analista","engenheiro","arquiteto","cientista","controller",
                              "business partner","scrum master","product owner","pmo",
                              "tech lead","tech recruiter","especialista","auditor",
                              "médico","enfermeiro","advogado","comprador","tesoureiro"]):
        return 0.35
    return 0.57


def pick_funcao(dept: str, cc: str) -> str:
    funcs = STRUCTURE[dept][cc]
    w = [weight_funcao(f) for f in funcs]
    total = sum(w)
    w = [x / total for x in w]
    return random.choices(funcs, weights=w, k=1)[0]


def determine_tipo_contratacao(funcao: str, idade: int) -> str:
    if funcao in APRENDIZ_FUNCOES and 17 <= idade <= 24 and random.random() < 0.15:
        return "Aprendiz"
    if funcao in ESTAGIO_FUNCOES and 25 <= idade <= 40 and random.random() < 0.12:
        return "Estágio"
    return "CLT"


# ─── TABELAS SALARIAIS ────────────────────────────────────────────────────────
print("Carregando tabelas salariais...")
df_sal_clt      = pd.read_excel(PATH_SAL_CLT)
df_sal_aprendiz = pd.read_excel(PATH_SAL_APRENDIZ)
df_sal_estagio  = pd.read_excel(PATH_SAL_ESTAGIO)

def get_salary(funcao: str, cidade: str, tipo_contratacao: str) -> float:
    if tipo_contratacao == "Aprendiz":
        df = df_sal_aprendiz
    elif tipo_contratacao == "Estágio":
        df = df_sal_estagio
    else:
        df = df_sal_clt
    row = df[df["Função"] == funcao]
    if row.empty:
        row = df_sal_clt[df_sal_clt["Função"] == funcao]
    if row.empty:
        return 1500.0
    if cidade in row.columns and pd.notna(row.iloc[0][cidade]):
        return float(row.iloc[0][cidade])
    if "São Paulo" in row.columns:
        return float(row.iloc[0]["São Paulo"])
    return 1500.0


# ─── GERAÇÃO DOS REGISTROS ESPECIAIS (Diretores e Coordenadores) ───────────────

print("Gerando registros especiais...")
special_records = []

DIRECTOR_FUNCOES = ["Diretor Administrativo","Diretor de Operações",
                    "Diretor de Tecnologia","Diretor Comercial"]

# 4 diretores ativos + 4 desligados
for func in DIRECTOR_FUNCOES:
    for situacao in ["Ativo", "Desligado"]:
        sexo = random.choice(["Masculino","Feminino"])
        adm  = random_workday(date(2005,1,1), date(2010,12,31) if situacao == "Ativo" else date(2018,12,31))
        dnasc = adm - timedelta(days=365 * random.randint(35, 55))
        cidade_nat, estado_nat = random.choice(CIDADES_NATURAIS)
        dem   = random_workday(adm + timedelta(days=365), date(2023,12,31)) if situacao == "Desligado" else None

        special_records.append({
            "matricula_colaborador": None,
            "nome_colaborador":      gerar_nome(sexo),
            "sexo":                  sexo,
            "data_nascimento":       dnasc,
            "idade_na_contratacao":  (adm - dnasc).days // 365,
            "idade":                 (TODAY - dnasc).days // 365,
            "cidade_moradia":        "São Paulo",
            "estado_moradia":        "SP",
            "pais":                  "Brasil",
            "naturalidade":          f"{cidade_nat} - {estado_nat}",
            "data_admissao":         adm,
            "data_demissao":         dem,
            "situacao":              situacao,
            "motivo_desligamento":   random.choice(["Pedido de demissão","Iniciativa da empresa"]) if situacao == "Desligado" else None,
            "tipo_desligamento":     "Demissão sem Justa Causa" if situacao == "Desligado" else None,
            "tipo_contratacao":      "CLT",
            "escolaridade":          random.choice(["Superior Completo","Pós-Graduação Completo"]),
            "departamento":          "Administrativo",
            "centro_custo":          "Diretoria",
            "funcao":                func,
            "salario_contratacao":   get_salary(func, "São Paulo", "CLT"),
            "vale_alimentacao":      500.0,
            "auxilio_combustivel":   350.0,
            "auxilio_creche":        0.0,
            "loja":                  "Matriz",
            "cidade_loja":           "São Paulo",
            "estado_loja":           "SP",
            "pais_loja":             "Brasil",
        })

# Coordenadores Administrativo: 1 ativo + 1 desligado por centro_custo
for cc in [c for c in STRUCTURE["Administrativo"] if c != "Diretoria"]:
    coord_funcs = [f for f in STRUCTURE["Administrativo"][cc] if "Coordenador" in f]
    if not coord_funcs:
        continue
    cf = coord_funcs[0]
    for situacao in ["Ativo", "Desligado"]:
        sexo  = random.choice(["Masculino","Feminino"])
        adm   = random_workday(date(2005,1,1), date(2020,12,31))
        dnasc = adm - timedelta(days=365 * random.randint(30, 52))
        cidade_nat, estado_nat = random.choice(CIDADES_NATURAIS)
        dem   = random_workday(adm + timedelta(days=180), min(TODAY, date(2025,12,31))) if situacao == "Desligado" else None

        special_records.append({
            "matricula_colaborador": None,
            "nome_colaborador":      gerar_nome(sexo),
            "sexo":                  sexo,
            "data_nascimento":       dnasc,
            "idade_na_contratacao":  (adm - dnasc).days // 365,
            "idade":                 (TODAY - dnasc).days // 365,
            "cidade_moradia":        "São Paulo",
            "estado_moradia":        "SP",
            "pais":                  "Brasil",
            "naturalidade":          f"{cidade_nat} - {estado_nat}",
            "data_admissao":         adm,
            "data_demissao":         dem,
            "situacao":              situacao,
            "motivo_desligamento":   random.choice(["Pedido de demissão","Iniciativa da empresa"]) if situacao == "Desligado" else None,
            "tipo_desligamento":     "Demissão sem Justa Causa" if situacao == "Desligado" else None,
            "tipo_contratacao":      "CLT",
            "escolaridade":          random.choice(["Superior Completo","Pós-Graduação Incompleto"]),
            "departamento":          "Administrativo",
            "centro_custo":          cc,
            "funcao":                cf,
            "salario_contratacao":   get_salary(cf, "São Paulo", "CLT"),
            "vale_alimentacao":      500.0,
            "auxilio_combustivel":   350.0,
            "auxilio_creche":        0.0,
            "loja":                  "Matriz",
            "cidade_loja":           "São Paulo",
            "estado_loja":           "SP",
            "pais_loja":             "Brasil",
        })

# Coordenadores Operações e Comercial: 2-3 ativos + 1-2 desligados por loja
for dept in ["Operações", "Comercial"]:
    for loja in DEPT_LOJAS[dept]:
        info   = LOJAS[loja]
        cidade = info["cidade"]
        estado = info["estado"]
        for cc, funcs in STRUCTURE[dept].items():
            coord_funcs = [f for f in funcs if "Coordenador" in f]
            if not coord_funcs:
                continue
            cf = coord_funcs[0]
            for situacao, n in [("Ativo", random.randint(2,3)), ("Desligado", random.randint(1,2))]:
                for _ in range(n):
                    sexo  = random.choice(["Masculino","Feminino"])
                    adm   = random_workday(ADMISSAO_START, date(2024,12,31))
                    dnasc = adm - timedelta(days=365 * random.randint(26, 50))
                    cidade_nat, estado_nat = random.choice(CIDADES_NATURAIS)
                    dem   = None
                    if situacao == "Desligado":
                        dem_e = min(TODAY, date(2026,3,31))
                        dem_s = adm + timedelta(days=90)
                        if dem_s < dem_e:
                            dem = random_workday(dem_s, dem_e)

                    special_records.append({
                        "matricula_colaborador": None,
                        "nome_colaborador":      gerar_nome(sexo),
                        "sexo":                  sexo,
                        "data_nascimento":       dnasc,
                        "idade_na_contratacao":  (adm - dnasc).days // 365,
                        "idade":                 (TODAY - dnasc).days // 365,
                        "cidade_moradia":        cidade,
                        "estado_moradia":        estado,
                        "pais":                  "Brasil",
                        "naturalidade":          f"{cidade_nat} - {estado_nat}",
                        "data_admissao":         adm,
                        "data_demissao":         dem,
                        "situacao":              situacao,
                        "motivo_desligamento":   random.choice(["Pedido de demissão","Iniciativa da empresa"]) if situacao == "Desligado" else None,
                        "tipo_desligamento":     "Demissão sem Justa Causa" if situacao == "Desligado" else None,
                        "tipo_contratacao":      "CLT",
                        "escolaridade":          random.choice(["Superior Incompleto","Superior Completo"]),
                        "departamento":          dept,
                        "centro_custo":          cc,
                        "funcao":                cf,
                        "salario_contratacao":   get_salary(cf, cidade, "CLT"),
                        "vale_alimentacao":      500.0,
                        "auxilio_combustivel":   350.0,
                        "auxilio_creche":        0.0,
                        "loja":                  loja,
                        "cidade_loja":           cidade,
                        "estado_loja":           estado,
                        "pais_loja":             "Brasil",
                    })

print(f"  Registros especiais: {len(special_records)}")

# ─── GERAÇÃO DA POPULAÇÃO GERAL ───────────────────────────────────────────────

DEPT_WEIGHTS = {"Comercial": 0.55, "Operações": 0.20, "Administrativo": 0.15, "Tecnologia": 0.10}

print(f"Gerando {TARGET_RECORDS - len(special_records)} registros gerais...")
general_records = []

for i in range(TARGET_RECORDS - len(special_records)):
    if i % 10_000 == 0:
        print(f"  {i}...")

    # Escolhe dept, cc, funcao e loja
    dept = random.choices(list(DEPT_WEIGHTS), weights=list(DEPT_WEIGHTS.values()))[0]
    cc   = random.choice(list(STRUCTURE[dept].keys()))
    # Exclui Diretoria da seleção aleatória — apenas registros especiais têm Diretores
    if cc == "Diretoria":
        cc = random.choice([c for c in STRUCTURE[dept] if c != "Diretoria"])
    funcao = pick_funcao(dept, cc)
    # Garante que diretores nunca sejam gerados aleatoriamente
    if "Diretor" in funcao:
        funcao = "Gerente de Vendas" if dept == "Comercial" else "Gerente de Logística"

    loja   = random.choice(DEPT_LOJAS[dept])
    info   = LOJAS[loja]
    cidade = info["cidade"]
    estado = info["estado"]
    sexo   = "Feminino" if random.random() < 0.45 else "Masculino"

    # Faixa de idade na admissão
    is_gestao   = any(x in funcao for x in ["Coordenador","Gerente"])
    is_juridico = "Advogado" in funcao
    min_age = 26 if is_gestao else (25 if is_juridico else 17)
    max_age = 60 if is_gestao else 65

    idade_adm = random.randint(min_age, max_age)

    tipo = determine_tipo_contratacao(funcao, idade_adm)
    if tipo == "Aprendiz": idade_adm = random.randint(17, 24)
    if tipo == "Estágio":  idade_adm = random.randint(25, 40)

    adm   = random_workday(ADMISSAO_START, ADMISSAO_END)
    dnasc = adm - timedelta(days=365 * idade_adm + random.randint(0, 364))
    idade_hoje = (TODAY - dnasc).days // 365

    # Situação (75% ativo, ~22% desligado, ~3% aposentado)
    r_sit = random.random()
    situacao = "Ativo" if r_sit < 0.75 else ("Desligado" if r_sit < 0.97 else "Aposentado")

    # Valida aposentado
    if situacao == "Aposentado":
        if tipo != "CLT":
            situacao = "Desligado"
        elif (sexo == "Feminino" and idade_hoje < 62) or (sexo == "Masculino" and idade_hoje < 65):
            situacao = "Ativo"

    # Demissão
    dem = motivo_des = tipo_des = None
    if situacao in ["Desligado", "Aposentado"]:
        dem_s = adm + timedelta(days=30)
        dem_e = min(TODAY, date(2026,3,31))
        if dem_s >= dem_e: dem_e = dem_s + timedelta(days=60)
        dem = random_workday(dem_s, dem_e)
        tenure_dias = (dem - adm).days if dem else 0

        if situacao == "Aposentado":
            motivo_des = "Aposentadoria"
            tipo_des   = "Demissão sem Justa Causa"
        elif tipo in ["Aprendiz","Estágio"]:
            motivo_des = "Término de Contrato" if tenure_dias >= 730 else random.choice(["Baixo desempenho","Descumprimento de regras","Pedido de demissão"])
            tipo_des   = "Demissão sem Justa Causa"
        else:
            if random.random() < 0.004:
                motivo_des = "Abandono"
                tipo_des   = "Demissão por Justa Causa"
            else:
                motivo_des = random.choice(["Pedido de demissão","Iniciativa da empresa"])
                tipo_des   = "Demissão sem Justa Causa"

    esc           = get_escolaridade(funcao, tipo, idade_adm)
    sal           = get_salary(funcao, cidade, tipo)
    is_gestao_ben = any(x in funcao for x in ["Coordenador","Gerente","Diretor"])
    auxc          = 350.0 if is_gestao_ben else 0.0
    creche        = 400.0 if (sexo == "Feminino" and random.random() < 0.30) else 0.0
    cidade_nat, estado_nat = random.choice(CIDADES_NATURAIS)

    general_records.append({
        "matricula_colaborador": None,
        "nome_colaborador":      gerar_nome(sexo),
        "sexo":                  sexo,
        "data_nascimento":       dnasc,
        "idade_na_contratacao":  idade_adm,
        "idade":                 idade_hoje,
        "cidade_moradia":        cidade,
        "estado_moradia":        estado,
        "pais":                  "Brasil",
        "naturalidade":          f"{cidade_nat} - {estado_nat}",
        "data_admissao":         adm,
        "data_demissao":         dem,
        "situacao":              situacao,
        "motivo_desligamento":   motivo_des,
        "tipo_desligamento":     tipo_des,
        "tipo_contratacao":      tipo,
        "escolaridade":          esc,
        "departamento":          dept,
        "centro_custo":          cc,
        "funcao":                funcao,
        "salario_contratacao":   sal,
        "vale_alimentacao":      500.0,
        "auxilio_combustivel":   auxc,
        "auxilio_creche":        creche,
        "loja":                  loja,
        "cidade_loja":           cidade,
        "estado_loja":           estado,
        "pais_loja":             "Brasil",
    })

# ─── CONSOLIDAÇÃO E ATRIBUIÇÃO DE MATRÍCULA ───────────────────────────────────
print("Consolidando e ordenando por data_admissao...")
all_records = special_records + general_records
all_records.sort(key=lambda r: r["data_admissao"])

for idx, rec in enumerate(all_records, 1):
    rec["matricula_colaborador"] = f"COL{idx:05d}"

df = pd.DataFrame(all_records)

# Formata datas
for col in ["data_nascimento","data_admissao","data_demissao"]:
    df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")

# ─── SALVA ────────────────────────────────────────────────────────────────────
df.to_csv(OUTPUT_COLAB, index=False)
print(f"Salvo: {OUTPUT_COLAB}  ({len(df)} linhas)")

lookup_cols = ["matricula_colaborador","nome_colaborador","data_admissao","data_demissao",
               "situacao","departamento","centro_custo","funcao","loja","cidade_loja",
               "tipo_contratacao","salario_contratacao","sexo","data_nascimento","idade_na_contratacao"]
df[lookup_cols].to_csv(OUTPUT_LOOKUP, index=False)
print(f"Salvo: {OUTPUT_LOOKUP}")

print("\n=== Validação rápida ===")
print(df["situacao"].value_counts())
print(df[df["funcao"].str.contains("Diretor", na=False)][["funcao","situacao"]].value_counts())
