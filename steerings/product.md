# ASGArdian - Product Vision (Visão Geral do Produto)

## 1. O Problema
Jogadores de videogame frequentemente ficam travados em puzzles, missões complexas ou caminhos ocultos. Ao buscarem ajuda em detonados ou guias tradicionais na internet, eles são inevitavelmente expostos a grandes spoilers do enredo, mortes de personagens e reviravoltas da história que arruinam a experiência do jogo.

## 2. A Solução
O ASGArdian (Anti-Spoiler Gameplay Assistant) é um agente inteligente baseado em grafos que atua como um guia contextual dinâmico. O sistema recebe o cenário exato onde o jogador está travado e fornece apenas a pista sutil ou a resposta direta necessária para prosseguir, ocultando e filtrando de forma absoluta qualquer informação cronologicamente posterior no roteiro do jogo.

## 3. Funcionalidades Principais
* **Busca Dinâmica de Detonados:** Consulta IGN database (`guides_database.json`) com fallback para Groq/Gemini quando guia não encontrado. Suporta qualquer jogo sem base de dados local estática.
* **Validação de Pré-requisitos:** Identifica items, habilidades ou níveis necessários para aquela parte do jogo antes de fornecer a dica.
* **Interrupção Human-in-the-loop (HITL):** Caso falte um item essencial para progredir, o sistema pausa o fluxo de execução e pergunta ao usuário se ele deseja saber a localização do item.
* **Reuso Inteligente do Fluxo de Busca:** Quando o usuário aprova a busca pelo item faltante, o grafo reutiliza os mesmos nós `fetch_guide_node` e `process_guide_node` com um novo contexto de busca (`current_issue` atualizado para "como obter [item]"), evitando duplicação de lógica. A flag `is_item_search` no estado controla o roteamento para impedir loop infinito no `verify_requirements_node`.
* **Nível de Ajuda Customizável:** Permite ao usuário escolher entre receber uma dica sutil (focada em elementos do cenário) ou a resposta direta da mecânica.
* **Filtro Atômico Anti-Spoiler (Loop de Crítica):** Um nó crítico de auto-correção que revisa a resposta final contra as informações futuras do guia para garantir vazamento zero de história. Pode reescrever indefinidamente até passar na auditoria.
* **Regeneração de Dica ("Gerar Nova Dica"):** O usuário pode gerar uma nova resposta sem refazer a busca web. A flag `is_regenerating=True` faz o sistema pular diretamente para `generate_help_node`, reutilizando o guia já extraído.
* **Proteção Contra Loops:** Múltiplas camadas: contador por nó, timeout global, flag `is_item_search` para evitar re-verificação, `reset_execution_counters()` para resetar entre buscas.
