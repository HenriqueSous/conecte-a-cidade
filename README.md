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

### 3. Executar o Jogo
```bash
python main.py
```

O jogo abre no menu principal. **Jogar** inicia a primeira fase disponível ainda não concluída. **Selecionar Fase** permite repetir fases desbloqueadas e mostra as estrelas conquistadas. Os espaços reservados para fases futuras aparecem como **Em breve**.

Conclua **Primeiras Conexões** para liberar a fase 2, **Rotas do Bairro**. Ao terminar a fase 2, você libera **Encruzilhada**. Nessa fase, cabos instalados podem bloquear novas conexões. A prévia fica vermelha ao apontar para uma ligação bloqueada.

---

## 🎮 Como Jogar

| Ação | Comando |
|---|---|
| **Selecionar casa / Criar cabo** | Clique com o **Botão Esquerdo** na primeira casa e depois na segunda |
| **Remover cabo existente** | Clique novamente nas duas casas do cabo (alternância) |
| **Cancelar seleção** | Clique com o **Botão Direito** ou no fundo do mapa |
| **Desfazer última ação** | Tecla **Z** |
| **Reiniciar fase** | Tecla **R** |
| **Pausar ou continuar** | Tecla **ESC** |

Ao concluir uma fase, o jogo grava a conclusão e os recordes em `progresso.json`, ao lado de `main.py`. Esse arquivo é carregado automaticamente na próxima execução. Cada nova fase deve ter um JSON válido em `dados/fases/`, com nome `fase_NN.json` e ID correspondente. A fase fica disponível se a anterior já tiver sido concluída.

### Dicas de Estratégia
- **Casas ligadas à rede** acendem em **dourado**. As isoladas permanecem em cinza escuro.
- **Cabos normais** aparecem em **azul ciano**.
- **Cabos redundantes** (que fecham ciclos desnecessários) aparecem em **laranja**.
- Ao final, sua pontuação e estrelas (★ a ★★★) são calculadas comparando seu gasto total com o **par**, o menor custo possível dentro das regras da fase.

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
A ferramenta verifica o JSON e o orçamento, compara **Kruskal e Prim** e avisa sobre problemas de legibilidade do mapa. Em **Encruzilhada**, ela também usa busca exata com poda para conferir o par sem cruzamentos. A opção `--gravar-par` atualiza o par e o orçamento dos mapas com essa restrição.

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
│   ├── interface.py            # Renderizador do mapa, HUD e painel de vitória
│   ├── telas.py                # Menu, seleção de fases, instruções e pausa
│   └── progresso.py            # Leitura e salvamento dos recordes da campanha
├── dados/
│   └── fases/
│       ├── fase_01.json        # Primeiras Conexões
│       ├── fase_02.json        # Rotas do Bairro
│       └── fase_03.json        # Encruzilhada
├── ferramentas/
│   └── validar_fases.py        # Validador de consistência e solução ideal
├── tests/
│   ├── test_algoritmos.py      # Testes de Kruskal, Prim, BFS e DSU
│   ├── test_geometria.py       # Testes de interseção de retas e casos de borda
│   ├── test_fases.py           # Testes de carregamento e design das fases
│   ├── test_jogo.py            # Testes das regras de negócio e orçamento
│   └── test_menu.py            # Testes de navegação e progresso
└── docs/
    ├── CONCEITOS.md            # Relação matéria teórica -> funções do código
    └── DECISOES.md             # Diário de bordo de decisões de engenharia
```
