"""
calcular_impacto_recomendacoes.py
Desafio Prático - Estágio AI & Data Lab | Bari
Parte 1 — Pergunta 4: números de suporte para as 3 recomendações
priorizadas. Calculado com precisão a partir da base tratada, em vez de
estimativas aproximadas — cada cenário abaixo declara a premissa usada.
"""

import pandas as pd

pd.set_option('display.float_format', lambda x: f'{x:,.2f}')


def secao(titulo):
    print("\n" + "=" * 78)
    print(titulo)
    print("=" * 78)


df = pd.read_csv('propostas_credito_tratado.csv')
df['contratada'] = (df['status_final'] == 'Contratada').astype(int)

# --- R1: reduzir a taxa de queda condicional da Etapa 5 (Formalização) ---
secao("R1. Etapa 5 (Formalização) — impacto de reduzir a taxa de queda condicional")
chegaram_5 = (df['etapa_max_funil'] >= 5).sum()
pararam_5 = (df['etapa_max_funil'] == 5).sum()
taxa_queda_atual = pararam_5 / chegaram_5
ticket_medio_parados_5 = df.loc[df['etapa_max_funil'] == 5, 'valor_solicitado'].mean()
print(f"Chegaram na etapa 5: {chegaram_5} | Pararam ali: {pararam_5} | "
      f"Taxa de queda atual: {taxa_queda_atual*100:.1f}%")
print(f"Ticket médio de quem para na etapa 5: R$ {ticket_medio_parados_5:,.2f}")

for reducao_pp in [5, 10, 15]:
    nova_taxa = taxa_queda_atual - reducao_pp / 100
    propostas_recuperadas = chegaram_5 * (reducao_pp / 100)
    valor_recuperado = propostas_recuperadas * ticket_medio_parados_5
    print(f"Se a taxa de queda cair {reducao_pp} p.p. (de {taxa_queda_atual*100:.1f}% para "
          f"{nova_taxa*100:.1f}%): ~{propostas_recuperadas:.0f} propostas a mais, "
          f"~R$ {valor_recuperado:,.2f}")

# --- R2: elevar a conversão do canal Correspondente ---
secao("R2. Canal Correspondente — impacto de elevar a conversão")
corresp = df[df['canal_origem'] == 'Correspondente']
n_corresp = len(corresp)
taxa_corresp = corresp['contratada'].mean()
ticket_medio_corresp = corresp['valor_solicitado'].mean()
taxa_outros = df.loc[df['canal_origem'] != 'Correspondente', 'contratada'].mean()
print(f"Correspondente: {n_corresp} propostas | taxa atual: {taxa_corresp*100:.1f}% | "
      f"ticket médio: R$ {ticket_medio_corresp:,.2f}")
print(f"Taxa dos demais canais (referência): {taxa_outros*100:.1f}%")

for cenario, alvo in [('conservador — metade do gap', taxa_corresp + (taxa_outros - taxa_corresp) / 2),
                       ('otimista — paridade total', taxa_outros)]:
    propostas_adicionais = n_corresp * (alvo - taxa_corresp)
    valor_adicional = propostas_adicionais * ticket_medio_corresp
    print(f"Cenário {cenario}: taxa alvo {alvo*100:.1f}%, "
          f"~{propostas_adicionais:.0f} propostas a mais, ~R$ {valor_adicional:,.2f}")

# --- R3: exposição a risco de contratos com LTV acima da política (60%) ---
secao("R3. Exposição a risco — contratos com LTV acima de 60%")
contratos_acima_ltv = df[(df['ltv'] > 0.60) & (df['contratada'] == 1)]
n_exp = len(contratos_acima_ltv)
total_contratos = int(df['contratada'].sum())
valor_exp = contratos_acima_ltv['valor_solicitado'].sum()
ltv_medio_exp = contratos_acima_ltv['ltv'].mean()
print(f"Contratos com LTV > 60%: {n_exp} de {total_contratos} totais "
      f"({n_exp/total_contratos*100:.1f}%)")
print(f"Valor total desses contratos: R$ {valor_exp:,.2f}")
print(f"LTV médio nesse grupo específico: {ltv_medio_exp*100:.1f}%")
