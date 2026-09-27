"""
gerar_csv_sinteticos.py
Gera os CSVs sintéticos usados para testar gerar_relatorio_semanal.py contra
os casos-limite que a Parte 2 pede para cobrir: arquivo válido, coluna
crítica ausente, coluna não-crítica ausente, formato novo (abaixo e acima
do limiar crítico), encoding alternativo, e arquivo vazio.

Roda uma vez (python testes/gerar_csv_sinteticos.py) e escreve tudo em
testes/dados_sinteticos/.
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
PASTA = "dados_sinteticos"

CANAIS = ["Correspondente", "Organico", "Mídia paga", "Indicação", "Parceria"]
TIPOS_IMOVEL = ["Apartamento", "Casa", "Comercial", "Terreno", "Sobrado"]
STATUS_POSSIVEIS = ["Contratada", "Reprovada crédito", "Desistência cliente", "Reprovada garantia"]


def _base(n: int) -> pd.DataFrame:
    datas_entrada = pd.date_range("2024-01-01", "2025-12-01", periods=n)
    valor_imovel = RNG.uniform(150_000, 900_000, n).round(2)
    valor_solicitado = (valor_imovel * RNG.uniform(0.2, 0.75, n)).round(2)
    etapa_max_funil = RNG.integers(1, 7, n)
    status_final = RNG.choice(STATUS_POSSIVEIS, n, p=[0.2, 0.4, 0.25, 0.15])
    # garante coerência básica: quem é 'Contratada' tende a etapa 6
    status_final = status_final.copy()
    idx_contratada_forcada = RNG.choice(n, size=max(1, n // 6), replace=False)
    status_final[idx_contratada_forcada] = "Contratada"
    etapa_max_funil[idx_contratada_forcada] = 6

    df = pd.DataFrame(
        {
            "id_proposta": [f"PR-{i:06d}" for i in range(1, n + 1)],
            "data_entrada": [d.strftime("%Y-%m-%d") for d in datas_entrada],
            "canal_origem": RNG.choice(CANAIS, n),
            "cidade": RNG.choice(["São Paulo", "Curitiba", "Belo Horizonte", "Recife"], n),
            "uf": RNG.choice(["SP", "PR", "MG", "PE"], n),
            "tipo_imovel": RNG.choice(TIPOS_IMOVEL, n),
            "valor_imovel": [f"{v:.2f}" for v in valor_imovel],
            "valor_solicitado": valor_solicitado,
            "prazo_meses": RNG.choice([120, 180, 240], n),
            "score_credito": RNG.integers(300, 1000, n),
            "idade_cliente": RNG.integers(21, 75, n),
            "renda_mensal_declarada": RNG.uniform(3000, 40000, n).round(2),
            "flag_cliente_recorrente": RNG.integers(0, 2, n),
            "consultor_id": RNG.choice([f"C{i:03d}" for i in range(1, 21)], n),
            "etapa_max_funil": etapa_max_funil,
            "status_final": status_final,
            "tempo_analise_dias": RNG.integers(1, 90, n),
            "data_assinatura_contrato": "",
            "taxa_juros_aa": np.round(RNG.uniform(0.94, 1.73, n), 2),
        }
    )
    contratadas = df["status_final"] == "Contratada"
    df.loc[contratadas, "data_assinatura_contrato"] = [
        (pd.Timestamp(d) + pd.Timedelta(days=int(t))).strftime("%Y-%m-%d")
        for d, t in zip(df.loc[contratadas, "data_entrada"], df.loc[contratadas, "tempo_analise_dias"])
    ]
    return df


def gerar_valido():
    df = _base(300)
    # três linhas com prefixo "R$" - mesmo precedente da Parte 1 (item 5)
    idx = [5, 42, 199]
    df.loc[idx, "valor_imovel"] = [f"R$ {df.loc[i, 'valor_imovel']}" for i in idx]
    # uma linha de data em formato brasileiro (dd/mm/aaaa) - precedente item 7
    df.loc[10, "data_entrada"] = "15/03/2024"
    # uma idade inválida - precedente item 6
    df.loc[20, "idade_cliente"] = 14
    # uma etapa == 7 com status Contratada - precedente item 9 (deve ser corrigida)
    df.loc[30, "etapa_max_funil"] = 7
    df.loc[30, "status_final"] = "Contratada"
    # uma etapa anômala (9) SEM Contratada - não deve ser corrigida automaticamente
    df.loc[31, "etapa_max_funil"] = 9
    df.loc[31, "status_final"] = "Reprovada crédito"
    # grafia divergente de canal (item 2)
    df.loc[40, "canal_origem"] = " correspondente "
    df.to_csv(f"{PASTA}/valido.csv", index=False, encoding="utf-8")


def gerar_falta_coluna_critica():
    df = _base(100).drop(columns=["valor_imovel"])
    df.to_csv(f"{PASTA}/falta_coluna_critica.csv", index=False, encoding="utf-8")


def gerar_falta_coluna_nao_critica():
    df = _base(100).drop(columns=["idade_cliente"])
    df.to_csv(f"{PASTA}/falta_coluna_nao_critica.csv", index=False, encoding="utf-8")


def gerar_formato_novo_aviso():
    df = _base(200)
    # ~2% das linhas com um formato de moeda nunca visto (separador de milhar
    # brasileiro + vírgula decimal) - deve gerar AVISO, não abortar.
    idx = RNG.choice(200, size=4, replace=False)
    df.loc[idx, "valor_imovel"] = ["R$ 1.234.567,89"] * len(idx)
    df.to_csv(f"{PASTA}/formato_novo_aviso.csv", index=False, encoding="utf-8")


def gerar_formato_novo_critico():
    df = _base(200)
    # mais de 20% das linhas num formato totalmente diferente (moeda
    # americana) - deve abortar, não gerar relatório com números errados.
    idx = RNG.choice(200, size=60, replace=False)
    df.loc[idx, "valor_imovel"] = ["USD 123,456.78"] * len(idx)
    df.to_csv(f"{PASTA}/formato_novo_critico.csv", index=False, encoding="utf-8")


def gerar_encoding_latin1():
    df = _base(50)
    df.loc[0, "cidade"] = "São José dos Campos"
    df.loc[1, "cidade"] = "Conceição do Araguaia"
    df.to_csv(f"{PASTA}/encoding_latin1.csv", index=False, encoding="latin-1")


def gerar_canal_novo():
    df = _base(150)
    idx = RNG.choice(150, size=6, replace=False)
    df.loc[idx, "canal_origem"] = "Digital Ads"  # canal fora das 5 grafias oficiais conhecidas
    df.to_csv(f"{PASTA}/canal_novo.csv", index=False, encoding="utf-8")


def gerar_vazio():
    df = _base(1).iloc[0:0]  # mesmas colunas, zero linhas
    df.to_csv(f"{PASTA}/vazio.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    import os
    os.makedirs(PASTA, exist_ok=True)
    gerar_valido()
    gerar_falta_coluna_critica()
    gerar_falta_coluna_nao_critica()
    gerar_formato_novo_aviso()
    gerar_formato_novo_critico()
    gerar_encoding_latin1()
    gerar_canal_novo()
    gerar_vazio()
    print("CSVs sintéticos gerados em", PASTA)
