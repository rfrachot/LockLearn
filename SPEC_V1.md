# LockLearn — Spécification fonctionnelle et technique V1

**Statut :** Draft v0.6  
**Date :** 15 septembre 2026  
**Nom de travail :** LockLearn  
**Plateforme cible :** Home Assistant / HACS  
**Architecture :** locale, self-hosted, local-first  
**Backend :** Python / Home Assistant custom integration  
**Frontend :** TypeScript + Lit, panneau Home Assistant dédié  
**Stockage :** SQLite  
**Distribution :** GitHub + HACS

---

# 1. Vision

LockLearn est une plateforme de **micro-learning self-hosted intégrée à Home Assistant**.

L'objectif initial est de permettre l'apprentissage passif de langues grâce à des notifications régulières sur les appareils des utilisateurs, puis de fournir une interface Home Assistant complète pour les sessions d'apprentissage actives, les quiz, les examens et les statistiques.

Le moteur ne doit cependant **pas être conçu spécifiquement pour le japonais**.

Le japonais — particulièrement les kanji — constitue le premier cas d'usage de référence, mais le modèle doit permettre nativement :

- japonais → français ;
- français → japonais ;
- japonais → anglais ;
- français → anglais ;
- espagnol → français ;
- anglais → allemand ;
- ou toute autre combinaison de langues disponible dans un dataset.

Le moteur doit également être suffisamment générique pour accueillir ultérieurement des contenus non linguistiques : capitales, culture générale, vocabulaire professionnel, mathématiques, etc.

La règle architecturale fondamentale est donc :

> **LockLearn est un moteur d'apprentissage de concepts et de contenus, pas un dictionnaire de japonais.**

---

# 2. Principes du projet

## 2.1 Local-first

Aucun backend LockLearn externe n'est requis.

Le fonctionnement normal doit nécessiter uniquement :

- Home Assistant ;
- l'intégration LockLearn ;
- les datasets installés ;
- éventuellement l'application Companion pour les notifications.

Aucun compte LockLearn.

Aucun serveur SaaS.

Aucune API distante obligatoire.

Aucune télémétrie obligatoire.

Aucune synchronisation cloud LockLearn.

Une connexion Internet peut être utilisée ponctuellement pour :

- installer LockLearn via HACS ;
- vérifier et télécharger des mises à jour de datasets ;
- installer des packs ou assets optionnels.

Le moteur fonctionne sans dépendance Internet externe tant que le client peut joindre l'instance Home Assistant. Le terme normatif est **local-first**, pas local-first : un client hors réseau sans accès distant à HA ne peut pas utiliser le panel ni garantir le retour des actions de notification.

---

## 2.2 Multi-utilisateur natif

Le multi-utilisateur n'est pas une extension future : il fait partie du modèle V1.

Chaque utilisateur peut posséder :

- ses propres profils ;
- ses propres parcours ;
- ses propres réglages ;
- son propre historique ;
- sa propre progression ;
- ses propres statistiques.

Des profils peuvent également être partagés.

Exemple :

```text
Renaud
├── Japonais N5
└── Anglais avancé

Tiffanie
├── Japonais N5
└── Espagnol A1

Lou
├── Japonais débutant
└── Espagnol débutant
```

`Lou` peut être administré simultanément par Renaud et Tiffanie.

---

## 2.3 Content-agnostic

Le moteur ne doit jamais supposer qu'un contenu est nécessairement :

```text
mot → traduction
```

Il doit pouvoir manipuler :

```text
texte
image
audio
contenu riche
```

et des objets pédagogiques :

```text
vocabulaire
kanji
grammaire
expression
phrase
contenu personnalisé
```

---

## 2.4 Multilingue dans les deux sens

La langue source et la langue cible sont indépendantes.

Un même dataset peut donc permettre :

```text
JA → FR
FR → JA
JA → EN
EN → JA
FR → EN
EN → FR
```

sans dupliquer les traductions pour chaque paire.

---

## 2.5 Progression indépendante de la direction

La progression n'est pas attachée directement à un `Concept` ni à une simple paire de langues.

L'unité pédagogique évaluée est une **Card** :

```text
(profile, track, learning_item, prompt_facet, answer_facet)
```

Exemples pour un même kanji :

```text
休 : glyph → meaning_fr
休 : glyph → reading_on
休 : glyph → reading_kun
休 : meaning_fr → glyph
```

Ces cartes peuvent partager le même `Concept`, mais leur progression reste indépendante.

Le `Concept` sert à :

- relier les représentations sémantiques équivalentes ;
- détecter les réponses alternatives valides ;
- construire des distracteurs ;
- produire des statistiques agrégées.

Il **ne porte pas directement le SRS**.

La notion de `direction` est donc remplacée dans le cœur du moteur par une paire de **facettes** :

```text
prompt_facet
answer_facet
```

Une facette peut être linguistique ou multimédia :

```text
text:ja:glyph
text:fr:meaning
text:ja:reading_on
text:ja:reading_kun
image:primary
audio:pronunciation
```

Les paires de facettes autorisées sont déclarées par les datasets / types de LearningItem, et non codées en dur dans le moteur.

---

# 3. Scope fonctionnel V1

La V1 repose sur trois surfaces obligatoires et une surface déjà spécifiée pour V1.1 :

```text
3.1 apprentissage passif / notifications
3.2 quiz passif / notifications
3.3 sessions actives / panel
3.4 examen / V1.1
```

## 3.1 Apprentissage passif

La notification d'apprentissage suit par défaut une **révélation en deux temps**.

### Étape A — tentative de rappel

La première notification montre uniquement le prompt et les éventuels éléments de contexte qui ne révèlent pas la réponse.

Exemple :

```text
休

[ Révéler ]   [ Je ne sais pas ]
```

Un mnémotechnique, une traduction, une lecture ou un exemple qui révèle la réponse ne doit pas être affiché à ce stade.

### Étape B — réponse et auto-évaluation

L'action `Révéler` déclenche le remplacement de la notification, avec le **même tag**, par une seconde notification :

```text
休

repos · se reposer
キュウ

[ 👍 Je savais ]   [ 👎 À revoir ]
```

Le jugement 👍/👎 intervient donc **après une tentative de récupération**, pas après exposition immédiate à la réponse.

Si l'aller-retour vers Home Assistant échoue et qu'un renderer/fallback doit afficher directement la réponse, l'interaction est enregistrée comme :

```text
exposure_only
```

et ne peut pas promouvoir la carte dans le SRS.

### Nouveaux items

La notification est principalement un canal de **récupération espacée**, pas le canal principal d'encodage initial.

Politique V1 recommandée :

```text
nouveaux items introduits principalement dans le panel
1–2 teasers maximum/jour/profil en notification
révisions et relearning prioritaires en notification
```

Les nouveaux items sont préférentiellement introduits dans les ~60 % premiers de la fenêtre active ; la fin de fenêtre privilégie les révisions afin de bénéficier d'un espacement traversant la nuit.

### Invariant pédagogique

Une auto-évaluation produite alors que la réponse était déjà visible n'est jamais considérée comme une preuve de récupération réussie.

## 3.2 Quiz passif

Une notification peut contenir une question de récupération simple.

Format V1 privilégié en notification : **binaire ou 2–3 actions maximum** selon les capacités de la plateforme.

Exemple :

```text
休

[ se reposer ]
[ attendre ]
[ Je ne sais pas ]
```

Règles :

- `Je ne sais pas` est toujours une réponse valide et ne doit jamais être pénalisée comme une faute de devinette ;
- une bonne réponse reçoit un feedback correctif immédiat ;
- une mauvaise réponse montre immédiatement la bonne réponse en mode learning/quiz ;
- 4 à 6 options sont autorisées dans le panel ;
- les QCM de notification ne sont pas considérés comme une mesure forte de production L1→L2 ;
- sur iOS, où les actions peuvent nécessiter une expansion, les formats binaires sont privilégiés et les QCM complets sont dirigés vers le panel.

Le plancher de hasard des QCM est pris en compte dans `ReviewPolicy` : un correct MCQ n'est pas équivalent à une réponse libre exacte.

La saisie libre en notification (`REPLY` Android / `textInput` iOS) est un **spike P0** : elle n'est activée que si les deux plateformes sont suffisamment fiables.

## 3.3 Sessions actives

Le panneau Home Assistant permet de lancer une session immédiatement sans attendre les notifications.

L'utilisateur choisit notamment :

```text
Parcours
Type de session
Nombre de cartes
Facettes / sens de travail
Types de contenu
Stratégie de sélection
```

Formats V1 panel :

```text
learning reveal + auto-évaluation
MCQ 4–6 options
free_text
cloze-MCQ pour grammaire
```

La saisie libre est V1 **dans le panel** pour les cartes dont la normalisation et la `grading_policy` sont compatibles.

Chaque question propose explicitement :

```text
Je ne sais pas
Indice (si disponible)
Signaler cette question
```

Une réponse correcte après indice est enregistrée avec `hint_used=true` et constitue une preuve plus faible qu'une réponse correcte sans indice.

Les sessions entrelacent les types de contenu selon leurs pondérations plutôt que de servir de gros blocs homogènes :

```text
vocab → kanji → grammar → vocab → ...
```

sous réserve des contraintes de sibling burial et de disponibilité.

## 3.4 Mode examen — V1.1

Le mode examen sert à l'évaluation et reste une cible **V1.1**, non bloquante pour `1.0.0`.

Contrairement au quiz classique :

- aucune indication immédiate après chaque réponse ;
- réponses figées une fois validées ;
- questions sélectionnées avant le début ;
- score calculé à la fin ;
- analyse des erreurs disponible après soumission.

L'écran `Revoir mes erreurs` affiche toujours :

```text
prompt
réponse donnée
bonne réponse
contexte / explication disponible
```

Par défaut, un examen ne modifie pas directement les boxes SRS.

Cependant, une récupération correcte pendant l'examen est un vrai événement mnésique. LockLearn enregistre :

```text
retrieval_occurred = true
```

et applique un **cooldown court** (valeur V1.1 recommandée : ~12 h) empêchant de reposer immédiatement la même carte après l'examen, sans promotion durable de box.

Exemple de résultat :

```text
24 / 30
80 %

Points faibles
Matrice de confusion
Réponses lentes
```

# 4. Modèle de domaine

Le modèle repose sur les objets suivants :

```text
Source
SourceSnapshot
Dataset
DatasetBuild
DatasetArtifact
Pack
Concept
Term
LearningItem
Facet
CardDefinition
ContentBlock
Asset
Profile
Track
Progress
ReviewEvent
Session
Exam
Schedule
NotificationInteraction
```

Distinctions fondamentales :

```text
Concept       = unité sémantique
Term          = représentation linguistique
LearningItem  = objet pédagogique
Facet         = face interrogeable d'un LearningItem
CardDefinition= couple prompt_facet → answer_facet
Progress      = état SRS d'une Card pour un profil/track
```

Ces distinctions sont normatives.

---

# 5. Concept

Un `Concept` représente une unité sémantique ou pédagogique abstraite **dans le périmètre d'un dataset ou corpus dont l'alignement sémantique est garanti**.

V1 ne tente pas d'aligner automatiquement des sens provenant de sources indépendantes. LockLearn ne doit par exemple pas prétendre qu'un `sense` JMdict et une définition Wiktionary/Kaikki décrivent le même sens uniquement parce que leurs glosses se ressemblent.

Règle V1 :

```text
Concept = unité sémantique native et fiable de la source
```

Exemples :

```text
JMdict entry + sense index
Wiktionary lexical entry + sense index
LockLearn authored grammar rule
LockLearn authored vocabulary concept
```

Pour JMdict, la granularité recommandée est **le sense**, pas l'entrée entière, lorsque la source distingue plusieurs sens.

Chaque `Concept` possède au minimum :

```text
concept_id
dataset_id
source_record_id
source_sense_id optional
concept_type
```

Le `Concept` sert à :

- regrouper les réponses alternatives fiables au sein d'une source ;
- éviter certains distracteurs manifestement équivalents ;
- agréger certaines statistiques ;
- porter des relations sémantiques explicites.

Il ne porte jamais directement la progression SRS.

L'alignement cross-source est une évolution future explicite, avec provenance, méthode et niveau de confiance.

# 6. Term

Un `Term` est une représentation linguistique.

Exemple :

```text
term_id: ja_休
language: ja
text: 休
```

```text
term_id: fr_repos
language: fr
text: repos
```

```text
term_id: en_rest
language: en
text: rest
```

---

# 7. Relation Concept ↔ Term

Relation plusieurs-à-plusieurs **à l'intérieur d'un dataset ou d'un corpus dont l'alignement est garanti**.

Exemple :

```text
concept_rest_jmdict_001
├── ja_休む
├── en_to_rest
└── en_take_a_rest
```

Un `Term` peut appartenir à plusieurs `Concepts`, ce qui permet de modéliser la polysémie.

```text
bank
├── concept_financial_bank
└── concept_river_bank
```

V1 interdit de fusionner automatiquement des concepts provenant de datasets indépendants à partir d'un simple rapprochement textuel.

Les réponses alternatives considérées comme valides pour un quiz proviennent en priorité :

1. des glosses/termes du **même concept natif** ;
2. des synonymes explicitement fournis par la source ;
3. d'une curation LockLearn versionnée.

Les relations cross-source futures utilisent un modèle explicite :

```text
concept_alignment
source_concept_id
target_concept_id
confidence
method
review_status
```

Aucune relation cross-source n'est considérée comme vérité pédagogique sans validation.

# 8. LearningItem

`LearningItem` représente un objet pédagogique affichable et interrogeable.

Types V1 :

```text
vocabulary
kanji
grammar
expression
```

Un LearningItem peut référencer un ou plusieurs concepts et expose des **facettes**.

Exemple :

```text
learning_item: ja_kanji_休
facets:
  glyph
  mnemonic_keyword_fr
  reading_on
  reading_kun
  radical
  components
```

Une `CardDefinition` déclare une paire de facettes réellement interrogeable :

```text
learning_item_id
prompt_facet_id
answer_facet_id
context_hint_facet_ids[]
answer_semantics
grading_policy
```

`grading_policy` doit pouvoir retourner au minimum :

```text
correct
wrong
unrecognized
```

`unrecognized` signifie : réponse plausible mais non reconnue par le dataset. Elle ne déclenche pas d'échec SRS automatique et propose un signalement de contenu.


`answer_semantics` décrit la nature de la réponse attendue :

```text
single_value
set_of_valid_values
ordered_sequence
free_text
reserved_rule_based
```

`grading_policy` est stable et versionnable :

```text
exact
any_of
fuzzy_normalized
rule_based_reserved
```

V1 implémente au minimum :

```text
exact
any_of
fuzzy_normalized pour les scripts/langues explicitement supportés
```

Le `context_hint` sert à rendre les prompts linguistiquement déterminés lorsque le stimulus seul est ambigu :

```text
part of speech
register
domain
source sense note
example fragment
```

Le moteur central manipule les facettes et policies sans connaître la logique spécifique au japonais.

Types réservés :

```text
sentence
culture
conjugation
custom
```

# 9. ContentBlock

Un LearningItem est constitué de blocs de contenu ordonnés.

Types de blocs prévus :

```text
text
rich_text
image
audio
```

Chaque bloc possède un **rôle sémantique** :

```text
prompt
answer
hint
example
mnemonic
metadata
```

et des métadonnées de révélation :

```text
reveals_answer: true|false
mask_strategy
```

