"""
nodes.py — Implementação dos 5 nós do grafo ASGArdian.

Cada função recebe o AgentState completo e retorna um dicionário
com apenas os campos que foram modificados naquele nó.

Nós implementados:
1. fetch_guide_node      — busca detonados via Gemini + Google Search
2. process_guide_node    — extrai requisitos, passos e spoilers do resultado bruto
3. verify_requirements_node — compara inventário com requisitos (ignora se is_item_search=True)
4. generate_help_node    — gera hint ou answer com base no help_type
5. critique_spoiler_node — audita a resposta contra spoilers futuros
"""

import re
from typing import Any, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from backend.config import GOOGLE_API_KEY
from backend.graph.state import AgentState
from backend.prompts.templates import (
    FETCH_GUIDE_PROMPT,
    PROCESS_GUIDE_PROMPT,
    VERIFY_REQUIREMENTS_PROMPT,
    GENERATE_HINT_PROMPT,
    GENERATE_ANSWER_PROMPT,
    CRITIQUE_SPOILER_PROMPT,
)

# ---------------------------------------------------------------------------
# Instância compartilhada do modelo Gemini com Google Search habilitado
# ---------------------------------------------------------------------------

def _get_llm_with_search() -> ChatGoogleGenerativeAI:
    """Retorna instância do Gemini 1.5 Flash com ferramenta Google Search nativa."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GOOGLE_API_KEY,
        tools="google_search_retrieval",
    )


def _get_llm() -> ChatGoogleGenerativeAI:
    """Retorna instância do Gemini 1.5 Flash sem ferramentas (para processamento puro)."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GOOGLE_API_KEY,
    )


# ---------------------------------------------------------------------------
# Nó 1: fetch_guide_node
# ---------------------------------------------------------------------------

def fetch_guide_node(state: AgentState) -> Dict[str, Any]:
    """
    Usa o Gemini com Google Search nativa para buscar detonados em tempo real.

    Na primeira passagem: busca pelo problema original do jogador.
    Na segunda passagem (is_item_search=True): busca como obter o missing_item.
    O campo current_issue já foi atualizado pelo roteador antes desta chamada.

    Retorna: raw_search_result populado com o conteúdo bruto encontrado.
    """
    prompt = FETCH_GUIDE_PROMPT.format(
        game_name=state["game_name"],
        mission_name=state["mission_name"],
        current_issue=state["current_issue"],
    )

    llm = _get_llm_with_search()
    response = llm.invoke([HumanMessage(content=prompt)])
    raw_result = response.content if hasattr(response, "content") else str(response)

    return {"raw_search_result": raw_result}


# ---------------------------------------------------------------------------
# Nó 2: process_guide_node
# ---------------------------------------------------------------------------

def process_guide_node(state: AgentState) -> Dict[str, Any]:
    """
    Analisa o raw_search_result e extrai de forma estruturada:
    - required_requirements: lista de pré-requisitos
    - generated_text: passo a passo (guide_steps) para uso nos próximos nós
    - Atualiza raw_search_result com os spoilers futuros identificados
      (preservados em raw_search_result para uso no critique_spoiler_node)

    Retorna: required_requirements e generated_text (com os passos extraídos).
    O campo raw_search_result é prefixado com SPOILERS_FUTUROS para consulta posterior.
    """
    prompt = PROCESS_GUIDE_PROMPT.format(
        raw_search_result=state["raw_search_result"],
        game_name=state["game_name"],
        current_issue=state["current_issue"],
    )

    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, "content") else str(response)

    # Extrai PREREQUISITOS
    req_match = re.search(r"PREREQUISITOS:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
    req_raw = req_match.group(1).strip() if req_match else ""
    requirements = (
        []
        if not req_raw or req_raw.lower() in ("nenhum", "none", "[]")
        else [r.strip() for r in req_raw.split(",") if r.strip()]
    )

    # Extrai PASSOS
    steps_match = re.search(r"PASSOS:\s*(.+?)(?:SPOILERS_FUTUROS:|$)", content, re.IGNORECASE | re.DOTALL)
    guide_steps = steps_match.group(1).strip() if steps_match else content

    # Extrai SPOILERS_FUTUROS e anexa ao raw_search_result para o critique usar
    spoiler_match = re.search(r"SPOILERS_FUTUROS:\s*(.+?)$", content, re.IGNORECASE | re.DOTALL)
    future_spoilers = spoiler_match.group(1).strip() if spoiler_match else "nenhum"

    # Guarda spoilers no raw_search_result com marcação clara para o critique
    enriched_result = f"{state['raw_search_result']}\n\n---SPOILERS_FUTUROS---\n{future_spoilers}"

    return {
        "required_requirements": requirements,
        "generated_text": guide_steps,
        "raw_search_result": enriched_result,
    }


# ---------------------------------------------------------------------------
# Nó 3: verify_requirements_node
# ---------------------------------------------------------------------------

def verify_requirements_node(state: AgentState) -> Dict[str, Any]:
    """
    Compara os required_requirements com o player_inventory do jogador.

    Se is_item_search=True: este nó NÃO deve ser chamado (o roteador pula).
    Se inventário completo: missing_item = None.
    Se falta algo: missing_item = nome do item mais crítico.

    Retorna: missing_item (str ou None).
    """
    # Salvaguarda — não deveria ser chamado na segunda passagem
    if state.get("is_item_search", False):
        return {"missing_item": None}

    requirements = state.get("required_requirements", [])

    # Se não há requisitos, não há nada faltando
    if not requirements:
        return {"missing_item": None}

    prompt = VERIFY_REQUIREMENTS_PROMPT.format(
        required_requirements=", ".join(requirements),
        player_inventory=", ".join(state.get("player_inventory", [])),
    )

    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, "content") else str(response)

    # Extrai o MISSING_ITEM da resposta
    match = re.search(r"MISSING_ITEM:\s*(.+)", content, re.IGNORECASE)
    missing_raw = match.group(1).strip() if match else "none"

    missing_item = (
        None if missing_raw.lower() in ("none", "nenhum", "nenhum item", "")
        else missing_raw
    )

    return {"missing_item": missing_item}


