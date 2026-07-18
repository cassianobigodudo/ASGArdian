"""
nodes.py — Implementação dos 5 nós do grafo ASGArdian.

Cada função recebe o AgentState completo e retorna um dicionário
com apenas os campos que foram modificados naquele nó.

Nós implementados:
1. fetch_guide_node      — busca detonados via Groq (ou Gemini)
2. process_guide_node    — extrai requisitos, passos e spoilers do resultado bruto
3. verify_requirements_node — compara inventário com requisitos (ignora se is_item_search=True)
4. generate_help_node    — gera hint ou answer com base no help_type
5. critique_spoiler_node — audita a resposta contra spoilers futuros
"""

import re
import logging
import time
import signal
import requests
from typing import Any, Dict
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from groq import Groq

from backend.config import PROVIDER, API_KEY, MODEL
from backend.errors import (
    APIConnectionError,
    EmptySearchResultError,
    GuideProcessingError,
)
from backend.graph.state import AgentState
from backend.prompts.templates import (
    ANALYZE_PROBLEM_PROMPT,
    FETCH_GUIDE_PROMPT,
    PROCESS_GUIDE_PROMPT,
    VERIFY_REQUIREMENTS_PROMPT,
    GENERATE_HINT_PROMPT,
    GENERATE_ANSWER_PROMPT,
    CRITIQUE_SPOILER_PROMPT,
)

# ---------------------------------------------------------------------------
# Logger do modulo
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# Rate limiting para respeitar limite do Groq
_last_llm_call_time = 0
_min_delay_between_calls = 2.0  # 2 segundos entre chamadas (aumentado para respeitar rate limit do Groq)

# Proteção contra loops infinitos
_node_execution_count = {}
_max_node_executions = 5  # Máximo de vezes que um nó pode ser executado
_total_execution_time_start = None
_max_total_execution_time = 300  # 5 minutos máximo

def _search_web(query: str, num_results: int = 5) -> list:
    """
    Busca na web usando DuckDuckGo e retorna resultados com conteúdo.
    
    Filtra e prioriza sites de guias/wikis, ignora vendas e anúncios.
    
    Args:
        query: Termo de busca
        num_results: Número de resultados a buscar
    
    Returns:
        Lista de dicionários com {title, link, snippet, content}
    """
    print(f"\n🌐 WEB SEARCH INICIADO")
    print(f"   Query: {query}")
    
    # Domínios PREFERIDOS (guias, wikis, tutoriais)
    PREFERRED_DOMAINS = [
        'ign.com', 'gamefaqs.com', 'fandom.com', 'wiki.', 'reddit.com/r/',
        'youtube.com', 'twitch.tv', 'guides.co', 'polygon.com',
        'venturebeat.com', 'metacritic.com', 'gamerguides.com'
    ]
    
    # Domínios IGNORADOS (vendas, anúncios, lojas)
    BLOCKED_DOMAINS = [
        'rockstargames.com', 'store.', 'shop', 'ebay.', 'amazon.',
        'grancursosonline.com', 'udemy.', 'coursera.', 'skillshare.',
        'marriott.', 'booking.', 'airbnb.', 'hotels.', 'trivago.',
        'aliexpress.', 'mercadolivre.', 'olx.', 'classifieds.',
        'ads.', 'advertising.', 'banner.', '.ad', 'promoted.'
    ]
    
    try:
        results = []
        ddgs = DDGS()
        
        print(f"   Buscando {num_results * 3} resultados (com filtro)...")
        
        # Busca com DuckDuckGo - pede mais para poder filtrar
        search_results = list(ddgs.text(query, max_results=num_results * 3))
        
        if not search_results:
            print(f"   ⚠️ Nenhum resultado encontrado")
            return []
        
        print(f"   ✅ Encontrados {len(search_results)} resultados (antes de filtro)")
        
        # Filtra e prioriza resultados
        filtered_results = []
        preferred_results = []
        
        for result in search_results:
            link = result.get('href', '').lower()
            
            # Verifica se está bloqueado
            if any(blocked in link for blocked in BLOCKED_DOMAINS):
                print(f"   ⛔ BLOQUEADO: {link[:60]}")
                continue
            
            # Verifica se é preferido
            is_preferred = any(preferred in link for preferred in PREFERRED_DOMAINS)
            
            if is_preferred:
                preferred_results.append(result)
            else:
                filtered_results.append(result)
        
        # Prioriza resultados preferidos
        final_results = preferred_results + filtered_results
        print(f"   ✅ Após filtro: {len(final_results)} resultados ({len(preferred_results)} preferidos)")
        
        # Processa cada resultado até ter num_results válidos
        for i, result in enumerate(final_results[:num_results * 2]):
            if len(results) >= num_results:
                break
                
            try:
                title = result.get('title', '')
                link = result.get('href', '')
                snippet = result.get('body', '')
                
                print(f"\n   📄 Resultado {len(results)+1}: {title[:60]}...")
                print(f"      URL: {link}")
                
                # Tenta buscar conteúdo completo da página
                content = ""
                if link:
                    try:
                        print(f"      Buscando conteúdo completo...")
                        response = requests.get(link, timeout=5, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            # Remove scripts e styles
                            for script in soup(["script", "style"]):
                                script.decompose()
                            content = soup.get_text(separator=' ', strip=True)[:2000]  # Limita a 2000 chars
                            print(f"      ✅ Conteúdo extraído ({len(content)} chars)")
                    except Exception as e:
                        print(f"      ⚠️ Erro ao buscar conteúdo: {str(e)[:50]}")
                        content = snippet
                
                results.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet,
                    'content': content or snippet
                })
                
            except Exception as e:
                print(f"      ❌ Erro ao processar resultado: {e}")
                continue
        
        print(f"\n   🎉 Total de {len(results)} resultados processados")
        return results
        
    except Exception as e:
        print(f"   ❌ Erro na busca web: {e}")
        logger.error(f"Erro na busca web: {e}")
        return []