`mask_strategy` permet de masquer une réponse **à l'intérieur** d'un bloc plutôt que de cacher tout le bloc.

Stratégies prévues :

```text
none
hide_block
blank_term
blank_span
replace_with_placeholder
```

Exemple :

```text
私は本を読んでいる。
        ↓
私は本を読んで＿＿。
```

Le renderer reste agnostique au type pédagogique : il sait rendre un bloc.

Le générateur de questions raisonne sur :

```text
facet
role
reveals_answer
mask_strategy
```

`rich_text` n'autorise jamais de HTML arbitraire. Il repose sur un sous-ensemble Markdown/AST strict, sanitizé au build et au rendu. Aucun `unsafeHTML` n'est autorisé sur du contenu dataset.

Un bloc `mnemonic` est traité comme un **indice révélable**, pas comme une partie du prompt par défaut.

Afficher le mnémotechnique avant la tentative de rappel rend l'événement non vérifié pour le SRS.

# 10. Exemple : contenu kanji

```text
LearningItem
type = kanji
concept = concept_rest

blocks:
1. text: 休
2. readings
3. meanings
4. kanji_components
5. example
```

Métadonnées :

```text
JLPT
nombre de traits
lecture ON
lecture KUN
radical
composants
grade scolaire éventuel
tags
```

Important :

**radical / 部首** et **composants graphiques** doivent rester deux notions distinctes.

---

# 11. Exemple : grammaire

Une règle grammaticale comprend à la fois du **matériel de référence** et des cartes de récupération.

Exemple :

```text
LearningItem:
  id: grammar_ja_teiru
  type: grammar
  language: ja
  level: N5
  register: plain

Title:
  〜ている

Summary:
  Action en cours ou état résultant.

Example:
  私は本を読んでいる。
```

V1 ne se contente pas d'un QCM métalinguistique « 〜ている signifie quoi ? ».

Le format obligatoire de pratique grammaticale V1 est au minimum le **cloze-QCM** :

```text
私は本を読んで＿＿。

[ いる ]
[ ある ]
[ なる ]
[ Je ne sais pas ]
```

La saisie libre peut également être utilisée dans le panel lorsque la normalisation est fiable.

Métadonnées de registre :

```text
plain
polite
formal
colloquial
```

Elles s'appliquent aux règles et exemples, et ne sont pas spécifiques au japonais dans le core.

# 12. Images

Le modèle V1 doit être compatible avec des images même si leur utilisation complète n'est pas nécessaire pour la première release publique.

Exemples futurs :

```text
🐱 image → 猫
猫 → image
image → chat
image → cat
```

Les images ne sont pas stockées sous forme de BLOB SQLite sauf justification particulière.

Architecture :

```text
assets/
├── 15/
│   └── cat.webp
├── 27/
│   └── apple.webp
└── ...
```

La DB conserve :

```text
asset_id
mime_type
path
hash
width
height
license
attribution
```

---

# 13. Audio

Le modèle prévoit également :

```text
audio → texte
texte → audio
audio → traduction
```

L'audio est hors MVP fonctionnel, mais le schéma ne doit pas nécessiter de migration conceptuelle majeure pour l'ajouter.

---

# 14. Tags

Tout LearningItem peut posséder plusieurs tags.

Exemples :

```text
jlpt:n5
theme:food
theme:travel
grammar:particle
grammar:verb
difficulty:beginner
source:jmdict
```

Ils doivent être requêtables.

Ils permettront notamment :

```text
Réviser uniquement la nourriture
Réviser uniquement les particules
Examen N5
Afficher mes difficultés liées au radical 言
```

---

# 15. Packs

Un Pack n'est pas une copie des données.

Il représente principalement une **sélection organisée de LearningItems**.

Exemples :

```text
Japanese N5
Japanese Travel
Japanese Food
Spanish A1
English B2
```

Un même LearningItem peut appartenir à plusieurs packs.

Un pack peut déclarer des prérequis et contraintes d'introduction :

```text
prerequisite_card_keys[]
unlock_when
confusable_group
min_intro_gap_days
```

Exemple :

```text
recognition JA→FR
    ↓ débloque après seuil
production FR→JA
```

Le sélecteur de nouvelles cartes filtre les cartes dont les prérequis ne sont pas satisfaits.

Les groupes `confusable` évitent d'introduire le même jour des éléments fortement interférents (`待/持`, `未/末`, `シ/ツ`, etc.).


Exemple :

```text
食べる
```

peut apparaître dans :

```text
Japanese N5
Japanese Food
Japanese Essentials
```

sans être dupliqué.

---

# 16. Dataset versus Pack

Distinction importante :

**Dataset**

Contient les connaissances :

```text
concepts
terms
grammar
examples
assets
```

**Pack**

Contient une sélection pédagogique :

```text
quels contenus ?
dans quel ordre ?
quels niveaux ?
quels tags ?
```

---

# 17. Multilinguisme

Les langues utilisent des identifiants BCP 47 lorsque nécessaire :

```text
fr
en
ja
es
de
fr-FR
en-GB
pt-BR
```

Les `Term` stockent au minimum :

```text
language_tag
script
text
normalized_text
```

`script` suit ISO 15924 lorsque pertinent :

```text
Latn
Jpan
Hira
Kana
Hani
```

`normalized_text` prépare notamment la saisie libre future sans migration structurelle.

La normalisation est **script-aware et versionnée** :

```text
normalization_version
```

Elle ne doit pas appliquer aveuglément les mêmes transformations à toutes les langues.

Principes :

- Unicode NFC/NFKC uniquement lorsque la langue/script l'autorise ;
- casse ignorée lorsque linguistiquement acceptable ;
- accents conservés lorsqu'ils sont sémantiques (`año` ≠ `ano`) ;
- kana/largeur traités par une policy japonaise dédiée ;
- ponctuation/espaces normalisés selon le type de carte.

Changer l'algorithme exige une nouvelle `normalization_version`, un rebuild des index concernés et des tests linguistiques.

Fallback BCP 47 :

```text
fr-FR → fr → default
en-GB → en → default
```

Le fallback sert à l'affichage et à la sélection de contenu, jamais à inventer une traduction absente.


La résolution de langue suit une règle documentée de fallback BCP 47 :

```text
fr-FR → fr → langue par défaut du dataset
```

Le moteur ne doit jamais hardcoder un comportement pédagogique selon une langue dans son cœur. Les comportements spécifiques passent par des adapters internes ou les métadonnées du dataset.

---

# 18. Profil utilisateur

Un `Profile` représente une personne qui apprend.

Un profil n'est pas un compte Home Assistant.

Pour simplifier l'onboarding, un profil peut appliquer un preset :

```text
child
standard
intensive
custom
```

Les presets fixent des valeurs initiales, jamais des limitations irréversibles :

```text
session length
max_new_per_day_cards
daily notification budget
quiet hours
```

Le preset enfant utilise par défaut des sessions plus courtes et un budget de notifications plus faible.

Exemple :

```text
Profile:
  Lou
```

peut exister sans compte HA propre.

---

# 19. Relation avec les utilisateurs Home Assistant

Lorsqu'un utilisateur Home Assistant crée son profil personnel :

```text
HA user Renaud
        ↓
Profile Renaud
```

LockLearn utilise l'utilisateur HA authentifié.

---

# 20. ACL des profils

Table conceptuelle :

```text
profile_members

profile_id
ha_user_id
role
```

Rôles V1 :

```text
owner
editor
viewer
```

### Owner

Peut :

```text
voir
modifier
supprimer
partager
modifier ACL
modifier progression
```

### Editor

Peut :

```text
voir
modifier parcours
modifier planning
lancer sessions
gérer progression
```

Ne peut pas :

```text
supprimer le profil
modifier les owners
```

### Viewer

Peut :

```text
consulter progression
consulter statistiques
```

---

# 21. Plusieurs owners

Un profil doit pouvoir avoir plusieurs owners.

Exemple :

```text
Lou
├── owner: Renaud
└── owner: Tiffanie
```

Cela répond au cas parental sans introduire une hiérarchie artificielle.

---

# 22. Confidentialité entre profils

Par défaut :

```text
Renaud ne voit pas Tiffanie
Tiffanie ne voit pas Renaud
```

Un profil privé n'apparaît pas simplement comme « non modifiable » :

il n'est pas retourné par les API de listing pour un utilisateur non autorisé.

Toutes les vérifications ACL sont effectuées **backend-side**.

---

# 23. Administrateurs Home Assistant

Un administrateur HA possède nécessairement des pouvoirs importants sur l'installation.

Cependant, dans l'interface normale LockLearn :

```text
HA admin ≠ owner automatique de tous les profils
```

Les fonctions système peuvent être administratives :

```text
diagnostic
réparation DB
gestion des datasets
migration
```

sans exposer automatiquement l'apprentissage privé d'autres utilisateurs.

---

# 24. Track / parcours

Un `Track` représente un apprentissage configuré pour un profil.

Exemple :

```text
Tiffanie / Japanese N5
```

Configuration :

```text
profile
pack
source_language
target_language
allowed_directions
content_types
scheduler
SRS settings
notification targets
```

---


Chaque track référence explicitement une `pack_version` pinée ; les mises à jour sont intégrées volontairement après aperçu du diff.

# 25. Plusieurs tracks simultanés

Un profil peut avoir :

```text
Japanese N5
Spanish A1
English B2
```

actifs simultanément.

Chaque track possède sa propre progression.

Un Track peut aussi définir un objectif :

```text
target_date
target_coverage
target_retention
```

LockLearn estime si l'objectif est réaliste avec le quota courant et propose un rythme nécessaire.

Les profils proposent des presets :

```text
child
standard
intensive
custom
```

qui règlent notamment :

```text
session length
max_new_per_day_cards
max_reviews_per_day_cards
daily_push_budget
```


---

# 26. Direction

La configuration utilisateur peut rester exprimée simplement comme :

```text
JA → FR
FR → JA
```

mais cette notion est uniquement une **préférence d'interface**.

Le moteur la résout en `CardDefinition` basées sur des facettes.

Exemple :

```text
JA → FR
```

peut activer :

```text
glyph → meaning_fr
word_ja → meaning_fr
example_ja → translation_fr
```

Le track peut également sélectionner explicitement les cartes autorisées :

```text
glyph → reading_on
glyph → reading_kun
meaning_fr → glyph
```

La progression est distincte pour chaque couple de facettes.

---

# 27. Pondération des contenus

Un Track peut définir :

```text
vocabulary: 50 %
kanji:      30 %
grammar:    20 %
```

Ces valeurs sont des objectifs de volume.

Les sessions et le scheduler privilégient **l'entrelacement** : ils évitent de servir tous les items d'un type en bloc lorsque plusieurs types sont disponibles.

L'arbitrage doit aussi respecter :

```text
items due
relearning priority
sibling burial
new-card quota
content weights
track priority
```

# 28. Progression

La progression est une projection matérialisée par carte.

Clé logique minimale :

```text
profile_id
track_id
learning_item_id
prompt_facet_id
answer_facet_id
```

Un identifiant stable `card_key` peut être dérivé de ce tuple.

Champs principaux :

```text
state
mastery
box
seen_count
verified_correct_count
verified_wrong_count
self_known_count
self_review_count
first_seen_at
last_seen_at
last_result
next_due_at
streak_correct
leech_score
difficulty_factor
last_verified_at
verified_success_since_box
user_state
suspend_until
example_rotation_index
content_status
```

`content_status` permet notamment :

```text
active
removed
superseded
```

`user_state` est indépendant du lifecycle du contenu :

```text
active
known_already
suspended
buried
```

Actions utilisateur :

```text
Je connais déjà
Suspendre
Masquer jusqu'à...
Réactiver
```

À la création d'un track, une calibration optionnelle de 20–40 cartes échantillonnées permet d'estimer ce que l'apprenant connaît déjà et d'éviter plusieurs jours de trivialités.

Un item retiré d'un dataset ne provoque jamais de suppression en cascade de la progression. Il devient un **tombstone** / contenu retiré et reste visible dans l'historique.

---

# 29. SRS V1

La V1 utilise une stratégie SRS simple, déterministe et explicable derrière une interface `ReviewPolicy`.

États de planification :

```text
new
learning
review
relearning
leech
```

`mastered` n'est **pas** un état terminal. C'est une étiquette d'affichage calculée lorsqu'une carte dépasse un seuil de rétention/intervalle. Une carte dite « maîtrisée » reste dans la rotation.

Exemple d'intervalles de base :

```text
box 0 → prochain créneau / learning
box 1 → 8 h
box 2 → 1 jour
box 3 → 3 jours
box 4 → 7 jours
box 5 → 14 jours
box 6 → 30 jours
box 7 → 60 jours
```

Chaque intervalle reçoit un jitter déterministe, par exemple ±10 %.

### Temps réellement écoulé

Le calcul du prochain intervalle tient compte du temps réellement écoulé depuis la dernière récupération vérifiée.

`review_events` conserve :

```text
scheduled_interval_days
elapsed_days
```

Une carte prouvant une rétention très au-delà de son intervalle prévu ne doit pas être rétrogradée artificiellement vers un intervalle plus court.

La formule exacte appartient à la `ReviewPolicy`, mais doit respecter :

```text
effective_interval = f(base_interval, elapsed_days, difficulty_factor, result, jitter)
```

### Difficulté par carte

Chaque carte possède :

```text
difficulty_factor ∈ [0.6, 2.0]
```

Valeur initiale :

```text
1.0
```

Exemple de policy V1 :

```text
verified failure             → × 0.85
verified success no hint     → × 1.05
verified success with hint   → no increase
```

Le facteur est borné et versionné par `policy_version`.

### Learning / relearning steps

Les cartes `new`, `learning` et `relearning` utilisent des étapes courtes explicites, distinctes de la file longue.

Valeurs V1 recommandées :

```text
learning_steps_minutes   = [1, 10, 60]
relearning_steps_minutes = [10, 60]
```

Après un échec, **aucun re-test immédiat** : la carte est replacée plus loin dans la session/file afin d'éviter un faux succès de mémoire de travail.

### Promotion vérifiée

Une auto-évaluation post-révélation peut faire progresser l'état `learning`, mais ne peut pas promouvoir indéfiniment la carte dans les boxes longues.

Règle V1 :

```text
au moins une récupération vérifiée
avant toute promotion au-delà d'un seuil de box configurable
```

Valeur recommandée :

```text
verified_gate_box = 2
```

Une carte au-delà de ce seuil doit périodiquement repasser par une récupération vérifiée.

### Rechute

Un échec vérifié sur une carte en `review` :

```text
state → relearning
box → max(0, box - relapse_penalty)
```

Valeur recommandée V1 :

```text
relapse_penalty = 2 boxes
```

La carte n'est pas remise systématiquement à zéro.

Une carte `relearning` doit être re-testée le jour même avant de retourner dans la file longue.

### Sibling burial

Plusieurs `CardDefinition` issues du même LearningItem sont des **sœurs**.

Le scheduler évite de les servir trop rapprochées afin d'empêcher l'amorçage artificiel.

Policy :

```text
sibling_gap_new_minutes      ≈ 1440
sibling_gap_review_minutes   ≈ 240
```

Ces valeurs sont configurables.

### Quotas et charge

`max_new_per_day` est exprimé en **cartes**, jamais en LearningItems.

Une entrée qui génère quatre CardDefinitions peut donc consommer jusqu'à quatre introductions sur plusieurs jours selon sibling burial.

Défauts recommandés :

