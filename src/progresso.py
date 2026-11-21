"""
Carrega e salva as conclusões e os recordes da campanha em progresso.json.
O progresso depende apenas dos resultados das partidas, sem importar pygame.
"""

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.fases import TOTAL_FASES
from src.pontuacao import PONTOS_MAXIMOS_FASE, ResultadoPartida

PONTOS_MAXIMOS_CAMPANHA = TOTAL_FASES * PONTOS_MAXIMOS_FASE


@dataclass(frozen=True)
class RegistroFase:
    concluida: bool = False
    melhor_pontuacao: int = 0
    melhor_custo: int | None = None
    estrelas: int = 0


class Progresso:
    """Mantém o melhor resultado de cada fase entre execuções do jogo."""

    def __init__(self, caminho: Path) -> None:
        self.caminho = caminho
        self._fases = self._carregar()

    def obter(self, numero: int) -> RegistroFase:
        return self._fases.get(str(numero), RegistroFase())

    def fase_desbloqueada(self, numero: int) -> bool:
        return numero == 1 or self.obter(numero - 1).concluida

    @property
    def campanha_concluida(self) -> bool:
        # O registro da última fase também identifica a conclusão em arquivos antigos.
        return self.obter(TOTAL_FASES).concluida

    @property
    def pontuacao_total(self) -> int:
        return sum(self.obter(numero).melhor_pontuacao for numero in range(1, TOTAL_FASES + 1))

    def registrar_conclusao(self, numero: int, resultado: ResultadoPartida) -> bool:
        anterior = self.obter(numero)
        melhor_custo = resultado.custo_jogador
        if anterior.melhor_custo is not None:
            melhor_custo = min(anterior.melhor_custo, melhor_custo)
        self._fases[str(numero)] = RegistroFase(
            concluida=True,
            melhor_pontuacao=max(anterior.melhor_pontuacao, min(resultado.pontos, PONTOS_MAXIMOS_FASE)),
            melhor_custo=melhor_custo,
            estrelas=max(anterior.estrelas, resultado.estrelas),
        )
        return self._salvar()

    def _carregar(self) -> dict[str, RegistroFase]:
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError, RecursionError) as erro:
            logging.warning("Não foi possível ler o progresso em %s: %s", self.caminho, erro)
            return {}

        fases = dados.get("fases") if isinstance(dados, dict) else None
        if not isinstance(fases, dict):
            return {}

        registros = {}
        for numero, registro in fases.items():
            if not isinstance(registro, dict) or registro.get("concluida") is not True:
                continue
            pontos = registro.get("melhor_pontuacao")
            if type(pontos) is not int:
                pontos = 0
            custo = registro.get("melhor_custo")
            estrelas = registro.get("estrelas")
            registros[numero] = RegistroFase(
                concluida=True,
                melhor_pontuacao=max(0, min(pontos, PONTOS_MAXIMOS_FASE)),
                melhor_custo=custo if type(custo) is int and custo > 0 else None,
                estrelas=estrelas if type(estrelas) is int and 0 <= estrelas <= 3 else 0,
            )
        return registros

    def _salvar(self) -> bool:
        dados = {
            "fases": {numero: asdict(registro) for numero, registro in self._fases.items()},
            "campanha_concluida": self.campanha_concluida,
        }
        temporario = None
        try:
            # Substitui o progresso só depois de escrever o JSON inteiro.
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.caminho.parent, delete=False
            ) as arquivo:
                temporario = Path(arquivo.name)
                json.dump(dados, arquivo, indent=4, ensure_ascii=False)
                arquivo.write("\n")
            temporario.replace(self.caminho)
        except OSError as erro:
            logging.warning("Não foi possível salvar o progresso em %s: %s", self.caminho, erro)
            if temporario is not None:
                try:
                    temporario.unlink(missing_ok=True)
                except OSError:
                    pass
            return False
        return True
