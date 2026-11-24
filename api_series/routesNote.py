from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import recommendation.gestionUtilisateur as gu
from api_series.auth import utilisateur_courant
from api_series.database import get_conn

router = APIRouter(tags=["Notes"])


# MODELES DE DONNEES

class NoteCreationIn(BaseModel):
    idSerie: int
    note: int = Field(ge=1, le=5)


class NoteModificationIn(BaseModel):
    note: int = Field(ge=1, le=5)


# Traduit le message d'erreur de gestionUtilisateur en code HTTP
def _erreur_http(message: str) -> HTTPException:
    if message == "Cette valeur existe déjà dans la base.":
        return HTTPException(status_code=409, detail="Cette série est déjà notée.")
    if message.startswith("Cette opération est impossible"):
        return HTTPException(status_code=404, detail="Série ou compte introuvable.")
    if message.startswith("Aucune note trouvée"):
        return HTTPException(status_code=404, detail=message)
    return HTTPException(status_code=400, detail=message)


# LISTE DES SERIES : GET /series (public)
@router.get("/series")
def liste_series(conn=Depends(get_conn)):
    return gu.afficher_series(conn)


# CREATE : POST /notes
@router.post("/notes", status_code=201)
def creer_note(donnees: NoteCreationIn,
               id_utilisateur: int = Depends(utilisateur_courant),
               conn=Depends(get_conn)):
    res = gu.creer_note(conn, id_utilisateur, donnees.idSerie, donnees.note)
    if not res["succes"]:
        raise _erreur_http(res["message"])

    return {"message": res["message"]}


# READ : GET /notes (toutes les notes de l'utilisateur connecté)
@router.get("/notes")
def afficher_mes_notes(id_utilisateur: int = Depends(utilisateur_courant),
                       conn=Depends(get_conn)):
    return gu.afficher_mes_notes(conn, id_utilisateur)


# READ : GET /notes/{idSerie}
@router.get("/notes/{id_serie}")
def afficher_ma_note(id_serie: int,
                     id_utilisateur: int = Depends(utilisateur_courant),
                     conn=Depends(get_conn)):
    note = gu.afficher_ma_note(conn, id_utilisateur, id_serie)
    if note is None:
        raise HTTPException(status_code=404, detail="Aucune note trouvée pour cette série.")
    return note


# UPDATE : PUT /notes/{idSerie}
@router.put("/notes/{id_serie}")
def modifier_note(id_serie: int, donnees: NoteModificationIn,
                  id_utilisateur: int = Depends(utilisateur_courant),
                  conn=Depends(get_conn)):
    res = gu.modifier_note(conn, id_utilisateur, id_serie, donnees.note)
    if not res["succes"]:
        raise _erreur_http(res["message"])

    return {"message": res["message"]}


# DELETE : DELETE /notes/{idSerie}
@router.delete("/notes/{id_serie}")
def supprimer_note(id_serie: int,
                   id_utilisateur: int = Depends(utilisateur_courant),
                   conn=Depends(get_conn)):
    res = gu.supprimer_note(conn, id_utilisateur, id_serie)
    if not res["succes"]:
        raise _erreur_http(res["message"])

    return {"message": res["message"]}