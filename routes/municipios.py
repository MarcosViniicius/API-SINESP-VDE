from depends import *
from fastapi import APIRouter
from utils import check_handler, safe_get_unique_values, logger
router = APIRouter()


@router.get("/municipios", summary="Lista de municípios", tags=["Dimensões"])
def get_municipios(request: Request, uf: Optional[str] = Query(None, description="Filtrar por UF")):
    """Lista municípios, opcionalmente filtrados por UF"""
    try:
        current_handler = check_handler()
        df = current_handler.df
        
        if uf:
            # Filtrar por UF
            df_filtrado = df[df['uf'].str.upper() == uf.upper()]
            if df_filtrado.empty:
                return {"municipios": [], "total": 0, "uf": uf, "status": "nenhum_resultado"}
            
            # Obter municípios únicos do dataframe filtrado
            municipios = df_filtrado['municipio'].dropna().unique().tolist()
            municipios = sorted([m for m in municipios if str(m).strip() not in ['', 'nan', 'None', 'null', '<NA>']])
        else:
            municipios = safe_get_unique_values("municipio")
        
        return {
            "municipios": municipios, 
            "total": len(municipios), 
            "uf": uf if uf else "todas",
            "status": "sucesso"
        }
    except Exception as e:
        logger.error(f"Erro em get_municipios: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de municípios")