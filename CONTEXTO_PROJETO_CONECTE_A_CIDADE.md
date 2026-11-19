# Conecte a Cidade — Documento de Contexto e Regras de Desenvolvimento

> **Para a IA que vai desenvolver o projeto:** este documento é a fonte única de verdade. Leia-o inteiro antes de escrever qualquer código. As seções 1 a 3 explicam o contexto; as seções 4 a 9 definem o que construir; as seções 10 a 14 definem **como** construir; as seções 15 a 17 definem a ordem de trabalho e os critérios de aceite.

---

## 1. Contexto acadêmico

- **Disciplina:** Matemática Discreta II, curso de Bacharelado em Sistemas de Informação.
- **Enunciado do professor:** *"O projeto da disciplina refere-se ao uso de grafos na modelagem de um jogo de autoria do próprio indivíduo ou grupo, ou estudo de um jogo existente do ponto de vista da Teoria dos Grafos."*
- **Escolha da equipe:** criar um jogo autoral, digital, desenvolvido por programação.
- **Conteúdo da disciplina (apostila):** representação de grafos, isomorfismo, caminhos, conectividade, Euler, Hamilton, caminho mais curto (Dijkstra), planaridade, coloração, árvores, travessias (DFS/BFS) e árvores geradoras mínimas (Prim e Kruskal).

### O que isso implica para o projeto

1. O grafo **é a estrutura do jogo**, não um enfeite. Vértices, arestas e pesos precisam existir de forma explícita no código.
2. Os algoritmos da disciplina devem ser **implementados à mão** pela equipe (com sua IA), e não importados de bibliotecas. Isso é o que será avaliado.
3. O jogo **não é educativo**. O jogador não precisa aprender teoria: ela fica por baixo, nos cálculos e nas regras. O aspecto acadêmico aparece no código e no relatório, e não em textos explicativos dentro do jogo.

## 2. Perfil da equipe (muito importante)

- A equipe é composta por **iniciantes completos**, sem experiência em desenvolvimento de jogos.
- Todo o código será **lido, entendido, explicado e defendido** pelos integrantes em uma apresentação.
- Por isso, **clareza vale mais do que sofisticação**. Veja as regras da seção 10.

## 3. Restrições técnicas fixas (não negociáveis)

| Item | Decisão |
|---|---|
| Linguagem | **Python 3.10 ou superior** |
| Biblioteca gráfica | **pygame-ce** (`pip install pygame-ce`). Nunca instalar `pygame` junto com `pygame-ce`, porque conflitam |
| Engine | **Nenhuma.** Sem Godot, Unity etc. |
| Dimensão | 2D |
| Dependências de runtime | Apenas `pygame-ce` e a biblioteca padrão do Python |
| Bibliotecas de grafos | **Proibido** usar NetworkX ou similares na lógica do jogo. É permitido usá-las **somente em testes**, para validar os resultados |
| Arte | Nenhum arquivo de imagem é obrigatório. Tudo é desenhado com formas do pygame (círculos, linhas, polígonos, retângulos) |
| Idioma | Interface, comentários, nomes de variáveis e funções em **português (sem acentos nos identificadores)** |
| Plataforma | Deve rodar em Windows, Linux e macOS com `python main.py` |

---

## 4. Descrição do jogo

**Conecte a Cidade** é um jogo 2D de puzzle e estratégia no qual o jogador assume o papel de um planejador de redes responsável por conectar as casas de um bairro. O objetivo de cada fase é ligar todas as casas à rede (de internet, energia ou outro serviço) utilizando o menor custo financeiro possível, respeitando um orçamento limitado. Ao final, o jogo compara a solução do jogador com a solução ideal e atribui uma pontuação de acordo com o aproveitamento obtido.

O mapa de cada fase é modelado como um grafo não orientado e ponderado: as casas são os vértices, as ligações possíveis entre elas são as arestas, e o custo de cada ligação é o peso da aresta. A fase é concluída quando o grafo formado pelas ligações escolhidas se torna conexo, e a solução ideal é obtida por meio dos algoritmos de árvore geradora mínima de Prim e Kruskal. Além deles, o projeto aplica outros conceitos da disciplina, como conectividade e planaridade, em fases nas quais as ligações não podem se cruzar. A dificuldade é crescente ao longo das fases.

