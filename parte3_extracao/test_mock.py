#!/usr/bin/env python3
"""
Testa o pipeline inteiro (validação de formato + critério de acerto + CSV)
usando respostas SIMULADAS do Gemini, sem gastar nenhuma chamada de API real.

Cobre três cenários:
  1. Extração "perfeita" (idêntica ao gabarito) -> deve dar 100% no avaliar.py
  2. Extração que "chuta" nos 5 casos-chave (exatamente os erros que a Parte 3
     pede pra evitar) -> avaliar.py deve pegar TODOS eles
  3. Resposta da API mal-formada (JSON quebrado, campo faltando, status
     inválido) -> validar_formato() deve rejeitar, não aceitar calado

Rodar: python3 test_mock.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from campos_schema import CAMPOS_SIMPLES, CAMPOS_AREA
from extrator import validar_formato
from avaliar import avaliar, valores_batem
from json_para_csv import gerar_csv

GABARITO = json.loads(Path(__file__).parent.joinpath("gabarito.json").read_text(encoding="utf-8"))
LAUDOS = [k for k in GABARITO if k.startswith("laudo_")]


def gabarito_para_formato_extrator(laudo: str) -> dict:
    """Converte uma entrada do gabarito ('obs') pro formato do extrator
    ('observacao') - só o nome da chave muda."""
    saida = {}
    for campo, info in GABARITO[laudo].items():
        d = dict(info)
        d["observacao"] = d.pop("obs", "")
        saida[campo] = d
    return saida


def cenario_1_extracao_perfeita():
    print("--- Cenário 1: extração idêntica ao gabarito ---")
    tudo = {laudo: gabarito_para_formato_extrator(laudo) for laudo in LAUDOS}
    relatorio = avaliar(GABARITO, tudo)
    pg = relatorio["placar_geral"]
    assert pg["pct_acerto_completo"] == 100.0, f"esperado 100%, deu {pg['pct_acerto_completo']}%"
    for c in relatorio["casos_chave"]:
        assert c["passou"], f"caso-chave deveria passar com dado perfeito: {c}"
    print(f"    OK — placar {pg['pct_acerto_completo']}%, todos os {len(relatorio['casos_chave'])} casos-chave passaram.\n")


def cenario_2_extrator_que_chuta():
    print("--- Cenário 2: extrator que 'chuta' nos 5 casos-chave (deve ser pego) ---")
    tudo = {laudo: gabarito_para_formato_extrator(laudo) for laudo in LAUDOS}

    tudo["laudo_04"]["ano_construcao"] = {"valor": 2015, "status": "ok", "observacao": "chutado"}
    tudo["laudo_08"]["matricula"] = {"valor": "99.999", "status": "ok", "observacao": "chutado"}
    tudo["laudo_17"]["area_secundaria"] = {"valor_m2": 92, "rotulo_original": "área total", "status": "ok", "observacao": "escolhido arbitrariamente"}
    tudo["laudo_11"]["ano_construcao"] = {"valor": 2018, "status": "ok", "observacao": "chutado"}
    tudo["laudo_05"]["area_secundaria"] = {"valor_m2": 4.8, "rotulo_original": "área do terreno", "status": "ok", "observacao": "sem converter"}

    relatorio = avaliar(GABARITO, tudo)
    falhas = [c for c in relatorio["casos_chave"] if not c["passou"]]
    assert len(falhas) == 5, f"esperava pegar os 5 chutes injetados, pegou {len(falhas)}: {falhas}"
    print(f"    OK — avaliar.py pegou os {len(falhas)}/5 chutes injetados de propósito (nenhum passou batido).\n")


def cenario_3_resposta_malformada():
    print("--- Cenário 3: respostas de API mal-formadas (validar_formato deve rejeitar) ---")

    casos = {
        "json quebrado": "{not valid json",
        "campo faltando": json.dumps({c: {"valor": "x", "status": "ok", "observacao": ""} for c in CAMPOS_SIMPLES[:-1]}),  # falta 1 campo simples e as áreas
        "status inválido": json.dumps({
            **{c: {"valor": "x", "status": "ok", "observacao": ""} for c in CAMPOS_SIMPLES},
            **{c: {"valor_m2": 1, "rotulo_original": "x", "status": "talvez", "observacao": ""} for c in CAMPOS_AREA},
        }),
    }
    for nome, bruto in casos.items():
        try:
            validar_formato(bruto)
            raise AssertionError(f"'{nome}' deveria ter sido rejeitado por validar_formato, mas passou")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"    OK — '{nome}' rejeitado corretamente: {e}")
    print()


def cenario_4_csv_nao_quebra_com_nulos():
    print("--- Cenário 4: geração de CSV não quebra com status ausente/nao_aplicavel (valores null) ---")
    tudo = {laudo: gabarito_para_formato_extrator(laudo) for laudo in LAUDOS}
    saida = Path(__file__).parent / "resultados_mock_teste.csv"
    gerar_csv(tudo, saida)
    linhas = saida.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == 1 + len(LAUDOS), f"esperava {1 + len(LAUDOS)} linhas (header + 17), deu {len(linhas)}"
    saida.unlink()
    print(f"    OK — CSV gerado com {len(linhas)-1} linhas de dado, sem erro com campos nulos.\n")


def cenario_5_onus_negado_nao_falso_positivo():
    print("--- Cenário 5: 'sem ônus' reconhece paráfrases sem confundir negação com confirmação ---")

    # bug real do laudo_02: "sem gravames conhecidos" tem a palavra "gravame"
    # negada por "sem" - substring ingênuo confundia isso com ônus real
    casos_devem_bater = [
        "sem gravames conhecidos",
        "não foram identificados ônus na certidão analisada",
        "inexistência de ônus reais",
    ]
    for texto in casos_devem_bater:
        assert valores_batem("sem ônus", texto, "onus"), \
            f"deveria reconhecer {texto!r} como equivalente a 'sem ônus', mas não reconheceu"

    # continua rejeitando ônus real, e também incerteza (status "ausente",
    # diferente de confirmar ausência - ver laudo_08 no gabarito)
    casos_nao_devem_bater = [
        "hipoteca registrada em cartório",
        "há hipoteca registrada, sem penhora",
        "não foi possível identificar hipoteca ou penhora",
    ]
    for texto in casos_nao_devem_bater:
        assert not valores_batem("sem ônus", texto, "onus"), \
            f"não deveria reconhecer {texto!r} como 'sem ônus' (há ônus real mencionado)"

    print(f"    OK — {len(casos_devem_bater)} paráfrases de ausência reconhecidas, "
          f"{len(casos_nao_devem_bater)} menções reais de ônus continuam rejeitadas.\n")


def cenario_6_texto_livre_tolera_parafraseio_mas_nao_erro():
    print("--- Cenário 6: texto livre tolera parafraseio/reordenação, mas não mascara erro real ---")

    # 5 pares reais da 1a rodada completa (§9.2.1): o extrator ficou mais
    # fiel ao laudo do que a paráfrase que escrevi à mão no gabarito
    casos_devem_bater = [
        ("onus", "Rua do Comércio, 77, Edifício Horizonte, sala 503, Curitiba/PR",
                  "Rua do Comércio, 77, Edifício Horizonte, sala comercial 503, Curitiba/PR"),
        ("endereco", "Condomínio Parque Norte, SQN 214, bloco C, apto 407, Brasília/DF",
                      "Condomínio Parque Norte, Brasília/DF, SQN 214, bloco C, apto 407"),
        ("onus", "reserva legal registrada, sem hipoteca apontada",
                  "reserva legal registrada; não foi apontada hipoteca"),
        ("onus", "penhora cancelada (data do cancelamento não informada)",
                  "penhora cancelada, conforme averbação; documento não informa data do cancelamento"),
        ("onus", "sem ônus (declarado pelo proprietário, certidão não anexada)",
                  "Não há ônus, segundo declaração do proprietário; certidão não anexada."),
        ("matricula", "32.110", "Matrícula 32.110"),  # gabarito só com o número (§9.2.2)
    ]
    for campo, esperado, obtido in casos_devem_bater:
        assert valores_batem(esperado, obtido, campo), \
            f"deveria reconhecer como equivalente: {esperado!r} vs {obtido!r}"

    casos_nao_devem_bater = [
        ("endereco", "Rua do Comércio, 77, Curitiba/PR", "Rua do Comércio, 79, Curitiba/PR"),
        ("endereco", "Rua das Flores, 77, Curitiba/PR", "Rua dos Pinheiros, 77, Curitiba/PR"),
        ("matricula", "Matrícula 32.110", "Matrícula 32.119"),
        ("onus", "penhora cancelada (data do cancelamento não informada)", "hipoteca ativa em favor do banco XYZ"),
        ("matricula", "32.110", ""),  # esperado não-vazio vs obtido vazio - não pode bater
    ]
    for campo, esperado, obtido in casos_nao_devem_bater:
        assert not valores_batem(esperado, obtido, campo), \
            f"não deveria reconhecer como equivalente (há erro real): {esperado!r} vs {obtido!r}"

    print(f"    OK — {len(casos_devem_bater)} pares reais reconhecidos como equivalentes, "
          f"{len(casos_nao_devem_bater)} erros reais continuam rejeitados.\n")


if __name__ == "__main__":
    cenario_1_extracao_perfeita()
    cenario_2_extrator_que_chuta()
    cenario_3_resposta_malformada()
    cenario_4_csv_nao_quebra_com_nulos()
    cenario_5_onus_negado_nao_falso_positivo()
    cenario_6_texto_livre_tolera_parafraseio_mas_nao_erro()
    print("=== TODOS OS TESTES PASSARAM ===")
