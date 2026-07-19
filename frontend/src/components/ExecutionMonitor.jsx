import React, { useState, useEffect, useRef } from 'react'
import NodeStatus from './NodeStatus'
import ResponseDisplay from './ResponseDisplay'
import HITLDialog from './HITLDialog'
import './ExecutionMonitor.css'

const NODES = [
  { id: 'fetch_guide_node', name: 'Buscar Guia', icon: '🔍', description: 'Buscando detonado na internet' },
  { id: 'process_guide_node', name: 'Processar', icon: '📋', description: 'Processando conteúdo' },
  { id: 'verify_requirements_node', name: 'Verificar', icon: '✅', description: 'Verificando requisitos' },
  { id: 'generate_help_node', name: 'Gerar Resposta', icon: '💭', description: 'Gerando resposta' },
  { id: 'critique_spoiler_node', name: 'Auditar', icon: '🛡️', description: 'Auditando spoilers' }
]

export default function ExecutionMonitor({
  threadId,
  executionData,
  onComplete,
  onReset
}) {
  const [nodeStatus, setNodeStatus] = useState({})
  const [response, setResponse] = useState(null)
  const [events, setEvents] = useState([])
  const [error, setError] = useState(null)
  const [isComplete, setIsComplete] = useState(false)
  const [hitlData, setHitlData] = useState(null)
  const wsRef = React.useRef(null)

  useEffect(() => {
    // Inicializa status dos nós
    const initialStatus = {}
    NODES.forEach(node => {
      initialStatus[node.id] = 'pending'
    })
    setNodeStatus(initialStatus)

    // Conecta WebSocket direto ao backend (sem proxy)
    const wsUrl = `ws://localhost:8000/api/ws/${threadId}`
    
    console.log('🔗 [Frontend] Conectando WebSocket:', wsUrl)
    console.log('📤 [Frontend] Payload a enviar:', executionData)
    wsRef.current = new WebSocket(wsUrl)

    wsRef.current.onopen = () => {
      console.log('✅ [Frontend] WebSocket conectado com sucesso!')
      console.log('📤 [Frontend] Enviando payload:', JSON.stringify(executionData, null, 2))
      // Envia payload
      wsRef.current.send(JSON.stringify({
        payload: executionData
      }))
    }

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data)
      console.log('📥 [Frontend] Mensagem recebida:', message)
      handleWebSocketMessage(message)
    }

    wsRef.current.onerror = (error) => {
      console.error('❌ [Frontend] Erro WebSocket:', error)
      console.log('⚠️ [Frontend] Erro durante conexão')
    }

    wsRef.current.onclose = () => {
      console.log('🔌 [Frontend] WebSocket desconectado')
    }

    return () => {
      if (wsRef.current) {
        console.log('🧹 [Frontend] Limpando conexão WebSocket')
        wsRef.current.close()
      }
    }
  }, [threadId, executionData])

  const handleWebSocketMessage = (message) => {
    const { type, data, timestamp } = message

    console.log(`📨 [Frontend] Tipo: ${type}`, data)

    // Adiciona evento ao log
    setEvents(prev => [...prev, { type, data, timestamp }])

    switch (type) {
      case 'execution_start':
        console.log('🎬 [Frontend] Execução iniciada:', data)
        break

      case 'node_started':
        console.log(`🔵 [Frontend] Nó iniciado: ${data.node}`)
        setNodeStatus(prev => ({
          ...prev,
          [data.node]: 'running'
        }))
        break

      case 'node_completed':
        console.log(`✅ [Frontend] Nó completado: ${data.node}`)
        setNodeStatus(prev => ({
          ...prev,
          [data.node]: 'success'
        }))
        break

      case 'hitl_question':
        console.log('❓ [Frontend] Pergunta HITL:', data)
        setHitlData({
          missing_item: data.missing_item,
          message: data.message
        })
        break

      case 'hitl_resumed':
        console.log('▶️ [Frontend] Retomando após HITL:', data)
        setHitlData(null)
        setNodeStatus(prev => ({
          ...prev,
          'fetch_guide_node': 'running'
        }))
        break

      case 'execution_blocked':
        console.log('🚫 [Frontend] Execução bloqueada:', data)
        setError(data.message)
        setIsComplete(true)
        onComplete()
        break

      case 'complete':
        console.log('🏁 [Frontend] Execução completa:', data)
        setNodeStatus(prev => ({
          ...prev,
          'critique_spoiler_node': 'success'
        }))
        setResponse(data.response)
        setIsComplete(true)
        onComplete()
        break

      case 'error':
        console.log('❌ [Frontend] Erro recebido:', data)
        setNodeStatus(prev => ({
          ...prev,
          [prev[Object.keys(prev).find(key => prev[key] === 'running')] || 'fetch_guide_node']: 'error'
        }))
        setError(data.message)
        setIsComplete(true)
        onComplete()
        break

      default:
        console.log('❓ [Frontend] Tipo desconhecido:', type)
        break
    }
  }

  const handleHITLResponse = (approval) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'hitl_response',
        approval
      }))
      setHitlData(null)
    }
  }

  return (
    <div className="execution-monitor">
      <div className="monitor-main">
        {/* Visualização do Grafo */}
        <div className="graph-visualization">
          <h3>Fluxo de Execução</h3>
          <div className="nodes-container">
            {NODES.map((node, index) => (
              <div key={node.id} className="node-wrapper">
                <NodeStatus
                  node={node}
                  status={nodeStatus[node.id] || 'pending'}
                />
                {index < NODES.length - 1 && (
                  <div className="arrow">→</div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Resposta Final */}
        {response && (
          <ResponseDisplay
            response={response}
            game={executionData.game_name}
            mission={executionData.mission_name}
            helpType={executionData.help_type}
            threadId={threadId}
            onRegenerate={setResponse}
          />
        )}

        {/* Erro */}
        {error && !response && (
          <div className="error-panel">
            <h3>❌ Erro</h3>
            <p>{error}</p>
            <button onClick={onReset} className="button-reset">
              Tentar Novamente
            </button>
          </div>
        )}

        {/* Progresso */}
        {!isComplete && !hitlData && (
          <div className="progress-panel">
            <div className="spinner"></div>
            <p>Executando... Aguarde</p>
          </div>
        )}
      </div>

      {/* Painel Lateral de Logs */}
      <div className="monitor-sidebar">
        <div className="event-log">
          <h4>📋 Log de Eventos</h4>
          <div className="event-list">
            {events.map((event, index) => (
              <div key={index} className="event-item">
                <span className="event-time">
                  {new Date(event.timestamp).toLocaleTimeString('pt-BR')}
                </span>
                <span className="event-type">{event.type}</span>
                <span className="event-data">
                  {event.data.node || event.data.status || ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* HITL Dialog */}
      {hitlData && (
        <HITLDialog
          missingItem={hitlData.missing_item}
          message={hitlData.message}
          onResponse={handleHITLResponse}
        />
      )}

      {/* Botão de Reset */}
      {isComplete && (
        <div className="completion-actions">
          <button onClick={onReset} className="button-reset-main">
            🔄 Nova Busca
          </button>
          <button onClick={onReset} className="button-back">
            ⬅️ Voltar
          </button>
        </div>
      )}
    </div>
  )
}
