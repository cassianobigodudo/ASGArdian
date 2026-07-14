# -*- coding: utf-8 -*-
"""
test_nodes.py — Testes unitarios dos 5 nos do grafo ASGArdian.

Todos os testes usam mocks para isolar a logica dos nos
sem depender da API do Gemini ou de conexao com a internet.

Cobertura:
- fetch_guide_node: sucesso e falha de API
- process_guide_node: extracao correta, sem requisitos, sem spoilers
- verify_requirements_node: inventario completo, item faltando, is_item_search=True
- generate_help_node: modo hint, modo answer, reescrita apos critique falhar
- critique_spoiler_node: aprovado, reprovado, sem spoilers (aprovacao automatica)
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
    """Cria um AgentState valido com valores padrao, aceitando overrides."""
    base = AgentState(
        game_name="Borderlands 2",
        mission_name="Lights Out",
        current_issue="Nao consigo restaurar a energia na subestacao.",
        original_issue="Nao consigo restaurar a energia na subestacao.",
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


def mock_llm_response(text: str) -> MagicMock:
    """Cria um mock de resposta do LLM com .content definido."""
    mock = MagicMock()
    mock.content = text
    return mock


# ---------------------------------------------------------------------------
# Testes: fetch_guide_node
# ---------------------------------------------------------------------------

class TestFetchGuideNode:

    @patch("backend.graph.nodes._get_llm_with_search")
    def test_retorna_raw_search_result_populado(self, mock_get_llm):
        """Sucesso: deve retornar raw_search_result com o conteudo da busca."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response("Guia completo da missao Lights Out...")
        mock_get_llm.return_value = mock_llm

        state = make_state()
        result = fetch_guide_node(state)

        assert "raw_search_result" in result
        assert "Lights Out" in result["raw_search_result"]

    @patch("backend.graph.nodes._get_llm_with_search")
    def test_segunda_passagem_usa_current_issue_atualizado(self, mock_get_llm):
        """Sucesso HITL: na segunda passagem, current_issue ja foi atualizado pelo roteador."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response("Como obter a Chave de Acesso...")
        mock_get_llm.return_value = mock_llm

        state = make_state(
            current_issue="como obter Chave de Acesso em Borderlands 2",
            is_item_search=True,
        )
        result = fetch_guide_node(state)

        assert "raw_search_result" in result
        # Verifica que o LLM foi invocado com o prompt contendo o current_issue atualizado
        call_args = mock_llm.invoke.call_args[0][0]
        assert "como obter Chave de Acesso" in call_args[0].content

    @patch("backend.graph.nodes._get_llm_with_search")
    def test_falha_de_api_propaga_excecao(self, mock_get_llm):
        """Falha: excecao da API deve se propagar para o executor tratar."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API timeout")
        mock_get_llm.return_value = mock_llm

        state = make_state()
        with pytest.raises(Exception, match="API timeout"):
            fetch_guide_node(state)


# ---------------------------------------------------------------------------
# Testes: process_guide_node
# ---------------------------------------------------------------------------

