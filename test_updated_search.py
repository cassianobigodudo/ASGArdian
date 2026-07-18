#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste: Função _search_web atualizada com extração inteligente"""

import sys
sys.path.insert(0, '/home/user/ASGArdian')

from backend.graph.nodes import _search_web

# Teste com query real
query = "Grand Theft Auto V Crystal Maze guide walkthrough"

print(f"\n{'='*80}")
print(f"TESTE: _search_web com extração inteligente")
print(f"Query: {query}")
print(f"{'='*80}\n")

results = _search_web(query, num_results=3)

print(f"\n{'='*80}")
print(f"RESULTADOS: {len(results)} encontrados")
print(f"{'='*80}\n")

for i, result in enumerate(results, 1):
    print(f"\n[{i}] {result['title']}")
    print(f"    Link: {result['link']}")
    print(f"    Snippet: {result['snippet'][:100]}...")
    print(f"    Conteúdo (chars): {len(result['content'])}")
    print(f"    Conteúdo preview:")
    print(f"    {result['content'][:500]}...")
    print()
