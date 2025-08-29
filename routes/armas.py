from depends import Request,HTTPException
from fastapi import APIRouter
from utils import safe_get_unique_values, logger
router = APIRouter()


@router.get("/armas", summary="Lista de armas", tags=["Dimensões"])
def get_armas(request: Request):
    """Lista todos os tipos de armas"""
    try:
        armas = safe_get_unique_values("arma")
        return {"armas": armas, "total": len(armas), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_armas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de armas")

@router.get("/api/armas", summary="Lista de armas", tags=["Dados"])
def get_armas_legacy(request: Request):
    """Lista todos os tipos de armas (endpoint legacy)"""
    try:
        armas = safe_get_unique_values("arma")
        return {"armas": armas, "total": len(armas), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_armas_legacy: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de armas")
