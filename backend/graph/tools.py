# -*- coding: utf-8 -*-
"""
tools.py -- Ferramentas do LangGraph para o ASGArdian.

Implementa as seguintes tools:
1. search_game_guide: Busca guia de jogo (IGN database ou LLM)
2. extract_guide_structure: Extrai estrutura (pré-requisitos, passos, spoilers)
3. validate_player_inventory: Valida inventário do jogador
4. find_item_location: Busca localização de um item específico
5. detect_spoiler: Detecta spoilers em texto

Cada tool é decorada com @tool do LangChain e pode ser integrada ao LLM.
"""

from langchain_core.tools import tool
from typing import List, Dict, Any
import logging

from backend.guides_loader import get_guides_loader

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL 1: search_game_guide
# ============================================================================

@tool
def search_game_guide(game_name: str, mission_name: str) -> str:
    """Busca um guia de jogo para uma missão específica.
    
    Procura no banco de dados IGN (guides_database.json) e retorna o conteúdo
    completo do guia se encontrado. Se não encontrado, avisa que está indisponível.
    
    Args:
        game_name: Nome do jogo (ex: "Red Dead Redemption 2")
        mission_name: Nome da missão ou localização (ex: "Outlaws from the West")
        
    Returns:
        String com o conteúdo do guia ou mensagem de erro
        
    Examples:
        >>> result = search_game_guide("Red Dead Redemption 2", "Outlaws from the West")
        >>> len(result) > 0  # True se encontrou
    """
    try:
        guides_loader = get_guides_loader()
        guide_result = guides_loader.get_guide_content(game_name, mission_name)
        
        if guide_result:
            url, content = guide_result
            formatted_result = f"{content}\n\n---FONTES---\n1. IGN Walkthrough\n   Link: {url}"
            logger.info(f"✅ search_game_guide: Guia encontrado para {game_name} - {mission_name}")
            return formatted_result
        else:
            logger.warning(f"⚠️ search_game_guide: Guia não encontrado para {game_name} - {mission_name}")
            return f"Guia não encontrado no banco de dados para '{game_name}' - '{mission_name}'"
    
    except Exception as e:
        logger.error(f"❌ search_game_guide: Erro ao buscar guia: {e}")
        return f"Erro ao buscar guia: {str(e)}"


# ============================================================================
# TOOL 2: extract_guide_structure
# ============================================================================

@tool
def extract_guide_structure(guide_text: str) -> Dict[str, Any]:
    """Extrai estrutura de um guia (pré-requisitos, passos, spoilers).
    
    Analisa texto bruto de um guia e extrai:
    - Pré-requisitos (itens críticos necessários)
    - Passos (instruções mecânicas)
    - Spoilers futuros (plot twists, mortes, etc)
    
    Args:
        guide_text: Texto completo do guia
        
    Returns:
        Dicionário com chaves: prerequisites, steps, future_spoilers
        
    Examples:
        >>> result = extract_guide_structure("Use a chave vermelha...")
        >>> "prerequisites" in result  # True
        >>> result["prerequisites"]  # Lista de items
    """
    try:
        # Análise simples do conteúdo
        prerequisites = []
        steps = []
        spoilers = []
        
        lines = guide_text.split('\n')
        
        # Procura por palavras-chave de pré-requisitos
        prerequisite_keywords = ['precisa', 'necessário', 'requer', 'item:', 'equipamento:', 'habilidade:']
        spoiler_keywords = ['morre', 'morte', 'traição', 'final', 'plot twist', 'revelar', 'surprise']
        
        for line in lines:
            line_lower = line.lower()
            
            # Detecta pré-requisitos
            if any(kw in line_lower for kw in prerequisite_keywords):
                if line.strip() and line not in prerequisites:
                    prerequisites.append(line.strip())
            
            # Detecta spoilers
            if any(kw in line_lower for kw in spoiler_keywords):
                if line.strip() and line not in spoilers:
                    spoilers.append(line.strip())
            
            # Detecta passos (linhas com números ou "passo")
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', 'Passo', 'passo')):
                if line.strip() and line not in steps:
                    steps.append(line.strip())
        
        result = {
            "prerequisites": prerequisites if prerequisites else ["nenhum"],
            "steps": steps if steps else ["Conteúdo do guia não estruturado"],
            "future_spoilers": spoilers if spoilers else ["nenhum"]
        }
        
        logger.info(f"✅ extract_guide_structure: Extraídos {len(prerequisites)} pré-requisitos, {len(steps)} passos, {len(spoilers)} spoilers")
        return result
    
    except Exception as e:
        logger.error(f"❌ extract_guide_structure: Erro ao extrair estrutura: {e}")
        return {
            "prerequisites": ["erro na extração"],
            "steps": ["erro na extração"],
            "future_spoilers": ["erro na extração"]
        }


