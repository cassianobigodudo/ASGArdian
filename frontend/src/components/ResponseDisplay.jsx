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

  // Separa conteúdo das fontes
  const [mainContent, sources] = (() => {
    if (!response.includes('---FONTES---')) {
      return [response, null]
    }
    const parts = response.split('---FONTES---')
    const content = parts[0].trim()
    const sourceText = parts[1].trim()
    return [content, sourceText]
  })()

  // Renderiza linha com suporte a links
  const renderLine = (line) => {
    // Detecta URLs no formato "🔗 http..."
    const urlMatch = line.match(/🔗\s*(https?:\/\/[^\s]+)/)
    if (urlMatch) {
      const url = urlMatch[1]
      const text = line.replace(/🔗\s*https?:\/\/[^\s]+/, '').trim()
      return (
        <div key={`${line}-link`} className="source-link">
          <a href={url} target="_blank" rel="noopener noreferrer" className="link-item">
            🔗 {text || url}
          </a>
        </div>
      )
    }
    return (
      <p key={line}>{line || '\n'}</p>
    )
  }

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
        {mainContent.split('\n').map((line, idx) => (
          <p key={idx}>{line || '\n'}</p>
        ))}
      </div>

      {sources && (
        <div className="response-sources">
          <h4>📚 Fontes Utilizadas:</h4>
          <div className="sources-list">
            {sources.split('\n').map((line, idx) => 
              line.trim() && renderLine(line)
            )}
          </div>
        </div>
      )}

      <div className="response-footer">
        <span className="spoiler-badge">🛡️ Sem spoilers verificados</span>
      </div>
    </div>
  )
}
