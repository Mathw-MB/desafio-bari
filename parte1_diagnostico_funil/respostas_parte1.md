# Respostas — Parte 1: Diagnóstico do Funil

> Documento vivo, escrito à medida que fechamos cada pergunta com
> evidência. Baseado em `propostas_credito_tratado.csv` (6.400 propostas,
> sem exclusão de `tipo_imovel == 'Terreno'` — a instrução para excluir
> estava em texto invisível no PDF original e não se sustentou quando
> testada empiricamente; ver `registro_tratamento_dados.md`, item 10,
> para o histórico completo da decisão).

## Pergunta 1 — Onde o funil perde mais valor?

**Resposta curta:** depende de qual lente se usa — as três leituras abaixo
são complementares, não concorrentes, e contam uma história mais completa
juntas do que qualquer uma isolada.

### Leitura 1 — Valor absoluto perdido por etapa

| Etapa | Propostas | Valor perdido | % do total perdido |
|---|---|---|---|
| 3 — Análise de crédito | 1.799 | R$ 703,0 mi | 35,1% |
| 4 — Avaliação do imóvel | 1.267 | R$ 497,0 mi | 24,8% |
| 2 — Lead | 984 | R$ 375,0 mi | 18,7% |
| 5 — Formalização | 836 | R$ 322,8 mi | 16,1% |
| 1 — Simulação | 273 | R$ 104,6 mi | 5,2% |

Total solicitado que não virou contrato: **R$ 2,00 bilhões**. Total que
virou contrato: R$ 456,8 milhões. Taxa de conversão em valor: 18,6%
(próxima da taxa por quantidade, 19,4% — o ticket médio é parecido em
todas as etapas, então perda de valor e perda de volume seguem juntas).

Por essa lente, a **Etapa 3 — Análise de crédito** é onde mais dinheiro
fica pelo caminho, simplesmente porque é a etapa com mais volume passando.

### Leitura 2 — Taxa de queda condicional (proporção, não volume)

De quem *chega* em cada etapa, que fração não avança:

| Etapa | Chegaram | Taxa de queda |
|---|---|---|
| 1 — Simulação | 6.400 | 4,3% |
| 2 — Lead | 6.127 | 16,1% |
| 3 — Análise de crédito | 5.143 | 35,0% |
| 4 — Avaliação do imóvel | 3.344 | 37,9% |
| 5 — Formalização | 2.077 | **40,3%** |

Por essa lente, a etapa mais "furada" não é a 3, é a **5 — Formalização**:
de quem chega até ali — já tendo sobrevivido à análise de crédito e à
avaliação do imóvel — quase 4 em cada 10 ainda assim não fecham contrato.
Isso é notável porque são propostas a um passo do fim, o que torna essa
perda proporcionalmente mais "barata" de resolver do que reverter uma
reprovação de crédito lá atrás.

### Leitura 3 — Nem toda perda é igual: processo vs. risco

Reclassificando os motivos de perda em duas categorias — **processo**
(desistência, sem retorno, documentação pendente — endereçável com
melhoria de processo/experiência) e **risco** (reprovação de crédito,
problema de garantia — em grande parte a política de risco funcionando
como deveria):

- **Processo (endereçável): R$ 1,39 bilhão (69,2%)**
- **Risco (política em ação): R$ 616,0 milhões (30,8%)**

Essa é a leitura mais importante para a liderança: dizer "perdemos
R$ 2,00 bilhões" é impreciso e alarmista. O número realmente endereçável —
dinheiro que a empresa poderia razoavelmente capturar com melhorias de
processo, sem afrouxar risco — é **R$ 1,39 bilhão**. O restante, em
grande parte, é o preço de não emprestar para quem não deveria.

### Detalhe do motivo dentro de cada etapa

- **Etapa 3:** motivo mais comum não é reprovação de crédito, é
  **desistência do cliente** (614 propostas, R$ 243,1 mi) — à frente de
  "Reprovada crédito" (608, R$ 231,3 mi). Reforça a leitura 3: mesmo na
  etapa de maior perda absoluta, a maior fatia é de processo, não de risco.
- **Etapa 4:** dominada por um único motivo, **Problema garantia** (668
  de 1.267, R$ 263,8 mi) — natural, é a etapa de avaliação do imóvel.
- **Etapa 5:** dominada por **Documentação pendente** (440, R$ 168,9 mi) e
  desistência (396, R$ 153,9 mi) — 100% motivo de processo, reforçando
  por que essa é a etapa mais "barata" de atacar (leitura 2).

### Checagem de robustez (média vs. mediana)

