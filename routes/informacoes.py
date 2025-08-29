from depends import *
from fastapi import APIRouter
router = APIRouter()


@router.get("/notas-metodologicas/estados", summary="Notas metodológicas por estado", tags=["Informações"])
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

@router.get("/bases-dados/oficiais", summary="Links para bases de dados oficiais", tags=["Informações"])
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

@router.get("/classificacoes/criminais", summary="Classificações de crimes no SINESP VDE", tags=["Informações"])
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
