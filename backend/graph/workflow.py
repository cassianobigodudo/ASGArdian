# -*- coding: utf-8 -*-
"""
workflow.py -- Montagem e compilacao do StateGraph do ASGArdian.

Responsabilidades deste modulo:
- Registrar os 5 nos no grafo
- Definir todas as arestas (fixas e condicionais)
- Compilar com MemorySaver e interrupt_before para o HITL
- Exportar `app` como ponto de entrada unico para o main.py

Topologia:
    START
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
    - RN05: se is_item_search=True, pula o verify para evitar loop infinito
    - Caso contrario, segue o fluxo normal de verificacao de requisitos
    """
    if state.get("is_item_search", False):
        return "generate_help_node"
    return "verify_requirements_node"


def route_after_verify(state: AgentState) -> str:
    """
    Apos verify_requirements_node:
    - Se nao ha item faltando: avanca para gerar a ajuda
    - Se user_approval="nao": encerra o fluxo (jogador recusou a busca)
    - Se ha item faltando e sem aprovacao: prepara o estado HITL e vai para fetch
      (o grafo pausara em interrupt_before=["fetch_guide_node"])
    """
    missing = state.get("missing_item")
    approval = state.get("user_approval")

    if not missing:
        return "generate_help_node"

    if approval == "nao":
        return END

    # missing_item existe e user_approval nao foi dado ainda (ou foi "sim")
    # Redireciona para fetch -- o HITL vai pausar antes se user_approval=None
    return "fetch_guide_node"


def route_after_critique(state: AgentState) -> str:
    """
    Apos critique_spoiler_node:
    - Se aprovado: encerra o fluxo com a resposta final
    - Se reprovado: volta ao generate para reescrita sem spoilers
    """
    if state.get("critique_passed", False):
        return END
    return "generate_help_node"


# ---------------------------------------------------------------------------
# Construcao do grafo
# ---------------------------------------------------------------------------

def build_workflow() -> StateGraph:
    """
    Constroi e retorna o StateGraph completo do ASGArdian.
    Nao compila -- permite testes de estrutura sem MemorySaver.
    """
    workflow = StateGraph(AgentState)

    # --- Registro dos 5 nos ---
    workflow.add_node("fetch_guide_node", fetch_guide_node)
    workflow.add_node("process_guide_node", process_guide_node)
    workflow.add_node("verify_requirements_node", verify_requirements_node)
    workflow.add_node("generate_help_node", generate_help_node)
    workflow.add_node("critique_spoiler_node", critique_spoiler_node)

    # --- Ponto de entrada ---
    workflow.set_entry_point("fetch_guide_node")

    # --- Arestas fixas ---
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
    Compila o workflow com persistencia de memoria e interrupt_before para HITL.

    interrupt_before=["fetch_guide_node"]: o grafo pausa antes de fetch sempre
    que for reiniciado apos o verify detectar um missing_item.
    O main.py e responsavel por checar se a pausa e necessaria (user_approval=None)
    e por injetar o user_approval antes de retomar.
    """
    memory = MemorySaver()
    workflow = build_workflow()
    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["fetch_guide_node"],
    )
    return app


# Instancia compilada exportada para uso no main.py
app = compile_app()
