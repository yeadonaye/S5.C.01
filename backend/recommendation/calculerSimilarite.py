"""
Script à lancer UNE SEULE FOIS (puis à chaque fois que les mots/tfidf changent)
pour calculer la similarité entre toutes les séries et la stocker dans la
table Similarite.

Utilisation (depuis le dossier backend) :
    python recommendation/calculerSimilarite.py

Après ça, l'API n'a plus rien à calculer au démarrage : elle lit simplement
les valeurs dans la base.
"""
import os
import sys
import time

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import similarite as sim

load_dotenv()

DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise RuntimeError("La variable DB_URL est manquante dans le fichier .env.")


# Une ligne par couple ORDONNE (A, B) : on stocke A->B et B->A
# pour que la lecture se fasse avec un simple WHERE idSerie1 = ...
SQL_CREATION_TABLE = """
    CREATE TABLE IF NOT EXISTS Similarite (
        idSerie1 INTEGER NOT NULL REFERENCES Serie(idSerie) ON DELETE CASCADE,
        idSerie2 INTEGER NOT NULL REFERENCES Serie(idSerie) ON DELETE CASCADE,
        valeur   DOUBLE PRECISION NOT NULL,
        PRIMARY KEY (idSerie1, idSerie2),
        CHECK (idSerie1 <> idSerie2)
    )
"""


def calculer_et_stocker():
    conn = psycopg2.connect(DB_URL)
    try:
        debut = time.time()

        # 1. Calcul de la matrice (même code qu'avant, mais fait une seule fois)
        print("Lecture des données et calcul de la matrice de similarité...")
        ids, titres, donnees = sim.charger_donnees_series(conn)
        S = sim.construire_matrice_similarite(
            titres, donnees, exclus=sim.construire_mots_exclus()
        )
        print(f"  Matrice {S.shape[0]} x {S.shape[1]} calculée "
              f"en {time.time() - debut:.1f} s")

        # 2. Transformation en lignes (idSerie1, idSerie2, valeur), diagonale exclue
        lignes = [
            (ids[i], ids[j], float(S[i, j]))
            for i in range(len(ids))
            for j in range(len(ids))
            if i != j
        ]

        # 3. Création de la table puis remplacement complet des valeurs
        with conn:
            with conn.cursor() as cur:
                cur.execute(SQL_CREATION_TABLE)
                cur.execute("TRUNCATE TABLE Similarite")
                execute_values(
                    cur,
                    "INSERT INTO Similarite (idSerie1, idSerie2, valeur) VALUES %s",
                    lignes,
                    page_size=5000,
                )

        print(f"  {len(lignes)} similarités enregistrées dans la table Similarite "
              f"(durée totale : {time.time() - debut:.1f} s)")

    finally:
        conn.close()


if __name__ == "__main__":
    calculer_et_stocker()
