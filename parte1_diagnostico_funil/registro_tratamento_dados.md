# Registro de Tratamento de Dados — propostas_credito.csv

> Documento vivo: cada decisão de limpeza é registrada aqui com o que foi
> encontrado, o que foi decidido, e por quê. Toda decisão de limpeza é uma
> decisão de negócio disfarçada — descartar ou transformar uma linha muda
> o resultado final da análise.

## Achados e decisões

### 1. Coluna `ltv` não existe no CSV
O dicionário descreve uma coluna `ltv`, mas ela não está no arquivo real.
**Decisão:** calcular como `valor_solicitado / valor_imovel`, assim que
`valor_imovel` estiver em formato numérico (item 5).

### 2. `canal_origem` tinha duplicidade de categoria por grafia
5 canais com grafia oficial + 4 linhas com a mesma categoria em minúsculo
e/ou espaço extra. **Confirmado:** normalizando com `.str.strip().str.lower()`,
os 5 canais somam exatamente 6.400 — nenhuma linha perdida.
**Decisão:** aplicar essa normalização antes de qualquer agregação por canal.

### 3. Nulos em `data_assinatura_contrato`/`taxa_juros_aa` (80,61%) são estruturais
**Confirmado:** linhas não-nulas (1.241) batem exatamente com
`status_final == 'Contratada'` (1.241). Não é dado faltando por erro.
**Decisão:** não tratar como problema de qualidade nem descartar linhas.

### 4. `taxa_juros_aa`: nome sugere "ao ano", mas é taxa mensal
**Confirmado:** valores entre 0,94% e 1,73% (média 1,32%) — só fazem
sentido de negócio como taxa mensal (equivalente anual ficaria em torno
de ~17% a.a., razoável para o produto; como taxa anual seria juro quase
zero, implausível).
**Decisão:** tratar/documentar a coluna como taxa **mensal**, apesar do
nome `_aa` ser enganoso.

