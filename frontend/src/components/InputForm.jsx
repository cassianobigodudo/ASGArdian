import React, { useState } from 'react'
import axios from 'axios'
import './InputForm.css'

const EXAMPLE_PAYLOADS = {
  borderlands2: {
    game_name: 'Borderlands 2',
    mission_name: 'Lights Out',
    current_issue: 'Estou na área da subestação e não consigo restaurar a energia. Já ativei duas alavancas mas nada acontece.',
    help_type: 'hint',
    player_inventory: ['Shotgun Torque', 'Shield Adaptive', 'Grenade Singularity']
  },
  gtav: {
    game_name: 'Grand Theft Auto V',
    mission_name: 'The Big Score',
    current_issue: 'Não consigo abrir o cofre da joalheria. Tentei dinamite mas não funcionou.',
    help_type: 'answer',
    player_inventory: ['Explosivos', 'Motoserras', 'Batida']
  }
}

export default function InputForm({ onStartExecution }) {
  const [formData, setFormData] = useState({
    game_name: '',
    mission_name: '',
    current_issue: '',
    help_type: 'hint',
    player_inventory: ''
  })

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    setError(null)
  }

  const handleLoadExample = (exampleKey) => {
    const example = EXAMPLE_PAYLOADS[exampleKey]
    setFormData({
      ...example,
      player_inventory: example.player_inventory.join(', ')
    })
    setError(null)
  }

  const validateForm = () => {
    if (!formData.game_name.trim()) return 'Nome do jogo é obrigatório'
    if (!formData.mission_name.trim()) return 'Nome da missão é obrigatório'
    if (!formData.current_issue.trim()) return 'Descrição do problema é obrigatória'
    if (!formData.help_type) return 'Tipo de ajuda é obrigatório'
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      // Prepara payload
      const payload = {
        game_name: formData.game_name.trim(),
        mission_name: formData.mission_name.trim(),
        current_issue: formData.current_issue.trim(),
        help_type: formData.help_type,
        player_inventory: formData.player_inventory
          .split(',')
          .map(item => item.trim())
          .filter(item => item)
      }

      // Inicia execução via API
      const response = await axios.post('/api/run-agent', payload)
      const { thread_id } = response.data

      // Inicia execução
      onStartExecution(thread_id, payload)

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Erro ao iniciar execução'
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="input-form-container">
      <div className="form-wrapper">
        <h2>Bem-vindo, Jogador!</h2>
        <p className="form-description">
          Descreva o seu problema no jogo e o ASGArdian ajudará sem revelar spoilers
        </p>

        <form onSubmit={handleSubmit} className="input-form">
          {error && (
            <div className="error-message">
              <span>⚠️</span> {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="game_name">Nome do Jogo *</label>
            <input
              id="game_name"
              name="game_name"
              type="text"
              placeholder="Ex: Borderlands 2, GTA V, The Witcher 3"
              value={formData.game_name}
              onChange={handleInputChange}
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="mission_name">Missão / Localização *</label>
            <input
              id="mission_name"
              name="mission_name"
              type="text"
              placeholder="Ex: Lights Out, The Big Score"
              value={formData.mission_name}
              onChange={handleInputChange}
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="current_issue">Qual é o seu problema? *</label>
            <textarea
              id="current_issue"
              name="current_issue"
              placeholder="Descreva onde você está travado e o que já tentou..."
              value={formData.current_issue}
              onChange={handleInputChange}
              rows="4"
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="help_type">Tipo de Ajuda *</label>
            <select
              id="help_type"
              name="help_type"
              value={formData.help_type}
              onChange={handleInputChange}
              disabled={isLoading}
            >
              <option value="hint">💭 Dica Sutil (pense fora da caixa)</option>
              <option value="answer">✅ Solução Direta (me mostre o caminho)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="player_inventory">Seu Inventário (itens separados por vírgula)</label>
            <textarea
              id="player_inventory"
              name="player_inventory"
              placeholder="Ex: Shotgun, Shield, Explosivos"
              value={formData.player_inventory}
              onChange={handleInputChange}
              rows="2"
              disabled={isLoading}
            />
            <small>Se deixar vazio, supomos que você tem todos os itens necessários</small>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="submit-button"
          >
            {isLoading ? (
              <>
                <span className="loader"></span> Iniciando...
              </>
            ) : (
              '🚀 Começar Busca'
            )}
          </button>
        </form>

        <div className="examples-section">
          <h3>Ou experimente com um exemplo:</h3>
          <div className="example-buttons">
            <button
              type="button"
              onClick={() => handleLoadExample('borderlands2')}
              disabled={isLoading}
              className="example-button"
            >
              Borderlands 2
            </button>
            <button
              type="button"
              onClick={() => handleLoadExample('gtav')}
              disabled={isLoading}
              className="example-button"
            >
              GTA V
            </button>
          </div>
        </div>
      </div>

      <div className="info-panel">
        <h3>ℹ️ Como Funciona</h3>
        <ul>
          <li>
            <strong>1. Busca:</strong> O ASGArdian busca detonados em tempo real
          </li>
          <li>
            <strong>2. Análise:</strong> Extrai apenas o relevante para seu ponto
          </li>
          <li>
            <strong>3. Filtro:</strong> Remove spoilers futuros da resposta
          </li>
          <li>
            <strong>4. Entrega:</strong> Você recebe uma dica ou solução limpa
          </li>
          <li>
            <strong>5. HITL:</strong> Se faltar item, você aprova a busca
          </li>
        </ul>

        <h3>🛡️ Garantias</h3>
        <ul>
          <li>✅ Sem revelar enredo futuro</li>
          <li>✅ Sem spoilers de morte de personagens</li>
          <li>✅ Sem arruinar reviravoltas</li>
          <li>✅ Busca dinâmica em tempo real</li>
        </ul>
      </div>
    </div>
  )
}
