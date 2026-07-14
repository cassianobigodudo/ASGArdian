# -*- coding: utf-8 -*-
"""
test_nodes.py — Testes unitários dos 5 nós do grafo ASGArdian.

Todos os testes usam mocks para isolar a lógica dos nós
sem depender da API do Groq/Gemini ou de conexão com a internet.

Cobertura:
- fetch_guide_node: sucesso e falha de API
- process_guide_node: extração correta, sem requisitos, sem spoilers
- verify_requirements_node: inventário completo, item faltando, is_item_search=True
- generate_help_node: modo hint, modo answer, reescrita após critique falhar
- critique_spoiler_node: aprovado, reprovado, sem spoilers (aprovação automática)
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.graph.state import AgentState
from backend.graph.nodes import (
    fetch_guide_node,
    process_guide_node,
    verify_requirements_node,
    generate_help_node,
    critique_spoiler_node,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_state(**overrides) -> AgentState:
    """Cria um AgentState válido com valores padrão, aceitando overrides."""
    base = AgentState(
        game_name="Borderlands 2",
        mission_name="Lights Out",
        current_issue="Não consigo restaurar a energia na subestação.",
        original_issue="Não consigo restaurar a energia na subestação.",
        help_type="hint",
        player_inventory=["Shotgun Torque", "Shield Adaptive"],
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
# Testes: fetch_guide_node
# ---------------------------------------------------------------------------

class TestFetchGuideNode:

    @patch("backend.graph.nodes._invoke_llm")
    def test_retorna_raw_search_result_populado(self, mock_invoke_llm):
        """Sucesso: deve retornar raw_search_result com o conteúdo da busca."""
        mock_invoke_llm.return_value = "Guia completo da missão Lights Out..."

        state = make_state()
        result = fetch_guide_node(state)

        assert "raw_search_result" in result
        assert "Lights Out" in result["raw_search_result"]
        assert mock_invoke_llm.called

    @patch("backend.graph.nodes._invoke_llm")
    def test_segunda_passagem_usa_current_issue_atualizado(self, mock_invoke_llm):
        """Sucesso HITL: na segunda passagem, current_issue já foi atualizado pelo roteador."""
        mock_invoke_llm.return_value = "Como obter a Chave de Acesso..."

        state = make_state(
            current_issue="como obter Chave de Acesso em Borderlands 2",
            is_item_search=True,
        )
        result = fetch_guide_node(state)

        assert "raw_search_result" in result
        # Verifica que o _invoke_llm foi chamado
        assert mock_invoke_llm.called
        # Verifica que o prompt contém o current_issue atualizado
        call_prompt = mock_invoke_llm.call_args[0][0]
        assert "como obter Chave de Acesso" in call_prompt

    @patch("backend.graph.nodes._invoke_llm")
    def test_falha_de_api_propaga_excecao(self, mock_invoke_llm):
        """Falha: exceção da API deve se propagar para o executor tratar."""
        mock_invoke_llm.side_effect = Exception("API timeout")

        state = make_state()
        from backend.errors import APIConnectionError
        with pytest.raises(APIConnectionError):
            fetch_guide_node(state)

    @patch("backend.graph.nodes._invoke_llm")
    def test_resposta_vazia_lanca_erro(self, mock_invoke_llm):
        """Falha: resposta vazia deve lançar EmptySearchResultError."""
        mock_invoke_llm.return_value = ""

        state = make_state()
        from backend.errors import EmptySearchResultError
        with pytest.raises(EmptySearchResultError):
            fetch_guide_node(state)


# ---------------------------------------------------------------------------
# Testes: process_guide_node
# ---------------------------------------------------------------------------

class TestProcessGuideNode:

    @patch("backend.graph.nodes._invoke_llm")
    def test_extrai_requisitos_passos_e_spoilers(self, mock_invoke_llm):
        """Sucesso: deve extrair corretamente os três blocos do formato estruturado."""
        llm_output = (
            "PREREQUISITOS: Chave de Acesso, Nível 10\n"
            "PASSOS: 1. Vire a esquerda. 2. Use a alavanca.\n"
            "SPOILERS_FUTUROS: O chefe aparece após completar a missão."
        )
        mock_invoke_llm.return_value = llm_output

        state = make_state(raw_search_result="conteúdo bruto do guia")
        result = process_guide_node(state)

        assert "Chave de Acesso" in result["required_requirements"]
        assert "Nível 10" in result["required_requirements"]
        assert "Vire a esquerda" in result["generated_text"]
        assert "---SPOILERS_FUTUROS---" in result["raw_search_result"]
        assert "chefe aparece" in result["raw_search_result"]

    @patch("backend.graph.nodes._invoke_llm")
    def test_sem_requisitos_retorna_lista_vazia(self, mock_invoke_llm):
        """Sucesso: 'nenhum' nos pré-requisitos deve resultar em lista vazia."""
        llm_output = (
            "PREREQUISITOS: nenhum\n"
            "PASSOS: 1. Vá para a direita.\n"
            "SPOILERS_FUTUROS: nenhum"
        )
        mock_invoke_llm.return_value = llm_output

        state = make_state(raw_search_result="guia simples")
        result = process_guide_node(state)

        assert result["required_requirements"] == []

    @patch("backend.graph.nodes._invoke_llm")
    def test_sem_spoilers_futuros_registra_nenhum(self, mock_invoke_llm):
        """Sucesso: sem spoilers futuros deve registrar 'nenhum' na seção."""
        llm_output = (
            "PREREQUISITOS: nenhum\n"
            "PASSOS: 1. Pressione o botão.\n"
            "SPOILERS_FUTUROS: nenhum"
        )
        mock_invoke_llm.return_value = llm_output

        state = make_state(raw_search_result="guia")
        result = process_guide_node(state)

        assert "---SPOILERS_FUTUROS---" in result["raw_search_result"]
        spoiler_content = result["raw_search_result"].split("---SPOILERS_FUTUROS---")[-1].strip()
        assert spoiler_content.lower() == "nenhum"

    @patch("backend.graph.nodes._invoke_llm")
    def test_resposta_vazia_lanca_erro(self, mock_invoke_llm):
        """Falha: resposta vazia deve lançar GuideProcessingError."""
        mock_invoke_llm.return_value = ""

        state = make_state(raw_search_result="guia")
        from backend.errors import GuideProcessingError
        with pytest.raises(GuideProcessingError):
            process_guide_node(state)


# ---------------------------------------------------------------------------
# Testes: verify_requirements_node
# ---------------------------------------------------------------------------

class TestVerifyRequirementsNode:

    @patch("backend.graph.nodes._invoke_llm")
    def test_inventario_completo_retorna_missing_none(self, mock_invoke_llm):
        """Sucesso: jogador tem todos os itens, missing_item deve ser None."""
        mock_invoke_llm.return_value = "MISSING_ITEM: none"

        state = make_state(
            required_requirements=["Shotgun Torque"],
            player_inventory=["Shotgun Torque", "Shield Adaptive"],
        )
        result = verify_requirements_node(state)

        assert result["missing_item"] is None

    @patch("backend.graph.nodes._invoke_llm")
    def test_item_faltando_retorna_nome_do_item(self, mock_invoke_llm):
        """Falha de inventário: missing_item deve conter o nome do item ausente."""
        mock_invoke_llm.return_value = "MISSING_ITEM: Chave de Acesso"

        state = make_state(
            required_requirements=["Chave de Acesso"],
            player_inventory=["Shotgun Torque"],
        )
        result = verify_requirements_node(state)

        assert result["missing_item"] == "Chave de Acesso"

    def test_is_item_search_true_pula_verificacao(self):
        """RN05: quando is_item_search=True, o nó deve retornar missing_item=None sem chamar LLM."""
        state = make_state(
            is_item_search=True,
            required_requirements=["Item que não existe"],
            player_inventory=[],
        )
        # Sem mock — se chamar o LLM vai falhar por falta de API key real
        result = verify_requirements_node(state)

        assert result["missing_item"] is None

    def test_sem_requisitos_retorna_missing_none_sem_chamar_llm(self):
        """Otimização: sem requisitos não deve chamar o LLM."""
        state = make_state(
            required_requirements=[],
            player_inventory=["Qualquer item"],
        )
        result = verify_requirements_node(state)

        assert result["missing_item"] is None

    @patch("backend.graph.nodes._invoke_llm")
    def test_api_exception_lanca_api_connection_error(self, mock_invoke_llm):
        """Falha: exceção da API deve lançar APIConnectionError."""
        mock_invoke_llm.side_effect = Exception("API error")

        state = make_state(required_requirements=["Item"])
        from backend.errors import APIConnectionError
        with pytest.raises(APIConnectionError):
            verify_requirements_node(state)


# ---------------------------------------------------------------------------
# Testes: generate_help_node
# ---------------------------------------------------------------------------

class TestGenerateHelpNode:

    @patch("backend.graph.nodes._invoke_llm")
    def test_modo_hint_gera_dica_sutil(self, mock_invoke_llm):
        """Sucesso hint: deve gerar resposta contendo o marcador anti-spoiler."""
        resposta = "Observe os elementos visuais da sala com atenção. [Nenhum spoiler de enredo foi incluído nesta resposta.]"
        mock_invoke_llm.return_value = resposta

        state = make_state(help_type="hint", generated_text="1. Vá para a direita.")
        result = generate_help_node(state)

        assert "generated_text" in result
        assert len(result["generated_text"]) > 0

    @patch("backend.graph.nodes._invoke_llm")
    def test_modo_answer_gera_solucao_direta(self, mock_invoke_llm):
        """Sucesso answer: deve gerar solução numerada."""
        resposta = "1. Vá para a esquerda.\n2. Use a alavanca.\n[Nenhum spoiler de enredo foi incluído nesta resposta.]"
        mock_invoke_llm.return_value = resposta

        state = make_state(help_type="answer", generated_text="1. Vá para a esquerda.")
        result = generate_help_node(state)

        assert "generated_text" in result
        assert len(result["generated_text"]) > 0

    @patch("backend.graph.nodes._invoke_llm")
    def test_reescrita_apos_critique_falhar_injeta_feedback(self, mock_invoke_llm):
        """Reescrita: quando critique_passed=False, o prompt deve conter aviso de spoiler."""
        mock_invoke_llm.return_value = "Resposta corrigida sem spoiler. [Nenhum spoiler de enredo foi incluído nesta resposta.]"

        state = make_state(
            help_type="hint",
            critique_passed=False,
            generated_text="Resposta anterior com spoiler",
        )
        result = generate_help_node(state)

        # Verifica que _invoke_llm foi chamado
        assert mock_invoke_llm.called
        # Verifica que o prompt contém o feedback do critique
        call_prompt = mock_invoke_llm.call_args[0][0]
        assert "REPROVADA" in call_prompt or "spoiler" in call_prompt.lower()
        assert "generated_text" in result

    @patch("backend.graph.nodes._invoke_llm")
    def test_resposta_vazia_lanca_erro(self, mock_invoke_llm):
        """Falha: resposta vazia deve lançar GuideProcessingError."""
        mock_invoke_llm.return_value = ""

        state = make_state(help_type="hint", generated_text="guia")
        from backend.errors import GuideProcessingError
        with pytest.raises(GuideProcessingError):
            generate_help_node(state)

    @patch("backend.graph.nodes._invoke_llm")
    def test_api_exception_lanca_api_connection_error(self, mock_invoke_llm):
        """Falha: exceção da API deve lançar APIConnectionError."""
        mock_invoke_llm.side_effect = Exception("API error")

        state = make_state(help_type="hint", generated_text="guia")
        from backend.errors import APIConnectionError
        with pytest.raises(APIConnectionError):
            generate_help_node(state)


# ---------------------------------------------------------------------------
# Testes: critique_spoiler_node
# ---------------------------------------------------------------------------

class TestCritiqueSpoilerNode:

    @patch("backend.graph.nodes._invoke_llm")
    def test_resposta_aprovada_seta_critique_passed_true(self, mock_invoke_llm):
        """Sucesso: CRITIQUE_RESULT: PASSED deve setar critique_passed=True e preencher final_response."""
        mock_invoke_llm.return_value = "CRITIQUE_RESULT: PASSED"

        state = make_state(
            raw_search_result="conteúdo\n\n---SPOILERS_FUTUROS---\nO chefe morre no final.",
            generated_text="Vá para a esquerda e use a alavanca.",
        )
        result = critique_spoiler_node(state)

        assert result["critique_passed"] is True
        assert result["final_response"] == "Vá para a esquerda e use a alavanca."

    @patch("backend.graph.nodes._invoke_llm")
    def test_resposta_reprovada_seta_critique_passed_false(self, mock_invoke_llm):
        """Falha: CRITIQUE_RESULT: FAILED deve setar critique_passed=False e final_response vazia."""
        mock_invoke_llm.return_value = (
            "CRITIQUE_RESULT: FAILED\nREASON: A resposta menciona a morte do chefe."
        )

        state = make_state(
            raw_search_result="conteúdo\n\n---SPOILERS_FUTUROS---\nO chefe morre no final.",
            generated_text="Após resolver o puzzle, o chefe morre.",
        )
        result = critique_spoiler_node(state)

        assert result["critique_passed"] is False
        assert result["final_response"] == ""

    def test_sem_spoilers_futuros_aprovacao_automatica(self):
        """Otimização: sem spoilers identificados, aprovação deve ser automática sem chamar LLM."""
        state = make_state(
            raw_search_result="conteúdo\n\n---SPOILERS_FUTUROS---\nnenhum",
            generated_text="Pressione o botão vermelho.",
        )
        # Sem mock — não deve chamar o LLM
        result = critique_spoiler_node(state)

        assert result["critique_passed"] is True
        assert result["final_response"] == "Pressione o botão vermelho."

    def test_sem_marcacao_spoilers_aprovacao_automatica(self):
        """Segurança: raw_search_result sem marcação de spoilers também aprova automaticamente."""
        state = make_state(
            raw_search_result="conteúdo sem marcação",
            generated_text="Vire a esquerda.",
        )
        result = critique_spoiler_node(state)

        assert result["critique_passed"] is True

    @patch("backend.graph.nodes._invoke_llm")
    def test_api_exception_lanca_api_connection_error(self, mock_invoke_llm):
        """Falha: exceção da API deve lançar APIConnectionError."""
        mock_invoke_llm.side_effect = Exception("API error")

        state = make_state(
            raw_search_result="conteúdo\n\n---SPOILERS_FUTUROS---\nSpoiler importante",
            generated_text="Resposta",
        )
        from backend.errors import APIConnectionError
        with pytest.raises(APIConnectionError):
            critique_spoiler_node(state)
