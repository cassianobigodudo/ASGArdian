#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_debug_api.py - Teste DEBUG com API real
"""

import sys
import os
import io

# Fix encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import logging
from backend.graph.workflow import app
from backend.graph.state import AgentState
from backend.example_payload import payload_gta_v_hint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def show_state(state, title):
    """Exibe o estado do grafo."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print("game_name:", state.get("game_name"))
    print("mission_name:", state.get("mission_name"))
    print("help_type:", state.get("help_type"))
    print("raw_search_result:", str(state.get("raw_search_result", ""))[:80] + "...")
    print("required_requirements:", state.get("required_requirements"))
    print("missing_item:", state.get("missing_item"))
    print("is_item_search:", state.get("is_item_search"))
    print("user_approval:", state.get("user_approval"))
    print("generated_text:", str(state.get("generated_text", ""))[:80] + "...")
    print("critique_passed:", state.get("critique_passed"))
    print("final_response:", str(state.get("final_response", ""))[:80] + "...")
    print("=" * 80)

def main():
    """Executa teste debug."""
    print("\n" + "=" * 80)
    print("DEBUG: Teste Real com API Gemini")
    print("=" * 80)
    
    thread_id = "debug_001"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Estado inicial
    initial_state = AgentState(
        game_name=payload_gta_v_hint["game_name"],
        mission_name=payload_gta_v_hint["mission_name"],
        current_issue=payload_gta_v_hint["current_issue"],
        original_issue=payload_gta_v_hint["current_issue"],
        help_type=payload_gta_v_hint["help_type"],
        player_inventory=payload_gta_v_hint["player_inventory"],
        raw_search_result="",
        required_requirements=[],
        missing_item=None,
        is_item_search=False,
        user_approval=None,
        generated_text="",
        critique_passed=False,
        final_response="",
    )
    
    print("\nIniciando execucao...")
    print("Jogo: {}".format(initial_state['game_name']))
    print("Missao: {}".format(initial_state['mission_name']))
    
    try:
        # Primeira invocacao
        print("\n[Passo 1] Invocando grafo...")
        result = app.invoke(initial_state, config=config)
        show_state(result, "Estado apos Passo 1")
        
        # Verificar se pausou
        snapshot = app.get_state(config)
        print("Proximos nos:", snapshot.next)
        
        step = 2
        while snapshot.next and step < 10:
            print("\n[Passo {}] Retomando grafo...".format(step))
            if "fetch_guide_node" in snapshot.next:
                print("  -> Injetando user_approval='sim'")
                app.update_state(config, {"user_approval": "sim", "is_item_search": True})
            
            result = app.invoke(None, config=config)
            show_state(result, "Estado apos Passo {}".format(step))
            
            snapshot = app.get_state(config)
            print("Proximos nos:", snapshot.next)
            step += 1
        
        print("\nFLUXO CONCLUIDO!")
        print("Final Response:", result.get("final_response", "[VAZIO]")[:200])
        return True
        
    except Exception as e:
        print("\nERRO:", e)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
