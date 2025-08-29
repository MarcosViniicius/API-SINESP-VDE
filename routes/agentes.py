from depends import Request, HTTPException
from fastapi import APIRouter
from utils import safe_get_unique_values, logger
router = APIRouter()


@router.get("/agentes", summary="Lista de agentes", tags=["Dimensões"])
def get_agentes(request: Request):
    """Lista todos os tipos de agentes envolvidos"""
    try:
        agentes = safe_get_unique_values("agente")
        return {"agentes": agentes, "total": len(agentes), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_agentes: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de agentes")

@router.get("/api/agentes", summary="Lista de agentes", tags=["Dados"])
def get_agentes_legacy(request: Request):
    """Lista todos os tipos de agentes (endpoint legacy)"""
    try:
        agentes = safe_get_unique_values("agente")
        return {"agentes": agentes, "total": len(agentes), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_agentes_legacy: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de agentes")
