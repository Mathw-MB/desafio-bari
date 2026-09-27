"""
relatorio_html.py
Desafio Prático - Estágio AI & Data Lab | Bari - Parte 2 (Automação/RPA)

Exportador HTML. Consome o dicionário produzido por
metricas.calcular_metricas() - não sabe nada sobre pandas bruto nem sobre
tratamento.py. Gera um único arquivo .html autocontido (CSS e imagens de
gráfico embutidas em base64), pensado para ser aberto em qualquer navegador
sem instalar nada e anexado direto num e-mail.

Paleta de cores: paleta padrão validada (categórica, sequencial e de status)
do guia interno de visualização de dados - cores já testadas para
segurança de daltonismo e contraste, não escolhidas no olho. Como este é um
relatório estático (impresso/anexado, não um dashboard ao vivo), o modo
escuro foi deliberadamente deixado de fora para poupar tempo dado o prazo -
decisão registrada em decisoes_parte2.md.
"""

import base64
import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Paleta (ver decisoes_parte2.md / guia de visualização de dados)
COR_SUPERFICIE = "#fcfcfb"
COR_PLANO_FUNDO = "#f9f9f7"
COR_TINTA_PRIMARIA = "#0b0b0b"
COR_TINTA_SECUNDARIA = "#52514e"
COR_TINTA_MUTED = "#898781"
COR_GRADE = "#e1e0d9"
COR_EIXO = "#c3c2b7"

CATEGORICA = {
    "Correspondente": "#2a78d6",
    "Organico": "#eb6834",
    "Mídia paga": "#1baf7a",
    "Indicação": "#eda100",
    "Parceria": "#e87ba4",
}
SEQUENCIAL_ORDINAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]  # steps 250,350,450,550,650

STATUS_BOM = "#0ca30c"
STATUS_AVISO = "#fab219"
STATUS_CRITICO = "#d03b3b"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial"],
        "axes.edgecolor": COR_EIXO,
        "axes.labelcolor": COR_TINTA_SECUNDARIA,
        "text.color": COR_TINTA_PRIMARIA,
        "xtick.color": COR_TINTA_MUTED,
        "ytick.color": COR_TINTA_MUTED,
        "axes.facecolor": COR_SUPERFICIE,
        "figure.facecolor": COR_SUPERFICIE,
        "grid.color": COR_GRADE,
    }
)


