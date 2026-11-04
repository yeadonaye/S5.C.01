import numpy as np
import psycopg2

import gestionUtilisateur as gu
import similarite as sim  # Change this if your similarity file has another name.

""" $env:DATABASE_URL = "postgresql://postgres.txthevshtuxweaeqmosa:sxeEsh0KLaiKhlK2@aws-0-eu-west-1.pooler.supabase.com:5432/postgres" """

NB_RECOMMANDATIONS = 5
_moteur_similarite = None


# =========================================================
# RECOMMANDATIONS
# =========================================================

def charger_moteur_similarite(conn):
    """Charge la matrice de similarité une seule fois."""
    global _moteur_similarite

    if _moteur_similarite is None:
        ids, titres, donnees = sim.charger_donnees(conn)
        exclus = sim.construire_exclus()
        matrice = sim.construire_S(titres, donnees, exclus=exclus)

        _moteur_similarite = {
            "ids": ids,
            "titres": titres,
            "matrice": matrice,
            "index_par_id": {
                id_serie: index for index, id_serie in enumerate(ids)
            },
        }

    return _moteur_similarite


def afficher_series_mieux_notees(conn):
    """Affiche les séries les mieux notées par l'ensemble des utilisateurs."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.titre, AVG(e.note) AS moyenne, COUNT(*) AS nb_notes
            FROM Serie s
            JOIN Evaluer e ON e.idSerie = s.idSerie
            GROUP BY s.idSerie, s.titre
            ORDER BY moyenne DESC, nb_notes DESC, s.titre
            LIMIT %s
            """,
            (NB_RECOMMANDATIONS,),
        )
        series = cur.fetchall()

    print("\n--- Séries les mieux notées ---")

    if not series:
        print("Aucune série n'a encore été notée.")
        return

    for rang, (titre, moyenne, nb_notes) in enumerate(series, start=1):
        print(
            f"{rang}. {titre} — {moyenne:.2f}/5 "
            f"({nb_notes} note(s))"
        )


def recommander_pour_utilisateur(conn, id_utilisateur):
    """Recommande des séries selon les notes d'un utilisateur connecté."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT idSerie, note
            FROM Evaluer
            WHERE idUtilisateur = %s
            """,
            (id_utilisateur,),
        )
        notes = cur.fetchall()

    if not notes:
        print("\nVous n'avez pas encore noté de série.")
        print("Notez quelques séries pour obtenir des recommandations.")
        return

    moteur = charger_moteur_similarite(conn)
    ids = moteur["ids"]
    titres = moteur["titres"]
    matrice = moteur["matrice"]
    index_par_id = moteur["index_par_id"]

    # Ne recommande pas les séries que l'utilisateur a déjà notées.
    ids_deja_notes = {id_serie for id_serie, _ in notes}

    # Convertit les notes en poids :
    # 5/5 -> +2 ; 4/5 -> +1 ; 3/5 -> 0 ; 2/5 -> -1 ; 1/5 -> -2.
    notes_ponderees = [
        (id_serie, note - 3)
        for id_serie, note in notes
        if note != 3 and id_serie in index_par_id
    ]

    if not notes_ponderees:
        print("\nToutes vos notes sont à 3/5.")
        print("Notez des séries avec des notes différentes pour affiner")
        print("vos recommandations.")
        return

    scores = np.zeros(len(titres), dtype=float)
    poids_total = sum(abs(poids) for _, poids in notes_ponderees)

    # Les séries similaires aux séries appréciées gagnent des points.
    # Les séries similaires aux séries peu appréciées en perdent.
    for id_serie, poids in notes_ponderees:
        index_serie = index_par_id[id_serie]
        scores += matrice[index_serie] * poids

    scores /= poids_total

    candidats = [
        index
        for index, id_serie in enumerate(ids)
        if id_serie not in ids_deja_notes
    ]
    candidats.sort(key=lambda index: scores[index], reverse=True)
    meilleurs = candidats[:NB_RECOMMANDATIONS]

    print("\n--- Vos recommandations ---")

    if not meilleurs:
        print("Aucune série à recommander.")
        return

    for rang, index in enumerate(meilleurs, start=1):
        print(f"{rang}. {titres[index]} (score : {scores[index]:.3f})")


# =========================================================
# MENU D'UN UTILISATEUR CONNECTE
# =========================================================

def menu_utilisateur_connecte(conn, id_utilisateur):
    while True:
        print("\n=== MON ESPACE ===")
        print("1. Lire mon compte")
        print("2. Modifier mon compte")
        print("3. Supprimer mon compte")
        print("4. Gestion de mes notes")
        print("5. Obtenir mes recommandations")
        print("0. Déconnexion")

        choix = input("Votre choix : ").strip()

        if choix == "1":
            gu.afficher_compte(conn, id_utilisateur)

        elif choix == "2":
            gu.modifier_compte(conn, id_utilisateur)

        elif choix == "3":
            if gu.supprimer_compte(conn, id_utilisateur):
                return

        elif choix == "4":
            gu.menu_notes(conn, id_utilisateur)

        elif choix == "5":
            recommander_pour_utilisateur(conn, id_utilisateur)

        elif choix == "0":
            print("Déconnexion.")
            return

        else:
            print("Choix invalide.")


# =========================================================
# MENU PRINCIPAL
# =========================================================

def main():
    try:
        conn = gu.connecter()
        print("Connexion à la base réussie.")

    except psycopg2.Error as e:
        print("Impossible de se connecter à la base :", e)
        return

    try:
        while True:
            print("\n=== RECOMMANDATION DE SERIES ===")
            print("1. Voir les séries les mieux notées")
            print("2. Créer un compte")
            print("3. Se connecter")
            print("0. Quitter")

            choix = input("Votre choix : ").strip()

            if choix == "1":
                afficher_series_mieux_notees(conn)

            elif choix == "2":
                gu.creer_compte(conn)

            elif choix == "3":
                id_utilisateur = gu.connecter_utilisateur(conn)

                if id_utilisateur is not None:
                    menu_utilisateur_connecte(conn, id_utilisateur)

            elif choix == "0":
                print("Au revoir.")
                break

            else:
                print("Choix invalide.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()