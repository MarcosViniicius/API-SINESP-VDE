from depends import *
from fastapi import APIRouter
from utils import check_handler, logger
router = APIRouter()


@router.get("/ranking/ufs-violencia", summary="Ranking de UFs por violência", tags=["Estatísticas"])
def ranking_ufs_violencia(
    request: Request,
    limit: int = Query(27, ge=1, le=50, description="Limite de resultados")
):
    """Ranking das UFs com maior número de casos de violência"""
    try:
        current_handler = check_handler()
        df = current_handler.df
        
        # Agrupar por UF e somar as vítimas
        ranking = df.groupby('uf')['total_vitima'].sum().reset_index()
        ranking = ranking.sort_values('total_vitima', ascending=False)
        ranking = ranking.head(limit)
        
        # Converter para lista de dicionários
        resultado = []
        for _, row in ranking.iterrows():
            resultado.append({
                "uf": row['uf'],
                "total_vitimas": int(row['total_vitima']),
                "posicao": len(resultado) + 1
            })
        
        return {
            "ranking": resultado,
            "total_ufs": len(resultado),
            "status": "sucesso"
        }
    except Exception as e:
        logger.error(f"Erro em ranking_ufs_violencia: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar ranking de UFs")
