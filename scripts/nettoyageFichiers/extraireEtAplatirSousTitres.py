import argparse
import filecmp
import shutil
import tempfile
import zipfile
import zlib
from contextlib import suppress
from itertools import count
from pathlib import Path

import py7zr

EXTENSIONS = {".srt", ".sub"}
UTILES = EXTENSIONS | {".zip"}  # sous-titres + ZIP imbriqués
NIVEAUX_MAX = 10  # profondeur max de ZIP imbriqués (évite une boucle infinie)
NOM_MAX = 100  # longueur max d'un nom de fichier extrait (limite Windows de 260 caractères)
ERREURS_ZIP = (
    zipfile.BadZipFile, zlib.error, EOFError, OSError,
    RuntimeError, NotImplementedError,
)


def chemin_libre(chemin):
    """Retourne chemin, ou chemin avec _1, _2... s'il existe déjà."""
    if not chemin.exists():
        return chemin
    for i in count(1):
        candidat = chemin.with_name(f"{chemin.stem}_{i}{chemin.suffix}")
        if not candidat.exists():
            return candidat


def nom_court(nom):
    """Raccourcit un nom de fichier trop long en gardant son extension."""
    if len(nom) <= NOM_MAX:
        return nom
    p = Path(nom)
    return p.stem[: NOM_MAX - 10] + p.suffix


def extraire_zip(zip_path, serie):
    """Extrait les sous-titres et ZIP internes d'un ZIP dans un dossier
    temporaire court (à la racine de la série), puis supprime le ZIP."""
    tmp = Path(tempfile.mkdtemp(dir=serie, prefix="t"))
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                nom = Path(info.filename.replace("\\", "/")).name
                if Path(nom).suffix.lower() not in UTILES:
                    continue
                cible = chemin_libre(tmp / nom_court(nom))
                with archive.open(info) as src, open(cible, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        zip_path.unlink()
    except ERREURS_ZIP:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def extraire_zips(serie, dossier_erreurs):
    """Décompresse tous les ZIP de la série (y compris imbriqués).
    Les ZIP en échec sont déplacés dans dossier_erreurs."""
    for _ in range(NIVEAUX_MAX):
        zips = [z for z in serie.rglob("*.zip") if z.is_file()]
        if not zips:
            return
        for zip_path in zips:
            try:
                extraire_zip(zip_path, serie)
            except ERREURS_ZIP as e:
                print("Erreur :", zip_path.name, "-", e)
                dossier_erreurs.mkdir(exist_ok=True)
                cible = chemin_libre(dossier_erreurs / f"{serie.name}__{zip_path.name}")
                shutil.move(zip_path, cible)
    print("Attention : ZIP encore imbriqués après", NIVEAUX_MAX, "niveaux :", serie.name)


def aplatir(serie):
    """Met tous les sous-titres non vides à la racine, supprime le reste."""
    for f in sorted(serie.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() not in EXTENSIONS or f.stat().st_size == 0:
            f.unlink()
        elif f.parent != serie:
            dest = serie / f.name
            if dest.exists() and filecmp.cmp(f, dest, shallow=False):
                f.unlink()  # doublon identique
            else:
                shutil.move(f, chemin_libre(dest))

    # supprimer les sous-dossiers devenus vides (les plus profonds d'abord)
    for d in sorted(serie.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if d.is_dir():
            with suppress(OSError):
                d.rmdir()


def main():
    base = Path(__file__).resolve().parent
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, default=base.parents[1] / "sous-titres.7z")
    p.add_argument("--sortie", type=Path, default=base / "resultat")
    args = p.parse_args()

    if not args.archive.is_file():
        raise SystemExit(f"Archive introuvable : {args.archive}")
    if args.sortie.exists() and any(args.sortie.iterdir()):
        raise SystemExit(f"Le dossier de sortie n'est pas vide : {args.sortie}")

    args.sortie.mkdir(parents=True, exist_ok=True)
    try:
        with py7zr.SevenZipFile(args.archive, "r") as f:
            f.extractall(path=args.sortie)
    except Exception as e:
        raise SystemExit(f"Erreur lors de l'extraction du 7z : {e}")

    contenu = list(args.sortie.iterdir())
    racine = contenu[0] if len(contenu) == 1 and contenu[0].is_dir() else args.sortie
    erreurs = args.sortie / "_zips_en_erreur"

    series = [d for d in racine.iterdir() if d.is_dir()]
    supprimees, plantees = [], []
    for serie in series:
        print("Série :", serie.name)
        try:
            extraire_zips(serie, erreurs)
            aplatir(serie)
        except Exception as e:  # une série cassée ne doit pas bloquer les autres
            print("Erreur inattendue sur", serie.name, "-", repr(e))
            plantees.append(serie.name)
            continue
        if not any(serie.iterdir()):
            serie.rmdir()
            supprimees.append(serie.name)

    print(f"\n{len(series)} séries au début, {len(series) - len(supprimees)} à la fin.")
    print(f"Supprimées car sans sous-titres : {supprimees}")
    if plantees:
        print(f"Séries en erreur inattendue : {plantees}")
    if erreurs.exists():
        print(f"ZIP illisibles conservés dans : {erreurs}")


if __name__ == "__main__":
    main()