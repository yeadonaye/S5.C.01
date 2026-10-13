
import csv
import html
import re
from pathlib import Path


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

DOSSIER_SCRIPT = Path(__file__).resolve().parent

# Dossier contenant les fichiers originaux
SOURCE = DOSSIER_SCRIPT / "resultat" / "sous-titres"

# Dossier contenant les fichiers nettoyés
DESTINATION = (
    DOSSIER_SCRIPT
    / "resultat"
    / "dossierNettoyerSousTitres"
)

# Rapport CSV généré à la fin
RAPPORT = DESTINATION / "_rapport_nettoyage.csv"

# Extensions prises en charge
EXTENSIONS_SRT = {".srt", ".vo", ".txt"}
EXTENSIONS = EXTENSIONS_SRT | {".sub", ".ass"}

# Format SRT :
# 00:00:31,053 --> 00:00:33,044
HORODATAGE_SRT = re.compile(
    r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*"
    r"\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}"
)

# Format MicroDVD :
# {243}{287}Dialogue
MICRODVD = re.compile(r"^\s*\{\d+\}\{\d+\}(.*)$")


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

    # Exiger au moins un horodatage pour reconnaître un SRT
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
# 6. NETTOYAGE ASS
# --------------------------------------------------

def nettoyer_ass(texte):
    """Extrait les dialogues des fichiers ASS."""
    resultat = []
    dialogues_reconnus = 0

    for ligne in texte.splitlines():

        if not ligne.lstrip().startswith("Dialogue:"):
            continue

        # Le dixième champ contient le texte.
        # Limiter le découpage à 9 virgules permet
        # de conserver les virgules présentes dans le dialogue.
        champs = ligne.split(",", 9)

        if len(champs) != 10:
            continue

        dialogues_reconnus += 1
        dialogue = champs[9]

        # Supprimer les commandes de mise en forme ASS
        dialogue = re.sub(r"\{[^}]*\}", "", dialogue)

        # Convertir les marqueurs de retour à la ligne
        dialogue = re.sub(r"\\[Nn]", "\n", dialogue)
        dialogue = dialogue.replace(r"\h", " ")

        for morceau in dialogue.splitlines():
            morceau = nettoyer_ligne(morceau)

            if morceau:
                resultat.append(morceau)

    if dialogues_reconnus == 0:
        return None

    return "\n".join(resultat).strip()


# --------------------------------------------------
# 7. DÉTECTION APPROXIMATIVE DE LA LANGUE
# --------------------------------------------------

def detecter_langue(nom_fichier):
    """
    Estime la langue à partir des marqueurs du nom.
    VO seul ne permet pas de déterminer la langue.
    """
    nom = nom_fichier.upper()
    marqueurs = re.split(r"[^A-Z0-9]+", nom)

    anglais = any(
        marqueur in {"EN", "ENG", "ENGLISH"}
        for marqueur in marqueurs
    )

    francais = any(
        marqueur in {"FR", "VF", "FRENCH", "VOSTFR"}
        for marqueur in marqueurs
    )

    if anglais and not francais:
        return "en"

    if francais and not anglais:
        return "fr"

    return "unknown"


# --------------------------------------------------
# 8. TRAITEMENT D'UN FICHIER
# --------------------------------------------------

def nettoyer_fichier(chemin):
    """Choisit le nettoyeur selon le format du fichier."""
    extension = chemin.suffix.lower()
    texte = lire_fichier(chemin)

    if extension in EXTENSIONS_SRT:
        contenu = nettoyer_srt(texte)

    elif extension == ".sub":
        contenu = nettoyer_microdvd(texte)

    elif extension == ".ass":
        contenu = nettoyer_ass(texte)

    else:
        return None, "format non pris en charge"

    if contenu is None:
        return None, "structure de sous-titres non reconnue"

    if not contenu.strip():
        return None, "aucun dialogue extrait"

    return contenu, "traite"


# --------------------------------------------------
# 9. TRAITEMENT DU DATASET
# --------------------------------------------------

def main():

    if not SOURCE.is_dir():
        raise FileNotFoundError(
            f"Dossier source introuvable : {SOURCE}"
        )

    DESTINATION.mkdir(parents=True, exist_ok=True)

    rapport = []
    nombre_traites = 0
    nombre_ignores = 0
    nombre_erreurs = 0

    fichiers = sorted(
        chemin
        for chemin in SOURCE.rglob("*")
        if chemin.is_file()
    )

    total = len(fichiers)

    print(f"Fichiers à inspecter : {total}")
    print("Début du nettoyage...\n")

    for numero, fichier in enumerate(fichiers, start=1):

        extension = fichier.suffix.lower()
        chemin_relatif = fichier.relative_to(SOURCE)
        langue = detecter_langue(fichier.name)

        # Ignorer les extensions non prises en charge
        if extension not in EXTENSIONS:
            rapport.append({
                "fichier_source": str(chemin_relatif),
                "statut": "ignore",
                "raison": "extension non prise en charge",
                "langue": langue,
                "fichier_sortie": ""
            })

            nombre_ignores += 1

        else:
            try:
                contenu, statut = nettoyer_fichier(fichier)

                if contenu is None:
                    rapport.append({
                        "fichier_source": str(chemin_relatif),
                        "statut": "ignore",
                        "raison": statut,
                        "langue": langue,
                        "fichier_sortie": ""
                    })

                    nombre_ignores += 1

                else:
                    # Ajouter l'extension d'origine au nom
                    # pour éviter les collisions entre formats.
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

                    rapport.append({
                        "fichier_source": str(chemin_relatif),
                        "statut": "traite",
                        "raison": "",
                        "langue": langue,
                        "fichier_sortie": str(sortie_relative)
                    })

                    nombre_traites += 1

            except Exception as erreur:
                rapport.append({
                    "fichier_source": str(chemin_relatif),
                    "statut": "erreur",
                    "raison": str(erreur),
                    "langue": langue,
                    "fichier_sortie": ""
                })

                nombre_erreurs += 1

        # Afficher la progression toutes les 500 entrées
        if numero % 500 == 0 or numero == total:
            pourcentage = (
                numero / total * 100 if total else 100
            )

            print(
                f"Progression : {numero}/{total} "
                f"({pourcentage:.1f} %) | "
                f"Traités : {nombre_traites} | "
                f"Ignorés : {nombre_ignores} | "
                f"Erreurs : {nombre_erreurs}"
            )

    # --------------------------------------------------
    # 10. ÉCRITURE DU RAPPORT CSV
    # --------------------------------------------------

    with RAPPORT.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as fichier_csv:

        colonnes = [
            "fichier_source",
            "statut",
            "raison",
            "langue",
            "fichier_sortie"
        ]

        redacteur = csv.DictWriter(
            fichier_csv,
            fieldnames=colonnes,
            delimiter=";"
        )

        redacteur.writeheader()
        redacteur.writerows(rapport)

    # --------------------------------------------------
    # 11. BILAN FINAL
    # --------------------------------------------------

    print("\n========== BILAN DU NETTOYAGE ==========")
    print(f"Fichiers inspectés : {total}")
    print(f"Fichiers traités : {nombre_traites}")
    print(f"Fichiers ignorés : {nombre_ignores}")
    print(f"Fichiers en erreur : {nombre_erreurs}")
    print(f"Dossier de sortie : {DESTINATION}")
    print(f"Rapport CSV : {RAPPORT}")


if __name__ == "__main__":
    main()