```text
child      = 3 nouvelles cartes / jour
standard   = 8 nouvelles cartes / jour
intensive  = 15 nouvelles cartes / jour
```

À la création/modification d'un track, LockLearn estime la charge future :

```text
~X reviews/day in 3 weeks
~Y reviews/day in 3 months
~Z deliverable by notification
```

Un avertissement/Repairs apparaît lorsque `due_count` dépasse durablement `max_reviews_per_day_cards`.

La policy définit :

```text
max_new_per_day_cards
max_reviews_per_day_cards
max_notification_new_teasers
relapse_penalty
relearning_delay
sibling_gap_new_minutes
sibling_gap_review_minutes
leech_thresholds
mode_weights
mastery_formula
verified_gate_box
learning_steps_minutes
relearning_steps_minutes
difficulty_factor_bounds
```

### Mastery

`mastery ∈ [0,1]` est calculé à la lecture à partir de :

```text
box / interval
verified history
time since last verified retrieval
recent relapses
```

Il **décroît avec le temps** depuis la dernière récupération vérifiée.

Le pourcentage « maîtrisé » est une vue de synthèse secondaire ; les métriques primaires sont :

```text
cards due today
retention at last verified review
recent verified accuracy
```

Chaque `ReviewPolicy` possède un `policy_version` stable.

# 30. Correspondance des actions

Le moteur distingue explicitement :

```text
exposure
self_assessment_after_retrieval
verified_mcq
verified_free_text
verified_cloze
exam_retrieval
```

Règle fondamentale :

> **Aucune promotion de box SRS ne peut être déclenchée par une auto-évaluation émise alors que la réponse était déjà visible.**

Conséquences :

```text
exposure_only               → new peut devenir learning, aucune promotion longue
👍 après reveal post-tentative → signal positif faible
👎 après reveal             → signal négatif / relearning possible
panel "À revoir"            → signal négatif
panel "Difficile"           → succès faible
panel "Facile"              → succès fort
MCQ correct                 → signal vérifié moyen
free_text correct           → signal vérifié fort
correct avec hint_used      → poids réduit
Je ne sais pas              → catégorie distincte, traité comme échec pour la planification
unrecognized free_text      → aucun échec SRS automatique
```

En V1, `presentation_to_answer_ms` est **une statistique de fluence**, pas un modulateur automatique du SRS.

Les latences de notification ne servent jamais à mesurer la fluence cognitive.

Après `Je ne sais pas`, LockLearn :

1. affiche la bonne réponse ;
2. journalise `idk` séparément ;
3. replace la carte plus loin dans la session/relearning ;
4. ne la reteste jamais immédiatement.

Pour une réponse `free_text` plausible mais absente des réponses acceptées, l'utilisateur peut choisir :

```text
Ma réponse devrait être acceptée
```

L'événement devient `unrecognized`, n'est pas compté comme erreur SRS, et alimente `locklearn/content/report`.

Lorsque le quota de nouveaux est atteint mais qu'un slot learning reste disponible :

```text
1. relearning due
2. review due
3. weak/leech review
4. skip
```

# 31. Leech

Une carte devient `leech` si l'une des conditions versionnées est satisfaite.

Valeur V1 recommandée :

```text
A. >= 6 échecs vérifiés sur les 10 dernières tentatives dans les 60 derniers jours
OU
B. >= 8 rechutes vérifiées dans les 60 derniers jours
```

Action V1 :

- marquer la carte `leech` ;
- réduire sa fréquence automatique ;
- l'exposer dans « Mes difficultés » ;
- proposer une session ciblée ;
- afficher ses confusions fréquentes ;
- proposer en priorité la création/édition d'un **mnémotechnique personnel** ;
- conserver la réactivation manuelle.

Matrice de confusion :

```text
expected_answer_id
chosen_answer_id
count
```

Exemple :

```text
待 confondu avec 持 : 7 / 9 erreurs récentes
```

Cette métrique sert à la fois à aider l'apprenant et à détecter les cartes/distracteurs défectueux.

## 31.1 Annotations personnelles

Un apprenant peut ajouter une note ou un mnémotechnique personnel sur :

```text
learning_item_id
ou card_key
```

Table :

```text
user_annotations
profile_id
learning_item_id nullable
card_key nullable
note
created_at
updated_at
```

Ces annotations restent privées au profil sauf partage explicite.

Pour un `leech`, la première remédiation proposée est de créer ou modifier un mnémotechnique personnel avant d'augmenter simplement la fréquence de répétition.

# 32. Annulation d'une réponse

Le dashboard doit permettre :

```text
Annuler la dernière réponse
```

Chaque mutation de progression enregistre :

```text
policy_version
dataset_generation
normalization_version
pre_state_snapshot
post_state_snapshot
```

Deux opérations distinctes existent.

### Rebuild d'intégrité

```text
rebuild_progress_from_snapshots()
```

Restaure/rejoue les snapshots historiques avec leur policy d'origine pour reconstruire la projection telle qu'elle a réellement été appliquée.

### Recompute algorithmique

```text
recompute_progress(policy_version=<target>)
```

Recalcule volontairement l'historique selon une nouvelle policy.

Cette opération produit un rapport de divergences, peut être limitée à un profil/track et ne se déclenche jamais automatiquement lors d'une mise à jour ordinaire.

`stats_daily` est également une projection et possède sa propre commande de rebuild.

L'undo restaure le `pre_state_snapshot` de la dernière mutation admissible ou crée un événement compensatoire cohérent. Il ne décrémente jamais naïvement un compteur.

# 33. Historique événementiel

Chaque interaction est stockée dans `review_events`.

Champs minimaux :

```text
id
profile_id
track_id
learning_item_id
prompt_facet_id
answer_facet_id
card_key
mode
question_type
result
answer_id
expected_answer_id
hint_used
retrieval_occurred
scheduled_interval_days
elapsed_days
grading_result
signal_quality
retrieval_occurred
signal_quality
policy_version
dataset_generation
normalization_version
pre_state_snapshot
post_state_snapshot
presentation_to_answer_ms
delivery_to_action_ms
session_id
notification_id
created_at_utc
local_date
timezone_name
utc_offset_minutes
```

Sémantique des latences :

```text
presentation_to_answer_ms
  temps entre rendu effectif de la question dans le panel et réponse
  utilisable pour heuristiques de fluence

delivery_to_action_ms
  temps entre notification envoyée/livrée et action
  inclut le temps avant que l'utilisateur remarque la notification
  ne doit jamais moduler la force mnésique
```

`hint_used=true` réduit la force du signal vérifié.

`retrieval_occurred=true` permet notamment le cooldown court après examen sans promotion de box.

`review_events` reste la source d'audit ; `progress` et `stats_daily` sont des projections reconstructibles selon leur `policy_version`.

# 34. Scheduler

Le scheduler fonctionne d'abord au niveau Profile, puis arbitre les contraintes au niveau target.

`scheduled_slots` est **l'état matérialisé autoritaire** du planning.

Le déterminisme sert uniquement à générer les slots futurs non matérialisés et à rendre `scheduler/preview` reproductible.

Seed recommandé :

```text
profile_id + local_date + scheduler_config_version
```

Modifier une configuration à 14 h ne replanifie jamais rétroactivement les slots déjà envoyés/consommés.

La sélection du contenu pédagogique se fait **au moment de l'envoi**, pas au moment où le slot est créé.

### Notification selection policy

Les rares slots notification sont alloués selon un ordre explicite :

```text
1. relearning due
2. review due proche/au-delà de l'échéance
3. carte à difficulté élevée mais récupérable
4. calibration nécessaire (auto-évaluée mais jamais vérifiée récemment)
5. teaser nouveau, très limité
```

LockLearn évite de gaspiller un slot notification sur une carte dont la prochaine échéance est encore lointaine.

Les nouveaux items sont introduits principalement dans le panel ; les notifications ne servent qu'à quelques teasers contrôlés.

Si une session active est en cours pour le même profil/track, les notifications de ce track sont temporairement suspendues ou différées selon policy.

Le scheduler détecte les sauts d'horloge/NTP et réconcilie les slots au démarrage Home Assistant.

Toutes les dates persistées sont en UTC ; les fenêtres et streaks utilisent la timezone du profil au moment de l'événement.

En cas de contraintes impossibles, l'arbitrage utilise un **weighted round-robin** par priorité de track plutôt qu'un algorithme glouton.

Un Repairs est créé lorsque la demande dépasse durablement la capacité disponible.

### Contexte Home Assistant / réceptivité

Chaque profil peut définir une condition HA évaluée **au moment de l'envoi** :

```text
receptive_when
defer_window_minutes
```

Exemples :

```text
ne pas envoyer si conduite détectée
ne pas envoyer si sommeil
ne pas envoyer si mode cinéma
envoyer préférentiellement si présent au bureau / téléphone en charge
```

Si la condition est fausse, le slot est reporté dans `defer_window_minutes` plutôt que compté comme désintérêt.

V1 collecte aussi les données nécessaires à un futur `receptivity_profile` :

```text
weekday
local_hour
delivered
cleared
answered
delivery_to_action_ms
```

V1.1 pourra déplacer les créneaux vers les périodes où l'utilisateur répond réellement.

### Slots liés aux routines

LockLearn prévoit deux types de slot particulièrement adaptés à Home Assistant :

```text
pre_sleep_consolidation
morning_first_review
```

Ils peuvent être déclenchés par une entité/automation HA (routine coucher, présence au lit, réveil, etc.) plutôt que par une heure fixe.

`pre_sleep_consolidation` privilégie une courte révision des éléments encodés dans la journée.

`morning_first_review` privilégie les éléments de la veille.

# 35. Fenêtre active

Exemple de fenêtre :

```text
08:00 → 20:00
```

Valeur par défaut recommandée pour un profil standard :

```text
4 à 8 notifications maximum / jour / profil
tous tracks confondus
```

Les valeurs plus élevées restent configurables mais ne doivent pas être les exemples par défaut.

Répartition recommandée :

```text
nouveauté teaser : 0–2 / jour
relearning : priorité haute
review : majorité des slots
quiz notification : budget limité
```

Les nouveaux contenus sont favorisés dans les ~60 % premiers de la fenêtre ; la fin de fenêtre favorise les révisions.

# 36. Distribution temporelle

Les slots sont pseudo-aléatoires mais matérialisés et reproductibles.

Exemple raisonnable :

```text
09:10 JA review
11:45 ES review
14:20 JA quiz
17:30 JA relearning
19:10 ES review
```

L'heure de slot n'est **pas** l'heure réelle d'apprentissage.

Doze, FCM/APNs, réseau et disponibilité du Companion peuvent décaler la livraison.

Tous les intervalles SRS sont calculés depuis :

```text
horodatage réel de réponse / récupération
```

et jamais depuis l'heure théorique du slot.

# 37. Paramètres scheduler

Niveau profil :

```text
timezone
active_days
active_windows
minimum_gap
maximum_notifications_per_hour
quiet_hours
```

Niveau target :

```text
minimum_gap
maximum_notifications_per_hour
```

Niveau track :

```text
learning_count
quiz_count
priority
allowed_windows override
max_new_per_day_cards
max_reviews_per_day_cards
```

Les timestamps persistés sont en UTC. Les fenêtres sont évaluées dans le fuseau du profil.

Le scheduler doit traiter explicitement les transitions DST : heure locale inexistante, heure dupliquée, changement de jour local.

---

# 38. Notifications manquées

LockLearn ne doit jamais déclencher un déluge de rattrapage.

Par défaut :

```text
missed slot → expired
```

et non :

```text
missed slot → send immediately later
```

Une stratégie future `limited_catchup` pourra être ajoutée.

---

# 39. Notification en attente

Il faut éviter l'accumulation de questions non répondues.

Politique par défaut :

```text
skip_if_pending
```

Alternatives prévues :

```text
replace
stack
```

### Backoff adaptatif

Le scheduler suit le taux d'expiration **et de notification explicitement balayée/cleared** par target/profil.

Si plusieurs notifications consécutives expirent sans interaction, le budget quotidien diminue progressivement.

Exemple de policy :

```text
3 expirations consécutives → -25 % budget
6 expirations consécutives → -50 % budget
interaction réussie → restauration progressive
```

Le backoff ne modifie jamais les données SRS ; il ne fait qu'adapter le canal de notification.

# 40. Notifications V1

La V1 utilise principalement les notifications actionnables classiques du Companion App.

Chaque notification possède un `NotificationInteraction` persistant :

```text
interaction_id
token
tag
profile_id
track_id
target_id
card_key
stage
created_at
expires_at
status
```

`stage` :

```text
prompt
revealed
answered
```

### Canaux et confidentialité

Android utilise des canaux distincts au minimum pour :

```text
learning/teaser
quiz/review
relearning
```

afin que l'utilisateur puisse régler leur importance séparément.

La seconde notification de révélation utilise le même `tag`, `alert_once`/équivalent et un comportement silencieux afin d'éviter une seconde vibration/son.

Chaque profil peut définir une visibilité lockscreen :

```text
public
private
secret
```

La valeur par défaut d'un profil partagé/enfant est `private`.

Si une action mobile semble avoir été déclenchée mais n'est pas confirmée côté HA avant expiration, LockLearn expose dans le dashboard une surface :

```text
Réponses mobiles non enregistrées récemment
```

plutôt que de laisser l'échec entièrement silencieux.

### Learning — révélation en deux temps

Étape 1 :

```text
prompt seul
[ Révéler ] [ Je ne sais pas ]
```

Étape 2 après action :

```text
même tag
réponse + explication
[ 👍 Je savais ] [ 👎 À revoir ]
```

Le remplacement par `tag` et la latence action→notification de remplacement sont des **gates P0 Android+iOS**.

Si la seconde étape ne peut pas être obtenue de manière fiable, fallback : affichage direct de la réponse et événement `exposure_only`, sans promotion de box.

### Quiz notification

- Android : viser 2–3 actions visibles maximum ;
- iOS : privilégier le binaire / reveal car les actions peuvent nécessiter une expansion ;
- QCM complet : panel ;
- saisie libre notification : spike P0 seulement.

### Consommation single-use

Une réponse est consommée atomiquement :

```sql
UPDATE notification_interactions
SET status='consumed'
WHERE id=? AND status='pending' AND expires_at > ?
```

Le résultat n'est appliqué que si une ligne est consommée.

LockLearn vérifie `event.context.user_id` lorsqu'il est disponible.

### Capabilities target

Le renderer gère :

```text
tag / replace
clear_notification
TTL / timeout
channel / importance Android
visible action count
text input support
media support
```

### Connectivité

Une réponse nécessite que le Companion puisse joindre Home Assistant.

LockLearn est donc **local-first, pas offline-first**.

### Trust model

Un administrateur HA garde techniquement des pouvoirs élevés sur l'instance. LockLearn applique ACL, single-use et expirations, mais ne prétend pas isoler cryptographiquement un profil d'un administrateur HA.

# 41. Live Updates

Les Live Updates / Live Activities ne sont pas une dépendance V1.

Ils pourront faire l'objet d'un renderer expérimental ultérieur.

Le système central doit fonctionner sans eux.

---

# 42. Images dans les notifications

Le renderer notification doit prévoir :

```text
text
image attachment
audio attachment
```

mais la V1 n'est pas obligée d'implémenter tous ces renderers.

---

# 43. Appareils et targets

Un Profile n'est jamais assimilé à un appareil.

Chaque target stocke prioritairement :

