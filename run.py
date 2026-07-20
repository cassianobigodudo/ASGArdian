#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run.py — Script simplificado para iniciar o servidor backend ASGArdian.

Uso:
    python run.py

O servidor estará disponível em: http://localhost:8000
"""

import subprocess
import sys


def main():
    """Inicia o servidor backend com uvicorn."""
    print("🛡️ Iniciando ASGArdian Backend...")
    print("📍 Servidor: http://localhost:8000")
    print("🔄 Modo: Desenvolvimento (com reload automático)")
    print("-" * 80)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro ao iniciar o servidor: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
