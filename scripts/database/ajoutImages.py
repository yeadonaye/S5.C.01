import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
TMDB_KEY = os.getenv("TMDB_API_KEY")
BUCKET = "affiches"

# J'ai ajouter cette liste parce que pour ces séries spécifiquement,
# le programme n'as pas pu trouver des affiches, j'ai donc modifier
# le code pour qu'il utilise les vrais nom des séries à la place des
# noms qui étais dans la BD.

TITRES = {
    'battlestargalactica': 'Battlestar Galactica',
    'betteroffted': 'Better Off Ted',
    'bionicwoman': 'Bionic Woman',
    'breakingbad': 'Breaking Bad',
    'burnnotice': 'Burn Notice',
    'criminalminds': 'Criminal Minds',
    'desperatehousewives': 'Desperate Housewives',
    'dirtysexymoney': 'Dirty Sexy Money',
    'doctorwho': 'Doctor Who',
    'eleventhhour': 'Eleventh Hour',
    'fearitself': 'Fear Itself',
    'flightoftheconchords': 'Flight of the Conchords',
    'fridaynightlights': 'Friday Night Lights',
    'garyunmarried': 'Gary Unmarried',
    'ghostwhisperer': 'Ghost Whisperer',
    'gossipgirl': 'Gossip Girl',
    'greysanatomy': "Grey's Anatomy",
    'howimetyourmother': 'How I Met Your Mother',
    'intreatment': 'In Treatment',
    'johnfromcincinnati': 'John from Cincinnati',
    'knightrider': 'Knight Rider',
    'kylexy': 'Kyle XY',
    'legendoftheseeker': 'Legend of the Seeker',
    'lietome': 'Lie to Me',
    'mastersofscifi': 'Masters of Science Fiction',
    'melroseplace': 'Melrose Place',
    'mynameisearl': 'My Name Is Earl',
    'ncislosangeles': 'NCIS: Los Angeles',
    'onetreehill': 'One Tree Hill',
    'painkillerjane': 'Painkiller Jane',
    'prisonbreak': 'Prison Break',
    'privatepractice': 'Private Practice',
    'pushingdaisies': 'Pushing Daisies',
    'raines': 'Raines',
    'samanthawho': 'Samantha Who?',
    'sexandthecity': 'Sex and the City',
    'sixfeetunder': 'Six Feet Under',
    'sonsofanarchy': 'Sons of Anarchy',
    'southpark': 'South Park',
    'stargateatlantis': 'Stargate Atlantis',
    'stargatesg1': 'Stargate SG-1',
    'thebigbangtheory': 'The Big Bang Theory',
    'theblackdonnellys': 'The Black Donnellys',
    'thekillpoint': 'The Kill Point',
    'thelostroom': 'The Lost Room',
    'thementalist': 'The Mentalist',
    'thenine': 'The Nine',
    'theoc': 'The O.C.',
    'thepretender': 'The Pretender',
    'thesarahconnorchronicles': 'Terminator: The Sarah Connor Chronicles',
    'theshield': 'The Shield',
    'thesopranos': 'The Sopranos',
    'thetudors': 'The Tudors',
    'thevampirediaries': 'The Vampire Diaries',
    'thewire': 'The Wire',
    'trucalling': 'Tru Calling',
    'trueblood': 'True Blood',
    'uglybetty': 'Ugly Betty',
    'veronicamars': 'Veronica Mars',
    'womensmurderclub': "Women's Murder Club",
}

# Séries ambiguës (remakes, séries homonymes) : on précise l'année de début
ANNEES = {
    'doctorwho': 2005,
    'battlestargalactica': 2004,
    'knightrider': 2008,
    'melroseplace': 2009,
    'bionicwoman': 2007,
    'eleventhhour': 2008,
}

def chercher_affiche(titre, annee=None):
    params = {"api_key": TMDB_KEY, "query": titre, "language": "en-US"}
    if annee:
        params["first_air_date_year"] = annee
    r = requests.get("https://api.themoviedb.org/3/search/tv", params=params)
    for res in r.json().get("results", []):
        if res.get("poster_path"):
            return res["name"], res["poster_path"]
    return None, None


# On ne traite que les séries qui n'ont pas encore d'affiche
series = (
    supabase.table("serie")
    .select("idserie, titre")
    .is_("affiche_url", "null")
    .execute()
    .data
)

non_trouvees = []
for s in series:
    titre_reel = TITRES.get(s["titre"], s["titre"])
    nom_tmdb, poster = chercher_affiche(titre_reel, ANNEES.get(s["titre"]))
    if not poster:
        non_trouvees.append(s["titre"])
        continue

    image = requests.get(f"https://image.tmdb.org/t/p/w500{poster}").content
    chemin = f"{s['idserie']}.jpg"
    supabase.storage.from_(BUCKET).upload(
        chemin, image, {"content-type": "image/jpeg", "upsert": "true"}
    )
    url = supabase.storage.from_(BUCKET).get_public_url(chemin)
    supabase.table("serie").update({"affiche_url": url}).eq("idserie", s["idserie"]).execute()

    print(f"{s['titre']}  ->  {nom_tmdb}")

print("\nSéries sans affiche :", non_trouvees)