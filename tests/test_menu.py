"""
Verifica o fluxo do menu e o progresso com eventos do Pygame sem abrir janela.
As fases de teste e o progresso ficam em um diretório temporário.
"""

import json
from pathlib import Path
from shutil import copyfile

import pygame
import pytest

from main import ALTURA_TELA, LARGURA_TELA, RAIZ_PROJETO, Aplicacao, main
from src import fases
from src.interface import COR_PREVIA_INVALIDA, COR_PREVIA_VALIDA, RenderizadorJogo
from src.jogo import Jogo
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
        yield pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.RESIZABLE)
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


def test_fase_03_previa_so_bloqueia_apos_construir_cabo(superficie):
    fase = fases.carregar_fase(fases.obter_caminho_fase(3, RAIZ_PROJETO))
    jogo = Jogo(fase)
    renderizador = RenderizadorJogo()
    alvo = fase.obter_posicao(4)
    # Ponto no primeiro quarto de 2–4, fora do rótulo e dos sprites.
    ponto_na_previa = (666, 238)

    jogo.selecionar_casa(2)
    renderizador.desenhar(superficie, jogo, alvo)
    assert superficie.get_at(ponto_na_previa)[:3] == COR_PREVIA_VALIDA

    jogo.cancelar_selecao()
    jogo.selecionar_casa(1)
    assert jogo.selecionar_casa(3)
    assert jogo.pode_construir(0, 1)[0]  # Compartilha a casa 1 com o cabo construído.
    jogo.selecionar_casa(2)
    renderizador.desenhar(superficie, jogo, alvo)
    assert superficie.get_at(ponto_na_previa)[:3] == COR_PREVIA_INVALIDA
    assert not jogo.selecionar_casa(4)
    assert jogo.mensagem_feedback == "Este cabo cruzaria outro cabo."
    assert jogo.gasto == 5 and jogo.cabos_construidos == {(1, 3)}

    assert jogo.desfazer()
    jogo.selecionar_casa(2)
    assert jogo.selecionar_casa(4)


def test_fase_03_desbloqueio_e_resultados(projeto_temporario, superficie, monkeypatch):
    pasta_fases = projeto_temporario / "dados" / "fases"
    for nome in ["fase_02.json", "fase_03.json"]:
        copyfile(RAIZ_PROJETO / "dados" / "fases" / nome, pasta_fases / nome)

    carregar_fase_real = fases.carregar_fase

    def carregar_fase_existente(caminho):
        assert Path(caminho).is_file()
        return carregar_fase_real(caminho)

    monkeypatch.setattr(fases, "carregar_fase", carregar_fase_existente)
    aplicacao = Aplicacao(superficie, projeto_temporario)
    aplicacao.progresso.registrar_conclusao(1, avaliar_resultado(46, 46))
    clicar_botao(aplicacao, "Selecionar Fase")
    assert [cartao.situacao for cartao in aplicacao.cartoes] == [
        "Concluída", "Disponível", "Bloqueada", "Em breve", "Em breve"
    ]
    clicar(aplicacao, aplicacao.cartoes[2].botao.area.center)
    assert aplicacao.jogo is None
    clicar(aplicacao, aplicacao.cartoes[1].botao.area.center)
    conectar(aplicacao, [(0, 3), (2, 3), (3, 6), (2, 5), (4, 6), (1, 4), (5, 7)])
    clicar_botao(aplicacao, "Próxima fase")
    assert aplicacao.jogo.fase.id == 3

    aplicacao = Aplicacao(superficie, projeto_temporario)
    clicar_botao(aplicacao, "Jogar")
    assert aplicacao.jogo.fase.id == 3
    conectar(aplicacao, [(1, 3)])
    pressionar_esc(aplicacao)
    clicar_botao(aplicacao, "Reiniciar fase")
    assert aplicacao.jogo.gasto == 0

    conectar(aplicacao, [(0, 1), (0, 4), (1, 3), (2, 6), (3, 7), (4, 5), (6, 7), (7, 8)])
    assert aplicacao.tela_atual == "resultado"
    assert aplicacao.jogo.resultado.custo_jogador == 82
    assert aplicacao.jogo.resultado.estrelas == 2
    assert "Próxima fase" not in [botao.texto for botao in aplicacao.botoes]
    clicar_botao(aplicacao, "Repetir fase")
    conectar(aplicacao, [(0, 1), (0, 4), (2, 4), (2, 6), (3, 4), (3, 7), (4, 5), (7, 8)])
    assert aplicacao.tela_atual == "resultado"
    clicar_botao(aplicacao, "Voltar à seleção de fases")
    assert aplicacao.cartoes[2].situacao == "Concluída"
    assert [cartao.situacao for cartao in aplicacao.cartoes[3:]] == ["Em breve", "Em breve"]

    reaberto = Aplicacao(superficie, projeto_temporario)
    registro = reaberto.progresso.obter(3)
    assert registro.concluida
    assert (registro.melhor_custo, registro.melhor_pontuacao, registro.estrelas) == (74, 1000, 3)


