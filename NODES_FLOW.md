# 🔄 Fluxo de Dados - Entrada e Saída de Cada Nó

## 🔍 NÓ 1: fetch_guide_node

### 📥 ENTRADA
```
game_name: "GTA V"
mission_name: "The Big Score"
current_issue: "Como abrir o cofre?"
is_item_search: False
player_inventory: ["Chave Mestra", "Explosivos"]
```

### 🔄 PROCESSO
1. Formata FETCH_GUIDE_PROMPT com os dados acima
2. Chama Groq com o prompt
3. Groq retorna informações sobre como resolver o problema
4. Resultado é armazenado em `raw_search_result`

### 📤 SAÍDA
```
raw_search_result: "~2400-2850 caracteres com informações do detonado"
```

---

## 📋 NÓ 2: process_guide_node

### 📥 ENTRADA
```
game_name: "GTA V"
current_issue: "Como abrir o cofre?"
raw_search_result: "~2400-2850 caracteres"
```

### 🔄 PROCESSO
1. Formata PROCESS_GUIDE_PROMPT com `raw_search_result`
2. Chama Groq para extrair estruturado (PREREQUISITOS, PASSOS, SPOILERS_FUTUROS)
3. Parse a resposta com regex:
   - PREREQUISITOS: "Chave Mestra, Explosivos"
   - PASSOS: "1. Vá para...\n2. Use a chave..."
   - SPOILERS_FUTUROS: "Um personagem importante morre nesta missão"

### 📤 SAÍDA
```
required_requirements: ["Chave Mestra", "Explosivos"]
generated_text: "1. Vá para...\n2. Use a chave..."
raw_search_result: (enriquecido com ---SPOILERS_FUTUROS--- no final)
```

---

## ✅ NÓ 3: verify_requirements_node

### 📥 ENTRADA
```
required_requirements: ["Chave Mestra", "Explosivos"]
player_inventory: ["Chave Mestra", "Explosivos"]
is_item_search: False
```

### 🔄 PROCESSO
1. Compara `required_requirements` com `player_inventory`
2. Formata VERIFY_REQUIREMENTS_PROMPT
3. Chama Groq para determinar se está faltando algum item
4. Parse resposta: "MISSING_ITEM: none" ou "MISSING_ITEM: Lança-Granadas"

### 📤 SAÍDA
```
missing_item: None    (se tudo ok)
   OU
missing_item: "Lança-Granadas"  (se faltar algo)
```

---

## 💭 NÓ 4: generate_help_node

### 📥 ENTRADA
```
game_name: "GTA V"
current_issue: "Como abrir o cofre?"
help_type: "hint"  (ou "answer")
generated_text: "1. Vá para...\n2. Use a chave..."  (steps)
critique_passed: False (se for reescrita) ou não definido (primeira vez)
```

### 🔄 PROCESSO
1. Se `critique_passed=False`: injeta feedback de que resposta anterior tinha spoilers
2. Seleciona template (GENERATE_HINT_PROMPT ou GENERATE_ANSWER_PROMPT)
3. Formata com dados acima
4. Chama Groq para gerar resposta final
5. Groq retorna uma dica ou resposta direta

### 📤 SAÍDA
```
generated_text: "Uma dica: procure por um painel com três cores diferentes..."
   OU
generated_text: "1. Localize o painel no sudeste\n2. Use a chave vermelha\n3. Aguarde 5 segundos"
```

---

## 🛡️  NÓ 5: critique_spoiler_node

### 📥 ENTRADA
```
generated_text: "Uma dica: procure por um painel..."
raw_search_result: (com ---SPOILERS_FUTUROS--- no final contendo spoilers)
```

### 🔄 PROCESSO
1. Extrai section de spoilers do `raw_search_result`
2. Se não há spoilers: aprovação automática ✅
3. Senão: formata CRITIQUE_SPOILER_PROMPT com:
   - future_spoilers: "Um personagem importante morre nesta missão"
   - generated_text: "Uma dica: procure por um painel..."
4. Chama Groq para verificar se há overlap
5. Parse resposta: "CRITIQUE_RESULT: PASSED" ou "CRITIQUE_RESULT: FAILED"

### 📤 SAÍDA
```
critique_passed: True
final_response: "Uma dica: procure por um painel..."
```

Se `critique_passed: False`, o fluxo volta ao nó 4 (generate_help_node) para reescrever.

---

## 🔀 ROTEADORES CONDICIONAIS

### Após process_guide_node:
- Se `is_item_search=True` → vai direto para generate_help_node
- Senão → vai para verify_requirements_node

### Após verify_requirements_node:
- Se `missing_item=None` → vai para generate_help_node
- Se `missing_item="algo"` → vai para fetch_guide_node (segunda busca)
- Se `user_approval="nao"` → encerra (fim)

### Após critique_spoiler_node:
- Se `critique_passed=True` → encerra com final_response ✅
- Se `critique_passed=False` → volta ao generate_help_node (reescrita)

---

## ⏱️  TEMPOS ESPERADOS

Com rate limiting de 2 segundos entre chamadas ao Groq:

- **fetch_guide_node**: ~4-5s (inclui delay + chamada)
- **process_guide_node**: ~3-4s
- **verify_requirements_node**: ~2-3s
- **generate_help_node**: ~2-3s
- **critique_spoiler_node**: ~2-3s

**TOTAL SEM REESCRITAS**: ~13-18 segundos

**COM REESCRITA (se critique falhar)**: +2-3s