```text
target_id
device_registry_id
platform
capabilities
friendly_name
last_resolved_notify_service
```

Le `device_registry_id` est l'identité stable.

Le service `notify.*` est résolu au moment de l'envoi et n'est jamais considéré comme identifiant permanent.

Si le service ne peut plus être résolu :

- target en erreur ;
- Repairs créé ;
- notification non considérée comme envoyée.

Les notifications adressées à un appareil partagé affichent explicitement le nom du profil LockLearn.

Un target peut être marqué :

```text
shared_device: true
```

Les réponses issues d'un target partagé reçoivent par défaut :

```text
signal_quality = reduced
```

et ne franchissent pas seules le seuil de promotion vérifiée (`verified_gate_box`), sauf configuration explicite du profil.


Le scheduler applique aussi :

```text
minimum_gap_per_target
daily_push_budget
adaptive_backoff_state
```

# 44. Plusieurs appareils

Un profil peut recevoir :

```text
learning → téléphone
quiz     → téléphone
```

puis éventuellement :

```text
learning → téléphone + montre
```

Les targets sont configurables par track ou héritées du profil.

---

# 45. Dashboard LockLearn

LockLearn fournit un **custom panel Home Assistant** accessible depuis la sidebar.

Le frontend ne doit jamais accéder directement aux fichiers SQLite.

Toutes les opérations passent par le backend.

---

# 46. Stack frontend

Choix V1 :

```text
TypeScript
Lit
Vite
```

Pourquoi Lit :

- léger ;
- adapté aux Web Components ;
- cohérent avec l'écosystème HA ;
- pas besoin d'embarquer un framework lourd.

Le frontend compilé est distribué avec l'intégration.

Aucune dépendance JavaScript à charger depuis un CDN en production.

---

# 47. Navigation du dashboard

Sections prévues :

```text
Home
Learn
Quiz
Exam
Stats
Profiles
Tracks
Packs
Settings
```

Les sections visibles dépendent des permissions.

---

# 48. Home

Exemple :

```text
Bonjour Renaud

Japanese N5
12 cartes à revoir aujourd'hui
Rétention vérifiée récente : 86 %

[ Continuer ]
[ Quiz rapide ]
[ Examen — V1.1 ]

Dernière session
18 / 20

Prochaine notification
17:42
```

Puis :

```text
English B2
...
```

---

# 49. Profile switcher

Exemple :

```text
Mes profils
  Renaud

Partagés avec moi
  Lou
```

Un utilisateur ne voit aucun profil auquel il n'a pas accès.

---

# 50. Learn

### Introduction

Une carte `new` n'est pas d'abord traitée comme une carte oubliée.

La première présentation est une phase d'encodage explicite :

```text
contenu complet
mnémotechnique / composants utiles
1 exemple
prononciation/lecture pertinente
contexte
```

Elle produit :

```text
mode = introduction
retrieval_occurred = false
```

Après plusieurs cartes intercalées, LockLearn planifie obligatoirement une première récupération dans la même session selon `learning_steps_minutes`.

Aucun échec SRS n'est généré simplement parce qu'un item n'était pas encore connu.


Mode session learning.

### Prompt

```text
休

[ Révéler ]
[ Je ne sais pas ]
```

### Après révélation

```text
休
repos · se reposer

[ 👎 À revoir ]   [ 👍 Je savais ]
```

Un indice ou mnémotechnique n'est révélé qu'à la demande et marque `hint_used=true`.

# 51. Quiz

Formats V1 panel :

```text
MCQ 4–6 options
free_text
cloze-MCQ
```

Architecture réservée :

```text
image_choice
audio_choice
rule_based grading
```

Chaque format inclut :

```text
Je ne sais pas
feedback correctif immédiat hors examen
context_hint si nécessaire
```

`free_text` utilise `grading_policy` et `normalization_version`.

# 52. Distracteurs

Les distracteurs doivent être plausibles sans devenir des enseignants de mauvaises associations.

Stratégies :

```text
same_level
same_type
similar_semantics
same_tag
confusable
random fallback
```

Règles V1 :

- `confusable` est **interdit** pour les cartes `new`, `learning` et `relearning` ;
- il devient disponible en `review` pour entraîner la discrimination ;
- une mauvaise réponse affiche immédiatement la bonne réponse hors examen ;
- un distracteur connu comme réponse valide alternative est retiré ;
- le moteur ne prétend pas éliminer les synonymes inconnus indécidables.

Avant validation, le moteur exclut au minimum :

```text
same native concept
same normalized accepted answer
explicit synonym tag
current sibling answer where relevant
```

Les distracteurs sont **ré-échantillonnés à chaque présentation** et la position de la bonne réponse est équilibrée sur la durée (`answer_position_balance`).

Les exemples tournent lorsqu'un LearningItem en possède plusieurs :

```text
example_rotation_index
```

La rotation reste déterministe pour pouvoir reproduire/debugger une question.

### Feedback correctif

Après une erreur hors examen, LockLearn affiche immédiatement la bonne réponse.

Lorsqu'une confusion connue existe, le feedback peut être **contrastif** :

```text
Tu as choisi 持
Bonne réponse : 待
Différence : ...
```

Les métadonnées de composants/radicaux peuvent enrichir ce feedback sans être obligatoires.

Chaque question propose :

```text
Signaler cette question
```

Les signalements alimentent le workflow qualité du dataset.

Aucun `ORDER BY RANDOM()` sur les gros corpus.

# 53. Session

Une `Session` est persistante.

Champs :

```text
id
profile_id
track_id
type
strategy
status
version
started_at
last_activity_at
completed_at
question_count
current_position
settings_json
```

`version` implémente un contrôle optimiste de concurrence.

`session/answer` exige :

```text
session_id
expected_version
question_id
answer
```

et effectue une mutation CAS.

Si deux clients répondent simultanément à la même question, un seul gagne ; l'autre reçoit :

```text
locklearn/stale_session
```

Le backend expose aussi :

```text
locklearn/session/subscribe
```

pour synchroniser les clients ouverts.

## 53.1 Gestion de la fatigue intra-session

Heuristiques V1 :

- ne pas introduire de nouvelles cartes dans les 25 % finaux d'une session bornée ;
- si la précision vérifiée des 10 dernières réponses chute sous un seuil configurable, proposer :

```text
Terminer la session
Passer en reconnaissance uniquement
Continuer malgré tout
```

LockLearn ne doit pas transformer la fatigue en série artificielle d'échecs pédagogiques.

# 54. Reprise cross-platform

Une session commencée :

```text
sur Android
```

peut être continuée :

```text
sur PC
sur tablette
sur navigateur
```

car l'état réside dans Home Assistant.

---

# 55. Examen

Options V1 :

```text
nombre de questions
directions
content types
pack/level/tags
shuffle
```

Options réservées :

```text
time limit
negative scoring
adaptive difficulty
```

---

Après un examen, l'étape suivante par défaut est **Revoir mes erreurs** avec feedback correctif obligatoire.

Les distracteurs `confusable` sont interdits en examen pour les cartes qui ne sont pas encore stabilisées en `review`.

Même lorsqu'un examen ne modifie pas directement le SRS, chaque carte testée reçoit :

```text
retrieval_occurred = true
```

et une courte fenêtre anti-redondance (par exemple 12 h) empêche de reposer immédiatement la même carte dans une review automatique.

# 56. Sélection examen

Un examen ne doit pas choisir uniquement les items ayant le plus mauvais SRS.

Il doit produire un échantillon représentatif.

La stratégie V1 :

```text
balanced
```

prend en compte :

```text
content_type
level
tags
difficulty
```

---

# 57. Statistiques

L'historique brut reste la source de vérité ; des agrégats journaliers sont précalculés.

`stats_daily` suit notamment :

```text
learning_exposures
verified_retrievals
self_known
verified_correct
verified_wrong
quiz_total
free_text_total
hints_used
new_cards
reviewed_cards
relearning_cards
leech_cards
active_seconds
```

Les matrices de confusion sont calculables depuis les événements :

```text
card_key
expected_answer_id
chosen_answer_id
count
```

Les dates journalières conservent timezone/offset historique ; un changement de fuseau ne réécrit pas le passé.

# 58. Statistiques dashboard

Afficher en priorité des métriques pédagogiquement honnêtes :

```text
cartes à revoir aujourd'hui
rétention lors de la dernière récupération vérifiée
précision vérifiée récente
nouveaux / review / relearning
leeches
confusions fréquentes
```

### Calibration métacognitive

LockLearn compare auto-évaluation et performance vérifiée :

```text
Tu as déclaré connaître 34 cartes cette semaine.
11 ont ensuite été ratées lors d'une récupération vérifiée.
```

Cette métrique ne sert pas à culpabiliser l'utilisateur ; elle l'aide à calibrer son jugement.

### Mastery

Le `mastery %` global reste disponible mais est présenté comme indicateur synthétique secondaire, calculé avec décroissance temporelle.

### Streak

Valeur par défaut :

```text
grace_days = 1
```

Une journée de grâce évite qu'un jour manqué détruise immédiatement la série.

Option future possible : jeton de gel mensuel.

Le streak se base par défaut sur l'atteinte d'un **objectif quotidien de file due**, et non sur une seule réponse.

Exemple :

```text
daily_goal = traiter >= 80 % des cartes dues, avec minimum absolu configurable
grace_days = 1
```

Les jours sans cartes dues sont neutres.

Le dashboard affiche aussi :

```text
self-assessed known vs later verified accuracy
confusion matrix
notification receptivity by hour/day
```


# 59. Home Assistant entities

LockLearn peut exposer certains agrégats comme `SensorEntity`.

Chaque Track possède un UUID stable utilisé comme `unique_id`; les noms et `entity_id` visibles sont laissés à Home Assistant et peuvent changer sans casser l'identité.

Les sensors d'un profil sont regroupés dans un **Device** logique LockLearn représentant le profil ou le track selon le design final retenu en ADR.

Exemples :

```text
Mastery
Quiz accuracy
Streak
Due count
Last exam score
```

Les métriques bruyantes sont désactivées par défaut et mises à jour avec une fréquence limitée / debounce afin de ne pas alimenter Recorder à chaque clic.

La documentation recommande d'exclure de Recorder les sensors non nécessaires à l'historique.

---

# 60. Confidentialité des sensors HA

Important :

les ACL LockLearn et les permissions d'entités Home Assistant sont deux systèmes distincts.

Par conséquent, l'exposition de sensors est **opt-in** par profil/track.

Le dashboard LockLearn privé reste la méthode recommandée pour les statistiques détaillées.

Aucun vocabulaire étudié ou détail personnel ne doit être exposé dans les attributs d'un sensor par défaut.

---

# 61. Automatisations HA

LockLearn exploite Home Assistant comme plateforme d'automatisation à part entière.

Il expose trois mécanismes.

### Services / actions

```text
locklearn.start_session
locklearn.send_now
locklearn.snooze
locklearn.pause_track
locklearn.resume_track
```

### Events pédagogiques

Événements V1 :

```text
locklearn_answered
locklearn_quiz_correct
locklearn_quiz_wrong
locklearn_quiz_idk
locklearn_free_text_unrecognized

locklearn_card_entered_relearning
locklearn_card_mastery_threshold_reached
locklearn_leech_detected
locklearn_confusion_detected

locklearn_daily_goal_reached
locklearn_track_goal_reached

locklearn_session_completed
locklearn_exam_completed

locklearn_dataset_updated
locklearn_notification_cleared
```

Ainsi, une automatisation HA peut par exemple :

```text
quiz correct → flash lumière verte
quiz wrong → flash lumière rouge
3 wrong consécutifs → proposer une pause
daily goal reached → lancer une scène
exam passed → notification / récompense maison
leech detected → afficher un rappel sur dashboard
```

### Payload d'event

Le payload doit rester stable, minimal et respectueux de la vie privée.

Exemple :

```yaml
event_type: locklearn_quiz_wrong
data:
  event_id: <uuid>
  interaction_id: <uuid>
  profile_id: <uuid>
  track_id: <uuid>
  card_key: <stable id>
  session_id: <uuid|null>
  mode: quiz
  result: wrong
  streak_correct: 0
  consecutive_wrong: 2
  content_type: vocabulary
  source_language: ja
  target_language: fr
```

Par défaut, **aucun mot, traduction, phrase ou réponse utilisateur en clair** n'est inclus dans l'event bus.

Un réglage avancé pourra autoriser explicitement un payload enrichi si l'utilisateur en assume la visibilité dans HA.


### Sémantique d'émission

Les events de résultat sont **émis uniquement après commit réussi** de l'interaction dans `state.db`.

Chaque event contient un `event_id` et, lorsqu'il correspond à une réponse, un `interaction_id` stable.

LockLearn garantit au niveau applicatif :

```text
une interaction consommée → au plus un résultat pédagogique appliqué
```

Le bus Home Assistant n'est pas utilisé comme source de vérité : `review_events` reste l'audit canonique.

`locklearn_answered` constitue l'event générique ; les events `locklearn_quiz_correct`, `locklearn_quiz_wrong`, etc. sont des événements de commodité pour rendre les automatisations simples à configurer.

### Sécurité / ACL

Les events sont des sorties d'observation ; ils ne donnent aucun nouveau droit d'écriture.

Les services entrants suivent les règles ACL/unattended documentées §62.1.

### Sensors optionnels

Pour les seuils, historiques génériques et dashboards.

### Blueprints

Au moins trois blueprints d'exemple doivent être fournis :

```text
feedback lumineux correct / incorrect
récompense objectif quotidien
alerte / encouragement après série d'échecs
```

Le moteur expose aussi des compteurs utiles aux conditions :

```text
consecutive_correct
consecutive_wrong
session_accuracy
daily_goal_progress
```

---

# 62. Architecture backend

Arborescence indicative :

```text
custom_components/locklearn/
├── __init__.py
├── manifest.json
├── const.py
├── config_flow.py
├── diagnostics.py
│
├── api/
│   ├── websocket.py
│   └── schemas.py
│
├── core/
│   ├── concepts.py
│   ├── learning.py
│   ├── quiz.py
│   ├── exams.py
│   ├── sessions.py
│   ├── scheduler.py
│   ├── srs.py
│   ├── stats.py
│   └── permissions.py
│
├── storage/
│   ├── content_repository.py
│   ├── state_repository.py
│   ├── migrations/
│   └── schema/
│
├── datasets/
│   ├── manager.py
│   ├── updater.py
│   ├── importer.py
│   ├── manifest.py
│   ├── provenance.py
│   └── validation.py
│
├── notifications/
│   ├── manager.py
│   ├── renderer.py
│   └── events.py
│
├── sensor.py
│
├── frontend/
│   └── locklearn-panel.js
│
└── translations/
    ├── en.json
    └── fr.json
```

---


# 62.1 Cycle de vie Home Assistant et intégrations natives

LockLearn implémente explicitement :

```text
async_unload_entry / reload propre
annulation de tous les timers/callbacks scheduler
fermeture/drain des connexions SQLite
backup hooks adaptés au plancher HA
Repairs / issue registry
UpdateEntity datasets
services/actions Home Assistant
events Home Assistant
```

## Reload/unload

Un reload doit empêcher la création de nouveaux slots, annuler les callbacks, arrêter les opérations longues, fermer readers/writer et désenregistrer les ressources concernées.

Aucun callback d'une ancienne génération ne doit survivre.

## Backup

Avant backup :

```text
queue/stop user writes
PRAGMA wal_checkpoint(TRUNCATE)
snapshot cohérent de state.db
resume writes
```

