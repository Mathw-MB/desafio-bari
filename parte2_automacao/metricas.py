"""
metricas.py
Desafio Prático - Estágio AI & Data Lab | Bari - Parte 2 (Automação/RPA)

Funções puras: recebem o DataFrame já tratado (saída de
tratamento.carregar_e_tratar) e devolvem estruturas de dados simples
(dicts, DataFrames, escalares) - nenhuma delas sabe nada sobre HTML, Excel
ou qualquer formato de saída. Isso é proposital: os dois exportadores
(relatorio_html.py e relatorio_excel.py) consomem exatamente o mesmo
dicionário produzido por calcular_metricas(), então adicionar um terceiro
formato no futuro não exige tocar em nenhuma lógica de negócio aqui.

As métricas escolhidas reaproveitam o que mais importou na Parte 1:
conversão geral e por canal, valor perdido por etapa do funil (com taxa de
queda condicional), % de propostas acima do limite de LTV de 60%, a
checagem de consistência etapa_max_funil == 6 vs status_final == 'Contratada',
a série mensal de conversão (resposta direta à percepção da liderança de
queda "nos últimos meses" - ver decisoes_parte2.md, item 8) e a perda por
motivo de desfecho (reaproveitando os quatro motivos que o próprio
enunciado do desafio já nomeia: reprovação de crédito, problema na
garantia, desistência do cliente, documentação que nunca chega).
"""

import pandas as pd

ETAPAS_FUNIL = {
    1: "Simulação",
    2: "Lead",
    3: "Análise de crédito",
    4: "Avaliação do imóvel",
    5: "Formalização",
    6: "Contratação",
}
LTV_LIMITE = 0.60
STATUS_CONTRATADA = "Contratada"


def calcular_conversao_geral(df: pd.DataFrame) -> dict:
    total = len(df)
    contratadas = int((df["status_final"] == STATUS_CONTRATADA).sum())
    taxa = contratadas / total if total else 0.0
    return {"total_propostas": total, "total_contratadas": contratadas, "taxa_conversao": taxa}


def calcular_conversao_por_canal(df: pd.DataFrame) -> pd.DataFrame:
    agrupado = (
        df.groupby("canal_origem")
        .agg(
            total_propostas=("id_proposta", "count"),
            total_contratadas=("status_final", lambda s: (s == STATUS_CONTRATADA).sum()),
        )
        .reset_index()
    )
    agrupado["taxa_conversao"] = agrupado["total_contratadas"] / agrupado["total_propostas"]
    return agrupado.sort_values("taxa_conversao", ascending=False).reset_index(drop=True)


