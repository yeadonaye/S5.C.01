# Storyboard du projet — Moteur de recherche & recommandation de séries TV

> Version non-alternant (projet complet : recherche + recommandation + API REST + interface web)

---

## 1. Cadrage & mise en place du projet

**Description générale** : Poser les fondations organisationnelles avant de coder quoi que ce soit — outils, binôme, dépôt, planning.

- Créer le tableau Trello du projet et inviter l'enseignant (<julien.broisin@irit.fr>)
- Créer le dépôt Git (GitLab/GitHub) et donner l'accès à l'enseignant
- Définir la répartition des rôles dans le binôme (même si tout le monde touche à tout)
- Lister les livrables attendus et leurs échéances dans Trello (créer une carte par livrable)
- Choisir la stack technique (langage, framework API, framework front, base de données)
- Mettre en place l'environnement de dev (repo cloné en local, structure de dossiers, README initial)

---

## 2. Analyse et conception (Dossier d'analyse et de conception)

**Description générale** : Rédiger le dossier qui explique *quoi* et *comment*, avant d'implémenter. C'est un livrable en soi, à produire tôt car il structure toute la suite.

- Rédiger les objectifs généraux de l'application
- Décrire les fonctions principales (recherche, recommandation, gestion de compte) + un cas d'utilisation par fonction
- Réaliser les diagrammes de séquence des fonctions principales
- Concevoir l'architecture générale (schéma des composants : scripts de traitement, base de données, moteur de recherche, moteur de recommandation, API REST, front web) et décrire leurs interactions
- Concevoir le modèle conceptuel de données (MCD) + description textuelle
- Concevoir le modèle logique de données (MLD) + description textuelle
- Réaliser les maquettes de l'interface web (pages recherche, résultats, recommandations, compte utilisateur, notation d'une série)
- Compiler et mettre en forme le dossier final

---

## 3. Préparation des données (nettoyage, indexation)

**Description générale** : Avant de pouvoir chercher/recommander quoi que ce soit, il faut transformer les 128 fichiers de sous-titres bruts en données exploitables et propres, stockées en base.

- Explorer un échantillon de fichiers de sous-titres pour comprendre leur format (SRT, encodage, structure)
- Écrire un script de parsing des sous-titres (extraction du texte, suppression des timecodes/balises)
- Écrire un script de nettoyage du texte : suppression de la ponctuation, mise en minuscule, suppression des stopwords, éventuellement lemmatisation/stemming
- Définir le modèle de base de données pour stocker séries, sous-titres nettoyés, index de mots, utilisateurs, notes
- Écrire le script de création de la base de données (migrations/schéma)
- Écrire le script d'indexation : construire l'index inversé ou la représentation vectorielle (ex. TF-IDF) des séries à partir du texte nettoyé
- Écrire un script d'import qui exécute toute la chaîne (parsing → nettoyage → indexation → insertion en base) pour les 128 séries
- Vérifier la qualité des données (quelques séries testées manuellement)

---

## 4. Moteur de recherche

**Description générale** : Permettre à un utilisateur de taper des mots-clés et retrouver les séries les plus pertinentes, en s'appuyant sur les techniques de fouille de texte (pas sur des métadonnées comme le genre).

- Choisir la méthode de scoring de pertinence (TF-IDF, BM25, similarité cosinus, etc.)
- Implémenter la fonction de recherche multi-mots-clés sur l'index construit à l'étape 3
- Implémenter le tri des résultats par pertinence
- Optimiser les performances pour rester sous quelques dixièmes de seconde (indexation adaptée, mise en cache éventuelle)
- Tester la recherche sur des cas connus (ex. "crash avion île" → Lost dans le top 3)
- Ajuster les paramètres du modèle selon les résultats des tests

---

## 5. Moteur de recommandation

**Description générale** : Suggérer des séries à un utilisateur en croisant le contenu textuel des séries et les notes données par les utilisateurs (recommandation basée contenu + collaborative).

- Concevoir le modèle de notation (note de 1 à 5 par utilisateur/série)
- Implémenter une recommandation basée sur le contenu (similarité textuelle entre séries aimées et autres séries)
- Implémenter (ou au moins réfléchir à) une recommandation collaborative basée sur les notes des autres utilisateurs
- Définir la stratégie pour un utilisateur non connecté ou sans historique (ex. séries populaires ou recommandation par mots-clés)
- Implémenter la fonction de recommandation finale (combinaison des approches)
- Optimiser les performances (temps de réponse acceptable)
- Tester la pertinence des recommandations sur des cas concrets

