import numpy as np
import psycopg2

from similarite import charger_similarites


DB_URL = "postgresql://postgres.txthevshtuxweaeqmosa:sxeEsh0KLaiKhlK2@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"


def charger_notes(id_utilisateur):
    """Retourne les notes d'un utilisateur sous forme de dictionnaire."""

    conn = psycopg2.connect(DB_URL)

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT idSerie, note
            FROM Evaluer
            WHERE idUtilisateur = %s
        """, (id_utilisateur,))

        notes = dict(cur.fetchall())

        cur.close()
        return notes

    finally:
        conn.close()


def recommander(S, ids, titres, notes, n=5):
    """
    Recommande des séries à partir des notes d'un utilisateur.

    S     : matrice de similarité
    ids   : identifiants des séries dans l'ordre de S
    titres: titres dans l'ordre de S
    notes : dictionnaire {idSerie: note}
    n     : nombre de recommandations
    """

    # Associer chaque identifiant à sa position dans S
    index = {id_serie: i for i, id_serie in enumerate(ids)}

    # Ne garder que les notes des séries présentes dans la matrice
    notes_valides = {
        id_serie: note
        for id_serie, note in notes.items()
        if id_serie in index
    }

    # Cas 1 : aucune note disponible
    if not notes_valides:
        return []

    # Convertir les notes en poids : -2, -1, 0, +1, +2
    poids = np.zeros(len(ids))

    for id_serie, note in notes_valides.items():
        poids[index[id_serie]] = note - 3

    # Cas 2 : toutes les notes sont égales à 3
    if np.all(poids == 0):
        return []

    # Calculer un score pour chaque série
    scores = S @ poids

    # Exclure les séries déjà évaluées
    for id_serie in notes_valides:
        scores[index[id_serie]] = -np.inf

    # Trier les séries par score décroissant
    classement = np.argsort(scores)[::-1]

    recommandations = []

    for i in classement:
        if scores[i] == -np.inf:
            continue

        # Trouver la série évaluée qui contribue le plus au score
        contributions = S[i] * poids

        meilleure = np.argmax(contributions)

        id_source = ids[meilleure]
        titre_source = titres[meilleure]

        note_source = notes_valides[id_source]

        if contributions[meilleure] > 0:
            raison = f"Parce que vous avez aimé {titre_source} ({note_source}/5)"
        elif contributions[meilleure] < 0:
            raison = f"Malgré votre note de {note_source}/5 à {titre_source}"
        else:
            raison = "Série relativement proche de vos goûts"

        recommandations.append({
            "titre": titres[i],
            "score": round(float(scores[i]), 3),
            "raison": raison
        })

        if len(recommandations) == n:
            break

    return recommandations


if __name__ == "__main__":

    # Charger les similarités une seule fois
    S, ids, titres = charger_similarites()

    # Exemple : utilisateur dont l'identifiant est 1
    notes = charger_notes(1)

    recommandations = recommander(S, ids, titres, notes)

    if not recommandations:
        print("Pas assez de notes pour faire des recommandations.")

    else:
        print("\nVos recommandations :")

        for serie in recommandations:
            print(
                f"{serie['titre']} "
                f"(score : {serie['score']})"
            )
            print(f"  {serie['raison']}")