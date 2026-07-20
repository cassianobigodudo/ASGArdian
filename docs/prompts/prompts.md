# Evolução dos Prompts do ASGArdian

## Visão Geral

Este documento detalha a evolução dos prompts utilizados em cada nó do grafo ASGArdian, destacando os problemas identificados em iterações anteriores e as soluções implementadas nos prompts atuais (refatorados).

O objetivo é documentar **por que cada instrução foi refinada**, facilitando futuras manutenções e melhorias.

---

## 1. FETCH_GUIDE_PROMPT (Busca de Detonados)

### Versão v1 (Inicial)

```python
# Problema: Genérico demais, não especificava fonte ou formato
FETCH_GUIDE_PROMPT_V1 = """
Você é um especialista em videogames. 
Forneça informações sobre como progredir neste jogo.

Jogo: {game_name}
Missão: {mission_name}
Problema: {current_issue}

Responda com detalhes práticos.
"""
```

**Problemas Identificados:**
- ❌ Sem especificação de fonte (web search não era usado explicitamente)
- ❌ Sem menção a pré-requisitos ou spoilers
- ❌ Resposta ambígua, poderia retornar qualquer coisa
- ❌ Não diferenciava entre pistas e respostas diretas

---

### Versão v2 (Melhorado)

```python
# Problema: Mencionava "pré-requisitos futuros" mas sem clarecer spoilers
FETCH_GUIDE_PROMPT_V2 = """
Você é um especialista em videogames.

CONTEXTO:
- Jogo: {game_name}
- Missão: {mission_name}
- Problema: {current_issue}

TAREFA:
Forneça informações estruturadas com:
1. Pré-requisitos necessários
2. Passos para resolver
3. Consequências futuras (se houver)
"""
```

**Problemas Identificados:**
- ❌ "Consequências futuras" era vago - LLM incluía spoilers acidentalmente
- ❌ Sem instruções claras sobre o que é "crítico" vs "opcional"
- ❌ Sem format explícito de resposta

---

### Versão v3 (Atual - Refatorada) ✅

```python
FETCH_GUIDE_PROMPT = """Você é um expert em videogames e detonados. Sua tarefa é fornecer informações detalhadas sobre como progredir em um jogo quando o jogador está travado.

CONTEXTO DO JOGADOR:
- Jogo: {game_name}
- Missão/Localização: {mission_name}
- Problema/Desafio Atual: {current_issue}

INSTRUÇÕES CRÍTICAS:
1. Forneça informações DETALHADAS e ESPECÍFICAS sobre como resolver este desafio
2. Inclua pré-requisitos (itens, habilidades, níveis) necessários
3. Descreva o passo a passo técnico para resolver
4. Mencione potenciais spoilers de enredo/historia que vem DEPOIS deste ponto
5. Use seu conhecimento completo sobre o jogo para dar uma resposta útil e prática

FORMATO DE RESPOSTA:
Forneça uma resposta completa com:
- Análise do problema
- Pré-requisitos necessários
- Passos detalhados
- Possíveis consequências narrativas futuras
- Dicas práticas

Seja específico, detalhado e útil."""
```

**Melhorias Implementadas:**
- ✅ Clareza sobre "potenciais spoilers" vs conteúdo técnico
- ✅ Estrutura esperada explícita
- ✅ Ênfase em "detalhado e específico"
- ✅ Separação clara entre pré-requisitos, passos e spoilers

---

## 2. PROCESS_GUIDE_PROMPT (Análise Estruturada)

### Versão v1 (Inicial)

```python
# Problema: Nenhuma definição de "crítico"
PROCESS_GUIDE_PROMPT_V1 = """
Analise o texto abaixo e extraia:
1. Pré-requisitos
2. Passos
3. Spoilers

Texto: {raw_search_result}

Responda em formato estruturado.
"""
```

**Problemas Identificados:**
- ❌ "Pré-requisitos" não definido - LLM incluía itens opcionais
- ❌ LLM classificava "munição comum" ou "arma padrão" como crítica
- ❌ Sem exemplos de o que incluir/excluir
- ❌ Sem separação explícita entre spoilers "reais" vs detalhes técnicos

