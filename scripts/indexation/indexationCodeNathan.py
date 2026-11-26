
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

# indexation.py is inside the "indexation" folder.
DOSSIER_PROJET = Path(__file__).resolve().parent.parent

# Folder produced by your stop-word removal script.
RACINE = (
    DOSSIER_PROJET
    / "nettoyageFichiers"
    / "resultat"
    / "sousTitresSansStopWords"
)

# Index output folder.
SORTIE = DOSSIER_PROJET / "resultatIndexation"


# --------------------------------------------------
# 2. READ THE SERIES
# --------------------------------------------------

def main():

    if not RACINE.is_dir():
        raise FileNotFoundError(
            f"Dataset introuvable : {RACINE}"
        )

    dossiers = sorted(
        dossier
        for dossier in RACINE.iterdir()
        if dossier.is_dir()
    )

    if not dossiers:
        raise ValueError(
            f"Aucun dossier de série trouvé dans : {RACINE}"
        )

    noms = []
    documents = []

    for dossier in dossiers:

        # Read every processed episode in this series,
        # including files inside nested directories.
        fichiers = sorted(dossier.rglob("*.txt"))

        if not fichiers:
            print(f"Aucun fichier TXT ignoré : {dossier.name}")
            continue

        textes = []

        for fichier in fichiers:
            texte = fichier.read_text(
                encoding="utf-8-sig",
                errors="ignore"
            )

            if texte.strip():
                textes.append(texte)

        if not textes:
            print(f"Aucun texte exploitable : {dossier.name}")
            continue

        # One document = all processed subtitles of one series.
        noms.append(dossier.name)
        documents.append(" ".join(textes))

    if not documents:
        raise ValueError(
            "Aucun texte exploitable pour calculer TF-IDF."
        )

    print(f"Séries indexées : {len(documents)}")
    print("Calcul de TF-IDF...")


    # --------------------------------------------------
    # 3. CALCULATE TF-IDF
    # --------------------------------------------------

    vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b\w+\b"
    )

    matrice = vectorizer.fit_transform(documents)
    mots = vectorizer.get_feature_names_out()


    # --------------------------------------------------
    # 4. EXPORT THE INDEX
    # --------------------------------------------------

    SORTIE.mkdir(parents=True, exist_ok=True)

    for i, nom in enumerate(noms):

        ligne = matrice.getrow(i)

        scores = {
            mots[j]: round(float(score), 6)
            for j, score in zip(ligne.indices, ligne.data)
        }

        scores = dict(
            sorted(
                scores.items(),
                key=lambda element: element[1],
                reverse=True
            )
        )

        chemin_sortie = SORTIE / f"{nom}.json"

        with chemin_sortie.open(
            "w",
            encoding="utf-8"
        ) as fichier:
            json.dump(
                scores,
                fichier,
                ensure_ascii=False,
                indent=2
            )

    # Save the vectorizer too, so the search engine can
    # reuse the same vocabulary and IDF weights later.
    import pickle

    with (SORTIE / "vectorizer.pkl").open("wb") as fichier:
        pickle.dump(vectorizer, fichier)

    print(f"\nIndexation terminée.")
    print(f"Séries indexées : {len(noms)}")
    print(f"Vocabulaire : {len(mots)} termes")
    print(f"Résultats enregistrés dans : {SORTIE}")


if __name__ == "__main__":
    main()
