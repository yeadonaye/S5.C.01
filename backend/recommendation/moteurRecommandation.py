import psycopg2
from psycopg2 import errors

import gestionUtilisateur as gu


NB_RECOMMANDATIONS = 5


# SERIES LES MIEUX NOTEES

# Retourne les séries les mieux notées par l'ensemble des utilisateurs
# Triées par moyenne, puis par nombre de notes, puis par titre
def recuperer_series_mieux_notees(conn, limite=NB_RECOMMANDATIONS):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT s.idSerie, s.titre, AVG(e.note) AS moyenne,
                   COUNT(*) AS nb_notes
            FROM Serie s
            JOIN Evaluer e ON e.idSerie = s.idSerie
            GROUP BY s.idSerie, s.titre
            ORDER BY moyenne DESC, nb_notes DESC, s.titre
            LIMIT %s
        """, (limite,))

        series = cur.fetchall()

    return [
        {"idSerie": id_serie, "titre": titre,
         "moyenne": round(float(moyenne), 2), "nbNotes": nb_notes}
        for id_serie, titre, moyenne, nb_notes in series
    ]


# RECOMMANDATIONS POUR UN UTILISATEUR

# Recommande des séries selon les notes d'un utilisateur
# Les notes sont converties en poids : 5/5 -> +2, 4/5 -> +1, 3/5 -> 0,
# 2/5 -> -1, 1/5 -> -2
# Les séries proches de celles qu'il a aimées gagnent des points,
# les séries proches de celles qu'il n'a pas aimées en perdent
# Les séries déjà notées ne sont jamais recommandées
# Les similarités ne sont plus calculées ici : elles sont lues dans la table
# Similarite (remplie par le script calculerSimilarite.py)
def recommander_pour_utilisateur(conn, id_utilisateur,
                                 limite=NB_RECOMMANDATIONS):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT idSerie, note
            FROM Evaluer
            WHERE idUtilisateur = %s
        """, (id_utilisateur,))

        notes = cur.fetchall()

    if not notes:
        return gu.reponse(
            False,
            "Notez quelques séries pour obtenir des recommandations.",
            recommandations=[]
        )

    poids_total = sum(abs(note - 3) for _, note in notes)

    if poids_total == 0:
        return gu.reponse(
            False,
            "Notez des séries avec des notes différentes de 3/5 "
            "pour obtenir des recommandations.",
            recommandations=[]
        )

    # Score d'une série candidate = somme(similarité avec une série notée * poids)
    # divisée par la somme des poids en valeur absolue
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.idSerie, s.titre,
                       SUM(sim.valeur * (e.note - 3)) / %s AS score
                FROM Evaluer e
                JOIN Similarite sim ON sim.idSerie1 = e.idSerie
                JOIN Serie s ON s.idSerie = sim.idSerie2
                WHERE e.idUtilisateur = %s
                  AND e.note <> 3
                  AND s.idSerie NOT IN (
                      SELECT idSerie FROM Evaluer WHERE idUtilisateur = %s
                  )
                GROUP BY s.idSerie, s.titre
                ORDER BY score DESC, s.idSerie
                LIMIT %s
            """, (poids_total, id_utilisateur, id_utilisateur, limite))

            resultats = cur.fetchall()

    except errors.UndefinedTable:
        conn.rollback()
        return gu.reponse(
            False,
            "La table Similarite n'existe pas encore. "
            "Lancez le script calculerSimilarite.py.",
            recommandations=[]
        )

    if not resultats:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS (SELECT 1 FROM Similarite)")
            table_remplie = cur.fetchone()[0]

        if not table_remplie:
            return gu.reponse(
                False,
                "Les similarités n'ont pas encore été calculées. "
                "Lancez le script calculerSimilarite.py.",
                recommandations=[]
            )

        return gu.reponse(False, "Aucune série à recommander.",
                          recommandations=[])

    recommandations = [
        {"idSerie": id_serie, "titre": titre,
         "score": round(float(score), 3)}
        for id_serie, titre, score in resultats
    ]

    return gu.reponse(True, "Recommandations calculées.",
                      recommandations=recommandations)
