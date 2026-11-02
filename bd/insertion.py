import os, io, csv, json, math
from collections import defaultdict
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv(DB_URL)
DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indexation/resultatIndexation")
LONGUEUR_MAX = 100  # taille max d'un mot (VARCHAR(100))


def lire_fichier(chemin):
    """Retourne {mot: tfidf} pour une série (fichier JSON)."""
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def copier(cur, table_et_colonnes, lignes):
    buf = io.StringIO()
    csv.writer(buf).writerows(lignes)
    buf.seek(0)
    cur.copy_expert(f"COPY {table_et_colonnes} FROM STDIN WITH (FORMAT csv)", buf)


# 1. Lecture des fichiers
series = {}
for nom in sorted(os.listdir(DOSSIER)):
    if not nom.endswith(".json"):
        continue
    titre = os.path.splitext(nom)[0]
    series[titre] = lire_fichier(os.path.join(DOSSIER, nom))

# 2. idf calculé sur TOUS les mots
nb_series = len(series)
df = defaultdict(int)
for mots in series.values():
    for mot in mots:
        df[mot] += 1
idf = {mot: math.log(nb_series / d) for mot, d in df.items()}

# 3. Seul filtre : longueur maximale du mot (plus de limite par série)
for titre, mots in series.items():
    series[titre] = {m: v for m, v in mots.items() if len(m) <= LONGUEUR_MAX}

mots_gardes = {m for mots in series.values() for m in mots}

# 4. Insertion en base
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Vidage des tables + remise à zéro des identifiants
cur.execute("TRUNCATE Posseder, Mot, Serie RESTART IDENTITY CASCADE")

copier(cur, "Serie(titre)", [(t,) for t in series])
copier(cur, "Mot(mot, idf)", [(m, idf[m]) for m in mots_gardes])

cur.execute("SELECT titre, idSerie FROM Serie")
id_serie = dict(cur.fetchall())
cur.execute("SELECT mot, idMot FROM Mot")
id_mot = dict(cur.fetchall())

lignes = [
    (id_serie[titre], id_mot[mot], tfidf)
    for titre, mots in series.items()
    for mot, tfidf in mots.items()
]
copier(cur, "Posseder(idSerie, idMot, tfidf)", lignes)

conn.commit()
cur.close()
conn.close()
print(f"{len(series)} séries, {len(mots_gardes)} mots, {len(lignes)} lignes dans Posseder")