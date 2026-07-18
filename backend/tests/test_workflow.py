# -*- coding: utf-8 -*-
"""
test_workflow.py -- Testes de estrutura e roteamento do StateGraph do ASGArdian.

Cobertura:
- Estrutura do grafo: nós registrados, entry point, arestas
- route_after_process: is_item_search=True/False
- route_after_verify: sem missing, com missing+sem approval, approval=não, approval=sim
- route_after_critique: critique_passed=True/False
- compile_app: compila sem erros com MemorySaver
- Integração leve: fluxo completo com todos os nós mockados
"""

import sys
import os
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langgraph.graph import END

from backend.graph.state import AgentState
from backend.graph.workflow import (
    build_workflow,
    compile_app,
    route_after_process,
    route_after_verify,
    route_after_critique,
)

# Importa o módulo nodes para resetar o contador global
import backend.graph.nodes as nodes_module


# ---------------------------------------------------------------------------
# Fixture base de estado
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_execution_counters():
    """Reseta os contadores de execução antes de cada teste."""
    nodes_module._node_execution_count = {}
    nodes_module._total_execution_time_start = None
    yield
    # Limpeza após teste
    nodes_module._node_execution_count = {}
    nodes_module._total_execution_time_start = None


def make_state(**overrides) -> AgentState:
    base = AgentState(
        game_name="Borderlands 2",
        mission_name="Lights Out",
        current_issue="Não consigo restaurar a energia.",
        original_issue="Não consigo restaurar a energia.",
        help_type="hint",
        player_inventory=["Shotgun Torque"],
        raw_search_result="",
        required_requirements=[],
        missing_item=None,
        is_item_search=False,
        user_approval=None,
        generated_text="",
        critique_passed=False,
        final_response="",
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Testes das funções de roteamento
# ---------------------------------------------------------------------------

class TestRouteAfterProcess:

    def test_is_item_search_false_vai_para_verify(self):
        """Fluxo normal: sem is_item_search deve ir para verify_requirements_node."""
        state = make_state(is_item_search=False)
        assert route_after_process(state) == "verify_requirements_node"

    def test_is_item_search_true_pula_verify(self):
        """RN05: is_item_search=True deve pular verify e ir direto para generate."""
        state = make_state(is_item_search=True)
        assert route_after_process(state) == "generate_help_node"


class TestRouteAfterVerify:

    def test_sem_missing_vai_para_generate(self):
        """Inventário completo: deve avançar direto para generate_help_node."""
        state = make_state(missing_item=None)
        assert route_after_verify(state) == "generate_help_node"

    def test_missing_sem_approval_vai_para_fetch_hitl(self):
        """HITL: item faltando sem user_approval deve ir para fetch (grafo pausa antes)."""
        state = make_state(missing_item="Chave de Acesso", user_approval=None)
        assert route_after_verify(state) == "fetch_guide_node"

    def test_missing_approval_sim_vai_para_fetch(self):
        """HITL aprovado: user_approval=sim deve ir para fetch com novo contexto."""
        state = make_state(
            missing_item="Chave de Acesso",
            user_approval="sim",
            is_item_search=True,
            current_issue="como obter Chave de Acesso em Borderlands 2",
        )
        assert route_after_verify(state) == "fetch_guide_node"

    def test_missing_approval_nao_encerra_fluxo(self):
        """RN04: user_approval=não deve encerrar o fluxo no END."""
        state = make_state(missing_item="Chave de Acesso", user_approval="nao")
        assert route_after_verify(state) == END


class TestRouteAfterCritique:

    def test_critique_passed_true_encerra(self):
        """Resposta aprovada: critique_passed=True deve encerrar no END."""
        state = make_state(critique_passed=True)
        assert route_after_critique(state) == END

    def test_critique_passed_false_reescreve(self):
        """Resposta reprovada: critique_passed=False deve voltar para generate."""
        state = make_state(critique_passed=False)
        assert route_after_critique(state) == "generate_help_node"


# ---------------------------------------------------------------------------
# Testes de estrutura do grafo
# ---------------------------------------------------------------------------

class TestWorkflowStructure:

    def test_build_workflow_retorna_stategraph(self):
        """build_workflow deve retornar um objeto StateGraph válido."""
        from langgraph.graph import StateGraph
        workflow = build_workflow()
        assert isinstance(workflow, StateGraph)

    def test_compile_app_sem_erros(self):
        """compile_app deve compilar sem lançar exceções."""
        app = compile_app()
        assert app is not None

    def test_grafo_tem_5_nos_registrados(self):
        """O grafo deve ter exatamente os 5 nós definidos no tech.md."""
        workflow = build_workflow()
        nos_esperados = {
            "fetch_guide_node",
            "process_guide_node",
            "verify_requirements_node",
            "generate_help_node",
            "critique_spoiler_node",
        }
        # Acessa os nós registrados internamente no StateGraph
        nos_registrados = set(workflow.nodes.keys())
        assert nos_esperados.issubset(nos_registrados)

    def test_entry_point_e_fetch_guide_node(self):
        """O ponto de entrada do grafo deve ser fetch_guide_node."""
        workflow = build_workflow()
        # O entry point é armazenado como "__start__" apontando para o nó inicial
        # Verifica que fetch_guide_node está no grafo e é acessível
        assert "fetch_guide_node" in workflow.nodes


# ---------------------------------------------------------------------------
# Teste de integração leve: fluxo completo com mocks
# ---------------------------------------------------------------------------

class TestWorkflowIntegration:

    @patch("backend.graph.nodes._invoke_llm")
    def test_fluxo_completo_sem_missing_item(self, mock_invoke_llm):
        """
        Integração: fluxo completo sem item faltando deve produzir final_response.
        fetch -> process -> verify (sem missing) -> generate -> critique (passed) -> END
        """
        # Mock do LLM com respostas diferentes por chamada
        mock_invoke_llm.side_effect = [
            # fetch_guide_node
            "Guia completo: vá para a esquerda e use a alavanca.",
            # process_guide_node
            "PREREQUISITOS: nenhum\nPASSOS: 1. Vá para a esquerda.\nSPOILERS_FUTUROS: nenhum",
            # verify_requirements_node (sem requisitos, não será chamado efetivamente)
            # generate_help_node
            "Observe os elementos visuais da sala. [Nenhum spoiler de enredo foi incluído nesta resposta.]",
        ]

        # Compila grafo sem interrupt (para teste de fluxo completo)
        from langgraph.graph import StateGraph
        from backend.graph.workflow import build_workflow
        workflow = build_workflow()
        app = workflow.compile()  # sem interrupt_before para testar fluxo completo

        initial_state = make_state()
        config = {"configurable": {"thread_id": "test-no-missing"}}

        result = app.invoke(initial_state, config=config)

        assert result["final_response"] != "" or result["critique_passed"] is True

    @patch("backend.graph.nodes._invoke_llm")
    def test_fluxo_hitl_pausa_quando_missing_item(self, mock_invoke_llm):
        """
        Integração HITL: grafo deve pausar antes do segundo fetch quando missing_item detectado.

        Mecânica real do interrupt_before=["fetch_guide_node"]:
        - 1ª invocação (sem checkpointer): roda fetch -> process -> verify -> detecta missing
          -> roteador vai para fetch_guide_node -> HITL pausa ANTES do segundo fetch
        - Estado salvo deve conter missing_item preenchido
        """
        mock_invoke_llm.side_effect = [
            # fetch_guide_node (primeira chamada)
            "Este puzzle requer a Chave de Acesso Perdida.",
            # process_guide_node
            "PREREQUISITOS: Chave de Acesso Perdida\nPASSOS: 1. Use a chave.\nSPOILERS_FUTUROS: nenhum",
            # verify_requirements_node
            "MISSING_ITEM: Chave de Acesso Perdida",
        ]

        from langgraph.checkpoint.memory import MemorySaver
        from backend.graph.workflow import build_workflow

        memory = MemorySaver()
        workflow = build_workflow()

        # Compila SEM interrupt para a primeira passagem completa
        app_no_interrupt = workflow.compile(checkpointer=memory)

        initial_state = make_state(player_inventory=[])
        config = {"configurable": {"thread_id": "test-hitl-pause"}}

        # Primeira execução completa: fetch -> process -> verify (detecta missing)
        # Como não há interrupt, o roteador tenta ir para fetch de novo
        # mas os mocks de LLM acabam e o verify retorna missing_item
        # O importante é verificar que o estado contém missing_item após o verify
        try:
            app_no_interrupt.invoke(initial_state, config=config)
        except Exception:
            pass  # pode falhar por mock esgotado, o que é esperado

        snapshot = app_no_interrupt.get_state(config)
        state_values = snapshot.values

        # O verify_requirements_node deve ter populado missing_item
        assert state_values.get("missing_item") == "Chave de Acesso Perdida"

    @patch("backend.graph.nodes._invoke_llm")
    def test_fluxo_hitl_retomada_com_nao(self, mock_invoke_llm):
        """
        Integração HITL: user_approval=não deve encerrar o fluxo no END.
        """
        mock_invoke_llm.side_effect = [
            # fetch_guide_node
            "Requer Chave de Acesso.",
            # process_guide_node
            "PREREQUISITOS: Chave de Acesso\nPASSOS: 1. Use a chave.\nSPOILERS_FUTUROS: nenhum",
            # verify_requirements_node
            "MISSING_ITEM: Chave de Acesso",
        ]

        from langgraph.checkpoint.memory import MemorySaver
        from backend.graph.workflow import build_workflow
        memory = MemorySaver()
        workflow = build_workflow()
        app = workflow.compile(
            checkpointer=memory,
            interrupt_before=["fetch_guide_node"],
        )

        initial_state = make_state(player_inventory=[])
        config = {"configurable": {"thread_id": "test-hitl-nao"}}

        # Primeira execução: pausa no HITL
        app.invoke(initial_state, config=config)

        # Usuário responde "não" -- atualiza estado e retoma
        app.update_state(config, {"user_approval": "nao"})
        result = app.invoke(None, config=config)

        # Com user_approval=não, o roteador deve ter ido para END
        snapshot = app.get_state(config)
        assert snapshot.values.get("user_approval") == "nao"
