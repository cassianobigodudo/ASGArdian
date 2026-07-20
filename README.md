# ASGArdian 🛡️
### Anti-Spoiler Gameplay Assistant

> Um agente inteligente baseado em grafos que guia jogadores travados sem arruinar a experiência com spoilers.

---

## 📌 O Problema

Jogadores frequentemente ficam presos em puzzles ou missões complexas. Ao buscar ajuda em detonados tradicionais, são inevitavelmente expostos a spoilers do enredo — mortes de personagens, reviravoltas, desfechos — que destroem a experiência do jogo.

## 💡 A Solução

O ASGArdian recebe o contexto exato onde o jogador está travado e fornece **apenas a dica necessária para aquele momento**, filtrando qualquer informação cronologicamente posterior no roteiro do jogo.

---

## 🛠️ Arquitetura Detalhada

### Agentes do Sistema (5 Nós do Grafo)

1. **`fetch_guide_node`** (Busca de Detonados)
   - Consulta `guides_database.json` (IGN direto)
   - Fallback para Groq/Gemini se não encontrado
   - Query padrão: `"{game_name} {mission_name} guide walkthrough"`
   - Na 2ª passagem (HITL): `"como obter {missing_item} em {game_name}"`

2. **`process_guide_node`** (Análise de Conteúdo)
   - Extrai pré-requisitos críticos
   - Identifica passos mecânicos
   - Detecta spoilers narrativos futuros
   - Popula `required_requirements` e `future_spoilers`

3. **`verify_requirements_node`** (Validação de Inventário)
   - Compara `required_requirements` com `player_inventory`
   - Se inventário vazio: assume que jogador tem tudo
   - **Pulado** quando `is_item_search=True` (evita loop infinito)
   - Popula `missing_item` se algo crítico faltar

4. **`generate_help_node`** (Geração de Resposta)
   - Modo `hint`: dica sutil sem entregar a solução
   - Modo `answer`: sequência direta e objetiva
   - Incentiva uso de items críticos quando aplicável
   - Pode ser reescrito indefinidamente pelo critique

5. **`critique_spoiler_node`** (Auditoria Anti-Spoiler)
   - Valida resposta contra `future_spoilers`
   - Rejeita respostas com spoilers explícitos
   - Sem limite de reescritas até passar na auditoria
   - Garante `critique_passed=True` para encerrar

### Fluxo de Controle HITL

```
Inventário Incompleto Detectado
  │
  ├─ is_item_search=False (1ª passagem)
  │  ├─ user_approval="sim"  → atualiza current_issue + is_item_search=True → fetch_guide_node
  │  └─ user_approval="nao"  → END (bloqueio)
  │
  └─ is_item_search=True (2ª passagem)
     └─ Pula verify_requirements_node (por design)
```

### Proteção Contra Loops

| Camada | Mecanismo | Limite |
|---|---|---|
| Por Nó | `_node_execution_count` | 5 execuções/nó |
| Global | `_total_execution_time_start` | 300s (5min) |
| HITL | `is_item_search` flag | Pula verify na 2ª passagem |
| Reescrita | Critique loop | Indefinido até passar |

---

O coração da aplicação é um **StateGraph** do LangGraph com **5 nós** e roteamento condicional. Quando um item está faltando no inventário, o grafo reutiliza os mesmos nós de busca com um contexto atualizado — controlado pela flag `is_item_search` no estado para evitar loop infinito.

```
[INPUT]
   │
   ▼
fetch_guide_node          → Groq/Gemini busca detonados em tempo real
   │                         Na 2ª passagem: busca "como obter [missing_item]"
   ▼
process_guide_node        → Extrai pré-requisitos, passo a passo e spoilers futuros
   │
   ▼
verify_requirements_node  → Compara inventário com requisitos
   │                         (ignorado quando is_item_search=True → evita loop)
   │
   ├── missing_item + is_item_search=False
   │       │
   │       ▼
   │   [HITL: pausa e aguarda user_approval]
   │       │
   │       ├── "sim" → atualiza current_issue + is_item_search=True → volta ao fetch_guide_node
   │       └── "nao" → END (informa bloqueio)
   │
   └── ok ou is_item_search=True
           │
           ▼
       generate_help_node    → Gera hint ou answer baseado no help_type
           │
           ▼
       critique_spoiler_node → Audita a resposta contra spoilers futuros
           │
           ├── passed=True  → END
           └── passed=False → generate_help_node (reescreve sem spoilers)
```

### Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.12+ |
| Orquestração | LangGraph (StateGraph) |
| LLM Primário | **Groq** (Mixtral 8x7B) — Recomendado ⭐ |
| LLM Fallback | Gemini 2.0 Flash (fallback automático) |
| Busca Real-Time | Google Search (ferramenta nativa Gemini) |
| Framework LLM | LangChain + Groq SDK + LangChain-Google-GenAI |
| Persistência HITL | LangGraph MemorySaver |
| Env Management | python-dotenv |

---

## ⚙️ Configuração do Ambiente

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/ASGArdian.git
cd ASGArdian
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com sua chave:

```bash
cp .env.example .env
```

Edite o `.env`:

```env
# Groq API (RECOMENDADO - Melhor performance e quota generosa)
GROQ_API_KEY=sua_chave_do_groq_aqui

# Google API (Gemini) - Fallback automático se Groq não estiver configurado
GOOGLE_API_KEY=sua_chave_do_gemini_aqui
```

#### Obter Chaves de API

**Groq** (Recomendado):
- Vá em https://console.groq.com/keys
- Crie uma nova chave de API
- Cole em `GROQ_API_KEY`

**Google Gemini** (Fallback):
- Vá em https://aistudio.google.com/app/apikey
- Crie uma nova chave de API
- Cole em `GOOGLE_API_KEY`

> 💡 **Nota**: O sistema prioriza Groq se ambas as chaves estiverem presentes. Use Groq para melhor performance.

---

## 🚀 Como Executar

### Backend

```bash
python run.py
```

O servidor estará disponível em **http://localhost:8000** com modo desenvolvimento ativado (reload automático).

### Frontend (em outro terminal)

```bash
cd frontend
npm run dev
```

O frontend estará disponível em **http://localhost:5173**

### Ambos os servidores

Abra dois terminais e execute os comandos acima simultaneamente.

---

## 📥 Payload de Entrada

O agente aceita obrigatoriamente os seguintes campos:

```python
input_payload = {
    "game_name": "Borderlands 2",
    "mission_name": "Lights Out",
    "current_issue": "Estou na área da subestação e não consigo restaurar a energia. Já ativei duas alavancas mas nada acontece.",
    "help_type": "hint",   # "hint" (pista indireta) ou "answer" (solução direta)
    "player_inventory": ["Shotgun Torque", "Shield Adaptive", "Grenade Singularity"]
}
```

### Campos

| Campo | Tipo | Descrição |
|---|---|---|
| `game_name` | `str` | Nome do jogo |
| `mission_name` | `str` | Nome da missão ou localização atual |
| `current_issue` | `str` | Descrição livre de onde o jogador está travado |
| `help_type` | `"hint" \| "answer"` | Nível de ajuda desejado |
| `player_inventory` | `List[str]` | Itens ou habilidades que o jogador possui |

---

## 📤 Exemplos de Saída

### Modo `hint` (pista indireta)

```
🛡️ ASGArdian — Dica Sutil:

Você já ativou as alavancas corretas. Preste atenção nos elementos
visuais da sala — há algo no teto da subestação que ainda não
interagiu com você. Observe as luzes indicadoras antes de tentar
novamente.

[Nenhum spoiler de enredo foi incluído nesta resposta.]
```

### Modo `answer` (solução direta)

```
🛡️ ASGArdian — Solução:

1. Após ativar as duas alavancas laterais, localize o painel central
   de controle (marcado com um ícone amarelo no minimapa).
2. Interaja com o painel para conectar o circuito principal.
3. A energia será restaurada e a porta norte será desbloqueada.

[Nenhum spoiler de enredo foi incluído nesta resposta.]
```

### Fluxo HITL — Item Faltando

```
⚠️ ASGArdian — Pré-requisito Detectado:

Para completar esta missão, você precisará do item: "Chave de Acesso Perdida".
Este item não foi encontrado no seu inventário.

Deseja saber onde encontrá-lo? (sim/nao):
```

**Se "sim":** o agente atualiza o contexto de busca e executa um novo ciclo completo de `fetch → process → generate → critique` focado em como obter o item, sem revelar o que acontece depois de obtê-lo.

**Se "nao":** o agente encerra informando que o progresso está bloqueado pelo item faltante.

---