def calcular_funil_por_etapa(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada etapa 1-5 (a etapa 6 é o próprio sucesso), calcula:
    - propostas que alcançaram ao menos essa etapa;
    - propostas que morreram exatamente nessa etapa (etapa_max_funil == N
      e não contrataram);
    - taxa de queda condicional (morreram na etapa / alcançaram a etapa);
    - valor_solicitado somado das que morreram ali (valor potencial perdido).
    """
    linhas = []
    for etapa in range(1, 6):
        alcancaram = df[df["etapa_max_funil"] >= etapa]
        morreram = df[(df["etapa_max_funil"] == etapa) & (df["status_final"] != STATUS_CONTRATADA)]
        n_alcancaram = len(alcancaram)
        n_morreram = len(morreram)
        taxa_queda = n_morreram / n_alcancaram if n_alcancaram else 0.0
        valor_perdido = float(morreram["valor_solicitado"].sum())
        linhas.append(
            {
                "etapa": etapa,
                "nome_etapa": ETAPAS_FUNIL[etapa],
                "propostas_que_alcancaram": n_alcancaram,
                "propostas_perdidas_na_etapa": n_morreram,
                "taxa_queda_condicional": taxa_queda,
                "valor_solicitado_perdido": valor_perdido,
            }
        )
    return pd.DataFrame(linhas)


def calcular_pct_ltv_acima_limite(df: pd.DataFrame, limite: float = LTV_LIMITE) -> dict:
    validos = df["ltv"].notna() & ~df["ltv"].isin([float("inf"), float("-inf")])
    total_validos = int(validos.sum())
    acima = int(((df["ltv"] > limite) & validos).sum())
    pct = acima / total_validos if total_validos else 0.0
    return {
        "limite": limite,
        "total_propostas_com_ltv_valido": total_validos,
        "propostas_acima_do_limite": acima,
        "pct_acima_do_limite": pct,
    }


def checar_consistencia_etapa_status(df: pd.DataFrame) -> dict:
    """
    A regra de negócio esperada é etapa_max_funil == 6 <=> status_final ==
    'Contratada'. Reporta os dois sentidos do descasamento (proposta em
    etapa 6 mas não contratada; proposta contratada mas etapa != 6) para
    quem for investigar saber onde olhar.
    """
    etapa6 = df["etapa_max_funil"] == 6
    contratada = df["status_final"] == STATUS_CONTRATADA

    etapa6_nao_contratada = df.loc[etapa6 & ~contratada, "id_proposta"].tolist()
    contratada_sem_etapa6 = df.loc[contratada & ~etapa6, "id_proposta"].tolist()

    consistente = len(etapa6_nao_contratada) == 0 and len(contratada_sem_etapa6) == 0
    return {
        "consistente": consistente,
        "ids_etapa6_nao_contratada": etapa6_nao_contratada,
        "ids_contratada_sem_etapa6": contratada_sem_etapa6,
    }


def calcular_conversao_mensal(df: pd.DataFrame, n_meses_recentes: int = 2) -> dict:
    """
    Série mensal de conversão a partir de data_entrada - a métrica que
    faltava na primeira versão deste módulo (ver decisoes_parte2.md, item
    8). Não precisa de nenhum histórico entre execuções: cada rodada
    reprocessa o CSV bruto inteiro, que já tem ~2 anos de `data_entrada`,
    então a série mensal sai de uma única execução, do mesmo jeito que a
    Pergunta 2 da Parte 1 calculou.

    `data_entrada` é uma coluna não-crítica - se estiver ausente ou não
    tiver nenhuma data válida, retorna disponivel=False em vez de quebrar,
    e os exportadores mostram a seção como indisponível.
    """
    if "data_entrada" not in df.columns or df["data_entrada"].notna().sum() == 0:
        return {"disponivel": False, "serie": pd.DataFrame(), "meses_recentes_destacados": []}

    valido = df[df["data_entrada"].notna()].copy()
    valido["mes"] = valido["data_entrada"].dt.to_period("M")

    serie = (
        valido.groupby("mes")
        .agg(
            total_propostas=("id_proposta", "count"),
            total_contratadas=("status_final", lambda s: (s == STATUS_CONTRATADA).sum()),
        )
        .reset_index()
        .sort_values("mes")
    )
    serie["taxa_conversao"] = serie["total_contratadas"] / serie["total_propostas"]
    serie["mes_rotulo"] = serie["mes"].astype(str)

    meses_recentes = serie["mes_rotulo"].tail(n_meses_recentes).tolist()

    return {"disponivel": True, "serie": serie, "meses_recentes_destacados": meses_recentes}


def calcular_perda_por_motivo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Quebra as propostas que NÃO contrataram por status_final (motivo de
    desfecho) - o enunciado do desafio já nomeia quatro motivos possíveis
    de perda no funil (reprovação de crédito, problema na garantia,
    desistência do cliente, documentação que nunca chega). Como não sabemos
    de antemão todos os valores que status_final pode assumir na base real,
    a quebra é genérica por valor encontrado - um motivo novo aparece aqui
    naturalmente, sem precisar de nenhum código novo.
    """
    nao_contratadas = df[df["status_final"] != STATUS_CONTRATADA]
    if nao_contratadas.empty:
        return pd.DataFrame(columns=["status_final", "quantidade", "valor_solicitado_perdido"])

    agrupado = (
        nao_contratadas.groupby("status_final")
        .agg(
            quantidade=("id_proposta", "count"),
            valor_solicitado_perdido=("valor_solicitado", "sum"),
        )
        .reset_index()
        .sort_values("valor_solicitado_perdido", ascending=False)
        .reset_index(drop=True)
    )
    return agrupado


def montar_resumo_qualidade_dados(log: dict) -> dict:
    """
    Reaproveita o log produzido por tratamento.carregar_e_tratar para
    montar a seção de qualidade de dados do relatório - a mesma
    transparência que o registro_tratamento_dados.md dá para a Parte 1,
    só que por execução, automaticamente.
    """
    return {
        "encoding_usado": log.get("encoding_usado"),
        "linhas_brutas": log.get("linhas_brutas"),
        "linhas_tratadas": log.get("linhas_tratadas"),
        "linhas_idade_invalida": log.get("linhas_idade_invalida"),
        "linhas_data_inconsistente": log.get("linhas_data_inconsistente"),
        "linhas_etapa_corrigida": log.get("linhas_etapa_corrigida"),
        "linhas_etapa_anomala_nao_corrigida": log.get("linhas_etapa_anomala_nao_corrigida"),
        "propostas_terreno_mantidas": log.get("propostas_terreno_mantidas"),
        "canais_nao_reconhecidos": log.get("canais_nao_reconhecidos", []),
        "avisos": log.get("avisos", []),
    }


def calcular_metricas(df: pd.DataFrame, log: dict) -> dict:
    """Ponto de entrada único: monta todo o pacote de métricas + qualidade
    de dados que os exportadores (HTML/Excel) vão consumir."""
    return {
        "conversao_geral": calcular_conversao_geral(df),
        "conversao_por_canal": calcular_conversao_por_canal(df),
        "funil_por_etapa": calcular_funil_por_etapa(df),
        "ltv": calcular_pct_ltv_acima_limite(df),
        "consistencia_etapa_status": checar_consistencia_etapa_status(df),
        "conversao_mensal": calcular_conversao_mensal(df),
        "perda_por_motivo": calcular_perda_por_motivo(df),
        "qualidade_dados": montar_resumo_qualidade_dados(log),
    }
