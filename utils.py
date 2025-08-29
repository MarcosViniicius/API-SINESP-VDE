import os
import sys
from pathlib import Path
from fastapi import HTTPException
import logging
import pandas as pd
import numpy as np

# Detectar se está rodando na Vercel
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('NOW_REGION') is not None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar o handler de dados
try:
    from data_handler import SinespDataHandler
except ImportError as e:
    logger.error(f"Erro ao importar SinespDataHandler: {e}")
    if IS_VERCEL:
        # No Vercel, tentar importar de forma alternativa
        import importlib.util
        spec = importlib.util.spec_from_file_location("data_handler", Path(__file__).parent / "data_handler.py")
        data_handler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_handler_module)
        SinespDataHandler = data_handler_module.SinespDataHandler
    else:
        raise

# Cache global para handler (importante para Vercel)
_global_handler = None

def get_handler():
    """Retorna handler com cache global para otimizar performance na Vercel"""
    global _global_handler

    if _global_handler is None:
        try:
            logger.info("Inicializando SinespDataHandler...")
            _global_handler = SinespDataHandler()
            logger.info("SinespDataHandler inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar SinespDataHandler: {e}")
            _global_handler = None

    return _global_handler

# Inicializar handler apenas se não for Vercel (na Vercel será lazy-loaded)
handler = None
if not IS_VERCEL:
    try:
        handler = get_handler()
    except Exception as e:
        logger.error(f"Erro na inicialização: {e}")
        handler = None

def check_handler():
    """Verifica se o handler está disponível"""
    global handler

    try:
        if IS_VERCEL:
            handler = get_handler()

        if handler is None:
            raise HTTPException(status_code=503, detail="Sistema de dados não disponível. Verifique se existem arquivos de dados.")

        return handler
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro em check_handler: {e}")
        raise HTTPException(status_code=503, detail="Sistema de dados não disponível.")

def safe_get_unique_values(column_name: str, sort_values: bool = True):
    """Função auxiliar para obter valores únicos de uma coluna com segurança"""
    try:
        current_handler = check_handler()
        df = current_handler.df

        if column_name not in df.columns:
            return []

        # Obter valores únicos removendo NaN e valores vazios
        series = df[column_name].dropna()

        # Converter para string e limpar
        if len(series) > 0:
            # Para colunas categóricas, converter para string
            if series.dtype.name == 'category':
                unique_values = series.cat.categories.tolist()
            else:
                unique_values = series.astype(str).unique()

            # Filtrar valores vazios/inválidos
            unique_values = [
                v for v in unique_values
                if v and str(v).strip() not in ['', 'nan', 'None', 'null', '<NA>']
            ]

            if sort_values:
                return sorted(unique_values)
            else:
                return unique_values
        else:
            return []
    except Exception as e:
        logger.error(f"Erro ao obter valores únicos da coluna {column_name}: {e}")
        return []

def safe_numeric_operation(column_name, operation="sum", default_value=0):
    """Operação numérica segura em uma coluna"""
    try:
        current_handler = check_handler()
        df = current_handler.df

        if column_name not in df.columns:
            logger.warning(f"Coluna '{column_name}' não encontrada")
            return default_value

        series = df[column_name]

        if series is None or len(series) == 0:
            return default_value

        # Para operações específicas
        if operation == "nunique":
            result = series.nunique()
        elif operation == "count":
            result = series.count()
        elif operation == "sum":
            # Para soma, garantir que é numérico
            if series.dtype in ['object', 'string', 'category']:
                logger.warning(f"Tentativa de soma em coluna categórica: {column_name}")
                return default_value
            numeric_series = pd.to_numeric(series, errors='coerce')
            result = numeric_series.sum()
        else:
            return default_value

        # Verificar se o resultado é válido usando numpy
        if pd.isna(result) or np.isinf(result):
            return default_value

        return int(result) if operation in ["count", "nunique"] else float(result)
    except Exception as e:
        logger.error(f"Erro em safe_numeric_operation para {column_name}: {e}")
        return default_value