# ============================================================================
# TOOL 3: validate_player_inventory
# ============================================================================

@tool
def validate_player_inventory(required_items: List[str], player_items: List[str]) -> Dict[str, Any]:
    """Valida se o jogador tem os itens necessários.
    
    Compara semanticamente os items requeridos com o inventário do jogador.
    Usa matching flexível para lidar com variações de nomes.
    
    Args:
        required_items: Lista de items críticos necessários
        player_items: Lista de items que o jogador possui
        
    Returns:
        Dicionário com:
        - complete: bool (True se tem tudo)
        - missing: List[str] (items faltantes)
        - match_details: List[str] (detalhes da validação)
        
    Examples:
        >>> result = validate_player_inventory(["Chave Vermelha"], ["Chave", "Pistola"])
        >>> result["complete"]  # False
        >>> result["missing"]  # ["Chave Vermelha"]
    """
    try:
        missing = []
        match_details = []
        
        # Caso especial: inventário vazio = assume que tem tudo
        if not player_items or all(not item.strip() for item in player_items):
            logger.info(f"ℹ️ validate_player_inventory: Inventário vazio, assumindo que jogador tem tudo")
            return {
                "complete": True,
                "missing": [],
                "match_details": ["Inventário vazio - assumindo que jogador possui todos os items"]
            }
        
        # Valida cada item requerido
        for required in required_items:
            if required.lower() == "nenhum":
                continue
            
            required_lower = required.lower()
            found = False
            
            for player_item in player_items:
                player_lower = player_item.lower()
                
                # Matching semântico: verifica se strings se sobrepõem
                if (required_lower in player_lower or 
                    player_lower in required_lower or
                    required_lower.split()[0] == player_lower.split()[0]):
                    found = True
                    match_details.append(f"✅ '{required}' encontrado em '{player_item}'")
                    break
            
            if not found:
                missing.append(required)
                match_details.append(f"❌ '{required}' NÃO encontrado no inventário")
        
        complete = len(missing) == 0
        logger.info(f"✅ validate_player_inventory: Complete={complete}, Missing={len(missing)}")
        
        return {
            "complete": complete,
            "missing": missing,
            "match_details": match_details
        }
    
    except Exception as e:
        logger.error(f"❌ validate_player_inventory: Erro na validação: {e}")
        return {
            "complete": False,
            "missing": ["erro na validação"],
            "match_details": [f"Erro: {str(e)}"]
        }


# ============================================================================
# TOOL 4: find_item_location
# ============================================================================

