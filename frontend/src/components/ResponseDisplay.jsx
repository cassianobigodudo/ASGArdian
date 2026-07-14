import React, { useState } from 'react'
import './ResponseDisplay.css'

export default function ResponseDisplay({
  response,
  game,
  mission,
  helpType
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(response)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const title = helpType === 'hint'
    ? '💭 Dica Sutil'
    : '✅ Solução Direta'

  return (
    <div className="response-display">
      <div className="response-header">
        <div>
          <h3>{title}</h3>
          <p className="response-context">
            {game} • {mission}
          </p>
        </div>
        <button
          onClick={handleCopy}
          className="button-copy"
          title="Copiar resposta"
        >
          {copied ? '✅ Copiado!' : '📋 Copiar'}
        </button>
      </div>

      <div className="response-content">
        {response.split('\n').map((line, idx) => (
          <p key={idx}>{line || '\n'}</p>
        ))}
      </div>

      <div className="response-footer">
        <span className="spoiler-badge">🛡️ Sem spoilers verificados</span>
      </div>
    </div>
  )
}