**Número de fases: 10.**

---

## 5. Modelagem formal (grafo)

Cada fase é um grafo **G = (V, E, w)**:

- **V**: conjunto de casas (vértices), numeradas de `0` a `n-1`. Cada vértice tem uma posição `(x, y)` na tela.
- **E**: conjunto de **ligações possíveis** (arestas não orientadas), definidas explicitamente na fase. **Não** é um grafo completo: apenas os pares listados na fase podem ser ligados.
- **w: E → inteiros positivos**: o custo de cada ligação, **definido explicitamente no arquivo da fase**.
- **Central**: o vértice `0` é a central (fonte da rede). Uma casa está "na rede" se existe caminho de cabos construídos entre ela e a central.
- **Solução do jogador**: um subconjunto `S ⊆ E` de cabos construídos. O grafo `H = (V, S)` é o que será avaliado.
- **Fase concluída** ⇔ `H` é conexo (todas as casas estão na mesma componente da central).
- **Solução ideal (par)**: o custo mínimo de um subconjunto `S` que torne `H` conexo, respeitando as regras da fase. Sem restrição de cruzamento, é o custo de uma **árvore geradora mínima** de G.

### Regra de custo (importante)

O custo **não** deve ser calculado a partir da distância na tela. Em testes anteriores, usar só a distância tornou a solução óbvia a olho nu. Portanto:

- Os custos são **escritos manualmente no arquivo JSON da fase**.
- Eles devem criar **armadilhas**: uma ligação visualmente curta pode ser cara, e uma longa pode ser barata.
- O custo é sempre exibido sobre a linha da ligação.

---

## 6. Regras do jogo (mecânica)

### 6.1 Construir e remover cabos

1. O jogador clica em uma casa (ela fica destacada) e depois em outra.
2. Se existe uma ligação possível entre as duas, o cabo é **construído**: o custo é somado ao gasto e a linha passa de fina a grossa.
3. Se **não** existe ligação possível, o jogo mostra uma mensagem curta e a seleção é limpa.
4. Clicar de novo nas mesmas duas casas **remove** o cabo e devolve o custo (comportamento de alternância).
5. Clicar no mesmo vértice duas vezes, no fundo do mapa ou com o botão direito cancela a seleção.
6. Uma casa pode ter **quantas ligações** o jogador quiser.
7. **Desfazer (Z)** remove o último cabo construído, mantendo uma pilha de histórico.

### 6.2 Orçamento

- Cada fase tem um **orçamento rígido**, definido no JSON.
- Se o custo do novo cabo fizer o gasto total ultrapassar o orçamento, o cabo **não é construído** e o jogo avisa.
- O orçamento é calculado como `ceil(par × fator)`. O fator diminui ao longo das fases (veja a seção 7).

### 6.3 Vitória

- Após cada construção, verificar a conectividade com **BFS** (ou DFS) a partir da central.
- Se todas as casas estão na rede, a fase termina com vitória e a tela de resultado é exibida.

### 6.4 Becos sem saída (obrigatório)

Como o orçamento é rígido, o jogador pode ficar sem como terminar. O jogo deve detectar isso e avisar:

- Calcular um **limite inferior** do custo restante: contrair as componentes atuais e calcular a árvore geradora mínima das arestas que ainda não foram usadas (respeitando o bloqueio por cruzamento, se existir).
- Se esse limite for maior que o orçamento restante, mostrar a mensagem *"Com esse orçamento não dá para conectar tudo. Desfaça ou reinicie."*
- Não encerrar a fase automaticamente. O jogador decide se desfaz ou reinicia.

### 6.5 Cabo redundante (feedback visual discreto)

- Um cabo que liga duas casas que **já estavam conectadas entre si** (forma um ciclo) é desenhado em **laranja**, em vez de azul.
- Não exibir texto didático sobre isso, só a cor.

