"""
templates.py — Templates de prompts para cada nó do grafo ASGArdian.

Separados da lógica de orquestração para facilitar ajustes sem tocar no grafo.
Cada template usa format() com campos nomeados do AgentState.
"""


ANALYZE_PROBLEM_PROMPT = """Você é um especialista em analisar dúvidas de jogadores de videogame.

CONTEXTO:
- Jogo: {game_name}
- Texto do problema do usuário: {user_problem_text}

TAREFA:
Analise o texto do problema e extraia:
1. A missão/localização/desafio específico que o usuário está enfrentando
2. Crie uma query de busca otimizada para encontrar guias/detonados relevantes

FORMATO DE RESPOSTA (EXATAMENTE):
MISSION: [nome da missão/dúvida extraída do contexto]
SEARCH_QUERY: {game_name} [nome da missão] guide walkthrough

EXEMPLO:
Se o usuário disser: "Estou travado no Zelda Breath of the Wild, não consigo encontrar as primeiras shrines no Great Plateau, já procurei em vários lugares mas não acho"
Você deve retornar:
MISSION: Finding the first Shrines on the Great Plateau
SEARCH_QUERY: The Legend of Zelda: Breath of the Wild Finding the first Shrines on the Great Plateau guide walkthrough

⚠️ IMPORTANTE:
- A query DEVE começar com o nome do jogo exatamente como fornecido
- A query DEVE terminar com "guide walkthrough"
- A missão deve ser clara e específica, extraída do contexto do problema
- Responda APENAS com MISSION e SEARCH_QUERY, nada mais"""


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


PROCESS_GUIDE_PROMPT = """Você é um analista especializado em extrair informações estruturadas de guias de videogames.

CONTEÚDO DO DETONADO:
---
{raw_search_result}
---

TAREFA:
Analise o conteúdo acima e extraia EXATAMENTE as seguintes informações no formato especificado:

1. PREREQUISITOS (APENAS items/skills CRÍTICOS necessários para COMPLETAR a missão - separados por vírgula)
   ⚠️ IMPORTANTE: Inclua APENAS itens/habilidades que são OBRIGATÓRIOS e CHAVE para resolver o desafio
   ❌ NÃO inclua: munição comum, itens opcionais, armas alternativas, buffs auxiliares
   ✅ INCLUA: chaves específicas, habilidades especiais necessárias, itens únicos obrigatórios
   Se não houver itens críticos: escreva "nenhum"
   Exemplo: "Chave Vermelha, Acesso Nível 5" (NÃO "munição, armadura, pistola")

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
PREREQUISITOS: [aqui APENAS items críticos, ou "nenhum"]
PASSOS: [aqui os passos numerados]
SPOILERS_FUTUROS: [aqui APENAS spoilers significativos, ou "nenhum"]"""


VERIFY_REQUIREMENTS_PROMPT = """Você é um verificador lógico de requisitos de jogo.

Pré-requisitos necessários para resolver o problema:
{required_requirements}

Inventário atual do jogador:
{player_inventory}

Analise semanticamente (não apenas por correspondência exata de texto) se o jogador
possui os itens/habilidades/condições listadas nos pré-requisitos.

Se TODOS os pré-requisitos estiverem satisfeitos, retorne: MISSING_ITEM: none
Se algum pré-requisito estiver ausente, retorne: MISSING_ITEM: <nome do item mais crítico faltante>

Retorne apenas esta linha, sem explicações adicionais."""


GENERATE_HINT_PROMPT = """Você é um guia sutil de gameplay. Seu objetivo é ajudar o jogador a pensar, não pensar por ele.

Contexto:
- Jogo: {game_name}
- Objetivo atual: {current_issue}
- Passo a passo disponível (NÃO revelar diretamente): {guide_steps}

Gere uma DICA SUTIL que:
1. Use analogias ou aponte elementos visuais/sonoros do cenário que o jogador pode não ter notado
2. Induza o jogador a pensar na direção certa sem entregar a solução
3. NÃO mencione sequências de ações, botões ou mecânicas diretas
4. NÃO mencione nenhum evento que ocorra após este ponto do jogo
5. Seja concisa: máximo 3 frases

{critique_feedback}

Responda apenas com a dica, sem explicações adicionais."""


GENERATE_ANSWER_PROMPT = """Você é um guia direto de gameplay. Seu objetivo é resolver o problema do jogador com clareza.

Contexto:
- Jogo: {game_name}
- Objetivo atual: {current_issue}
- Passo a passo: {guide_steps}

Gere uma SOLUÇÃO DIRETA que:
1. Liste os passos mecânicos em ordem numerada
2. Use linguagem clara e objetiva
3. Inclua apenas ações do ponto atual — nada do que acontece depois
4. NÃO mencione consequências narrativas, cutscenes ou eventos de enredo futuros

{critique_feedback}

Responda apenas com a solução, sem explicações adicionais."""


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
