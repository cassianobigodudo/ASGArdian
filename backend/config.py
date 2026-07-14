"""
config.py — Carregamento seguro de variáveis de ambiente via python-dotenv.
Suporta tanto Google Gemini quanto Groq (recomendado).
Nenhuma credencial deve ser hardcoded neste arquivo.
"""

import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env na raiz do projeto
load_dotenv()


def get_api_config() -> dict:
    """
    Retorna configuração de API com chave e provedor.
    Prioriza Groq se ambas as chaves estiverem disponíveis.
    Lança ValueError em tempo de inicialização se nenhuma chave for encontrada.
    """
    google_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not google_key and not groq_key:
        raise ValueError(
            "Nenhuma chave de API foi encontrada.\n"
            "Configure GROQ_API_KEY (recomendado) ou GOOGLE_API_KEY no arquivo .env\n"
            "Veja .env.example para mais detalhes."
        )
    
    # Preferência: Groq se disponível (melhor performance e quota)
    if groq_key:
        return {
            "provider": "groq",
            "api_key": groq_key,
            "model": "llama-3.1-8b-instant",  # Modelo rápido e estável do Groq
        }
    else:
        return {
            "provider": "gemini",
            "api_key": google_key,
            "model": "gemini-2.0-flash",
        }


# Configuração centralizada exportada para uso nos nós
_config = get_api_config()

PROVIDER = _config["provider"]
API_KEY = _config["api_key"]
MODEL = _config["model"]

# Compatibilidade com código antigo
GOOGLE_API_KEY = _config["api_key"] if _config["provider"] == "gemini" else None
GROQ_API_KEY = _config["api_key"] if _config["provider"] == "groq" else None