Le hook possède un timeout strict.

Les gros contenus reconstruisibles (`content.db`, packages datasets, assets publics) doivent idéalement être exclus des backups. P0 valide la stratégie réellement supportée par le plancher HA.

`state.db` reste toujours backupé de manière cohérente.

## Repairs

Au minimum :

```text
dataset obsolete
notification target unresolved
migration failed
DB integrity failure
dataset signature invalid
scheduler configuration infeasible
content cache unexpectedly included in backups
```

## Services / actions Home Assistant

Services V1 :

```text
locklearn.start_session
locklearn.send_now
locklearn.snooze
locklearn.pause_track
```

Autorisation :

- avec `context.user_id` : ACL normale ;
- sans utilisateur : aucune lecture/export/modification destructive ;
- unattended autorisé uniquement si `allow_unattended_actions: true` sur le profil et pour une allowlist d'actions non lisantes/non destructrices.

Toute action unattended est auditée.

## Events HA

Exemples :

```text
locklearn_mastery_threshold_reached
locklearn_exam_completed
locklearn_track_paused
locklearn_dataset_updated
```

Les events ne contiennent jamais de contenu privé inutile.

# 63. Config Entry Home Assistant

LockLearn utilise **une seule Config Entry**.

`manifest.json` :

```text
config_flow: true
single_config_entry: true
```

Les profils et tracks ne doivent pas devenir des Config Entries séparées.

Ils constituent des données applicatives LockLearn.

---

# 64. Pourquoi pas ConfigSubentries pour les profils ?

Les profils :

- sont multi-user ;
- ont des ACL ;
- sont fréquemment créés/modifiés ;
- possèdent une grande quantité de state ;
- ne représentent pas une connexion externe Home Assistant.

Ils restent donc dans `state.db`.

---

# 65. Frontend ↔ Backend

Communication principale :

```text
Home Assistant WebSocket API
```

Le frontend utilise :

```text
hass.callWS(...)
```

Aucune API REST supplémentaire n'est nécessaire sauf éventuellement pour le streaming/téléchargement d'assets.

---


# 65.1 Serving des assets

Les assets de datasets publics ne contiennent aucune donnée utilisateur privée. Ils peuvent être servis par un chemin statique dédié si cela est compatible avec le plancher HA retenu.

Les exports et assets privés ne doivent jamais utiliser un static path public. Ils passent par une route authentifiée ou une URL signée/éphémère compatible avec leur mode d'affichage.

Le choix exact (`async_sign_path`, route dédiée, static public) doit être figé en ADR après prototype P0.

---

# 66. API WebSocket indicative

Commandes principales :

```text
locklearn/bootstrap
locklearn/profiles/list
locklearn/profiles/create
locklearn/profiles/update
locklearn/profiles/delete
locklearn/profiles/share
locklearn/tracks/list
locklearn/tracks/create
locklearn/tracks/update
locklearn/tracks/delete
locklearn/tracks/integrate_pack_update
locklearn/session/start
locklearn/session/get
locklearn/session/answer
locklearn/session/undo
locklearn/session/pause
locklearn/session/complete
locklearn/session/subscribe
locklearn/stats/get
locklearn/scheduler/preview
locklearn/packs/list
locklearn/packs/get
locklearn/datasets/install
locklearn/datasets/update
locklearn/operations/subscribe
locklearn/content/report
locklearn/admin/diagnostics
locklearn/admin/rebuild_progress
locklearn/admin/rebuild_stats
```

Chaque commande contenant un `profile_id` refait l'autorisation backend.

## Contrat d'erreur

```text
locklearn/forbidden
locklearn/not_found
locklearn/invalid_request
locklearn/stale_session
locklearn/dataset_unavailable
locklearn/pack_version_mismatch
locklearn/target_unavailable
locklearn/rate_limited
locklearn/operation_in_progress
locklearn/integrity_error
```

## Pagination

Toute commande listant une collection utilise `limit` + `cursor` avec limites serveur strictes.

## Opérations longues

Installation dataset, import/export, rebuild et migrations exposent :

```text
operation_id
progress
phase
cancellable
error
```

via `locklearn/operations/subscribe`.

# 67. Base de données

Deux domaines logiques restent séparés : `content` et `state`.

V1 utilise **un seul `content.db` actif par génération** au runtime.

Architecture :

```text
state.db

content/
├── current.db
├── generations/
│   ├── <generation_id>.db
│   └── ...
├── packages/
│   └── <dataset_id>/<version>.db
└── catalog.json
```

Les artefacts datasets officiels restent préconstruits séparément par CI.

Lors d'une activation/mise à jour, LockLearn construit `content.next.db` en attachant **un package dataset à la fois** et en copiant ses tables normalisées via `INSERT INTO ... SELECT ...`.

Ce merge local ne parse jamais les corpus amont bruts.

Après validation :

1. créer une nouvelle `generation_id` ;
2. bloquer la création de nouveaux readers sur l'ancienne génération ;
3. drainer les readers existants ;
4. basculer atomiquement `current` ;
5. ouvrir les nouveaux readers ;
6. garder la génération précédente pour rollback.

Ce choix supprime la limite runtime `SQLITE_MAX_ATTACHED` tout en conservant la séparation logique content/state.

# 68. content.db

`content.db` est immutable pendant une génération active.

Tables principales :

```text
schema_version
generation_metadata
languages
licenses
sources
source_snapshots
datasets
dataset_versions
concepts
terms
concept_terms
learning_items
learning_item_concepts
facets
card_definitions
content_blocks
tags
learning_item_tags
packs
pack_versions
pack_items
examples
example_translations
assets_metadata
kanji_metadata
kanji_readings
kanji_components
radicals
grammar_metadata
tombstones
provenance
```

Index minimaux :

```text
terms(language, normalized_text)
learning_items(content_type)
pack_items(pack_version_id, learning_item_id)
card_definitions(learning_item_id, prompt_facet_id, answer_facet_id)
learning_item_tags(tag_id, learning_item_id)
concept_terms(concept_id, term_id)
```

`content.db` contient aussi des pré-agrégats par pack/version :

```text
total cards
total items
items by type/tag/level
```

# 69. state.db

`state.db` contient :

```text
schema_version
profiles
profile_members
tracks
track_pack_versions
track_card_rules
track_content_weights
notification_targets
progress
review_events
user_annotations
sessions
session_items
session_answers
exam_attempts
scheduler_config
scheduled_slots
notification_interactions
stats_daily
settings
```

Les lignes `progress` sont créées **lazy**, à la première exposition/mutation d'une carte.

### Requête chaude : due

Index obligatoire :

```text
progress(profile_id, track_id, state, next_due_at)
```

### Requête chaude : new

Anti-join entre `content.db` et `state.db` avec un seul `content.db` attaché.

Index :

```text
UNIQUE progress(profile_id, track_id, card_key)
```

Le dénominateur de progression vient des pré-agrégats du pack version piné.

Autres index obligatoires :

```text
review_events(card_key, created_at_utc DESC)
review_events(profile_id, created_at_utc DESC)
scheduled_slots(profile_id, scheduled_for_utc, status)
notification_interactions(target_id, status, expires_at)
sessions(profile_id, status, last_activity_at)
```

Il n'existe aucune FK SQL vers `content.db`; l'intégrité cross-domain est applicative.

# 70. Emplacement des DB

Les données runtime ne résident jamais dans `custom_components/locklearn/`.

Séparation logique :

```text
persistent user state:
  state.db

reconstructible content cache:
  current content.db
  downloaded dataset packages
  public assets
```

Le chemin exact du cache content est décidé par ADR/P0 selon les APIs disponibles au plancher HA afin d'éviter de gonfler inutilement les backups.

L'UI affiche :

```text
state size
content cache size
asset size
backup policy
```

Si le plancher HA ne permet pas d'exclure proprement le cache content, l'utilisateur est averti et une politique de purge/re-download est proposée.

# 71. Accès SQLite

Aucun I/O SQLite bloquant sur la boucle async Home Assistant.

Architecture V1 :

```text
state writer:
  ThreadPoolExecutor(max_workers=1)
  connexion dédiée

state/content readers:
  connexions courtes ou thread-local
  read-only content attach
```

Pragmas recommandés :

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
```

Les connexions `sqlite3` ne sont jamais partagées arbitrairement entre threads.

Au runtime, une connexion de sélection peut attacher **uniquement le `content.db` actif**.

Les opérations longues sont chunkées, annulables, soumises à backpressure et ne doivent pas monopoliser le writer. Les interactions utilisateur courtes sont prioritaires.

Les backups SQLite utilisent `sqlite3.Connection.backup()` ou un snapshot cohérent après checkpoint WAL. Une copie brute d'un fichier avec WAL actif est interdite.

# 72. Migrations DB

Chaque DB possède un `schema_version` et des migrations séquentielles.

Une migration doit être :

```text
transactionnelle
versionnée
testée
récupérable
```

Avant migration de `state.db`, une sauvegarde cohérente est créée via `Connection.backup()`.

Les datasets distribués sont immuables par version : on ne migre pas un gros dataset téléchargé en place ; on télécharge ou reconstruit hors instance une nouvelle version compatible.

Une migration du catalogue/génération de contenu ne doit jamais invalider silencieusement `state.db`.

---

# 73. Migration Config Entry

Ne pas confondre :

```text
Config Entry migration
Database migration
Dataset migration
```

Ce sont trois mécanismes distincts.

---

# 74. Sources de contenu et chaîne de mise à jour

Le contenu n'est pas saisi directement dans SQLite à la main et Home Assistant ne doit pas télécharger puis parser les gros fichiers amont bruts lors d'une mise à jour normale.

La chaîne recommandée sépare clairement :

```text
sources amont
    ↓
source adapters / importers
    ↓
normalisation JSONL / SQLite intermédiaire
    ↓
validation sémantique + audit licences
    ↓
build du dataset LockLearn
    ↓
artefact versionné + manifest + checksums
    ↓
GitHub Release
    ↓
Dataset Manager LockLearn
    ↓
staging + validation locale
    ↓
activation atomique d’une génération de datasets préconstruits
```

Cette architecture permet :

- d'éviter de faire tourner un ETL lourd sur chaque instance Home Assistant ;
- de séparer les mises à jour du code et celles des données ;
- d'assurer une provenance reproductible ;
- de respecter les obligations de mise à jour imposées par certaines sources ;
- de fonctionner sans dépendance runtime aux sources Internet une fois le dataset installé ;
- de rollback vers la dernière version valide en cas d'échec.

## 74.1 Source

Une `Source` décrit une source amont indépendante.

Exemple conceptuel :

```text
id: edrdg:jmdict
name: JMdict
provider: EDRDG
license: CC-BY-SA-4.0
update_policy: regular
upstream_cadence: daily
adapter: jmdict_ng
```

Les propriétés minimales sont :

```text
source_id
name
provider
homepage
license_id
attribution_template
adapter_id
refresh_policy
commercial_compatible
notes
```

## 74.2 SourceSnapshot

Chaque ingestion conserve l'identité exacte de la version amont utilisée.

```text
source_id
upstream_version
upstream_date
retrieved_at
source_url
sha256
adapter_version
```

Il doit être possible de répondre à la question :

> « Avec quelles versions exactes des sources ce dataset a-t-il été construit ? »

sans consulter les logs CI.

## 74.3 Provenance au niveau des données

Toute donnée issue d'une source externe doit pouvoir être rattachée à sa provenance.

Selon le type de source, la granularité peut être :

```text
dataset
entry
sentence
asset
```

Les champs disponibles doivent permettre de conserver :

```text
source_id
source_record_id
source_snapshot_id
license_id
author/contributor si requis
modified_from_source
```

En V1, les données provenant de sources indépendantes restent dans des `Concepts` distincts sauf alignement explicitement curaté. Leur provenance ne doit jamais être fusionnée ou perdue.

## 74.4 Stable IDs et mises à jour

Les IDs LockLearn sont stables entre deux versions d'un dataset.

Une mise à jour de dataset ne doit pas modifier arbitrairement :

```text
concept_id
term_id
learning_item_id
facet_id
card_definition_id
```

car `state.db` conserve des progressions qui référencent ces identités.

Une source possédant ses propres IDs stables doit les réutiliser dans le namespace LockLearn lorsque cela est raisonnable.

Exemple :

```text
edrdg:jmdict:1234567
```

Lorsque la source ne possède pas d'ID stable, le pipeline doit générer un identifiant déterministe documenté.

## 74.5 DatasetBuild

Chaque artefact publié possède un manifest de build.

Minimum :

```text
dataset_id
dataset_version
built_at
content_schema_version
minimum_locklearn_version
sources[]
licenses[]
item_counts
sha256
build_tool_version
```

Le manifest doit également permettre d'indiquer :

```text
added_count
changed_count
removed_count
```

par rapport à la version précédente lorsque disponible.


## 74.5.1 Format d’artefact dataset

Artefact officiel recommandé :

```text
<dataset_id>-<version>.zip
├── manifest.json
├── dataset.db
├── assets/ (optionnel)
├── LICENSES/
└── SIGNATURE.ed25519
```

`.tar.gz` peut aussi être supporté. `.tar.zst` n'est pas retenu en V1 afin d'éviter une dépendance Python tierce.

La vérification de signature recommandée utilise Ed25519 via `cryptography`, déjà présent dans l'écosystème Home Assistant.

Le manifest déclare :

```text
compressed_size
uncompressed_size
asset_count
entry_count
schema_version
required_free_disk
content_hash
signing_key_id
```

### Trousseau de clés

```text
key_id
public_key
valid_from
valid_until
status
```

Statuts : `active`, `deprecated`, `revoked`.

La rotation/révocation passe par une release de code LockLearn avant expiration de la clé courante.

Checksum et signature ont des rôles distincts : corruption accidentelle vs authenticité.

### Sécurité archive

Avant extraction : chemins absolus/`..`/symlinks/hardlinks refusés, nombre de fichiers et tailles bornés, expansion ratio contrôlé, espace disque vérifié.

### Reproductibilité

V1 exige la **reproductibilité du contenu**, pas nécessairement du fichier SQLite bit-à-bit. La CI calcule un `canonical_content_hash` sur un export canonique déterministe des tables.

Budgets initiaux :

```text
<= 150 MiB par dataset officiel cible
<= 500 MiB cumulés installés avant avertissement
activation: espace libre >= 2x content généré + marge
```

## 74.6 Distribution des mises à jour

Les mises à jour de datasets sont indépendantes des releases HACS de LockLearn.

**Forte recommandation :** utiliser deux dépôts GitHub distincts :

```text
locklearn
→ code Home Assistant / frontend / HACS
→ licence MIT recommandée

