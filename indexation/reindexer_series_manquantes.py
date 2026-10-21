
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer

# Chemins relatifs depuis le dossier S5.C.01
BASE = Path(__file__).resolve().parent.parent

RACINE = BASE / "nettoyageFichiers" / "resultat" / "dossierNettoyerSousTitres"
SORTIE = BASE / "indexation" / "resultatIndexation"

SERIES_MANQUANTES = ["journeyman", "sixfeetunder", "spaced"]


def lire_serie(dossier):
    contenu = []

    for fichier in dossier.glob("*.txt"):
        contenu.append(
            fichier.read_text(encoding="utf-8", errors="ignore")
        )

    return "\n".join(contenu)


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)

    for nom in SERIES_MANQUANTES:
        dossier = RACINE / nom

        if not dossier.is_dir():
            print(f"[ERREUR] Dossier introuvable : {dossier}")
            continue

        texte = lire_serie(dossier)

        if not texte.strip():
            print(f"[ERREUR] Aucun texte exploitable pour : {nom}")
            continue

        vectorizer = TfidfVectorizer()

        try:
            matrice = vectorizer.fit_transform([texte])
        except ValueError as erreur:
            print(f"[ERREUR] {nom} : {erreur}")
            continue

        mots = vectorizer.get_feature_names_out()
        ligne = matrice[0]

        scores = {
            mots[j]: round(float(ligne[0, j]), 6)
            for j in ligne.nonzero()[1]
        }

        scores = dict(
            sorted(scores.items(), key=lambda x: x[1], reverse=True)
        )

        destination = SORTIE / f"{nom}.json"

        with destination.open("w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)

        print(f"[OK] {destination.name} créé ({len(scores)} mots)")

    print("\nRéindexation terminée.")


if __name__ == "__main__":
    main()
