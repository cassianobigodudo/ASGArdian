# 🛡️ ASGArdian Frontend

Interface visual moderna para o ASGArdian — Anti-Spoiler Gameplay Assistant.

## 🎨 Features

- ✨ **Streaming em Tempo Real** — Acompanhe cada nó do grafo executando
- 📊 **Visualização do Fluxo** — Veja o pipeline de processamento
- 🔄 **WebSocket Bi-direcional** — Comunicação em tempo real com o backend
- 🎯 **HITL Dialog** — Interaja quando faltar um item
- 📋 **Log de Eventos** — Rastreie todos os eventos da execução
- 🎨 **Design Responsivo** — Funciona em desktop, tablet e mobile

## 🚀 Como Iniciar

### 1. Instalar Dependências

```bash
cd frontend
npm install
```

### 2. Iniciar Backend (API FastAPI)

Em outro terminal:

```bash
# Certifique-se de que você está na raiz do projeto
python -m backend.api
```

Você verá:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Iniciar Frontend (Dev Server)

```bash
# Ainda dentro de frontend/
npm run dev
```

Você verá:
```
VITE v5.0.0  ready in 123 ms

➜  Local:   http://localhost:5173/
```

### 4. Abrir no Navegador

Abra [http://localhost:5173](http://localhost:5173) no seu navegador.

---

## 📁 Estrutura do Frontend

```
frontend/
├── index.html                 # Entry point HTML
├── package.json              # Dependências e scripts
├── vite.config.js           # Configuração Vite
├── postcss.config.js        # Configuração PostCSS
├── README.md                # Este arquivo
└── src/
    ├── main.jsx             # Bootstrap React
    ├── index.css            # Estilos globais
    ├── App.jsx              # Componente raiz
    ├── App.css              # Estilos do App
    └── components/
        ├── InputForm.jsx      # Formulário de entrada
        ├── InputForm.css
        ├── ExecutionMonitor.jsx  # Monitor em tempo real
        ├── ExecutionMonitor.css
        ├── NodeStatus.jsx     # Status de cada nó
        ├── NodeStatus.css
        ├── ResponseDisplay.jsx # Exibição da resposta
        ├── ResponseDisplay.css
        ├── HITLDialog.jsx     # Dialog Human-in-the-Loop
        └── HITLDialog.css
```

---

## 🔌 Comunicação Backend-Frontend

### Fluxo WebSocket

```
Frontend                          Backend
   │                                 │
   ├──── POST /api/run-agent ────→   │
   │     (validar payload)           │
   │                                 │
   │← ── {thread_id} ────────────────┤
   │                                 │
   ├──── WS /ws/{thread_id} ────→   │
   │     (send payload)              │
   │                                 │
   │← ── node_started ────────────┤  │
   │← ── node_completed ──────────┤  │
   │← ── hitl_pause ───────────────┤  │
   │  (user interacts)               │
   │                                 │
   ├──── hitl_response ──────────→   │
   │     (approval)                  │
   │                                 │
   │← ── complete / error ─────────┤ │
   │                                 │
```

### Eventos WebSocket

| Evento | Dados | Descrição |
|--------|-------|-----------|
| `execution_start` | `game_name`, `mission_name`, `current_issue` | Início da execução |
| `node_started` | `node`, `description` | Um nó começou |
| `node_completed` | `node`, `status` | Um nó terminou |
| `hitl_pause` | `missing_item`, `message` | Aguardando aprovação do usuário |
| `hitl_resumed` | `message` | Usuário aprovou, continuando |
| `complete` | `response`, `game_name`, `mission_name` | Execução concluída |
| `error` | `message` | Erro durante execução |

---

## 🎨 Paleta de Cores

| Uso | Cor | Hex |
|-----|-----|-----|
| Primário | Azul | `#3498db` |
| Sucesso | Verde | `#2ecc71` |
| Erro | Vermelho | `#e74c3c` |
| Aviso | Laranja | `#f39c12` |
| Background | Azul Escuro | `#1a1a2e`, `#0f3460` |
| Texto | Cinza Claro | `#ecf0f1` |

---

## 🔧 Troubleshooting

### Port já em uso

Se receber erro de porta já em uso:

```bash
# Frontend (porta 5173)
npm run dev -- --port 5174

# Backend (porta 8000)
python -m backend.api --port 8001
```

### WebSocket recusa conexão

Certifique-se de que:
1. Backend está rodando em `localhost:8000`
2. CORS está habilitado (já está no código)
3. Firewall não está bloqueando

### Payload inválido

Verifique se todos os 5 campos obrigatórios foram preenchidos:
- `game_name` (não vazio)
- `mission_name` (não vazio)
- `current_issue` (não vazio)
- `help_type` ("hint" ou "answer")
- `player_inventory` (lista de strings)

---

## 📦 Build para Produção

```bash
npm run build
```

Isso gera uma pasta `dist/` pronta para deploy.

---

## 🚀 Deploy

### Servir com Nginx/Apache

```bash
# Copie os arquivos de dist/ para seu servidor
cp -r dist/* /var/www/asgardian/

# Configure seu servidor web para servir o index.html em 404s
```

### Deploy com Docker

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY frontend/ .
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 📝 Licença

MIT - Veja [`LICENSE`](../LICENSE) para detalhes.
