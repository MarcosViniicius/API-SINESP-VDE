from depends import *
from fastapi import APIRouter
from utils import check_handler, logger
router = APIRouter()


@router.get("/ocorrencias", summary="Buscar ocorrências", tags=["Consultas"])
def buscar_ocorrencias(
    request: Request,
    uf: Optional[str] = Query(None, description="UF"),
    municipio: Optional[str] = Query(None, description="Município"),
    evento: Optional[str] = Query(None, description="Tipo de evento"),
    ano: Optional[int] = Query(None, description="Ano"),
    agente: Optional[str] = Query(None, description="Tipo de agente"),
    arma: Optional[str] = Query(None, description="Tipo de arma"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação")
):
    """Busca ocorrências com filtros opcionais e paginação"""
    try:
        current_handler = check_handler()
        df = current_handler.df.copy()
        
        # Aplicar filtros
        if uf:
            df = df[df['uf'].str.contains(uf, case=False, na=False)]
        if municipio:
            df = df[df['municipio'].str.contains(municipio, case=False, na=False)]
        if evento:
            df = df[df['evento'].str.contains(evento, case=False, na=False)]
        if agente:
            df = df[df['agente'].str.contains(agente, case=False, na=False)]
        if arma:
            df = df[df['arma'].str.contains(arma, case=False, na=False)]
        if ano:
            df = df[df['data_referencia'].str.contains(str(ano), na=False)]
        
        total_encontrado = len(df)
        
        # Aplicar paginação
        df_resultado = df.iloc[offset:offset + limit]
        
        # Converter para lista de dicionários com tratamento de tipos
        resultados = []
        for _, row in df_resultado.iterrows():
            registro = {}
            for col, val in row.items():
                # Tratar valores NaN e infinitos
                if pd.isna(val) or (isinstance(val, (int, float)) and np.isinf(val)):
                    registro[col] = None
                elif isinstance(val, (np.integer, np.floating)):
                    # Converter tipos numpy para tipos Python nativos
                    registro[col] = int(val) if isinstance(val, np.integer) else float(val)
                else:
                    registro[col] = val
            resultados.append(registro)
        
        return {
            "ocorrencias": resultados,
            "paginacao": {
                "total_encontrado": total_encontrado,
                "total_exibido": len(resultados),
                "offset": offset,
                "limit": limit,
                "proxima_pagina": offset + limit if offset + limit < total_encontrado else None
            },
            "filtros_aplicados": {
                "uf": uf,
                "municipio": municipio,
                "evento": evento,
                "ano": ano,
                "agente": agente,
                "arma": arma
            },
            "status": "sucesso" if len(resultados) > 0 else "nenhum_resultado"
        }
    except Exception as e:
        logger.error(f"Erro em buscar_ocorrencias: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar ocorrências")
