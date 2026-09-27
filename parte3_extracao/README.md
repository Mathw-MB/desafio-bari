# Parte 3 — Extração com IA

Solução que extrai 9 campos estruturados de 17 laudos de avaliação de
imóvel em texto livre, cada um num formato diferente, usando a API do
Gemini com saída restrita a um schema JSON. Ver `decisoes_parte3.md` para
o porquê de cada decisão técnica.

**Antes de rodar qualquer coisa: os resultados já estão prontos.**
`resultados/` já vem com a extração completa dos 17 laudos, o placar de
acerto e o CSV consolidado — rodar de novo é opcional, só necessário se
você quiser conferir a extração com sua própria chamada de API. Pra só
avaliar o trabalho, vá direto em `decisoes_parte3.md` e
`resultados/consolidado.csv` — nenhum comando abaixo é pré-requisito.

## O que tem em cada arquivo

| Arquivo | O que faz |
|---|---|
| `laudos_avaliacao/*.txt` | Os 17 laudos originais fornecidos no desafio — entrada, nunca modificada. |
| `campos_schema.py` | Definição única dos campos, dos 4 estados possíveis e do schema JSON pedido à API — importado por todos os outros scripts, pra "o que se pede" e "o que se avalia" nunca divergirem. |
| `gabarito.json` | As respostas certas dos 17 laudos, escritas manualmente antes de qualquer extração — usado só para medir acerto, nunca para gerar o resultado. |
| `extrator.py` | Chama a API do Gemini (`gemini-3.5-flash-lite` por padrão, trocável) e salva um JSON por laudo em `resultados/`. |
| `avaliar.py` | Compara `resultados/tudo.json` contra `gabarito.json` campo a campo e gera o placar de acerto + relatório detalhado. |
| `json_para_csv.py` | Gera `resultados/consolidado.csv` a partir do JSON — sempre derivado, nunca editado à mão. |
| `test_mock.py` | Testa todo o pipeline com dados simulados (formato, critério de acerto, CSV), sem gastar nenhuma chamada de API real. |
| `decisoes_parte3.md` | Por que cada decisão técnica foi tomada, incluindo os bugs reais encontrados ao longo do caminho — leitura recomendada antes do código. |
| `resultados/` | Saída já processada: um JSON por laudo, `tudo.json` (consolidado), `relatorio_avaliacao.json` (placar) e `consolidado.csv`. Já commitada — ver nota acima. |

## Antes de começar

Você precisa do **Python 3.9 ou mais recente**. Pra conferir, abra um
terminal e rode `python --version` (ou `python3 --version`); se aparecer
um número de versão, está instalado.

**Este projeto está separado em pastas por parte do desafio** — algo como
`parte1_diagnostico_funil/`, `parte2_automacao/`, `parte3_extracao/`.
Todo comando deste guia precisa ser rodado com o terminal **dentro da
pasta `parte3_extracao`**. Rodar de dentro da pasta errada não avisa "pasta
errada" de forma óbvia — o Python roda normalmente e só reclama depois,
dizendo que não encontra `extrator.py` ou `campos_schema.py`.

## Como rodar — passo a passo

### 1. Abra um terminal dentro da pasta `parte3_extracao`

No Windows: abra o Explorador de Arquivos, navegue até a pasta
`parte3_extracao` (a que tem o arquivo `extrator.py` dentro), clique com o
botão direito em um espaço vazio dentro dela e escolha **"Abrir no
Terminal"** (Windows 11) ou **Shift + botão direito → "Abrir janela do
PowerShell aqui"** (Windows 10).

Alternativa, em qualquer sistema: abra o terminal de onde estiver e use
`cd` com o caminho completo:

```bash
cd "C:\Users\SeuUsuario\Área de Trabalho\desafio-bari\parte3_extracao"
```

**Como confirmar que deu certo:** rode `dir` (Windows) ou `ls`
(Mac/Linux) e confira se `extrator.py` aparece na lista. Se não aparecer,
repita o passo 1.

### 2. Crie o ambiente virtual (só na primeira vez)

```bash
python -m venv venv
```

### 3. Ative o ambiente virtual (toda vez que for rodar)

