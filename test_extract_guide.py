#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste: Extrair conteúdo da IGN (Crystal Maze)"""

import requests
from bs4 import BeautifulSoup

url = "https://www.ign.com/wikis/gta-5/Crystal_Maze"

print(f"[+] Tentando extrair conteudo de: {url}\n")

try:
    # Headers completos
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Referer': 'https://www.ign.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    print("[*] Fazendo requisição HTTP para IGN...")
    response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
    
    print(f"[+] Status: {response.status_code}")
    print(f"[+] URL final: {response.url}")
    print(f"[+] Content-Type: {response.headers.get('content-type', 'N/A')}")
    print(f"[+] Tamanho: {len(response.content)} bytes\n")
    
    if response.status_code != 200:
        print(f"[-] Erro HTTP {response.status_code}")
        exit(1)
    
    # Parse HTML
    print("[*] Parseando HTML...")
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove scripts e styles
    print("[*] Removendo scripts e styles...")
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Extrai texto
    print("[*] Extraindo texto...")
    text = soup.get_text(separator=' ', strip=True)
    
    # Informações
    full_text = text
    preview = text[:2500]
    
    print(f"[+] Conteudo extraido: {len(full_text)} caracteres\n")
    print("="*80)
    print("CONTEUDO (primeiros 2500 caracteres):")
    print("="*80)
    print(preview)
    print("\n" + "="*80)
    
    # Análise
    print("\n[*] Análise:")
    print(f"[+] Total de conteúdo: {len(full_text)} caracteres")
    print(f"[+] Contém 'Crystal Maze': {'Crystal Maze' in full_text}")
    print(f"[+] Contém 'guide': {'guide' in full_text.lower()}")
    print(f"[+] Contém 'step': {'step' in full_text.lower()}")
    print(f"[+] Contém 'mission': {'mission' in full_text.lower()}")
    
    if len(full_text) > 500:
        print(f"\n[SUCCESS] Conseguiu extrair conteúdo real do site IGN!")
    
except requests.exceptions.ConnectionError as e:
    print(f"[-] Erro de conexão: {e}")
except requests.exceptions.Timeout as e:
    print(f"[-] Timeout: {e}")
except Exception as e:
    print(f"[-] Erro: {type(e).__name__}: {e}")



