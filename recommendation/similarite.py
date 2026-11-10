import os
import re
import numpy as np
import psycopg2
from scipy.sparse import csr_matrix, diags
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")


# REGLAGES RETENUS APRES LES TESTS

IDF_MIN = 0.7            # on ignore les mots trop courants (IDF en dessous), ils n'aident pas à différencier les séries
IDF_MAX = 2.5            # on ignore les mots trop précis (IDF au-dessus), ils n'apparaissent que dans une ou deux séries
SUBLINEAIRE = True       # compresse le tfidf avec un log pour qu'un mot répété 50 fois ne pèse pas 50 fois plus qu'un mot dit une fois
FILTRER_PRENOMS = True   # retire les prénoms anglais du corpus NLTK pour que deux séries ne se ressemblent pas juste à cause d'un prénom commun


# NETTOYAGE DES MOTS : POURQUOI ICI ?
# Oui, c'est bizarre de voir un peu de nettoyage ici, mais c'est voulu.
# Les prénoms et noms de personnages sont très utiles pour un moteur de
# recherche : walt, meth ou heisenberg permettent de retrouver Breaking Bad.
# Ils sont donc gardés dans la base.
# En revanche, pour la similarité et les recommandations, ils faussent le
# résultat : si le personnage principal de deux séries s'appelle John, elles
# seront recommandées l'une à l'autre uniquement parce que le même prénom
# apparaît dans les deux.
# C'est pour ça qu'on les retire ici, au moment de calculer la similarité,
# et pas pendant le nettoyage général.
#
# Le filtre IDF fait le reste du travail :
# - les mots trop courants (IDF trop petit) sont ceux qui sont passés
#   à travers le nettoyage, ils n'aident pas à différencier les séries
# - les mots trop précis (IDF trop grand) sont ceux qui n'apparaissent que
#   dans une ou deux séries, comme les noms trop spécifiques
# On ne garde que les mots entre IDF_MIN et IDF_MAX.


# MOTS A EXCLURE

# Noms de famille et personnages propres à une série (vus dans mots_suspects)
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


# LISTE DES PRENOMS

# Récupère les prénoms anglais du corpus NLTK
# Retourne un ensemble vide si NLTK est indisponible
def charger_prenoms_nltk():
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


# Rassemble tous les mots à ignorer : personnages + prénoms (si activé)
# Les mots de la liste GARDER ne sont jamais exclus
def construire_mots_exclus(prenoms=FILTRER_PRENOMS):
    exclus = set(STOP_PERSONNAGES)
    if prenoms:
        exclus |= charger_prenoms_nltk()
    return exclus - GARDER


# CHARGEMENT DES DONNEES

# Lit la base une seule fois
# Retourne (ids, titres, donnees) avec donnees = (lignes, mots, tfidf, idf)
def charger_donnees_series(conn):
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


# MATRICE DE SIMILARITE

# Construit la matrice n x n qui donne la similarité entre chaque paire de séries
# Garde seulement les mots dont l'IDF est entre idf_min et idf_max,
# ignore les mots exclus et ceux qui contiennent un chiffre
def construire_matrice_similarite(titres, donnees, idf_min=IDF_MIN,
                                  idf_max=IDF_MAX, sublineaire=SUBLINEAIRE,
                                  exclus=frozenset()):
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


# Raccourci : ouvre la connexion, lit la base une fois et calcule la matrice
# Retourne (S, ids, titres)
def charger_matrice_similarite():
    conn = psycopg2.connect(DB_URL)
    try:
        ids, titres, donnees = charger_donnees_series(conn)
    finally:
        conn.close()
    S = construire_matrice_similarite(
        titres, donnees, exclus=construire_mots_exclus()
    )
    return S, ids, titres


# RECHERCHE DE SERIES SIMILAIRES

# Met un titre en minuscules et sans espaces pour pouvoir le comparer
def normaliser_titre(s):
    return "".join(s.lower().split())


# Retourne la position d'une série dans la liste des titres
# Lève une erreur si le titre n'existe pas
def trouver_index_serie(titres, titre):
    cible = normaliser_titre(titre)
    for i, t in enumerate(titres):
        if normaliser_titre(t) == cible:
            return i
    raise ValueError(f"Titre introuvable : {titre!r}\nTitres disponibles : {titres}")


# Retourne les n séries les plus proches d'un titre, avec leur score
def trouver_series_similaires(S, titres, titre, n=5):
    i = trouver_index_serie(titres, titre)
    top = np.argsort(S[i])[::-1][:n]
    return [(titres[j], round(float(S[i, j]), 3)) for j in top]