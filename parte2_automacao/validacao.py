"""
validacao.py
Desafio Prático - Estágio AI & Data Lab | Bari - Parte 2 (Automação/RPA)

Camada de validação de entrada. Roda ANTES do tratamento pesado (tratamento.py)
e depois de cada conversão de tipo, com dois papéis distintos:

1. validar_colunas_criticas / listar_colunas_nao_criticas_ausentes:
   confere se o arquivo bruto tem o esquema mínimo esperado, com mensagem de
   erro legível para quem não escreveu o código (não um KeyError cru do
   pandas no meio do processamento).

2. checar_taxa_conversao:
   depois de converter uma coluna (valor_imovel para número, datas, etc.),
   compara a taxa de valores que existiam no bruto mas viraram nulo após a
   conversão contra uma taxa basal conhecida (documentada em
   registro_tratamento_dados.md da Parte 1). Isso existe porque um parser
   como `pd.to_numeric(errors='coerce')` converte silenciosamente qualquer
   formato não reconhecido em NaN - sem isso, um formato novo (ex.: "US$" em
   vez de "R$", ou separador de milhar brasileiro) produziria um relatório
   com números errados sem nenhum aviso.
"""

from dataclasses import dataclass, field


COLUNAS_CRITICAS = [
    "id_proposta",
    "canal_origem",
    "etapa_max_funil",
    "status_final",
    "valor_solicitado",
    "valor_imovel",
]

COLUNAS_NAO_CRITICAS = {
    "idade_cliente": "métricas de idade do proponente",
    "score_credito": "associação entre score e contratação",
    "prazo_meses": "análise de prazo pretendido",
    "taxa_juros_aa": "taxa de juros média por segmento",
    "consultor_id": "quebra por consultor",
    "cidade": "quebra por região (cidade)",
    "uf": "quebra por região (UF)",
    "renda_mensal_declarada": "análise de renda declarada",
    "flag_cliente_recorrente": "efeito de cliente recorrente",
    "tempo_analise_dias": "tempo médio de análise",
    "data_assinatura_contrato": "consistência de datas e taxa mensal de contratação",
    "data_entrada": "série temporal de entrada de propostas",
    "tipo_imovel": "quebra por tipo de imóvel",
}

# Taxas basais conhecidas de falha de conversão (proporção de valores que
# existiam no bruto e viraram nulo após a conversão), medidas contra
# propostas_credito.csv na Parte 1. Ver registro_tratamento_dados.md.
# Colunas não listadas aqui usam BASAL_PADRAO.
BASAIS_CONHECIDAS = {
    "valor_imovel": 0.0,       # nenhuma linha falhou em converter na Parte 1
    "data_entrada": 0.0,
    "data_assinatura_contrato": 0.0,
    "idade_cliente": 0.0,
}
BASAL_PADRAO = 0.0

# Acima da basal + este valor (em pontos percentuais), gera aviso.
LIMIAR_AVISO_PP = 0.001   # 0,1 p.p. acima da basal já é motivo de aviso
# Acima deste valor absoluto de falha, o formato mudou por completo -
# continuar seria reportar números sem sentido. Aborta a execução.
LIMIAR_CRITICO = 0.20


class ColunaCriticaAusenteError(Exception):
    """Uma ou mais colunas indispensáveis para as métricas centrais não
    foram encontradas no arquivo de entrada."""


class FormatoNovoCriticoError(Exception):
    """A taxa de valores não-convertíveis numa coluna ultrapassou o limiar
    crítico: o formato da coluna provavelmente mudou por completo e
    qualquer métrica calculada em cima dela seria ruído."""


@dataclass
class ResultadoChecagemFormato:
    coluna: str
    taxa_falha: float
    taxa_basal: float
    status: str  # "ok" | "aviso" | "critico"
    n_falhas_novas: int
    exemplos_brutos: list = field(default_factory=list)

    def mensagem(self) -> str:
        pct = self.taxa_falha * 100
        base = f"{self.coluna}: {self.n_falhas_novas} valor(es) não-convertível(eis) ({pct:.3f}% das linhas)"
        if self.status == "ok":
            return f"{base} - dentro da taxa basal conhecida ({self.taxa_basal * 100:.3f}%)."
        exemplos = ", ".join(repr(e) for e in self.exemplos_brutos[:5])
        if self.status == "aviso":
            return (f"{base} - ACIMA da taxa basal conhecida ({self.taxa_basal * 100:.3f}%). "
                    f"Possível formato novo não coberto pelo parser. Exemplos brutos: {exemplos}")
        return (f"{base} - CRÍTICO (limiar de {LIMIAR_CRITICO * 100:.0f}%). "
                f"O formato da coluna provavelmente mudou por completo. Exemplos brutos: {exemplos}")


def validar_colunas_criticas(colunas_presentes):
    """
    Levanta ColunaCriticaAusenteError se qualquer coluna crítica não estiver
    presente. Deve ser chamada logo após ler o cabeçalho do CSV, antes de
    gastar tempo processando o arquivo inteiro.
    """
    faltando = [c for c in COLUNAS_CRITICAS if c not in colunas_presentes]
    if faltando:
        raise ColunaCriticaAusenteError(
            "Colunas obrigatórias ausentes no arquivo de entrada: "
            f"{faltando}. Colunas encontradas: {list(colunas_presentes)}. "
            "Sem essas colunas não é possível calcular as métricas centrais "
            "do funil - execução abortada, nenhum relatório foi gerado."
        )


def listar_colunas_nao_criticas_ausentes(colunas_presentes):
    """
    Retorna um dicionário {coluna: métrica_afetada} para colunas
    não-críticas ausentes. Não levanta exceção - quem chama decide como
    sinalizar isso no relatório e no log.
    """
    return {
        c: motivo
        for c, motivo in COLUNAS_NAO_CRITICAS.items()
        if c not in colunas_presentes
    }


def checar_taxa_conversao(nome_coluna, serie_bruta, serie_convertida) -> ResultadoChecagemFormato:
    """
    Compara, para uma coluna que passou por conversão de tipo (numérica ou
    data), a taxa de valores que existiam no bruto e viraram nulo depois da
    conversão contra a taxa basal conhecida daquela coluna.

    Levanta FormatoNovoCriticoError se a taxa de falha ultrapassar
    LIMIAR_CRITICO. Caso contrário, retorna um ResultadoChecagemFormato com
    status "ok" ou "aviso" para quem chama decidir o que fazer (logar,
    marcar no relatório).
    """
    if len(serie_bruta) != len(serie_convertida):
        raise ValueError("séries de tamanhos diferentes - checagem inválida")

    mask_falha_nova = serie_convertida.isna() & serie_bruta.notna()
    n_falhas = int(mask_falha_nova.sum())
    total = len(serie_bruta)
    taxa_falha = n_falhas / total if total else 0.0
    taxa_basal = BASAIS_CONHECIDAS.get(nome_coluna, BASAL_PADRAO)

    exemplos = serie_bruta[mask_falha_nova].astype(str).head(5).tolist()

    if taxa_falha >= LIMIAR_CRITICO:
        status = "critico"
    elif taxa_falha > taxa_basal + LIMIAR_AVISO_PP:
        status = "aviso"
    else:
        status = "ok"

    resultado = ResultadoChecagemFormato(
        coluna=nome_coluna,
        taxa_falha=taxa_falha,
        taxa_basal=taxa_basal,
        status=status,
        n_falhas_novas=n_falhas,
        exemplos_brutos=exemplos,
    )

    if status == "critico":
        raise FormatoNovoCriticoError(resultado.mensagem())

    return resultado
