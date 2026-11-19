"""
Interface visual e renderização gráfica do jogo Conecte a Cidade usando pygame-ce.
Desenha o mapa, cabos possíveis, cabos construídos, casas, efeitos de brilho,
HUD superior e a tela de resultado.
"""

import math
from typing import Optional, Tuple
import pygame

from src.jogo import Jogo
from src.fases import Casa

# Paleta de cores do jogo
COR_FUNDO = (18, 24, 38)
COR_HUD_FUNDO = (12, 16, 26)
COR_BORDA_HUD = (35, 48, 75)
COR_TEXTO_CLARO = (235, 240, 250)
COR_TEXTO_MUTED = (140, 155, 180)
COR_TEXTO_DESTAQUE = (255, 215, 80)
COR_ALERTA = (255, 75, 75)

COR_LIGACAO_POSSIVEL = (60, 75, 105)
COR_CABO_NORMAL = (30, 200, 255)
COR_CABO_REDUNDANTE = (255, 140, 20)
COR_PREVIA_VALIDA = (255, 255, 255)
COR_PREVIA_INVALIDA = (255, 60, 60)

COR_CASA_DESCONECTADA = (70, 85, 110)
COR_CASA_LIGADA = (255, 205, 50)
COR_CASA_CENTRAL = (255, 90, 60)
COR_HALO_BRILHO = (255, 215, 80, 45)


