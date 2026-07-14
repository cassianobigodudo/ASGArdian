# -*- coding: utf-8 -*-
"""
api.py -- API FastAPI com streaming WebSocket para o frontend.

Responsabilidades:
- Servir endpoint HTTP POST /api/run-agent para iniciar execução
- Streaming WebSocket /ws para atualizações em tempo real dos nós
- Gerenciar state da execução e pausas HITL
"""

import json
import uuid
import logging
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from backend.main import run_agent, validate_payload, build_initial_state
from backend.graph.workflow import app as graph_app
from backend.errors import ASGArdianError, PayloadValidationError

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gerenciador de conexões WebSocket
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Gerencia conexões WebSocket ativas e broadcast de eventos."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.execution_state: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, thread_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[thread_id] = websocket
        self.execution_state[thread_id] = {"status": "connected"}
    
    async def disconnect(self, thread_id: str):
        if thread_id in self.active_connections:
            del self.active_connections[thread_id]
        if thread_id in self.execution_state:
            del self.execution_state[thread_id]
    
    async def send_event(self, thread_id: str, event_type: str, data: Dict[str, Any]):
        """Envia evento para cliente WebSocket."""
        if thread_id not in self.active_connections:
            logger.warning(f"Conexão {thread_id} não ativa")
            return
        
        message = {
            "type": event_type,
            "timestamp": uuid.uuid4().isoformat(),
            "data": data
        }
        
        try:
            await self.active_connections[thread_id].send_json(message)
        except Exception as e:
            logger.error(f"Erro ao enviar evento: {e}")
            await self.disconnect(thread_id)
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Envia evento para todas as conexões ativas."""
        for thread_id in self.active_connections:
            await self.send_event(thread_id, event_type, data)


manager = ConnectionManager()

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management para FastAPI."""
    logger.info("🛡️ ASGArdian API iniciado")
    yield
    logger.info("🛡️ ASGArdian API finalizado")


app = FastAPI(
    title="ASGArdian API",
    description="API para execução do agente anti-spoiler com streaming em tempo real",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Rotas HTTP
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ASGArdian API",
        "version": "1.0.0"
    }


