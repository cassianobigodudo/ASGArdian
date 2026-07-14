#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_groq_quick.py — Teste rápido com Groq (versão simplificada)
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=" * 60)
print("🧪 TESTE RÁPIDO COM GROQ")
print("=" * 60)

# ETAPA 1: Config
print("\n1️⃣ Carregando configuração...")
from backend.config import PROVIDER, API_KEY, MODEL
print(f"   ✅ PROVIDER: {PROVIDER}")
print(f"   ✅ MODEL: {MODEL}")

if PROVIDER != "groq":
    print(f"   ⚠️  AVISO: Esperava Groq mas obtive {PROVIDER}")
    sys.exit(1)

# ETAPA 2: Teste simples
print("\n2️⃣ Invocando Groq com prompt simples...")
from backend.graph.nodes import _invoke_llm

try:
    prompt = "Você é amigável. Em uma frase: qual é o melhor jogo?"
    print(f"   📤 Enviando prompt...")
    resposta = _invoke_llm(prompt)
    print(f"   ✅ Resposta: {resposta[:80]}...")
except Exception as e:
    print(f"   ❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ETAPA 3: Teste com nó real
print("\n3️⃣ Testando fetch_guide_node...")
from backend.graph.state import AgentState
from backend.graph.nodes import fetch_guide_node

state = AgentState(
    game_name="GTA V",
    mission_name="The Big Score",
    current_issue="Não consigo abrir o cofre.",
    original_issue="Não consigo abrir o cofre.",
    help_type="hint",
    player_inventory=["Hacking Device"],
    raw_search_result="",
    required_requirements=[],
    missing_item=None,
    is_item_search=False,
    user_approval=None,
    generated_text="",
    critique_passed=False,
    final_response="",
)

try:
    print(f"   📤 Chamando fetch_guide_node...")
    result = fetch_guide_node(state)
    print(f"   ✅ Resultado: {len(result['raw_search_result'])} caracteres recebidos")
    print(f"   Amostra: {result['raw_search_result'][:100]}...")
except Exception as e:
    print(f"   ❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TESTE COM GROQ PASSOU!")
print("=" * 60)
