#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
guides_loader.py — Carrega guias da IGN usando o banco de dados JSON

Permite que os agentes procurem por jogo + missão e obtenham o link e conteúdo da IGN.
"""

import json
import requests
import logging
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from typing import Optional, Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Caminho para o banco de dados de guias
GUIDES_DB_PATH = Path(__file__).parent / "guides_database.json"


class GuidesLoader:
    """Carrega e gerencia guias da IGN a partir do banco de dados JSON."""
    
    def __init__(self):
        self.guides_db = self._load_guides_db()
    
    def _load_guides_db(self) -> dict:
        """Carrega o banco de dados JSON com links de guias."""
        try:
            with open(GUIDES_DB_PATH, 'r', encoding='utf-8') as f:
                db = json.load(f)
                logger.info(f"[GUIDES LOADER] Banco de dados carregado de: {GUIDES_DB_PATH}")
                return db
        except FileNotFoundError:
            logger.warning(f"Guides database not found at {GUIDES_DB_PATH}")
            return {"guides": []}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {GUIDES_DB_PATH}")
            return {"guides": []}
    
    def reload_guides_db(self):
        """Recarrega o banco de dados do arquivo JSON (útil para atualizações dinâmicas)."""
        logger.info(f"[GUIDES LOADER] Recarregando banco de dados...")
        self.guides_db = self._load_guides_db()
        logger.info(f"[GUIDES LOADER] Banco recarregado com {len(self.guides_db.get('guides', []))} jogos")
    
    def find_guide_url(self, game_name: str, mission_name: str) -> Optional[str]:
        """
        Procura um guia pelo nome do jogo e missão com fuzzy matching.
        
        Usa SequenceMatcher para encontrar correspondências mesmo com variações
        de escrita (espaços, caracteres especiais, etc).
        
        IMPORTANTE: Recarrega o banco de dados do arquivo ANTES de buscar,
        para garantir que sempre lê a versão mais recente.
        
        Args:
            game_name: Nome do jogo (ex: "GTA 5", "Grand Theft Auto V")
            mission_name: Nome da missão (ex: "Crystal Maze")
        
        Returns:
            URL do guia na IGN ou None se não encontrado
        """
        # Recarrega banco antes de cada busca (garante leitura de arquivo atualizado)
        self.reload_guides_db()
        
        print(f"\n[GUIDES LOADER] Procurando: {game_name} - {mission_name}")
        
        game_name_lower = game_name.lower().strip()
        mission_name_lower = mission_name.lower().strip()
        
        GAME_THRESHOLD = 0.6  # 60% de similaridade mínima para jogos
        MISSION_THRESHOLD = 0.65  # 65% de similaridade mínima para missões
        
        for game in self.guides_db.get("guides", []):
            # Verifica jogo por nome exato ou fuzzy
            game_names = [game["game"].lower()] + [alias.lower() for alias in game.get("game_aliases", [])]
            
            best_game_score = 0
            for gname in game_names:
                similarity = SequenceMatcher(None, game_name_lower, gname).ratio()
                if similarity > best_game_score:
                    best_game_score = similarity
            
            # Se encontrou jogo com boa similaridade, procura missão
            if best_game_score >= GAME_THRESHOLD:
                print(f"  [OK] Jogo encontrado (score: {best_game_score:.1%}): {game['game']}")
                
                best_mission_match = None
                best_mission_score = 0
                
                for mission in game.get("missions", []):
                    mission_names = [mission["name"].lower()] + [alias.lower() for alias in mission.get("mission_aliases", [])]
                    
                    for mname in mission_names:
                        similarity = SequenceMatcher(None, mission_name_lower, mname).ratio()
                        
                        if similarity > best_mission_score:
                            best_mission_score = similarity
                            best_mission_match = mission
                
                if best_mission_score >= MISSION_THRESHOLD:
                    url = best_mission_match.get("url")
                    print(f"  [OK] Missão encontrada (score: {best_mission_score:.1%}): {best_mission_match['name']}")
                    print(f"  [OK] URL: {url}")
                    return url
                else:
                    print(f"  [AVISO] Nenhuma missão com score >= {MISSION_THRESHOLD:.0%}")
                    if best_mission_match:
                        print(f"         Melhor match: '{best_mission_match['name']}' (score: {best_mission_score:.1%})")
                
                # Saiu do loop de jogos após encontrar o jogo correto
                return None
        
        print(f"  [ERRO] Jogo não encontrado")
        return None
    
    def extract_ign_guide(self, url: str) -> Optional[str]:
        """
        Extrai o conteúdo do guia da IGN.
        
        Estratégia:
        1. Faz requisição ao URL
        2. Procura pelo div.content (conteúdo real do guia)
        3. Remove navegação, scripts e styles
        4. Retorna o texto completo SEM LIMITE de caracteres
        
        Args:
            url: URL do guia na IGN
        
        Returns:
            Conteúdo do guia extraído ou None se falhar
        """
        print(f"\n[IGN EXTRACTOR] Extraindo: {url}")
        
        try:
            # Headers para evitar bloqueios
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            response = requests.get(url, timeout=10, headers=headers)
            
            if response.status_code != 200:
                print(f"  [ERRO] HTTP {response.status_code}")
                return None
            
            print(f"  [OK] Status: {response.status_code}")
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts e styles
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Estratégia 1: IGN usa div.content
            content_div = soup.find('div', {'class': 'content'})
            if content_div:
                text = content_div.get_text(separator='\n', strip=True)
                print(f"  [OK] Conteúdo extraído via div.content: {len(text)} chars")
                print(f"  [INFO] Primeiros 500 chars:\n{text[:500]}")
                print(f"  [INFO] Últimos 500 chars:\n{text[-500:]}")
                return text  # SEM LIMITE
            
            # Estratégia 2: Fallback para main
            main = soup.find('main')
            if main:
                text = main.get_text(separator='\n', strip=True)
                print(f"  [OK] Conteúdo extraído via main: {len(text)} chars")
                print(f"  [INFO] Primeiros 500 chars:\n{text[:500]}")
                print(f"  [INFO] Últimos 500 chars:\n{text[-500:]}")
                return text  # SEM LIMITE
            
            # Estratégia 3: Fallback para article
            article = soup.find('article')
            if article:
                text = article.get_text(separator='\n', strip=True)
                print(f"  [OK] Conteúdo extraído via article: {len(text)} chars")
                print(f"  [INFO] Primeiros 500 chars:\n{text[:500]}")
                print(f"  [INFO] Últimos 500 chars:\n{text[-500:]}")
                return text  # SEM LIMITE
            
            # Estratégia 4: Último recurso - todo o texto
            text = soup.get_text(separator='\n', strip=True)
            print(f"  [AVISO] Conteúdo extraído via fallback (todo texto): {len(text)} chars")
            print(f"  [INFO] Primeiros 500 chars:\n{text[:500]}")
            print(f"  [INFO] Últimos 500 chars:\n{text[-500:]}")
            return text  # SEM LIMITE
            
        except requests.exceptions.RequestException as e:
            print(f"  [ERRO] Erro de requisição: {e}")
            return None
        except Exception as e:
            print(f"  [ERRO] Erro ao extrair: {e}")
            return None
    
    def get_guide_content(self, game_name: str, mission_name: str) -> Optional[Tuple[str, str]]:
        """
        Procura e extrai o conteúdo de um guia em uma chamada.
        
        Args:
            game_name: Nome do jogo
            mission_name: Nome da missão
        
        Returns:
            Tupla (url, conteúdo) ou None se não encontrado
        """
        print(f"\n{'='*80}")
        print(f"[GUIDES LOADER] Buscando guia: {game_name} - {mission_name}")
        print(f"{'='*80}")
        
        # Procura URL
        url = self.find_guide_url(game_name, mission_name)
        if not url:
            print(f"\n[ERRO] Guia não encontrado no banco de dados")
            return None
        
        # Extrai conteúdo
        content = self.extract_ign_guide(url)
        if not content:
            print(f"\n[ERRO] Falha ao extrair conteúdo")
            return None
        
        print(f"\n[OK] Guia carregado com sucesso!")
        return (url, content)


# Instance global para uso nos nodes
_guides_loader = None


def get_guides_loader() -> GuidesLoader:
    """Retorna a instância global do GuidesLoader."""
    global _guides_loader
    if _guides_loader is None:
        _guides_loader = GuidesLoader()
    return _guides_loader


if __name__ == "__main__":
    # Teste
    loader = GuidesLoader()
    
    result = loader.get_guide_content("GTA 5", "Crystal Maze")
    if result:
        url, content = result
        print(f"\nURL: {url}")
        print(f"\nConteúdo:\n{content}")
    else:
        print("\nFalha ao carregar guia")
