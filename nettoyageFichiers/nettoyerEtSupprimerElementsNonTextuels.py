import argparse
import html
import re
from collections import Counter
from pathlib import Path

TIMESTAMP = re.compile(
    r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}"
)
MICRODVD = re.compile(r"^\s*\{(\d+)\}\{(\d+)\}(.*)$")
BALISES = re.compile(r"<[^>]*>|\{[^}]*\}")  # <i>, <b>, {\an8}, {y:i}...


def lire(chemin):
    """Décode en UTF-16 (si BOM), puis UTF-8, sinon cp1252."""
    donnees = chemin.read_bytes()
    if donnees.startswith((b"\xff\xfe", b"\xfe\xff")):
        return donnees.decode("utf-16")
    try:
        return donnees.decode("utf-8-sig")
    except UnicodeDecodeError:
        return donnees.decode("cp1252", errors="replace")


def nettoyer_ligne(ligne):
    ligne = BALISES.sub("", html.unescape(ligne))
    return " ".join(ligne.split())  # normalise aussi les espaces insécables


def nettoyer_srt(texte):
    lignes = texte.splitlines()
    sortie, trouves = [], 0
    for i, ligne in enumerate(lignes):
        if TIMESTAMP.match(ligne):
            trouves += 1
        elif ligne.strip().isdigit() and i + 1 < len(lignes) and TIMESTAMP.match(lignes[i + 1]):
            continue  # numéro de sous-titre
        elif ligne := nettoyer_ligne(ligne):
            sortie.append(ligne)
        elif sortie and sortie[-1]:
            sortie.append("")  # séparation entre sous-titres
    return "\n".join(sortie).strip() if trouves else None


def nettoyer_microdvd(texte):
    sortie, trouves = [], 0
    for ligne in texte.splitlines():
        if m := MICRODVD.match(ligne):
            trouves += 1
            if m[1] == m[2] == "1":  # en-tête "{1}{1}23.976" (fps)
                continue
            dialogue = [l for l in map(nettoyer_ligne, m[3].split("|")) if l]
            if dialogue:
                sortie += dialogue + [""]
    return "\n".join(sortie).strip() if trouves else None


NETTOYEURS = {".srt": nettoyer_srt, ".sub": nettoyer_microdvd}


def main():
    base = Path(__file__).resolve().parent / "resultat"
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=base / "sous-titres")
    p.add_argument("--destination", type=Path, default=base / "dossierNettoyerSousTitres")
    args = p.parse_args()

    if not args.source.is_dir():
        raise SystemExit(f"Dossier source introuvable : {args.source}")
    args.destination.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(
        f for f in args.source.rglob("*")
        if f.is_file() and f.suffix.lower() in NETTOYEURS
    )
    stats = Counter()

    for n, f in enumerate(fichiers, 1):
        rel = f.relative_to(args.source)
        try:
            contenu = NETTOYEURS[f.suffix.lower()](lire(f))
            if contenu:
                sortie = args.destination / rel.with_name(rel.name + ".txt")
                sortie.parent.mkdir(parents=True, exist_ok=True)
                sortie.write_text(contenu, encoding="utf-8")
                stats["traités"] += 1
            else:
                stats["ignorés"] += 1
        except Exception:
            stats["erreurs"] += 1

        if n % 500 == 0 or n == len(fichiers):
            print(f"{n}/{len(fichiers)}", dict(stats))

    print(f"\nTerminé : {dict(stats)} -> {args.destination}")


if __name__ == "__main__":
    main()