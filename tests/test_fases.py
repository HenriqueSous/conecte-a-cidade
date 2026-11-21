"""
Testes unitários de carregamento e integridade das fases.
"""

from itertools import combinations
from math import ceil, dist

import pytest

from ferramentas.validar_fases import custo_vizinhas_mais_proximas, verificar_legibilidade
from src.fases import carregar_fase, obter_caminho_fase
from src.algoritmos import kruskal, prim


@pytest.fixture
def fase_2():
    return carregar_fase(obter_caminho_fase(2))


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


def test_fase_02_valida(fase_2):
    assert fase_2.id == 2
    assert fase_2.grafo.n == 8
    assert 12 <= len(fase_2.ligacoes) <= 16
    assert not fase_2.sem_cruzamento
    assert fase_2.orcamento == ceil(fase_2.par * 1.40)
    custo_kruskal, agm_kruskal = kruskal(fase_2.grafo.n, fase_2.grafo.arestas())
    custo_prim, agm_prim = prim(fase_2.grafo, inicio=0)
    assert len(agm_kruskal) == len(agm_prim) == fase_2.grafo.n - 1
    assert custo_kruskal == custo_prim == fase_2.par == 79


def test_fase_02_comparacao_de_rotas_e_legibilidade(fase_2):
    assert custo_vizinhas_mais_proximas(fase_2) > fase_2.orcamento
    assert verificar_legibilidade(fase_2) == []

    def comprimento(aresta):
        origem, destino, _ = aresta
        return dist(fase_2.obter_posicao(origem), fase_2.obter_posicao(destino))

    arestas = fase_2.grafo.arestas()
    curtas_mais_caras = set()
    for curta, longa in combinations(sorted(arestas, key=comprimento), 2):
        compartilham_casa = set(curta[:2]).intersection(longa[:2])
        if compartilham_casa and curta[2] > longa[2] and comprimento(curta) < comprimento(longa):
            curtas_mais_caras.add(curta)
    assert len(curtas_mais_caras) / len(arestas) >= 0.30
