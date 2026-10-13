#let code       = "S5.C.01"
#let titre      = "Proposer une solution optimisée à partir des données"
#let sous-titre = "Dossier d'analyse et de conception"
#let auteurs    = ("HISABU Nathan Tekeste", "SENTAYEHU Yeadonaye Ashenafi")
#let encadrant  = "M. Julien BROISIN"
#let formation  = "BUT Informatique"
#let annee      = "2026 – 2027"

// fonction pour les commentaires
#let commentaire(author, msg, color) = {
  text(color, style: "italic")[#underline[*#author* :] #msg]
}
#let yado(msg) = commentaire("Yeadonaye", msg, rgb("#0091ff"))
#let nathan(msg) = commentaire("Nathan", msg, rgb("#e100ff"))

// Couleurs
#let accent = rgb("#d6283a")   // rouge UT
#let sombre = rgb("#6b1d27")   // bordeaux
#let gris   = luma(110)

// Réglages globaux
#set text(
  font: "Libertinus Serif", size: 12pt, lang: "fr", region: "fr")
#set heading(numbering: "1.")
#show heading.where(level: 1): set text(fill: sombre)
#set figure(supplement: "Fig.")
#set page(
  paper: "a4",
  margin: (top: 1.5cm, bottom: 2cm, left: 2cm, right: 2cm),
  header: context if counter(page).get().first() > 1 [
    #text(size: 10pt)[S5.C.01 - Proposer une solution optimisée à partir des données]
    #v(-0.5em)
    #line(length: 100%, stroke: 1pt + sombre)
    ],
  footer: context if counter(page).get().first() > 1 [
    #place(
      left + bottom, 
      dx: -0.7cm,
      dy: -0.5cm,
      image("assets/logoIUT.png")
    )

    #align(right)[
      Page #counter(page).display() sur #counter(page).final().first()
    ]
  ]
)

// =============
// Page de garde
// =============
#page(paper: "a4", margin: (x: 2.5cm, top: 2cm, bottom: 2cm), numbering: none)[

  // Bandeau à gauche
  #place(left + top, dx: -2.5cm, dy: -2cm, rect(width: 0.6cm, height: 29.7cm, fill: accent))

  #grid(
    rows: (auto, 1fr, auto),

    // logos
    grid(
      columns: (1fr, 1fr),
      align: (left + horizon, right + horizon),
      image("./assets/logoUT.png", height: 2cm),
      image("./assets/logoIUT.png", height: 3cm),
    ),

    // titre
    align(center + horizon)[
      #text(size: 30pt, weight: "bold", fill: accent, tracking: 3pt)[
        SAÉ #code
      ]
      #v(0.6cm)
      #line(length: 3cm, stroke: 2.5pt + accent)
      #v(0.9cm)
      #text(size: 30pt, weight: "bold", fill: sombre)[#titre]
      #v(0.9cm)
      #text(size: 20pt, weight: "bold", fill: gris)[#sous-titre]
    ],

    // auteurs / encadrant
    {
      grid(
        columns: (1fr, 1fr),
        gutter: 1cm,
        [
          #text(size: 9pt, fill: accent, weight: "bold", tracking: 1pt)[RÉALISÉ PAR]
          #v(0.2cm)
          #for a in auteurs [#a \ ]
        ],
        align(right)[
          #text(size: 9pt, fill: accent, weight: "bold", tracking: 1pt)[ENCADRANT]
          #v(0.2cm)
          #encadrant
        ],
      )
    },
  )
]
#pagebreak()

// ========
// Sommaire
// ========
#{
  show outline.entry.where(level: 1): it => {
    set text(weight: "bold")
    it
  }
  show outline.entry.where(level: 2): it => {
    set text(size: 11pt, fill: sombre)
    it
  }
  show outline.entry.where(level: 3): it => {
    set text(size: 11pt, style: "italic", fill: gris)
    it
  }
  outline(title: "Table des matières", indent: 2em, depth: 3)
}
#pagebreak()


= Objectifs généraux

Le binôme est chargé de réaliser un moteur de recherche et un moteur de recommandation de séries TV, à partir des fichiers de sous-titres de 128 séries mis à disposition par l'IUT. L'application permettra à tout utilisateur, connecté ou non, de rechercher des séries à partir d'un ou plusieurs mots-clés et d'obtenir des recommandations de séries pertinentes.

Ainsi, chaque utilisateur pourra rechercher et découvrir des séries directement depuis l'interface web, sans avoir besoin de créer de compte. Un utilisateur souhaitant personnaliser ses recommandations pourra créer un compte afin d'évaluer les séries qu'il a appréciées (note de 1 à 5), ces évaluations venant enrichir le moteur de recommandation. Les fonctions de recherche et de recommandation reposent sur des techniques de fouille de texte appliquées au contenu des sous-titres, et sont exposées sous la forme d'une API REST consommée par l'interface web.

= Enumération des fonctions

Les fonctions principales attendues se divisent en deux catégories principales: #text(fill: accent)[visiteur (non connecté)] et #text(fill: accent)[utilisateur connecté].

Fonctions d'un visiteur (non connecté) : Rechercher et découvrir des séries
#pad(left: 1.5em)[
  + Rechercher des séries à partir d'un ou de plusieurs mots-clés
  + Obtenir des recommendations de séries (par défaut, donc les séries ayant des évaluations plus importantes)
]

Fonctions d'un utilisateur connecté : Gérer son compte et personnaliser ses recommendations
#pad(left: 1.5em)[
  + Modifier son compte
  + Supprimer son compte
  + Se connecter / se déconnecter
  + Evaluer une série (note allant de 1 à 5)
  + Rechercher des séries à partir d'un ou de plusieurs mots-clés
  + Obtenir des recommendations personnalisées basées sur ses évaluations
]

