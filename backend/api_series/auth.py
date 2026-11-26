import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("La variable JWT_SECRET est manquante dans le fichier .env.")

ALGORITHME = "HS256"
DUREE_TOKEN_HEURES = 24

schema_obligatoire = HTTPBearer()                    # affiché dans Swagger
schema_optionnel = HTTPBearer(auto_error=False)


def creer_token(id_utilisateur: int) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=DUREE_TOKEN_HEURES)
    return jwt.encode(
        {"sub": str(id_utilisateur), "exp": expiration},
        JWT_SECRET,
        algorithm=ALGORITHME,
    )


def _lire_token(credentials: HTTPAuthorizationCredentials) -> int:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHME])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Token invalide ou expiré.")


# Routes réservées aux utilisateurs connectés : 401 si pas de token valide
# Routes réservées aux utilisateurs connectés : 401/403 si pas de token valide
def utilisateur_courant(
    credentials: HTTPAuthorizationCredentials = Depends(schema_obligatoire),
) -> int:
    return _lire_token(credentials)


# Routes ouvertes à tous : retourne None si pas de token
# (un token présent mais invalide est quand même refusé)
def utilisateur_optionnel(
    credentials: HTTPAuthorizationCredentials | None = Depends(schema_optionnel),
) -> int | None:
    if credentials is None:
        return None
    return _lire_token(credentials)