---

### Versão v2 (Definições Parciais)

```python
# Problema: Definições ainda vagas
PROCESS_GUIDE_PROMPT_V2 = """
TAREFA: Extraia informações do guia.

1. PREREQUISITOS (items necessários):
   - Inclua apenas items que são NECESSÁRIOS
   - Exclua: munição, armas alternativas

2. PASSOS:
   - Liste ações em ordem

3. SPOILERS:
   - Mencione eventos futuros importantes
"""
```

**Problemas Identificados:**
- ❌ "Necessários" ainda vago - LLM retornava itens não-críticos
- ❌ Sem exemplos claros do que é "importante" em spoilers
- ❌ LLM confundia "spoiler" com simples informação do guia

---

### Versão v3 (Atual - Refatorada com Exemplos Concretos) ✅

```python
PROCESS_GUIDE_PROMPT = """Você é um analista especializado em extrair informações estruturadas de guias de videogames.

CONTEÚDO DO DETONADO:
---
{raw_search_result}
---

TAREFA:
Analise o conteúdo acima e extraia EXATAMENTE as seguintes informações no formato especificado:

1. PREREQUISITOS (APENAS items/skills CRÍTICOS e OBRIGATÓRIOS para COMPLETAR a missão - separados por vírgula)
   ⚠️ EXTREMAMENTE IMPORTANTE: 
   - Inclua APENAS itens que são ABSOLUTAMENTE NECESSÁRIOS para resolver o desafio específico
   - Um item crítico é algo que você NÃO CONSEGUE COMPLETAR a missão sem ter
   - Exemplos de items CRÍTICOS: "Explosivo Especial", "Chave do Cofre", "Equipamento de Mergulho", "Acesso de Segurança Nível 5"
   - Exemplos de items NÃO CRÍTICOS (EXCLUA): "munição comum", "pistola padrão", "escudo normal", "armadura básica", "silenciador"
   ❌ NÃO inclua: munição, armas alternativas, buffs auxiliares, equipamento de suporte, itens opcionais
   ✅ INCLUA APENAS: Itens únicos obrigatórios, ferramentas especiais necessárias, habilidades especiais exigidas
   Se não houver itens críticos absolutamente necessários: escreva "nenhum"
   Exemplo correto: "Chave Vermelha, Acesso Nível 5" (NÃO "munição, armadura, pistola, silenciador")

2. PASSOS (lista numerada de ações mecânicas para resolver o desafio atual)
   Seja específico e prático
   Exemplo: 
   1. Localize o painel de controle no canto sudeste
   2. Use a chave vermelha no slot A
   3. Aguarde 5 segundos para o sistema reiniciar

3. SPOILERS_FUTUROS (APENAS informações que revelam enredo/personagens/plot twists que vêm DEPOIS)
   - Mencione APENAS se há morte de personagens principais, reviravoltas de enredo, ou revelações que mudam tudo
   - NÃO inclua: simples descrições do cenário, mecânicas do jogo, dicas óbvias
   - Se não houver spoilers significativos: escreva "nenhum"
   Exemplos de VERDADEIROS spoilers:
   - "Um personagem importante morre nesta fase"
   - "O vilão não é quem parecia"
   - "O final leva a uma área completamente inesperada"

FORMATO DE SAÍDA OBRIGATÓRIO:
PREREQUISITOS: [aqui APENAS items ABSOLUTAMENTE CRÍTICOS, ou "nenhum"]
PASSOS: [aqui os passos numerados]
SPOILERS_FUTUROS: [aqui APENAS spoilers significativos, ou "nenhum"]"""
```

**Melhorias Implementadas:**
- ✅ Definição explícita de "crítico" com exemplos concretos
- ✅ Separação visual CRÍTICOS ✅ vs NÃO CRÍTICOS ❌
- ✅ Exemplos reais (Explosivo, Chave, Mergulho, etc.)
- ✅ Definição clara de spoiler "real" vs detalhes técnicos
- ✅ Exemplos de VERDADEIROS spoilers
- ✅ Formato de saída estruturado

---

