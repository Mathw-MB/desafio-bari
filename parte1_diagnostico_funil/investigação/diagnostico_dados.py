"""
diagnostico_dados.py (v2)
Desafio Prático - Estágio AI & Data Lab | Bari

v2: a v1 quebrou no cálculo do LTV porque valor_imovel veio como texto,
não número. Esta versão investiga o formato bruto de valor_imovel antes
de tentar converter qualquer coisa, detalha as 3 linhas com data inválida
e a linha com etapa_max_funil fora do range 1-6, e confirma que os nulos
de data_assinatura_contrato batem com o total de propostas Contratadas.
Este script só LÊ o arquivo — nada aqui altera o CSV original.
"""

import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)

CAMINHO_CSV = "propostas_credito.csv"

COLUNAS_ESPERADAS = [
    "id_proposta", "data_entrada", "canal_origem", "cidade", "uf",
    "tipo_imovel", "valor_imovel", "valor_solicitado", "ltv", "prazo_meses",
    "score_credito", "idade_cliente", "renda_mensal_declarada",
    "flag_cliente_recorrente", "consultor_id", "etapa_max_funil",
    "status_final", "tempo_analise_dias", "data_assinatura_contrato",
    "taxa_juros_aa",
]


def secao(titulo):
    print("\n" + "=" * 78)
    print(titulo)
    print("=" * 78)


# --- Carregamento -------------------------------------------------------
df = pd.read_csv(CAMINHO_CSV)
if df.shape[1] == 1:
    print("Aviso: só 1 coluna foi lida — separador provavelmente não é vírgula.")
    df = pd.read_csv(CAMINHO_CSV, sep=';')

# --- 1. Volume ------------------------------------------------------------
secao("1. Quantidade de linhas e colunas")
print(f"Linhas: {df.shape[0]}")
print(f"Colunas: {df.shape[1]}")

# --- 2/3. Colunas reais vs. dicionário -------------------------------------
secao("2/3. Colunas reais do CSV vs. dicionário do desafio")
colunas_reais = list(df.columns)
print(colunas_reais)
faltando = set(COLUNAS_ESPERADAS) - set(colunas_reais)
sobrando = set(colunas_reais) - set(COLUNAS_ESPERADAS)
print(f"\nEsperadas mas ausentes: {faltando or 'nenhuma'}")
print(f"Presentes mas fora do dicionário: {sobrando or 'nenhuma'}")

# --- 4. Tipos de dado -------------------------------------------------------
secao("4. Tipo de dado (dtype) por coluna")
print(df.dtypes)

# --- 5. canal_origem --------------------------------------------------------
secao("5. Valores únicos de canal_origem (com contagem)")
print(df['canal_origem'].value_counts(dropna=False))

secao("5b. Preview: canal_origem após normalizar (strip + minúsculas)")
canal_normalizado = df['canal_origem'].str.strip().str.lower()
print(canal_normalizado.value_counts())

# --- 6. Período --------------------------------------------------------------
secao("6. Período coberto pela base (data_entrada)")
datas_entrada = pd.to_datetime(df['data_entrada'], errors='coerce')
print(f"Data mínima: {datas_entrada.min()}")
print(f"Data máxima: {datas_entrada.max()}")
print(f"Linhas com data_entrada não interpretável: {datas_entrada.isna().sum()}")

secao("6b. Detalhe das linhas com data_entrada não interpretável")
print(df.loc[datas_entrada.isna(), ['id_proposta', 'data_entrada']])

# --- 7. Nulos ------------------------------------------------------------
secao("7. Nulos por coluna")
nulos = df.isnull().sum()
pct_nulos = (nulos / len(df) * 100).round(2)
print(pd.DataFrame({'qtd_nulos': nulos, 'pct_nulos': pct_nulos}))

