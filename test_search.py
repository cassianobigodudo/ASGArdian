#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste da busca com WHITELIST relaxada - 100 resultados"""

from duckduckgo_search import DDGS

query = "Grand Theft Auto V Crystal Maze guide walkthrough"
print(f"\nBuscando: {query}\n")

# WHITELIST RELAXADA - mais permissiva
GOOD_DOMAINS = [
    'ign.com', 'gamefaqs.com', 'fandom.com', 'wiki.',
    'reddit.com', 'youtube.com', 'twitch.tv', 'polygon.com',
    'gamerguides.com', '.org', '.edu',
    'pinterest.',  # Às vezes tem dicas lá
    'twitter.com',  # Comunidade pode ter tips
    'discord.',  # Servidores de comunidade
    'steam',  # Community guides no Steam
    'guides.com',  # Sites de guias genéricos
]

ddgs = DDGS()
search_results = list(ddgs.text(query, max_results=100))

print(f"Encontrados {len(search_results)} resultados BRUTOS:\n")

for i, result in enumerate(search_results, 1):
    link = result.get('href', '')
    title = result.get('title', '')
    print(f"{i}. {title[:60]}")
    print(f"   {link}\n")

print("\n" + "="*70)
print("Filtrando por WHITELIST...\n")

good_count = 0
for result in search_results:
    link = result.get('href', '').lower()
    title = result.get('title', '')
    
    is_good = any(domain in link for domain in GOOD_DOMAINS)
    
    if is_good:
        good_count += 1
        print(f"{good_count}. {title[:60]}")
        print(f"   {link}\n")
        if good_count >= 5:
            break

print(f"\nTotal aceito pela whitelist: {good_count}")








