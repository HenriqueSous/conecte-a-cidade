"""
Ferramenta para validação de fases do jogo Conecte a Cidade.
Compara Prim e Kruskal, calcula o par sem cruzamentos por busca exata
e verifica orçamento, legibilidade do mapa e estratégia por distância.
"""

import argparse
import glob
from itertools import combinations
import json
import math
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import time

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.algoritmos import buscar_agm_sem_cruzamentos, kruskal, prim, verificar_conectividade
from src.fases import Fase, Ligacao, carregar_fase
from src.geometria import Ponto
from src.grafo import Grafo


FATORES_ORCAMENTO = {
    1: 1.60,
    2: 1.40,
    3: 1.32,
    4: 1.30,
    5: 1.22,
    6: 1.40,
    7: 1.30,
    8: 1.20,
    9: 1.12,
    10: 1.05
}

ALTURA_ROTULO = 16
RAIO_AREA_CASA = 36


def custo_vizinhas_mais_proximas(fase: Fase) -> int:
    """Usa Prim para ligar a rede à vizinha mais próxima e soma os custos reais."""
    def comprimento(ligacao: Ligacao) -> float:
        origem = fase.obter_posicao(ligacao.de)
        destino = fase.obter_posicao(ligacao.para)
        return math.dist(origem, destino)

    grafo_distancias = Grafo(fase.grafo.n)
    # Troca os custos pela ordem das distâncias para reaproveitar pesos inteiros no Prim.
    ligacoes = sorted(fase.ligacoes, key=comprimento)
    for ordem, ligacao in enumerate(ligacoes, start=1):
        grafo_distancias.adicionar_aresta(ligacao.de, ligacao.para, ordem)

    _, rede = prim(grafo_distancias, inicio=0)
    return sum(ligacoes[ordem - 1].custo for _, _, ordem in rede)


def distancia_ate_segmento(ponto: Ponto, inicio: Ponto, fim: Ponto) -> float:
    """Mede a distância do ponto à sua projeção dentro do segmento."""
    dx, dy = fim[0] - inicio[0], fim[1] - inicio[1]
    produto_escalar = (ponto[0] - inicio[0]) * dx + (ponto[1] - inicio[1]) * dy
    fracao = max(0, min(1, produto_escalar / (dx * dx + dy * dy)))
    projecao = (inicio[0] + fracao * dx, inicio[1] + fracao * dy)
    return math.dist(ponto, projecao)


def verificar_legibilidade(fase: Fase) -> list[str]:
    """Identifica ligações que passam por casas e possíveis colisões de rótulos."""
    avisos = []
    rotulos = []
    for ligacao in fase.ligacoes:
        inicio = fase.obter_posicao(ligacao.de)
        fim = fase.obter_posicao(ligacao.para)
        nome = f"{ligacao.de}–{ligacao.para}"
        x, y = (int((a + b) / 2) for a, b in zip(inicio, fim))
        # Estima a largura da caixa do Pygame com folga para diferenças de fonte.
        largura = max(20, 8 + 9 * len(str(ligacao.custo)))
        rotulos.append((nome, x, y, largura))

        for casa in fase.casas:
            if casa.id in (ligacao.de, ligacao.para):
                continue
            if distancia_ate_segmento((casa.x, casa.y), inicio, fim) < RAIO_AREA_CASA:
                avisos.append(f"A ligação {nome} passa pela área da casa {casa.id}.")

    for (nome_a, xa, ya, largura_a), (nome_b, xb, yb, largura_b) in combinations(rotulos, 2):
        if abs(xa - xb) * 2 < largura_a + largura_b and abs(ya - yb) < ALTURA_ROTULO:
            avisos.append(f"Os rótulos de custo das ligações {nome_a} e {nome_b} podem se sobrepor.")
    return avisos


def calcular_par(fase: Fase, custo_agm: int) -> int | None:
    """Calcula o par segundo a regra da fase e verifica o efeito da restrição."""
    if not fase.sem_cruzamento:
        return custo_agm

    posicoes = [fase.obter_posicao(casa.id) for casa in fase.casas]
    resultado = buscar_agm_sem_cruzamentos(posicoes, fase.grafo.arestas())
    if resultado is None:
        print("[ERRO] A fase não admite uma rede que conecte todas as casas sem cruzamentos.")
        return None
    par, _ = resultado
    if par <= custo_agm:
        print(f"[ERRO] O par sem cruzamentos ({par}) deve superar a AGM convencional ({custo_agm}).")
        return None
    return par


