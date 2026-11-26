from fastapi import APIRouter, Query

from recherche.moteurDeRecherche import rechercher

router = APIRouter(tags=["Recherche"])


# GET /recherche?q=crash+avion+ile&limite=10
# Accessible à tout le monde (connecté ou non)
# Fonction synchrone : FastAPI l'exécute dans un thread, donc le
# serveur n'est pas bloqué pendant la requête SQL
@router.get("/recherche")
def recherche_series(
    q: str = Query(..., min_length=1, description="Un ou plusieurs mots-clés"),
    limite: int = Query(10, ge=1, le=50, description="Nombre maximum de résultats"),
):
    resultats = rechercher(q, limite)

    return {
        "requete": q,
        "nbResultats": len(resultats),
        "resultats": [
            {
                "idSerie": id_serie,
                "titre": titre,
                "nbMotsTrouves": nb_mots,
                "score": round(float(score), 4),
            }
            for id_serie, titre, nb_mots, score in resultats
        ],
    }