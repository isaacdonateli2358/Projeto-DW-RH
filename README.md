# HR DataBase — Scripts de Geração de Dados Sintéticos

## Visão Geral

Dois scripts Python que geram **50.000 colaboradores** e todas as bases
auxiliares de RH em formato SQL, prontos para uso em Power BI, SQL Server,
MySQL, PostgreSQL ou qualquer banco relacional.

---

## Estrutura de Arquivos

```
📁 projeto/
├── 01_gerar_colaboradores.py      ← Gera a base principal
├── 02_gerar_sql.py                ← Gera todos os SQLs + ZIP final
├── tabela_salarial_funcao.xlsx
├── tabela_salarial_funcao_aprendizes.xlsx
├── tabela_salarial_funcao_estagiario.xlsx
│
├── colaboradores.csv              ← Gerado pelo script 1
├── lookup.csv                     ← Gerado pelo script 1
│
└── sql_output/                    ← Gerado pelo script 2
    ├── colaboradores.sql
    ├── folha_pagamento.sql
    ├── treinamentos.sql
    ├── avaliacao_desempenho.sql
    ├── absenteismo.sql
    ├── recrutamento_selecao.sql
    ├── metas.sql
    ├── headcount_orcado.sql
    └── tabela_salarial.sql
```

---

## Requisitos

```bash
pip install pandas openpyxl numpy
```

Python 3.9+

---

## Como Usar

### Passo 1 — Gerar a base de colaboradores

```bash
python 01_gerar_colaboradores.py
```

Saída:
- `colaboradores.csv` (50.000 linhas)
- `lookup.csv` (subset com colunas-chave)

Tempo estimado: **~2 minutos**

---

### Passo 2 — Gerar todos os SQLs

```bash
python 02_gerar_sql.py
```

Saída:
- Pasta `sql_output/` com 9 arquivos `.sql`
- `RH_DataBase_SQL.zip` com todos os arquivos comprimidos `.sql.gz`

Tempo estimado: **~5-10 minutos** (a folha de pagamento tem ~5,8 milhões de linhas)

---

## Bases Geradas

| Arquivo                   | Registros aprox. | Descrição                              |
|---------------------------|------------------|----------------------------------------|
| colaboradores.sql         | 50.000           | Base principal de colaboradores        |
| folha_pagamento.sql       | ~5,8 milhões     | Histórico mensal jan/2005–dez/2026     |
| treinamentos.sql          | ~220 mil         | Histórico de cursos por colaborador    |
| avaliacao_desempenho.sql  | ~440 mil         | Avaliações anuais e semestrais         |
| absenteismo.sql           | ~115 mil         | Faltas, atestados, atrasos             |
| recrutamento_selecao.sql  | 50.000           | Processo seletivo de cada contratação  |
| metas.sql                 | ~84 mil          | Metas organizacionais mensais          |
| headcount_orcado.sql      | ~370 mil         | Headcount orçado por função/loja/mês   |
| tabela_salarial.sql       | ~10 mil          | Referência salarial por cidade/função  |

---

## Relacionamento entre Tabelas

Todas as tabelas se relacionam via `matricula_colaborador` (chave: `COL00001` a `COL50000`).

```
colaboradores (PK: matricula_colaborador)
    ├── folha_pagamento
    ├── treinamentos
    ├── avaliacao_desempenho
    ├── absenteismo
    └── recrutamento_selecao

metas           → relaciona por departamento + centro_custo + loja
headcount_orcado → relaciona por loja + departamento + centro_custo + funcao
tabela_salarial  → referência por tipo_contratacao + funcao + cidade
```

---

## Importando no MySQL/MariaDB

```bash
# Descomprime
gunzip sql_output/*.sql.gz

# Cria banco e importa
mysql -u root -p -e "CREATE DATABASE rh_db;"
mysql -u root -p rh_db < sql_output/colaboradores.sql
mysql -u root -p rh_db < sql_output/folha_pagamento.sql
# ... demais arquivos
```

## Importando no PostgreSQL

```bash
psql -U postgres -c "CREATE DATABASE rh_db;"
psql -U postgres -d rh_db -f sql_output/colaboradores.sql
# ... demais arquivos
```

---

## Regras de Negócio Implementadas

### Colaboradores
- ✅ Exatamente 4 Diretores ativos (1 por título) + 4 desligados, todos na Matriz
- ✅ Coordenadores Administrativo: 1 ativo + 1 desligado por centro de custo
- ✅ Coordenadores Operações/Comercial: 2-3 ativos + 1-2 desligados por loja
- ✅ Aprendizes: 17-24 anos, funções auxiliares, Médio Incompleto/Completo
- ✅ Estagiários: 25-40 anos, Superior Incompleto ou Pós-Graduação Incompleto
- ✅ Aposentados: mulheres ≥ 62 anos, homens ≥ 65 anos, somente CLT
- ✅ ~75% Ativos, ~22% Desligados, ~3% Aposentados
- ✅ Salários por cidade e função conforme tabelas fornecidas
- ✅ Vale alimentação R$ 500 (todos), auxílio combustível R$ 350 (gestão), auxílio creche R$ 400 (30% mulheres)
- ✅ Apenas dias úteis (Seg–Sex) para admissão e demissão

### Departamentos × Lojas
- Administrativo e Tecnologia → somente Matriz (São Paulo)
- Operações → 3 Centros de Distribuição (Campinas, Maringá, Santos)
- Comercial → 40 lojas em todo o Brasil

### Folha de Pagamento
- Reajuste salarial anual automático (2,5%–7%)
- INSS progressivo (tabela 2025) e IRRF calculados
- Bônus trimestral para gestão, comissões para Comercial/Vendas
- Horas extras mais frequentes em Operações e Comercial
- FGTS 8% + encargos patronais ~20%

### Headcount Orçado
- Meses de alta temporada (Jan, Abr, Jul, Dez): +15-35% no Comercial
