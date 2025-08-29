from depends import *
from fastapi import APIRouter
from utils import check_handler, safe_numeric_operation, logger, handler
router = APIRouter()


@router.get("/estatisticas/resumo", summary="Estatísticas gerais", tags=["Estatísticas"])
def estatisticas_resumo(request: Request):
    """Estatísticas gerais do dataset"""
    try:
        current_handler = check_handler()
        df = current_handler.df
        
        stats = {
            "total_registros": len(df),
            "total_vitimas": safe_numeric_operation("total_vitima", "sum"),
            "vitimas_femininas": safe_numeric_operation("feminino", "sum"),
            "vitimas_masculinas": safe_numeric_operation("masculino", "sum"),
            "vitimas_nao_informado": safe_numeric_operation("nao_informado", "sum"),
            "ufs_cobertas": safe_numeric_operation("uf", "nunique"),
            "municipios_cobertos": safe_numeric_operation("municipio", "nunique"),
            "tipos_eventos": safe_numeric_operation("evento", "nunique"),
            "status": "sucesso"
        }
        return stats
    except Exception as e:
        logger.error(f"Erro em estatisticas_resumo: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar estatísticas de resumo")

@router.get("/estatisticas/por-uf", summary="Estatísticas por UF", tags=["Estatísticas"])
def estatisticas_por_uf(request: Request, uf: str = Query(..., description="UF para consulta")):
    """Estatísticas detalhadas por UF"""
    try:
        check_handler()
        df = handler.df
        
        # Filtrar por UF
        df_uf = df[df['uf'].str.upper() == uf.upper()]
        
        if df_uf.empty:
            return {
                "uf": uf,
                "total_registros": 0,
                "status": "nenhum_resultado"
            }
        
        stats = {
            "uf": uf.upper(),
            "total_registros": len(df_uf),
            "total_vitimas": int(df_uf['total_vitima'].sum()),
            "vitimas_femininas": int(df_uf['feminino'].sum()),
            "vitimas_masculinas": int(df_uf['masculino'].sum()),
            "vitimas_nao_informado": int(df_uf['nao_informado'].sum()),
            "municipios_afetados": df_uf['municipio'].nunique(),
            "tipos_eventos": df_uf['evento'].nunique(),
            "eventos_mais_comuns": df_uf['evento'].value_counts().head(5).to_dict(),
            "status": "sucesso"
        }
        
        return stats
    except Exception as e:
        logger.error(f"Erro em estatisticas_por_uf: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar estatísticas por UF")

@router.get("/estatisticas/por-ano", summary="Estatísticas por ano", tags=["Estatísticas"])
def estatisticas_por_ano(request: Request, ano: int = Query(..., description="Ano para consulta")):
    """Estatísticas detalhadas por ano"""
    try:
        check_handler()
        df = handler.df
        
        # Filtrar por ano (usando data_referencia ou arquivo_origem)
        mask = df['data_referencia'].str.contains(str(ano), na=False)
        if 'arquivo_origem' in df.columns:
            mask_arquivo = df['arquivo_origem'].str.contains(str(ano), na=False)
            mask = mask | mask_arquivo
        
        df_ano = df[mask]
        
        if df_ano.empty:
            return {
                "ano": ano,
                "total_registros": 0,
                "status": "nenhum_resultado"
            }
        
        stats = {
            "ano": ano,
            "total_registros": len(df_ano),
            "total_vitimas": int(df_ano['total_vitima'].sum()),
            "vitimas_femininas": int(df_ano['feminino'].sum()),
            "vitimas_masculinas": int(df_ano['masculino'].sum()),
            "vitimas_nao_informado": int(df_ano['nao_informado'].sum()),
            "ufs_afetadas": df_ano['uf'].nunique(),
            "municipios_afetados": df_ano['municipio'].nunique(),
            "tipos_eventos": df_ano['evento'].nunique(),
            "top_ufs": df_ano.groupby('uf')['total_vitima'].sum().sort_values(ascending=False).head(5).to_dict(),
            "status": "sucesso"
        }
        
        return stats
    except Exception as e:
        logger.error(f"Erro em estatisticas_por_ano: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar estatísticas por ano")
