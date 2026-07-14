"""
config.py — Carregamento seguro de variáveis de ambiente via python-dotenv.
Nenhuma credencial deve ser hardcoded neste arquivo.
"""

import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env na raiz do projeto
load_dotenv()


def get_google_api_key() -> str:
    """
    Retorna a GOOGLE_API_KEY do ambiente.
    Lança ValueError em tempo de inicialização se a variável não estiver definida,
    evitando falhas silenciosas durante a execução do grafo.
    """
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "GOOGLE_API_KEY não encontrada. "
            "Defina a variável no arquivo .env com base no .env.example."
        )
    return key


# Expõe a chave como constante para uso nos nós do grafo
GOOGLE_API_KEY: str = get_google_api_key()
