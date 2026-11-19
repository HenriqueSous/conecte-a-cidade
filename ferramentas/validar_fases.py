"""
Ferramenta para validação de fases do jogo Conecte a Cidade.
Executa a validação cruzada entre Kruskal e Prim, checa orçamento,
conectividade, distâncias mínimas e integridade dos arquivos JSON.
"""

import glob
import math
import os
import sys
import time

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.algoritmos import kruskal, prim, verificar_conectividade
from src.fases import carregar_fase


FATORES_ORCAMENTO = {
    1: 1.60,
    2: 1.50,
    3: 1.40,
    4: 1.30,
    5: 1.22,
    6: 1.40,
    7: 1.30,
    8: 1.20,
    9: 1.12,
    10: 1.05
}


def validar_fase_individual(caminho_arquivo: str) -> bool:
    """Valida uma única fase e exibe o relatório."""
    inicio_tempo = time.perf_counter()
    print(f"\n--- Validando: {os.path.basename(caminho_arquivo)} ---")

    try:
        fase = carregar_fase(caminho_arquivo)
    except Exception as e:
        print(f"[ERRO] Falha ao carregar fase: {e}")
        return False

    n = fase.grafo.n
    arestas = fase.grafo.arestas()

    # 1. Checagem de conectividade
    if not verificar_conectividade(fase.grafo, inicio=0):
        print("[ERRO] O grafo da fase é desconexo!")
        return False

    # 2. Validação cruzada: Kruskal vs Prim
    custo_kruskal, agm_kruskal = kruskal(n, arestas)
    custo_prim, agm_prim = prim(fase.grafo, inicio=0)

    if custo_kruskal != custo_prim:
        print(f"[ERRO] Divergência na AGM! Kruskal deu {custo_kruskal} e Prim deu {custo_prim}.")
        return False

    if not fase.sem_cruzamento:
        if fase.par != custo_kruskal:
            print(f"[AVISO] Par gravado ({fase.par}) difere da AGM ({custo_kruskal}).")
    
    # 3. Validação do orçamento
    fator_esperado = FATORES_ORCAMENTO.get(fase.id, 1.30)
    orcamento_calculado = math.ceil(fase.par * fator_esperado)
    if fase.orcamento != orcamento_calculado:
        print(f"[AVISO] Orçamento gravado ({fase.orcamento}) difere de ceil(par * {fator_esperado}) = {orcamento_calculado}")

    tempo_ms = (time.perf_counter() - inicio_tempo) * 1000

    print(f"Sucesso: Fase {fase.id} ('{fase.nome}')")
    print(f"Casas: {n} | Ligações: {len(arestas)}")
    print(f"Par: {fase.par} (Kruskal: {custo_kruskal}, Prim: {custo_prim})")
    print(f"Orçamento: {fase.orcamento} (Folga: +{fase.orcamento - fase.par})")
    print(f"Tempo de validação: {tempo_ms:.2f} ms")
    return True


def main() -> None:
    diretorio_fases = os.path.join(os.path.dirname(__file__), "..", "dados", "fases")
    arquivos = sorted(glob.glob(os.path.join(diretorio_fases, "fase_*.json")))

    if not arquivos:
        print("Nenhum arquivo de fase encontrado em dados/fases/!")
        sys.exit(1)

    todos_sucessos = True
    for arq in arquivos:
        sucesso = validar_fase_individual(arq)
        if not sucesso:
            todos_sucessos = False

    print("\n" + "=" * 45)
    if todos_sucessos:
        print("Resultado: TODAS AS FASES SÃO VÁLIDAS!")
    else:
        print("Resultado: HOUVE ERROS NA VALIDAÇÃO.")
        sys.exit(1)


if __name__ == "__main__":
    main()
