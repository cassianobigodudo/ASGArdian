#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Testar se DuckDuckGo ignora palavras-chave específicas em diferentes jogos"""

from duckduckgo_search import DDGS

test_cases = [
    # (jogo_completo, missao, jogo_apenas)
    ("Red Dead Redemption 2 Chapter 3", "Red Dead Redemption 2"),
    ("Hollow Knight Kingdom's Edge", "Hollow Knight"),
    ("Grand Theft Auto V Crystal Maze", "Grand Theft Auto V"),
]

ddgs = DDGS()

for full_query, just_game in test_cases:
    print(f"\n{'='*80}")
    print(f"Jogo: {full_query}")
    print(f"{'='*80}\n")
    
    # Testa query completa (jogo + missão)
    print(f"[A] Query completa: {full_query}")
    try:
        results_full = list(ddgs.text(f"{full_query} guide", max_results=5))
        print(f"    Resultados: {len(results_full)}")
        for i, r in enumerate(results_full, 1):
            print(f"    {i}. {r.get('title', '')[:60]}")
    except Exception as e:
        print(f"    ERRO: {e}")
    
    # Testa query apenas com o jogo
    print(f"\n[B] Query apenas jogo: {just_game}")
    try:
        results_game = list(ddgs.text(f"{just_game} guide", max_results=5))
        print(f"    Resultados: {len(results_game)}")
        for i, r in enumerate(results_game, 1):
            print(f"    {i}. {r.get('title', '')[:60]}")
    except Exception as e:
        print(f"    ERRO: {e}")
    
    # Compara
    print(f"\n[RESULTADO]")
    if len(results_full) == len(results_game):
        # Verifica se são os MESMOS resultados
        titles_full = [r.get('title', '') for r in results_full]
        titles_game = [r.get('title', '') for r in results_game]
        
        if titles_full == titles_game:
            print(f"  PROBLEMA CONFIRMADO: DuckDuckGo retorna os MESMOS resultados!")
            print(f"  A missão '{full_query.split()[-1]}' foi IGNORADA")
        else:
            print(f"  Resultados diferentes mas mesmo tamanho")
    else:
        print(f"  Tamanhos diferentes ({len(results_full)} vs {len(results_game)})")
