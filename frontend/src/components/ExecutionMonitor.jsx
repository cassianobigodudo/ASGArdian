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
  const [error, setError] = useState(null)
  const [isComplete, setIsComplete] = useState(false)
  const [hitlData, setHitlData] = useState(null)
  const [events, setEvents] = useState([])
  const wsRef = useRef(null)

  useEffect(() => {
    // Inicializa status dos nós
    const initialStatus = {}
    NODES.forEach(node => {
      initialStatus[node.id] = 'pending'
    })
    setNodeStatus(initialStatus)

    // Conecta WebSocket
    const wsUrl = `ws://localhost:8000/ws/${threadId}`
    wsRef.current = new WebSocket(wsUrl)

    wsRef.current.onopen = () => {
      console.log('WebSocket conectado')
      // Envia payload
      wsRef.current.send(JSON.stringify({
        payload: executionData
      }))
    }

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleWebSocketMessage(message)
    }

    wsRef.current.onerror = (error) => {
      console.error('Erro WebSocket:', error)
      setError('Erro na conexão com servidor')
    }

    wsRef.current.onclose = () => {
      console.log('WebSocket desconectado')
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [threadId, executionData])

  const handleWebSocketMessage = (message) => {
    const { type, data, timestamp } = message

    // Adiciona evento ao log
    setEvents(prev => [...prev, { type, data, timestamp }])

    switch (type) {
      case 'execution_start':
        console.log('Execução iniciada:', data)
        break

      case 'node_started':
        setNodeStatus(prev => ({
          ...prev,
          [data.node]: 'running'
        }))
        break

      case 'node_completed':
        setNodeStatus(prev => ({
          ...prev,
          [data.node]: 'success'
        }))
        break

      case 'hitl_pause':
        setHitlData({
          missing_item: data.missing_item,
          message: data.message
        })
        break

      case 'hitl_resumed':
        setHitlData(null)
        setNodeStatus(prev => ({
          ...prev,
          'fetch_guide_node': 'running'
        }))
        break

      case 'execution_blocked':
        setError(data.message)
        setIsComplete(true)
        onComplete()
        break

      case 'complete':
        setNodeStatus(prev => ({
          ...prev,
          'critique_spoiler_node': 'success'
        }))
        setResponse(data.response)
        setIsComplete(true)
        onComplete()
        break

      case 'error':
        setNodeStatus(prev => ({
          ...prev,
          [prev[Object.keys(prev).find(key => prev[key] === 'running')] || 'fetch_guide_node']: 'error'
        }))
        setError(data.message)
        setIsComplete(true)
        onComplete()
        break

      default:
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
        <button onClick={onReset} className="button-reset-main">
          🔄 Nova Busca
        </button>
      )}
    </div>
  )
}
