from depends import *
from fastapi import APIRouter
from utils import safe_get_unique_values, logger
router = APIRouter()


@router.get("/ufs", summary="Lista de UFs", tags=["Dimensões"])
def get_ufs(request: Request):
    """Lista todas as UFs disponíveis"""
    try:
        ufs = safe_get_unique_values("uf")
        return {"ufs": ufs, "total": len(ufs), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_ufs: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de UFs")