import os
import hmac
import hashlib
import secrets
import getpass

import psycopg2
from psycopg2 import errors


# =========================================================
# CONNEXION A LA BASE DE DONNEES
# =========================================================

DB_URL = os.environ.get("DATABASE_URL")

if not DB_URL:
    raise RuntimeError(
        "La variable d'environnement DATABASE_URL est manquante."
    )


def connecter():
    return psycopg2.connect(DB_URL)


# =========================================================
# GESTION DES MOTS DE PASSE
# =========================================================

def hasher_mot_de_passe(mot_de_passe):
    sel = secrets.token_bytes(16)

    empreinte = hashlib.scrypt(
        mot_de_passe.encode("utf-8"),
        salt=sel,
        n=16384,
        r=8,
        p=1
    )

    return sel.hex() + ":" + empreinte.hex()


def verifier_mot_de_passe(mot_de_passe, hash_stocke):
    try:
        sel_hex, empreinte_hex = hash_stocke.split(":")
        sel = bytes.fromhex(sel_hex)
        empreinte_attendue = bytes.fromhex(empreinte_hex)

        empreinte = hashlib.scrypt(
            mot_de_passe.encode("utf-8"),
            salt=sel,
            n=16384,
            r=8,
            p=1
        )

        return hmac.compare_digest(empreinte, empreinte_attendue)

    except (ValueError, TypeError):
        return False


# =========================================================
# OUTILS COMMUNS
# =========================================================

def lire_texte(message):
    return input(message).strip()


def lire_mot_de_passe(message):
    return getpass.getpass(message)


def lire_entier(message):
    try:
        return int(lire_texte(message))
    except ValueError:
        print("Veuillez saisir un nombre valide.")
        return None


def afficher_message_erreur(e):
    if isinstance(e, errors.UniqueViolation):
        print("Cette valeur existe déjà dans la base.")
    elif isinstance(e, errors.ForeignKeyViolation):
        print("Cette opération est impossible : référence invalide.")
    else:
        print("Une erreur est survenue :", e)


# =========================================================
# CRUD UTILISATEUR
# CREATE -> READ -> UPDATE -> DELETE
# =========================================================

# CREATE — créer un compte

def creer_compte(conn):
    nom = lire_texte("Nom : ")
    prenom = lire_texte("Prénom : ")
    email = lire_texte("Email : ").lower()
    mot_de_passe = lire_mot_de_passe("Mot de passe : ")

    if not nom or not prenom or not email or not mot_de_passe:
        print("Tous les champs sont obligatoires.")
        return

    hash_mdp = hasher_mot_de_passe(mot_de_passe)

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO Utilisateur
                        (nom, prenom, email, motDePasseHash)
                    VALUES (%s, %s, %s, %s)
                    RETURNING idUtilisateur
                """, (nom, prenom, email, hash_mdp))

                id_utilisateur = cur.fetchone()[0]

        print(f"Compte créé avec succès. ID : {id_utilisateur}")

    except psycopg2.Error as e:
        afficher_message_erreur(e)


# READ — afficher mon compte

def afficher_compte(conn, id_utilisateur):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT nom, prenom, email, dateInscription
            FROM Utilisateur
            WHERE idUtilisateur = %s
        """, (id_utilisateur,))

        utilisateur = cur.fetchone()

    if utilisateur is None:
        print("Compte introuvable.")
        return

    nom, prenom, email, date_inscription = utilisateur

    print("\n--- Mon compte ---")
    print("Nom :", nom)
    print("Prénom :", prenom)
    print("Email :", email)
    print("Inscription :", date_inscription)


# UPDATE — modifier mon compte

def modifier_compte(conn, id_utilisateur):
    print("\n--- Modifier mon compte ---")
    print("Laissez un champ vide pour le conserver.")

    nom = lire_texte("Nouveau nom : ")
    prenom = lire_texte("Nouveau prénom : ")
    email = lire_texte("Nouvel email : ").lower()
    nouveau_mdp = lire_mot_de_passe(
        "Nouveau mot de passe (vide pour conserver) : "
    )

    try:
        with conn:
            with conn.cursor() as cur:
                if nom:
                    cur.execute("""
                        UPDATE Utilisateur
                        SET nom = %s
                        WHERE idUtilisateur = %s
                    """, (nom, id_utilisateur))

                if prenom:
                    cur.execute("""
                        UPDATE Utilisateur
                        SET prenom = %s
                        WHERE idUtilisateur = %s
                    """, (prenom, id_utilisateur))

                if email:
                    cur.execute("""
                        UPDATE Utilisateur
                        SET email = %s
                        WHERE idUtilisateur = %s
                    """, (email, id_utilisateur))

                if nouveau_mdp:
                    hash_mdp = hasher_mot_de_passe(nouveau_mdp)

                    cur.execute("""
                        UPDATE Utilisateur
                        SET motDePasseHash = %s
                        WHERE idUtilisateur = %s
                    """, (hash_mdp, id_utilisateur))

        print("Compte modifié avec succès.")

    except psycopg2.Error as e:
        afficher_message_erreur(e)


# DELETE — supprimer mon compte

