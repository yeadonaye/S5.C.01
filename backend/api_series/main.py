import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for chemin in (RACINE, os.path.join(RACINE, "recommendation")):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_series import routesRecherche, routesRecommandation, routesUtilisateur, routesNote

load_dotenv()


app = FastAPI(
    title="API Séries TV",
    description="Moteur de recherche et de recommandation de séries TV",
    version="1.0.0",
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