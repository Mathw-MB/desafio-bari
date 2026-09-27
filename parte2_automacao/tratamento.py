"""
tratamento.py
Desafio Prático - Estágio AI & Data Lab | Bari - Parte 2 (Automação/RPA)

Esta é uma cópia do tratamento.py da Parte 1, com as mesmas 10 decisões de
negócio documentadas em registro_tratamento_dados.md (a lógica de limpeza
não muda: canal_origem, valor_imovel, ltv, datas, idade, etapa_max_funil,
taxa_juros, Terreno mantido). O que muda aqui, e está documentado em
decisoes_parte2.md, é a robustez em torno dessa mesma lógica - porque este
script agora roda sem supervisão, toda semana, e o arquivo de entrada pode
vir diferente do que veio na Parte 1:

- leitura com fallback de encoding (utf-8 -> latin-1), registrado no log;
- idade_cliente não quebra mais o script inteiro se vier um valor
  genuinamente não-numérico (antes: TypeError não tratado no .astype);
- a correção de etapa_max_funil fora do intervalo 1-6 deixou de ser
  hardcoded para o valor 7 (caso específico da Parte 1) e passou a seguir
  uma regra geral: só corrige automaticamente quando há DUAS evidências
  convergentes (valor == etapa_max + 1 E status_final == 'Contratada'),
  exatamente a mesma lógica que justificou a correção original (ver item 9
  do registro). Qualquer outro valor fora do range é sinalizado para
  revisão humana, não corrigido às cegas nem descartado - mesma filosofia
  do item 6 (idade_cliente = 14).

Scripts de partes diferentes não importam um do outro - este arquivo é
autocontido dentro de parte2_automacao/.
"""

import numpy as np
import pandas as pd

from validacao import checar_taxa_conversao

ETAPA_MIN, ETAPA_MAX = 1, 6


def ler_csv_com_fallback_encoding(caminho_csv, log):
    """
    Tenta ler o CSV em utf-8 primeiro (formato esperado); se falhar por
    encoding, tenta latin-1 (comum em exports de sistemas legados
    brasileiros) antes de desistir. Registra qual encoding foi usado -
    silenciosamente aceitar o encoding errado pode corromper acentos sem
    lançar nenhum erro.
    """
    for encoding in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(caminho_csv, encoding=encoding)
            if df.shape[1] == 1:
                df = pd.read_csv(caminho_csv, sep=";", encoding=encoding)
            log["encoding_usado"] = encoding
            return df
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(
        "utf-8/latin-1", b"", 0, 1,
        f"Não foi possível ler {caminho_csv} nem como utf-8 nem como latin-1."
    )


def parse_data_hibrida(serie):
    """
    Converte uma coluna de datas em texto para datetime, lidando com a
    mistura de formatos ISO (AAAA-MM-DD, maioria) e brasileiro
    (DD/MM/AAAA, minoria) sem corromper as datas que já estavam certas.
    Ver item 7 do registro de tratamento de dados para o motivo de não
    usar simplesmente dayfirst=True na coluna inteira.
    """
    parsed = pd.to_datetime(serie, errors="coerce")
    faltando = parsed.isna() & serie.notna()
    if faltando.any():
        parsed.loc[faltando] = pd.to_datetime(serie[faltando], dayfirst=True, errors="coerce")
    return parsed


def limpar_valor_imovel(serie):
    """
    Converte valor_imovel (texto) para número. Formato padrão: string
    decimal simples ("495077.66"). Exceção conhecida: algumas linhas vêm
    como "R$ 495077.66" - removemos o prefixo e espaços antes de converter.
    Ver item 5 do registro de tratamento de dados. Qualquer outro formato
    não reconhecido vira nulo aqui (comportamento do pd.to_numeric) - é
    checar_taxa_conversao(), chamada em carregar_e_tratar, que garante que
    isso não passe despercebido.
    """
    limpo = serie.astype(str).str.replace("R$", "", regex=False).str.strip()
    return pd.to_numeric(limpo, errors="coerce")


