#!/usr/bin/env python3
"""
Critério de acerto da Parte 3.

Compara a saída do extrator (resultados/tudo.json) contra o gabarito
construído manualmente (gabarito.json) e produz:
  - um placar geral (% de campos corretos)
  - o resultado nominal dos "casos-chave" (as armadilhas conhecidas dos
    laudos 04, 05, 08, 11 e 17 — ver decisoes_parte3.md, seção 5)
  - a lista detalhada de todo campo que errou, pra inspeção manual

Uso:
    python3 avaliar.py resultados/tudo.json
    python3 avaliar.py resultados_mock/tudo.json   # pra rodar contra o mock
"""
import json
import re
import sys
from pathlib import Path

from campos_schema import CAMPOS_SIMPLES, CAMPOS_AREA

TOLERANCIA_NUMERICA = 0.5  # metros quadrados / reais - diferença de arredondamento aceitável

# "sem ônus" no gabarito casa com qualquer frase que tenha negação e não
# mencione um ônus real - evita exigir a frase exata quando cada laudo
# descreve a ausência de um jeito diferente (ver decisoes_parte3.md, §9.2).
NEGACOES_ONUS = ("não", "sem", "inexist")
ONUS_POSITIVOS = ("hipoteca", "penhora", "alienação", "servidão", "gravame", "restrição")
JANELA_NEGACAO_PALAVRAS = 4  # palavras antes do termo de ônus que contam como negação

# limiar de sobreposição de palavras pra textos livres (endereco, onus...).
# calibrado contra 5 pares reais que ficaram entre 0.75 e 1.0 (§9.2.1)
LIMIAR_SOBREPOSICAO_TEXTO = 0.7

SINONIMOS_TEXTO = {"sem": "não"}  # "sem ônus" = "não há ônus"


def _textos_livres_equivalentes(esperado: str, obtido: str, limiar: float = LIMIAR_SOBREPOSICAO_TEXTO) -> bool:
    """
    Compara dois textos livres (endereço, ônus...) tolerando reordenação e
    parafraseio - sem isso o critério pune o extrator por ser mais fiel ao
    laudo do que a paráfrase que escrevi à mão no gabarito (§9.2.1).

    Duas travas contra falso positivo:
    1. todo número do texto esperado precisa aparecer no obtido (e vice-versa)
       - sobreposição de palavras não pode mascarar um número diferente
    2. mesmo com os números batendo, ainda exige uma fração alta (padrão 70%)
       das palavras do texto mais curto presentes no mais longo
    """
    e = str(esperado).strip().lower()
    o = str(obtido).strip().lower()
    if e == o:
        return True

    numeros_e = set(re.findall(r"\d+", e))
    numeros_o = set(re.findall(r"\d+", o))
    if numeros_e != numeros_o:
        return False

    palavras_e = {SINONIMOS_TEXTO.get(t, t) for t in re.findall(r"\w+", e, re.UNICODE) if not t.isdigit()}
    palavras_o = {SINONIMOS_TEXTO.get(t, t) for t in re.findall(r"\w+", o, re.UNICODE) if not t.isdigit()}
    if not palavras_e or not palavras_o:
        # um lado é só dígito (ex.: "32.110" vs "Matrícula 32.110") - números
        # já bateram acima, então só rejeita se um dos dois era vazio (§9.2.2)
        return bool(e) and bool(o)

    menor, maior = (palavras_e, palavras_o) if len(palavras_e) <= len(palavras_o) else (palavras_o, palavras_e)
    sobreposicao = len(menor & maior) / len(menor)
    return sobreposicao >= limiar


def _tem_onus_real(texto: str) -> bool:
    """
    Verifica se um termo de ônus real aparece sem negação logo antes. Uma
    checagem só por substring falha em "sem gravames conhecidos" (a palavra
    "gravame" bate mesmo negada) - por isso olhamos as palavras anteriores.
    """
    palavras = texto.replace(",", " ").replace(";", " ").split()
    for i, palavra in enumerate(palavras):
        if any(termo in palavra for termo in ONUS_POSITIVOS):
            janela = " ".join(palavras[max(0, i - JANELA_NEGACAO_PALAVRAS):i])
            if not any(neg in janela for neg in NEGACOES_ONUS):
                return True
    return False

CASOS_CHAVE = [
    ("laudo_04", "ano_construcao", "nao_aplicavel", "terreno sem edificação"),
    ("laudo_04", "onus", "ausente", "'nada informado no documento'"),
    ("laudo_08", "matricula", "ausente", "'matrícula não apresentada'"),
    ("laudo_08", "onus", "ausente", "'não foi possível verificar'"),
    ("laudo_11", "ano_construcao", "nao_aplicavel", "'ano de construção: inexistente'"),
    ("laudo_17", "area_secundaria", "contraditorio", "95 no cabeçalho vs 92 na tabela"),
    ("laudo_05", "area_secundaria", "ok", "unidade em hectares, não m² — valor_m2 deveria vir convertido (~48000), não 4.8"),
]


