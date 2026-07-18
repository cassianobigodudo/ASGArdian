#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste WebSocket para diagnosticar o problema com Groq
"""

import asyncio
import json
import websockets
import sys

async def test_websocket():
    thread_id = "test-debug-" + str(time.time())
    ws_url = f"ws://localhost:8000/api/ws/{thread_id}"
    
    print(f"🔗 Conectando ao WebSocket: {ws_url}")
    
    async with websockets.connect(ws_url) as ws:
        print("✅ Conectado!")
        
        # Envia payload
        payload = {
            "payload": {
                "game_name": "GTA V",
                "mission_name": "The Big Score",
                "current_issue": "Como abrir o cofre?",
                "help_type": "hint",
                "player_inventory": ["Chave Mestra", "Explosivos"]
            }
        }
        
        print(f"📤 Enviando payload...")
        await ws.send(json.dumps(payload))
        
        # Recebe eventos
        print(f"⏳ Aguardando eventos...\n")
        try:
            while True:
                event = await ws.recv()
                data = json.loads(event)
                print(f"📥 [{data['type']}]: {data['data']}\n")
        except websockets.exceptions.ConnectionClosed:
            print("\n✅ Conexão fechada")

if __name__ == "__main__":
    import time
    asyncio.run(test_websocket())
