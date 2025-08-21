from mangum import Mangum
from api_simple import app

# Handler principal para Vercel
handler = Mangum(app, lifespan="off")

# Para compatibilidade
def lambda_handler(event, context):
    return handler(event, context)
