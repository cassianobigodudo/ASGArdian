# ASGArdian - Architecture & Tech Specs (Especificações Técnicas)

## 1. Stack Tecnológica
* **Linguagem Principal:** Python 3.10+
* **Orquestração de Agentes:** LangGraph (StateGraph)
* **Framework LLM:** LangChain / LangChain-Google-GenAI
* **Modelo com Busca Real-Time:** `gemini-1.5-flash` com ferramenta nativa `Google Search`
* **Gerenciamento de Ambiente:** `python-dotenv`
* **Persistência de Estado (HITL):** LangGraph `MemorySaver`

## 2. Estrutura do Estado (`AgentState`)
Definido via `TypedDict` para tráfego contínuo e persistência entre os nós do grafo.

```python
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    game_name: str
    mission_name: str
    current_issue: str
    original_issue: str          # Preserva o problema original antes de qualquer redirecionamento
    help_type: str                   # "hint" ou "answer"
    player_inventory: List[str]
    raw_search_result: str           # Conteúdo bruto retornado pelo Gemini via Google Search
    required_requirements: List[str] # Itens obrigatórios identificados pela LLM
    missing_item: Optional[str]      # Item que falta no inventário do jogador (se houver)
    is_item_search: bool             # Flag que indica se o fluxo atual é uma busca pelo item faltante
    user_approval: Optional[str]     # "sim", "nao" ou None (resposta do HITL)
    generated_text: str              # Resposta temporária gerada
    critique_passed: bool            # Status do filtro anti-spoiler
    final_response: str              # Resposta final validada
```

## 3. Topologia do Grafo (LangGraph)

### Nós (Nodes):
1. `fetch_guide_node`: O Gemini ativa a busca nativa do Google em tempo real. Na primeira passagem, pesquisa detonados com base no problema original. Na segunda passagem (quando `is_item_search=True`), pesquisa especificamente como obter o `missing_item`. Salva o resultado em `raw_search_result`.
2. `process_guide_node`: LLM analisa o texto bruto e extrai de forma estruturada os pré-requisitos, o passo a passo e os potenciais spoilers futuros.
3. `verify_requirements_node`: Compara logicamente os `required_requirements` com o `player_inventory`. Se o jogador não possuir algo necessário **e** `is_item_search` for `False`, preenche `missing_item`. Se `is_item_search` for `True`, este nó é ignorado pelo roteamento — evitando loop infinito.
4. `generate_help_node`: LLM gera a pista (modo `hint`) ou a solução detalhada (modo `answer`) baseando-se no cenário atual do estado.
5. `critique_spoiler_node`: LLM atua como uma camada independente de auditoria, validando se a resposta gerada vaza fatos futuros do enredo. Modifica o booleano `critique_passed`.

### Arestas Condicionais e Roteamento:
* **Após `verify_requirements_node`:**
  * Se `missing_item` for identificado **e** `is_item_search=False`: pausa o grafo via HITL e aguarda `user_approval`.
    * Se `user_approval = "sim"`: seta `is_item_search=True`, atualiza `current_issue` para `"como obter [missing_item] em [game_name]"` e redireciona para `fetch_guide_node`.
    * Se `user_approval = "nao"`: encerra o fluxo informando o bloqueio.
  * Se `is_item_search=True` **ou** inventário completo: avança direto para `generate_help_node`.
* **Após `critique_spoiler_node`:** Se `critique_passed` for `True`, encerra o fluxo no `END`. Se for `False`, redireciona o fluxo de volta para `generate_help_node`, anexando o feedback da falha para que o texto seja reescrito sem spoilers.

### Mecânica Human-in-the-loop (HITL) e Compilação:
O grafo deve ser compilado utilizando persistência em memória e uma regra estrita de pausa imediatamente antes de executar o segundo ciclo de busca quando um item está faltando:

```python
from langgraph.checkpoint.memory import MemorySaver

# Configura o checkpointer de memória para manter os estados das threads
memory = MemorySaver()

# Compila o workflow injetando a trava de segurança para o operador humano
# A interrupção ocorre antes de fetch_guide_node quando is_item_search está prestes a ser True
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["fetch_guide_node"]
)
```

> **Nota:** A lógica de interrupção é condicional — o HITL só deve pausar na segunda passagem por `fetch_guide_node`, quando `missing_item` foi identificado e `user_approval` ainda é `None`. Na primeira passagem, o nó executa normalmente.
