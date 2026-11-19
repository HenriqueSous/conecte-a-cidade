"""
Funções geométricas de teste de interseção entre segmentos de reta 2D.
Utilizado para verificar a regra de não cruzamento de cabos (planaridade).
Nenhuma biblioteca externa ou gráfica é utilizada neste módulo.
"""

from typing import Tuple

Ponto = Tuple[float, float]


def orientacao(p: Ponto, q: Ponto, r: Ponto) -> int:
    """
    Determina a orientação do trio ordenado de pontos (p, q, r).
    
    Conceito da disciplina e geometria computacional:
    Calcula o produto vetorial (orientação no plano 2D):
    - Retorna 0 se os pontos forem colineares.
    - Retorna 1 se o sentido for horário.
    - Retorna 2 se o sentido for anti-horário.
    """
    valor = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if abs(valor) < 1e-9:
        return 0
    return 1 if valor > 0 else 2


def ponto_no_segmento(p: Ponto, q: Ponto, r: Ponto) -> bool:
    """
    Verifica se o ponto colinear q pertence ao segmento pr.
    """
    dentro_x = min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
    dentro_y = min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
    return dentro_x and dentro_y


def pontos_iguais(p1: Ponto, p2: Ponto) -> bool:
    """
    Verifica se dois pontos são idênticos no plano considerando tolerância numérica.
    """
    return abs(p1[0] - p2[0]) < 1e-9 and abs(p1[1] - p2[1]) < 1e-9


def segmentos_se_cruzam(p1: Ponto, q1: Ponto, p2: Ponto, q2: Ponto) -> bool:
    """
    Verifica se o segmento p1-q1 cruza o segmento p2-q2 segundo as regras do jogo:
    
    Regras:
    1. Dois segmentos que compartilham um extremo (mesma casa) NÃO contam como cruzamento,
       exceto se forem colineares e um sobrepuser o outro.
    2. Cruzamento no interior (em forma de X) conta como cruzamento.
    3. Toque em T (um segmento toca o interior de outro) conta como cruzamento.
    4. Segmentos colineares com sobreposição contam como cruzamento.
    
    :return: True se houver cruzamento proibido, False caso contrário.
    """
    # Verifica se compartilham um extremo
    mesmo_p1_p2 = pontos_iguais(p1, p2)
    mesmo_p1_q2 = pontos_iguais(p1, q2)
    mesmo_q1_p2 = pontos_iguais(q1, p2)
    mesmo_q1_q2 = pontos_iguais(q1, q2)

    extremo_compartilhado = mesmo_p1_p2 or mesmo_p1_q2 or mesmo_q1_p2 or mesmo_q1_q2

    # Caso sejam exatamente o mesmo segmento
    if (mesmo_p1_p2 and mesmo_q1_q2) or (mesmo_p1_q2 and mesmo_q1_p2):
        return True

    # Se compartilham um extremo, verificar se são colineares com sobreposição além do vértice
    if extremo_compartilhado:
        o1 = orientacao(p1, q1, p2)
        o2 = orientacao(p1, q1, q2)
        if o1 == 0 and o2 == 0:
            # Colineares com extremo compartilhado: verificar se há sobreposição interna
            # Identifica o vértice compartilhado e os dois outros extremos
            if mesmo_p1_p2:
                comum, outro1, outro2 = p1, q1, q2
            elif mesmo_p1_q2:
                comum, outro1, outro2 = p1, q1, p2
            elif mesmo_q1_p2:
                comum, outro1, outro2 = q1, p1, q2
            else:
                comum, outro1, outro2 = q1, p1, p2

            # Há sobreposição se um dos outros pontos estiver entre o ponto comum e o outro
            if ponto_no_segmento(comum, outro1, outro2) and not pontos_iguais(comum, outro1):
                return True
            if ponto_no_segmento(comum, outro2, outro1) and not pontos_iguais(comum, outro2):
                return True

        # Compartilham um extremo em direções diferentes: permitido!
        return False

    # Orientações para teste geral de interseção
    o1 = orientacao(p1, q1, p2)
    o2 = orientacao(p1, q1, q2)
    o3 = orientacao(p2, q2, p1)
    o4 = orientacao(p2, q2, q1)

    # Caso geral de cruzamento em X (orientações alternadas)
    if o1 != o2 and o3 != o4:
        return True

    # Casos especiais: colinearidade e toque em T
    if o1 == 0 and ponto_no_segmento(p1, p2, q1):
        return True
    if o2 == 0 and ponto_no_segmento(p1, q2, q1):
        return True
    if o3 == 0 and ponto_no_segmento(p2, p1, q2):
        return True
    if o4 == 0 and ponto_no_segmento(p2, q1, q2):
        return True

    return False
