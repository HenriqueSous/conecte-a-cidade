"""
Testes unitários de carregamento e integridade das fases.
"""

import pytest
from src.fases import carregar_fase, obter_caminho_fase
from src.algoritmos import kruskal, prim


def test_fase_01_valida():
    caminho = obter_caminho_fase(1)
    fase = carregar_fase(caminho)

    assert fase.id == 1
    assert fase.nome == "Primeiras Conexões"
    assert len(fase.casas) == 5
    assert len(fase.ligacoes) == 7
    assert fase.casas[0].central is True

    # Validação do par
    custo_kruskal, _ = kruskal(fase.grafo.n, fase.grafo.arestas())
    custo_prim, _ = prim(fase.grafo, inicio=0)
    assert custo_kruskal == fase.par
    assert custo_prim == fase.par
