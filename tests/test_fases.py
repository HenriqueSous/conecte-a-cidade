"""
Testes unitários de carregamento e integridade das fases.
"""

from itertools import combinations, product
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


@pytest.fixture
def fase_4():
    return carregar_fase(obter_caminho_fase(4))


def verificar_rede_sem_cruzamentos(fase, rede, par):
    grafo_solucao = Grafo(fase.grafo.n)
    arestas = fase.grafo.arestas()
    for aresta in rede:
        assert aresta in arestas
        grafo_solucao.adicionar_aresta(*aresta)
    assert len(rede) == fase.grafo.n - 1
    assert verificar_conectividade(grafo_solucao)
    assert sum(custo for _, _, custo in rede) == par
    for (u, v, _), (a, b, _) in combinations(rede, 2):
        origens_e_destinos = [fase.obter_posicao(numero) for numero in (u, v, a, b)]
        assert not segmentos_se_cruzam(*origens_e_destinos)


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


@pytest.mark.parametrize("numero, custo_por_distancia", [(2, 129), (3, 98), (4, 181), (5, 166)])
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

    verificar_rede_sem_cruzamentos(fase, rede, par)

    sem_rota_otima = [aresta for aresta in arestas if aresta[:2] != (2, 4)]
    custo_alternativo, rede_alternativa = buscar_agm_sem_cruzamentos(posicoes, sem_rota_otima)
    assert par < custo_alternativo == 82 <= fase.orcamento
    assert (1, 3, 5) in rede_alternativa


def test_fase_04_par_e_orcamento(fase_4):
    arestas = fase_4.grafo.arestas()
    assert fase_4.id == 4
    assert fase_4.grafo.n == 12 and 20 <= len(arestas) <= 28
    assert fase_4.sem_cruzamento
    assert fase_4.orcamento == ceil(fase_4.par * 1.18) == 128
    assert verificar_conectividade(fase_4.grafo)

    custo_kruskal, _ = kruskal(fase_4.grafo.n, arestas)
    assert custo_kruskal == prim(fase_4.grafo)[0] == 94
    posicoes = [fase_4.obter_posicao(casa.id) for casa in fase_4.casas]
    par, rede = buscar_agm_sem_cruzamentos(posicoes, arestas)
    assert custo_kruskal < par == fase_4.par == 108 <= fase_4.orcamento
    verificar_rede_sem_cruzamentos(fase_4, rede, par)


def test_fase_04_conflitos_e_rotas_alternativas(fase_4):
    arestas = fase_4.grafo.arestas()
    posicoes = [fase_4.obter_posicao(casa.id) for casa in fase_4.casas]
    conflitos = set()
    for (u, v, _), (a, b, _) in combinations(arestas, 2):
        if segmentos_se_cruzam(posicoes[u], posicoes[v], posicoes[a], posicoes[b]):
            conflitos.add(frozenset(((u, v), (a, b))))
    assert conflitos == {frozenset(((1, 5), (2, 4))), frozenset(((2, 6), (3, 5)))}

    # Excluir um cabo de cada conflito cobre todas as redes permitidas.
    # Nessas quatro opções, as arestas restantes podem ser comparadas por AGM.
    custos_por_exclusao = {
        ((1, 5), (2, 6)): 108,
        ((2, 4), (2, 6)): 117,
        ((1, 5), (3, 5)): 133,
        ((2, 4), (3, 5)): 132,
    }
    for excluidas, esperado in custos_por_exclusao.items():
        disponiveis = [aresta for aresta in arestas if aresta[:2] not in excluidas]
        custo, rede = kruskal(fase_4.grafo.n, disponiveis)
        assert custo == esperado
        verificar_rede_sem_cruzamentos(fase_4, rede, custo)
    assert 108 < 117 <= fase_4.orcamento < 132


def test_fase_05_par_e_orcamento():
    fase = carregar_fase(obter_caminho_fase(5))
    arestas = fase.grafo.arestas()
    assert fase.id == 5 and fase.sem_cruzamento
    assert fase.grafo.n == 14 and 24 <= len(arestas) <= 34
    assert verificar_conectividade(fase.grafo)
    assert kruskal(fase.grafo.n, arestas)[0] == prim(fase.grafo)[0] == 104

    posicoes = [fase.obter_posicao(casa.id) for casa in fase.casas]
    par, rede = buscar_agm_sem_cruzamentos(posicoes, arestas)
    assert fase.par == par == 122 > 104
    assert fase.orcamento == ceil(par * 1.05) == 129
    verificar_rede_sem_cruzamentos(fase, rede, par)

    direta = (0, 9, 17)
    rede_com_ligacao_direta = [aresta for aresta in rede if aresta[:2] != (5, 9)] + [direta]
    assert dist(posicoes[0], posicoes[9]) < dist(posicoes[5], posicoes[9])
    verificar_rede_sem_cruzamentos(fase, rede_com_ligacao_direta, 130)
    assert 130 > fase.orcamento


def test_fase_05_custos_dos_tres_conflitos():
    fase = carregar_fase(obter_caminho_fase(5))
    arestas = fase.grafo.arestas()
    conflitos = []
    for (u, v, _), (a, b, _) in combinations(arestas, 2):
        posicoes = [fase.obter_posicao(numero) for numero in (u, v, a, b)]
        if segmentos_se_cruzam(*posicoes):
            conflitos.append(((u, v), (a, b)))
    assert conflitos == [((1, 6), (2, 5)), ((2, 7), (3, 6)), ((3, 8), (4, 7))]

    # As oito combinações de exclusões cobrem todas as redes sem cruzamentos.
    custos = {}
    for excluidas in product(*conflitos):
        disponiveis = [aresta for aresta in arestas if aresta[:2] not in excluidas]
        custo, rede = kruskal(fase.grafo.n, disponiveis)
        verificar_rede_sem_cruzamentos(fase, rede, custo)
        custos[excluidas] = custo
    assert min(custos.values()) == fase.par
    assert custos[((1, 6), (2, 7), (3, 8))] == 123 <= fase.orcamento
    assert min(custo for excluidas, custo in custos.items() if (4, 7) in excluidas) == 130


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
