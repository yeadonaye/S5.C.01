
import html
import re
from pathlib import Path


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

DOSSIER_SCRIPT = Path(__file__).resolve().parent

# Dossier contenant les sous-titres déjà nettoyés
SOURCE = DOSSIER_SCRIPT / "resultat" / "sous-titres"

# Dossier contenant les dialogues extraits
DESTINATION = (
    DOSSIER_SCRIPT
    / "resultat"
    / "dossierNettoyerSousTitres"
)

# Format SRT :
# 00:00:31,053 --> 00:00:33,044
HORODATAGE_SRT = re.compile(
    r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*"
    r"\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}"
)

# Format MicroDVD :
# {243}{287}Dialogue
MICRODVD = re.compile(
    r"^\s*\{\d+\}\{\d+\}(.*)$"
)


# --------------------------------------------------
# 2. LECTURE DES FICHIERS
# --------------------------------------------------

def lire_fichier(chemin):
    """Lit un fichier en essayant plusieurs encodages."""

    donnees = chemin.read_bytes()

    for encodage in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return donnees.decode(encodage)
        except UnicodeDecodeError:
            continue

    raise ValueError("Impossible de décoder le fichier")


# --------------------------------------------------
# 3. NETTOYAGE DES LIGNES
# --------------------------------------------------

def nettoyer_ligne(ligne):
    """Nettoie une ligne sans supprimer son dialogue."""

    ligne = html.unescape(ligne)

    # Supprimer les balises HTML, par exemple <i> et <b>
    ligne = re.sub(r"<[^>]*>", "", ligne)

    # Normaliser les espaces et les tabulations
    ligne = re.sub(r"[ \t]+", " ", ligne)

    return ligne.strip()


# --------------------------------------------------
# 4. NETTOYAGE SRT
# --------------------------------------------------

def nettoyer_srt(texte):
    """Extrait le dialogue d'un fichier SRT."""

    lignes = texte.splitlines()
    resultat = []
    horodatages_trouves = 0

    for i, ligne in enumerate(lignes):

        # Supprimer les horodatages
        if HORODATAGE_SRT.match(ligne):
            horodatages_trouves += 1
            continue

        # Supprimer le numéro du sous-titre
        # uniquement s'il précède un horodatage
        if (
            ligne.strip().isdigit()
            and i + 1 < len(lignes)
            and HORODATAGE_SRT.match(lignes[i + 1])
        ):
            continue

        ligne = nettoyer_ligne(ligne)

        if ligne:
            resultat.append(ligne)
        elif resultat and resultat[-1] != "":
            # Conserver une séparation entre les sous-titres
            resultat.append("")

    # Vérifier que le fichier contient une structure SRT
    if horodatages_trouves == 0:
        return None

    return "\n".join(resultat).strip()


# --------------------------------------------------
# 5. NETTOYAGE MICRODVD (.SUB)
# --------------------------------------------------

def nettoyer_microdvd(texte):
    """Extrait le dialogue des fichiers MicroDVD."""

    resultat = []
    lignes_reconnues = 0

    for ligne in texte.splitlines():

        correspondance = MICRODVD.match(ligne)

        if not correspondance:
            continue

        lignes_reconnues += 1
        dialogue = correspondance.group(1)

        # Dans MicroDVD, | sépare les lignes de dialogue
        for morceau in dialogue.split("|"):
            morceau = nettoyer_ligne(morceau)

            if morceau:
                resultat.append(morceau)

    if lignes_reconnues == 0:
        return None

    return "\n".join(resultat).strip()


# --------------------------------------------------
# 6. TRAITEMENT D'UN FICHIER
# --------------------------------------------------

def nettoyer_fichier(chemin):
    """Choisit le nettoyeur selon l'extension."""

    extension = chemin.suffix.lower()
    texte = lire_fichier(chemin)

    if extension == ".srt":
        contenu = nettoyer_srt(texte)

    elif extension == ".sub":
        contenu = nettoyer_microdvd(texte)

    else:
        return None

    if contenu is None or not contenu.strip():
        return None

    return contenu


# --------------------------------------------------
# 7. TRAITEMENT DU DATASET
# --------------------------------------------------

def main():

    if not SOURCE.is_dir():
        raise FileNotFoundError(
            f"Dossier source introuvable : {SOURCE}"
        )

    DESTINATION.mkdir(parents=True, exist_ok=True)

    nombre_traites = 0
    nombre_ignores = 0
    nombre_erreurs = 0

    # Parcourir les fichiers dans le dossier source
    fichiers = sorted(
        chemin
        for chemin in SOURCE.rglob("*")
        if chemin.is_file()
        and chemin.suffix.lower() in {".srt", ".sub"}
    )

    total = len(fichiers)

    print(f"Fichiers à inspecter : {total}")
    print("Début du nettoyage...\n")

    for numero, fichier in enumerate(fichiers, start=1):

        chemin_relatif = fichier.relative_to(SOURCE)

        try:
            contenu = nettoyer_fichier(fichier)

            if contenu is None:
                nombre_ignores += 1

            else:
                # Ajouter .txt au nom d'origine
                # Exemple : episode.srt devient episode.srt.txt
                sortie_relative = Path(
                    str(chemin_relatif) + ".txt"
                )

                sortie = DESTINATION / sortie_relative

                sortie.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                sortie.write_text(
                    contenu,
                    encoding="utf-8"
                )

                nombre_traites += 1

        except Exception as erreur:
            print(f"Erreur sur {chemin_relatif} : {erreur}")
            nombre_erreurs += 1

        # Afficher la progression toutes les 500 entrées
        if numero % 500 == 0 or numero == total:
            pourcentage = numero / total * 100

            print(
                f"Progression : {numero}/{total} "
                f"({pourcentage:.1f} %) | "
                f"Traités : {nombre_traites} | "
                f"Ignorés : {nombre_ignores} | "
                f"Erreurs : {nombre_erreurs}"
            )

    # --------------------------------------------------
    # 8. BILAN FINAL
    # --------------------------------------------------

    print("\n========== BILAN DU NETTOYAGE ==========")
    print(f"Fichiers inspectés : {total}")
    print(f"Fichiers traités : {nombre_traites}")
    print(f"Fichiers ignorés : {nombre_ignores}")
    print(f"Fichiers en erreur : {nombre_erreurs}")
    print(f"Dossier de sortie : {DESTINATION}")


if __name__ == "__main__":
    main()