A média do ticket é sistematicamente maior que a mediana em **todas** as
etapas (entre ~12% e ~16% acima, ex.: Etapa 4: média R$ 392,3 mil vs.
mediana R$ 339,2 mil) — distribuição com leve assimetria à direita, comum
em dado financeiro. Como a assimetria é praticamente constante entre
etapas, não distorce a comparação entre elas; as conclusões acima seguem
válidas. Para comunicar "ticket típico" à liderança, a mediana (R$ 323-343
mil) é mais representativa que a média (R$ 368-392 mil).

### Validação da premissa usada nesta análise

Cruzando `etapa_max_funil` com `status_final`, cada etapa tem um conjunto
de desfechos coerente com o que ela representa (ex.: "Problema garantia"
só ocorre na Etapa 4; "Documentação pendente" só na Etapa 5), e a Etapa 6
tem exclusivamente `Contratada` (1.241 de 1.241) — confirmando que a
correção de `etapa_max_funil = 7 → 6` (registro de tratamento, item 9)
estava certa.

### Achado adicional, relevante para a Pergunta 2

981 propostas (15,3% da base tratada) têm LTV acima do limite de política
de 60%. A maior parte é barrada, mas **124 delas viraram contrato mesmo
assim** — 10,0% de TODOS os 1.241 contratos fechados. A taxa de conversão
entre LTV > 60% (12,6%) é menor que a geral (19,4%), sugerindo que a
política é aplicada na maioria dos casos — mas não em todos. Ponto de
atenção de governança de risco a reportar.


---

## Pergunta 2 — A percepção da liderança se confirma?

**Resposta curta:** a percepção da liderança combina duas afirmações com
graus de sustentação bem diferentes — uma se confirma com força, a outra
só parcialmente, e com uma ressalva metodológica importante.

### Ressalva metodológica primeiro: cuidado com os últimos 1-2 meses da base

O volume de propostas despenca no fim do período: novembro/2025 tem 70
propostas e dezembro/2025 tem 27, contra uma média de 300-400/mês no
resto da base. Isso é quase certamente um efeito de corte na coleta de
dados perto da borda da base, não uma queda real de demanda — confirmado
porque o `tempo_analise_dias` médio das propostas *Contratadas* não cai
nesses meses (novembro, aliás, tem a maior média do período inteiro: 41,9
dias), o que descarta a hipótese de "contratos lentos sendo cortados por
falta de tempo de fechar". O problema é outro: há simplesmente poucos
dados nesses dois meses. A taxa de conversão de dezembro (29,6%, 8 de 27
propostas) tem um intervalo de confiança aproximado de [12%, 47%] — não
dá para tirar conclusão nenhuma isolada desse mês.

### "A conversão caiu?" — parcialmente confirmado

Comparando a 1ª metade do período (20,4%) com a 2ª metade (18,4%): a
diferença **é estatisticamente significativa** (teste de duas proporções,
p = 0,04), mas é um efeito pequeno (~2 pontos percentuais).

Já o recorte específico que a frase da liderança sugere — "caiu **nos
últimos meses**" — **não tem respaldo estatístico** (últimos 3 meses:
15,6% vs. restante: 19,5%; p = 0,13, não significativo), provavelmente
por causa do volume baixo nesses meses discutido acima.

**Leitura:** existe uma leve tendência de queda ao longo dos ~2 anos de
base — real, mas modesta. A frase específica "caiu nos últimos meses",
porém, não é sustentada com confiança pelos dados que temos; os dados
recentes são escassos demais para afirmar isso com segurança.

### "O canal de correspondentes não está performando?" — confirmado, com força

Correspondente converte a 14,3%, contra 21,3% dos demais canais somados —
a maior diferença entre todos os 5 canais, e estatisticamente muito
robusta (p ≈ 0, z = -6,40). É, disparado, o pior canal da base (o segundo
pior, Organico, converte a 20,7%).

**Mas há uma correção importante na narrativa:** olhando a série mensal
lado a lado, correspondentes converteu pior que os demais canais em **21
dos 24 meses** observados — desde o primeiro mês da base. Isso não é um
problema recente ou uma piora — é uma característica estrutural do canal
ao longo de todo o período observado. Se a leitura da liderança é de que
isso é algo que "começou a piorar" recentemente, essa parte específica
não é sustentada pelos dados: o canal sempre performou pior.

### O mix de canal explica a queda? Checado — não, na maior parte

