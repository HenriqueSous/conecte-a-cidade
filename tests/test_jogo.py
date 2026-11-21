"""
Testes unitários da lógica e regras da partida (sem interface gráfica).
"""

import pytest
from src.fases import carregar_fase, obter_caminho_fase
from src.jogo import Jogo
from src.pontuacao import calcular_estrelas, calcular_aproveitamento, calcular_pontos


@pytest.fixture
def jogo_fase_1():
    fase = carregar_fase(obter_caminho_fase(1))
    return Jogo(fase)


def test_construir_e_remover_cabo(jogo_fase_1):
    jogo = jogo_fase_1
    assert jogo.gasto == 0
    assert len(jogo.cabos_construidos) == 0

    # Seleciona casa 0 e depois casa 2 (custo 10)
    jogo.selecionar_casa(0)
    assert jogo.casa_selecionada == 0
    jogo.selecionar_casa(2)
    assert jogo.gasto == 10
    assert (0, 2) in jogo.cabos_construidos
    assert jogo.casa_selecionada is None

    # Alternância: selecionar as mesmas duas casas remove o cabo
    jogo.selecionar_casa(0)
    jogo.selecionar_casa(2)
    assert jogo.gasto == 0
    assert (0, 2) not in jogo.cabos_construidos


def test_desfazer_historico(jogo_fase_1):
    jogo = jogo_fase_1
    jogo.selecionar_casa(0)
    jogo.selecionar_casa(1)  # custo 12
    assert jogo.gasto == 12

    jogo.desfazer()
    assert jogo.gasto == 0
    assert (0, 1) not in jogo.cabos_construidos


def test_orçamento_bloqueia_construcao(jogo_fase_1):
    jogo = jogo_fase_1
    # Forçar gasto quase no limite do orçamento (74)
    jogo.gasto = 70
    # Tentativa de construir ligação de custo 12 (0-1) deve falhar
    permitido, motivo = jogo.pode_construir(0, 1)
    assert permitido is False
    assert "Orçamento" in motivo


def test_cabo_redundante_ciclo(jogo_fase_1):
    jogo = jogo_fase_1
    # Conecta 0-1 e 0-2 (sem fechar ciclo)
    jogo.selecionar_casa(0)
    jogo.selecionar_casa(1)
    jogo.selecionar_casa(0)
    jogo.selecionar_casa(2)

    assert (0, 1) not in jogo.cabos_redundantes
    assert (0, 2) not in jogo.cabos_redundantes

    # Conecta 1-2: forma um ciclo triangular entre 0, 1 e 2
    jogo.selecionar_casa(1)
    jogo.selecionar_casa(2)

    # 1-2 deve ser detectado como cabo redundante
    assert (1, 2) in jogo.cabos_redundantes
    assert jogo.vitoria is False  # casas 3 e 4 ainda não estão conectadas


def test_vitoria_e_pontuacao(jogo_fase_1):
    jogo = jogo_fase_1
    # Construir árvore ótima da Fase 1: (0, 2)[10], (3, 4)[11], (0, 1)[12], (2, 3)[13] = 46
    conexoes = [(0, 2), (3, 4), (0, 1), (2, 3)]
    for u, v in conexoes:
        jogo.selecionar_casa(u)
        jogo.selecionar_casa(v)

    assert jogo.vitoria is True
    assert jogo.gasto == 46
    assert jogo.resultado is not None
    assert jogo.resultado.estrelas == 3
    assert jogo.resultado.pontos == 1000



def test_reiniciar_jogo(jogo_fase_1):
    jogo = jogo_fase_1
    jogo.selecionar_casa(0)
    jogo.selecionar_casa(1)
    assert jogo.gasto > 0

    jogo.reiniciar()
    assert jogo.gasto == 0
    assert len(jogo.cabos_construidos) == 0
    assert jogo.vitoria is False
    assert jogo.casa_selecionada is None


def test_pontuacao_calculos():
    # Custo igual ao par -> 3 estrelas e 1000 pontos
    assert calcular_estrelas(46, 46) == 3
    assert calcular_pontos(46, 46) == 1000
    assert calcular_aproveitamento(46, 46) == 100.0

    # Aproveitamento >= 85% -> 2 estrelas
    # Ex: par=46, gasto=52 -> 46/52 = 88.46%
    assert calcular_estrelas(52, 46) == 2
    assert calcular_pontos(46, 52) == 885

    # Aproveitamento < 85% -> 1 estrela
    # Ex: par=46, gasto=65 -> 46/65 = 70.76%
    assert calcular_estrelas(65, 46) == 1


def test_fase_02_detecta_beco_sem_saida_e_permite_corrigir():
    jogo = Jogo(carregar_fase(obter_caminho_fase(2)))
    for origem, destino in [(0, 3), (2, 3), (2, 5), (3, 5), (0, 2)]:
        assert jogo.selecionar_casa(origem)
        assert jogo.selecionar_casa(destino)

    assert jogo.gasto == 66
    assert (3, 5) in jogo.cabos_redundantes
    assert (0, 2) in jogo.cabos_redundantes
    assert jogo.beco_sem_saida
    assert jogo.desfazer()
    assert jogo.gasto == 49
    assert not jogo.beco_sem_saida

    for origem, destino in [(3, 6), (4, 6), (1, 4), (5, 7)]:
        assert jogo.selecionar_casa(origem)
        assert jogo.selecionar_casa(destino)
    assert jogo.vitoria
    assert jogo.resultado.custo_jogador == 97
    assert jogo.resultado.pontos == 814
    assert jogo.resultado.estrelas == 1
