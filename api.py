from depends import *
from routes.home import router as home_router  # importa o router do outro arquivo
from routes.info import router as info_router
from routes.status import router as status_router
from routes.ufs import router as ufs_router
from routes.agentes import router as agentes_router
from routes.anos import router as anos_router
from routes.eventos import router as eventos_router
from routes.armas import router as armas_router
from routes.faixas_etarias import router as faixas_etarias_router
from routes.municipios import router as municipios_router
from routes.ocorrencias import router as ocorrencias_router
from routes.estatisticas import router as estatisticas_router
from routes.rankings import router as rankings_router
from routes.series import router as series_router
from routes.resumos import router as resumos_router
from routes.downloads import router as downloads_router
from routes.informacoes import router as informacoes_router
from routes.metodologia import router as metodologia_router
from routes.info_details import router as info_details_router
from utils import logger, handler, get_handler, check_handler, safe_get_unique_values, safe_numeric_operation

# Comando para iniciar api: python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Detectar se está rodando na Vercel
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('NOW_REGION') is not None

# Configurações específicas para Vercel
if IS_VERCEL:
    # Adicionar o diretório atual ao path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

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
    """,
    docs_url="/",  # Página principal será a documentação
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

app.include_router(home_router)
app.include_router(info_router)
app.include_router(status_router)
app.include_router(ufs_router)
app.include_router(agentes_router)
app.include_router(anos_router)
app.include_router(eventos_router)
app.include_router(armas_router)
app.include_router(faixas_etarias_router)
app.include_router(municipios_router)
app.include_router(ocorrencias_router)
app.include_router(estatisticas_router)
app.include_router(rankings_router)
app.include_router(resumos_router)
app.include_router(series_router)
app.include_router(downloads_router)
app.include_router(informacoes_router)
app.include_router(metodologia_router)
app.include_router(info_details_router)