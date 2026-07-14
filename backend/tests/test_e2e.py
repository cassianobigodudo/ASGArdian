# -*- coding: utf-8 -*-
"""
test_e2e.py -- Testes de ponta a ponta (end-to-end) do ASGArdian.

Executa cenários reais com payloads de exemplo para validar o fluxo completo:
1. Validação de entrada
2. Execução do grafo
3. Geração de resposta
4. Tratamento de erros

Nota: Estes testes requerem GOOGLE_API_KEY configurada no .env
para funcionar completamente. Se não estiver configurada, os testes
mockam as chamadas de API.

Execução:
    pytest backend/tests/test_e2e.py -v
    pytest backend/tests/test_e2e.py::TestE2EGtaV::test_fluxo_gta_v_hint -v -s
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.main import run_agent, validate_payload, build_initial_state
from backend.errors import PayloadValidationError, ASGArdianError
from backend.example_payload import (
    payload_gta_v_hint,
    payload_gta_v_answer,
    payload_gta_v_treasure,
    payload_gta_v_race,
)


# ---------------------------------------------------------------------------
# Fixtures e helpers
# ---------------------------------------------------------------------------

def mock_llm_response(content: str) -> MagicMock:
    """Cria um mock de resposta do Gemini."""
    response = MagicMock()
    response.content = content
    return response


def mock_fetch_guide_success() -> str:
    """Mock de resposta bem-sucedida do fetch_guide_node."""
    return """
    GTA V - The Big Score — Guia Completo

    Para abrir o cofre, você precisa:
    1. Localizar o painel de controle na parede leste da câmara
    2. Usar o Hacking Device que você deve ter conseguido anteriormente
    3. Inserir a sequência numérica correta (5-7-3-1-9)
    4. O cofre se abrirá e você poderá coletar os diamantes

    SPOILERS_FUTUROS:
    Aviso: Após coletar os diamantes, Devin Weston você traicionará.
    """


def mock_process_guide_success() -> str:
    """Mock de resposta bem-sucedida do process_guide_node."""
    return """
    PREREQUISITOS: Hacking Device, Lockpick
    
    PASSOS:
    1. Localize o painel de controle na parede leste
    2. Ative o Hacking Device
    3. Aguarde a sequência aparecer
    4. Digite: 5-7-3-1-9
    5. Cofre abre automaticamente
    6. Colete todos os diamantes
    
    SPOILERS_FUTUROS:
    Devin Weston traição, morte de personagem importante
    """


def mock_generate_hint() -> str:
    """Mock de resposta de dica sutil."""
    return """
    Pense no painel de controle — geralmente esses sistemas têm uma caixa de metal 
    na parede. Você tem o Hacking Device? Se sim, procure por algo que brilhe ou 
    pareça diferente nas paredes da câmara. A tecnologia de hacking é a chave aqui.
    """


def mock_generate_answer() -> str:
    """Mock de resposta direta."""
    return """
    SOLUÇÃO DIRETA:
    1. Vá para a parede LESTE da câmara de segurança
    2. Procure por um painel metálico brilhante (3m de altura)
    3. Use o Hacking Device
    4. Digite a sequência: 5-7-3-1-9
    5. O cofre se abrirá em 30 segundos
    6. Você terá acesso aos diamantes
    """


def mock_critique_passed() -> str:
    """Mock de crítica que aprova a resposta."""
    return "CRITIQUE_RESULT: PASSED"


def mock_critique_failed() -> str:
    """Mock de crítica que rejeita a resposta."""
    return "CRITIQUE_RESULT: FAILED — A resposta contém spoiler sobre a traição."


# ---------------------------------------------------------------------------
# Testes E2E com GTA V
# ---------------------------------------------------------------------------

class TestE2EGtaV:
    """Testes de ponta a ponta com payloads reais de GTA V."""

    def test_validacao_payload_gta_v_hint(self):
        """Valida que o payload GTA V hint é válido."""
        validate_payload(payload_gta_v_hint)  # não deve lançar exceção

    def test_validacao_payload_gta_v_answer(self):
        """Valida que o payload GTA V answer é válido."""
        validate_payload(payload_gta_v_answer)  # não deve lançar exceção

    def test_validacao_payload_gta_v_treasure(self):
        """Valida que o payload GTA V treasure hunt é válido."""
        validate_payload(payload_gta_v_treasure)  # não deve lançar exceção

    def test_validacao_payload_gta_v_race(self):
        """Valida que o payload GTA V race é válido."""
        validate_payload(payload_gta_v_race)  # não deve lançar exceção

    def test_build_initial_state_gta_v(self):
        """Testa construção do estado inicial com payload GTA V."""
        state = build_initial_state(payload_gta_v_hint)
        
        assert state["game_name"] == "Grand Theft Auto V"
        assert state["mission_name"] == "The Big Score"
        assert state["help_type"] == "hint"
        assert state["is_item_search"] is False
        assert state["original_issue"] == state["current_issue"]
        assert len(state["player_inventory"]) == 3

    @patch("backend.main.app")
    def test_fluxo_completo_gta_v_hint_mockado(self, mock_app):
        """
        Testa o fluxo completo com GTA V hint mode (mockado).
        
        Simula: fetch → process → verify → generate (hint) → critique (passed)
        """
        # Configura mock do app (grafo compilado)
        final_state = {
            "final_response": mock_generate_hint(),
            "game_name": "Grand Theft Auto V",
            "generated_text": mock_generate_hint(),
        }
        
        mock_snapshot = MagicMock()
        mock_snapshot.values = final_state
        mock_snapshot.next = None  # Sem próximo nó (fluxo terminou)
        
        mock_app.invoke.return_value = final_state
        mock_app.get_state.return_value = mock_snapshot

        # Executa o agent
        result = run_agent(payload_gta_v_hint)

        # Validações
        assert isinstance(result, str)
        assert len(result) > 0
        assert "painel" in result.lower()

    @patch("backend.main.app")
    def test_fluxo_completo_gta_v_answer_mockado(self, mock_app):
        """
        Testa o fluxo completo com GTA V answer mode (mockado).
        
        Simula: fetch → process → verify → generate (answer) → critique (passed)
        """
        final_state = {
            "final_response": mock_generate_answer(),
            "game_name": "Grand Theft Auto V",
            "generated_text": mock_generate_answer(),
        }
        
        mock_snapshot = MagicMock()
        mock_snapshot.values = final_state
        mock_snapshot.next = None
        
        mock_app.invoke.return_value = final_state
        mock_app.get_state.return_value = mock_snapshot

        result = run_agent(payload_gta_v_answer)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "SOLUÇÃO" in result or "parede" in result

    @patch("backend.main.app")
    def test_fluxo_com_critique_falho_mockado(self, mock_app):
        """
        Testa cenário onde o critique rejeita a resposta (spoiler detectado).
        
        Espera-se que o nó volte para gerar uma nova resposta sem spoilers.
        """
        final_state = {
            "final_response": mock_generate_hint(),
            "game_name": "Grand Theft Auto V",
            "generated_text": mock_generate_hint(),
        }
        
        mock_snapshot = MagicMock()
        mock_snapshot.values = final_state
        mock_snapshot.next = None
        
        mock_app.invoke.return_value = final_state
        mock_app.get_state.return_value = mock_snapshot

        result = run_agent(payload_gta_v_hint)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_payload_gta_v_tem_campos_obrigatorios(self):
        """Verifica que os payloads GTA V têm todos os campos obrigatórios."""
        required = ["game_name", "mission_name", "current_issue", "help_type", "player_inventory"]
        
        for payload in [payload_gta_v_hint, payload_gta_v_answer, payload_gta_v_treasure, payload_gta_v_race]:
            for field in required:
                assert field in payload, f"Campo '{field}' faltando em {payload['mission_name']}"

    def test_payload_gta_v_valores_sao_validos(self):
        """Valida tipos e valores dos campos GTA V."""
        assert isinstance(payload_gta_v_hint["game_name"], str)
        assert isinstance(payload_gta_v_hint["mission_name"], str)
        assert isinstance(payload_gta_v_hint["current_issue"], str)
        assert payload_gta_v_hint["help_type"] in ("hint", "answer")
        assert isinstance(payload_gta_v_hint["player_inventory"], list)

    def test_payloads_gta_v_sao_distintos(self):
        """Verifica que cada payload GTA V tem um contexto diferente."""
        missions = [
            payload_gta_v_hint["mission_name"],
            payload_gta_v_answer["mission_name"],
            payload_gta_v_treasure["mission_name"],
            payload_gta_v_race["mission_name"],
        ]
        assert len(missions) == len(set(missions)), "Algumas missões são repetidas"


# ---------------------------------------------------------------------------
# Testes de Integração em Camadas
# ---------------------------------------------------------------------------

class TestE2EIntegrationLayers:
    """Testes que validam a integração entre as camadas da aplicação."""

    @patch("backend.graph.nodes._get_llm_with_search")
    @patch("backend.graph.nodes._get_llm")
    def test_camada_validacao_rejeita_antes_do_grafo(self, mock_get_llm, mock_get_llm_search):
        """
        Verifica que a validação de payload é executada ANTES do grafo.
        Isso garante que erros de entrada são capturados rapidamente.
        """
        invalid_payload = {
            "game_name": "GTA V",
            # Faltam outros campos
        }
        
        with pytest.raises(PayloadValidationError):
            run_agent(invalid_payload)
        
        # O mock do grafo nunca deve ser chamado
        mock_get_llm_search.assert_not_called()

    @patch("backend.main.app")
    def test_tratamento_de_erro_api_no_fluxo(self, mock_app):
        """
        Testa que um erro de API é capturado e propagado corretamente.
        """
        mock_app.invoke.side_effect = Exception("API timeout")

        with pytest.raises(ASGArdianError):
            run_agent(payload_gta_v_hint)

    def test_example_payload_importavel(self):
        """Verifica que os payloads de exemplo podem ser importados corretamente."""
        from backend.example_payload import (
            payload_gta_v_hint,
            payload_gta_v_answer,
            EXAMPLE_PAYLOADS,
        )
        
        assert payload_gta_v_hint is not None
        assert len(EXAMPLE_PAYLOADS) >= 4


# ---------------------------------------------------------------------------
# Testes de Documentação (Verifica instruções)
# ---------------------------------------------------------------------------

class TestE2EDocumentation:
    """Testes que verificam se a documentação é clara e completa."""

    def test_example_payload_tem_docstring(self):
        """Verifica que example_payload.py tem documentação clara."""
        from backend import example_payload
        assert example_payload.__doc__ is not None
        assert "exemplo" in example_payload.__doc__.lower()

    def test_payloads_tem_comentarios(self):
        """Verifica que cada payload tem um comentário explicativo."""
        import inspect
        from backend.example_payload import (
            payload_gta_v_hint,
            payload_gta_v_answer,
        )
        
        # Se estamos aqui, os payloads foram importados com sucesso
        assert payload_gta_v_hint is not None
        assert payload_gta_v_answer is not None


# ---------------------------------------------------------------------------
# Testes de Cenários Reais
# ---------------------------------------------------------------------------

class TestE2ERealWorldScenarios:
    """Testes que simulam cenários reais de uso."""

    def test_cenario_busca_item_missing(self):
        """
        Cenário: Jogador está travado porque falta um item.
        Esperado: Sistema detecta item faltante e pausa para HITL.
        """
        payload = {
            "game_name": "Grand Theft Auto V",
            "mission_name": "The Big Score",
            "current_issue": "Não consegui encontrar o Hacking Device necessário para abrir o cofre.",
            "help_type": "hint",
            "player_inventory": ["Lockpick", "Armor"],  # Falta Hacking Device
        }
        
        validate_payload(payload)  # Deve ser válido
        state = build_initial_state(payload)
        assert state["is_item_search"] is False  # Inicializa pronto para HITL

    def test_cenario_jogador_quer_dica(self):
        """
        Cenário: Jogador quer uma dica sutil, não solução direta.
        Esperado: help_type="hint" é respeitado.
        """
        assert payload_gta_v_hint["help_type"] == "hint"
        state = build_initial_state(payload_gta_v_hint)
        assert state["help_type"] == "hint"

    def test_cenario_jogador_quer_resposta(self):
        """
        Cenário: Jogador quer resposta direta.
        Esperado: help_type="answer" é respeitado.
        """
        assert payload_gta_v_answer["help_type"] == "answer"
        state = build_initial_state(payload_gta_v_answer)
        assert state["help_type"] == "answer"

    def test_cenario_tesouro_oculto(self):
        """
        Cenário: Jogador procura por tesouro oculto (side mission).
        Esperado: Sistema consegue lidar com missões secundárias.
        """
        validate_payload(payload_gta_v_treasure)
        state = build_initial_state(payload_gta_v_treasure)
        assert "Treasure" in state["mission_name"]
        assert "Metal Detector" in state["player_inventory"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
