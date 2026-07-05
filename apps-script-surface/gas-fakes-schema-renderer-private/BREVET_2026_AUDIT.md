# BREVET 2026 — Curriculum vs App Audit
**Session:** 2026-06-21 | **Deployment:** @183 | **For 2nd opinion / verification**

Live app: `https://script.google.com/a/krygier.fr/macros/s/AKfycbzEz1TNzeXCfjTLHbpcOUvQHxHnBFj-0l1JvuCLga7J4Gy2bEE25zHJBajvwYdetIcHuA/exec?nav=brevet-2026`

Sources used: `BREVET_2026_CURRICULUM.md` (official exam architecture) + `BREVET_2026_MANUEL.md` (course content). Both generated from PDFs: `source_dnb2026_automatismes.pdf`, `source_cycle4_francais.pdf`, `source_cycle4_histgeo_juin2025.pdf`, `source_emc_programme.pdf`, `source_cycle4_physchimie_jul2025.pdf`, `source_cycle4_svt_jul2025.pdf`, `source_cycle4_technologie_2025.pdf`.

---

## HOW THE APP WORKS

A JSON payload (`payloads/brevet_full.json`) feeds a GAS renderer. Each subject is a hub tab with slides. Slides use atom types:
- `brevet_timeline` — clickable chronological timeline
- `brevet_automatismes` — 20-min timed drill (no calculator)
- `flashcard_deck` — flip cards
- `knowledge_check` — MCQ with explanation
- `key_takeaways` + `steps` — structured lesson blocks

---

## FIXES APPLIED THIS SESSION (patches to brevet_full.json @183)

| # | What | Fix |
|---|---|---|
| 1 | **FR Épreuve: wrong points and timings** | Fixed: Partie 1 = 50 pts/1h10 (was 60 pts/1h30); Rédaction = 40 pts/1h30 (was 1h10) |
| 2 | **Maths Stats: fluctuation d'échantillonnage** | Removed — lycée topic, not in DNB curriculum |
| 3 | **Techno: chaîne d'information** | Removed "→ Agir (actionneur)" — actionneurs belong to chaîne d'énergie |
| 4 | **ASSR2 card: wrong age/usage** | Fixed: "prérequis permis de conduire à 18 ans" (was "cyclomoteur à 14 ans") |
| 5 | **FR Grammaire: missing figures de style** | Added: Allégorie, Oxymore, Périphrase |
| 6 | **FR Conjugaison: missing concordance des temps** | Added card: discours indirect concordance table |
| 7 | **FR Réécriture: missing discours indirect variant** | Added as 3rd step + updated key_takeaways |
| 8 | **HG 1930-1945: URSS/Stalinisme absent** | Added timeline event: Staline 1924-1953 (Holodomor, Goulag, terreur) |
| 9 | **HG 1930-1945: CNR missing** | Added: CNR 1943 (Jean Moulin) |
| 10 | **HG 1942 event: Samudaripen absent** | Updated title + desc to include génocide des Tsiganes |
| 11 | **HG 1945-1991: 6 repères manquants** | Added: 1944 (vote femmes), 1945 (Sécu sociale), 1955 (Bandung), 1962 (Cuba), 1974-75 (Veil/IVG), 1981 (Mitterrand/Badinter) |
| 12 | **HG Europe: 1979 + 1986 missing** | Added: premières élections Parlement EU, Acte Unique |
| 13 | **HG Géographie: zones productives absent** | Added: 10 métropoles, zones agricoles, GPM, diagonale du vide |
| 14 | **HG EMC: Axes 1 & 3 entirely absent** | Added 6 cards: Défenseur des droits, discrimination, laïcité (1905 vs 2004), symboles républicains, DDHC/CIDE, parcours citoyen |
| 15 | **SVT Corps: procréation incomplete** | Enriched: spermatozoïdes, nidation, ménopause. Added: asepsie/antisepsie, vaccination HPV |
| 16 | **SVT Terre: biodiversité absent** | Added: réseaux trophiques + risques climatiques |
| 17 | **PC: ondes + signaux + C=m/V absent** | Added 3 cards: ondes sonores (340 m/s), d=v×t/2 (sonar/radar/écho), C=m/V + sécurité dilution |

