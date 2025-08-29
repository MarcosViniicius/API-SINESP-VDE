from depends import *
from fastapi import APIRouter
from utils import safe_get_unique_values, logger
router = APIRouter()


@router.get("/faixas-etarias", summary="Lista de faixas etárias", tags=["Dimensões"])
def get_faixas_etarias(request: Request):
    """Lista todas as categorias de faixa etária"""
    try:
        faixas = safe_get_unique_values("faixa_etaria")
        return {"faixas_etarias": faixas, "total": len(faixas), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_faixas_etarias: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de faixas etárias")
