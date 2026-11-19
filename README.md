# Conecte a Cidade 🏙️⚡

Jogo 2D de puzzle e estratégia desenvolvido em **Python** e **pygame-ce** para a disciplina de **Matemática Discreta II** (Bacharelado em Sistemas de Informação - IFBA).

O jogador assume o papel de planejador de redes urbanas, tendo como missão ligar todas as casas de um bairro à central de energia/internet gastando o menor valor possível e respeitando um orçamento rigoroso.

---

## 📚 Conceitos Acadêmicos Implementados

Todos os algoritmos foram **implementados à mão**, sem dependência de bibliotecas de grafos:
- **Representação formal de grafos ponderados** (`src/grafo.py`)
- **Busca em Largura (BFS)** para cálculo de conectividade e alcance da rede (`src/algoritmos.py`)
- **Árvore Geradora Mínima (Kruskal)** com união-busca para cálculo da solução ideal (`src/algoritmos.py`)
- **Árvore Geradora Mínima (Prim)** com fila de prioridades para validação cruzada (`src/algoritmos.py`)
- **Detecção de Ciclos e Cabos Redundantes** (`src/algoritmos.py`)
- **Planaridade e Testes de Interseção de Segmentos** via produto vetorial (`src/geometria.py`)

Para o mapa detalhado dos tópicos teóricos, consulte [docs/CONCEITOS.md](docs/CONCEITOS.md).

---

## 🚀 Como Instalar e Executar

### 1. Pré-requisitos
- **Python 3.10** ou superior instalado.

### 2. Instalação das Dependências
Instale o `pygame-ce` e o `pytest`:
```bash
pip install -r requirements.txt
```

> **Atenção:** Certifique-se de usar `pygame-ce` (`pip install pygame-ce`), e não o `pygame` antigo.

### 3. Executar o Jogo (Fase 1 - Tutorial)
```bash
python main.py
```

---

## 🎮 Como Jogar

| Ação | Comando |
|---|---|
| **Selecionar casa / Criar cabo** | Clique com o **Botão Esquerdo** na primeira casa e depois na segunda |
| **Remover cabo existente** | Clique novamente nas duas casas do cabo (alternância) |
| **Cancelar seleção** | Clique com o **Botão Direito** ou no fundo do mapa |
| **Desfazer última ação** | Tecla **Z** |
| **Reiniciar fase** | Tecla **R** |
| **Sair do jogo** | Tecla **ESC** |

### Dicas de Estratégia
- **Casas ligadas à rede** acendem em **dourado**. As isoladas permanecem em cinza escuro.
- **Cabos normais** aparecem em **azul ciano**.
- **Cabos redundantes** (que fecham ciclos desnecessários) aparecem em **laranja**.
- Ao final, sua pontuação e estrelas (★ a ★★★) são calculadas comparando seu gasto total com a **solução ideal (par)** calculada pela Árvore Geradora Mínima.

---

## 🧪 Testes e Validação

### Executar a suíte de testes unitários:
```bash
pytest
```

### Executar a ferramenta de validação de fases:
```bash
python ferramentas/validar_fases.py
```
A ferramenta verifica se o JSON é válido, se o grafo é conexo, se o orçamento obedece ao fator e realiza a **validação cruzada entre Kruskal e Prim** para certificar a solução ótima gravada.

---

## 📁 Estrutura do Projeto

```
Conecte a Cidade/
├── main.py                     # Inicialização do jogo e loop principal
├── requirements.txt            # Dependências (pygame-ce, pytest)
├── pytest.ini                  # Configuração do pytest
├── README.md                   # Instruções de execução e documentação
├── src/
│   ├── __init__.py
│   ├── grafo.py                # Modelagem do grafo (vértices, arestas, pesos)
│   ├── algoritmos.py           # BFS, Kruskal, Prim, DSU, limite inferior
│   ├── geometria.py            # Testes de interseção de segmentos 2D
│   ├── fases.py                # Leitura e validação dos arquivos JSON
│   ├── jogo.py                 # Máquina de regras da partida (sem pygame)
│   ├── pontuacao.py            # Cálculo de aproveitamento, estrelas e pontos
│   └── interface.py            # Renderizador gráfico do mapa e HUD com pygame-ce
├── dados/
│   └── fases/
│       └── fase_01.json        # Configuração da Fase 1 (Tutorial)
├── ferramentas/
│   └── validar_fases.py        # Validador de consistência e solução ideal
├── tests/
│   ├── test_algoritmos.py      # Testes de Kruskal, Prim, BFS e DSU
│   ├── test_geometria.py       # Testes de interseção de retas e casos de borda
│   ├── test_fases.py           # Testes de carga e integridade da Fase 1
│   └── test_jogo.py            # Testes das regras de negócio e orçamento
└── docs/
    ├── CONCEITOS.md            # Relação matéria teórica -> funções do código
    └── DECISOES.md             # Diário de bordo de decisões de engenharia
```