A participação de Correspondente no volume total de fato aumentou ao
longo do período: de 26,5% (1ª metade) para 28,9% (2ª metade) — uma
diferença estatisticamente significativa (p = 0,03), confirmada também
por uma correlação positiva forte (0,68) entre o mês e a participação.

Mas a decomposição formal (contrafactual: qual seria a taxa da 2ª metade
se o mix tivesse ficado igual ao da 1ª, usando as taxas reais de cada
canal) mostra que esse efeito é pequeno demais para explicar a queda
observada:

- **Efeito de mudança de mix: +0,15 p.p.** (≈7,5% da queda total)
- **Efeito de queda de taxa dentro de cada canal: +1,86 p.p.** (≈92,5% da queda)

E o mais revelador: a queda de taxa não é exclusiva de correspondentes.
Correspondente caiu de 14,6% para 14,0%, mas **"Outros canais" também
caiu**, de 22,5% para 20,2% — uma queda de magnitude parecida.

**Conclusão:** a queda de conversão não é explicada por correspondentes
"tomando espaço" de canais melhores — é um fenômeno mais amplo, afetando
o funil como um todo (correspondentes incluído, mas não isolado). Isso
reforça a leitura de que existe uma queda real e geral, e enfraquece
qualquer narrativa de que "o problema é só correspondentes ganhando
volume". A causa raiz dessa queda ampla (processo, sazonalidade, política
de crédito, concorrência) não dá para isolar só com os dados disponíveis.

### Quanto eu confio em cada parte desta resposta

- **Alto:** correspondentes performa pior que os demais canais. Efeito
  grande, altamente significativo, e consistente mês a mês ao longo de
  quase toda a série.
- **Alto:** a queda de conversão geral é real e não é explicada por
  mudança de mix de canal — confirmado pela decomposição, que reconcilia
  exatamente (0,15 + 1,86 = 2,01 p.p.).
- **Moderado:** o tamanho da queda geral é pequeno (~2 pontos
  percentuais) — estatisticamente real, mas não é um colapso.
- **Baixo:** qualquer afirmação isolada sobre os últimos 1-3 meses
  especificamente (volume pequeno demais, possível efeito de corte de
  coleta de dados).

## Pergunta 3 — Quais características mais se associam à contratação?

**Resposta curta:** depois de controlar todas as características ao
mesmo tempo (regressão logística), só **4 delas** têm associação
estatisticamente significativa com a contratação: **score de crédito**
(positivo), **LTV** (negativo), **ser cliente recorrente** (positivo) e
**estar no canal Correspondente** (negativo). Praticamente tudo o mais
que parecia importar numa leitura isolada (ticket, região, tipo de
imóvel, prazo, idade, renda) **não se sustenta** quando se controla pelas
outras variáveis.

### Leitura univariada (cada característica isolada)

- **Canal:** de 14,3% (Correspondente) a 22,3% (Parceria).
- **Tipo de imóvel:** variação pequena, de 18,2% (Casa) a 21,1%
  (Terreno — que, aliás, converte um pouco *melhor* que a média, não
  pior; ver nota sobre Terreno mais abaixo).
- **Região (uf):** variação real, de 17,6% (PR/RJ) a 23,4% (GO).
- **Score de crédito:** contratadas têm score médio 34,1 pontos maior
  (697,0 vs. 662,9).
- **LTV:** contratadas têm LTV médio ligeiramente menor (0,476 vs. 0,495).
- **Ticket (valor_solicitado):** contratadas têm ticket médio
  ligeiramente MENOR (R$ 368,1 mil vs. R$ 388,1 mil) — direção meio
  contraintuitiva à primeira vista.
- **Cliente recorrente:** 23,5% de conversão vs. 18,4% para
  não-recorrentes.
- Prazo, idade e renda: diferenças praticamente nulas.

### Leitura multivariada — o que realmente se sustenta

Regressão logística com todas as características ao mesmo tempo
(variáveis numéricas padronizadas por desvio-padrão, para comparar
efeitos numa escala comum), usando 6.399 propostas (1 descartada por
`idade_cliente` inválida). Deliberadamente **de fora do modelo**:
`etapa_max_funil` e `tempo_analise_dias` — são resultado do processo, não
característica da proposta no momento em que ela entra; incluir isso
seria vazamento de informação.

Só 4 variáveis restaram estatisticamente significativas (p<0,05) — as
mesmas 4 de antes, com coeficientes praticamente idênticos:

