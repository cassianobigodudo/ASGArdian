#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extração: O conteúdo REAL do guia da IGN"""

import requests
from bs4 import BeautifulSoup

url = "https://www.ign.com/wikis/gta-5/Crystal_Maze"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

r = requests.get(url, timeout=10, headers=headers)
soup = BeautifulSoup(r.content, 'html.parser')

print("="*80)
print("EXTRAÇÃO: Conteúdo Real do Guia IGN")
print("="*80)

# Estratégia 1: Extrai o div.content
content_div = soup.find('div', {'class': 'content'})
if content_div:
    print("\n✓ ENCONTRADO: <div class='content'>")
    
    # Remove scripts e styles
    for script in content_div(['script', 'style', 'nav']):
        script.decompose()
    
    text = content_div.get_text(separator='\n', strip=True)
    print(f"\nTamanho: {len(text)} caracteres")
    print("\n" + "="*80)
    print("CONTEÚDO EXTRAÍDO:")
    print("="*80)
    print(text[:3000])  # Primeiros 3000 chars
    print("\n... (truncado)")
else:
    print("\n✗ NÃO ENCONTRADO: <div class='content'>")

# Estratégia 2: Procura por seções de passos
print("\n\n" + "="*80)
print("ANÁLISE: Estrutura de Passos")
print("="*80)

headings = soup.find_all(['h2', 'h3'])
print(f"\nEncontrado {len(headings)} headings\n")

for i, h in enumerate(headings[:15], 1):
    text = h.get_text(strip=True)
    # Procura pelo próximo parágrafo
    next_p = h.find_next('p')
    if next_p:
        p_text = next_p.get_text(strip=True)[:100]
        print(f"{i:2d}. {text:40s} -> {p_text}...")
    else:
        print(f"{i:2d}. {text}")