def supprimer_compte(conn, id_utilisateur):
    confirmation = lire_texte(
        "Supprimer définitivement votre compte ? (oui/non) : "
    ).lower()

    if confirmation != "oui":
        print("Suppression annulée.")
        return False

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM Utilisateur
                    WHERE idUtilisateur = %s
                """, (id_utilisateur,))

        print("Compte supprimé.")
        return True

    except psycopg2.Error as e:
        afficher_message_erreur(e)
        return False


# =========================================================
# CONNEXION UTILISATEUR
# =========================================================

def connecter_utilisateur(conn):
    email = lire_texte("Email : ").lower()
    mot_de_passe = lire_mot_de_passe("Mot de passe : ")

    with conn.cursor() as cur:
        cur.execute("""
            SELECT idUtilisateur, nom, prenom, motDePasseHash
            FROM Utilisateur
            WHERE email = %s
        """, (email,))

        utilisateur = cur.fetchone()

    if utilisateur is None:
        print("Email ou mot de passe incorrect.")
        return None

    id_utilisateur, nom, prenom, hash_stocke = utilisateur

    if not verifier_mot_de_passe(mot_de_passe, hash_stocke):
        print("Email ou mot de passe incorrect.")
        return None

    print(f"\nBienvenue {prenom} {nom} !")
    return id_utilisateur


# =========================================================
# CRUD NOTES
# CREATE -> READ -> UPDATE -> DELETE
# =========================================================

# CREATE — créer une note
# La liste des séries permet de choisir l'ID à noter.

def creer_note(conn, id_utilisateur):
    afficher_series(conn)

    id_serie = lire_entier("\nID de la série à noter : ")
    if id_serie is None:
        return

    note = lire_entier("Note sur 5 : ")
    if note is None:
        return

    if not 1 <= note <= 5:
        print("La note doit être comprise entre 1 et 5.")
        return

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO Evaluer (idUtilisateur, idSerie, note)
                    VALUES (%s, %s, %s)
                """, (id_utilisateur, id_serie, note))

        print("Note créée avec succès.")

    except psycopg2.Error as e:
        afficher_message_erreur(e)


# READ — afficher toutes mes notes

def afficher_mes_notes(conn, id_utilisateur):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT s.idSerie, s.titre, e.note, e.dateEvaluation
            FROM Evaluer e
            JOIN Serie s ON s.idSerie = e.idSerie
            WHERE e.idUtilisateur = %s
            ORDER BY s.titre
        """, (id_utilisateur,))

        notes = cur.fetchall()

    print("\n--- Toutes mes notes ---")

    if not notes:
        print("Vous n'avez encore noté aucune série.")
        return

    for id_serie, titre, note, date in notes:
        print(f"ID {id_serie} - {titre} : {note}/5 (le {date})")


# READ — afficher ma note pour une série précise

def afficher_ma_note(conn, id_utilisateur):
    id_serie = lire_entier("ID de la série : ")
    if id_serie is None:
        return

    with conn.cursor() as cur:
        cur.execute("""
            SELECT s.titre, e.note, e.dateEvaluation
            FROM Evaluer e
            JOIN Serie s ON s.idSerie = e.idSerie
            WHERE e.idUtilisateur = %s
              AND e.idSerie = %s
        """, (id_utilisateur, id_serie))

        note = cur.fetchone()

    if note is None:
        print("Vous n'avez pas encore noté cette série.")
        return

    titre, valeur, date = note
    print(f"{titre} : {valeur}/5 (le {date})")


# UPDATE — modifier ma note pour une série précise

def modifier_note(conn, id_utilisateur):
    id_serie = lire_entier(
        "ID de la série dont vous voulez modifier la note : "
    )
    if id_serie is None:
        return

    nouvelle_note = lire_entier("Nouvelle note sur 5 : ")
    if nouvelle_note is None:
        return

    if not 1 <= nouvelle_note <= 5:
        print("La note doit être comprise entre 1 et 5.")
        return

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE Evaluer
                    SET note = %s,
                        dateEvaluation = CURRENT_DATE
                    WHERE idUtilisateur = %s
                      AND idSerie = %s
                """, (nouvelle_note, id_utilisateur, id_serie))

                note_modifiee = cur.rowcount

        if note_modifiee == 0:
            print("Aucune note trouvée pour cette série.")
        else:
            print("Note modifiée avec succès.")

    except psycopg2.Error as e:
        afficher_message_erreur(e)


# DELETE — supprimer ma note pour une série précise

def supprimer_note(conn, id_utilisateur):
    id_serie = lire_entier(
        "ID de la série dont vous voulez supprimer la note : "
    )
    if id_serie is None:
        return

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM Evaluer
                    WHERE idUtilisateur = %s
                      AND idSerie = %s
                """, (id_utilisateur, id_serie))

                note_supprimee = cur.rowcount

        if note_supprimee == 0:
            print("Aucune note trouvée pour cette série.")
        else:
            print("Note supprimée.")

    except psycopg2.Error as e:
        afficher_message_erreur(e)


# =========================================================
# AFFICHER LES SERIES
# Utilisé lors de la création d'une note
# =========================================================

def afficher_series(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT idSerie, titre
            FROM Serie
            ORDER BY titre
        """)
        series = cur.fetchall()

    print("\n--- Toutes les séries ---")

    if not series:
        print("Aucune série trouvée.")
        return

    for id_serie, titre in series:
        print(f"{id_serie} - {titre}")





