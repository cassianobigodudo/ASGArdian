#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug: Por que DuckDuckGo não retorna resultados?"""

from ddgs import DDGS

queries = [
    'gta 5',
    'crystal maze',
    'gta guide',
    'game walkthrough',
    'how to play',
]

ddgs = DDGS()

print("="*80)
print("DEBUG: DuckDuckGo Query Testing")
print("="*80)

for q in queries:
    try:
        print(f"\nQuery: {q}")
        results = list(ddgs.text(q, max_results=5))
        print(f"  ✓ Resultados: {len(results)}")
        if results:
            for i, r in enumerate(results[:2], 1):
                print(f"    {i}. {r.get('title', '')[:60]}")
                print(f"       {r.get('href', '')[:60]}")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
