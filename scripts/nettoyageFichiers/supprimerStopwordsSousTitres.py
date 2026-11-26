import argparse
import re
import unicodedata
from collections import Counter
from pathlib import Path

MOT = re.compile(r"[^\W_]+(?:'[^\W_]+)*")  # mots et contractions (don't, l'homme)
ELISION = re.compile(r"^(?:[cçdjlmnst]|qu|jusqu|lorsqu|puisqu|quoiqu)'(?=\w)")


def normaliser(texte):
    return unicodedata.normalize("NFC", texte).lower().replace("’", "'")


def charger_stopwords(chemin):
    lignes = chemin.read_text(encoding="utf-8-sig").splitlines()
    mots = {normaliser(ligne.strip()) for ligne in lignes}
    return {m for m in mots if m and not m.startswith("#")}


def mots_utiles(texte, stopwords):
    for mot in MOT.findall(normaliser(texte)):
        if mot in stopwords:
            continue
        mot = ELISION.sub("", mot)  # l'homme -> homme, qu'est -> est
        if len(mot) > 1 and mot not in stopwords:
            yield mot


def main():
    base = Path(__file__).resolve().parent
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=base / "resultat" / "dossierNettoyerSousTitres")
    p.add_argument("--destination", type=Path, default=base / "resultat" / "sousTitresSansStopWords")
    p.add_argument("--stopwords", type=Path, default=base / "stopwords_fr_en.txt")
    args = p.parse_args()

    if not args.source.is_dir():
        raise SystemExit(f"Dossier source introuvable : {args.source}")
    stopwords = charger_stopwords(args.stopwords)
    fichiers = sorted(f for f in args.source.rglob("*.txt") if not f.name.startswith("_"))
    print(f"{len(stopwords)} stop words, {len(fichiers)} fichiers")

    stats = Counter()
    for n, f in enumerate(fichiers, 1):
        rel = f.relative_to(args.source)
        try:
            texte = f.read_text(encoding="utf-8-sig")
            sortie = args.destination / rel
            sortie.parent.mkdir(parents=True, exist_ok=True)
            sortie.write_text(" ".join(mots_utiles(texte, stopwords)), encoding="utf-8")
            stats["traités"] += 1
        except (OSError, UnicodeError) as e:
            stats["erreurs"] += 1
            print(f"Erreur sur {rel} : {e}")

        if n % 500 == 0 or n == len(fichiers):
            print(f"{n}/{len(fichiers)}", dict(stats))

    print(f"\nTerminé : {dict(stats)} -> {args.destination}")


if __name__ == "__main__":
    main()