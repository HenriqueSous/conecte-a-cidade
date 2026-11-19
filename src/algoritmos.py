"""
Algoritmos de teoria dos grafos implementados manualmente para o jogo Conecte a Cidade.
Contém Busca em Largura (BFS), estrutura União-Busca (Disjoint Set Union),
algoritmo de Kruskal e algoritmo de Prim para Árvore Geradora Mínima (AGM).
Nenhuma biblioteca externa de grafos é utilizada neste módulo.
"""

from collections import deque
import heapq
from typing import Dict, List, Optional, Set, Tuple
from src.grafo import Grafo


class UniaoBusca:
    """
    Estrutura de dados União-Busca (Disjoint Set Union - DSU).
    
    Conceito da disciplina:
    Partição de um conjunto em classes de equivalência disjuntas.
    Utilizada para detectar ciclos e gerenciar componentes conexas no algoritmo de Kruskal.
    Aplica compressão de caminho e união por posto para máxima eficiência.
    """

    def __init__(self, n: int) -> None:
        """
        Inicializa n elementos, cada um sendo representante do seu próprio conjunto.
        """
        self.pai: List[int] = list(range(n))
        self.posto: List[int] = [0] * n
        self.quantidade_conjuntos: int = n

    def encontrar(self, u: int) -> int:
        """
        Encontra o representante (raiz) do conjunto que contém o elemento u.
        Aplica compressão de caminho (aponta o nó diretamente para a raiz).
        """
        if self.pai[u] != u:
            self.pai[u] = self.encontrar(self.pai[u])
        return self.pai[u]

    def unir(self, u: int, v: int) -> bool:
        """
        Une os conjuntos que contêm u e v.
        
        :return: True se u e v estavam em conjuntos diferentes (união realizada);
                 False se já pertenciam ao mesmo conjunto (já conectados / formaria ciclo).
        """
        raiz_u = self.encontrar(u)
        raiz_v = self.encontrar(v)

        if raiz_u == raiz_v:
            return False

        # União por posto: árvore de menor altura fica sob a de maior altura
        if self.posto[raiz_u] < self.posto[raiz_v]:
            self.pai[raiz_u] = raiz_v
        elif self.posto[raiz_u] > self.posto[raiz_v]:
            self.pai[raiz_v] = raiz_u
        else:
            self.pai[raiz_v] = raiz_u
            self.posto[raiz_u] += 1

        self.quantidade_conjuntos -= 1
        return True


def kruskal(n: int, arestas: List[Tuple[int, int, int]]) -> Tuple[int, List[Tuple[int, int, int]]]:
    """
    Calcula a Árvore Geradora Mínima (AGM) de um grafo usando o Algoritmo de Kruskal.
    
    Conceito da disciplina:
    Árvore Geradora Mínima (Kruskal): estratégia gulosa que ordena todas as arestas
    por custo crescente e insere uma a uma se seus extremos não estiverem na mesma
    componente conexa, evitando a formação de ciclos com o auxílio de União-Busca.
    
    :param n: Número de vértices do grafo (0 a n-1).
    :param arestas: Lista de tuplas (u, v, custo).
    :return: Tupla com (custo_total, lista_de_arestas_da_agm). Se o grafo for desconexo,
             retorna o custo das componentes conectadas e arestas selecionadas.
    """
    if n <= 1:
        return 0, []

    # Ordenação gulosa pelo custo da aresta
    arestas_ordenadas = sorted(arestas, key=lambda item: item[2])
    dsu = UniaoBusca(n)
    arestas_agm: List[Tuple[int, int, int]] = []
    custo_total = 0

    for u, v, custo in arestas_ordenadas:
        if dsu.unir(u, v):
            arestas_agm.append((min(u, v), max(u, v), custo))
            custo_total += custo
            # Uma árvore geradora sobre n vértices possui exatamente n - 1 arestas
            if len(arestas_agm) == n - 1:
                break

    return custo_total, arestas_agm


def prim(grafo: Grafo, inicio: int = 0) -> Tuple[int, List[Tuple[int, int, int]]]:
    """
    Calcula a Árvore Geradora Mínima (AGM) de um grafo usando o Algoritmo de Prim.
    
    Conceito da disciplina:
    Árvore Geradora Mínima (Prim): estratégia gulosa que cresce uma árvore a partir de um
    vértice inicial, sempre adicionando a aresta de corte de menor peso que conecta um
    vértice já na árvore a um vértice fora dela.
    
    :param grafo: Instância da classe Grafo.
    :param inicio: Vértice inicial para iniciar a árvore (padrão 0).
    :return: Tupla com (custo_total, lista_de_arestas_da_agm).
    """
    n = grafo.n
    if n <= 1:
        return 0, []

    visitados: Set[int] = {inicio}
    arestas_agm: List[Tuple[int, int, int]] = []
    custo_total = 0

    # Fila de prioridade (heap min) guardando: (custo, origem, destino)
    fila_prioridade: List[Tuple[int, int, int]] = []

    for vizinho, custo in grafo.adjacencias[inicio].items():
        heapq.heappush(fila_prioridade, (custo, inicio, vizinho))

    while fila_prioridade and len(visitados) < n:
        custo, u, v = heapq.heappop(fila_prioridade)

        if v in visitados:
            continue

        visitados.add(v)
        arestas_agm.append((min(u, v), max(u, v), custo))
        custo_total += custo

        for proximo, peso in grafo.adjacencias[v].items():
            if proximo not in visitados:
                heapq.heappush(fila_prioridade, (peso, v, proximo))

    return custo_total, arestas_agm


