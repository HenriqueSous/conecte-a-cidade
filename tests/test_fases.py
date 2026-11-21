"""
Testes unitários de carregamento e integridade das fases.
"""

from itertools import combinations
import json
from math import ceil, dist

import pytest

from ferramentas.validar_fases import custo_vizinhas_mais_proximas, validar_fase_individual, verificar_legibilidade
from src.algoritmos import buscar_agm_sem_cruzamentos, kruskal, prim, verificar_conectividade
from src.fases import carregar_fase, obter_caminho_fase
from src.geometria import segmentos_se_cruzam
from src.grafo import Grafo


@pytest.fixture
def fase_2():
    return carregar_fase(obter_caminho_fase(2))


def test_fase_01_valida():
    caminho = obter_caminho_fase(1)
    fase = carregar_fase(caminho)

    assert fase.id == 1
    assert not fase.sem_cruzamento
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


@pytest.mark.parametrize("numero, custo_por_distancia", [(2, 129), (3, 98)])
def test_comparacao_de_rotas_e_legibilidade(numero, custo_por_distancia):
    fase = carregar_fase(obter_caminho_fase(numero))
    assert custo_vizinhas_mais_proximas(fase) == custo_por_distancia > fase.par
    assert verificar_legibilidade(fase) == []

    def comprimento(aresta):
        origem, destino, _ = aresta
        return dist(fase.obter_posicao(origem), fase.obter_posicao(destino))

    arestas = fase.grafo.arestas()
    curtas_mais_caras = set()
    for curta, longa in combinations(sorted(arestas, key=comprimento), 2):
        compartilham_casa = set(curta[:2]).intersection(longa[:2])
        if compartilham_casa and curta[2] > longa[2] and comprimento(curta) < comprimento(longa):
            curtas_mais_caras.add(curta)
    assert len(curtas_mais_caras) / len(arestas) >= 0.30


def test_fase_03_par_sem_cruzamentos():
    fase = carregar_fase(obter_caminho_fase(3))
    arestas = fase.grafo.arestas()
    assert fase.id == 3
    assert fase.grafo.n == 9 and 14 <= len(arestas) <= 19
    assert fase.sem_cruzamento
    assert fase.orcamento == ceil(fase.par * 1.32) == 98

    custo_kruskal, agm = kruskal(fase.grafo.n, arestas)
    assert custo_kruskal == prim(fase.grafo)[0] == 66
    assert (1, 3, 5) in agm and (2, 4, 6) in agm
    posicoes = [fase.obter_posicao(casa.id) for casa in fase.casas]
    par, rede = buscar_agm_sem_cruzamentos(posicoes, arestas)
    assert custo_kruskal < par == fase.par == 74

    grafo_solucao = Grafo(fase.grafo.n)
    for aresta in rede:
        assert aresta in arestas
        grafo_solucao.adicionar_aresta(*aresta)
    assert len(rede) == fase.grafo.n - 1
    assert verificar_conectividade(grafo_solucao)
    assert sum(custo for _, _, custo in rede) == par
    for (u, v, _), (a, b, _) in combinations(rede, 2):
        assert not segmentos_se_cruzam(posicoes[u], posicoes[v], posicoes[a], posicoes[b])

    sem_rota_otima = [aresta for aresta in arestas if aresta[:2] != (2, 4)]
    custo_alternativo, rede_alternativa = buscar_agm_sem_cruzamentos(posicoes, sem_rota_otima)
    assert par < custo_alternativo == 82 <= fase.orcamento
    assert (1, 3, 5) in rede_alternativa


def test_validador_atualiza_par_e_orcamento_so_quando_solicitado(tmp_path):
    with open(obter_caminho_fase(3), encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    caminho = tmp_path / "fase_03.json"
    dados.update(par=66, orcamento=88)
    caminho.write_text(json.dumps(dados), encoding="utf-8")

    assert not validar_fase_individual(str(caminho))
    assert carregar_fase(caminho).par == 66
    assert validar_fase_individual(str(caminho), gravar=True)
    fase = carregar_fase(caminho)
    assert (fase.par, fase.orcamento) == (74, 98)
