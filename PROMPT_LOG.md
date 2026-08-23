# PROMPT LOG : comment j'ai construit ce projet avec l'IA

> Ce fichier documente ma méthode de travail réelle avec l'IA (Claude).

---

## Contexte de départ

3e et dernier projet du même audit que `lead-qualification-automation-poc` et `data-triage-express-poc` : le sprint `Structuration de backlog produit` (700€) n'avait qu'une preuve approximative (`ai-use-case-prioritizer`, qui fait un scoring 5D de projets IA — un angle voisin mais pas le même livrable que "backlog réorganisé en grille impact/effort/urgence + reformulé en user stories").

## Étape 1 — Trouver une vraie source de backlog "en vrac"

Un vrai backlog client n'était pas disponible sans nommer une entreprise. Plutôt que d'inventer des tickets, utilisation de l'API publique GitHub (`api.github.com/repos/.../issues`, sans authentification) pour récupérer 30 vraies demandes d'évolution du dépôt **streamlit/streamlit** — l'outil même sur lequel tourne tout le reste du portfolio. Choix assumé : ce n'est pas un "vrai backlog produit interne", mais c'est un vrai backlog non trié, avec de vrais signaux de demande (réactions, commentaires) et de vrais labels de priorisation posés par de vrais mainteneurs — largement suffisant pour démontrer la méthode, et strictement honnête sur son origine (disclosure claire dans le README).

## Étape 2 — Refuser de faire semblant de mesurer l'effort

Premier réflexe (rejeté) : dériver un score d'effort depuis la longueur du texte de description. Problème identifié en le construisant : la longueur d'un ticket ne dit rien de sa complexité technique réelle, et prétendre le contraire aurait été le genre d'automatisation qui a l'air rigoureuse mais ment. **Décision** : le score d'effort reste un **proxy explicitement approximatif** (surface fonctionnelle touchée via les labels `area:`/`feature:`), affiché comme un point de départ éditable dans l'app (`st.data_editor`), jamais présenté comme une mesure fiable. Documenté explicitement dans `DATA_DICTIONARY.md`.

## Étape 3 — Refuser de faire semblant de deviner le "en tant que" / "afin de"

Même logique pour la reformulation en user story : générer automatiquement un rôle et un bénéfice à partir du seul titre aurait été inventé, pas déduit. Le scaffold manuel (`user_story_template`) laisse ces deux champs vides (`___`), toujours. Une brique IA optionnelle (Claude, BYOK, jamais stockée, même pattern que `pharm-automate/src/rag_agent.py::repondre_avec_claude`) propose un premier jet à partir du titre + de la description réelle, explicitement présenté comme "à relire", pas comme un livrable final.

## Étape 4 — Vérification en local et un résultat honnête, pas forcé

7 tests Pytest écrits contre les 30 vraies issues (voir `tests/test_backlog.py`), tous verts au premier passage complet. App testée dans le navigateur : les 4 onglets, aucune erreur console. **Constat en testant** : sur ce backlog précis, la matrice ne remplit que 2 des 4 quadrants (Quick win et Fill-in) — aucun item n'atteint le seuil "effort élevé" avec la formule choisie. Tentation écartée : ajuster la formule juste pour "mieux remplir" la démo. Décision : garder la formule telle qu'honnêtement conçue, documenter ce résultat comme un fait du jeu de données réel (pas un bug), et vérifier séparément par un test unitaire dédié (`test_classify_quadrant_all_four_cases`) que les 4 branches de classification fonctionnent bien, indépendamment de ce backlog précis.

---

## Ce que ce projet prouve (pour un client ou un prospect)

| Compétence démontrée | Preuve dans ce projet |
|---|---|
| Scoring transparent et documenté | Formules impact/urgence/effort entièrement écrites dans `DATA_DICTIONARY.md` |
| Honnêteté sur les limites d'une automatisation | Effort explicitement présenté comme un proxy éditable, jamais un verdict |
| Usage cadré de l'IA générative | Reformulation IA optionnelle, jamais imposée, jamais substituée au scaffold honnête |
| Rigueur méthodologique | Résultat "décevant" (2 quadrants sur 4) assumé et expliqué plutôt que maquillé |
| Réutilisation cohérente du portfolio | Même pattern Claude BYOK que `pharm-automate`, même principe de données réelles que les 2 autres projets de ce lot |

---

## Ma conclusion

> Je ne suis pas développeuse. Mais je sais qu'un outil qui prétend mesurer ce qu'il ne peut pas mesurer (l'effort de dev depuis un texte, l'intention derrière un ticket) est plus dangereux qu'utile — je préfère un outil honnête sur ses limites à un outil qui a l'air plus intelligent qu'il ne l'est.

*Gisèle Metouck, Consultante Business Analysis & Automation IA*
