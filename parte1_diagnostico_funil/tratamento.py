"""
tratamento.py
Desafio Prático - Estágio AI & Data Lab | Bari

Funções de limpeza e tratamento de propostas_credito.csv, isoladas em
funções reaproveitáveis. Este módulo é usado tanto na Parte 1 (análise)
quanto na Parte 2 (automação/RPA) — a lógica de tratamento não é
reescrita duas vezes, só importada.

Todas as decisões aplicadas aqui estão documentadas e justificadas em
registro_tratamento_dados.md — este script é a implementação daquelas
decisões, não o lugar onde elas são discutidas.

Rodar direto (python tratamento.py) lê propostas_credito.csv, aplica o
tratamento, salva propostas_credito_tratado.csv e imprime um log do que
foi feito.
"""

import numpy as np
import pandas as pd


def parse_data_hibrida(serie):
    """
    Converte uma coluna de datas em texto para datetime, lidando com a
    mistura de formatos ISO (AAAA-MM-DD, maioria) e brasileiro
    (DD/MM/AAAA, minoria) sem corromper as datas que já estavam certas.
    Ver item 7 do registro de tratamento de dados para o motivo de não
    usar simplesmente dayfirst=True na coluna inteira.
    """
    parsed = pd.to_datetime(serie, errors='coerce')
    faltando = parsed.isna() & serie.notna()
    if faltando.any():
        parsed.loc[faltando] = pd.to_datetime(serie[faltando], dayfirst=True, errors='coerce')
    return parsed


def limpar_valor_imovel(serie):
    """
    Converte valor_imovel (texto) para número. Formato padrão: string
    decimal simples ("495077.66"). Exceção: algumas linhas vêm como
    "R$ 495077.66" — removemos o prefixo e espaços antes de converter.
    Ver item 5 do registro de tratamento de dados.
    """
    limpo = serie.astype(str).str.replace('R$', '', regex=False).str.strip()
    return pd.to_numeric(limpo, errors='coerce')


def normalizar_canal_origem(serie):
    """
    Normaliza canal_origem removendo espaços extras e diferenças de
    maiúscula/minúscula, padronizando para a grafia oficial (a mais
    frequente na base). Ver item 2 do registro de tratamento de dados.
    """
    normalizado = serie.str.strip().str.lower()
    grafia_oficial = {
        'correspondente': 'Correspondente',
        'organico': 'Organico',
        'mídia paga': 'Mídia paga',
        'indicação': 'Indicação',
        'parceria': 'Parceria',
    }
    return normalizado.map(grafia_oficial).fillna(normalizado)


def carregar_e_tratar(caminho_csv, log=None):
    """
    Lê o CSV bruto e aplica todas as regras de tratamento documentadas em
    registro_tratamento_dados.md. Retorna (df_tratado, log).

    `log` é um dicionário que esta função preenche com um resumo do que
    foi feito — útil para imprimir na tela e, mais pra frente, para o log
    de execução da Parte 2.
    """
    if log is None:
        log = {}

    df = pd.read_csv(caminho_csv)
    if df.shape[1] == 1:
        df = pd.read_csv(caminho_csv, sep=';')

    log['linhas_brutas'] = len(df)

  
    log['propostas_terreno_mantidas'] = int((df['tipo_imovel'] == 'Terreno').sum())

    # Item 2: normalizar canal_origem
    df['canal_origem'] = normalizar_canal_origem(df['canal_origem'])

    # Item 5: valor_imovel para numérico
    df['valor_imovel'] = limpar_valor_imovel(df['valor_imovel'])

    # Item 1: calcular LTV (não existe pronto no CSV)
    df['ltv'] = df['valor_solicitado'] / df['valor_imovel']
    log['propostas_ltv_acima_60pct'] = int((df['ltv'] > 0.60).sum())

    # Item 7: parse híbrido de datas (evita o bug do dayfirst cego)
    df['data_entrada'] = parse_data_hibrida(df['data_entrada'])
    df['data_assinatura_contrato'] = parse_data_hibrida(df['data_assinatura_contrato'])

    # Item 6: idade_cliente inválida (< 18 ou > 100) vira nula — não descartamos a linha,
    # e não chutamos um valor plausível no lugar (ver item 6 do registro).
    df['idade_cliente'] = df['idade_cliente'].astype('Int64')
    idade_invalida = ~df['idade_cliente'].between(18, 100)
    log['linhas_idade_invalida'] = int(idade_invalida.sum())
    df.loc[idade_invalida, 'idade_cliente'] = pd.NA

    # Item 9: corrigir etapa_max_funil == 7 para 6 (justificativa completa no registro)
    linha_a_corrigir = df['etapa_max_funil'] == 7
    log['linhas_etapa_corrigida'] = int(linha_a_corrigir.sum())
    log['ids_etapa_corrigida'] = df.loc[linha_a_corrigir, 'id_proposta'].tolist()
    df.loc[linha_a_corrigir, 'etapa_max_funil'] = 6

    # Item 8: marcar (sem descartar) a linha com assinatura antes da entrada
    df['data_inconsistente'] = df['data_assinatura_contrato'] < df['data_entrada']
    log['linhas_data_inconsistente'] = int(df['data_inconsistente'].sum())

    # Item 4: taxa_juros_aa é, na prática, mensal. Mantemos a coluna original
    # (rastreabilidade) e criamos uma cópia com nome sem ambiguidade.
    df['taxa_juros_am'] = df['taxa_juros_aa']

    # Sanity check: algum valor de ltv não calculável (divisão por zero/NaN)?
    log['linhas_ltv_nao_calculavel'] = int(df['ltv'].isna().sum() + np.isinf(df['ltv']).sum())

    log['linhas_tratadas'] = len(df)

    return df, log


if __name__ == '__main__':
    df_tratado, log = carregar_e_tratar('propostas_credito.csv')

    print("=" * 70)
    print("LOG DE EXECUÇÃO DO TRATAMENTO")
    print("=" * 70)
    for chave, valor in log.items():
        print(f"{chave}: {valor}")

    df_tratado.to_csv('propostas_credito_tratado.csv', index=False)
    print(f"\nArquivo tratado salvo em propostas_credito_tratado.csv")
    print(f"Linhas finais: {len(df_tratado)} (de {log['linhas_brutas']} originais)")
