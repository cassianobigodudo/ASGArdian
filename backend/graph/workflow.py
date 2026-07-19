# -*- coding: utf-8 -*-
"""
workflow.py -- Montagem e compilacao do StateGraph do ASGArdian.

Responsabilidades deste modulo:
- Registrar os 6 nos no grafo (incluindo analyze_problem_node)
- Definir todas as arestas (fixas e condicionais)
- Compilar com MemorySaver
- Exportar `app` como ponto de entrada unico para o main.py

Topologia:
    START
      |
    analyze_problem_node (NOVO - extrai mission e search_query)
      |
    fetch_guide_node
      |
    process_guide_node
      |
    [route_after_process]
      |-- is_item_search=True  --> generate_help_node
      |-- is_item_search=False --> verify_requirements_node
                                        |
                                   [route_after_verify]
                                        |-- missing_item=None         --> generate_help_node
                                        |-- user_approval="nao"       --> END
                                        |-- missing_item+sem approval --> fetch_guide_node (HITL pausa aqui)
                                              |
                                         generate_help_node
                                              |
                                         critique_spoiler_node
                                              |
                                        [route_after_critique]
                                              |-- critique_passed=True  --> END
                                              |-- critique_passed=False --> generate_help_node
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.graph.state import AgentState
from backend.graph.nodes import (
    # analyze_problem_node,  # DESATIVADO
    fetch_guide_node,
    process_guide_node,
    verify_requirements_node,
    generate_help_node,
    critique_spoiler_node,
)

# ---------------------------------------------------------------------------
# Funcoes de roteamento condicional
# ---------------------------------------------------------------------------

def route_after_process(state: AgentState) -> str:
    """
    Apos process_guide_node:
    - Se is_regenerating=True: pula direto para generate_help_node (nova dica)
    - Se is_item_search=True: pula o verify para evitar loop infinito
    - Caso contrario, segue o fluxo normal de verificacao de requisitos
    """
    if state.get("is_regenerating", False):
        return "generate_help_node"
    if state.get("is_item_search", False):
        return "generate_help_node"
    return "verify_requirements_node"


def route_after_verify(state: AgentState) -> str:
    """
    Apos verify_requirements_node:
    - Se nao ha item faltando: avanca para gerar a ajuda
    - Se user_approval="nao": encerra o fluxo (jogador recusou a busca)
    - Se user_approval="sim": vai para fetch_guide_node (segunda busca)
    - Se há missing_item E user_approval=None: PAUSA para HITL fazer pergunta
    """
    missing = state.get("missing_item")
    approval = state.get("user_approval")

    if not missing:
        # Sem item faltando: segue para gerar ajuda
        return "generate_help_node"

    if approval == "nao":
        # Usuário recusou busca pelo item
        return END

    if approval == "sim":
        # Usuário aprovou: vai buscar o item
        return "fetch_guide_node"

    # approval=None E missing_item=True: item faltando, usuário não respondeu ainda
    # Retorna fetch_guide_node - o LangGraph pausará ANTES de executá-lo (interrupt_before)
    # para que o HITL possa fazer a pergunta ao usuário
    return "fetch_guide_node"


def route_after_critique(state: AgentState) -> str:
    """
    Apos critique_spoiler_node:
    - Se critique_passed=True: ENCERRA o fluxo (retorna END)
    - Se critique_passed=False: volta ao generate_help_node para reescrita
    
    IMPORTANTE: Este é o ÚLTIMO nó antes do final. Sempre retorna END ou generate_help_node.
    """
    passed = state.get("critique_passed", False)
    
    if passed:
        # Resposta aprovada: encerra o fluxo completamente
        return END
    
    # Resposta reprovada: volta para reescrever sem spoilers
    return "generate_help_node"


# ---------------------------------------------------------------------------
# Construcao do grafo
# ---------------------------------------------------------------------------

def build_workflow() -> StateGraph:
    """
    Constroi e retorna o StateGraph completo do ASGArdian.
    Nao compila -- permite testes de estrutura sem MemorySaver.
    
    NOTA: analyze_problem_node foi desativado. A search_query é gerada
    diretamente no fetch_guide_node usando: [game] [mission] guide walkthrough
    """
    workflow = StateGraph(AgentState)

    # --- Registro dos 5 nos (analyze_problem_node DESATIVADO) ---
    # workflow.add_node("analyze_problem_node", analyze_problem_node)
    workflow.add_node("fetch_guide_node", fetch_guide_node)
    workflow.add_node("process_guide_node", process_guide_node)
    workflow.add_node("verify_requirements_node", verify_requirements_node)
    workflow.add_node("generate_help_node", generate_help_node)
    workflow.add_node("critique_spoiler_node", critique_spoiler_node)

    # --- Ponto de entrada ---
    workflow.set_entry_point("fetch_guide_node")

    # --- Arestas fixas ---
    # workflow.add_edge("analyze_problem_node", "fetch_guide_node")
    workflow.add_edge("fetch_guide_node", "process_guide_node")
    workflow.add_edge("generate_help_node", "critique_spoiler_node")

    # --- Arestas condicionais ---

    # Apos process: decide se pula verify (RN05) ou nao
    workflow.add_conditional_edges(
        "process_guide_node",
        route_after_process,
        {
            "verify_requirements_node": "verify_requirements_node",
            "generate_help_node": "generate_help_node",
        },
    )

    # Apos verify: decide entre gerar ajuda, pausar HITL ou encerrar
    workflow.add_conditional_edges(
        "verify_requirements_node",
        route_after_verify,
        {
            "generate_help_node": "generate_help_node",
            "fetch_guide_node": "fetch_guide_node",
            END: END,
        },
    )

    # Apos critique: decide entre encerrar ou reescrever
    workflow.add_conditional_edges(
        "critique_spoiler_node",
        route_after_critique,
        {
            END: END,
            "generate_help_node": "generate_help_node",
        },
    )

    return workflow


# ---------------------------------------------------------------------------
# Compilacao com MemorySaver e HITL
# ---------------------------------------------------------------------------

def compile_app():
    """
    Compila o workflow com persistencia de memoria.
    
    NOTA: Removemos interrupt_before pois a pausa HITL é controlada manualmente
    no api.py. O interrupt_before pausaria ANTES de fetch_guide_node SEMPRE,
    impedindo a primeira execução.
    """
    memory = MemorySaver()
    workflow = build_workflow()
    app = workflow.compile(checkpointer=memory)
    return app


# Instancia compilada exportada para uso no main.py
app = compile_app()
