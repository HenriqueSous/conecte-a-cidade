"""
Motor de regras e gerenciamento do estado da partida do jogo Conecte a Cidade.
Controla seleção de casas, construção e remoção de cabos, orçamento, histórico
para desfazer (Z), detecção de vitória via BFS, cabos redundantes e becos sem saída.
Este módulo não depende de pygame e pode ser completamente testado sem interface gráfica.
"""

from typing import Dict, List, Optional, Set, Tuple
from src.grafo import Grafo
from src.fases import Fase
from src.algoritmos import (
    bfs_componente,
    detectar_cabo_redundante,
    calcular_limite_inferior_restante
)
from src.geometria import segmentos_se_cruzam
from src.pontuacao import avaliar_resultado, ResultadoPartida

MENSAGEM_CRUZAMENTO = "Este cabo cruzaria outro cabo."


class Jogo:
    """
    Gerencia o estado e as regras de uma partida em uma fase.
    """

    def __init__(self, fase: Fase) -> None:
        """
        Inicializa a partida com a fase especificada.
        """
        self.fase = fase
        self.casa_selecionada: Optional[int] = None
        # Conjunto de cabos construídos no formato canônico (u, v) onde u < v
        self.cabos_construidos: Set[Tuple[int, int]] = set()
        # Pilha de histórico para desfazer: tuplas (acao, u, v, custo) onde acao é 'construir' ou 'remover'
        self.historico: List[Tuple[str, int, int, int]] = []
        self.gasto: int = 0
        self.vitoria: bool = False
        self.beco_sem_saida: bool = False
        self.mensagem_feedback: str = "Clique em uma casa para começar a conectar."
        self.resultado: Optional[ResultadoPartida] = None

        # Atualiza componentes iniciais
        self.casas_na_rede: Set[int] = set()
        self.cabos_redundantes: Set[Tuple[int, int]] = set()
        self._atualizar_estado()

    @property
    def orcamento_restante(self) -> int:
        """Retorna quanto dinheiro ainda resta no orçamento."""
        return self.fase.orcamento - self.gasto

    def cancelar_selecao(self) -> None:
        """Cancela a seleção da casa atual."""
        self.casa_selecionada = None

    def selecionar_casa(self, casa_id: int) -> bool:
        """
        Trata o clique do jogador em uma casa.
        
        :param casa_id: ID da casa clicada (0 a n-1).
        :return: True se uma ação de construção/remoção foi realizada com sucesso.
        """
        if self.vitoria:
            return False

        if not (0 <= casa_id < self.fase.grafo.n):
            self.cancelar_selecao()
            return False

        # Primeiro clique: seleciona a casa
        if self.casa_selecionada is None:
            self.casa_selecionada = casa_id
            self.mensagem_feedback = f"Casa {casa_id} selecionada. Escolha outra casa para ligar."
            return True

        # Clicar na mesma casa desseleciona
        if self.casa_selecionada == casa_id:
            self.cancelar_selecao()
            self.mensagem_feedback = "Seleção cancelada."
            return False

        u = self.casa_selecionada
        v = casa_id
        u_can, v_can = (min(u, v), max(u, v))
        self.cancelar_selecao()

        # Verifica se existe ligação viável entre as duas casas
        if not self.fase.grafo.existe(u_can, v_can):
            self.mensagem_feedback = "Não existe ligação viável entre essas casas."
            return False

        # Se o cabo já está construído, remove-o (comportamento de alternância)
        if (u_can, v_can) in self.cabos_construidos:
            return self._remover_cabo(u_can, v_can, registrar_historico=True)

        # Caso contrário, tenta construir o cabo
        return self._construir_cabo(u_can, v_can, registrar_historico=True)

    def pode_construir(self, u: int, v: int) -> Tuple[bool, str]:
        """
        Verifica se a ligação entre u e v pode ser construída no momento.
        Útil para a prévia visual na interface.
        
        :return: Tupla (permitido, motivo).
        """
        if u == v:
            return False, "Mesma casa"

        u_can, v_can = (min(u, v), max(u, v))
        if not self.fase.grafo.existe(u_can, v_can):
            return False, "Sem ligação viável"

        if (u_can, v_can) in self.cabos_construidos:
            return True, "Remover cabo existente"

        if self._cruza_cabo_construido(u_can, v_can):
            return False, MENSAGEM_CRUZAMENTO

        custo = self.fase.grafo.custo(u_can, v_can) or 0
        if self.gasto + custo > self.fase.orcamento:
            return False, "Orçamento insuficiente"

        return True, "Construção permitida"

    def _cruza_cabo_construido(self, u: int, v: int) -> bool:
        """Consulta só os cabos já instalados em fases com a restrição ativa."""
        if not self.fase.sem_cruzamento:
            return False

        origem = self.fase.obter_posicao(u)
        destino = self.fase.obter_posicao(v)
        return any(
            segmentos_se_cruzam(origem, destino, self.fase.obter_posicao(a), self.fase.obter_posicao(b))
            for a, b in self.cabos_construidos
        )

    def _construir_cabo(self, u: int, v: int, registrar_historico: bool = True) -> bool:
        """Constrói um cabo entre u e v se respeitar o orçamento e regras."""
        u_can, v_can = (min(u, v), max(u, v))
        custo = self.fase.grafo.custo(u_can, v_can)
        if custo is None:
            return False

        permitido, motivo = self.pode_construir(u_can, v_can)
        if not permitido:
            self.mensagem_feedback = motivo
            return False

        self.cabos_construidos.add((u_can, v_can))
        self.gasto += custo

        if registrar_historico:
            self.historico.append(("construir", u_can, v_can, custo))

        self.mensagem_feedback = f"Cabo ligado entre {u_can} e {v_can} (custo {custo})."
        self._atualizar_estado()
        return True

    def _remover_cabo(self, u: int, v: int, registrar_historico: bool = True) -> bool:
        """Remove um cabo construído e devolve o custo."""
        u_can, v_can = (min(u, v), max(u, v))
        if (u_can, v_can) not in self.cabos_construidos:
            return False

        custo = self.fase.grafo.custo(u_can, v_can) or 0
        self.cabos_construidos.remove((u_can, v_can))
        self.gasto -= custo

        if registrar_historico:
            self.historico.append(("remover", u_can, v_can, custo))

        self.mensagem_feedback = f"Cabo removido entre {u_can} e {v_can} (+{custo} devolvidos)."
        self._atualizar_estado()
        return True

    def desfazer(self) -> bool:
        """
        Desfaz a última ação de construção ou remoção (tecla Z).
        """
        if not self.historico:
            self.mensagem_feedback = "Nada para desfazer."
            return False

        acao, u, v, custo = self.historico.pop()
        if acao == "construir":
            # Desfazer construção = remover sem registrar no histórico
            self.cabos_construidos.remove((u, v))
            self.gasto -= custo
            self.mensagem_feedback = f"Ação desfeita: cabo entre {u} e {v} removido."
        elif acao == "remover":
            # Desfazer remoção = reconstruir sem registrar no histórico
            self.cabos_construidos.add((u, v))
            self.gasto += custo
            self.mensagem_feedback = f"Ação desfeita: cabo entre {u} e {v} restaurado."

        self.cancelar_selecao()
        self._atualizar_estado()
        return True

    def reiniciar(self) -> None:
        """Reinicia a partida para o estado inicial da fase."""
        self.casa_selecionada = None
        self.cabos_construidos.clear()
        self.historico.clear()
        self.gasto = 0
        self.vitoria = False
        self.beco_sem_saida = False
        self.resultado = None
        self.mensagem_feedback = "Fase reiniciada. Clique em uma casa para começar."
        self._atualizar_estado()

    def _atualizar_estado(self) -> None:
        """
        Recalcula conectividade (BFS), cabos redundantes, condição de vitória
        e detecção de beco sem saída.
        """
        n = self.fase.grafo.n
        # Cria um subgrafo H apenas com as arestas construídas
        subgrafo_construido = Grafo(n)
        for u, v in self.cabos_construidos:
            custo = self.fase.grafo.custo(u, v) or 0
            subgrafo_construido.adicionar_aresta(u, v, custo)

        # BFS a partir da central (casa 0) para identificar casas na rede
        self.casas_na_rede = bfs_componente(subgrafo_construido, inicio=0)

        # Identifica cabos redundantes (que fecham ciclo)
        # Um cabo é redundante se, ao ser removido temporariamente, seus extremos continuam na mesma componente
        self.cabos_redundantes.clear()
        cabos_lista = list(self.cabos_construidos)
        for i, (u, v) in enumerate(cabos_lista):
            outros_cabos = cabos_lista[:i] + cabos_lista[i + 1:]
            if detectar_cabo_redundante(n, outros_cabos, u, v):
                self.cabos_redundantes.add((u, v))

        # Checagem de vitória: todas as n casas estão na rede (conectadas à central 0)
        if len(self.casas_na_rede) == n:
            self.vitoria = True
            self.beco_sem_saida = False
            self.resultado = avaliar_resultado(self.fase.par, self.gasto)
            self.mensagem_feedback = (
                f"Parabéns! Todas as casas foram conectadas! "
                f"Gasto: {self.gasto} (Par: {self.fase.par}) - {self.resultado.estrelas} Estrelas!"
            )
            return

        self.vitoria = False

        # Detecção de beco sem saída (Seção 6.4)
        arestas_disponiveis = [
            (lig.de, lig.para, lig.custo)
            for lig in self.fase.ligacoes
            if (min(lig.de, lig.para), max(lig.de, lig.para)) not in self.cabos_construidos
            and not self._cruza_cabo_construido(lig.de, lig.para)
        ]

        custo_minimo_restante = calcular_limite_inferior_restante(
            n,
            list(self.cabos_construidos),
            arestas_disponiveis
        )

        self.beco_sem_saida = custo_minimo_restante is None or custo_minimo_restante > self.orcamento_restante
        if custo_minimo_restante is None and self.fase.sem_cruzamento:
            self.mensagem_feedback = "Os cabos atuais bloqueiam a rede. Desfaça ou reinicie."
        elif self.beco_sem_saida:
            self.mensagem_feedback = "Com esse orçamento não dá para conectar tudo. Desfaça ou reinicie."
