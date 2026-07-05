---
id: brevet-2026-sciences
type: Course
schema: national-education/fr/dnb-2026
subject: sciences
name: "Sciences — DNB 2026 (PC + SVT + Technologie)"
educationalLevel: "Collège 3ème"
provider:
  name: "Ministère de l'Éducation Nationale"
competencyFramework: fr-socle-commun-c4
source: "BREVET_2026_MANUEL.md — Section 4 Sciences"
language: fr

required_competencies:
  - id: pc-atomique
    label: "PC — Modèle atomique, numéro atomique Z, tableau périodique"
    weight: high
  - id: pc-reactions
    label: "PC — Équations de réaction, loi de Lavoisier, équilibrage"
    weight: high
  - id: pc-solutions
    label: "PC — C=m/V, pH (acide/neutre/basique), sécurité dilution"
    weight: high
  - id: pc-mecanique
    label: "PC — v=d/t, forces vectorielles, P=mg, U=RI, P=UI, E=Pt"
    weight: high
  - id: pc-ondes
    label: "PC — Ondes sonores vs lumineuses, d=v×t/2 (aller-retour)"
    weight: medium
  - id: svt-terre
    label: "SVT — Tectonique des plaques, séismes (foyer/épicentre), volcanisme effusif/explosif"
    weight: high
  - id: svt-biodiversite
    label: "SVT — Écosystèmes, biodiversité, perturbations anthropiques"
    weight: medium
  - id: svt-vivant
    label: "SVT — Corps à l'effort, agents pathogènes, vaccination, procréation"
    weight: high
  - id: techno-chaines
    label: "Techno — Chaîne d'énergie + chaîne d'information"
    weight: high
  - id: techno-reseaux
    label: "Techno — IP, switch, routeur, TCP/IP, client/serveur, RGPD"
    weight: medium
  - id: techno-programmation
    label: "Techno — Algorithmique Python/Scratch, variables, boucles, conditionnelles"
    weight: medium

exam:
  duration: PT1H
  total_points: 50
  note: "Tirage au sort le jour J : 2 matières sur 3 (PC, SVT, Techno) — 25 pts chacune. Réviser les 3 intégralement. Orthographe et clarté de la rédaction évaluées même en Sciences."

---

# Physique-Chimie

<!-- competency: pc-atomique -->
## Modèle atomique et tableau périodique {#concept .weight-high}

