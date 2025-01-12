import os
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

# Acceder a la variable de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(OPENAI_API_KEY)

