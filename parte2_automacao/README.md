# Parte 2 — Automação / RPA

Rotina que lê o CSV bruto de propostas, aplica o tratamento de dados,
calcula as métricas-chave do funil e exporta um relatório (HTML e/ou
Excel) pronto para a liderança comercial. Pensada para ser rodada toda
segunda-feira por alguém que não escreveu este código, sem precisar
entender o que acontece por dentro — é exatamente por isso que o passo a
passo abaixo é longo e detalhado: o objetivo é que ele funcione mesmo
para quem nunca abriu um terminal antes.

## O que tem em cada arquivo

| Arquivo | O que faz |
|---|---|
| `tratamento.py` | Limpeza e tratamento dos dados brutos (cópia adaptada do módulo da Parte 1 — ver `decisoes_parte2.md` para o que mudou e por quê). |
| `validacao.py` | Valida se o CSV de entrada tem as colunas esperadas e detecta formato novo/inesperado dentro de uma coluna. |
| `metricas.py` | Calcula as métricas do funil a partir dos dados já tratados. Não sabe nada sobre formato de saída. |
| `relatorio_html.py` | Gera o relatório em HTML (autocontido, com gráficos embutidos). |
| `relatorio_excel.py` | Gera o relatório em Excel (`.xlsx`, com abas separadas). |
| `gerar_relatorio_semanal.py` | Orquestrador / ponto de entrada. É este arquivo que você roda. |
| `decisoes_parte2.md` | Decisões de design desta parte (formato, filosofia de falha, limiares, bugs encontrados nos testes). |
| `testes/gerar_csv_sinteticos.py` | Gera os CSVs sintéticos usados para testar os casos-limite. |
| `testes/dados_sinteticos/` | CSVs sintéticos: arquivo válido, coluna crítica ausente, coluna não-crítica ausente, formato novo (aviso e crítico), encoding alternativo, arquivo vazio. |
| `testes/saida_exemplo/`, `testes/logs_exemplo/` | Exemplo de saída de uma execução real contra `valido.csv`, para conferência sem precisar rodar nada. |

## Antes de começar

Você precisa ter o **Python 3.9 ou mais recente** instalado. Pra
conferir, abra um terminal e rode `python --version` (ou `python3
--version`); se aparecer um número de versão, está instalado.

**Um ponto que causa confusão com frequência, então vale deixar claro
antes de qualquer comando:** este projeto está separado em pastas por
parte do desafio — algo como `parte1_diagnostico_funil/`,
`parte2_automacao/`, `parte3_extracao/`. Todo comando deste guia precisa
ser rodado com o terminal **dentro da pasta `parte2_automacao`**, nunca
em outra. Rodar o mesmo comando de dentro da pasta errada (por exemplo
`parte3_extracao`) não dá erro de "pasta errada" de forma óbvia — o
Python roda normalmente e só reclama depois, dizendo que não encontra o
arquivo `gerar_relatorio_semanal.py`, porque esse arquivo só existe
dentro de `parte2_automacao`.

## Como rodar — passo a passo

### 1. Abra um terminal dentro da pasta `parte2_automacao`

No Windows: abra o Explorador de Arquivos, navegue até a pasta
`parte2_automacao` (a que tem o arquivo `gerar_relatorio_semanal.py`
dentro), clique com o botão direito em um espaço vazio dentro dela e
escolha **"Abrir no Terminal"** (Windows 11) ou seguindo **Shift + botão
direito → "Abrir janela do PowerShell aqui"** (Windows 10).

Alternativa que funciona em qualquer versão do Windows/Mac/Linux: abra o
terminal de onde estiver e use o comando `cd` (change directory) com o
caminho completo da pasta, por exemplo:

```bash
cd "C:\Users\SeuUsuario\Área de Trabalho\desafio-bari\parte2_automacao"
```

(troque pelo caminho real no seu computador — normalmente é o mesmo
caminho da pasta `desafio-bari`, trocando só a parte final para
`parte2_automacao`).

**Como confirmar que deu certo antes de continuar:** rode `dir` (Windows)
ou `ls` (Mac/Linux) e confira se `gerar_relatorio_semanal.py` aparece na
lista. Se não aparecer, você ainda não está na pasta certa — repita o
passo 1.

### 2. Crie o ambiente virtual (só na primeira vez)

```bash
python -m venv venv
```

Isso cria uma pasta `venv` **dentro da pasta onde você está** — por isso
o passo 1 importa: se você rodar este comando na pasta errada, ele
funciona sem erro nenhum, só cria o ambiente no lugar errado, e o
problema só aparece depois.

### 3. Ative o ambiente virtual (toda vez que for rodar, não só na primeira)

```bash
venv\Scripts\activate
```

(Mac/Linux: `source venv/bin/activate`)

Se funcionou, o início da linha do terminal passa a mostrar `(venv)`
antes do resto. Se não aparecer isso, o comando não teve efeito — mais
uma vez, o motivo mais comum é estar na pasta errada (a pasta `venv` só
existe dentro de `parte2_automacao`, criada no passo 2).

### 4. Instale as dependências (só na primeira vez)

```bash
pip install -r requirements.txt
```

## 5. Confirme o arquivo de dados

O `propostas_credito.csv` já vem incluído nesta pasta. Se quiser usar
outro arquivo ou caminho, informe no passo 6 com `--entrada`.

### 6. Rode o script

```bash
python gerar_relatorio_semanal.py --entrada propostas_credito.csv
```

### 7. Confira o resultado

Por padrão, o relatório sai na pasta `saida/` (HTML e Excel) e o log de
execução na pasta `logs/` (um `.log` legível + um `.json` estruturado por
execução), ambas criadas dentro de `parte2_automacao`. Para escolher só
um formato de saída ou pastas diferentes:

```bash
python gerar_relatorio_semanal.py --entrada propostas_credito.csv --formato html
python gerar_relatorio_semanal.py --entrada propostas_credito.csv --saida relatorios/ --logs logs/
```

Depois de rodar, confira o código de saída (tabela abaixo) e, principalmente
em caso de aviso ou falha, abra o `.log` mais recente em `logs/` antes de
repassar o relatório adiante.

## Deu erro "can't open file ... No such file or directory"?

Esse erro específico significa que o terminal está rodando o Python de
dentro da pasta errada — o Python abriu normalmente (por isso não é um
erro de instalação), só não encontrou `gerar_relatorio_semanal.py` porque
esse arquivo não existe na pasta onde o terminal está agora. Volte ao
passo 1: rode `cd` até a pasta `parte2_automacao` (confirme com `dir`/`ls`
que `gerar_relatorio_semanal.py` aparece na lista) e rode o comando do
passo 6 de novo a partir daí.

## Códigos de saída

| Código | Significado |
|---|---|
| `0` | Sucesso, sem nenhum aviso de qualidade de dados. |
| `1` | Sucesso, mas com aviso(s) — o relatório foi gerado, vale abrir o log antes de repassar. |
| `2` | Falha — nenhum relatório foi gerado (coluna crítica ausente, arquivo ilegível/vazio, ou o formato de uma coluna mudou por completo). |

## O que fazer se a execução falhar (código 2)

Abra o `.log` mais recente em `logs/` — a última linha `[ERROR]` explica o
motivo (coluna ausente e qual, ou formato de coluna que mudou por
completo, com exemplos dos valores que não converteram). Nenhum relatório
é gerado nesse caso, de propósito: é melhor investigar antes de mandar
números que podem estar errados para a liderança.
