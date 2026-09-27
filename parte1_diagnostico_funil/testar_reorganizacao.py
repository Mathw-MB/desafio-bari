"""
testar_reorganizacao.py
Rode isto DE DENTRO da pasta parte1_diagnostico_funil/, depois de mover os
arquivos, para confirmar que nada quebrou. Não é parte da entrega — é só
uma ferramenta de verificação, pode apagar depois de confirmar que passou.
"""

import os
import subprocess
import sys

# Garante que o script rode a partir da própria pasta onde ele está salvo,
# independente de como foi iniciado (terminal, botão "Run" do VS Code etc.)
# — o botão Run às vezes usa a raiz do workspace como pasta de trabalho,
# não a pasta do arquivo, o que faria os caminhos relativos abaixo falharem.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Rodando a partir de: {os.getcwd()}\n")


def secao(titulo):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)


secao("1. Arquivos esperados na pasta atual")
scripts = [
    'tratamento.py', 'analise_funil_valor.py', 'analise_hipotese_lideranca.py',
    'analise_mix_canal.py', 'analise_associacao_contratacao.py',
    'calcular_impacto_recomendacoes.py',
]
faltando = [f for f in scripts + ['propostas_credito.csv'] if not os.path.exists(f)]
if faltando:
    print(f"FALTANDO: {faltando}")
    print("Pare aqui e corrija antes de continuar — os testes abaixo vão falhar.")
else:
    print("Todos os scripts e o CSV bruto estão presentes nesta pasta. OK.")

secao("2. Rodando tratamento.py e conferindo o log contra os valores já validados")
resultado = subprocess.run([sys.executable, 'tratamento.py'], capture_output=True, text=True)
print(resultado.stdout)
if resultado.returncode != 0:
    print("ERRO ao rodar tratamento.py:")
    print(resultado.stderr)
else:
    esperado = [
        'linhas_brutas: 6400',
        'propostas_terreno_mantidas: 535',
        'linhas_idade_invalida: 1',
        "ids_etapa_corrigida: ['PR-000081']",
        'linhas_data_inconsistente: 1',
        'linhas_ltv_nao_calculavel: 0',
        'linhas_tratadas: 6400',
    ]
    print("Conferência linha a linha do log:")
    todos_ok = True
    for linha in esperado:
        ok = linha in resultado.stdout
        todos_ok = todos_ok and ok
        print(f"  {'OK' if ok else 'DIVERGENTE'} — {linha}")
    print("\n>>> TUDO CONFERE <<<" if todos_ok else "\n>>> ATENÇÃO: algo não bateu, investigar <<<")

secao("3. Testando se os outros 5 scripts rodam sem erro (sem comparar números)")
for script in [s for s in scripts if s != 'tratamento.py']:
    r = subprocess.run([sys.executable, script], capture_output=True, text=True)
    print(f"  {script}: {'OK (rodou sem erro)' if r.returncode == 0 else 'ERRO'}")
    if r.returncode != 0:
        print("    Últimas linhas do erro:")
        for linha in r.stderr.strip().split("\n")[-5:]:
            print(f"    {linha}")

secao("FIM DO TESTE")
