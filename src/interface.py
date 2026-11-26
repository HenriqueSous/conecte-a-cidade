"""
Interface visual e renderização gráfica do jogo Conecte a Cidade usando pygame-ce.
Desenha o mapa, cabos possíveis, cabos construídos, casas, efeitos de brilho,
HUD superior e a tela de resultado.
"""

import math
from pathlib import Path
from typing import Optional, Tuple
import pygame

from src.jogo import Jogo, MENSAGEM_CRUZAMENTO
from src.progresso import PONTOS_MAXIMOS_CAMPANHA

PASTA_ASSETS = Path(__file__).resolve().parents[1] / "assets" / "conecte_a_cidade_v1"

# Paleta de cores do jogo
COR_FUNDO = (18, 24, 38)
COR_HUD_FUNDO = (12, 16, 26)
COR_BORDA_HUD = (35, 48, 75)
COR_TEXTO_CLARO = (235, 240, 250)
COR_TEXTO_MUTED = (140, 155, 180)
COR_TEXTO_DESTAQUE = (255, 215, 80)
COR_ALERTA = (255, 75, 75)

COR_LIGACAO_POSSIVEL = (110, 137, 164)
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

        self.fundo_padrao = self._carregar_imagem(
            "background/Fundo Mapa.png", (largura, altura), preencher=True
        )
        self.fundos_por_fase: dict[int, pygame.Surface | None] = {}
        self.moldura = self._carregar_imagem("ui/moldura_fase.png", (590, 350))
        self.sprites = {
            "central": self._carregar_imagem("sprites/central_energia.png", (88, 88)),
            "ligada": self._carregar_imagem("sprites/casa_acesa.png", (88, 88)),
            "desligada": self._carregar_imagem("sprites/casa_apagada.png", (88, 88)),
        }
        # O brilho e as margens transparentes variam entre os três PNGs.
        self.centros_sprites = {
            sprite: sprite.get_bounding_rect(min_alpha=128).center
            for sprite in self.sprites.values() if sprite is not None
        }
        casa_ligada = self.sprites["ligada"]
        self.icone_casa = (
            pygame.transform.smoothscale(casa_ligada, (26, 26))
            if casa_ligada is not None else None
        )
        self.icone_moeda = self._carregar_imagem("hud/moeda.png", (22, 22))
        self.icone_alerta = self._carregar_imagem("hud/alerta_cruzamento.png", (22, 22))
        self.estrela_cheia = self._carregar_imagem("hud/estrela_cheia.png", (44, 44))
        self.estrela_vazia = self._carregar_imagem("hud/estrela_vazia.png", (44, 44))
        self.raio_casa = 32

    def _carregar_imagem(
        self, arquivo: str, tamanho: Tuple[int, int], preencher: bool = False
    ) -> Optional[pygame.Surface]:
        """Carrega e redimensiona a imagem uma vez, com alternativa desenhada se faltar."""
        try:
            imagem = pygame.image.load(str(PASTA_ASSETS / arquivo))
        except (OSError, pygame.error):
            return None
        if pygame.display.get_surface() is not None:
            imagem = imagem.convert_alpha()
        if preencher:
            largura, altura = tamanho
            fator = max(largura / imagem.get_width(), altura / imagem.get_height())
            tamanho_escalado = (math.ceil(imagem.get_width() * fator), math.ceil(imagem.get_height() * fator))
            imagem = pygame.transform.smoothscale(imagem, tamanho_escalado)
            recorte = pygame.Rect((0, 0), tamanho)
            recorte.center = imagem.get_rect().center
            return imagem.subsurface(recorte)
        return pygame.transform.smoothscale(imagem, tamanho)

    def desenhar(
        self, superficie: pygame.Surface, jogo: Jogo, pos_mouse: Tuple[int, int],
        pontos_campanha: int | None = None,
    ) -> None:
        """Desenha o quadro completo do jogo."""
        fase_id = jogo.fase.id
        if fase_id not in self.fundos_por_fase:
            fundo = self._carregar_imagem(
                f"background/alinhados/fundo_fase_{fase_id}.png",
                (self.largura, self.altura),
                preencher=True,
            )
            self.fundos_por_fase[fase_id] = fundo if fundo is not None else self.fundo_padrao

        superficie.fill(COR_FUNDO)
        fundo = self.fundos_por_fase[fase_id]
        if fundo is not None:
            superficie.blit(fundo, (0, 0))

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
            self._desenhar_painel_vitoria(superficie, jogo, pontos_campanha)

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
        for casa in jogo.fase.casas:
            cx, cy = int(casa.x), int(casa.y)
            ligada = casa.id in jogo.casas_na_rede
            selecionada = (casa.id == jogo.casa_selecionada)

            if casa.central:
                sprite = self.sprites["central"]
                cor_corpo = COR_CASA_CENTRAL
            elif ligada:
                sprite = self.sprites["ligada"]
                cor_corpo = COR_CASA_LIGADA
            else:
                sprite = self.sprites["desligada"]
                cor_corpo = COR_CASA_DESCONECTADA

            if sprite is not None:
                centro_x, centro_y = self.centros_sprites[sprite]
                sup.blit(sprite, (cx - centro_x, cy - centro_y))
            else:
                if ligada:
                    brilho = pygame.Surface((68, 68), pygame.SRCALPHA)
                    pygame.draw.circle(brilho, COR_HALO_BRILHO, (34, 34), 34)
                    sup.blit(brilho, brilho.get_rect(center=(cx, cy)))
                pygame.draw.circle(sup, cor_corpo, (cx, cy), 22)
                if casa.central:
                    self._desenhar_icone_central(sup, cx, cy)
                else:
                    self._desenhar_icone_casa(sup, cx, cy, ligada)

            if selecionada:
                pygame.draw.circle(sup, COR_TEXTO_CLARO, (cx, cy), self.raio_casa + 4, width=2)

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
        if self.icone_casa is not None:
            sup.blit(self.icone_casa, (16, 31))
        sup.blit(txt_rede, (44 if self.icone_casa is not None else 20, 36))

        # 3. Orçamento e Gastos
        restante = jogo.orcamento_restante
        cor_restante = COR_ALERTA if restante <= 10 or jogo.beco_sem_saida else COR_TEXTO_DESTAQUE
        texto_orcamento = f"Gasto: {jogo.gasto} / {jogo.fase.orcamento}  (Restante: {restante})"
        txt_orc = self.fonte_normal.render(texto_orcamento, True, cor_restante)
        rect_orc = txt_orc.get_rect(topright=(self.largura - 20, 10))
        sup.blit(txt_orc, rect_orc)
        if self.icone_moeda is not None:
            sup.blit(self.icone_moeda, self.icone_moeda.get_rect(midright=(rect_orc.left - 4, rect_orc.centery)))

        if jogo.fase.sem_cruzamento:
            txt_regra = self.fonte_pequena.render("Cabos não podem cruzar", True, COR_TEXTO_CLARO)
            rect_regra = txt_regra.get_rect(topright=(self.largura - 20, 38))
            sup.blit(txt_regra, rect_regra)
            if self.icone_alerta is not None:
                sup.blit(self.icone_alerta, self.icone_alerta.get_rect(midright=(rect_regra.left - 4, rect_regra.centery)))

        # 4. Mensagem de Feedback de uma linha
        cruzamento_bloqueado = jogo.mensagem_feedback == MENSAGEM_CRUZAMENTO
        cor_feedback = COR_ALERTA if jogo.beco_sem_saida or cruzamento_bloqueado else COR_TEXTO_MUTED
        txt_msg = self.fonte_pequena.render(jogo.mensagem_feedback, True, cor_feedback)
        sup.blit(txt_msg, (320, 14))

        # 5. Dica de comandos
        dica = "[Clique] Conectar/Remover  |  [Z] Desfazer  |  [R] Reiniciar  |  [ESC] Pausar"
        txt_dica = self.fonte_pequena.render(dica, True, (110, 125, 150))
        sup.blit(txt_dica, (320, 38))

    def _desenhar_painel_vitoria(
        self, sup: pygame.Surface, jogo: Jogo, pontos_campanha: int | None
    ) -> None:
        """Exibe o modal com a pontuação e estrelas conquistadas."""
        assert jogo.resultado is not None
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 210))
        sup.blit(overlay, (0, 0))

        # Caixa do painel
        largura_p, altura_p = 590, 350
        cx, cy = self.largura // 2, self.altura // 2
        rect_painel = pygame.Rect(cx - largura_p // 2, cy - altura_p // 2, largura_p, altura_p)
        if self.moldura is not None:
            sup.blit(self.moldura, self.moldura.get_rect(center=(cx, cy)))
        else:
            pygame.draw.rect(sup, (24, 32, 50), rect_painel, border_radius=12)
            pygame.draw.rect(sup, COR_CABO_NORMAL, rect_painel, width=2, border_radius=12)

        # Título
        titulo = "FASE CONCLUÍDA!"
        if pontos_campanha is not None:
            titulo = "Parabéns! Você conectou toda a cidade!"
        txt_vitoria = self.fonte_destaque.render(titulo, True, COR_TEXTO_DESTAQUE)
        sup.blit(txt_vitoria, txt_vitoria.get_rect(center=(cx, cy - 117)))

        self._desenhar_estrelas(sup, jogo.resultado.estrelas, cx, cy - 70)

        # Estatísticas
        res = jogo.resultado
        linhas = [
            f"Seu Custo: {res.custo_jogador}  |  Solução Ideal (Par): {res.par}",
            f"Aproveitamento: {res.aproveitamento:.1f}%",
            f"Pontuação: {res.pontos} pontos"
        ]
        y_inicial, passo = cy - 24, 26
        if pontos_campanha is not None:
            linhas.append(f"Pontuação total: {pontos_campanha} / {PONTOS_MAXIMOS_CAMPANHA}")
            y_inicial, passo = cy - 30, 22
        for idx, linha in enumerate(linhas):
            txt_linha = self.fonte_normal.render(linha, True, COR_TEXTO_CLARO)
            sup.blit(txt_linha, txt_linha.get_rect(center=(cx, y_inicial + idx * passo)))

    def _desenhar_estrelas(self, sup: pygame.Surface, quantidade: int, x: int, y: int) -> None:
        """Desenha as três estrelas, preenchendo as que foram conquistadas."""
        for indice in range(3):
            conquistada = indice < quantidade
            estrela = self.estrela_cheia if conquistada else self.estrela_vazia
            if estrela is None:
                simbolo = "★" if conquistada else "☆"
                estrela = self.fonte_destaque.render(simbolo, True, COR_TEXTO_DESTAQUE)
            sup.blit(estrela, estrela.get_rect(center=(x + (indice - 1) * 48, y)))