# ---------------------------------------------------------------------------
# Nó 4: generate_help_node
# ---------------------------------------------------------------------------

def generate_help_node(state: AgentState) -> Dict[str, Any]:
    """
    Gera a resposta de ajuda de acordo com o help_type:
    - "hint": dica sutil sem passo a passo direto (RN02)
    - "answer": solução direta e numerada (RN02)

    Se critique_passed=False (reescrita), o feedback da falha é injetado no prompt
    para que o modelo corrija o problema identificado sem spoilers.

    Retorna: generated_text com a resposta gerada.
    """
    guide_steps = state.get("generated_text", "")

    # Injeta feedback do critique se a resposta anterior falhou
    critique_feedback = ""
    if state.get("critique_passed") is False and state.get("generated_text"):
        critique_feedback = (
            "\n⚠️ ATENÇÃO — A resposta anterior foi REPROVADA por conter spoilers. "
            "Reescreva completamente sem mencionar eventos futuros do enredo."
        )

    template = (
        GENERATE_HINT_PROMPT if state["help_type"] == "hint"
        else GENERATE_ANSWER_PROMPT
    )

    prompt = template.format(
        game_name=state["game_name"],
        current_issue=state["current_issue"],
        guide_steps=guide_steps,
        critique_feedback=critique_feedback,
    )

    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    generated = response.content if hasattr(response, "content") else str(response)

    return {"generated_text": generated}


# ---------------------------------------------------------------------------
# Nó 5: critique_spoiler_node
# ---------------------------------------------------------------------------

def critique_spoiler_node(state: AgentState) -> Dict[str, Any]:
    """
    Audita a resposta gerada contra a lista de spoilers futuros identificados.

    Se CRITIQUE_RESULT: PASSED → critique_passed=True, final_response=generated_text
    Se CRITIQUE_RESULT: FAILED → critique_passed=False (roteador volta ao generate_help_node)

    Retorna: critique_passed e final_response (só preenchida se aprovada).
    """
    # Extrai spoilers futuros do raw_search_result enriquecido
    raw = state.get("raw_search_result", "")
    spoiler_section = ""
    if "---SPOILERS_FUTUROS---" in raw:
        spoiler_section = raw.split("---SPOILERS_FUTUROS---")[-1].strip()
    if not spoiler_section or spoiler_section.lower() in ("nenhum", "none"):
        # Sem spoilers identificados: aprovação automática
        return {
            "critique_passed": True,
            "final_response": state.get("generated_text", ""),
        }

    prompt = CRITIQUE_SPOILER_PROMPT.format(
        future_spoilers=spoiler_section,
        generated_text=state.get("generated_text", ""),
    )

    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, "content") else str(response)

    passed = "CRITIQUE_RESULT: PASSED" in content.upper()

    return {
        "critique_passed": passed,
        "final_response": state.get("generated_text", "") if passed else "",
    }
