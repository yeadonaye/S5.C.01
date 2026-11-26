from fastapi import APIRouter, Depends, HTTPException, Query

import recommendation.gestionUtilisateur as gu
from api_series.auth import utilisateur_optionnel
from api_series.database import get_conn
from recommendation import moteurRecommandation as moteur

router = APIRouter(tags=["Recommandation"])


# GET /recommandations
# Sans token : séries les mieux notées / Avec token : recommandations personnalisées
@router.get("/recommandations")
def recommandations(
    limite: int = Query(5, ge=1, le=20, description="Nombre de recommandations"),
    id_utilisateur: int | None = Depends(utilisateur_optionnel),
    conn=Depends(get_conn),
):
    if id_utilisateur is None:
        return {
            "type": "populaires",
            "message": "Séries les mieux notées par la communauté.",
            "recommandations": moteur.recuperer_series_mieux_notees(conn, limite),
        }

    if gu.afficher_compte(conn, id_utilisateur) is None:
        raise HTTPException(status_code=401, detail="Compte introuvable.")

    res = moteur.recommander_pour_utilisateur(conn, id_utilisateur, limite)
    return {
        "type": "personnalisees",
        "message": res["message"],
        "recommandations": res["recommandations"],
    }