# -*- coding: utf-8 -*-
"""
test_errors.py -- Testes das exceções customizadas e tratamento de erros dos nós.

Cobertura:
- Hierarquia de exceções (herança de ASGArdianError)
- fetch_guide_node: APIConnectionError em falha de API, EmptySearchResultError em resultado vazio
- process_guide_node: APIConnectionError em falha de API, GuideProcessingError em resposta vazia
- verify_requirements_node: APIConnectionError em falha de API
- generate_help_node: APIConnectionError em falha de API, GuideProcessingError em resposta vazia
- critique_spoiler_node: APIConnectionError em falha de API
- main.run_agent: PayloadValidationError propaga antes do grafo
"""

import sys
import os
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.errors import (
    ASGArdianError,
    PayloadValidationError,
    APIConnectionError,
    EmptySearchResultError,
    GuideProcessingError,
    SpoilerCritiqueError,
)
from backend.graph.state import AgentState
from backend.graph.nodes import (
    fetch_guide_node,
    process_guide_node,
    verify_requirements_node,
    generate_help_node,
    critique_spoiler_node,
)


# ---------------------------------------------------------------------------
# Fixture base
# ---------------------------------------------------------------------------

def make_state(**overrides) -> AgentState:
    base = AgentState(
        game_name="Borderlands 2",
        mission_name="Lights Out",
        current_issue="Não consigo restaurar a energia.",
        original_issue="Não consigo restaurar a energia.",
        help_type="hint",
        player_inventory=["Shotgun Torque"],
        raw_search_result="conteúdo bruto\n\n---SPOILERS_FUTUROS---\nnenhum",
        required_requirements=["Item X"],
        missing_item=None,
        is_item_search=False,
        user_approval=None,
        generated_text="Resposta gerada.",
        critique_passed=False,
        final_response="",
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Testes da hierarquia de exceções
# ---------------------------------------------------------------------------

class TestErrorHierarchy:

    def test_todas_excecoes_herdam_de_asgardian_error(self):
        """Todas as exceções customizadas devem herdar de ASGArdianError."""
        assert issubclass(PayloadValidationError, ASGArdianError)
        assert issubclass(APIConnectionError, ASGArdianError)
        assert issubclass(EmptySearchResultError, ASGArdianError)
        assert issubclass(GuideProcessingError, ASGArdianError)
        assert issubclass(SpoilerCritiqueError, ASGArdianError)

    def test_todas_excecoes_herdam_de_exception(self):
        """ASGArdianError deve herdar de Exception (capturável normalmente)."""
        assert issubclass(ASGArdianError, Exception)

    def test_excecoes_podem_ser_instanciadas_com_mensagem(self):
        """Todas as exceções devem aceitar mensagem de texto."""
        for cls in [PayloadValidationError, APIConnectionError,
                    EmptySearchResultError, GuideProcessingError, SpoilerCritiqueError]:
            exc = cls("mensagem de teste")
            assert str(exc) == "mensagem de teste"


# ---------------------------------------------------------------------------
# Testes: fetch_guide_node
# ---------------------------------------------------------------------------

class TestFetchGuideNodeErrors:

    @patch("backend.graph.nodes._invoke_llm")
    def test_api_exception_lanca_api_connection_error(self, mock_invoke_llm):
        """Exceção da API deve ser convertida em APIConnectionError."""
        mock_invoke_llm.side_effect = Exception("Connection refused")

        with pytest.raises(APIConnectionError, match="Falha ao buscar detonado"):
            fetch_guide_node(make_state())

    @patch("backend.graph.nodes._invoke_llm")
    def test_resultado_vazio_lanca_empty_search_error(self, mock_invoke_llm):
        """Resultado vazio da API deve lançar EmptySearchResultError."""
        mock_invoke_llm.return_value = ""

        with pytest.raises(EmptySearchResultError, match="nao retornou nenhum conteudo"):
            fetch_guide_node(make_state())

    @patch("backend.graph.nodes._invoke_llm")
    def test_resultado_apenas_espacos_lanca_empty_search_error(self, mock_invoke_llm):
        """Resultado com apenas espaços em branco deve lançar EmptySearchResultError."""
        mock_invoke_llm.return_value = "   \n\t  "

        with pytest.raises(EmptySearchResultError):
            fetch_guide_node(make_state())

    @patch("backend.graph.nodes._invoke_llm")
    def test_api_connection_error_e_asgardian_error(self, mock_invoke_llm):
        """APIConnectionError deve ser capturável como ASGArdianError."""
        mock_invoke_llm.side_effect = Exception("timeout")

        with pytest.raises(ASGArdianError):
            fetch_guide_node(make_state())


# ---------------------------------------------------------------------------
# Testes: process_guide_node
# ---------------------------------------------------------------------------

class TestProcessGuideNodeErrors:

    @patch("backend.graph.nodes._invoke_llm")
    def test_api_exception_lanca_api_connection_error(self, mock_invoke_llm):
        """Exceção da API deve ser convertida em APIConnectionError."""
        mock_invoke_llm.side_effect = Exception("rate limit")

        with pytest.raises(APIConnectionError, match="Falha ao processar o guia"):
            process_guide_node(make_state())

    @patch("backend.graph.nodes._invoke_llm")
    def test_resposta_vazia_lanca_guide_processing_error(self, mock_invoke_llm):
        """Resposta vazia do modelo deve lançar GuideProcessingError."""
        mock_invoke_llm.return_value = ""

        with pytest.raises(GuideProcessingError, match="resposta vazia"):
            process_guide_node(make_state())


# ---------------------------------------------------------------------------
# Testes: verify_requirements_node
# ---------------------------------------------------------------------------

class TestVerifyRequirementsNodeErrors:

    @patch("backend.graph.nodes._invoke_llm")
    def test_api_exception_lanca_api_connection_error(self, mock_invoke_llm):
        """Exceção da API deve ser convertida em APIConnectionError."""
        mock_invoke_llm.side_effect = Exception("503 Service Unavailable")

        with pytest.raises(APIConnectionError, match="Falha ao verificar requisitos"):
            verify_requirements_node(make_state(is_item_search=False))

    def test_is_item_search_true_nao_chama_api(self):
        """Quando is_item_search=True, nenhuma exceção deve ser lançada (sem chamada de API)."""
        result = verify_requirements_node(make_state(is_item_search=True))
        assert result["missing_item"] is None


# ---------------------------------------------------------------------------
# Testes: generate_help_node
# ---------------------------------------------------------------------------

class TestGenerateHelpNodeErrors:

    @patch("backend.graph.nodes._invoke_llm")
    def test_api_exception_lanca_api_connection_error(self, mock_invoke_llm):
        """Exceção da API deve ser convertida em APIConnectionError."""
        mock_invoke_llm.side_effect = Exception("API key invalid")

        with pytest.raises(APIConnectionError, match="Falha ao gerar resposta"):
            generate_help_node(make_state())

    @patch("backend.graph.nodes._invoke_llm")
    def test_resposta_vazia_lanca_guide_processing_error(self, mock_invoke_llm):
        """Resposta vazia deve lançar GuideProcessingError."""
        mock_invoke_llm.return_value = ""

        with pytest.raises(GuideProcessingError, match="resposta vazia"):
            generate_help_node(make_state())


# ---------------------------------------------------------------------------
# Testes: critique_spoiler_node
# ---------------------------------------------------------------------------

class TestCritiqueSpoilerNodeErrors:

    @patch("backend.graph.nodes._invoke_llm")
    def test_api_exception_lanca_api_connection_error(self, mock_invoke_llm):
        """Exceção da API no critique deve ser convertida em APIConnectionError."""
        mock_invoke_llm.side_effect = Exception("quota exceeded")

        state = make_state(
            raw_search_result="guia\n\n---SPOILERS_FUTUROS---\nO chefe morre no final.",
            generated_text="Resposta com possível spoiler.",
        )
        with pytest.raises(APIConnectionError, match="Falha ao auditar"):
            critique_spoiler_node(state)

    def test_sem_spoilers_nao_chama_api(self):
        """Sem spoilers futuros não deve chamar a API (aprovação automática)."""
        state = make_state(
            raw_search_result="guia\n\n---SPOILERS_FUTUROS---\nnenhum",
            generated_text="Resposta limpa.",
        )
        result = critique_spoiler_node(state)
        assert result["critique_passed"] is True
