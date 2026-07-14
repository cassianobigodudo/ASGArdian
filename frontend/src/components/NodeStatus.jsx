import React from 'react'
import './NodeStatus.css'

export default function NodeStatus({ node, status }) {
  const getStatusClass = (s) => {
    switch (s) {
      case 'pending': return 'node-pending'
      case 'running': return 'node-running'
      case 'success': return 'node-success'
      case 'error': return 'node-error'
      default: return 'node-pending'
    }
  }

  const getStatusIcon = (s) => {
    switch (s) {
      case 'pending': return '⏱️'
      case 'running': return '⚙️'
      case 'success': return '✅'
      case 'error': return '❌'
      default: return '⏱️'
    }
  }

  return (
    <div className={`node-status ${getStatusClass(status)}`}>
      <div className="node-main">
        <div className="node-icon">{node.icon}</div>
        <div className="node-info">
          <h4>{node.name}</h4>
          <p>{node.description}</p>
        </div>
      </div>
      <div className="node-status-indicator">{getStatusIcon(status)}</div>
    </div>
  )
}
