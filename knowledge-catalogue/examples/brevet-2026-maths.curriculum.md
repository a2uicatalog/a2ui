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
source: source_dnb2026_automatismes.pdf
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
  - id: maths-algebre-identites
    label: "Identités remarquables"
    weight: high
  - id: maths-algebre-equations
    label: "Équations du 1er et 2e degré"
    weight: high
  - id: maths-algebre-fonctions
    label: "Fonction linéaire et affine"
    weight: medium
  - id: maths-algebre-nombres-premiers
    label: "Nombres premiers jusqu'à 30"
    weight: low
  - id: maths-stats-probabilites
    label: "Probabilités — arbres, événements contraires"
    weight: high
  - id: maths-algo-scratch
    label: "Algorithmique — boucles, variables, conditionnelles"
    weight: medium

exam:
  duration: PT2H
  total_points: 20
  parts:
    - id: automatismes
      name: Automatismes
      duration: PT20M
      points: 6
      constraints: [no-calculator, timed-removal]
    - id: raisonnement
      name: Raisonnement et Problèmes
      duration: PT1H40M
      points: 14
      note: "2 pts réservés à la clarté du raisonnement — triptyque obligatoire"

render:
  hub_label: "📐 Maths"
  hub_color: "#6366f1"
---

# Automatismes

<!-- competency: maths-automatismes-fractions -->
## Fractions et décimales {#drill .no-calculator .weight-high}

| Fraction | Décimal |
|---|---|
| 1/2 | 0,5 |
| 1/4 | 0,25 |
| 3/4 | 0,75 |
| 1/3 | 0,333... |
| 2/3 | 0,666... |
| 3/2 | 1,5 |
| 5/4 | 1,25 |
| 1/5 | 0,2 |

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

- **Par 2** : le chiffre des unités est pair (0, 2, 4, 6, 8)
- **Par 3** : la somme des chiffres est divisible par 3
- **Par 5** : le chiffre des unités est 0 ou 5
- **Par 9** : la somme des chiffres est divisible par 9
- **Par 10** : le chiffre des unités est 0

> [!PIÈGE]
> "Divisible par 6" n'est pas un critère autonome — vérifier divisibilité par 2 ET par 3 séparément.

# Géométrie

<!-- competency: maths-geometrie-pythagore -->
## Théorème de Pythagore {#concept .theorem .weight-high}

**Définition:** Dans un triangle rectangle en A, on a BC² = AB² + AC²

**Variantes:**
- Direct: si rectangle en A → BC² = AB² + AC²
- Réciproque: si BC² = AB² + AC² → triangle rectangle en A
- Contraposée: si BC² ≠ AB² + AC² → triangle non rectangle en A

**Méthode (triptyque obligatoire):**
1. Données: "Le triangle ABC est tel que..."
2. Propriété: "D'après le théorème de Pythagore..."
3. Conclusion: "Donc le triangle ABC est rectangle en A"

> [!PIÈGE]
> Ne jamais écrire BC² = AB² + AC² en première ligne sans avoir calculé les deux membres séparément.
> Calculer d'une part BC², puis d'autre part AB²+AC², puis conclure par égalité ou inégalité.

<!-- competency: maths-geometrie-thales -->
## Théorème de Thalès {#concept .theorem .weight-high}

**Configuration emboîtée:** Droites (AB) et (AC) sécantes en A. Si (MN) parallèle à (BC):
AM/AB = AN/AC = MN/BC

**Configuration papillon (ou sablier):** Droites (BD) et (CE) sécantes en A. Si (BC) ∥ (DE):
AB/AD = AC/AE = BC/DE

> [!PIÈGE]
> Vérifier la configuration avant d'appliquer le théorème. En papillon, les rapports s'inversent par rapport à l'emboîtée — toujours partir du sommet A.

<!-- competency: maths-geometrie-trigo -->
## Trigonométrie {#concept .weight-high}

Dans un triangle rectangle en A:
- sin B = côté opposé / hypoténuse = AC/BC
- cos B = côté adjacent / hypoténuse = AB/BC
- tan B = côté opposé / côté adjacent = AC/AB

**Mnémotechnique:** SOH-CAH-TOA

> [!PIÈGE]
> L'hypoténuse est TOUJOURS le côté face à l'angle droit. Ne pas confondre côté adjacent et côté opposé selon l'angle considéré.

# Algèbre

<!-- competency: maths-algebre-identites -->
## Identités remarquables {#concept .weight-high}

- (a+b)² = a² + 2ab + b²
- (a-b)² = a² - 2ab + b²
- (a+b)(a-b) = a² - b²

**Utilisation:** développer, factoriser, vérifier une égalité algébrique.

> [!PIÈGE]
> (a+b)² ≠ a²+b² — l'erreur la plus fréquente. Le terme 2ab est obligatoire.

<!-- competency: maths-algebre-equations -->
## Équations {#concept .weight-high}

**1er degré:** ax + b = 0 → x = -b/a (si a ≠ 0)

**2e degré (trinôme):** ax² + bx + c = 0
- Discriminant: Δ = b² - 4ac
- Si Δ > 0: deux solutions x = (-b ± √Δ) / 2a
- Si Δ = 0: une solution double x = -b/2a
- Si Δ < 0: pas de solution réelle

<!-- competency: maths-algebre-fonctions -->
## Fonctions linéaires et affines {#concept .weight-medium}

- **Linéaire:** f(x) = ax — droite passant par l'origine
- **Affine:** f(x) = ax + b — droite de pente a, ordonnée à l'origine b

**Lecture graphique:** pente = (y2-y1)/(x2-x1) entre deux points

<!-- competency: maths-algebre-nombres-premiers -->
## Nombres premiers {#glossary .weight-low}

- **Nombre premier** : entier > 1 dont les seuls diviseurs sont 1 et lui-même
- **Liste jusqu'à 30** : 2, 3, 5, 7, 11, 13, 17, 19, 23, 29
- **Décomposition** : tout entier > 1 se décompose de façon unique en produit de nombres premiers

# Statistiques et Probabilités

<!-- competency: maths-stats-probabilites -->
## Probabilités {#concept .weight-high}

**Vocabulaire:**
- Expérience aléatoire: résultat imprévisible
- Univers Ω: ensemble de tous les résultats possibles
- Événement: sous-ensemble de Ω
- P(A) = nombre de cas favorables / nombre de cas possibles (équiprobabilité)

**Événements:**
- Contraires: P(Ā) = 1 - P(A)
- Incompatibles: P(A∩B) = 0
- Indépendants: P(A∩B) = P(A) × P(B)

**Arbres de probabilité:** multiplier les probabilités sur les branches, additionner les branches favorables.

> [!PIÈGE]
> "Indépendants" ≠ "incompatibles". Deux événements incompatibles (qui ne peuvent pas se produire ensemble) ne sont pas indépendants — si l'un se produit, l'autre ne peut pas, donc ils s'influencent.

# Algorithmique

<!-- competency: maths-algo-scratch -->
## Algorithmique {#concept .weight-medium}

**Structures de base (Scratch ou Python):**
- Variable: case mémoire nommée contenant une valeur
- Séquence: instructions exécutées dans l'ordre
- Boucle bornée: répéter N fois (for)
- Boucle non bornée: répéter tant que condition (while)
- Conditionnelle: si... alors... sinon (if/else)

**Lecture d'algorithme:** tracer l'état des variables à chaque étape (tableau de valeurs).

> [!PIÈGE]
> Une boucle "répéter 5 fois" exécute le bloc exactement 5 fois — ne pas confondre avec "tant que compteur < 5" qui peut varier selon l'état initial du compteur.
