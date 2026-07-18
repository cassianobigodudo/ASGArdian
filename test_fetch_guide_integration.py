#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste: fetch_guide_node integrado com guides_loader"""

import sys
from backend.graph.state import AgentState
from backend.graph.nodes import fetch_guide_node

# Mock state
state = AgentState(
    game_name="GTA 5",
    mission_name="Crystal Maze",
    current_issue="Como completar Crystal Maze em GTA 5",
    original_issue="Como completar Crystal Maze em GTA 5",
    help_type="answer",
    player_inventory=["M1911 Pistol", "Combat Knife"],
    raw_search_result="",
    required_requirements=[],
    missing_item=None,
    is_item_search=False,
    user_approval=None,
    generated_text="",
    critique_passed=False,
    final_response="",
)

print("="*80)
print("TESTE: fetch_guide_node com guides_loader")
print("="*80)

try:
    result = fetch_guide_node(state)
    
    print("\n" + "="*80)
    print("RESULTADO:")
    print("="*80)
    print(f"\nraw_search_result ({len(result['raw_search_result'])} chars):")
    print(result['raw_search_result'][:800])
    print("\n... (truncado)")
    
except Exception as e:
    print(f"\n✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
