"""
Módulo para carregamento e validação de arquivos de fases em formato JSON.
Garante que os dados da fase sejam válidos, consistentes e que o grafo seja conexo.
Nenhuma biblioteca externa de interface é utilizada neste módulo.
"""

from dataclasses import dataclass
import json
import math
import os
from typing import Any, Dict, List, Tuple
from src.grafo import Grafo
from src.algoritmos import verificar_conectividade


@dataclass
class Casa:
    """Representa uma casa (vértice do grafo) no mapa."""
    id: int
    x: float
    y: float
    central: bool = False


@dataclass
class Ligacao:
    """Representa uma ligação viável (aresta do grafo) entre duas casas."""
    de: int
    para: int
    custo: int


@dataclass
class Fase:
    """Contém todos os dados validados de uma fase do jogo."""
    id: int
    nome: str
    orcamento: int
    par: int
    sem_cruzamento: bool
    casas: List[Casa]
    ligacoes: List[Ligacao]
    grafo: Grafo

    def obter_posicao(self, casa_id: int) -> Tuple[float, float]:
        """Retorna a posição (x, y) de uma casa pelo seu id."""
        return (self.casas[casa_id].x, self.casas[casa_id].y)


def validar_dados_fase(dados: Dict[str, Any]) -> None:
    """
    Valida a integridade dos campos obrigatórios e das regras geométricas e de grafos.
    Lança ValueError se houver alguma inconsistência.
    """
    campos_obrigatorios = ["id", "nome", "orcamento", "par", "casas", "ligacoes"]
    for campo in campos_obrigatorios:
        if campo not in dados:
            raise ValueError(f"Campo obrigatório ausente na fase: '{campo}'")

    casas_dados = dados["casas"]
    ligacoes_dados = dados["ligacoes"]
    n = len(casas_dados)

    if n < 2:
        raise ValueError("A fase precisa ter pelo menos 2 casas.")

    # Validação dos IDs das casas (deve ser de 0 a n-1)
    ids_encontrados = set()
    for i, c in enumerate(casas_dados):
        cid = c.get("id")
        if cid != i:
            raise ValueError(f"Casas devem ter IDs sequenciais de 0 a n-1. Esperado {i}, recebido {cid}")
        ids_encontrados.add(cid)

    # A casa 0 deve ser a central
    if not casas_dados[0].get("central", False):
        raise ValueError("A casa de ID 0 deve ser a central (central: true).")

    # Validação de posições na tela (1000 x 680 com margem para HUD)
    posicoes = [(c["x"], c["y"]) for c in casas_dados]
    for i, (x, y) in enumerate(posicoes):
        if not (20 <= x <= 980 and 80 <= y <= 660):
            raise ValueError(f"Casa {i} está fora dos limites visíveis da tela: ({x}, {y})")

    # Validação de distância mínima de 80px entre as casas
    for i in range(n):
        for j in range(i + 1, n):
            dist = math.dist(posicoes[i], posicoes[j])
            if dist < 80:
                raise ValueError(f"Casas {i} e {j} estão muito próximas ({dist:.1f}px < 80px).")

    # Construção do grafo para checagem de conectividade
    grafo = Grafo(n)
    arestas_vistas = set()

    for lig in ligacoes_dados:
        u, v, custo = lig.get("de"), lig.get("para"), lig.get("custo")
        if u is None or v is None or custo is None:
            raise ValueError("Ligação malformada: deve conter 'de', 'para' e 'custo'.")
        if u not in ids_encontrados or v not in ids_encontrados:
            raise ValueError(f"Ligação ({u}, {v}) referencia casa inexistente.")
        if u == v:
            raise ValueError(f"Ligação ({u}, {v}) conecta a mesma casa.")
        if custo <= 0:
            raise ValueError(f"Custo da ligação ({u}, {v}) deve ser um inteiro positivo.")

        par_can = (min(u, v), max(u, v))
        if par_can in arestas_vistas:
            raise ValueError(f"Ligação duplicada encontrada entre as casas {u} e {v}.")
        arestas_vistas.add(par_can)
        grafo.adicionar_aresta(u, v, custo)

    # Validação de conectividade
    if not verificar_conectividade(grafo, inicio=0):
        raise ValueError("O grafo da fase é desconexo: nem todas as casas alcançam a central.")


def carregar_fase(caminho_arquivo: str) -> Fase:
    """
    Carrega e valida uma fase a partir de um arquivo JSON.
    
    :param caminho_arquivo: Caminho do arquivo JSON da fase.
    :return: Instância de Fase preenchida e validada.
    """
    if not os.path.isfile(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo de fase não encontrado: {caminho_arquivo}")

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        dados = json.load(f)

    validar_dados_fase(dados)

    casas = [
        Casa(id=c["id"], x=float(c["x"]), y=float(c["y"]), central=bool(c.get("central", False)))
        for c in dados["casas"]
    ]

    ligacoes = [
        Ligacao(de=int(l["de"]), para=int(l["para"]), custo=int(l["custo"]))
        for l in dados["ligacoes"]
    ]

    grafo = Grafo(len(casas))
    for lig in ligacoes:
        grafo.adicionar_aresta(lig.de, lig.para, lig.custo)

    return Fase(
        id=int(dados["id"]),
        nome=str(dados["nome"]),
        orcamento=int(dados["orcamento"]),
        par=int(dados["par"]),
        sem_cruzamento=bool(dados.get("sem_cruzamento", False)),
        casas=casas,
        ligacoes=ligacoes,
        grafo=grafo
    )


def obter_caminho_fase(fase_id: int, base_dir: str = ".") -> str:
    """Retorna o caminho relativo do arquivo JSON de uma fase dado seu ID."""
    nome_arquivo = f"fase_{fase_id:02d}.json"
    return os.path.join(base_dir, "dados", "fases", nome_arquivo)