def valores_batem(esperado, obtido, campo: str) -> bool:
    if esperado is None and obtido is None:
        return True
    if esperado is None or obtido is None:
        return False
    if isinstance(esperado, (int, float)) and isinstance(obtido, (int, float)):
        return abs(float(esperado) - float(obtido)) <= TOLERANCIA_NUMERICA

    if campo == "onus" and str(esperado).strip().lower() == "sem ônus":
        texto = str(obtido).strip().lower()
        tem_negacao = any(n in texto for n in NEGACOES_ONUS)
        return tem_negacao and not _tem_onus_real(texto)

    return _textos_livres_equivalentes(esperado, obtido)


def comparar_campo(campo: str, esperado: dict, obtido: dict) -> dict:
    status_ok = esperado.get("status") == obtido.get("status")

    # campos simples usam "valor", áreas usam "valor_m2" (ver campos_schema.py)
    chave_valor = "valor_m2" if campo in CAMPOS_AREA else "valor"

    valor_ok = True
    if esperado.get("status") == "ok":
        valor_ok = valores_batem(esperado.get(chave_valor), obtido.get(chave_valor), campo)

    return {
        "campo": campo,
        "status_esperado": esperado.get("status"),
        "status_obtido": obtido.get("status"),
        "status_correto": status_ok,
        "valor_esperado": esperado.get(chave_valor),
        "valor_obtido": obtido.get(chave_valor),
        "valor_correto": valor_ok,
        "acerto_total": status_ok and valor_ok,
    }


def avaliar(gabarito: dict, resultados: dict) -> dict:
    todos_campos = CAMPOS_SIMPLES + CAMPOS_AREA
    detalhes = []
    for laudo, campos_gabarito in gabarito.items():
        if not laudo.startswith("laudo_"):
            continue
        obtido_laudo = resultados.get(laudo)
        if obtido_laudo is None:
            detalhes.append({"laudo": laudo, "campo": "*", "erro": "laudo ausente na saída do extrator"})
            continue
        if "_erro_validacao" in obtido_laudo:
            detalhes.append({"laudo": laudo, "campo": "*", "erro": f"falha de validação de formato: {obtido_laudo['_erro_validacao']}"})
            continue
        for campo in todos_campos:
            esperado = campos_gabarito[campo]
            obtido = obtido_laudo.get(campo, {})
            comp = comparar_campo(campo, esperado, obtido)
            comp["laudo"] = laudo
            detalhes.append(comp)

    total = sum(1 for d in detalhes if "acerto_total" in d)
    corretos = sum(1 for d in detalhes if d.get("acerto_total"))
    status_corretos = sum(1 for d in detalhes if d.get("status_correto"))

    # casos-chave
    resultado_casos_chave = []
    for laudo, campo, status_esperado, descricao in CASOS_CHAVE:
        d = next((x for x in detalhes if x.get("laudo") == laudo and x.get("campo") == campo), None)
        if d is None:
            resultado_casos_chave.append({"laudo": laudo, "campo": campo, "descricao": descricao, "passou": False, "motivo": "não encontrado na saída"})
        else:
            resultado_casos_chave.append({
                "laudo": laudo, "campo": campo, "descricao": descricao,
                # acerto_total (não só status): laudo_05 tem status "ok" nos dois
                # cenários - o que muda é o valor (conversão de unidade)
                "passou": d["acerto_total"],
                "status_obtido": d["status_obtido"],
                "valor_obtido": d["valor_obtido"],
            })

    return {
        "placar_geral": {
            "total_campos": total,
            "acertos_completos": corretos,
            "pct_acerto_completo": round(100 * corretos / total, 1) if total else 0,
            "status_corretos": status_corretos,
            "pct_status_correto": round(100 * status_corretos / total, 1) if total else 0,
        },
        "casos_chave": resultado_casos_chave,
        "erros_detalhados": [d for d in detalhes if not d.get("acerto_total", True)],
    }


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 avaliar.py <caminho para tudo.json>")
        sys.exit(1)

    caminho_resultados = Path(sys.argv[1])
    gabarito = json.loads(Path(__file__).parent.joinpath("gabarito.json").read_text(encoding="utf-8"))
    resultados = json.loads(caminho_resultados.read_text(encoding="utf-8"))

    relatorio = avaliar(gabarito, resultados)

    print("=== PLACAR GERAL ===")
    pg = relatorio["placar_geral"]
    print(f"Status correto (ok/ausente/nao_aplicavel/contraditorio classificado certo): {pg['status_corretos']}/{pg['total_campos']} ({pg['pct_status_correto']}%)")
    print(f"Acerto completo (status E valor certos):                                   {pg['acertos_completos']}/{pg['total_campos']} ({pg['pct_acerto_completo']}%)")

    print("\n=== CASOS-CHAVE (armadilhas conhecidas) ===")
    for c in relatorio["casos_chave"]:
        marca = "PASSOU" if c["passou"] else "FALHOU"
        print(f"[{marca}] {c['laudo']}.{c['campo']}: {c['descricao']}")
        if not c["passou"]:
            if "motivo" in c:
                print(f"         motivo: {c['motivo']} (esse laudo ainda não foi rodado)")
            else:
                print(f"         obtido: status={c.get('status_obtido', '?')!r} valor={c.get('valor_obtido', '?')!r}")

    saida_json = caminho_resultados.parent / "relatorio_avaliacao.json"
    saida_json.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRelatório completo salvo em {saida_json}")


if __name__ == "__main__":
    main()
