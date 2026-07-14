# 🎮 ASGArdian — Guia de Execução Manual

Este documento explica como executar o ASGArdian com exemplos de payload reais de **GTA V** e outros jogos.

---

## 📋 Pré-requisitos

1. **Python 3.10+** instalado
2. **Ambiente virtual ativado** (`.venv`)
3. **GOOGLE_API_KEY configurada** no `.env`
4. **Dependências instaladas**: `pip install -r requirements.txt`

---

## ⚡ Execução Rápida

### Opção 1: Com um dos Payloads Pré-configurados

```bash
python -c "
from backend.example_payload import payload_gta_v_hint
from backend.main import run_agent

result = run_agent(payload_gta_v_hint)
print('\n✅ Resposta Final:')
print(result)
"
```

### Opção 2: Importar e Usar um Payload Específico

```bash
python -c "
from backend.example_payload import payload_gta_v_answer, payload_gta_v_treasure
from backend.main import run_agent

# Executar com answer mode (solução direta)
result = run_agent(payload_gta_v_answer)

# Ou com treasure hunt
# result = run_agent(payload_gta_v_treasure)
"
```

### Opção 3: Criar um Payload Personalizado

```python
# arquivo: my_test.py
from backend.main import run_agent

payload = {
    "game_name": "Grand Theft Auto V",
    "mission_name": "Death Wish",
    "current_issue": (
        "Estou na missão final (Death Wish). Consegui chegar até o confronto com "
        "os três antagonistas, mas não consigo derrotá-los. Qual é a melhor estratégia?"
    ),
    "help_type": "answer",
    "player_inventory": ["Minigun", "RPG", "Combat Rifle", "Armor x5"],
}

result = run_agent(payload)
print(result)
```

Depois executar:

```bash
python my_test.py
```

---

## 🎯 Exemplos de Payloads Disponíveis

### 1. **GTA V — The Big Score (Hint Mode)**

```python
from backend.example_payload import payload_gta_v_hint
from backend.main import run_agent

# Jogador procura pista sutil para abrir o cofre
result = run_agent(payload_gta_v_hint)
```

**Contexto:** Jogador está na câmara de segurança do banco e não consegue abrir o cofre. O sistema fornecerá uma dica sutil (não a solução direta).

---

### 2. **GTA V — The Merryweather Heist (Answer Mode)**

```python
from backend.example_payload import payload_gta_v_answer
from backend.main import run_agent

# Jogador quer solução direta para derrotar soldados
result = run_agent(payload_gta_v_answer)
```

**Contexto:** Jogador está travado em um combate intenso e quer a resposta direta para vencer.

---

### 3. **GTA V — Treasure Hunt (Hint Mode)**

```python
from backend.example_payload import payload_gta_v_treasure
from backend.main import run_agent

# Jogador procura direções para encontrar moedas de ouro ocultas
result = run_agent(payload_gta_v_treasure)
```

**Contexto:** Side mission onde encontrar 50 moedas de ouro espalhadas por Los Santos. Sistema fornecerá dicas de onde procurar.

---

### 4. **GTA V — Street Race (Answer Mode)**

```python
from backend.example_payload import payload_gta_v_race
from backend.main import run_agent

# Jogador quer estratégia de corrida
result = run_agent(payload_gta_v_race)
```

**Contexto:** Jogador sempre perde na corrida e quer saber qual veículo e rota usar.

---

### 5. **Borderlands 2 — Lights Out (Hint Mode)**

```python
from backend.example_payload import payload_borderlands_2_hint
from backend.main import run_agent

result = run_agent(payload_borderlands_2_hint)
```

**Contexto:** Referência mantida do exemplo anterior. Jogador está na subestação.

---

## 🔄 Fluxo Com HITL (Human-in-the-Loop)

Se o sistema detectar que falta um item essencial, ele **pausará e perguntará ao usuário**:

```
⚠️  Pré-requisito detectado: 'Hacking Device' não encontrado no inventario.
   Deseja saber onde encontrar 'Hacking Device'? (sim/nao):
```

**Respondendo SIM:**
- O sistema fará uma nova busca: "como obter Hacking Device em Grand Theft Auto V"
- Fornecerá informações sobre onde encontrar o item
- Retomará o fluxo original com a dica/resposta