@tool
def find_item_location(game_name: str, item_name: str) -> str:
    """Encontra onde obter um item específico em um jogo.
    
    Busca no banco de dados de guias pela localização/como obter um item.
    Útil quando o inventário do jogador está incompleto.
    
    Args:
        game_name: Nome do jogo
        item_name: Nome do item a encontrar
        
    Returns:
        String com informações sobre onde/como obter o item
        
    Examples:
        >>> result = find_item_location("Red Dead 2", "Chave Vermelha")
        >>> "localização" in result.lower() or "obter" in result.lower()
    """
    try:
        guides_loader = get_guides_loader()
        
        # Tenta buscar especificamente por "como obter [item]"
        search_query = f"como obter {item_name}"
        guide_result = guides_loader.get_guide_content(game_name, search_query)
        
        if guide_result:
            url, content = guide_result
            result = f"{content}\n\n---FONTE---\nIGN Guide: {url}"
            logger.info(f"✅ find_item_location: Encontrado '{item_name}' em {game_name}")
            return result
        else:
            logger.warning(f"⚠️ find_item_location: Não encontrado guia para '{item_name}' em {game_name}")
            return f"Guia para obter '{item_name}' em '{game_name}' não encontrado no banco de dados"
    
    except Exception as e:
        logger.error(f"❌ find_item_location: Erro ao buscar localização: {e}")
        return f"Erro ao buscar localização do item: {str(e)}"


# ============================================================================
# TOOL 5: detect_spoiler
# ============================================================================

@tool
def detect_spoiler(text: str, spoiler_keywords: List[str] = None) -> Dict[str, Any]:
    """Detecta se um texto contém spoilers significativos.
    
    Analisa o texto procurando por palavras-chave de spoilers.
    Pode usar palavras-chave customizadas ou padrão.
    
    Args:
        text: Texto a analisar
        spoiler_keywords: Lista customizada de palavras-chave (opcional)
        
    Returns:
        Dicionário com:
        - is_spoiler: bool (True se contém spoilers)
        - severity: "none" | "low" | "medium" | "high"
        - detected_keywords: List[str] (palavras-chave encontradas)
        - details: str (explicação)
        
    Examples:
        >>> result = detect_spoiler("O personagem morre no final")
        >>> result["is_spoiler"]  # True
        >>> result["severity"]  # "high"
    """
    try:
        # Palavras-chave padrão de spoilers significativos
        default_keywords = [
            'morre', 'morte', 'morreu',
            'traição', 'traidor', 'trai',
            'final', 'ending', 'desfecho',
            'plot twist', 'plot twist',
            'revelar', 'revelação', 'surprise',
            'verdadeiro vilão', 'vilão é',
            'personagem importante',
            'decisão final', 'escolha final'
        ]
        
        keywords_to_check = spoiler_keywords if spoiler_keywords else default_keywords
        text_lower = text.lower()
        
        detected = []
        for keyword in keywords_to_check:
            if keyword.lower() in text_lower:
                detected.append(keyword)
        
        # Calcula severidade baseada na quantidade e tipo de spoilers
        severity = "none"
        is_spoiler = len(detected) > 0
        
        if is_spoiler:
            if len(detected) >= 3:
                severity = "high"
            elif len(detected) == 2:
                severity = "medium"
            else:
                severity = "low"
        
        result = {
            "is_spoiler": is_spoiler,
            "severity": severity,
            "detected_keywords": detected,
            "details": f"Encontrados {len(detected)} possíveis spoilers no texto"
        }
        
        logger.info(f"✅ detect_spoiler: is_spoiler={is_spoiler}, severity={severity}")
        return result
    
    except Exception as e:
        logger.error(f"❌ detect_spoiler: Erro ao detectar spoiler: {e}")
        return {
            "is_spoiler": False,
            "severity": "error",
            "detected_keywords": [],
            "details": f"Erro na detecção: {str(e)}"
        }


# ============================================================================
# Exports
# ============================================================================

AVAILABLE_TOOLS = [
    search_game_guide,
    extract_guide_structure,
    validate_player_inventory,
    find_item_location,
    detect_spoiler
]

__all__ = [
    'search_game_guide',
    'extract_guide_structure',
    'validate_player_inventory',
    'find_item_location',
    'detect_spoiler',
    'AVAILABLE_TOOLS'
]
