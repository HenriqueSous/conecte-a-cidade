"""
Ponto de entrada do Conecte a Cidade.
Inicia o Pygame e controla a navegação entre o menu e a partida.
"""

from functools import partial
from pathlib import Path

import pygame
from pygame._sdl2 import Window

from src.fases import TOTAL_FASES, carregar_catalogo_fases
from src.interface import RenderizadorJogo
from src.jogo import Jogo
from src.progresso import Progresso
from src.telas import CartaoFase, Telas

LARGURA_TELA = 1000
ALTURA_TELA = 680
TAMANHO_JOGO = (LARGURA_TELA, ALTURA_TELA)
FPS = 60
RAIZ_PROJETO = Path(__file__).resolve().parent


class Aplicacao:
    """Encaminha os eventos para a tela atual e salva a vitória da partida."""

    def __init__(self, superficie: pygame.Surface, pasta_projeto: Path = RAIZ_PROJETO) -> None:
        self.janela = superficie
        self.tamanho_janela = superficie.get_size()
        self._ajustar_area_jogo()
        self.fases = carregar_catalogo_fases(str(pasta_projeto))
        self.progresso = Progresso(pasta_projeto / "progresso.json")
        self.telas = Telas(LARGURA_TELA, ALTURA_TELA)
        self.renderizador = RenderizadorJogo(LARGURA_TELA, ALTURA_TELA)
        self.jogo: Jogo | None = None
        self.cartoes: list[CartaoFase] = []
        self.rodando = True
        self.progresso_salvo = True
        self._abrir_menu()

    def executar(self) -> None:
        relogio = pygame.time.Clock()
        while self.rodando:
            for evento in pygame.event.get():
                self.tratar_evento(evento)
                if not self.rodando:
                    return
            self.desenhar(self._posicao_no_jogo(pygame.mouse.get_pos()))
            if self.superficie is not self.janela:
                self.janela.fill((0, 0, 0))
                pygame.transform.smoothscale(
                    self.superficie, self.area_jogo.size, self.janela.subsurface(self.area_jogo)
                )
            pygame.display.flip()
            relogio.tick(FPS)

    def _abrir_menu(self) -> None:
        self.jogo = None
        self.tela_atual = "menu"
        self.botoes = self.telas.organizar_botoes([
            ("Jogar", self._jogar),
            ("Selecionar Fase", self._abrir_selecao),
            ("Como Jogar", self._abrir_instrucoes),
            ("Sair", self._sair),
        ], y=287, primeiro_em_destaque=True)

    def _definir_tela_cheia(self, tela_cheia: bool) -> None:
        if tela_cheia:
            self.tamanho_janela = pygame.display.get_window_size()
            self.janela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.janela = pygame.display.set_mode(self.tamanho_janela, pygame.RESIZABLE)
        self._ajustar_area_jogo()

    def _ajustar_area_jogo(self) -> None:
        area_janela = self.janela.get_rect()
        self.area_jogo = pygame.Rect((0, 0), TAMANHO_JOGO).fit(area_janela)
        self.area_jogo.size = max(1, self.area_jogo.width), max(1, self.area_jogo.height)
        self.superficie = self.janela
        if area_janela.size != TAMANHO_JOGO:
            self.superficie = pygame.Surface(TAMANHO_JOGO).convert(self.janela)

    def _posicao_no_jogo(self, posicao: tuple[int, int]) -> tuple[int, int]:
        area = self.area_jogo
        x, y = posicao
        return ((x - area.x) * LARGURA_TELA // area.width,
                (y - area.y) * ALTURA_TELA // area.height)

    def _abrir_selecao(self) -> None:
        self.jogo = None
        self.tela_atual = "selecao"
        self.cartoes = [self._cartao_fase(numero) for numero in range(1, TOTAL_FASES + 1)]
        self.botoes = self.telas.organizar_botoes([("Voltar", self._abrir_menu)], y=565)

    def _cartao_fase(self, numero: int) -> CartaoFase:
        fase = self.fases.get(numero)
        registro = self.progresso.obter(numero)
        acao = None
        if fase is None:
            situacao = "Em breve"
        elif not self.progresso.fase_desbloqueada(numero):
            situacao = "Bloqueada"
        else:
            situacao = "Concluída" if registro.concluida else "Disponível"
            acao = partial(self._iniciar_fase, numero)
        nome = fase.nome if fase is not None else ""
        return self.telas.criar_cartao_fase(numero, nome, situacao, registro.estrelas, acao)

    def _abrir_instrucoes(self) -> None:
        self.tela_atual = "instrucoes"
        self.botoes = self.telas.organizar_botoes([("Voltar", self._abrir_menu)], y=532)

    def _fases_disponiveis(self) -> list[int]:
        return [numero for numero in self.fases if self.progresso.fase_desbloqueada(numero)]

    def _jogar(self) -> None:
        for numero in self._fases_disponiveis():
            if not self.progresso.obter(numero).concluida:
                self._iniciar_fase(numero)
                return
        self._abrir_selecao()

    def _iniciar_fase(self, numero: int) -> None:
        fase = self.fases.get(numero)
        if fase is not None and self.progresso.fase_desbloqueada(numero):
            self.jogo = Jogo(fase)
            self._continuar()

    def _continuar(self) -> None:
        self.tela_atual = "partida"
        self.botoes = []

    def _reiniciar(self) -> None:
        assert self.jogo is not None
        self.jogo.reiniciar()
        self._continuar()

    def _pausar(self) -> None:
        self.tela_atual = "pausa"
        self.botoes = self.telas.organizar_botoes([
            ("Continuar", self._continuar),
            ("Reiniciar fase", self._reiniciar),
            ("Voltar ao menu principal", self._abrir_menu),
        ], y=275, primeiro_em_destaque=True)

    def _exibir_resultado(self) -> None:
        assert self.jogo is not None and self.jogo.resultado is not None
        numero = self.jogo.fase.id
        self.progresso_salvo = self.progresso.registrar_conclusao(numero, self.jogo.resultado)
        self.tela_atual = "resultado"

        acoes = [
            ("Repetir fase", self._reiniciar),
            ("Voltar à seleção de fases", self._abrir_selecao),
            ("Menu principal", self._abrir_menu),
        ]
        proxima = next((fase for fase in self._fases_disponiveis() if fase > numero), None)
        if proxima is not None:
            acoes.insert(0, ("Próxima fase", partial(self._iniciar_fase, proxima)))
        self.botoes = self.telas.organizar_botoes(
            acoes, y=401, largura=260, altura=36, colunas=2, primeiro_em_destaque=True
        )

    def _sair(self) -> None:
        self.rodando = False

    def tratar_evento(self, evento: pygame.event.Event) -> None:
        if evento.type == pygame.QUIT:
            self._sair()
        elif evento.type == pygame.WINDOWMAXIMIZED and not self.janela.get_flags() & pygame.FULLSCREEN:
            # O SDL restaura a maximização ao sair da tela cheia se ela estiver ativa ao entrar.
            Window.from_display_module().restore()
            self._definir_tela_cheia(True)
        elif evento.type == pygame.WINDOWSIZECHANGED:
            self._ajustar_area_jogo()
        elif evento.type == pygame.KEYDOWN:
            self._tratar_tecla(evento.key)
        elif evento.type == pygame.MOUSEBUTTONDOWN and self.area_jogo.collidepoint(evento.pos):
            self._tratar_clique(evento.button, self._posicao_no_jogo(evento.pos))

    def _tratar_tecla(self, tecla: int) -> None:
        if tecla == pygame.K_F11:
            self._definir_tela_cheia(not self.janela.get_flags() & pygame.FULLSCREEN)
        elif tecla == pygame.K_ESCAPE:
            if self.tela_atual == "partida":
                self._pausar()
            elif self.tela_atual == "pausa":
                self._continuar()
            elif self.tela_atual == "resultado":
                self._abrir_selecao()
            elif self.tela_atual in ("selecao", "instrucoes"):
                self._abrir_menu()
        elif tecla == pygame.K_r and self.tela_atual in ("partida", "resultado"):
            self._reiniciar()
        elif tecla == pygame.K_z and self.tela_atual == "partida":
            assert self.jogo is not None
            self.jogo.desfazer()

    def _tratar_clique(self, botao_mouse: int, posicao: tuple[int, int]) -> None:
        if self.tela_atual == "partida":
            self._tratar_clique_partida(botao_mouse, posicao)
        elif botao_mouse == 1:
            botoes = self.botoes
            if self.tela_atual == "selecao":
                botoes = botoes + [cartao.botao for cartao in self.cartoes]
            for botao in botoes:
                if botao.acao is not None and botao.area.collidepoint(posicao):
                    botao.acao()
                    return

    def _tratar_clique_partida(self, botao_mouse: int, posicao: tuple[int, int]) -> None:
        assert self.jogo is not None
        if botao_mouse == 3:
            self.jogo.cancelar_selecao()
        elif botao_mouse == 1:
            casa = self.renderizador.obter_casa_sob_mouse(self.jogo, posicao)
            if casa is None:
                self.jogo.cancelar_selecao()
            else:
                self.jogo.selecionar_casa(casa)
                if self.jogo.vitoria:
                    self._exibir_resultado()

    def desenhar(self, pos_mouse: tuple[int, int]) -> None:
        if self.tela_atual == "menu":
            self.telas.desenhar_menu(self.superficie)
        elif self.tela_atual == "selecao":
            self.telas.desenhar_selecao(self.superficie, self.cartoes, pos_mouse, self.progresso.pontuacao_total)
        elif self.tela_atual == "instrucoes":
            self.telas.desenhar_instrucoes(self.superficie)
        elif self.jogo is not None:
            pontos_campanha = None
            if self.tela_atual == "resultado" and self.jogo.fase.id == TOTAL_FASES:
                pontos_campanha = self.progresso.pontuacao_total
            self.renderizador.desenhar(self.superficie, self.jogo, pos_mouse, pontos_campanha)
            if self.tela_atual == "pausa":
                self.telas.desenhar_pausa(self.superficie)
            elif self.tela_atual == "resultado" and not self.progresso_salvo:
                self.telas.desenhar_aviso_progresso(self.superficie)
        self.telas.desenhar_botoes(self.superficie, self.botoes, pos_mouse)


def main() -> None:
    pygame.init()
    try:
        pygame.display.set_caption("Conecte a Cidade")
        superficie = pygame.display.set_mode(TAMANHO_JOGO, pygame.RESIZABLE)
        Aplicacao(superficie).executar()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
