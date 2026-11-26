import os
import sys
from contextlib import asynccontextmanager

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for chemin in (RACINE, os.path.join(RACINE, "recommendation")):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_series import routesRecherche, routesRecommandation, routesUtilisateur, routesNote
from recommendation import moteurRecommandation

load_dotenv()


# Au démarrage : calcule la matrice de similarité une seule fois
@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = psycopg2.connect(os.getenv("DB_URL"))
    try:
        moteurRecommandation.charger_moteur_similarite(conn)
    finally:
        conn.close()
    yield


app = FastAPI(
    title="API Séries TV",
    description="Moteur de recherche et de recommandation de séries TV",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routesRecherche.router)
app.include_router(routesRecommandation.router)
app.include_router(routesUtilisateur.router)  
app.include_router(routesNote.router)         


@app.get("/", tags=["Santé"])
def accueil():
    return {"message": "API Séries TV opérationnelle"}