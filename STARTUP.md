# 🛡️ ASGArdian — Como Executar (Frontend + Backend)

## Pré-requisitos

- Python 3.10+ instalado
- Node.js 16+ instalado
- npm ou yarn
- Chaves de API configuradas (`.env`)

---

## 🚀 Execução Rápida (3 passos)

### 1️⃣ Instalar Dependências Backend

```bash
pip install -r requirements.txt
```

### 2️⃣ Instalar Dependências Frontend

```bash
cd frontend
npm install
cd ..
```

### 3️⃣ Rodar Backend e Frontend em Paralelo

Abra **2 terminais**:

#### Terminal 1 — Backend (API FastAPI)

```bash
python -m backend.api
```

Esperado:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### Terminal 2 — Frontend (Vite Dev Server)

```bash
cd frontend
npm run dev
```

Esperado:
```
VITE v5.0.0  ready in 123 ms

➜  Local:   http://localhost:5173/
```

### 4️⃣ Abrir no Navegador

Acesse: **http://localhost:5173**

---

## 📊 Arquitetura de Execução

```
┌─────────────────────────────────────────────────────────┐
│                   NAVEGADOR (React)                     │
│              localhost:5173                             │
│  ┌────────────────────────────────────────────────────┐ │
│  │  InputForm      ExecutionMonitor   ResponseDisplay│ │
│  │  (formulário)   (fluxo em tempo   (resultado)     │ │
│  │                  real)                             │ │
│  └────────────────────────────────────────────────────┘ │
│                       ↕ HTTP + WebSocket                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              FastAPI + LangGraph                         │
│              localhost:8000                             │
│  ┌────────────────────────────────────────────────────┐ │
│  │  POST /api/run-agent     ← inicia execução        │ │
│  │  WS /ws/{thread_id}      ← streaming de eventos   │ │
│  │  GET /api/health         ← health check           │ │
│  └────────────────────────────────────────────────────┘ │
│                       ↓                                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Backend LangGraph (5 nós)                         │ │
│  │  - fetch_guide_node                                │ │
│  │  - process_guide_node                              │ │
│  │  - verify_requirements_node                        │ │
│  │  - generate_help_node                              │ │
│  │  - critique_spoiler_node                           │ │
│  └────────────────────────────────────────────────────┘ │
│                       ↓                                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │  LLM Providers                                      │ │
│  │  - Groq (primary)                                  │ │
│  │  - Gemini (fallback)                               │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Fluxo de Uso

### 1. Inserir Dados

```json
{
  "game_name": "Borderlands 2",
  "mission_name": "Lights Out",
  "current_issue": "Não consigo restaurar a energia",
  "help_type": "hint",
  "player_inventory": ["Shotgun", "Shield"]
}
```

### 2. Ver Execução em Tempo Real

Frontend exibe:
- 🔍 Buscando detonado
- 📋 Processando guia
- ✅ Verificando requisitos
- 💭 Gerando resposta
- 🛡️ Auditando spoilers

### 3. Receber Resposta

```
💭 Dica Sutil:

Você já ativou as alavancas corretas. Preste atenção 
nos elementos visuais da sala...

[Nenhum spoiler de enredo foi incluído nesta resposta.]
```

### 4. (Opcional) HITL — Se Faltar Item

Dialog aparece perguntando se quer buscar o item faltante.

---

## 🛠️ Troubleshooting

### ❌ Erro: "Port 8000 already in use"

```bash
# Encontre e mate o processo
lsof -i :8000      # macOS/Linux
netstat -ano | grep :8000  # Windows

# Ou use outra porta
python -m backend.api --port 8001
```

### ❌ Erro: "CORS error"

CORS já está habilitado no `backend/api.py`. Se persistir:

```python
# Edite backend/api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### ❌ Erro: "WebSocket connection refused"

Certifique-se de que:
1. Backend está rodando (`python -m backend.api`)
2. Porta 8000 está acessível
3. Firewall não está bloqueando

### ❌ Erro: "npm: command not found"

Instale Node.js: https://nodejs.org/

```bash
# Após instalar, verifique
node --version
npm --version
```

---

## 📊 Desenvolvimento

### Estrutura do Projeto

```
ASGArdian/
├── backend/
│   ├── main.py              # Executor principal
│   ├── api.py               # FastAPI + WebSocket ← NOVO
│   ├── graph/
│   │   ├── nodes.py         # 5 nós do grafo
│   │   ├── state.py         # AgentState
│   │   └── workflow.py      # Compilação do grafo
│   ├── prompts/
│   │   └── templates.py     # Prompts dos nós
│   └── tests/
│       ├── test_main.py     # 26 testes
│       ├── test_nodes.py    # 17 testes
│       ├── test_workflow.py # 15 testes
│       └── ...
├── frontend/                ← NOVO
│   ├── src/
│   │   ├── components/      # InputForm, ExecutionMonitor, etc.
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
├── docs/
│   └── prompts/
│       ├── prompts.md       # Documentação de prompts
│       └── GROQ_TEST_RESULTS.md
├── requirements.txt         # Atualizado com FastAPI
└── README.md
```

### Scripts Úteis

```bash
# Testar backend
python -m pytest backend/tests/ -v

# Limpar cache frontend
rm -rf frontend/node_modules frontend/dist

# Build frontend
cd frontend && npm run build && cd ..

# Verificar código Python
python -m flake8 backend/

# Type checking (opcional)
python -m mypy backend/
```

---

## 🔒 Segurança

- `.env` nunca é commitado (verificado com `.gitignore`)
- Chaves carregadas via `python-dotenv`
- CORS habilitado para localhost:5173
- WebSocket valida payload antes de processar

---

## 🚀 Deploy (Produção)

### Backend (Gunicorn + Nginx)

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.api:app
```

### Frontend (Build estático)

```bash
cd frontend
npm run build
# Copie dist/ para seu servidor web estático
```

---

## 📚 Documentação

- **Backend**: [`backend/api.py`](backend/api.py)
- **Frontend**: [`frontend/README.md`](frontend/README.md)
- **LangGraph**: [`backend/graph/workflow.py`](backend/graph/workflow.py)
- **Prompts**: [`docs/prompts/prompts.md`](docs/prompts/prompts.md)

---

## ✨ Próximos Passos

- [ ] Adicionar testes E2E do frontend
- [ ] Integração com mais LLMs (OpenAI, Claude)
- [ ] Cache de respostas
- [ ] Histórico de buscas
- [ ] Modo offline

---

Enjoy! 🛡️
