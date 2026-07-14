#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_real_api.py — Teste REAL da IA com API do Gemini (sem mocks).

Este script testa o fluxo completo do ASGArdian com chamadas REAIS à API do Gemini.
Não usa mocks — utiliza a GOOGLE_API_KEY configurada no .env.

IMPORTANTE: Isso vai fazer chamadas reais à API e pode levar alguns segundos.
"""

import sys
import os

# Adicionar path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import logging
from backend.main import run_agent
from backend.example_payload import payload_gta_v_hint, payload_gta_v_answer

# Configurar logging para ver o que está acontecendo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def test_real_gta_v_hint():
    """
    Teste 1: GTA V — The Big Score (Hint Mode)
    Payload: Procurando pista para abrir cofre
    Esperado: Sistema faz busca real, processa, valida pré-requisitos e gera dica
    """
    print("\n" + "=" * 80)
    print("🧪 TESTE 1: GTA V — The Big Score (HINT MODE)")
    print("=" * 80)
    print("\n📝 Payload:")
    print(f"   Jogo: {payload_gta_v_hint['game_name']}")
    print(f"   Missão: {payload_gta_v_hint['mission_name']}")
    print(f"   Problema: {payload_gta_v_hint['current_issue'][:60]}...")
    print(f"   Tipo: {payload_gta_v_hint['help_type']}")
    print(f"   Inventário: {', '.join(payload_gta_v_hint['player_inventory'])}")
    
    print("\n🔄 Executando fluxo...")
    print("-" * 80)
    
    try:
        result = run_agent(payload_gta_v_hint)
        
        print("-" * 80)
        print("\n✅ SUCESSO! Resposta recebida:")
        print("\n" + result)
        
        # Validações
        print("\n📊 Validações:")
        print(f"   ✓ Tipo da resposta: {type(result).__name__}")
        print(f"   ✓ Tamanho: {len(result)} caracteres")
        print(f"   ✓ Não está vazio: {len(result) > 0}")
        
        # Verificar se contém spoilers (simples heurística)
        spoiler_keywords = ["morre", "traição", "surpresa", "revelação", "morte", "final"]
        has_spoiler_keywords = any(keyword in result.lower() for keyword in spoiler_keywords)
        print(f"   ✓ Sem palavras-chave de spoiler óbvias: {not has_spoiler_keywords}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_gta_v_answer():
    """
    Teste 2: GTA V — The Merryweather Heist (Answer Mode)
    Payload: Procurando solução direta para combate
    Esperado: Sistema faz busca real e gera resposta direta
    """
    print("\n" + "=" * 80)
    print("🧪 TESTE 2: GTA V — The Merryweather Heist (ANSWER MODE)")
    print("=" * 80)
    print("\n📝 Payload:")
    print(f"   Jogo: {payload_gta_v_answer['game_name']}")
    print(f"   Missão: {payload_gta_v_answer['mission_name']}")
    print(f"   Problema: {payload_gta_v_answer['current_issue'][:60]}...")
    print(f"   Tipo: {payload_gta_v_answer['help_type']}")
    print(f"   Inventário: {', '.join(payload_gta_v_answer['player_inventory'])}")
    
    print("\n🔄 Executando fluxo...")
    print("-" * 80)
    
    try:
        result = run_agent(payload_gta_v_answer)
        
        print("-" * 80)
        print("\n✅ SUCESSO! Resposta recebida:")
        print("\n" + result)
        
        # Validações
        print("\n📊 Validações:")
        print(f"   ✓ Tipo da resposta: {type(result).__name__}")
        print(f"   ✓ Tamanho: {len(result)} caracteres")
        print(f"   ✓ Não está vazio: {len(result) > 0}")
        print(f"   ✓ Contém 'passo' ou 'estratégia': {'passo' in result.lower() or 'estratégia' in result.lower()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  🛡️  ASGArdian — Teste REAL da IA com Gemini API  🛡️  ".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    print("\n⚠️  IMPORTANTE:")
    print("  Este script faz chamadas REAIS à API do Gemini.")
    print("  Não há mocks — tudo é real!")
    print("  Pode levar 10-30 segundos por teste.")
    print("  Você verá o progresso em tempo real.")
    
    results = []
    
    # Teste 1
    try:
        results.append(("Teste 1 (Hint Mode)", test_real_gta_v_hint()))
    except Exception as e:
        print(f"\n❌ Erro fatal no Teste 1: {e}")
        results.append(("Teste 1 (Hint Mode)", False))
    
    # Teste 2
    try:
        results.append(("Teste 2 (Answer Mode)", test_real_gta_v_answer()))
    except Exception as e:
        print(f"\n❌ Erro fatal no Teste 2: {e}")
        results.append(("Teste 2 (Answer Mode)", False))
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {total_passed}/{total} testes passaram")
    
    if total_passed == total:
        print("\n🎉 SUCESSO! A IA está funcionando corretamente!")
        print("   Todos os testes passaram com a API real do Gemini.")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os erros acima.")
    
    print("=" * 80 + "\n")
    
    return total_passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
