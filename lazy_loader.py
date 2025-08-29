"""
Inicialização lazy para Vercel - carrega dados apenas quando necessário
"""
import os
import logging
from pathlib import Path

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flag para controlar se os dados já foram carregados
_data_loaded = False
_data_handler = None

def get_data_handler():
    """Carrega o handler de dados apenas quando necessário"""
    global _data_loaded, _data_handler

    if not _data_loaded:
        try:
            logger.info("Carregando dados pela primeira vez...")
            from data_handler import SinespDataHandler
            _data_handler = SinespDataHandler()
            _data_loaded = True
            logger.info("Dados carregados com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            _data_handler = None

    return _data_handler

def is_data_available():
    """Verifica se os dados estão disponíveis"""
    try:
        handler = get_data_handler()
        return handler is not None
    except:
        return False
