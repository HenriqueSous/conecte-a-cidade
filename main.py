"""
Ponto de entrada do jogo Conecte a Cidade.
Inicia o Pygame, carrega a Fase 1 e executa o loop principal de eventos a 60 FPS.
"""

import sys
import pygame

from src.fases import carregar_fase, obter_caminho_fase
from src.jogo import Jogo
from src.interface import RenderizadorJogo

LARGURA_TELA = 1000
ALTURA_TELA = 680
FPS = 60


def main() -> None:
    # Inicialização do Pygame
    pygame.init()
    pygame.display.set_caption("Conecte a Cidade — Fase 1 (Tutorial)")
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    relogio = pygame.time.Clock()

    # Carregamento da Fase 1
    caminho_fase1 = obter_caminho_fase(1)
    fase = carregar_fase(caminho_fase1)
    jogo = Jogo(fase)
    renderizador = RenderizadorJogo(LARGURA_TELA, ALTURA_TELA)

    rodando = True
    while rodando:
        pos_mouse = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif evento.key == pygame.K_z:
                    jogo.desfazer()
                elif evento.key == pygame.K_r:
                    jogo.reiniciar()

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:  # Botão esquerdo: selecionar ou ligar
                    casa_clicada = renderizador.obter_casa_sob_mouse(jogo, pos_mouse)
                    if casa_clicada is not None:
                        jogo.selecionar_casa(casa_clicada)
                    else:
                        jogo.cancelar_selecao()
                elif evento.button == 3:  # Botão direito: cancela seleção
                    jogo.cancelar_selecao()

        # Renderização do jogo
        renderizador.desenhar(tela, jogo, pos_mouse)
        pygame.display.flip()
        relogio.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
