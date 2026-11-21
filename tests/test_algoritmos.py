"""
Testes unitários dos algoritmos de grafos (Kruskal, Prim, BFS, União-Busca).
"""

import pytest
from src.grafo import Grafo
from src.algoritmos import (
    UniaoBusca,
    kruskal,
    prim,
    bfs_componente,
    verificar_conectividade,
    detectar_cabo_redundante,
    calcular_limite_inferior_restante,
    buscar_agm_sem_cruzamentos,
)


def test_uniao_busca():
    dsu = UniaoBusca(5)
    assert dsu.quantidade_conjuntos == 5
    assert dsu.unir(0, 1) is True
    assert dsu.quantidade_conjuntos == 4
    assert dsu.unir(1, 2) is True
    assert dsu.encontrar(0) == dsu.encontrar(2)
    # Tentar unir elementos já conectados deve retornar False (ciclo)
    assert dsu.unir(0, 2) is False
    assert dsu.quantidade_conjuntos == 3


def test_kruskal_e_prim_mesmo_custo():
    # Grafo de teste com 4 vértices e 5 arestas
    g = Grafo(4)
    g.adicionar_aresta(0, 1, 10)
    g.adicionar_aresta(0, 2, 6)
    g.adicionar_aresta(0, 3, 5)
    g.adicionar_aresta(1, 3, 15)
    g.adicionar_aresta(2, 3, 4)

    # Arestas: (2, 3)=4, (0, 3)=5, (0, 2)=6 (ciclo), (0, 1)=10. AGM total = 4 + 5 + 10 = 19
    custo_kruskal, agm_kruskal = kruskal(4, g.arestas())
    custo_prim, agm_prim = prim(g, inicio=0)

    assert custo_kruskal == 19
    assert custo_prim == 19
    assert len(agm_kruskal) == 3
    assert len(agm_prim) == 3


def test_bfs_e_conectividade():
    g = Grafo(4)
    g.adicionar_aresta(0, 1, 5)
    g.adicionar_aresta(1, 2, 8)
    # Vértice 3 está desconexo
    assert verificar_conectividade(g, inicio=0) is False
    assert bfs_componente(g, inicio=0) == {0, 1, 2}

    # Conecta o vértice 3
    g.adicionar_aresta(2, 3, 2)
    assert verificar_conectividade(g, inicio=0) is True
    assert bfs_componente(g, inicio=0) == {0, 1, 2, 3}


def test_detectar_cabo_redundante():
    # Construídas: 0-1 e 1-2. Vértices 0, 1, 2 já estão conectados
    arestas = [(0, 1), (1, 2)]
    # Ligar 0-2 forma um ciclo redundante
    assert detectar_cabo_redundante(4, arestas, 0, 2) is True
    # Ligar 2-3 NÃO é redundante (expande para nova casa)
    assert detectar_cabo_redundante(4, arestas, 2, 3) is False


def test_limite_inferior_restante():
    # 4 casas: 0, 1, 2, 3
    # Construído: 0-1
    # Disponíveis: (1, 2, custo 10), (2, 3, custo 5)
    construidas = [(0, 1)]
    disponiveis = [(1, 2, 10), (2, 3, 5)]
    # Para ligar {0, 1}, {2}, {3}: precisa de 10 + 5 = 15
    limite = calcular_limite_inferior_restante(4, construidas, disponiveis)
    assert limite == 15


def test_busca_exata_rejeita_cruzamento_e_testa_alternativa():
    posicoes = [(0, 0), (100, 100), (0, 100), (100, 0)]
    arestas = [(0, 1, 1), (2, 3, 2), (0, 2, 3)]
    assert kruskal(4, arestas)[0] == 6
    assert buscar_agm_sem_cruzamentos(posicoes, arestas) is None

    arestas.append((1, 3, 7))
    assert buscar_agm_sem_cruzamentos(posicoes, arestas) == (11, [(0, 1, 1), (0, 2, 3), (1, 3, 7)])
