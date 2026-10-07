#let code       = "S5.C.01"
#let titre      = "Proposer une solution optimisée à partir des données"
#let sous-titre = "Dossier de programmation"
#let auteurs    = ("HISABU Nathan Teskeste", "SENTAYEHU Yeadonaye Ashenafi")
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
  outline(title: text(fill: accent)[Table des matières], indent: 2em, depth: 3)
}
#pagebreak()

