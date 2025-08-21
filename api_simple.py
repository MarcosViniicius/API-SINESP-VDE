# API SINESP VDE - Versão simplificada para Vercel

import os
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from data_handler import SinespDataHandler
from typing import Optional
import pandas as pd
import numpy as np
import logging
import tempfile

# Detectar se está rodando na Vercel
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('NOW_REGION') is not None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache global para handler (importante para Vercel)
_global_handler = None

def get_handler():
    """Retorna handler com cache global para otimizar performance na Vercel"""
    global _global_handler
    
    if _global_handler is None:
        try:
            _global_handler = SinespDataHandler()
            logger.info("SinespDataHandler inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar SinespDataHandler: {e}")
            _global_handler = None
    
    return _global_handler

# Inicializar handler apenas se não for Vercel (na Vercel será lazy-loaded)
handler = None if IS_VERCEL else get_handler()

app = FastAPI(
    title="API SINESP VDE", 
    version="3.0", 
    description="""
    # API SINESP VDE 2015-2025
    
    API para consulta de dados de segurança pública do Sistema Nacional de Informações de Segurança Pública (SINESP).
    
    ## 📊 Fonte dos Dados
    **Ministério da Justiça e Segurança Pública** - Última atualização: 20/08/2025
    
    ## 🔍 Endpoints Principais
    - **Metadados**: `/status`, `/info`
    - **Dimensões**: `/ufs`, `/municipios`, `/eventos`
    - **Consultas**: `/ocorrencias`
    - **Resumos**: `/resumo/vitimas`
    """,
    docs_url="/",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_handler():
    """Verifica se o handler está disponível"""
    global handler
    
    if IS_VERCEL:
        handler = get_handler()
    
    if handler is None:
        raise HTTPException(status_code=503, detail="Sistema de dados não disponível.")

@app.get("/status", summary="Status da API", tags=["Metadados"])
def status():
    """Healthcheck da API"""
    try:
        check_handler()
        total_registros = len(handler.df) if handler.df is not None else 0
        
        return {
            "status": "ok",
            "timestamp": pd.Timestamp.now().isoformat(),
            "versao_api": "3.0",
            "total_registros": total_registros,
            "periodo_cobertura": "2015-2025"
        }
    except Exception as e:
        logger.error(f"Erro em /status: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "erro",
                "timestamp": pd.Timestamp.now().isoformat(),
                "mensagem": "Sistema de dados não disponível"
            }
        )

@app.get("/info", summary="Informações da API", tags=["Metadados"])
def info():
    """Informações gerais sobre a API"""
    try:
        check_handler()
        total_registros = len(handler.df) if handler.df is not None else 0
        
        return {
            "api": "SINESP VDE 2015-2025",
            "status": "online",
            "fonte": "Ministério da Justiça e Segurança Pública",
            "total_registros": total_registros,
            "versao": "3.0"
        }
    except Exception as e:
        logger.error(f"Erro em /info: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter informações da API")

@app.get("/ufs", summary="Lista de UFs", tags=["Dimensões"])
def get_ufs():
    """Lista todas as UFs disponíveis"""
    try:
        check_handler()
        ufs = sorted(handler.df['uf'].dropna().unique().tolist())
        return {"ufs": ufs, "total": len(ufs)}
    except Exception as e:
        logger.error(f"Erro em get_ufs: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de UFs")

@app.get("/municipios", summary="Lista de municípios", tags=["Dimensões"])
def get_municipios(uf: Optional[str] = Query(None, description="Filtrar por UF")):
    """Lista municípios, opcionalmente filtrados por UF"""
    try:
        check_handler()
        df = handler.df
        
        if uf:
            df = df[df['uf'].str.upper() == uf.upper()]
            if df.empty:
                return {"municipios": [], "total": 0, "uf": uf}
        
        municipios = sorted(df['municipio'].dropna().unique().tolist())
        return {"municipios": municipios, "total": len(municipios), "uf": uf if uf else "todas"}
    except Exception as e:
        logger.error(f"Erro em get_municipios: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de municípios")

@app.get("/eventos", summary="Lista de eventos", tags=["Dimensões"])
def get_eventos():
    """Lista todos os tipos de eventos/ocorrências"""
    try:
        check_handler()
        eventos = sorted(handler.df['evento'].dropna().unique().tolist())
        return {"eventos": eventos, "total": len(eventos)}
    except Exception as e:
        logger.error(f"Erro em get_eventos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de eventos")

@app.get("/ocorrencias", summary="Buscar ocorrências", tags=["Consultas"])
def buscar_ocorrencias(
    uf: Optional[str] = Query(None, description="UF"),
    municipio: Optional[str] = Query(None, description="Município"),
    evento: Optional[str] = Query(None, description="Tipo de evento"),
    ano: Optional[int] = Query(None, description="Ano"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados")
):
    """Busca ocorrências com filtros opcionais"""
    try:
        check_handler()
        df = handler.df.copy()
        
        # Aplicar filtros
        if uf:
            df = df[df['uf'].str.contains(uf, case=False, na=False)]
        if municipio:
            df = df[df['municipio'].str.contains(municipio, case=False, na=False)]
        if evento:
            df = df[df['evento'].str.contains(evento, case=False, na=False)]
        if ano:
            df = df[df['data_referencia'].str.contains(str(ano), na=False)]
        
        total_encontrado = len(df)
        df_resultado = df.head(limit)
        
        # Converter para lista de dicionários
        resultados = []
        for _, row in df_resultado.iterrows():
            registro = {}
            for col, val in row.items():
                if pd.isna(val) or (isinstance(val, (int, float)) and np.isinf(val)):
                    registro[col] = None
                elif isinstance(val, (np.integer, np.floating)):
                    registro[col] = int(val) if isinstance(val, np.integer) else float(val)
                else:
                    registro[col] = val
            resultados.append(registro)
        
        return {
            "ocorrencias": resultados,
            "total_encontrado": total_encontrado,
            "total_exibido": len(resultados),
            "filtros": {"uf": uf, "municipio": municipio, "evento": evento, "ano": ano}
        }
    except Exception as e:
        logger.error(f"Erro em buscar_ocorrencias: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar ocorrências")

@app.get("/resumo/vitimas", summary="Resumo de vítimas", tags=["Resumos"])
def resumo_vitimas(
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ano: Optional[int] = Query(None, description="Filtrar por ano")
):
    """Totais de vítimas com filtros opcionais"""
    try:
        check_handler()
        df = handler.df.copy()
        
        # Aplicar filtros
        if uf:
            df = df[df['uf'].str.upper() == uf.upper()]
        if ano:
            df = df[df['data_referencia'].str.contains(str(ano), na=False)]
        
        if df.empty:
            return {
                "total_vitimas": 0,
                "vitimas_femininas": 0,
                "vitimas_masculinas": 0,
                "filtros": {"uf": uf, "ano": ano}
            }
        
        return {
            "total_vitimas": int(df['total_vitima'].sum()),
            "vitimas_femininas": int(df['feminino'].sum()),
            "vitimas_masculinas": int(df['masculino'].sum()),
            "vitimas_nao_informado": int(df['nao_informado'].sum()),
            "registros_analisados": len(df),
            "filtros": {"uf": uf, "ano": ano}
        }
    except Exception as e:
        logger.error(f"Erro em resumo_vitimas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar resumo de vítimas")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
