#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste para verificar se DuckDuckGo está recebendo a query completa"""

from duckduckgo_search import DDGS

queries = [
    "Grand Theft Auto V",
    "Grand Theft Auto V Crystal Maze",
    "Grand Theft Auto V Crystal Maze guide",
    "Grand Theft Auto V Crystal Maze guide walkthrough",
]

ddgs = DDGS()

for query in queries:
    print(f"\n{'='*70}")
    print(f"Query enviada: {query}")
    print(f"Query length: {len(query)}")
    print(f"{'='*70}\n")
    
    try:
        results = list(ddgs.text(query, max_results=5))
        print(f"Resultados retornados: {len(results)}\n")
        
        for i, result in enumerate(results, 1):
            title = result.get('title', '')[:70]
            url = result.get('href', '')
            print(f"{i}. {title}")
            print(f"   {url}\n")
    except Exception as e:
        print(f"ERRO: {e}\n")

print("\nConclusao:")
print("Se a query completa retorna 0 e a query curta retorna resultados,")
print("entao DuckDuckGo esta ignorando palavras-chave da query.")
