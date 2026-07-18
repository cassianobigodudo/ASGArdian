"""
Test script para validar a integração de pesquisa web no fetch_guide_node.
"""

import asyncio
import json
import logging
from backend.graph.nodes import fetch_guide_node
from backend.graph.state import AgentState

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

async def test_fetch_guide_web_search():
    """Testa fetch_guide_node com pesquisa web real."""
    
    print("\n" + "="*80)
    print("🧪 TESTE DE INTEGRAÇÃO: FETCH_GUIDE_NODE COM PESQUISA WEB")
    print("="*80)
    
    # Cria estado inicial
    initial_state: AgentState = {
        "game_name": "The Legend of Zelda: Breath of the Wild",
        "mission_name": "Tutorial Area - Great Plateau",
        "current_issue": "How to find the first Shrine on the Great Plateau",
        "player_inventory": ["Rusty Sword", "Wooden Shield", "Apple"],
        "help_type": "hint",
        "is_item_search": False,
        "missing_item": None,
        "user_approval": None,
        "raw_search_result": "",
        "required_requirements": [],
        "generated_text": "",
        "critique_passed": None,
        "final_response": "",
        "hitl_question": "",
    }
    
    print("\n📥 INPUT PARA FETCH_GUIDE_NODE:")
    print(f"   Game: {initial_state['game_name']}")
    print(f"   Mission: {initial_state['mission_name']}")
    print(f"   Issue: {initial_state['current_issue']}\n")
    
    try:
        # Executa fetch_guide_node
        print("🔍 Iniciando fetch_guide_node com pesquisa web...\n")
        result = fetch_guide_node(initial_state)
        
        raw_result = result["raw_search_result"]
        
        print("\n" + "="*80)
        print("✅ RESULTADO DO FETCH_GUIDE_NODE")
        print("="*80)
        
        # Verifica se há fontes
        if "---FONTES---" in raw_result:
            print("\n✅ FONTES ENCONTRADAS!")
            
            # Separa conteúdo e fontes
            content_part, sources_part = raw_result.split("---FONTES---", 1)
            
            print("\n📄 CONTEÚDO PRINCIPAL:")
            print(content_part[:500] + "...\n")
            
            print("\n📚 SEÇÃO DE FONTES:")
            print(sources_part[:300] + "...\n")
            
            # Valida se tem URLs
            if "http" in sources_part:
                print("✅ URLs encontradas nas fontes!")
                # Lista as URLs
                lines = sources_part.strip().split('\n')
                for line in lines:
                    if "http" in line or "🔗" in line:
                        print(f"   {line}")
        else:
            print("\n⚠️ Nenhuma seção de FONTES detectada")
            print("\n📄 CONTEÚDO RETORNADO:")
            print(raw_result[:500] + "...")
        
        print("\n" + "="*80)
        print(f"✅ TESTE CONCLUÍDO COM SUCESSO")
        print(f"   Tamanho total do raw_search_result: {len(raw_result)} caracteres")
        print("="*80 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(test_fetch_guide_web_search())