### 6.6 Regra de planaridade (sem cruzamento)

Em fases com a regra `sem_cruzamento: true`:

- Um cabo **não pode ser construído** se o seu segmento de reta cruzar o de um cabo já construído.
- Ao passar o mouse para escolher a segunda casa, a prévia fica **vermelha** e a tentativa de construir mostra *"Este cabo cruzaria outro cabo."*
- **Dois segmentos que compartilham um extremo (a mesma casa) não contam como cruzamento.**
- Casos de borda a tratar: segmentos colineares com sobreposição contam como cruzamento; um segmento que apenas toca um vértice de outro (sem ser seu extremo) conta como cruzamento.
- Apenas os **cabos construídos** bloqueiam. As linhas finas das ligações possíveis não bloqueiam nada.
- A verificação é **geométrica** (posições na tela), e não um teste formal de planaridade do grafo.

---

## 7. Pontuação

- **Aproveitamento** = `par ÷ custo_do_jogador × 100`, limitado a 100 %.
- **Pontos da fase** = `round(1000 × par ÷ custo_do_jogador)`. O máximo é 1000, quando o custo é igual ao par.
- **Estrelas:**
  - ★★★: custo igual ao par.
  - ★★: aproveitamento ≥ 85 %.
  - ★: fase concluída.
- Guardar o **melhor resultado** de cada fase.
- Pontuação total = soma dos melhores pontos de cada fase.
- A tela de resultado mostra: custo do jogador, par, aproveitamento, estrelas e pontos.

---

## 8. Design das 10 fases

Cada fase é um arquivo JSON **criado à mão** (não gerado aleatoriamente em tempo de execução). A dificuldade cresce de forma gradual. Os números abaixo são **metas de design**, e a IA deve ajustá-los depois de validar com a ferramenta da seção 12.

| Fase | Casas | Ligações possíveis (aprox.) | Fator do orçamento | Sem cruzamento | Objetivo de design |
|---|---|---|---|---|---|
| 1 | 5 | 6 a 8 | 1,60 | Não | Tutorial. Aprender a clicar e ligar |
| 2 | 6 | 8 a 10 | 1,50 | Não | Perceber que cabos extras gastam dinheiro |
| 3 | 7 | 10 a 13 | 1,40 | Não | Primeira armadilha: custo curto não significa barato |
| 4 | 8 | 12 a 16 | 1,30 | Não | Várias rotas parecidas, exige comparar |
| 5 | 9 | 14 a 19 | 1,22 | Não | Orçamento apertado, sem margem para erro |
| 6 | 9 | 14 a 19 | 1,40 | **Sim** | Introduz a regra de cruzamento (orçamento folgado de novo) |
| 7 | 10 | 16 a 22 | 1,30 | **Sim** | Cruzamento + várias armadilhas |
| 8 | 11 | 18 a 25 | 1,20 | **Sim** | Cruzamento + orçamento apertado |
| 9 | 12 | 20 a 28 | 1,12 | **Sim** | Pouca folga, exige planejar a ordem |
| 10 | 14 | 24 a 34 | 1,05 | **Sim** | Desafio final, margem mínima |

### Critérios de qualidade de cada fase

- O grafo é **conexo** (existe solução).
- Os custos **não são proporcionais à distância**. Mostrar isso em pelo menos 30 % das ligações a partir da fase 3.
- A solução ótima **não deve ser obtida** ligando sempre a vizinha mais próxima. A ferramenta de validação deve emitir um aviso se isso acontecer a partir da fase 3.
- Nas fases com `sem_cruzamento`, deve haver **pelo menos uma ligação barata que cruza** outra (armadilha) e, idealmente, o par exige abrir mão dela.
- Nenhuma ligação deve atravessar uma casa que não seja seu extremo (evitar ambiguidade visual).
- As casas ficam dentro da área jogável e com distância mínima entre si de pelo menos 80 px.
- Os rótulos de custo não devem ficar sobrepostos. Ajustar posições se necessário.

---

## 9. Algoritmos obrigatórios (implementação própria)

