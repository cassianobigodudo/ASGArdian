# ASGArdian - Diretrizes de Versionamento e Automatização de Commits

Você é um agente de desenvolvimento integrado à IDE. Suas operações Git devem seguir estritamente as regras de padronização e atomização abaixo para garantir a conformidade com a avaliação do projeto.

Sempre commite com o usuário que está conectado com esse repositório

## 1. Padrão de Mensagem (Conventional Commits)
Todas as suas mensagens de commit automáticas devem seguir rigorosamente o formato:
`<tipo>(<escopo>): <descrição curta e direta em letras minúsculas>`

### Tipos Obrigatórios:
* `feat`: Implementação de novos nós, esquemas de estado ou integrações do LangGraph.
* `fix`: Correções de bugs de execução, loops infinitos no grafo ou vazamento de contexto.
* `docs`: Atualizações em arquivos de prompt ou markdown.
* `refactor`: Otimizações de código que não mudam a lógica do grafo.

### Exemplos de Escopos:
* `graph`, `tools`, `prompts`, `state`, `config`.

### Exemplos Válidos:
* `feat(state): define a estrutura inicial do agentstate com suporte a hitl`
* `feat(tools): integra a ferramenta de busca tavily ao fetch_guide_node`
* `fix(graph): corrige loop infinito na aresta condicional de analise de spoiler`

## 2. Regras de Ouro para Atomização (Não misture escopos)
Você deve pausar e realizar um commit imediatamente após finalizar cada bloco lógico isolado de código. Nunca acumule tarefas diferentes.

### Gatilhos Obrigatórios para Commit:
1. Assim que criar/modificar a classe `AgentState`.
2. Logo após finalizar a escrita completa e isolada de um único Nó do grafo.
3. Logo após ligar as arestas e compilar o `workflow.compile()`.
4. Sempre que salvar alterações em arquivos dentro da pasta `docs/`.

*Nota técnica para o agente:* Antes de commitar, valide a sintaxe do arquivo alterado para não quebrar a branch de desenvolvimento com erros de indentação ou importações ausentes.