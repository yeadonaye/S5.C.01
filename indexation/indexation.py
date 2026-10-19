import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

# Chemin vers le répertoire racine (à adapter si besoin)
RACINE = Path(r"nettoyageFichiers\resultat\sous-titres")
# Le dossier de sortie est créé à côté du répertoire racine
SORTIE = RACINE.parent / "resultatIndexation"


def main():
    dossiers = sorted(d for d in RACINE.iterdir() if d.is_dir())
    noms = [d.name for d in dossiers]
    # 1 document = le fichier .srt unique de chaque dossier
    documents = [
        next(d.glob("*.srt")).read_text(encoding="utf-8", errors="ignore")
        for d in dossiers
    ]

    vectorizer = TfidfVectorizer()
    matrice = vectorizer.fit_transform(documents)
    mots = vectorizer.get_feature_names_out()

    SORTIE.mkdir(exist_ok=True)
    for i, nom in enumerate(noms):
        ligne = matrice[i]
        scores = {mots[j]: round(float(ligne[0, j]), 6) for j in ligne.nonzero()[1]}
        scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
        with open(SORTIE / f"{nom}.json", "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)

    print(f"{len(noms)} fichiers d'indexation créés dans {SORTIE}")


if __name__ == "__main__":
    main()