---

## 6. Gestion des utilisateurs et des comptes

**Description générale** : Permettre la création de comptes et l'enregistrement des notes, tout en gardant la recherche/recommandation accessible sans connexion.

- Concevoir le modèle utilisateur (identifiants, sécurité des mots de passe)
- Implémenter la création de compte
- Implémenter la modification de compte
- Implémenter la suppression de compte
- Implémenter l'authentification (connexion/déconnexion)
- Implémenter la fonctionnalité de notation d'une série (1 à 5) par un utilisateur connecté
- Vérifier que la recherche et la recommandation restent accessibles sans compte/connexion

---

## 7. API REST

**Description générale** : Exposer toutes les fonctionnalités (recherche, recommandation, gestion de compte, notation) via une API REST propre et documentée.

- Définir les routes de l'API (recherche, recommandation, comptes utilisateurs, notation)
- Implémenter les endpoints de recherche
- Implémenter les endpoints de recommandation
- Implémenter les endpoints de gestion de compte (CRUD)
- Implémenter les endpoints de notation d'une série
- Gérer l'authentification/autorisation au niveau de l'API (ex. token)
- Gérer les erreurs et les codes de retour HTTP
- Documenter l'API (ex. Swagger/OpenAPI ou documentation manuelle)
- Tester chaque endpoint (via Postman/curl ou tests automatisés)

---

## 8. Interface web

**Description générale** : Construire une interface ergonomique qui consomme l'API REST et permet à un utilisateur lambda d'utiliser toutes les fonctionnalités.

- Mettre en place le projet front-end (structure, dépendances)
- Développer la page/formulaire de recherche par mots-clés
- Développer la page d'affichage des résultats de recherche
- Développer la page de recommandations personnalisées
- Développer les pages de gestion de compte (création, modification, suppression, connexion)
- Développer la fonctionnalité de notation d'une série depuis l'interface
- Connecter l'interface à l'API REST
- Soigner l'ergonomie et le responsive design
- Tester l'interface avec un utilisateur non technique

---

## 9. Tests (Dossier de tests)

**Description générale** : Prouver que les fonctions jugées essentielles marchent correctement, et documenter ces tests dans un dossier dédié.

- Sélectionner les fonctions critiques à tester (recherche, recommandation, création de compte, notation, endpoints API)
- Écrire des scénarios de test pour chaque fonction sélectionnée
- Exécuter les tests et consigner les résultats (captures d'écran, tableaux)
- Rédiger le dossier de tests avec les scénarios et résultats

---

## 10. Documentation (Dossier de programmation & Manuel d'utilisation)

**Description générale** : Documenter le code pour un lecteur technique, et l'usage de l'application pour un lecteur non technique.

- Sélectionner les extraits de code représentatifs des fonctions clés (nettoyage, indexation, recherche, recommandation, API)
- Rédiger le dossier de programmation autour de ces extraits (explications, choix techniques)
- Rédiger le manuel d'utilisation pas-à-pas (recherche, recommandation, création de compte, notation) avec captures d'écran, pour un utilisateur non informaticien

---

## 11. Finalisation et livraison

**Description générale** : Rassembler tous les livrables, vérifier leur conformité avec la consigne, et déposer sur Moodle.

- Relire et mettre en forme le dossier d'analyse et de conception
- Relire et mettre en forme le dossier de programmation
- Relire et mettre en forme le dossier de tests
- Vérifier que le code source complet est propre et présent sur le dépôt Git
- Relire et mettre en forme le manuel d'utilisation
- Vérifier l'activité Trello et Git du binôme (traçabilité pour l'évaluation)
- Déposer l'ensemble des livrables sur Moodle dans les espaces prévus

---

### Suggestion d'usage

Chaque section ci-dessus peut devenir une **liste Trello**, et chaque sous-tâche une **carte**. Les tâches 1 à 3 sont bloquantes pour tout le reste (pas de recherche/recommandation sans données propres et indexées) — à démarrer en priorité.
