"""
analise_funil_valor.py
Desafio Prático - Estágio AI & Data Lab | Bari
Parte 1 — Pergunta 1: "Onde o funil perde mais valor? Não só onde perde
mais propostas — onde perde mais dinheiro potencial."

Usa o arquivo já tratado (propostas_credito_tratado.csv), não o bruto —
o tratamento (Terreno removido, LTV calculado, datas e valores corrigidos
etc.) já foi feito pelo tratamento.py.
"""

import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')

df = pd.read_csv('propostas_credito_tratado.csv')


def secao(titulo):
    print("\n" + "=" * 78)
    print(titulo)
    print("=" * 78)


# --- 0. Checar a premissa: etapa_max_funil == 6 sempre bate com Contratada? ---
secao("0. Cruzamento etapa_max_funil x status_final (checando a premissa)")
print(pd.crosstab(df['etapa_max_funil'], df['status_final']))

# --- 1. Volume e valor solicitado por etapa máxima atingida ---
secao("1. Propostas e valor solicitado por etapa_max_funil")
resumo_etapa = df.groupby('etapa_max_funil').agg(
    qtd_propostas=('id_proposta', 'count'),
    valor_total_solicitado=('valor_solicitado', 'sum'),
    valor_medio_solicitado=('valor_solicitado', 'mean'),
).reset_index()
print(resumo_etapa)

# --- 2. "Valor perdido" por etapa: dinheiro solicitado em propostas que
#         pararam ali e nunca viraram contrato (etapas 1 a 5) ---
secao("2. Valor 'perdido' por etapa (propostas que pararam ali, sem contratar)")
perda_por_etapa = (
    df[df['etapa_max_funil'] < 6]
    .groupby('etapa_max_funil')
    .agg(qtd_propostas=('id_proposta', 'count'), valor_perdido=('valor_solicitado', 'sum'))
    .reset_index()
    .sort_values('valor_perdido', ascending=False)
)
perda_por_etapa['pct_do_valor_perdido_total'] = (
    perda_por_etapa['valor_perdido'] / perda_por_etapa['valor_perdido'].sum() * 100
).round(1)
print(perda_por_etapa)

total_perdido = perda_por_etapa['valor_perdido'].sum()
total_contratado = df.loc[df['etapa_max_funil'] == 6, 'valor_solicitado'].sum()
print(f"\nTotal solicitado que NÃO virou contrato: R$ {total_perdido:,.2f}")
print(f"Total solicitado que virou contrato:     R$ {total_contratado:,.2f}")
print(f"Taxa de conversão em valor: {total_contratado / (total_contratado + total_perdido) * 100:.1f}%")

# --- 3. Dentro de cada etapa de parada, qual o motivo (status_final)? ---
secao("3. Dentro de cada etapa onde a proposta parou, qual o status_final?")
detalhe = (
    df[df['etapa_max_funil'] < 6]
    .groupby(['etapa_max_funil', 'status_final'])
    .agg(qtd=('id_proposta', 'count'), valor=('valor_solicitado', 'sum'))
    .reset_index()
    .sort_values(['etapa_max_funil', 'valor'], ascending=[True, False])
)
print(detalhe)

# --- 4. Achado do LTV > 60%: o que acontece com essas propostas? ---
secao("4. LTV acima de 60% (limite da política) — o que acontece com essas propostas?")
acima_ltv = df[df['ltv'] > 0.60]
print(f"Total de propostas com LTV > 60%: {len(acima_ltv)}")
print(acima_ltv['status_final'].value_counts())
qtd_contratadas_acima_ltv = (acima_ltv['status_final'] == 'Contratada').sum()
print(f"\nDessas, viraram contrato: {qtd_contratadas_acima_ltv}")
print(f"Taxa de contratação geral (toda a base tratada): {(df['status_final'] == 'Contratada').mean()*100:.1f}%")
print(f"Taxa de contratação entre LTV > 60%: {(acima_ltv['status_final'] == 'Contratada').mean()*100:.1f}%")

# --- 5. Taxa de queda condicional por etapa: de quem CHEGA na etapa, quantos não avançam ---
# Isso é diferente da seção 2 (valor absoluto perdido) aqui olhamos proporção, não volume.
# Uma etapa pode perder pouco dinheiro em termos absolutos (porque pouca gente chega até
# ela) mas ainda assim ser, proporcionalmente, o maior gargalo do processo.
secao("5. Taxa de queda condicional por etapa (proporção de quem chega e não avança)")
restante = len(df)
linhas_queda = []
for etapa in [1, 2, 3, 4, 5]:
    parou_aqui = int((df['etapa_max_funil'] == etapa).sum())
    taxa_queda = parou_aqui / restante * 100
    linhas_queda.append({
        'etapa': etapa, 'chegaram': restante, 'pararam_aqui': parou_aqui,
        'taxa_queda_pct': round(taxa_queda, 1),
    })
    restante -= parou_aqui
print(pd.DataFrame(linhas_queda))
print(f"\nChegaram até virar contrato: {restante} "
      f"(deve bater com a contagem de status_final == 'Contratada')")

# --- 6. Perda de valor: motivo de PROCESSO (endereçável) vs. motivo de RISCO (política em ação) ---
# Nem toda "perda" é igual: reprovação de crédito e problema de garantia são, em grande
# parte, a política de risco funcionando como deveria — não é dinheiro que a empresa
# "deveria" ter capturado. Já desistência, sem retorno e documentação pendente são, em
# princípio, endereçáveis com melhoria de processo/experiência do cliente.
secao("6. Perda de valor: motivo de processo (endereçável) vs. motivo de risco (política em ação)")
motivos_processo = ['Desistiu', 'Sem retorno', 'Documentação pendente']
motivos_risco = ['Reprovada crédito', 'Problema garantia']

perdidos = df[df['etapa_max_funil'] < 6]
valor_processo = perdidos.loc[perdidos['status_final'].isin(motivos_processo), 'valor_solicitado'].sum()
valor_risco = perdidos.loc[perdidos['status_final'].isin(motivos_risco), 'valor_solicitado'].sum()
total_classificado = valor_processo + valor_risco

print(f"Perda por motivo de PROCESSO (endereçável):   R$ {valor_processo:,.2f} "
      f"({valor_processo/total_classificado*100:.1f}%)")
print(f"Perda por motivo de RISCO (política em ação): R$ {valor_risco:,.2f} "
      f"({valor_risco/total_classificado*100:.1f}%)")
print(f"Total classificado: R$ {total_classificado:,.2f}")

# --- 7. Robustez: média vs. mediana do ticket por etapa, pra checar se a média não está
#         sendo puxada por outliers (poucas propostas de ticket muito alto distorcendo o quadro) ---
secao("7. valor_solicitado por etapa: média vs. mediana (checagem de robustez)")
print(df.groupby('etapa_max_funil')['valor_solicitado'].agg(['mean', 'median', 'std']).round(2))
