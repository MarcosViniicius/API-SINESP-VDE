from depends import *
from fastapi import APIRouter
from utils import safe_get_unique_values, logger
router = APIRouter()


@router.get("/eventos", summary="Lista de tipos de eventos", tags=["Dimensões"])
def get_eventos(request: Request):
    """Lista todos os tipos de eventos/ocorrências"""
    try:
        eventos = safe_get_unique_values("evento")
        return {"eventos": eventos, "total": len(eventos), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_eventos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de eventos")