secao("7b. Nulos em data_assinatura_contrato batem com status Contratada?")
qtd_contratada = (df['status_final'] == 'Contratada').sum()
qtd_nao_nula_assinatura = df['data_assinatura_contrato'].notna().sum()
print(f"Linhas com status_final == 'Contratada': {qtd_contratada}")
print(f"Linhas com data_assinatura_contrato preenchida: {qtd_nao_nula_assinatura}")
print(f"Batem exatamente? {qtd_contratada == qtd_nao_nula_assinatura}")

# --- 8. Duplicatas ---------------------------------------------------------
secao("8. Duplicatas")
print(f"Linhas 100% duplicadas: {df.duplicated().sum()}")
if 'id_proposta' in df.columns:
    print(f"id_proposta duplicado: {df['id_proposta'].duplicated().sum()}")

# --- 9. Categorias --------------------------------------------------------
secao("9. Valores únicos das colunas categóricas")
for col in ['canal_origem', 'tipo_imovel', 'uf', 'status_final']:
    if col in df.columns:
        print(f"\n-- {col} --")
        print(sorted(df[col].dropna().unique()))

# --- 10. status_final ------------------------------------------------------
secao("10. Distribuição de status_final")
print(df['status_final'].value_counts(dropna=False))

# --- 11. etapa_max_funil ----------------------------------------------------
secao("11. Distribuição de etapa_max_funil")
print(df['etapa_max_funil'].value_counts(dropna=False).sort_index())
fora_range = df[~df['etapa_max_funil'].between(1, 6)]
print(f"Linhas com etapa_max_funil fora de 1-6: {len(fora_range)}")

secao("11b. Detalhe da(s) linha(s) com etapa_max_funil fora de 1-6")
print(fora_range)

# --- 12. Investigação do formato bruto de valor_imovel ------------------
secao("12. Investigando o formato bruto de valor_imovel (NÃO convertendo ainda)")
print("Amostra de 20 valores brutos:")
print(df['valor_imovel'].sample(20, random_state=42).tolist())
print(f"\nContém 'R$': {df['valor_imovel'].str.contains('R\\$', na=False).sum()} linhas")
print(f"Contém vírgula: {df['valor_imovel'].str.contains(',', na=False).sum()} linhas")
print(f"Contém ponto: {df['valor_imovel'].str.contains('.', regex=False, na=False).sum()} linhas")
print(f"Valores nulos: {df['valor_imovel'].isna().sum()}")
print(f"Valores únicos: {df['valor_imovel'].nunique()} (de {len(df)} linhas)")

# --- 13a. score_credito -----------------------------------------------------
secao("13a. Faixa de score_credito (esperado 0-1000)")
print(df['score_credito'].describe())
print(f"Fora de 0-1000: {(~df['score_credito'].between(0, 1000)).sum()}")

# --- 13b. taxa_juros_aa -------------------------------------------------
secao("13b. taxa_juros_aa — nome sugere 'ao ano', dicionário diz '% a.m.'")
print(df['taxa_juros_aa'].describe())

# --- 13c. Valores <= 0 (protegido contra coluna ainda não numérica) --
secao("13c. Valores <= 0 em colunas que deveriam ser positivas")
for col in ['valor_imovel', 'valor_solicitado', 'prazo_meses',
            'idade_cliente', 'renda_mensal_declarada']:
    if col in df.columns:
        try:
            qtd = (df[col] <= 0).sum()
            print(f"{col}: {qtd} linha(s) com valor <= 0")
        except TypeError:
            print(f"{col}: pulado — coluna ainda não é numérica (ver item 4 do registro de tratamento)")

# --- 13d. idade_cliente -------------------------------------------------
secao("13d. idade_cliente fora de 18-100")
print(f"Fora de 18-100: {(~df['idade_cliente'].between(18, 100)).sum()}")

# --- 13e. Consistência de datas -----------------------------------------
secao("13e. data_assinatura_contrato anterior a data_entrada")
data_assinatura = pd.to_datetime(df['data_assinatura_contrato'], errors='coerce')
inconsistente = data_assinatura < datas_entrada
print(f"Linhas com assinatura antes da entrada: {inconsistente.sum()}")

secao("FIM DO DIAGNÓSTICO")
