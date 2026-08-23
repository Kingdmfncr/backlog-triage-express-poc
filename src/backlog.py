"""Moteur de structuration de backlog : scoring impact/effort/urgence (grille
transparente, pas une boîte noire), classification en quadrant, reformulation
en user story (scaffold manuel toujours disponible, brique IA optionnelle
BYOK pour un premier jet à relire).

Choix assumé sur l'effort : aucune heuristique ne peut mesurer la complexité
technique réelle d'un ticket depuis son seul texte. Le score d'effort produit
ici est un point de départ approximatif (surface fonctionnelle touchée), pas
un verdict — il est toujours éditable dans l'app avant toute décision."""
from __future__ import annotations

import pandas as pd


def load_backlog(items: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(items)
    required = {"id", "titre", "description", "reactions", "commentaires", "labels"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Champs manquants dans le backlog : {missing}")
    return df


def _quantile_score(series: pd.Series) -> pd.Series:
    """Score 1-5 relatif au backlog chargé (quantiles), pas des seuils absolus
    universels — un backlog interne calme et un backlog OSS très suivi n'ont pas
    la même échelle, mais le classement relatif à l'intérieur d'un même backlog
    reste ce qui compte pour prioriser."""
    ranks = series.rank(pct=True)
    return (ranks * 4).round().astype(int) + 1  # 1 à 5


def score_impact(df: pd.DataFrame) -> pd.Series:
    """Impact = engagement mesuré (réactions + commentaires), un vrai signal de
    demande, pas une estimation inventée."""
    engagement = df["reactions"] + df["commentaires"]
    return _quantile_score(engagement)


def score_urgence(df: pd.DataFrame) -> pd.Series:
    """Urgence basée sur des labels réels : confirmé/probable par les mainteneurs
    -> urgent ; explicitement écarté -> pas urgent ; friction quotidienne signalée
    ('papercut') -> légère hausse. Base neutre à 3/5, jamais 0 ni 6 (clamp)."""
    def _score(labels):
        s = 3
        labels_l = [str(l).lower() for l in labels]
        if any("confirmed" in l or "likely" in l for l in labels_l):
            s += 2
        if any("unlikely" in l for l in labels_l):
            s -= 2
        if any("papercut" in l for l in labels_l):
            s += 1
        return max(1, min(5, s))
    return df["labels"].apply(_score)


def score_effort_proxy(df: pd.DataFrame) -> pd.Series:
    """Proxy d'effort = surface fonctionnelle touchée (nombre de labels
    area:/feature: distincts), atténué si 'papercut' (signalé comme correctif
    mineur par la communauté). Base à 2/5 (plutôt bas par défaut), clamp 1-5.
    Rappel : proxy de départ, à ajuster manuellement dans l'app."""
    def _score(labels):
        labels_l = [str(l).lower() for l in labels]
        surface = sum(1 for l in labels_l if l.startswith("area:") or l.startswith("feature:"))
        s = 2 + max(0, surface - 1) // 2
        if any("papercut" in l for l in labels_l):
            s = max(1, s - 1)
        return max(1, min(5, s))
    return df["labels"].apply(_score)


def classify_quadrant(impact: int, effort: int) -> str:
    """Seuil fixe au milieu de l'échelle 1-5 (>3 = fort/élevé) — simple à
    expliquer en session de passation, pas besoin de recalculer un seuil relatif
    pour comprendre le classement d'un item donné."""
    impact_fort = impact > 3
    effort_eleve = effort > 3
    if impact_fort and not effort_eleve:
        return "Quick win"
    if impact_fort and effort_eleve:
        return "Big bet"
    if not impact_fort and not effort_eleve:
        return "Fill-in"
    return "Time sink"


def user_story_template(titre: str) -> str:
    """Scaffold toujours disponible, sans IA : ne prétend jamais deviner le
    'en tant que' ou le 'afin de', laissés à compléter par un humain qui connaît
    le contexte réel du produit."""
    return f"En tant que ___, je veux {titre.strip().rstrip('.').lower()}, afin de ___."


def user_story_ai(titre: str, description: str, api_key: str) -> str | None:
    """Premier jet de reformulation via Claude (BYOK, jamais stocké). Retourne
    None si l'appel échoue — l'app retombe alors sur le scaffold manuel, jamais
    une erreur silencieuse remplacée par une réponse inventée. Même pattern que
    pharm-automate/src/rag_agent.py."""
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        prompt = (
            "Reformule ce ticket de backlog produit en une user story au format strict "
            "'En tant que [rôle], je veux [action], afin de [bénéfice].'. "
            "Reste concis (1 phrase), déduis le rôle et le bénéfice du contexte fourni "
            "sans inventer de détail technique qui ne serait pas dans le texte source.\n\n"
            f"Titre : {titre}\nDescription : {description[:800]}"
        )
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=150, temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return None


def structurer_backlog(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["impact"] = score_impact(out)
    out["urgence"] = score_urgence(out)
    out["effort_propose"] = score_effort_proxy(out)
    out["quadrant"] = [classify_quadrant(i, e) for i, e in zip(out["impact"], out["effort_propose"])]
    out["user_story_scaffold"] = out["titre"].apply(user_story_template)
    return out.sort_values(["impact", "urgence"], ascending=[False, False])
