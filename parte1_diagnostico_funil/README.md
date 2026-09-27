# Parte 1 — Diagnóstico do Funil

Análise da base de propostas de crédito do Bari: onde o funil perde mais
valor, se a percepção da liderança se confirma, quais características se
associam à contratação, e recomendações priorizadas com impacto estimado.

**Diferente da Parte 2, isto não é uma ferramenta com um único comando —
é uma sequência de 6 scripts, cada um lendo o que o anterior produziu.**
O código sozinho não é a resposta: ele existe para ser lido junto com
`respostas_parte1.md`, que interpreta cada número. Rodar os scripts sem
ler esse documento mostra os cálculos, mas não a análise.

## O que tem em cada arquivo

| Arquivo | O que faz |
|---|---|
| `tratamento.py` | Módulo de limpeza dos dados brutos. Lê `propostas_credito.csv`, aplica as 10 decisões documentadas em `registro_tratamento_dados.md`, e gera `propostas_credito_tratado.csv`. **Roda primeiro, sempre** — os outros 5 dependem do arquivo que ele produz. |
| `analise_funil_valor.py` | Pergunta 1 — onde o funil perde mais valor (por etapa, em absoluto e em taxa condicional). |
| `analise_hipotese_lideranca.py` | Pergunta 2 — testa estatisticamente se a conversão caiu e se o canal Correspondente está pior. |
| `analise_mix_canal.py` | Pergunta 2 (complemento) — decompõe a queda de conversão em efeito de mix de canal vs. efeito de taxa por canal. |
| `analise_associacao_contratacao.py` | Pergunta 3 — regressão logística: quais características realmente se associam à contratação. |
| `calcular_impacto_recomendacoes.py` | Pergunta 4 — números de suporte para as 3 recomendações priorizadas. |
| `registro_tratamento_dados.md` | Cada problema encontrado na base, a decisão tomada, e por quê — inclusive a história completa de uma decisão que foi revertida depois de uma investigação (ver seção "Terreno" no próprio arquivo). |
| `respostas_parte1.md` | As 4 perguntas respondidas com evidência, metodologia e nível de confiança declarado — é este arquivo que dá sentido aos números que os scripts imprimem. |
| `testar_reorganizacao.py` | Script de verificação: confirma que os arquivos certos estão na pasta e que os 6 scripts principais rodam sem erro. Não é parte da análise — é uma checagem rápida para rodar **antes** de tudo o mais (ver passo 6). |
| `investigacao/` | Scripts exploratórios usados para *chegar* nas decisões de tratamento — não fazem parte do pipeline final e não precisam ser rodados para reproduzir a análise. Documentam o processo: `diagnostico_dados.py` (diagnóstico inicial da base bruta), `investigacao_extra.py` e `investigacao_datas_v2.py` (investigação de formato de valores e de um bug de datas), `investigacao_terreno.py` (checagem empírica que motivou reverter uma decisão de tratamento). Cada um roda de forma independente contra `propostas_credito.csv`, em qualquer ordem. |

## Antes de começar

Você precisa ter o **Python 3.9 ou mais recente** instalado. Para
conferir, abra um terminal e rode `python --version` (ou `python3
--version`); se aparecer um número de versão, está instalado.

**Mesmo aviso que vale para as outras partes deste projeto:** esta pasta
(`parte1_diagnostico_funil`) é uma de várias dentro do repositório —
existem também `parte2_automacao/` e `parte3_extracao/`. Todo comando
deste guia precisa ser rodado com o terminal **dentro desta pasta**,
nunca em outra. Rodar da pasta errada não dá um erro óbvio de cara — o
Python abre normalmente e só reclama depois, dizendo que não encontra
`tratamento.py`, porque esse arquivo só existe aqui dentro.

## Como rodar — passo a passo

### 1. Abra um terminal dentro da pasta `parte1_diagnostico_funil`

No Windows: abra o Explorador de Arquivos, navegue até a pasta
`parte1_diagnostico_funil` (a que tem o arquivo `tratamento.py` dentro),
clique com o botão direito em um espaço vazio dentro dela e escolha
**"Abrir no Terminal"** (Windows 11) ou **Shift + botão direito → "Abrir
janela do PowerShell aqui"** (Windows 10).

Alternativa que funciona em qualquer sistema: abra o terminal de onde
estiver e use `cd` com o caminho completo, por exemplo:

