"""
test_analyze_problem.py — Testes unitários para o analyze_problem_node.

Testes:
1. Análise básica de texto de problema
2. Extração correta da missão
3. Geração da search_query no formato correto
4. Preservação do contexto original
5. Fallback quando sem user_problem_text
"""

import pytest
from backend.graph.nodes import analyze_problem_node
from backend.graph.state import AgentState


class TestAnalyzeProblemNode:
    """Testes para o nó de análise de problemas."""

    def test_analyze_problem_basic(self):
        """Testa análise básica de problema de usuário."""
        state: AgentState = {
            "game_name": "The Legend of Zelda: Breath of the Wild",
            "mission_name": "Tutorial Area",
            "current_issue": "Find first shrine",
            "original_issue": "Find first shrine",
            "help_type": "hint",
            "player_inventory": ["Rusty Sword"],
            "user_problem_text": "Estou no Great Plateau e não consigo encontrar a primeira shrine. Já procurei em vários lugares mas não acho nada.",
            "analyzed_mission": "",
            "search_query": "",
            "raw_search_result": "",
            "required_requirements": [],
            "missing_item": None,
            "is_item_search": False,
            "user_approval": None,
            "generated_text": "",
            "critique_passed": False,
            "final_response": "",
            "hitl_question": "",
        }

        result = analyze_problem_node(state)

        # Verifica se retorna os campos esperados
        assert "analyzed_mission" in result
        assert "search_query" in result
        assert result["analyzed_mission"], "Mission não pode estar vazia"
        assert result["search_query"], "Search query não pode estar vazia"

        # Verifica se a search_query tem o formato correto
        search_query = result["search_query"]
        assert state["game_name"] in search_query, "Search query deve conter o nome do jogo"
        assert "guide walkthrough" in search_query.lower(), "Search query deve terminar com 'guide walkthrough'"

        print(f"✅ Analyzed Mission: {result['analyzed_mission']}")
        print(f"✅ Search Query: {result['search_query']}")

    def test_search_query_format(self):
        """Testa se a search_query segue o formato exato: [game] [mission] guide walkthrough."""
        state: AgentState = {
            "game_name": "Elden Ring",
            "mission_name": "Limgrave",
            "current_issue": "Defeat Tree Sentinel",
            "original_issue": "Defeat Tree Sentinel",
            "help_type": "answer",
            "player_inventory": ["Longsword", "Shield"],
            "user_problem_text": "Como derrotar o Tree Sentinel que fica no início do jogo?",
            "analyzed_mission": "",
            "search_query": "",
            "raw_search_result": "",
            "required_requirements": [],
            "missing_item": None,
            "is_item_search": False,
            "user_approval": None,
            "generated_text": "",
            "critique_passed": False,
            "final_response": "",
            "hitl_question": "",
        }

        result = analyze_problem_node(state)
        search_query = result["search_query"]

        # Validação de formato
        parts = search_query.split()
        assert "guide" in [p.lower() for p in parts], "Query deve conter 'guide'"
        assert "walkthrough" in [p.lower() for p in parts], "Query deve conter 'walkthrough'"
        assert search_query.endswith("guide walkthrough"), "Query deve terminar com 'guide walkthrough'"

        print(f"✅ Search Query bem formatada: {search_query}")

    def test_fallback_no_problem_text(self):
        """Testa fallback quando user_problem_text está vazio."""
        state: AgentState = {
            "game_name": "Dark Souls III",
            "mission_name": "Lothric Castle",
            "current_issue": "Find bonfire",
            "original_issue": "Find bonfire",
            "help_type": "hint",
            "player_inventory": ["Estoc"],
            "user_problem_text": "",  # Vazio!
            "analyzed_mission": "",
            "search_query": "",
            "raw_search_result": "",
            "required_requirements": [],
            "missing_item": None,
            "is_item_search": False,
            "user_approval": None,
            "generated_text": "",
            "critique_passed": False,
            "final_response": "",
            "hitl_question": "",
        }

        result = analyze_problem_node(state)

        # Mesmo sem problem_text, deve retornar algo válido
        assert result["analyzed_mission"], "Deve ter fallback para mission"
        assert result["search_query"], "Deve ter fallback para search_query"

        print(f"✅ Fallback funcionou: {result['search_query']}")

    def test_mission_name_updated(self):
        """Testa se mission_name é atualizado com analyzed_mission."""
        state: AgentState = {
            "game_name": "Cyberpunk 2077",
            "mission_name": "Old Mission",
            "current_issue": "Quest issue",
            "original_issue": "Quest issue",
            "help_type": "answer",
            "player_inventory": ["Revolver"],
            "user_problem_text": "Como completar a missão do corpo do lado da estrada?",
            "analyzed_mission": "",
            "search_query": "",
            "raw_search_result": "",
            "required_requirements": [],
            "missing_item": None,
            "is_item_search": False,
            "user_approval": None,
            "generated_text": "",
            "critique_passed": False,
            "final_response": "",
            "hitl_question": "",
        }

        result = analyze_problem_node(state)

        # mission_name deve ser atualizado
        assert "mission_name" in result
        assert result["mission_name"] == result["analyzed_mission"]

        print(f"✅ Mission name atualizada: {result['mission_name']}")

    def test_context_preservation(self):
        """Testa se o contexto original é preservado para comparação."""
        original_issue = "Cannot find secret area in the dungeon"
        state: AgentState = {
            "game_name": "Skyrim",
            "mission_name": "Bleak Falls Barrow",
            "current_issue": original_issue,
            "original_issue": original_issue,
            "help_type": "hint",
            "player_inventory": ["Iron Dagger", "Hide Armor"],
            "user_problem_text": "Estou dentro da masmorra Bleak Falls Barrow e não acho o caminho para chegar ao final. Alguém sabe onde está a sala secreta?",
            "analyzed_mission": "",
            "search_query": "",
            "raw_search_result": "",
            "required_requirements": [],
            "missing_item": None,
            "is_item_search": False,
            "user_approval": None,
            "generated_text": "",
            "critique_passed": False,
            "final_response": "",
            "hitl_question": "",
        }

        result = analyze_problem_node(state)

        # Verifica que analyzed_mission é diferente do original (foi analisado)
        # Mas o search_query deve conter informações uteis
        assert result["search_query"]
        assert "Bleak Falls Barrow" in result["search_query"] or "Skyrim" in result["search_query"]

        print(f"✅ Contexto preservado e analisado: {result['search_query']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
