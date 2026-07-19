"""
state.py — Definição do AgentState do ASGArdian.

Todos os 14 campos trafegam continuamente entre os nós do StateGraph.
A flag `is_item_search` é a salvaguarda contra loop infinito no fluxo HITL.
O campo `original_issue` preserva o contexto do jogador quando o fluxo
é redirecionado para buscar um item faltante.
"""

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
    raw_search_result: str           # Conteúdo bruto retornado pelo Gemini via Google Search
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
    _rewrite_count: int   # Contador de tentativas de reescrita (máx 2)