**Structure de l'atome :**
- **Noyau** : protons (charge positive +) + neutrons (charge neutre)
- **Électrons** : charge négative −, gravitent autour du noyau
- Atome électriquement neutre : nombre de protons = nombre d'électrons
- **Numéro atomique Z** = nombre de protons dans le noyau (identifie l'élément chimique)

**Tableau périodique (familles clés) :**
- Classé par Z croissant (hydrogène Z=1, carbone Z=6, oxygène Z=8…)
- **Colonne 1 — Alcalins** : réactifs avec l'eau (lithium, sodium, potassium)
- **Colonne 17 — Halogènes** : très réactifs (fluor, chlore, brome, iode)
- **Colonne 18 — Gaz nobles** : inertes chimiquement (hélium, néon, argon) — couche externe complète

> [!PIÈGE]
> Z = nombre de protons = nombre d'électrons (dans un atome neutre). Confondre Z (numéro atomique) avec la masse atomique est l'erreur classique. La masse atomique ≈ protons + neutrons — Z ne compte que les protons.

<!-- competency: pc-reactions -->
## Équations de réaction chimique {#concept .weight-high}

**Loi de conservation de Lavoisier :**
- La masse se conserve dans toute réaction chimique
- Le nombre d'atomes de chaque espèce se conserve

**Écriture d'une équation de réaction :**
Réactifs → Produits

**Équilibrage (ajuster les coefficients stœchiométriques) :**
- Compter les atomes de chaque élément des deux côtés
- Ajuster uniquement les **coefficients** devant les formules
- **JAMAIS** modifier les indices dans les formules chimiques (H₂O ≠ HO₂)

**Exemple :** Combustion du méthane
CH₄ + 2 O₂ → CO₂ + 2 H₂O
— Vérification : C: 1=1 ✓ | H: 4=4 ✓ | O: 4=4 ✓

> [!PIÈGE]
> On n'équilibre JAMAIS en changeant les indices (les petits chiffres dans les formules). Écrire H₄O pour équilibrer l'hydrogène = erreur chimique fondamentale. On ajuste uniquement les grands coefficients devant chaque formule.

<!-- competency: pc-solutions -->
## Solutions et pH {#concept .weight-high}

**Concentration en masse :**
> C = m / V
> C en g/L, m en grammes, V en litres

**pH :**
- pH < 7 : solution **acide** (majorité d'ions H⁺)
- pH = 7 : solution **neutre** (eau pure à 25°C)
- pH > 7 : solution **basique** (majorité d'ions HO⁻)

**Règle de sécurité — Dilution d'un acide :**
Toujours verser l'**acide dans l'eau** (jamais l'inverse).
— L'acide concentré dans l'eau : chaleur dissipée progressivement.
— L'eau dans l'acide concentré : bouillonnement violent, projections acides dangereuses.

> [!PIÈGE]
> Unités dans C = m/V : la masse DOIT être en grammes et le volume en litres. Si le volume est donné en mL, diviser par 1000. Appliquer la formule avec les mauvaises unités = résultat absurde et tous les points de calcul perdus.

<!-- competency: pc-mecanique -->
## Mouvement, forces et énergie {#glossary .weight-high}

**Calcul de vitesse :**
> v = d / t
> Conversions : m/s × 3,6 = km/h | km/h ÷ 3,6 = m/s

**Types de mouvement :**
- Trajectoire rectiligne / circulaire
- Vitesse uniforme (constante) / accéléré (augmente) / décéléré (diminue)

**Forces :**
- À distance : gravité (poids), magnétisme
- De contact : frottement, réaction du support (normale)
- Représentation vectorielle : point d'application, direction, sens, valeur (en Newtons N)

**Masse vs Poids :**

| | Masse (m) | Poids (P) |
|---|---|---|
| Unité | kilogrammes (kg) | Newtons (N) |
| Nature | quantité de matière | force gravitationnelle |
| Varie selon le lieu ? | **Non** — invariable | **Oui** — dépend de g |
| Formule | — | P = m × g |

g_Terre ≈ 9,8 N/kg | g_Lune ≈ 1,6 N/kg

**Lois électriques :**
- Loi d'Ohm : **U = R × I** (U en Volts V, R en Ohms Ω, I en Ampères A)
- Puissance : **P = U × I** (en Watts W)
- Énergie : **E = P × t** (en Joules si t en secondes | en kWh si P en kW et t en heures)

**Formes d'énergie :** cinétique, potentielle, mécanique (Ec + Ep), thermique, chimique, électrique, rayonnante

> [!PIÈGE]
> Masse ≠ poids. La masse est invariable (même sur la Lune). Le poids dépend de g. Un astronaute de 80 kg pèse P = 80 × 9,8 = 784 N sur Terre, mais P = 80 × 1,6 = 128 N sur la Lune. Sa masse reste 80 kg.

<!-- competency: pc-ondes -->
## Ondes et signaux {#concept .weight-medium}

**Ondes sonores :**
- Onde **mécanique** : nécessite un milieu matériel — ne se propage pas dans le vide
- Vitesse dans l'air : ~340 m/s à 20°C
- Caractérisée par fréquence (Hz) et amplitude (volume)

**Ondes lumineuses :**
- Se propagent dans le **vide** à c = 3 × 10⁸ m/s
- Réfraction lors d'un changement de milieu (brisure du rayon)
- Lumière blanche → spectre continu (arc-en-ciel) décomposé par un prisme

**Mesure par aller-retour (écho, sonar, radar, échographie) :**
> d = v × t / 2
> Le signal fait l'aller ET le retour — diviser le temps total par 2

> [!PIÈGE]
> Son ≠ lumière : le son ne se propage PAS dans le vide (espace = silence total). La lumière se propage dans le vide à 300 000 km/s. Confondre les deux lors d'une question sur les étoiles est une erreur majeure.

# Sciences de la Vie et de la Terre

<!-- competency: svt-terre -->
## Tectonique des plaques {#concept .weight-high}

**Principe général :**
La lithosphère est découpée en plaques rigides mobiles (quelques cm/an sur l'asthénosphère ductile).

**Types de frontières :**

| Type | Mouvement | Conséquences |
|---|---|---|
| **Divergence** (dorsales) | Plaques qui s'écartent | Création lithosphère océanique + volcanisme **effusif** (lave fluide) |
| **Convergence** (subduction) | Plaque océanique dense plonge | Séismes violents + volcanisme **explosif** (lave visqueuse, dangereux) |

**Mécanisme des séismes :**
1. Contraintes tectoniques s'accumulent sur une faille
2. Rupture brusque au **foyer** (hypocentre) — en profondeur
3. Ondes sismiques se propagent dans toutes directions
4. **Épicentre** : point à la surface à la verticale du foyer — vibrations maximales

**Répartition mondiale :** ceinture de feu du Pacifique, dorsale médio-atlantique

> [!PIÈGE]
> Foyer ≠ épicentre. Le foyer est EN PROFONDEUR (là où la rupture se produit). L'épicentre est EN SURFACE (à la verticale du foyer). Les dégâts sont maximaux à l'épicentre, pas au foyer.

<!-- competency: svt-biodiversite -->
## Écosystèmes et biodiversité {#concept .weight-medium}

**Composantes d'un écosystème :**
- **Biotope** : milieu physique (sol, eau, air, température, lumière)
- **Biocénose** : ensemble des êtres vivants du milieu
- Biotope + Biocénose → liés par des réseaux trophiques (chaînes alimentaires)

**Perturbations anthropiques :**
- Déforestation, artificialisation des sols, pollutions chimiques
- Espèces invasives qui déséquilibrent les réseaux trophiques
- Changement climatique : modification des niches écologiques

**Solutions :**
- Préservation in situ (parcs naturels, réserves)
- Restauration d'écosystèmes dégradés
- Lutte contre espèces invasives

<!-- competency: svt-vivant -->
## Corps humain et santé {#concept .weight-high}

**Fonctionnement à l'effort :**
- Muscles : besoin accru en O₂ et glucose → fréquences cardiaque et respiratoire augmentent
- Commande du mouvement : cerveau (décision) → moelle épinière (relais) → nerfs moteurs → muscles
- Retour sensitif : nerfs sensitifs → moelle épinière → cerveau
- **Dopage** : perturbe les régulations hormonales et cardiaques, risques graves (dépendance, mort subite)

**Agents pathogènes :**

| Étape | Définition |
|---|---|
| **Contamination** | Pénétration de l'agent pathogène après franchissement des barrières (peau, muqueuses) |
| **Infection** | Multiplication active dans l'organisme → apparition des symptômes |
| **Asepsie** | Prévenir la contamination (lavage des mains, outils stériles) |
| **Antisepsie** | Détruire les microbes sur une plaie ouverte (désinfectant) |
| **Antibiotiques** | Détruisent les **bactéries uniquement** — aucune efficacité contre les virus |
| **Vaccination** | Agent atténué/inactivé → stimule la mémoire immunitaire → protection individuelle ET collective |

**Immunité de groupe :** si une proportion critique de la population est immunisée, le virus ne trouve plus assez de personnes susceptibles pour se propager.
Exemple : vaccination HPV (cancer du col de l'utérus — campagne nationale dès 11 ans)

**Procréation humaine :**
- ♂ : production continue de spermatozoïdes dès la puberté
- ♀ : cycle ~28 jours — ovulation à J14 — règles si pas de fécondation — ménopause
- **Fécondation** : spermatozoïde + ovule → **cellule-œuf (zygote)** — se produit dans les trompes de Fallope
- **Nidation** : implantation du zygote dans l'endomètre → développement embryonnaire

> [!PIÈGE]
> Antibiotiques ≠ antiviraux. Prescrire des antibiotiques contre une grippe, le COVID ou la rougeole est une erreur biologique fondamentale lourdement pénalisée — et une cause réelle d'antibiorésistance mondiale. Contre un virus : vaccination (prévention), antiviraux spécifiques (traitement), asepsie (barrière).

# Technologie

<!-- competency: techno-chaines -->
## Chaînes d'énergie et d'information {#concept .weight-high}

Tout système automatisé possède deux chaînes en interaction :

**Chaîne d'information :**
Acquérir (Capteurs) → Traiter (Microcontrôleur) → Communiquer (Fils / Radio)

**Chaîne d'énergie :**
Alimenter (Batterie / Secteur) → Distribuer (Relais / Disjoncteur) → Convertir (Moteur / LED / Résistance) → Transmettre (Engrenages / Courroies)

**Composants clés :**
- **Capteurs** : convertissent une grandeur physique en signal exploitable (présence, température, luminosité, distance)
- **Actionneurs** : convertissent le signal en action mécanique, lumineuse ou sonore (moteur, vérin, LED, buzzer)

**Exemple — Robot aspirateur :**
1. Capteur ultrason détecte un mur → signal électrique (Acquérir)
2. Microcontrôleur traite → décide de tourner (Traiter)
3. Ordre envoyé aux moteurs (Communiquer)
4. Batterie → relais → moteurs électriques → engrenages → roues tournent (Énergie)

> [!PIÈGE]
> La chaîne d'information DIRIGE la chaîne d'énergie — le flux va de l'information vers l'énergie, pas l'inverse. Un capteur appartient à la chaîne d'information (il "acquiert"), pas à la chaîne d'énergie.

<!-- competency: techno-reseaux -->
## Réseaux et Internet {#glossary .weight-medium}

- **Adresse IP** : identifiant unique de chaque machine sur un réseau (ex : 192.168.1.1)
- **Switch / Commutateur** : distribue les données dans un réseau local (LAN)
- **Routeur** : aiguille les paquets de données entre des réseaux distincts (LAN → Internet)
- **Client / Serveur** : le client envoie une requête HTTP(S), le serveur renvoie les données demandées
- **TCP/IP** : données découpées en paquets → transmission indépendante → réassemblage à l'arrivée
- **RGPD** : Règlement Général sur la Protection des Données — consentement explicite, droit à l'oubli, protection des données personnelles des utilisateurs européens

> [!PIÈGE]
> Switch ≠ routeur. Un switch gère les communications INTERNES à un réseau local (entre les appareils de la maison). Un routeur gère les communications ENTRE réseaux (la maison ↔ Internet). Confondre les deux dans un schéma réseau = perte immédiate de points.

<!-- competency: techno-programmation -->
## Programmation et algorithmique {#concept .weight-medium}

**Structures fondamentales :**
- **Variable** : case mémoire nommée qui stocke une valeur (nombre, texte, booléen)
- **Boucle** : répétition d'instructions — "Répéter N fois" (bornée) ou "Tant que condition" (non bornée)
- **Conditionnelle** : branchement selon un état — "Si condition Alors… Sinon…"
- **Séquence** : instructions exécutées dans l'ordre, l'une après l'autre

**En Python :**
```python
ma_variable = 5
for i in range(5):         # boucle bornée
    print(ma_variable)

if ma_variable > 3:        # conditionnelle
    print("Grand")
else:
    print("Petit")
```

**Données numérisées :** stockage (fichiers), mise en forme (tableur/CSV), transmission réseau

**Démarche projet :**
1. Concevoir l'algorithme (schéma bloc ou pseudo-code)
2. Coder en Python ou Scratch
3. Tester sur un cas simple, puis sur des cas limites
4. Valider sur le système réel

> [!PIÈGE]
> "Répéter 5 fois" exécute le bloc exactement 5 fois — le compteur interne commence à 1 (ou 0 en Python) et se termine à 5 (ou 4). Ne pas confondre la borne avec une condition "tant que i < 5" qui dépend de la valeur initiale de i.

# Dictionnaire Sciences

<!-- competency: pc-atomique -->
## Vocabulaire Sciences {#glossary}

- **Aléa** : événement naturel d'intensité donnée, imprévisible dans le temps
- **Antibiotique** : substance détruisant spécifiquement les bactéries (inefficace contre les virus)
- **Antisepsie** : élimination des micro-organismes sur des tissus vivants
- **Asepsie** : prévention de l'introduction de micro-organismes dans un milieu
- **Capteur** : composant convertissant une grandeur physique en signal exploitable
- **Cellule-œuf / Zygote** : cellule initiale issue de la fécondation
- **Contamination** : pénétration d'agents pathogènes après franchissement des barrières
- **Dorsale océanique** : frontière de divergence sous-marine — volcanisme effusif
- **Épicentre** : point en surface à la verticale du foyer sismique
- **Foyer (hypocentre)** : lieu en profondeur où se produit la rupture sismique
- **Immunité de groupe** : protection collective quand une proportion critique est immunisée
- **Masse** : quantité de matière, invariable selon le lieu (kg)
- **Numéro atomique Z** : nombre de protons dans le noyau
- **Plaque lithosphérique** : fragment rigide et mobile de la surface terrestre
- **Poids** : force gravitationnelle exercée sur un corps — varie selon g (N)
- **Subduction** : plongée d'une plaque lithosphérique océanique dense sous une autre
- **Vaccin** : préparation induisant une réponse immunitaire préventive
