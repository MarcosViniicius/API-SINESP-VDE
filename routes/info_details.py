from depends import *
from fastapi import APIRouter
from utils import logger, check_handler
router = APIRouter()


@router.get("/info", summary="Informações detalhadas da API", tags=["Metadados"])
def info_detalhada(request: Request):
    """Informações detalhadas sobre a API e dados disponíveis"""
    try:
        current_handler = check_handler()
        total_registros = len(current_handler.df) if current_handler and current_handler.df is not None else 0
        colunas_disponiveis = list(current_handler.df.columns) if current_handler and current_handler.df is not None else []
        anos_disponiveis = current_handler.get_anos_disponiveis() if current_handler and current_handler.df is not None else []
        
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