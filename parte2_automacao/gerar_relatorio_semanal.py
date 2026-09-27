#!/usr/bin/env python3
"""
gerar_relatorio_semanal.py
Desafio Prático - Estágio AI & Data Lab | Bari - Parte 2 (Automação/RPA)

Orquestrador. É este o arquivo que alguém que não escreveu o código roda
toda segunda-feira. Amarra validação de esquema -> tratamento -> métricas
-> exportação, com log estruturado e códigos de saída pensados para um
agendador (cron / Agendador de Tarefas do Windows) conseguir reagir:

    0 -> sucesso, sem nenhum aviso de qualidade de dados
    1 -> sucesso, mas com aviso(s) de qualidade de dados (relatório saiu,
         vale uma olhada no log antes de repassar para a liderança)
    2 -> falha: nenhum relatório foi gerado (coluna crítica ausente,
         arquivo ilegível, ou formato de uma coluna mudou por completo)

Uso:
    python gerar_relatorio_semanal.py --entrada propostas_credito.csv
    python gerar_relatorio_semanal.py --entrada caminho/outro.csv --formato excel
    python gerar_relatorio_semanal.py --ajuda-completa   (ver README.md)
"""

import argparse
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd

from metricas import calcular_metricas
from relatorio_excel import gerar_excel
from relatorio_html import gerar_html
from tratamento import carregar_e_tratar
from validacao import (
    ColunaCriticaAusenteError,
    FormatoNovoCriticoError,
    listar_colunas_nao_criticas_ausentes,
    validar_colunas_criticas,
)

CODIGO_SUCESSO = 0
CODIGO_SUCESSO_COM_AVISOS = 1
CODIGO_FALHA = 2


def configurar_logging(pasta_logs: Path, timestamp: str) -> logging.Logger:
    pasta_logs.mkdir(parents=True, exist_ok=True)
    caminho_log = pasta_logs / f"execucao_{timestamp}.log"

    logger = logging.getLogger("relatorio_semanal")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formato = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    handler_arquivo = logging.FileHandler(caminho_log, encoding="utf-8")
    handler_arquivo.setFormatter(formato)
    logger.addHandler(handler_arquivo)

    handler_console = logging.StreamHandler(sys.stdout)
    handler_console.setFormatter(formato)
    logger.addHandler(handler_console)

    logger.info(f"Log desta execução salvo em: {caminho_log}")
    return logger


def ler_colunas_do_cabecalho(caminho_csv: Path):
    """Lê só o cabeçalho (nrows=0) para validar esquema antes de gastar
    tempo processando o arquivo inteiro. Tenta utf-8, depois latin-1."""
    for encoding in ("utf-8", "latin-1"):
        try:
            df_vazio = pd.read_csv(caminho_csv, nrows=0, encoding=encoding)
            if df_vazio.shape[1] == 1:
                df_vazio = pd.read_csv(caminho_csv, nrows=0, sep=";", encoding=encoding)
            return list(df_vazio.columns)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8/latin-1", b"", 0, 1, "encoding não reconhecido")


