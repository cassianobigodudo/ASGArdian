# -*- coding: utf-8 -*-
"""
test_main.py -- Testes unitarios do executor principal (main.py).

Cobertura:
- validate_payload: campos ausentes, tipos invalidos, help_type invalido
- build_initial_state: campos inicializados corretamente
- _is_paused_for_hitl: cenarios de pausa e sem pausa
- run_agent: fluxo sem missing (mock), fluxo HITL com "nao", fluxo HITL com "sim"
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.main import (
    validate_payload,
    build_initial_state,
    _is_paused_for_hitl,
    run_agent,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def valid_payload(**overrides):
    base = {
        "game_name": "Borderlands 2",
        "mission_name": "Lights Out",
        "current_issue": "Nao consigo restaurar a energia.",
        "help_type": "hint",
        "player_inventory": ["Shotgun Torque"],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Testes: validate_payload
# ---------------------------------------------------------------------------

class TestValidatePayload:

    def test_payload_valido_nao_lanca_excecao(self):
        """Payload completo e valido nao deve levantar excecao."""
        validate_payload(valid_payload())  # nao deve lancar

    def test_campo_ausente_lanca_value_error(self):
        """Payload sem campo obrigatorio deve lancar ValueError."""
        payload = valid_payload()
        del payload["game_name"]
        with pytest.raises(ValueError, match="game_name"):
            validate_payload(payload)

    def test_todos_campos_obrigatorios_validados(self):
        """Cada um dos 5 campos obrigatorios deve ser validado individualmente."""
        campos = ["game_name", "mission_name", "current_issue", "help_type", "player_inventory"]
        for campo in campos:
            payload = valid_payload()
            del payload[campo]
            with pytest.raises(ValueError, match=campo):
                validate_payload(payload)

    def test_campo_none_lanca_value_error(self):
        """Campo com valor None deve lancar ValueError."""
        with pytest.raises(ValueError, match="game_name"):
            validate_payload(valid_payload(game_name=None))

    def test_game_name_vazio_lanca_value_error(self):
        """game_name vazio (string em branco) deve lancar ValueError."""
        with pytest.raises(ValueError, match="game_name"):
            validate_payload(valid_payload(game_name="   "))

    def test_help_type_invalido_lanca_value_error(self):
        """help_type fora de 'hint'/'answer' deve lancar ValueError."""
        with pytest.raises(ValueError, match="help_type"):
            validate_payload(valid_payload(help_type="spoiler"))

    def test_help_type_hint_valido(self):
        """help_type='hint' e valido."""
        validate_payload(valid_payload(help_type="hint"))

    def test_help_type_answer_valido(self):
        """help_type='answer' e valido."""
        validate_payload(valid_payload(help_type="answer"))

    def test_player_inventory_nao_lista_lanca_value_error(self):
        """player_inventory como string deve lancar ValueError."""
        with pytest.raises(ValueError, match="player_inventory"):
            validate_payload(valid_payload(player_inventory="Shotgun"))

    def test_player_inventory_lista_vazia_valida(self):
        """player_inventory como lista vazia e valido (jogador sem itens)."""
        validate_payload(valid_payload(player_inventory=[]))


# ---------------------------------------------------------------------------
# Testes: build_initial_state
# ---------------------------------------------------------------------------

class TestBuildInitialState:

    def test_campos_do_payload_transferidos(self):
        """Os 5 campos do payload devem estar no estado inicial."""
        state = build_initial_state(valid_payload())
        assert state["game_name"] == "Borderlands 2"
        assert state["mission_name"] == "Lights Out"
        assert state["help_type"] == "hint"

    def test_original_issue_igual_ao_current_issue(self):
        """original_issue deve ser identico ao current_issue na inicializacao."""
        state = build_initial_state(valid_payload())
        assert state["original_issue"] == state["current_issue"]

    def test_is_item_search_inicializa_como_false(self):
        """RN05: is_item_search deve comecar como False."""
        state = build_initial_state(valid_payload())
        assert state["is_item_search"] is False

    def test_user_approval_inicializa_como_none(self):
        """user_approval deve comecar como None (aguardando HITL)."""
        state = build_initial_state(valid_payload())
        assert state["user_approval"] is None

    def test_missing_item_inicializa_como_none(self):
        """missing_item deve comecar como None."""
        state = build_initial_state(valid_payload())
        assert state["missing_item"] is None

    def test_campos_intermediarios_inicializados_vazios(self):
        """Campos intermediarios devem comecar com valores padrao seguros."""
        state = build_initial_state(valid_payload())
        assert state["raw_search_result"] == ""
        assert state["required_requirements"] == []
        assert state["generated_text"] == ""
        assert state["final_response"] == ""
        assert state["critique_passed"] is False


# ---------------------------------------------------------------------------
# Testes: _is_paused_for_hitl
# ---------------------------------------------------------------------------

class TestIsPausedForHitl:

    def _make_snapshot(self, next_nodes, missing_item, user_approval):
        snapshot = MagicMock()
        snapshot.next = next_nodes
        snapshot.values = {
            "missing_item": missing_item,
            "user_approval": user_approval,
        }
        return snapshot

    def test_pausado_quando_fetch_next_e_missing_sem_approval(self):
        """Deve retornar True quando proximo no e fetch e ha missing sem approval."""
        snapshot = self._make_snapshot(
            next_nodes=["fetch_guide_node"],
            missing_item="Chave de Acesso",
            user_approval=None,
        )
        assert _is_paused_for_hitl(snapshot) is True

    def test_nao_pausado_sem_missing_item(self):
        """Sem missing_item nao deve ser considerado pausado."""
        snapshot = self._make_snapshot(
            next_nodes=["fetch_guide_node"],
            missing_item=None,
            user_approval=None,
        )
        assert _is_paused_for_hitl(snapshot) is False

    def test_nao_pausado_quando_approval_ja_definido(self):
        """Com user_approval ja definido nao deve ser pausado."""
        snapshot = self._make_snapshot(
            next_nodes=["fetch_guide_node"],
            missing_item="Chave",
            user_approval="sim",
        )
        assert _is_paused_for_hitl(snapshot) is False

    def test_nao_pausado_quando_proximo_nao_e_fetch(self):
        """Pausado em outro no (nao fetch) nao e HITL."""
        snapshot = self._make_snapshot(
            next_nodes=["generate_help_node"],
            missing_item="Chave",
            user_approval=None,
        )
        assert _is_paused_for_hitl(snapshot) is False

    def test_nao_pausado_sem_proximo_no(self):
        """Sem proximo no (grafo terminou) nao e pausado."""
        snapshot = self._make_snapshot(
            next_nodes=[],
            missing_item="Chave",
            user_approval=None,
        )
        assert _is_paused_for_hitl(snapshot) is False

    def test_nao_pausado_com_snapshot_none(self):
        """Snapshot None nao deve lancar excecao."""
        assert _is_paused_for_hitl(None) is False


# ---------------------------------------------------------------------------
# Testes: run_agent (com grafo mockado)
# ---------------------------------------------------------------------------

class TestRunAgent:

    def test_validate_payload_chamado_antes_do_grafo(self):
        """Payload invalido deve falhar antes de qualquer chamada ao grafo."""
        with pytest.raises(ValueError, match="help_type"):
            run_agent(valid_payload(help_type="invalido"))

    @patch("backend.main.app")
    def test_fluxo_simples_sem_hitl_retorna_final_response(self, mock_app):
        """Fluxo sem missing_item deve retornar final_response diretamente."""
        # Simula estado final do grafo
        mock_snapshot = MagicMock()
        mock_snapshot.next = []  # grafo terminou
        mock_snapshot.values = {
            "missing_item": None,
            "user_approval": None,
            "final_response": "Va para a esquerda e use a alavanca.",
            "generated_text": "Va para a esquerda e use a alavanca.",
            "game_name": "Borderlands 2",
        }

        mock_app.invoke.return_value = mock_snapshot.values
        mock_app.get_state.return_value = mock_snapshot

        result = run_agent(valid_payload())

        assert result == "Va para a esquerda e use a alavanca."
        mock_app.invoke.assert_called_once()

    @patch("backend.main.app")
    @patch("builtins.input", return_value="nao")
    def test_hitl_com_nao_retorna_mensagem_de_bloqueio(self, mock_input, mock_app):
        """user_approval=nao deve retornar mensagem de bloqueio sem continuar."""
        # Estado apos primeira execucao: grafo pausado com missing_item
        mock_snapshot_paused = MagicMock()
        mock_snapshot_paused.next = ["fetch_guide_node"]
        mock_snapshot_paused.values = {
            "missing_item": "Chave de Acesso",
            "user_approval": None,
            "final_response": "",
            "generated_text": "",
            "game_name": "Borderlands 2",
        }

        mock_app.invoke.return_value = {}
        mock_app.get_state.return_value = mock_snapshot_paused

        result = run_agent(valid_payload())

        assert "bloqueado" in result.lower()
        assert "Chave de Acesso" in result
        mock_input.assert_called_once()

    @patch("backend.main.app")
    @patch("builtins.input", return_value="sim")
    def test_hitl_com_sim_atualiza_estado_e_retoma(self, mock_input, mock_app):
        """user_approval=sim deve atualizar estado, retomar e retornar final_response."""
        # Primeiro get_state: pausado
        mock_snapshot_paused = MagicMock()
        mock_snapshot_paused.next = ["fetch_guide_node"]
        mock_snapshot_paused.values = {
            "missing_item": "Chave de Acesso",
            "user_approval": None,
            "final_response": "",
            "generated_text": "",
            "game_name": "Borderlands 2",
        }

        # Segundo get_state: grafo terminou apos retomada
        mock_snapshot_done = MagicMock()
        mock_snapshot_done.next = []
        mock_snapshot_done.values = {
            "missing_item": "Chave de Acesso",
            "user_approval": "sim",
            "final_response": "A Chave esta no cofre da sala leste.",
            "generated_text": "A Chave esta no cofre da sala leste.",
            "game_name": "Borderlands 2",
        }

        mock_app.invoke.side_effect = [{}, {}]
        mock_app.get_state.side_effect = [
            mock_snapshot_paused,
            mock_snapshot_done,
        ]

        result = run_agent(valid_payload())

        assert result == "A Chave esta no cofre da sala leste."
        mock_app.update_state.assert_called_once()
        # Verifica que o estado foi atualizado com is_item_search=True
        update_call = mock_app.update_state.call_args[0][1]
        assert update_call["user_approval"] == "sim"
        assert update_call["is_item_search"] is True
        assert "Chave de Acesso" in update_call["current_issue"]
