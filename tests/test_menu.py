"""
Verifica o fluxo do menu e o progresso com eventos do Pygame sem abrir janela.
As fases de teste e o progresso ficam em um diretório temporário.
"""

from pathlib import Path
from shutil import copyfile

import pygame
import pytest

from main import ALTURA_TELA, LARGURA_TELA, RAIZ_PROJETO, Aplicacao, main
from src import fases
from src.pontuacao import avaliar_resultado
from src.progresso import Progresso


@pytest.fixture
def projeto_temporario(tmp_path):
    pasta = tmp_path / "dados" / "fases"
    pasta.mkdir(parents=True)
    copyfile(RAIZ_PROJETO / "dados" / "fases" / "fase_01.json", pasta / "fase_01.json")
    return tmp_path


@pytest.fixture
def superficie(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    try:
        yield pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    finally:
        pygame.quit()


def clicar(aplicacao, posicao):
    evento = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=posicao)
    aplicacao.tratar_evento(evento)
    if aplicacao.rodando:
        aplicacao.desenhar(posicao)


def clicar_botao(aplicacao, rotulo):
    botao = next(botao for botao in aplicacao.botoes if botao.texto == rotulo)
    clicar(aplicacao, botao.area.center)


def pressionar_esc(aplicacao):
    aplicacao.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    aplicacao.desenhar((0, 0))


def conectar(aplicacao, ligacoes):
    fase = aplicacao.jogo.fase
    for origem, destino in ligacoes:
        clicar(aplicacao, fase.obter_posicao(origem))
        clicar(aplicacao, fase.obter_posicao(destino))


def test_navegacao_conclusao_e_repeticao(projeto_temporario, superficie):
    aplicacao = Aplicacao(superficie, projeto_temporario)
    assert aplicacao.tela_atual == "menu"
    assert aplicacao.jogo is None
    aplicacao.desenhar((0, 0))

    clicar_botao(aplicacao, "Como Jogar")
    assert aplicacao.tela_atual == "instrucoes"
    clicar_botao(aplicacao, "Voltar")
    clicar_botao(aplicacao, "Selecionar Fase")
    assert aplicacao.tela_atual == "selecao"
    assert [cartao.situacao for cartao in aplicacao.cartoes] == ["Disponível"] + ["Em breve"] * 4
    for cartao in aplicacao.cartoes[1:]:
        clicar(aplicacao, cartao.botao.area.center)
        assert aplicacao.jogo is None
    clicar_botao(aplicacao, "Voltar")
    clicar_botao(aplicacao, "Jogar")
    assert aplicacao.jogo.fase.id == 1

    conectar(aplicacao, [(0, 2)])
    pressionar_esc(aplicacao)
    assert aplicacao.tela_atual == "pausa"
    clicar_botao(aplicacao, "Continuar")
    assert aplicacao.jogo.gasto == 10
    pressionar_esc(aplicacao)
    clicar_botao(aplicacao, "Reiniciar fase")
    assert aplicacao.tela_atual == "partida"
    assert aplicacao.jogo.gasto == 0

    conectar(aplicacao, [(0, 2), (3, 4), (0, 1), (2, 3)])
    assert aplicacao.tela_atual == "resultado"
    assert "Próxima fase" not in [botao.texto for botao in aplicacao.botoes]
    progresso = Progresso(projeto_temporario / "progresso.json")
    assert progresso.obter(1).concluida
    assert progresso.obter(1).melhor_pontuacao == 1000
    assert progresso.obter(1).melhor_custo == 46
    assert progresso.obter(1).estrelas == 3

    clicar_botao(aplicacao, "Repetir fase")
    conectar(aplicacao, [(0, 2), (3, 4), (0, 1), (1, 3)])
    assert aplicacao.jogo.resultado.custo_jogador == 47
    clicar_botao(aplicacao, "Voltar à seleção de fases")
    assert aplicacao.cartoes[0].situacao == "Concluída"
    assert aplicacao.cartoes[0].estrelas == 3
    clicar(aplicacao, aplicacao.cartoes[0].botao.area.center)
    assert aplicacao.jogo.fase.id == 1
    pressionar_esc(aplicacao)
    clicar_botao(aplicacao, "Voltar ao menu principal")
    clicar_botao(aplicacao, "Sair")
    assert not aplicacao.rodando

    reaberto = Aplicacao(superficie, projeto_temporario)
    assert reaberto.progresso.obter(1) == progresso.obter(1)
    clicar_botao(reaberto, "Jogar")
    assert reaberto.tela_atual == "selecao"