## 🔄 Human-in-the-Loop (HITL)

Quando um pré-requisito está ausente no inventário, o grafo **pausa automaticamente** antes de iniciar a nova busca. O sistema aguarda confirmação explícita do usuário via `user_approval`.

O reuso dos nós de busca é controlado pela flag `is_item_search` no `AgentState`:
- `False` (padrão): fluxo normal, `verify_requirements_node` é executado
- `True`: segunda passagem, `verify_requirements_node` é ignorado para evitar loop infinito

### WebSocket em Tempo Real

O frontend se conecta via WebSocket para receber eventos de execução:

```javascript
// Frontend se conecta
ws = new WebSocket(`ws://localhost:8000/api/ws/${threadId}`);

// Envia payload
ws.send(JSON.stringify({ payload: {...} }));

// Recebe eventos
ws.onmessage = (event) => {
  const { type, data } = JSON.parse(event.data);
  
  // Types: execution_start, node_started, node_completed, 
  //        content_update, hitl_question, complete, error
};

// HITL: responde à pergunta
ws.send(JSON.stringify({ type: 'hitl_response', approval: 'sim' }));
```

---

---

## 🧪 Testando o Agente

### 1. Teste via Frontend (Recomendado)
1. Inicie backend: `python run.py`
2. Inicie frontend: `cd frontend && npm run dev`
3. Abra http://localhost:5174
4. Preencha o formulário:
   - **Jogo**: "Red Dead Redemption 2"
   - **Missão**: "Outlaws from the West"
   - **Problema**: "Dois caras em um cavalo me atacam depois que Abigail me salva do Mr. Milton. Como mato eles rápido?"
   - **Tipo de Ajuda**: Hint ou Answer
   - **Inventário**: deixe vazio (assume que tem tudo) ou adicione itens
5. Observe os eventos em tempo real

### 2. Teste via CLI (Python)
```python
from backend.main import run_agent

payload = {
    "game_name": "Red Dead Redemption 2",
    "mission_name": "Outlaws from the West",
    "current_issue": "Dois caras em um cavalo me atacam. Como mato eles?",
    "help_type": "hint",
    "player_inventory": []  # Vazio = assume que tem tudo
}

response = run_agent(payload)
print(response)
```

### 3. Teste via HTTP POST
```bash
curl -X POST http://localhost:8000/api/run-agent \
  -H "Content-Type: application/json" \
  -d '{
    "game_name": "Borderlands 2",
    "mission_name": "Lights Out",
    "current_issue": "Não consigo restaurar a energia",
    "help_type": "answer",
    "player_inventory": ["Shotgun"]
  }'
```

Você receberá um `thread_id` para se conectar via WebSocket:
```bash
ws://localhost:8000/api/ws/{thread_id}
```

---

Toda resposta passa por um nó de crítica independente (`critique_spoiler_node`) que garante:

- ❌ Nenhum desfecho de missão ou arco narrativo futuro
- ❌ Nenhuma morte ou aparição surpresa de personagem
- ❌ Nenhuma reviravolta da história posterior ao ponto atual do jogador
- ✅ Apenas mecânicas e elementos do cenário presente

O filtro se aplica **tanto** à resposta do problema original **quanto** à resposta sobre como obter o item faltante.

---

## 📁 Estrutura do Projeto

```
ASGArdian/
├── backend/
│   ├── main.py              # Ponto de entrada da aplicação
│   ├── graph/
│   │   ├── state.py         # Definição do AgentState (inclui is_item_search e original_issue)
│   │   ├── nodes.py         # Implementação dos 5 nós do grafo
│   │   └── workflow.py      # Montagem e compilação do StateGraph
│   ├── prompts/
│   │   └── templates.py     # Templates de prompts por nó
│   └── config.py            # Carregamento de variáveis de ambiente
├── frontend/                # Interface do usuário (a implementar)
├── docs/
│   └── prompts/
│       └── prompts.md       # Evolução e documentação dos prompts
├── steerings/               # Diretrizes do projeto (leitura da IA)
├── .env.example             # Modelo de variáveis de ambiente
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📚 Documentação de Prompts

A evolução dos prompts utilizados em cada nó do grafo está documentada em [`docs/prompts/prompts.md`](docs/prompts/prompts.md).

---

## 📄 Licença

Distribuído sob a licença MIT. Veja [`LICENSE`](LICENSE) para mais informações.
