#!/usr/bin/env python3
"""
Extrator de campos estruturados dos laudos de avaliação de imóvel (Parte 3).

Uso:
    python3 extrator.py                 # roda os 17 laudos
    python3 extrator.py --so laudo_17   # roda só um, pra teste rápido
    python3 extrator.py --retomar       # reprocessa só o que faltou/falhou

Saída: um JSON por laudo em resultados/, mais resultados/tudo.json consolidado.

Se der AttributeError tipo "'Client' object has no attribute 'models'", a API
do google-genai mudou de novo - copie o erro e ajuste chamar_api() abaixo.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from campos_schema import RESPONSE_SCHEMA, PROMPT_INSTRUCOES, STATUS_VALIDOS, CAMPOS_SIMPLES, CAMPOS_AREA

LAUDOS_DIR = Path(__file__).parent / "laudos_avaliacao"
SAIDA_DIR = Path(__file__).parent / "resultados"

# trocável via GEMINI_MODEL sem editar código (ver decisoes_parte3.md, seção 8)
MODELO = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
VERSAO_ARQUIVO = "2026-09-26-h"  # impresso ao rodar, confirma a versão


def montar_client():
    try:
        from dotenv import load_dotenv
        load_dotenv()  # lê .env da pasta, se existir
    except ImportError:
        pass  # dotenv não instalado, segue com variável de ambiente normal

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERRO: não encontrei a API key.")
        print("Gere uma gratuitamente em https://aistudio.google.com/apikey (precisa só de conta Google).")
        print("Depois, crie um arquivo .env nesta pasta (copie .env.example) com a linha:")
        print("  GEMINI_API_KEY=sua-key-aqui")
        sys.exit(1)
    try:
        from google import genai
    except ImportError:
        print("ERRO: pacote 'google-genai' não instalado. Rode: pip install google-genai")
        sys.exit(1)
    return genai.Client(api_key=api_key)


MAX_TENTATIVAS = 5
ESPERA_INICIAL_S = 8      # 503: dobra a cada tentativa (8s, 16s, 32s...)
ESPERA_RATE_LIMIT_S = 35  # 429 por minuto: espera fixa
PAUSA_ENTRE_LAUDOS_S = 4  # entre laudos, pra não estourar limite por minuto


def chamar_api(client, texto_laudo: str) -> str:
    """Chama a API e retorna o texto bruto da resposta (deveria ser JSON)."""
    from google.genai import errors as genai_errors
    from google.genai import types

    prompt = PROMPT_INSTRUCOES.format(texto_laudo=texto_laudo)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMA,
    )

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            response = client.models.generate_content(model=MODELO, contents=prompt, config=config)
            return response.text
        except AttributeError as e:
            print("ERRO DE COMPATIBILIDADE DE SDK — não é erro de key nem de laudo.")
            print(f"Detalhe: {e}")
            print("Copie esta mensagem inteira e volte com ela para ajustarmos a chamada.")
            raise
        except genai_errors.ServerError as e:
            # 503/500: sobrecarga temporária do servidor, não é erro nosso - retry com backoff
            if tentativa == MAX_TENTATIVAS:
                print(f"    Desisti após {MAX_TENTATIVAS} tentativas — servidor continua indisponível: {e}")
                raise
            espera = ESPERA_INICIAL_S * (2 ** (tentativa - 1))
            print(f"    [tentativa {tentativa}/{MAX_TENTATIVAS}] Gemini sobrecarregado (503) — esperando {espera}s e tentando de novo...")
            time.sleep(espera)
        except genai_errors.ClientError as e:
            codigo = getattr(e, "code", None)
            if codigo == 429:
                # dois tipos de 429: limite por minuto (retry resolve) e cota
                # diária do tier gratuito (não resolve hoje). O quotaId no
                # corpo do erro distingue os dois - contém "PerDay" quando é
                # diário. Sem atributo dedicado no SDK, checamos str(e) mesmo.
                if "PerDay" in str(e):
                    print(f"    Cota DIÁRIA do tier gratuito esgotada para o modelo {MODELO}.")
                    print(f"    Só reseta no próximo dia - esperar agora não resolve.")
                    print(f"    Detalhe: {e}")
                    raise
                if tentativa == MAX_TENTATIVAS:
                    print(f"    Desisti após {MAX_TENTATIVAS} tentativas — cota/limite de taxa ainda excedido: {e}")
                    raise
                print(f"    [tentativa {tentativa}/{MAX_TENTATIVAS}] limite de taxa (429) — esperando {ESPERA_RATE_LIMIT_S}s...")
                time.sleep(ESPERA_RATE_LIMIT_S)
            else:
                # 400/401/403 etc - erro de configuração, retry não ajuda
                print(f"ERRO DO CLIENTE (provavelmente key ou configuração): {e}")
                raise

    raise RuntimeError("não deveria chegar aqui")


def validar_formato(bruto: str) -> dict:
    """
    Segunda camada de garantia de formato: confere que todos os campos
    existem com status válido. Formato fora do esperado é erro explícito,
    não passa batido.
    """
    dado = json.loads(bruto)  # estoura JSONDecodeError se vier lixo

    todos_campos = CAMPOS_SIMPLES + CAMPOS_AREA
    faltando = [c for c in todos_campos if c not in dado]
    if faltando:
        raise ValueError(f"Resposta da API não tem os campos: {faltando}")

    for campo in todos_campos:
        status = dado[campo].get("status")
        if status not in STATUS_VALIDOS:
            raise ValueError(f"Campo '{campo}' com status inválido: {status!r}")

    return dado


def processar_laudo(client, caminho_txt: Path) -> dict:
    texto = caminho_txt.read_text(encoding="utf-8")
    bruto = chamar_api(client, texto)
    try:
        return validar_formato(bruto)
    except (json.JSONDecodeError, ValueError) as e:
        # guarda o erro em vez de derrubar o script - "erro" é melhor que nada
        return {"_erro_validacao": str(e), "_resposta_bruta": bruto}


def main():
    print(f"(extrator.py versão {VERSAO_ARQUIVO}, modelo: {MODELO})")

    parser = argparse.ArgumentParser()
    parser.add_argument("--so", help="rodar só um laudo específico, ex.: laudo_17 (sem .txt)")
    parser.add_argument("--retomar", action="store_true",
                         help="reprocessa só os laudos que falharam (ou nunca rodaram) numa execução anterior, mantendo os que já deram certo")
    args = parser.parse_args()

    client = montar_client()
    SAIDA_DIR.mkdir(exist_ok=True)

    # sempre carrega tudo.json se existir, não só com --retomar - senão
    # "--so laudo_05" sozinho reescrevia o arquivo do zero e apagava os
    # outros 16 (bug real, ver decisoes_parte3.md §9)
    tudo = {}
    caminho_tudo = SAIDA_DIR / "tudo.json"
    if caminho_tudo.exists():
        tudo = json.loads(caminho_tudo.read_text(encoding="utf-8"))

    if args.so:
        arquivos = [LAUDOS_DIR / f"{args.so}.txt"]
    elif args.retomar:
        todos_arquivos = sorted(LAUDOS_DIR.glob("laudo_*.txt"))
        arquivos = [c for c in todos_arquivos
                    if c.stem not in tudo or "_erro_execucao" in tudo[c.stem] or "_erro_validacao" in tudo[c.stem]]
        ja_ok = len(todos_arquivos) - len(arquivos)
        print(f"Retomando: {ja_ok} laudo(s) já ok, {len(arquivos)} pra reprocessar: {[c.stem for c in arquivos]}")
        if not arquivos:
            print("Nada pra reprocessar - os 17 já estão ok em resultados/tudo.json.")
            return
    else:
        arquivos = sorted(LAUDOS_DIR.glob("laudo_*.txt"))

    falhas = []
    for caminho in arquivos:
        nome = caminho.stem
        print(f"Processando {nome}...", end=" ", flush=True)
        t0 = time.time()
        try:
            resultado = processar_laudo(client, caminho)
        except Exception as e:
            # falha final (retry esgotado ou erro inesperado) não derruba o
            # lote - registra este e segue pros próximos
            resultado = {"_erro_execucao": f"{type(e).__name__}: {e}"}
            falhas.append(nome)
        dt = time.time() - t0
        ok = not ("_erro_validacao" in resultado or "_erro_execucao" in resultado)
        print(f"{'ok' if ok else 'ERRO'} ({dt:.1f}s)")

        (SAIDA_DIR / f"{nome}.json").write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tudo[nome] = resultado

        # grava a cada laudo, não só no final - se interromper no meio, o
        # que já rodou não se perde
        (SAIDA_DIR / "tudo.json").write_text(
            json.dumps(tudo, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        if caminho != arquivos[-1]:
            time.sleep(PAUSA_ENTRE_LAUDOS_S)  # evita estourar limite por minuto

    print(f"\nConcluído. {len(arquivos)} laudo(s) processado(s). Saída em {SAIDA_DIR}/")
    if falhas:
        print(f"ATENÇÃO: {len(falhas)} laudo(s) falharam mesmo após retry: {falhas}")
        print("Rode de novo só esses, ex.: python3 extrator.py --so " + falhas[0])
        sys.exit(1)  # sinaliza falha parcial pra quem rodar (ou um script em volta)


if __name__ == "__main__":
    main()