```bash
cd "C:\Users\SeuUsuario\Área de Trabalho\desafio-bari\parte1_diagnostico_funil"
```

**Como confirmar que deu certo:** rode `dir` (Windows) ou `ls`
(Mac/Linux) e confira se `tratamento.py` aparece na lista. Se não
aparecer, repita o passo 1.

### 2. Crie o ambiente virtual (só na primeira vez)

```bash
python -m venv venv
```

### 3. Ative o ambiente virtual (toda vez que for rodar)

```bash
venv\Scripts\activate
```

(Mac/Linux: `source venv/bin/activate`)

O início da linha do terminal deve passar a mostrar `(venv)`. Se não
aparecer, o motivo mais comum é estar na pasta errada — a pasta `venv`
só existe dentro de `parte1_diagnostico_funil`, criada no passo 2.

### 4. Instale as dependências (só na primeira vez)

```bash
pip install -r requirements.txt
```

### 5. Confirme que o arquivo de dados está na pasta

O `propostas_credito.csv` já vem incluído neste repositório, dentro de
`parte1_diagnostico_funil`. Confirme com `dir`/`ls` que ele aparece —
se por algum motivo não estiver lá, é o único arquivo que precisa ser
copiado manualmente antes de continuar.

### 6. Rode a verificação automática primeiro

```bash
python testar_reorganizacao.py
```

Isso confirma, em segundos, que os arquivos estão no lugar certo e que
os 6 scripts principais rodam sem erro — antes de você (ou quem estiver
avaliando) investir tempo lendo a análise manualmente. Se algo aqui
falhar, o motivo quase certamente é o CSV não estar na pasta, ou o
terminal estar na pasta errada (ver seção de erro comum, abaixo).

### 7. Rode os scripts principais, nesta ordem

```bash
python tratamento.py
```

Confira se a saída bate com estes valores (são os que validamos durante
o desenvolvimento):

```
linhas_brutas: 6400
propostas_terreno_mantidas: 535
linhas_idade_invalida: 1
ids_etapa_corrigida: ['PR-000081']
linhas_data_inconsistente: 1
linhas_ltv_nao_calculavel: 0
linhas_tratadas: 6400
```

Se bateu, os outros 5 podem ser rodados em qualquer ordem entre si (todos
dependem só do `propostas_credito_tratado.csv` que o passo acima gerou,
não uns dos outros):

```bash
python analise_funil_valor.py
python analise_hipotese_lideranca.py
python analise_mix_canal.py
python analise_associacao_contratacao.py
python calcular_impacto_recomendacoes.py
```

Cada um imprime no terminal os números que sustentam uma das 4
perguntas. **Para entender o que esses números significam, leia-os ao
lado de `respostas_parte1.md`** — o script mostra o cálculo, o documento
mostra a interpretação, a premissa por trás, e o quanto se confia em cada
achado.

### 8. (Opcional) Veja o processo de investigação

Os scripts dentro de `investigacao/` não são necessários para reproduzir
a análise — documentam como chegamos nas decisões de tratamento. Rodam
de forma independente, cada um direto contra `propostas_credito.csv`:

```bash
cd investigacao
python diagnostico_dados.py
python investigacao_extra.py
python investigacao_datas_v2.py
python investigacao_terreno.py
```

## Deu erro "can't open file ... No such file or directory"?

Significa que o terminal está rodando o Python de dentro da pasta
errada — o Python abriu normalmente (não é erro de instalação), só não
encontrou o script porque ele não existe na pasta onde o terminal está
agora. Isso aconteceu com a gente mesmo durante o desenvolvimento, usando
o botão "Run" do VS Code em vez do terminal. Volte ao passo 1: confirme
com `dir`/`ls` que o arquivo aparece na lista antes de rodar qualquer
comando.

## Sobre a confiabilidade dos scripts

Cada script com lógica nova (o parser de data, a regressão logística, a
decomposição de mix) foi testado contra dados sintéticos fabricados, com
resultado conhecido de antemão, antes de ser considerado pronto para
rodar contra a base real — não é uma suíte de testes formal e reproduzível
(diferente da Parte 2, que tem uma por exigência do próprio enunciado),
mas cada decisão de tratamento tem seu raciocínio e evidência registrados
em `registro_tratamento_dados.md`.

## Tempo levado nesta parte

Ver `README.md` na raiz do repositório.