locklearn-data
→ adapters de build, manifests et releases de datasets officiels
→ licences de données conservées source par source
```

Cela permet notamment de ne pas mélanger la licence du logiciel avec les obligations ShareAlike des données.

Aucun serveur permanent n'est nécessaire : GitHub Actions et GitHub Releases suffisent.

## 74.7 Pipeline GitHub Actions recommandé

Un workflow dataset doit pouvoir être déclenché :

```text
schedule
workflow_dispatch
```

Cadence recommandée pour les sources actives :

```text
check hebdomadaire
publication uniquement si les données ont changé
```

Le workflow :

1. récupère les versions amont ;
2. vérifie la licence attendue ;
3. télécharge les sources ;
4. calcule les checksums ;
5. normalise les données ;
6. exécute les validations ;
7. construit l'artefact LockLearn ;
8. génère le manifest de provenance ;
9. exécute les tests de non-régression ;
10. publie une release uniquement si nécessaire.

## 74.8 Update Manager Home Assistant

LockLearn possède un `DatasetManager` local.

Il doit :

```text
lister les datasets installés
connaître leur version
vérifier les versions disponibles
télécharger l'artefact préconstruit dans staging
vérifier signature + checksum + compatibilité
valider le schéma et les licences attendues
valider les IDs/tombstones
activer une nouvelle génération de catalogue
conserver un rollback
```

L'UI affiche :

```text
version installée
version disponible
date des sources amont
âge des données
taille disque
état de mise à jour
changelog
sources et licences
```

Une `UpdateEntity` Home Assistant par dataset officiel est recommandée.

Budgets V1 recommandés pour les datasets officiels :

```text
≤ 150 MiB par artefact officiel par défaut
≤ 500 MiB cumulés installés par défaut avant avertissement
```

Ces seuils sont configurables mais une release officielle qui les dépasse doit le documenter explicitement.

---

## 74.9 Stratégie d'activation

Une mise à jour ne parse jamais les gros corpus amont sur Home Assistant.

Processus :

```text
download package SQLite préconstruit
↓
verify detached Ed25519 signature
↓
verify checksum / manifest
↓
open read-only + integrity_check
↓
validate schema / stable IDs / tombstones
↓
merge package dans content.next.db
↓
validate content.next.db
↓
drain old reader generation
↓
switch current generation
↓
open new readers
↓
retain previous generation for rollback
```

Le merge local est une copie SQL de tables normalisées, pas un ETL amont.

Les items supprimés deviennent tombstones. Cycle autorisé :

```text
active → removed → active
```

Si un item revient plus tard avec le même ID stable, sa progression historique est réutilisée.

## 74.10 Fréquence et données obsolètes

La politique de refresh est définie dans le manifest de la source et non codée en dur dans le moteur.

Exemple :

```text
EDRDG/JMdict:
  check_interval: 7 days
  target_refresh: <= 30 days
```

EDRDG exige qu'un logiciel utilisant ses fichiers dispose d'une procédure de mise à jour régulière et donne l'exemple d'une mise à jour au moins mensuelle pour les services de dictionnaire.

Pour cette raison, les datasets officiels utilisant JMdict/KANJIDIC doivent :

- être reconstruits régulièrement ;
- exposer l'âge des données ;
- vérifier les mises à jour automatiquement par défaut ;
- proposer une mise à jour en un clic ;
- avertir lorsqu'une version dépasse le seuil de fraîcheur défini par la source.

Une installation momentanément hors ligne continue à fonctionner avec la dernière version valide ; LockLearn ne doit jamais casser l'apprentissage uniquement parce qu'une source n'est pas joignable.

## 74.11 Pas de dépendance runtime aux sources amont

Une fois un dataset installé :

```text
JMdict
Wiktionary
Tatoeba
KanjiVG
```

ne sont jamais interrogés pour répondre à une session ou afficher une notification.

Toutes les données nécessaires sont locales.

---

# 75. IDs stables

Chaque objet possède un ID stable.

Exemple :

```text
edrdg:jmdict:1234567
locklearn:grammar:ja:n5:teiru
locklearn:concept:rest
```

Ne jamais utiliser l'index de ligne comme identité.

Les changements d'ID entre versions sont considérés comme des migrations de données et doivent fournir un mapping explicite lorsque de la progression utilisateur peut être concernée.

---

# 76. Pack format

Un pack doit posséder au minimum :

```text
id
name
description
version

languages

dataset_requirements

content_filters/items

license
attribution

sources[]
provenance_requirements

author
source_url

minimum_locklearn_version
```

Chaque `Track` **pin** explicitement une `pack_version`.

Une nouvelle version n'est jamais absorbée silencieusement. L'UI affiche un diff :

```text
+ 42 cards
- 3 removed
~ 8 changed
```

et demande une action explicite `Integrate update`.

Les nouvelles cartes restent soumises à `max_new_per_day_cards`.


Un pack ne doit pas recopier silencieusement du contenu provenant d'un dataset : il référence les IDs stables des LearningItems et Concepts lorsque possible.

Un pack distribué publiquement doit déclarer toutes ses dépendances de datasets et leurs versions minimales compatibles.


## 76.1 Règles de curation japonaises recommandées

Le pack japonais officiel par défaut doit éviter plusieurs cartes techniquement générables mais pédagogiquement faibles.

Règles :

- les cartes `glyph → reading_on` et `glyph → reading_kun` isolées sont **désactivées par défaut** ;
- les lectures sont apprises prioritairement à travers des mots/exemples qui sélectionnent réellement la lecture ;
- les cartes de production sont ancrées sur des **mots complets**, avec okurigana lorsque nécessaire (`se reposer → 休む`, pas `→ 休`) ;
- le « sens » isolé d'un kanji est étiqueté comme **mot-clé mnémotechnique** et non comme traduction sémantique exhaustive ;
- les cartes inverses `mnemonic_keyword → glyph` sont des cartes de production et exigent un format de réponse suffisamment fort avant activation par défaut ;
- les exemples et règles portent un champ `register` lorsque pertinent (`plain`, `polite`, `formal`, etc.) ;
- un prompt ambigu doit inclure un `context_hint` suffisant plutôt que transformer une ambiguïté linguistique en faux échec utilisateur ;
- chaque exemple peut déclarer `required_item_ids[]` ;
- le moteur privilégie un exemple dont le lexique est déjà couvert par l'apprenant ;
- les blocs japonais prévoient dès V1 un champ de lecture/furigana structuré, même si certains renderers avancés arrivent plus tard ;
- si un élément hors couverture est indispensable dans un exemple, le renderer peut afficher le furigana pour éviter un faux échec grammatical.

Ces règles appartiennent au **pack/curation**, pas au core LockLearn : un pack tiers peut faire d'autres choix, mais doit les déclarer explicitement.

---

# 77. Politique de licences et sources fortement recommandées

## 77.1 Principe général

LockLearn doit rester compatible avec :

```text
dons
sponsoring
usage commercial éventuel
redistribution HACS/GitHub
```

Par conséquent, les datasets **officiels distribués avec LockLearn** ne doivent pas incorporer de contenu sous licence :

```text
NonCommercial / NC
NoDerivatives / ND
all rights reserved sans permission explicite
licence inconnue ou ambiguë
```

Licences acceptables par défaut :

```text
CC0 / domaine public
CC BY
CC BY-SA
licences explicitement compatibles avec une réutilisation commerciale
```

Toute nouvelle source passe par un audit de licence documenté avant son intégration au pipeline officiel.

## 77.2 Licence recommandée du projet

**Code LockLearn : MIT.**

Cette licence est recommandée car elle est simple, permissive et n'entre pas en conflit avec la distribution HACS ni avec l'acceptation de dons.

Les données sont licenciées séparément du code.

**Contenu éditorial original LockLearn : CC BY-SA 4.0 recommandé.**

Cela concerne notamment :

```text
explications grammaticales originales
mnémotechniques originales
curation pédagogique originale
packs rédigés par le projet
```

Un fichier ou une base compilée peut contenir plusieurs licences ; LockLearn ne doit jamais prétendre relicencier une donnée amont lorsque sa licence ne le permet pas.

## 77.3 EDRDG — JMdict

**Statut : forte recommandation.**

Usage recommandé :

```text
pivot lexical japonais
formes écrites
lectures
parties du discours
sens anglais
relations entre entrées
informations lexicales japonaises
```

Les composants japonais et anglais couverts par EDRDG sont distribués sous **CC BY-SA 4.0** et l'usage commercial est explicitement autorisé sous réserve du respect des obligations d'attribution et de mise à jour.

Point important : EDRDG précise que les équivalents de traduction non anglais présents dans JMdict — notamment français, allemand, néerlandais, etc. — peuvent être couverts par des copyrights séparés détenus par leurs compilateurs.

**Décision V1 :**

- utiliser JMdict comme source forte pour le japonais et l'anglais ;
- ne pas considérer automatiquement les glosses françaises de JMdict comme réutilisables sous la seule licence générale EDRDG ;
- n'activer leur import officiel qu'après audit documentaire spécifique de leur provenance/licence ;
- privilégier une source clairement licenciée telle que Wiktionary/Kaikki pour les glosses françaises tant que cet audit n'est pas clos.

EDRDG publie les données régulièrement et exige une procédure de mise à jour régulière. Le pipeline LockLearn doit donc conserver la date de la source JMdict utilisée et viser une fraîcheur inférieure ou égale à 30 jours pour les releases officielles.

## 77.4 EDRDG — KANJIDIC2 + RADKFILE/KRADFILE

**Statut : forte recommandation pour le japonais.**

Usage recommandé :

```text
kanji
lectures ON/KUN
nombre de traits
radicaux
composants visibles
métadonnées kanji
```

KANJIDIC2 et RADKFILE/KRADFILE sont couverts par la déclaration de licence EDRDG en CC BY-SA 4.0 avec usage commercial autorisé sous conditions.

KANJIDIC2 contient néanmoins certains champs provenant de contributeurs tiers avec conditions spécifiques. Le pipeline LockLearn doit maintenir une liste blanche des champs importés et documenter toute extension avant de l'activer.

Recommandation V1 : importer uniquement les champs nécessaires à LockLearn, plutôt que recopier aveuglément tout KANJIDIC2.

## 77.5 Wiktionary via Wiktextract / Kaikki

**Statut : forte recommandation pour le multilingue général.**

Kaikki fournit des extractions machine-readable de Wiktionary via Wiktextract et les met à jour régulièrement, généralement au moins une fois par semaine.

Usage recommandé :

```text
FR ↔ EN
ES ↔ FR
DE ↔ FR
JA → FR lorsque disponible
synonymes
prononciations textuelles
catégories grammaticales
formes lexicales
```

Le contenu textuel de Wiktionary est disponible sous **CC BY-SA 4.0** et, selon les éditions, également sous GFDL. Pour LockLearn, la voie de réutilisation préférée est CC BY-SA 4.0 lorsqu'elle est applicable.

Important : les médias ou contenus importés dans une entrée Wiktionary peuvent avoir leur propre licence. Le pipeline officiel ne doit donc pas importer automatiquement images ou sons uniquement parce qu'ils sont référencés par Wiktionary.

## 77.6 Tatoeba

**Statut : forte recommandation pour les phrases d'exemple.**

Usage recommandé :

```text
phrases naturelles
traductions de phrases
exemples de vocabulaire
exemples de grammaire après validation
```

Le texte Tatoeba est par défaut distribué sous **CC BY 2.0 France**, avec attribution de l'auteur requise ; certaines phrases originales peuvent être sous CC0.

Le pipeline doit donc conserver au minimum :

```text
tatoeba_sentence_id
author
license
language
```

Les phrases marquées avec un problème de licence ne doivent jamais être importées.

**Audio Tatoeba : non importé par défaut.**

Les enregistrements audio utilisent différentes licences selon les contributeurs, dont certaines peuvent interdire l'usage commercial. Un futur import audio doit appliquer une liste blanche de licences compatibles et conserver l'auteur de chaque enregistrement.

## 77.7 KanjiVG

**Statut : recommandé, priorité secondaire V1 / forte valeur V2.**

KanjiVG fournit :

```text
SVG de kanji
ordre des traits
sens/direction des traits
informations de composants
radicaux
```

Licence : **CC BY-SA 3.0**.

Usage recommandé :

```text
stroke order
illustrations pédagogiques
futurs exercices d'écriture
visualisation des composants
```

Le schéma Asset V1 doit être capable de référencer KanjiVG même si le renderer d'ordre des traits est livré ultérieurement.

## 77.8 Grammaire

**Forte recommandation V1 : contenu éditorial LockLearn original.**

Les règles grammaticales elles-mêmes peuvent être documentées à partir de connaissances linguistiques générales, mais LockLearn doit rédiger ses propres :

```text
explications
résumés
exemples pédagogiques
quiz
mnémotechniques
```

Le projet ne doit pas copier ou dériver directement un guide sous licence NonCommercial.

Le contenu grammatical original officiel est recommandé sous :

```text
CC BY-SA 4.0
```

afin de rester compatible avec les objectifs de redistribution et d'usage commercial/dons.

## 77.9 JLPT

Le projet ne doit pas présenter comme « liste officielle actuelle du JLPT » une liste tierce reconstruite sans provenance claire.

Les packs :

```text
Japanese N5
Japanese N4
...
```

sont considérés comme des **curations LockLearn compatibles avec les niveaux JLPT**, avec provenance documentée, et non comme une reproduction d'une liste officielle canonique sauf preuve contraire.

La sélection de niveau doit être versionnée comme le reste du contenu pédagogique.

#
## 77.9.1 Compatibilité de distribution et marques

- KanjiVG (CC BY-SA 3.0) reste distribué comme asset/dataset séparé et n'est pas juridiquement fusionné dans un artefact CC BY-SA 4.0.
- Les datasets officiels refusent tout contenu `NC`, `ND`, licence inconnue ou incompatible avec une utilisation commerciale.
- Chaque pack communautaire doit déclarer une licence explicite dans son manifest ; l'installation est refusée si elle manque.
- `LICENSING.md` documente une procédure de signalement/retrait pour contenu litigieux.
- Les packs faisant référence aux niveaux JLPT affichent un disclaimer :

> This project is not affiliated with or endorsed by the Japan Foundation or JEES.

Le nom du produit LockLearn ne doit pas incorporer `JLPT`.

# 77.10 Registre de licences

Chaque licence possède un enregistrement normalisé :

```text
license_id
spdx_or_internal_id
name
version
commercial_use_allowed
derivatives_allowed
share_alike
attribution_required
source_url
notes
```

Le build échoue si une source officielle contient une licence :

```text
unknown
NC
ND
incompatible
```

sauf exception explicitement documentée et approuvée.

## 77.11 Écran Sources & Licences

La licence et la provenance doivent être visibles depuis :

```text
LockLearn → Sources & Licences
```

L'écran doit afficher :

```text
source
version/date amont
licence
attribution
lien source
modifications éventuelles
version du dataset LockLearn
```

Pour les sources exigeant une attribution individuelle, par exemple certaines phrases Tatoeba, l'application peut fournir une vue de détail ou une attribution générée dynamiquement plutôt que de dupliquer toutes les mentions sur chaque écran d'apprentissage.

---

# 78. Localisation de l'interface

L'interface de LockLearn est indépendante des langues enseignées.

Exemple :

```text
UI en français
Source = japonais
Target = anglais
```

V1 doit fournir au minimum :

```text
en
fr
```

---

# 79. Accessibilité

Le frontend doit :

- fonctionner au clavier ;
- posséder des labels accessibles ;
- ne pas reposer uniquement sur la couleur ;
- supporter les tailles d'écran mobiles ;
- respecter autant que possible le thème HA ;
- prévoir les textes longs ;
- ne pas imposer de hover.

---

# 80. Performance

Objectif : aucun polling permanent.

## Budgets V1 mesurables

Sur le matériel de référence minimal défini en P0 :

```text
session/answer p95 backend     < 100 ms hors rendu frontend
next-card selection p95       < 150 ms
scheduler slot generation     < 250 ms / profil / jour
panel initial JS bundle gzip  < 500 KiB cible
state.db 5-year estimate      documentée et testée
content activation            budget par taille de corpus
```

Les valeurs exactes sont ajustables après benchmark P0 puis deviennent des gates de performance.

Aucun `ORDER BY RANDOM()` sur une grosse table. Les distracteurs utilisent des pools/index ou un sampling indexé.

## Observabilité

Logs structurés par domaine : scheduler, notification, dataset, storage, security, session.

Métriques internes : scheduler drift, taux d'expiration des notifications, targets non résolus, latence writer queue, durée activation dataset, latence réponse session.

Elles ne deviennent pas automatiquement des sensors HA.

# 81. Batterie téléphone

LockLearn ne maintient aucune connexion mobile propre.

Les notifications sont envoyées par le mécanisme normal Home Assistant Companion.

Quelques notifications quotidiennes constituent la charge nominale.

Les assets ne doivent pas être téléchargés inutilement.

---

# 82. Sécurité

Invariants : frontend non fiable, backend autoritaire, ACL à chaque mutation, SQL paramétré, aucun secret dans logs, aucune donnée personnelle inutile dans diagnostics.

## Contenu tiers / XSS

`rich_text` n'accepte jamais de HTML arbitraire.

```text
strict Markdown/AST allowlist
no unsafeHTML
no remote script
no eval / Function
sanitize at build
sanitize at render boundary
```

Un custom panel chargé dans le document principal HA ne peut pas définir sa propre CSP indépendante. Un ADR évalue `embed_iframe: true` comme option d'isolation supplémentaire.

## SVG

Tout SVG tiers, notamment KanjiVG, est sanitizé au build : suppression de `<script>`, handlers `on*`, références externes et `foreignObject`. Ne jamais injecter le markup SVG brut dans le DOM.

## Archives et imports

Toute archive est hostile : traversal, symlinks/hardlinks, nombre de fichiers, tailles compressée/décompressée et expansion ratio sont contrôlés.

## Filtres de packs

`content_filters` utilisent JSON Schema strict + whitelist de champs/opérateurs. Ils ne deviennent jamais un mini-langage SQL.

## Intégrité datasets

Les datasets officiels sont signés Ed25519 avec rotation/révocation de clés.

## Assets

Les assets publics peuvent utiliser un chemin statique uniquement s'ils ne contiennent aucune donnée privée. Les exports privés utilisent des URLs temporaires/signées.

## Services et bus HA

Le threat model reconnaît qu'un administrateur HA conserve des capacités élevées. Les services sans `context.user_id` suivent `allow_unattended_actions`.

## Rétention

La suppression définitive d'un profil supprime progress, événements, sessions, stats, ACL et exports temporaires. Les exports expirent automatiquement. La politique de rétention est documentée dans `PRIVACY.md`.

## Maintenance longue

Rebuild/import sont chunkés, annulables, journalisés et reprenables.

# 83. Diagnostics

Un fichier diagnostics doit inclure uniquement :

```text
LockLearn version
HA version
DB schema versions
nombre de datasets
nombre de packs
nombre total de profils sans noms ni identifiants
scheduler status
last errors
migration status
```

Pas :

```text
noms des profils
mots étudiés
réponses
statistiques personnelles détaillées
notification contents
```

---

# 84. Export / import

Le profil doit pouvoir être exporté dans une archive versionnée.

L'export est généré côté backend dans un répertoire temporaire privé et servi via une URL signée/éphémère.

Il contient au minimum :

```text
manifest.json
tracks.json
progress.json
reviews.json (optionnel selon choix utilisateur)
sessions.json (optionnel)
```

L'import applique toutes les protections d'archive définies en sécurité et réalise d'abord un dry-run de compatibilité/mapping.

---


# 84.1 Désinstallation et récupération

Lors de la suppression de l'intégration, LockLearn propose explicitement :

```text
Keep user data
Delete user state
Delete content cache
Delete everything
```

Aucune purge de `state.db` n'est silencieuse.

En cas d'échec `PRAGMA integrity_check` : writer en lecture seule, Repairs, restauration depuis snapshot cohérent si disponible, rebuild des projections si possible, jamais d'écrasement automatique de la seule copie.

Les snapshots de maintenance ont une rétention bornée.

---

# 85. Suppression d'un profil

Deux niveaux :

```text
Archive
Delete permanently
```

Archive : conserve historique et stats, désactive scheduler/notifications.

Delete permanently : supprime les données personnelles du profil dans `state.db`, y compris `review_events`, sessions, stats et ACL, après confirmation forte.

Les agrégats anonymisés ne peuvent être conservés que si `PRIVACY.md` le permet explicitement.

---

# 86. Suppression d'un pack

Un pack utilisé par un Track actif ne peut pas être supprimé silencieusement.

Options :

```text
refus
ou archivage explicite du track
```

La suppression d'un dataset n'efface jamais l'historique utilisateur. Les références deviennent `content_status=removed` tant que nécessaire.

---

# 87. Statistiques longues durée Home Assistant

Les sensors appropriés pourront utiliser les mécanismes standards de `SensorEntity` et `state_class` lorsqu'ils correspondent réellement à leur sémantique.

Ne pas détourner les long-term statistics pour chaque métrique interne.

L'historique complet LockLearn reste dans `state.db`.

---

# 88. Installation

V1 :

```text
HACS
→ Custom repository
→ LockLearn
→ Install
→ Restart HA
→ Settings
→ Devices & Services
→ Add Integration
→ LockLearn
```

---

# 89. Config Flow initial

L'installation doit être extrêmement simple.

Écran initial :

```text
Welcome to LockLearn

