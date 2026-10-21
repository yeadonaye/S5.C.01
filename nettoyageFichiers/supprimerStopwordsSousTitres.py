
import re
from pathlib import Path


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

DOSSIER_SCRIPT = Path(__file__).resolve().parent

# Dossier contenant les dialogues déjà nettoyés
SOURCE = (
    DOSSIER_SCRIPT
    / "resultat"
    / "dossierNettoyerSousTitres"
)

# Fichier contenant les stop words français et anglais
FICHIER_STOPWORDS = DOSSIER_SCRIPT / "stopwords_fr_en.txt"

# Nouveau dossier contenant les textes sans stop words
DESTINATION = (
    DOSSIER_SCRIPT
    / "resultat"
    / "sousTitresSansStopWords"
)


# --------------------------------------------------
# 2. CHARGEMENT DES STOP WORDS
# --------------------------------------------------

def charger_stopwords(chemin):
    """Charge les stop words depuis un fichier texte."""

    if not chemin.is_file():
        raise FileNotFoundError(
            f"Fichier de stop words introuvable : {chemin}"
        )

    stopwords = set()

    with chemin.open("r", encoding="utf-8-sig") as fichier:
        for ligne in fichier:
            mot = ligne.strip().lower()

            # Ignorer les lignes vides et les commentaires
            if not mot or mot.startswith("#"):
                continue

            # Uniformiser les apostrophes
            mot = mot.replace("’", "'")

            stopwords.add(mot)

    return stopwords


# --------------------------------------------------
# 3. TOKENISATION
# --------------------------------------------------

# Reconnaît les mots accentués et les contractions
# comme don't, l'homme et aujourd'hui.
MOT = re.compile(
    r"[^\W_]+(?:['’][^\W_]+)*",
    re.UNICODE
)


# --------------------------------------------------
# 4. SUPPRESSION DES STOP WORDS
# --------------------------------------------------

def supprimer_stopwords(texte, stopwords):
    """Supprime les mots présents dans la liste de stop words."""

    mots = MOT.findall(texte.lower())

    mots_conserves = [
        mot
        for mot in mots
        if mot.replace("’", "'") not in stopwords
    ]

    # Conserver uniquement les mots utiles à l'indexation
    return " ".join(mots_conserves)


# --------------------------------------------------
# 5. TRAITEMENT D'UN FICHIER
# --------------------------------------------------

def traiter_fichier(fichier, stopwords):
    """Lit un fichier, supprime les stop words et écrit le résultat."""

    chemin_relatif = fichier.relative_to(SOURCE)
    sortie = DESTINATION / chemin_relatif

    texte = fichier.read_text(encoding="utf-8-sig")

    texte_nettoye = supprimer_stopwords(texte, stopwords)

    sortie.parent.mkdir(parents=True, exist_ok=True)

    sortie.write_text(texte_nettoye, encoding="utf-8")


# --------------------------------------------------
# 6. TRAITEMENT DE TOUT LE DATASET
# --------------------------------------------------

def main():

    if not SOURCE.is_dir():
        raise FileNotFoundError(
            f"Dossier source introuvable : {SOURCE}"
        )

    stopwords = charger_stopwords(FICHIER_STOPWORDS)

    DESTINATION.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(
        fichier
        for fichier in SOURCE.rglob("*.txt")
        if fichier.is_file()
    )

    total = len(fichiers)
    nombre_traites = 0
    nombre_erreurs = 0

    print(f"Stop words chargés : {len(stopwords)}")
    print(f"Fichiers à traiter : {total}")
    print("Début de la suppression des stop words...\n")

    for numero, fichier in enumerate(fichiers, start=1):

        try:
            traiter_fichier(fichier, stopwords)
            nombre_traites += 1

        except (OSError, UnicodeError) as erreur:
            print(f"Erreur sur {fichier.name} : {erreur}")
            nombre_erreurs += 1

        if numero % 500 == 0 or numero == total:
            pourcentage = numero / total * 100

            print(
                f"Progression : {numero}/{total} "
                f"({pourcentage:.1f} %) | "
                f"Traités : {nombre_traites} | "
                f"Erreurs : {nombre_erreurs}"
            )

    print("\n========== BILAN FINAL ==========")
    print(f"Fichiers trouvés : {total}")
    print(f"Fichiers traités : {nombre_traites}")
    print(f"Fichiers en erreur : {nombre_erreurs}")
    print(f"Dossier de sortie : {DESTINATION}")


if __name__ == "__main__":
    main()
