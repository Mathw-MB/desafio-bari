"""
analise_hipotese_lideranca.py
Desafio Prático - Estágio AI & Data Lab | Bari
Parte 1 — Pergunta 2: "A percepção da liderança se confirma? A conversão
caiu? O canal de correspondentes está mal? Responda com números e diga o
quanto você confia na sua própria resposta."

Usa propostas_credito_tratado.csv. As colunas de data voltam como texto
nesse CSV (limitação do formato CSV — não guarda tipo datetime), então
reaplicamos parse_data_hibrida antes de qualquer conta com datas, a mesma
função usada em tratamento.py.
"""

import numpy as np
import pandas as pd
from statistics import NormalDist

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)


def secao(titulo):
    print("\n" + "=" * 78)
    print(titulo)
    print("=" * 78)


def parse_data_hibrida(serie):
    parsed = pd.to_datetime(serie, errors='coerce')
    faltando = parsed.isna() & serie.notna()
    if faltando.any():
        parsed.loc[faltando] = pd.to_datetime(serie[faltando], dayfirst=True, errors='coerce')
    return parsed


def teste_duas_proporcoes(x1, n1, x2, n2):
    """Teste z de duas proporções (bicaudal). Sem depender de scipy/statsmodels."""
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    erro_padrao = (p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) ** 0.5
    z = (p1 - p2) / erro_padrao
    pvalor = 2 * (1 - NormalDist().cdf(abs(z)))
    return z, pvalor


df = pd.read_csv('propostas_credito_tratado.csv')
df['data_entrada'] = parse_data_hibrida(df['data_entrada'])
df['data_assinatura_contrato'] = parse_data_hibrida(df['data_assinatura_contrato'])
df['contratada'] = (df['status_final'] == 'Contratada').astype(int)
df['mes_entrada'] = df['data_entrada'].dt.to_period('M')

# --- 0. Checagem de censura: propostas recentes tiveram tempo hábil de fechar? ---
# Se meses recentes mostrarem tempo_analise_dias anormalmente baixo (ou poucos
# contratos com esse tempo), pode ser sinal de que a base foi "cortada" antes de
# essas propostas terem tempo de virar contrato — o que inflaria uma falsa queda
# de conversão nos últimos meses, sem ser um problema real de negócio.
secao("0a. tempo_analise_dias por status_final (contexto)")
print(df.groupby('status_final')['tempo_analise_dias'].agg(['mean', 'median', 'count']).round(1))

secao("0b. tempo_analise_dias de propostas CONTRATADAS, por mês de entrada (checagem de censura)")
contratadas_por_mes = df[df['contratada'] == 1].groupby('mes_entrada')['tempo_analise_dias'].agg(['mean', 'count'])
print(contratadas_por_mes)

# --- 1. Série mensal: propostas, contratos e taxa de conversão ---
secao("1. Série mensal de propostas e taxa de conversão")
serie_mensal = df.groupby('mes_entrada').agg(
    propostas=('id_proposta', 'count'),
    contratos=('contratada', 'sum'),
).reset_index()
serie_mensal['taxa_conversao_pct'] = (serie_mensal['contratos'] / serie_mensal['propostas'] * 100).round(1)
print(serie_mensal.to_string(index=False))

serie_mensal['idx_mes'] = range(len(serie_mensal))
correlacao = serie_mensal['idx_mes'].corr(serie_mensal['taxa_conversao_pct'])
print(f"\nCorrelação entre índice do mês e taxa de conversão: {correlacao:.3f}")
print("(negativo = tendência de queda ao longo do tempo; positivo = tendência de alta)")

