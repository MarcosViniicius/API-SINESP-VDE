from fastapi import FastAPI
from mangum import Mangum
import os
import sys

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar a aplicação do arquivo api.py
try:
    from api import app
except ImportError as e:
    print(f"Erro ao importar api: {e}")
    # Fallback: criar uma aplicação básica
    app = FastAPI(title="API SINESP VDE", description="Erro na inicialização")
    
    @app.get("/")
    def root():
        return {"error": "Erro na inicialização da API", "details": str(e)}

# Handler para Vercel (com configurações específicas)
handler = Mangum(app, lifespan="off")

# Para compatibilidade, também exportamos app
__all__ = ["app", "handler"]
