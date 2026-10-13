
import sys
import shutil
import zipfile
from pathlib import Path
import py7zr


def nom_libre(dossier, nom):
    """Trouve un nom de fichier qui n'existe pas déjà."""
    fichier = dossier / nom

    if not fichier.exists():
        return fichier

    base = Path(nom)

    numero = 1
    while True:
        nouveau_nom = dossier / f"{base.stem}_doublon{numero}{base.suffix}"

        if not nouveau_nom.exists():
            return nouveau_nom

        numero += 1


def aplatir_dossier(serie):
    """Déplace tous les fichiers dans le dossier principal de la série."""
    for fichier in list(serie.rglob("*")):
        if fichier.is_file() and fichier.parent != serie:
            destination = nom_libre(serie, fichier.name)
            shutil.move(str(fichier), str(destination))

    # Supprime les sous-dossiers devenus vides
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
    """Extrait les ZIP et supprime ceux qui ne fonctionnent pas."""
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
                        if nom.endswith("/"):
                            continue

                        nom_fichier = Path(
                            nom.replace("\\", "/")
                        ).name

                        if not nom_fichier:
                            continue

                        destination = nom_libre(serie, nom_fichier)
                        fichiers_crees.append(destination)

                        with archive.open(nom) as source:
                            with open(destination, "wb") as cible:
                                shutil.copyfileobj(source, cible)

                # Tout a réussi : supprimer le ZIP original
                zip_path.unlink()
                print("ZIP extrait :", zip_path.name)

            except (zipfile.BadZipFile, OSError, RuntimeError,
                    NotImplementedError, KeyError) as erreur:

                print("Erreur :", zip_path.name, "-", erreur)

                # Supprimer les fichiers partiellement extraits
                for fichier in fichiers_crees:
                    try:
                        fichier.unlink(missing_ok=True)
                    except OSError:
                        pass

                # Supprimer le ZIP qui ne fonctionne pas
                try:
                    zip_path.unlink()
                    print("ZIP supprimé :", zip_path.name)
                except OSError as suppression:
                    print("Impossible de supprimer le ZIP :",
                          suppression)

                zips_en_erreur.add(zip_path.name)

    aplatir_dossier(serie)



def main():
    # 1. Récupérer le chemin de l'archive
    archive = Path(
        sys.argv[1] if len(sys.argv) > 1 else "sous-titres.7z"
    )

    if not archive.is_file():
        print("Archive introuvable :", archive)
        return

    # 2. Créer le dossier de sortie
    sortie = Path(
        sys.argv[2] if len(sys.argv) > 2
        else archive.stem + "_extrait"
    )

    if sortie.exists() and any(sortie.iterdir()):
        print("Le dossier de sortie n'est pas vide :", sortie)
        return

    sortie.mkdir(parents=True, exist_ok=True)

    # 3. Extraire le fichier .7z
    with py7zr.SevenZipFile(archive, mode="r") as fichier:
        fichier.extractall(path=sortie)

    # 4. Trouver les dossiers des séries
    contenu = list(sortie.iterdir())

    if len(contenu) == 1 and contenu[0].is_dir():
        racine = contenu[0]
    else:
        racine = sortie

    series = [d for d in racine.iterdir() if d.is_dir()]

    # 5. Traiter chaque série
    for serie in series:
        print("\nSérie :", serie.name)

        aplatir_dossier(serie)
        traiter_serie(serie)

    print("\nTerminé ! Résultat :", racine)


if __name__ == "__main__":
    main()
