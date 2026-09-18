from pathlib import Path
from collections import Counter, defaultdict
import py7zr
import re


# ============================================================
# CONFIGURATION
# ============================================================

ARCHIVE_PATH = Path("sous-titres.7z")

# Subtitle formats we're interested in
SUBTITLE_EXTENSIONS = {
    ".srt",
    ".vtt",
    ".ass",
    ".ssa",
    ".sub",
    ".sbv"
}


# ============================================================
# DATA WE WILL COLLECT
# ============================================================

series = set()
subtitle_files = []

nested_archives = []

language_counts = Counter()
extension_counts = Counter()

episodes_by_series = defaultdict(set)


# ============================================================
# HELPERS
# ============================================================

def detect_language(filename):
    """
    Try to identify VO / VF from the filename.

    Examples:
        S01E01.VO.srt -> VO
        S01E01.VF.srt -> VF
        episode_vo.srt -> VO
    """

    name = filename.lower()

    if re.search(r'(^|[._\-\s])vo([._\-\s]|$)', name):
        return "VO"

    if re.search(r'(^|[._\-\s])vf([._\-\s]|$)', name):
        return "VF"

    return "UNKNOWN"


def detect_episode(filename):
    """
    Detect episode codes such as:

        S01E01
        S02E15
        S1E3
    """

    match = re.search(
        r's\d{1,2}e\d{1,2}',
        filename,
        re.IGNORECASE
    )

    if match:
        return match.group(0).upper()

    return None


def get_series_name(path):
    """
    Assume the first directory inside the archive
    corresponds to the series name.

    Example:

        Lost/Season1/S01E01.VO.srt

    -> Lost
    """

    parts = Path(path).parts

    if len(parts) >= 2:
        return parts[0]

    return None


# ============================================================
# START
# ============================================================

print("=" * 70)
print("EXPLORATION DU DATASET")
print("=" * 70)


# Check that the archive exists
if not ARCHIVE_PATH.exists():

    print(
        f"❌ Fichier introuvable : "
        f"{ARCHIVE_PATH}"
    )

    print(
        "\n💡 Vérifie que le fichier "
        "'sous-titres.7z' est dans le même "
        "dossier que ce script."
    )

    raise SystemExit


print(f"\n📦 Archive : {ARCHIVE_PATH}")

print("🔍 Lecture de la structure du 7z...\n")


# ============================================================
# READ 7Z
# ============================================================

try:

    with py7zr.SevenZipFile(
        ARCHIVE_PATH,
        mode="r"
    ) as archive:

        # Get every file/path contained in the archive
        all_files = archive.getnames()

except Exception as e:

    print("❌ Impossible de lire l'archive.")

    print(f"Erreur : {e}")

    raise SystemExit


print(
    f"📁 Éléments trouvés dans l'archive : "
    f"{len(all_files)}"
)


# ============================================================
# ANALYZE ARCHIVE CONTENTS
# ============================================================

for path in all_files:

    path_obj = Path(path)

    # Ignore directories
    if path.endswith("/"):
        continue

    suffix = path_obj.suffix.lower()


    # --------------------------------------------------------
    # NESTED ARCHIVES
    # --------------------------------------------------------

    if suffix in {
        ".7z",
        ".zip",
        ".rar",
        ".tar"
    }:

        nested_archives.append(path)

        continue


    # --------------------------------------------------------
    # SUBTITLE FILES
    # --------------------------------------------------------

    if suffix not in SUBTITLE_EXTENSIONS:
        continue


    # Detect information
    language = detect_language(path)

    episode = detect_episode(path)

    series_name = get_series_name(path)


    # Store subtitle information
    subtitle_files.append({

        "path": path,

        "extension": suffix,

        "language": language,

        "episode": episode

    })


    # Update statistics
    extension_counts[suffix] += 1

    language_counts[language] += 1


    # Store series
    if series_name:

        series.add(series_name)


        if episode:

            episodes_by_series[
                series_name
            ].add(episode)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("📊 RÉSUMÉ")
print("=" * 70)


print(
    f"\n📺 Séries découvertes : "
    f"{len(series)}"
)


print(
    f"📝 Fichiers de sous-titres : "
    f"{len(subtitle_files)}"
)


# ------------------------------------------------------------
# LANGUAGE
# ------------------------------------------------------------

print("\n🌍 Versions :")

for language, count in language_counts.most_common():

    print(
        f"   {language:<10} {count}"
    )


# ------------------------------------------------------------
# EXTENSIONS
# ------------------------------------------------------------

print("\n📄 Formats de sous-titres :")

for extension, count in extension_counts.most_common():

    print(
        f"   {extension:<10} {count}"
    )


# ------------------------------------------------------------
# NESTED ARCHIVES
# ------------------------------------------------------------

print(
    f"\n📦 Archives imbriquées : "
    f"{len(nested_archives)}"
)


# ============================================================
# SERIES + EPISODES
# ============================================================

print("\n" + "=" * 70)
print("📺 SÉRIES")
print("=" * 70)


for name in sorted(series):

    episodes = episodes_by_series[name]

    print(
        f"{name:<45} "
        f"{len(episodes):>3} épisodes détectés"
    )


# ============================================================
# POSSIBLE MISSING EPISODES
# ============================================================

print("\n" + "=" * 70)
print("🔎 VÉRIFICATION DES ÉPISODES")
print("=" * 70)


for name in sorted(series):

    episodes = episodes_by_series[name]


    if not episodes:
        continue


    # Convert S01E01 -> (1, 1)
    parsed = []


    for episode in episodes:

        match = re.match(
            r"S(\d+)E(\d+)",
            episode
        )


        if match:

            season = int(match.group(1))

            ep = int(match.group(2))

            parsed.append(
                (season, ep)
            )


    if not parsed:
        continue


    # Group episodes by season
    seasons = defaultdict(list)


    for season, ep in parsed:

        seasons[season].append(ep)


    missing = []


    # Look for gaps
    for season, eps in seasons.items():

        eps = sorted(eps)


        for ep in range(
            min(eps),
            max(eps) + 1
        ):

            if ep not in eps:

                missing.append(
                    f"S{season:02d}E{ep:02d}"
                )


    # Display possible missing episodes
    if missing:

        print(f"\n⚠️ {name}")

        print(
            "   Épisodes potentiellement "
            "manquants :"
        )

        print(
            "   " + ", ".join(missing)
        )


# ============================================================
# UNKNOWN VF / VO
# ============================================================

unknown = [

    item

    for item in subtitle_files

    if item["language"] == "UNKNOWN"

]


print("\n" + "=" * 70)
print("❓ SOUS-TITRES SANS VF / VO IDENTIFIÉ")
print("=" * 70)


print(
    f"\nNombre : {len(unknown)}"
)


# Show first 50
for item in unknown[:50]:

    print(
        f"   {item['path']}"
    )


if len(unknown) > 50:

    print(
        f"   ... et "
        f"{len(unknown) - 50} autres"
    )


# ============================================================
# NESTED ARCHIVES
# ============================================================

print("\n" + "=" * 70)
print("📦 ARCHIVES IMBRIQUÉES")
print("=" * 70)


if nested_archives:

    for archive in nested_archives:

        print(
            f"   {archive}"
        )

else:

    print("   Aucune archive imbriquée détectée.")


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("✅ EXPLORATION TERMINÉE")
print("   Aucun fichier n'a été extrait.")
print("   Aucun fichier n'a été modifié.")
print("=" * 70)