# Dictionnaire de données — Backlog Triage Express

## Backlog de démo (`data/backlog_demo_github_streamlit.json`)

30 issues réelles, ouvertes, label `type:enhancement`, dépôt `streamlit/streamlit`, récupérées le 2026-08-23 via `GET https://api.github.com/repos/streamlit/streamlit/issues?state=open&labels=type:enhancement&per_page=30&sort=comments&direction=desc` (API publique GitHub, sans authentification). Les pull requests sont exclues (filtre sur le champ `pull_request` absent).

| Champ | Type | Origine | Exemple |
|---|---|---|---|
| `id` | entier | `number` de l'issue GitHub | `611` |
| `titre` | texte | `title` | `"Export to standalone HTML file"` |
| `description` | texte (tronqué à 1200 caractères) | `body` | — |
| `url` | texte | `html_url` | `https://github.com/streamlit/streamlit/issues/611` |
| `reactions` | entier | `reactions.total_count` | `285` |
| `commentaires` | entier | `comments` | `65` |
| `labels` | liste de texte | `labels[].name` | `["type:enhancement", "status:unlikely", "area:utilities"]` |
| `cree_le` | date | `created_at` (tronqué au jour) | `2019-03-04` |

## Schéma attendu pour un backlog uploadé (mode "Uploader mon propre backlog")

Mêmes champs obligatoires : `id`, `titre`, `description`, `reactions`, `commentaires`, `labels`. Pour un backlog qui n'a pas de "réactions"/"commentaires" au sens GitHub, transposer le signal le plus proche disponible (ex. nombre de votes clients, nombre de demandes similaires reçues) — le principe (un signal de demande mesuré, pas inventé) reste valable au-delà de GitHub.

## Formules de scoring

### Impact (1-5, quantile du backlog chargé)

```
engagement = reactions + commentaires
impact = 1 + round(4 * rang_percentile(engagement))
```

Le rang est calculé **relativement au backlog chargé**, pas sur une échelle absolue — un backlog de 10 tickets internes calmes et un backlog de 30 issues très suivies d'un projet open-source populaire n'ont pas la même échelle brute, mais le classement relatif à l'intérieur d'un même backlog reste ce qui compte pour prioriser.

### Urgence (1-5, base 3, ajustée par labels)

```
urgence = 3
        + 2 si un label contient "confirmed" ou "likely" (les mainteneurs jugent le sujet légitime/probable)
        - 2 si un label contient "unlikely" (explicitement écarté)
        + 1 si un label contient "papercut" (friction quotidienne signalée par la communauté)
        clampé entre 1 et 5
```

### Effort (1-5, **proxy de départ, toujours éditable**)

```
surface = nombre de labels commençant par "area:" ou "feature:"
effort = 2 + max(0, surface - 1) // 2
       - 1 si un label contient "papercut" (signalé comme correctif mineur)
       clampé entre 1 et 5
```

**Limite assumée et documentée** : aucune heuristique texte ne mesure la complexité de développement réelle. Ce score est un point de départ (plus un ticket touche de zones fonctionnelles distinctes, plus il est probable qu'il soit complexe), **toujours éditable ligne par ligne dans l'app avant toute décision**. Sur le backlog de démo, ce proxy ne dépasse jamais 3/5 (aucun item n'a 5+ labels area/feature) — un résultat honnête de ce jeu de données précis, pas un signe que la formule est cassée (voir `PROMPT_LOG.md`).

## Classification en quadrant

| Impact | Effort | Quadrant |
|---|---|---|
| > 3 | ≤ 3 | Quick win |
| > 3 | > 3 | Big bet |
| ≤ 3 | ≤ 3 | Fill-in |
| ≤ 3 | > 3 | Time sink |

Seuil fixe au milieu de l'échelle 1-5 (>3), volontairement simple à expliquer en session de passation plutôt qu'un seuil relatif recalculé à chaque fois.

## User story

- **Scaffold manuel** (toujours disponible) : `En tant que ___, je veux {titre en minuscules}, afin de ___.` — les blancs ne sont jamais remplis automatiquement, pour ne pas prétendre deviner un rôle ou un bénéfice non exprimés dans le texte source.
- **Premier jet IA** (optionnel, BYOK) : Claude Haiku reformule à partir du titre + des 800 premiers caractères de la description, avec consigne explicite de ne pas inventer de détail technique absent du texte source. Retourne `None` si l'appel échoue (l'app affiche alors le scaffold manuel), jamais une erreur silencieuse remplacée par une réponse inventée — même pattern que `pharm-automate/src/rag_agent.py`.
