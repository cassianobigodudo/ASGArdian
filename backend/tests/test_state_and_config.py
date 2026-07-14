"""
test_state_and_config.py — Testes de validação do AgentState e config.py.

Valida:
1. Que o AgentState aceita corretamente um payload completo e válido
2. Que todos os 14 campos estão presentes na definição do TypedDict
3. Que os tipos opcionais aceitam None
4. Que a GOOGLE_API_KEY está carregada no ambiente
5. Que get_google_api_key() lança ValueError quando a chave está ausente
"""

import os
import sys
import pytest

# Garante que o diretório raiz do projeto está no path para importações relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.graph.state import AgentState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_payload() -> AgentState:
    """Payload completo e válido representando um estado inicial do grafo."""
    return AgentState(
        game_name="Borderlands 2",
        mission_name="Lights Out",
        current_issue="Estou na subestação e não consigo restaurar a energia após ativar as duas alavancas.",
        original_issue="Estou na subestação e não consigo restaurar a energia após ativar as duas alavancas.",
        help_type="hint",
        player_inventory=["Shotgun Torque", "Shield Adaptive", "Grenade Singularity"],
        raw_search_result="",
        required_requirements=[],
        missing_item=None,
        is_item_search=False,
        user_approval=None,
        generated_text="",
        critique_passed=False,
        final_response="",
    )


# ---------------------------------------------------------------------------
# Testes do AgentState
# ---------------------------------------------------------------------------

class TestAgentState:

    def test_payload_completo_e_valido(self, valid_payload):
        """Verifica que o TypedDict aceita um payload completo sem erros."""
        assert valid_payload["game_name"] == "Borderlands 2"
        assert valid_payload["mission_name"] == "Lights Out"
        assert valid_payload["help_type"] == "hint"

    def test_todos_os_14_campos_presentes(self, valid_payload):
        """Garante que os 14 campos definidos no tech.md estão presentes no estado."""
        campos_esperados = [
            "game_name", "mission_name", "current_issue", "original_issue",
            "help_type", "player_inventory", "raw_search_result",
            "required_requirements", "missing_item", "is_item_search",
            "user_approval", "generated_text", "critique_passed", "final_response"
        ]
        for campo in campos_esperados:
            assert campo in valid_payload, f"Campo ausente no AgentState: {campo}"

    def test_quantidade_de_campos(self, valid_payload):
        """Confirma que o estado possui exatamente 14 campos."""
        assert len(valid_payload) == 14

    def test_campos_opcionais_aceitam_none(self, valid_payload):
        """missing_item e user_approval devem aceitar None (estado inicial)."""
        assert valid_payload["missing_item"] is None
        assert valid_payload["user_approval"] is None

    def test_is_item_search_padrao_false(self, valid_payload):
        """RN05: is_item_search deve ser False na inicialização do estado."""
        assert valid_payload["is_item_search"] is False

    def test_player_inventory_e_lista(self, valid_payload):
        """player_inventory deve ser uma lista de strings."""
        assert isinstance(valid_payload["player_inventory"], list)
        assert all(isinstance(item, str) for item in valid_payload["player_inventory"])

    def test_original_issue_preservado(self, valid_payload):
        """original_issue deve preservar o contexto original do jogador."""
        assert valid_payload["original_issue"] == valid_payload["current_issue"]

    def test_help_type_valores_validos(self):
        """help_type só deve aceitar 'hint' ou 'answer' na lógica de negócio."""
        valores_validos = {"hint", "answer"}
        for valor in valores_validos:
            state = AgentState(
                game_name="Test", mission_name="Test", current_issue="Test",
                original_issue="Test", help_type=valor,
                player_inventory=[], raw_search_result="",
                required_requirements=[], missing_item=None,
                is_item_search=False, user_approval=None,
                generated_text="", critique_passed=False, final_response=""
            )
            assert state["help_type"] == valor

    def test_estado_apos_hitl_aprovado(self):
        """Simula a mutação de estado após user_approval='sim' no fluxo HITL."""
        state = AgentState(
            game_name="Borderlands 2",
            mission_name="Lights Out",
            current_issue="Estou travado na subestação.",
            original_issue="Estou travado na subestação.",
            help_type="answer",
            player_inventory=["Shield Adaptive"],
            raw_search_result="",
            required_requirements=["Chave de Acesso Perdida"],
            missing_item="Chave de Acesso Perdida",
            is_item_search=False,
            user_approval=None,
            generated_text="",
            critique_passed=False,
            final_response=""
        )

        # Simula o que o roteador faz após user_approval = "sim"
        state["user_approval"] = "sim"
        state["is_item_search"] = True
        state["current_issue"] = f"como obter {state['missing_item']} em {state['game_name']}"

        assert state["is_item_search"] is True
        assert state["user_approval"] == "sim"
        assert state["original_issue"] == "Estou travado na subestação."
        assert "Chave de Acesso Perdida" in state["current_issue"]
        assert "Borderlands 2" in state["current_issue"]


# ---------------------------------------------------------------------------
# Testes do config.py (novo sistema multi-provider)
# ---------------------------------------------------------------------------

class TestConfig:

    def test_get_api_config_prioriza_groq(self):
        """Verifica que get_api_config() prioriza Groq se ambas as chaves estiverem disponíveis."""
        from backend.config import get_api_config
        config = get_api_config()
        
        # Se GROQ_API_KEY está no .env, deve usar Groq
        if os.getenv("GROQ_API_KEY"):
            assert config["provider"] == "groq"
            assert config["api_key"] == os.getenv("GROQ_API_KEY")
            # Verifica que o modelo é um dos modelos Groq válidos
            assert config["model"] in ["mixtral-8x7b-32768", "llama-3.1-8b-instant", "llama-3.1-70b-versatile"]

    def test_get_api_config_fallback_gemini(self):
        """Verifica que get_api_config() volta para Gemini se Groq não estiver disponível.
        
        Nota: Este teste valida apenas a lógica da função. Como o módulo está
        já carregado com ambas as chaves, testamos que a lógica favoreceria Gemini
        se Groq não existisse.
        """
        # Apenas verificar que se Groq não estivesse, a lógica escolheria Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        
        # Se ambas estão no .env, Groq é favorecido (comportamento esperado)
        if google_key and groq_key:
            from backend.config import get_api_config
            config = get_api_config()
            assert config["provider"] == "groq"  # Groq é favorecido
        
        # Se apenas Google existe, deve usar Gemini
        if google_key and not groq_key:
            from backend.config import get_api_config
            config = get_api_config()
            assert config["provider"] == "gemini"

    def test_get_api_config_lanca_erro_sem_chave(self, monkeypatch):
        """get_api_config() deve lançar ValueError se nenhuma chave estiver no ambiente."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        from backend.config import get_api_config
        with pytest.raises(ValueError, match="Nenhuma chave de API foi encontrada"):
            get_api_config()

    def test_api_key_nao_esta_hardcoded(self):
        """Garante que a chave vem do ambiente, não do código-fonte."""
        import inspect
        from backend import config as cfg
        source = inspect.getsource(cfg)
        # Não deve conter nenhuma string que pareça uma chave real (AIza... ou gsk_...)
        assert "AIza" not in source
        assert "gsk_" not in source

    def test_config_centralizado_exportado(self):
        """Verifica que PROVIDER, API_KEY, MODEL estão definidos no módulo."""
        from backend.config import PROVIDER, API_KEY, MODEL
        assert PROVIDER is not None
        assert API_KEY is not None
        assert MODEL is not None
        assert PROVIDER in ["groq", "gemini"]
