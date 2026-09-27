"""
Definição única dos campos que extraímos de cada laudo, e do schema JSON
correspondente. Este módulo é importado tanto pelo extrator (extrator.py)
quanto pelo avaliador (avaliar.py) e pelos testes (test_mock.py) — assim o
formato nunca diverge entre "o que pedimos" e "o que avaliamos".

Cada campo (exceto tipo_imovel e endereco, que são simples) tem a mesma
estrutura de 3 partes:
    valor      -> o dado em si (string, número, ou null)
    status     -> "ok" | "ausente" | "nao_aplicavel" | "contraditorio"
    observacao -> texto livre, só quando há algo relevante a registrar
                  (ex.: "estimado a partir de idade aparente", "cabeçalho
                  diverge da tabela interna")

Ver decisoes_parte3.md, seção 4, para a justificativa de cada estado.
"""

STATUS_VALIDOS = ["ok", "ausente", "nao_aplicavel", "contraditorio"]

CAMPOS_SIMPLES = [
    "tipo_imovel",
    "endereco",
    "ano_construcao",
    "valor_avaliacao",
    "matricula",
    "onus",
    "data_vistoria",
    "responsavel_tecnico",
]
CAMPOS_AREA = ["area_principal", "area_secundaria"]


def _schema_campo_simples(tipo_valor: str, descricao_valor: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "valor": {"type": tipo_valor, "nullable": True, "description": descricao_valor},
            "status": {"type": "string", "enum": STATUS_VALIDOS},
            "observacao": {"type": "string"},
        },
        "required": ["valor", "status", "observacao"],
    }


def _schema_campo_area(descricao_valor: str) -> dict:
    return {
        "type": "object",
        "properties": {
            "valor_m2": {"type": "number", "nullable": True,
                         "description": descricao_valor + " Valor em metros quadrados — se a unidade original não for m² (ex.: hectares), converta e registre a conversão em observacao."},
            "rotulo_original": {"type": "string", "nullable": True,
                                 "description": "o termo exato usado no laudo, ex.: 'área privativa', 'terreno', 'área útil'"},
            "status": {"type": "string", "enum": STATUS_VALIDOS},
            "observacao": {"type": "string"},
        },
        "required": ["valor_m2", "rotulo_original", "status", "observacao"],
    }


# schema JSON Schema pedido à API (response_schema, ver extrator.py)
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "tipo_imovel": _schema_campo_simples("string", "tipo do imóvel (ex.: apartamento, casa, terreno, sala comercial, galpão)"),
        "endereco": _schema_campo_simples("string", "endereço completo como aparece no laudo"),
        "area_principal": _schema_campo_area(
            "A área CONSTRUÍDA/EDIFICADA do imóvel — privativa, útil, coberta, "
            "ou 'benfeitorias construídas'. É a edificação em si. NUNCA o "
            "terreno/lote, mesmo que o terreno seja numericamente maior."
        ),
        "area_secundaria": _schema_campo_area(
            "A segunda grandeza de área relatada no laudo, que NÃO é a "
            "construção: área total, terreno, lote, ou área comum."
        ),
        "ano_construcao": _schema_campo_simples("integer", "ano de construção/edificação. Se só houver 'idade aparente', calcule a partir da data da vistoria e registre em observacao que é estimativa."),
        "valor_avaliacao": _schema_campo_simples("number", "valor de avaliação em reais, sem formatação (ex.: 642000.00)"),
        "matricula": _schema_campo_simples("string", "número de matrícula e cartório/registro, como aparece no laudo"),
        "onus": _schema_campo_simples("string", "descrição do ônus/gravame, ou confirmação de ausência"),
        "data_vistoria": _schema_campo_simples("string", "data da vistoria em formato ISO (AAAA-MM-DD)"),
        "responsavel_tecnico": _schema_campo_simples("string", "nome e registro profissional (CREA/CAU/CNAI) do responsável técnico"),
    },
    "required": CAMPOS_SIMPLES + CAMPOS_AREA,
}


PROMPT_INSTRUCOES = """\
Você vai extrair campos estruturados de um laudo de avaliação de imóvel em texto livre.

REGRAS OBRIGATÓRIAS, mais importantes que preencher todos os campos:

1. NUNCA invente ou estime um valor que não esteja no texto, exceto no único
   caso explicitamente permitido: calcular ano_construcao a partir de uma
   "idade aparente" mencionada + a data da vistoria (e mesmo aí, registre em
   observacao que é uma estimativa, não uma data exata).

2. Se um campo não existir no documento, use status "ausente", valor null,
   e explique em observacao o que o texto realmente diz (ex.: "documento diz
   'não foi possível verificar por ausência de certidão'").

   Cuidado especial com "onus": uma frase que apenas diz que a informação NÃO
   FOI FORNECIDA (ex.: "nada informado no documento", "não foi possível
   verificar") NÃO é o valor do campo - é o próprio documento avisando que
   o campo está vazio. Nesse caso o status é "ausente", valor null, e a
   frase do documento vai em observacao (nunca em valor). Isso é diferente
   de o documento CONFIRMAR que não há ônus (ex.: "não há ônus", "sem
   gravames conhecidos") - aí sim é uma resposta válida, status "ok" e o
   valor é essa confirmação. A pergunta a se fazer: o documento está
   respondendo "não há ônus" (ok) ou só dizendo "não sei"/"não constou"
   (ausente)?

3. Se um campo não se aplica a este tipo de imóvel (ex.: ano de construção de
   um terreno sem edificação), use status "nao_aplicavel", não "ausente".

4. Se o documento apresentar dois valores conflitantes para o mesmo campo
   (ex.: um valor no início do texto e outro depois, ou o texto disser
   explicitamente que há divergência), use status "contraditorio", valor
   null, e registre os dois valores em observacao. NUNCA escolha um dos dois
   nem calcule uma média.

5. Preste atenção à UNIDADE de cada área (m² é o padrão, mas pode aparecer em
   hectares ou outra unidade) — se não for m², converta e diga isso em
   observacao.

6. Se houver mais de uma data no texto com papéis diferentes (ex.: uma data
   de consulta a um registro e outra data de vistoria propriamente dita),
   use a que está explicitamente rotulada como data da vistoria/inspeção, e
   se houver ambiguidade real, registre em observacao.

7. area_principal é SEMPRE a área construída/edificada (privativa, útil,
   coberta, "benfeitorias construídas") — a edificação em si. area_secundaria
   é a outra grandeza relatada (área total, terreno, lote, área comum). Essa
   regra vale mesmo quando o terreno é numericamente muito maior que a
   construção (ex.: imóvel rural) — não decida por qual número é maior, e
   sim por qual das duas é a construção.

Laudo:
---
{texto_laudo}
---
"""
