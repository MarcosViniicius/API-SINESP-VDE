from depends import Request,HTTPException
from fastapi import APIRouter
from utils import check_handler, logger
router = APIRouter()


@router.get("/anos", summary="Lista de anos disponíveis", tags=["Dados"])
def get_anos(request: Request):
    """Lista todos os anos disponíveis nos dados"""
    try:
        current_handler = check_handler()
        anos = current_handler.get_anos_disponiveis()
        return {"anos": anos, "total": len(anos), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_anos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de anos")
