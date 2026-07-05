---
id: brevet-2026-maths
type: Course
schema: fr-dnb
subject: maths
name: "Mathématiques — DNB 2026"
educationalLevel: "Collège 3ème"
provider:
  name: "Ministère de l'Éducation Nationale"
competencyFramework: fr-socle-commun-c4
source: "BREVET_2026_MANUEL.md — Section 1 Mathématiques"
language: fr

required_competencies:
  - id: maths-automatismes-fractions
    label: "Fractions et décimales (sans calculatrice)"
    weight: high
  - id: maths-automatismes-carres
    label: "Carrés parfaits 1² à 12²"
    weight: high
  - id: maths-automatismes-divisibilite
    label: "Critères de divisibilité"
    weight: high
  - id: maths-geometrie-pythagore
    label: "Pythagore — direct, réciproque, contraposée"
    weight: high
  - id: maths-geometrie-thales
    label: "Thalès — emboîtée et papillon"
    weight: high
  - id: maths-geometrie-trigo
    label: "Trigonométrie sin, cos, tan"
    weight: high
  - id: maths-geometrie-volumes
    label: "Volumes — formules"
    weight: medium
  - id: maths-algebre-identites
    label: "Identités remarquables"
    weight: high
  - id: maths-algebre-equations
    label: "Équations 1er degré + équation-produit nul"
    weight: high
  - id: maths-algebre-fonctions
    label: "Fonction linéaire f(x)=ax et affine f(x)=ax+b"
    weight: medium
  - id: maths-algebre-nombres-premiers
    label: "Nombres premiers jusqu'à 30"
    weight: low
  - id: maths-stats-probabilites
    label: "Probabilités — événement contraire, équiprobabilité"
    weight: high
  - id: maths-algo-scratch
    label: "Algorithmique Scratch — boucles, variables, conditionnelles"
    weight: medium

exam:
  duration: PT2H
  total_points: 20
  parts:
    - id: automatismes
      name: "Partie A — Automatismes"
      duration: PT20M
      points: 6
      constraints: [no-calculator, timed-removal]
      note: "Feuille ramassée à 20 min exactement — aucun accès au livret avant"
    - id: raisonnement
      name: "Partie B — Raisonnement & Problèmes"
      duration: PT1H40M
      points: 14
      constraints: [calculator-non-programmable]
      note: "2 pts sur 14 réservés à la clarté du raisonnement — calcul sans rédaction = 0 sur ces 2 pts"

---

# Automatismes

<!-- competency: maths-automatismes-fractions -->
## Fractions et décimales {#drill .no-calculator .weight-high}

| Fraction | Décimal |
|---|---|
| 1/2 | 0,5 |
| 1/4 | 0,25 |
| 3/4 | 0,75 |
| 3/2 | 1,5 |
| 4/2 | 2 |
| 5/2 | 2,5 |
| 1/10 | 0,1 |
| 1,2 | 12/10 = 6/5 = 120% |

<!-- competency: maths-automatismes-carres -->
## Carrés parfaits {#drill .no-calculator .weight-high}

| n | n² |
|---|---|
| 1 | 1 |
| 2 | 4 |
| 3 | 9 |
| 4 | 16 |
| 5 | 25 |
| 6 | 36 |
| 7 | 49 |
| 8 | 64 |
| 9 | 81 |
| 10 | 100 |
| 11 | 121 |
| 12 | 144 |

<!-- competency: maths-automatismes-divisibilite -->
## Critères de divisibilité {#glossary .weight-high}

- **Par 2** : chiffre des unités pair (0, 2, 4, 6, 8)
- **Par 3** : somme des chiffres est un multiple de 3
- **Par 5** : chiffre des unités est 0 ou 5
- **Par 9** : somme des chiffres est un multiple de 9

> [!PIÈGE]
> "Divisible par 6" n'est pas un critère autonome — vérifier divisibilité par 2 ET par 3 séparément.

# Arithmétique

<!-- competency: maths-algebre-nombres-premiers -->
## Nombres premiers {#glossary .weight-low}

- **Nombre premier** : entier > 1 ayant exactement deux diviseurs : 1 et lui-même
- **Liste jusqu'à 30** : 2, 3, 5, 7, 11, 13, 17, 19, 23, 29
- **Décomposition** : tout entier ≥ 2 se décompose de façon unique en produit de facteurs premiers
- **PGCD** : plus grand entier divisant simultanément deux nombres. Si PGCD(a,b) = 1 → fraction a/b irréductible

# Calcul littéral et algèbre

<!-- competency: maths-algebre-identites -->
## Identités remarquables {#concept .weight-high}

Les trois identités fondamentales :
- (a + b)² = a² + 2ab + b²
- (a − b)² = a² − 2ab + b²
- (a − b)(a + b) = a² − b²

Factorisation : ka + kb = k(a + b)

> [!PIÈGE]
> (a + b)² ≠ a² + b² — le terme 2ab est obligatoire. Erreur la plus fréquente en algèbre.

<!-- competency: maths-algebre-equations -->
## Équations {#concept .weight-high}

**1er degré :** ax + b = c → x = (c − b)/a (pour a ≠ 0)

**Équation-produit nul :** (ax + b)(cx + d) = 0 ⟺ ax + b = 0 OU cx + d = 0

**Développement :**
- Distributivité simple : k(a + b) = ka + kb
- Double : (a + b)(c + d) = ac + ad + bc + bd

<!-- competency: maths-algebre-fonctions -->
## Fonctions {#concept .weight-medium}

- **Linéaire** : f(x) = ax — droite passant par l'origine — modélise la proportionnalité
- **Affine** : f(x) = ax + b — droite quelconque — a = coefficient directeur, b = ordonnée à l'origine