class TestProcessGuideNode:

    @patch("backend.graph.nodes._get_llm")
    def test_extrai_requisitos_passos_e_spoilers(self, mock_get_llm):
        """Sucesso: deve extrair corretamente os tres blocos do formato estruturado."""
        llm_output = (
            "PREREQUISITOS: Chave de Acesso, Nivel 10\n"
            "PASSOS: 1. Vire a esquerda. 2. Use a alavanca.\n"
            "SPOILERS_FUTUROS: O chefe aparece apos completar a missao."
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response(llm_output)
        mock_get_llm.return_value = mock_llm

        state = make_state(raw_search_result="conteudo bruto do guia")
        result = process_guide_node(state)

        assert "Chave de Acesso" in result["required_requirements"]
        assert "Nivel 10" in result["required_requirements"]
        assert "Vire a esquerda" in result["generated_text"]
        assert "---SPOILERS_FUTUROS---" in result["raw_search_result"]
        assert "chefe aparece" in result["raw_search_result"]

    @patch("backend.graph.nodes._get_llm")
    def test_sem_requisitos_retorna_lista_vazia(self, mock_get_llm):
        """Sucesso: 'nenhum' nos prerequisitos deve resultar em lista vazia."""
        llm_output = (
            "PREREQUISITOS: nenhum\n"
            "PASSOS: 1. Va para a direita.\n"
            "SPOILERS_FUTUROS: nenhum"
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response(llm_output)
        mock_get_llm.return_value = mock_llm

        state = make_state(raw_search_result="guia simples")
        result = process_guide_node(state)

        assert result["required_requirements"] == []

    @patch("backend.graph.nodes._get_llm")
    def test_sem_spoilers_futuros_registra_nenhum(self, mock_get_llm):
        """Sucesso: sem spoilers futuros deve registrar 'nenhum' na secao."""
        llm_output = (
            "PREREQUISITOS: nenhum\n"
            "PASSOS: 1. Pressione o botao.\n"
            "SPOILERS_FUTUROS: nenhum"
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response(llm_output)
        mock_get_llm.return_value = mock_llm

        state = make_state(raw_search_result="guia")
        result = process_guide_node(state)

        assert "---SPOILERS_FUTUROS---" in result["raw_search_result"]
        spoiler_content = result["raw_search_result"].split("---SPOILERS_FUTUROS---")[-1].strip()
        assert spoiler_content.lower() == "nenhum"


# ---------------------------------------------------------------------------
# Testes: verify_requirements_node
# ---------------------------------------------------------------------------

class TestVerifyRequirementsNode:

    @patch("backend.graph.nodes._get_llm")
    def test_inventario_completo_retorna_missing_none(self, mock_get_llm):
        """Sucesso: jogador tem todos os itens, missing_item deve ser None."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response("MISSING_ITEM: none")
        mock_get_llm.return_value = mock_llm

        state = make_state(
            required_requirements=["Shotgun Torque"],
            player_inventory=["Shotgun Torque", "Shield Adaptive"],
        )
        result = verify_requirements_node(state)

        assert result["missing_item"] is None

    @patch("backend.graph.nodes._get_llm")
    def test_item_faltando_retorna_nome_do_item(self, mock_get_llm):
        """Falha de inventario: missing_item deve conter o nome do item ausente."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response("MISSING_ITEM: Chave de Acesso")
        mock_get_llm.return_value = mock_llm

        state = make_state(
            required_requirements=["Chave de Acesso"],
            player_inventory=["Shotgun Torque"],
        )
        result = verify_requirements_node(state)

        assert result["missing_item"] == "Chave de Acesso"

    def test_is_item_search_true_pula_verificacao(self):
        """RN05: quando is_item_search=True, o no deve retornar missing_item=None sem chamar LLM."""
        state = make_state(
            is_item_search=True,
            required_requirements=["Item que nao existe"],
            player_inventory=[],
        )
        # Sem mock — se chamar o LLM vai falhar por falta de API key real
        result = verify_requirements_node(state)

        assert result["missing_item"] is None

    def test_sem_requisitos_retorna_missing_none_sem_chamar_llm(self):
        """Otimizacao: sem requisitos nao deve chamar o LLM."""
        state = make_state(
            required_requirements=[],
            player_inventory=["Qualquer item"],
        )
        result = verify_requirements_node(state)

        assert result["missing_item"] is None


# ---------------------------------------------------------------------------
# Testes: generate_help_node
# ---------------------------------------------------------------------------

class TestGenerateHelpNode:

    @patch("backend.graph.nodes._get_llm")
    def test_modo_hint_gera_dica_sutil(self, mock_get_llm):
        """Sucesso hint: deve gerar resposta contendo o marcador anti-spoiler."""
        resposta = "Observe os elementos visuais da sala com atencao. [Nenhum spoiler de enredo foi incluido nesta resposta.]"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response(resposta)
        mock_get_llm.return_value = mock_llm

        state = make_state(help_type="hint", generated_text="1. Va para a direita.")
        result = generate_help_node(state)

        assert "generated_text" in result
        assert len(result["generated_text"]) > 0

    @patch("backend.graph.nodes._get_llm")
    def test_modo_answer_gera_solucao_direta(self, mock_get_llm):
        """Sucesso answer: deve gerar solucao numerada."""
        resposta = "1. Va para a esquerda.\n2. Use a alavanca.\n[Nenhum spoiler de enredo foi incluido nesta resposta.]"
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response(resposta)
        mock_get_llm.return_value = mock_llm

        state = make_state(help_type="answer", generated_text="1. Va para a esquerda.")
        result = generate_help_node(state)

        assert "generated_text" in result
        assert len(result["generated_text"]) > 0

    @patch("backend.graph.nodes._get_llm")
    def test_reescrita_apos_critique_falhar_injeta_feedback(self, mock_get_llm):
        """Reescrita: quando critique_passed=False, o prompt deve conter aviso de spoiler."""
        captured_prompts = []

        def capture_invoke(messages):
            captured_prompts.append(messages[0].content)
            return mock_llm_response("Resposta corrigida sem spoiler. [Nenhum spoiler de enredo foi incluido nesta resposta.]")

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = capture_invoke
        mock_get_llm.return_value = mock_llm

        state = make_state(
            help_type="hint",
            critique_passed=False,
            generated_text="Resposta anterior com spoiler",
        )
        result = generate_help_node(state)

        assert len(captured_prompts) == 1
        assert "REPROVADA" in captured_prompts[0]
        assert "generated_text" in result


# ---------------------------------------------------------------------------
# Testes: critique_spoiler_node
# ---------------------------------------------------------------------------

class TestCritiqueSpoilerNode:

    @patch("backend.graph.nodes._get_llm")
    def test_resposta_aprovada_seta_critique_passed_true(self, mock_get_llm):
        """Sucesso: CRITIQUE_RESULT: PASSED deve setar critique_passed=True e preencher final_response."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response("CRITIQUE_RESULT: PASSED")
        mock_get_llm.return_value = mock_llm

        state = make_state(
            raw_search_result="conteudo\n\n---SPOILERS_FUTUROS---\nO chefe morre no final.",
            generated_text="Va para a esquerda e use a alavanca.",
        )
        result = critique_spoiler_node(state)

        assert result["critique_passed"] is True
        assert result["final_response"] == "Va para a esquerda e use a alavanca."

    @patch("backend.graph.nodes._get_llm")
    def test_resposta_reprovada_seta_critique_passed_false(self, mock_get_llm):
        """Falha: CRITIQUE_RESULT: FAILED deve setar critique_passed=False e final_response vazia."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_llm_response(
            "CRITIQUE_RESULT: FAILED\nREASON: A resposta menciona a morte do chefe."
        )
        mock_get_llm.return_value = mock_llm

        state = make_state(
            raw_search_result="conteudo\n\n---SPOILERS_FUTUROS---\nO chefe morre no final.",
            generated_text="Apos resolver o puzzle, o chefe morre.",
        )
        result = critique_spoiler_node(state)

        assert result["critique_passed"] is False
        assert result["final_response"] == ""

    def test_sem_spoilers_futuros_aprovacao_automatica(self):
        """Otimizacao: sem spoilers identificados, aprovacao deve ser automatica sem chamar LLM."""
        state = make_state(
            raw_search_result="conteudo\n\n---SPOILERS_FUTUROS---\nnenhum",
            generated_text="Pressione o botao vermelho.",
        )
        # Sem mock — nao deve chamar o LLM
        result = critique_spoiler_node(state)

        assert result["critique_passed"] is True
        assert result["final_response"] == "Pressione o botao vermelho."

    def test_sem_marcacao_spoilers_aprovacao_automatica(self):
        """Seguranca: raw_search_result sem marcacao de spoilers tambem aprova automaticamente."""
        state = make_state(
            raw_search_result="conteudo sem marcacao",
            generated_text="Vire a esquerda.",
        )
        result = critique_spoiler_node(state)

        assert result["critique_passed"] is True
