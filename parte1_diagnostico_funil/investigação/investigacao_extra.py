"""
investigacao_extra.py
Desafio Prático - Estágio AI & Data Lab | Bari

Últimos 3 pontos em aberto antes de fechar as regras de limpeza:
1. As linhas de valor_imovel que contêm 'R$'
2. A linha com idade_cliente fora de 18-100
3. A linha com data_assinatura_contrato anterior a data_entrada
4. Confirmar que format='mixed' + dayfirst=True resolve as 3 datas
   que antes ficavam como não interpretáveis
"""

import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)

df = pd.read_csv("propostas_credito.csv")

print("1) Linhas com 'R$' em valor_imovel:")
print(df.loc[df['valor_imovel'].str.contains('R\\$', na=False), ['id_proposta', 'valor_imovel']])

print("\n2) Linha(s) com idade_cliente fora de 18-100:")
print(df[~df['idade_cliente'].between(18, 100)])

print("\n3) Linha(s) com data_assinatura_contrato anterior a data_entrada:")
datas_entrada = pd.to_datetime(df['data_entrada'], format='mixed', dayfirst=True, errors='coerce')
data_assinatura = pd.to_datetime(df['data_assinatura_contrato'], format='mixed', dayfirst=True, errors='coerce')
inconsistente = data_assinatura < datas_entrada
print(df[inconsistente])

print("\n4) format='mixed' + dayfirst=True resolveu as datas antes não interpretáveis?")
print(f"Linhas ainda não interpretáveis: {datas_entrada.isna().sum()}")