Todos em `src/algoritmos.py` e em `src/geometria.py`, **sem importar pygame** e sem bibliotecas de grafos.

| Algoritmo | Uso no jogo |
|---|---|
| **Kruskal** (com união-busca / union-find) | Calcula o par da fase sem restrição de cruzamento |
| **Prim** | Segundo cálculo independente do par. Serve para **validação cruzada**: o custo deve ser igual ao de Kruskal em todas as fases |
| **BFS** (ou DFS) | Verifica a conectividade, identifica as casas na rede e detecta cabo redundante |
| **Interseção de segmentos** (teste de orientação) | Regra de cruzamento das fases 6 a 10 |
| **Busca exata com poda** (backtracking + limite inferior por AGM) | Calcula o par nas fases com `sem_cruzamento`, onde Kruskal/Prim sozinhos **não bastam** (veja a nota abaixo) |

### Nota importante sobre o par nas fases com cruzamento proibido

A árvore geradora mínima comum pode conter cabos que se cruzam. Nas fases 6 a 10, o par precisa ser o **menor custo entre as soluções que não têm cruzamentos**. Por isso:

- A ferramenta de validação deve calcular esse par por **busca exata**: enumerar as arestas em ordem de custo, decidir incluir ou excluir cada uma, rejeitar a escolha que cause cruzamento ou ciclo, e **podar** quando `custo_atual + limite_inferior ≥ melhor_encontrado`. O limite inferior pode ser a AGM do que resta, ignorando os cruzamentos.
- Para até 14 casas e cerca de 34 arestas, isso roda rápido.
- O par calculado é **gravado no JSON** da fase (`par`). O jogo em execução **lê** esse valor e não recalcula.
- Sempre vale `par_com_cruzamento ≥ custo_AGM_sem_restricao`. A ferramenta deve verificar isso.

---

## 10. Regras de desenvolvimento (como escrever o código)

### 10.1 Estilo orientado a iniciantes

1. **Simplicidade primeiro.** Prefira funções e classes simples a abstrações avançadas. Evite metaprogramação, decoradores complexos, herança profunda, padrões de projeto elaborados e `lambda` encadeadas.
2. **Comentários em português** explicando o *porquê*, e não só o *o quê*, principalmente nos algoritmos. Cada função de algoritmo tem uma docstring dizendo: o que faz, os parâmetros, o retorno e **qual conceito da disciplina ela implementa**.
3. Funções curtas (idealmente até 30 linhas), com um único objetivo.
4. Nomes descritivos em português, sem abreviações obscuras. Constantes em `MAIUSCULAS`.
5. Sem "código esperto". Se houver duas formas de fazer, escolha a mais fácil de explicar.
6. Dicas de tipo (`type hints`) são bem-vindas nas funções de lógica, mas opcionais.
7. Cada arquivo começa com um comentário de 2 a 4 linhas dizendo para que serve.

### 10.2 Separação de responsabilidades

- **A lógica não conhece a interface.** `grafo.py`, `algoritmos.py`, `geometria.py`, `fases.py` e `jogo.py` **não podem** importar `pygame`.
- **A interface não toma decisões de regra.** Ela só chama métodos do jogo e desenha o estado.
- O estado do jogo vive em um objeto (`Jogo`) que pode ser criado e testado sem abrir janela.

### 10.3 Dados e fases

- Fases em **JSON** em `dados/fases/`. Para criar ou alterar uma fase, não deve ser necessário mexer em código.
- Ao carregar, validar a fase e mostrar um erro claro se ela estiver inválida (campo ausente, aresta apontando para vértice inexistente, grafo desconexo).

### 10.4 Robustez

- O jogo nunca deve travar por um clique inesperado. Cliques fora do mapa, cliques rápidos e teclas repetidas são tratados.
- Se o arquivo de progresso estiver ausente ou corrompido, o jogo recria um progresso vazio e continua.
- Taxa de quadros fixa em 60 FPS, e o jogo só redesenha o necessário.

### 10.5 Proibições