---

## CURRENT COVERAGE STATUS BY SUBJECT

### 📐 MATHÉMATIQUES

| Topic | Curriculum requires | App covers | Status |
|---|---|---|---|
| Épreuve structure (2h, 6+14 pts, 2 pts raisonnement) | ✓ | ✓ | ✅ |
| Automatismes drill (20 min, sans calculatrice) | ✓ | ✓ 16 questions | ✅ |
| Fractions↔décimales table (1/2=0.5, 3/4=0.75…) | MEN Oct 2025 | In drill | ✅ |
| Carrés parfaits 1²–12² | MEN Oct 2025 | In drill | ✅ |
| Critères de divisibilité 2,3,5,9 | MEN Oct 2025 | In drill | ✅ |
| Pythagore (direct + réciproque + contraposée) | ✓ | Direct + réciproque ✓ / contraposée **not named** | ⚠️ |
| Thalès (emboîtés + papillon) | ✓ | Emboîtés ✓ / papillon **not named** | ⚠️ |
| Trigonométrie sin/cos/tan | ✓ | ✅ |  |
| Identités remarquables | ✓ | ✅ |  |
| Nombres premiers (liste jusqu'à 30) | ✓ | **Absent** | ❌ |
| Fonction linéaire f(x)=ax vs affine f(x)=ax+b | ✓ | Affine ✓ / linéaire **not distinguished** | ⚠️ |
| Probabilités + arbres | ✓ | ✅ |  |
| Fluctuation d'échantillonnage | ❌ not in DNB | Removed | ✅ fixed |
| Format preuve géométrique (triptyque Données/Propriété/Conclusion) | ✓ | In pièges | ✅ |

### 📖 FRANÇAIS

| Topic | Curriculum requires | App covers | Status |
|---|---|---|---|
| Épreuve: 50 pts Partie 1 (1h10) + 10 pts dictée + 40 pts rédaction (1h30) | ✓ | ✅ fixed @183 | ✅ fixed |
| Réécriture variante 1: singulier→pluriel | ✓ | ✅ |  |
| Réécriture variante 2: changement de temps | ✓ | ✅ |  |
| Réécriture variante 3: discours indirect | ✓ | ✅ added @183 | ✅ fixed |
| Concordance des temps | ✓ | ✅ added @183 | ✅ fixed |
| Figures de style: Métaphore, Comparaison, Personnification, Hyperbole, Antithèse | ✓ | ✅ |  |
| Figures de style: Allégorie, Oxymore, Périphrase | ✓ | ✅ added @183 | ✅ fixed |
| Classes grammaticales + fonctions | ✓ | ✅ |  |
| Propositions subordonnées (relative, complétive, conjonctive) | ✓ | ✅ |  |
| Temps du récit (imparfait/passé simple) | ✓ | ✅ |  |
| Rédaction: argumentatif + narratif structures | ✓ | ✅ |  |
| 4 Entrées littéraires (roman, poésie, théâtre, presse) | ✓ | **Absent** | ❌ |
| Formation des mots (radical, préfixe, suffixe) | ✓ | **Absent** | ❌ |

### 🗺 HISTOIRE-GÉOGRAPHIE + EMC

| Topic | Curriculum requires | App covers | Status |
|---|---|---|---|
| Épreuve: 40 pts HG + 20 pts EMC + règle 30 lignes | ✓ | ✅ |  |
| Thème 1: Nazis (Hitler, antisémitisme, Jeunesses hitlériennes) | ✓ | ✅ |  |
| Thème 1: URSS (Staline, collectivisation, Holodomor, Goulag) | ✓ | ✅ added @183 | ✅ fixed |
| Thème 1: Comparaison totalitarismes (opposés mais similaires) | ✓ | Implied in new event | ⚠️ partial |
| Thème 1: Front Populaire 1936 | ✓ | ✅ |  |
| Thème 2: Shoah (processus génocidaire) | ✓ | ✅ |  |
| Thème 2: Samudaripen | ✓ | ✅ added @183 | ✅ fixed |
| Thème 2: CNR 1943 | ✓ | ✅ added @183 | ✅ fixed |
| Thème 3: Guerre froide (Berlin, plan Marshall, Cuba 1962) | ✓ | ✅ Cuba added @183 | ✅ fixed |
| Thème 3: Conférence de Bandung 1955 | ✓ | ✅ added @183 | ✅ fixed |
| Thème 3: Décolonisation (Algérie) | ✓ | ✅ (timeline 1954-1962) |  |
| Thème 4: 1944 vote femmes, 1945 Sécu sociale | ✓ | ✅ added @183 | ✅ fixed |
| Thème 4: 1974-75 (majorité, Veil IVG), 1981 (Mitterrand, Badinter) | ✓ | ✅ added @183 | ✅ fixed |
| Thème 5 Europe: toutes les étapes CECA→Brexit | ✓ | ✅ incl. 1979+1986 @183 | ✅ fixed |
| Géo: 10 métropoles par nom | ✓ | ✅ added @183 | ✅ fixed |
| Géo: zones productives (Beauce, Bretagne, Val de Loire) | ✓ | ✅ added @183 | ✅ fixed |
| Géo: Grands Ports Maritimes | ✓ | ✅ added @183 | ✅ fixed |
| Géo: périurbanisation, mobilités résidentielles | ✓ | Partial (métropolisation card) | ⚠️ |
| EMC Axe 2: vocabulaire judiciaire | ✓ | ✅ 9 cards |  |
| EMC Axe 1: discrimination, cyber-harcèlement, Défenseur des droits, laïcité | ✓ | ✅ added @183 | ✅ fixed |
| EMC Axe 3: symboles républicains, Loi 1905/2004, DDHC/CIDE, séparation des pouvoirs | ✓ | ✅ added @183 (partial — séparation des pouvoirs not explicit) | ⚠️ |
| Développement construit (méthode 30 lignes, structure 4 blocs) | ✓ | ✅ in Épreuve steps |  |

### 🔬 SCIENCES

| Topic | Curriculum requires | App covers | Status |
|---|---|---|---|
| Épreuve: tirage au sort 2/3 matières, 25 pts chacune | ✓ | ✅ |  |
| PC: modèle atomique, tableau périodique familles | ✓ | Atomique ✅ / familles **absent** | ⚠️ |
| PC: équations de réaction (équilibrage) | ✓ | ✅ |  |
| PC: C=m/V, sécurité dilution | ✓ | ✅ added @183 | ✅ fixed |
| PC: pH (acide/base/neutre) | ✓ | ✅ |  |
| PC: v=d/t, conversions m/s↔km/h | ✓ | ✅ |  |
| PC: masse vs poids (P=mg) | ✓ | ✅ |  |
| PC: U=RI, P=UI, E=Pt | ✓ | ✅ |  |
| PC: ondes sonores (340 m/s, fréquence, amplitude) | ✓ | ✅ added @183 | ✅ fixed |
| PC: signaux de mesure d=v×t/2 (sonar/radar/écho) | ✓ | ✅ added @183 | ✅ fixed |
| SVT: tectonique des plaques, séismes, volcanisme | ✓ | ✅ |  |
| SVT: réseaux trophiques, biodiversité, perturbations anthropiques | ✓ | ✅ added @183 | ✅ fixed |
| SVT: risques climatiques (tempêtes, submersions) | ✓ | ✅ added @183 | ✅ fixed |
| SVT: système nerveux, commande du mouvement | ✓ | ✅ |  |
| SVT: contamination/infection, asepsie/antisepsie | ✓ | ✅ incl. asepsie @183 | ✅ fixed |
| SVT: antibiotiques (bactéries uniquement) | ✓ | ✅ |  |
| SVT: vaccination + immunité de groupe | ✓ | ✅ + HPV added @183 | ✅ fixed |
| SVT: procréation (zygote, nidation, cycle ♀, spermatozoïdes ♂) | ✓ | ✅ enriched @183 | ✅ fixed |
| Techno: chaîne d'énergie + chaîne d'information (corrected) | ✓ | ✅ fixed @183 | ✅ fixed |
| Techno: réseaux, IP, routeur, TCP/IP, RGPD | ✓ | ✅ |  |
| Techno: codage binaire/hexadécimal | ✓ | **Absent** | ❌ |
| Techno: réparation/fabrication (impression 3D, découpe laser) | ✓ | **Absent** | ❌ |

### 🎤 ORAL

| Topic | Curriculum requires | App covers | Status |
|---|---|---|---|
| Format individuel (5 min exposé + 10 min entretien) | ✓ | ✅ |  |
| Format collectif (jusqu'à 3 élèves, 25 min) | ✓ | **Absent** | ❌ |
| 3 projets éligibles (EPI, 4 Parcours, Histoire des Arts) | ✓ | **Not enumerated** | ❌ |
| Barème: 10 pts sujet + 10 pts expression | ✓ | ✅ |  |
| ASSR2 (permis à 18 ans) | ✓ | ✅ fixed @183 | ✅ fixed |
| PIX (5 domaines) | ✓ | ✅ |  |
| PSC1 (PLS, DEA, 15/17/18/112) | ✓ | ✅ |  |
| Aménagements (PAP/PAI/PPS + tiers-temps) | ✓ | ✅ |  |

---

## REMAINING GAPS (not fixed this session)

| Priority | Gap | Location | Suggested fix |
|---|---|---|---|
| 🟠 Medium | **FR: 4 entrées littéraires** (roman engagé, poésie lyrique, théâtre, presse humaniste) | FR Grammaire or new slide | Add flashcard_deck with 4 cards per entrée |
| 🟠 Medium | **FR: formation des mots** (radical, préfixe, suffixe) | FR Grammaire | Add card to grammaire deck |
| 🟡 Low | **Maths: nombres premiers jusqu'à 30** (2,3,5,7,11,13,17,19,23,29) | Maths Algèbre | Add 1 flashcard |
| 🟡 Low | **Maths: Thalès configuration papillon** | Maths Géométrie | Mention in existing Thalès card |
| 🟡 Low | **Maths: contraposée de Pythagore** | Maths Géométrie | Add to existing Pythagore card |
| 🟡 Low | **Maths: fonction linéaire f(x)=ax** distinguished from affine | Maths Algèbre | Update card |
| 🟡 Low | **HG: Trente Glorieuses** (named) | HG 1945-1991 | Add to 1945 event desc or new event |
| 🟡 Low | **HG: comparaison totalitarismes** (même méthodes, idéologies opposées) | HG 1930-1945 | Explicit knowledge_check question |
| 🟡 Low | **HG: séparation des pouvoirs** (exécutif/législatif/judiciaire) | HG EMC | Add to EMC Axe 3 card or new card |
| 🟡 Low | **PC: familles tableau périodique** (alcalins, halogènes, gaz nobles) | PC cards | Add card |
| 🟡 Low | **Techno: codage binaire/hexa** | Techno cards | Add card |
| 🟡 Low | **Techno: réparation/fabrication** | Techno cards | Add card |
| 🟡 Low | **Oral: format collectif + projets éligibles** | Oral slide | Add to key_takeaways |

---

## QUESTIONS FOR 2ND OPINION

1. **FR Épreuve timing**: Is the split definitively 1h10 for Partie 1 and 1h30 for Rédaction, or does the BO leave it flexible?
2. **Réécriture**: Is "passage au discours indirect" as common as singulier↔pluriel and changement de temps in recent sessions?
3. **HG Géographie**: Are the 10 métropoles expected by exact name (memorisation) or just by category?
4. **Sciences tirage au sort**: Does the student need to know all 3 sciences equally, or is there any weighting?
5. **EMC Axe 3**: Is "séparation des pouvoirs" testable as a standalone EMC question or only in the HG context?
6. **Maths automatismes**: Are ALL 16 items in the current drill matching the MEN October 2025 list, or should additional ones be added?