def _check_execution_limits(node_name: str):
    """Verifica se atingiu limites de execução para evitar loops infinitos."""
    global _node_execution_count, _total_execution_time_start
    
    if _total_execution_time_start is None:
        _total_execution_time_start = time.time()
    
    # Verifica tempo total de execução
    elapsed_total = time.time() - _total_execution_time_start
    if elapsed_total > _max_total_execution_time:
        raise Exception(f"⏱️ TIMEOUT TOTAL: Execução excedeu {_max_total_execution_time}s")
    
    # Verifica execução por nó
    _node_execution_count[node_name] = _node_execution_count.get(node_name, 0) + 1
    if _node_execution_count[node_name] > _max_node_executions:
        raise Exception(f"🔄 LOOP DETECTADO: {node_name} foi executado {_max_node_executions}+ vezes")

def _wait_for_rate_limit():
    """Aguarda o tempo mínimo entre chamadas ao LLM para respeitar rate limit."""
    global _last_llm_call_time
    elapsed = time.time() - _last_llm_call_time
    if elapsed < _min_delay_between_calls:
        delay = _min_delay_between_calls - elapsed
        print(f"⏳ Rate limit: aguardando {delay:.1f}s antes da próxima chamada...")
        time.sleep(delay)

# ---------------------------------------------------------------------------
# Factory de LLM baseado no provedor configurado
# ---------------------------------------------------------------------------