**Respondendo NÃO:**
- O sistema encerra com mensagem de bloqueio
- Jogador precisa obter o item fora do sistema

---

## 🧪 Executar a Suite de Testes E2E

Para validar o funcionamento completo com payloads de GTA V:

```bash
# Todos os testes E2E
pytest backend/tests/test_e2e.py -v

# Apenas testes de GTA V
pytest backend/tests/test_e2e.py::TestE2EGtaV -v

# Teste específico (hint mode)
pytest backend/tests/test_e2e.py::TestE2EGtaV::test_fluxo_completo_gta_v_hint_mockado -v

# Com output detalhado
pytest backend/tests/test_e2e.py -v -s
```

---

## 📊 Resultado Esperado

Ao executar com sucesso, você verá:

```
🛡️  ASGArdian iniciando busca para: Grand Theft Auto V — The Big Score
   Problema: Estou na fase do roubo do banco...
   Modo: Dica Sutil

[Sistema busca detonado real na internet]
[Processa informações estruturadas]
[Gera resposta sem spoilers]

🛡️  ASGArdian:

Pense no painel de controle — geralmente esses sistemas têm uma caixa de metal 
na parede. Você tem o Hacking Device? Se sim, procure por algo que brilhe ou 
pareça diferente nas paredes da câmara...
```

---

## 🛠️ Troubleshooting

### Erro: "GOOGLE_API_KEY não configurada"

**Solução:** Adicione a chave no arquivo `.env`:

```env
GOOGLE_API_KEY=sua_chave_aqui
```

### Erro: "Módulo backend não encontrado"

**Solução:** Certifique-se de estar na raiz do projeto e execute:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

(ou no Windows PowerShell):

```powershell
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)"
```

### Erro: "Timeout na API"

**Solução:** A API do Gemini pode estar lenta. Espere alguns segundos e tente novamente.

---

## 📚 Estrutura de Payloads

Todo payload **deve conter** 5 campos obrigatórios:

```python
{
    "game_name": str,              # Nome do jogo
    "mission_name": str,           # Nome da missão/localização
    "current_issue": str,          # Descrição do problema em texto livre
    "help_type": "hint" | "answer", # Tipo de ajuda desejada
    "player_inventory": List[str], # Itens que o jogador possui
}
```

---

## 🎬 Exemplo Completo

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exemplo_gta_v.py — Teste manual com GTA V
"""

from backend.example_payload import EXAMPLE_PAYLOADS
from backend.main import run_agent

def main():
    print("=" * 80)
    print("ASGArdian — Tester Manual (GTA V)")
    print("=" * 80)
    
    # Lista payloads disponíveis
    print("\nPayloads disponíveis:")
    for i, (key, payload) in enumerate(EXAMPLE_PAYLOADS.items(), 1):
        print(f"  {i}. {key}")
        print(f"     Jogo: {payload['game_name']}")
        print(f"     Missão: {payload['mission_name']}")
        print(f"     Tipo: {payload['help_type']}")
        print()
    
    # Escolhe um payload (default: gta_v_hint)
    choice = input("Escolha um payload (1-5, default=1): ").strip() or "1"
    
    try:
        idx = int(choice) - 1
        payload_name = list(EXAMPLE_PAYLOADS.keys())[idx]
        payload = EXAMPLE_PAYLOADS[payload_name]
    except (ValueError, IndexError):
        payload = EXAMPLE_PAYLOADS["gta_v_hint"]
    
    print(f"\n🎮 Executando: {payload_name}")
    print(f"   Jogo: {payload['game_name']}")
    print(f"   Missão: {payload['mission_name']}\n")
    
    try:
        result = run_agent(payload)
        print("\n" + "=" * 80)
        print("✅ Execução concluída com sucesso!")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        raise

if __name__ == "__main__":
    main()
```

Salve como `teste_manual.py` e execute:

```bash
python teste_manual.py
```

---

## 📞 Próximos Passos

- ✅ **Bloco 6 Completo:** Exemplos E2E com GTA V
- ⏳ **Bloco 7 (Opcional):** Frontend com FastAPI/Flask
- ⏳ **Deploy:** Docker, CI/CD, produção

---

**Divirta-se usando o ASGArdian! 🛡️✨**