@app.post("/api/run-agent")
async def run_agent_endpoint(payload: Dict[str, Any]):
    """
    Inicia execução do agente com streaming WebSocket.
    
    Payload:
    {
        "game_name": "Borderlands 2",
        "mission_name": "Lights Out",
        "current_issue": "Descrição do problema",
        "help_type": "hint" ou "answer",
        "player_inventory": ["item1", "item2"]
    }
    
    Retorna:
    {
        "thread_id": "uuid",
        "status": "started",
        "message": "Conexão WebSocket iniciada para streaming"
    }
    """
    try:
        validate_payload(payload)
    except PayloadValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    thread_id = str(uuid.uuid4())
    
    return {
        "thread_id": thread_id,
        "status": "started",
        "message": "Conecte via WebSocket para receber atualizações em tempo real",
        "ws_endpoint": f"ws://localhost:8000/ws/{thread_id}"
    }


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """
    WebSocket endpoint para streaming de eventos em tempo real.
    
    Eventos enviados:
    - "node_started": Nó iniciou execução
    - "node_completed": Nó completou com resultado
    - "hitl_pause": Grafo pausado aguardando user_approval
    - "error": Erro durante execução
    - "complete": Execução finalizada
    """
    await manager.connect(thread_id, websocket)
    logger.info(f"Cliente conectado: {thread_id}")
    
    try:
        # Aguarda mensagem inicial com payload
        data = await websocket.receive_json()
        payload = data.get("payload")
        
        if not payload:
            await manager.send_event(thread_id, "error", {
                "message": "Payload não fornecido na mensagem inicial"
            })
            await manager.disconnect(thread_id)
            return
        
        # Valida payload
        try:
            validate_payload(payload)
        except PayloadValidationError as e:
            await manager.send_event(thread_id, "error", {
                "message": f"Payload inválido: {str(e)}"
            })
            await manager.disconnect(thread_id)
            return
        
        # Envia confirmação de início
        await manager.send_event(thread_id, "execution_start", {
            "game_name": payload["game_name"],
            "mission_name": payload["mission_name"],
            "current_issue": payload["current_issue"],
        })
        
        # Executa o agente com streaming
        initial_state = build_initial_state(payload)
        config = {"configurable": {"thread_id": thread_id}}
        
        # Executa primeiro ciclo
        await manager.send_event(thread_id, "node_started", {
            "node": "fetch_guide_node",
            "description": "🔍 Buscando detonado na internet..."
        })
        
        try:
            result = graph_app.invoke(initial_state, config=config)
            
            # Simula eventos dos nós (em produção, seria integrado com LangGraph hooks)
            nodes_sequence = [
                ("fetch_guide_node", "🔍 Buscando detonado"),
                ("process_guide_node", "📋 Processando guia"),
                ("verify_requirements_node", "✅ Verificando requisitos"),
                ("generate_help_node", "💭 Gerando resposta"),
                ("critique_spoiler_node", "🛡️ Verificando spoilers")
            ]
            
            for node_name, description in nodes_sequence:
                await manager.send_event(thread_id, "node_started", {
                    "node": node_name,
                    "description": description
                })
                
                # Simula processamento
                import asyncio
                await asyncio.sleep(0.5)
                
                await manager.send_event(thread_id, "node_completed", {
                    "node": node_name,
                    "status": "success"
                })
            
            # Verifica se há pausa HITL
            snapshot = graph_app.get_state(config)
            if snapshot.next and "fetch_guide_node" in snapshot.next:
                missing_item = snapshot.values.get("missing_item")
                if missing_item:
                    await manager.send_event(thread_id, "hitl_pause", {
                        "missing_item": missing_item,
                        "message": f"Item faltando: {missing_item}. Deseja buscar?"
                    })
                    
                    # Aguarda resposta do usuário via WebSocket
                    while True:
                        user_message = await websocket.receive_json()
                        if user_message.get("type") == "hitl_response":
                            user_approval = user_message.get("approval")  # "sim" ou "nao"
                            
                            if user_approval == "nao":
                                await manager.send_event(thread_id, "execution_blocked", {
                                    "message": f"Progresso bloqueado: '{missing_item}' ausente"
                                })
                                break
                            
                            elif user_approval == "sim":
                                # Atualiza estado e retoma
                                graph_app.update_state(config, {
                                    "user_approval": "sim",
                                    "is_item_search": True,
                                    "current_issue": f"como obter {missing_item} em {payload['game_name']}"
                                })
                                
                                await manager.send_event(thread_id, "hitl_resumed", {
                                    "message": f"Buscando: como obter {missing_item}"
                                })
                                
                                # Retoma execução
                                result = graph_app.invoke(None, config=config)
                                snapshot = graph_app.get_state(config)
                                break
            
            # Execução completa
            final_response = snapshot.values.get("final_response", "")
            
            await manager.send_event(thread_id, "complete", {
                "status": "success",
                "response": final_response,
                "game_name": payload["game_name"],
                "mission_name": payload["mission_name"]
            })
            
        except ASGArdianError as e:
            await manager.send_event(thread_id, "error", {
                "message": f"Erro do agente: {str(e)}"
            })
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            await manager.send_event(thread_id, "error", {
                "message": f"Erro inesperado: {str(e)}"
            })
    
    except WebSocketDisconnect:
        logger.info(f"Cliente desconectado: {thread_id}")
        await manager.disconnect(thread_id)
    except Exception as e:
        logger.error(f"Erro na conexão WebSocket: {e}")
        await manager.disconnect(thread_id)


# ---------------------------------------------------------------------------
# Servidor
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