class RenderizadorJogo:
    """Gerencia o desenho de todos os elementos gráficos do jogo na tela."""

    def __init__(self, largura: int = 1000, altura: int = 680) -> None:
        self.largura = largura
        self.altura = altura
        self.altura_hud = 65

        # Inicialização das fontes
        pygame.font.init()
        self.fonte_titulo = pygame.font.SysFont("Arial", 20, bold=True)
        self.fonte_normal = pygame.font.SysFont("Arial", 15)
        self.fonte_pequena = pygame.font.SysFont("Arial", 12, bold=True)
        self.fonte_destaque = pygame.font.SysFont("Arial", 26, bold=True)

        self.raio_casa = 22

    def desenhar(self, superficie: pygame.Surface, jogo: Jogo, pos_mouse: Tuple[int, int]) -> None:
        """Desenha o quadro completo do jogo."""
        superficie.fill(COR_FUNDO)

        # 1. Desenha as conexões possíveis (fundo)
        self._desenhar_ligacoes_possiveis(superficie, jogo)

        # 2. Desenha os cabos já construídos pelo jogador
        self._desenhar_cabos_construidos(superficie, jogo)

        # 3. Desenha linha de prévia com mouse se houver casa selecionada
        if jogo.casa_selecionada is not None and not jogo.vitoria:
            self._desenhar_previa_mouse(superficie, jogo, pos_mouse)

        # 4. Desenha as casas e a central
        self._desenhar_casas(superficie, jogo)

        # 5. Desenha o HUD no topo
        self._desenhar_hud(superficie, jogo)

        # 6. Se o jogador venceu, desenha painel de vitória
        if jogo.vitoria and jogo.resultado:
            self._desenhar_painel_vitoria(superficie, jogo)

    def obter_casa_sob_mouse(self, jogo: Jogo, pos_mouse: Tuple[int, int]) -> Optional[int]:
        """Retorna o ID da casa sob a coordenada do mouse, se houver."""
        mx, my = pos_mouse
        for casa in jogo.fase.casas:
            if math.dist((mx, my), (casa.x, casa.y)) <= self.raio_casa + 4:
                return casa.id
        return None

    def _desenhar_ligacoes_possiveis(self, sup: pygame.Surface, jogo: Jogo) -> None:
        """Desenha as linhas finas cinza com os custos das conexões possíveis."""
        for lig in jogo.fase.ligacoes:
            u_can, v_can = (min(lig.de, lig.para), max(lig.de, lig.para))
            # Se já está construído, pula (será desenhado com destaque depois)
            if (u_can, v_can) in jogo.cabos_construidos:
                continue

            p1 = jogo.fase.obter_posicao(u_can)
            p2 = jogo.fase.obter_posicao(v_can)
            pygame.draw.line(sup, COR_LIGACAO_POSSIVEL, p1, p2, width=2)
            self._desenhar_rotulo_custo(sup, p1, p2, str(lig.custo), ativo=False)

    def _desenhar_cabos_construidos(self, sup: pygame.Surface, jogo: Jogo) -> None:
        """Desenha os cabos instalados com espessura e cores indicativas."""
        for u, v in jogo.cabos_construidos:
            p1 = jogo.fase.obter_posicao(u)
            p2 = jogo.fase.obter_posicao(v)
            custo = jogo.fase.grafo.custo(u, v) or 0

            # Laranja se redundante (forma ciclo), Azul ciano se normal
            redundante = (u, v) in jogo.cabos_redundantes
            cor = COR_CABO_REDUNDANTE if redundante else COR_CABO_NORMAL
            pygame.draw.line(sup, cor, p1, p2, width=5)
            self._desenhar_rotulo_custo(sup, p1, p2, str(custo), ativo=True, redundante=redundante)

    def _desenhar_previa_mouse(self, sup: pygame.Surface, jogo: Jogo, pos_mouse: Tuple[int, int]) -> None:
        """Desenha a linha tracejada ou sólida indicativa da conexão em andamento."""
        assert jogo.casa_selecionada is not None
        p_origem = jogo.fase.obter_posicao(jogo.casa_selecionada)
        casa_alvo = self.obter_casa_sob_mouse(jogo, pos_mouse)

        if casa_alvo is not None and casa_alvo != jogo.casa_selecionada:
            p_destino = jogo.fase.obter_posicao(casa_alvo)
            permitido, _ = jogo.pode_construir(jogo.casa_selecionada, casa_alvo)
            cor = COR_PREVIA_VALIDA if permitido else COR_PREVIA_INVALIDA
            pygame.draw.line(sup, cor, p_origem, p_destino, width=3)
            custo = jogo.fase.grafo.custo(jogo.casa_selecionada, casa_alvo)
            if custo is not None:
                self._desenhar_rotulo_custo(sup, p_origem, p_destino, str(custo), ativo=False)
        else:
            # Segue o cursor
            pygame.draw.line(sup, (160, 180, 210), p_origem, pos_mouse, width=2)

    def _desenhar_casas(self, sup: pygame.Surface, jogo: Jogo) -> None:
        """Desenha os ícones das casas com iluminação e destaque da central."""
        superficie_brilho = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)

        for casa in jogo.fase.casas:
            cx, cy = int(casa.x), int(casa.y)
            ligada = casa.id in jogo.casas_na_rede
            selecionada = (casa.id == jogo.casa_selecionada)

            # 1. Halo suave de luz para casas na rede
            if ligada:
                pygame.draw.circle(superficie_brilho, COR_HALO_BRILHO, (cx, cy), self.raio_casa + 12)

            # 2. Cor do corpo da casa
            if casa.central:
                cor_corpo = COR_CASA_CENTRAL
            elif ligada:
                cor_corpo = COR_CASA_LIGADA
            else:
                cor_corpo = COR_CASA_DESCONECTADA

            # Desenha círculo base
            pygame.draw.circle(sup, cor_corpo, (cx, cy), self.raio_casa)

            # Borda externa
            cor_borda = (255, 255, 255) if selecionada else (25, 30, 45)
            largura_borda = 4 if selecionada else 2
            pygame.draw.circle(sup, cor_borda, (cx, cy), self.raio_casa, width=largura_borda)

            # Ícone interno geométrico
            if casa.central:
                # Ícone de torre / raio na central
                self._desenhar_icone_central(sup, cx, cy)
            else:
                # Telhado e corpo simples de casinha
                self._desenhar_icone_casa(sup, cx, cy, ligada)

            # Rótulo com o número da casa
            txt_id = self.fonte_pequena.render(str(casa.id), True, (255, 255, 255))
            rect_txt = txt_id.get_rect(center=(cx, cy + self.raio_casa + 12))
            sup.blit(txt_id, rect_txt)

        sup.blit(superficie_brilho, (0, 0))

    def _desenhar_icone_central(self, sup: pygame.Surface, cx: int, cy: int) -> None:
        """Desenha um símbolo geométrico de torre/raio na central."""
        pontos_raio = [
            (cx - 2, cy - 10),
            (cx + 6, cy - 10),
            (cx + 1, cy - 1),
            (cx + 7, cy - 1),
            (cx - 4, cy + 10),
            (cx - 1, cy + 2),
            (cx - 6, cy + 2)
        ]
        pygame.draw.polygon(sup, (255, 255, 255), pontos_raio)

    def _desenhar_icone_casa(self, sup: pygame.Surface, cx: int, cy: int, ligada: bool) -> None:
        """Desenha um ícone simples de telhado e parede."""
        cor = (40, 45, 60) if ligada else (200, 210, 230)
        # Telhado triangular
        pontos_telhado = [(cx, cy - 9), (cx - 8, cy - 1), (cx + 8, cy - 1)]
        pygame.draw.polygon(sup, cor, pontos_telhado)
        # Corpo retangular
        pygame.draw.rect(sup, cor, (cx - 6, cy - 1, 12, 8))

    def _desenhar_rotulo_custo(
        self,
        sup: pygame.Surface,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        texto: str,
        ativo: bool,
        redundante: bool = False
    ) -> None:
        """Desenha a caixinha com o valor numérico do custo na metade da aresta."""
        mx = int((p1[0] + p2[0]) / 2)
        my = int((p1[1] + p2[1]) / 2)

        txt = self.fonte_pequena.render(texto, True, (255, 255, 255))
        largura_box = max(20, txt.get_width() + 8)
        altura_box = 16
        rect_box = pygame.Rect(mx - largura_box // 2, my - altura_box // 2, largura_box, altura_box)

        if ativo:
            cor_bg = (180, 80, 10) if redundante else (15, 110, 150)
            cor_borda = COR_CABO_REDUNDANTE if redundante else COR_CABO_NORMAL
        else:
            cor_bg = (24, 32, 48)
            cor_borda = (50, 65, 95)

        pygame.draw.rect(sup, cor_bg, rect_box, border_radius=4)
        pygame.draw.rect(sup, cor_borda, rect_box, width=1, border_radius=4)
        rect_txt = txt.get_rect(center=rect_box.center)
        sup.blit(txt, rect_txt)

    def _desenhar_hud(self, sup: pygame.Surface, jogo: Jogo) -> None:
        """Renderiza a barra superior de informações e controles."""
        rect_hud = pygame.Rect(0, 0, self.largura, self.altura_hud)
        pygame.draw.rect(sup, COR_HUD_FUNDO, rect_hud)
        pygame.draw.line(sup, COR_BORDA_HUD, (0, self.altura_hud), (self.largura, self.altura_hud), 2)

        # 1. Título da fase
        txt_fase = self.fonte_titulo.render(f"Fase {jogo.fase.id}: {jogo.fase.nome}", True, COR_TEXTO_CLARO)
        sup.blit(txt_fase, (20, 10))

        # 2. Conexões das casas (x / n)
        n_total = jogo.fase.grafo.n
        n_conectadas = len(jogo.casas_na_rede)
        txt_rede = self.fonte_normal.render(f"Casas na rede: {n_conectadas}/{n_total}", True, COR_TEXTO_MUTED)
        sup.blit(txt_rede, (20, 36))

        # 3. Orçamento e Gastos
        restante = jogo.orcamento_restante
        cor_restante = COR_ALERTA if restante <= 10 or jogo.beco_sem_saida else COR_TEXTO_DESTAQUE
        texto_orcamento = f"Gasto: {jogo.gasto} / {jogo.fase.orcamento}  (Restante: {restante})"
        txt_orc = self.fonte_normal.render(texto_orcamento, True, cor_restante)
        rect_orc = txt_orc.get_rect(topright=(self.largura - 20, 10))
        sup.blit(txt_orc, rect_orc)

        # 4. Mensagem de Feedback de uma linha
        cor_feedback = COR_ALERTA if jogo.beco_sem_saida else COR_TEXTO_MUTED
        txt_msg = self.fonte_pequena.render(jogo.mensagem_feedback, True, cor_feedback)
        sup.blit(txt_msg, (280, 14))

        # 5. Dica de comandos
        dica = "[Clique] Conectar/Remover  |  [Z] Desfazer  |  [R] Reiniciar  |  [ESC] Sair"
        txt_dica = self.fonte_pequena.render(dica, True, (110, 125, 150))
        sup.blit(txt_dica, (280, 38))

    def _desenhar_painel_vitoria(self, sup: pygame.Surface, jogo: Jogo) -> None:
        """Exibe o modal com a pontuação e estrelas conquistadas."""
        assert jogo.resultado is not None
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 210))
        sup.blit(overlay, (0, 0))

        # Caixa do painel
        largura_p, altura_p = 480, 300
        cx, cy = self.largura // 2, self.altura // 2
        rect_painel = pygame.Rect(cx - largura_p // 2, cy - altura_p // 2, largura_p, altura_p)
        pygame.draw.rect(sup, (24, 32, 50), rect_painel, border_radius=12)
        pygame.draw.rect(sup, COR_CABO_NORMAL, rect_painel, width=2, border_radius=12)

        # Título
        txt_vitoria = self.fonte_destaque.render("FASE CONCLUÍDA!", True, COR_TEXTO_DESTAQUE)
        sup.blit(txt_vitoria, txt_vitoria.get_rect(center=(cx, cy - 100)))

        # Estrelas (★)
        estrelas_str = "★ " * jogo.resultado.estrelas + "☆ " * (3 - jogo.resultado.estrelas)
        txt_estrelas = self.fonte_destaque.render(estrelas_str.strip(), True, (255, 220, 40))
        sup.blit(txt_estrelas, txt_estrelas.get_rect(center=(cx, cy - 60)))

        # Estatísticas
        res = jogo.resultado
        linhas = [
            f"Seu Custo: {res.custo_jogador}  |  Solução Ideal (Par): {res.par}",
            f"Aproveitamento: {res.aproveitamento:.1f}%",
            f"Pontuação: {res.pontos} pontos"
        ]
        for idx, linha in enumerate(linhas):
            txt_linha = self.fonte_normal.render(linha, True, COR_TEXTO_CLARO)
            sup.blit(txt_linha, txt_linha.get_rect(center=(cx, cy - 10 + idx * 26)))

        # Ações
        txt_acoes = self.fonte_pequena.render("Pressione [R] para jogar novamente ou [ESC] para fechar", True, COR_TEXTO_MUTED)
        sup.blit(txt_acoes, txt_acoes.get_rect(center=(cx, cy + 105)))
