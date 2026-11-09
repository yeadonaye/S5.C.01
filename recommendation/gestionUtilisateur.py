import os
import hmac
import hashlib
import secrets

import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv


# CONNEXION A LA BASE DE DONNEES

load_dotenv()

DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise RuntimeError(
        "La variable DB_URL est manquante dans le fichier .env."
    )


def connecter():
    return psycopg2.connect(DB_URL)


# GESTION DES MOTS DE PASSE

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


# OUTILS COMMUNS
# Chaque fonction retourne un dictionnaire avec "succes" et "message"

def message_erreur(e):
    if isinstance(e, errors.UniqueViolation):
        return "Cette valeur existe déjà dans la base."
    if isinstance(e, errors.ForeignKeyViolation):
        return "Cette opération est impossible : référence invalide."
    return f"Une erreur est survenue : {e}"


def reponse(succes, message, **extra):
    return {"succes": succes, "message": message, **extra}


# CRUD UTILISATEUR

# CREATE : créer un compte

def creer_compte(conn, nom, prenom, email, mot_de_passe):
    nom = nom.strip()
    prenom = prenom.strip()
    email = email.strip().lower()

    if not nom or not prenom or not email or not mot_de_passe:
        return reponse(False, "Tous les champs sont obligatoires.")

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

        return reponse(True, "Compte créé avec succès.",
                       idUtilisateur=id_utilisateur)

    except psycopg2.Error as e:
        return reponse(False, message_erreur(e))


# READ : afficher un compte
# Retourne un dictionnaire, ou None si le compte n'existe pas

def afficher_compte(conn, id_utilisateur):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT nom, prenom, email, dateInscription
            FROM Utilisateur
            WHERE idUtilisateur = %s
        """, (id_utilisateur,))

        utilisateur = cur.fetchone()

    if utilisateur is None:
        return None

    nom, prenom, email, date_inscription = utilisateur

    return {
        "nom": nom,
        "prenom": prenom,
        "email": email,
        "dateInscription": date_inscription,
    }


# UPDATE : modifier un compte
# Un paramètre à None (ou vide) est conservé tel quel

def modifier_compte(conn, id_utilisateur, nom=None, prenom=None,
                    email=None, nouveau_mdp=None):
    champs = []
    valeurs = []

    if nom and nom.strip():
        champs.append("nom = %s")
        valeurs.append(nom.strip())

    if prenom and prenom.strip():
        champs.append("prenom = %s")
        valeurs.append(prenom.strip())

    if email and email.strip():
        champs.append("email = %s")
        valeurs.append(email.strip().lower())

    if nouveau_mdp:
        champs.append("motDePasseHash = %s")
        valeurs.append(hasher_mot_de_passe(nouveau_mdp))

    if not champs:
        return reponse(False, "Aucune modification demandée.")

    valeurs.append(id_utilisateur)

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE Utilisateur SET {', '.join(champs)} "
                    "WHERE idUtilisateur = %s",
                    valeurs
                )

                modifie = cur.rowcount

        if modifie == 0:
            return reponse(False, "Compte introuvable.")

        return reponse(True, "Compte modifié avec succès.")

    except psycopg2.Error as e:
        return reponse(False, message_erreur(e))


# DELETE : supprimer un compte
# La confirmation se fait côté front

def supprimer_compte(conn, id_utilisateur):
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM Utilisateur
                    WHERE idUtilisateur = %s
                """, (id_utilisateur,))

                supprime = cur.rowcount

        if supprime == 0:
            return reponse(False, "Compte introuvable.")

        return reponse(True, "Compte supprimé.")

    except psycopg2.Error as e:
        return reponse(False, message_erreur(e))


# CONNEXION UTILISATEUR
# Retourne les infos de l'utilisateur, ou None si identifiants incorrects

def connecter_utilisateur(conn, email, mot_de_passe):
    email = email.strip().lower()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT idUtilisateur, nom, prenom, motDePasseHash
            FROM Utilisateur
            WHERE email = %s
        """, (email,))

        utilisateur = cur.fetchone()

    if utilisateur is None:
        return None

    id_utilisateur, nom, prenom, hash_stocke = utilisateur

    if not verifier_mot_de_passe(mot_de_passe, hash_stocke):
        return None

    return {
        "idUtilisateur": id_utilisateur,
        "nom": nom,
        "prenom": prenom,
    }


# CRUD NOTES

# CREATE : créer une note

def creer_note(conn, id_utilisateur, id_serie, note):
    if not 1 <= note <= 5:
        return reponse(False, "La note doit être comprise entre 1 et 5.")

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO Evaluer (idUtilisateur, idSerie, note)
                    VALUES (%s, %s, %s)
                """, (id_utilisateur, id_serie, note))

        return reponse(True, "Note créée avec succès.")

    except psycopg2.Error as e:
        return reponse(False, message_erreur(e))


# READ : toutes les notes d'un utilisateur

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

    return [
        {"idSerie": id_serie, "titre": titre,
         "note": note, "dateEvaluation": date}
        for id_serie, titre, note, date in notes
    ]


# READ : la note d'un utilisateur pour une série précise
# Retourne None si la série n'a pas été notée

def afficher_ma_note(conn, id_utilisateur, id_serie):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT s.titre, e.note, e.dateEvaluation
            FROM Evaluer e
            JOIN Serie s ON s.idSerie = e.idSerie
            WHERE e.idUtilisateur = %s
              AND e.idSerie = %s
        """, (id_utilisateur, id_serie))

        resultat = cur.fetchone()

    if resultat is None:
        return None

    titre, note, date = resultat

    return {
        "idSerie": id_serie,
        "titre": titre,
        "note": note,
        "dateEvaluation": date,
    }


# UPDATE : modifier la note d'une série

def modifier_note(conn, id_utilisateur, id_serie, nouvelle_note):
    if not 1 <= nouvelle_note <= 5:
        return reponse(False, "La note doit être comprise entre 1 et 5.")

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
            return reponse(False, "Aucune note trouvée pour cette série.")

        return reponse(True, "Note modifiée avec succès.")

    except psycopg2.Error as e:
        return reponse(False, message_erreur(e))


# DELETE : supprimer la note d'une série

def supprimer_note(conn, id_utilisateur, id_serie):
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
            return reponse(False, "Aucune note trouvée pour cette série.")

        return reponse(True, "Note supprimée.")

    except psycopg2.Error as e:
        return reponse(False, message_erreur(e))


# LISTE DES SERIES
# Utilisé pour choisir la série à noter

def afficher_series(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT idSerie, titre
            FROM Serie
            ORDER BY titre
        """)
        series = cur.fetchall()

    return [{"idSerie": id_serie, "titre": titre}
            for id_serie, titre in series]