"""
analise_mix_canal.py
Desafio Prático - Estágio AI & Data Lab | Bari
Complemento à Pergunta 2: será que a participação do canal Correspondente
no volume total mudou ao longo do tempo? Se sim, isso pode explicar parte
da queda de conversão como um efeito de composição/mix (mais propostas
vindo de um canal mais fraco), e não necessariamente cada canal piorando
individualmente.

Usa propostas_credito_tratado.csv. Datas voltam como texto no CSV, então
reaplicamos parse_data_hibrida antes de qualquer conta com datas.
"""

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
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    erro_padrao = (p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) ** 0.5
    z = (p1 - p2) / erro_padrao
    pvalor = 2 * (1 - NormalDist().cdf(abs(z)))
    return z, pvalor


df = pd.read_csv('propostas_credito_tratado.csv')
df['data_entrada'] = parse_data_hibrida(df['data_entrada'])
df['contratada'] = (df['status_final'] == 'Contratada').astype(int)
df['mes_entrada'] = df['data_entrada'].dt.to_period('M')
df['grupo_canal'] = df['canal_origem'].where(df['canal_origem'] == 'Correspondente', 'Outros canais')

# --- 1. Participação de Correspondente no volume total, mês a mês ---
secao("1. Participação (%) de Correspondente no volume total de propostas, por mês")
volume_mensal = df.groupby(['mes_entrada', 'grupo_canal']).size().unstack(fill_value=0)
volume_mensal['total'] = volume_mensal.sum(axis=1)
volume_mensal['pct_correspondente'] = (
    volume_mensal.get('Correspondente', 0) / volume_mensal['total'] * 100
).round(1)
print(volume_mensal[['Correspondente', 'Outros canais', 'total', 'pct_correspondente']])

volume_mensal_idx = volume_mensal.reset_index()
volume_mensal_idx['idx_mes'] = range(len(volume_mensal_idx))
correlacao_participacao = volume_mensal_idx['idx_mes'].corr(volume_mensal_idx['pct_correspondente'])
print(f"\nCorrelação entre índice do mês e % de participação de Correspondente: {correlacao_participacao:.3f}")
print("(positivo = correspondentes ganhando participação ao longo do tempo)")

# --- 2. Participação de Correspondente: 1ª metade vs. 2ª metade (teste estatístico) ---
secao("2. Participação de Correspondente no volume: 1ª metade vs. 2ª metade")
mediana_data = df['data_entrada'].median()
primeira = df[df['data_entrada'] <= mediana_data]
segunda = df[df['data_entrada'] > mediana_data]

n1_total = len(primeira)
n1_corresp = int((primeira['canal_origem'] == 'Correspondente').sum())
n2_total = len(segunda)
n2_corresp = int((segunda['canal_origem'] == 'Correspondente').sum())

print(f"1ª metade: {n1_corresp}/{n1_total} = {n1_corresp/n1_total*100:.1f}% correspondente")
print(f"2ª metade: {n2_corresp}/{n2_total} = {n2_corresp/n2_total*100:.1f}% correspondente")
z, p = teste_duas_proporcoes(n1_corresp, n1_total, n2_corresp, n2_total)
sig = "diferença estatisticamente significativa" if p < 0.05 else "SEM diferença estatisticamente significativa"
print(f"Teste de duas proporções: z = {z:.3f}, p-valor = {p:.4f} ({sig} a 5%)")

# --- 3. Decomposição: quanto da queda geral é "mix de canal" vs. "taxa dentro de cada canal" ---
secao("3. Decomposição da queda de conversão: efeito de mix vs. efeito de taxa por canal")

taxa_geral_1 = primeira['contratada'].mean() * 100
taxa_geral_2 = segunda['contratada'].mean() * 100
print(f"Taxa de conversão geral observada: 1ª metade = {taxa_geral_1:.2f}% | 2ª metade = {taxa_geral_2:.2f}%")
print(f"Queda observada: {taxa_geral_1 - taxa_geral_2:.2f} pontos percentuais")

taxa_por_canal_1 = primeira.groupby('grupo_canal')['contratada'].mean()
taxa_por_canal_2 = segunda.groupby('grupo_canal')['contratada'].mean()
mix_1 = primeira['grupo_canal'].value_counts(normalize=True)
mix_2 = segunda['grupo_canal'].value_counts(normalize=True)

print("\nTaxa de conversão por grupo de canal (%):")
print(pd.DataFrame({'1a_metade': (taxa_por_canal_1 * 100).round(2),
                     '2a_metade': (taxa_por_canal_2 * 100).round(2)}))
print("\nParticipação no volume por grupo de canal (%):")
print(pd.DataFrame({'1a_metade': (mix_1 * 100).round(2),
                     '2a_metade': (mix_2 * 100).round(2)}))

# Contrafactual: taxa geral que teríamos na 2ª metade SE o mix tivesse ficado igual ao
# da 1ª metade, usando as taxas REAIS de cada canal observadas na 2ª metade.
taxa_contrafactual = (mix_1 * taxa_por_canal_2).sum() * 100
print(f"\nContrafactual — se o mix de canal não tivesse mudado (mas as taxas reais da "
      f"2ª metade sim): taxa geral seria {taxa_contrafactual:.2f}%")
print(f"Taxa real observada na 2ª metade: {taxa_geral_2:.2f}%")

efeito_mix = taxa_contrafactual - taxa_geral_2
efeito_taxa = taxa_geral_1 - taxa_contrafactual
print(f"\nEfeito atribuível à MUDANÇA DE MIX de canal: {efeito_mix:+.2f} p.p.")
print(f"Efeito atribuível à QUEDA DE TAXA dentro de cada canal: {efeito_taxa:+.2f} p.p.")
print(f"Soma dos dois efeitos: {efeito_mix + efeito_taxa:.2f} "
      f"(deve bater com a queda total observada: {taxa_geral_1 - taxa_geral_2:.2f})")
