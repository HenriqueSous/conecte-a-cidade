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
- 2026-11-21: A fase 2 usa 8 casas e 14 ligações, com custos definidos à mão para oferecer rotas alternativas. O par é 79 e o orçamento é 111 pelo fator 1,40 da seção 8.
- 2026-11-21: O validador usa Prim com distâncias para medir a estratégia da vizinha mais próxima e soma os custos reais dos cabos selecionados.
- 2026-11-21: Encruzilhada usa um único cruzamento entre dois cabos baratos. O par sem cruzamentos é 74, a AGM convencional custa 66 e o orçamento é 98 pelo fator 1,32.
- 2026-11-21: A busca exata calcula o par no validador. Durante a partida, os cabos instalados também filtram as opções consideradas no limite inferior de custo restante.
- 2026-11-21: Entre Bairros tem dois pontos de cruzamento interdependentes. A melhor rede custa 108, um atalho permite concluir por 117 e combinar os dois atalhos exige pelo menos 132, acima do orçamento 128 calculado com o fator 1,18.
- 2026-11-21: Rede da Cidade tem três pontos de cruzamento, par 122 e orçamento 129. Trocar a ligação da casa 9 pelo cabo direto à central leva a rede ótima a 130.
- 2026-11-21: A conclusão da fase 5 identifica a campanha concluída, e a pontuação total soma os recordes das cinco fases.
