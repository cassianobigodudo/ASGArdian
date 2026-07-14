# ASGArdian 🛡️
### Anti-Spoiler Gameplay Assistant

> Um agente inteligente baseado em grafos que guia jogadores travados sem arruinar a experiência com spoilers.

---

## 📌 O Problema

Jogadores frequentemente ficam presos em puzzles ou missões complexas. Ao buscar ajuda em detonados tradicionais, são inevitavelmente expostos a spoilers do enredo — mortes de personagens, reviravoltas, desfechos — que destroem a experiência do jogo.

## 💡 A Solução

O ASGArdian recebe o contexto exato onde o jogador está travado e fornece **apenas a dica necessária para aquele momento**, filtrando qualquer informação cronologicamente posterior no roteiro do jogo.

---

## 🏗️ Arquitetura do Agente

O coração da aplicação é um **StateGraph** do LangGraph com 6 nós e roteamento condicional:

```
[INPUT]
   │
   ▼
fetch_guide_node          → Gemini busca detonados em tempo real (Google Search nativa)
   │
   ▼
process_guide_node        → Extrai pré-requisitos, passo a passo e spoilers futuros
   │
   ▼
verify_requirements_node  → Compara inventário do jogador com requisitos necessários
   │
   ├── missing_item? ──► [HITL: interrupt_before] ──► guide_missing_item_node
   │                                                        │
   │                                                        ▼
   └── inventário ok? ──────────────────────────► generate_help_node
                                                        │
                                                        ▼
                                                 critique_spoiler_node
                                                        │
                                                 ├── passed? ──► [END]
                                                 └── failed? ──► generate_help_node (loop)
```

### Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.10+ |
| Orquestração | LangGraph (StateGraph) |
| LLM | Gemini 1.5 Flash |
| Busca Real-Time | Google Search (ferramenta nativa Gemini) |
| Framework LLM | LangChain + LangChain-Google-GenAI |
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
GOOGLE_API_KEY=sua_chave_do_gemini_aqui
```

> 🔑 Obtenha sua chave em: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## 🚀 Como Executar

```bash
python backend/main.py
```

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

---

## 🔄 Human-in-the-Loop (HITL)

Quando um pré-requisito está ausente no inventário, o grafo **pausa automaticamente** antes de revelar a localização do item. O sistema aguarda confirmação explícita do usuário:

- **`sim`** → O agente retoma o fluxo e gera o passo a passo para obter o item
- **`nao`** → O agente encerra informando que o progresso está bloqueado pelo item faltante

---

## 🔒 Regras Anti-Spoiler

Toda resposta passa por um nó de crítica independente (`critique_spoiler_node`) que garante:

- ❌ Nenhum desfecho de missão ou arco narrativo futuro
- ❌ Nenhuma morte ou aparição surpresa de personagem
- ❌ Nenhuma reviravolta da história posterior ao ponto atual do jogador
- ✅ Apenas mecânicas e elementos do cenário presente

---

## 📁 Estrutura do Projeto

```
ASGArdian/
├── backend/
│   ├── main.py              # Ponto de entrada da aplicação
│   ├── graph/
│   │   ├── state.py         # Definição do AgentState
│   │   ├── nodes.py         # Implementação dos 6 nós do grafo
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
