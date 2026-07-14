# ASGArdian - Functional Specifications (Especificações Funcionais)

## 1. Fluxo de Entrada de Dados (Input Payload)
O sistema deve aceitar e processar obrigatoriamente as seguintes variáveis de entrada do usuário:
* `game_name` (String): Nome do jogo eletrônico (Ex: "Borderlands 2").
* `mission_name` (String): Nome da missão ou localização atual (Ex: "Lights Out").
* `current_issue` (String): Descrição em texto livre de onde o jogador está travado.
* `help_type` (Enum): Opção restrita entre "hint" (pista indireta) ou "answer" (solução direta).
* `player_inventory` (Lista de Strings): Itens ou habilidades relevantes que o jogador possui no momento.

## 2. Regras de Negócio e Comportamento

### RN01: Verificação de Pré-requisitos
* Se o guia gerado dinamicamente apontar que a resolução exige um item/habilidade que NÃO está presente em `player_inventory`, o fluxo de dicas padrão deve ser interrompido.
* A verificação de pré-requisitos **só é executada na primeira passagem** pelo fluxo. Quando `is_item_search=True`, o roteamento após `process_guide_node` ignora o `verify_requirements_node` e avança direto para `generate_help_node`, evitando loop infinito.

### RN02: Modos de Resposta
* **Modo hint:** A resposta não pode dar o passo a passo. Deve usar analogias ou apontar elementos visuais do cenário mapeados no guia para induzir o jogador a pensar.
* **Modo answer:** Fornece a sequência direta de comandos ou ações mecânicas de forma clara e objetiva.

### RN03: Bloqueio Estrito de Spoilers
* Nenhuma resposta gerada pode conter termos que descrevam o desfecho da missão atual, consequências narrativas futuras, mortes ou aparições surpresa de personagens.
* O filtro anti-spoiler (`critique_spoiler_node`) se aplica **tanto** à resposta do problema original **quanto** à resposta sobre como obter o item faltante.

### RN04: Interrupção de Estado (Human-in-the-loop)
* Quando o sistema detectar a ausência de um pré-requisito, o grafo DEVE ser interrompido usando persistência de estado (checkpointer) antes de executar a segunda busca.
* O sistema deve congelar a execução e aguardar uma confirmação explícita do usuário (`user_approval`).
* Se `user_approval` for "sim":
  1. O campo `original_issue` é preservado com o problema original do jogador.
  2. O campo `current_issue` é atualizado para `"como obter [missing_item] em [game_name]"`.
  3. A flag `is_item_search` é setada para `True`.
  4. O grafo reinicia a partir de `fetch_guide_node` com o novo contexto de busca.
* Se `user_approval` for "nao", o agente encerra o fluxo informando apenas que o progresso está bloqueado por falta do item.

### RN05: Controle de Loop (is_item_search)
* O campo `is_item_search` no `AgentState` é a salvaguarda que impede o grafo de entrar em loop infinito durante a busca pelo item faltante.
* Quando `True`, o roteamento após `process_guide_node` pula o `verify_requirements_node` e vai direto para `generate_help_node`.
* O valor padrão de `is_item_search` na inicialização do estado é sempre `False`.
