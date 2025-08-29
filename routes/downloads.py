
import json
import os
import tempfile
from typing import Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from utils import check_handler, logger

router = APIRouter()


@router.get("/download/csv", summary="Exportar dados como CSV", tags=["Exportação"])
def download_csv(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    municipio: Optional[str] = Query(None, description="Filtrar por município"),
    evento: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    limit: int = Query(10000, ge=1, le=50000, description="Limite de registros")
):
    """Exporta os dados filtrados como arquivo CSV"""
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
        if ano:
            df = df[df['data_referencia'].str.contains(str(ano), na=False)]
        
        # Limitar resultados
        df = df.head(limit)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado com os filtros aplicados")
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as tmp_file:
            df.to_csv(tmp_file.name, index=False, encoding='utf-8')
            tmp_filename = tmp_file.name
        
        # Definir nome do arquivo baseado nos filtros
        filename_parts = ["sinesp_vde"]
        if uf:
            filename_parts.append(f"uf_{uf}")
        if municipio:
            filename_parts.append(f"municipio_{municipio[:10]}")
        if evento:
            filename_parts.append(f"evento_{evento[:10]}")
        if ano:
            filename_parts.append(f"ano_{ano}")
        
        filename = "_".join(filename_parts) + ".csv"
        
        def cleanup():
            try:
                os.unlink(tmp_filename)
            except:
                pass
        
        return FileResponse(
            tmp_filename,
            media_type='text/csv',
            filename=filename,
            background=cleanup
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro em download_csv: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar arquivo CSV")

@router.get("/download/json", summary="Exportar dados como JSON", tags=["Exportação"])
def download_json(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    municipio: Optional[str] = Query(None, description="Filtrar por município"),
    evento: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    limit: int = Query(5000, ge=1, le=25000, description="Limite de registros")
):
    """Exporta os dados filtrados como arquivo JSON"""
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
        if ano:
            df = df[df['data_referencia'].str.contains(str(ano), na=False)]
        
        # Limitar resultados
        df = df.head(limit)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Nenhum dado encontrado com os filtros aplicados")
        
        # Tratar valores NaN e tipos numpy
        df_clean = df.copy()
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(lambda x: None if pd.isna(x) else x)
        
        # Converter para dicionário
        data = {
            "metadados": {
                "fonte": "SINESP VDE - Ministério da Justiça e Segurança Pública",
                "data_exportacao": pd.Timestamp.now().isoformat(),
                "total_registros": len(df_clean),
                "filtros_aplicados": {
                    "uf": uf,
                    "municipio": municipio,
                    "evento": evento,
                    "ano": ano
                }
            },
            "dados": df_clean.to_dict(orient='records')
        }
        
        # Criar arquivo temporário JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False, indent=2, default=str)
            tmp_filename = tmp_file.name
        
        # Definir nome do arquivo
        filename_parts = ["sinesp_vde"]
        if uf:
            filename_parts.append(f"uf_{uf}")
        if municipio:
            filename_parts.append(f"municipio_{municipio[:10]}")
        if evento:
            filename_parts.append(f"evento_{evento[:10]}")
        if ano:
            filename_parts.append(f"ano_{ano}")
        
        filename = "_".join(filename_parts) + ".json"
        
        def cleanup():
            try:
                os.unlink(tmp_filename)
            except:
                pass
        
        return FileResponse(
            tmp_filename,
            media_type='application/json',
            filename=filename,
            background=cleanup
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro em download_json: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar arquivo JSON")