def _invoke_llm(prompt: str) -> str:
    """
    Invoca o LLM (Groq ou Gemini) e retorna a resposta em texto.
    Unifica a interface para ambos os provedores.
    Respeita rate limit com delay entre chamadas.
    """
    global _last_llm_call_time
    
    # Aguarda rate limit
    _wait_for_rate_limit()
    
    print(f"\n📡 _INVOKE_LLM INICIADO")
    print(f"   Provider: {PROVIDER}")
    print(f"   Model: {MODEL}")
    print(f"   Prompt length: {len(prompt)} chars")
    
    if PROVIDER == "groq":
        try:
            print(f"   Chamando Groq...")
            logger.debug(f"📤 Chamando Groq com modelo: {MODEL}")
            logger.debug(f"📤 Prompt (primeiros 200 chars): {prompt[:200]}...")
            
            client = Groq(api_key=API_KEY)
            message = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL,
                temperature=0.7,
            )
            
            result = message.choices[0].message.content
            _last_llm_call_time = time.time()  # Registra hora da chamada
            
            print(f"   ✅ Groq retornou: {len(result)} chars")
            logger.debug(f"📥 Resposta recebida do Groq ({len(result)} chars)")
            logger.debug(f"📥 Resposta (primeiros 200 chars): {result[:200]}...")
            
            return result
        except Exception as e:
            print(f"   ❌ Erro Groq: {e}")
            logger.error(f"❌ Erro ao usar Groq: {e}")
            logger.error(f"❌ Tipo de erro: {type(e).__name__}")
            raise APIConnectionError(f"Falha ao invocar Groq: {e}") from e
    else:
        try:
            print(f"   Chamando Gemini...")
            logger.debug(f"📤 Chamando Gemini com modelo: {MODEL}")
            logger.debug(f"📤 Prompt (primeiros 200 chars): {prompt[:200]}...")
            
            llm = ChatGoogleGenerativeAI(
                model=MODEL,
                google_api_key=API_KEY,
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            
            result = response.content if hasattr(response, "content") else str(response)
            _last_llm_call_time = time.time()  # Registra hora da chamada
            
            print(f"   ✅ Gemini retornou: {len(result)} chars")
            logger.debug(f"📥 Resposta recebida do Gemini ({len(result)} chars)")
            logger.debug(f"📥 Resposta (primeiros 200 chars): {result[:200]}...")
            
            return result
        except Exception as e:
            print(f"   ❌ Erro Gemini: {e}")
            logger.error(f"❌ Erro ao usar Gemini: {e}")
            logger.error(f"❌ Tipo de erro: {type(e).__name__}")
            raise APIConnectionError(f"Falha ao invocar Gemini: {e}") from e


# ---------------------------------------------------------------------------
# Nó 0: analyze_problem_node (NOVO - PRIMEIRO NÓ)
# ---------------------------------------------------------------------------

def analyze_problem_node(state: AgentState) -> Dict[str, Any]:
    """
    Você é um agente especializado em jogos e em formatação de texto para buscas de detonados em jogos
    Analisa o texto completo do problema fornecido pelo usuário.
    
    REGRAS:PRIORIZA o mission_name fornecido como base para a análise.
    a query SEMPRE tem que ser a mesma que está formatada, não pesquise nada além do formato da query fornecida
    
    Extrai:
    - A missão (sempre usa mission_name fornecido)
    - Sempre executar essa query para busca: "[game] [mission] guide walkthrough"
    - Preserva o contexto original para comparação posterior
    
    Retorna: analyzed_mission e search_query preenchidos.
    """
    # Verifica limites de execução
    _check_execution_limits("analyze_problem_node")
    
    print(f"\n{'='*80}")
    print(f"🔎 NÓ 0: ANALYZE_PROBLEM_NODE (NOVO)")
    print(f"{'='*80}")
    print(f"📥 INPUT DO NÓ:")
    print(f"   game_name: {state['game_name']}")
    print(f"   mission_name: {state['mission_name']}")
    print(f"   user_problem_text: {state.get('user_problem_text', '')[:100]}...")
    
    logger.debug(f"🔎 analyze_problem_node iniciado")
    logger.debug(f"   - game_name: {state['game_name']}")
    logger.debug(f"   - mission_name: {state['mission_name']}")
    logger.debug(f"   - user_problem_text length: {len(state.get('user_problem_text', ''))}")
    
    user_problem = state.get("user_problem_text", state.get("current_issue", ""))
    mission_name = state.get("mission_name", "Unknown Mission")
    
    if not user_problem or not user_problem.strip():
        print(f"   ⚠️ Nenhum texto de problema fornecido, usando mission_name como base")
        analyzed_mission = mission_name
        search_query = f"{state['game_name']} {mission_name} guide walkthrough"
    else:
        prompt = ANALYZE_PROBLEM_PROMPT.format(
            game_name=state["game_name"],
            mission_name=mission_name,
            user_problem_text=user_problem,
        )
        
        print(f"   Analisando problema com LLM (priorizando mission_name)...")
        
        try:
            response = _invoke_llm(prompt)
            print(f"   ✅ LLM retornou: {len(response)} caracteres")
            logger.debug(f"✅ analyze_problem_node: LLM retornou {len(response)} caracteres")
        except Exception as exc:
            print(f"   ❌ ERRO: {exc}")
            logger.error(f"❌ analyze_problem_node: falha na chamada ao LLM: {exc}")
            raise APIConnectionError(
                f"Falha ao analisar problema. Detalhe: {exc}"
            ) from exc
        
        # Extrai MISSION - PRIORIZA mission_name fornecido
        mission_match = re.search(r"MISSION:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        analyzed_mission_raw = mission_match.group(1).strip() if mission_match else mission_name
        
        # Se a LLM retornou algo diferente, usa o fornecido (prioriza)
        # Mas se retornou o mesmo ou similar, mantém
        if analyzed_mission_raw.lower() != mission_name.lower():
            print(f"   ℹ️ LLM sugeriu diferente, mantendo mission_name fornecido")
            analyzed_mission = mission_name
        else:
            analyzed_mission = analyzed_mission_raw
        
        # Extrai SEARCH_QUERY
        query_match = re.search(r"SEARCH_QUERY:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        search_query = query_match.group(1).strip() if query_match else f"{state['game_name']} {mission_name} guide walkthrough"
        
        print(f"\n   📋 EXTRAÇÃO:")
        print(f"   Mission (prioritizada): {analyzed_mission}")
        print(f"   Search Query: {search_query}")
    
    print(f"\n📤 OUTPUT DO NÓ:")
    print(f"   analyzed_mission: {analyzed_mission}")
    print(f"   search_query: {search_query}")
    print(f"{'='*80}\n")
    
    return {
        "analyzed_mission": analyzed_mission,
        "search_query": search_query,
        "mission_name": analyzed_mission,  # Atualiza mission_name com a análise (mas priorizando o fornecido)
    }


# ---------------------------------------------------------------------------

def fetch_guide_node(state: AgentState) -> Dict[str, Any]:
    """
    Busca detonados NA WEB usando DuckDuckGo com query simples.
    
    Query gerada automaticamente: "[game_name] [mission_name] guide walkthrough"
    Sem análise de problema - direto para a busca.

    Retorna: raw_search_result populado com conteúdo sintetizado + links em ---FONTES---.
    """
    # Verifica limites de execução
    _check_execution_limits("fetch_guide_node")
    
    print(f"\n{'='*80}")
    print(f"🔍 NÓ 1: FETCH_GUIDE_NODE (WEB SEARCH)")
    print(f"{'='*80}")
    print(f"📥 INPUT DO NÓ:")
    print(f"   game_name: {state['game_name']}")
    print(f"   mission_name: {state['mission_name']}")
    print(f"   current_issue: {state['current_issue']}")
    print(f"   is_item_search: {state.get('is_item_search', False)}")
    
    logger.debug(f"🔍 fetch_guide_node iniciado (WEB SEARCH)")
    logger.debug(f"   - game_name: {state['game_name']}")
    logger.debug(f"   - mission_name: {state['mission_name']}")
    
    # ETAPA 1: Gera search_query automática
    print(f"\n📡 ETAPA 1: GERACAO DE SEARCH_QUERY")
    
    # Se é busca de item (is_item_search=True), usa current_issue. Caso contrário, usa mission_name
    if state.get('is_item_search', False):
        search_query = f"{state['game_name']} {state['current_issue']} guide walkthrough"
    else:
        search_query = f"{state['game_name']} {state['mission_name']} guide walkthrough"
    
    print(f"   Query: {search_query}")
    
    web_results = _search_web(search_query, num_results=5)
    
    if not web_results:
        print(f"\n   ⚠️ Nenhum resultado de web encontrado, usando LLM com fallback...")
        # Fallback: usa LLM com current_issue (que pode ser atualizado para busca de item)
        if state.get('is_item_search', False):
            # Busca de item: customiza o prompt
            prompt = f"""Você é um expert em videogames e detonados. Forneça informações detalhadas sobre como obter um item específico.

CONTEXTO DO JOGADOR:
- Jogo: {state["game_name"]}
- Necessidade: {state["current_issue"]}

TAREFA:
Forneça informações DETALHADAS sobre como obter o item solicitado, incluindo:
1. Localização do item
2. Pré-requisitos necessários
3. Passo a passo técnico
4. Dicas práticas

Seja específico e detalhado."""
        else:
            # Busca de missão: usa prompt original
            prompt = f"""Você é um expert em videogames e detonados. Forneça informações detalhadas sobre como progredir neste jogo.

CONTEXTO DO JOGADOR:
- Jogo: {state["game_name"]}
- Missão/Localização: {state["mission_name"]}

TAREFA:
Forneça informações DETALHADAS e ESPECÍFICAS sobre como completar esta missão/localização, incluindo:
1. Pré-requisitos (itens, habilidades)
2. Passo a passo técnico
3. Potenciais spoilers de enredo que vem DEPOIS
4. Dicas práticas

Seja específico e detalhado."""
        try:
            raw_result = _invoke_llm(prompt)
            print(f"   ✅ LLM retornou (fallback): {len(raw_result)} caracteres")
        except Exception as exc:
            logger.error(f"❌ fetch_guide_node: falha na chamada ao LLM (fallback): {exc}")
            raise APIConnectionError(
                f"Falha ao buscar detonado. Web search vazio e LLM também falhou. Detalhe: {exc}"
            ) from exc
    else:
        # ETAPA 2: Sintetiza resultados com Groq
        print(f"\n🧠 ETAPA 2: SÍNTESE COM GROQ")
        
        # Prepara conteúdo dos resultados para o LLM
        web_content = "\n\n---\n\n".join([
            f"📄 {r['title']}\nURL: {r['link']}\n\nConteúdo: {r['content']}"
            for r in web_results
        ])
        
        print(f"   Enviando {len(web_results)} resultados para síntese...")
        
        synthesis_prompt = f"""Você recebeu resultados de busca web sobre um detonado de videogame. 
Sintetize as informações em uma resposta completa e útil.

CONTEXTO DO JOGADOR:
- Jogo: {state['game_name']}
- Missão/Localização: {state['mission_name']}

RESULTADOS DA BUSCA WEB:
---
{web_content}
---

INSTRUÇÕES:
1. Sintetize as informações encontradas em uma resposta coerente
2. Mantenha as URLs dos sites de origem para referência
3. Inclua pré-requisitos (itens, habilidades) necessários
4. Descreva o passo a passo para resolver
5. Mencione possíveis spoilers futuros se relevante

FORMATO:
Forneça uma resposta completa que combina informações dos sites listados acima.
No final, liste as FONTES utilizadas com seus URLs."""

        try:
            raw_result = _invoke_llm(synthesis_prompt)
            print(f"   ✅ Síntese completada: {len(raw_result)} caracteres")
            
            if not raw_result or not raw_result.strip():
                print(f"   ⚠️ Síntese retornou vazio, usando fallback LLM...")
                # Se a síntese retornou vazio, usa fallback
                if state.get('is_item_search', False):
                    fallback_prompt = f"""Você é um expert em videogames. Forneça informações sobre como obter um item.

CONTEXTO:
- Jogo: {state['game_name']}
- Necessidade: {state['current_issue']}

Forneça uma resposta completa e detalhada."""
                else:
                    fallback_prompt = f"""Você é um expert em videogames. Forneça informações sobre como completar uma missão.

CONTEXTO:
- Jogo: {state['game_name']}
- Missão: {state['mission_name']}

Forneça uma resposta completa e detalhada."""
                
                raw_result = _invoke_llm(fallback_prompt)
        except Exception as exc:
            logger.error(f"❌ fetch_guide_node: falha na síntese com Groq: {exc}")
            raise APIConnectionError(
                f"Falha ao sintetizar resultados de web search. Detalhe: {exc}"
            ) from exc
        
        # ETAPA 3: Enriquece com seção de fontes
        print(f"\n📚 ETAPA 3: ADIÇÃO DE FONTES")
        
        # Cria seção de fontes
        sources_section = "\n\n---FONTES---\n"
        for i, result in enumerate(web_results, 1):
            sources_section += f"{i}. {result['title']}\n   🔗 {result['link']}\n"
        
        raw_result = raw_result + sources_section
        print(f"   ✅ Seção de fontes adicionada com {len(web_results)} links")

    if not raw_result or not raw_result.strip():
        print(f"   ❌ raw_result VAZIO!")
        logger.error(f"❌ fetch_guide_node: raw_result vazio!")
        raise EmptySearchResultError(
            f"A busca para '{state['current_issue']}' em '{state['game_name']}' "
            "nao retornou nenhum conteudo. Tente reformular o problema."
        )

    print(f"   ✅ raw_search_result preenchido com sucesso ({len(raw_result)} chars)")
    logger.debug(f"✅ raw_search_result preenchido com sucesso")
    
    print(f"\n📤 OUTPUT DO NÓ:")
    print(f"   raw_search_result: {len(raw_result)} caracteres")
    print(f"   Primeiros 300 chars: {raw_result[:300]}...")
    print(f"{'='*80}\n")
    
    return {"raw_search_result": raw_result}


# ---------------------------------------------------------------------------
# Nó 2: process_guide_node
# ---------------------------------------------------------------------------

def process_guide_node(state: AgentState) -> Dict[str, Any]:
    """
    Analisa o raw_search_result e extrai de forma estruturada:
    - required_requirements: lista de pré-requisitos
    - generated_text: passo a passo (guide_steps) para uso nos próximos nós
    - Atualiza raw_search_result com os spoilers futuros identificados
      (preservados em raw_search_result para uso no critique_spoiler_node)

    Retorna: required_requirements e generated_text (com os passos extraídos).
    O campo raw_search_result é prefixado com SPOILERS_FUTUROS para consulta posterior.
    """
    # Verifica limites de execução
    _check_execution_limits("process_guide_node")
    
    print(f"\n{'='*80}")
    print(f"📋 NÓ 2: PROCESS_GUIDE_NODE")
    print(f"{'='*80}")
    print(f"📥 INPUT DO NÓ:")
    print(f"   game_name: {state['game_name']}")
    print(f"   current_issue: {state['current_issue']}")
    print(f"   raw_search_result: {len(state['raw_search_result'])} caracteres")
    print(f"   Primeiros 200 chars: {state['raw_search_result'][:200]}...")
    
    logger.debug(f"⚙️ process_guide_node iniciado")
    logger.debug(f"   - raw_search_result: {len(state['raw_search_result'])} caracteres")
    
    prompt = PROCESS_GUIDE_PROMPT.format(
        raw_search_result=state["raw_search_result"],
        game_name=state["game_name"],
        current_issue=state["current_issue"],
    )

    try:
        content = _invoke_llm(prompt)
        logger.debug(f"✅ process_guide_node: LLM retornou {len(content)} caracteres")
        print(f"\n   📤 Resposta do LLM: {len(content)} caracteres")
        print(f"   Primeiros 300 chars: {content[:300]}...")
    except Exception as exc:
        logger.error(f"❌ process_guide_node: falha na chamada ao LLM: {exc}")
        raise APIConnectionError(f"Falha ao processar o guia. Detalhe: {exc}") from exc

    if not content or not content.strip():
        logger.error(f"❌ process_guide_node: content vazio!")
        raise GuideProcessingError("O modelo retornou resposta vazia ao processar o guia.")

    # Extrai PREREQUISITOS
    req_match = re.search(r"PREREQUISITOS:\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
    req_raw = req_match.group(1).strip() if req_match else ""
    requirements = (
        []
        if not req_raw or req_raw.lower() in ("nenhum", "none", "[]")
        else [r.strip() for r in req_raw.split(",") if r.strip()]
    )
    logger.debug(f"   - requirements encontrados: {requirements}")
    print(f"\n   Pré-requisitos extraídos: {requirements}")

    # Extrai PASSOS
    steps_match = re.search(r"PASSOS:\s*(.+?)(?:SPOILERS_FUTUROS:|$)", content, re.IGNORECASE | re.DOTALL)
    guide_steps = steps_match.group(1).strip() if steps_match else content
    logger.debug(f"   - guide_steps: {len(guide_steps)} caracteres")
    print(f"   Passos extraídos: {len(guide_steps)} caracteres")

    # Extrai SPOILERS_FUTUROS e anexa ao raw_search_result para o critique usar
    spoiler_match = re.search(r"SPOILERS_FUTUROS:\s*(.+?)$", content, re.IGNORECASE | re.DOTALL)
    future_spoilers = spoiler_match.group(1).strip() if spoiler_match else "nenhum"
    logger.debug(f"   - future_spoilers: {future_spoilers[:100]}...")
    print(f"   Spoilers futuros: {future_spoilers[:100]}...")

    # Guarda spoilers no raw_search_result com marcação clara para o critique
    enriched_result = f"{state['raw_search_result']}\n\n---SPOILERS_FUTUROS---\n{future_spoilers}"
    
    print(f"\n📤 OUTPUT DO NÓ:")
    print(f"   required_requirements: {requirements}")
    print(f"   generated_text: {len(guide_steps)} caracteres")
    print(f"   raw_search_result enriquecido: {len(enriched_result)} caracteres")
    print(f"{'='*80}\n")

    return {
        "required_requirements": requirements,
        "generated_text": guide_steps,
        "raw_search_result": enriched_result,
    }


# ---------------------------------------------------------------------------
# Nó 3: verify_requirements_node
# ---------------------------------------------------------------------------

def verify_requirements_node(state: AgentState) -> Dict[str, Any]:
    """
    Compara os required_requirements com o player_inventory do jogador.

    Se is_item_search=True: este nó NÃO deve ser chamado (o roteador pula).
    Se inventário completo: missing_item = None.
    Se falta algo: missing_item = nome do item mais crítico.

    Retorna: missing_item (str ou None).
    """
    # Verifica limites de execução
    _check_execution_limits("verify_requirements_node")
    
    print(f"\n{'='*80}")
    print(f"✅ NÓ 3: VERIFY_REQUIREMENTS_NODE")
    print(f"{'='*80}")
    print(f"📥 INPUT DO NÓ:")
    print(f"   required_requirements: {state.get('required_requirements', [])}")
    print(f"   player_inventory: {state.get('player_inventory', [])}")
    print(f"   is_item_search: {state.get('is_item_search', False)}")
    
    # Salvaguarda — não deveria ser chamado na segunda passagem
    if state.get("is_item_search", False):
        print(f"\n   ⚠️ is_item_search=True, pulando verificação")
        print(f"\n📤 OUTPUT DO NÓ:")
        print(f"   missing_item: None")
        print(f"{'='*80}\n")
        return {"missing_item": None}

    requirements = state.get("required_requirements", [])

    # Se não há requisitos, não há nada faltando
    if not requirements:
        print(f"\n   ℹ️ Nenhum requisito a verificar")
        print(f"\n📤 OUTPUT DO NÓ:")
        print(f"   missing_item: None")
        print(f"{'='*80}\n")
        return {"missing_item": None}

    prompt = VERIFY_REQUIREMENTS_PROMPT.format(
        required_requirements=", ".join(requirements),
        player_inventory=", ".join(state.get("player_inventory", [])),
    )

    try:
        content = _invoke_llm(prompt)
        print(f"\n   📤 Resposta do LLM: {content}")
    except Exception as exc:
        logger.error("verify_requirements_node: falha na chamada ao LLM: %s", exc)
        raise APIConnectionError(f"Falha ao verificar requisitos. Detalhe: {exc}") from exc

    # Extrai o MISSING_ITEM da resposta
    match = re.search(r"MISSING_ITEM:\s*(.+)", content, re.IGNORECASE)
    missing_raw = match.group(1).strip() if match else "none"

    missing_item = (
        None if missing_raw.lower() in ("none", "nenhum", "nenhum item", "")
        else missing_raw
    )
    
    print(f"\n📤 OUTPUT DO NÓ:")
    print(f"   missing_item: {missing_item}")
    print(f"{'='*80}\n")

    return {"missing_item": missing_item}


# ---------------------------------------------------------------------------
# Nó 4: generate_help_node
# ---------------------------------------------------------------------------

def generate_help_node(state: AgentState) -> Dict[str, Any]:
    """
    Gera a resposta de ajuda de acordo com o help_type:
    - "hint": dica sutil sem passo a passo direto (RN02)
    - "answer": solução direta e numerada (RN02)

    Se critique_passed=False (reescrita), o feedback da falha é injetado no prompt
    para que o modelo corrija o problema identificado sem spoilers.
    
    LIMITE: Máximo 2 tentativas de reescrita antes de aceitar e seguir.

    Retorna: generated_text com a resposta gerada.
    """
    # Verifica limites de execução
    _check_execution_limits("generate_help_node")
    
    print(f"\n{'='*80}")
    print(f"💭 NÓ 4: GENERATE_HELP_NODE")
    print(f"{'='*80}")
    print(f"📥 INPUT DO NÓ:")
    print(f"   game_name: {state['game_name']}")
    print(f"   current_issue: {state['current_issue']}")
    print(f"   help_type: {state['help_type']}")
    print(f"   generated_text (guide_steps): {len(state.get('generated_text', ''))} caracteres")
    print(f"   critique_passed: {state.get('critique_passed')}")
    print(f"   Primeiros 200 chars dos steps: {state.get('generated_text', '')[:200]}...")
    
    guide_steps = state.get("generated_text", "")

    # Injeta feedback do critique se a resposta anterior falhou
    critique_feedback = ""
    rewrite_count = state.get("_rewrite_count", 0)
    
    if state.get("critique_passed") is False:
        rewrite_count += 1
        if rewrite_count >= 2:
            # Máximo 2 tentativas, aceita e segue
            print(f"\n   ⚠️ LIMITE DE REESCRITA ATINGIDO (2 tentativas)")
            print(f"   Aceitando resposta como está")
            # Marca como passou para não voltar mais
            return {
                "generated_text": guide_steps,
                "critique_passed": True,
                "_rewrite_count": rewrite_count,
            }
        
        critique_feedback = (
            "\n⚠️ ATENCAO — A resposta anterior foi REPROVADA por conter spoilers. "
            "Reescreva completamente sem mencionar eventos futuros do enredo."
        )
        print(f"\n   🔄 MODO REESCRITA ({rewrite_count}/2): Aplicando feedback do critique")

    template = (
        GENERATE_HINT_PROMPT if state["help_type"] == "hint"
        else GENERATE_ANSWER_PROMPT
    )

    prompt = template.format(
        game_name=state["game_name"],
        current_issue=state["current_issue"],
        guide_steps=guide_steps,
        critique_feedback=critique_feedback,
    )

    try:
        generated = _invoke_llm(prompt)
        print(f"\n   📤 Resposta do LLM: {len(generated)} caracteres")
        print(f"   Primeiros 300 chars: {generated[:300]}...")
    except Exception as exc:
        logger.error("generate_help_node: falha na chamada ao LLM: %s", exc)
        raise APIConnectionError(f"Falha ao gerar resposta de ajuda. Detalhe: {exc}") from exc

    if not generated or not generated.strip():
        raise GuideProcessingError("O modelo retornou resposta vazia ao gerar a ajuda.")
    
    print(f"\n📤 OUTPUT DO NÓ:")
    print(f"   generated_text: {len(generated)} caracteres")
    print(f"   _rewrite_count: {rewrite_count}")
    print(f"{'='*80}\n")

    return {
        "generated_text": generated,
        "_rewrite_count": rewrite_count,
    }


# ---------------------------------------------------------------------------
# Nó 5: critique_spoiler_node
# ---------------------------------------------------------------------------

def critique_spoiler_node(state: AgentState) -> Dict[str, Any]:
    """
    Audita a resposta gerada contra a lista de spoilers futuros identificados.

    Se CRITIQUE_RESULT: PASSED → critique_passed=True, final_response=generated_text
    Se CRITIQUE_RESULT: FAILED → critique_passed=False (roteador volta ao generate_help_node)

    Retorna: critique_passed e final_response (só preenchida se aprovada).
    """
    # Verifica limites de execução
    _check_execution_limits("critique_spoiler_node")
    
    print(f"\n{'='*80}")
    print(f"🛡️  NÓ 5: CRITIQUE_SPOILER_NODE")
    print(f"{'='*80}")
    print(f"📥 INPUT DO NÓ:")
    print(f"   generated_text: {len(state.get('generated_text', ''))} caracteres")
    print(f"   Primeiros 300 chars: {state.get('generated_text', '')[:300]}...")
    
    # Extrai spoilers futuros do raw_search_result enriquecido
    raw = state.get("raw_search_result", "")
    spoiler_section = ""
    if "---SPOILERS_FUTUROS---" in raw:
        spoiler_section = raw.split("---SPOILERS_FUTUROS---")[-1].strip()
    
    print(f"   spoilers futuros: {spoiler_section[:200]}...")
    
    if not spoiler_section or spoiler_section.lower() in ("nenhum", "none"):
        # Sem spoilers identificados: aprovação automática
        print(f"\n   ✅ Nenhum spoiler identificado, aprovação automática")
        print(f"\n📤 OUTPUT DO NÓ:")
        print(f"   critique_passed: True")
        print(f"   final_response: {len(state.get('generated_text', ''))} caracteres")
        print(f"{'='*80}\n")
        return {
            "critique_passed": True,
            "final_response": state.get("generated_text", ""),
        }

    prompt = CRITIQUE_SPOILER_PROMPT.format(
        future_spoilers=spoiler_section,
        generated_text=state.get("generated_text", ""),
    )

    try:
        content = _invoke_llm(prompt)
        print(f"\n   📤 Resposta do LLM: {content}")
    except Exception as exc:
        logger.error("critique_spoiler_node: falha na chamada ao LLM: %s", exc)
        raise APIConnectionError(f"Falha ao auditar resposta. Detalhe: {exc}") from exc

    passed = "CRITIQUE_RESULT: PASSED" in content.upper()
    
    print(f"\n📤 OUTPUT DO NÓ:")
    print(f"   critique_passed: {passed}")
    print(f"   final_response: {len(state.get('generated_text', '')) if passed else 0} caracteres")
    print(f"{'='*80}\n")

    return {
        "critique_passed": passed,
        "final_response": state.get("generated_text", "") if passed else "",
    }
