# -*- coding: utf-8 -*-
"""
main.py -- Executor principal do agente ASGArdian.

Responsabilidades:
- Validar o payload de entrada (5 campos obrigatorios do spec.md)
- Inicializar o AgentState com valores padrao seguros
- Executar o grafo compilado (app) gerenciando o ciclo HITL
- Detectar pausas do interrupt_before e interagir com o usuario
- Retornar a final_response validada

Fluxo principal:
    1. validate_payload(input_data)
    2. run_agent(input_data) -> executa ate pausar ou terminar
    3. Se pausado (missing_item detectado):
       a. Exibe item faltante ao usuario
       b. Le user_approval (sim/nao)
       c. Se "sim": atualiza estado e retoma
       d. Se "nao": encerra com mensagem de bloqueio
    4. Retorna final_response
"""

import uuid
import logging
from typing import Any, Dict

from backend.graph.workflow import app
from backend.graph.state import AgentState
from backend.errors import (
    ASGArdianError,
    PayloadValidationError,
    APIConnectionError,
    EmptySearchResultError,
)

# ---------------------------------------------------------------------------
# Configuracao basica de logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validacao de payload (Criterio 8 -- validacao de dados malformados)
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ["game_name", "mission_name", "current_issue", "help_type", "player_inventory"]
VALID_HELP_TYPES = {"hint", "answer"}


def validate_payload(data: Dict[str, Any]) -> None:
    """
    Valida os 5 campos obrigatorios do payload de entrada.
    Lanca PayloadValidationError com mensagem clara se algum campo estiver ausente ou invalido.
    """
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise PayloadValidationError(f"Campo obrigatorio ausente no payload: '{field}'")
        if data[field] is None:
            raise PayloadValidationError(f"Campo '{field}' nao pode ser None.")

    if not isinstance(data["game_name"], str) or not data["game_name"].strip():
        raise PayloadValidationError("'game_name' deve ser uma string nao vazia.")

    if not isinstance(data["mission_name"], str) or not data["mission_name"].strip():
        raise PayloadValidationError("'mission_name' deve ser uma string nao vazia.")

    if not isinstance(data["current_issue"], str) or not data["current_issue"].strip():
        raise PayloadValidationError("'current_issue' deve ser uma string nao vazia.")

    if data["help_type"] not in VALID_HELP_TYPES:
        raise PayloadValidationError(
            f"'help_type' deve ser 'hint' ou 'answer'. Recebido: '{data['help_type']}'"
        )

    if not isinstance(data["player_inventory"], list):
        raise PayloadValidationError("'player_inventory' deve ser uma lista de strings.")


def build_initial_state(data: Dict[str, Any]) -> AgentState:
    """
    Constroi o AgentState inicial a partir do payload validado.
    Preenche todos os campos intermediarios com valores padrao seguros.
    """
    # Extrai o texto do problema se fornecido, caso contrário usa current_issue
    user_problem_text = data.get("user_problem_text", data.get("current_issue", ""))
    
    return AgentState(
        game_name=data["game_name"],
        mission_name=data["mission_name"],
        current_issue=data["current_issue"],
        original_issue=data["current_issue"],   # preserva o contexto original
        help_type=data["help_type"],
        player_inventory=data["player_inventory"],
        user_problem_text=user_problem_text,    # Novo: texto completo do problema
        analyzed_mission="",                     # Novo: missão extraída
        search_query="",                         # Novo: query otimizada
        raw_search_result="",
        required_requirements=[],
        missing_item=None,
        is_item_search=False,                   # RN05: sempre False na inicializacao
        user_approval=None,
        is_regenerating=False,                  # Novo: regeneração não ativa por padrão
        generated_text="",
        critique_passed=False,
        final_response="",
        hitl_question="",
        _rewrite_count=0,                        # Novo: contador de reescritas
    )


# ---------------------------------------------------------------------------
# Executor principal com loop HITL
# ---------------------------------------------------------------------------