= Description des grandes fonctionnalités
== Cas d'utilisation
#figure(
  image("../diagrammes/images/diagrammeCasUtilisation.png", width: 40em),
  caption: "Diagramme de cas d'utilisation du système de recher et recommandation de séries"
)

== Fiches détaillées par fonction
#v(1em)
Cas d'utilisation (#text(weight: "bold")[Rechercher des séries]):

#pad(left: 1.5em)[
  #text(weight: "bold", fill: accent)[Rôle :] Ce cas d'utilisation est déclanché lorsqu'un utilisateur (connecté ou pas) souhaite réaliser une recherche de série à partir d'un ou plusieurs mots-clés.

  #text(weight: "bold", fill: accent)[Début :] Lorsque l'utilisateur saisit un ou plusieurs mots-clées dans la barre de recherche et valide (en cliquant sur le bouton 'rechercher')

  #text(weight: "bold", fill: accent)[Fin :] A l'affichage de la liste des séries triées par pertinence.

  #text(weight: "bold", fill: accent)[Précondition :] Néant (fonction accessible sans connexion obligatoire)

  #text(weight: "bold", fill: accent)[Postcondition :] Néant

  #text(weight: "bold", fill: accent)[Données en entrée :] Néant

  #text(weight: "bold", fill: accent)[Données en sortie :] Néant

  #text(weight: "bold", fill: accent)[Exception :] Aucun résultat pertinent trouvé.
]
#v(2em)
Cas d'utilisation (#text(weight: "bold")[Recommander des séries]):

#pad(left: 1.5em)[
  #text(weight: "bold", fill: accent)[Rôle :] Ce cas d'utilisation est déclenché lorsqu'un utilisateur souhaite se voir proposer des séries susceptibles de l'intéresser, en fonction de ses évaluations passées s'il est connecté (Recommandation personnalisé), ou des séries les mieux notées dans le cas contraire (Recommandation des meilleures séries).

  #text(weight: "bold", fill: accent)[Début :] Lorsque l'utilisateur accède à la page de recherche.

  #text(weight: "bold", fill: accent)[Fin :] A l'affichage de la liste des séries triées par pertinence.

  #text(weight: "bold", fill: accent)[Précondition :] Néant si c'est un visieur; utilisateur authentifié pour obtenir des recommendations personnalisées.

  #text(weight: "bold", fill: accent)[Postcondition :] Néant

  #text(weight: "bold", fill: accent)[Données en entrée :] Identifiant utilisateur (si connecté)

  #text(weight: "bold", fill: accent)[Données en sortie :] Liste de séries recommandées, triées par score de pertinence.

  #text(weight: "bold", fill: accent)[Exception :] Aucune évaluation disponible pour personnaliser (repli sur les recommandation par défaut)/ Problème de connexion avec le serveur.
]
#v(2em)
Cas d'utilisation (#text(weight: "bold")[Gérer son compte]):

#pad(left: 1.5em)[
  #text(weight: "bold", fill: accent)[Rôle :] Ce cas d'utilisation regroupe la création, la modificatio, et la suppression d'un compte utilisateur, ainsi que la connexion/déconnexion et l'évaluation d'une série (note de 1 à 5), ces deux dernières actions nécessitent d'être authentifié d'abord.

  #text(weight: "bold", fill: accent)[Début :] Lorsque l'utilisateur accède à l'espace compte (ou espace d'inscription).

  #text(weight: "bold", fill: accent)[Fin :] A la déconnexion ou à la fermeture de la session.

  #text(weight: "bold", fill: accent)[Précondition :] Identifiants valides pour la connexion; email non déjà utilisé pour la création de compte; compte existant pour la suprression.

  #text(weight: "bold", fill: accent)[Postcondition :] Le compte est créé, ou modifié, ou supprimé dans la base de données, ou l'évaulation est enregistrée.

  #text(weight: "bold", fill: accent)[Données en entrée :] Email, mot de passe (création, ou connexion)

  #text(weight: "bold", fill: accent)[Données en sortie :] Confirmation de l'opération effectué

  #text(weight: "bold", fill: accent)[Exception :] Idententifiants invalides, ou Email déjà utilisé, ou problème de ocnnexion avec le serveur
]
#pagebreak()

== Diagrammes de séquence

Digramme de séquence pour la fonctionnalité de recherche de série à partir d'un ou de plusieurs mots clés.
#figure(
  image("../diagrammes/images/diagrammeDeSequenceRecherche.png", width: 40em),
  caption: [Diagramme de séquence de recherche de série]
)

#v(3em)

Digramme de séquance pour la fonctionnalité de recommendation de série (pour un utilisateur connecté ou non connecté).
#figure(
  image("../diagrammes/images/diagrammeDeSequenceRecommandation.png", width: 40em),
  caption: [Diagramme de séquence de recommendation de série]
)

#v(3em)

Digramme de séquence pour la fonctionnalité de notation de série.
#figure(
  image("../diagrammes/images/diagrammeDeSequenceNoteSeries.png", width: 40em),
  caption: [Diagramme de séquence de notation de série]
)

= Architecture générale
#yado("A faire une fois que le projet est terminé")

== Description des composants et de leurs intéractions
== Arborescence de l'application
#yado("A faire une fois l'application terminé")

= Modèle de données
== MCD
#figure(
  image("../diagrammes/images/MCD.png", width: 40em),
  caption: [Modèle conceptuel de données]
)

== MLD
#figure(
  image("../diagrammes/images/MLD.png", width: 40em),
  caption: [MLD textuel du modèle conceptuel de données]
)

= Maquettes de l'interface web
#yado("A faire une fois que le projet est terminé")
