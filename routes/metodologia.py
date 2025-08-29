from depends import *
from fastapi import APIRouter
router = APIRouter()


@router.get("/metodologia", summary="Metodologia e Notas Técnicas", tags=["Informações"])
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
