from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

import recommendation.gestionUtilisateur as gu
from api_series.auth import creer_token, utilisateur_courant
from api_series.database import get_conn

router = APIRouter(tags=["Utilisateurs"])


# MODELES DE DONNEES

class InscriptionIn(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    motDePasse: str = Field(min_length=8, max_length=128)


class ConnexionIn(BaseModel):
    email: EmailStr
    motDePasse: str


class ModificationIn(BaseModel):
    nom: str | None = Field(None, max_length=100)
    prenom: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    nouveauMotDePasse: str | None = Field(None, min_length=8, max_length=128)
    ancienMotDePasse: str | None = None  # obligatoire pour changer de mot de passe


# CREATE : POST /utilisateurs
@router.post("/utilisateurs", status_code=201)
def creer_compte(donnees: InscriptionIn, conn=Depends(get_conn)):
    res = gu.creer_compte(
        conn, donnees.nom, donnees.prenom, donnees.email, donnees.motDePasse
    )
    if not res["succes"]:
        raise HTTPException(status_code=400, detail=res["message"])

    return {"message": res["message"], "idUtilisateur": res["idUtilisateur"]}


# CONNEXION : POST /connexion
@router.post("/connexion")
def connexion(donnees: ConnexionIn, conn=Depends(get_conn)):
    utilisateur = gu.connecter_utilisateur(conn, donnees.email, donnees.motDePasse)
    if utilisateur is None:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    return {
        "token": creer_token(utilisateur["idUtilisateur"]),
        "typeToken": "bearer",
        "utilisateur": utilisateur,
    }


# READ : GET /utilisateurs/moi
@router.get("/utilisateurs/moi")
def afficher_compte(id_utilisateur: int = Depends(utilisateur_courant),
                    conn=Depends(get_conn)):
    compte = gu.afficher_compte(conn, id_utilisateur)
    if compte is None:
        raise HTTPException(status_code=404, detail="Compte introuvable.")
    return compte


# UPDATE : PUT /utilisateurs/moi
@router.put("/utilisateurs/moi")
def modifier_compte(donnees: ModificationIn,
                    id_utilisateur: int = Depends(utilisateur_courant),
                    conn=Depends(get_conn)):
    # Changer de mot de passe demande de prouver qu'on connaît l'ancien
    if donnees.nouveauMotDePasse:
        if not donnees.ancienMotDePasse:
            raise HTTPException(status_code=400,
                                detail="L'ancien mot de passe est requis.")

        compte = gu.afficher_compte(conn, id_utilisateur)
        if compte is None:
            raise HTTPException(status_code=404, detail="Compte introuvable.")

        if gu.connecter_utilisateur(conn, compte["email"],
                                    donnees.ancienMotDePasse) is None:
            raise HTTPException(status_code=403,
                                detail="Ancien mot de passe incorrect.")

    res = gu.modifier_compte(
        conn, id_utilisateur,
        nom=donnees.nom,
        prenom=donnees.prenom,
        email=donnees.email,
        nouveau_mdp=donnees.nouveauMotDePasse,
    )
    if not res["succes"]:
        statut = 404 if res["message"] == "Compte introuvable." else 400
        raise HTTPException(status_code=statut, detail=res["message"])

    return {"message": res["message"]}


# DELETE : DELETE /utilisateurs/moi
# Les notes de l'utilisateur sont supprimées en cascade (ON DELETE CASCADE)
@router.delete("/utilisateurs/moi")
def supprimer_compte(id_utilisateur: int = Depends(utilisateur_courant),
                     conn=Depends(get_conn)):
    res = gu.supprimer_compte(conn, id_utilisateur)
    if not res["succes"]:
        raise HTTPException(status_code=404, detail=res["message"])

    return {"message": res["message"]}