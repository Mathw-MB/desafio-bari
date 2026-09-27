"""
investigacao_terreno.py
Desafio Prático - Estágio AI & Data Lab | Bari
"""

import pandas as pd
from statistics import NormalDist

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 130)


def secao(titulo):
    print("\n" + "=" * 78)
    print(titulo)
    print("=" * 78)


def limpar_valor_imovel(serie):
    limpo = serie.astype(str).str.replace('R$', '', regex=False).str.strip()
    return pd.to_numeric(limpo, errors='coerce')


def teste_duas_proporcoes(x1, n1, x2, n2):
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    erro_padrao = (p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) ** 0.5
    z = (p1 - p2) / erro_padrao
    pvalor = 2 * (1 - NormalDist().cdf(abs(z)))
    return z, pvalor


df = pd.read_csv('propostas_credito.csv')
df['valor_imovel'] = limpar_valor_imovel(df['valor_imovel'])
df['ltv'] = df['valor_solicitado'] / df['valor_imovel']
df['contratada'] = (df['status_final'] == 'Contratada').astype(int)

secao("1. Perfil de cada tipo_imovel (incluindo Terreno)")
resumo = df.groupby('tipo_imovel').agg(
    qtd=('id_proposta', 'count'),
    taxa_contratacao_pct=('contratada', lambda s: round(s.mean() * 100, 1)),
    ltv_medio=('ltv', lambda s: round(s.mean(), 3)),
    ltv_mediano=('ltv', lambda s: round(s.median(), 3)),
    score_medio=('score_credito', lambda s: round(s.mean(), 1)),
    ticket_medio=('valor_solicitado', lambda s: round(s.mean(), 2)),
    prazo_medio=('prazo_meses', lambda s: round(s.mean(), 1)),
)
print(resumo)

secao("2. Terreno vs. TODOS os outros tipos combinados — taxa de contratação")
terreno = df[df['tipo_imovel'] == 'Terreno']
outros = df[df['tipo_imovel'] != 'Terreno']
x1, n1 = int(terreno['contratada'].sum()), len(terreno)
x2, n2 = int(outros['contratada'].sum()), len(outros)
print(f"Terreno: {n1} propostas | {x1} contratos | taxa: {x1/n1*100:.1f}%")
print(f"Outros:  {n2} propostas | {x2} contratos | taxa: {x2/n2*100:.1f}%")
z, p = teste_duas_proporcoes(x1, n1, x2, n2)
sig = "diferença estatisticamente significativa" if p < 0.05 else "SEM diferença estatisticamente significativa"
print(f"Teste de duas proporções: z={z:.3f}, p={p:.4f} ({sig} a 5%)")

secao("3. LTV: Terreno vs. Outros")
print(f"LTV médio Terreno: {terreno['ltv'].mean():.3f} | mediano: {terreno['ltv'].median():.3f}")
print(f"LTV médio Outros:  {outros['ltv'].mean():.3f} | mediano: {outros['ltv'].median():.3f}")

secao("4. Distribuição de etapa_max_funil: Terreno vs. Outros (proporção dentro de cada grupo)")
print(pd.crosstab(df['tipo_imovel'] == 'Terreno', df['etapa_max_funil'], normalize='index').round(3))

secao("5. Distribuição de canal_origem: Terreno vs. Outros (proporção dentro de cada grupo)")
print(pd.crosstab(df['tipo_imovel'] == 'Terreno', df['canal_origem'], normalize='index').round(3))

secao("6. status_final: Terreno vs. Outros (proporção dentro de cada grupo)")
print(pd.crosstab(df['tipo_imovel'] == 'Terreno', df['status_final'], normalize='index').round(3))
