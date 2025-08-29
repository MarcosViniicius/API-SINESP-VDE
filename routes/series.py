from depends import *
from fastapi import APIRouter
from utils import check_handler, logger
router = APIRouter()


@router.get("/series/ocorrencias", summary="Série temporal de ocorrências", tags=["Séries Temporais"])
def serie_temporal_ocorrencias(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    municipio: Optional[str] = Query(None, description="Filtrar por município"),
    evento: Optional[str] = Query(None, description="Filtrar por tipo de evento")
):
    """Evolução temporal (ano a ano) do total de vítimas"""
    try:
        current_handler = check_handler()
        df = current_handler.df.copy()
        
        # Aplicar filtros
        if uf:
            df = df[df['uf'].str.upper() == uf.upper()]
        if municipio:
            df = df[df['municipio'].str.contains(municipio, case=False, na=False)]
        if evento:
            df = df[df['evento'].str.contains(evento, case=False, na=False)]
        
        if df.empty:
            return {
                "serie_temporal": {},
                "tendencia": "sem_dados",
                "filtros": {"uf": uf, "municipio": municipio, "evento": evento},
                "status": "nenhum_resultado"
            }
        
        # Extrair ano da data_referencia
        anos = []
        for data_ref in df['data_referencia']:
            try:
                if pd.isna(data_ref):
                    continue
                # Tentar extrair ano da data
                data_parsed = pd.to_datetime(data_ref, errors='coerce')
                if not pd.isna(data_parsed):
                    anos.append(data_parsed.year)
                else:
                    # Fallback: procurar por 4 dígitos no texto
                    import re
                    matches = re.findall(r'\b(20\d{2})\b', str(data_ref))
                    if matches:
                        anos.append(int(matches[0]))
            except:
                continue
        
        df['ano_extraido'] = anos[:len(df)]
        
        # Agrupar por ano e somar vítimas
        serie = df.groupby('ano_extraido')['total_vitima'].sum().to_dict()
        serie = {k: int(v) for k, v in serie.items() if k and not pd.isna(k)}
        serie_ordenada = dict(sorted(serie.items()))
        
        # Calcular tendência simples
        valores = list(serie_ordenada.values())
        if len(valores) >= 2:
            tendencia = "crescente" if valores[-1] > valores[0] else "decrescente" if valores[-1] < valores[0] else "estavel"
        else:
            tendencia = "insuficiente"
        
        return {
            "serie_temporal": serie_ordenada,
            "total_vitimas": sum(serie_ordenada.values()),
            "periodo": f"{min(serie_ordenada.keys())}-{max(serie_ordenada.keys())}" if serie_ordenada else "N/A",
            "tendencia": tendencia,
            "filtros": {"uf": uf, "municipio": municipio, "evento": evento},
            "status": "sucesso"
        }
    except Exception as e:
        logger.error(f"Erro em serie_temporal_ocorrencias: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar série temporal")