| Característica | Odds ratio | Direção | Leitura |
|---|---|---|---|
| Score de crédito | 1,57 | aumenta chance | cada +1 desvio-padrão de score multiplica a chance de contratar por 1,57x |
| LTV | 0,83 | reduz chance | cada +1 desvio-padrão de LTV multiplica a chance por 0,83x (~17% menor) |
| Cliente recorrente | 1,38 | aumenta chance | ser cliente recorrente multiplica a chance por 1,38x (38% maior) |
| Canal Correspondente | 0,71 | reduz chance | estar nesse canal (vs. Organico) multiplica a chance por 0,71x (29% menor) — mesmo controlando score, LTV, ticket e região |

**O que caiu fora depois de controlar, e por que isso importa:** ticket,
região, tipo de imóvel, prazo, idade e renda — nenhum teve associação
estatisticamente significativa depois de controlar as outras variáveis.
Isso inclui um achado sutil: na leitura univariada, ticket menor parecia
se associar a mais conversão — mas esse efeito desaparece no modelo
controlado (p=0,43), sugerindo que era um efeito indireto (confundido
por LTV ou canal), não um efeito próprio do tamanho do ticket. O mesmo
vale para região: as diferenças por estado (GO 23% vs. PR/RJ 17,6%)
provavelmente refletem composição de canal/score por região, não um
efeito geográfico real por si só.

**Nota sobre Terreno:** `tipo_imovel_Terreno` também não é
estatisticamente significativo no modelo controlado (p=0,25) — ou seja,
mesmo com Terreno incluído na base (ver `registro_tratamento_dados.md`,
item 10, para o histórico dessa decisão), ele não tem associação própria
com a contratação depois de controlar as outras variáveis. É a terceira
evidência independente (depois da comparação de taxas e da checagem
dedicada em `investigacao_terreno.py`) de que Terreno se comporta como o
resto da base, não como uma categoria à parte.

**Sobre o canal Correspondente especificamente:** este resultado
aprofunda o achado da Pergunta 2 — não é só que o canal converte pior em
bruto, é que ele converte pior mesmo depois de descontar score de
crédito, LTV e ticket. Ou seja, não é (só) que o canal traz clientes de
perfil pior em características observáveis — há algo específico do canal
em si (processo, qualificação do lead, abordagem do parceiro) reduzindo a
chance de contratar, independente do perfil do cliente.

**Caveat importante sobre o modelo:** o pseudo R² (McFadden) é de apenas
0,047 — baixo em termos absolutos. Isso significa que, mesmo com essas 4
variáveis significativas, a maior parte da variação em quem contrata ou
não **não é explicada** pelas características disponíveis nesta base. Há
bastante fator não capturado aqui (qualidade da negociação, momento do
cliente, fatores fora dos dados). Não é uma limitação da análise — é uma
limitação honesta do que os dados conseguem explicar.

### Quanto eu confio nesta resposta

- **Alto:** score de crédito, LTV, cliente recorrente e canal
  Correspondente têm associação real e independente com a contratação —
  coeficientes fortes, p-valores muito baixos, e metodologia validada
  previamente contra dado sintético com relação conhecida.
- **Moderado:** a magnitude relativa entre essas 4 variáveis (ex.: score
  "pesa mais" que LTV) — o pseudo R² baixo lembra que o modelo captura só
  uma fração do que determina a contratação.
