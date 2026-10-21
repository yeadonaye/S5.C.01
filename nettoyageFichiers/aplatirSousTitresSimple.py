import sys
import shutil
import zipfile
from pathlib import Path
import py7zr


EXTENSIONS_AUTORISEES = {".srt", ".sub"}


def fichier_valide(fichier):
    """Vérifie si le fichier est un sous-titre non vide autorisé."""
    return (
        fichier.is_file()
        and fichier.suffix.lower() in EXTENSIONS_AUTORISEES
        and fichier.stat().st_size > 0
    )


def fichiers_identiques(fichier1, fichier2):
    """Compare le contenu de deux fichiers sans les charger entièrement en mémoire."""
    if fichier1.stat().st_size != fichier2.stat().st_size:
        return False

    with open(fichier1, "rb") as f1, open(fichier2, "rb") as f2:
        while True:
            bloc1 = f1.read(1024 * 1024)
            bloc2 = f2.read(1024 * 1024)

            if bloc1 != bloc2:
                return False

            if not bloc1:
                return True


def aplatir_dossier(serie):
    """Conserve les sous-titres autorisés, supprime les fichiers inutiles,
    déplace les fichiers à la racine et traite les collisions de noms.
    """

    for fichier in list(serie.rglob("*")):
        if not fichier.is_file():
            continue

        # Supprimer les fichiers dont l'extension n'est pas autorisée
        if fichier.suffix.lower() not in EXTENSIONS_AUTORISEES:
            print("Fichier ignoré :", fichier.name)
            fichier.unlink()
            continue

        # Supprimer les fichiers de sous-titres vides
        if fichier.stat().st_size == 0:
            print("Fichier vide supprimé :", fichier.name)
            fichier.unlink()
            continue

        # Le fichier est déjà à la racine
        if fichier.parent == serie:
            continue

        destination = serie / fichier.name

        if destination.exists():
            if fichiers_identiques(fichier, destination):
                print("Doublon identique supprimé :", fichier.name)
                fichier.unlink()
            else:
                # Préserver les deux fichiers en cas de collision
                compteur = 1

                while True:
                    nouveau_nom = (
                        f"{fichier.stem}_{compteur}{fichier.suffix}"
                    )
                    nouvelle_destination = serie / nouveau_nom

                    if not nouvelle_destination.exists():
                        break

                    compteur += 1

                shutil.move(str(fichier), str(nouvelle_destination))
                print("Collision de nom :", nouveau_nom)
        else:
            shutil.move(str(fichier), str(destination))

    # Supprimer les sous-dossiers devenus vides
    for dossier in sorted(
        serie.rglob("*"),
        key=lambda p: len(p.parts),
        reverse=True
    ):
        if dossier.is_dir():
            try:
                dossier.rmdir()
            except OSError:
                pass


def traiter_serie(serie):
    """Extrait les ZIP, conserve uniquement les sous-titres autorisés
    et nettoie les fichiers de la série.
    """

    zips_en_erreur = set()

    while True:
        zips = [
            z for z in serie.glob("*.zip")
            if z.name not in zips_en_erreur
        ]

        if not zips:
            break

        for zip_path in zips:
            fichiers_crees = []

            try:
                with zipfile.ZipFile(zip_path) as archive:
                    for nom in archive.namelist():

                        if nom.endswith(("/", "\\")):
                            continue

                        nom_fichier = Path(
                            nom.replace("\\", "/")
                        ).name

                        if not nom_fichier:
                            continue

                        # Ignorer les fichiers qui ne sont pas des sous-titres
                        if Path(nom_fichier).suffix.lower() not in EXTENSIONS_AUTORISEES:
                            continue

                        destination = serie / nom_fichier

                        # Ne pas extraire les fichiers vides
                        info = archive.getinfo(nom)

                        if info.file_size == 0:
                            print("Sous-titre vide ignoré :", nom_fichier)
                            continue

                        # Si le nom existe déjà, comparer les contenus
                        if destination.exists():
                            identique = False

                            if destination.is_file():
                                with archive.open(nom) as source:
                                    with open(destination, "rb") as existant:
                                        identique = True

                                        while True:
                                            bloc1 = source.read(1024 * 1024)
                                            bloc2 = existant.read(1024 * 1024)

                                            if bloc1 != bloc2:
                                                identique = False
                                                break

                                            if not bloc1:
                                                break

                            if identique:
                                print(
                                    "Doublon identique ignoré :",
                                    nom_fichier
                                )
                                continue

                            # Les contenus diffèrent : conserver les deux
                            compteur = 1

                            while True:
                                nouveau_nom = (
                                    f"{Path(nom_fichier).stem}_"
                                    f"{compteur}"
                                    f"{Path(nom_fichier).suffix}"
                                )
                                destination = serie / nouveau_nom

                                if not destination.exists():
                                    break

                                compteur += 1

                        with archive.open(nom) as source:
                            with open(destination, "wb") as cible:
                                shutil.copyfileobj(source, cible)

                        fichiers_crees.append(destination)

                # Extraction réussie : supprimer le ZIP original
                zip_path.unlink()
                print("ZIP extrait :", zip_path.name)

            except (
                zipfile.BadZipFile,
                OSError,
                RuntimeError,
                NotImplementedError,
                KeyError
            ) as erreur:

                print("Erreur :", zip_path.name, "-", erreur)

                # Supprimer uniquement les fichiers créés pendant
                # cette tentative d'extraction
                for fichier in fichiers_crees:
                    try:
                        fichier.unlink(missing_ok=True)
                    except OSError:
                        pass

                # Préserver le ZIP pour pouvoir l'inspecter
                zips_en_erreur.add(zip_path.name)

    # Nettoyer les fichiers restants et aplatir la série
    aplatir_dossier(serie)


def main():
    # 1. Récupérer le chemin de l'archive
    archive = Path(__file__).resolve().parents[2] / "sous-titres.7z"

    if not archive.is_file():
        print("Archive introuvable :", archive)
        return

    # 2. Créer le dossier de sortie
    sortie = Path(__file__).resolve().parent / "resultat"

    if sortie.exists() and any(sortie.iterdir()):
        print("Le dossier de sortie n'est pas vide :", sortie)
        return

    sortie.mkdir(parents=True, exist_ok=True)

    # 3. Extraire le fichier .7z
    try:
        with py7zr.SevenZipFile(archive, mode="r") as fichier:
            fichier.extractall(path=sortie)
    except Exception as erreur:
        print("Erreur lors de l'extraction du 7z :", erreur)
        return

    # 4. Trouver les dossiers des séries
    contenu = list(sortie.iterdir())

    if len(contenu) == 1 and contenu[0].is_dir():
        racine = contenu[0]
    else:
        racine = sortie

    series = [
        dossier for dossier in racine.iterdir()
        if dossier.is_dir()
    ]

    # 5. Traiter chaque série
    for serie in series:
        print("\nSérie :", serie.name)
        traiter_serie(serie)

    print("\nTerminé ! Résultat :", racine)

    # Bilan du nombre de séries
    series_finales = [
        dossier for dossier in racine.iterdir()
        if dossier.is_dir()
    ]

    print("\n========== BILAN FINAL ==========")
    print("Nombre de séries au début :", len(series))
    print("Nombre de séries à la fin :", len(series_finales))
    print("Nombre de séries manquantes :", len(series) - len(series_finales))
    print("=================================")


if __name__ == "__main__":
    main()