- Não usar `NetworkX`, `igraph` etc. na lógica.
- Não usar engine, nem `pygame_gui` ou outras bibliotecas de interface. Os botões são desenhados e tratados manualmente.
- Não adicionar dependências sem necessidade.
- Não colocar texto didático sobre teoria dos grafos na interface do jogo.
- Não escrever tudo em um arquivo só (exceto em protótipos descartáveis).
- Não reescrever a arquitetura "por gosto" no meio do desenvolvimento.

---

## 11. Arquitetura e estrutura de arquivos

```
conecte-a-cidade/
├── main.py                    # ponto de entrada: inicia o pygame e o loop principal
├── requirements.txt           # pygame-ce
├── README.md                  # como instalar, rodar, jogar e criar fases
├── src/
│   ├── grafo.py               # classe Grafo (vértices, arestas, pesos, vizinhança)
│   ├── algoritmos.py          # BFS, Kruskal, Prim, união-busca, busca exata com poda
│   ├── geometria.py           # interseção de segmentos
│   ├── fases.py               # carregar e validar fases em JSON
│   ├── jogo.py                # regras e estado da partida (sem pygame)
│   ├── pontuacao.py           # aproveitamento, estrelas e pontos
│   ├── progresso.py           # salvar e carregar progresso (JSON local)
│   ├── interface.py           # desenho do mapa, casas, cabos e HUD
│   └── telas.py               # menu, seleção de fases, jogo, resultado, pausa
├── dados/
│   └── fases/
│       ├── fase_01.json
│       └── ... fase_10.json
├── ferramentas/
│   └── validar_fases.py       # valida as fases e calcula/confere o par
├── tests/
│   ├── test_algoritmos.py
│   ├── test_geometria.py
│   ├── test_jogo.py
│   └── test_fases.py
└── docs/
    └── CONCEITOS.md           # mapa conceito da disciplina → arquivo/função (para o relatório)
```

### Formato do arquivo de fase (JSON)

```json
{
  "id": 6,
  "nome": "Sem cruzar!",
  "orcamento": 52,
  "par": 37,
  "sem_cruzamento": true,
  "casas": [
    { "id": 0, "x": 120, "y": 300, "central": true },
    { "id": 1, "x": 300, "y": 180 },
    { "id": 2, "x": 310, "y": 420 }
  ],
  "ligacoes": [
    { "de": 0, "para": 1, "custo": 6 },
    { "de": 0, "para": 2, "custo": 9 },
    { "de": 1, "para": 2, "custo": 4 }
  ]
}
```

Regras do formato:

- `id` da casa vai de 0 a n-1, e a casa `0` é sempre a central.
- `ligacoes` são **não orientadas** e sem duplicatas (`de < para` por convenção).
- `custo` é um inteiro positivo.
- `par` é calculado pela ferramenta de validação (seção 12) e **gravado no arquivo**. O orçamento deve ser `ceil(par × fator)`, conforme a tabela da seção 8.
- Resolução lógica fixa da área jogável: **1000 × 680**, com uma faixa superior (HUD) de cerca de 65 px.

### Classe `Grafo` (referência mínima)

```python
class Grafo:
    def __init__(self, n): ...
    def adicionar_aresta(self, u, v, custo): ...
    def custo(self, u, v): ...          # None se não existir
    def existe(self, u, v): ...
    def vizinhos(self, u): ...
    def arestas(self): ...              # lista de (u, v, custo) com u < v
```

Usar a chave canônica `(min(u, v), max(u, v))` para arestas não orientadas.

---

## 12. Ferramenta de validação (`ferramentas/validar_fases.py`)

Rodar com `python ferramentas/validar_fases.py`. Para cada fase, deve:

1. Checar que o JSON é válido e que o grafo é **conexo**.
2. Calcular o par com **Kruskal** e com **Prim** e **falhar** se divergirem.
3. Se `sem_cruzamento`, calcular o par com a **busca exata**, conferir `par_exato ≥ custo_AGM` e gravar o valor.
4. Conferir que o orçamento é coerente com `ceil(par × fator)` da tabela.
5. Avisar (sem falhar) se a heurística "ligar sempre a vizinha mais próxima" atingir o par a partir da fase 3.
6. Avisar se houver rótulos de custo sobrepostos ou ligações que atravessem outra casa.
7. Imprimir um resumo: casas, ligações, par, orçamento, folga e tempo de cálculo.

