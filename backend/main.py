# ==========================================
# MAIN - Aplicacao Principal FastAPI
# Sistema de Apoio Educacional para TEA
# ==========================================

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Adicionar diretorio backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base, ensure_columns
import models  # noqa: F401  (registra todas as tabelas no Base)
from auth import create_demo_user

from routers import (
    auth, profiles, activities, sessions, recommendations, achievements, goals, settings,
    notes, routine, plans, access, requests, moods, summary,
)

# ---- Criar tabelas ----
Base.metadata.create_all(bind=engine)
ensure_columns()


# ---- Lifespan ----
@asynccontextmanager
async def lifespan(app):
    """Executar ao iniciar o servidor."""
    db = SessionLocal()
    try:
        create_demo_user(db)
        print("=" * 50)
        print("[*] Sistema TEA - Apoio Educacional v2.0")
        print("[*] Fundamentado em ABA, TEACCH e Ed. Inclusiva")
        print("[*] API Docs: http://localhost:8000/api/docs")
        print("[*] Frontend:  http://localhost:8000")
        print("[*] Demo: admin / admin1234")
        print("=" * 50)
    finally:
        db.close()
    yield


# ---- Criar app ----
app = FastAPI(
    title="Sistema TEA - Apoio Educacional",
    description="API do Sistema de Apoio Educacional para Criancas com TEA. "
                "Fundamentado em ABA, TEACCH e principios de educacao inclusiva.",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Registrar Routers ----
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(activities.router)
app.include_router(sessions.router)
app.include_router(recommendations.router)
app.include_router(achievements.router)
app.include_router(goals.router)
app.include_router(settings.router)
app.include_router(notes.router)
app.include_router(routine.router)
app.include_router(plans.router)
app.include_router(access.router)
app.include_router(requests.router)
app.include_router(moods.router)
app.include_router(summary.router)

# ---- Servir Frontend Estatico ----
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    # Servir arquivos estaticos (CSS, JS, imagens)
    app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")
    app.mount("/img", StaticFiles(directory=os.path.join(frontend_dir, "img")), name="img")

    @app.get("/manifest.json")
    async def manifest():
        return FileResponse(os.path.join(frontend_dir, "manifest.json"))

    @app.get("/service-worker.js")
    async def service_worker():
        return FileResponse(
            os.path.join(frontend_dir, "service-worker.js"),
            media_type="application/javascript",
        )

    # Todas as rotas nao-API servem o index.html (SPA)
    @app.get("/")
    async def root():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        # Se nao for rota de API, servir index.html
        if not full_path.startswith("api/"):
            file_path = os.path.join(frontend_dir, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(frontend_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
