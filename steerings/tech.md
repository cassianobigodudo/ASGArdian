# ASGArdian - Architecture & Tech Specs (Especificações Técnicas)

## 1. Stack Tecnológica
* **Linguagem Principal:** Python 3.10+
* **Orquestração de Agentes:** LangGraph (StateGraph)
* **Framework LLM:** LangChain
* **Provedor de LLM:** Groq (Llama 3.1 70B) - RECOMENDADO
  * Alternativa: Google Gemini (legado, quota limitada)
* **Modelo Padrão:** `mixtral-8x7b-32768` (Groq) ou `gemini-2.0-flash` (Gemini)
* **Busca Web:** Integrada no conhecimento do Llama 3.1 (Groq) ou Google Search nativo (Gemini)
* **Gerenciamento de Ambiente:** `python-dotenv`
* **Persistência de Estado (HITL):** LangGraph `MemorySaver`

## 2. Suporte Multi-Provedor

O ASGArdian agora suporta múltiplos provedores de LLM:

### Groq (Recomendado) ⭐
- **Vantagens:**
  - Muito mais rápido (100+ tokens/segundo)
  - Quota generosa (quota muito maior que free tier do Gemini)
  - Modelo poderoso (Llama 3.1 70B ou Mixtral 8x7B)
  - Temperatura configurável
- **Configuração:** Adicionar `GROQ_API_KEY` no `.env`
- **Obter Chave:** https://console.groq.com/keys

### Google Gemini (Legado)
- **Desvantagens:**
  - Quota limitada no free tier
  - Mais lento que Groq
- **Configuração:** Adicionar `GOOGLE_API_KEY` no `.env`
- **Fallback:** Usado automaticamente se `GROQ_API_KEY` não estiver configurada

## 3. Estrutura do Estado (`AgentState`)
Definido via `TypedDict` para tráfego contínuo e persistência entre os nós do grafo. 14 campos trafegam continuamente entre todos os nós.

```python
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    # --- Dados de entrada do jogador (payload obrigatório) ---
    game_name: str              # Nome do jogo (ex: "Borderlands 2")
    mission_name: str           # Nome da missão ou localização atual
    current_issue: str          # Problema atual — pode ser atualizado no fluxo HITL
    original_issue: str         # Preserva o problema original antes do redirecionamento HITL
    help_type: str              # "hint" (pista sutil) ou "answer" (solução direta)
    player_inventory: List[str] # Itens ou habilidades que o jogador possui

    # --- Análise do problema (novo nó: analyze_problem_node) ---
    user_problem_text: str      # Texto completo do problema fornecido pelo usuário
    analyzed_mission: str       # Missão/dúvida extraída da análise do problema
    search_query: str           # Query otimizada para busca: "[game] [mission] guide walkthrough"

    # --- Resultados intermediários do grafo ---
    raw_search_result: str           # Conteúdo bruto retornado pelo IGN database/Groq/Gemini
    required_requirements: List[str] # Pré-requisitos extraídos pelo process_guide_node
    missing_item: Optional[str]      # Item ausente no inventário identificado pelo verify_node

    # --- Controle de fluxo e HITL ---
    is_item_search: bool         # RN05: True na 2ª passagem — ignora verify para evitar loop
    user_approval: Optional[str] # Resposta HITL: "sim", "nao" ou None (aguardando)
    is_regenerating: bool        # Flag para "Gerar Nova Dica" - pula diretamente para generate_help_node

    # --- Resposta gerada e validada ---
    generated_text: str   # Resposta temporária gerada pelo generate_help_node
    critique_passed: bool # True se o critique_spoiler_node aprovou a resposta
    final_response: str   # Resposta final validada e entregue ao jogador
    hitl_question: str    # Pergunta HITL para o usuário
    
    # --- Proteção contra loops infinitos de reescrita ---
    _rewrite_count: int   # Contador de tentativas de reescrita (máx indefinido até passar no critique)
```

## 4. Topologia do Grafo (LangGraph)

### Nós (Nodes):
1. `fetch_guide_node`: O LLM (Groq ou Gemini) busca informações contextualizadas. Na primeira passagem, pesquisa detonados com base no problema original. Na segunda passagem (quando `is_item_search=True`), pesquisa especificamente como obter o `missing_item`. Salva o resultado em `raw_search_result`.
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

## 5. Proteção Contra Loops Infinitos

### Implementação:
O sistema possui múltiplas camadas de proteção contra loops em `nodes.py`:

1. **Contador por Nó**: `_node_execution_count` rastreia quantas vezes cada nó foi executado
   - Limite: máx 5 execuções por nó (configurável via `_max_node_executions`)
   - Quando atingido: lança exceção `"LOOP DETECTADO"`

2. **Tempo Total de Execução**: `_total_execution_time_start` marca o início da execução
   - Limite: 300 segundos (5 minutos)
   - Quando atingido: lança exceção `"TIMEOUT TOTAL"`

3. **Flag `is_item_search`**: RN05 - evita re-verificação infinita
   - Quando `True`: roteador pula `verify_requirements_node` e vai direto para `generate_help_node`
   - Impede que a mesma busca refaça a verificação de requisitos

4. **Função `reset_execution_counters()`**: Chamada no início de cada nova execução no `api.py`
   - Reseta `_node_execution_count` e `_total_execution_time_start`
   - Permite que múltiplas buscas sequenciais funcionem sem falsa detecção de loop

### Fluxo de Reescrita (Critique Loop):
O `critique_spoiler_node` pode reescrever a resposta indefinidamente:
- Se `critique_passed=False`: retorna para `generate_help_node` para reescrita
- Se `critique_passed=True`: encerra o fluxo no `END`
- **Não há limite de reescritas** - o LLM continua refinando até passar na auditoria de spoilers

### Regeneração de Dica (Feature "Gerar Nova Dica"):
Quando o usuário clica no botão de regeneração:
1. Frontend chama `POST /api/regenerate-hint` com `thread_id`
2. Backend seta `is_regenerating=True` no estado
3. Roteador (`route_after_process`) detecta flag e pula para `generate_help_node`
4. Após geração, `is_regenerating` é resetado para `False` para evitar nova regeneração auto-disparada
