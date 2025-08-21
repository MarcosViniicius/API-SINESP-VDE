# Comando para iniciar api: python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

import os
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from data_handler import SinespDataHandler
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import logging
import io
import tempfile
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import time

# Detectar se está rodando na Vercel
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('NOW_REGION') is not None

# Configurar rate limiting (mais restritivo na Vercel)
rate_limit = "50/minute" if IS_VERCEL else "100/minute"
limiter = Limiter(key_func=get_remote_address)

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
    
    [Base de Dados Oficial](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2015-a-2025)
    
    ## 📋 Principais Indicadores
    - Homicídios e Feminicídios
    - Tentativas de Homicídio 
    - Estupros
    - Roubos e Furtos (Veículos, Carga, Instituições Financeiras)
    - Tráfico de Drogas e Apreensões
    - Dados de Bombeiros (APH, Combate a Incêndios, etc.)
    
    ## 🔍 Endpoints Principais
    - **Metadados**: `/api/info`, `/status`, `/info`
    - **Dimensões**: `/ufs`, `/municipios`, `/eventos`, `/agentes`, `/armas`, `/faixas-etarias`
    - **Consultas**: `/ocorrencias`
    - **Resumos**: `/resumo/vitimas`, `/resumo/faixa-etaria`, `/resumo/armas`, `/resumo/agentes`
    - **Séries**: `/series/ocorrencias`
    - **Exportação**: `/download/csv`, `/download/json`
    
    **⚠️ Importante:** Alguns indicadores podem ter múltiplas linhas no mesmo mês (somar valores).
    
    **🛡️ Rate Limiting:** 50 requests/minuto por IP na Vercel para proteger o serviço.
    """,
    docs_url="/",  # Página principal será a documentação
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Adicionar middlewares
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/home", summary="Informações da API", tags=["Metadados"])
@limiter.limit(rate_limit)
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
            f"Rate limiting: {rate_limit} por IP",
            "Alguns indicadores podem ter múltiplas linhas no mesmo mês",
            "Para dados oficiais, sempre consultar fontes governamentais"
        ],
        
        "periodo_cobertura": "2015-2025",
        "status": "online"
    }

@app.get("/status", summary="Status da API", tags=["Metadados"])
@limiter.limit(rate_limit)
def status(request: Request):
    """Healthcheck da API com informações de status"""
    try:
        check_handler()
        total_registros = len(handler.df) if handler.df is not None else 0
        memoria = handler.get_memory_usage()
        
        return {
            "status": "ok",
            "timestamp": pd.Timestamp.now().isoformat(),
            "versao_api": "3.0",
            "total_registros": total_registros,
            "memoria_mb": memoria["dataframe_size_mb"],
            "ultima_atualizacao_dados": "20/08/2025",
            "periodo_cobertura": "2015-2025",
            "uptime": "online",
            "rate_limiting": f"{rate_limit}"
        }
    except Exception as e:
        logger.error(f"Erro em /status: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "erro",
                "timestamp": pd.Timestamp.now().isoformat(),
                "mensagem": "Sistema de dados não disponível",
                "erro": str(e)
            }
        )

@app.get("/info", summary="Informações detalhadas da API", tags=["Metadados"])
@limiter.limit(rate_limit)
def info_detalhada(request: Request):
    """Informações detalhadas sobre a API e dados disponíveis"""
    try:
        check_handler()
        total_registros = len(handler.df) if handler.df is not None else 0
        colunas_disponiveis = list(handler.df.columns) if handler.df is not None else []
        anos_disponiveis = handler.get_anos_disponiveis() if handler.df is not None else []
        
        return {
            "api": {
                "nome": "SINESP VDE API",
                "versao": "3.0",
                "descricao": "API para consulta de dados de segurança pública",
                "documentacao": "/docs"
            },
            
            "dados": {
                "fonte": "Ministério da Justiça e Segurança Pública",
                "ultima_atualizacao": "20/08/2025",
                "total_registros": total_registros,
                "periodo_coberto": f"{min(anos_disponiveis) if anos_disponiveis else 'N/A'}-{max(anos_disponiveis) if anos_disponiveis else 'N/A'}",
                "anos_disponiveis": anos_disponiveis
            },
            
            "estrutura": {
                "total_colunas": len(colunas_disponiveis),
                "colunas_principais": ["uf", "municipio", "evento", "data_referencia", "total_vitima"],
                "campos_vitimas": ["feminino", "masculino", "nao_informado", "total_vitima"],
                "campos_contexto": ["agente", "arma", "faixa_etaria"],
                "todas_colunas": colunas_disponiveis
            },
            
            "descricao_campos": {
                "uf": "Unidade Federativa (estado)",
                "municipio": "Nome do município",
                "evento": "Tipo de evento/ocorrência",
                "data_referencia": "Data de referência do registro",
                "agente": "Agente envolvido na ocorrência",
                "arma": "Tipo de arma utilizada",
                "faixa_etaria": "Categoria de faixa etária das vítimas",
                "feminino": "Número de vítimas do sexo feminino",
                "masculino": "Número de vítimas do sexo masculino",
                "nao_informado": "Número de vítimas com sexo não informado",
                "total_vitima": "Total de vítimas",
                "total": "Total geral",
                "total_peso": "Peso total (para apreensões)",
                "abrangencia": "Abrangência do registro",
                "formulario": "Formulário de origem"
            },
            
            "observacoes_importantes": [
                "Alguns indicadores podem apresentar múltiplas linhas para o mesmo mês",
                "Para totais corretos, somar os valores quando necessário",
                "Dados passam por processo de consolidação até homologação",
                "API possui rate limiting de 50 requests/minuto por IP na Vercel"
            ],
            
            "link_oficial": "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2015-a-2025"
        }
    except Exception as e:
        logger.error(f"Erro em /info: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter informações da API")

def check_handler():
    """Verifica se o handler está disponível"""
    global handler
    
    if IS_VERCEL:
        handler = get_handler()
    
    if handler is None:
        raise HTTPException(status_code=503, detail="Sistema de dados não disponível. Verifique se existem arquivos de dados.")

def safe_get_unique_values(column_name: str, sort_values: bool = True):
    """Função auxiliar para obter valores únicos de uma coluna com segurança"""
    check_handler()
    
    if column_name not in handler.df.columns:
        return []
    
    try:
        # Obter valores únicos removendo NaN e valores vazios
        series = handler.df[column_name].dropna()
        
        # Converter para string e limpar
        if len(series) > 0:
            # Para colunas categóricas, converter para string
            if series.dtype.name == 'category':
                unique_values = series.cat.categories.tolist()
            else:
                unique_values = series.astype(str).unique()
            
            # Filtrar valores vazios/inválidos
            unique_values = [
                v for v in unique_values 
                if v and str(v).strip() not in ['', 'nan', 'None', 'null', '<NA>']
            ]
            
            if sort_values:
                return sorted(unique_values)
            else:
                return unique_values
        else:
            return []
    except Exception as e:
        logger.error(f"Erro ao obter valores únicos da coluna {column_name}: {e}")
        return []

def safe_numeric_operation(column_name, operation="sum", default_value=0):
    """Operação numérica segura em uma coluna"""
    try:
        check_handler()
        df = handler.df
        
        if column_name not in df.columns:
            logger.warning(f"Coluna '{column_name}' não encontrada")
            return default_value
            
        series = df[column_name]
        
        if series is None or len(series) == 0:
            return default_value
        
        # Para operações específicas
        if operation == "nunique":
            result = series.nunique()
        elif operation == "count":
            result = series.count()
        elif operation == "sum":
            # Para soma, garantir que é numérico
            if series.dtype in ['object', 'string', 'category']:
                logger.warning(f"Tentativa de soma em coluna categórica: {column_name}")
                return default_value
            numeric_series = pd.to_numeric(series, errors='coerce')
            result = numeric_series.sum()
        else:
            return default_value
        
        # Verificar se o resultado é válido usando numpy
        if pd.isna(result) or np.isinf(result):
            return default_value
        
        return int(result) if operation in ["count", "nunique"] else float(result)
    except Exception as e:
        logger.error(f"Erro em safe_numeric_operation para {column_name}: {e}")
        return default_value

@app.get("/api/info", summary="Informações da API", tags=["Informações"])
def info():
    """Informações gerais sobre a API e dados disponíveis"""
    try:
        check_handler()
        total_registros = len(handler.df) if handler.df is not None else 0
        
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

@app.get("/metodologia", summary="Metodologia e Notas Técnicas", tags=["Informações"])
@limiter.limit(rate_limit)
def metodologia(request: Request):
    """Informações metodológicas detalhadas sobre os dados do SINESP VDE"""
    return {
        "titulo": "Metodologia SINESP VDE - Sistema Nacional de Informações de Segurança Pública",
        "fonte": "Ministério da Justiça e Segurança Pública",
        "periodo_cobertura": "2015-2025",
        "ultima_atualizacao": "20/08/2025 16h15",
        
        "processo_consolidacao": {
            "fases": [
                "1. PRÉ-INCLUSÃO (data de corte)",
                "2. INCLUSÃO (revisão de boletins)",
                "3. CONSOLIDAÇÃO PRELIMINAR",
                "4. HOMOLOGAÇÃO (publicação oficial)"
            ],
            "prazo_geral": "15-16 dias do mês subsequente",
            "prazo_especial": "20-23 dias (alguns indicadores/estados)"
        },
        
        "notas_importantes": {
            "duplicacao_dados": {
                "indicadores_afetados": ["Tentativa de Homicídio", "Estupro"],
                "problema": "Podem ocorrer casos com duas linhas para o mesmo mês",
                "solucao": "Os valores devem ser somados para obter o total correto"
            },
            
            "pessoas_desaparecidas": {
                "limitacao": "Não há relação direta entre pessoas desaparecidas e localizadas",
                "motivo": "Recorte mensal é insuficiente para retificações",
                "consequencia": "Dados podem não refletir a realidade atual"
            },
            
            "contagem_metodologia": {
                "rio_de_janeiro": "Número de registros/casos, não vítimas individuais",
                "geral": "Metodologia pode variar entre estados"
            }
        },
        
        "limitacoes_regionais": {
            "amazonas": {
                "problema": "Instabilidade de internet no interior",
                "impacto": "Atraso na consolidação de dados",
                "solucao_parcial": "Dados da capital (Manaus) são reportados no prazo"
            },
            
            "rio_de_janeiro": {
                "sistema": "Sistema Integrado de Metas",
                "prazo_legal": "11º dia útil",
                "revisoes": "Recursos e retificações trimestrais (erratas)"
            }
        },
        
        "classificacao_crimes": {
            "cvli": {
                "nome": "Crimes Violentos Letais Intencionais",
                "tipos": [
                    "Homicídio Doloso",
                    "Feminicídio", 
                    "Latrocínio (Roubo seguido de morte)",
                    "Lesão Corporal seguida de morte"
                ]
            },
            
            "criterios_especiais": {
                "homicidio": "Exclui feminicídio, lesão corporal seguida de morte, latrocínio e crimes culposos",
                "feminicidio": "Por razões da condição de sexo feminino (Art. 121, § 2º, VI CP)",
                "latrocinio": "Roubo com resultado morte (Art. 157, § 3º, II CP)",
                "intervencao_agente": "Morte por agente público em exercício da função"
            }
        },
        
        "dados_bombeiros": {
            "fonte": "Secretaria de Estado de Defesa Civil",
            "categorias": [
                "Atendimento Pré-hospitalar (APH)",
                "Busca e Salvamento", 
                "Combate a Incêndios",
                "Emissão de Alvarás de Licença",
                "Vistorias de Prevenção"
            ],
            "observacao": "ISP não realiza conferência/auditoria dos microdados"
        },
        
        "apreensoes": {
            "drogas": {
                "cocaina": "Inclui pasta base, crack, oxi, merla (Portaria 344 Anvisa)",
                "maconha": "THC e derivados: prensado, haxixe, skank, óleo"
            },
            "armas": "Todas as espécies, incluindo fabricação caseira",
            "status_estruturacao": "Em processo de consolidação para padrão SINESP-VDE"
        },
        
        "links_oficiais": {
            "base_dados": "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2015-a-2025",
            "amazonas_detalhes": "https://www.ssp.am.gov.br/ssp-dados/",
            "rio_janeiro_detalhes": "https://www.ispdados.rj.gov.br/Notas.html"
        },
        
        "disclaimer": "Esta API é uma ferramenta independente para facilitar acesso aos dados públicos. Para dados oficiais, consulte sempre as fontes governamentais."
    }

@app.get("/ufs", summary="Lista de UFs", tags=["Dimensões"])
@limiter.limit(rate_limit)
def get_ufs(request: Request):
    """Lista todas as UFs disponíveis"""
    try:
        ufs = safe_get_unique_values("uf")
        return {"ufs": ufs, "total": len(ufs), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_ufs: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de UFs")

@app.get("/municipios", summary="Lista de municípios", tags=["Dimensões"])
@limiter.limit(rate_limit)
def get_municipios(request: Request, uf: Optional[str] = Query(None, description="Filtrar por UF")):
    """Lista municípios, opcionalmente filtrados por UF"""
    try:
        check_handler()
        df = handler.df
        
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

@app.get("/eventos", summary="Lista de tipos de eventos", tags=["Dimensões"])
@limiter.limit("60/minute")
def get_eventos(request: Request):
    """Lista todos os tipos de eventos/ocorrências"""
    try:
        eventos = safe_get_unique_values("evento")
        return {"eventos": eventos, "total": len(eventos), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_eventos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de eventos")

@app.get("/agentes", summary="Lista de agentes", tags=["Dimensões"])
@limiter.limit("60/minute")
def get_agentes(request: Request):
    """Lista todos os tipos de agentes envolvidos"""
    try:
        agentes = safe_get_unique_values("agente")
        return {"agentes": agentes, "total": len(agentes), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_agentes: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de agentes")

@app.get("/armas", summary="Lista de armas", tags=["Dimensões"])
@limiter.limit("60/minute")
def get_armas(request: Request):
    """Lista todos os tipos de armas"""
    try:
        armas = safe_get_unique_values("arma")
        return {"armas": armas, "total": len(armas), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_armas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de armas")

@app.get("/faixas-etarias", summary="Lista de faixas etárias", tags=["Dimensões"])
@limiter.limit("60/minute")
def get_faixas_etarias(request: Request):
    """Lista todas as categorias de faixa etária"""
    try:
        faixas = safe_get_unique_values("faixa_etaria")
        return {"faixas_etarias": faixas, "total": len(faixas), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_faixas_etarias: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de faixas etárias")

@app.get("/ocorrencias", summary="Buscar ocorrências", tags=["Consultas"])
@limiter.limit("30/minute")
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
        check_handler()
        df = handler.df.copy()
        
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

# ==== ENDPOINTS DE RESUMOS ESTATÍSTICOS ====

@app.get("/resumo/vitimas", summary="Resumo de vítimas", tags=["Resumos"])
@limiter.limit("30/minute")
def resumo_vitimas(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    evento: Optional[str] = Query(None, description="Filtrar por tipo de evento")
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

@app.get("/resumo/faixa-etaria", summary="Resumo por faixa etária", tags=["Resumos"])
@limiter.limit("30/minute")
def resumo_faixa_etaria(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ano: Optional[int] = Query(None, description="Filtrar por ano")
):
    """Distribuição de vítimas por faixa etária"""
    try:
        check_handler()
        df = handler.df.copy()
        
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

@app.get("/resumo/armas", summary="Resumo por tipo de arma", tags=["Resumos"])
@limiter.limit("30/minute")
def resumo_armas(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ano: Optional[int] = Query(None, description="Filtrar por ano")
):
    """Estatísticas por tipo de arma"""
    try:
        check_handler()
        df = handler.df.copy()
        
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

@app.get("/resumo/agentes", summary="Resumo por tipo de agente", tags=["Resumos"])
@limiter.limit("30/minute")
def resumo_agentes(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ano: Optional[int] = Query(None, description="Filtrar por ano")
):
    """Estatísticas por tipo de agente"""
    try:
        check_handler()
        df = handler.df.copy()
        
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

# ==== ENDPOINTS DE SÉRIES TEMPORAIS ====

@app.get("/series/ocorrencias", summary="Série temporal de ocorrências", tags=["Séries Temporais"])
@limiter.limit("20/minute")
def serie_temporal_ocorrencias(
    request: Request,
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    municipio: Optional[str] = Query(None, description="Filtrar por município"),
    evento: Optional[str] = Query(None, description="Filtrar por tipo de evento")
):
    """Evolução temporal (ano a ano) do total de vítimas"""
    try:
        check_handler()
        df = handler.df.copy()
        
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

@app.get("/ranking/ufs-violencia", summary="Ranking de UFs por violência", tags=["Estatísticas"])
@limiter.limit("30/minute")
def ranking_ufs_violencia(
    request: Request,
    limit: int = Query(27, ge=1, le=50, description="Limite de resultados")
):
    """Ranking das UFs com maior número de casos de violência"""
    try:
        check_handler()
        df = handler.df
        
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

# ==== ENDPOINTS DE EXPORTAÇÃO ====

@app.get("/download/csv", summary="Exportar dados como CSV", tags=["Exportação"])
@limiter.limit("5/minute")
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

@app.get("/download/json", summary="Exportar dados como JSON", tags=["Exportação"])
@limiter.limit("5/minute") 
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
        import json
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

@app.get("/estatisticas/resumo", summary="Estatísticas gerais", tags=["Estatísticas"])
@limiter.limit("30/minute")
def estatisticas_resumo(request: Request):
    """Estatísticas gerais do dataset"""
    try:
        check_handler()
        df = handler.df
        
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

@app.get("/agentes", summary="Lista de agentes", tags=["Dados"])
@limiter.limit("60/minute")
def get_agentes_legacy(request: Request):
    """Lista todos os tipos de agentes (endpoint legacy)"""
    try:
        agentes = safe_get_unique_values("agente")
        return {"agentes": agentes, "total": len(agentes), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_agentes_legacy: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de agentes")

@app.get("/armas", summary="Lista de armas", tags=["Dados"])
@limiter.limit("60/minute")
def get_armas_legacy(request: Request):
    """Lista todos os tipos de armas (endpoint legacy)"""
    try:
        armas = safe_get_unique_values("arma")
        return {"armas": armas, "total": len(armas), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_armas_legacy: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de armas")

@app.get("/anos", summary="Lista de anos disponíveis", tags=["Dados"])
@limiter.limit("60/minute")
def get_anos(request: Request):
    """Lista todos os anos disponíveis nos dados"""
    try:
        check_handler()
        anos = handler.get_anos_disponiveis()
        return {"anos": anos, "total": len(anos), "status": "sucesso"}
    except Exception as e:
        logger.error(f"Erro em get_anos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter lista de anos")

@app.get("/estatisticas/por-uf", summary="Estatísticas por UF", tags=["Estatísticas"])
@limiter.limit("30/minute")
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

@app.get("/estatisticas/por-ano", summary="Estatísticas por ano", tags=["Estatísticas"])
@limiter.limit("30/minute")
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

@app.get("/notas-metodologicas/estados", summary="Notas metodológicas por estado", tags=["Informações"])
def notas_metodologicas_estados(uf: Optional[str] = Query(None, description="UF específica (AM, RJ, etc.)")):
    """Notas metodológicas específicas por estado"""
    
    notas_estados = {
        "AM": {
            "estado": "Amazonas",
            "orgao_responsavel": "CIESP/SEAGI/SSP",
            "site_oficial": "https://www.ssp.am.gov.br/ssp-dados/",
            "prazo_inclusao": "10 dias (finaliza entre dias 15-16)",
            "prazo_consolidacao": "20-23 dias do mês subsequente",
            "limitacoes": [
                "Instabilidade intermitente de internet no interior",
                "Delegacias do interior elaboram relatórios mensais em arquivo virtual",
                "Compilação PCAM: média 30 dias do mês subsequente",
                "Apenas mandados de prisão de Manaus reportados no prazo"
            ],
            "observacoes_especiais": {
                "formulario_4": "Exceto tráfico de drogas, consolidado entre dias 20-23",
                "mandados_prisao": "Interior reportado fora do prazo devido à compilação",
                "pessoas_desaparecidas": "Muitos não retornam para finalizar procedimento"
            },
            "metodologia": "Boletins de roubo e furto revisados conforme Catálogo de Classificação Estatística"
        },
        
        "RJ": {
            "estado": "Rio de Janeiro",
            "orgao_responsavel": "Instituto de Segurança Pública (ISP)",
            "site_oficial": "https://www.ispdados.rj.gov.br/Notas.html",
            "prazo_legal": "11º dia útil (entre dias 15-16)",
            "sistema": "Sistema Integrado de Metas",
            "fases_dados": [
                "1. Dados parciais",
                "2. Dados consolidados", 
                "3. Dados consolidados com errata"
            ],
            "controle_qualidade": [
                "Corregedoria Geral de Polícia (CGPOL/SEPOL)",
                "Instituto de Segurança Pública (ISP)"
            ],
            "registro_aditamento": {
                "funcao": "Atualiza RO quando nova evidência surge",
                "exemplos": "Tentativa que evolui para óbito",
                "impacto": "Pode alterar estatística se ocorrer antes do fechamento"
            },
            "sistema_metas": {
                "lei": "Resolução SESEG Nº 932 de 19/02/2016",
                "recursos": "Analisados pela CGPOL",
                "erratas": "Publicadas trimestralmente"
            },
            "metodologia_contagem": "Data do Registro de Ocorrência",
            "observacoes": {
                "pessoas_desaparecidas": "Sem relação direta nominal com localizadas",
                "roubo_carga": "Números diferentes do IEC para SIM",
                "contagem": "Número de registros, não vítimas individuais"
            }
        }
    }
    
    if uf:
        uf_upper = uf.upper()
        if uf_upper in notas_estados:
            return {
                "uf": uf_upper,
                "notas_metodologicas": notas_estados[uf_upper],
                "status": "sucesso"
            }
        else:
            return {
                "uf": uf_upper,
                "notas_metodologicas": {},
                "observacao": "Estado sem notas metodológicas especiais documentadas",
                "status": "sem_notas_especiais"
            }
    
    return {
        "estados_com_notas": list(notas_estados.keys()),
        "total_estados": len(notas_estados),
        "notas_completas": notas_estados,
        "observacao": "Use parâmetro 'uf' para consultar estado específico",
        "status": "sucesso"
    }

@app.get("/bases-dados/oficiais", summary="Links para bases de dados oficiais", tags=["Informações"])
def bases_dados_oficiais():
    """Links diretos para as bases de dados oficiais por ano"""
    return {
        "fonte": "Ministério da Justiça e Segurança Pública",
        "pagina_principal": "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2015-a-2025",
        "ultima_atualizacao": "20/08/2025 16h15",
        
        "bases_por_ano": {
            "2025": "BASE DE DADOS 2025",
            "2024": "BASE DE DADOS 2024", 
            "2023": "BASE DE DADOS 2023",
            "2022": "BASE DE DADOS 2022",
            "2021": "BASE DE DADOS 2021",
            "2020": "BASE DE DADOS 2020",
            "2019": "BASE DE DADOS 2019",
            "2018": "BASE DE DADOS 2018",
            "2017": "BASE DE DADOS 2017",
            "2016": "BASE DE DADOS 2016",
            "2015": "BASE DE DADOS 2015"
        },
        
        "observacao_importante": {
            "tentativa_homicidio": "Podem ocorrer casos com duas linhas no mesmo mês",
            "estupro": "Podem ocorrer casos com duas linhas no mesmo mês",
            "solucao": "Somar os valores para obter total correto"
        },
        
        "orgaos_detalhamento": {
            "amazonas": {
                "orgao": "SSP/AM - CIESP/SEAGI",
                "site": "https://www.ssp.am.gov.br/ssp-dados/",
                "documento": "Nota Técnica 004 CIESP/SEAGI/SSP"
            },
            "rio_de_janeiro": {
                "orgao": "Instituto de Segurança Pública do RJ",
                "site": "https://www.ispdados.rj.gov.br/Notas.html",
                "sistema": "Sistema Integrado de Metas"
            }
        },
        
        "status": "ativo"
    }

@app.get("/classificacoes/criminais", summary="Classificações de crimes no SINESP VDE", tags=["Informações"])
@limiter.limit("30/minute")
def classificacoes_criminais(request: Request):
    """Classificações detalhadas dos tipos criminais conforme metodologia SINESP VDE"""
    return {
        "fonte": "Metodologia Instituto de Segurança Pública - RJ (Referência Nacional)",
        "base_legal": "Código Penal Brasileiro e legislação específica",
        
        "crimes_violentos_letais_intencionais": {
            "1_homicidio_doloso": {
                "definicao": "Morte de alguém com indício de crime ou agressão externa",
                "exclui": ["Feminicídio", "Lesão Corporal Seguida de Morte", "Latrocínio", "Crimes culposos"],
                "inclui": [
                    "Morte violenta por acidente de trânsito com dolo",
                    "Encontro de ossada/cadáver com indício criminal",
                    "Morte a esclarecer com suspeita"
                ],
                "contagem": "Total de vítimas (M/F/NI)"
            },
            
            "2_latrocinio": {
                "definicao": "Roubo seguido de morte",
                "base_legal": "Art. 157, § 3º, II do Código Penal",
                "caracteristica": "Subtração + violência/ameaça + resultado morte",
                "contagem": "Total de vítimas (M/F/NI)"
            },
            
            "3_lesao_corporal_morte": {
                "definicao": "Ofensa à integridade corporal com resultado morte",
                "base_legal": "Art. 129, § 3º do Código Penal", 
                "inclui": "Violência doméstica e familiar",
                "contagem": "Total de vítimas (M/F/NI)"
            },
            
            "4_feminicidio": {
                "definicao": "Homicídio contra mulher por razão de gênero",
                "base_legal": "Art. 121, § 2º, VI do Código Penal",
                "caracteristica": "Por razões da condição de sexo feminino",
                "contagem": "Total de vítimas"
            }
        },
        
        "outros_crimes_violentos": {
            "tentativa_homicidio": {
                "definicao": "Homicídio tentado (execução iniciada, não consumada)",
                "observacao": "Pode apresentar múltiplas linhas no mesmo mês",
                "inclui": "Tentativa de feminicídio",
                "contagem": "Total de vítimas (M/F/NI)"
            },
            
            "intervencao_agente_estado": {
                "definicao": "Morte por agente público em exercício da função",
                "condicoes": "Em serviço ou em razão dele",
                "requisito": "Hipóteses de exclusão de ilicitude",
                "contagem": "Total de vítimas (M/F/NI)"
            },
            
            "estupro": {
                "definicao": "Estupros e estupros de vulneráveis consumados",
                "observacao": "Pode apresentar múltiplas linhas no mesmo mês",
                "contagem_especial": "Crimes acompanhados de estupro contam também aqui",
                "contagem": "Total de vítimas (M/F/NI)"
            }
        },
        
        "crimes_patrimonio": {
            "roubo_veiculo": {
                "definicao": "Subtração de veículo inteiro mediante violência/ameaça",
                "inclui": ["Automóveis", "Caminhões sem carga", "Motocicletas", "Transporte coletivo"],
                "exclui": ["Roubos de peças", "Roubos a passageiros no interior"],
                "contagem": "Total de ocorrências"
            },
            
            "roubo_instituicao_financeira": {
                "definicao": "Roubo de valores de/em instituição financeira",
                "inclui": ["Bancos", "Caixas eletrônicos", "Financeiras", "Casas de câmbio"],
                "exclui": "Roubos a pessoas físicas em estabelecimentos financeiros",
                "contagem": "Total de ocorrências"
            },
            
            "roubo_carga": {
                "definicao": "Roubo de carga transportada",
                "inclui": ["Veículo + carga", "Todos tipos de carga comercial", "Qualquer modal de transporte"],
                "exclui": "Valores fiduciários (carros-fortes)",
                "base_legal": "Lei 11.442/2007",
                "contagem": "Total de ocorrências"
            },
            
            "furto_veiculo": {
                "definicao": "Subtração de veículo sem violência/ameaça",
                "tipos": ["Simples", "Qualificado", "Agravado", "Coisa comum"],
                "contagem": "Total de ocorrências"
            }
        },
        
        "drogas_e_armas": {
            "trafico_drogas": {
                "definicao": "Registros com natureza Tráfico de Drogas",
                "base_legal": "Lei 11.343/06",
                "inclui": ["Associação", "Financiamento", "Uso de violência", "Envolvimento de menores"],
                "contagem": "Total de ocorrências"
            },
            
            "apreensao_cocaina": {
                "definicao": "Substâncias com cocaína conforme Portaria 344 Anvisa",
                "formas": ["Pó", "Pasta base", "Crack", "Oxi", "Merla"],
                "contagem": "Total por peso (kg)"
            },
            
            "apreensao_maconha": {
                "definicao": "Substâncias com THC conforme Portaria 344/98 Anvisa",
                "formas": ["Prensado", "Haxixe", "Skank", "Óleo/Resina"],
                "contagem": "Total por peso (kg)"
            },
            
            "arma_fogo_apreendida": {
                "definicao": "Armas de qualquer tipo e espécie",
                "inclui": "Fabricação caseira",
                "contagem": "Total por espécie"
            }
        },
        
        "mortes_especiais": {
            "morte_esclarecer": {
                "definicao": "Morte sem indícios de crime ou agressão externa",
                "caracteristica": "Morte natural/acidental",
                "contagem": "Total de vítimas (M/F/NI)"
            },
            
            "morte_transito": {
                "definicao": "Homicídio culposo em circunstâncias de trânsito",
                "base_legal": "Art. 302 do Código de Trânsito Brasileiro",
                "caracteristica": "Negligência, imprudência ou imperícia",
                "contagem": "Total de vítimas (M/F/NI)"
            },
            
            "morte_agente_estado": {
                "definicao": "Morte de profissionais de segurança pública",
                "categorias": ["PM", "PC", "GM", "P.Penal", "Perícia", "BM"],
                "observacao": "Critérios de ativa/exercício variam por estado",
                "contagem": "Total de vítimas por categoria"
            },
            
            "suicidio": {
                "definicao": "Morte por ato intencional próprio",
                "suicidio_agente": "Específico para profissionais segurança pública",
                "contagem": "Total de vítimas (M/F/NI)"
            }
        },
        
        "pessoas_desaparecidas": {
            "desaparecida": {
                "definicao": "Pessoa desaparecida com/sem motivação conhecida",
                "contagem": "Total por gênero e idade (maior/menor)",
                "limitacao": "Sem relação direta com pessoas localizadas"
            },
            
            "localizada": {
                "definicao": "Pessoa encontrada após desaparecimento",
                "contagem": "Total por gênero e idade (maior/menor)",
                "observacao": "Pode não corresponder temporalmente aos desaparecimentos"
            }
        },
        
        "sistema_prisional": {
            "mandado_prisao_cumprido": {
                "definicao": "Boletins com mandado de prisão cumprido",
                "contagem": "Total de pessoas (pode haver múltiplas por registro)",
                "variacao_regional": "Amazonas: apenas Manaus no prazo regular"
            }
        },
        
        "bombeiros": {
            "atendimento_pre_hospitalar": {
                "definicao": "Emergências médicas atendidas",
                "sigla": "APH",
                "contagem": "Total de atendimentos"
            },
            
            "busca_salvamento": {
                "definicao": "Operações de busca e resgate",
                "contagem": "Total de atendimentos"
            },
            
            "combate_incendios": {
                "definicao": "Operações de extinção de incêndios",
                "contagem": "Total de atendimentos"
            },
            
            "alvara_licenca": {
                "definicao": "Alvarás emitidos para unidades locais",
                "finalidade": "Prevenção de incêndio e pânico",
                "contagem": "Total de emissões"
            },
            
            "vistorias": {
                "definicao": "Vistorias de prevenção realizadas",
                "finalidade": "Prevenção de incêndio e pânico",
                "contagem": "Total de vistorias"
            }
        },
        
        "observacoes_gerais": {
            "contagem_variavel": "Metodologia pode variar entre estados (registros vs. vítimas)",
            "duplicacao_mensal": "Tentativa homicídio e estupro podem ter múltiplas linhas",
            "consolidacao": "Dados passam por várias fases até homologação final",
            "atualizacao": "Registros podem ser retificados posteriormente"
        }
    }
