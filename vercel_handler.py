"""
Handler alternativo para Vercel - versão otimizada
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório atual ao path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Importar apenas o necessário para Vercel
try:
    from api import app
    handler = app
except Exception as e:
    print(f"Erro ao importar aplicação: {e}")
    # Fallback simples
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="API SINESP VDE - Vercel")

    @app.get("/")
    async def root():
        return {"message": "API em manutenção", "status": "loading"}

    @app.get("/health")
    async def health():
        return {"status": "ok", "environment": "vercel"}

    handler = app
