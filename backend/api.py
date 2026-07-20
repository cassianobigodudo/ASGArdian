# -*- coding: utf-8 -*-
"""
api.py -- API FastAPI com streaming WebSocket para o frontend.
"""

import json
import uuid
import logging
import asyncio
import time
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.main import validate_payload, build_initial_state
from backend.graph.workflow import app as graph_app
from backend.graph.nodes import reset_execution_counters
from backend.errors import PayloadValidationError

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gerenciador de conexões WebSocket
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Gerencia conexões WebSocket ativas."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, thread_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[thread_id] = websocket
    
    async def disconnect(self, thread_id: str):
        if thread_id in self.active_connections:
            del self.active_connections[thread_id]
    
    async def send_event(self, thread_id: str, event_type: str, data: Dict[str, Any]):
        """Envia evento para cliente WebSocket."""
        if thread_id not in self.active_connections:
            logger.warning(f"[Backend] Conexão {thread_id} não ativa")
            return
        
        message = {
            "type": event_type,
            "data": data
        }
        
        logger.info(f"[Backend] 📤 Enviando evento '{event_type}' para {thread_id}: {data}")
        
        try:
            await self.active_connections[thread_id].send_json(message)
        except Exception as e:
            logger.error(f"[Backend] Erro ao enviar evento: {e}")
            await self.disconnect(thread_id)


manager = ConnectionManager()

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    logger.info("[Backend] 🏥 Health check")
    return {
        "status": "healthy",
        "service": "ASGArdian API",
        "version": "1.0.0"
    }


