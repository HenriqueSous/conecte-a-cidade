"""
Desenha o menu, a seleção de fases, as instruções e a pausa usando Pygame.
Os botões compartilham a mesma área para desenho, hover e clique.
"""

from collections.abc import Callable
from dataclasses import dataclass
from math import cos, pi, sin

import pygame

from src.interface import (
    COR_BORDA_HUD,
    COR_CABO_NORMAL,
    COR_FUNDO,
    COR_HUD_FUNDO,
    COR_TEXTO_CLARO,
    COR_TEXTO_DESTAQUE,
    COR_TEXTO_MUTED,
)
from src.progresso import PONTOS_MAXIMOS_CAMPANHA

COR_PAINEL = (24, 35, 53)
COR_HOVER = (27, 54, 72)
COR_REALCE = (20, 48, 65)
COR_DESABILITADO = (19, 27, 43)


@dataclass
class Botao:
    area: pygame.Rect
    texto: str
    acao: Callable[[], None] | None
    destaque: bool = False


@dataclass
class CartaoFase:
    botao: Botao
    nome: str
    situacao: str
    estrelas: int


class Telas:
    """Elementos gráficos das telas que cercam a partida."""

    def __init__(self, largura: int, altura: int) -> None:
        self.centro_x = largura // 2
        self.centro_y = altura // 2
        self.fonte_titulo = pygame.font.SysFont("Arial", 62, bold=True)
        self.fonte_secao = pygame.font.SysFont("Arial", 36, bold=True)
        self.fonte_botao = pygame.font.SysFont("Arial", 20, bold=True)
        self.fonte_texto = pygame.font.SysFont("Arial", 20)
        self.fonte_pequena = pygame.font.SysFont("Arial", 16)
        self.fundo = self._criar_fundo(largura, altura)
        self.sombra = pygame.Surface((largura, altura), pygame.SRCALPHA)
        self.sombra.fill((10, 15, 25, 210))

    def organizar_botoes(
        self, acoes: list[tuple[str, Callable[[], None]]], y: int,
        largura: int = 320, altura: int = 48, colunas: int = 1,
        primeiro_em_destaque: bool = False,
    ) -> list[Botao]:
        """Centraliza os botões de cada linha, inclusive se a última estiver incompleta."""
        espacamento = 14
        botoes = []
        for indice, (texto, acao) in enumerate(acoes):
            linha, coluna = divmod(indice, colunas)
            na_linha = min(colunas, len(acoes) - linha * colunas)
            largura_linha = na_linha * (largura + espacamento) - espacamento
            x = self.centro_x - largura_linha // 2 + coluna * (largura + espacamento)
            topo = y + linha * (altura + espacamento)
            area = pygame.Rect(x, topo, largura, altura)
            botoes.append(Botao(area, texto, acao, primeiro_em_destaque and indice == 0))
        return botoes

    def criar_cartao_fase(
        self, numero: int, nome: str, situacao: str, estrelas: int,
        acao: Callable[[], None] | None,
    ) -> CartaoFase:
        area = pygame.Rect(self.centro_x - 380, 161 + (numero - 1) * 75, 760, 63)
        return CartaoFase(Botao(area, f"Fase {numero}", acao), nome, situacao, estrelas)

    def desenhar_menu(self, superficie: pygame.Surface) -> None:
        superficie.blit(self.fundo, (0, 0))
        self._desenhar_casa(superficie, self.centro_x, 123, COR_TEXTO_DESTAQUE)
        self._texto(superficie, "CONECTE A CIDADE", self.fonte_titulo, (self.centro_x, 197))
        self._detalhe_titulo(superficie, 247)

    def desenhar_selecao(
        self, superficie: pygame.Surface, cartoes: list[CartaoFase], pos_mouse: tuple[int, int],
        pontuacao_total: int,
    ) -> None:
        superficie.blit(self.fundo, (0, 0))
        self._texto(superficie, "Selecionar Fase", self.fonte_secao, (self.centro_x, 83))
        self._detalhe_titulo(superficie, 121)
        total = f"Pontuação total: {pontuacao_total} / {PONTOS_MAXIMOS_CAMPANHA}"
        self._texto(superficie, total, self.fonte_pequena, (self.centro_x, 142), COR_TEXTO_DESTAQUE)
        for cartao in cartoes:
            self._desenhar_cartao_fase(superficie, cartao, pos_mouse)

    def desenhar_instrucoes(self, superficie: pygame.Surface) -> None:
        superficie.blit(self.fundo, (0, 0))
        self._texto(superficie, "Como Jogar", self.fonte_secao, (self.centro_x, 124))
        self._detalhe_titulo(superficie, 164)
        painel = pygame.Rect(self.centro_x - 360, 204, 720, 278)
        self._painel(superficie, painel, COR_PAINEL, COR_BORDA_HUD)
        self._texto(superficie, "Ligue todas as casas à central dentro do orçamento.",
                    self.fonte_botao, (self.centro_x, 249), COR_TEXTO_DESTAQUE)
        controles = [
            "Clique em duas casas para criar ou remover um cabo.",
            "Clique no fundo ou use o botão direito para cancelar a seleção.",
            "Z desfaz a última ação e R reinicia a fase.",
            "ESC abre o menu de pausa.",
            "Use Maximizar ou F11 para entrar em tela cheia. F11 volta à janela.",
        ]
        for indice, texto in enumerate(controles):
            self._texto(superficie, texto, self.fonte_texto, (self.centro_x, 303 + indice * 37))

    def desenhar_pausa(self, superficie: pygame.Surface) -> None:
        superficie.blit(self.sombra, (0, 0))
        painel = pygame.Rect(self.centro_x - 222, self.centro_y - 164, 444, 328)
        self._painel(superficie, painel, COR_HUD_FUNDO, COR_CABO_NORMAL)
        self._texto(superficie, "Pausa", self.fonte_secao, (self.centro_x, self.centro_y - 111))

    def desenhar_aviso_progresso(self, superficie: pygame.Surface) -> None:
        self._texto(superficie, "O progresso desta partida não pôde ser salvo.",
                    self.fonte_pequena, (self.centro_x, self.centro_y + 200), COR_TEXTO_DESTAQUE)

    def desenhar_botoes(
        self, superficie: pygame.Surface, botoes: list[Botao], pos_mouse: tuple[int, int]
    ) -> None:
        for botao in botoes:
            self._desenhar_base_botao(superficie, botao, pos_mouse)
            self._texto(superficie, botao.texto, self.fonte_botao, botao.area.center)

    def _desenhar_cartao_fase(
        self, superficie: pygame.Surface, cartao: CartaoFase, pos_mouse: tuple[int, int]
    ) -> None:
        botao = cartao.botao
        self._desenhar_base_botao(superficie, botao, pos_mouse)
        x, y = botao.area.left, botao.area.centery
        cor_numero = COR_CABO_NORMAL if botao.acao is not None else COR_TEXTO_MUTED
        self._texto(superficie, botao.texto, self.fonte_botao, (x + 56, y), cor_numero)
        nome = self.fonte_texto.render(cartao.nome, True, COR_TEXTO_CLARO)
        largura_nome = min(nome.get_width(), 330)
        superficie.blit(nome, (x + 128, y - nome.get_height() // 2),
                        pygame.Rect(0, 0, largura_nome, nome.get_height()))
        for indice in range(3):
            self._desenhar_estrela(superficie, x + 491 + indice * 26, y, indice < cartao.estrelas)
        cor_situacao = COR_TEXTO_DESTAQUE if cartao.situacao == "Concluída" else cor_numero
        self._texto(superficie, cartao.situacao, self.fonte_pequena, (x + 652, y), cor_situacao)

    def _desenhar_base_botao(
        self, superficie: pygame.Surface, botao: Botao, pos_mouse: tuple[int, int]
    ) -> None:
        fundo, borda = COR_PAINEL, COR_BORDA_HUD
        if botao.acao is None:
            fundo = COR_DESABILITADO
        elif botao.area.collidepoint(pos_mouse):
            fundo, borda = COR_HOVER, COR_CABO_NORMAL
        elif botao.destaque:
            fundo, borda = COR_REALCE, COR_CABO_NORMAL
        self._painel(superficie, botao.area, fundo, borda)

    def _criar_fundo(self, largura: int, altura: int) -> pygame.Surface:
        fundo = pygame.Surface((largura, altura))
        fundo.fill(COR_FUNDO)
        cor_conexao = (28, 58, 79)
        for x in range(20, largura, 40):
            for y in range(20, altura, 40):
                pygame.draw.circle(fundo, (33, 44, 64), (x, y), 1)

        rede = [(26, 410), (77, 410), (77, 554), (151, 554), (195, 614), (279, 614)]
        for casas in (rede, [(largura - x, altura - y) for x, y in rede]):
            pygame.draw.lines(fundo, cor_conexao, False, casas, width=2)
            for x, y in casas:
                pygame.draw.circle(fundo, cor_conexao, (x, y), 4)
            for indice in (1, 3, 5):
                x, y = casas[indice]
                self._desenhar_casa(fundo, x, y, (56, 92, 111))
        return fundo

    def _detalhe_titulo(self, superficie: pygame.Surface, y: int) -> None:
        x = self.centro_x
        pygame.draw.line(superficie, COR_CABO_NORMAL, (x - 43, y), (x + 43, y), width=2)
        pygame.draw.circle(superficie, COR_TEXTO_DESTAQUE, (x, y), 4)

    @staticmethod
    def _desenhar_casa(superficie: pygame.Surface, x: int, y: int, cor: tuple[int, int, int]) -> None:
        pygame.draw.circle(superficie, COR_FUNDO, (x, y), 19)
        pontos = [(x - 12, y - 2), (x, y - 12), (x + 12, y - 2)]
        pygame.draw.lines(superficie, cor, False, pontos, width=2)
        pygame.draw.rect(superficie, cor, (x - 9, y - 2, 19, 13), width=2, border_radius=2)
        pygame.draw.rect(superficie, cor, (x - 2, y + 4, 5, 7), width=1)

    @staticmethod
    def _desenhar_estrela(superficie: pygame.Surface, x: int, y: int, preenchida: bool) -> None:
        pontos = []
        for indice in range(10):
            angulo = indice * pi / 5 - pi / 2
            raio = 10 if indice % 2 == 0 else 4.5
            pontos.append((round(x + raio * cos(angulo)), round(y + raio * sin(angulo))))
        cor = COR_TEXTO_DESTAQUE if preenchida else COR_TEXTO_MUTED
        pygame.draw.polygon(superficie, cor, pontos, width=0 if preenchida else 1)

    @staticmethod
    def _painel(superficie: pygame.Surface, area: pygame.Rect, fundo: tuple, borda: tuple) -> None:
        pygame.draw.rect(superficie, fundo, area, border_radius=9)
        pygame.draw.rect(superficie, borda, area, width=1, border_radius=9)

    @staticmethod
    def _texto(
        superficie: pygame.Surface, texto: str, fonte: pygame.font.Font,
        centro: tuple[int, int], cor: tuple = COR_TEXTO_CLARO,
    ) -> None:
        imagem = fonte.render(texto, True, cor)
        superficie.blit(imagem, imagem.get_rect(center=centro))
