CREATE TABLE Utilisateur (
    idUtilisateur   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom             VARCHAR(100) NOT NULL,
    prenom          VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    motDePasseHash  VARCHAR(255) NOT NULL,
    dateInscription DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE Serie (
    idSerie INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titre   VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Mot (
    idMot INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mot   VARCHAR(100) NOT NULL UNIQUE,
    idf   REAL NOT NULL
);

CREATE TABLE Evaluer (
    idUtilisateur  BIGINT NOT NULL REFERENCES Utilisateur(idUtilisateur) ON DELETE CASCADE,
    idSerie        INT    NOT NULL REFERENCES Serie(idSerie) ON DELETE CASCADE,
    note           SMALLINT NOT NULL CHECK (note BETWEEN 1 AND 5),
    dateEvaluation DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (idUtilisateur, idSerie)
);

CREATE TABLE Posseder (
    idSerie INT NOT NULL REFERENCES Serie(idSerie) ON DELETE CASCADE,
    idMot   INT NOT NULL REFERENCES Mot(idMot) ON DELETE CASCADE,
    tfidf   REAL NOT NULL,
    PRIMARY KEY (idSerie, idMot)
);

-- Index pour la recherche par mot-clé (le PK couvre déjà idSerie en premier)
CREATE INDEX idx_posseder_mot ON Posseder(idMot);

-- Sécurité Supabase : bloque l'accès public via l'API automatique
ALTER TABLE Utilisateur ENABLE ROW LEVEL SECURITY;
ALTER TABLE Serie       ENABLE ROW LEVEL SECURITY;
ALTER TABLE Mot         ENABLE ROW LEVEL SECURITY;
ALTER TABLE Evaluer     ENABLE ROW LEVEL SECURITY;
ALTER TABLE Posseder    ENABLE ROW LEVEL SECURITY;