def gravar_par_e_orcamento(caminho_arquivo: str, par: int, orcamento: int) -> None:
    """Atualiza os dois valores juntos ao substituir o JSON completo."""
    caminho = Path(caminho_arquivo)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados.update(par=par, orcamento=orcamento)
    with TemporaryDirectory(dir=caminho.parent) as pasta_temporaria:
        temporario = Path(pasta_temporaria) / caminho.name
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporario.replace(caminho)


def validar_fase_individual(caminho_arquivo: str, gravar: bool = False) -> bool:
    """Valida uma única fase e exibe o relatório."""
    inicio_tempo = time.perf_counter()
    print(f"\n--- Validando: {os.path.basename(caminho_arquivo)} ---")

    try:
        fase = carregar_fase(caminho_arquivo)
    except Exception as e:
        print(f"[ERRO] Falha ao carregar fase: {e}")
        return False

    n = fase.grafo.n
    arestas = fase.grafo.arestas()

    # 1. Checagem de conectividade
    if not verificar_conectividade(fase.grafo, inicio=0):
        print("[ERRO] O grafo da fase é desconexo!")
        return False

    # 2. Validação cruzada: Kruskal vs Prim
    custo_kruskal, _ = kruskal(n, arestas)
    custo_prim, _ = prim(fase.grafo, inicio=0)

    if custo_kruskal != custo_prim:
        print(f"[ERRO] Divergência na AGM! Kruskal deu {custo_kruskal} e Prim deu {custo_prim}.")
        return False

    par_calculado = calcular_par(fase, custo_kruskal)
    if par_calculado is None:
        return False

    fator_esperado = FATORES_ORCAMENTO.get(fase.id, 1.30)
    orcamento_calculado = math.ceil(par_calculado * fator_esperado)
    if gravar and fase.sem_cruzamento and (fase.par, fase.orcamento) != (par_calculado, orcamento_calculado):
        try:
            gravar_par_e_orcamento(caminho_arquivo, par_calculado, orcamento_calculado)
        except OSError as erro:
            print(f"[ERRO] Falha ao gravar o par e o orçamento: {erro}")
            return False
        fase.par, fase.orcamento = par_calculado, orcamento_calculado
        print("Par e orçamento atualizados no JSON.")

    if fase.par != par_calculado:
        print(f"[ERRO] Par gravado ({fase.par}) difere do par calculado ({par_calculado}).")
        return False

    if fase.orcamento != orcamento_calculado:
        if fase.sem_cruzamento:
            print(f"[ERRO] Orçamento gravado ({fase.orcamento}) difere do calculado ({orcamento_calculado}).")
            return False
        print(f"[AVISO] Orçamento gravado ({fase.orcamento}) difere de ceil(par * {fator_esperado}) = {orcamento_calculado}")

    if fase.id >= 2:
        custo_por_distancia = custo_vizinhas_mais_proximas(fase)
        print(f"Custo ao ligar as vizinhas mais próximas: {custo_por_distancia}")
        if custo_por_distancia == fase.par:
            print("[AVISO] Escolher as ligações pela distância visual atingiu o par.")

    for aviso in verificar_legibilidade(fase):
        print(f"[AVISO] {aviso}")

    tempo_ms = (time.perf_counter() - inicio_tempo) * 1000

    print(f"Sucesso: Fase {fase.id} ('{fase.nome}')")
    print(f"Casas: {n} | Ligações: {len(arestas)}")
    tipo_par = "Par sem cruzamentos" if fase.sem_cruzamento else "Par"
    print(f"{tipo_par}: {fase.par} | AGM convencional (Kruskal e Prim): {custo_kruskal}")
    print(f"Orçamento: {fase.orcamento} (Folga: +{fase.orcamento - fase.par})")
    print(f"Tempo de validação: {tempo_ms:.2f} ms")
    return True


def main() -> None:
    argumentos = argparse.ArgumentParser(description="Valida os arquivos de fase do jogo.")
    argumentos.add_argument("--gravar-par", action="store_true",
                            help="atualiza o par e o orçamento das fases sem cruzamentos")
    opcoes = argumentos.parse_args()

    diretorio_fases = os.path.join(os.path.dirname(__file__), "..", "dados", "fases")
    arquivos = sorted(glob.glob(os.path.join(diretorio_fases, "fase_*.json")))

    if not arquivos:
        print("Nenhum arquivo de fase encontrado em dados/fases/!")
        sys.exit(1)

    todos_sucessos = True
    for arq in arquivos:
        sucesso = validar_fase_individual(arq, gravar=opcoes.gravar_par)
        if not sucesso:
            todos_sucessos = False

    print("\n" + "=" * 45)
    if todos_sucessos:
        print("Resultado: TODAS AS FASES SÃO VÁLIDAS!")
    else:
        print("Resultado: HOUVE ERROS NA VALIDAÇÃO.")
        sys.exit(1)


if __name__ == "__main__":
    main()
