# -*- coding: utf-8 -*-
"""
example_payload.py -- Payloads de exemplo para teste manual do ASGArdian.

Contém exemplos reais de cenários de jogos conhecidos (GTA V, Borderlands 2, etc.)
para facilitar testes manuais e demonstração das funcionalidades.

Uso:
    python -c "from backend.example_payload import payload_gta_v_hint; from backend.main import run_agent; run_agent(payload_gta_v_hint)"
"""

# ============================================================================
# GTA V — Exemplo 1: Procurando por um item (hint mode)
# ============================================================================

payload_gta_v_hint = {
    "game_name": "Grand Theft Auto V",
    "mission_name": "The Big Score",
    "current_issue": (
        "Estou na fase do roubo do banco. Consegui entrar na câmara de segurança, "
        "mas não consigo abrir o cofre. Procurei por toda a sala e não achei nada. "
        "Será que preciso de uma ferramenta especial ou há um botão que não encontrei?"
    ),
    "help_type": "hint",
    "player_inventory": ["Hacking Device", "Lockpick", "C4 Explosives"],
}

# ============================================================================
# GTA V — Exemplo 2: Missão difícil (answer mode)
# ============================================================================

payload_gta_v_answer = {
    "game_name": "Grand Theft Auto V",
    "mission_name": "The Merryweather Heist",
    "current_issue": (
        "Travei na parte em que preciso eliminar os soldados da Merryweather. "
        "Não consegue avanço nenhum — estou no estacionamento e eles têm muitas armas. "
        "Qual é a melhor estratégia para passar desta fase?"
    ),
    "help_type": "answer",
    "player_inventory": ["Assault Rifle", "Shotgun", "RPG", "Body Armor x3"],
}

# ============================================================================
# GTA V — Exemplo 3: Tesouro oculto (hint mode)
# ============================================================================

payload_gta_v_treasure = {
    "game_name": "Grand Theft Auto V",
    "mission_name": "Treasure Hunt (Side Mission)",
    "current_issue": (
        "Encontrei uma moeda de ouro perto de Fort Zancudo. O mapa do tesouro aponta "
        "para mais 49 moedas espalhadas por Los Santos, mas não tenho a menor ideia "
        "de onde procurar. Como faço para encontrar essas moedas ocultas?"
    ),
    "help_type": "hint",
    "player_inventory": ["Treasure Map", "Binoculars", "Metal Detector"],
}

# ============================================================================
# GTA V — Exemplo 4: Desafio de corrida (answer mode)
# ============================================================================

payload_gta_v_race = {
    "game_name": "Grand Theft Auto V",
    "mission_name": "Street Race - Vinewood Hills Circuit",
    "current_issue": (
        "Estou tentando completar a corrida de rua em Vinewood Hills, mas sempre perco "
        "para a IA nos últimos 500 metros. Qual veículo é mais rápido? E qual é a melhor "
        "linha de corrida para vencer?"
    ),
    "help_type": "answer",
    "player_inventory": ["Turbo Upgraded Car", "$50,000", "Armor"],
}

# ============================================================================
# Borderlands 2 — Exemplo de referência (mantido para compatibilidade)
# ============================================================================

payload_borderlands_2_hint = {
    "game_name": "Borderlands 2",
    "mission_name": "Lights Out",
    "current_issue": (
        "Estou na subestação e não consigo restaurar a energia. Já ativei duas alavancas "
        "mas nada acontece. Estou perdido nesta área."
    ),
    "help_type": "hint",
    "player_inventory": ["Shotgun Torque", "Shield Adaptive", "Grenade Singularity"],
}

# ============================================================================
# Dicionário de payloads para fácil acesso
# ============================================================================

EXAMPLE_PAYLOADS = {
    "gta_v_hint": payload_gta_v_hint,
    "gta_v_answer": payload_gta_v_answer,
    "gta_v_treasure": payload_gta_v_treasure,
    "gta_v_race": payload_gta_v_race,
    "borderlands_2_hint": payload_borderlands_2_hint,
}


if __name__ == "__main__":
    """Exemplo de uso direto do módulo."""
    print("Payloads de Exemplo Disponíveis:")
    for key in EXAMPLE_PAYLOADS:
        print(f"  - {key}")
    print("\nUso: python -c 'from backend.example_payload import payload_gta_v_hint; ...")