def _fmt_moeda(valor: float) -> str:
    """Formata em R$ com separador de milhar '.' e decimal ',' (padrão
    brasileiro) - Python formata número com vírgula de milhar e ponto
    decimal por padrão, o que ficaria estranho num relatório em português
    para uma empresa brasileira. HTML estático não tem formatação
    sensível a localidade como o Excel tem, então é feito manualmente aqui."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _fmt_pct(fracao: float, casas: int = 1) -> str:
    texto = f"{fracao * 100:.{casas}f}"
    return f"{texto.replace('.', ',')}%"


def _fig_para_base64(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("ascii")


def _grafico_conversao_por_canal(df_canal) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    cores = [CATEGORICA.get(c, COR_TINTA_MUTED) for c in df_canal["canal_origem"]]
    barras = ax.bar(df_canal["canal_origem"], df_canal["taxa_conversao"] * 100, color=cores, width=0.6)
    ax.set_ylabel("Taxa de conversão (%)")
    ax.set_title("Conversão por canal de origem", loc="left", fontsize=12, color=COR_TINTA_PRIMARIA)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linewidth=0.6)
    ax.set_axisbelow(True)
    for barra, valor in zip(barras, df_canal["taxa_conversao"]):
        ax.annotate(_fmt_pct(valor), (barra.get_x() + barra.get_width() / 2, barra.get_height()),
                    ha="center", va="bottom", fontsize=9, color=COR_TINTA_SECUNDARIA)
    fig.tight_layout()
    return _fig_para_base64(fig)


def _grafico_valor_perdido_por_etapa(df_funil) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    cores = SEQUENCIAL_ORDINAL[: len(df_funil)]
    barras = ax.bar(df_funil["nome_etapa"], df_funil["valor_solicitado_perdido"] / 1000, color=cores, width=0.6)
    ax.set_ylabel("Valor solicitado perdido (R$ mil)")
    ax.set_title("Valor potencial perdido por etapa do funil", loc="left", fontsize=12, color=COR_TINTA_PRIMARIA)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linewidth=0.6)
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    for barra, linha in zip(barras, df_funil.itertuples()):
        ax.annotate(f"{_fmt_pct(linha.taxa_queda_condicional, casas=0)} queda",
                    (barra.get_x() + barra.get_width() / 2, barra.get_height()),
                    ha="center", va="bottom", fontsize=8, color=COR_TINTA_SECUNDARIA)
    fig.tight_layout()
    return _fig_para_base64(fig)


def _grafico_conversao_mensal(serie, meses_destacados) -> str:
    fig, ax = plt.subplots(figsize=(8, 3.6))
    x = range(len(serie))
    ax.plot(x, serie["taxa_conversao"] * 100, color=CATEGORICA["Correspondente"],
            linewidth=2, marker="o", markersize=4)

    n_destacados = len(meses_destacados)
    if n_destacados:
        ax.axvspan(len(serie) - n_destacados - 0.5, len(serie) - 0.5, color=STATUS_AVISO, alpha=0.12)
        ax.annotate("período citado pela liderança", xy=(len(serie) - n_destacados / 2 - 0.5, ax.get_ylim()[1]),
                    ha="center", va="bottom", fontsize=8, color=COR_TINTA_SECUNDARIA, annotation_clip=False)

    ax.set_ylabel("Taxa de conversão (%)")
    ax.set_title("Conversão mensal (data de entrada da proposta)", loc="left", fontsize=12, color=COR_TINTA_PRIMARIA)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linewidth=0.6)
    ax.set_axisbelow(True)

    passo = max(1, len(serie) // 12)
    ax.set_xticks(list(x)[::passo])
    ax.set_xticklabels(serie["mes_rotulo"].tolist()[::passo], rotation=35, ha="right", fontsize=8)
    fig.tight_layout()
    return _fig_para_base64(fig)


def _grafico_perda_por_motivo(df_motivo) -> str:
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.5 * len(df_motivo) + 1)))
    cores = SEQUENCIAL_ORDINAL[: len(df_motivo)][::-1] if len(df_motivo) <= len(SEQUENCIAL_ORDINAL) else \
        [SEQUENCIAL_ORDINAL[-1]] * len(df_motivo)
    ordem = df_motivo.sort_values("valor_solicitado_perdido")
    barras = ax.barh(ordem["status_final"], ordem["valor_solicitado_perdido"] / 1000, color=cores)
    ax.set_xlabel("Valor solicitado perdido (R$ mil)")
    ax.set_title("Valor perdido por motivo de desfecho", loc="left", fontsize=12, color=COR_TINTA_PRIMARIA)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linewidth=0.6)
    ax.set_axisbelow(True)
    for barra, linha in zip(barras, ordem.itertuples()):
        ax.annotate(f"{linha.quantidade} propostas", (barra.get_width(), barra.get_y() + barra.get_height() / 2),
                    ha="left", va="center", fontsize=8, color=COR_TINTA_SECUNDARIA, xytext=(4, 0),
                    textcoords="offset points")
    fig.tight_layout()
    return _fig_para_base64(fig)


def _stat_tile(valor: str, rotulo: str, cor_destaque: str = COR_TINTA_PRIMARIA) -> str:
    return f"""
    <div class="stat-tile">
      <div class="stat-valor" style="color:{cor_destaque}">{valor}</div>
      <div class="stat-rotulo">{rotulo}</div>
    </div>"""


def _lista_avisos(avisos) -> str:
    if not avisos:
        return '<p class="ok-msg">Nenhum aviso de qualidade de dados nesta execução.</p>'
    itens = "".join(f"<li>{aviso}</li>" for aviso in avisos)
    return f'<div class="banner-aviso"><strong>Avisos de qualidade de dados nesta execução:</strong><ul>{itens}</ul></div>'


def gerar_html(metricas: dict, caminho_saida: str, nome_arquivo_origem: str) -> None:
    conv_geral = metricas["conversao_geral"]
    conv_canal = metricas["conversao_por_canal"]
    funil = metricas["funil_por_etapa"]
    ltv = metricas["ltv"]
    consistencia = metricas["consistencia_etapa_status"]
    conversao_mensal = metricas["conversao_mensal"]
    perda_por_motivo = metricas["perda_por_motivo"]
    qualidade = metricas["qualidade_dados"]

    grafico_canal_b64 = _grafico_conversao_por_canal(conv_canal)
    grafico_funil_b64 = _grafico_valor_perdido_por_etapa(funil)

    if conversao_mensal["disponivel"] and len(conversao_mensal["serie"]) >= 2:
        secao_mensal = f"""
  <h2>A conversão está caindo "nos últimos meses"? (percepção da liderança)</h2>
  <img src="data:image/png;base64,{_grafico_conversao_mensal(conversao_mensal['serie'], conversao_mensal['meses_recentes_destacados'])}" alt="Gráfico de conversão mensal">
  <p class="ok-msg">Faixa destacada: {", ".join(conversao_mensal['meses_recentes_destacados'])} - os meses mais recentes da base, o mesmo recorte que motivou a percepção da liderança. Compare visualmente com o restante da série antes de tirar conclusão sobre tendência.</p>"""
    else:
        secao_mensal = """
  <h2>A conversão está caindo "nos últimos meses"? (percepção da liderança)</h2>
  <p class="ok-msg">Indisponível nesta execução - coluna 'data_entrada' ausente ou sem nenhuma data válida.</p>"""

    if not perda_por_motivo.empty:
        linhas_motivo = "".join(
            f"<tr><td>{r.status_final}</td><td>{r.quantidade}</td><td>{_fmt_moeda(r.valor_solicitado_perdido)}</td></tr>"
            for r in perda_por_motivo.itertuples()
        )
        secao_motivo = f"""
  <h2>Por que o funil perde valor (motivo de desfecho)</h2>
  <img src="data:image/png;base64,{_grafico_perda_por_motivo(perda_por_motivo)}" alt="Gráfico de valor perdido por motivo">
  <table>
    <thead><tr><th>Motivo (status_final)</th><th>Propostas</th><th>Valor solicitado perdido</th></tr></thead>
    <tbody>{linhas_motivo}</tbody>
  </table>"""
    else:
        secao_motivo = ""

    cor_ltv = STATUS_CRITICO if ltv["pct_acima_do_limite"] > 0 else STATUS_BOM
    cor_consistencia = STATUS_BOM if consistencia["consistente"] else STATUS_CRITICO

    linhas_canal = "".join(
        f"<tr><td>{r.canal_origem}</td><td>{r.total_propostas}</td>"
        f"<td>{r.total_contratadas}</td><td>{_fmt_pct(r.taxa_conversao)}</td></tr>"
        for r in conv_canal.itertuples()
    )
    linhas_funil = "".join(
        f"<tr><td>{r.etapa}. {r.nome_etapa}</td><td>{r.propostas_que_alcancaram}</td>"
        f"<td>{r.propostas_perdidas_na_etapa}</td><td>{_fmt_pct(r.taxa_queda_condicional)}</td>"
        f"<td>{_fmt_moeda(r.valor_solicitado_perdido)}</td></tr>"
        for r in funil.itertuples()
    )

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório Semanal do Funil - Bari</title>
<style>
  body {{ background:{COR_PLANO_FUNDO}; color:{COR_TINTA_PRIMARIA};
         font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         margin:0; padding:24px; }}
  .container {{ max-width: 960px; margin: 0 auto; background:{COR_SUPERFICIE};
                border-radius:8px; padding:32px; border:1px solid {COR_GRADE}; }}
  h1 {{ font-size:22px; margin-bottom:4px; }}
  h2 {{ font-size:16px; margin-top:36px; border-bottom:1px solid {COR_GRADE}; padding-bottom:6px; }}
  .subtitulo {{ color:{COR_TINTA_SECUNDARIA}; font-size:13px; margin-top:0; }}
  .stats-row {{ display:flex; gap:16px; flex-wrap:wrap; margin-top:16px; }}
  .stat-tile {{ flex:1; min-width:160px; background:{COR_PLANO_FUNDO}; border:1px solid {COR_GRADE};
                border-radius:8px; padding:16px; }}
  .stat-valor {{ font-size:28px; font-weight:600; }}
  .stat-rotulo {{ font-size:12px; color:{COR_TINTA_SECUNDARIA}; margin-top:4px; }}
  table {{ width:100%; border-collapse:collapse; margin-top:12px; font-size:13px; }}
  th, td {{ text-align:left; padding:8px 10px; border-bottom:1px solid {COR_GRADE}; }}
  th {{ color:{COR_TINTA_SECUNDARIA}; font-weight:600; font-size:12px; text-transform:uppercase; }}
  img {{ max-width:100%; margin-top:8px; }}
  .banner-aviso {{ background:#fff8e6; border:1px solid {STATUS_AVISO}; border-radius:8px;
                    padding:12px 16px; margin-top:16px; font-size:13px; }}
  .banner-aviso ul {{ margin:8px 0 0 18px; }}
  .ok-msg {{ color:{COR_TINTA_SECUNDARIA}; font-size:13px; }}
  footer {{ margin-top:32px; font-size:11px; color:{COR_TINTA_MUTED}; }}
</style>
</head>
<body>
<div class="container">
  <h1>Relatório Semanal do Funil de Crédito - Bari</h1>
  <p class="subtitulo">Gerado automaticamente em {agora} a partir de {nome_arquivo_origem}</p>

  {_lista_avisos(qualidade["avisos"])}

  <h2>Visão geral</h2>
  <div class="stats-row">
    {_stat_tile(_fmt_pct(conv_geral["taxa_conversao"]), f'Conversão geral ({conv_geral["total_contratadas"]} de {conv_geral["total_propostas"]} propostas)')}
    {_stat_tile(_fmt_pct(ltv["pct_acima_do_limite"]), f'Propostas com LTV acima de {int(ltv["limite"]*100)}% ({ltv["propostas_acima_do_limite"]} de {ltv["total_propostas_com_ltv_valido"]})', cor_ltv)}
    {_stat_tile("Consistente" if consistencia["consistente"] else "Inconsistente", "etapa_max_funil = 6 vs status_final = Contratada", cor_consistencia)}
  </div>

  {secao_mensal}

  <h2>Conversão por canal</h2>
  <img src="data:image/png;base64,{grafico_canal_b64}" alt="Gráfico de conversão por canal">
  <table>
    <thead><tr><th>Canal</th><th>Propostas</th><th>Contratadas</th><th>Taxa de conversão</th></tr></thead>
    <tbody>{linhas_canal}</tbody>
  </table>

  <h2>Onde o funil perde valor (por etapa)</h2>
  <img src="data:image/png;base64,{grafico_funil_b64}" alt="Gráfico de valor perdido por etapa do funil">
  <table>
    <thead><tr><th>Etapa</th><th>Alcançaram</th><th>Perdidas aqui</th><th>Taxa de queda</th><th>Valor solicitado perdido</th></tr></thead>
    <tbody>{linhas_funil}</tbody>
  </table>

  {secao_motivo}

  <h2>Qualidade dos dados desta execução</h2>
  <table>
    <tbody>
      <tr><td>Encoding do arquivo lido</td><td>{qualidade["encoding_usado"]}</td></tr>
      <tr><td>Linhas brutas / tratadas</td><td>{qualidade["linhas_brutas"]} / {qualidade["linhas_tratadas"]}</td></tr>
      <tr><td>Idades inválidas (nulificadas)</td><td>{qualidade["linhas_idade_invalida"]}</td></tr>
      <tr><td>Datas inconsistentes (assinatura antes da entrada)</td><td>{qualidade["linhas_data_inconsistente"]}</td></tr>
      <tr><td>etapa_max_funil corrigida automaticamente</td><td>{qualidade["linhas_etapa_corrigida"]}</td></tr>
      <tr><td>etapa_max_funil anômala, não corrigida (revisão humana)</td><td>{qualidade["linhas_etapa_anomala_nao_corrigida"]}</td></tr>
      <tr><td>Propostas com tipo_imovel = Terreno mantidas na base</td><td>{qualidade["propostas_terreno_mantidas"]}</td></tr>
      <tr><td>Canais fora das 5 grafias oficiais conhecidas</td><td>{", ".join(qualidade["canais_nao_reconhecidos"]) or "nenhum"}</td></tr>
    </tbody>
  </table>

  <footer>
    Relatório gerado automaticamente por gerar_relatorio_semanal.py (Parte 2 - Automação/RPA).
    Metodologia de tratamento e limpeza documentada em registro_tratamento_dados.md (Parte 1).
  </footer>
</div>
</body>
</html>"""

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html)