☑ Create my personal profile
Language interface: Français

[ Finish ]
```

Les détails sont ensuite configurés dans le panneau LockLearn.

## First-run usable

Une installation neuve ne doit pas ouvrir un panneau vide.

La release HACS embarque un **mini-dataset de démonstration signé** et très petit, par exemple `Japanese Starter` (~100–500 items), afin qu'une première session soit possible en moins d'une minute après installation.

Les datasets complets sont ensuite installables depuis LockLearn.


---

# 90. Pas de YAML obligatoire

Aucun `configuration.yaml` ne doit être requis.

---

# 91. Frontend packaging

Arborescence :

```text
frontend/
├── src/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── dist/

custom_components/locklearn/frontend/
└── locklearn-panel.js
```

Le build frontend est inclus dans la release HACS.

Le `js_url` du panel inclut un cache-buster de version.

Le code gère le fait que `customElements.define()` ne permet pas de redéfinir un tag déjà enregistré : en cas de mismatch frontend/backend, LockLearn demande un **rechargement complet** au lieu de tenter un second `define()`.

## i18n frontend

Le panel possède son propre catalogue i18n FR/EN, distinct des traductions backend HA. Fallback : locale exacte → langue de base → anglais.

## Japonais / CJK

Le renderer japonais met `lang="ja"`, utilise une stack CJK système, assure une taille minimale lisible et réserve `<ruby>/<rt>` pour les furigana futurs. Le rendu Han est testé sur Windows, Linux, Android et iOS.


---

# 92. Architecture repo recommandée

```text
locklearn/
├── custom_components/
│   └── locklearn/
│
├── frontend/
│
├── datasets/
│   ├── src/
│   ├── schemas/
│   ├── adapters/
│   ├── manifests/
│   └── tools/
│
├── tests/
│   ├── backend/
│   ├── frontend/
│   ├── integration/
│   └── datasets/
│
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── development/
│   ├── user/
│   └── data/
│
├── scripts/
│
├── AGENTS.md
├── README.md
├── SPEC_V1.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── ROADMAP.md
├── LICENSE
├── DATA_SOURCES.md
├── DATA_UPDATES.md
├── LICENSING.md
└── hacs.json
```

---

# 93. Tests backend

Framework :

```text
pytest
```

Couverture obligatoire des éléments critiques :

```text
ACL
SRS
scheduler
quiz
distractors
grading_policy + normalization
context_hint / masking
sessions
exam scoring
database migrations
pack import
stats
notification events
```

---

# 94. Tests ACL

Construire explicitement une matrice.

Exemple :

```text
              owner editor viewer outsider
read            ✓      ✓      ✓       ✗
edit track      ✓      ✓      ✗       ✗
answer          ✓      ✓      ✗       ✗
share           ✓      ✗      ✗       ✗
delete          ✓      ✗      ✗       ✗
```

Tout endpoint doit avoir un test d'accès négatif.

---

# 95. Tests scheduler

Utiliser une horloge injectable.

Tests :

```text
quiet hours
timezone
DST
multiple tracks
minimum gap
quota
missed slots
pending notification
reschedule after config change
restart HA
clock jump / NTP reconciliation
adaptive notification backoff
new-item early-window preference
session-active notification suppression
deterministic preview/actual schedule
shared target arbitration
active session suppression
DST nonexistent/duplicated local time
```

---

# 96. Tests SRS

Tests déterministes sur :

```text
👍
👎
correct
wrong
undo
leech
relearning
relapse demotion
sibling burial
max_new_per_day_cards
hint weighting
visible-answer no-promotion
mastery time decay
due_at
signal weights
mastery formula
rebuild projection invariant
```

Aucune dépendance au `datetime.now()` direct dans la logique métier.

Utiliser une abstraction Clock.

---

# 97. Tests DB

Chaque migration doit être testée depuis :

```text
version N
→ version N+1
```

Et idéalement :

```text
ancienne release supportée
→ dernière release
```

---

# 98. Tests frontend

Minimum :

```text
Vitest
```

Pour :

```text
stores
permissions
session state
renderers
answer handling
```

E2E :

```text
Playwright
```

pour les parcours essentiels.

---

# 99. CI

GitHub Actions :

```text
Backend lint
Backend typing
Backend tests

Frontend lint
Frontend typecheck
Frontend tests
Frontend build

Dataset validation
Schema validation
Source licence audit
Provenance validation
Dataset canonical-content reproducibility check

HACS validation
Hassfest validation

Migration tests
```

---

# 100. Versioning

Utiliser SemVer :

```text
MAJOR.MINOR.PATCH
```

Exemple :

```text
1.0.0
1.1.0
1.1.1
```

Les versions du logiciel sont indépendantes des versions de datasets.

---

# 101. Compatibility matrix

Plancher initial V1 :

```text
Home Assistant >= 2025.2
```

Ce plancher peut être relevé avant `1.0.0`, mais pas abaissé sans validation explicite.

P0 le confirme contre : single config entry, static paths, Repairs, backup lifecycle, device registry, custom panel et WebSocket subscriptions.

Documenter : LockLearn version, minimum HA, latest HA testé, DB schema, Content schema, Frontend protocol version.

Tests CI : minimum supported HA + latest stable HA.

Pour les tests d'intégration, utiliser `pytest-homeassistant-custom-component` avec des jobs/pins séparés lorsque nécessaire.

# 102. Documentation : principe général

La documentation est un livrable du projet.

Elle ne doit jamais être considérée comme :

> « quelque chose qu'on écrira quand le code sera fini ».

Chaque feature non triviale doit mettre à jour simultanément :

```text
code
tests
documentation
```

---

# 103. Documentation requise

## README.md

Destiné aux utilisateurs potentiels.

Doit contenir :

```text
vision
screenshots
fonctionnalités
installation
quick start
compatibilité
liens docs
licence
support
sponsors/dons éventuels
```

---

# 104. SPEC_V1.md

Le présent document.

Il définit :

```text
scope
comportement attendu
invariants
critères d'acceptation
```

Il ne doit pas devenir une description ligne par ligne du code.

---

# 105. ARCHITECTURE.md

Vue actuelle de l'architecture.

Doit expliquer :

```text
backend
frontend
data flow
databases
scheduler
notifications
authentication
permissions
pack system
```

Schéma recommandé :

```text
                    Home Assistant
                         │
             ┌───────────┴──────────┐
             │                      │
      LockLearn Panel          Companion App
             │                      │
          WebSocket             Notification
             │                      │
             └──────────┬───────────┘
                        │
                  LockLearn Core
                        │
      ┌─────────────────┼──────────────────┐
      │                 │                  │
 Scheduler            SRS            Session Engine
      │                 │                  │
      └─────────────────┼──────────────────┘
                        │
             ┌──────────┴──────────┐
             │                     │
   catalog + datasets        state.db
```

---

# 106. DATA_MODEL.md

Documenter :

```text
Concept
Term
LearningItem
Facet
CardDefinition
ContentBlock
Pack
Dataset
Profile
Track
Progress
Session
ReviewEvent
```

Avec exemples réels.

---

# 107. DATABASE.md

Doit contenir :

```text
ER diagram
tables
PK/FK
indexes
constraints
migration policy
backup policy
```

Le fichier SQL des migrations reste source de vérité technique.

---

# 108. PACK_FORMAT.md

Doit documenter précisément le format communautaire des packs/datasets.

Inclure :

```text
manifest
IDs
languages
content types
tags
licenses
sources
source snapshots
provenance
assets
compatibility
validation
update policy
```

Prévoir un JSON Schema machine-readable.

## 108.1 DATA_SOURCES.md

Doit documenter chaque source officielle :

```text
usage
provider
format amont
adapter
licence
attribution
champs importés
champs volontairement exclus
risques connus
fréquence amont
politique de refresh
```

Les décisions de licence importantes doivent pointer vers un ADR ou une note d'audit datée.

## 108.2 DATA_UPDATES.md

Doit documenter :

```text
workflow GitHub Actions
source snapshots
build reproducible
release manifest
checksums
dataset manager
staging
activation atomique
rollback
local/runtime behavior without upstream connectivity
stale-data warnings
```

## 108.3 LICENSING.md

Doit séparer clairement :

```text
licence du code
licence de la documentation
licences des datasets
licences des assets
attributions obligatoires
politique des contributions
compatibilité commerciale
```

Inclure une liste explicite des licences autorisées/interdites pour les datasets officiels.

---


Le format documente également :

```text
Facet IDs stables
CardDefinition IDs stables
answer_semantics
grading_policy
context hints
register
normalization_version
sibling relationships
```

# 109. PERMISSIONS.md

Documenter :

```text
HA User
Profile
owner/editor/viewer
admin
frontend security
backend ACL
entity privacy caveat
```

---

# 110. SRS.md

Documenter :

```text
algorithme
états
intervalles
mapping des réponses
leech
mastery
future FSRS migration
relearning / relapse policy
sibling burial
signal quality / hint weighting
mastery time decay
metacognitive calibration
```

Le but est qu'un futur changement d'algorithme puisse être analysé sans lire tout le code.

---

# 111. SCHEDULER.md

Documenter :

```text
quotas
fenêtres
randomisation
minimum gap
multi-track arbitration
quiet hours
DST
restart behavior
pending notifications
missed slots
```

---

# 112. NOTIFICATIONS.md

Documenter :

```text
Android
iOS
actions
platform capabilities
tag / replace
clear notification
TTL / expiration
channels / importance
pending state
connectivity requirements
push quotas / provider limits
shared targets
notification lifecycle
threat model des actions Companion
```

Les limites de nombre d'actions sont stockées par capacité de target et vérifiées contre la documentation Companion au moment de chaque release majeure.

---

# 113. FRONTEND.md

Documenter :

```text
Lit architecture
routing
state management
WebSocket interface
renderers
responsive design
accessibility
sanitization
asset loading
```

Le panel privilégie des composants propres stylés via les CSS custom properties/thèmes Home Assistant. L'utilisation d'éléments frontend internes non API (`ha-dialog`, etc.) doit être minimale, isolée et couverte par des tests de compatibilité.

Aucun HTML de dataset n'est rendu directement.

---

# 114. API.md

Chaque WebSocket command doit documenter :

```text
request
response
permissions
errors
version
```

Les contrats doivent également exister sous forme machine-readable lorsque possible.

---

# 115. MIGRATIONS.md

Trois familles :

```text
HA Config Entry
state.db
content generation/catalog schema
dataset package/content schema
```

Chaque migration importante possède :

```text
raison
version source
version cible
rollback/recovery
```

---

# 116. SECURITY.md

Doit contenir :

```text
threat model
ACL
SQL security
asset serving
diagnostics redaction
backup
reporting vulnerabilities
```

---

# 117. PRIVACY.md

LockLearn étant multi-user, documenter clairement :

```text
ce qui est privé
ce qui est partagé
ce qui apparaît dans HA entities
ce qui est exporté
ce qui part vers le Companion App
```

---

# 118. DEVELOPMENT.md

Installation développeur complète :

```text
Python setup
HA dev instance
frontend setup
dataset build
tests
lint
build release
```

Objectif :

> un nouveau contributeur doit pouvoir lancer LockLearn sans devoir demander « comment tu fais tourner le bordel ? ».

---

# 119. TESTING.md

Décrire :

```text
test pyramid
commands
fixtures
fake clock
test DB
frontend tests
E2E
CI
```

---

# 120. RELEASE.md

Checklist :

```text
tests green
frontend build
dataset validation
migration test
version bump
CHANGELOG
GitHub release
HACS validation
compatibility check
```

---

# 121. TROUBLESHOOTING.md

Cas utilisateurs :

```text
notifications absentes
mauvais target
scheduler arrêté
DB migration failure
pack incompatible
frontend panel absent
permissions
```

---

# 122. ROADMAP.md

Séparer clairement :

```text
Committed
Candidate
Ideas
Rejected
```

Éviter que chaque idée devienne implicitement une promesse.

---

# 123. ADR — Architecture Decision Records

Les décisions techniques importantes doivent recevoir un ADR.

Arborescence :

```text
docs/adr/
├── ADR-0001-sqlite-storage.md
├── ADR-0002-concept-term-model.md
├── ADR-0003-multi-user-acl.md
├── ADR-0004-custom-panel.md
├── ADR-0005-srs-v1.md
├── ADR-0006-normal-actionable-notifications.md
└── ...
```

Chaque ADR contient :

```text
Context
Decision
Alternatives
Consequences
Status
```

Exemple :

**ADR-0001 : SQLite plutôt que JSON runtime**

Conserver la raison.

Ne pas seulement écrire :

> « On utilise SQLite ».

Mais :

> « JSON a été envisagé, puis abandonné comme stockage runtime en raison des relations many-to-many, du multi-user, des historiques et statistiques. JSONL reste utilisé comme format source des datasets. »

C'est exactement le genre d'information qui évite qu'un futur contributeur « simplifie » l'architecture en cassant la logique initiale.

---

# 124. AGENTS.md

Comme le développement peut utiliser des agents de code, un `AGENTS.md` doit faire partie du repo.

Il doit donner :

```text
vision du projet
architecture rapide
invariants
commandes tests/build
fichiers de référence
règles de migration
règles ACL
règles DB
règles frontend
Definition of Done
```

Invariants à mettre en gros :

```text
NEVER bypass backend ACL.