def run_agent(input_data: Dict[str, Any], thread_id: str = None) -> str:
    """
    Executa o grafo ASGArdian de ponta a ponta com suporte a HITL.

    Args:
        input_data: payload com os 5 campos obrigatorios do spec.md
        thread_id: identificador da sessao (gerado automaticamente se None)

    Returns:
        final_response: resposta final validada e sem spoilers
    """
    validate_payload(input_data)

    if thread_id is None:
        thread_id = str(uuid.uuid4())

    config = {"configurable": {"thread_id": thread_id}}
    initial_state = build_initial_state(input_data)

    print(f"\n🛡️  ASGArdian iniciando busca para: {input_data['game_name']} — {input_data['mission_name']}")
    print(f"   Problema: {input_data['current_issue']}")
    print(f"   Modo: {'Dica Sutil' if input_data['help_type'] == 'hint' else 'Solucao Direta'}\n")

    # --- Primeira execucao ---
    # O grafo roda ate pausar (interrupt_before) ou terminar
    try:
        result = app.invoke(initial_state, config=config)
    except APIConnectionError as exc:
        logger.error("Falha de API na primeira execucao: %s", exc)
        raise
    except EmptySearchResultError as exc:
        logger.warning("Busca sem resultado: %s", exc)
        raise
    except ASGArdianError as exc:
        logger.error("Erro do agente: %s", exc)
        raise
    except Exception as exc:
        logger.error("Erro inesperado na execucao do grafo: %s", exc)
        raise ASGArdianError(f"Erro inesperado: {exc}") from exc

    # --- Verifica se o grafo pausou no HITL ---
    snapshot = app.get_state(config)
    current_state = snapshot.values

    # Loop HITL: continua enquanto o grafo estiver pausado aguardando aprovacao
    while _is_paused_for_hitl(snapshot):
        missing = current_state.get("missing_item")
        print(f"\n⚠️  Pre-requisito detectado: '{missing}' nao encontrado no inventario.")
        print(f"   Deseja saber onde encontrar '{missing}'? (sim/nao): ", end="")

        user_input = input().strip().lower()

        if user_input not in ("sim", "nao"):
            print("   Resposta invalida. Por favor, digite 'sim' ou 'nao'.")
            continue

        if user_input == "nao":
            print(f"\n🔒 Progresso bloqueado: o item '{missing}' e necessario para continuar.")
            print(f"   Obtenha '{missing}' e tente novamente.")
            return f"Progresso bloqueado: '{missing}' ausente no inventario."

        # user_approval = "sim": prepara estado para segunda busca
        app.update_state(
            config,
            {
                "user_approval": "sim",
                "is_item_search": True,
                "current_issue": f"como obter {missing} em {current_state['game_name']}",
            },
        )

        # Retoma o grafo a partir do ponto pausado
        try:
            result = app.invoke(None, config=config)
        except ASGArdianError as exc:
            logger.error("Falha ao retomar grafo apos HITL: %s", exc)
            raise
        except Exception as exc:
            logger.error("Erro inesperado ao retomar grafo: %s", exc)
            raise ASGArdianError(f"Erro ao retomar execucao: {exc}") from exc

        snapshot = app.get_state(config)
        current_state = snapshot.values

    # --- Extrai e retorna a resposta final ---
    final = current_state.get("final_response", "")
    if not final:
        # Fallback: usa generated_text se final_response nao foi preenchida
        final = current_state.get("generated_text", "")

    print(f"\n🛡️  ASGArdian:\n\n{final}\n")
    return final


def _is_paused_for_hitl(snapshot) -> bool:
    """
    Verifica se o grafo esta pausado aguardando interacao HITL.
    O grafo pausa quando ha missing_item E o proximo no e fetch_guide_node.
    """
    if not snapshot:
        return False

    next_nodes = snapshot.next
    state = snapshot.values

    return (
        bool(next_nodes) and
        "fetch_guide_node" in next_nodes and
        bool(state.get("missing_item")) and
        state.get("user_approval") is None
    )


# ---------------------------------------------------------------------------
# Ponto de entrada CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Payload de exemplo para teste manual
    example_payload = {
        "game_name": "Borderlands 2",
        "mission_name": "Lights Out",
        "current_issue": (
            "Estou na area da subestacao e nao consigo restaurar a energia. "
            "Ja ativei duas alavancas mas nada acontece."
        ),
        "help_type": "hint",
        "player_inventory": ["Shotgun Torque", "Shield Adaptive", "Grenade Singularity"],
    }

    response = run_agent(example_payload)
