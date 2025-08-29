from depends import *
from fastapi import APIRouter
from utils import check_handler, logger
router = APIRouter()


@router.get("/status", summary="Status da API", tags=["Metadados"])
def status(request: Request):
    """Healthcheck da API com informações de status"""
    try:
        current_handler = check_handler()
        total_registros = len(current_handler.df) if current_handler and current_handler.df is not None else 0
        memoria = current_handler.get_memory_usage() if current_handler else {"dataframe_size_mb": 0}
        
        return {
            "status": "ok",
            "timestamp": pd.Timestamp.now().isoformat(),
            "versao_api": "3.0",
            "total_registros": total_registros,
            "memoria_mb": memoria["dataframe_size_mb"],
            "ultima_atualizacao_dados": "20/08/2025",
            "periodo_cobertura": "2015-2025",
            "uptime": "online",
            "rate_limiting": f"{"50/minute"}"
        }
    except Exception as e:
        logger.error(f"Erro em /status: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "erro",
                "timestamp": pd.Timestamp.now().isoformat(),
                "mensagem": "Sistema de dados não disponível",
                "erro": str(e)
            }
        )