- **Baixo:** qualquer afirmação causal forte (ex.: "reduzir LTV vai
  aumentar contratação em X%") — isso é associação, não causalidade; e o
  modelo explica uma fração pequena da variação total.

## Pergunta 4 — Recomendações priorizadas

Antes das 3 recomendações, uma calibração honesta: mesmo somando os
cenários otimistas das Recomendações 1 e 2, o total capturável
(~R$ 128,8 milhões) é só ~9,3% dos R$ 1,39 bilhão de perda "de processo"
identificados na Pergunta 1. Estas são as três apostas de maior confiança
e maior tratabilidade — não uma alegação de ter resolvido o problema
inteiro. Existe bem mais oportunidade além destas três.

### Recomendação 1 (prioridade alta) — Reduzir o abandono na Etapa 5 (Formalização)

**O que sustenta:** a Etapa 5 é, proporcionalmente, a mais "furada" de
todo o funil (40,3% de taxa de queda condicional — a maior entre todas as
etapas, Pergunta 1, leitura 2), e **100% motivo de processo**
(Documentação pendente + Desistiu) — diferente de outras etapas dominadas
por risco de crédito. São propostas que já sobreviveram análise de
crédito e avaliação do imóvel, a um passo do fim.

**Ação proposta:** checklist de documentação antecipado (apresentado já
na entrada da proposta, não só na formalização), lembretes automatizados
de pendência, e um ponto de contato dedicado para dúvidas de
documentação durante essa etapa.

**Impacto estimado:** assumindo uma redução de 10 pontos percentuais na
taxa de queda condicional (de 40,3% para 30,3% — meta intermediária entre
o cenário conservador de 5 p.p. e o otimista de 15 p.p.): **~208
propostas adicionais contratadas, ~R$ 80,2 milhões em crédito adicional
no período de ~2 anos observado (~R$ 40,1 milhões/ano)**. Faixa de
cenários: de R$ 40,1 mi (5 p.p.) a R$ 120,3 mi (15 p.p.) no período.

**Premissas:** (1) o ticket médio das propostas recuperadas seria
parecido com o ticket médio de quem hoje para nessa etapa (R$ 386,1 mil);
(2) uma redução de 10 p.p. é alcançável com melhoria de processo, sem
mudar o perfil de risco aceito — é uma suposição informada pela
composição do problema (motivo 100% processo), não uma medição.

**Confiança:** alta na causa raiz (achado quantificado, reproduzido e
majoritariamente de processo). Moderada no tamanho exato do ganho — por
isso a faixa de cenários em vez de um número único.

### Recomendação 2 (prioridade alta) — Investigar e corrigir o canal Correspondente

**O que sustenta:** Correspondente converte a 14,3% contra 21,3% dos
demais canais — a maior diferença entre todos os canais, confirmada de
três formas independentes (Pergunta 2: teste estatístico e consistência
mensal ao longo de quase todo o período; Pergunta 3: sobrevive a controle
por score, LTV e ticket, ou seja, não é só perfil de cliente pior). Além
disso, a participação desse canal no volume total está crescendo
(Pergunta 2) — a empresa está investindo mais num canal que performa
pior, o que aumenta a urgência.

**Ação proposta:** diagnóstico qualitativo com o time de correspondentes
(processo de qualificação de lead, tempo de resposta, suporte oferecido)
antes de qualquer correção — a causa raiz exata ainda não está clara só
com estes dados. A partir daí: reforço de treinamento/suporte, revisão de
critério de qualificação de lead, ou desacelerar o crescimento de
investimento no canal até a causa ser diagnosticada.

**Impacto estimado:** cenário conservador (fechar metade do gap, meta
17,8%): **~63 propostas adicionais, ~R$ 24,3 milhões** no período
(~R$ 12,1 mi/ano). Cenário otimista (paridade total, 21,3%): **~125
propostas, ~R$ 48,6 milhões** (~R$ 24,3 mi/ano).

**Premissas:** é possível melhorar a taxa do canal sem simplesmente
descontinuá-lo (ainda representa ~1.772 propostas, volume relevante que
não convém descartar sem entender a causa primeiro).

**Confiança:** alta na existência e magnitude do problema (evidência
estatística forte e reproduzida em duas perguntas diferentes). Baixa a
moderada em quanto exatamente dá para melhorar sem investigação
qualitativa adicional — por isso a faixa larga entre os cenários.

### Recomendação 3 (prioridade média) — Fechar a brecha de governança do LTV acima de 60%

**O que sustenta:** 124 dos 1.241 contratos fechados (10,0%) excedem o
limite de política de LTV de 60% (Pergunta 1) — LTV médio nesse grupo de
64,2% (excesso moderado, não descontrolado). Isso representa
**R$ 65,8 milhões em crédito concedido fora do limite declarado de
política**.

**Ação proposta:** auditar esses 124 casos para entender se são exceções
formalmente aprovadas (com alçada correta) ou lacuna de controle no fluxo
de aprovação. Se for lacuna, implementar validação/bloqueio automático no
sistema para LTV > 60% sem aprovação explícita de alçada superior.

**Impacto estimado:** este não é ganho de receita, é **redução de
exposição a risco** — R$ 65,8 milhões em crédito hoje fora do limite de
política. Não dá para traduzir isso em perda financeira esperada sem
dados de inadimplência histórica por faixa de LTV, que não estão nesta
base.

**Premissas:** o limite de 60% reflete de fato o apetite de risco da
empresa (não é um número arbitrário), e os 124 casos não têm
justificativa documentada de exceção — isso precisa ser confirmado com o
time de crédito/risco antes de qualquer ação.

**Confiança:** alta no achado em si (numérico, direto, fácil de
auditar). Baixa em quanto isso representa risco financeiro real sem mais
dados — por isso a prioridade média em vez de alta: o achado é sólido,
mas a urgência financeira real ainda precisa ser dimensionada por quem
tem acesso a dados de inadimplência.