# Géométrie

<!-- competency: maths-geometrie-volumes -->
## Formules de mesure {#glossary .weight-medium}

- **Cercle** : P = 2πr | Aire disque = πr²
- **Triangle** : A = (base × hauteur) / 2
- **Cube** : V = c³
- **Pavé droit** : V = L × l × h
- **Cylindre** : V = πr²h
- **Pyramide** : V = (Abase × h) / 3
- **Cône** : V = (πr²h) / 3
- **Sphère** : V = (4/3)πr³

<!-- competency: maths-geometrie-pythagore -->
## Théorème de Pythagore {#concept .theorem .weight-high}

**Direct :** Si un triangle est rectangle en A, alors BC² = AB² + AC²

**Réciproque :** Si BC² = AB² + AC² (grand côté² = somme des deux autres²), alors le triangle est rectangle en A.

**Contraposée :** Si BC² ≠ AB² + AC², alors le triangle n'est pas rectangle.

**Méthode exigée (triptyque) :**
1. Données : "Je sais que dans le triangle ABC, le plus grand côté est BC avec BC = …"
2. Calculs séparés : "D'une part BC² = … D'autre part AB² + AC² = …"
3. Propriété : "Or, d'après la réciproque du théorème de Pythagore…"
4. Conclusion : "Donc le triangle ABC est rectangle en A."

> [!PIÈGE]
> Ne jamais écrire BC² = AB² + AC² en première ligne. Calculer d'une part BC², puis d'autre part AB²+AC², puis seulement constater l'égalité et conclure. Le correcteur barre immédiatement si l'égalité est posée avant les calculs.

<!-- competency: maths-geometrie-thales -->
## Théorème de Thalès {#concept .theorem .weight-high}

**Configuration emboîtée :** Si (MN) est parallèle à (BC) dans le triangle ABC :
AM/AB = AN/AC = MN/BC

**Configuration papillon :** Droites (BD) et (CE) sécantes en A, avec (BC) ∥ (DE) :
AB/AD = AC/AE = BC/DE

(A est entre B et D, et entre C et E — les rapports partent tous du sommet A.)

> [!PIÈGE]
> Vérifier la configuration avant d'appliquer. En papillon, A est entre B et D (et entre C et E) — les rapports s'écrivent depuis le sommet A.

<!-- competency: maths-geometrie-trigo -->
## Trigonométrie {#concept .weight-high}

Dans un triangle rectangle (angle droit en A) :
- cos(B) = côté adjacent / hypoténuse
- sin(B) = côté opposé / hypoténuse
- tan(B) = côté opposé / côté adjacent

**Mnémotechnique :** SOH-CAH-TOA

> [!PIÈGE]
> L'hypoténuse est TOUJOURS le côté face à l'angle droit — ne pas la confondre avec le côté adjacent selon l'angle choisi.

# Statistiques et Probabilités

<!-- competency: maths-stats-probabilites -->
## Probabilités {#concept .weight-high}

**Formule de base (équiprobabilité) :**
P(A) = nombre d'issues favorables / nombre d'issues possibles
— valable uniquement si toutes les issues ont la même probabilité.

**Règles fondamentales :**
- 0 ≤ P(A) ≤ 1
- P(Ā) = 1 − P(A) — événement contraire
- P(A∩B) = 0 — événements incompatibles (ne peuvent pas se produire simultanément)
- P(A∪B) = P(A) + P(B) si A et B incompatibles

**Arbres de probabilité :**
- Chaque branche porte la probabilité de l'issue correspondante
- Multiplier les probabilités le long d'une branche (succession d'événements)
- Additionner les branches correspondant à l'événement cherché
- La somme de toutes les branches issues d'un même nœud = 1

> [!PIÈGE]
> Indépendants ≠ incompatibles. Deux événements incompatibles (P(A∩B) = 0) ne peuvent pas être indépendants — si l'un se produit, l'autre est impossible, donc ils s'influencent.

**Statistiques :**
- Moyenne : somme des valeurs ÷ effectif total
- Médiane : valeur partageant la série ordonnée en deux moitiés égales

**Proportionnalité :**
- Augmentation de t% : multiplier par (1 + t/100)
- Diminution de t% : multiplier par (1 − t/100)

# Algorithmique

<!-- competency: maths-algo-scratch -->
## Algorithmique Scratch {#concept .weight-medium}

Blocs Scratch à reconnaître :
- **Boucle** : "Répéter N fois"
- **Variable** : "Définir ma_variable à…"
- **Conditionnelle** : "Si… Alors… Sinon"

> [!PIÈGE]
> Une boucle "Répéter 5 fois" exécute le bloc exactement 5 fois — ne pas confondre le compteur (qui commence à 1) avec une condition "tant que compteur < 5" (qui dépend de l'état initial).

# Dictionnaire

<!-- competency: maths-algebre-nombres-premiers -->
## Vocabulaire clé {#glossary}

- **Abscisse** : coordonnée horizontale d'un point dans un repère
- **Antécédent** : valeur x donnée à une fonction pour obtenir f(x)
- **Coefficient directeur** : paramètre a dans f(x) = ax + b — détermine la pente
- **Équiprobabilité** : toutes les issues ont la même probabilité
- **Homothétie** : transformation multipliant toutes les distances par k depuis un centre fixe
- **Hypoténuse** : côté le plus long d'un triangle rectangle, en face de l'angle droit
- **Image** : résultat f(x) renvoyé par une fonction
- **Médiane** : valeur partageant la population en deux moitiés égales
- **Ordonnée à l'origine** : valeur b où la droite coupe l'axe vertical
- **PGCD** : plus grand entier divisant simultanément plusieurs nombres
