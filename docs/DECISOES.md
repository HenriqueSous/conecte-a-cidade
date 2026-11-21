# Registro de Decisões de Projeto

Este documento registra decisões pontuais de arquitetura e implementação tomadas durante o desenvolvimento.

- 2026-11-19: Utilizada resolução de 1000x680 com área do HUD nos primeiros 65px de altura conforme seção 11 do contexto.
- 2026-11-19: Chave canônica para arestas não orientadas fixada como (min(u, v), max(u, v)) em todas as estruturas.
- 2026-11-19: Fase 1 projetada com 5 casas e 7 ligações possíveis, par 46 e orçamento 74 (fator 1.60).
- 2026-11-19: Algoritmos Kruskal e Prim implementados com validação cruzada garantindo mesmo custo de árvore geradora mínima.
- 2026-11-19: Detecção de beco sem saída calculada usando contração de componentes e AGM das arestas restantes não usadas.
- 2026-11-21: Integrado o pacote visual da pasta `assets`, com desenhos do Pygame como alternativa para arquivos ausentes.
- 2026-11-21: O jogo verifica os arquivos de fase ao abrir e consulta a conclusão da fase anterior para liberar cada entrada válida.
- 2026-11-21: O jogo salva a conclusão e os recordes por fase em `progresso.json` antes de mostrar o resultado da partida.
