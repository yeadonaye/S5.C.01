"""
Extrait un .7z de sous-titres puis, pour chaque série (sous-dossier direct de la racine) :
  - décompresse tous les .zip (y compris ceux imbriqués dans d'autres zips)
  - aplatit tout : plus aucun sous-dossier dans le dossier de la série
  - garde tous les fichiers (.srt, .txt, ...)
  - supprime les .zip une fois extraits avec succès
  - en cas de collision de nom, ajoute "_doublon" à la fin du nom
    (avant l'extension) : fichier.srt -> fichier_doublon.srt

Usage :
    python aplatir_sous_titres.py                       (cherche sous-titres.7z à côté du script)
    python aplatir_sous_titres.py chemin\\vers\\archive.7z
    python aplatir_sous_titres.py archive.7z -o D:\\resultat

L'archive d'origine n'est jamais modifiée.
"""

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

import py7zr

IGNORES_NOMS = {".ds_store", "thumbs.db", "desktop.ini"}
IGNORES_DOSSIERS = {"__macosx"}


def nom_libre(dossier: Path, nom: str, doublons: list) -> Path:
    """Retourne un chemin libre dans `dossier`, en ajoutant _doublon si besoin."""
    cible = dossier / nom
    if not cible.exists():
        return cible
    base = Path(nom)
    n = 1
    while True:
        suffixe = "_doublon" if n == 1 else f"_doublon{n}"
        cible = dossier / f"{base.stem}{suffixe}{base.suffix}"
        if not cible.exists():
            doublons.append((nom, cible.name))
            return cible
        n += 1


def a_ignorer(chemin_interne: str) -> bool:
    parties = [p.lower() for p in chemin_interne.replace("\\", "/").split("/") if p]
    if not parties:
        return True
    if any(p in IGNORES_DOSSIERS for p in parties[:-1]):
        return True
    nom = parties[-1]
    return nom in IGNORES_NOMS or nom.startswith("._")


def extraire_zip_a_plat(zip_path: Path, dest: Path, doublons: list) -> None:
    """Extrait tous les fichiers du zip directement dans `dest` (sans sous-dossiers)."""
    with open(zip_path, "rb") as f:
        entete = f.read(8)
    if entete.startswith(b"Rar!"):
        raise zipfile.BadZipFile("c'est en réalité un fichier RAR renommé en .zip (à extraire avec WinRAR/7-Zip)")
    with zipfile.ZipFile(zip_path) as zf:
        # Vérifie l'intégrité avant de toucher à quoi que ce soit
        mauvais = zf.testzip()
        if mauvais:
            raise zipfile.BadZipFile(f"membre corrompu : {mauvais}")
        for info in zf.infolist():
            if info.is_dir() or a_ignorer(info.filename):
                continue
            nom = Path(info.filename.replace("\\", "/")).name  # basename => pas de path traversal
            if not nom:
                continue
            cible = nom_libre(dest, nom, doublons)
            with zf.open(info) as src, open(cible, "wb") as out:
                shutil.copyfileobj(src, out)


def remonter_fichiers(serie: Path, doublons: list) -> None:
    """Déplace tous les fichiers des sous-dossiers vers la racine de la série."""
    sous_fichiers = [p for p in serie.rglob("*") if p.is_file() and p.parent != serie]
    for f in sorted(sous_fichiers):
        if a_ignorer(f.name):
            f.unlink()
            continue
        cible = nom_libre(serie, f.name, doublons)
        shutil.move(str(f), str(cible))
    # Supprime les dossiers devenus vides (les plus profonds d'abord)
    for d in sorted((p for p in serie.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        try:
            d.rmdir()
        except OSError:
            pass  # non vide : on laisse, sera visible dans le rapport


def traiter_serie(serie: Path) -> dict:
    stats = {"zips_ok": 0, "zips_erreur": [], "doublons": []}
    zips_en_echec = set()

    # 1) Remonte d'abord les fichiers éventuellement déjà dans des sous-dossiers
    remonter_fichiers(serie, stats["doublons"])

    # 2) Boucle jusqu'à ce qu'il n'y ait plus de zip à traiter (gère l'imbrication)
    while True:
        zips = [p for p in serie.glob("*.zip") if p.name not in zips_en_echec]
        if not zips:
            break
        for z in sorted(zips):
            try:
                extraire_zip_a_plat(z, serie, stats["doublons"])
            except (zipfile.BadZipFile, NotImplementedError, RuntimeError, OSError) as e:
                stats["zips_erreur"].append((z.name, str(e)))
                zips_en_echec.add(z.name)
                continue
            z.unlink()
            stats["zips_ok"] += 1
    return stats


def trouver_racine(dossier: Path) -> Path:
    """Si l'archive contient un unique dossier racine (ex: sous-titres/), on descend dedans."""
    contenu = [p for p in dossier.iterdir()]
    if len(contenu) == 1 and contenu[0].is_dir():
        return contenu[0]
    return dossier


def main() -> int:
    parser = argparse.ArgumentParser(description="Extrait et aplatit une archive de sous-titres.")
    parser.add_argument("archive", nargs="?", default="sous-titres.7z", help="chemin du .7z")
    parser.add_argument("-o", "--sortie", help="dossier de sortie (défaut : <archive>_extrait)")
    args = parser.parse_args()

    archive = Path(args.archive).resolve()
    if not archive.is_file():
        print(f"Archive introuvable : {archive}")
        return 1

    sortie = Path(args.sortie).resolve() if args.sortie else archive.with_name(archive.stem + "_extrait")
    if sortie.exists() and any(sortie.iterdir()):
        print(f"Le dossier de sortie existe déjà et n'est pas vide : {sortie}")
        print("Supprime-le ou choisis un autre dossier avec -o.")
        return 1
    sortie.mkdir(parents=True, exist_ok=True)

    print(f"Extraction de {archive.name} vers {sortie} ...")
    with py7zr.SevenZipFile(archive, mode="r") as z:
        z.extractall(path=sortie)

    racine = trouver_racine(sortie)
    series = sorted(p for p in racine.iterdir() if p.is_dir())
    print(f"{len(series)} séries trouvées dans {racine}\n")

    total_zips = 0
    tous_doublons = []
    toutes_erreurs = []
    for serie in series:
        st = traiter_serie(serie)
        total_zips += st["zips_ok"]
        tous_doublons += [(serie.name, a, b) for a, b in st["doublons"]]
        toutes_erreurs += [(serie.name, n, e) for n, e in st["zips_erreur"]]
        print(f"  {serie.name:<30} {st['zips_ok']:>3} zip(s) extrait(s)")

    print("\n=== Résumé ===")
    print(f"Zips extraits et supprimés : {total_zips}")
    print(f"Collisions renommées (_doublon) : {len(tous_doublons)}")
    for s, orig, nouveau in tous_doublons:
        print(f"   [{s}] {orig} -> {nouveau}")
    if toutes_erreurs:
        print(f"Zips en erreur (conservés) : {len(toutes_erreurs)}")
        for s, n, e in toutes_erreurs:
            print(f"   [{s}] {n} : {e}")
    print(f"\nTerminé. Résultat dans : {racine}")
    return 0 if not toutes_erreurs else 2


if __name__ == "__main__":
    sys.exit(main())