import sys
import os
import traceback

# Adiciona o diretório raiz ao sys.path para importar app.py e modules
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="GEONIV Error Diagnostic")
    tb_str = traceback.format_exc()

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    async def catch_all(full_path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "Vercel Startup Import Error",
                "error": str(e),
                "type": type(e).__name__,
                "traceback": tb_str
            }
        )