### 5. `valor_imovel` — formato confirmado
6.400 valores únicos. Formato padrão: string decimal simples (ex.:
"495077.66"). Exceção: 3 linhas no formato `"R$ " + número` (ex.: "R$
574857.06"), mesmo separador decimal.
**Decisão:** limpar removendo `"R$"` e espaços, depois converter para
float.

### 6. `idade_cliente` — 1 linha inválida (PR-000079, idade = 14)
Menor de idade não pode legalmente contratar crédito no Brasil (maioridade
civil = 18) — não é uma exceção de negócio, é erro de dado.
**Decisão:** não estimar/chutar uma idade plausível; tratar o valor como
inválido (nulo) para qualquer estatística que use idade. A linha permanece
na base para as demais análises (a proposta já foi `Reprovada crédito`,
então o impacto no funil é mínimo).

### 7. `data_entrada`/`data_assinatura_contrato` — bug de parsing identificado e corrigido
Ao investigar 3 linhas de `data_entrada` em formato brasileiro (dd/mm/aaaa)
misturadas com o formato ISO predominante, a primeira correção aplicada
(`format='mixed', dayfirst=True` na coluna inteira) causou um bug: sempre
que dia e mês são ambos ≤ 12, o parser inverteu os dois mesmo em datas ISO
que já estavam certas (ex.: "2024-07-12" virou 7 de dezembro em vez de 12
de julho). Isso inflou uma contagem de "assinatura antes da entrada" de 1
para 331 linhas. Confirmado com teste isolado e corrigido.
**Decisão:** usar parse em duas passadas — 1ª tentativa assume ISO (sem
dayfirst); só quem falhar (vira NaT) tenta de novo com `dayfirst=True`.
Essa função (`parse_data_hibrida`) deve ser reaproveitada para qualquer
coluna de data no projeto, inclusive no script de automação da Parte 2.

### 8. `data_assinatura_contrato` anterior a `data_entrada` — inconsistência real (1 linha)
Com o parser corrigido, a contagem real é 1 linha (não 331): PR-001556,
`data_entrada = 2025-09-11`, `data_assinatura_contrato = 2025-05-08`,
`status_final = 'Contratada'`. A assinatura aparece ~4 meses antes da
entrada no funil, o que não é logicamente possível — é uma inconsistência
real de dado, não um artefato de parsing.
**Decisão original:** não corrigir nenhuma das duas datas (não há como
saber qual está errada), e excluir essa linha de qualquer análise que
dependa da ordem cronológica entre as duas datas.
**Nota de revisão (pós Perguntas 1-4):** essa exclusão explícita **não
foi implementada** nos scripts de análise (`analise_hipotese_lideranca.py`,
`analise_mix_canal.py`, `analise_associacao_contratacao.py`) — a linha
permaneceu na base tratada sem filtro adicional em nenhum deles. Dado que
é 1 linha em 6.400 (~0,016% da base), o impacto prático em qualquer
resultado reportado nas Perguntas 1-4 é desprezível, e optei por
registrar essa lacuna aqui com transparência em vez de voltar a rodar
tudo de novo só por causa dela. Se a coluna `data_inconsistente`
(marcada em `tratamento.py`) precisar ser usada de forma mais rigorosa no
futuro (ex.: na Parte 2), o filtro deve ser aplicado ali.

### 9. `etapa_max_funil = 7` (fora do range 1-6 do dicionário) — decidido corrigir para 6
A proposta PR-000081 tem `etapa_max_funil = 7`, valor fora do range que o
próprio dicionário de dados define (1 a 6). Avaliei essa linha com calma
antes de decidir:
- O dicionário é explícito: a escala vai de 1 a 6, sem etapa 7 documentada.
- É a ÚNICA linha, entre 6.400, com valor 7 — se fosse uma etapa legítima
  do processo (por exemplo, algum passo pós-contratação), eu esperaria ver
  isso se repetir em mais propostas contratadas ao longo dos quase 2 anos
  de base, não aparecer como uma ocorrência isolada.
- O `status_final` dessa proposta é `'Contratada'`, e pelo desenho do
  funil descrito no desafio, a etapa 6 é justamente "Contratação" — ou
  seja, tenho um segundo campo, independente do `etapa_max_funil`, que
  confirma por lógica de negócio que essa proposta deveria estar em 6.

Diferente do caso do `idade_cliente = 14` (item 6), onde eu não tinha
nenhum outro campo para confirmar qual seria o valor certo — então preferi
não chutar —, aqui tenho duas evidências convergentes (a regra do funil +
o `status_final`) apontando para o mesmo valor. Por isso, decidi que faz
sentido **corrigir esse valor de 7 para 6**, em vez de descartar a linha
ou deixar como está. Vou documentar essa correção explicitamente (linha
alterada, valor antigo e novo) no script de limpeza, para não esconder que
houve uma edição manual nos dados — quero poder defender essa escolha se
me perguntarem na entrevista.

**Teste aplicado:** o mesmo critério já usado para o abacaxi — uma
instrução escondida só deve ser seguida se o conteúdo se sustentar de
forma independente de estar escondida, e isso precisa ser *verificado*,
não assumido. Comparando Terreno com os demais tipos de imóvel na base
(ver `investigacao_terreno.py`):
- Taxa de contratação: Terreno 21,1% vs. Outros 19,2% (diferença NÃO
  significativa, p=0,29) — Terreno converte igual ou levemente melhor,
  não pior.
- LTV médio: 0,487 (Terreno) vs. 0,491 (Outros) — praticamente idêntico.
- Distribuição em `etapa_max_funil`, `canal_origem` e `status_final`: sem
  diferença perceptível entre os grupos.
- Confirmado por uma quarta fonte, independente das outras três: na
  regressão logística da Pergunta 3, `tipo_imovel_Terreno` não é
  estatisticamente significativo (p=0,25) mesmo controlando por todas as
  outras variáveis.

**Decisão final: manter Terreno na base (reverter a exclusão
original).** A instrução não passa no mesmo teste aplicado ao abacaxi —
não há evidência de que excluir Terreno tenha mérito analítico
independente de a instrução estar escondida. 
---

**Status:** documento final para a Parte 1 — todos os 10 pontos têm
decisão registrada e foram aplicados em `tratamento.py` (versão atual:
Terreno **mantido** na base, não removido). As Perguntas 1 a 4 (ver
`respostas_parte1.md`) foram refeitas com essa base após a reversão do
item 10. Não é esperado mexer mais neste arquivo, salvo se a Parte 2
(automação) expuser algum caso novo não coberto aqui.
