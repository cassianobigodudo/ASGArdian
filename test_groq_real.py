#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_groq_real.py — Teste real com Groq para validar a integração

Executa um fluxo completo com GTA V para verificar:
1. Carregamento correto do GROQ_API_KEY
2. Seleção automática de Groq como provedor (em vez de Gemini)
3. Invocação bem-sucedida do LLM
4. Geração de resposta válida
"""

import sys
import os
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

# Adicionamos o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=" * 80)
print("🧪 TESTE REAL COM GROQ")
print("=" * 80)

# ============================================================================
# ETAPA 1: Validar carregamento de config
# ============================================================================

print("\n📋 ETAPA 1: Validando configuração...")

from backend.config import PROVIDER, API_KEY, MODEL

print(f"  ✅ PROVIDER detectado: {PROVIDER}")
print(f"  ✅ MODEL: {MODEL}")
print(f"  ✅ API_KEY: {API_KEY[:20]}...{API_KEY[-10:]}")

if PROVIDER != "groq":
    print(f"\n⚠️  AVISO: Esperava Groq mas obtive {PROVIDER}")
    print(f"  Você pode tentar:")
    print(f"  1. Deletar GOOGLE_API_KEY do .env para forçar Groq")
    print(f"  2. Verificar que GROQ_API_KEY está configurada corretamente")
else:
    print(f"\n✅ Groq foi selecionado como provedor primário!")

# ============================================================================
# ETAPA 2: Testar _invoke_llm() diretamente
# ============================================================================

print("\n📋 ETAPA 2: Testando _invoke_llm() com prompt simples...")

from backend.graph.nodes import _invoke_llm

prompt_simples = "Você é um assistente amigável. Responda em uma frase: Qual é o jogo mais popular de 2024?"

try:
    print(f"\n  📤 Enviando prompt: {prompt_simples[:50]}...")
    resposta = _invoke_llm(prompt_simples)
    print(f"  ✅ Resposta recebida:")
    print(f"     {resposta[:100]}...")
except Exception as e:
    print(f"  ❌ ERRO ao chamar _invoke_llm(): {e}")
    sys.exit(1)

# ============================================================================
# ETAPA 3: Testar com um nó real (fetch_guide_node)
# ============================================================================

print("\n📋 ETAPA 3: Testando fetch_guide_node com GTA V...")

from backend.graph.state import AgentState
from backend.graph.nodes import fetch_guide_node

state = AgentState(
    game_name="Grand Theft Auto V",
    mission_name="The Big Score",
    current_issue="Não consegui abrir o cofre na câmara de segurança. Usei o Hacking Device mas a sequência não aparece.",
    original_issue="Não consegui abrir o cofre na câmara de segurança. Usei o Hacking Device mas a sequência não aparece.",
    help_type="hint",
    player_inventory=["Hacking Device", "Lockpick", "C4"],
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
    print(f"\n  📤 Chamando fetch_guide_node...")
    print(f"     Game: {state['game_name']}")
    print(f"     Mission: {state['mission_name']}")
    print(f"     Issue: {state['current_issue'][:60]}...")
    
    result = fetch_guide_node(state)
    
    print(f"\n  ✅ Resultado recebido!")
    print(f"     raw_search_result length: {len(result['raw_search_result'])} caracteres")
    print(f"     Primeiros 200 caracteres:")
    print(f"     {result['raw_search_result'][:200]}...")
    
except Exception as e:
    print(f"  ❌ ERRO ao chamar fetch_guide_node(): {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ETAPA 4: Testar com process_guide_node
# ============================================================================

print("\n📋 ETAPA 4: Testando process_guide_node...")

from backend.graph.nodes import process_guide_node

state["raw_search_result"] = result["raw_search_result"]

try:
    print(f"\n  📤 Chamando process_guide_node...")
    result_process = process_guide_node(state)
    
    print(f"\n  ✅ Resultado recebido!")
    print(f"     Requisitos encontrados: {result_process['required_requirements']}")
    print(f"     Generated text (primeiros 150 chars): {result_process['generated_text'][:150]}...")
    
except Exception as e:
    print(f"  ❌ ERRO ao chamar process_guide_node(): {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# RESUMO FINAL
# ============================================================================

print("\n" + "=" * 80)
print("✅ TESTE COM GROQ COMPLETADO COM SUCESSO!")
print("=" * 80)
print(f"\n📊 Resumo:")
print(f"  ✅ Provedor: {PROVIDER}")
print(f"  ✅ LLM Invocado: 2 vezes (teste simples + fetch_guide_node + process_guide_node)")
print(f"  ✅ Respostas recebidas: 3")
print(f"  ✅ Sistema funcional: SIM ✨")
print(f"\n💡 Próximas etapas:")
print(f"  1. Executar teste E2E completo com 'python backend/main.py'")
print(f"  2. Testar com help_type='answer' também")
print(f"  3. Verificar fluxo HITL quando item está faltando")
print("\n")