# --- 2. Primeira metade do período vs. segunda metade ---
secao("2. Primeira metade do período vs. segunda metade (teste estatístico)")
mediana_data = df['data_entrada'].median()
print(f"Data mediana da base: {mediana_data.date()}")
primeira = df[df['data_entrada'] <= mediana_data]
segunda = df[df['data_entrada'] > mediana_data]
n1, x1 = len(primeira), int(primeira['contratada'].sum())
n2, x2 = len(segunda), int(segunda['contratada'].sum())
print(f"1ª metade: {n1} propostas, {x1} contratos, taxa = {x1/n1*100:.1f}%")
print(f"2ª metade: {n2} propostas, {x2} contratos, taxa = {x2/n2*100:.1f}%")
z, p = teste_duas_proporcoes(x1, n1, x2, n2)
sig = "diferença estatisticamente significativa" if p < 0.05 else "SEM diferença estatisticamente significativa"
print(f"Teste de duas proporções: z = {z:.3f}, p-valor = {p:.4f} ({sig} a 5%)")

# --- 2b. Últimos 3 meses vs. restante (recorte específico da percepção da liderança) ---
secao("2b. Últimos 3 meses da base vs. restante do período")
data_max = df['data_entrada'].max()
corte = data_max - pd.DateOffset(months=3)
recentes = df[df['data_entrada'] > corte]
resto = df[df['data_entrada'] <= corte]
n_r, x_r = len(recentes), int(recentes['contratada'].sum())
n_re, x_re = len(resto), int(resto['contratada'].sum())
print(f"Últimos 3 meses ({corte.date()} a {data_max.date()}): {n_r} propostas, taxa = {x_r/n_r*100:.1f}%")
print(f"Restante do período: {n_re} propostas, taxa = {x_re/n_re*100:.1f}%")
z2, p2 = teste_duas_proporcoes(x_r, n_r, x_re, n_re)
sig2 = "diferença estatisticamente significativa" if p2 < 0.05 else "SEM diferença estatisticamente significativa"
print(f"Teste de duas proporções: z = {z2:.3f}, p-valor = {p2:.4f} ({sig2} a 5%)")

# --- 3. Canal Correspondente vs. demais canais ---
secao("3. Canal Correspondente vs. demais canais")
correspondente = df[df['canal_origem'] == 'Correspondente']
outros = df[df['canal_origem'] != 'Correspondente']
n_c, x_c = len(correspondente), int(correspondente['contratada'].sum())
n_o, x_o = len(outros), int(outros['contratada'].sum())
print(f"Correspondente: {n_c} propostas, {x_c} contratos, taxa = {x_c/n_c*100:.1f}%")
print(f"Demais canais:  {n_o} propostas, {x_o} contratos, taxa = {x_o/n_o*100:.1f}%")
z3, p3 = teste_duas_proporcoes(x_c, n_c, x_o, n_o)
sig3 = "diferença estatisticamente significativa" if p3 < 0.05 else "SEM diferença estatisticamente significativa"
print(f"Teste de duas proporções: z = {z3:.3f}, p-valor = {p3:.4f} ({sig3} a 5%)")

secao("3b. Taxa de conversão por canal (todos, para contexto)")
por_canal = df.groupby('canal_origem').agg(
    propostas=('id_proposta', 'count'),
    contratos=('contratada', 'sum'),
).reset_index()
por_canal['taxa_conversao_pct'] = (por_canal['contratos'] / por_canal['propostas'] * 100).round(1)
print(por_canal.sort_values('taxa_conversao_pct', ascending=False).to_string(index=False))

# --- 4. A eventual queda é geral ou específica do canal correspondentes? ---
secao("4. Conversão mensal: Correspondente vs. demais canais, lado a lado")
df['grupo_canal'] = np.where(df['canal_origem'] == 'Correspondente', 'Correspondente', 'Outros canais')
serie_grupo = df.groupby(['mes_entrada', 'grupo_canal']).agg(
    propostas=('id_proposta', 'count'),
    contratos=('contratada', 'sum'),
).reset_index()
serie_grupo['taxa_conversao_pct'] = (serie_grupo['contratos'] / serie_grupo['propostas'] * 100).round(1)
pivot = serie_grupo.pivot(index='mes_entrada', columns='grupo_canal', values='taxa_conversao_pct')
print(pivot)
