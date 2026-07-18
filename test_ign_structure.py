#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Análise: O que IGN realmente retorna?"""

import requests
from bs4 import BeautifulSoup

url = "https://www.ign.com/wikis/gta-5/Crystal_Maze"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

r = requests.get(url, timeout=10, headers=headers)
soup = BeautifulSoup(r.content, 'html.parser')

print("="*80)
print("ANÁLISE: Estrutura HTML da IGN")
print("="*80)

# Procura por elementos típicos de conteúdo
elements_to_check = [
    ('article', {}),
    ('main', {}),
    ('div', {'class': 'content'}),
    ('div', {'class': 'wiki-content'}),
    ('div', {'role': 'main'}),
]

print("\n1. ELEMENTOS DE CONTEÚDO:")
for tag, attrs in elements_to_check:
    elem = soup.find(tag, attrs)
    if elem:
        text = elem.get_text(separator=' ', strip=True)[:300]
        print(f"\n✓ <{tag} {attrs}>: {len(text)} chars")
        print(f"  Preview: {text[:200]}...")
    else:
        print(f"\n✗ <{tag} {attrs}>: não encontrado")

# Procura por paragrafos
print("\n\n2. PARAGRAFOS (primeiro 5):")
paragraphs = soup.find_all('p', limit=5)
for i, p in enumerate(paragraphs, 1):
    text = p.get_text(strip=True)[:100]
    if text:
        print(f"  {i}. {text}")

# Procura por lists
print("\n\n3. LISTAS (primeiro 3):")
lists = soup.find_all('li', limit=15)
for i, li in enumerate(lists[:3], 1):
    text = li.get_text(strip=True)[:100]
    if text:
        print(f"  {i}. {text}")

# Procura por headings
print("\n\n4. HEADINGS:")
headings = soup.find_all(['h1', 'h2', 'h3'], limit=10)
for i, h in enumerate(headings, 1):
    text = h.get_text(strip=True)
    if text and text != 'GTA 5 Guide':
        print(f"  {i}. {text}")

# Analisa tamanhos
print("\n\n5. ANÁLISE DE TAMANHO:")
print(f"  HTML total: {len(r.content)} bytes")
print(f"  Texto extraído: {len(soup.get_text())} chars")

# Procura por conteúdo real (keywords)
full_text = soup.get_text().lower()
keywords = ['step', 'instruction', 'guide', 'walkthrough', 'location', 'objective', 'mission']
print(f"\n6. KEYWORDS ENCONTRADAS:")
for kw in keywords:
    count = full_text.count(kw)
    if count > 0:
        print(f"  '{kw}': {count}x")
    else:
        print(f"  '{kw}': ✗")

print("\n" + "="*80)
print("CONCLUSÃO: IGN retorna informação útil?")
print("="*80)

if len(soup.get_text()) > 2000 and 'step' in full_text:
    print("✓ SIM - Contém conteúdo real")
elif len(soup.get_text()) > 500:
    print("? PARCIAL - Contém texto mas pode ser navegação")
else:
    print("✗ NÃO - Apenas navegação/estrutura da página")