---

## 13. Interface e experiência

### Telas

1. **Menu principal:** Jogar, Como jogar (3 linhas de instrução), Sair.
2. **Seleção de fases:** grade com as 10 fases, estrelas obtidas e fases **bloqueadas** até concluir a anterior.
3. **Jogo:** mapa + HUD.
4. **Resultado:** custo, par, aproveitamento, estrelas, pontos e botões *Repetir* e *Próxima fase*.
5. **Pausa (ESC):** Continuar, Reiniciar, Voltar ao menu.

### HUD durante a partida

- Número da fase e nome.
- Casas na rede: `x / n`.
- Gasto, orçamento e restante (o restante fica vermelho quando é pequeno).
- Mensagem de feedback de uma linha.
- Indicação de que a fase tem a regra *sem cruzamento*.

### Desenho do mapa

- Ligações possíveis: linhas finas cinza, com o **custo em um rótulo** no ponto médio.
- Cabos construídos: linhas grossas azuis (laranja se redundantes), rótulo destacado.
- Casas: ícone simples de casinha desenhado com formas. **A central é diferente** (ícone de raio ou torre).
- Casas na rede **acendem** em dourado, com um halo suave. As isoladas ficam cinzas.
- Ao escolher a primeira casa, uma linha de prévia acompanha o mouse. Sobre uma segunda casa, a prévia mostra o custo e fica branca (válida) ou vermelha (inválida).
- Paleta sugerida: fundo azul-escuro, azul-ciano nos cabos, dourado nas casas ligadas. O contraste do texto deve ser bom.
- Fonte padrão do pygame é aceitável. Fontes personalizadas são opcionais.

### Controles

| Ação | Controle |
|---|---|
| Selecionar casa / ligar | Botão esquerdo do mouse |
| Cancelar seleção | Botão direito ou clique no fundo |
| Desfazer | `Z` |
| Reiniciar fase | `R` |
| Pausa / voltar | `ESC` |

---

## 14. Persistência

- Arquivo `progresso.json` ao lado do jogo, com: fases concluídas, melhores custo, estrelas e pontos por fase.
- Salvar ao concluir uma fase. Carregar ao iniciar.
- A fase `n+1` é liberada ao concluir a fase `n`.
- Um modo de desenvolvimento (por exemplo, a variável de ambiente `CONECTE_DEV=1`) libera todas as fases para testes.

---

## 15. Plano de trabalho (marcos)

Cada marco deve **terminar com o jogo rodando**. Não avance para o próximo se o anterior não funcionar e não tiver testes.

1. **Núcleo de grafos:** `grafo.py`, `algoritmos.py` (BFS, união-busca, Kruskal, Prim) e testes. Sem pygame.
2. **Geometria e fases:** `geometria.py`, `fases.py`, JSON de exemplo (fase 1) e validação.
3. **Regras do jogo:** `jogo.py` e `pontuacao.py` completos, testados sem janela (construir, remover, desfazer, orçamento, vitória, beco sem saída, cruzamento).
4. **Interface mínima jogável:** janela, mapa, clique para ligar, HUD básico. Fase 1 jogável do começo ao fim.
5. **Telas e fluxo:** menu, seleção, resultado, pausa, progresso.
6. **As 10 fases:** criar os JSON, rodar a validação, ajustar custos, orçamentos e posições.
7. **Busca exata com poda** e par das fases 6 a 10.
8. **Acabamento:** halo das casas acesas, animações leves, mensagens, correção de rótulos sobrepostos.
9. **Documentação:** `README.md`, `docs/CONCEITOS.md`, revisão de comentários.

---

## 16. Testes obrigatórios

Usar `pytest` (ou `unittest`). Mínimo:

