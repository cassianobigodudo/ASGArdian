# -*- coding: utf-8 -*-
"""
errors.py -- Excecoes customizadas do ASGArdian.

Centraliza todos os tipos de erro do sistema para facilitar
o tratamento preciso em cada camada (nos, main, testes).
"""


class ASGArdianError(Exception):
    """Erro base do ASGArdian. Todas as excecoes do sistema herdam desta."""
    pass


class PayloadValidationError(ASGArdianError):
    """Payload de entrada invalido ou com campos ausentes."""
    pass


class APIConnectionError(ASGArdianError):
    """Falha na comunicacao com a API do Gemini ou Google Search."""
    pass


class EmptySearchResultError(ASGArdianError):
    """A busca retornou resultado vazio ou sem conteudo util."""
    pass


class GuideProcessingError(ASGArdianError):
    """Falha ao extrair informacoes estruturadas do conteudo bruto do guia."""
    pass


class SpoilerCritiqueError(ASGArdianError):
    """O nó de critica atingiu o limite de tentativas de reescrita sem aprovacao."""
    pass
