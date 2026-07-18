# 🔒 Proteção Contra Loops Infinitos

## ⚠️ Problema Identificado
O servidor estava ficando em loop infinito, possivelmente causado por:
- Roteadores condicionais retornando ao mesmo nó múltiplas vezes
- Retries infinitos do Groq (429 Too Many Requests)
- Cliente WebSocket desconectando enquanto grafo ainda executava

## ✅ Soluções Implementadas

### 1️⃣ **Limites por Nó** (no `backend/graph/nodes.py`)

Cada nó agora verifica no início se foi executado muitas vezes:
```python
_max_node_executions = 5  # Máximo de vezes que um nó pode rodar
```

**Nós protegidos:**
- `fetch_guide_node` - máx 5 execuções
- `process_guide_node` - máx 5 execuções  
- `verify_requirements_node` - máx 5 execuções
- `generate_help_node` - máx 5 execuções (reescritas de critique)
- `critique_spoiler_node` - máx 5 execuções

**Erro lançado:**
```
🔄 LOOP DETECTADO: fetch_guide_node foi executado 5+ vezes
```

### 2️⃣ **Timeout Total de Execução** (no `backend/api.py`)

```python
max_execution_time = 300  # 5 minutos máximo total
max_iterations = 10       # Máximo de invocações do grafo
```

**Checks:**
- Após `graph_app.invoke()` completa, verifica se excedeu tempo
- Se sim, envia erro e desconecta WebSocket
- Cliente recebe: `"Timeout: execução excedeu 300s"`

### 3️⃣ **Proteção por Iteração** (no `backend/api.py`)

```python
iteration_count = 0
max_iterations = 10  # Máximo de vezes que graph_app.invoke() é chamado

if iteration_count > max_iterations:
    # Para a execução
    await manager.send_event(thread_id, "error", {
        "message": f"Loop infinito detectado após {max_iterations} iterações"
    })
```

---

## 📊 Limites em Ação

### Cenário 1: Reescritas Normais (Esperado)
```
✅ generate_help_node (iteração 1) → resposta com spoilers
✅ critique_spoiler_node (iteração 1) → FAILED
✅ generate_help_node (iteração 2) → resposta sem spoilers
✅ critique_spoiler_node (iteração 2) → PASSED
✅ Execução completa (~20 segundos)
```

### Cenário 2: Loop Detectado (Proteção Ativa)
```
✅ fetch_guide_node (iteração 1)
✅ verify_requirements_node (iteração 1) → missing_item detected
✅ fetch_guide_node (iteração 2) → busca pelo item
✅ verify_requirements_node (iteração 2) → ainda falta
✅ fetch_guide_node (iteração 3) → busca novamente
✅ verify_requirements_node (iteração 3) → ainda falta
✅ fetch_guide_node (iteração 4) → busca novamente
✅ verify_requirements_node (iteração 4) → ainda falta
✅ fetch_guide_node (iteração 5) → busca novamente
❌ verify_requirements_node (iteração 5) → LOOP DETECTADO!
🔴 Erro: "🔄 LOOP DETECTADO: verify_requirements_node foi executado 5+ vezes"
```

---

## 🎯 Comportamento Esperado

### Se tudo funcionar bem:
1. Execução completa em 15-20 segundos
2. Todos os 5 nós executam 1-2 vezes cada
3. Cliente recebe `complete` event com resposta final

### Se houver loop:
1. Após 5+ execuções do mesmo nó → erro capturado
2. Mensagem de erro enviada ao cliente
3. WebSocket desconectado
4. Servidor continua rodando (não trava)

### Se timeout:
1. Após 300 segundos (5 minutos) → erro capturado
2. Mensagem de timeout enviada ao cliente
3. WebSocket desconectado
4. Servidor continua rodando

---

## 🔍 Como Monitorar

### No backend logs:
```
[Backend] 🚀 Invocando graph_app...
[Backend] ✅ Grafo executado em 18.5s (iteração 1)
[Backend] 🎉 TODAS AS VALIDAÇÕES PASSARAM!
```

### Ou se houver erro:
```
[Backend] ❌ LOOP INFINITO: Grafo executou 5+ vezes
[Backend] 🔄 LOOP DETECTADO: fetch_guide_node foi executado 5+ vezes
[Backend] ⏱️ TIMEOUT TOTAL: Execução excedeu 300s
```

---

## 📝 Resumo das Proteções

| Proteção | Limite | Ação |
|----------|--------|------|
| Nó por nó | 5x execução | Lança exceção |
| Iterações | 10x invoke() | Envia erro ao cliente |
| Tempo total | 300s (5 min) | Envia erro ao cliente |
| Rate limit | 2s entre chamadas | Aguarda antes de chamar |

Agora o servidor é resiliente contra loops infinitos! 🛡️

