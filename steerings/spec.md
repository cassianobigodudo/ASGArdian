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


## 3. Topologia do Grafo (LangGraph) - Implementação Real

### Nós (Nodes):
1. **`fetch_guide_node`**: 
   - Busca detonado IGN no `guides_database.json` usando `GuidesLoader`
   - Se não encontrado, usa Groq/Gemini como fallback
   - Na primeira passagem: busca sobre `{game_name} {mission_name} guide walkthrough`
   - Na segunda passagem (quando `is_item_search=True`): busca sobre como obter o `missing_item`
   - Salva o resultado em `raw_search_result`

2. **`process_guide_node`**: 
   - LLM analisa o texto bruto
   - Extrai de forma estruturada os pré-requisitos críticos em `required_requirements`
   - Lista os passos mecânicos
   - Identifica spoilers narrativos futuros em `future_spoilers`
   - Retorna dados estruturados para próximo nó

3. **`verify_requirements_node`**: 
   - Compara logicamente os `required_requirements` com o `player_inventory`
   - Se o jogador não possuir algo necessário **e** `is_item_search` for `False`, preenche `missing_item`
   - **Ignorado** se `is_item_search=True` (roteador pula direto para `generate_help_node`)
   - Se inventário está vazio, assume que o jogador tem tudo (não valida)

4. **`generate_help_node`**: 
   - LLM gera a pista (modo `hint`) ou a solução detalhada (modo `answer`)
   - Recebe `required_requirements` para poder sugerir seu uso na resposta
   - Salva em `generated_text`
   - Pode ser executado múltiplas vezes se critique_spoiler_node rejeitar a resposta

5. **`critique_spoiler_node`**: 
   - LLM atua como camada independente de auditoria
   - Valida se a resposta gerada vaza fatos futuros do enredo
   - Modifica `critique_passed` (True/False)
   - Se rejeitada: retorna para `generate_help_node` com feedback de reescrita
   - Se aprovada: salva em `final_response` e encerra o fluxo

### Arestas Condicionais e Roteamento:
* **`route_after_process`**: 
  - Se `is_regenerating=True`: → `generate_help_node` (nova dica, pula busca)
  - Se `is_item_search=True`: → `generate_help_node` (segunda busca, pula verify)
  - Senão: → `verify_requirements_node` (fluxo normal)

* **`route_after_verify`**:
  - Se `missing_item=None`: → `generate_help_node` (tudo ok, segue normal)
  - Se `user_approval="nao"`: → `END` (jogador recusou, encerra)
  - Se `user_approval="sim"`: → `fetch_guide_node` (segunda busca)
  - Se `missing_item` E `user_approval=None`: → `fetch_guide_node` (HITL pausa ANTES de executar)

* **`route_after_critique`**: 
  - Se `critique_passed=True`: → `END` (resposta aprovada, encerra)
  - Se `critique_passed=False`: → `generate_help_node` (reescreve sem spoilers)

### Compilação e Persistência:
```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# A pausa HITL é controlada manualmente no api.py:
# 1. Grafo executa até completar
# 2. api.py detecta: result.missing_item E result.user_approval=None
# 3. Envia evento 'hitl_question' ao frontend via WebSocket
# 4. Aguarda resposta WebSocket do usuário (sim/nao)
# 5. Atualiza estado com user_approval via graph_app.update_state()
# 6. Retoma grafo.invoke() para segunda busca
```
