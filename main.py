from fastapi import FastAPI
from mangum import Mangum
import os
import sys

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar a aplicação do arquivo api.py
from api import app

# Handler para Vercel
handler = Mangum(app)

# Para compatibilidade, também exportamos app
__all__ = ["app", "handler"]
