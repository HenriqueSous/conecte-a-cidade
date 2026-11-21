"""
Cálculo de pontuação, aproveitamento e estrelas do jogo Conecte a Cidade.
Regras da Seção 7:
- Aproveitamento = (par ÷ custo_do_jogador) × 100 (limitado a 100%)
- Pontos = round(1000 × par ÷ custo_do_jogador)
- Estrelas: 3 para custo == par, 2 para aproveitamento >= 85%, 1 para conclusão
"""

from dataclasses import dataclass

PONTOS_MAXIMOS_FASE = 1000


@dataclass
class ResultadoPartida:
    """Armazena o resultado consolidado ao concluir uma fase."""
    custo_jogador: int
    par: int
    aproveitamento: float
    pontos: int
    estrelas: int


def calcular_aproveitamento(par: int, custo_jogador: int) -> float:
    """
    Calcula a porcentagem de eficiência do jogador em relação à solução ótima (par).
    """
    if custo_jogador <= 0 or par <= 0:
        return 0.0
    return min(100.0, (par / custo_jogador) * 100.0)


def calcular_pontos(par: int, custo_jogador: int) -> int:
    """
    Calcula os pontos da partida (máximo 1000 pontos quando custo == par).
    """
    if custo_jogador <= 0 or par <= 0:
        return 0
    return min(PONTOS_MAXIMOS_FASE, round(PONTOS_MAXIMOS_FASE * (par / custo_jogador)))


def calcular_estrelas(custo_jogador: int, par: int) -> int:
    """
    Calcula a quantidade de estrelas obtidas:
    - 3 estrelas: custo igual ao par (solução ótima).
    - 2 estrelas: aproveitamento >= 85%.
    - 1 estrela: fase concluída com qualquer custo válido.
    """
    if custo_jogador == par:
        return 3
    aproveitamento = calcular_aproveitamento(par, custo_jogador)
    if aproveitamento >= 85.0:
        return 2
    return 1


def avaliar_resultado(par: int, custo_jogador: int) -> ResultadoPartida:
    """
    Gera o resumo completo de avaliação da fase concluída.
    """
    aprov = calcular_aproveitamento(par, custo_jogador)
    pontos = calcular_pontos(par, custo_jogador)
    estrelas = calcular_estrelas(custo_jogador, par)
    return ResultadoPartida(
        custo_jogador=custo_jogador,
        par=par,
        aproveitamento=aprov,
        pontos=pontos,
        estrelas=estrelas
    )