def test_fase_02_reconhecida_e_desbloqueada(projeto_temporario, superficie, monkeypatch):
    carregamentos = []
    carregar_fase_real = fases.carregar_fase

    def registrar_carregamento(caminho):
        carregamentos.append(Path(caminho).name)
        return carregar_fase_real(caminho)

    monkeypatch.setattr(fases, "carregar_fase", registrar_carregamento)
    primeira_execucao = Aplicacao(superficie, projeto_temporario)
    assert carregamentos == ["fase_01.json"]
    primeira_execucao.progresso.registrar_conclusao(1, avaliar_resultado(46, 46))

    pasta_fases = projeto_temporario / "dados" / "fases"
    copyfile(RAIZ_PROJETO / "dados" / "fases" / "fase_02.json", pasta_fases / "fase_02.json")
    carregamentos.clear()
    aplicacao = Aplicacao(superficie, projeto_temporario)
    assert list(aplicacao.fases) == [1, 2]
    assert carregamentos == ["fase_01.json", "fase_02.json"]
    clicar_botao(aplicacao, "Jogar")
    assert aplicacao.jogo.fase.id == 2

    (projeto_temporario / "progresso.json").unlink()
    aplicacao = Aplicacao(superficie, projeto_temporario)
    clicar_botao(aplicacao, "Selecionar Fase")
    assert [cartao.situacao for cartao in aplicacao.cartoes] == ["Disponível", "Bloqueada"] + ["Em breve"] * 3
    assert aplicacao.cartoes[1].nome == "Rotas do Bairro"
    clicar(aplicacao, aplicacao.cartoes[1].botao.area.center)
    assert aplicacao.jogo is None
    clicar(aplicacao, aplicacao.cartoes[0].botao.area.center)
    conectar(aplicacao, [(0, 2), (3, 4), (0, 1), (2, 3)])
    clicar_botao(aplicacao, "Próxima fase")
    assert aplicacao.jogo.fase.id == 2

    conectar(aplicacao, [(0, 3), (2, 3), (3, 6), (2, 5), (3, 4), (1, 4), (5, 7)])
    assert aplicacao.tela_atual == "resultado"
    assert aplicacao.jogo.resultado.custo_jogador == 81
    assert aplicacao.jogo.resultado.estrelas == 2
    clicar_botao(aplicacao, "Repetir fase")
    conectar(aplicacao, [(0, 3), (2, 3), (3, 6), (2, 5), (4, 6), (1, 4), (5, 7)])
    assert aplicacao.tela_atual == "resultado"
    assert "Próxima fase" not in [botao.texto for botao in aplicacao.botoes]
    assert "fase_03.json" not in carregamentos
    clicar_botao(aplicacao, "Menu principal")
    clicar_botao(aplicacao, "Sair")

    reaberto = Aplicacao(superficie, projeto_temporario)
    registro = reaberto.progresso.obter(2)
    assert registro.concluida
    assert registro.melhor_custo == 79
    assert registro.melhor_pontuacao == 1000
    assert registro.estrelas == 3
    clicar_botao(reaberto, "Jogar")
    assert reaberto.tela_atual == "selecao"
    assert reaberto.cartoes[1].situacao == "Concluída"
    assert reaberto.cartoes[1].estrelas == 3
    assert reaberto.cartoes[2].situacao == "Em breve"


def test_catalogo_ignora_fase_invalida(projeto_temporario):
    caminho_invalido = projeto_temporario / "dados" / "fases" / "fase_03.json"
    caminho_invalido.write_text("[]", encoding="utf-8")
    assert list(fases.carregar_catalogo_fases(str(projeto_temporario))) == [1]


@pytest.mark.parametrize("conteudo", ["{", "[]", '{"fases": {"1": false}}'])
def test_progresso_corrompido_pode_ser_regravado(tmp_path, conteudo):
    caminho = tmp_path / "progresso.json"
    caminho.write_text(conteudo, encoding="utf-8")
    progresso = Progresso(caminho)
    assert progresso.fase_desbloqueada(1)
    assert not progresso.fase_desbloqueada(2)
    assert progresso.registrar_conclusao(1, avaliar_resultado(46, 46))
    assert Progresso(caminho).fase_desbloqueada(2)


def test_main_abre_e_encerra_com_sair(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    paginas_de_eventos = iter([
        [],
        [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 497))],
    ])
    monkeypatch.setattr(pygame.event, "get", lambda: next(paginas_de_eventos))
    main()
    assert not pygame.get_init()
