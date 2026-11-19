"""
Testes unitários de interseção geométrica de segmentos (regras de planaridade).
"""

from src.geometria import segmentos_se_cruzam


def test_cruzamento_em_x():
    # Cruzamento típico em forma de X
    s1 = ((0, 0), (10, 10))
    s2 = ((0, 10), (10, 0))
    assert segmentos_se_cruzam(s1[0], s1[1], s2[0], s2[1]) is True


def test_extremo_compartilhado_nao_cruza():
    # Dois cabos saindo da mesma casa
    s1 = ((0, 0), (10, 0))
    s2 = ((0, 0), (0, 10))
    assert segmentos_se_cruzam(s1[0], s1[1], s2[0], s2[1]) is False


def test_toque_em_t_cruza():
    # Segmento vertical toca o meio do segmento horizontal
    s1 = ((0, 0), (10, 0))
    s2 = ((5, 5), (5, 0))
    assert segmentos_se_cruzam(s1[0], s1[1], s2[0], s2[1]) is True


def test_colinear_sobreposto_cruza():
    # Dois segmentos na mesma linha que se sobrepõem
    s1 = ((0, 0), (10, 0))
    s2 = ((5, 0), (15, 0))
    assert segmentos_se_cruzam(s1[0], s1[1], s2[0], s2[1]) is True


def test_colinear_separado_nao_cruza():
    # Dois segmentos na mesma linha mas distantes
    s1 = ((0, 0), (5, 0))
    s2 = ((8, 0), (12, 0))
    assert segmentos_se_cruzam(s1[0], s1[1], s2[0], s2[1]) is False


def test_segmentos_paralelos_nao_cruzam():
    # Segmentos paralelos sem colinearidade
    s1 = ((0, 0), (10, 0))
    s2 = ((0, 5), (10, 5))
    assert segmentos_se_cruzam(s1[0], s1[1], s2[0], s2[1]) is False