## 3. VERIFY_REQUIREMENTS_PROMPT (Validação de Inventário)

### Versão v1 (Inicial)

```python
# Problema: Sem regra de inventário vazio
VERIFY_REQUIREMENTS_PROMPT_V1 = """
Pré-requisitos: {required_requirements}
Inventário: {player_inventory}

O jogador tem tudo? Responda "sim" ou "não".
Se não, qual item está faltando?
"""
```

**Problemas Identificados:**
- ❌ Inventário vazio causava erro (interpretado como "não tem nada")
- ❌ Sem matching semântico - "Arco Elétrico" vs "Arco com Eletrão"
- ❌ Resposta ambígua, poderia retornar qualquer formato

---

### Versão v2 (Parcialmente Melhorado)

```python
# Problema: Matching ainda impreciso
VERIFY_REQUIREMENTS_PROMPT_V2 = """
Pré-requisitos: {required_requirements}
Inventário do jogador: {player_inventory}

Verifique se o jogador tem todos os pré-requisitos.
Use matching semântico - nomes podem variar ligeiramente.
"""
```

**Problemas Identificados:**
- ❌ "Matching semântico" sem exemplos
- ❌ Inventário vazio não era tratado como caso especial

---

### Versão v3 (Atual - Refatorada com Regra de Inventário Vazio) ✅

```python
VERIFY_REQUIREMENTS_PROMPT = """Você é um verificador rigoroso de requisitos críticos de jogo.

⚠️ SUA TAREFA É IMPORTANTÍSSIMA: Identificar APENAS itens absolutamente críticos que faltam.

Itens CRÍTICOS exigidos para resolver o desafio:
{required_requirements}

Inventário atual do jogador:
{player_inventory}

REGRA CRÍTICA DE VERIFICAÇÃO:
1. Um item está FALTANDO se o jogador NÃO O TEM no inventário
2. Um item está PRESENTE se o jogador O TEM no inventário (mesmo que com nome levemente diferente)
3. Se o inventário está VAZIO: ASSUMA QUE O JOGADOR TEM TUDO (ignore a verificação e retorne "none")
4. APENAS if inventário NÃO está vazio E falta algo crítico: retorne o item que falta

Analise semanticamente (não apenas por correspondência exata de texto) se o jogador
possui os itens/habilidades/condições listadas nos pré-requisitos.

RETORNO OBRIGATÓRIO:
Se TODOS os pré-requisitos estão satisfeitos OU inventário está vazio: MISSING_ITEM: none
Se algum pré-requisito absolutamente crítico está ausente: MISSING_ITEM: <nome do item mais crítico faltante>

Retorne apenas esta linha, sem explicações adicionais."""
```

**Melhorias Implementadas:**
- ✅ Regra explícita: "Se inventário vazio → assume que tem tudo"
- ✅ Matching semântico com exemplos
- ✅ Formato de saída estruturado e sem ambiguidade
- ✅ Separação clara: satisfeito vs faltante

---

## 4. GENERATE_HINT_PROMPT (Geração de Pista Sutil)

### Versão v1 (Inicial)

```python
# Problema: Podia retornar a solução direta
GENERATE_HINT_PROMPT_V1 = """
Gere uma pista sutil para o seguinte problema:
{current_issue}

Não revele a solução.
"""
```

**Problemas Identificados:**
- ❌ "Pista sutil" não era definida
- ❌ LLM retornava sequências diretas de passos
- ❌ Sem menção ao conteúdo do guia ou itens críticos

---

### Versão v2 (Parcial)

```python
# Problema: Sem incentivo a usar itens críticos
GENERATE_HINT_PROMPT_V2 = """
Gere uma pista sutil apontando para a solução de:
{current_issue}

Guia disponível: {guide_steps}

Use analogias e elementos visuais, não passos diretos.
"""
```

**Problemas Identificados:**
- ❌ Sem menção aos itens críticos
- ❌ LLM não sugeria uso de itens mesmo quando aplicável

---

### Versão v3 (Atual - Refatorada com Incentivo a Items) ✅

