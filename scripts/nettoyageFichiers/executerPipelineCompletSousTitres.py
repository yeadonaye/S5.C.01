import subprocess
import sys
from pathlib import Path

# Dossier contenant ce script et les trois scripts a executer
DOSSIER = Path(__file__).resolve().parent

# Scripts de traitement des sous-titres, dans l'ordre d'execution
SCRIPTS = [
    "extraireEtAplatirSousTitres.py",
    "nettoyerEtSupprimerElementsNonTextuels.py",
    "supprimerStopwordsSousTitres.py",
]


def main():
    print("=" * 60)
    print("EXECUTION DU PIPELINE COMPLET DE TRAITEMENT DES SOUS-TITRES")
    print("=" * 60)

    for numero, nom_script in enumerate(SCRIPTS, start=1):
        chemin_script = DOSSIER / nom_script

        if not chemin_script.is_file():
            print(f"\nERREUR : script introuvable : {chemin_script}")
            sys.exit(1)

        print(f"\n[{numero}/{len(SCRIPTS)}] Execution : {nom_script}")
        print("-" * 60)

        resultat = subprocess.run(
            [sys.executable, str(chemin_script)],
            cwd=str(DOSSIER),
        )

        if resultat.returncode != 0:
            print(f"\nECHEC : {nom_script}")
            print("Les scripts suivants ne seront pas executes.")
            sys.exit(resultat.returncode)

        print(f"\nTERMINE : {nom_script}")

    print("\n" + "=" * 60)
    print("PIPELINE TERMINE AVEC SUCCES !")
    print("=" * 60)


if __name__ == "__main__":
    main()