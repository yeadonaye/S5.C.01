
import re
import numpy as np
import psycopg2
from scipy.sparse import csr_matrix, diags

DB_URL = "postgresql://postgres.txthevshtuxweaeqmosa:sxeEsh0KLaiKhlK2@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

# Réglage retenu après les tests
IDF_MIN = 0.7
IDF_MAX = 2.5
SUBLINEAIRE = True
FILTRER_PRENOMS = True      # retire les prénoms (corpus NLTK)

# --- Listes de mots à exclure --------------------------------------------

# Déchets de sous-titres : tags de release, légendes sourds/malentendants
STOP_TAGS = set("""
uncut sdi lls pos ydy bbs raceman seriessub arcadya tagne akazab bizut
italiansubs fbl mpm sixe iike iove ie cl ofthe fs56 tyno subtitle iook
bleep indistinct chattering suspenseful instrumental paced comms nc dd
lt sgt erm spoilers uk sie der bene que la fm hooray cant joes replie
loky lci sl abs bolo wil tru sadgeezer méfies puta
""".split())

# Noms de famille / personnages propres à une série (vus dans mots_suspects)
STOP_PERSONNAGES = set("""
bauer buchanan hodges palmer saunders raines heller dixon matthews langley
weiss devlin hart clifton jenkins parkinson stevens swanson crowley jeffries
goodman decker lynch ramos kirk elliott badger paso moody prose larkin shaw
tang nash winger chang pierce reid garcia strauss russo cajun hopper baxter
rutherford holt dawson perez davies norton sloan lloyd carter bishop bowman
newton conrad peck kif bender hewitt brooks gordon rufus malley yang burke
shepherd bennet lyle foley beckett malik gilligan klein churchill browning
lennox johnston hawkins cunningham connelly fowler sterling leary hoffman
whitman pearson ames reese crews hollis tucker barrett hutch campbell
briggs evans watt gomez morrow cavanaugh simms andrews talbot abbott pollock
camden hickey mcgee franks paulson mcguire pendleton oaks prescott cutter
becker burrows fife montgomery archer lassie spencer carlton gregor burton
clayton crocker fuller emerson billings brody newman chapman greer armstrong
baldwin farrell hauser jarvis huey dokey louie lino reilly maxwell harrington
pelt cho lisbon soprano walt pinkman tuco heisenberg skyler sheldon leonard
ross chandler joey monica bing phoebe rachel buffy willow tara xander
winchester sammy kent lana lex clark kryptonite bartowski intersect
lisbon seeker darken sg atlantis galactica starbuck kara apollo
""".split())

# Prénoms qui sont aussi de vrais mots : on les garde
GARDER = set("""
will mark bill rose grace hunter drew ray pat art faith hope joy april may
june august dawn eve angel jordan summer sue major king cook bob jack
""".split())


def charger_prenoms():
    """Prénoms anglais du corpus NLTK (vide si NLTK indisponible)."""
    try:
        import nltk
        try:
            from nltk.corpus import names
            liste = names.words()
        except LookupError:
            nltk.download("names", quiet=True)
            from nltk.corpus import names
            liste = names.words()
        return {n.lower() for n in liste} - GARDER
    except Exception as e:
        print(f"[!] Prénoms NLTK indisponibles ({e}). Filtre prénoms ignoré.")
        return set()


def construire_exclus(prenoms=FILTRER_PRENOMS):
    exclus = set(STOP_TAGS) | set(STOP_PERSONNAGES)
    if prenoms:
        exclus |= charger_prenoms()
    return exclus - GARDER


# --- Chargement et matrice -----------------------------------------------

def charger_donnees(conn):
    """Une seule lecture de la base. Retourne (ids, titres, donnees)."""
    cur = conn.cursor()
    cur.execute("SELECT idSerie, titre FROM Serie ORDER BY idSerie")
    series = cur.fetchall()
    ids = [s[0] for s in series]
    titres = [s[1] for s in series]
    ligne_de = {idS: i for i, idS in enumerate(ids)}

    cur.execute("""
        SELECT p.idSerie, m.mot, p.tfidf, m.idf
        FROM Posseder p JOIN Mot m ON m.idMot = p.idMot
    """)
    rows = cur.fetchall()
    cur.close()

    lignes = np.array([ligne_de[r[0]] for r in rows])
    mots = np.array([r[1] for r in rows])
    tfidf = np.array([r[2] for r in rows], dtype=float)
    idf = np.array([r[3] for r in rows], dtype=float)
    return ids, titres, (lignes, mots, tfidf, idf)


def construire_S(titres, donnees, idf_min=IDF_MIN, idf_max=IDF_MAX,
                 sublineaire=SUBLINEAIRE, exclus=frozenset()):
    """Matrice de similarité n×n en mémoire.
    exclus : mots à ignorer (en plus des mots contenant un chiffre)."""
    lignes, mots, tfidf, idf = donnees

    vocab, inv = np.unique(mots, return_inverse=True)
    mauvais_vocab = np.array(
        [(w in exclus) or bool(re.search(r"\d", w)) for w in vocab]
    )
    garde = (idf >= idf_min) & (idf <= idf_max) & ~mauvais_vocab[inv]

    l, m, t, w = lignes[garde], inv[garde], tfidf[garde], idf[garde]
    if sublineaire:
        t = np.log1p(t * 100)
    valeurs = t * w

    _, col = np.unique(m, return_inverse=True)
    M = csr_matrix((valeurs, (l, col)), shape=(len(titres), col.max() + 1))

    normes = np.sqrt(np.asarray(M.power(2).sum(axis=1)).ravel())
    normes[normes == 0] = 1
    M = diags(1 / normes) @ M

    S = (M @ M.T).toarray()
    np.fill_diagonal(S, 0)
    return S


def charger_similarites():
    """Raccourci : lit la base une fois et retourne (S, ids, titres)."""
    conn = psycopg2.connect(DB_URL)
    try:
        ids, titres, donnees = charger_donnees(conn)
    finally:
        conn.close()
    S = construire_S(titres, donnees, exclus=construire_exclus())
    return S, ids, titres


def _norm(s):
    return "".join(s.lower().split())


def trouver_index(titres, titre):
    cible = _norm(titre)
    for i, t in enumerate(titres):
        if _norm(t) == cible:
            return i
    raise ValueError(f"Titre introuvable : {titre!r}\nTitres disponibles : {titres}")


def similaires(S, titres, titre, n=5):
    i = trouver_index(titres, titre)
    top = np.argsort(S[i])[::-1][:n]
    return [(titres[j], round(float(S[i, j]), 3)) for j in top]


if __name__ == "__main__":
    conn = psycopg2.connect(DB_URL)
    ids, titres, donnees = charger_donnees(conn)
    conn.close()

    exclus = construire_exclus()
    S = construire_S(titres, donnees, exclus=exclus)

    n = len(titres)
    print(f"\n=== stoplist + prénoms | {len(exclus)} mots exclus | moyenne : {S.sum() / (n * (n - 1)):.3f}")

    for serie in ["The vampire diaries"]:
        print(f"  {serie} :")
        for t, score in similaires(S, titres, serie):
            print(f"    {t}  {score}")
