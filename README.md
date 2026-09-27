# Desafio Prático — Estágio AI & Data Lab | Bari

Candidato: Matheus Miguel Barbosa

Entrega completa do desafio: diagnóstico do funil de crédito (Parte 1),
automação do relatório semanal (Parte 2), e extração estruturada de
laudos de avaliação com IA (Parte 3). O enunciado original está em
`Desafio_Prático-Estágio_AI_DataLab_Bari.pdf`.

**Cada uma das 3 partes pode ser avaliada só lendo os documentos, sem
precisar rodar nada** — rodar os scripts é para quem quiser verificar ou
reproduzir o resultado, não é pré-requisito para avaliar o trabalho. Os
detalhes de cada parte estão nos parágrafos abaixo e, com profundidade
completa, no `README.md` de cada pasta.

## Estrutura do repositório

```
desafio-bari/
├── README.md                       este arquivo
├── DIARIO.md                       uso de IA e autocrítica (Parte 4 do desafio)
├── resumo_executivo.md             1 página para a liderança, sem jargão técnico
├── Desafio_Prático-Estágio_AI_DataLab_Bari.pdf
├── parte1_diagnostico_funil/
├── parte2_automacao/
└── parte3_extracao/
```

## As 3 partes

| Parte | O que é | Pasta |
|---|---|---|
| 1 | Diagnóstico do funil: 4 perguntas respondidas com evidência estatística | `parte1_diagnostico_funil/` |
| 2 | Rotina que gera o relatório semanal do funil (HTML/Excel), com tratamento de erro e robustez a formato inesperado | `parte2_automacao/` |
| 3 | Extração estruturada de 9 campos de 17 laudos de avaliação, via IA, com critério de acerto próprio | `parte3_extracao/` |

### Parte 1 — Diagnóstico do funil

**Para avaliar sem rodar nada:** leia `parte1_diagnostico_funil/respostas_parte1.md`
(as 4 perguntas, com metodologia e nível de confiança) e
`registro_tratamento_dados.md` (cada decisão de limpeza, incluindo uma
que foi revertida depois de uma investigação).

**Para rodar:**
```bash
cd parte1_diagnostico_funil
python -m venv venv && venv\Scripts\activate      # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
# copie propostas_credito.csv para esta pasta
python testar_reorganizacao.py                     # confirma que está tudo certo
python tratamento.py
python analise_funil_valor.py
python analise_hipotese_lideranca.py
python analise_mix_canal.py
python analise_associacao_contratacao.py
python calcular_impacto_recomendacoes.py
```
Detalhes completos, incluindo o que esperar ver em cada passo:
`parte1_diagnostico_funil/README.md`.

### Parte 2 — Automação do relatório semanal

**Para avaliar sem rodar nada:** veja `parte2_automacao/testes/saida_exemplo/`
e `testes/logs_exemplo/` — saída real de uma execução já processada.

**Para rodar:**
```bash
cd parte2_automacao
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
# copie propostas_credito.csv para esta pasta
python gerar_relatorio_semanal.py --entrada propostas_credito.csv
```
Detalhes completos, incluindo os códigos de saída e o que fazer se a
execução falhar: `parte2_automacao/README.md`.

### Parte 3 — Extração com IA

**Para avaliar sem rodar nada:** a extração dos 17 laudos já está
processada em `parte3_extracao/resultados/`, junto com o placar de acerto
contra o gabarito e o CSV consolidado. Rodar de novo só é necessário para
conferir com sua própria chamada de API.

**Para rodar (opcional):**
```bash
cd parte3_extracao
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python3 test_mock.py              # testa toda a lógica sem gastar chamada de API
# configure .env com sua GEMINI_API_KEY (ver README da pasta)
python3 extrator.py
python3 avaliar.py resultados/tudo.json
python3 json_para_csv.py resultados/tudo.json resultados/consolidado.csv
```
Detalhes completos, incluindo como gerar uma API key gratuita e o que
fazer em caso de erro de cota: `parte3_extracao/README.md`.

## Diário de bordo e resumo executivo

- **`DIARIO.md`** — registro de uso de IA (situações concretas onde ajudou,
  atrapalhou, ou precisou ser corrigida), um conceito aprendido do zero, e
  autocrítica. Cobre o desafio inteiro, não uma parte específica.
- **`resumo_executivo.pdf`** — as conclusões da Parte 1 em 1 página, escritas
  para a liderança comercial, sem jargão técnico.

## Tempo total gasto

**~19 horas**, entre as 3 partes, a documentação e a organização da entrega.