CANAIS_CONHECIDOS = {"Correspondente", "Organico", "Mídia paga", "Indicação", "Parceria"}


def normalizar_canal_origem(serie):
    """
    Normaliza canal_origem removendo espaços extras e diferenças de
    maiúscula/minúscula, padronizando para a grafia oficial (a mais
    frequente na base). Ver item 2 do registro de tratamento de dados.

    Um valor que não bate com nenhuma grafia conhecida (variação de
    digitação OU canal genuinamente novo que o negócio passou a usar)
    passa como está, só com espaços/caixa normalizados - não é descartado
    nem forçado a virar um dos 5 conhecidos. É `detectar_canais_novos`,
    chamada em carregar_e_tratar, que garante que isso não passe
    despercebido.
    """
    normalizado = serie.str.strip().str.lower()
    grafia_oficial = {
        "correspondente": "Correspondente",
        "organico": "Organico",
        "mídia paga": "Mídia paga",
        "indicação": "Indicação",
        "parceria": "Parceria",
    }
    return normalizado.map(grafia_oficial).fillna(normalizado)


def detectar_canais_novos(serie_normalizada):
    """
    canal_origem é uma coluna CRÍTICA - a conversão por canal é uma das
    métricas mais centrais do relatório, e é a que responde diretamente à
    pergunta da liderança sobre o canal Correspondente. Um canal que não
    bate com nenhuma das 5 grafias oficiais conhecidas (nem por variação
    de digitação) merece um aviso explícito, mesmo sem abortar a execução
    - pode ser só sujeira, ou pode ser um canal novo que o negócio passou
    a usar e que vale a pena a liderança saber que está sendo somado à
    conversão geral pela primeira vez.
    """
    encontrados = set(serie_normalizada.dropna().unique())
    return sorted(encontrados - CANAIS_CONHECIDOS)


def corrigir_etapa_max_funil(df, log):
    """
    etapa_max_funil fora do intervalo 1-6 (fora do que o dicionário de
    dados define) só é corrigido automaticamente quando há duas evidências
    convergentes, replicando a lógica do item 9 do registro de tratamento
    (caso original: PR-000081, valor 7, status_final == 'Contratada'):

        1. o valor é exatamente ETAPA_MAX + 1 (sugere um "off-by-one" na
           extração, não um valor arbitrário);
        2. status_final == 'Contratada' confirma, por um campo
           independente, que a proposta de fato chegou ao fim do funil.

    Qualquer outro valor fora do range (0, negativo, muito maior que 6, ou
    exatamente ETAPA_MAX + 1 sem confirmação de Contratada) é sinalizado
    para revisão humana e MANTIDO como está - mesma filosofia do item 6
    (idade_cliente = 14): não chutar um valor plausível sem uma segunda
    evidência que sustente a escolha.
    """
    fora_do_range = ~df["etapa_max_funil"].between(ETAPA_MIN, ETAPA_MAX)

    corrigivel = (
        fora_do_range
        & (df["etapa_max_funil"] == ETAPA_MAX + 1)
        & (df["status_final"] == "Contratada")
    )
    anomalia_nao_corrigida = fora_do_range & ~corrigivel

    log["linhas_etapa_corrigida"] = int(corrigivel.sum())
    log["ids_etapa_corrigida"] = df.loc[corrigivel, "id_proposta"].tolist()
    df.loc[corrigivel, "etapa_max_funil"] = ETAPA_MAX

    log["linhas_etapa_anomala_nao_corrigida"] = int(anomalia_nao_corrigida.sum())
    log["ids_etapa_anomala_nao_corrigida"] = df.loc[anomalia_nao_corrigida, "id_proposta"].tolist()
    if anomalia_nao_corrigida.any():
        log.setdefault("avisos", []).append(
            f"{int(anomalia_nao_corrigida.sum())} proposta(s) com etapa_max_funil fora do "
            f"intervalo {ETAPA_MIN}-{ETAPA_MAX} sem segunda evidência para correção automática "
            f"- mantidas como estão, ver ids_etapa_anomala_nao_corrigida no log."
        )

    return df