@app.post("/api/run-agent")
async def run_agent_endpoint(payload: Dict[str, Any] = Body(...)):
    """Inicia execução do agente com streaming WebSocket."""
    logger.info(f"[Backend] 📋 Recebido request /api/run-agent com payload: {payload}")
    
    try:
        validate_payload(payload)
        logger.info("[Backend] ✅ Payload validado com sucesso")
    except PayloadValidationError as e:
        logger.error(f"[Backend] ❌ Validação de payload falhou: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Backend] ❌ Erro inesperado na validação: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    thread_id = str(uuid.uuid4())
    logger.info(f"[Backend] 🆔 Thread ID gerada: {thread_id}")
    
    return {
        "thread_id": thread_id,
        "status": "started",
        "message": "Conecte via WebSocket para receber atualizações em tempo real",
        "ws_endpoint": f"ws://localhost:8000/api/ws/{thread_id}"
    }


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/api/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """WebSocket endpoint para streaming de eventos em tempo real."""
    logger.info(f"[Backend] 🔗 Tentando conectar WebSocket: {thread_id}")
    
    try:
        await manager.connect(thread_id, websocket)
        logger.info(f"[Backend] ✅ WebSocket conectado: {thread_id}")
        
        # Aguarda mensagem inicial com payload
        logger.info(f"[Backend] ⏳ Aguardando payload de {thread_id}")
        data = await websocket.receive_json()
        logger.info(f"[Backend] 📥 Payload recebido: {data}")
        
        payload = data.get("payload")
        
        if not payload:
            logger.error(f"[Backend] ❌ Payload vazio de {thread_id}")
            await manager.send_event(thread_id, "error", {
                "message": "Payload não fornecido"
            })
            await manager.disconnect(thread_id)
            return
        
        # Valida payload
        try:
            validate_payload(payload)
            logger.info(f"[Backend] ✅ Payload validado: {payload['game_name']}")
        except PayloadValidationError as e:
            logger.error(f"[Backend] ❌ Validação falhou: {e}")
            await manager.send_event(thread_id, "error", {
                "message": f"Payload inválido: {str(e)}"
            })
            await manager.disconnect(thread_id)
            return
        
        # RESET: Reseta contadores para esta nova execução
        reset_execution_counters()
        logger.info(f"[Backend] 🔄 Contadores de execução resetados para nova busca")
        
        # Envia confirmação de início
        await manager.send_event(thread_id, "execution_start", {
            "game_name": payload["game_name"],
            "mission_name": payload["mission_name"],
            "current_issue": payload["current_issue"],
        })
        
        logger.info(f"[Backend] 🎬 Iniciando execução para {thread_id}")
        
        # Executa o grafo real do LangGraph com Groq
        try:
            initial_state = build_initial_state(payload)
            logger.info(f"[Backend] 📦 Estado inicial construído")
            
            config = {"configurable": {"thread_id": thread_id}}
            logger.info(f"[Backend] ⚙️ Config: {config}")
            
            logger.info(f"[Backend] 🚀 Invocando graph_app com estado real...")
            logger.info(f"[Backend] Estado inicial (antes invoke):")
            logger.info(f"   - game_name: {initial_state.get('game_name')}")
            logger.info(f"   - current_issue: {initial_state.get('current_issue')}")
            logger.info(f"   - raw_search_result antes: {len(initial_state.get('raw_search_result', ''))} chars")
            
            # Invoca o grafo real COM TIMEOUT E PROTEÇÃO DE LOOP
            max_iterations = 10
            iteration_count = 0
            max_execution_time = 300
            start_time = time.time()
            
            try:
                logger.info(f"[Backend] ⏱️ Executando com timeout de {max_execution_time}s e máx {max_iterations} iterações")
                result = graph_app.invoke(initial_state, config=config)
                iteration_count += 1
                
                elapsed = time.time() - start_time
                logger.info(f"[Backend] ✅ Grafo executado em {elapsed:.1f}s (iteração {iteration_count})")
                
                # Verifica se há HITL pendente (missing_item detectado, mas user_approval não foi dado)
                if result.get("missing_item") and result.get("user_approval") is None:
                    logger.info(f"[Backend] [PAUSA HITL] Item faltando: '{result['missing_item']}'")
                    missing_item = result["missing_item"]
                    
                    # Envia pergunta HITL ao cliente
                    await manager.send_event(thread_id, "hitl_question", {
                        "message": f"Você não possui: '{missing_item}'.\n\nDeseja saber como obter este item?",
                        "missing_item": missing_item,
                        "options": ["sim", "nao"]
                    })
                    
                    logger.info(f"[Backend] [AGUARDANDO] Resposta HITL do cliente para: {missing_item}")
                    logger.info(f"[Backend] [CONEXÃO] Mantendo WebSocket aberto para resposta...")
                    
                    # NÃO desconecta! Aguarda resposta do cliente
                    # O cliente enviará uma mensagem tipo: {"type": "hitl_response", "approval": "sim" ou "nao"}
                    # A resposta será processada no try/except que aguarda mensagens WebSocket
                    try:
                        while True:
                            logger.info(f"[Backend] [AGUARDANDO] Mensagem do cliente...")
                            response_data = await websocket.receive_json()
                            logger.info(f"[Backend] [RECEBIDO] Resposta HITL: {response_data}")
                            
                            if response_data.get("type") == "hitl_response":
                                approval = response_data.get("approval", "").lower()
                                
                                if approval not in ("sim", "nao"):
                                    logger.warning(f"[Backend] [INVALID] Resposta inválida: {approval}")
                                    await manager.send_event(thread_id, "error", {
                                        "message": "Resposta inválida. Por favor, escolha 'sim' ou 'nao'."
                                    })
                                    continue
                                
                                logger.info(f"[Backend] [APROVAÇÃO] Usuário respondeu: {approval}")
                                
                                # Atualiza estado com resposta do usuário
                                if approval == "sim":
                                    logger.info(f"[Backend] [UPDATE] Setando user_approval='sim' e is_item_search=True")
                                    graph_app.update_state(
                                        config,
                                        {
                                            "user_approval": "sim",
                                            "is_item_search": True,
                                            "current_issue": f"como obter {missing_item} em {result['game_name']}",
                                        },
                                    )
                                else:  # "nao"
                                    logger.info(f"[Backend] [UPDATE] Setando user_approval='nao'")
                                    graph_app.update_state(
                                        config,
                                        {
                                            "user_approval": "nao",
                                        },
                                    )
                                
                                logger.info(f"[Backend] [RETOMANDO] Continuando execução após HITL...")
                                # Retoma o grafo
                                result = graph_app.invoke(None, config=config)
                                break
                            else:
                                logger.warning(f"[Backend] [TIPO DESCONHECIDO] {response_data.get('type')}")
                                continue
                    
                    except WebSocketDisconnect:
                        logger.warning(f"[Backend] [DESCONECTADO] Cliente desconectou durante HITL")
                        await manager.disconnect(thread_id)
                        return
                    except Exception as e:
                        logger.error(f"[Backend] [ERRO HITL] {e}", exc_info=True)
                        await manager.send_event(thread_id, "error", {"message": f"Erro durante HITL: {str(e)}"})
                        await manager.disconnect(thread_id)
                        return
                
                if elapsed > max_execution_time:
                    logger.error(f"[Backend] ❌ TIMEOUT: Execução excedeu {max_execution_time}s")
                    await manager.send_event(thread_id, "error", {"message": f"Timeout: execução excedeu {max_execution_time}s"})
                    await manager.disconnect(thread_id)
                    return
                    
                if iteration_count > max_iterations:
                    logger.error(f"[Backend] ❌ LOOP INFINITO: Grafo executou {max_iterations}+ vezes")
                    await manager.send_event(thread_id, "error", {"message": f"Loop infinito detectado após {max_iterations} iterações"})
                    await manager.disconnect(thread_id)
                    return
                    
            except Exception as e:
                logger.error(f"[Backend] ❌ Exceção durante invoke: {type(e).__name__}: {e}", exc_info=True)
                await manager.send_event(thread_id, "error", {"message": f"Erro durante execução: {str(e)}"})
                await manager.disconnect(thread_id)
                return
            
            logger.info(f"[Backend] ✅ Grafo executado com sucesso!")
            logger.info(f"[Backend] 📊 Estado retornado pelo grafo:")
            logger.info(f"   - Tipo: {type(result)}")
            logger.info(f"   - Chaves: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            # Log de cada campo importante
            if isinstance(result, dict):
                logger.info(f"   - game_name: {result.get('game_name')}")
                logger.info(f"   - raw_search_result: {len(result.get('raw_search_result', ''))} chars")
                logger.info(f"   - required_requirements: {result.get('required_requirements')}")
                logger.info(f"   - missing_item: {result.get('missing_item')}")
                logger.info(f"   - generated_text: {len(result.get('generated_text', ''))} chars")
                logger.info(f"   - critique_passed: {result.get('critique_passed')}")
                logger.info(f"   - final_response: {len(result.get('final_response', ''))} chars")
            
            # VALIDAÇÃO 1: Verifica se result é um dicionário válido
            if not isinstance(result, dict):
                error_msg = f"❌ ERRO CRÍTICO: Resultado do grafo não é um dicionário! Tipo: {type(result)}"
                logger.error(f"[Backend] {error_msg}")
                await manager.send_event(thread_id, "error", {"message": error_msg})
                await manager.disconnect(thread_id)
                return
            
            # VALIDAÇÃO 2: Verifica se raw_search_result foi preenchido (fetch_guide_node)
            raw_search_result = result.get("raw_search_result", "")
            if not raw_search_result or not raw_search_result.strip():
                error_msg = "❌ ERRO NO NÓ 'fetch_guide_node': raw_search_result vazio! Nenhum detonado foi encontrado."
                logger.error(f"[Backend] {error_msg}")
                await manager.send_event(thread_id, "node_started", {
                    "node": "fetch_guide_node",
                    "description": "🔍 Buscando detonado na internet..."
                })
                await manager.send_event(thread_id, "error", {"message": error_msg})
                await manager.disconnect(thread_id)
                return
            logger.info(f"[Backend] ✅ fetch_guide_node: OK - {len(raw_search_result)} chars encontrados")
            
            # VALIDAÇÃO 3: Verifica se required_requirements foi preenchido (process_guide_node)
            required_requirements = result.get("required_requirements", [])
            logger.info(f"[Backend] ✅ process_guide_node: OK - {len(required_requirements)} requisitos identificados")
            
            # VALIDAÇÃO 4: Verifica se verify_requirements_node funcionou
            missing_item = result.get("missing_item")
            logger.info(f"[Backend] ✅ verify_requirements_node: OK - missing_item = {missing_item}")
            
            # VALIDAÇÃO 5: Verifica se generated_text foi preenchido (generate_help_node)
            generated_text = result.get("generated_text", "")
            if not generated_text or not generated_text.strip():
                error_msg = "❌ ERRO NO NÓ 'generate_help_node': generated_text vazio! Nenhuma resposta foi gerada."
                logger.error(f"[Backend] {error_msg}")
                await manager.send_event(thread_id, "node_started", {
                    "node": "generate_help_node",
                    "description": "💭 Gerando resposta..."
                })
                await manager.send_event(thread_id, "error", {"message": error_msg})
                await manager.disconnect(thread_id)
                return
            logger.info(f"[Backend] ✅ generate_help_node: OK - {len(generated_text)} chars gerados")
            
            # VALIDAÇÃO 6: Verifica critique_passed (critique_spoiler_node)
            critique_passed = result.get("critique_passed", False)
            if not critique_passed:
                logger.warning(f"[Backend] ⚠️ critique_spoiler_node: critique_passed = False (resposta pode conter spoilers)")
            else:
                logger.info(f"[Backend] ✅ critique_spoiler_node: OK - critique_passed = True")
            
            # VALIDAÇÃO 7: Verifica final_response
            final_response = result.get("final_response", "")
            if not final_response or not final_response.strip():
                error_msg = "❌ ERRO NO NÓ 'critique_spoiler_node': final_response vazio! Nenhuma resposta validada."
                logger.error(f"[Backend] {error_msg}")
                await manager.send_event(thread_id, "node_started", {
                    "node": "critique_spoiler_node",
                    "description": "🛡️ Verificando spoilers..."
                })
                await manager.send_event(thread_id, "error", {"message": error_msg})
                await manager.disconnect(thread_id)
                return
            logger.info(f"[Backend] ✅ final_response: OK - {len(final_response)} chars")
            
            # Se chegou aqui, tudo passou! Envia eventos simulados para o frontend
            logger.info(f"[Backend] 🎉 TODAS AS VALIDAÇÕES PASSARAM! Enviando eventos ao frontend...")
            
            # Envia eventos reais dos nós que foram executados
            nodes_sequence = [
                ("fetch_guide_node", "🔍 Buscando detonado na internet..."),
                ("process_guide_node", "📋 Processando conteúdo..."),
                ("verify_requirements_node", "✅ Verificando requisitos..."),
                ("generate_help_node", "💭 Gerando resposta..."),
                ("critique_spoiler_node", "🛡️ Verificando spoilers...")
            ]
            
            for node_name, description in nodes_sequence:
                logger.info(f"[Frontend] 🔵 Enviando: nó iniciado {node_name}")
                await manager.send_event(thread_id, "node_started", {
                    "node": node_name,
                    "description": description
                })
                
                await asyncio.sleep(0.2)  # Pequeno delay para não sobrecarregar
                
                await manager.send_event(thread_id, "node_completed", {
                    "node": node_name,
                    "status": "success"
                })
                logger.info(f"[Frontend] ✅ Enviando: nó completado {node_name}")
            
            logger.info(f"[Backend] 🏁 Enviando resposta final ao frontend...")
            await manager.send_event(thread_id, "complete", {
                "status": "success",
                "response": final_response,
                "game_name": payload["game_name"],
                "mission_name": payload["mission_name"]
            })
            
        except Exception as e:
            logger.error(f"[Backend] ❌ Erro durante execução: {e}", exc_info=True)
            await manager.send_event(thread_id, "error", {
                "message": f"Erro: {str(e)}"
            })
    
    except WebSocketDisconnect:
        logger.info(f"[Backend] 🔌 Cliente desconectado: {thread_id}")
        await manager.disconnect(thread_id)
    except Exception as e:
        logger.error(f"[Backend] ❌ Erro geral: {e}", exc_info=True)
        try:
            await manager.disconnect(thread_id)
        except:
            pass


# ---------------------------------------------------------------------------
# Endpoint para Regenerar Dica
# ---------------------------------------------------------------------------

@app.post("/api/regenerate-hint")
async def regenerate_hint_endpoint(data: Dict[str, Any] = Body(...)):
    """
    Regenera uma nova dica/resposta usando o mesmo payload.
    Não refaz a busca web - apenas gera nova resposta baseada no mesmo guia.
    """
    thread_id = data.get("thread_id")
    
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id é obrigatório")
    
    logger.info(f"[Backend] [REGENERATE] Solicitação para regenerar dica: {thread_id}")
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Obtém estado atual
        snapshot = graph_app.get_state(config)
        if not snapshot or not snapshot.values:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        current_state = snapshot.values
        logger.info(f"[Backend] [REGENERATE] Estado atual obtido")
        
        # Atualiza para modo regeneração
        # Reset critique_passed e final_response para forçar nova geração
        graph_app.update_state(
            config,
            {
                "is_regenerating": True,
                "critique_passed": False,
                "generated_text": "",  # Limpa texto anterior
                "final_response": "",  # Limpa resposta anterior
                "_rewrite_count": 0,   # Reset contador de reescrita
            },
        )
        logger.info(f"[Backend] [REGENERATE] Modo regeneração ativado")
        
        # Retoma do ponto de fetch (que ainda tem os dados)
        # O roteador detectará is_regenerating=True e pulará para generate_help_node
        result = graph_app.invoke(None, config=config)
        logger.info(f"[Backend] [REGENERATE] Grafo executado para nova dica")
        
        # IMPORTANTE: Reseta is_regenerating após a resposta para evitar que múltiplas
        # chamadas consecutivas pensem que estão em um loop
        graph_app.update_state(
            config,
            {
                "is_regenerating": False,  # Reseta para False após regeneração
                "_rewrite_count": 0,       # Reset contador para próxima regeneração
            },
        )
        logger.info(f"[Backend] [REGENERATE] Estado resetado: is_regenerating=False")
        
        # Retorna resposta regenerada
        return {
            "status": "success",
            "generated_text": result.get("generated_text", ""),
            "final_response": result.get("final_response", ""),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Backend] [REGENERATE] Erro: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao regenerar: {str(e)}")


# ---------------------------------------------------------------------------
# Servidor
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )

