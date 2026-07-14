# ASGArdian - Guia de Conformidade e Critérios de Avaliação (Nota Máxima)

Você é um agente de desenvolvimento de IA integrado à IDE. Seu objetivo absoluto é garantir que o código, os commits e a documentação atendam à pontuação máxima (1,0 ou 2,0 dependendo do peso) de cada critério oficial da disciplina.

---

## 1. Gestão do Repositório e Produtividade (Peso: 1,0 ponto cada)

### Critério 1: Versionamento com branches e commits semânticos (Alvo: 1,0)
* **Regra estrita:** Os commits devem ser incrementais, claros e alinhados ao padrão do `git-conventions.md`.
* **Ação da IA:** Realize commits automáticos a cada bloco lógico concluído (ex: término de um nó, criação do estado). Nunca faça commits massivos acumulando tarefas distintas.

### Critério 2: Contribuição individual e produtividade (Alvo: 1,0)
* **Regra estrita:** O histórico do repositório deve provar o desenvolvimento ativo do projeto.
* **Ação da IA:** Garanta uma frequência saudável de commits estruturados, cobrindo tanto a implementação de funcionalidades no código quanto a escrita e refinamento dos markdowns de documentação.

---

## 2. Organização e Engenharia de Prompts (Peso: 2,0 pontos)

### Critério 3: Organização dos arquivos, documentação e prompts (Alvo: 2,0)
* **Regra estrita:** O repositório deve ser impecável visual e estruturalmente.
* **Ação da IA:** Mantenha a estrutura de pastas proposta. Garanta que o `README.md` contenha instruções claras de execução, exemplos reais de payload de entrada e texto de saída do ASGArdian. Salve e documente a evolução dos prompts em `docs/prompts/prompts.md`.

---

## 3. Estrutura e Engenharia do Agente (Peso: 1,0 ponto cada)

### Critério 4: Ideia do projeto e apresentação (Alvo: 1,0)
* **Regra estrita:** Alinhamento perfeito com o conceito de agentes orquestrados.
* **Ação da IA:** O código deve refletir exatamente o fluxo proposto para a apresentação de slides: um problema real (spoilers de gameplay), a solução do agente, suas entradas, saídas e controle de fluxo.

### Critério 5: Implementação do agente com LangGraph (Alvo: 1,0)
* **Regra estrita:** O coração da aplicação deve ser um grafo funcional.
* **Ação da IA:** Utilize o framework LangGraph criando um `StateGraph` explícito para ditar o fluxo de controle e tomada de decisão através do tráfego do `AgentState`. O grafo possui 5 nós: `fetch_guide_node`, `process_guide_node`, `verify_requirements_node`, `generate_help_node` e `critique_spoiler_node`. O reuso de nós via flag `is_item_search` é parte intencional da arquitetura.

### Critério 6: Uso de ferramenta integrada ao agente (Alvo: 1,0)
* **Regra estrita:** Ações autônomas e estruturadas usando ferramentas externas reais (nada de simulações em texto estático).
* **Ação da IA:** Garanta que o nó de busca utilize o Gemini integrado à ferramenta nativa `Google Search` para capturar dados dinâmicos da internet em tempo real durante a execução. Isso se aplica tanto à busca do detonado original quanto à busca direcionada ao item faltante quando `is_item_search=True`.

### Critério 7: Cuidados básicos de segurança (Alvo: 1,0)
* **Regra estrita:** Vazamento zero de chaves ou tokens.
* **Ação da IA:** Não exponha strings de credenciais no código-fonte. Utilize a biblioteca `python-dotenv` para carregar as chaves. Certifique-se de que o arquivo `.gitignore` oculte o `.env` e que exista um `.env.example` limpo apenas com as variáveis de modelo (sem os valores reais).

---

## 4. Gerenciamento de Estado Avançado (Peso: 2,0 pontos)

### Critério 8: Contexto, memória e validação básica (Alvo: 2,0)
* **Regra estrita:** Uso robusto de memória e prevenção de erros ou dados malformados.
* **Ação da IA:**
  1. Implemente validações nos nós (como garantir que o payload de entrada contenha todos os campos obrigatórios antes de rodar o grafo).
  2. Utilize o estado (`AgentState`) de forma contínua para apoiar as decisões das arestas condicionais, incluindo a flag `is_item_search` e o campo `original_issue` para preservação de contexto.
  3. Implemente a persistência de memória do LangGraph (`MemorySaver`) para gerenciar as threads de execução e viabilizar a interrupção Human-in-the-loop (HITL) configurada em `tech.md`.
  4. A flag `is_item_search` é um exemplo direto de gerenciamento de estado avançado: ela controla o roteamento condicional para evitar loop infinito sem adicionar nós desnecessários ao grafo.
