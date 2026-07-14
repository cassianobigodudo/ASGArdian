import React, { useState } from 'react'
import InputForm from './components/InputForm'
import ExecutionMonitor from './components/ExecutionMonitor'
import './App.css'

export default function App() {
  const [threadId, setThreadId] = useState(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionData, setExecutionData] = useState(null)

  const handleStartExecution = (threadId, data) => {
    setThreadId(threadId)
    setIsExecuting(true)
    setExecutionData(data)
  }

  const handleExecutionComplete = () => {
    setIsExecuting(false)
  }

  const handleReset = () => {
    setThreadId(null)
    setIsExecuting(false)
    setExecutionData(null)
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <h1>🛡️ ASGArdian</h1>
          <p>Anti-Spoiler Gameplay Assistant</p>
        </div>
        <div className="header-status">
          {isExecuting ? (
            <span className="status-badge executing">
              <span className="status-dot"></span>
              Executando...
            </span>
          ) : (
            <span className="status-badge ready">
              <span className="status-dot"></span>
              Pronto
            </span>
          )}
        </div>
      </header>

      <main className="app-main">
        {!threadId ? (
          <InputForm onStartExecution={handleStartExecution} />
        ) : (
          <ExecutionMonitor
            threadId={threadId}
            executionData={executionData}
            onComplete={handleExecutionComplete}
            onReset={handleReset}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>Desenvolvido com ❤️ usando LangGraph + React</p>
      </footer>
    </div>
  )
}
