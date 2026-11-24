import numpy as np

import gestionUtilisateur as gu
import similarite as sim


NB_RECOMMANDATIONS = 5

# Contient la matrice de similarité et ses données une fois calculées
# Reste à None tant que le moteur n'a pas été chargé
_cache_matrice_similarite = None


# MOTEUR DE SIMILARITE

# Charge la matrice de similarité une seule fois et la garde en mémoire
# Les appels suivants réutilisent directement le résultat déjà calculé
def charger_moteur_similarite(conn):
    global _cache_matrice_similarite

    if _cache_matrice_similarite is None:
        ids, titres, donnees = sim.charger_donnees_series(conn)
        exclus = sim.construire_mots_exclus()
        matrice = sim.construire_matrice_similarite(
            titres, donnees, exclus=exclus
        )

        _cache_matrice_similarite = {
            "ids": ids,
            "titres": titres,
            "matrice": matrice,
            "index_par_id": {
                id_serie: index for index, id_serie in enumerate(ids)
            },
        }

    return _cache_matrice_similarite


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

    moteur = charger_moteur_similarite(conn)
    ids = moteur["ids"]
    titres = moteur["titres"]
    matrice = moteur["matrice"]
    index_par_id = moteur["index_par_id"]

    ids_deja_notes = {id_serie for id_serie, _ in notes}

    notes_ponderees = [
        (id_serie, note - 3)
        for id_serie, note in notes
        if note != 3 and id_serie in index_par_id
    ]

    if not notes_ponderees:
        return gu.reponse(
            False,
            "Notez des séries avec des notes différentes de 3/5 "
            "pour obtenir des recommandations.",
            recommandations=[]
        )

    scores = np.zeros(len(titres), dtype=float)
    poids_total = sum(abs(poids) for _, poids in notes_ponderees)

    for id_serie, poids in notes_ponderees:
        scores += matrice[index_par_id[id_serie]] * poids

    scores /= poids_total

    candidats = [
        index for index, id_serie in enumerate(ids)
        if id_serie not in ids_deja_notes
    ]
    candidats.sort(key=lambda index: scores[index], reverse=True)

    recommandations = [
        {"idSerie": ids[index], "titre": titres[index],
         "score": round(float(scores[index]), 3)}
        for index in candidats[:limite]
    ]

    if not recommandations:
        return gu.reponse(False, "Aucune série à recommander.",
                          recommandations=[])

    return gu.reponse(True, "Recommandations calculées.",
                      recommandations=recommandations)