def carregar_e_tratar(caminho_csv, log=None):
    """
    Lê o CSV bruto e aplica todas as regras de tratamento documentadas em
    registro_tratamento_dados.md, com as checagens de robustez adicionais
    da Parte 2 (ver docstring do módulo). Retorna (df_tratado, log).

    `log` é um dicionário que esta função preenche com um resumo do que foi
    feito, incluindo os resultados de checar_taxa_conversao para cada
    coluna convertida - usado tanto para o log de execução quanto para a
    seção de qualidade de dados do relatório da Parte 2.
    """
    if log is None:
        log = {}
    log.setdefault("avisos", [])

    df = ler_csv_com_fallback_encoding(caminho_csv, log)
    log["linhas_brutas"] = len(df)

    if df.empty:
        raise ValueError(
            f"O arquivo {caminho_csv} não tem nenhuma linha de dados (só cabeçalho, "
            "ou está totalmente vazio). Nada para tratar - execução abortada, "
            "nenhum relatório foi gerado."
        )

    # Item 10 (revisado): NÃO removemos tipo_imovel == 'Terreno'. Ver
    # registro_tratamento_dados.md, item 10, para a investigação completa
    # que fundamenta manter Terreno na base. Coluna não-crítica: se ausente,
    # não trava a execução, só perde essa métrica específica.
    if "tipo_imovel" in df.columns:
        log["propostas_terreno_mantidas"] = int((df["tipo_imovel"] == "Terreno").sum())
    else:
        log["propostas_terreno_mantidas"] = "não disponível (coluna 'tipo_imovel' ausente)"
        log["avisos"].append("coluna 'tipo_imovel' ausente - quebra por tipo de imóvel indisponível nesta execução.")

    # Item 2: normalizar canal_origem
    df["canal_origem"] = normalizar_canal_origem(df["canal_origem"])
    canais_novos = detectar_canais_novos(df["canal_origem"])
    log["canais_nao_reconhecidos"] = canais_novos
    if canais_novos:
        log["avisos"].append(
            f"canal_origem tem {len(canais_novos)} valor(es) fora das 5 grafias oficiais "
            f"conhecidas: {canais_novos}. Pode ser sujeira de digitação ou um canal novo "
            f"de verdade - confira antes de repassar o relatório."
        )

    # Item 5: valor_imovel para numérico, com checagem de formato novo
    valor_imovel_bruto = df["valor_imovel"]
    df["valor_imovel"] = limpar_valor_imovel(valor_imovel_bruto)
    resultado_valor_imovel = checar_taxa_conversao("valor_imovel", valor_imovel_bruto, df["valor_imovel"])
    log["checagem_valor_imovel"] = resultado_valor_imovel.mensagem()
    if resultado_valor_imovel.status == "aviso":
        log["avisos"].append(resultado_valor_imovel.mensagem())

    # Item 1: calcular LTV (não existe pronto no CSV)
    df["ltv"] = df["valor_solicitado"] / df["valor_imovel"]
    log["propostas_ltv_acima_60pct"] = int((df["ltv"] > 0.60).sum())

    # Item 7: parse híbrido de datas (evita o bug do dayfirst cego), com
    # checagem de formato novo para cada coluna de data. Ambas são
    # não-críticas: se uma faltar, a execução segue sem ela em vez de
    # quebrar (é exatamente o KeyError cru que o teste com dado sintético
    # pegou antes de esta versão existir - ver decisoes_parte2.md).
    for coluna_data in ("data_entrada", "data_assinatura_contrato"):
        if coluna_data not in df.columns:
            log[f"checagem_{coluna_data}"] = f"coluna '{coluna_data}' ausente - checagem não aplicável"
            log["avisos"].append(f"coluna '{coluna_data}' ausente - datas dessa coluna não puderam ser processadas.")
            continue
        bruta = df[coluna_data]
        df[coluna_data] = parse_data_hibrida(bruta)
        resultado = checar_taxa_conversao(coluna_data, bruta, df[coluna_data])
        log[f"checagem_{coluna_data}"] = resultado.mensagem()
        if resultado.status == "aviso":
            log["avisos"].append(resultado.mensagem())

    # Item 6: idade_cliente inválida (< 18 ou > 100) vira nula - não
    # descartamos a linha, e não chutamos um valor plausível no lugar (ver
    # item 6 do registro). to_numeric(errors='coerce') primeiro evita que
    # um valor genuinamente não-numérico quebre o .astype('Int64') inteiro.
    # Coluna não-crítica: se ausente, a execução segue sem essa checagem.
    if "idade_cliente" in df.columns:
        idade_bruta = df["idade_cliente"]
        idade_numerica = pd.to_numeric(idade_bruta, errors="coerce")
        resultado_idade = checar_taxa_conversao("idade_cliente", idade_bruta, idade_numerica)
        log["checagem_idade_cliente"] = resultado_idade.mensagem()
        if resultado_idade.status == "aviso":
            log["avisos"].append(resultado_idade.mensagem())
        df["idade_cliente"] = idade_numerica.astype("Int64")
        idade_invalida = ~df["idade_cliente"].between(18, 100)
        log["linhas_idade_invalida"] = int(idade_invalida.sum())
        df.loc[idade_invalida, "idade_cliente"] = pd.NA
    else:
        log["checagem_idade_cliente"] = "coluna 'idade_cliente' ausente - checagem não aplicável"
        log["linhas_idade_invalida"] = "não disponível (coluna 'idade_cliente' ausente)"
        log["avisos"].append("coluna 'idade_cliente' ausente - métricas de idade indisponíveis nesta execução.")

    # Item 9 (generalizado): ver corrigir_etapa_max_funil
    df = corrigir_etapa_max_funil(df, log)

    # Item 8: marcar (sem descartar) a linha com assinatura antes da entrada.
    # Precisa das duas colunas de data - se qualquer uma faltar, não dá pra
    # calcular a inconsistência, então a coluna sai como NA em vez de quebrar.
    if "data_entrada" in df.columns and "data_assinatura_contrato" in df.columns:
        df["data_inconsistente"] = df["data_assinatura_contrato"] < df["data_entrada"]
        log["linhas_data_inconsistente"] = int(df["data_inconsistente"].sum())
    else:
        df["data_inconsistente"] = pd.NA
        log["linhas_data_inconsistente"] = "não disponível (coluna de data ausente)"

    # Item 4: taxa_juros_aa é, na prática, mensal. Mantemos a coluna
    # original (rastreabilidade) e criamos uma cópia com nome sem ambiguidade.
    if "taxa_juros_aa" in df.columns:
        df["taxa_juros_am"] = df["taxa_juros_aa"]
    else:
        log["avisos"].append("coluna 'taxa_juros_aa' ausente - taxa_juros_am não pôde ser derivada.")

    # Sanity check: algum valor de ltv não calculável (divisão por zero/NaN)?
    log["linhas_ltv_nao_calculavel"] = int(df["ltv"].isna().sum() + np.isinf(df["ltv"]).sum())

    log["linhas_tratadas"] = len(df)

    return df, log


if __name__ == "__main__":
    df_tratado, log = carregar_e_tratar("propostas_credito.csv")

    print("=" * 70)
    print("LOG DE EXECUÇÃO DO TRATAMENTO")
    print("=" * 70)
    for chave, valor in log.items():
        print(f"{chave}: {valor}")

    df_tratado.to_csv("propostas_credito_tratado.csv", index=False)
    print(f"\nArquivo tratado salvo em propostas_credito_tratado.csv")
    print(f"Linhas finais: {len(df_tratado)} (de {log['linhas_brutas']} originais)")
