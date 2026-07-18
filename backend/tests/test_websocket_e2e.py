"""
Test script para validar o fluxo completo end-to-end via WebSocket.
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

async def test_websocket_e2e():
    """Testa o fluxo completo do agente via WebSocket."""
    
    print("\n" + "="*80)
    print("🧪 TESTE END-TO-END: AGENTE COM PESQUISA WEB VIA WEBSOCKET")
    print("="*80 + "\n")
    
    # Payload para o agente
    payload = {
        "game_name": "The Legend of Zelda: Breath of the Wild",
        "mission_name": "Tutorial Area - Great Plateau",
        "current_issue": "How to find the first Shrine on the Great Plateau",
        "player_inventory": ["Rusty Sword", "Wooden Shield", "Apple"],
        "help_type": "hint"
    }
    
    print("📥 PAYLOAD:")
    print(json.dumps(payload, indent=2))
    print()
    
    # Thread ID (você precisaria gerar um via /api/run-agent)
    thread_id = "test-e2e-001"
    ws_url = f"ws://localhost:8000/api/ws/{thread_id}"
    
    try:
        print(f"🔗 Conectando ao WebSocket: {ws_url}\n")
        async with websockets.connect(ws_url) as websocket:
            # Envia payload ao servidor
            print("📤 Enviando payload...")
            await websocket.send(json.dumps(payload))
            
            # Aguarda eventos
            print("⏳ Aguardando eventos...\n")
            
            event_count = 0
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60)
                    event = json.loads(message)
                    event_count += 1
                    
                    event_type = event.get("type", "unknown")
                    data = event.get("data", {})
                    
                    print(f"\n📨 EVENTO {event_count}: {event_type}")
                    print(f"   Status: {data.get('status', 'N/A')}")
                    
                    if event_type == "node_executed":
                        print(f"   Nó: {data.get('node_name', 'N/A')}")
                        if "raw_search_result" in data:
                            result = data["raw_search_result"]
                            has_sources = "---FONTES---" in result
                            print(f"   Resultado: {len(result)} chars, Fontes: {'✅ SIM' if has_sources else '❌ NÃO'}")
                    
                    elif event_type == "response_ready":
                        final_response = data.get("final_response", "")
                        print(f"   Resposta: {final_response[:100]}...")
                        if "---FONTES---" in data.get("raw_search_result", ""):
                            print(f"   ✅ FONTES ENCONTRADAS NA RESPOSTA FINAL!")
                        break
                    
                    elif event_type == "error":
                        print(f"   ❌ ERRO: {data.get('message', 'N/A')}")
                        break
                
                except asyncio.TimeoutError:
                    print("⏱️ Timeout aguardando evento (60s)")
                    break
        
        print("\n" + "="*80)
        print(f"✅ TESTE CONCLUÍDO - {event_count} eventos recebidos")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket_e2e())
