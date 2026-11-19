"""
Estrutura de dados para representação de grafos não orientados e ponderados.
Este módulo modela o mapa da cidade com casas (vértices), ligações possíveis
(arestas) e custos de instalação de cabos (pesos das arestas).
"""

from typing import Dict, List, Optional, Tuple


class Grafo:
    """
    Representa um grafo não orientado com pesos inteiros positivos nas arestas.
    
    Conceito da disciplina:
    Um grafo G = (V, E) onde V é o conjunto de vértices (casas de 0 a n-1)
    e E é o conjunto de pares não orientados {u, v} com função de peso w(u, v).
    """

    def __init__(self, n: int) -> None:
        """
        Inicializa o grafo com n vértices identificados de 0 a n-1.
        
        :param n: Quantidade total de vértices (casas).
        """
        self.n = n
        # Lista de adjacência: para cada vértice, mapeia vizinho -> custo
        self.adjacencias: List[Dict[int, int]] = [{} for _ in range(n)]
        # Dicionário de arestas para acesso rápido por chave canônica (u, v) onde u < v
        self._arestas: Dict[Tuple[int, int], int] = {}

    def adicionar_aresta(self, u: int, v: int, custo: int) -> None:
        """
        Adiciona uma ligação não orientada e ponderada entre u e v.
        
        Conceito da disciplina:
        Aresta não orientada: a ligação entre u e v é bidirecional (u-v equivale a v-u).
        """
        if u == v:
            raise ValueError("Não são permitidos laços (aresta de um vértice para ele mesmo).")
        if not (0 <= u < self.n and 0 <= v < self.n):
            raise ValueError(f"Vértices fora do intervalo [0, {self.n - 1}]: {u}, {v}")

        u_can, v_can = (min(u, v), max(u, v))
        self._arestas[(u_can, v_can)] = custo
        self.adjacencias[u][v] = custo
        self.adjacencias[v][u] = custo

    def custo(self, u: int, v: int) -> Optional[int]:
        """
        Retorna o custo da ligação entre u e v, ou None se não existir.
        """
        u_can, v_can = (min(u, v), max(u, v))
        return self._arestas.get((u_can, v_can))

    def existe(self, u: int, v: int) -> bool:
        """
        Verifica se existe ligação direta entre u e v.
        """
        u_can, v_can = (min(u, v), max(u, v))
        return (u_can, v_can) in self._arestas

    def vizinhos(self, u: int) -> List[int]:
        """
        Retorna a lista de vértices adjacentes a u.
        
        Conceito da disciplina:
        Vizinhança aberta N(u): conjunto de vértices diretamente conectados a u.
        """
        if not (0 <= u < self.n):
            return []
        return list(self.adjacencias[u].keys())

    def arestas(self) -> List[Tuple[int, int, int]]:
        """
        Retorna todas as arestas do grafo como lista de tuplas (u, v, custo), com u < v.
        """
        return [(u, v, custo) for (u, v), custo in self._arestas.items()]