def bfs_componente(grafo: Grafo, inicio: int = 0) -> Set[int]:
    """
    Executa Busca em Largura (BFS) para encontrar todos os vértices acessíveis a partir do início.
    
    Conceito da disciplina:
    Busca em Largura e Conectividade: travessia sistemática por níveis usando fila (FIFO).
    O conjunto de vértices visitados define a componente conexa do vértice de origem.
    
    :param grafo: Instância da classe Grafo.
    :param inicio: Vértice de partida (por exemplo, a central 0).
    :return: Conjunto com os índices dos vértices alcançáveis.
    """
    if grafo.n == 0:
        return set()

    visitados: Set[int] = {inicio}
    fila: deque[int] = deque([inicio])

    while fila:
        atual = fila.popleft()
        for vizinho in grafo.vizinhos(atual):
            if vizinho not in visitados:
                visitados.add(vizinho)
                fila.append(vizinho)

    return visitados


def verificar_conectividade(grafo: Grafo, inicio: int = 0) -> bool:
    """
    Verifica se o grafo é conexo (todas as casas estão conectadas à central).
    
    Conceito da disciplina:
    Grafo Conexo: um grafo não orientado é conexo se e somente se existe pelo menos um
    caminho entre quaisquer dois de seus vértices (ou seja, uma única componente conexa).
    
    :param grafo: Instância da classe Grafo.
    :param inicio: Vértice de referência (central 0).
    :return: True se todos os n vértices forem visitados, False caso contrário.
    """
    if grafo.n == 0:
        return True
    visitados = bfs_componente(grafo, inicio)
    return len(visitados) == grafo.n


def detectar_cabo_redundante(n: int, arestas_construidas: List[Tuple[int, int]], u: int, v: int) -> bool:
    """
    Verifica se a ligação (u, v) é redundante (forma ciclo com os cabos já existentes).
    
    Conceito da disciplina:
    Ciclo simples em grafos: adicionar uma aresta entre dois vértices que já pertencem
    à mesma componente conexa fecha um ciclo fundamental na rede.
    
    :param n: Quantidade de vértices.
    :param arestas_construidas: Lista de arestas já construídas (u, v).
    :param u: Primeiro vértice da nova aresta.
    :param v: Segundo vértice da nova aresta.
    :return: True se u e v já possuem caminho entre si na rede atual, False caso contrário.
    """
    dsu = UniaoBusca(n)
    for aresta_u, aresta_v in arestas_construidas:
        dsu.unir(aresta_u, aresta_v)

    # Se já estão no mesmo conjunto, a adição de (u, v) é redundante
    return dsu.encontrar(u) == dsu.encontrar(v)


def calcular_limite_inferior_restante(
    n: int,
    arestas_construidas: List[Tuple[int, int]],
    arestas_disponiveis: List[Tuple[int, int, int]]
) -> Optional[int]:
    """
    Calcula um limite inferior para o custo de completar a conexão de todas as casas.
    
    Conceito da disciplina:
    Contração de componentes conexas e Árvore Geradora Mínima restante.
    Agrupa os vértices já conectados pelas arestas construídas e calcula o custo
    mínimo (Kruskal) para conectar as componentes restantes usando arestas ainda disponíveis.
    
    :param n: Número de vértices.
    :param arestas_construidas: Lista de arestas já construídas (u, v).
    :param arestas_disponiveis: Lista de arestas ainda não construídas (u, v, custo).
    :return: Custo mínimo restante para conectar tudo, ou None se for impossível conectar.
    """
    dsu = UniaoBusca(n)
    for u, v in arestas_construidas:
        dsu.unir(u, v)

    # Se já formou uma única componente, não falta gastar nada
    if dsu.quantidade_conjuntos == 1:
        return 0

    # Ordena as arestas disponíveis pelo custo para executar Kruskal sobre as componentes
    arestas_ordenadas = sorted(arestas_disponiveis, key=lambda item: item[2])
    custo_restante = 0

    for u, v, custo in arestas_ordenadas:
        if dsu.unir(u, v):
            custo_restante += custo
            if dsu.quantidade_conjuntos == 1:
                return custo_restante

    # Se esgotou as arestas disponíveis e ainda não conectou tudo, é impossível
    return None