def rodar(caminho_entrada: str, pasta_saida: str, pasta_logs: str, formato: str) -> int:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = configurar_logging(Path(pasta_logs), timestamp)
    logger.info("=" * 70)
    logger.info("INÍCIO - Relatório Semanal do Funil de Crédito (Bari)")
    logger.info(f"Arquivo de entrada: {caminho_entrada}")
    logger.info(f"Formato(s) de saída solicitado(s): {formato}")
    logger.info("=" * 70)

    caminho_csv = Path(caminho_entrada)
    if not caminho_csv.exists():
        logger.error(f"FALHA: arquivo de entrada não encontrado: {caminho_csv}")
        logger.error("Nenhum relatório foi gerado. Confira o caminho e rode novamente.")
        return CODIGO_FALHA

    try:
        colunas = ler_colunas_do_cabecalho(caminho_csv)
    except UnicodeDecodeError:
        logger.error(f"FALHA: não foi possível ler {caminho_csv} nem como utf-8 nem como latin-1.")
        return CODIGO_FALHA

    try:
        validar_colunas_criticas(colunas)
    except ColunaCriticaAusenteError as erro:
        logger.error(f"FALHA: {erro}")
        return CODIGO_FALHA

    colunas_nao_criticas_ausentes = listar_colunas_nao_criticas_ausentes(colunas)
    for coluna, motivo in colunas_nao_criticas_ausentes.items():
        logger.warning(f"Coluna não-crítica ausente: '{coluna}' - afeta: {motivo}. Seguindo sem ela.")

    try:
        df_tratado, log_tratamento = carregar_e_tratar(str(caminho_csv))
    except FormatoNovoCriticoError as erro:
        logger.error(f"FALHA CRÍTICA DE FORMATO: {erro}")
        logger.error("Nenhum relatório foi gerado - o formato de uma coluna mudou "
                      "por completo e qualquer métrica calculada seria ruído. "
                      "É necessário revisar o parser antes de rodar de novo.")
        return CODIGO_FALHA
    except ValueError as erro:
        logger.error(f"FALHA: {erro}")
        return CODIGO_FALHA
    except Exception:
        logger.error("FALHA INESPERADA durante o tratamento dos dados:")
        logger.error(traceback.format_exc())
        return CODIGO_FALHA

    for chave, valor in log_tratamento.items():
        if chave != "avisos":
            logger.info(f"{chave}: {valor}")
    for aviso in log_tratamento.get("avisos", []):
        logger.warning(aviso)

    try:
        metricas = calcular_metricas(df_tratado, log_tratamento)
    except Exception:
        logger.error("FALHA INESPERADA ao calcular métricas:")
        logger.error(traceback.format_exc())
        return CODIGO_FALHA

    if colunas_nao_criticas_ausentes:
        metricas["qualidade_dados"]["colunas_nao_criticas_ausentes"] = colunas_nao_criticas_ausentes

    pasta_saida_path = Path(pasta_saida)
    pasta_saida_path.mkdir(parents=True, exist_ok=True)

    try:
        if formato in ("html", "ambos"):
            caminho_html = pasta_saida_path / f"relatorio_funil_{timestamp}.html"
            gerar_html(metricas, str(caminho_html), caminho_csv.name)
            logger.info(f"Relatório HTML gerado em: {caminho_html}")

        if formato in ("excel", "ambos"):
            caminho_excel = pasta_saida_path / f"relatorio_funil_{timestamp}.xlsx"
            gerar_excel(metricas, str(caminho_excel), caminho_csv.name)
            logger.info(f"Relatório Excel gerado em: {caminho_excel}")
    except Exception:
        logger.error("FALHA INESPERADA ao exportar o relatório:")
        logger.error(traceback.format_exc())
        return CODIGO_FALHA

    caminho_log_json = Path(pasta_logs) / f"execucao_{timestamp}.json"
    with open(caminho_log_json, "w", encoding="utf-8") as f:
        json.dump(
            {"timestamp": timestamp, "arquivo_entrada": str(caminho_csv),
             "log_tratamento": {k: v for k, v in log_tratamento.items()},
             "colunas_nao_criticas_ausentes": colunas_nao_criticas_ausentes},
            f, ensure_ascii=False, indent=2, default=str,
        )
    logger.info(f"Log estruturado (JSON) salvo em: {caminho_log_json}")

    total_avisos = len(log_tratamento.get("avisos", [])) + len(colunas_nao_criticas_ausentes)
    if total_avisos > 0:
        logger.warning(f"Execução concluída COM {total_avisos} aviso(s) - revise o log antes de repassar o relatório.")
        logger.info("=" * 70)
        return CODIGO_SUCESSO_COM_AVISOS

    logger.info("Execução concluída com sucesso, sem avisos.")
    logger.info("=" * 70)
    return CODIGO_SUCESSO


def main():
    parser = argparse.ArgumentParser(
        description="Gera o relatório semanal do funil de crédito do Bari a partir do CSV bruto de propostas."
    )
    parser.add_argument("--entrada", default="propostas_credito.csv", help="Caminho do CSV bruto de propostas.")
    parser.add_argument("--saida", default="saida", help="Pasta onde salvar o(s) relatório(s) gerado(s).")
    parser.add_argument("--logs", default="logs", help="Pasta onde salvar os logs de execução.")
    parser.add_argument("--formato", choices=["html", "excel", "ambos"], default="ambos",
                         help="Formato do relatório de saída (padrão: ambos).")
    args = parser.parse_args()

    codigo_saida = rodar(args.entrada, args.saida, args.logs, args.formato)
    sys.exit(codigo_saida)


if __name__ == "__main__":
    main()