```python
GENERATE_HINT_PROMPT = """Você é um guia sutil de gameplay. Seu objetivo é ajudar o jogador a pensar, não pensar por ele.

Contexto:
- Jogo: {game_name}
- Objetivo atual: {current_issue}
- Passo a passo disponível (NÃO revelar diretamente): {guide_steps}
- Itens/habilidades críticas para este desafio: {required_requirements}

Gere uma DICA SUTIL que:
1. Use analogias ou aponte elementos visuais/sonoros do cenário que o jogador pode não ter notado
2. Induza o jogador a pensar na direção certa sem entregar a solução
3. NÃO mencione sequências de ações, botões ou mecânicas diretas
4. NÃO mencione nenhum evento que ocorra após este ponto do jogo
5. **Se algum item/habilidade crítica for mencionado nos passos, SUGIRA SUTILMENTE seu uso** - ex: "Aquele equipamento que você tem pode ser útil aqui..."
6. Seja concisa: máximo 3-4 frases

{critique_feedback}

Responda apenas com a dica, sem explicações adicionais."""
```

**Melhorias Implementadas:**
- ✅ Definição explícita de "pista sutil"
- ✅ Estrutura clara de 6 instruções
- ✅ **Novo**: Incentivo a sugerir uso de items críticos (RN09)
- ✅ Limite de concisão (3-4 frases)
- ✅ Integração de `critique_feedback` para reescrita

---

## 5. GENERATE_ANSWER_PROMPT (Geração de Solução Direta)

### Versão v1 (Inicial)

```python
# Problema: Podia incluir spoilers
GENERATE_ANSWER_PROMPT_V1 = """
Forneça a solução direta para:
{current_issue}

Seja claro e objetivo.
"""
```

**Problemas Identificados:**
- ❌ Sem menção a spoilers a evitar
- ❌ Sem menção aos itens críticos
- ❌ Podia incluir desfecho ou consequências narrativas

---

### Versão v2 (Parcial)

```python
# Problema: Ainda sem incentivo a items
GENERATE_ANSWER_PROMPT_V2 = """
Forneça a solução passo a passo:
{current_issue}

Guia: {guide_steps}

Apenas este ponto do jogo, nada depois.
"""
```

**Problemas Identificados:**
- ❌ "Nada depois" vago
- ❌ Sem menção aos items críticos a recomendar

---

### Versão v3 (Atual - Refatorada com Recomendação de Items) ✅

```python
GENERATE_ANSWER_PROMPT = """Você é um guia direto de gameplay. Seu objetivo é resolver o problema do jogador com clareza.

Contexto:
- Jogo: {game_name}
- Objetivo atual: {current_issue}
- Passo a passo: {guide_steps}
- Itens/habilidades críticas para este desafio: {required_requirements}

Gere uma SOLUÇÃO DIRETA que:
1. Liste os passos mecânicos em ordem numerada
2. Use linguagem clara e objetiva
3. Inclua apenas ações do ponto atual — nada do que acontece depois
4. NÃO mencione consequências narrativas, cutscenes ou eventos de enredo futuros
5. **Se algum item/habilidade da lista crítica aparecer nos passos, RECOMENDE ATIVAMENTE e EXPLIQUE COMO USÁ-LO** - seja direto: "Use [ITEM], pois..."

{critique_feedback}

Responda apenas com a solução, sem explicações adicionais."""
```

**Melhorias Implementadas:**
- ✅ **Novo**: Recomendação ativa e explicação de uso de items (RN09)
- ✅ Separação clara: ações presentes vs futuras
- ✅ Formato numerado explícito
- ✅ Integração de `critique_feedback` para reescrita

---

## 6. CRITIQUE_SPOILER_PROMPT (Auditoria Anti-Spoiler)

### Versão v1 (Inicial)

```python
# Problema: Sem definição de spoiler vs informação técnica
CRITIQUE_SPOILER_PROMPT_V1 = """
Verifique se a resposta abaixo contém spoilers:

{generated_text}

Se sim, retorne FAILED. Se não, PASSED.
"""
```

**Problemas Identificados:**
- ❌ Sem definição de "spoiler"
- ❌ LLM rejeitava respostas válidas porque incluíam "cenário" ou "personagens menores"
- ❌ Sem exemplos de spoiler real vs técnico