def test_fase_04_desbloqueio_e_repeticao(projeto_temporario, superficie, monkeypatch):
    pasta_fases = projeto_temporario / "dados" / "fases"
    for nome in ["fase_02.json", "fase_03.json", "fase_04.json"]:
        copyfile(RAIZ_PROJETO / "dados" / "fases" / nome, pasta_fases / nome)

    carregar_fase_real = fases.carregar_fase

    def carregar_fase_existente(caminho):
        assert Path(caminho).is_file()
        return carregar_fase_real(caminho)

    monkeypatch.setattr(fases, "carregar_fase", carregar_fase_existente)
    aplicacao = Aplicacao(superficie, projeto_temporario)
    aplicacao.progresso.registrar_conclusao(1, avaliar_resultado(46, 46))
    aplicacao.progresso.registrar_conclusao(2, avaliar_resultado(79, 79))
    clicar_botao(aplicacao, "Selecionar Fase")
    assert aplicacao.cartoes[3].nome == "Entre Bairros"
    assert aplicacao.cartoes[3].situacao == "Bloqueada"
    assert aplicacao.cartoes[4].situacao == "Em breve"
    clicar(aplicacao, aplicacao.cartoes[3].botao.area.center)
    assert aplicacao.jogo is None

    clicar(aplicacao, aplicacao.cartoes[2].botao.area.center)
    conectar(aplicacao, [(0, 1), (0, 4), (2, 4), (2, 6), (3, 4), (3, 7), (4, 5), (7, 8)])
    clicar_botao(aplicacao, "Próxima fase")
    assert aplicacao.jogo.fase.id == 4

    aplicacao = Aplicacao(superficie, projeto_temporario)
    clicar_botao(aplicacao, "Selecionar Fase")
    assert aplicacao.cartoes[3].situacao == "Disponível"
    clicar(aplicacao, aplicacao.cartoes[3].botao.area.center)

    rede_otima = [(0, 1), (0, 4), (2, 4), (2, 10), (3, 5), (3, 8), (4, 5), (4, 7), (5, 6), (5, 11), (6, 9)]
    com_desvio = [(0, 7)] + [cabo for cabo in rede_otima if cabo != (4, 7)]
    conectar(aplicacao, com_desvio)
    assert aplicacao.tela_atual == "resultado"
    assert aplicacao.jogo.resultado.custo_jogador == 115
    assert aplicacao.jogo.resultado.estrelas == 2
    assert "Próxima fase" not in [botao.texto for botao in aplicacao.botoes]
    clicar_botao(aplicacao, "Repetir fase")
    conectar(aplicacao, reversed(rede_otima))
    assert aplicacao.tela_atual == "resultado"

    reaberto = Aplicacao(superficie, projeto_temporario)
    registro = reaberto.progresso.obter(4)
    assert registro.concluida
    assert (registro.melhor_custo, registro.melhor_pontuacao, registro.estrelas) == (108, 1000, 3)
    clicar_botao(reaberto, "Jogar")
    assert reaberto.tela_atual == "selecao"
    assert reaberto.cartoes[3].situacao == "Concluída" and reaberto.cartoes[3].estrelas == 3
    assert reaberto.cartoes[4].situacao == "Em breve"
    clicar(reaberto, reaberto.cartoes[4].botao.area.center)
    assert reaberto.jogo is None


