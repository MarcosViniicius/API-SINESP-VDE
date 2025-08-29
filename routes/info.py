from depends import *
from fastapi import APIRouter
from utils import check_handler, logger
router = APIRouter()


@router.get("/api/info", summary="Informações da API", tags=["Informações"])
def info():
    """Informações gerais sobre a API e dados disponíveis"""
    try:
        current_handler = check_handler()
        total_registros = len(current_handler.df) if current_handler and current_handler.df is not None else 0
        
        return {
            "api": "SINESP VDE 2015-2025",
            "status": "online",
            "fonte": "Ministério da Justiça e Segurança Pública",
            "ultima_atualizacao": "20/08/2025",
            "total_registros": total_registros,
            "link_oficial": "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2015-a-2025",
            "endpoints": {
                "consultas": ["/ocorrencias", "/ufs", "/municipios", "/eventos", "/anos"],
                "estatisticas": ["/estatisticas/resumo", "/estatisticas/por-uf", "/estatisticas/por-ano"],
                "rankings": ["/ranking/ufs-violencia"],
                "metodologia": ["/metodologia", "/notas-metodologicas/estados", "/classificacoes/criminais"]
            },
            "observacao": "Alguns indicadores podem ter múltiplas linhas no mesmo mês - somar valores para total correto"
        }
    except Exception as e:
        logger.error(f"Erro em /api/info: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter informações da API")