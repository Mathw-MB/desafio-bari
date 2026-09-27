"""
investigacao_datas_v2.py
Desafio Prático - Estágio AI & Data Lab | Bari

A rodada anterior comparou data_assinatura_contrato < data_entrada usando
format='mixed' + dayfirst=True nas duas colunas — e isso continha um bug
confirmado: dayfirst=True inverte dia/mês sempre que os dois números depois
do ano são <= 12 (ambíguo), mesmo em datas que já estavam certas no
formato ISO (AAAA-MM-DD). Isso gerou uma contagem inflada e não confiável
(331 linhas) de supostas inconsistências.

Este script corrige com parse em duas passadas:
1) tenta o parse padrão (assume ISO, sem dayfirst) — cobre a maioria;
2) só para quem falhar (virar NaT), tenta de novo com dayfirst=True —
   cobre as poucas linhas que sabemos que estão em formato brasileiro
   dd/mm/aaaa.

Esta função (parse_data_hibrida) deve ser reaproveitada no script de
limpeza definitivo, para qualquer coluna de data.
"""

import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)

df = pd.read_csv("propostas_credito.csv")


def parse_data_hibrida(serie):
    parsed = pd.to_datetime(serie, errors='coerce')
    faltando = parsed.isna() & serie.notna()
    if faltando.any():
        parsed.loc[faltando] = pd.to_datetime(serie[faltando], dayfirst=True, errors='coerce')
    return parsed


datas_entrada = parse_data_hibrida(df['data_entrada'])
data_assinatura = parse_data_hibrida(df['data_assinatura_contrato'])

print("data_entrada ainda não interpretável:", datas_entrada.isna().sum())

nulos_raw_assinatura = df['data_assinatura_contrato'].isna().sum()
nao_interpretavel_assinatura = (data_assinatura.isna() & df['data_assinatura_contrato'].notna()).sum()
print(f"data_assinatura_contrato — nulos originais (esperado): {nulos_raw_assinatura}")
print(f"data_assinatura_contrato — não interpretável além dos nulos originais: {nao_interpretavel_assinatura}")

inconsistente = data_assinatura < datas_entrada
print(f"\nLinhas com assinatura antes da entrada (recontagem correta): {inconsistente.sum()}")
print(df.loc[inconsistente, ['id_proposta', 'data_entrada', 'data_assinatura_contrato', 'status_final']])