- **Algoritmos:** Kruskal e Prim dão o mesmo custo em grafos conhecidos e em grafos aleatórios pequenos (comparar também com NetworkX, *apenas nos testes*). BFS identifica as componentes corretamente. União-busca funciona.
- **Geometria:** cruzamento em X, extremo compartilhado (não cruza), toque em T (cruza), colinear sobreposto (cruza), colinear separado (não cruza), segmentos paralelos.
- **Jogo:** construir e remover; desfazer; orçamento excedido bloqueia; vitória ao conectar tudo; cabo redundante identificado; cruzamento bloqueado só quando a regra está ativa; beco sem saída detectado; reiniciar volta ao estado inicial.
- **Fases:** as 10 fases carregam, são conexas, e `par` coincide com o recalculado.
- **Pontuação:** custo igual ao par dá 3 estrelas e 1000 pontos; limites de 85 % corretos.

---

## 17. Critérios de aceite (definição de pronto)

- [ ] `python main.py` abre o jogo em qualquer sistema com Python 3.10+ e `pygame-ce`.
- [ ] As 10 fases existem, são jogáveis e a dificuldade cresce visivelmente.
- [ ] As fases 6 a 10 impõem a regra de não cruzamento, com feedback claro.
- [ ] O par de cada fase é confirmado por Kruskal **e** Prim (e pela busca exata nas fases com cruzamento).
- [ ] Nenhuma fase é resolvida ligando sempre a vizinha mais próxima (aviso resolvido ou justificado).
- [ ] A lógica funciona sem `pygame` (os testes passam sem abrir janela).
- [ ] Nenhum algoritmo de grafos vem de biblioteca externa na lógica do jogo.
- [ ] O código está comentado em português e cada algoritmo cita o conceito da disciplina.
- [ ] `docs/CONCEITOS.md` mapeia cada conceito a um arquivo e a uma função.
- [ ] O progresso é salvo e carregado, e um arquivo corrompido não derruba o jogo.
- [ ] Os testes passam e `validar_fases.py` roda sem erros.

---

## 18. Escopo

### Obrigatório
Tudo das seções 4 a 17.

### Opcional (somente depois de todo o resto estar pronto e aprovado)
Estes itens **não** devem ser feitos antes. Se a IA tiver dúvida, deve deixá-los de fora:

- Sons e música.
- Animação passo a passo do Kruskal mostrando a solução ideal no fim da fase.
- Terrenos (rio, morro) com custo por região e cálculo com Dijkstra.
- Eventos durante a fase (cabo cortado, casa nova).
- Modo sandbox / editor de fases dentro do jogo.
- Sprites e artes externas.

---

## 19. Como a IA deve trabalhar

1. **Não peça confirmação para decisões pequenas.** Escolha a opção mais simples, que respeite este documento, e registre em `docs/DECISOES.md` (uma linha por decisão).
2. **Entregue por marcos** (seção 15). A cada marco, informe: o que foi feito, como rodar e como testar.
3. Se este documento for **ambíguo ou contraditório**, aponte o problema, escolha a interpretação mais simples e siga em frente.
4. Ao terminar cada arquivo, **releia-o como se fosse um aluno iniciante**: se algo for difícil de explicar, simplifique.
5. Ao final, entregue uma **lista curta de "pontos para explicar na apresentação"**: onde estão a modelagem do grafo, o Kruskal, o Prim, a BFS, a regra de cruzamento e a busca exata.

---

## 20. Glossário rápido

| Termo | Significado no projeto |
|---|---|
| Casa | Vértice do grafo |
| Central | Vértice `0`, origem da rede |
| Ligação possível | Aresta de E, listada na fase |
| Cabo | Ligação que o jogador construiu (aresta de S) |
| Custo | Peso da aresta |
| Orçamento | Limite máximo de gasto na fase |
| Par | Custo mínimo possível da fase (solução ideal) |
| Aproveitamento | `par ÷ custo_do_jogador` |
| Cabo redundante | Cabo que fecha um ciclo entre casas já conectadas |
| Beco sem saída | Estado em que o orçamento restante não basta para conectar tudo |
