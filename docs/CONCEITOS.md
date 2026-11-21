# Mapeamento de Conceitos de Teoria dos Grafos (Matemática Discreta II)

Este documento relaciona os tópicos teóricos da disciplina com a respectiva implementação no código-fonte do jogo **Conecte a Cidade**.

---

## 1. Modelagem e Representação de Grafos
- **Conceito:** Grafo não orientado ponderado $G = (V, E, w)$, onde $V$ são os vértices (casas), $E$ são os pares não ordenados $\{u, v\}$ de ligações viáveis e $w(u, v)$ são os custos de instalação.
- **Arquivo:** `src/grafo.py`
- **Classe:** `Grafo`
- **Métodos principais:**
  - `adicionar_aresta(u, v, custo)`: Adiciona a aresta com chave canônica `(min(u, v), max(u, v))` e insere na lista de adjacência bidirecional.
  - `vizinhos(u)`: Vizinhança aberta $N(u)$.
  - `custo(u, v)` e `existe(u, v)`: Acesso e checagem da função de peso $w$.

---

## 2. Busca em Largura (BFS) e Componentes Conexas
- **Conceito:** Travessia sistemática por níveis utilizando fila (FIFO) para identificar todos os vértices acessíveis a partir de uma origem e verificar se o grafo é conexo.
- **Arquivo:** `src/algoritmos.py`
- **Funções:**
  - `bfs_componente(grafo, inicio)`: Retorna o conjunto de casas que pertencem à componente conexa da central (casa 0).
  - `verificar_conectividade(grafo, inicio)`: Verifica se a componente alcança todos os $n$ vértices do grafo.
- **Uso no jogo:** No arquivo `src/jogo.py` (`_atualizar_estado`), chamado a cada construção para acender as casas na rede e checar a vitória.

---

## 3. Detecção de Ciclos e Cabos Redundantes
- **Conceito:** Um ciclo simples ocorre quando uma nova aresta liga dois vértices que já possuem um caminho alternativo entre si na mesma componente.
- **Arquivo:** `src/algoritmos.py`
- **Função:** `detectar_cabo_redundante(n, arestas_construidas, u, v)`
- **Uso no jogo:** Em `src/jogo.py` e `src/interface.py`, o cabo redundante é identificado e desenhado em **laranja**, fornecendo feedback visual discreto.

---

## 4. Partições e Estrutura União-Busca (Disjoint Set Union - DSU)
- **Conceito:** Manutenção de famílias de conjuntos disjuntos com operações eficientes de busca de representante (`encontrar`) e união de classes (`unir`), utilizando compressão de caminho e união por posto.
- **Arquivo:** `src/algoritmos.py`
- **Classe:** `UniaoBusca`
- **Uso no jogo:** Utilizada no algoritmo de Kruskal e na detecção de ciclos / contração de componentes.

---

## 5. Árvore Geradora Mínima (Algoritmo de Kruskal)
- **Conceito:** Algoritmo guloso baseado em ordenação de arestas. Seleciona as arestas de menor custo que conectam componentes disjuntas até cobrir todos os vértices com $n - 1$ arestas, evitando ciclos via União-Busca.
- **Arquivo:** `src/algoritmos.py`
- **Função:** `kruskal(n, arestas)`
- **Uso no jogo:** Calcula o par (solução ótima) das fases sem restrição de planaridade e calcula o limite inferior para detecção de becos sem saída.

---

## 6. Árvore Geradora Mínima (Algoritmo de Prim)
- **Conceito:** Algoritmo guloso centrado nos vértices. Constrói a árvore adicionando progressivamente a aresta de corte de menor peso que liga um vértice visitado a um não visitado, utilizando fila de prioridades (heap mínimo).
- **Arquivo:** `src/algoritmos.py`
- **Função:** `prim(grafo, inicio=0)`
- **Uso no jogo:** Utilizado na ferramenta `ferramentas/validar_fases.py` para validação cruzada independente com Kruskal.

---

## 7. Planaridade e Interseção Geométrica de Segmentos
- **Conceito:** Grafos planares e testes de orientação 2D via produto vetorial para determinar se dois segmentos de reta se cruzam.
- **Arquivo:** `src/geometria.py`
- **Funções:**
  - `orientacao(p, q, r)`: Produto vetorial para orientação horária, anti-horária ou colinear.
  - `segmentos_se_cruzam(p1, q1, p2, q2)`: Regra que bloqueia cruzamentos em X, toques em T e sobreposição colinear, permitindo conexões em extremos compartilhados.
- **Uso no jogo:** Aplicado em fases com restrição de não cruzamento (`sem_cruzamento: true`).

---

## 8. Busca Exata com Poda

- **Arquivo e função** — `src/algoritmos.py`, em `buscar_agm_sem_cruzamentos`.
- **Busca** — percorre as ligações por custo e explora a decisão de incluir ou excluir cada uma. A inclusão descarta cabos conflitantes dos passos seguintes e só é aceita quando une componentes diferentes.
- **Poda** — contrai os componentes já ligados e usa a AGM restante como limite inferior. Se esse limite e o gasto atual já atingem o custo da melhor rede encontrada, o ramo pode ser descartado.
- **Uso** — o validador calcula o par de Encruzilhada. A partida usa o par gravado no JSON.
