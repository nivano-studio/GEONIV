import sys
import os

# Adiciona o diretório raiz ao path para importação do aplicativo FastAPI
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
