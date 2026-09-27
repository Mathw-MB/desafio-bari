"""
analise_associacao_contratacao.py
Desafio Prático - Estágio AI & Data Lab | Bari
Parte 1 — Pergunta 3: "Quais características da proposta mais se
associam à contratação? (canal, LTV, tipo de imóvel, score, ticket,
região, prazo...)"

Duas leituras, como na Pergunta 1:
  A) Univariada — cada característica isolada, taxa de contratação simples.
  B) Multivariada — regressão logística controlando todas as
     características ao mesmo tempo. Importante porque elas estão
     correlacionadas entre si (ex.: será que LTV alto só "parece" ruim
     porque certos canais concentram tickets maiores?) a leitura
     univariada sozinha pode enganar.

Variáveis usadas: só características disponíveis NO MOMENTO da proposta
(canal, tipo de imóvel, região, score, LTV, ticket, prazo, idade, renda,
cliente recorrente). Ficam de fora de propósito: etapa_max_funil e
tempo_analise_dias, porque são resultado do processo, não característica
da proposta, incluir eles seria vazamento de informação (a pergunta é
"o que se associa a contratar", não "o que indica que já contratou").

Requer: pip install statsmodels (dentro do venv)
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 130)
pd.set_option('display.float_format', lambda x: f'{x:,.3f}')


def secao(titulo):
    print("\n" + "=" * 78)
    print(titulo)
    print("=" * 78)


df = pd.read_csv('propostas_credito_tratado.csv')
df['contratada'] = (df['status_final'] == 'Contratada').astype(int)

# =========================================================================
# PARTE A — Leitura univariada: cada característica isolada
# =========================================================================

secao("A1. Taxa de contratação por canal_origem")
print(df.groupby('canal_origem')['contratada'].agg(['mean', 'count'])
      .rename(columns={'mean': 'taxa_contratacao'}).sort_values('taxa_contratacao', ascending=False))

secao("A2. Taxa de contratação por tipo_imovel")
print(df.groupby('tipo_imovel')['contratada'].agg(['mean', 'count'])
      .rename(columns={'mean': 'taxa_contratacao'}).sort_values('taxa_contratacao', ascending=False))

secao("A3. Taxa de contratação por uf (região)")
print(df.groupby('uf')['contratada'].agg(['mean', 'count'])
      .rename(columns={'mean': 'taxa_contratacao'}).sort_values('taxa_contratacao', ascending=False))

secao("A4. Variáveis numéricas: média em propostas contratadas vs. não contratadas")
numericas = ['score_credito', 'ltv', 'valor_solicitado', 'prazo_meses',
             'idade_cliente', 'renda_mensal_declarada']
comparacao = df.groupby('contratada')[numericas].mean().T
comparacao.columns = ['nao_contratada', 'contratada']
comparacao['diferenca'] = comparacao['contratada'] - comparacao['nao_contratada']
print(comparacao)

secao("A5. flag_cliente_recorrente: taxa de contratação")
print(df.groupby('flag_cliente_recorrente')['contratada'].agg(['mean', 'count']))

# =========================================================================
# PARTE B — Leitura multivariada: regressão logística controlando tudo junto
# =========================================================================
secao("B0. Preparando os dados para a regressão")

dados = df.dropna(subset=['idade_cliente']).copy()
print(f"Linhas usadas no modelo: {len(dados)} (de {len(df)} — "
      f"{len(df) - len(dados)} descartada(s) por idade_cliente inválida)")

# Padronizar variáveis numéricas (z-score): sem isso, score_credito
# (300-1000) e ltv (0-1) teriam coeficientes em escalas incomparáveis,
# e não daria pra comparar o "tamanho do efeito" de forma justa.
numericas_modelo = ['score_credito', 'ltv', 'valor_solicitado', 'prazo_meses',
                     'idade_cliente', 'renda_mensal_declarada']
for col in numericas_modelo:
    dados[col + '_z'] = (dados[col] - dados[col].mean()) / dados[col].std()

# Categorias de referência explícitas (a "típica"), não a ordem alfabética
dados['canal_origem'] = pd.Categorical(
    dados['canal_origem'],
    categories=['Organico', 'Correspondente', 'Indicação', 'Mídia paga', 'Parceria'],
)
dados['tipo_imovel'] = pd.Categorical(
    dados['tipo_imovel'],
    categories=['Apartamento', 'Casa', 'Imóvel rural', 'Sala comercial', 'Terreno'],
)

colunas_modelo = [c + '_z' for c in numericas_modelo] + [
    'canal_origem', 'tipo_imovel', 'uf', 'flag_cliente_recorrente',
]
X = pd.get_dummies(dados[colunas_modelo], columns=['canal_origem', 'tipo_imovel', 'uf'],
                    drop_first=True, dtype=float)
X = sm.add_constant(X)
y = dados['contratada']

secao("B1. Regressão logística — coeficiente, odds ratio e p-valor (todas as variáveis)")
modelo = sm.Logit(y, X).fit(disp=0)
resultado = pd.DataFrame({
    'coeficiente': modelo.params,
    'odds_ratio': np.exp(modelo.params),
    'p_valor': modelo.pvalues,
}).drop('const')
print(resultado.sort_values('p_valor'))

secao("B2. Só as características com associação estatisticamente significativa (p<0.05)")
significativas = resultado[resultado['p_valor'] < 0.05].copy()
significativas['direcao'] = np.where(significativas['odds_ratio'] > 1, 'aumenta chance', 'reduz chance')
print(significativas.sort_values('p_valor'))

secao("B3. Qualidade do modelo (para contexto, não é o foco principal)")
print(f"Pseudo R² (McFadden): {modelo.prsquared:.4f}")
print(f"Observações usadas: {int(modelo.nobs)}")
print(f"Categoria de referência — canal: Organico | tipo_imovel: Apartamento | uf: "
      f"{sorted(dados['uf'].unique())[0]} (a que ficou de fora dos dummies)")
