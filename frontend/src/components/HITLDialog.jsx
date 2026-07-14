import React from 'react'
import './HITLDialog.css'

export default function HITLDialog({
  missingItem,
  message,
  onResponse
}) {
  return (
    <div className="hitl-overlay">
      <div className="hitl-dialog">
        <div className="hitl-header">
          <h2>⚠️ Pré-requisito Detectado</h2>
        </div>

        <div className="hitl-content">
          <p className="hitl-message">{message}</p>

          <div className="hitl-item-box">
            <strong>Item Faltante:</strong>
            <span>{missingItem}</span>
          </div>

          <p className="hitl-question">
            Você gostaria que o ASGArdian buscasse onde encontrar este item?
          </p>
        </div>

        <div className="hitl-actions">
          <button
            onClick={() => onResponse('nao')}
            className="button-no"
          >
            ❌ Não, Vou Sozinho
          </button>
          <button
            onClick={() => onResponse('sim')}
            className="button-yes"
          >
            ✅ Sim, Busque o Item
          </button>
        </div>

        <small className="hitl-note">
          💡 Dica: Se você aceitar, faremos uma nova busca focada em como obter o item, mantendo spoilers fora!
        </small>
      </div>
    </div>
  )
}