def test_campanha_com_progresso_anterior_e_repeticao(projeto_temporario, superficie, monkeypatch):
    pasta_fases = projeto_temporario / "dados" / "fases"
    for nome in ["fase_02.json", "fase_03.json", "fase_04.json", "fase_05.json"]:
        copyfile(RAIZ_PROJETO / "dados" / "fases" / nome, pasta_fases / nome)

    caminho_progresso = projeto_temporario / "progresso.json"
    registros_anteriores = {}
    for numero, custo in [(1, 46), (2, 79), (3, 74)]:
        registros_anteriores[str(numero)] = {
            "concluida": True, "melhor_pontuacao": 1000, "melhor_custo": custo, "estrelas": 3,
        }
    caminho_progresso.write_text(json.dumps({"fases": registros_anteriores}), encoding="utf-8")

    carregar_fase_real = fases.carregar_fase

    def carregar_fase_existente(caminho):
        assert Path(caminho).is_file()  # Falharia se tentasse carregar a fase 6.
        return carregar_fase_real(caminho)

    monkeypatch.setattr(fases, "carregar_fase", carregar_fase_existente)
    aplicacao = Aplicacao(superficie, projeto_temporario)
    assert aplicacao.progresso.pontuacao_total == 3000
    assert not aplicacao.progresso.campanha_concluida
    clicar_botao(aplicacao, "Selecionar Fase")
    assert [cartao.situacao for cartao in aplicacao.cartoes] == ["Concluída"] * 3 + ["Disponível", "Bloqueada"]
    assert aplicacao.cartoes[4].nome == "Rede da Cidade"
    clicar(aplicacao, aplicacao.cartoes[4].botao.area.center)
    assert aplicacao.jogo is None

    clicar(aplicacao, aplicacao.cartoes[3].botao.area.center)
    conectar(aplicacao, [(0, 1), (0, 4), (2, 4), (2, 10), (3, 5), (3, 8), (4, 5), (4, 7), (5, 6), (5, 11), (6, 9)])
    assert not aplicacao.progresso.campanha_concluida
    clicar_botao(aplicacao, "Próxima fase")
    assert aplicacao.jogo.fase.id == 5

    aplicacao = Aplicacao(superficie, projeto_temporario)
    clicar_botao(aplicacao, "Jogar")
    assert aplicacao.jogo.fase.id == 5
    rede_otima = [(1, 6), (2, 7), (4, 7), (0, 1), (2, 10), (5, 9), (6, 11),
                  (5, 6), (8, 13), (4, 12), (6, 7), (7, 8), (3, 10)]
    alternativa = [cabo for cabo in rede_otima if cabo not in ((1, 6), (2, 7), (3, 10))]
    alternativa.extend([(2, 5), (3, 6), (0, 5)])
    conectar(aplicacao, alternativa)
    assert aplicacao.tela_atual == "resultado"
    assert aplicacao.jogo.resultado.custo_jogador == 123
    assert aplicacao.jogo.resultado.estrelas == 2
    assert aplicacao.progresso.pontuacao_total == 4992
    assert aplicacao.progresso.campanha_concluida
    assert [botao.texto for botao in aplicacao.botoes] == [
        "Repetir fase", "Voltar à seleção de fases", "Menu principal",
    ]

    clicar_botao(aplicacao, "Repetir fase")
    conectar(aplicacao, reversed(rede_otima))
    assert aplicacao.jogo.resultado.custo_jogador == 122
    clicar_botao(aplicacao, "Repetir fase")
    conectar(aplicacao, alternativa)
    clicar_botao(aplicacao, "Voltar à seleção de fases")
    assert all(cartao.botao.acao is not None and cartao.situacao == "Concluída" for cartao in aplicacao.cartoes)
    assert aplicacao.progresso.pontuacao_total == 5000

    dados_salvos = json.loads(caminho_progresso.read_text(encoding="utf-8"))
    assert dados_salvos["campanha_concluida"] is True
    assert all(dados_salvos["fases"][numero] == registro for numero, registro in registros_anteriores.items())
    reaberto = Aplicacao(superficie, projeto_temporario)
    assert reaberto.progresso.campanha_concluida
    assert reaberto.progresso.pontuacao_total == 5000
    registro_final = reaberto.progresso.obter(5)
    assert (registro_final.melhor_custo, registro_final.melhor_pontuacao, registro_final.estrelas) == (122, 1000, 3)
    clicar_botao(reaberto, "Jogar")
    assert reaberto.tela_atual == "selecao"
    clicar(reaberto, reaberto.cartoes[0].botao.area.center)
    assert reaberto.jogo.fase.id == 1


@pytest.mark.parametrize("conteudo", ["{", "[]", '{"fases": {"1": false}}'])
def test_progresso_corrompido_pode_ser_regravado(tmp_path, conteudo):
    caminho = tmp_path / "progresso.json"
    caminho.write_text(conteudo, encoding="utf-8")
    progresso = Progresso(caminho)
    assert progresso.fase_desbloqueada(1)
    assert not progresso.fase_desbloqueada(2)
    assert progresso.registrar_conclusao(1, avaliar_resultado(46, 46))
    assert Progresso(caminho).fase_desbloqueada(2)


def test_maximizar_abre_tela_cheia_e_mantem_a_partida(projeto_temporario, superficie):
    aplicacao = Aplicacao(superficie, projeto_temporario)
    aplicacao.tratar_evento(pygame.event.Event(pygame.WINDOWMAXIMIZED))
    assert pygame.display.get_surface().get_flags() & pygame.FULLSCREEN
    assert aplicacao.superficie.get_size() == (LARGURA_TELA, ALTURA_TELA)

    area = aplicacao.area_jogo

    def clicar_em_tela_cheia(posicao):
        x, y = posicao
        clicar(aplicacao, (area.x + round(x * area.width / LARGURA_TELA),
                           area.y + round(y * area.height / ALTURA_TELA)))

    jogar = next(botao for botao in aplicacao.botoes if botao.texto == "Jogar")
    clicar_em_tela_cheia(jogar.area.center)
    jogo = aplicacao.jogo
    assert jogo is not None
    clicar_em_tela_cheia(jogo.fase.obter_posicao(0))
    clicar_em_tela_cheia(jogo.fase.obter_posicao(2))
    assert jogo.gasto == 10

    aplicacao.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11))
    assert not pygame.display.get_surface().get_flags() & pygame.FULLSCREEN
    assert pygame.display.get_surface().get_flags() & pygame.RESIZABLE
    assert aplicacao.tela_atual == "partida"
    assert aplicacao.jogo is jogo and jogo.gasto == 10


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