```bash
venv\Scripts\activate
```
(Mac/Linux: `source venv/bin/activate`)

Se funcionou, o início da linha do terminal passa a mostrar `(venv)`. Se
não aparecer, o comando não teve efeito — o motivo mais comum é estar na
pasta errada.

### 4. Instale as dependências (só na primeira vez)

```bash
pip install -r requirements.txt
```

### 5. Rode os testes com dado simulado (sem precisar de key nem internet)

```bash
python3 test_mock.py
```

**Como confirmar que deu certo:** a última linha impressa deve ser
`=== TODOS OS TESTES PASSARAM ===`. Esse passo não chama a API real — só
confere que a lógica de validação, do critério de acerto e do CSV está
funcionando antes de gastar qualquer chamada de verdade.

### 6. (Só se for rodar a extração de novo) Gere sua própria API key gratuita

O nível gratuito da API do Gemini não exige cartão de crédito — qualquer
pessoa com conta Google gera a própria em minutos:

1. Acesse **https://aistudio.google.com/apikey** e faça login com uma
   conta Google.
2. Gere uma nova chave de API (o site chama isso de "criar chave" ou
   "get API key" — a tela muda de vez em quando, mas a opção é sempre
   visível na página inicial).
3. Copie o valor gerado (uma string longa) — trate como uma senha, não
   compartilhe.

Crie um arquivo chamado `.env` dentro de `parte3_extracao` (copie
`.env.example` e renomeie) com a linha:

```
GEMINI_API_KEY=sua-key-aqui
```

Esse arquivo nunca é commitado (está no `.gitignore`) e o script lê dele
automaticamente — não precisa configurar variável de ambiente toda sessão.

Se esquecer este passo, o script avisa exatamente o que fazer (não trava
silenciosamente): rodar sem a key dá o erro `ERRO: não encontrei a API
key`, com o link acima e o nome do arquivo a criar.

### 7. Rode a extração de verdade

```bash
python3 extrator.py                  # todos os 17 laudos
python3 extrator.py --so laudo_01    # só um, pra teste rápido
python3 extrator.py --retomar        # reprocessa só o que faltou/falhou numa execução anterior
```

Cada laudo processado é impresso em tempo real (`ok` ou `ERRO`); ao final,
se algum falhar mesmo após as tentativas automáticas, o script avisa quais
e termina com código de saída `1` (sucesso total é código `0`).

**Se aparecer erro de cota (429) e demorar muito:** ver seção dedicada
abaixo — é um problema conhecido do tier gratuito, não um bug do código.

### 8. Avalie o resultado contra o gabarito

```bash
python3 avaliar.py resultados/tudo.json
```

Imprime o placar geral e o resultado de cada "caso-chave" (as armadilhas
específicas que os laudos testam — ver `decisoes_parte3.md`, seção 5), e
salva o relatório completo em `resultados/relatorio_avaliacao.json`.

### 9. Gere o CSV consolidado

```bash
python3 json_para_csv.py resultados/tudo.json resultados/consolidado.csv
```

## Se aparecer erro de cota da API (429 / "RESOURCE_EXHAUSTED")

**Sintoma:** algum laudo demora ~1-2 minutos e depois falha, ou a mensagem
de erro menciona `quotaId` e a palavra `PerDay`.

**O que significa:** o tier gratuito do Gemini tem um limite de chamadas
por **dia** (não por minuto) — bem menor que o número de laudos deste
projeto se você rodar tudo repetidas vezes no mesmo dia (testando,
reprocessando, etc.). Esperar alguns segundos não resolve, porque não é
um limite de velocidade, é uma cota que só reseta no dia seguinte.

**O que fazer:**
- Esperar até o dia seguinte e rodar `python3 extrator.py --retomar` — só
  reprocessa o que faltou, não recomeça do zero.
- Ou trocar de modelo sem editar código, caso o padrão esteja com cota
  mais apertada num dado momento:
  ```bash
  export GEMINI_MODEL="gemini-3.1-flash-lite"
  ```
- Isso não impede avaliar o trabalho: `resultados/` já tem a extração
  completa e bem-sucedida commitada.