NEVER perform blocking DB I/O on HA event loop.

NEVER mutate a released DB schema without a migration.

NEVER couple LockLearn Core to Japanese-specific behavior.

NEVER expose private learning data through HA entities by default.

NEVER store runtime state inside custom_components/.
```

---

# 125. CHANGELOG.md

Format structuré :

```text
Added
Changed
Fixed
Deprecated
Removed
Security
```

Les migrations doivent être signalées explicitement.

---

# 126. Commentaires de code

Documenter surtout :

```text
pourquoi
contraintes
invariants
cas non évidents
```

Éviter les commentaires inutiles du type :

```python
# Increment counter
counter += 1
```

---

# 127. Documentation générée

Lorsque possible, générer automatiquement :

```text
DB diagram
JSON schemas
WebSocket contracts
pack schemas
```

afin d'éviter les divergences entre documentation et code.

---

# 128. MVP technique

Le développement doit rester incrémental avec des gates installables.

### P0 — Architecture spikes / skeleton

Avant toute feature métier, valider sur une vraie instance HA minimale :

```text
HACS installable
Config Flow
minimum HA = 2025.2 candidate
Custom Panel + cache/update behavior
Android actionable notification
iOS actionable notification
action → replacement notification latency/tag semantics (Android+iOS)
visible actions without expansion per platform
notification free-text input spike (Android+iOS)
action → silent replacement notification / alert_once behavior
mobile_app_notification_cleared signal
lockscreen visibility per platform
shared-device identity/signal-quality behavior
event.context.user_id
device_id → notify service resolution
backup pre/post hook behavior
content cache / backup policy
SQLite state writer + content attach
content generation merge benchmark
session WebSocket subscription
```

Puis livrer :

```text
SQLite repositories
Custom Panel minimal
CI
Repairs skeleton
service/event skeleton
```

**Gate P0 :** aucun choix fondamental de notification, backup, storage ou panel ne reste basé sur une hypothèse non testée.

### P1 — Content core minimal

```text
Concept / Term / LearningItem / Facet / CardDefinition
1 mini dataset japonais signé
packages dataset SQLite préconstruits + génération content.db fusionnée
sanitization
update/rollback minimal
```

### P2 — Profils / tracks / ACL

```text
personal profile
shared profile
owner/editor/viewer
tracks
```

### P3 — Learning + SRS

```text
two-step learning reveal
quiz MCQ
panel free_text
panel cloze-MCQ grammar
progress par card
review_events + rebuild
SRS + relearning + sibling burial
elapsed-time-aware intervals + difficulty_factor
learning/relearning steps
prerequisite graph + confusable intro spacing
leech + confusion matrix
introduction mode
user annotations / personal mnemonics
track calibration / known-already state
```

### P4 — Scheduler + notifications

```text
scheduler déterministe
context-aware delivery / defer conditions
pre-sleep + morning review hooks
multi-track + multi-target arbitration
notification_selection_policy
context-aware receptive_when/defer
pre-sleep + morning review slots
adaptive backoff + cleared signal
notifications actionnables
expiration/tag/clear
```

### P5 — Dashboard utile

```text
Home
Learn
Quiz
Track config
Profile sharing
basic stats
```

**À ce stade seulement : première alpha réellement testable.**

### P6 — V1 hardening

```text
services/events HA
Repairs
UpdateEntity datasets
backup hooks
export/import sécurisé
migrations
E2E
full docs
```

### P7 — V1.1 candidates

```text
exam mode
advanced stats
optional HA sensors
image/audio renderers
```

L'examen reste une fonctionnalité souhaitée et spécifiée, mais n'est pas bloquant pour considérer le moteur V1 stable si le coût de finition menace la release.

---

# 129. V1 obligatoire

La release `1.0.0` doit avoir un **cœur réduit mais complet** :

```text
HACS installation
UI setup
custom panel

multi-user
shared profiles
multiple tracks

multilingual terms/facets
vocabulary
kanji
grammar reference + cloze-MCQ

learning two-step reveal
quiz MCQ
panel free_text
free learning session
free quiz session

introduction mode + learning steps
basic SRS par card/facets
elapsed-time-aware scheduling + difficulty_factor
verified promotion gate
prerequisite/card unlock rules
known-already / suspend / bury states
personal annotations/mnemonics
relearning / relapse policy
sibling burial
weak items / leech / confusion matrix
undo fiable + rebuild projection

scheduler déterministe
multi-track + multi-target arbitration
notifications actionnables robustes

basic stats dashboard
metacognitive calibration

SQLite state + génération content.db + packages datasets
migrations
backup-safe lifecycle
Repairs
services/events HA

pack/dataset model
provenance/licensing
signed dataset update + rollback
commercial-compatible official source policy

FR + EN UI
secure export/import

complete core documentation
services/actions HA de base

events HA de base

CI/tests
```

La philosophie V1 est : **moteur fiable et publiable avant richesse fonctionnelle**.

---

# 130. Prévu dans le data model mais pas obligatoirement complet en 1.0

Prévu architecturalement ou candidat V1.1 :

```text
exam mode + score
advanced statistics
optional HA sensors
image learning
embedded audio
image answers
audio questions
advanced lexical relations
conjugation-specific renderers
```

Le schéma V1 doit permettre ces fonctionnalités sans refonte structurelle majeure.

---

# 131. Hors scope V1

Explicitement repoussé :

```text
speech recognition
pronunciation scoring
handwriting recognition
kanji stroke recognition
OCR
AI-generated courses
AI-generated answers
LLM tutoring
cloud sync between HA instances
central LockLearn accounts
public marketplace backend
real-time multiplayer
gamification complexe
leaderboards publics
FSRS optimisé
native Android/iOS LockLearn app
```

---

# 132. Évolutions candidates V2+

## Audio

```text
listening comprehension
pronunciation examples
TTS
```

## Saisie libre avancée

V1 supporte déjà `free_text` dans le panel pour les policies simples.

V2+ étend notamment :

```text
morphologie complexe
plusieurs graphies équivalentes
règles grammaticales de correction
feedback détaillé
```

Normalisation configurable :

```text
case
accent
punctuation
kana variants
```

## Cloze avancé / génération dynamique

V1 inclut le cloze-QCM grammatical.

V2+ ajoute la génération dynamique de trous, plusieurs trous et correction libre.

## Image learning

```text
image → word
word → image
```

## Advanced Japanese

```text
stroke order
kanji families
phonetic components
radical statistics
furigana
conjugation
```

## FSRS

Remplacement optionnel du SRS simple.

## Community Packs

Installation de datasets tiers.

## Anki interoperability

```text
import
export
```

## Teacher mode

Gestion avancée de profils enfants/élèves.

---

# 133. Invariants architecturaux V1

Ces règles doivent survivre aux évolutions futures :

### 1.

```text
Profile != HA user
```

### 2.

```text
Profile != device
```

### 3.

```text
Track != pack
```

### 4.

```text
Concept != term
```

### 5.

```text
Learning mode != content type
```

Ainsi :

```text
grammar
```

n'est pas un mode.

Elle peut être :

```text
apprise
quizée
examinée
```

### 6.

```text
Progress is card/facet-specific.
```

### 7.

```text
Frontend never owns permissions.
```

### 8.

```text
Content data != user state.
```

### 9.

```text
HA Recorder != LockLearn database.
```

### 10.

```text
The core must not depend on Japanese.
```

### 11.

```text
Released dataset IDs are stable across updates unless an explicit migration mapping exists.
```

### 12.

```text
Official LockLearn datasets never import NC, ND, unknown or commercially incompatible content.
```

### 13.

```text
Dataset updates never replace the last-known-good content before validation succeeds.
```

---


### 14.

```text
Progress belongs to CardDefinition, not Concept.
```

### 15.

```text
Dataset updates never parse raw upstream corpora on the HA instance; merging prebuilt SQLite packages into a new content generation is allowed.
```

### 16.

```text
Cross-database referential integrity is application-enforced and tested.
```

### 17.

```text
Third-party rich content is never trusted HTML.
```

### 18.

```text
Review events are the audit source; progress is a rebuildable projection.
```

### 19.

```text
Notification actions are not strong user authentication.
```


### 20.

```text
Stable progression identity includes facet_id and card_definition_id.
```

Toute modification incompatible de ces IDs exige un mapping de migration explicite.


### 21.

```text
No SRS box promotion from self-assessment when the answer was already visible.
```

### 22.

```text
New-item quotas are counted in CardDefinitions, not LearningItems.
```

### 23.

```text
Sibling CardDefinitions are spaced to avoid priming-driven false success.
```

### 24.

```text
Notification timestamps never substitute for actual retrieval timestamps.
```

### 25.

```text
A hint changes the quality of the learning signal and is persisted.
```

### 26.

```text
Mastered is a display label, not a terminal scheduling state.
```


### 27.

```text
A self-assessed signal cannot indefinitely promote a card without a verified retrieval.
```

### 28.

```text
A new card is introduced before it is tested; first exposure is not treated as failure.
```

### 29.

```text
A failed card is not re-tested immediately from working memory.
```

### 30.

```text
Notification delivery is context-aware when the profile configures receptive_when.
```

### 31.

```text
Shared-device responses are lower-confidence unless explicitly trusted.
```

### 32.

```text
Home Assistant quiz/result events never expose learning content by default.
```

# 134. Critères de qualité

Une fonctionnalité n'est terminée que si :

```text
code terminé
tests terminés
typing/lint OK
permissions testées
migration considérée
documentation mise à jour
changelog mis à jour si pertinent
```

---

# 135. Definition of Done V1

LockLearn V1 est considérée terminée lorsqu'un scénario complet fonctionne :

### Renaud

```text
installe LockLearn depuis HACS
termine l'onboarding avec le mini-dataset
crée son profil
crée un track
configure 08:00–20:00 / learning / quiz
reçoit des notifications
répond 👍 / 👎 et aux quiz
ouvre le dashboard
enchaîne 20 cartes
reprend la même session depuis un autre client
voit ses statistiques de base
voit la provenance/licence du dataset
installe une nouvelle version de dataset
voit le diff d'un pack
intègre explicitement la nouvelle pack_version
ne perd aucune progression
```

### Tiffanie

```text
crée son profil privé
active Japanese et Spanish
possède ses propres réglages et progression
```

### Lou

```text
profil sans compte HA obligatoire
Renaud + Tiffanie owners
progression indépendante
notifications sur appareil partagé clairement identifiées
```

### Résilience

```text
reload HA sans double scheduler
backup/restore sans corruption state.db
target Companion renommé → Repairs + résolution
dataset invalide/signature invalide → version précédente conservée
session concurrente → stale_session géré
```

L'examen, les sensors HA avancés, image/audio et statistiques enrichies restent des objectifs V1.1 et ne bloquent pas `1.0.0`.

# 136. Objectif produit final de V1

LockLearn V1 doit pouvoir être résumé ainsi :

> **A self-hosted micro-learning platform for Home Assistant.**
>
> Learn passively through smart notifications, actively through learning sessions and quizzes, and keep all your learning data at home.

Le japonais et les kanji constituent le premier excellent showcase.

Mais l'architecture doit déjà permettre que quelqu'un installe LockLearn demain pour apprendre :

```text
anglais
espagnol
allemand
médecine
capitales
vocabulaire technique
```

sans avoir à modifier le moteur.

---

# 137. Philosophie finale

LockLearn ne cherche pas à remplacer immédiatement Duolingo, Anki ou une application linguistique spécialisée.

Son avantage est différent :

```text
Home Assistant est déjà présent.
Home Assistant connaît les utilisateurs.
Home Assistant connaît les appareils.
Home Assistant sait notifier.
Home Assistant est cross-platform.
Home Assistant dispose d'un dashboard.
Home Assistant sait historiser des sensors.
```

LockLearn fournit au-dessus :

```text
contenu
progression
scheduler
SRS
quiz
examens
statistiques
```

sans imposer un nouveau cloud, un nouveau compte ou un nouveau serveur.

L'objectif V1 est donc de construire **le moteur générique correctement**, puis d'utiliser l'apprentissage du japonais comme première démonstration ambitieuse de ses possibilités.
Les blocs textuels peuvent également porter, lorsque pertinent :

```text
reading
furigana
ruby_segments[]
```

Ces champs font partie du schéma V1 même si certains renderers avancés arrivent plus tard.

