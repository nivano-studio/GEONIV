import sys
import os

# Adiciona o diretório raiz ao sys.path para importar app.py e modules
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Top-level ASGI entrypoints explicitamente definidos para o scanner do Vercel
application = app
handler = app
