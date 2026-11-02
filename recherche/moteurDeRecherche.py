# moteur_recherche.py
import re, os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


# Nettoyer la chaîne de caractaires qui est en entrée
def extraire_mots(requete):
    """Découpe la requête en mots (minuscules, sans ponctuation)."""
    mots = re.findall(r"[a-zà-ÿ]+", requete.lower())
    return list(set(mots))  # doublons supprimés


# Fonction principale pour la recherche
def rechercher(requete, limite=5):
    """Retourne les séries les plus pertinentes pour les mots-clés donnés."""
    mots = extraire_mots(requete)
    if not mots:
        return []

    sql = """
        SELECT s.idserie,
               s.titre,
               COUNT(DISTINCT m.idmot) AS nb_mots_trouves,
               SUM(p.tfidf)            AS score
        FROM mot m
        JOIN posseder p ON p.idmot = m.idmot
        JOIN serie s    ON s.idserie = p.idserie
        WHERE m.mot = ANY(%s)
        GROUP BY s.idserie, s.titre
        ORDER BY nb_mots_trouves DESC, score DESC
        LIMIT %s
    """

    # Utiliser la connection pour exécuter la requête
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (mots, limite))
            return cur.fetchall()


if __name__ == "__main__":
    requete = input("Mots-clés : ")
    resultats = rechercher(requete)

    if not resultats:
        print("Aucune série trouvée.")
    for rang, (id_serie, titre, nb, score) in enumerate(resultats, start=1):
        print(f"{rang}. {titre}  (mots trouvés : {nb}, score : {float(score):.4f})")