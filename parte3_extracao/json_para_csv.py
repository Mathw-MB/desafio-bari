#!/usr/bin/env python3
"""
Gera um CSV consolidado (uma linha por laudo) a partir do JSON bruto do
extrator. É sempre DERIVADO do JSON — nunca editado à mão — pra não criar
duas fontes de verdade divergentes.

Cada campo vira duas colunas: <campo>_valor e <campo>_status.

Uso:
    python3 json_para_csv.py resultados/tudo.json resultados/consolidado.csv
"""
import csv
import json
import sys
from pathlib import Path

from campos_schema import CAMPOS_SIMPLES, CAMPOS_AREA


def valor_de(campo: str, dado: dict):
    # campos simples usam "valor", áreas usam "valor_m2" (ver campos_schema.py)
    if campo in CAMPOS_AREA:
        return dado.get("valor_m2")
    return dado.get("valor")


def gerar_csv(tudo: dict, caminho_saida: Path):
    todos_campos = CAMPOS_SIMPLES + CAMPOS_AREA
    colunas = ["laudo"]
    for c in todos_campos:
        colunas += [f"{c}_valor", f"{c}_status"]
        if c in CAMPOS_AREA:
            colunas.append(f"{c}_rotulo_original")

    with open(caminho_saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas)
        w.writeheader()
        for laudo, dado_laudo in sorted(tudo.items()):
            if "_erro_validacao" in dado_laudo:
                linha = {"laudo": laudo}
                linha.update({f"{c}_status": "ERRO_EXTRACAO" for c in todos_campos})
                w.writerow(linha)
                continue
            linha = {"laudo": laudo}
            for c in todos_campos:
                campo_dado = dado_laudo.get(c, {})
                linha[f"{c}_valor"] = valor_de(c, campo_dado)
                linha[f"{c}_status"] = campo_dado.get("status")
                if c in CAMPOS_AREA:
                    linha[f"{c}_rotulo_original"] = campo_dado.get("rotulo_original")
            w.writerow(linha)


def main():
    if len(sys.argv) < 3:
        print("Uso: python3 json_para_csv.py <entrada tudo.json> <saída .csv>")
        sys.exit(1)
    tudo = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    gerar_csv(tudo, Path(sys.argv[2]))
    print(f"CSV gerado em {sys.argv[2]}")


if __name__ == "__main__":
    main()