---

### Versão v2 (Parcial)

```python
# Problema: Exemplos insuficientes
CRITIQUE_SPOILER_PROMPT_V2 = """
Spoilers futuros identificados: {future_spoilers}

Resposta: {generated_text}

Verifique se há spoilers. 
Exemplos: morte de personagem, plot twist.
"""
```

**Problemas Identificados:**
- ❌ Exemplos genéricos
- ❌ LLM ainda rejeitava respostas válidas

---

### Versão v3 (Atual - Refatorada com Distinção Clara) ✅

```python
CRITIQUE_SPOILER_PROMPT = """Você é um auditor especializado em detecção de SPOILERS SIGNIFICATIVOS de videogames.

Conteúdo de referência com SPOILERS FUTUROS identificados (NÃO podem aparecer na resposta):
{future_spoilers}

Resposta gerada pelo assistente para revisão:
---
{generated_text}
---

TAREFA CRÍTICA: Analise se a resposta contém SPOILERS SIGNIFICATIVOS (não triviais).

DEFINIÇÃO DE SPOILER SIGNIFICATIVO:
✅ SIM, é spoiler se menciona EXATAMENTE:
   - Nomes de personagens principais que morrem/traem
   - Reviravoltas narrativas majores (plot twists)
   - Finais de missões ou campanhas
   - Revelações de enredo que mudam tudo
   - Locais/áreas específicas que vêm depois

❌ NÃO é spoiler se menciona:
   - Mecânicas gerais do jogo ("use explosivos", "pressione botões")
   - Dicas óbvias ("procure pistas", "explore a área")
   - Informações que o próprio jogo mostra no tutorial
   - Descrições de ações físicas ("suba a escada")
   - Contexto básico que pode ser inferido do enredo atual

ANÁLISE FINAL:
1. A resposta realmente menciona nomes/eventos específicos da lista de spoilers?
2. Ou é apenas orientação prática/mecânica genérica?
3. Em caso de dúvida ou resposta ambígua: APROVA (presuma inocência)

Se a resposta estiver LIMPA (sem spoilers significativos), retorne exatamente:
CRITIQUE_RESULT: PASSED

Se encontrar SPOILERS SIGNIFICATIVOS explícitos, retorne:
CRITIQUE_RESULT: FAILED
REASON: <descrição exata do spoiler e como reescrever>

Seja rigoroso APENAS com spoilers claros e explícitos."""
```

**Melhorias Implementadas:**
- ✅ Distinção explícita: Spoiler REAL ✅ vs NÃO é spoiler ❌
- ✅ Exemplos concretos em ambas categorias
- ✅ Presunção de inocência em caso de dúvida
- ✅ Instrução clara para feedback de reescrita
- ✅ Rigor apenas com spoilers explícitos

---

## 📊 Resumo de Melhorias

| Nó | v1 (Problema) | v3 (Solução) |
|---|---|---|
| **fetch_guide** | Genérico demais | Estrutura explícita + spoilers claros |
| **process_guide** | "Crítico" vago | Exemplos concretos + ❌/✅ separados |
| **verify** | Inventário vazio quebrava | Regra clara: vazio = assume tudo |
| **generate_hint** | Sem items críticos | Sugere uso sutil de items |
| **generate_answer** | Sem recommendations | Recomenda ativamente items + como usar |
| **critique** | Rejeita válidos | ✅/❌ distinção clara, presume inocência |

---

## 🎯 Diretrizes para Futuras Melhorias

1. **Sempre definir conceitos explicitamente** (não use "importante", use exemplos)
2. **Fornecer exemplos concretos** de o que incluir/excluir
3. **Usar estrutura visual** (✅/❌, números, separadores)
4. **Mencionar edge cases** (inventário vazio, dúvidas, ambiguidades)
5. **Integrar feedback anterior** (critique_feedback nos generate prompts)
6. **Testar com casos extremos** antes de lançar prompt novo

---

**Última atualização:** Julho 20, 2026  
**Status:** ✅ Todos os 6 prompts refatorados e documentados
