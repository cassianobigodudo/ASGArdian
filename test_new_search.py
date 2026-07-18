#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste do novo _search_web com filtro relaxado"""

from backend.graph.nodes import _search_web

print("\n" + "="*80)
print("Testando novo _search_web")
print("="*80)

results = _search_web('Borderlands 2 guide', num_results=5)

print(f"\n{'='*80}")
print(f"Retornou {len(results)} resultados:")
print(f"{'='*80}\n")

for i, r in enumerate(results, 1):
    print(f"{i}. {r['title'][:70]}")
    print(f"   {r['link']}")
    print()
