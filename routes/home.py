from depends import *
from fastapi import APIRouter
router = APIRouter()


@router.get("/api/home", summary="Informações da API", tags=["Metadados"])
def homepage_api(request: Request):
    """Informações da API (endpoint legacy)"""
    return {
        "titulo": "API SINESP VDE 2015-2025",
        "descricao": "API para consulta de dados de segurança pública do Sistema Nacional de Informações de Segurança Pública",
        "versao": "3.0",
        "fonte": "Ministério da Justiça e Segurança Pública",
        "ultima_atualizacao": "20/08/2025",
        
        "links_uteis": {
            "documentacao": "/",
            "redoc": "/redoc",
            "api_info": "/info",
            "status": "/status",
            "base_dados_oficial": "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2015-a-2025"
        },
        
        "endpoints_principais": {
            "metadados": ["/api/home", "/status", "/info"],
            "dimensoes": ["/ufs", "/municipios", "/eventos", "/agentes", "/armas", "/faixas-etarias"],
            "consultas": ["/ocorrencias"],
            "resumos": ["/resumo/vitimas", "/resumo/faixa-etaria", "/resumo/armas", "/resumo/agentes"],
            "series_temporais": ["/series/ocorrencias"],
            "exportacao": ["/download/csv", "/download/json"]
        },
        
        "observacoes": [
            f"Rate limiting: {"50/minute"} por IP",
            "Alguns indicadores podem ter múltiplas linhas no mesmo mês",
            "Para dados oficiais, sempre consultar fontes governamentais"
        ],
        
        "periodo_cobertura": "2015-2025",
        "status": "online"
    }