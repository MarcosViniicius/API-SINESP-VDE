from depends import *
from fastapi import APIRouter
from utils import check_handler, logger
router = APIRouter()


@router.get("/resumo/vitimas", summary="Resumo de vítimas", tags=["Resumos"])
def resumo_vitimas(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    evento: Optional[str] = Query(None, description="Filtrar por tipo de evento")
):
    """Totais de vítimas com filtros opcionais"""
    try:
        current_handler = check_handler()
        df = current_handler.df.copy()
        
        # Aplicar filtros
        if uf:
            df = df[df['uf'].str.upper() == uf.upper()]
        if ano:
            df = df[df['data_referencia'].str.contains(str(ano), na=False)]
        if evento:
            df = df[df['evento'].str.contains(evento, case=False, na=False)]
        
        if df.empty:
            return {
                "total_vitimas": 0,
                "vitimas_femininas": 0,
                "vitimas_masculinas": 0,
                "vitimas_nao_informado": 0,
                "filtros": {"uf": uf, "ano": ano, "evento": evento},
                "status": "nenhum_resultado"
            }
        
        resumo = {
            "total_vitimas": int(df['total_vitima'].sum()),
            "vitimas_femininas": int(df['feminino'].sum()),
            "vitimas_masculinas": int(df['masculino'].sum()),
            "vitimas_nao_informado": int(df['nao_informado'].sum()),
            "registros_analisados": len(df),
            "filtros": {"uf": uf, "ano": ano, "evento": evento},
            "percentuais": {
                "feminino": round((df['feminino'].sum() / df['total_vitima'].sum()) * 100, 2) if df['total_vitima'].sum() > 0 else 0,
                "masculino": round((df['masculino'].sum() / df['total_vitima'].sum()) * 100, 2) if df['total_vitima'].sum() > 0 else 0,
                "nao_informado": round((df['nao_informado'].sum() / df['total_vitima'].sum()) * 100, 2) if df['total_vitima'].sum() > 0 else 0
            },
            "status": "sucesso"
        }
        
        return resumo
    except Exception as e:
        logger.error(f"Erro em resumo_vitimas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar resumo de vítimas")

@router.get("/resumo/faixa-etaria", summary="Resumo por faixa etária", tags=["Resumos"])
def resumo_faixa_etaria(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ano: Optional[int] = Query(None, description="Filtrar por ano")
):
    """Distribuição de vítimas por faixa etária"""
    try:
        current_handler = check_handler()
        df = current_handler.df.copy()
        
        # Aplicar filtros
        if uf:
            df = df[df['uf'].str.upper() == uf.upper()]
        if ano:
            df = df[df['data_referencia'].str.contains(str(ano), na=False)]
        
        if df.empty or 'faixa_etaria' not in df.columns:
            return {
                "distribuicao": {},
                "total_vitimas": 0,
                "filtros": {"uf": uf, "ano": ano},
                "status": "nenhum_resultado"
            }
        
        # Agrupar por faixa etária e somar vítimas
        distribuicao = df.groupby('faixa_etaria')['total_vitima'].sum().to_dict()
        distribuicao = {k: int(v) for k, v in distribuicao.items() if k and str(k).strip() not in ['nan', 'None', '']}
        
        total = sum(distribuicao.values())
        
        # Calcular percentuais
        percentuais = {k: round((v / total) * 100, 2) if total > 0 else 0 for k, v in distribuicao.items()}
        
        return {
            "distribuicao": distribuicao,
            "percentuais": percentuais,
            "total_vitimas": total,
            "registros_analisados": len(df),
            "filtros": {"uf": uf, "ano": ano},
            "status": "sucesso"
        }
    except Exception as e:
        logger.error(f"Erro em resumo_faixa_etaria: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar resumo por faixa etária")

@router.get("/resumo/armas", summary="Resumo por tipo de arma", tags=["Resumos"])
def resumo_armas(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ano: Optional[int] = Query(None, description="Filtrar por ano")
):
    """Estatísticas por tipo de arma"""
    try:
        current_handler = check_handler()
        df = current_handler.df.copy()
        
        # Aplicar filtros
        if uf:
            df = df[df['uf'].str.upper() == uf.upper()]
        if ano:
            df = df[df['data_referencia'].str.contains(str(ano), na=False)]
        
        if df.empty or 'arma' not in df.columns:
            return {
                "estatisticas": {},
                "total_registros": 0,
                "filtros": {"uf": uf, "ano": ano},
                "status": "nenhum_resultado"
            }
        
        # Agrupar por tipo de arma
        stats_armas = df.groupby('arma').agg({
            'total_vitima': 'sum',
            'uf': 'nunique',
            'municipio': 'nunique'
        }).reset_index()
        
        estatisticas = {}
        for _, row in stats_armas.iterrows():
            arma = row['arma']
            if arma and str(arma).strip() not in ['nan', 'None', '']:
                estatisticas[arma] = {
                    "total_vitimas": int(row['total_vitima']),
                    "ufs_afetadas": int(row['uf']),
                    "municipios_afetados": int(row['municipio'])
                }
        
        # Ordenar por total de vítimas
        estatisticas = dict(sorted(estatisticas.items(), key=lambda x: x[1]['total_vitimas'], reverse=True))
        
        return {
            "estatisticas": estatisticas,
            "total_registros": len(df),
            "total_tipos_armas": len(estatisticas),
            "filtros": {"uf": uf, "ano": ano},
            "status": "sucesso"
        }
    except Exception as e:
        logger.error(f"Erro em resumo_armas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar resumo de armas")

@router.get("/resumo/agentes", summary="Resumo por tipo de agente", tags=["Resumos"])
def resumo_agentes(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ano: Optional[int] = Query(None, description="Filtrar por ano")
):
    """Estatísticas por tipo de agente"""
    try:
        current_handler = check_handler()
        df = current_handler.df.copy()
        
        # Aplicar filtros
        if uf:
            df = df[df['uf'].str.upper() == uf.upper()]
        if ano:
            df = df[df['data_referencia'].str.contains(str(ano), na=False)]
        
        if df.empty or 'agente' not in df.columns:
            return {
                "estatisticas": {},
                "total_registros": 0,
                "filtros": {"uf": uf, "ano": ano},
                "status": "nenhum_resultado"
            }
        
        # Agrupar por tipo de agente
        stats_agentes = df.groupby('agente').agg({
            'total_vitima': 'sum',
            'uf': 'nunique',
            'municipio': 'nunique'
        }).reset_index()
        
        estatisticas = {}
        for _, row in stats_agentes.iterrows():
            agente = row['agente']
            if agente and str(agente).strip() not in ['nan', 'None', '']:
                estatisticas[agente] = {
                    "total_vitimas": int(row['total_vitima']),
                    "ufs_afetadas": int(row['uf']),
                    "municipios_afetados": int(row['municipio'])
                }
        
        # Ordenar por total de vítimas
        estatisticas = dict(sorted(estatisticas.items(), key=lambda x: x[1]['total_vitimas'], reverse=True))
        
        return {
            "estatisticas": estatisticas,
            "total_registros": len(df),
            "total_tipos_agentes": len(estatisticas),
            "filtros": {"uf": uf, "ano": ano},
            "status": "sucesso"
        }
    except Exception as e:
        logger.error(f"Erro em resumo_agentes: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar resumo de agentes")
